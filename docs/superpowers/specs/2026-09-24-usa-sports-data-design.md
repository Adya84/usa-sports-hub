# USA Sports Hub Data Provider Design

## Goal

Replace the copied football data path with working no-key NFL, NBA, MLB and NHL data providers that supply sport-specific dashboard data and compact Home Assistant sensors.

## Scope

The first data release covers NFL and NBA through ESPN, MLB through the MLB Stats API, and NHL through the official NHL API. MLS remains visual-only until its provider is selected. No LMS, Acca, football-country, football-cup, or football-transfer features are retained.

## Architecture

`providers/` contains one focused client per source: `espn_nfl.py`, `espn_nba.py`, `mlb.py`, and `nhl.py`. Each client accepts an aiohttp session and exposes schedule, standings, teams, news and an optional live-game detail method.

`models.py` defines the provider-independent game and standing dictionaries. Provider adapters normalize identifiers, teams, logos, scores, status, start time, period, clock, venue and broadcast information into those dictionaries. Optional detailed data such as leaders, plays and box-score fields is held under `detail` and is not copied into sensor attributes by default.

`coordinator.py` becomes `UsaSportsCoordinator`. It maintains per-sport cache entries, refresh timestamps and error state. It requests a schedule/scoreboard and standings at ordinary intervals; when any game reports a live status, it polls that sport at a short interval and fetches the selected game detail only. It exposes one `data` structure indexed by sport for the frontend and sensors.

## Data flow

1. The coordinator asks each provider for the current schedule and standings.
2. The provider normalizes source payloads before returning them.
3. The coordinator caches the normalized payload, computes `live_games`, `next_game` and `latest_result`, and updates Home Assistant.
4. Sensors publish only those compact summaries. The custom panel can obtain full in-memory detail through the panel data endpoint introduced with the coordinator.

## Polling and resilience

Non-live data refreshes every 10 minutes. A sport with an in-progress game refreshes every 30 seconds. A completed game is refreshed once more before returning to the normal interval. Failed source calls retain the last successful cache and record a provider error; a source outage must not prevent the other sports from updating.

## Sensors

For each supported sport, the integration creates: live games count, next game, latest result, standings summary and provider status. Sensor state is concise; attributes contain normalized teams, scores, status and update time only. Play-by-play, roster payloads and full box scores are excluded from recorder-backed attributes.

## Frontend contract

The USA Sports Hub panel reads `usa_sports_hub.data` by sport. Overview cards render real next game, live status, latest result and top standings rows when available, and retain the existing visual placeholder only when a provider has no current response. Selecting a top sport tab changes the data view without changing the persistent USA masthead or left navigation.

## Testing

Provider unit tests use captured minimal JSON payloads and verify normalized games, standings, schedule dates and source errors. Coordinator tests verify normal and live refresh interval selection, stale-cache retention after one provider fails, and compact sensor output. Existing identity and panel tests remain green.

## Acceptance criteria

- NFL, NBA, MLB and NHL current schedule/scoreboard requests return normalized games.
- Each sport renders real overview data when the source responds.
- No code path imports the Football Hub coordinator, Football Hub API, football competition catalogue or football-only providers.
- Live polling does not persist full play-by-play into Home Assistant sensor attributes.
- A single provider failure does not take down the integration or erase cached data from other sports.
