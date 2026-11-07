'use strict';
const $ = id=>document.getElementById(id);
const esc = value=>String(value??'').replace(/[&<>"']/g,c=>({'&':'&amp;','<':'&lt;','>':'&gt;','"':'&quot;',"'":'&#39;'}[c]));
let results=null;
function showProfile() {
  const row=results?.candidates.find(r=>r.player.id===$('research-player').value);
  if (!row) return;
  const p=row.player;
  const axes=realRadarMetrics(results.metrics);
  const measured=axes.filter(([key])=>Number.isFinite(row.league_adjusted_percentiles[key]));
  $('research-detail').innerHTML=`<p class="eyebrow">HISTORICAL PLAYER PROFILE</p><h2>${esc(p.name)}</h2><p>${esc(p.club)} · Premier League 2015/16 · ${esc([p.primary_position,...p.secondary_positions].join(' / '))}</p><p>${esc(row.sample_note)}</p><p><strong>Role alignment: ${row.profile_score}/100</strong> across ${row.scored_metric_count} measured axes. This target-match heuristic is not an overall quality score or transfer forecast.</p>${measured.length>=3?renderRadar(row,{target_percentiles:results.profile.target_percentiles},null,measured):'<p>Fewer than three measured axes; radar unavailable.</p>'}<p class="hint">Omitted axes: ${esc(axes.filter(m=>!measured.includes(m)).map(m=>m[1]).join(', ')||'none')}. Missing values are excluded, not scored as zero.</p><a class="secondary" href="/compare">Compare this position group with other players →</a>`;
}
$('research-player').addEventListener('change',showProfile);
$('research-form').addEventListener('submit',async event=>{
  event.preventDefault();
  $('research-submit').disabled=true;
  $('research-error').hidden=true;
  $('research-results').hidden=true;
  $('research-status').textContent='Checking the historical position cohort…';
  try {
    const response=await fetch('/api/scout/search',{method:'POST',headers:{'Content-Type':'application/json'},body:JSON.stringify({objective:$('research-objective').value.trim(),min_minutes:Number($('research-minutes').value)})});
    const data=await response.json();
    if(!response.ok) throw Error(data.detail || 'The search could not be processed.');
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
fetch('/api/dataset').then(r=>{if(!r.ok)throw Error();return r.json();}).then(meta=>{
  $('research-method').innerHTML=`<p>${esc(meta.percentile_method)}</p><p>${esc(meta.minutes_definition)}</p><ul>${meta.limitations.map(v=>`<li>${esc(v)}</li>`).join('')}</ul><dl>${Object.entries(meta.metric_definitions).map(([key,value])=>`<dt><strong>${esc(key)}</strong></dt><dd>${esc(value)}</dd>`).join('')}</dl><p>Upstream revision: <a href="${esc(meta.source_url)}">${esc(meta.upstream_revision)}</a></p>`;
}).catch(()=>{$('research-method').textContent='Source details could not be loaded. Check the local service and refresh.';});
