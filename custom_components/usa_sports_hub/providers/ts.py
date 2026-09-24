"""Unified TS provider for NFL, NBA, MLB and NHL."""
from __future__ import annotations

from datetime import datetime, timedelta, timezone
from typing import Any
from urllib.parse import urlencode

from .base import ProviderClient
from .models import (
    compact_ts_news,
    normalize_ts_event,
    normalize_ts_standing,
    normalize_ts_team,
)


API_BASE = "https://api." + "the" + "score.com"
WEB_API_BASE = "https://www." + "the" + "score.com/api"
MLB_STATS_BASE = "https://statsapi.mlb.com/api/v1"


def _walk(value: Any):
    """Yield every dict/list node in a nested payload."""
    yield value
    if isinstance(value, dict):
        for child in value.values():
            yield from _walk(child)
    elif isinstance(value, list):
        for child in value:
            yield from _walk(child)


def _api_uris(value: Any, prefix: str) -> list[str]:
    found: list[str] = []
    for node in _walk(value):
        if not isinstance(node, dict):
            continue
        uri = node.get("api_uri")
        if isinstance(uri, str) and uri.startswith(prefix) and uri not in found:
            found.append(uri)
    return found


def _objects_with_keys(value: Any, keys: set[str], limit: int = 100) -> list[dict[str, Any]]:
    rows: list[dict[str, Any]] = []
    for node in _walk(value):
        if isinstance(node, dict) and keys.intersection(node):
            rows.append(node)
            if len(rows) >= limit:
                break
    return rows


def _named_lists(value: Any, names: set[str], limit: int = 120) -> list[dict[str, Any]]:
    """Collect dict rows from commonly named provider list fields."""
    rows: list[dict[str, Any]] = []
    for node in _walk(value):
        if not isinstance(node, dict):
            continue
        for key, child in node.items():
            if str(key).lower() not in names or not isinstance(child, list):
                continue
            for item in child:
                if isinstance(item, dict):
                    rows.append(item)
                    if len(rows) >= limit:
                        return rows
    return rows


def _dedupe_dicts(rows: list[dict[str, Any]], limit: int = 120) -> list[dict[str, Any]]:
    """Best-effort de-duplicate nested provider rows while preserving order."""
    seen: set[str] = set()
    result: list[dict[str, Any]] = []
    for row in rows:
        marker = str(
            row.get("id")
            or row.get("api_uri")
            or row.get("player_id")
            or row.get("team_id")
            or row
        )
        if marker in seen:
            continue
        seen.add(marker)
        result.append(row)
        if len(result) >= limit:
            break
    return result


class TSProvider(ProviderClient):
    """One provider implementation shared by all supported leagues."""

    def __init__(self, session, league: str):
        super().__init__(session)
        self.league = league.lower()
        self.base = f"{API_BASE}/{self.league}"

    def _events_url(self, past_days: int = 5, future_days: int = 14) -> str:
        now = datetime.now(timezone.utc)
        start = (now - timedelta(days=past_days)).replace(microsecond=0)
        end = (now + timedelta(days=future_days)).replace(microsecond=0)
        query = urlencode(
            {
                "game_date.gt": start.isoformat().replace("+00:00", "Z"),
                "game_date.lt": end.isoformat().replace("+00:00", "Z"),
            }
        )
        return f"{self.base}/events?{query}"

    async def async_schedule(self) -> list[dict[str, Any]]:
        payload = await self.async_get_json(self._events_url())
        if not isinstance(payload, list):
            return []
        games = [
            normalize_ts_event(item, self.league)
            for item in payload
            if isinstance(item, dict) and item.get("id") is not None
        ]
        games.sort(key=lambda item: str(item.get("start_time") or ""))
        return games

    async def async_ticker(self) -> list[dict[str, Any]]:
        payload = await self.async_get_json(f"{WEB_API_BASE}/ticker?leagues={self.league}")
        groups = payload.get("groups", []) if isinstance(payload, dict) else []
        for group in groups:
            if str(group.get("slug") or "").lower() == self.league:
                return group.get("events", []) or []
        return []

    async def async_standings(self) -> list[dict[str, Any]]:
        payload = await self.async_get_json(f"{self.base}/standings")
        if not isinstance(payload, list):
            return []
        rows = [item for item in payload if isinstance(item, dict)]
        season_types = {str(item.get("season_type") or "").lower() for item in rows}
        if "regular" in season_types:
            rows = [item for item in rows if str(item.get("season_type") or "").lower() == "regular"]
        elif "pre" in season_types:
            rows = [item for item in rows if str(item.get("season_type") or "").lower() == "pre"]
        return [normalize_ts_standing(item, self.league) for item in rows]

    async def async_news(self) -> list[dict[str, Any]]:
        # TS event payloads expose preview/recap metadata.  This keeps the
        # integration entirely off ESPN while still supplying useful league news.
        payload = await self.async_get_json(self._events_url(past_days=7, future_days=2))
        return compact_ts_news(payload if isinstance(payload, list) else [])

    async def async_teams(self) -> list[dict[str, Any]]:
        standings = await self.async_get_json(f"{self.base}/standings")
        teams: dict[str, dict[str, Any]] = {}
        if isinstance(standings, list):
            for row in standings:
                team = row.get("team") if isinstance(row, dict) else None
                if isinstance(team, dict) and team.get("id") is not None:
                    normalized = normalize_ts_team(team)
                    teams[str(normalized["id"])] = normalized
        if teams:
            return list(teams.values())

        # Pre-season feeds can occasionally have incomplete standings.  Fall
        # back to events so the team selector still populates.
        events = await self.async_get_json(self._events_url())
        if isinstance(events, list):
            for event in events:
                if not isinstance(event, dict):
                    continue
                for key in ("home_team", "away_team"):
                    team = event.get(key)
                    if isinstance(team, dict) and team.get("id") is not None:
                        normalized = normalize_ts_team(team)
                        teams[str(normalized["id"])] = normalized
        return list(teams.values())

    async def async_game_detail(self, game_id: str | int) -> dict[str, Any]:
        event = await self.async_get_json(f"{self.base}/events/{game_id}")
        if not isinstance(event, dict):
            return {"event": {}, "box_score": {}, "play_by_play": [], "drives": []}

        box = event.get("box_score") if isinstance(event.get("box_score"), dict) else {}
        box_uri = box.get("api_uri")
        box_score: dict[str, Any] = {}
        if isinstance(box_uri, str) and box_uri:
            box_score = await self.async_get_json(f"{API_BASE}{box_uri}")

        detail: dict[str, Any] = {
            "event": normalize_ts_event(event, self.league),
            "box_score": box_score if isinstance(box_score, dict) else {},
            "drives": [],
            "play_by_play": [],
            "scoring": [],
            "players": [],
            "injuries": [],
            "lineups": [],
            "statistics": [],
            "leaders": [],
            "periods": [],
            "officials": [],
            "situations": [],
            "related": [],
            "odds": event.get("odd") or {},
            "stadium": event.get("stadium_details") or {},
        }

        # NFL exposes drive endpoints whose payloads contain the full play list.
        drive_uris = _api_uris(box_score, f"/{self.league}/drives/")[:24]
        for uri in drive_uris:
            drive = await self.async_get_json(f"{API_BASE}{uri}")
            if isinstance(drive, dict):
                detail["drives"].append(drive)
                records = drive.get("play_by_play_detail_records")
                if isinstance(records, list):
                    detail["play_by_play"].extend(records)

        # Other sports often embed their records directly in the box score.
        if not detail["play_by_play"]:
            for node in _walk(box_score):
                if not isinstance(node, dict):
                    continue
                records = node.get("play_by_play_detail_records")
                if isinstance(records, list):
                    detail["play_by_play"].extend(
                        item for item in records if isinstance(item, dict)
                    )

        # MLB sometimes exposes no usable play-by-play through TS even while
        # the game is live. Resolve the matching MLB gamePk from the public MLB
        # schedule feed, then use its playByPlay endpoint as a detail fallback.
        if self.league == "mlb" and not detail["play_by_play"]:
            mlb_game_pk = None
            try:
                game_date = str(event.get("game_date") or "")[:10]
                home_name = str((event.get("home_team") or {}).get("full_name") or (event.get("home_team") or {}).get("name") or "").lower()
                away_name = str((event.get("away_team") or {}).get("full_name") or (event.get("away_team") or {}).get("name") or "").lower()
                schedule = await self.async_get_json(
                    f"{MLB_STATS_BASE}/schedule?sportId=1&date={game_date}"
                )
                for day in (schedule.get("dates", []) if isinstance(schedule, dict) else []):
                    for game in day.get("games", []) or []:
                        teams = game.get("teams") if isinstance(game.get("teams"), dict) else {}
                        home = ((teams.get("home") or {}).get("team") or {}) if isinstance(teams.get("home"), dict) else {}
                        away = ((teams.get("away") or {}).get("team") or {}) if isinstance(teams.get("away"), dict) else {}
                        h = str(home.get("name") or "").lower()
                        a = str(away.get("name") or "").lower()
                        if h == home_name and a == away_name:
                            mlb_game_pk = game.get("gamePk")
                            break
                    if mlb_game_pk:
                        break
            except Exception:
                mlb_game_pk = None

            if mlb_game_pk:
                try:
                    mlb_pbp = await self.async_get_json(
                        f"{MLB_STATS_BASE}/game/{mlb_game_pk}/playByPlay"
                    )
                except Exception:
                    mlb_pbp = {}
                if isinstance(mlb_pbp, dict):
                    all_plays = mlb_pbp.get("allPlays")
                    if isinstance(all_plays, list):
                        converted = []
                        for play in all_plays:
                            if not isinstance(play, dict):
                                continue
                            result = play.get("result") if isinstance(play.get("result"), dict) else {}
                            about = play.get("about") if isinstance(play.get("about"), dict) else {}
                            matchup = play.get("matchup") if isinstance(play.get("matchup"), dict) else {}
                            count = play.get("count") if isinstance(play.get("count"), dict) else {}
                            batter = matchup.get("batter") if isinstance(matchup.get("batter"), dict) else {}
                            pitcher = matchup.get("pitcher") if isinstance(matchup.get("pitcher"), dict) else {}
                            converted.append(
                                {
                                    "description": result.get("description") or result.get("event"),
                                    "event": result.get("event"),
                                    "inning": about.get("inning"),
                                    "half_inning": about.get("halfInning"),
                                    "is_scoring_play": about.get("isScoringPlay"),
                                    "away_score": result.get("awayScore"),
                                    "home_score": result.get("homeScore"),
                                    "rbi": result.get("rbi"),
                                    "balls": count.get("balls"),
                                    "strikes": count.get("strikes"),
                                    "outs": count.get("outs"),
                                    "batter": batter.get("fullName"),
                                    "pitcher": pitcher.get("fullName"),
                                }
                            )
                        detail["play_by_play"].extend(converted)

        # Follow additional game-detail endpoints advertised by the event/box score.
        # Different sports expose lineups, injuries, rosters, player stats and
        # officials through different nested api_uri fields, so discover them
        # dynamically rather than hard-coding one league's shape.
        related_source = {"event": event, "box_score": box_score}
        related_uris = _api_uris(related_source, f"/{self.league}/")
        allowed_fragments = (
            "lineup", "injur", "roster", "player", "stat", "leader",
            "official", "pitcher", "batter", "skater", "goalie",
        )
        related_payloads: list[Any] = []
        for uri in [
            uri for uri in related_uris
            if any(fragment in uri.lower() for fragment in allowed_fragments)
        ][:20]:
            try:
                payload = await self.async_get_json(f"{API_BASE}{uri}")
            except Exception:
                continue
            related_payloads.append(payload)

        detail["related"] = related_payloads[:20]

        # Pull useful compact collections from the complete event/detail tree.
        combined = {
            "event": event,
            "box_score": box_score,
            "drives": detail["drives"],
            "related": related_payloads,
        }
        detail["scoring"] = _dedupe_dicts(
            _objects_with_keys(
                combined,
                {"score_summary", "scoring_play", "scoring_type", "goal_type", "touchdown"},
                120,
            )
            + _named_lists(combined, {"scoring", "scoring_plays", "goals", "runs"}, 120),
            120,
        )
        detail["players"] = _dedupe_dicts(
            _objects_with_keys(
                combined,
                {
                    "full_name", "first_initial_and_last_name", "position_abbreviation",
                    "jersey_number", "player_id",
                },
                160,
            )
            + _named_lists(combined, {"players", "roster", "rosters", "skaters", "goalies"}, 160),
            160,
        )
        detail["injuries"] = _dedupe_dicts(
            _objects_with_keys(
                combined,
                {"date_injured", "return_date", "injury", "injury_status", "injury_type"},
                100,
            )
            + _named_lists(combined, {"injuries", "injured_players"}, 100),
            100,
        )
        detail["lineups"] = _dedupe_dicts(
            _objects_with_keys(
                combined,
                {"lineup", "batting_order", "starter", "starting_position", "depth_position"},
                140,
            )
            + _named_lists(
                combined,
                {
                    "lineup", "lineups", "starters", "starting_lineup",
                    "batting_order", "formations",
                },
                140,
            ),
            140,
        )
        detail["statistics"] = _dedupe_dicts(
            _objects_with_keys(
                combined,
                {
                    "passing_yards", "rushing_yards", "receiving_yards",
                    "points", "rebounds", "assists", "shots", "hits",
                    "runs", "earned_runs", "strikeouts", "saves",
                    "field_goals_made", "three_points_made", "goals",
                    "tackles", "interceptions", "home_runs",
                },
                180,
            )
            + _named_lists(
                combined,
                {
                    "statistics", "stats", "team_statistics", "player_statistics",
                    "player_stats", "team_stats",
                },
                180,
            ),
            180,
        )
        detail["leaders"] = _dedupe_dicts(
            _objects_with_keys(
                combined,
                {"leader", "leaders", "rank", "stat_value", "display_value"},
                100,
            )
            + _named_lists(combined, {"leaders", "game_leaders", "player_leaders"}, 100),
            100,
        )
        detail["periods"] = _dedupe_dicts(
            _objects_with_keys(
                combined,
                {"period", "segment", "segment_string", "quarter", "inning"},
                100,
            )
            + _named_lists(
                combined,
                {"periods", "segments", "quarters", "innings", "line_scores", "linescores"},
                100,
            ),
            100,
        )
        detail["officials"] = _dedupe_dicts(
            _objects_with_keys(
                combined,
                {"official", "official_type", "referee", "umpire"},
                60,
            )
            + _named_lists(combined, {"officials", "referees", "umpires"}, 60),
            60,
        )
        detail["situations"] = _dedupe_dicts(
            _objects_with_keys(
                combined,
                {
                    "down", "distance", "possession", "yard_line",
                    "balls", "strikes", "outs", "first_base", "second_base", "third_base",
                    "team_on_power_play", "home_strength", "away_strength",
                    "pitcher", "batter",
                },
                100,
            ),
            100,
        )

        # Keep the live sensor useful but bounded.
        detail["play_by_play"] = detail["play_by_play"][-160:]
        return detail


class NflProvider(TSProvider):
    def __init__(self, session):
        super().__init__(session, "nfl")


class NbaProvider(TSProvider):
    def __init__(self, session):
        super().__init__(session, "nba")


class MlbProvider(TSProvider):
    def __init__(self, session):
        super().__init__(session, "mlb")


class NhlProvider(TSProvider):
    def __init__(self, session):
        super().__init__(session, "nhl")
