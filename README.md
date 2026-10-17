# TrumpTradesBuytheDip

An evidence-first, plain-language watchlist for public financial disclosures. **Hackathon prototype: sample data only. No real trades or buy recommendations.**

This repository is licensed under AGPL-3.0. The project is in the Money Intelligence track of Money Talks 2.

Start with the [PRD](docs/prd.md) and [90-minute implementation plan](docs/technical-implementation-plan.md). The design keeps the disclosure source, publication delay, disclosed owner, and sample price calculation visible together. It does not claim that all trades are disclosed or that a price dip predicts returns.

## Local setup

Copy `.env.example` to `.env` and fill the two service credentials from the [key instructions](docs/technical-implementation-plan.md#keys-and-apis). Keep `.env` local. The hackathon demo uses fictional fixtures. Live primary-source ingestion and price feeds are future work, subject to access and use-rights checks.
