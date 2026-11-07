'use strict';
const $ = id => document.getElementById(id);
const escapeHTML = value => String(value ?? '').replace(/[&<>"']/g,c=>({'&':'&amp;','<':'&lt;','>':'&gt;','"':'&quot;',"'":'&#39;'}[c]));
const euros = value => new Intl.NumberFormat('en-IE',{style:'currency',currency:'EUR',maximumFractionDigits:0}).format(value);
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
    return `<article class="panel comparison-player ${i ? 'comparison-blue' : 'comparison-green'}"><p class="eyebrow">${i ? 'COMPARISON PLAYER' : 'FIRST PLAYER'}</p><h2>${escapeHTML(p.name)}</h2><p>${escapeHTML(p.club)} · ${escapeHTML(p.league)}</p><dl><div><dt>Listed positions</dt><dd>${escapeHTML([p.primary_position,...p.secondary_positions].join(' / '))}</dd></div><div><dt>Age / preferred foot</dt><dd>${p.age} / ${escapeHTML(p.preferred_foot)}</dd></div><div><dt>Estimated fee</dt><dd>${euros(p.market_value_eur)}</dd></div><div><dt>Estimated weekly wage</dt><dd>${euros(p.weekly_wage_eur)}</dd></div></dl><p class="hint">Sample reliability: ${r.reliability_score}/100. ${escapeHTML(r.reliability_summary)}. This is not a quality or data-accuracy score.</p></article>`;
  }).join('');
  const group = comparisonData.groups[comparisonData.group];
  const metrics = group.metrics.map(key=>RADAR_METRICS.find(m=>m[0]===key));
  $('comparison-radar').innerHTML = renderRadar(first,null,second,metrics);
  // Exact values are central to a comparison, so start with the table expanded.
  const values = $('comparison-radar').querySelector('.radar-values');
  if (values) values.open = true;
  const rows = [ ['minutes_played','League minutes'],['matches_played','Matches played'],
    ['pass_completion_pct','Pass completion (%)'],['progressive_passes_per90','Progressive passes / 90'],
    ['aerial_duels_won_pct','Aerial duels won (%)'] ];
  if (comparisonData.group !== 'goalkeepers') rows.push(
    ['goals_per90','Goals / 90'],['assists_per90','Assists / 90'],['xg_per90','xG / 90'],['xa_per90','xA / 90'],
    ['progressive_carries_per90','Progressive carries / 90'],['tackles_per90','Tackles / 90'],
    ['interceptions_per90','Interceptions / 90'],['pressures_recoveries_per90','Pressures & recoveries / 90']);
  $('raw-comparison').innerHTML = `<table><caption class="sr-only">Raw player statistics from illustrative records</caption><thead><tr><th scope="col">Metric</th>${selected.map(r=>`<th scope="col">${escapeHTML(r.player.name)}</th>`).join('')}</tr></thead><tbody>${rows.map(([key,label])=>`<tr><th scope="row">${label}</th>${selected.map(r=>`<td>${escapeHTML(r.player.raw_metrics[key] ?? 'Unavailable')}</td>`).join('')}</tr>`).join('')}</tbody></table>`;
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
    const params = new URLSearchParams({group,include_secondary:String($('include-secondary').checked)});
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
$('player-one').addEventListener('change',renderComparison);
$('player-two').addEventListener('change',renderComparison);
$('retry-load').addEventListener('click',loadComparison);
loadComparison();
