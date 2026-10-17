from decimal import Decimal

import httpx
import pytest

from app.core import SOURCE, dip_percent, load_rows, plain_summary, validate_row
from app.main import app
from app.providers import bounded_context
from scripts.replay_proofs import normalized_facts


def test_sample_rows_are_grounded_and_owner_truthful():
    rows = load_rows()
    assert len(rows) == 3
    assert all(row["raw_excerpt"] in SOURCE.read_text() for row in rows)
    assert rows[0]["disclosure_lag_days"] == 40
    assert rows[1]["reported_for"] == "spouse"
    assert "filer's spouse" in plain_summary(rows[1])
    assert "unspecified owner" in plain_summary(rows[2])
    assert all(row["source_sha256"] == rows[0]["source_sha256"] for row in rows)


def test_dip_formula_and_invalid_reference():
    assert dip_percent("100.00", "91.50") == Decimal("8.50")
    assert dip_percent("0", "91.50") is None
    assert dip_percent("100", "-1") is None


def test_source_mismatch_fails_closed():
    row = dict(load_rows()[0])
    row["raw_excerpt"] = "invented replacement"
    with pytest.raises(ValueError, match="not grounded"):
        validate_row(row, SOURCE.read_text())


def test_regression_replay_exposes_and_fixes_owner_date_bug():
    row = load_rows()[1]
    old = normalized_facts(row, "v1")
    fixed = normalized_facts(row, "v2")
    assert "personally purchased" in old and row["filed_date"] in old
    assert "filer's spouse" in fixed and row["transaction_date"] in fixed
    assert "personally purchased" not in fixed


def test_model_cannot_add_unapproved_trade_claims():
    assert "historical information" in bounded_context("TIMING")
    assert bounded_context("Buy this stock now") is None


@pytest.mark.asyncio
async def test_local_api_is_sample_only(monkeypatch):
    for name in ("NICRRON_API_KEY", "PRISMTRACE_PROJECT_ID", "PRISMTRACE_API_KEY"):
        monkeypatch.delenv(name, raising=False)
    transport = httpx.ASGITransport(app=app)
    async with httpx.AsyncClient(transport=transport, base_url="http://test") as client:
        page = await client.get("/")
        assert "FICTIONAL SAMPLE DATA" in page.text
        rows = (await client.get("/api/sample/transactions")).json()
        assert rows["sample_only"] is True
        assert rows["transactions"][0]["watch_event"] is True
        answer = (await client.post("/api/sample/explain/A2", json={"session_id": "demo-test"})).json()
        assert answer["sample_only"] is True
        assert answer["used_fallback"] is True
        assert "filer's spouse" in answer["summary"]
        assert "not configured" in answer["model_status"]
        assert (await client.get("/api/sample/transactions/nope")).status_code == 404
