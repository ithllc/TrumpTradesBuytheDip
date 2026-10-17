# PRD: TrumpTradesBuytheDip

**Status:** Hackathon scope, 2026-10-17. **Track:** Money Intelligence. **Builder:** one person.

## User and problem

A curious beginner sees headlines about public officials' investments but cannot tell what a filed transaction actually says, who owned it, when the public learned of it, or whether a falling price is merely a price change. The product makes the evidence and timing understandable in one screen.

## Core promise

“See the filing behind a reported trade, understand its delay, and follow a clearly defined price watch event.” The app never implies that a reported trade guarantees a return or that all trades are captured.

## Prototype journey

1. Open the app; a persistent banner says **Fictional sample data — educational demo**.
2. Choose a fictional sample filing from three cards (purchase, sale, ambiguous owner). Each card displays filer, disclosed owner, asset, transaction type, amount *range*, transaction date, filing date, and report availability/observation if known.
3. Select **Show evidence**. The panel displays the sample filing ID, page/row, exact sample excerpt, and which displayed fields were read from it. “Verified” in the prototype means fixture-to-display agreement, not verification of a real government filing.
4. Select **Explain simply**. The backend asks Nicrron to explain only the supplied row and chronology; the answer includes a link to its evidence panel. Unsupported claims are rejected.
5. Select **Watch price**. The app shows a sample observed price, a sample reference price, the formula, the percentage change, and the as-of time. If a threshold is crossed, it says “watch event,” not “buy.”
6. Open **What this does not tell us**: ownership/execution ambiguity, delayed disclosures, amount ranges, price movement versus future returns, and missing data.

## Requirements and acceptance

| ID | Requirement | Acceptance check |
| --- | --- | --- |
| P1 | Beginner-friendly cards | Each term (“filing”, “amount range”, “dip”) has a one-line explanation; no unexplained ticker-only UI. |
| P2 | Evidence custody | Every displayed reported transaction maps to one sample row; source ID, row/page, raw excerpt, and file hash are visible. Missing source hides the transaction from the verified list. |
| P3 | Time truth | Transaction, filing, public, observed, and price timestamps stay separate; unknown stays “unknown”; stale/late is explicit. |
| P4 | Owner truth | Filer and disclosed owner are separate; spouse/dependent/unknown never become a claim that the filer personally traded. |
| P5 | Deterministic watch event | Code computes the sample percentage using a declared reference window; a missing or zero reference prevents calculation. |
| P6 | Bounded explanation | Model output has citations to provided row IDs; unsupported material claims are rejected, with a plain fallback. |
| P7 | Honest scope | Demo banner appears on all views; no real-person fabricated trades, broker integration, recommendation, or performance claim. |
| P8 | Hackathon integration | At least one real Nicrron request and one PRISM KB-backed run are visible; Root Cause and v1/v2 Evaluator proofs are captured from the hosted PRISM project. |

## Data rules

Canonical fields: `filer_id`, `filer_role`, `reported_for`, `asset_name`, `ticker?`, `transaction_kind`, `transaction_date`, `amount_min?`, `amount_max?`, `filed_date?`, `first_public_at?`, `observed_at`, `source_url`, `source_id`, `source_page`, `source_row`, `raw_excerpt`, `source_sha256`, `status`. Store a correction or amendment as a new version linked to the old one; do not silently overwrite. A name or ticker match across filers is correlation, not confirmation of another person's intent.

## Non-goals today

Real data ingestion; automated scraping; full coverage of the President, all staff, or Congress; real prices; mobile app; notifications; a conviction score; personalized financial advice; trade execution; claims of market-beating performance.

## Success for the demo

- A novice can identify what was reported, by whom, for whom, and when in under 30 seconds.
- Three fixture cases yield accurate cards and evidence; the ambiguous-owner case does not say the official personally bought.
- Every numeric amount and price in an explanation matches the provided fixture or computed watch result.
- PRISM shows the three track proofs with screenshots and the same-input v1/v2 result; no proof is marked complete based solely on local code.

## Release gates after the event

Verify primary-source access and allowed use; source every real transaction; handle corrections and publication timing; license a price feed; review the legal and advice language; measure citation accuracy on a held-out set before making real-person cards public.
