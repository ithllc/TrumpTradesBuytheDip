"""Read-only PRISM health summary for this project, using shell environment keys."""

from __future__ import annotations

import argparse
import os
from collections import Counter
from datetime import datetime, timedelta, timezone

import httpx


def diagnose(hours: int) -> None:
    project = os.getenv("PRISMTRACE_PROJECT_ID")
    key = os.getenv("PRISMTRACE_API_KEY")
    if not project or not key:
        raise SystemExit("Load PRISMTRACE_PROJECT_ID and PRISMTRACE_API_KEY into the shell first.")
    base = os.getenv("PRISMTRACE_HOST", "https://prism.blockconvey.com").rstrip("/")
    headers = {"X-PRISMtrace-Key": key}
    since = (datetime.now(timezone.utc) - timedelta(hours=hours)).isoformat()
    with httpx.Client(base_url=base, headers=headers, timeout=20) as client:
        doctor = client.get("/api/setup-doctor", params={"project_id": project})
        doctor.raise_for_status()
        health = doctor.json()
        access = client.get("/api/entitlements", params={"project_id": project})
        access.raise_for_status()
        entitlement = access.json()
        clusters = client.get("/api/intelligence/clusters/analyze/status", params={"project_id": project})
        clusters.raise_for_status()
        cluster = clusters.json()
        traces = []
        for page in range(1, 6):
            response = client.get("/api/traces", params={"project_id": project, "date_from": since,
                                                         "page": page, "page_size": 100})
            response.raise_for_status()
            batch = response.json().get("traces", [])
            traces.extend(batch)
            if len(batch) < 100:
                break
    reasons = Counter()
    for trace in traces:
        evaluation = trace.get("evaluation") or {}
        if evaluation.get("flag_for_review"):
            reason = evaluation.get("flag_reason") or "flagged without reason"
            if "401" in reason and "anthropic" in reason.lower():
                reason = "PRISM trace analysis: upstream Anthropic 401 authentication error"
            reasons[reason[:180]] += 1
    print(f"Window: last {hours} hours; traces inspected: {len(traces)}")
    print(f"Connection: live={health.get('live_connected')}, app={health.get('app_connected')}, blocked_step={health.get('blocked_step')}")
    print(f"Evaluators Hub: {entitlement.get('feature_access', {}).get('evaluators_hub')}")
    print(f"Root Cause: {cluster.get('state')}, coverage={(cluster.get('summary') or {}).get('coverage')}")
    for reason, count in reasons.most_common(5):
        print(f"Flagged {count}: {reason}")
    if not reasons:
        print("No flagged trace analyses found in this window. This does not prove that no errors occurred.")


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--hours", type=int, default=24)
    args = parser.parse_args()
    if not 1 <= args.hours <= 168:
        parser.error("--hours must be between 1 and 168")
    diagnose(args.hours)
