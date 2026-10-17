# TrumpTradesBuytheDip

An evidence-first, plain-language watchlist for public financial disclosures. **Hackathon prototype: sample data only. No real trades or buy recommendations.**

This repository is licensed under AGPL-3.0. The project is in the Money Intelligence track of Money Talks 2.

Start with the [PRD](docs/prd.md) and [90-minute implementation plan](docs/technical-implementation-plan.md). The design keeps the disclosure source, publication delay, disclosed owner, and sample price calculation visible together. It does not claim that all trades are disclosed or that a price dip predicts returns.

## Local setup

Install with `python -m pip install -r requirements.txt`, then run `uvicorn app.main:app --reload` and open `http://127.0.0.1:8000`. The sample app works without keys and labels unavailable integrations on its explanation card. For local checks, install `requirements-dev.txt` and run `python -m pytest -q`.

Copy `.env.example` to `.env` and fill the two service credentials from the [key instructions](docs/technical-implementation-plan.md#keys-and-apis). Keep `.env` local. Load it into your shell before starting the server: `set -a; . ./.env; set +a`. The hackathon demo uses fictional fixtures. Live primary-source ingestion and price feeds are future work, subject to access and use-rights checks.

For the PRISM KB proof, upload [`sample_data/sample_filing.md`](sample_data/sample_filing.md) to the PRISM project and assign it to agent `trumptrades-sample-explainer`. Then click **Explain simply with AI** and confirm a trace with a retrieval step in PRISM. Root Cause and Evaluators Hub are dashboard actions described in the implementation plan; they are not automated by this prototype.

For a repeatable failure/fix demonstration, run `python -m scripts.replay_proofs --version v1`, inspect the six synthetic failures in PRISM, then run `python -m scripts.replay_proofs --version v2`. The v1 replay intentionally reproduces an owner/date normalization bug and is labeled as such in code and trace metadata. It makes six Nicrron calls per version, so run it only when the sample document is assigned and the account is ready. Trigger Root Cause and the custom evaluator in the PRISM dashboard as described in the plan.

If PRISM KB is still empty, `--source local` uses the committed fictional filing row to prepare Root Cause traces. Those traces are labeled `source_mode=local` and **do not** satisfy the KB proof. Rerun the KB path after upload.

The repository also has a small Dockerfile for a public demo host. The web explanation route has a 30-call in-process Nicrron cap per server process; the replay script has its own 12-call cost. Use a provider account budget and disable automatic wallet refill if you do not want it. `GET /healthz` returns a sample-only readiness response.

## Voice and performance

Choose a sample card and type a question or select **Speak a question**. Nicrron selects a supported topic; the server constructs an answer from the verified sample row. The browser reads that answer aloud, and **Hear answer** repeats it. Speech input depends on browser support and microphone permission; text works without either. Browser speech recognition may use a remote service. Questions are sent to Nicrron and recorded with the answer in PRISM. The model does not generate audio or unverified transaction facts.

The price card currently measures one fictional price change against a stated reference. It does not calculate the official's profit. A later real-data performance view should show a price or total-return series from both the reported transaction date and the first public date, with benchmark and observation time. Public filings generally do not provide the exact execution price, share count, or later exit, so label these as hypothetical asset returns, never a person's realized trade performance.

To inspect what PRISM recorded from this editor, load the private environment variables into your shell and run `python3 -m scripts.prism_diagnose --hours 24`. The script reads connection state, Evaluators Hub access, Root Cause coverage, and up to 500 recent traces. It does not modify PRISM or print keys. The API key can read traces and write KB documents/traces, but this account cannot create custom evaluators. PRISM's trace-analysis provider error also needs service-side repair.

## Public demo deployment

If you use Render, create a Blueprint from this public repository in the [Render dashboard](https://dashboard.render.com/) and select the included `render.yaml`. Its free web service uses `/healthz` and prompts for the three keys without putting them in Git. [Render's Blueprint docs](https://render.com/docs/blueprint-spec) describe `sync: false` secret fields. The deployed URL will have an `onrender.com` address; verify `/healthz`, the three cards, and the explanation action there. Upload the sample filing to PRISM KB before relying on the retrieval proof. If you use another host, the Dockerfile runs the same app with a supplied `PORT`.
