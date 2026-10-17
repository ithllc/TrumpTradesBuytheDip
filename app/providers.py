"""Server-side Nicrron and PRISM calls. All results are explicitly labeled."""

from __future__ import annotations

import asyncio
import os
import time
from datetime import datetime, timezone
from uuid import uuid4

import httpx

AGENT_ID = "trumptrades-sample-explainer"
MODEL = "nicrron/auto"
_model_call_lock = asyncio.Lock()
_model_calls = 0
CONTEXT = {
    "OWNER": "The filer and the person whose asset was reported may differ. Check the disclosed owner field.",
    "TIMING": "A disclosure can appear weeks after a transaction, so it is historical information.",
    "AMOUNT": "A disclosed amount is a range, not the exact amount spent or received.",
    "PRICE": "A price dip is a change from a reference; it does not predict a rebound.",
}


def prism_configured() -> bool:
    return bool(os.getenv("PRISMTRACE_PROJECT_ID") and os.getenv("PRISMTRACE_API_KEY"))


async def kb_search(query: str) -> tuple[str | None, str]:
    if not prism_configured():
        return None, "PRISM credentials not configured"
    payload = {"project_id": os.environ["PRISMTRACE_PROJECT_ID"], "agent_id": AGENT_ID, "query": query, "limit": 3}
    try:
        async with httpx.AsyncClient(timeout=12) as client:
            response = await client.post("https://api.prism.blockconvey.com/api/knowledge-base/search", json=payload,
                                         headers={"X-PRISMtrace-Key": os.environ["PRISMTRACE_API_KEY"]})
            response.raise_for_status()
            return response.text[:6000], "PRISM KB search completed"
    except httpx.HTTPError:
        return None, "PRISM KB unavailable; check document assignment and key"


async def nicrron_explain(row: dict, retrieval: str | None) -> tuple[str | None, int, str]:
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
        {"role": "system", "content": ("This is fictional sample data. Choose the one most useful beginner caveat "
                                        "from OWNER, TIMING, AMOUNT, or PRICE. Return exactly one of those words and nothing else. "
                                        "Use the supplied sample row and retrieval only. No investment recommendation.")},
        {"role": "user", "content": f"Sample row: {row['raw_excerpt']}\nRetrieved context: {source}\nWhich caveat matters most?"},
    ]
    started = time.monotonic()
    try:
        async with httpx.AsyncClient(timeout=25) as client:
            response = await client.post("https://api.nicrron.ai/v1/chat/completions",
                                         headers={"Authorization": f"Bearer {key}"},
                                         json={"model": MODEL, "messages": messages, "max_tokens": 90, "temperature": 0})
            response.raise_for_status()
            answer = response.json()["choices"][0]["message"]["content"].strip()
            return answer, int((time.monotonic() - started) * 1000), "Nicrron call completed"
    except (httpx.HTTPError, KeyError, IndexError, TypeError, ValueError):
        return None, int((time.monotonic() - started) * 1000), "Nicrron unavailable; using verified sample summary"


def bounded_context(text: str | None) -> str | None:
    return CONTEXT.get(text.strip().upper()) if text else None


async def record_prism(row: dict, output: str, retrieval: str | None, latency_ms: int, session_id: str, model_called: bool) -> str:
    if not prism_configured():
        return "PRISM credentials not configured"
    trace_id = f"sample-{uuid4()}"
    host = os.getenv("PRISMTRACE_HOST", "https://prism.blockconvey.com").rstrip("/")
    headers = {"X-PRISMtrace-Key": os.environ["PRISMTRACE_API_KEY"]}
    payload = {
        "project_id": os.environ["PRISMTRACE_PROJECT_ID"], "trace_id": trace_id,
        "model": MODEL if model_called else "deterministic-fallback",
        "input_messages": [{"role": "user", "content": f"Explain fictional sample row {row['id']}: {row['raw_excerpt']}"}],
        "output_message": output, "latency_ms": latency_ms, "session_id": session_id,
        "agent_id": AGENT_ID, "agent_name": "Sample disclosure explainer",
        "metadata": {"sample_only": True, "row_id": row["id"], "source_sha256": row["source_sha256"]},
    }
    try:
        async with httpx.AsyncClient(timeout=12) as client:
            response = await client.post(f"{host}/api/traces", json=payload, headers=headers)
            response.raise_for_status()
            if retrieval:
                now = datetime.now(timezone.utc).isoformat()
                span = {"trace_id": trace_id, "project_id": os.environ["PRISMTRACE_PROJECT_ID"], "session_id": session_id,
                        "spans": [{"name": "kb_search", "span_type": "retrieval", "start_time": now,
                                   "end_time": now, "input_text": f"sample row {row['id']}",
                                   "output_text": retrieval[:6000], "status": "ok"}]}
                span_response = await client.post(f"{host}/api/spans/ingest", json=span, headers=headers)
                span_response.raise_for_status()
            return f"PRISM trace received: {trace_id}"
    except httpx.HTTPError:
        return "PRISM trace not confirmed; check project, scopes, and host"
