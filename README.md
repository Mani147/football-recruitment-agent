# Touchline · Football recruitment workspace

A transparent recruitment demo: define a role, review the exact constraints, and inspect a shortlist with explainable scores, estimated costs and stored-record checks.

**This is a portfolio sandbox, not a live scouting service.** The seeded 2025/26 player metrics, narratives, fees and wages are illustrative benchmarks. There are no live StatsBomb, Opta, Transfermarkt or LLM calls. Narrative retrieval uses local TF-IDF similarity. Do not use the outputs as independently verified transfer advice.

## Run locally

Requires Python 3.11 or newer.

```bash
python -m venv .venv
# Windows PowerShell: .venv\Scripts\Activate.ps1
# macOS/Linux: source .venv/bin/activate
pip install -r requirements.txt
python -m backend.app.main
```

Open http://127.0.0.1:8000. No API key or separate seed command is required. Startup seeds an empty database and rebuilds the process-local narrative index from stored players on every launch. Existing nonempty databases are preserved. Set `DATABASE_PATH` to use a different SQLite file; database files are ignored by Git.

## The guided workflow

1. **Define the brief.** Name a supported role: GK, fullback, LB/RB, CB, DM, CM, AM, winger, LW/RW, or ST/CF. Describe the style you need. Set a fee ceiling in EUR millions, weekly gross wage cap, minimum minutes, and an optional age or preferred-foot override.
2. **Review the interpretation.** Check the effective position, club, age range, budget, wages, foot and minutes before running a search. Editing the form invalidates the prior review. Only displayed constraints are enforced; arbitrary nationality, league, release-clause and exact metric requirements in prose are not implemented.
3. **Inspect the shortlist.** Every candidate must pass the same eligibility gate, including secondary positions and sided roles. Players already at the recruiting club are excluded. There is no automatic budget, age, wage or minutes relaxation. Empty results explain how to explicitly revise the brief.
4. **Read the evidence.** Select a player to inspect score components, sample reliability, estimated annual book cost, tactical percentiles against targets, raw record checks and caveats. Download the dossier as JSON.

Text parsing is deterministic and intentionally limited. `U24` and `under 24 years` mean age 23 or younger. `age <=24` is inclusive. The age form field overrides text. Foot selection overrides text; “No preference” removes a text foot requirement. The stricter of a monetary amount in the text and the form fee ceiling is used. Text-only wages are not enforced: use the wage cap field. Monetary inputs must be EUR; dollar and pound prompts return a validation message. A club named in the role text can override the club field, and is shown during review.

## What the numbers mean

| Output | Meaning | Limits |
| --- | --- | --- |
| Fit / 100 | 40% tactical target match + 25% role-weighted statistical quality + 20% financial headroom + 15% age potential | Comparison score, not success probability. Fixed heuristic weights. |
| Tactical breakdown | League-adjusted percentile against each target | League multipliers are heuristics; percentiles are illustrative. |
| Reliability / 100 | Stored sample exposure, consistency, completeness and league tier | Does not independently establish data accuracy. |
| Annual book cost | Estimated fee / 5 + weekly gross wage × 52 | Excludes bonuses, agent fees, taxes and signing costs. Amortization helper caps the term at five years. |
| Stored-record audit | Supplied raw claims compared numerically with the stored record, plus strict fee and wage checks | Matching the demo record is not an external fact check. Missing, unknown or mismatched claims fail verification. Small samples produce a caveat. |
| Squad impact illustration | Heuristic defense and progression changes against the available Arsenal baseline | Unvalidated proxy. Other clubs explicitly disclose use of the Arsenal reference. Goalkeeper scoring lacks specialist shot-stopping metrics. |

The statistical score averages category percentiles using the role's priorities: defense (tackles/interceptions and aerial), progression (passes and carries), pressing/recovery, possession retention, and creation/goal threat. The tactical score uses the same categories to measure the shortfall against role targets. A shortfall of 15 percentile points corresponds to a 0.85 match factor; meeting a target gives 1.0.

## Verification

```bash
python -m pytest backend/tests -q
python -m backend.tests.integration_check
node --check backend/app/static/app.js
python -m backend.tests.eval_suite.run_evaluation --output work/evaluation.json
```

Node is needed only for the JavaScript syntax check; the app runs without a frontend build. GitHub Actions runs the tests, smoke check and JS syntax check.

The 50-scenario evaluation reports candidate coverage, empty results, clarification requests, errors, position agreement and constraint compliance separately. It checks every returned candidate against the effective brief and independently checks the scenario's age, budget and wage limits. Stress cases receive no automatic passes. Empty results remain in position-metric denominators; if no candidates are returned, candidate-compliance rates are `null`. Position agreement is not a measure of overall recruitment quality. Scenario text may contain unsupported preferences; those are not evaluated. Latency is measured locally, with no estimated LLM network latency or claimed external grounding accuracy.

## API

Interactive documentation: http://127.0.0.1:8000/api/docs

| Endpoint | Purpose |
| --- | --- |
| `POST /api/scout/profile` | Preview the interpreted brief without searching |
| `POST /api/scout/search` | Return dossier and workflow milestones |
| `GET /api/scout/stream` | SSE events emitted during actual execution, ending with `complete` or `error` |
| `GET /api/players` | List stored demo players |
| `GET /api/players/{id}` | Inspect a stored player |
| `POST /api/simulate?candidate_id=...&club=...` | Calculate the illustrative impact proxy |
| `GET /api/health` | App mode, version and player count |

Search/profile requests accept `objective`, `club`, `budget_eur`, `wage_cap_pw`, optional inclusive `age_max`, `min_minutes`, and optional `preferred_foot` (`Left`, `Right`, `Either`). SSE uses `budget` and `wage_cap` query names for compatibility and accepts the same optional constraints. Dossiers return `complete`, `no_matches`, or `needs_clarification` status. Invalid values receive HTTP 422. Stream execution failures return a safe error event; the UI closes the connection and offers retry instead of silently running the search again.

## Structure

- `backend/app/agents/`: role parsing, candidate retrieval, orchestration, finance and record verification.
- `backend/app/analytics/`: shared eligibility, role-based scoring, reliability, costs and impact proxy.
- `backend/app/data/`: SQLite records, demo seed data, bootstrap and local narrative index.
- `backend/app/static/`: accessible, responsive HTML/CSS/JavaScript interface; no build step or chart runtime.
- `backend/tests/`: regression tests, integration smoke check and scenario evaluation.

The default server listens on loopback at `127.0.0.1:8000`.
