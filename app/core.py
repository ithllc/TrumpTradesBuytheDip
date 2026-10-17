"""Deterministic facts and sample fixture validation."""

from __future__ import annotations

import hashlib
import json
from datetime import date
from decimal import Decimal, ROUND_HALF_UP
from pathlib import Path

BASE = Path(__file__).resolve().parent.parent
SOURCE = BASE / "sample_data" / "sample_filing.md"
DATA = BASE / "sample_data" / "transactions.json"


def dip_percent(reference: str, observed: str) -> Decimal | None:
    ref, price = Decimal(reference), Decimal(observed)
    if ref <= 0 or price < 0:
        return None
    return ((ref - price) / ref * Decimal("100")).quantize(Decimal("0.01"), rounding=ROUND_HALF_UP)


def validate_row(row: dict, document: str) -> dict:
    required = ("id", "filer", "role", "reported_for", "asset", "kind", "transaction_date", "amount_min", "amount_max", "filed_date", "first_public_at", "observed_at", "source_id", "source_row", "raw_excerpt")
    if any(k not in row for k in required):
        raise ValueError("sample row is incomplete")
    if row["reported_for"] not in {"official", "spouse", "dependent", "unknown"}:
        raise ValueError("invalid disclosed owner")
    if row["kind"] not in {"Purchase", "Sale", "Exchange"}:
        raise ValueError("invalid transaction type")
    if row["raw_excerpt"] not in document or row["source_row"] != row["id"]:
        raise ValueError("row is not grounded in sample filing")
    if not (0 <= row["amount_min"] <= row["amount_max"]):
        raise ValueError("invalid amount range")
    dates = [date.fromisoformat(row[k]) for k in ("transaction_date", "filed_date", "first_public_at", "observed_at")]
    if dates != sorted(dates):
        raise ValueError("impossible disclosure chronology")
    output = dict(row)
    output["source_sha256"] = hashlib.sha256(document.encode()).hexdigest()
    output["source_type"] = "fictional sample filing"
    output["disclosure_lag_days"] = (dates[2] - dates[0]).days
    pct = dip_percent(row["reference_price"], row["observed_price"])
    output["dip_pct"] = str(pct) if pct is not None else None
    output["watch_event"] = pct is not None and pct >= Decimal(row["threshold_pct"])
    return output


def load_rows() -> list[dict]:
    document = SOURCE.read_text(encoding="utf-8")
    rows = json.loads(DATA.read_text(encoding="utf-8"))
    return [validate_row(row, document) for row in rows]


def find_row(row_id: str) -> dict | None:
    return next((row for row in load_rows() if row["id"] == row_id), None)


def plain_summary(row: dict) -> str:
    owner = {"official": "the filer", "spouse": "the filer's spouse", "dependent": "the filer's dependent", "unknown": "an unspecified owner"}[row["reported_for"]]
    return (f"The sample filing reports a {row['kind'].lower()} of {row['asset']} for {owner}. "
            f"It gives an amount range of ${row['amount_min']:,}–${row['amount_max']:,}, "
            f"a transaction date of {row['transaction_date']}, and a first public date of {row['first_public_at']}. "
            "It does not tell us whether the price will rise or fall.")
