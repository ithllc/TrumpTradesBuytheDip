"""Sample-only hackathon web app."""

from __future__ import annotations

from pathlib import Path
from uuid import uuid4

from fastapi import FastAPI, HTTPException
from fastapi.responses import HTMLResponse
from pydantic import BaseModel, Field

from app.core import find_row, load_rows, plain_summary
from app.providers import bounded_context, kb_search, nicrron_explain, record_prism

app = FastAPI(title="TrumpTradesBuytheDip — fictional sample demo", docs_url=None, redoc_url=None)
INDEX = Path(__file__).parent / "index.html"
SAMPLE_FILING = Path(__file__).parent.parent / "sample_data" / "sample_filing.md"


class ExplainRequest(BaseModel):
    session_id: str = Field(default_factory=lambda: str(uuid4()), max_length=100, pattern=r"^[A-Za-z0-9_-]+$")


@app.get("/", response_class=HTMLResponse)
def home() -> str:
    return INDEX.read_text(encoding="utf-8")


@app.get("/healthz")
def health() -> dict:
    return {"ok": True, "sample_only": True}


@app.get("/sample-filing", response_class=HTMLResponse)
def sample_filing() -> str:
    from html import escape
    return ("<!doctype html><html><head><meta charset='utf-8'><title>Fictional sample filing</title>"
            "<style>body{font:18px/1.6 system-ui;max-width:800px;margin:3rem auto;padding:1rem}"
            "pre{white-space:pre-wrap}</style></head><body><p><a href='/'>← Back to demo</a></p>"
            "<strong>Fictional sample data — not a real government filing</strong><pre>"
            + escape(SAMPLE_FILING.read_text(encoding="utf-8")) + "</pre></body></html>")


@app.get("/api/sample/transactions")
def transactions() -> dict:
    return {"sample_only": True, "transactions": load_rows()}


@app.get("/api/sample/transactions/{row_id}")
def transaction(row_id: str) -> dict:
    row = find_row(row_id)
    if row is None:
        raise HTTPException(404, "Sample row not found")
    return {"sample_only": True, "transaction": row}


@app.post("/api/sample/explain/{row_id}")
async def explain(row_id: str, request: ExplainRequest) -> dict:
    row = find_row(row_id)
    if row is None:
        raise HTTPException(404, "Sample row not found")
    retrieval, kb_status = await kb_search(f"SAMPLE-2026-01 row {row_id} {row['asset']} owner and transaction", row_id)
    model_text, latency_ms, model_status = await nicrron_explain(row, retrieval)
    context = bounded_context(model_text)
    factual = plain_summary(row)
    output = factual + (f" AI context: {context}" if context else "")
    prism_status = await record_prism(row, output, retrieval, latency_ms, request.session_id, model_text)
    return {"sample_only": True, "summary": factual, "ai_context": context,
            "source_row": row_id, "kb_status": kb_status, "model_status": model_status,
            "prism_status": prism_status, "used_fallback": context is None}
