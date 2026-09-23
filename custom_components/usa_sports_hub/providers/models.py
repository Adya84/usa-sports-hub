"""Small provider-independent models safe to expose through Home Assistant."""
from __future__ import annotations

from typing import Any


LIVE_STATES = {"in", "live", "critical", "inprogress"}


def _number(value: Any) -> int | None:
    try:
        return int(value)
    except (TypeError, ValueError):
        return None


def game_from_espn(event: dict[str, Any], sport: str, league: str) -> dict[str, Any]:
    """Normalize one ESPN scoreboard event without carrying raw payloads."""
    competition = (event.get("competitions") or [{}])[0] or {}
    home = next((item for item in competition.get("competitors", []) if item.get("homeAway") == "home"), {}) or {}
    away = next((item for item in competition.get("competitors", []) if item.get("homeAway") == "away"), {}) or {}
    status_type = ((event.get("status") or {}).get("type") or {})
    state = str(status_type.get("state") or "").lower()
    return {
        "game_id": str(event.get("id") or ""), "sport": sport, "league": league,
        "home_team": (home.get("team") or {}).get("displayName") or "Home", "home_team_id": str((home.get("team") or {}).get("id") or ""),
        "home_abbreviation": (home.get("team") or {}).get("abbreviation") or "", "home_logo": ((home.get("team") or {}).get("logos") or [{}])[0].get("href"), "home_score": _number(home.get("score")),
        "away_team": (away.get("team") or {}).get("displayName") or "Away", "away_team_id": str((away.get("team") or {}).get("id") or ""),
        "away_abbreviation": (away.get("team") or {}).get("abbreviation") or "", "away_logo": ((away.get("team") or {}).get("logos") or [{}])[0].get("href"), "away_score": _number(away.get("score")),
        "status": status_type.get("name") or state or "scheduled", "status_detail": status_type.get("shortDetail") or "Scheduled",
        "is_live": state in LIVE_STATES, "is_final": bool(status_type.get("completed")), "start_time": event.get("date"),
        "period": status_type.get("period"), "clock": status_type.get("displayClock"), "venue": (competition.get("venue") or {}).get("fullName"),
        "broadcasts": [item.get("names", [""])[0] for item in competition.get("broadcasts", []) if item.get("names")],
    }


def standing(team: str, rank: int | None, record: str = "", logo: str | None = None) -> dict[str, Any]:
    return {"team": team, "rank": rank, "record": record, "logo": logo}
