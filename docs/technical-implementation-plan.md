# Technical implementation plan — 90-minute solo build

**Status:** plan, not proof of completion. **Target:** a live, sample-only Money Intelligence demo and three hosted PRISM proofs.

## Keys and APIs

| Needed now | How to obtain | Where to use |
| --- | --- | --- |
| `NICRRON_API_KEY` | Sign in to the [Nicrron dashboard](https://nicrron.ai/), create an API key, and confirm the account has model access or configured provider funding. [Quickstart](https://nicrron.ai/docs/quickstart) documents `https://api.nicrron.ai/v1`. | Server `.env` only. Never in browser JavaScript or Git. |
| `PRISMTRACE_PROJECT_ID` | Sign up/sign in at [PRISM](https://prism.blockconvey.com/); find it under Settings → Project. | Server `.env`. |
| `PRISMTRACE_API_KEY` | In the same PRISM project, create an API key with ingest and the scopes needed for KB search; save it when shown. [PRISM docs](https://blockconvey.com/docs) explain keys and traces. | Server `.env`; send as `X-PRISMtrace-Key`. |
| PRISM Evaluators Hub access | Check the account plan or event entitlement before the demo. Current [PRISM docs](https://blockconvey.com/docs) list Evaluators Hub on Builder. | Dashboard to create and run the custom evaluator. |

No government API key or live market-data key is needed for the hackathon sample. A later production build needs an authorized data-access and use-rights path for [House](https://disclosures-clerk.house.gov/FinancialDisclosure/ViewSearch), [Senate](https://efdsearch.senate.gov/search/home/), and [OGE](https://www.oge.gov/Web/OGE.nsf/publicresources_disclosure-quickstart?OpenForm=&Seq=1) records, plus a licensed market-price provider. Do not assume these disclosure sites expose a sanctioned unified API. House's search page states restrictions on commercial use; resolve those before a paid real-data product.

Create `.env` from `.env.example` within this repository. The local workspace's `untracked_docs/keys_and_apis/keys_and_apis.env` can hold the values, but it must never be copied into this public repo. If you put keys there, copy just the needed values into this repo's ignored `.env` or load them from the shell. Do not paste keys into chat or screenshots. `gh auth status` is already authenticated as `ithllc`; no new GitHub token is needed to create the repo.

## Minute-by-minute path

| Time | Work | Exit evidence |
| --- | --- | --- |
| 0–10 | Create public AGPL repo, sample fixture schema, `.env.example`, and local app skeleton. | Repo public, license visible, no secrets tracked. |
| 10–30 | Build three fictional filing cases and sample prices; implement validation and deterministic watch math. | Cards show source row, dates, owner, amount range, formula, and demo banner. |
| 30–45 | Add plain-language UI, evidence drawer, and Nicrron explanation endpoint with post-check and fallback. | One live model call through Nicrron and one rejected unsupported claim. |
| 45–60 | Upload the sample `.md` filing to PRISM KB, assign it to the agent, call `kb_search`, send a trace with stable session and retrieval context. | Hosted PRISM run visibly shows retrieval and source use. |
| 60–75 | Run 5–10 deliberately failing sample questions in v1 (e.g. ambiguous owner treated as filer, filing date mistaken for trade date); select and analyse them; run Root Cause. Fix the identified rule and replay the same inputs as v2. | PRISM cluster of 3+ failed runs; recorded cause and before/after examples. |
| 75–85 | In Evaluators Hub create “Every transaction claim and number must be supported by retrieved sample filing context; distinguish filer from reported owner and trade date from filing date.” Score v1 and v2 on the same inputs. | Two evaluator result views with input set and scores. |
| 85–90 | Rehearse two-minute demo, capture proof media, fill Devpost links. | Live URL, prototype URL, repo URL, three proof screenshots/video. |

If Builder access is unavailable, request the event entitlement immediately. A local substitute cannot honestly satisfy the required hosted evaluator proof. Keep building the rest of the app while access is resolved.

## Implementation tasks

1. Define `Transaction` and `PriceObservation` schema; validate source ID, page/row, raw excerpt, amount range, dates, `reported_for`, and sample flag. Fixture IDs are allowlisted; API calls never fetch arbitrary URLs.
2. Create three fictional examples: a filer-owned purchase, a spouse-owned sale, and an ambiguous owner. Set transaction date before filing date and a separately labeled observation date. Generate a sample Markdown filing document with row markers. Hash its bytes to bind card evidence to the document.
3. Implement `dip_pct` with `Decimal`; reference window and as-of date are shown. Missing/zero reference yields “cannot calculate.” A configurable threshold yields a watch event only.
4. Implement a Nicrron call that selects one of four beginner caveats from the provided row and retrieval. Map the selected token to a fixed plain-language sentence; reject any other output. Render transaction facts in deterministic code and record the result for PRISM.
5. Implement PRISM KB search and trace submission per [official docs](https://blockconvey.com/docs). Include `project_id`, `model`, `input_messages`, `output_message`, `latency_ms`, `session_id`, and `agent_id`; attach retrieval/tool context via the supported SDK or span path so `{context}` is populated for the evaluator. Verify the run appears in the PRISM dashboard.
6. Capture repeatable v1/v2 fixture questions and their expected answers. Use the same dataset for both; preserve trace/run IDs and screenshots. Do not claim a root-cause cluster if PRISM has not produced one.

The repository includes `scripts/replay_proofs.py` for six explicitly synthetic failure/fix cases. It calls Nicrron for each case, queries PRISM KB, and sends traces plus retrieval and normalization spans. Run `python -m scripts.replay_proofs --version v1` before Root Cause, then `python -m scripts.replay_proofs --version v2` after inspecting the failing examples. The v1 bug is deliberately reproduced and disclosed in source and trace metadata. Check the actual PRISM evaluator scores; do not state a score improvement until the dashboard confirms it.

## Checks before demo

- Fixture labels survive every route and screenshot; no fabricated real-person trades.
- A spouse-owned row cannot be worded as the official's personal purchase.
- An amount range remains a range; unknown timestamp stays unknown.
- Formula output matches code, and a price fall never becomes a recommendation.
- Nicrron and PRISM credentials are absent from Git status, HTTP responses, logs, and screenshots.
- PRISM KB, Root Cause, and v1/v2 Evaluator proofs are visible in the hosted project, with enough credits/entitlement for the required actions.

## Demo script

“This is fictional sample data. Here is what the filing says, who the asset belongs to, and how long after the trade the filing became public. The evidence panel shows the exact source row. The price card calculates a watch event, not a buy command. Here is the Nicrron explanation grounded in that row. In PRISM, the KB retrieval is visible. Our first version confused ownership/date in several sample cases; Root Cause grouped that failure, and this evaluator scores the same questions before and after the fix.”
