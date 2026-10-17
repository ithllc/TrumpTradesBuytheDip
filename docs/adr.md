# ADR 001: Evidence-first disclosure watchlist

**Status:** Accepted for hackathon prototype, 2026-10-17. **Owner:** solo builder.

## Context

The original idea combined President Trump, staff, and congressional trades into a “conviction” and “buy the dip” signal. Public disclosures cannot support a real-time copying strategy: a report can arrive weeks after the transaction, amount is often a range, and a report may cover a spouse or dependent. The hackathon also requires sample data only and live PRISM/Nicrron proof.

The [OGE access guide](https://www.oge.gov/Web/OGE.nsf/publicresources_disclosure-quickstart?OpenForm=&Seq=1) lists President/Vice President 278e and 278-T reports, while other executive officials' reports may require Form 201. The [House Clerk search](https://disclosures-clerk.house.gov/FinancialDisclosure/ViewSearch) and [Senate public disclosure portal](https://www.senate.gov/legislative/Public_Disclosure/financial-disclosure.htm) are separate systems. The [House notice](https://disclosures-clerk.house.gov/FinancialDisclosure/ViewSearch) restricts commercial uses of disclosure information; any real-data commercial launch needs a rights review.

## Decision

1. Build a **sample-only educational web prototype** with one fixture format for reported transactions, one for prices, and a source evidence panel. Fictional officials and fictional filings are labeled on every screen.
2. Parse, date, type, and calculate deterministically. A Nicrron model may explain a *provided* row in simple words, but it cannot assert a transaction without a source row. Unsupported answers fail closed to a plain deterministic summary.
3. Require an official source URL, report ID, row/page, raw excerpt, and source hash for a future real-data transaction to earn `verified_source` status. An aggregator can aid discovery, never be final evidence.
4. Represent `reported_for` separately from `filer`, with `official | spouse | dependent | unknown`. Use “reported transaction,” never “the official bought” unless the filing itself supports that wording.
5. Represent the chronology separately: transaction, filing, public availability, app observation, and price timestamp. Mark unknown dates as unknown. A `dip_pct = (reference_price - observed_price) / reference_price * 100` watch event needs a named reference window and sample data provenance. It is not an instruction to buy.
6. Omit “conviction” scoring, rank ordering of people, execution, brokerage, personalized advice, and push notifications from this prototype. A price watch label is allowed; an actionable recommendation is not.
7. Use Nicrron for every model call and PRISM KB, root cause, and evaluator for the Money Intelligence demo. No PRISM proof is claimed until the corresponding hosted run and screenshot exist.

## Consequences

The interface can demonstrate trust and usability within 90 minutes without fabricating accusations or implying a trading edge. It will not show real President or congressional transaction cards at the event. Later ingestion must resolve source access, permitted use, corrections, entity matching, price licensing, freshness, and advice/compliance review before a real-data release.

## Revisit when

We have written source-use rights, at least one end-to-end verified public filing, reliable availability timestamps, licensed price data, and a review of the app's language and alert behavior.
