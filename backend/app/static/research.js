'use strict';
const $ = id=>document.getElementById(id);
const esc = value=>String(value??'').replace(/[&<>"']/g,c=>({'&':'&amp;','<':'&lt;','>':'&gt;','"':'&quot;',"'":'&#39;'}[c]));
let results=null, metadataToken=0;
function showProfile() {
  const row=results?.candidates.find(r=>r.player.id===$('research-player').value);
  if (!row) return;
  const p=row.player;
  const axes=realRadarMetrics(results.metrics);
  const measured=axes.filter(([key])=>Number.isFinite(row.league_adjusted_percentiles[key]));
  const query=new URLSearchParams({group:results.group,competition:p.competition_code||'',season:p.season||'',player:p.id});
  const raw=[['minutes_played','Expanded minutes'],['matches_played','Matches'],['pass_completion_pct','Pass completion (%)'],['progressive_passes_per90','Progressive passes / 90'],['successful_takeons_per90','Successful take-ons / 90'],['tackles_per90','Tackles / 90'],['interceptions_per90','Interceptions / 90'],['ball_recoveries_per90','Recoveries / 90'],['xg_per90','OpenPlay xG / 90'],['xa_per90','OpenPlay xA / 90']];
  if(results.group==='goalkeepers') {
    raw.splice(4);
    raw.push(['keeper_saves_per90','Saves / 90'],['keeper_claims_per90','High claims / 90'],['keeper_sweeps_per90','Successful sweeps / 90']);
  }
  $('research-detail').innerHTML=`<p class="eyebrow">SEASON PLAYER PROFILE</p><h2>${esc(p.name)}</h2><p>${esc(p.club)} · ${esc(p.league)} ${esc(p.season)} · ${esc([p.primary_position,...p.secondary_positions].join(' / '))}</p><p>${esc(row.sample_note)}</p><p><strong>Role alignment: ${row.profile_score}/100</strong> across ${row.scored_metric_count} measured axes. This target-match heuristic is not an overall quality score or transfer forecast.</p>${measured.length>=3?renderRadar(row,{target_percentiles:results.profile.target_percentiles},null,measured):'<p>Fewer than three measured axes; radar unavailable.</p>'}<p class="hint">Omitted axes: ${esc(axes.filter(m=>!measured.includes(m)).map(m=>m[1]).join(', ')||'none')}. Missing values are excluded, not scored as zero.</p><details class="radar-values"><summary>View raw season output</summary><div class="radar-table-scroll"><table><tbody>${raw.map(([key,label])=>`<tr><th scope="row">${label}</th><td>${esc(p.raw_metrics[key]??'Unavailable')}</td></tr>`).join('')}</tbody></table></div></details><a class="secondary" href="/compare?${esc(query)}">Compare this player with others in the same position →</a>`;
}
$('research-player').addEventListener('change',showProfile);
$('research-form').addEventListener('submit',async event=>{
  event.preventDefault();
  $('research-submit').disabled=true;
  $('research-error').hidden=true;
  $('research-results').hidden=true;
  $('research-status').textContent='Checking the selected league, season and position cohort…';
  const selection=scopeQuery('research-competition','research-season');
  try {
    const response=await fetch('/api/scout/search',{method:'POST',headers:{'Content-Type':'application/json'},body:JSON.stringify({objective:$('research-objective').value.trim(),min_minutes:Number($('research-minutes').value),...selection})});
    const data=await response.json();
    if(!response.ok) throw Error(data.detail || 'The search could not be processed.');
    if(JSON.stringify(selection)!==JSON.stringify(scopeQuery('research-competition','research-season'))) return;
    results=data;
    $('research-status').textContent=data.status==='needs_clarification'?data.message : data.candidates.length ? `${data.eligible_count} eligible profiles; showing the top ${data.candidates.length}.` : 'No measured player profiles meet this position and playing-time requirement.';
    if (!data.candidates.length) return;
    $('research-role').textContent=`${data.profile.tactical_role_name} · ${data.profile.position} · minimum ${data.profile.min_minutes_played} minutes`;
    $('research-explanation').textContent=data.message;
    $('research-player').innerHTML=data.candidates.map(r=>`<option value="${esc(r.player.id)}">${esc(r.player.name)} — alignment ${r.profile_score}/100 (${r.scored_metric_count} axes)</option>`).join('');
    showProfile();
    $('research-results').hidden=false;
  } catch(error) {
    $('research-error').textContent=error instanceof TypeError ? 'Cannot reach the local service. Restart the server and retry; your text has been kept.' : error.message;
    $('research-error').hidden=false;
    $('research-status').textContent='Search could not complete.';
  } finally { $('research-submit').disabled=false; }
});
async function loadResearchMetadata() {
  const token=++metadataToken;
  $('research-results').hidden=true;
  $('research-status').textContent='Ready to explore the selected season.';
  try {
    const params=new URLSearchParams(scopeQuery('research-competition','research-season'));
    const response=await fetch(`/api/dataset?${params}`);
    if(!response.ok) throw Error();
    const meta=await response.json();
    if(token!==metadataToken) return;
    $('research-method').innerHTML=sourceMethodHTML(meta,esc);
    const active=meta.active_selection;
    if(active) $('research-coverage').textContent=`${active.competition} ${active.season} · ${active.included_matches}/${active.expected_matches} fixtures included · ${active.player_count} player-season profiles. OpenPlay preview; no live 2026/27 feed.`;
  } catch {
    if(token===metadataToken) $('research-method').textContent='Source details could not be loaded. Check the local service and refresh.';
  }
}
$('research-competition').addEventListener('change',loadResearchMetadata);
$('research-season').addEventListener('change',loadResearchMetadata);
loadResearchMetadata();
