"""Run a transparent synthetic v1/v2 regression through Nicrron and PRISM.

v1 deliberately reproduces a source-normalization bug: it substitutes the filer
for the owner and the filing date for the transaction date. v2 uses the source row.
Use only after uploading sample_filing.md to PRISM KB and checking entitlement.
"""

from __future__ import annotations

import argparse
import asyncio
import os
import time
from datetime import datetime, timezone
from uuid import uuid4

import httpx

from app.core import find_row, plain_summary
from app.providers import AGENT_ID, MODEL, bounded_context, kb_search

CASES = [
    ("A1", "Who made the reported purchase, and when?"),
    ("A1", "Is the filing date the same as the transaction date?"),
    ("A2", "Did the senator personally buy this asset?"),
    ("A2", "Who owned the reported transaction?"),
    ("A3", "Can we say the House member personally purchased this?"),
    ("A3", "What date was the transaction, rather than the filing?"),
]


def normalized_facts(row: dict, version: str) -> str:
    if version == "v1":
        return (f"The filing says {row['filer']} personally purchased {row['asset']} "
                f"on {row['filed_date']}.")
    return plain_summary(row)


async def one_case(client: httpx.AsyncClient, version: str, row_id: str, question: str) -> None:
    row = find_row(row_id)
    if row is None:
        raise RuntimeError(f"missing sample row {row_id}")
    retrieval, status = await kb_search(f"sample filing row {row_id} {row['asset']} owner transaction date")
    if not retrieval or row_id not in retrieval:
        raise RuntimeError(f"PRISM KB result for row {row_id} is missing: {status}. Upload sample_filing.md and assign agent {AGENT_ID}.")
    facts = normalized_facts(row, version)
    started = time.monotonic()
    messages = [
        {"role": "system", "content": "This is fictional sample data. Choose the most useful caveat: OWNER, TIMING, AMOUNT, or PRICE. Return exactly one word."},
        {"role": "user", "content": f"Question: {question}\nNormalized facts: {facts}\nRetrieved filing: {retrieval[:3000]}"},
    ]
    model_response = await client.post("https://api.nicrron.ai/v1/chat/completions",
                                       headers={"Authorization": f"Bearer {os.environ['NICRRON_API_KEY']}"},
                                       json={"model": MODEL, "messages": messages, "max_tokens": 100, "temperature": 0})
    model_response.raise_for_status()
    model_text = model_response.json()["choices"][0]["message"]["content"].strip()
    context = bounded_context(model_text)
    output = facts + (" AI context: " + context if context else "")
    trace_id = f"regression-{version}-{uuid4()}"
    session_id = f"regression-{version}-{row_id}-{uuid4()}"
    host = os.getenv("PRISMTRACE_HOST", "https://prism.blockconvey.com").rstrip("/")
    headers = {"X-PRISMtrace-Key": os.environ["PRISMTRACE_API_KEY"]}
    payload = {
        "project_id": os.environ["PRISMTRACE_PROJECT_ID"], "trace_id": trace_id,
        "model": MODEL, "input_messages": [{"role": "user", "content": question}],
        "output_message": output, "latency_ms": int((time.monotonic() - started) * 1000),
        "session_id": session_id, "agent_id": AGENT_ID, "agent_name": "Sample disclosure explainer",
        "metadata": {"sample_only": True, "regression_version": version, "row_id": row_id,
                     "bug": "owner/date normalization" if version == "v1" else "fixed"},
    }
    response = await client.post(f"{host}/api/traces", json=payload, headers=headers)
    response.raise_for_status()
    now = datetime.now(timezone.utc).isoformat()
    span = {"project_id": os.environ["PRISMTRACE_PROJECT_ID"], "trace_id": trace_id,
            "session_id": session_id, "spans": [
                {"name": "kb_search", "span_type": "retrieval", "start_time": now, "end_time": now,
                 "input_text": question, "output_text": retrieval[:6000], "status": "ok"},
                {"name": "normalized_facts", "span_type": "tool", "start_time": now, "end_time": now,
                 "input_text": f"sample row {row_id}", "output_text": facts, "status": "ok"},
            ]}
    span_response = await client.post(f"{host}/api/spans/ingest", json=span, headers=headers)
    span_response.raise_for_status()
    print(f"{version} {row_id}: {trace_id}")


async def run(version: str) -> None:
    missing = [name for name in ("NICRRON_API_KEY", "PRISMTRACE_PROJECT_ID", "PRISMTRACE_API_KEY") if not os.getenv(name)]
    if missing:
        raise SystemExit("Missing environment variables: " + ", ".join(missing))
    async with httpx.AsyncClient(timeout=30) as client:
        for row_id, question in CASES:
            await one_case(client, version, row_id, question)


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--version", choices=("v1", "v2"), required=True)
    args = parser.parse_args()
    asyncio.run(run(args.version))
