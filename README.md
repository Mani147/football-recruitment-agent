# Touchline · Football comparison and recruitment research

Compare players and discover performance profiles using **OpenPlay, 2023/24, 2024/25 and 2025/26**. Coverage includes the Premier League, La Liga, Bundesliga, Serie A and Ligue 1. The default selection is Premier League 2025/26. This snapshot has **8,317 player-season records and 5,229 included matches** across 15 league-seasons; it is not a live 2026/27 feed.

## Install and run

Requires Python 3.11+ and network access for the one-time data import. No API key is needed.

```bash
python -m venv .venv
# Windows: .venv\Scripts\Activate.ps1
# macOS/Linux: source .venv/bin/activate
pip install -r requirements.txt
python -m backend.app.data.import_openplay
python -m backend.app.main
```

Open http://127.0.0.1:8000 for role search or http://127.0.0.1:8000/compare for comparison. The app reads a local snapshot and needs no network during analysis. Importing downloads approximately 28 MB of Parquet and metadata files; it does not download 41 million individual events. DuckDB reads the provider's documented player-match aggregates. A fresh checkout must run the import before starting the app; missing data never falls back to invented player records.

## Using the workspace

1. Select a league and season on either page. Both comparison players come from this selection.
2. For recruitment research, name a position and style, review the interpreted role, and inspect the top profiles. For comparison, choose goalkeepers, fullbacks/wingbacks, centrebacks, midfielders (DM/CM/AM), wingers or strikers.
3. Set minimum playing time. Players below 900 minutes can be browsed on the comparison page but receive no percentiles.
4. Inspect the radar, exact percentiles and raw rates. Open the source panel to see included/excluded fixtures, cohort methodology and metric definitions.

Recognised words select predefined role targets; this is rule-based interpretation, not an unrestricted natural-language scouting model. The alignment score is an equal-weight mean target-match factor over measured axes, not an overall player rating or transfer forecast. Missing axes are omitted, never set to zero. New take-on, recovery and goalkeeper volume axes use a disclosed default target of the 75th percentile. Different leagues have separate reference populations; their percentiles should not be compared as league-adjusted ability ratings.

## Source and reproducibility

- Dataset: [openplay (Noah Bair)](https://github.com/nlbair/openplay), preview release `data-v0.1.0`, published November 3, 2026. The release links its underlying match records to WhoScored pages. This integration does not scrape those pages.
- [Release downloads](https://github.com/nlbair/openplay/releases/tag/data-v0.1.0) and [data dictionary](https://github.com/nlbair/openplay/blob/main/DATA_DICTIONARY.md).
- The checksum manifest is pinned to SHA-256 `5d185a3687dc6661a79b0ee9bb4363ed113ecf758142577812ebb9b88c8d0a27`. Every consumed file must match its manifest hash. Partial or corrupt transfers cannot replace verified cached files.
- Import only selects five leagues and the three requested seasons. Published problematic fixtures, incomplete lineups/minutes and source-score mismatches are excluded. Every included match's player goals plus opposing own goals must reconcile with its source score. Missing fixtures remain missing; coverage is displayed.
- Intra-league transfers are combined within the same player/league/season. Different leagues and seasons remain distinct records. IDs retain the upstream player ID, and each record retains its source match IDs.
- Rebuild with `python -m backend.app.data.import_openplay`. Optional `--cache` and `--output` accept paths. Default cache: `work/openplay-cache/`; output: `backend/app/data/openplay_2023_2026.json`. A failed build preserves the previous snapshot.

## Metrics and positions

**Minutes:** OpenPlay expanded minutes include stoppage time. All per-90 rates use that denominator. These rates differ from regulation-minute aggregates.

**Positions:** map the release's starting-position codes into the six groups. Primary position is weighted by minutes in appearances started in each position. Secondary positions require at least 270 such minutes and 10% of observed starting-appearance minutes. This is not a reconstruction of in-match position changes. Substitute positions are unknown; a player with no observed starts remains unclassified. Statistics include all included appearances, including substitute minutes.

**Percentiles:** primary-position peers in the same league and season with 900+ expanded minutes. At least 10 peers need usable values. Average ranks handle ties: `100 * (less + (equal - 1)/2) / (N - 1)`. Secondary-position players outside that reference cohort receive a clipped interpolated rank. Display filters do not change the cohort. Aerial percentages require 20 contests and pass completion requires 200 attempts. There is no league-strength multiplier.

**OpenPlay definitions:** progressive passes are completed, non-set-piece passes starting at x >= 40 and ending at least 25% closer to goal centre. Successful take-ons are not progressive carries; recoveries do not include pressures. xG comes from Noah Bair's OpenPlay model; xA sums the xG of linked shots set up by a player. Neither is presented as StatsBomb or Opta xG.

**Goalkeepers:** saves, high claims and successful sweeps per 90, plus distribution. These measure volume and workload, not save percentage, claim success rate or shot-difficulty-adjusted quality. Save percentage and post-shot xG are unavailable.

**Unknowns:** current ages, preferred foot, fees, wages, contracts, availability and validated squad-impact predictions. Source age fields are not used as verified age. Unsupported financial/demographic constraints return HTTP 422. These are performance shortlists for further investigation, not verified transfer opportunities.

## Attribution and access

The maintainer declares the data [CC BY 4.0](https://github.com/nlbair/openplay/blob/main/LICENSE), with credit to **openplay (Noah Bair)**. The website carries that attribution. This project has not independently established upstream redistribution permissions. Downloaded files and derived player records stay local and Git-ignored; the repository publishes integration code and aggregate audit results. Review the source terms for your intended deployment. The old StatsBomb import remains available as a historical research utility, but is not used by the default app.

## API

Interactive docs: http://127.0.0.1:8000/api/docs

| Route | Behavior |
| --- | --- |
| `GET /api/dataset?competition=eng&season=2025/26` | Catalogue, active coverage, source, definitions and limitations |
| `GET /api/compare/players?group=midfielders&competition=esp&season=2024/25&min_minutes=900` | Same-league, same-season position comparisons |
| `GET /api/players?competition=ger&season=2023/24` | Source-derived records in the selected league-season |
| `GET /api/players/{id}` | One unambiguous player/league/season record |
| `POST /api/scout/profile` and `/api/scout/search` | Accept `objective`, `min_minutes`, `competition` and `season` |
| `GET /api/scout/stream` | Same selection and constraints as role search |
| `POST /api/simulate` | HTTP 422: unsupported by this dataset |
| `GET /api/health` | Actual mode, available seasons and default-selection counts |

Competition codes: `eng`, `esp`, `ger`, `ita`, `fra`. Seasons: `2023/24`, `2024/25`, `2025/26`. Defaults: `eng`, `2025/26`. Invalid selections return HTTP 422. The legacy field name `league_adjusted_percentiles` is retained for shared charts; in real mode these are position/league/season percentiles with no league-strength adjustment. Check `data_mode` and metadata.

## Validation

```bash
python -m pytest backend/tests -q
node --test backend/tests/test_frontend.cjs
python -m backend.tests.integration_check
```

CI uses invented, isolated fixtures and does not download provider data. `TOUCHLINE_DATASET=demo` exists for legacy smoke tests; the original 22 hand-authored records and financial engine are regression fixtures, not the default app. Their old benchmark does not validate real-player rankings.

See [the import audit](docs/data-quality-report.md) for coverage and validation limits.
