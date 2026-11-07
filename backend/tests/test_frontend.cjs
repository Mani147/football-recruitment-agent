const test = require('node:test');
const assert = require('node:assert/strict');
const fs = require('node:fs');
const path = require('node:path');
const vm = require('node:vm');

function appWithFetch(fetch) {
  const context = vm.createContext({
    fetch,
    document: {
      getElementById: () => ({addEventListener() {}}),
      querySelectorAll: () => [],
    },
    window: {addEventListener() {}},
  });
  vm.runInContext(fs.readFileSync(path.join(__dirname, '../app/static/app.js'), 'utf8'), context);
  return () => vm.runInContext('postJSON("/api/scout/profile", {})', context);
}

function radarContext() {
  const context = vm.createContext({});
  vm.runInContext(fs.readFileSync(path.join(__dirname, '../app/static/radar.js'), 'utf8'), context);
  vm.runInContext(`
    const percentiles = Object.fromEntries(RADAR_METRICS.map(([key],i) => [key, i*10]));
    const candidate = {player:{name:'Player <one>'},league_adjusted_percentiles:percentiles};
    const profile = {target_percentiles:Object.fromEntries(RADAR_METRICS.map(([key]) => [key,75]))};
  `, context);
  return context;
}

test('position comparison radar supports fewer axes and does not invent a role target', () => {
  const context = radarContext();
  const html = vm.runInContext('renderRadar(candidate,null,candidate,RADAR_METRICS.slice(0,3))',context);
  assert.equal((html.match(/class="radar-point"/g)||[]).length,3);
  assert.equal((html.match(/scope="row"/g)||[]).length,3);
  assert.doesNotMatch(html,/class="radar-target"|Role target|<th scope="col">Target/);
  assert.match(html,/3 league-adjusted percentile axes/);
});

test('comparison selection stays within the position pool and never compares a player to themselves', () => {
  const context = vm.createContext({document:{getElementById:()=>({addEventListener(){}})},
    fetch:()=>new Promise(()=>{}),window:{}, URLSearchParams});
  vm.runInContext(fs.readFileSync(path.join(__dirname,'../app/static/compare.js'),'utf8'),context);
  const result = vm.runInContext(`matchingSelection([{player:{id:'a'}},{player:{id:'b'}}],'b','b').map(r=>r.player.id)`,context);
  assert.deepEqual(Array.from(result),['b','a']);
  assert.equal(vm.runInContext(`matchingSelection([{player:{id:'a'}}],'missing','a')[1]`,context),undefined);
  assert.equal(vm.runInContext(`matchingSelection([],'','')[0]`,context),undefined);
});

test('real season comparison preserves unknown money and omits unavailable chart axes', () => {
  const nodes=new Map();
  const node=id=>{
    if(!nodes.has(id)) nodes.set(id,{value:'',options:[],addEventListener(){},querySelector(){return null;}});
    return nodes.get(id);
  };
  const context=vm.createContext({document:{getElementById:node},fetch:()=>new Promise(()=>{}),URLSearchParams});
  for(const file of ['radar.js','compare.js']) vm.runInContext(fs.readFileSync(path.join(__dirname,'../app/static',file),'utf8'),context);
  vm.runInContext(`
    const metricKeys=['progressive_passes','progressive_carries','chance_creation_xa','possession_retention'];
    const row={data_mode:'statsbomb',player:{id:'a',name:'Real profile',club:'Historical club',league:'Premier League',
      primary_position:'CM',secondary_positions:[],age:null,preferred_foot:null,market_value_eur:null,weekly_wage_eur:null,raw_metrics:{minutes_played:1000},counts:{}},
      sample_note:'1000 minutes',league_adjusted_percentiles:{progressive_passes:75,progressive_carries:80,chance_creation_xa:70,possession_retention:null}};
    comparisonData={group:'midfielders',data_mode:'statsbomb',players:[row],groups:{midfielders:{metrics:metricKeys,label:'Midfielders'}}};
    renderComparison();
  `,context);
  assert.match(node('comparison-cards').innerHTML,/Not available/);
  assert.match(node('comparison-cards').innerHTML,/Not recorded/);
  assert.doesNotMatch(node('comparison-cards').innerHTML,/€0|undefined\/100/);
  assert.match(node('comparison-radar').innerHTML,/Unavailable axes omitted: Pass completion/);
  assert.match(node('comparison-radar').innerHTML,/3 position-cohort percentile axes/);
  assert.equal(node('player-two').disabled,true);
});

test('historical search sends performance constraints without fabricated finance or age fields', async () => {
  const nodes=new Map(), requests=[];
  const node=id=>{
    if(!nodes.has(id)) nodes.set(id,{value:'',addEventListener(k,fn){this[k]=fn;}});
    return nodes.get(id);
  };
  node('research-objective').value='Find a CM';node('research-minutes').value='900';
  const context=vm.createContext({document:{getElementById:node},fetch:async(url,options)=>{
    if(url==='/api/dataset') return {ok:true,json:async()=>({percentile_method:'Measured',minutes_definition:'Regulation',limitations:[],metric_definitions:{}})};
    requests.push(JSON.parse(options.body));
    return {ok:true,json:async()=>({status:'no_matches',candidates:[]})};
  }});
  vm.runInContext(fs.readFileSync(path.join(__dirname,'../app/static/research.js'),'utf8'),context);
  await node('research-form').submit({preventDefault(){}});
  assert.deepEqual(requests,[{objective:'Find a CM',min_minutes:900}]);
  assert.equal(node('research-submit').disabled,false);
});

test('radar maps all eight actual metrics to the 0–100 scale and provides exact values', () => {
  const html = vm.runInContext('renderRadar(candidate,profile)', radarContext());
  assert.match(html, /points="320.00,280.00/); // First metric is zero, at center.
  assert.equal((html.match(/class="radar-point"/g) || []).length, 8);
  assert.equal((html.match(/scope="row"/g) || []).length, 8);
  assert.match(html, /Player &lt;one&gt;/);
  assert.match(html, /aria-labelledby="radar-title radar-description"/);
  assert.match(html, /class="radar-target"/);
});

test('radar compares another player without inventing missing values', () => {
  const context = radarContext();
  assert.match(vm.runInContext('renderRadar(candidate,profile,candidate)',context), /class="radar-comparison"/);
  vm.runInContext('candidate.league_adjusted_percentiles.goal_threat_xg = null',context);
  const html = vm.runInContext('renderRadar(candidate,profile)',context);
  assert.match(html, /unavailable/);
  assert.doesNotMatch(html, /<svg/);
});

function themeContext(saved, darkSystem, blockedStorage = false) {
  const handlers = {}, attributes = {};
  const root = {dataset:{}};
  const button = {setAttribute:(k,v) => attributes[k]=v, addEventListener:(k,v) => handlers[k]=v};
  const media = {matches:darkSystem,addEventListener:(k,v) => handlers.system=v};
  const storage = {getItem:() => {if(blockedStorage) throw Error(); return saved;}, setItem:(k,v) => {if(blockedStorage) throw Error(); saved=v;}};
  const context = vm.createContext({document:{documentElement:root,getElementById:() => button,
    addEventListener:(k,v) => handlers.ready=v},window:{matchMedia:() => media},localStorage:storage});
  vm.runInContext(fs.readFileSync(path.join(__dirname, '../app/static/theme.js'),'utf8'),context);
  handlers.ready();
  return {root,button,handlers,attributes,saved:() => saved};
}

test('theme follows system initially, persists a manual choice, and restores it on reload', () => {
  const t = themeContext(null,true);
  assert.equal(t.root.dataset.theme,'dark');
  t.handlers.click();
  assert.equal(t.root.dataset.theme,'light');
  assert.equal(t.attributes['aria-pressed'],'false');
  assert.equal(t.saved(),'light');
  t.handlers.system({matches:true});
  assert.equal(t.root.dataset.theme,'light');
  assert.equal(themeContext(t.saved(),true).root.dataset.theme,'light');
});

test('theme remains usable with blocked storage and follows later system changes until overridden', () => {
  const t = themeContext(null,false,true);
  t.handlers.system({matches:true});
  assert.equal(t.root.dataset.theme,'dark');
  t.handlers.click();
  assert.equal(t.root.dataset.theme,'light');
});

test('selected-player details render the radar and the comparison control updates its overlay', () => {
  const nodes = new Map();
  const node = id => {
    if (!nodes.has(id)) nodes.set(id,{innerHTML:'',children:[],addEventListener(k,fn){this[k]=fn;}});
    return nodes.get(id);
  };
  const context = vm.createContext({document:{getElementById:node,querySelectorAll:() => []},window:{addEventListener(){}}});
  for (const file of ['radar.js','app.js']) {
    vm.runInContext(fs.readFileSync(path.join(__dirname,'../app/static',file),'utf8'),context);
  }
  vm.runInContext(`
    const pct = Object.fromEntries(RADAR_METRICS.map(([key]) => [key,75]));
    function candidate(id,name) {return {
      player:{id,name,club:'Club',league:'League',age:23,preferred_foot:'Left',primary_position:'DM',
        secondary_positions:[],raw_metrics:{minutes_played:1800},market_value_eur:20000000,weekly_wage_eur:50000},
      rank:1,fit_score:80,reliability_score:90,estimated_annual_cost_eur:6600000,
      league_adjusted_percentiles:pct,tactical_breakdown:[],why_recommended:[],risk_factors:[]
    };}
    currentDossier = {top_candidates:[candidate('a','Alpha'),candidate('b','Bravo')],
      verifications:[],impact_simulations:[],recruitment_profile:{target_percentiles:pct}};
    selectCandidate(0);
  `,context);
  assert.match(node('candidate-detail').innerHTML,/See the shape of their game/);
  assert.match(node('candidate-detail').innerHTML,/Alpha — percentile strengths/);
  node('radar-compare').change({target:{value:'b'}});
  assert.match(node('radar-content').innerHTML,/class="radar-comparison"/);
  assert.match(node('radar-content').innerHTML,/Bravo/);
  vm.runInContext('selectCandidate(1)',context);
  assert.match(node('candidate-detail').innerHTML,/Bravo — percentile strengths/);
  assert.doesNotMatch(node('candidate-detail').innerHTML,/class="radar-comparison"/);
});

test('an unreachable server shows actionable recovery guidance', async () => {
  const request = appWithFetch(async () => { throw new TypeError('Failed to fetch'); });
  await assert.rejects(request(), /Cannot reach the recruitment service.*restart the server.*Your brief has been kept/);
});

test('server validation errors remain visible rather than becoming connectivity errors', async () => {
  const request = appWithFetch(async () => ({ok:false, json:async () => ({detail:'Budgets must be in EUR.'})}));
  await assert.rejects(request(), /Budgets must be in EUR/);
});

test('successful requests still return the interpreted profile', async () => {
  const response = {profile:{position:'DM'}};
  const request = appWithFetch(async () => ({ok:true, json:async () => response}));
  assert.equal(await request(), response);
});
