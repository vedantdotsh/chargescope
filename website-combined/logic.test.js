const assert = require('node:assert/strict');
const fs = require('node:fs');
const vm = require('node:vm');
const logic = require('./logic.js');
const context = { window: {} };
vm.runInNewContext(fs.readFileSync(__dirname + '/data.js', 'utf8'), context);
const districts = context.window.COMBINED_DATA.districts;
assert.equal(districts.length, 18);
const near = (actual, expected) => assert.ok(Math.abs(actual - expected) < 1e-10, actual + ' != ' + expected);
const registered = logic.distribution(districts, false);
near(registered.q1, 15.647459288594);
near(registered.median, 18.299526705810);
near(registered.q3, 21.469883377948);
near(registered.low, 9.874302794160817);
near(registered.high, 24.821689090614363);
assert.equal(registered.outliers.length, 1);
near(registered.outliers[0], districts.find(item => item.code === '12067').registered.rate);
for (const excluded of [false, true]) {
  const scenario = excluded ? 'hypothetical' : 'registered';
  const rates = districts.map(item => item[scenario].points / item[scenario].population * 10000).sort((first, second) => first - second);
  const result = logic.distribution(districts, excluded);
  near(result.q1, rates[4] * .75 + rates[5] * .25);
  near(result.median, (rates[8] + rates[9]) / 2);
  near(result.q3, rates[12] * .25 + rates[13] * .75);
  const inliers = rates.filter(value => value >= result.q1 - 1.5 * (result.q3 - result.q1) && value <= result.q3 + 1.5 * (result.q3 - result.q1));
  near(result.low, inliers[0]); near(result.high, inliers.at(-1));
  const total = logic.totals(districts, excluded);
  near(total.rate, districts.reduce((sum, item) => sum + item[scenario].points, 0) / districts.reduce((sum, item) => sum + item[scenario].population, 0) * 10000);
  assert.equal(total.points, excluded ? 4491 : 5004);
  near(total.kw, excluded ? 272812 : 278455);
  assert.equal(total.installations, excluded ? 2519 : 3032);
  for (const item of districts) {
    near(item[scenario].rate, item[scenario].points / item[scenario].population * 10000);
    assert.equal(item.registered.population, item.hypothetical.population);
    for (const metric of ['rate', 'points', 'kw']) assert.equal(logic.rank(districts, item, metric, excluded), 1 + districts.filter(other => other[scenario][metric] > item[scenario][metric]).length);
  }
}
const tied = [10, 10, 5].map(points => ({ registered: { points } }));
assert.equal(logic.rank(tied, tied[0], 'points', false), 1);
assert.equal(logic.rank(tied, tied[1], 'points', false), 1);
assert.equal(logic.rank(tied, tied[2], 'points', false), 3);
assert.ok(!districts.some(item => item.code === '11000'));
const script = fs.readFileSync(__dirname + '/app.js', 'utf8');
const dictionaryStart = script.indexOf('  const copy = {');
const dictionaryEnd = script.indexOf('  const text =', dictionaryStart);
const dictionary = vm.runInNewContext(script.slice(dictionaryStart, dictionaryEnd).replace('const copy =', 'globalThis.dictionary =') + '; dictionary');
assert.deepEqual(Object.keys(dictionary.en).sort(), Object.keys(dictionary.de).sort());
assert.ok(Object.values(dictionary.de).every(value => typeof value === 'string' && value.length > 0));
console.log('PASS: pinned type-7 quartiles, both distributions, fences, all 18 rates/ranks, ties, ratio-of-sums, MW totals and Berlin exclusion');
