"""Unified TS provider for NFL, NBA, MLB and NHL."""
from __future__ import annotations

import asyncio
from datetime import datetime, timedelta, timezone
from email.utils import parsedate_to_datetime
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
MLB_LIVE_BASE = "https://statsapi.mlb.com/api/v1.1"
MLB_HEADSHOT_BASE = "https://img.mlbstatic.com/mlb-photos/image/upload/d_people:generic:headshot:67:current.png/w_213,q_auto:best/v1/people"


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
        # MLB's official live feed is the authoritative rich game source.
        # Do not make an extra TS box-score round trip before it; that delayed
        # current batter, count and bases by a full upstream request.
        if self.league != "mlb" and isinstance(box_uri, str) and box_uri:
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
        if drive_uris:
            drive_results = await asyncio.gather(
                *(self.async_get_json(f"{API_BASE}{uri}") for uri in drive_uris),
                return_exceptions=True,
            )
            for drive in drive_results:
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

        # MLB detail enrichment. Resolve the corresponding MLB gamePk once,
        # then use the public live game feed for inning linescore/current state.
        # This is internal-only data enrichment; source URLs are never rendered.
        mlb_live_data: dict[str, Any] = {}
        mlb_game_data: dict[str, Any] = {}
        if self.league == "mlb":
            mlb_game_pk = None
            try:
                raw_game_date = str(event.get("game_date") or "")
                # theScore uses RFC 2822 dates ("Wed, 23 Sep 2026 ..."), not
                # ISO strings. Slicing the first ten characters produced
                # "Wed, 23 S", preventing every official MLB schedule match.
                game_date = parsedate_to_datetime(raw_game_date).date().isoformat()
                home_name = str((event.get("home_team") or {}).get("full_name") or (event.get("home_team") or {}).get("name") or "").lower()
                away_name = str((event.get("away_team") or {}).get("full_name") or (event.get("away_team") or {}).get("name") or "").lower()
                # theScore's displayed game date can cross the MLB schedule
                # boundary around midnight. Search adjacent days and prefer a
                # game in the same state (especially an active live game)
                # rather than accidentally selecting tomorrow's roster.
                parsed_day = datetime.fromisoformat(game_date).date()
                schedule_dates = [
                    (parsed_day + timedelta(days=offset)).isoformat()
                    for offset in (-1, 0, 1)
                ]
                schedules = await asyncio.gather(
                    *(
                        self.async_get_json(
                            f"{MLB_STATS_BASE}/schedule?sportId=1&date={schedule_day}"
                        )
                        for schedule_day in schedule_dates
                    ),
                    return_exceptions=True,
                )
                candidates = []
                for schedule in schedules:
                    if not isinstance(schedule, dict):
                        continue
                    for day in schedule.get("dates", []):
                        for game in day.get("games", []) or []:
                            teams = game.get("teams") if isinstance(game.get("teams"), dict) else {}
                            home = ((teams.get("home") or {}).get("team") or {}) if isinstance(teams.get("home"), dict) else {}
                            away = ((teams.get("away") or {}).get("team") or {}) if isinstance(teams.get("away"), dict) else {}
                            if (
                                str(home.get("name") or "").lower() == home_name
                                and str(away.get("name") or "").lower() == away_name
                            ):
                                candidates.append(game)
                event_status = str(event.get("status") or event.get("event_status") or "").lower()
                preferred_state = (
                    "live" if event_status in {"in_progress", "live"}
                    else "final" if event_status == "final"
                    else "preview"
                )
                def _candidate_rank(game: dict[str, Any]) -> int:
                    status = game.get("status") if isinstance(game.get("status"), dict) else {}
                    state = str(status.get("abstractGameState") or "").lower()
                    return 0 if state == preferred_state else 1
                if candidates:
                    mlb_game_pk = sorted(candidates, key=_candidate_rank)[0].get("gamePk")
            except Exception:
                mlb_game_pk = None

            if mlb_game_pk:
                try:
                    feed = await self.async_get_json(
                        f"{MLB_LIVE_BASE}/game/{mlb_game_pk}/feed/live"
                    )
                except Exception:
                    feed = {}
                if isinstance(feed, dict):
                    candidate_live = feed.get("liveData") if isinstance(feed.get("liveData"), dict) else {}
                    candidate_game = feed.get("gameData") if isinstance(feed.get("gameData"), dict) else {}
                    feed_teams = candidate_game.get("teams") if isinstance(candidate_game.get("teams"), dict) else {}
                    feed_home = feed_teams.get("home") if isinstance(feed_teams.get("home"), dict) else {}
                    feed_away = feed_teams.get("away") if isinstance(feed_teams.get("away"), dict) else {}
                    # Guard against ever mixing detail from a different MLB game.
                    if (
                        str(feed_home.get("name") or "").lower() == home_name
                        and str(feed_away.get("name") or "").lower() == away_name
                    ):
                        mlb_live_data = candidate_live
                        mlb_game_data = candidate_game

                if not detail["play_by_play"] and mlb_live_data:
                    plays_root = mlb_live_data.get("plays") if isinstance(mlb_live_data.get("plays"), dict) else {}
                    all_plays = plays_root.get("allPlays")
                    if not isinstance(all_plays, list):
                        try:
                            mlb_pbp = await self.async_get_json(
                                f"{MLB_STATS_BASE}/game/{mlb_game_pk}/playByPlay"
                            )
                        except Exception:
                            mlb_pbp = {}
                        all_plays = mlb_pbp.get("allPlays") if isinstance(mlb_pbp, dict) else []

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
        # MLB's rich live feed already includes players, lineups, stats and
        # officials, so avoid extra TS detail calls. For other sports, fetch
        # advertised detail endpoints concurrently rather than one-by-one.
        selected_related_uris = [] if (self.league == "mlb" and mlb_live_data) else [
            uri for uri in related_uris
            if any(fragment in uri.lower() for fragment in allowed_fragments)
        ][:20]
        if selected_related_uris:
            related_results = await asyncio.gather(
                *(self.async_get_json(f"{API_BASE}{uri}") for uri in selected_related_uris),
                return_exceptions=True,
            )
            related_payloads.extend(
                payload for payload in related_results if isinstance(payload, (dict, list))
            )

        detail["related"] = related_payloads[:20]

        # Pull useful compact collections from the complete event/detail tree.
        combined = {
            "event": event,
            "box_score": box_score,
            "drives": detail["drives"],
            "related": related_payloads,
            "mlb_live": mlb_live_data,
            "mlb_game": mlb_game_data,
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
        # When an MLB event has not yet resolved to the official MLB live feed,
        # retain only real theScore roster people. The raw recursive collection
        # also contains teams/leagues, which previously appeared in the Players
        # sensor and carried no usable portrait data.
        if self.league == "mlb" and not mlb_live_data:
            fallback_players: list[dict[str, Any]] = []
            for row in detail["players"]:
                if not isinstance(row, dict):
                    continue
                player_id = str(row.get("id") or row.get("player_id") or "")
                name = row.get("full_name") or row.get("first_initial_and_last_name")
                headshots = row.get("headshots") if isinstance(row.get("headshots"), dict) else {}
                headshot = (
                    headshots.get("w192xh192")
                    or headshots.get("large")
                    or headshots.get("original")
                    or row.get("headshot")
                )
                if not (player_id and name and headshot):
                    continue
                fallback_players.append(
                    {
                        "id": player_id,
                        "player_id": player_id,
                        "full_name": name,
                        "headshot": headshot,
                        "position_abbreviation": row.get("position_abbreviation"),
                        "jersey_number": row.get("number") or row.get("jersey_number"),
                        "team_name": row.get("team_name"),
                    }
                )
            if fallback_players:
                detail["players"] = _dedupe_dicts(fallback_players, 160)
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

        if self.league == "mlb" and mlb_live_data:
            linescore = mlb_live_data.get("linescore") if isinstance(mlb_live_data.get("linescore"), dict) else {}
            innings = linescore.get("innings") if isinstance(linescore.get("innings"), list) else []
            inning_rows: list[dict[str, Any]] = []
            for inning in innings:
                if not isinstance(inning, dict):
                    continue
                home = inning.get("home") if isinstance(inning.get("home"), dict) else {}
                away = inning.get("away") if isinstance(inning.get("away"), dict) else {}
                inning_rows.append(
                    {
                        "name": f"Inning {inning.get('num') or ''}".strip(),
                        "inning": inning.get("num"),
                        "away_runs": away.get("runs"),
                        "away_hits": away.get("hits"),
                        "away_errors": away.get("errors"),
                        "home_runs": home.get("runs"),
                        "home_hits": home.get("hits"),
                        "home_errors": home.get("errors"),
                    }
                )
            if inning_rows:
                detail["periods"] = inning_rows

            offense = linescore.get("offense") if isinstance(linescore.get("offense"), dict) else {}
            defense = linescore.get("defense") if isinstance(linescore.get("defense"), dict) else {}
            # The linescore offense/defense blocks can omit names depending
            # on game state. Fall back to the current play matchup so "At Bat"
            # remains populated during live play.
            plays_root = mlb_live_data.get("plays") if isinstance(mlb_live_data.get("plays"), dict) else {}
            current_play = plays_root.get("currentPlay") if isinstance(plays_root.get("currentPlay"), dict) else {}
            matchup = current_play.get("matchup") if isinstance(current_play.get("matchup"), dict) else {}
            current_batter = matchup.get("batter") if isinstance(matchup.get("batter"), dict) else {}
            current_pitcher = matchup.get("pitcher") if isinstance(matchup.get("pitcher"), dict) else {}

            batter_obj = offense.get("batter") if isinstance(offense.get("batter"), dict) else {}
            pitcher_obj = defense.get("pitcher") if isinstance(defense.get("pitcher"), dict) else {}

            # Some live responses only include the player id in linescore/currentPlay.
            # Resolve that id against gameData.players so the UI still gets names.
            game_players = mlb_game_data.get("players") if isinstance(mlb_game_data.get("players"), dict) else {}
            def _mlb_person_name(obj: dict[str, Any]) -> str | None:
                if not isinstance(obj, dict):
                    return None
                direct = obj.get("fullName") or obj.get("name")
                if direct:
                    return str(direct)
                player_id = obj.get("id")
                if player_id is None:
                    return None
                person = game_players.get(f"ID{player_id}") or game_players.get(str(player_id)) or {}
                if isinstance(person, dict):
                    return person.get("fullName") or person.get("name")
                return None

            batter_name = (
                _mlb_person_name(batter_obj)
                or _mlb_person_name(current_batter)
            )
            pitcher_name = (
                _mlb_person_name(pitcher_obj)
                or _mlb_person_name(current_pitcher)
            )

            # Prefer currentPlay for count/inning because it changes on every
            # pitch; linescore can lag slightly between at-bats.
            current_count = current_play.get("count") if isinstance(current_play.get("count"), dict) else {}
            current_about = current_play.get("about") if isinstance(current_play.get("about"), dict) else {}

            batter_id = batter_obj.get("id") or current_batter.get("id")
            pitcher_id = pitcher_obj.get("id") or current_pitcher.get("id")

            # linescore.offense is authoritative for occupied bases. If a feed
            # omits one of those fields, reconstruct the current bases from the
            # runner movements in currentPlay.
            first_base = bool(offense.get("first") or offense.get("firstBase"))
            second_base = bool(offense.get("second") or offense.get("secondBase"))
            third_base = bool(offense.get("third") or offense.get("thirdBase"))
            if not (first_base or second_base or third_base):
                runner_rows = current_play.get("runners") if isinstance(current_play.get("runners"), list) else []
                occupied: set[str] = set()
                for runner in runner_rows:
                    if not isinstance(runner, dict):
                        continue
                    movement = runner.get("movement") if isinstance(runner.get("movement"), dict) else {}
                    end = str(movement.get("end") or "").lower()
                    if movement.get("isOut"):
                        continue
                    if end in {"1b", "first", "first base"}:
                        occupied.add("1b")
                    elif end in {"2b", "second", "second base"}:
                        occupied.add("2b")
                    elif end in {"3b", "third", "third base"}:
                        occupied.add("3b")
                first_base = "1b" in occupied
                second_base = "2b" in occupied
                third_base = "3b" in occupied

            current_situation = {
                "name": "Current game situation",
                "inning": current_about.get("inning") or linescore.get("currentInning"),
                "inning_state": current_about.get("halfInning") or linescore.get("inningState"),
                "inning_ordinal": linescore.get("currentInningOrdinal"),
                "balls": current_count.get("balls") if current_count.get("balls") is not None else linescore.get("balls"),
                "strikes": current_count.get("strikes") if current_count.get("strikes") is not None else linescore.get("strikes"),
                "outs": current_count.get("outs") if current_count.get("outs") is not None else linescore.get("outs"),
                "batter": batter_name,
                "pitcher": pitcher_name,
                "batter_id": str(batter_id or ""),
                "pitcher_id": str(pitcher_id or ""),
                "batter_headshot": f"{MLB_HEADSHOT_BASE}/{batter_id}/headshot/67/current" if batter_id else None,
                "pitcher_headshot": f"{MLB_HEADSHOT_BASE}/{pitcher_id}/headshot/67/current" if pitcher_id else None,
                "first_base": first_base,
                "second_base": second_base,
                "third_base": third_base,
            }
            detail["situations"] = [current_situation]


        # For MLB, replace generic recursive matches with a clean, game-specific
        # model from the official live box score. This prevents unrelated team,
        # league and season metadata from appearing as lineups or game stats.
        if self.league == "mlb" and mlb_live_data:
            live_box = mlb_live_data.get("boxscore") if isinstance(mlb_live_data.get("boxscore"), dict) else {}
            live_teams = live_box.get("teams") if isinstance(live_box.get("teams"), dict) else {}
            clean_players: list[dict[str, Any]] = []
            clean_lineups: list[dict[str, Any]] = []
            clean_stats: list[dict[str, Any]] = []

            for side in ("away", "home"):
                team_box = live_teams.get(side) if isinstance(live_teams.get(side), dict) else {}
                team_info = team_box.get("team") if isinstance(team_box.get("team"), dict) else {}
                team_name = team_info.get("name") or side.title()
                player_map = team_box.get("players") if isinstance(team_box.get("players"), dict) else {}

                team_stats = team_box.get("teamStats") if isinstance(team_box.get("teamStats"), dict) else {}
                for group_name in ("batting", "pitching", "fielding"):
                    group = team_stats.get(group_name)
                    if isinstance(group, dict):
                        row = {"name": f"{team_name} {group_name.title()}", "team_name": team_name, "group": group_name}
                        for key, value in group.items():
                            if not isinstance(value, (dict, list)):
                                row[key] = value
                        clean_stats.append(row)

                for player in player_map.values():
                    if not isinstance(player, dict):
                        continue
                    person = player.get("person") if isinstance(player.get("person"), dict) else {}
                    position = player.get("position") if isinstance(player.get("position"), dict) else {}
                    name = person.get("fullName") or person.get("name")
                    if not name:
                        continue
                    player_id = str(person.get("id") or "")
                    base = {
                        "id": player_id,
                        "full_name": name,
                        "team_name": team_name,
                        "side": side,
                        "position_abbreviation": position.get("abbreviation") or position.get("code"),
                        "position_name": position.get("name"),
                        "jersey_number": player.get("jerseyNumber"),
                        "batting_order": player.get("battingOrder"),
                        "game_status": player.get("gameStatus"),
                        "headshot": f"{MLB_HEADSHOT_BASE}/{player_id}/headshot/67/current" if player_id else None,
                    }
                    clean_players.append(base)

                    if player.get("battingOrder"):
                        lineup = dict(base)
                        try:
                            lineup["batting_spot"] = int(str(player.get("battingOrder"))) // 100
                        except (TypeError, ValueError):
                            lineup["batting_spot"] = player.get("battingOrder")
                        clean_lineups.append(lineup)

                    player_stats = player.get("stats") if isinstance(player.get("stats"), dict) else {}
                    for group_name in ("batting", "pitching", "fielding"):
                        group = player_stats.get(group_name)
                        if not isinstance(group, dict) or not group:
                            continue
                        row = {
                            "name": name,
                            "full_name": name,
                            "player_id": player_id,
                            "headshot": base.get("headshot"),
                            "team_name": team_name,
                            "position_abbreviation": base.get("position_abbreviation"),
                            "group": group_name,
                        }
                        for key, value in group.items():
                            if not isinstance(value, (dict, list)):
                                row[key] = value
                        clean_stats.append(row)

            clean_lineups.sort(
                key=lambda row: (
                    0 if row.get("side") == "away" else 1,
                    row.get("batting_spot") if isinstance(row.get("batting_spot"), int) else 99,
                )
            )
            detail["players"] = clean_players
            detail["lineups"] = clean_lineups
            detail["statistics"] = clean_stats

            officials = live_box.get("officials") if isinstance(live_box.get("officials"), list) else []
            clean_officials: list[dict[str, Any]] = []
            for item in officials:
                if not isinstance(item, dict):
                    continue
                official = item.get("official") if isinstance(item.get("official"), dict) else {}
                clean_officials.append(
                    {
                        "name": official.get("fullName") or official.get("name") or "Official",
                        "official_type": item.get("officialType"),
                    }
                )
            detail["officials"] = clean_officials

            plays_root = mlb_live_data.get("plays") if isinstance(mlb_live_data.get("plays"), dict) else {}
            all_mlb_plays = plays_root.get("allPlays") if isinstance(plays_root.get("allPlays"), list) else []
            clean_scoring: list[dict[str, Any]] = []
            player_directory = (
                mlb_game_data.get("players")
                if isinstance(mlb_game_data.get("players"), dict)
                else {}
            )
            for play in all_mlb_plays:
                if not isinstance(play, dict):
                    continue
                about = play.get("about") if isinstance(play.get("about"), dict) else {}
                if not about.get("isScoringPlay"):
                    continue
                result = play.get("result") if isinstance(play.get("result"), dict) else {}
                matchup = play.get("matchup") if isinstance(play.get("matchup"), dict) else {}
                batter = matchup.get("batter") if isinstance(matchup.get("batter"), dict) else {}
                scoring_player_id = str(batter.get("id") or "")
                # Some completed-game play records omit matchup.batter. Their
                # credited player still appears in play.players; use it so a
                # scoring summary always has an ID for its portrait.
                if not scoring_player_id:
                    credits = play.get("players") if isinstance(play.get("players"), list) else []
                    credited = next(
                        (
                            item.get("player") for item in credits
                            if isinstance(item, dict)
                            and isinstance(item.get("player"), dict)
                            and str(item.get("playerType") or "").lower()
                            in {"batter", "hitter", "scorer"}
                        ),
                        {},
                    )
                    scoring_player_id = str(credited.get("id") or "") if isinstance(credited, dict) else ""
                # Historical/final feeds can provide neither matchup nor a
                # credited-player record, while the scorer's name remains in
                # the result description (for example, "Jose Altuve singles").
                # Resolve it against the official player directory so the
                # portrait always gets an MLB player ID.
                if not scoring_player_id:
                    description = str(result.get("description") or "").casefold()
                    directory_matches = []
                    for key, candidate in player_directory.items():
                        if not isinstance(candidate, dict):
                            continue
                        candidate_name = str(
                            candidate.get("fullName") or candidate.get("name") or ""
                        ).strip()
                        if candidate_name and candidate_name.casefold() in description:
                            directory_matches.append((len(candidate_name), key, candidate))
                    if directory_matches:
                        _, matched_key, matched_player = max(directory_matches)
                        scoring_player_id = str(
                            matched_player.get("id")
                            or str(matched_key).removeprefix("ID")
                        )
                directory_player = (
                    player_directory.get(f"ID{scoring_player_id}")
                    or player_directory.get(scoring_player_id)
                    or {}
                )
                scoring_name = (
                    batter.get("fullName")
                    or batter.get("name")
                    or directory_player.get("fullName")
                    or directory_player.get("name")
                )
                clean_scoring.append(
                    {
                        "description": result.get("description") or result.get("event"),
                        "event": result.get("event"),
                        "inning": about.get("inning"),
                        "half_inning": about.get("halfInning"),
                        "away_score": result.get("awayScore"),
                        "home_score": result.get("homeScore"),
                        "rbi": result.get("rbi"),
                        "id": scoring_player_id,
                        "player_id": scoring_player_id,
                        "player_name": scoring_name,
                        "headshot": f"{MLB_HEADSHOT_BASE}/{scoring_player_id}/headshot/67/current" if scoring_player_id else None,
                    }
                )
            detail["scoring"] = clean_scoring

            venue = mlb_game_data.get("venue") if isinstance(mlb_game_data.get("venue"), dict) else {}
            if venue:
                location = venue.get("location") if isinstance(venue.get("location"), dict) else {}
                detail["stadium"] = {
                    "name": venue.get("name"),
                    "city": location.get("city"),
                    "state": location.get("stateAbbrev") or location.get("state"),
                }

        if self.league == "mlb":
            # The panel uses this to reject generic nested TS records. Showing
            # no value is preferable to displaying another game's venue,
            # players or statistics under the selected matchup.
            detail["event"]["mlb_live_verified"] = bool(mlb_live_data)

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
