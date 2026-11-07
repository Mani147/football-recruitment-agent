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
