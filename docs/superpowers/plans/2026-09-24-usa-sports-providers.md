# USA Sports Providers Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Add working no-key NFL, NBA, MLB and NHL data providers to USA Sports Hub.

**Architecture:** Provider modules normalize their respective public source into shared compact game and standing models. A new USA coordinator owns caches and adaptive refreshes, while sport sensors expose lean summary entities without recorder-heavy payloads.

**Tech Stack:** Home Assistant integration, Python 3.12, aiohttp, pytest/unittest-style provider tests.

**Spec:** `docs/superpowers/specs/2026-09-24-usa-sports-data-design.md`

## Global Constraints

- Use ESPN for NFL and NBA, MLB Stats API for MLB, and NHL API for NHL; no API keys.
- Preserve last good data when a provider fails.
- Poll live games at 30 seconds and ordinary data at 10 minutes.
- Do not include play-by-play or full box scores in sensor attributes.
- Remove runtime imports of copied Football Hub modules.

## Review Focus

- A malformed provider event must be ignored rather than stopping the sport refresh.
- Provider failure after a successful refresh must preserve cached sport data.
- A live status must select the 30-second interval; completed and scheduled games must select ten minutes.
- Timezone-bearing source dates must normalize to UTC ISO strings.
- Sensor attributes must not contain `plays`, `play_by_play`, or raw response objects.

---

### Task 1: Shared models and provider HTTP base

**Files:**
- Create: `custom_components/usa_sports_hub/providers/models.py`
- Create: `custom_components/usa_sports_hub/providers/base.py`
- Create: `tests/test_provider_models.py`

**Interfaces:**
- Produces: `normalise_game`, `normalise_standing`, `ProviderClient.async_get_json`.

- [ ] Write failing model tests for minimal normalized games, missing team names and compact detail.
- [ ] Run `python -m unittest tests.test_provider_models -v` and confirm failure from missing modules.
- [ ] Implement the model helpers and HTTP client with timeout and descriptive provider errors.
- [ ] Run model tests and commit shared provider foundation.

### Task 2: ESPN NFL and NBA providers

**Files:**
- Create: `custom_components/usa_sports_hub/providers/espn.py`
- Create: `custom_components/usa_sports_hub/providers/espn_nfl.py`
- Create: `custom_components/usa_sports_hub/providers/espn_nba.py`
- Create: `tests/test_espn_providers.py`

**Interfaces:**
- Consumes: `ProviderClient`, normalized model helpers.
- Produces: `async_schedule`, `async_standings`, `async_news`, `async_game_detail`.

- [ ] Write failing tests using ESPN scoreboard and standings fixtures.
- [ ] Run the ESPN tests and confirm failure from missing provider modules.
- [ ] Implement the reusable ESPN adapter and thin NFL/NBA configurations.
- [ ] Run provider tests and commit ESPN providers.

### Task 3: MLB and NHL providers

**Files:**
- Create: `custom_components/usa_sports_hub/providers/mlb.py`
- Create: `custom_components/usa_sports_hub/providers/nhl.py`
- Create: `tests/test_mlb_provider.py`
- Create: `tests/test_nhl_provider.py`

**Interfaces:**
- Consumes: `ProviderClient`, normalized model helpers.
- Produces: schedule, standings and live game detail methods aligned with ESPN providers.

- [ ] Write failing source-specific tests for MLB schedule/standings and NHL score/standings payloads.
- [ ] Run tests and confirm failure from missing modules.
- [ ] Implement each adapter with source-specific status/score normalization.
- [ ] Run provider tests and commit official-source providers.

### Task 4: USA coordinator and sensors

**Files:**
- Create: `custom_components/usa_sports_hub/coordinator.py`
- Create: `custom_components/usa_sports_hub/sensors/usa_sports.py`
- Modify: `custom_components/usa_sports_hub/__init__.py`
- Modify: `custom_components/usa_sports_hub/sensor.py`
- Create: `tests/test_usa_coordinator.py`

**Interfaces:**
- Consumes: all provider interfaces.
- Produces: `UsaSportsCoordinator.data` indexed by sport and five compact sensors per sport.

- [ ] Write failing tests for adaptive intervals, cache retention, independent provider failures and compact attributes.
- [ ] Run coordinator tests and confirm failure from missing coordinator.
- [ ] Implement the coordinator and sensor entities, replacing the copied Football Hub coordinator runtime path.
- [ ] Run all Python and panel tests and commit the data layer.

### Task 5: Dashboard data binding and release

**Files:**
- Modify: `custom_components/usa_sports_hub/frontend/usa-sports-hub-panel-v2.js`
- Modify: `custom_components/usa_sports_hub/manifest.json`
- Modify: `README.md`
- Modify: `www/usa-sports-hub-panel.js`

**Interfaces:**
- Consumes: coordinator sport summaries from Home Assistant.
- Produces: real overview cards while retaining placeholders for unavailable sources.

- [ ] Write a failing panel test for reading sport summaries and rejecting Football Hub UI labels.
- [ ] Implement card binding and sync the served panel copy.
- [ ] Run `node --check`, panel tests, Python tests and compileall.
- [ ] Commit, push and publish the next prerelease.
