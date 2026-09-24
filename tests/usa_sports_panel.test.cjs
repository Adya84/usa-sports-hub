const assert = require('node:assert/strict');
const fs = require('node:fs');
const test = require('node:test');

test('USA panel defines the sport selector and shared inner tabs', () => {
  const source = fs.readFileSync('custom_components/usa_sports_hub/frontend/usa-sports-hub-panel.js', 'utf8');
  for (const value of ['NFL', 'NBA', 'MLB', 'NHL', 'Overview', 'Standings', 'My Team', 'background-nfl.png', 'background-nba.png', 'background-mlb.png', 'background-nhl.png', 'KEEP US IN PLAY', 'UP TO DATE', 'COUNTRY', 'LEAGUE', 'TEAM', 'data-country', 'data-team', 'sensor.usa_sports_hub_', 'fixtures', 'results', 'standings', 'news', 'LIVE UPDATE', 'NOW PLAYING']) {
    assert.match(source, new RegExp(value));
  }
  assert.doesNotMatch(source, /Last Man Standing|Acca League/);
});

test('MLB selected game keeps matching detail instead of hiding it behind verification state', () => {
  const source = fs.readFileSync('custom_components/usa_sports_hub/frontend/usa-sports-hub-panel.js', 'utf8');
  assert.doesNotMatch(source, /if\(!verified\)\{[\s\S]{0,250}\[name\]:empty/);
  assert.match(source, /if\(!detailMatches\)\{[\s\S]{0,250}\[name\]:empty/);
});

test('MLB provider replaces generic play records with the official selected-game feed', () => {
  const source = fs.readFileSync('custom_components/usa_sports_hub/providers/ts.py', 'utf8');
  const officialFeed = source.indexOf('if mlb_live_data:');
  const replacement = source.indexOf('detail["play_by_play"] = converted');
  assert.ok(officialFeed >= 0 && replacement > officialFeed);
});

test('game selection identifies its sport without waiting for a full refresh', () => {
  const source = fs.readFileSync('custom_components/usa_sports_hub/frontend/usa-sports-hub-panel.js', 'utf8');
  assert.match(source, /select_live_match',\{fixture_id:this\.selectedLiveGame,sport:this\.sport\}/);
});

test('game centre retains an in-panel snapshot for previously opened games', () => {
  const source = fs.readFileSync('custom_components/usa_sports_hub/frontend/usa-sports-hub-panel.js', 'utf8');
  assert.match(source, /this\._gameDetailCache/);
  assert.match(source, /this\._gameDetailCache\.set\(activeDetailId/);
  assert.match(source, /this\._gameDetailCache\.get\(selectedGameId\)/);
  assert.match(source, /Loading game data — this can take up to 30 seconds/);
});

test('My Team uses dedicated team sensors and saved favourite controls', () => {
  const source = fs.readFileSync('custom_components/usa_sports_hub/frontend/usa-sports-hub-panel.js', 'utf8');
  for (const value of ['team_profile', 'team_squad', 'team_statistics', 'team_leaders', 'team_injuries', 'add_team_favourite', 'remove_team_favourite', 'MY TEAM · SEASON SNAPSHOT', 'MY SQUAD']) {
    assert.match(source, new RegExp(value));
  }
});
