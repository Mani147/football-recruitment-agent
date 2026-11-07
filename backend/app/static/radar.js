// Eight existing percentile dimensions. No new or inferred player statistics.
const RADAR_METRICS = [
  ['progressive_passes', 'Progressive passing', ['Progressive', 'passing']],
  ['progressive_carries', 'Progressive carries', ['Progressive', 'carries']],
  ['tackles_interceptions', 'Tackles & interceptions', ['Tackles &', 'interceptions']],
  ['ball_recoveries_pressures', 'Pressures & recoveries', ['Pressures &', 'recoveries']],
  ['aerial_dominance', 'Aerial dominance', ['Aerial', 'dominance']],
  ['chance_creation_xa', 'Chance creation (xA)', ['Chance creation', '(xA)']],
  ['possession_retention', 'Possession retention', ['Possession', 'retention']],
  ['goal_threat_xg', 'Goal threat (xG)', ['Goal threat', '(xG)']],
  ['save_pct','Save percentage',['Save','percentage']],
  ['keeper_claims_per90','Collections / 90',['Collections','/ 90']],
  ['keeper_sweeps_per90','Sweeper actions / 90',['Sweeper actions','/ 90']],
];
function realRadarMetrics(keys) {
  return keys.map(key => {
    if (key === 'possession_retention') return [key,'Pass completion',['Pass','completion']];
    if (key === 'aerial_dominance') return [key,'Aerial win percentage',['Aerial win','percentage']];
    return RADAR_METRICS.find(metric=>metric[0]===key);
  });
}
function renderRadar(candidate, profile = null, comparison = null, metrics = RADAR_METRICS.slice(0,8)) {
  const esc = value => String(value ?? '').replace(/[&<>"']/g, c => ({'&':'&amp;', '<':'&lt;', '>':'&gt;', '"':'&quot;', "'":'&#39;'}[c]));
  const real = candidate.data_mode === 'statsbomb';
  const values = source => metrics.map(([key]) => source?.[key]);
  const player = values(candidate.league_adjusted_percentiles);
  const target = profile ? values(profile.target_percentiles) : null;
  const other = comparison ? values(comparison.league_adjusted_percentiles) : null;
  if ([...player, ...(target || []), ...(other || [])].some(v => typeof v !== 'number' || !Number.isFinite(v) || v < 0 || v > 100)) {
    return '<p class="radar-unavailable">The percentile chart is unavailable because some values are missing or outside 0–100. Check the detailed evidence below.</p>';
  }
  const point = (index, value, radius = 180) => {
    const angle = -Math.PI / 2 + index * Math.PI * 2 / metrics.length;
    return [320 + Math.cos(angle) * radius * value / 100, 280 + Math.sin(angle) * radius * value / 100];
  };
  const coordinates = series => series.map((v,i) => point(i,v).map(x => x.toFixed(2)).join(',')).join(' ');
  const rings = [20,40,60,80,100].map(v => `<polygon class="radar-ring" points="${coordinates(Array(metrics.length).fill(v))}"/><text class="radar-tick" x="326" y="${280-180*v/100-4}">${v}</text>`).join('');
  const axes = metrics.map(([,label,lines],i) => {
    const [x,y] = point(i,100), [lx,ly] = point(i,100,228);
    const anchor = lx < 300 ? 'end' : lx > 340 ? 'start' : 'middle';
    return `<line class="radar-axis" x1="320" y1="280" x2="${x}" y2="${y}"/><text class="radar-label" text-anchor="${anchor}" x="${lx}" y="${ly-5}"><tspan x="${lx}">${esc(lines[0])}</tspan><tspan x="${lx}" dy="17">${esc(lines[1])}</tspan></text>`;
  }).join('');
  const dots = player.map((v,i) => { const [x,y] = point(i,v); return `<circle class="radar-point" cx="${x}" cy="${y}" r="4"><title>${esc(metrics[i][1])}: ${v}${target ? `; role target: ${target[i]}` : ''}</title></circle>`; }).join('');
  return `<figure class="radar-figure"><svg class="radar-chart" viewBox="0 0 640 560" role="img" aria-labelledby="radar-title radar-description"><title id="radar-title">${esc(candidate.player.name)} — percentile strengths</title><desc id="radar-description">${metrics.length} ${real ? 'position-cohort' : 'league-adjusted'} percentile axes, from 0 at the center to 100 at the outer edge. Solid green shows ${esc(candidate.player.name)}${target ? '; dashed amber shows the recruitment role targets.' : '.'}${comparison ? ` Blue shows ${esc(comparison.player.name)}.` : ''} Exact values follow in a table.</desc>${rings}${axes}${target ? `<polygon class="radar-target" points="${coordinates(target)}"/>` : ''}${other ? `<polygon class="radar-comparison" points="${coordinates(other)}"/>` : ''}<polygon class="radar-player" points="${coordinates(player)}"/>${dots}</svg><figcaption><div class="radar-legend"><span><i class="legend-player"></i>${esc(candidate.player.name)}</span>${target ? '<span><i class="legend-target"></i>Role target</span>' : ''}${comparison ? `<span><i class="legend-comparison"></i>${esc(comparison.player.name)}</span>` : ''}</div><p>Farther from the center means a higher percentile in that area. Shape shows a profile of strengths, not overall quality; ${real ? 'percentiles are calculated from the 2015/16 position cohort, without a league multiplier.' : 'these are illustrative, league-adjusted benchmarks.'}</p></figcaption></figure><details class="radar-values"><summary>View exact percentiles</summary><div class="radar-table-scroll"><table><caption class="sr-only">Percentiles by metric, on a scale of 0 to 100</caption><thead><tr><th scope="col">Area</th><th scope="col">${esc(candidate.player.name)}</th>${target ? '<th scope="col">Target</th>' : ''}${comparison ? `<th scope="col">${esc(comparison.player.name)}</th>` : ''}</tr></thead><tbody>${metrics.map(([,label],i) => `<tr><th scope="row">${esc(label)}</th><td>${player[i]}</td>${target ? `<td>${target[i]}</td>` : ''}${other ? `<td>${other[i]}</td>` : ''}</tr>`).join('')}</tbody></table></div></details>`;
}
