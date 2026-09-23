# USA Sports Hub 0.0.1 Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Create a standalone Home Assistant USA Sports Hub by adapting the current Football Hub integration and preserving its panel/style system.

**Architecture:** Copy the user-owned Football Hub baseline into an isolated repository, rename the Home Assistant integration contract to `usa_sports_hub`, and adapt its existing JavaScript panel and assets. Keep its provider/coordinator seams for a later API-adapter phase, rather than selecting or embedding providers now.

**Tech Stack:** Home Assistant custom integration, Python, aiohttp, JavaScript Custom Elements with Shadow DOM, CSS.

**Spec:** `docs/superpowers/specs/2026-09-23-usa-sports-hub-design.md`

## Global Constraints

- Copy from `C:\Users\adria\Documents\Codex\2026-09-13\ca\work\football-hub`, never edit it.
- Retain the existing frontend panel, CSS style system, responsive behavior, and Home Assistant structure; do not introduce React/Vite.
- Target NFL, NBA, MLB, NHL, MLS, and More Sports.
- Use project-owned USA branding; do not copy league trademarks.
- Do not embed unverified APIs, credentials, or invented live data.
- Publish only after tests and GitHub authentication checks pass.

## Review Focus

- All domain, manifest, panel, service-route, and browser-storage identifiers use `usa_sports_hub`.
- The Football Hub source working tree stays unchanged.
- Home Assistant imports the new integration without a `football_hub` dependency.
- The copied panel retains its responsive style/layout while football labels/assets are replaced.
- The app clearly shows provider setup is pending rather than claiming live results.

---

### Task 1: Copy and isolate the Football Hub baseline

**Files:**
- Create: `custom_components/usa_sports_hub/**`
- Create: `www/usa-sports-hub-panel.js`
- Create: copied repository metadata excluding `.git` and generated caches
- Modify: `.gitignore`

**Interfaces:**
- Consumes: the current Football Hub source tree.
- Produces: isolated USA Sports Hub source with no shared Git state.

- [ ] **Step 1: Record the source state**

Run: `git -C C:\Users\adria\Documents\Codex\2026-09-13\ca\work\football-hub status --short`

Expected: only existing generated caches, if any.

- [ ] **Step 2: Copy the baseline excluding `.git` and `__pycache__`**

Use PowerShell `Copy-Item` to copy the source root’s tracked files into this workspace, excluding `.git`, `__pycache__`, and source planning artifacts. Rename `custom_components/football_hub` to `custom_components/usa_sports_hub` and `www/football-hub-panel.js` to `www/usa-sports-hub-panel.js`.

- [ ] **Step 3: Add generated-file rules**

```gitignore
__pycache__/
*.py[cod]
.storage/
```

- [ ] **Step 4: Verify source isolation**

Run: `git -C C:\Users\adria\Documents\Codex\2026-09-13\ca\work\football-hub diff --exit-code`

Expected: exit code 0.

- [ ] **Step 5: Commit the isolated baseline**

```bash
git add .
git commit -m "chore: seed USA Sports Hub from Football Hub"
```

### Task 2: Rename the Home Assistant integration identity

**Files:**
- Modify: `custom_components/usa_sports_hub/manifest.json`
- Modify: `custom_components/usa_sports_hub/{const.py,__init__.py,config_flow.py,strings.json,services.yaml}`
- Modify: `custom_components/usa_sports_hub/translations/en.json`
- Test: `tests/test_integration_identity.py`

**Interfaces:**
- Consumes: copied integration source.
- Produces: `DOMAIN = "usa_sports_hub"`, `NAME = "USA Sports Hub"`, and a discoverable manifest.

- [ ] **Step 1: Write the failing identity test**

```python
from custom_components.usa_sports_hub.const import DOMAIN, NAME

def test_usa_sports_hub_identity():
    assert DOMAIN == "usa_sports_hub"
    assert NAME == "USA Sports Hub"
```

- [ ] **Step 2: Verify it fails**

Run: `python -m pytest tests/test_integration_identity.py -q`

Expected: FAIL before the renamed module exists.

- [ ] **Step 3: Rename identifiers and setup copy**

Set manifest `domain` and `name` to the new integration, update Python imports, configuration, translations, services, panel registration, and documentation links. Do not retain a runtime import from `football_hub`.

- [ ] **Step 4: Verify it passes**

Run: `python -m pytest tests/test_integration_identity.py -q`

Expected: PASS.

- [ ] **Step 5: Commit the identity change**

```bash
git add custom_components/usa_sports_hub tests/test_integration_identity.py
git commit -m "feat: establish USA Sports Hub identity"
```

### Task 3: Adapt the existing panel system for USA sports

**Files:**
- Create: `custom_components/usa_sports_hub/brand/usa-sports-hub-logo.svg`
- Create: `custom_components/usa_sports_hub/frontend/usa-sports-hub-background.svg`
- Modify: `custom_components/usa_sports_hub/frontend/usa-sports-hub-panel.js`
- Modify: `www/usa-sports-hub-panel.js`
- Test: `tests/usa-sports-hub-panel.test.cjs`

**Interfaces:**
- Consumes: renamed integration and the copied panel’s CSS/layout.
- Produces: `UsaSportsHubPanel` with USA branding and NFL/NBA/MLB/NHL/MLS/More Sports selectors.

- [ ] **Step 1: Write the failing panel contract test**

```js
test('panel provides the USA sports selector', () => {
  const source = readFileSync(panelPath, 'utf8');
  expect(source).toContain('USA Sports Hub');
  for (const sport of ['NFL', 'NBA', 'MLB', 'NHL', 'MLS', 'More Sports']) expect(source).toContain(sport);
  expect(source).not.toContain('football_hub_active_page');
});
```

- [ ] **Step 2: Verify it fails**

Run: `node --test tests/usa-sports-hub-panel.test.cjs`

Expected: FAIL with copied Football Hub references.

- [ ] **Step 3: Change brand/navigation, preserve the style system**

Rename the custom element, panel registration, storage keys, headers, labels, and asset paths. Keep the existing Shadow DOM, CSS classes, media queries, layout hierarchy, and interaction patterns. Replace football artwork with a custom star/stripe/shield logo and a subtle USA background; retheme only existing tokens to navy, white, red, and blue.

- [ ] **Step 4: Verify it passes**

Run: `node --test tests/usa-sports-hub-panel.test.cjs`

Expected: PASS.

- [ ] **Step 5: Commit the panel adaptation**

```bash
git add custom_components/usa_sports_hub/brand custom_components/usa_sports_hub/frontend www tests/usa-sports-hub-panel.test.cjs
git commit -m "feat: adapt Football Hub panel for USA sports"
```

### Task 4: Add the future USA sports provider boundary

**Files:**
- Create: `custom_components/usa_sports_hub/api/usa_sports.py`
- Modify: `custom_components/usa_sports_hub/api/coordinator.py`
- Test: `tests/test_usa_sports_provider.py`

**Interfaces:**
- Consumes: copied coordinator design.
- Produces: `UsaSportsProvider` with async scoreboard, standings, schedule, and news methods plus a safe `provider_not_configured` response.

- [ ] **Step 1: Write the failing contract test**

```python
from custom_components.usa_sports_hub.api.usa_sports import UsaSportsProvider

def test_provider_contract_exposes_initial_sports():
    assert UsaSportsProvider.SPORTS == ("nfl", "nba", "mlb", "nhl", "mls", "more")
```

- [ ] **Step 2: Verify it fails**

Run: `python -m pytest tests/test_usa_sports_provider.py -q`

Expected: FAIL because the provider boundary does not exist.

- [ ] **Step 3: Implement the safe provider boundary**

```python
class UsaSportsProvider:
    SPORTS = ("nfl", "nba", "mlb", "nhl", "mls", "more")
    async def get_scoreboard(self, sport: str) -> dict:
        return {"available": False, "sport": sport, "reason": "provider_not_configured"}
```

Wire this through the coordinator so the panel can show setup status. Do not make network calls or add credentials.

- [ ] **Step 4: Verify it passes**

Run: `python -m pytest tests/test_usa_sports_provider.py -q`

Expected: PASS.

- [ ] **Step 5: Commit the provider boundary**

```bash
git add custom_components/usa_sports_hub/api tests/test_usa_sports_provider.py
git commit -m "feat: add USA sports provider boundary"
```

### Task 5: Document, validate, and publish 0.0.1

**Files:**
- Modify: `README.md`
- Modify: `hacs.json`

**Interfaces:**
- Consumes: completed integration, tests, and an authenticated GitHub CLI account.
- Produces: an installable project and a private `usa-sports-hub` repository.

- [ ] **Step 1: Write USA Sports Hub setup documentation**

Document Home Assistant installation, the six sport selectors, the copied-panel basis, and the fact that live API configuration is the next phase.

- [ ] **Step 2: Run validation**

Run: `python -m pytest tests/test_integration_identity.py tests/test_usa_sports_provider.py -q && node --test tests/usa-sports-hub-panel.test.cjs && python -m compileall -q custom_components/usa_sports_hub`

Expected: all commands exit 0.

- [ ] **Step 3: Publish the repository**

Run: `git branch -M main && gh auth status && gh repo create usa-sports-hub --private --source . --remote origin --push`

Expected: GitHub creates the private repo and pushes `main`.

- [ ] **Step 4: Verify publication**

Run: `gh repo view --json name,url,visibility && git status --short`

Expected: `usa-sports-hub`, private visibility, clean working tree.
