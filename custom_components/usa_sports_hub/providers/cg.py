"""Unified CG provider for NFL, NBA, MLB and NHL."""
from __future__ import annotations

from datetime import datetime, timedelta, timezone
from typing import Any
from urllib.parse import urlencode

from .base import ProviderClient
from .models import (
    compact_cg_news,
    normalize_cg_event,
    normalize_cg_standing,
    normalize_cg_team,
)


API_BASE = "https://api." + "the" + "score.com"
WEB_API_BASE = "https://www." + "the" + "score.com/api"


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


class CGProvider(ProviderClient):
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
            normalize_cg_event(item, self.league)
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
        return [normalize_cg_standing(item, self.league) for item in rows]

    async def async_news(self) -> list[dict[str, Any]]:
        # CG event payloads expose preview/recap metadata.  This keeps the
        # integration entirely off ESPN while still supplying useful league news.
        payload = await self.async_get_json(self._events_url(past_days=7, future_days=2))
        return compact_cg_news(payload if isinstance(payload, list) else [])

    async def async_teams(self) -> list[dict[str, Any]]:
        standings = await self.async_get_json(f"{self.base}/standings")
        teams: dict[str, dict[str, Any]] = {}
        if isinstance(standings, list):
            for row in standings:
                team = row.get("team") if isinstance(row, dict) else None
                if isinstance(team, dict) and team.get("id") is not None:
                    normalized = normalize_cg_team(team)
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
                        normalized = normalize_cg_team(team)
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
            "event": normalize_cg_event(event, self.league),
            "box_score": box_score if isinstance(box_score, dict) else {},
            "drives": [],
            "play_by_play": [],
            "scoring": [],
            "players": [],
            "injuries": [],
            "lineups": [],
            "statistics": [],
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

        # Pull useful compact collections from the event + box-score tree.
        combined = {"event": event, "box_score": box_score, "drives": detail["drives"]}
        detail["scoring"] = _objects_with_keys(
            combined, {"score_summary", "scoring_play", "scoring_type", "goal_type"}, 80
        )
        detail["players"] = _objects_with_keys(
            combined, {"full_name", "first_initial_and_last_name", "position_abbreviation"}, 100
        )
        detail["injuries"] = _objects_with_keys(
            combined, {"date_injured", "return_date", "injury"}, 60
        )
        detail["lineups"] = _objects_with_keys(
            combined, {"lineup", "batting_order", "starter"}, 80
        )
        detail["statistics"] = _objects_with_keys(
            combined,
            {
                "passing_yards", "rushing_yards", "receiving_yards",
                "points", "rebounds", "assists", "shots", "hits",
                "runs", "earned_runs", "strikeouts", "saves",
            },
            100,
        )

        # Keep the live sensor useful but bounded.
        detail["play_by_play"] = detail["play_by_play"][-120:]
        return detail


class NflProvider(CGProvider):
    def __init__(self, session):
        super().__init__(session, "nfl")


class NbaProvider(CGProvider):
    def __init__(self, session):
        super().__init__(session, "nba")


class MlbProvider(CGProvider):
    def __init__(self, session):
        super().__init__(session, "mlb")


class NhlProvider(CGProvider):
    def __init__(self, session):
        super().__init__(session, "nhl")
