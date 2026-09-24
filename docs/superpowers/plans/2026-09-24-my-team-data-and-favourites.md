# My Team Data and Favourites Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Build a persistent, Football Hub-styled My Team dashboard backed by team-scoped TS API data and up to three Home Assistant favourites.

**Architecture:** The TS provider gains a compact `async_team_detail(team_id)` operation. The USA coordinator owns a bounded per-sport/team cache and dedicated sensors. Service-backed favourites persist `{sport, team_id, team}` in config-entry options; the panel uses team sensors only for team content and game sensors only for a selected fixture.

**Tech Stack:** Home Assistant custom integration, Python 3.12, aiohttp, browser Web Component JavaScript, Node test runner, `unittest`.

**Spec:** `docs/superpowers/specs/2026-09-24-my-team-data-and-favourites-design.md`

## Global Constraints

- Support NFL, NBA, MLB and NHL only.
- Retain last successful data on provider errors and never render another team or game as fallback.
- Persist at most three favourites, each keyed by sport and stable team ID.
- Do not periodically fetch heavyweight `/{sport}/teams/{team_id}/events` responses.
- Keep full payloads out of Home Assistant recorder attributes.
- Maintain the existing selected-game cache independently of team data.
- Publish the completed change as a prerelease, not a stable release.

## Review Focus

- Missing team statistics must render an unavailable state without using game statistics; Task 4 panel test.
- Adding a fourth favourite must leave the original three intact; Task 2 coordinator test.
- Same display names in separate sports must have separate caches; Task 2 coordinator test.
- A team endpoint failure after a successful refresh must retain prior roster/profile; Task 2 coordinator test.
- Selecting a live game must not change My Team squad or leaders; Task 4 panel test.

---

### Task 1: Normalize team-scoped TS data

**Files:**

- Modify: `custom_components/usa_sports_hub/providers/ts.py`
- Modify: `tests/test_usa_providers.py`

**Interfaces:**

- Consumes: `ProviderClient.async_get_json(url)` and a provider `league`.
- Produces: `TSProvider.async_team_detail(team_id: str | int) -> dict[str, object]` with `profile`, `squad`, `statistics`, `leaders` and `injuries`.

- [ ] **Step 1: Write the failing provider tests**

```python
def test_team_detail_normalizes_profile_and_squad(self):
    detail = normalize_team_detail(
        "mlb", {"id": 11, "full_name": "Los Angeles Angels", "standing": {"short_record": "60-98"}},
        [{"id": 7, "full_name": "Player One", "number": 9, "position_abbreviation": "OF", "headshots": {"small": "player.png"}}],
        [{"name": "Runs", "value": 4}], [{"name": "Top hitter", "value": "Player One"}], []
    )
    self.assertEqual(detail["profile"]["team_id"], "11")
    self.assertEqual(detail["squad"][0]["headshot"], "player.png")
```

Add a second test with object-shaped NBA statistics/leaders and `None` injuries, asserting empty lists rather than exceptions.

- [ ] **Step 2: Run the test to verify it fails**

Run: `python -m unittest tests.test_usa_providers -v`

Expected: FAIL because `normalize_team_detail` is not defined.

- [ ] **Step 3: Implement compact normalizers and API operation**

```python
def normalize_team_detail(league, profile, squad, statistics, leaders, injuries):
    profile = profile if isinstance(profile, dict) else {}
    return {
        "profile": {"team_id": str(profile.get("id") or ""), "name": profile.get("full_name") or profile.get("name") or "Team", "logo": _logo(profile), "standing": profile.get("standing") or {}, "extra": profile.get("team_extra_info") or []},
        "squad": [_compact_team_player(player) for player in squad if isinstance(player, dict)],
        "statistics": _list_or_empty(statistics),
        "leaders": _list_or_empty(leaders),
        "injuries": _list_or_empty(injuries),
    }
```

Implement `async_team_detail` with `asyncio.gather(..., return_exceptions=True)` for profile, players, statistics, leaders and injuries endpoints. Treat failed optional endpoints as empty; a failed profile request raises `ProviderError`.

- [ ] **Step 4: Run provider tests and syntax check**

Run: `python -m unittest tests.test_usa_providers -v; python -m compileall -q custom_components/usa_sports_hub/providers`

Expected: PASS.

- [ ] **Step 5: Commit**

```powershell
git add custom_components/usa_sports_hub/providers/ts.py tests/test_usa_providers.py
git commit -m "Add compact team data provider"
```

### Task 2: Add per-team cache and persistent favourites

**Files:**

- Modify: `custom_components/usa_sports_hub/coordinator.py`
- Modify: `custom_components/usa_sports_hub/__init__.py`
- Create: `tests/test_usa_team_coordinator.py`

**Interfaces:**

- Consumes: `TSProvider.async_team_detail(team_id)` and option `team_favourites`.
- Produces: `async_add_team_favourite(sport, team_id, team)`, `async_remove_team_favourite(sport, team_id)`, `async_select_team(sport, team_id)`, and `team_details[team_id]`.

- [ ] **Step 1: Write failing cache and favourite tests**

```python
def test_favourites_are_limited_and_keyed_by_sport_and_id(self):
    coordinator = make_coordinator(options={})
    coordinator._add_favourite_record("nfl", "1", "Bills")
    coordinator._add_favourite_record("nba", "1", "Celtics")
    coordinator._add_favourite_record("mlb", "11", "Angels")
    with self.assertRaisesRegex(ValueError, "maximum of three"):
        coordinator._add_favourite_record("nhl", "1", "Bruins")
    self.assertEqual(len(coordinator.team_favourites), 3)
```

Add tests proving NFL `team_details["1"]` cannot be read by NBA and that a provider error retains the prior team entry.

- [ ] **Step 2: Run tests to verify failure**

Run: `python -m unittest tests.test_usa_team_coordinator -v`

Expected: FAIL because no team favourite/cache API exists.

- [ ] **Step 3: Implement cache ownership and option persistence**

```python
def _team_cache_key(self, sport, team_id):
    if sport not in SPORTS or not str(team_id).strip():
        raise ValueError("Supported sport and team ID are required")
    return sport, str(team_id)

async def async_add_team_favourite(self, sport, team_id, team):
    key = self._team_cache_key(sport, team_id)
    if key not in {(x["sport"], x["team_id"]) for x in self.team_favourites} and len(self.team_favourites) >= 3:
        raise ValueError("A maximum of three favourite teams is supported")
```

Persist team records in entry options. Add `team_details` per sport to storage restoration/save. Publish cache immediately on selection; refresh selected team in background. Refresh at most one stale favourite per ordinary cycle. Removing a favourite deletes only its sport/team cache. Register `add_team_favourite`, `remove_team_favourite` and `select_team` services.

- [ ] **Step 4: Run coordinator and identity tests**

Run: `python -m unittest tests.test_usa_team_coordinator tests.test_integration_identity -v; python -m compileall -q custom_components/usa_sports_hub`

Expected: PASS.

- [ ] **Step 5: Commit**

```powershell
git add custom_components/usa_sports_hub/coordinator.py custom_components/usa_sports_hub/__init__.py tests/test_usa_team_coordinator.py
git commit -m "Cache team data and persist favourites"
```

### Task 3: Expose team data through dedicated sensors

**Files:**

- Modify: `custom_components/usa_sports_hub/sensors/usa_sports.py`
- Modify: `custom_components/usa_sports_hub/coordinator.py`
- Modify: `tests/test_integration_identity.py`

**Interfaces:**

- Consumes: `sports[sport]["team_details"]` and the selected team ID.
- Produces: `team_profile`, `team_squad`, `team_statistics`, `team_leaders`, `team_injuries` sensor sections.

- [ ] **Step 1: Write failing sensor-section test**

```python
def test_team_sections_are_detailed_and_unrecorded(self):
    source = Path("custom_components/usa_sports_hub/sensors/usa_sports.py").read_text()
    for section in ("team_profile", "team_squad", "team_statistics", "team_leaders", "team_injuries"):
        self.assertIn(f'"{section}"', source)
    self.assertIn("_unrecorded_attributes", source)
```

- [ ] **Step 2: Run the test to verify failure**

Run: `python -m unittest tests.test_integration_identity -v`

Expected: FAIL because team sensor sections are absent.

- [ ] **Step 3: Add sensor sections and composed output**

Extend `SECTIONS` and `DETAIL_KEYS`. In `_compose_data`, publish only the active team cache entry for the sport; publish empty containers if no team is selected. Add only compact `sport`, `team_id`, `team`, `updated` and `error` values to status.

- [ ] **Step 4: Run tests**

Run: `python -m unittest tests.test_integration_identity -v; python -m compileall -q custom_components/usa_sports_hub`

Expected: PASS.

- [ ] **Step 5: Commit**

```powershell
git add custom_components/usa_sports_hub/sensors/usa_sports.py custom_components/usa_sports_hub/coordinator.py tests/test_integration_identity.py
git commit -m "Expose team data sensors"
```

### Task 4: Build My Team page and favourite controls

**Files:**

- Modify: `custom_components/usa_sports_hub/frontend/usa-sports-hub-panel.js`
- Modify: `tests/usa_sports_panel.test.cjs`

**Interfaces:**

- Consumes: five `sensor.usa_sports_hub_{sport}_team_*` attributes, existing schedule sensors, and team-favourite services.
- Produces: scoped My Team cards and Football Hub-style favourite controls.

- [ ] **Step 1: Write failing panel contract tests**

```javascript
test('My Team consumes team-scoped sensors and favourite controls', () => {
  const source = fs.readFileSync('custom_components/usa_sports_hub/frontend/usa-sports-hub-panel.js', 'utf8');
  for (const name of ['team_profile', 'team_squad', 'team_statistics', 'team_leaders', 'team_injuries', 'add_team_favourite', 'remove_team_favourite']) {
    assert.match(source, new RegExp(name));
  }
  assert.match(source, /MY TEAM · SEASON SNAPSHOT/);
  assert.match(source, /favourites.length.*3/);
});
```

Add an assertion that My Team rendering does not source `players`, `lineups`, `statistics` or `leaders` from selected-game data.

- [ ] **Step 2: Run panel tests to verify failure**

Run: `node --test tests/usa_sports_panel.test.cjs`

Expected: FAIL because team-scoped controls are absent.

- [ ] **Step 3: Implement scoped rendering and interaction**

```javascript
const teamData = section => sensor(`team_${section}`)?.attributes?.[`team_${section}`] || (section === 'profile' ? {} : []);
const profile = teamData('profile');
const squad = teamData('squad');
const scopedGames = [...live, ...fixtures, ...results].filter(game => game.home_team_id === profile.team_id || game.away_team_id === profile.team_id);
```

Render club masthead; `0/3` favourites counter and chips; live/next game; season snapshot; recent/next schedule; squad; leaders; stats; injuries; and a correctly scoped news empty state. Team selection uses stable team ID. Add/remove controls call the new services and rerender. Add Football Hub-style title bars, dark cards, cyan outlines and glow, USA red live states and sport-background inheritance.

- [ ] **Step 4: Run frontend checks**

Run: `node --check custom_components/usa_sports_hub/frontend/usa-sports-hub-panel.js; node --test tests/usa_sports_panel.test.cjs`

Expected: PASS.

- [ ] **Step 5: Commit**

```powershell
git add custom_components/usa_sports_hub/frontend/usa-sports-hub-panel.js tests/usa_sports_panel.test.cjs
git commit -m "Build Football Hub styled My Team page"
```

### Task 5: Document, verify and publish the beta

**Files:**

- Modify: `README.md`
- Modify: `custom_components/usa_sports_hub/__init__.py`
- Modify: `custom_components/usa_sports_hub/manifest.json`

**Interfaces:**

- Consumes: completed provider, coordinator, sensor and panel features.
- Produces: release documentation and prerelease version `0.0.4-beta.32`.

- [ ] **Step 1: Update documentation**

Document My Team, three persistent favourites, team sensors, cached background refresh and sport-dependent optional data.

- [ ] **Step 2: Bump prerelease version**

Set `PANEL_VERSION` and manifest version to `0.0.4-beta.32`, retaining cache-busting module URL behavior.

- [ ] **Step 3: Run full verification**

Run: `python -m unittest tests.test_integration_identity tests.test_usa_providers tests.test_usa_team_coordinator -v; python -m compileall -q custom_components/usa_sports_hub; node --check custom_components/usa_sports_hub/frontend/usa-sports-hub-panel.js; node --test tests/usa_sports_panel.test.cjs; git diff --check`

Expected: all commands exit 0.

- [ ] **Step 4: Commit, push and publish**

```powershell
git add README.md custom_components/usa_sports_hub/__init__.py custom_components/usa_sports_hub/manifest.json
git commit -m "Release USA Sports Hub v0.0.4-beta.32"
git push origin HEAD:main
gh release create v0.0.4-beta.32 --prerelease --title "USA Sports Hub v0.0.4-beta.32" --notes "Adds the persistent My Team dashboard, up to three saved favourites, dedicated team sensors, squad and team-stat views." --target main
```

## Self-review

- Spec coverage: provider data, cache, favourites, dedicated sensors, dashboard, style, errors, tests and beta publishing are covered by Tasks 1-5.
- Placeholder scan: every task includes concrete interfaces, commands and implementation behavior.
- Type consistency: `team_profile`, `team_squad`, `team_statistics`, `team_leaders`, `team_injuries`, `team_favourites` and `(sport, team_id)` are consistent throughout.
- Review focus coverage: optional stats (Task 4), max-three validation (Task 2), sport isolation (Task 2), failure retention (Task 2) and selected-game leakage (Task 4) are explicitly tested.

