"""Server-side Nicrron and PRISM calls. All results are explicitly labeled."""

from __future__ import annotations

import asyncio
import json
import os
import time
from datetime import datetime, timedelta, timezone
from uuid import uuid4

import httpx

AGENT_ID = "trumptrades-sample-explainer"
MODEL = "openai/gpt-4o-mini"
_model_call_lock = asyncio.Lock()
_model_calls = 0
CONTEXT = {
    "OWNER": "The filer and the person whose asset was reported may differ. Check the disclosed owner field.",
    "TIMING": "A disclosure can appear weeks after a transaction, so it is historical information.",
    "AMOUNT": "A disclosed amount is a range, not the exact amount spent or received.",
    "PRICE": "A price dip is a change from a reference; it does not predict a rebound.",
    "SOURCE": "Open the evidence panel to read the exact fictional filing row behind this card.",
}


def prism_configured() -> bool:
    return bool(os.getenv("PRISMTRACE_PROJECT_ID") and os.getenv("PRISMTRACE_API_KEY"))


def kb_result_context(data: dict, expected_row_id: str) -> tuple[str | None, str]:
    results = data.get("results", [])
    if not isinstance(results, list) or not results:
        return None, "PRISM KB has no matching document; upload and assign the sample filing"
    context = json.dumps(results, ensure_ascii=False)
    if f"Row {expected_row_id}" not in context:
        return None, "PRISM KB returned no matching source row; check document assignment"
    return context[:6000], "PRISM KB found the sample filing row"


async def kb_search(query: str, expected_row_id: str) -> tuple[str | None, str]:
    if not prism_configured():
        return None, "PRISM credentials not configured"
    payload = {"project_id": os.environ["PRISMTRACE_PROJECT_ID"], "agent_id": AGENT_ID, "query": query, "limit": 3}
    try:
        async with httpx.AsyncClient(timeout=12) as client:
            response = await client.post("https://api.prism.blockconvey.com/api/knowledge-base/search", json=payload,
                                         headers={"X-PRISMtrace-Key": os.environ["PRISMTRACE_API_KEY"]})
            response.raise_for_status()
            return kb_result_context(response.json(), expected_row_id)
    except (httpx.HTTPError, ValueError, AttributeError):
        return None, "PRISM KB unavailable; check document assignment and key"


async def nicrron_explain(row: dict, retrieval: str | None, question: str = "") -> tuple[str | None, int, str]:
    global _model_calls
    key = os.getenv("NICRRON_API_KEY")
    if not key:
        return None, 0, "Nicrron key not configured"
    async with _model_call_lock:
        if _model_calls >= 30:
            return None, 0, "Demo model-call limit reached; using verified sample summary"
        _model_calls += 1
    source = retrieval or row["raw_excerpt"]
    messages = [
        {"role": "system", "content": ("This is fictional sample data. Select the topic that best answers the user's question: "
                                        "OWNER, TIMING, AMOUNT, PRICE, or SOURCE. Return exactly one of those words and nothing else. "
                                        "Use the supplied sample row and retrieval only. No investment recommendation.")},
        {"role": "user", "content": f"Sample row: {row['raw_excerpt']}\nRetrieved context: {source}\nUser question: {question or 'What should a beginner know about this filing?'}"},
    ]
    started = time.monotonic()
    try:
        async with httpx.AsyncClient(timeout=25) as client:
            response = await client.post("https://api.nicrron.ai/v1/chat/completions",
                                         headers={"Authorization": f"Bearer {key}"},
                                         json={"model": MODEL, "messages": messages, "max_tokens": 180, "temperature": 0})
            response.raise_for_status()
            content = response.json()["choices"][0]["message"].get("content")
            answer = content.strip() if isinstance(content, str) else ""
            if not answer:
                return None, int((time.monotonic() - started) * 1000), "Nicrron returned no text; using verified sample summary"
            return answer, int((time.monotonic() - started) * 1000), "Nicrron call completed"
    except (httpx.HTTPError, KeyError, IndexError, TypeError, ValueError):
        return None, int((time.monotonic() - started) * 1000), "Nicrron unavailable; using verified sample summary"


def bounded_context(text: str | None) -> str | None:
    return CONTEXT.get(text.strip().upper()) if text else None


def answer_for_topic(row: dict, topic: str | None) -> str | None:
    if not topic:
        return None
    owner = {"official": "the filer", "spouse": "the filer's spouse", "dependent": "the filer's dependent", "unknown": "not specified"}[row["reported_for"]]
    answers = {
        "OWNER": f"The disclosed owner is {owner}. The filing names {row['filer']} as the filer; that does not prove who placed the order.",
        "TIMING": f"The reported transaction date is {row['transaction_date']}. The filing date is {row['filed_date']}, and it first became public on {row['first_public_at']}.",
        "AMOUNT": f"The filing gives a range of ${row['amount_min']:,} to ${row['amount_max']:,}, not an exact trade value or execution price.",
        "PRICE": f"The fictional observed price is ${row['observed_price']} versus a ${row['reference_price']} reference over {row['reference_window']}. That is a {row['dip_pct']}% change, not a forecast or recommendation.",
        "SOURCE": f"This fictional example comes from sample report {row['source_id']}, row {row['source_row']}. Open the evidence panel to read the exact excerpt.",
    }
    return answers.get(topic.strip().upper())


async def record_prism(row: dict, output: str, retrieval: str | None, latency_ms: int, session_id: str, model_text: str | None, question: str = "") -> str:
    if not prism_configured():
        return "PRISM credentials not configured"
    trace_id = f"sample-{uuid4()}"
    host = os.getenv("PRISMTRACE_HOST", "https://prism.blockconvey.com").rstrip("/")
    headers = {"X-PRISMtrace-Key": os.environ["PRISMTRACE_API_KEY"]}
    payload = {
        "project_id": os.environ["PRISMTRACE_PROJECT_ID"], "trace_id": trace_id,
        "model": MODEL if model_text else "deterministic-fallback",
        "input_messages": [{"role": "user", "content": f"Sample row {row['id']}: {question.strip() or 'Explain this filing simply'}"}],
        "output_message": output, "latency_ms": latency_ms, "session_id": session_id,
        "agent_id": AGENT_ID, "agent_name": "Sample disclosure explainer",
        "metadata": {"sample_only": True, "row_id": row["id"], "source_sha256": row["source_sha256"]},
    }
    try:
        async with httpx.AsyncClient(timeout=12) as client:
            response = await client.post(f"{host}/api/traces", json=payload, headers=headers)
            response.raise_for_status()
            spans = []
            now = datetime.now(timezone.utc)
            if retrieval:
                spans.append({"name": "kb_search", "span_type": "retrieval", "start_time": now.isoformat(),
                              "end_time": now.isoformat(), "input_text": f"sample row {row['id']}",
                              "output_text": retrieval[:6000], "status": "ok"})
            if model_text:
                spans.append({"name": "nicrron_caveat_selection", "span_type": "llm",
                              "start_time": (now - timedelta(milliseconds=latency_ms)).isoformat(),
                              "end_time": now.isoformat(), "duration_ms": latency_ms,
                              "input_text": row["raw_excerpt"] + ("\n" + retrieval[:3000] if retrieval else ""),
                              "output_text": model_text, "model": MODEL, "status": "ok"})
            if spans:
                span = {"trace_id": trace_id, "project_id": os.environ["PRISMTRACE_PROJECT_ID"], "session_id": session_id,
                        "spans": spans}
                span_response = await client.post(f"{host}/api/spans/ingest", json=span, headers=headers)
                span_response.raise_for_status()
            return f"PRISM trace received: {trace_id}"
    except httpx.HTTPError:
        return "PRISM trace not confirmed; check project, scopes, and host"
