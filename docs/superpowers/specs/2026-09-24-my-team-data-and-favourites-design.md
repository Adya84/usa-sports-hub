# USA Sports Hub: My Team Data and Favourites Design

## Goal

Turn the existing schedule-only **My Team** tab into a persistent, sport-aware team hub.  It must use the TS provider's team endpoints directly, keep all data scoped to the selected team or selected fixture, and retain the USA Sports Hub visual identity while using the component language of Football Hub.

## Scope

Supported sports are NFL, NBA, MLB and NHL.  The team selector can save up to three permanent favourites across those sports.  A favourite persists in Home Assistant configuration, not browser local storage, and remains available after a browser change or Home Assistant restart.

## Data sources and contracts

The provider will add a team-detail operation keyed by `(sport, team_id)` and return these compact collections:

| Collection | TS endpoint | Purpose |
| --- | --- | --- |
| `team_profile` | `/{sport}/teams/{team_id}` | Identity, logo, colours, venue, coach/manager, standing and team extra information. |
| `team_squad` | `/{sport}/teams/{team_id}/players` | Roster, player portrait, number, position, injury state and published season statistics. |
| `team_statistics` | `/{sport}/teams/{team_id}/statistics` | Sport-specific aggregate or available team statistics. |
| `team_leaders` | `/{sport}/teams/{team_id}/leaders` | Published scoring and performance leaders. |
| `team_injuries` | `/{sport}/teams/{team_id}/injuries` | Published injury report, when provided as a list. |

Existing sport-wide `fixtures`, `results`, `live`, `standings` and `news` remain the fast, normal dashboard feed.  The page filters them by the active team to create recent form, next fixtures, results and the current live match.

Team-specific `events` endpoints are intentionally not polled as a normal sensor.  Their responses can be very large (NBA was observed at roughly 12 MB).  The dashboard will use the compact existing schedule for its normal recent/upcoming sections; a later pagination design may add full-history browsing without adding a heavy periodic request.

The profile's advertised RSS URL may be exposed as metadata but team news will only be rendered after its feed is fetched and normalized in a dedicated, bounded implementation.  It must never be substituted with unrelated league articles.

## Caching and refresh

`UsaSportsCoordinator` will keep a bounded `team_details` cache per sport, indexed by stable team ID.  Each entry contains its retrieval time and the compact data above.  It is persisted alongside the existing coordinator cache.

- The active team fetch renders a cached result immediately, then refreshes in the background.
- Saved favourites are refreshed on a staggered, bounded budget; no more than one expensive team refresh is started per ordinary coordinator cycle.
- Profile/squad data are retained on a transient provider failure.  A timestamp and error state are carried with the team cache.
- Game-detail data stays in the existing `details[game_id]` cache.  It is never used as a fallback for team profile, roster, stats or leaders.
- A missing optional collection is represented by an empty collection and a clear page empty state, never by content from another team or match.

## Favourites

Add services to save and remove favourites.  Records are stored in the config entry options with:

```json
{
  "sport": "mlb",
  "team_id": "11",
  "team": "Los Angeles Angels"
}
```

The backend validates supported sport, supplied team ID and the maximum of three records.  Duplicate `(sport, team_id)` additions are idempotent.  Removing a favourite removes its permanent selection and its retained team-detail cache.  The normal Team dropdown remains a temporary view selector; its browser preference is still retained separately.

## Sensors

Each existing sport gains the following detailed, unrecorded attributes:

- `team_profile`
- `team_squad`
- `team_statistics`
- `team_leaders`
- `team_injuries`

The `status` sensor exposes compact favourite summaries and the active-team cache state.  It must not include full rosters, match lists or player statistics.

## My Team user interface

The page contains:

1. A club masthead: crest, name, league, venue, coach/manager, conference/division, record and rank.
2. Favourite chips, add-to-favourites and remove controls.  The controls clearly show `0/3` through `3/3`.
3. A live game or next-game feature card, opening the existing Game Centre for the selected fixture.
4. A season snapshot with record, home/away record, form, streak and available playoff/division context.
5. Recent results and upcoming fixtures built from the compact league schedule.
6. A squad grid with portrait, player name, number, position, injury badge and a small set of available seasonal figures.
7. Sport-relevant team leaders, team statistics and injury report.
8. Team news only when a correctly scoped, normalized team feed is available.

All cards use Football Hub-style section bars, dark navy panels, blue/cyan borders and subtle glows.  USA Sports Hub retains USA navy as the base, red active/live states, white highlights, sport-specific accent colours and selected-sport background artwork.

## Error handling

- A team endpoint error preserves last successful data and reports a compact freshness/error message.
- Optional missing API payloads display an explicit unavailable state.
- The page must not display a roster, injury, statistic or leader from another team.
- The UI uses the selected team ID for data matching; names are display-only and normalized only as a compatibility fallback for existing schedule rows.

## Testing

- Provider tests cover compact normalization of profile, player, statistic, leader and injury payloads, plus malformed/optional payloads.
- Coordinator tests cover cache isolation by sport/team ID, retention on provider failure, cache expiry and three-favourite validation.
- Service tests cover add, duplicate add, max-three rejection and remove.
- Panel tests cover the Football Hub-style My Team sections, correctly scoped rendering, favourite controls and no unrelated selected-game data.
- Run Python provider/coordinator tests, Node panel tests, `compileall`, `node --check` and `git diff --check` before publishing a beta.
