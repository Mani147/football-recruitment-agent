# OpenPlay import audit

Source: openplay (Noah Bair), release `data-v0.1.0`. Imported November 7, 2026. Five leagues, 2023/24 through 2025/26. The current snapshot contains **8,317 player-season records from 5,229 included fixtures**. Data files and generated records are local and not committed.

| League | Season | Included / expected fixtures | Missing at source | Excluded | Player-seasons | Unclassified positions |
| --- | --- | --- | --- | --- | --- | --- |
| Premier League | 2023/24 | 378/380 | 0 | 2 | 570 | 82 |
| Premier League | 2024/25 | 377/380 | 0 | 3 | 562 | 71 |
| Premier League | 2025/26 | 379/380 | 0 | 1 | 537 | 63 |
| La Liga | 2023/24 | 380/380 | 0 | 0 | 598 | 75 |
| La Liga | 2024/25 | 380/380 | 0 | 0 | 589 | 58 |
| La Liga | 2025/26 | 380/380 | 0 | 0 | 600 | 71 |
| Bundesliga | 2023/24 | 305/306 | 0 | 1 | 494 | 73 |
| Bundesliga | 2024/25 | 302/306 | 0 | 4 | 480 | 49 |
| Bundesliga | 2025/26 | 300/306 | 0 | 6 | 498 | 63 |
| Serie A | 2023/24 | 380/380 | 0 | 0 | 590 | 86 |
| Serie A | 2024/25 | 379/380 | 0 | 1 | 599 | 79 |
| Serie A | 2025/26 | 380/380 | 0 | 0 | 586 | 70 |
| Ligue 1 | 2023/24 | 304/306 | 1 | 1 | 523 | 74 |
| Ligue 1 | 2024/25 | 304/306 | 0 | 2 | 542 | 83 |
| Ligue 1 | 2025/26 | 301/306 | 0 | 5 | 549 | 76 |

## Checks performed

The release checksum manifest is pinned in the importer. SHA-256 checks verify all four consumed files: coverage, published issues, match metadata and player-match aggregates. Source fixture counts must match the coverage manifest. Duplicate fixtures or player-match rows are rejected. Every included match has 11 recorded starters per side, usable player minutes and player goal totals (with opposing own goals) matching both source scores. Negative, missing or non-finite required counts and invalid attempt denominators fail the build. Failed builds preserve existing snapshots.

Known problematic fixtures are excluded. Additional exclusions arise from unknown/zero expanded minutes or source score/lineup inconsistencies. The website exposes excluded IDs and reasons per selection. Ligue 1 2023/24 also has one fixture absent from the release. Missing data is not extrapolated to a full season; per-90 rates use included appearances only.

## Interpretation limits

These checks establish reproducible ingestion and consistency with OpenPlay, not independent accuracy. We do not claim to have recoded matches from video or validated the OpenPlay xG model. The source is a community preview and the records link to WhoScored match pages; upstream redistribution permissions have not been independently established.

Starting-position codes are weighted by minutes in those starts. No positions are guessed for substitute-only players, and those records remain unclassified. A secondary position requires at least 270 starting-appearance minutes and 10% of observed starting-appearance minutes. Whole-season counts include substitute minutes and appearances in other roles.

Percentiles use primary-position peers within one league-season, with 900+ expanded minutes, at least 10 usable peers per metric, and minimum attempt counts for percentages. They are relative descriptions, not comparable league-adjusted ability estimates. Take-ons are not progressive carries, recoveries are not pressures, and goalkeeper actions measure workload volumes. Current finances, availability, verified age and squad-impact forecasts remain unsupported.

## Regression checks

Tests cover season/league separation, intra-league transfers, position exposure, substitute-only records, checksums, duplicate and invalid source records, denominator handling, percentile cohorts, selection validation, recruitment constraints, streaming selection and shared frontend behavior. Legacy StatsBomb aggregation tests remain isolated from the OpenPlay default. Runtime verification exercises all 15 league-season selections and six position groups.

Validation completed: 90 backend tests and 14 frontend tests pass. All 180 live comparison/search selections (15 league-seasons × six groups × two flows) returned the requested scope. Edge/Playwright checks passed for league/season search, linked player comparison, goalkeeper axes, theme persistence, season reload and mobile width, with no JavaScript errors. Desktop and mobile screenshots were visually inspected.
