const assert = require('node:assert/strict');
const fs = require('node:fs');
const test = require('node:test');

test('USA panel defines the sport selector and shared inner tabs', () => {
  const source = fs.readFileSync('custom_components/usa_sports_hub/frontend/usa-sports-hub-panel-v2.js', 'utf8');
  for (const value of ['NFL', 'NBA', 'MLB', 'NHL', 'MLS', 'More Sports', 'Overview', 'Standings', 'My Team']) {
    assert.match(source, new RegExp(value));
  }
  assert.doesNotMatch(source, /Last Man Standing|Acca League/);
});
