# TrumpTradesBuytheDip

An evidence-first, plain-language watchlist for public financial disclosures. **Hackathon prototype: sample data only. No real trades or buy recommendations.**

This repository is licensed under AGPL-3.0. The project is in the Money Intelligence track of Money Talks 2.

Start with the [PRD](docs/prd.md) and [90-minute implementation plan](docs/technical-implementation-plan.md). The design keeps the disclosure source, publication delay, disclosed owner, and sample price calculation visible together. It does not claim that all trades are disclosed or that a price dip predicts returns.

## Local setup

Install with `python -m pip install -r requirements.txt`, then run `uvicorn app.main:app --reload` and open `http://127.0.0.1:8000`. The sample app works without keys and labels unavailable integrations on its explanation card. For local checks, install `requirements-dev.txt` and run `python -m pytest -q`.

Copy `.env.example` to `.env` and fill the two service credentials from the [key instructions](docs/technical-implementation-plan.md#keys-and-apis). Keep `.env` local. Load it into your shell before starting the server: `set -a; . ./.env; set +a`. The hackathon demo uses fictional fixtures. Live primary-source ingestion and price feeds are future work, subject to access and use-rights checks.

For the PRISM KB proof, upload [`sample_data/sample_filing.md`](sample_data/sample_filing.md) to the PRISM project and assign it to agent `trumptrades-sample-explainer`. Then click **Explain simply with AI** and confirm a trace with a retrieval step in PRISM. Root Cause and Evaluators Hub are dashboard actions described in the implementation plan; they are not automated by this prototype.

For a repeatable failure/fix demonstration, run `python -m scripts.replay_proofs --version v1`, inspect the six synthetic failures in PRISM, then run `python -m scripts.replay_proofs --version v2`. The v1 replay intentionally reproduces an owner/date normalization bug and is labeled as such in code and trace metadata. It makes six Nicrron calls per version, so run it only when the sample document is assigned and the account is ready. Trigger Root Cause and the custom evaluator in the PRISM dashboard as described in the plan.
