'use strict';
function sourceMethodHTML(meta, escape) {
  const active=meta.active_selection;
  const coverage=active ? `<p><strong>${escape(active.competition)} ${escape(active.season)}: ${active.included_matches} / ${active.expected_matches} fixtures included.</strong> ${active.missing_source_matches} missing from the source; ${active.excluded_matches.length} excluded by quality checks. ${active.unclassified_players} players have no observed starting position.</p>${active.excluded_matches.length ? `<details><summary>Excluded fixtures</summary><ul>${active.excluded_matches.map(x=>`<li>Match ${escape(x.match_id)}: ${escape(x.reason)}</li>`).join('')}</ul></details>` : ''}` : '';
  return `${coverage}<p>${escape(meta.percentile_method)}</p><p>${escape(meta.minutes_definition)}</p><ul>${(meta.limitations||[]).map(x=>`<li>${escape(x)}</li>`).join('')}</ul><dl>${Object.entries(meta.metric_definitions||{}).map(([k,v])=>`<dt><strong>${escape(k)}</strong></dt><dd>${escape(v)}</dd>`).join('')}</dl><p>Source: <a href="${escape(meta.source_url)}">${escape(meta.source)}</a> · release ${escape(meta.upstream_revision)}.</p>`;
}
function scopeQuery(competitionId,seasonId) {
  const result={};
  const competition=document.getElementById(competitionId)?.value;
  const season=document.getElementById(seasonId)?.value;
  if(competition) result.competition=competition;
  if(season) result.season=season;
  return result;
}
