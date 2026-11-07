'use strict';
const $ = id => document.getElementById(id);
const money = value => new Intl.NumberFormat('en-IE', {style:'currency', currency:'EUR', maximumFractionDigits:0}).format(value);
const escapeHTML = value => String(value ?? '').replace(/[&<>"']/g, c => ({'&':'&amp;','<':'&lt;','>':'&gt;','"':'&quot;',"'":'&#39;'}[c]));
const listHTML = items => items.map(item => `<li>${escapeHTML(item)}</li>`).join('');
let reviewed = null, currentDossier = null, source = null, requestId = 0;

function showError(message) { $('error').textContent = message; $('error').hidden = false; }
function clearError() { $('error').hidden = true; $('error').textContent = ''; }
function setBusy(busy) {
  $('brief-fields').disabled = busy;
  $('search-button').disabled = busy;
  $('cancel-button').hidden = !busy;
}
function invalidate() {
  reviewed = null;
  $('search-button').hidden = true;
  $('review-content').hidden = true;
  $('review-placeholder').hidden = false;
  $('results').hidden = true;
  currentDossier = null;
  $('status').textContent = 'Brief changed. Review the interpretation before searching.';
  clearError();
}
$('brief-form').addEventListener('input', invalidate);
$('brief-form').addEventListener('change', invalidate);

function requestBody() {
  const body = { objective:$('objective').value.trim(), club:$('club').value.trim(),
    budget_eur:Number($('budget').value) * 1e6, wage_cap_pw:Number($('wage').value),
    min_minutes:Number($('minutes').value) };
  if ($('age').value !== '') body.age_max = Number($('age').value);
  if ($('foot').value !== '') body.preferred_foot = $('foot').value;
  return body;
}
function briefItems(p) {
  return [['Position',p.position_family === 'WINGER' && p.position === 'WINGER' ? 'Either wing' : p.position],
    ['Age range',`${p.age_min}–${p.age_max} years`], ['Maximum fee',money(p.budget_max_eur)],
    ['Weekly wage cap',money(p.wage_cap_eur_pw)], ['Minimum minutes',p.min_minutes_played.toLocaleString()],
    ['Preferred foot',p.preferred_foot || 'No preference']];
}
async function postJSON(url, body) {
  const response = await fetch(url, {method:'POST', headers:{'Content-Type':'application/json'}, body:JSON.stringify(body)});
  let data;
  try { data = await response.json(); } catch { throw new Error('The server returned an unreadable response. Please try again.'); }
  if (!response.ok) {
    const detail = Array.isArray(data.detail) ? data.detail.map(d => `${d.loc.at(-1)}: ${d.msg}`).join('; ') : data.detail;
    throw new Error(detail || 'Unable to process this brief. Check your inputs and try again.');
  }
  return data;
}
$('brief-form').addEventListener('submit', async event => {
  event.preventDefault();
  if (!$('brief-form').reportValidity()) return;
  clearError(); setBusy(true);
  const token = ++requestId;
  reviewed = null;
  $('results').hidden = true;
  $('search-button').hidden = true;
  $('review-button').textContent = 'Interpreting your brief…';
  $('status').textContent = 'Checking the role and effective constraints…';
  try {
    const body = requestBody();
    const data = await postJSON('/api/scout/profile', body);
    if (token !== requestId) return;
    const p = data.profile;
    $('review-placeholder').hidden = true;
    $('review-content').hidden = false;
    if (data.needs_clarification) {
      $('review-content').innerHTML = '<h3>We need a clearer position.</h3><p class="review-note">Add a recognised role such as striker, goalkeeper, fullback, centre-back, DM, CM, AM or winger. Then review your brief again.</p>';
      $('status').textContent = 'Position unclear. Edit the role text to continue.';
    } else {
      $('review-content').innerHTML = `<p class="review-role">${escapeHTML(p.tactical_role_name)}</p><p class="review-club">Recruiting for ${escapeHTML(p.target_club)}</p><dl class="brief-dl">${briefItems(p).map(([k,v]) => `<div><dt>${escapeHTML(k)}</dt><dd>${escapeHTML(v)}</dd></div>`).join('')}</dl><p class="review-note">${escapeHTML(data.notice)} Nationality, league preferences and exact metric thresholds written in the text are not enforced. No constraints will be relaxed automatically.</p>`;
      reviewed = {body, profile:p};
      $('search-button').hidden = false;
      $('status').textContent = 'Review these limits. When they look right, find matching players.';
    }
    $('review-heading').focus();
  } catch (error) { showError(error.message); $('status').textContent = 'Brief review failed. You can edit and try again.'; }
  finally { if (token === requestId) { setBusy(false); $('review-button').textContent = 'Review my brief →'; } }
});

function stopStream(message) {
  if (source) { source.close(); source = null; }
  setBusy(false);
  $('status').textContent = message;
}
$('cancel-button').addEventListener('click', () => stopStream('Stopped waiting for this search. Your reviewed brief is ready to run again.'));
$('search-button').addEventListener('click', () => {
  if (!reviewed || source) return;
  clearError(); setBusy(true);
  $('activity').hidden = false;
  $('events').replaceChildren();
  $('results').hidden = true;
  currentDossier = null;
  $('status').textContent = 'Finding eligible players, ranking fit and checking stored records…';
  const body = reviewed.body;
  const params = new URLSearchParams({objective:body.objective, club:body.club,
    budget:body.budget_eur, wage_cap:body.wage_cap_pw, min_minutes:body.min_minutes});
  if (body.age_max !== undefined) params.set('age_max', body.age_max);
  if (body.preferred_foot !== undefined) params.set('preferred_foot', body.preferred_foot);
  const stream = new EventSource(`/api/scout/stream?${params}`);
  source = stream;
  stream.onmessage = event => {
    if (source !== stream) return;
    try {
      const payload = JSON.parse(event.data);
      if (payload.event === 'milestone') {
        const item = document.createElement('li');
        const agent = document.createElement('strong');
        agent.textContent = payload.data.agent;
        item.append(agent, document.createTextNode(payload.data.message));
        $('events').append(item);
        $('events').scrollTop = $('events').scrollHeight;
      } else if (payload.event === 'complete') {
        stopStream('Search complete. Select a player to inspect the evidence and caveats.');
        renderDossier(payload.data.dossier);
      } else if (payload.event === 'error') {
        stopStream('Search failed. Your brief is still available to retry.');
        showError(payload.data.message);
      }
    } catch (error) {
      stopStream('Unable to display this result. Please retry.');
      showError(error.message);
    }
  };
  stream.onerror = () => {
    if (source !== stream) return;
    stopStream('Connection interrupted. Your brief is still available to retry.');
    showError('The search connection was interrupted. Check that the server is running, then try again.');
  };
});

function renderDossier(dossier) {
  currentDossier = dossier;
  $('results').hidden = false;
  const candidates = dossier.top_candidates || [];
  $('results-heading').textContent = candidates.length ? `${candidates.length} ${candidates.length === 1 ? 'player' : 'players'} to inspect` : 'No matching players';
  $('result-summary').textContent = candidates.length
    ? `${dossier.eligible_candidate_count} eligible ${dossier.eligible_candidate_count === 1 ? 'player' : 'players'} found. Showing the top ${candidates.length}; all meet the displayed constraints.`
    : dossier.director_executive_summary;
  $('effective-strip').innerHTML = briefItems(dossier.recruitment_profile).map(([k,v]) => `<span class="chip">${escapeHTML(k)}: <strong>${escapeHTML(v)}</strong></span>`).join('');
  $('dataset-notice').textContent = dossier.dataset_notice;
  $('limitations-list').innerHTML = listHTML(dossier.limitations);
  $('candidate-list').replaceChildren();
  $('candidate-detail').replaceChildren();
  $('result-grid').hidden = !candidates.length;
  $('empty-state').hidden = Boolean(candidates.length);
  if (!candidates.length) {
    $('empty-state').innerHTML = '<h3>Your limits stayed intact.</h3><p>No demo players meet every requirement. This is a dataset limitation, not proof that no suitable player exists. Try explicitly raising the fee or wage cap, widening the age range, lowering the minutes threshold, or removing a foot preference.</p><button type="button" class="secondary" id="edit-brief">Edit my brief ↑</button>';
    $('edit-brief').onclick = () => { $('brief').scrollIntoView({behavior:'smooth'}); $('objective').focus(); };
    $('status').textContent = 'No matching demo players. Edit the brief to explore a different set of limits.';
  } else {
    candidates.forEach((c, i) => {
      const button = document.createElement('button');
      button.className = 'candidate'; button.type = 'button';
      button.setAttribute('aria-pressed', 'false');
      button.setAttribute('aria-label', `Inspect rank ${c.rank}, ${c.player.name}, fit ${c.fit_score} of 100`);
      button.innerHTML = `<div class="candidate-top"><div><span class="rank">RANK ${c.rank}</span><h3>${escapeHTML(c.player.name)}</h3></div><div class="candidate-score">${c.fit_score}<span>FIT / 100</span></div></div><p>${escapeHTML(c.player.club)} · ${escapeHTML([c.player.primary_position,...c.player.secondary_positions].join(' / '))}</p><small>${c.player.age} yrs · ${money(c.player.market_value_eur)} fee · ${money(c.player.weekly_wage_eur)}/wk</small>`;
      button.onclick = () => selectCandidate(i);
      $('candidate-list').append(button);
    });
    selectCandidate(0);
  }
  $('results-heading').scrollIntoView({behavior:'smooth', block:'start'});
  $('results-heading').focus({preventScroll:true});
}
function selectCandidate(index) {
  const c = currentDossier.top_candidates[index], p = c.player;
  const audit = currentDossier.verifications.find(v => v.candidate_id === p.id);
  const sim = currentDossier.impact_simulations.find(s => s.candidate_id === p.id);
  Array.from($('candidate-list').children).forEach((button, i) => button.setAttribute('aria-pressed', String(i === index)));
  const breakdown = c.tactical_breakdown.map(b => `<div class="metric"><div class="metric-label"><span>${escapeHTML(b.metric_name)}</span><span>${b.player_league_adj_pct} / target ${b.target_pct}</span></div><div class="bar"><div class="bar-fill" style="width:${Math.max(0,Math.min(100,b.player_league_adj_pct))}%"></div><span class="target" style="left:${Math.max(0,Math.min(100,b.target_pct))}%"></span></div></div>`).join('');
  const delta = value => `${value > 0 ? '+' : ''}${value.toFixed(1)}`;
  $('candidate-detail').innerHTML = `<div class="detail-header"><div><p class="eyebrow">PLAYER EVIDENCE / #${c.rank}</p><h3>${escapeHTML(p.name)}</h3><p>${escapeHTML(p.club)} · ${escapeHTML(p.league)}<br>${p.age} years · ${escapeHTML(p.preferred_foot)} foot<br>Listed roles: ${escapeHTML([p.primary_position,...p.secondary_positions].join(' / '))}</p></div><span class="audit-badge ${audit?.is_verified ? '' : 'warning'}">${audit?.is_verified ? 'Record checks passed' : 'Review audit flags'}</span></div>
    <dl class="stat-row"><div><dt>Overall fit</dt><dd>${c.fit_score}<small> / 100</small></dd><p>Weighted comparison</p></div><div><dt>Sample reliability</dt><dd>${c.reliability_score}<small> / 100</small></dd><p>${p.raw_metrics.minutes_played.toLocaleString()} league minutes</p></div><div><dt>Estimated fee</dt><dd>${(p.market_value_eur/1e6).toFixed(1)}<small> M EUR</small></dd><p>${money(p.weekly_wage_eur)} per week</p></div><div><dt>Annual book cost</dt><dd>${(c.estimated_annual_cost_eur/1e6).toFixed(2)}<small> M EUR</small></dd><p>Fee ÷ 5 + annual wages</p></div></dl>
    <div class="detail-columns"><section class="detail-section"><h4>Why this player ranks here</h4><ul>${listHTML(c.why_recommended)}</ul><p>Tactical ${c.tactical_fit_score} · Statistical ${c.stat_fit_score} · Financial ${c.financial_fit_score} · Age ${c.age_potential_score}</p></section><section class="detail-section"><h4>What to investigate next</h4><ul>${listHTML(c.risk_factors)}</ul><p>${escapeHTML(c.reliability_summary)}</p><p>Confirm availability, medical history and actual asking price with independent sources.</p></section></div>
    <section class="detail-section"><h4>Tactical evidence against the target</h4><p class="metric-legend">Green bar: league-adjusted percentile. Dark marker: role target. These are heuristic comparisons within the demo data.</p>${breakdown}</section>
    <section class="detail-section"><h4>Stored-record audit</h4>${audit ? `<p><strong>${audit.matched_claim_count} of ${audit.checked_claim_count} raw metric claims match.</strong> Fee cap: ${audit.budget_compliance_verified ? 'passed' : 'failed'}. Wage cap: ${audit.wage_compliance_verified ? 'passed' : 'failed'}.</p>${audit.flagged_caveats.length ? `<ul>${listHTML(audit.flagged_caveats)}</ul>` : '<p>No record mismatches or cap violations found. This does not establish real-world accuracy.</p>'}<details><summary>Inspect checked values</summary><ul>${listHTML(audit.verified_claims)}</ul></details>` : '<p>No audit is available for this candidate.</p>'}</section>
    ${sim ? `<section class="detail-section impact"><h4>Squad impact illustration</h4><p>${sim.baseline_is_fallback ? `No baseline exists for ${escapeHTML(currentDossier.club)}. This illustration uses Arsenal FC as a reference.` : `Reference baseline: ${escapeHTML(sim.baseline_club)}.`} Not a validated prediction.</p><div class="impact-grid"><p>Defense index<strong>${sim.baseline_squad_defense} → ${sim.projected_squad_defense}</strong>Change ${delta(sim.projected_squad_defense-sim.baseline_squad_defense)}</p><p>Progression index<strong>${sim.baseline_squad_progression} → ${sim.projected_squad_progression}</strong>Change ${delta(sim.projected_squad_progression-sim.baseline_squad_progression)}</p></div></section>` : ''}`;
}
$('export-button').addEventListener('click', () => {
  if (!currentDossier) return;
  const url = URL.createObjectURL(new Blob([JSON.stringify(currentDossier, null, 2)], {type:'application/json'}));
  const link = document.createElement('a'); link.href = url; link.download = 'touchline-recruitment-dossier.json';
  document.body.append(link); link.click(); link.remove();
  setTimeout(() => URL.revokeObjectURL(url), 1000);
});
const presets = {
  dm:{text:'Find a high-pressing defensive midfielder with strong ball recovery and progressive passing', budget:40, foot:''},
  lb:{text:'Find a left-footed left back who can progress the ball and support attacks', budget:50, foot:'Left'},
  rw:{text:'Find a right winger with strong carrying and chance creation', budget:50, foot:'Either'}
};
document.querySelectorAll('[data-preset]').forEach(button => button.addEventListener('click', () => {
  const p = presets[button.dataset.preset];
  $('objective').value = p.text; $('budget').value = p.budget; $('foot').value = p.foot;
  $('age').value = ''; $('minutes').value = 800; $('wage').value = 120000;
  invalidate(); $('objective').focus();
}));
window.addEventListener('beforeunload', () => source?.close());
