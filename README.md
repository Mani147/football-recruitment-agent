# Touchline · Source-backed football season analysis

Explore real **StatsBomb Open Data, Premier League 2015/16** match events through explainable position profiles and two-player comparisons. This is a historical, non-commercial research workspace, not current recruitment intelligence.

The complete fixture list contains 380 matches, 20 teams and 38 fixtures per team. The local import produces 548 player-season records. All event goals, including own goals, reconcile with the score in each of the 380 source match records. This validates our ingestion against those records; it does not independently establish every annotation's accuracy.

## Install and run

Requires Python 3.11+ and network access for the one-time import.

```bash
python -m venv .venv
# Windows: .venv\Scripts\Activate.ps1
# macOS/Linux: source .venv/bin/activate
pip install -r requirements.txt
python -m backend.app.data.import_statsbomb
python -m backend.app.main
```

Open http://127.0.0.1:8000 for historical role search, or http://127.0.0.1:8000/compare for position-wise comparison. The app uses a generated local snapshot and needs no provider API key or network access during analysis. The source logo is loaded from the provider's repository for attribution.

**Data is not bundled or redistributed through this repository.** Review the [StatsBomb user agreement](https://github.com/hudl/open-data/blob/4b73468fc5b0f1950f9f66fada70ad3a4f9327cb/LICENSE.pdf) before fetching. It restricts redistribution and commercial use, and requires brand attribution for published analysis. Downloaded records and the generated snapshot are Git-ignored. The website includes the source logo and usage-agreement link. For commercial use or public data redistribution, obtain the appropriate provider permission first.

If the snapshot is missing, startup fails with the import command rather than silently substituting invented records. Do not expose `work/` as a static directory. The default server listens only on loopback.

## Reproducibility and source checks

- Upstream repository: [Hudl / StatsBomb Open Data](https://github.com/hudl/open-data).
- Pinned revision: `4b73468fc5b0f1950f9f66fada70ad3a4f9327cb`.
- Competition `2`, season `27`: Premier League 2015/16.
- The importer verifies 380 unique match IDs, 380 unique directed fixture pairs, 20 teams and 38 appearances per team. Each fixture must contain both half-end markers. Shot goals plus own-goal-for events must reconcile with both source scores.
- Raw events and lineups are downloaded directly, with bounded concurrency, retries and a compressed local cache. The snapshot records per-file SHA-256 hashes, upstream revision, retrieval time and every player's source match IDs. A failed build does not replace a previous snapshot.
- Rebuild using `python -m backend.app.data.import_statsbomb`. The default cache is `work/statsbomb-cache/`; the generated output is `backend/app/data/statsbomb_pl_2015_16.json`. Different output/cache locations can be supplied via `--output` and `--cache`.

## What is calculated

**Minutes and positions:** on-field intervals derived in source event order from Starting XI, substitutions, tactical shifts and dismissals. Each half is clipped to 45 regulation minutes. Temporary Player Off/On events are not subtracted. Source stoppage-time events still contribute to statistics, with a regulation-minute denominator. Primary position is the position with the most minutes; a secondary position needs at least 270 minutes and 10% of total minutes. Multi-club players are combined across the season and display all recorded clubs.

**Raw statistics:** counts and per-90 rates computed from event annotations. Progressive passes are completed open-play passes advancing at least 12 StatsBomb x-units toward goal; progressive carries use the same forward-distance threshold. These are project definitions, not claims to reproduce a vendor's proprietary aggregate metric. xG comes from provider shot values; xA is the summed xG of shots linked to assisting passes. Pressure plus recovery is a volume measure. Pass completion is labelled as such, not a general possession-retention score.

**Percentiles:** calculated separately for each requested position group against primary-position peers in this season with at least 900 regulation minutes. The average-rank formula for cohort members is `100 × (less + (equal − 1)/2) / (N − 1)`. For a secondary-position player outside the cohort, rank is interpolated as `less − 0.5` and clipped to 0–100. At least 10 reference players must have a usable metric. Aerial percentages require at least 20 aerial contests; pass completion requires 200 attempts; save rate requires 20 shots on target faced. Changing display filters does not change the reference cohort. There is **no league-strength multiplier** within this single-league dataset.

**Goalkeepers:** unadjusted save percentage from on-target shot outcomes while the keeper is active, plus collection and sweeper event rates and distribution measures. Save percentage is not adjusted for shot difficulty. Collections and sweeps measure volume, not success rate. Post-shot xG is unavailable.

**Historical role search:** recognised position/style text selects a predefined role target. Candidates are ordered by mean target-match factor across available position-specific percentile axes, with one equal weight per measured axis. Missing axes are excluded, and the scored-axis count is displayed. This heuristic is not an overall-quality rating, transfer recommendation, or forecast.

**Unavailable:** birth dates/ages, preferred foot, fees, wages, contracts, current availability, and validated squad-impact predictions. They are not filled with guesses or zero. Searches that request unavailable financial or demographic constraints return a clear HTTP 422 message. A chart omits unavailable axes and explains why; fewer than three measured axes produce no polygon. Players below the 900-minute cohort threshold remain browsable with the “All appearances” setting, but do not receive percentiles.

## Interface

- Season search: plain-language role, explicit minimum playing time, historical alignment score and measured-axis count.
- Comparison: goalkeepers, fullbacks/wingbacks, centrebacks, midfielders (DM/CM/AM), wingers and strikers (ST/CF), with an optional secondary-position filter.
- Position-specific radar, raw-stat table, exact percentile table, cohort and metric definitions. The comparison page has no invented overall winner or recruitment target.
- Persistent dark/light mode, responsive layout and reduced-motion support for the football header.

## API

Documentation: http://127.0.0.1:8000/api/docs

| Route | Behavior |
| --- | --- |
| `GET /api/dataset` | Source revision, season, coverage, definitions and limitations |
| `GET /api/players` / `GET /api/players/{id}` | Historical source-derived records; unknown financial and demographic fields are null |
| `GET /api/compare/players?group=midfielders&min_minutes=900&include_secondary=true` | Position-cohort comparisons |
| `POST /api/scout/profile` | Interpret the supported historical role constraints |
| `POST /api/scout/search` | Historical performance-profile search |
| `GET /api/scout/stream` | A completion event for the same real-data search |
| `POST /api/simulate` | HTTP 422: unsupported by this dataset |
| `GET /api/health` | Actual mode, season and player count |

Real-data API responses differ from the original demo dossiers. The legacy name `league_adjusted_percentiles` is retained for compatibility with shared chart code; in real mode these are computed position-cohort percentiles **without** a league adjustment. Use `data_mode` and metadata when interpreting them.

## Tests

```bash
python -m pytest backend/tests -q
node --test backend/tests/test_frontend.cjs
node --check backend/app/static/research.js
python -m backend.tests.integration_check
```

CI uses invented, explicitly isolated fixtures to test aggregation and API behavior without redistributing StatsBomb records or downloading an entire season. `TOUCHLINE_DATASET=demo` exists only for legacy fixture smoke tests. The hand-authored seed records and legacy financial engine are retained for regression testing; the default user-facing routes do not use them. The old 50-scenario demo benchmark does not measure real-player ranking quality and must not be reported as validation of the source-backed dataset.

See [the data quality report](docs/data-quality-report.md) for the import audit and remaining limitations.
