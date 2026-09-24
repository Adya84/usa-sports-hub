# 🇺🇸 USA Sports Hub

USA Sports Hub is a Home Assistant dashboard and sensor integration for major United States sports. It uses the familiar Football Hub panel system, redesigned with a USA Sports Hub identity and multi-sport navigation.

> **Project status:** 0.0.3 beta is under active development. NFL, NBA, MLB and NHL now use a unified TS data provider with detailed live event, standings, box-score and play-by-play support.

## Planned sports

- 🏈 NFL — TS
- 🏀 NBA — TS
- ⚾ MLB — TS
- 🏒 NHL — TS
- ⚽ MLS — planned
- ⭐ More Sports — WNBA, NCAA, F1, UFC and further sports planned

The integration uses public JSON endpoints from TS and does not require users to create an API key.

## Features

- USA-themed Home Assistant panel with a shared sports-hub layout
- League navigation for NFL, NBA, MLB, NHL, MLS and More Sports
- Live games, upcoming schedules, results and standings
- Team, player and leaderboard data
- Favourite-team sensors and match information
- Detailed live-game attributes for box scores and play-by-play
- A provider adapter layer so data sources can be changed without rebuilding the dashboard

## Installation

### HACS installation

1. Open **HACS** in Home Assistant.
2. Select the three-dot menu, then choose **Custom repositories**.
3. Add the USA Sports Hub repository URL:

   ```text
   https://github.com/Adya84/usa-sports-hub
   ```

4. Set the category to **Integration**, then select **Add**.
5. Search HACS for **USA Sports Hub** and select **Download**.
6. Restart Home Assistant.
7. Go to **Settings → Devices & services → Add integration**.
8. Search for **USA Sports Hub**, complete the setup flow, then open **USA Sports Hub** from the sidebar.

### Manual installation

1. Download a release ZIP from the USA Sports Hub GitHub repository.
2. Extract it.
3. Copy the `custom_components/usa_sports_hub` folder into your Home Assistant configuration directory.

   Your final path must be:

   ```text
   config/custom_components/usa_sports_hub/manifest.json
   ```

4. Restart Home Assistant.
5. Add **USA Sports Hub** from **Settings → Devices & services**.

After an update, hard-refresh the browser with **Ctrl+F5** (Windows/Linux) or **Cmd+Shift+R** (macOS) so Home Assistant reloads the latest panel JavaScript.

## Sensors

The integration is designed to provide consistent core sensors for every supported sport:

| Sensor group | Examples |
| --- | --- |
| Hub | Status, provider status, live-game count, selected game |
| Schedule | Today’s games, next game, weekly schedule, results |
| League | Standings, teams, leaders, news |
| Favourite team | Next game, latest result, live game, events, statistics, league position |
| Live game | Score, status, clock/period, box score, team statistics, play-by-play |

Each sport also exposes richer live attributes where the provider makes them available:

- **NFL:** possession, down and distance, yard line, drives, scoring plays, passing/rushing/receiving leaders.
- **NBA:** fouls, timeouts, shooting splits, player leaders, rebounds, assists and live plays.
- **MLB:** innings, balls, strikes, outs, bases, pitcher/batter, pitch data, runs/hits/errors.
- **NHL:** shots, power plays, penalties, goalie saves, faceoffs, hits, blocks and live events.

## Data providers

USA Sports Hub keeps providers separate from the panel and sensor models:

```text
USA Sports Hub
├── NFL  → TS
├── NBA  → TS
├── MLB  → TS
└── NHL  → TS
```

The shared TS adapter uses league-specific event, standings, team, box-score and live-detail endpoints while keeping the dashboard model consistent across sports.

## Development

The integration source is in:

```text
custom_components/usa_sports_hub
```

The panel source is in:

```text
custom_components/usa_sports_hub/frontend/usa-sports-hub-panel.js
```

Run the available lightweight checks from the repository root:

```bash
python -m unittest tests.test_integration_identity -v
python -m compileall -q custom_components/usa_sports_hub
```

## Support USA Sports Hub

USA Sports Hub is independently developed by Adrian Apel. If you enjoy the integration and would like to support ongoing features, live-data improvements, and new sports coverage, you can contribute through:

- [Ko-fi](https://ko-fi.com/ady1984)
- [PayPal](https://paypal.me/graffidoodle)

You can also support the project by starring the repository and reporting issues with a clear description, Home Assistant version, integration version, and relevant redacted logs.

## Disclaimer

USA Sports Hub is an independent Home Assistant integration. It is not affiliated with, endorsed by, or sponsored by Home Assistant, HACS, TS, MLB, NHL, NBA, NFL, MLS, or any other league, team, broadcaster, or data provider. Team names, league names, and logos remain the property of their respective owners.
