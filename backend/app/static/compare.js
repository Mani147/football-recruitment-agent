'use strict';
const $ = id => document.getElementById(id);
const escapeHTML = value => String(value ?? '').replace(/[&<>"']/g,c=>({'&':'&amp;','<':'&lt;','>':'&gt;','"':'&quot;',"'":'&#39;'}[c]));
const euros = value => value == null ? 'Not available' : new Intl.NumberFormat('en-IE',{style:'currency',currency:'EUR',maximumFractionDigits:0}).format(value);
let comparisonData = null, loadingToken = 0;

function matchingSelection(records, firstId, secondId) {
  const first = records.find(r=>r.player.id===firstId) || records[0];
  const second = records.find(r=>r.player.id===secondId && r.player.id!==first?.player.id)
    || records.find(r=>r.player.id!==first?.player.id);
  return [first,second];
}

function renderComparison() {
  if (!comparisonData?.players.length) return;
  const records = comparisonData.players;
  const [first,second] = matchingSelection(records,$('player-one').value,$('player-two').value);
  const option = r => `<option value="${escapeHTML(r.player.id)}">${escapeHTML(r.player.name)} · ${escapeHTML(r.player.club)} (${escapeHTML(r.player.primary_position)})</option>`;
  $('player-one').innerHTML = records.map(option).join('');
  $('player-one').value = first.player.id;
  $('player-two').innerHTML = second ? records.filter(r=>r.player.id!==first.player.id).map(option).join('') : '<option value="">No second player in this group</option>';
  $('player-two').value = second?.player.id || '';
  $('player-two').disabled = !second;
  const selected = [first,...(second?[second]:[])];
  $('comparison-cards').innerHTML = selected.map((r,i)=>{
    const p = r.player;
    return `<article class="panel comparison-player ${i ? 'comparison-blue' : 'comparison-green'}"><p class="eyebrow">${i ? 'COMPARISON PLAYER' : 'FIRST PLAYER'}</p><h2>${escapeHTML(p.name)}</h2><p>${escapeHTML(p.club)} · ${escapeHTML(p.league)}${p.season ? ` · ${escapeHTML(p.season)}` : ''}</p><dl><div><dt>Listed positions</dt><dd>${escapeHTML([p.primary_position,...p.secondary_positions].join(' / '))}</dd></div><div><dt>Age / preferred foot</dt><dd>${p.age ?? 'Not recorded'} / ${escapeHTML(p.preferred_foot || 'Not recorded')}</dd></div><div><dt>Estimated fee</dt><dd>${euros(p.market_value_eur)}</dd></div><div><dt>Estimated weekly wage</dt><dd>${euros(p.weekly_wage_eur)}</dd></div></dl><p class="hint">${r.sample_note ? escapeHTML(r.sample_note) : `Sample reliability: ${r.reliability_score}/100. ${escapeHTML(r.reliability_summary)}. This is not a quality or data-accuracy score.`}</p>${Number.isFinite(r.cohort_size) ? `<p class="hint">Reference group: ${r.cohort_size} primary-position peers with 900+ minutes. Metric-specific attempt thresholds can reduce this count.</p>` : ''}</article>`;
  }).join('');
  const group = comparisonData.groups[comparisonData.group];
  const allMetrics = comparisonData.data_mode==='statsbomb' ? realRadarMetrics(group.metrics) : group.metrics.map(key=>RADAR_METRICS.find(m=>m[0]===key));
  const metrics = allMetrics.filter(([key])=>Number.isFinite(first.league_adjusted_percentiles[key]) && (!second || Number.isFinite(second.league_adjusted_percentiles[key])));
  const missing = allMetrics.filter(m=>!metrics.includes(m)).map(m=>m[1]);
  $('comparison-radar').innerHTML = (metrics.length>=3 ? renderRadar(first,null,second,metrics) : '<p>Not enough measured axes for a radar. Increase playing time or choose another player; raw values remain below.</p>')
    + (missing.length ? `<p class="hint">Unavailable axes omitted: ${escapeHTML(missing.join(', '))}. Insufficient playing time, denominator or cohort size; missing does not mean zero.</p>` : '');
  // Exact values are central to a comparison, so start with the table expanded.
  const values = $('comparison-radar').querySelector('.radar-values');
  if (values) values.open = true;
  const rows = [ ['minutes_played','League minutes'],['matches_played','Matches played'],
    ['pass_completion_pct','Pass completion (%)'],['progressive_passes_per90','Progressive passes / 90'],
    ['aerial_duels_won_pct','Aerial duels won (%)'] ];
  if (comparisonData.group === 'goalkeepers' && comparisonData.data_mode === 'statsbomb') rows.push(['save_pct','Unadjusted save (%)'],['shots_on_target_faced','Shots on target faced'],['keeper_claims_per90','Collections / 90'],['keeper_sweeps_per90','Sweeper actions / 90']);
  if (comparisonData.group !== 'goalkeepers') rows.push(
    ['goals_per90','Goals / 90'],['assists_per90','Assists / 90'],['xg_per90','xG / 90'],['xa_per90','xA / 90'],
    ['progressive_carries_per90','Progressive carries / 90'],['tackles_per90','Tackles / 90'],
    ['interceptions_per90','Interceptions / 90'],['pressures_recoveries_per90','Pressures & recoveries / 90']);
  $('raw-comparison').innerHTML = `<table><caption class="sr-only">Raw player statistics from season records</caption><thead><tr><th scope="col">Metric</th>${selected.map(r=>`<th scope="col">${escapeHTML(r.player.name)}</th>`).join('')}</tr></thead><tbody>${rows.map(([key,label])=>`<tr><th scope="row">${label}</th>${selected.map(r=>`<td>${escapeHTML(r.player.raw_metrics[key] ?? r.player.counts?.[key] ?? 'Unavailable')}</td>`).join('')}</tr>`).join('')}</tbody></table>`;
  $('compare-status').textContent = `${records.length} ${group.label.toLowerCase()} available${comparisonData.include_secondary?' including secondary positions':''}. ${second ? 'Compare the profiles below.' : 'Only one player is available; a second profile cannot be shown.'}`;
}

async function loadComparison() {
  const token = ++loadingToken;
  const previous = [$('player-one').value,$('player-two').value];
  $('comparison-body').hidden = true;
  $('keeper-notice').hidden = true;
  $('compare-error').hidden = true;
  $('retry-load').hidden = true;
  $('compare-status').textContent = 'Loading this position group…';
  try {
    const group = $('position-group').value;
    const params = new URLSearchParams({group,include_secondary:String($('include-secondary').checked),min_minutes:$('compare-minutes').value});
    const response = await fetch(`/api/compare/players?${params}`);
    if (!response.ok) throw Error('Unable to load players. Please retry.');
    const data = await response.json();
    if (token !== loadingToken) return;
    comparisonData = data;
    $('data-notice').textContent = `${data.dataset_count} stored players. ${data.dataset_notice}`;
    for (const option of $('position-group').options) {
      const info = data.groups[option.value];
      option.textContent = `${info.label} (${info.count})`;
    }
    $('keeper-notice').hidden = group !== 'goalkeepers';
    if (data.data_mode === 'statsbomb') {
      $('keeper-notice').innerHTML = '<p><strong>Goalkeeper caveat.</strong> Save percentage is not adjusted for shot difficulty. Collections and sweeping are event counts, not success rates. Post-shot xG is unavailable.</p>';
      $('methodology').innerHTML = `<p>${escapeHTML(data.metadata.percentile_method)}</p><p>${escapeHTML(data.metadata.minutes_definition)}</p><ul>${data.metadata.limitations.map(x=>`<li>${escapeHTML(x)}</li>`).join('')}</ul><dl>${Object.entries(data.metadata.metric_definitions).map(([k,v])=>`<dt><strong>${escapeHTML(k)}</strong></dt><dd>${escapeHTML(v)}</dd>`).join('')}</dl>`;
    }
    if (!data.players.length) {
      $('compare-status').textContent = 'No stored players match this position group. Try including secondary positions or choose another group.';
      return;
    }
    $('player-one').innerHTML = data.players.map(r=>`<option value="${escapeHTML(r.player.id)}">${escapeHTML(r.player.name)}</option>`).join('');
    $('player-two').innerHTML = $('player-one').innerHTML;
    const [first,second] = matchingSelection(data.players,...previous);
    $('player-one').value = first.player.id;
    $('player-two').value = second?.player.id || '';
    renderComparison();
    $('comparison-body').hidden = false;
  } catch (error) {
    if (token !== loadingToken) return;
    $('compare-error').textContent = error instanceof TypeError
      ? 'Cannot reach the recruitment service. Restart the local server if needed, then retry loading.' : error.message;
    $('compare-error').hidden = false;
    $('retry-load').hidden = false;
    $('compare-status').textContent = 'Players could not be loaded.';
  }
}
$('position-group').addEventListener('change',loadComparison);
$('include-secondary').addEventListener('change',loadComparison);
$('compare-minutes').addEventListener('change',loadComparison);
$('player-one').addEventListener('change',renderComparison);
$('player-two').addEventListener('change',renderComparison);
$('retry-load').addEventListener('click',loadComparison);
loadComparison();
