# Data import audit

Source: StatsBomb Open Data, revision `4b73468fc5b0f1950f9f66fada70ad3a4f9327cb`. Competition: Premier League 2015/16. This report contains aggregate analysis and no redistributed match-event or player dataset.

| Check | Result |
| --- | --- |
| Imported match files | 380 events files and 380 lineup files |
| Fixture coverage | 20 teams; 38 matches per team; one home fixture against each other team |
| Event goal totals vs source score | 380 of 380 matches reconcile |
| Goals attributed to players | 988 |
| Own goals | 38 |
| Combined goal total | 1,026 |
| Players with positive regulation minutes | 548 |
| Maximum regulation minutes for a player | 3,420 |
| Minimum minutes for percentile cohorts | 900 |

Primary-position reference cohort sizes: goalkeepers 27, fullbacks/wingbacks 58, centrebacks 59, midfielders 84, wingers 59, strikers 37. Individual metric denominators can reduce these sizes; the API reports each metric's usable reference count. Secondary-position display options do not redefine reference cohorts.

These checks establish consistent ingestion and reproducible calculations against the source, not independent verification of every annotation, current player ability, commercial-use rights, or predictive validity. Statistics describe 2015/16; players' recorded clubs and roles are historical. Aggregation conventions and project-defined progression thresholds differ from other providers. The source data is provided as-is under its own agreement.

Reproduce the audit with the pinned importer and inspect local snapshot metadata, source match IDs and file hashes. Raw downloads and the derived snapshot remain local and are excluded from Git.
