"""Provider-independent normalizers for TS payloads."""
from __future__ import annotations

from typing import Any


LIVE_STATES = {
    "in_progress", "inprogress", "live", "critical", "in", "playing",
    "started", "active", "ongoing",
}


def _status_key(value: Any) -> str:
    """Normalise provider status strings for reliable live detection."""
    return str(value or "").strip().lower().replace("-", "_").replace(" ", "_")


def _number(value: Any) -> int | float | None:
    try:
        number = float(value)
        return int(number) if number.is_integer() else number
    except (TypeError, ValueError):
        return None


def _logo(team: dict[str, Any]) -> str | None:
    logos = team.get("logos") if isinstance(team.get("logos"), dict) else {}
    return logos.get("w72xh72") or logos.get("small") or logos.get("large")


def normalize_ts_team(team: dict[str, Any]) -> dict[str, Any]:
    location = str(team.get("location") or "")
    canada = {
        "Toronto", "Vancouver", "Montreal", "Montréal", "Ottawa",
        "Calgary", "Edmonton", "Winnipeg",
    }
    return {
        "id": str(team.get("id") or ""),
        "name": team.get("full_name") or team.get("name") or "Team",
        "short_name": team.get("short_name") or team.get("abbreviation") or "",
        "abbreviation": team.get("abbreviation") or team.get("short_name") or "",
        "location": location,
        "conference": team.get("conference"),
        "division": team.get("division"),
        "colour_1": team.get("colour_1"),
        "colour_2": team.get("colour_2"),
        "logo": _logo(team),
        "has_injuries": bool(team.get("has_injuries")),
        "has_rosters": bool(team.get("has_rosters")),
        "has_extra_info": bool(team.get("has_extra_info")),
        "country": "canada" if location in canada else "usa",
        "api_uri": team.get("api_uri"),
    }


def _team_collection(value: Any) -> list[dict[str, Any]]:
    """Return only provider rows that are safe to expose as compact data."""
    return [row for row in value if isinstance(row, dict)] if isinstance(value, list) else []


def _team_headshot(player: dict[str, Any]) -> str | None:
    headshots = player.get("headshots") if isinstance(player.get("headshots"), dict) else {}
    return (
        headshots.get("w192xh192")
        or headshots.get("small")
        or headshots.get("large")
        or player.get("headshot")
    )


def _team_person(row: dict[str, Any]) -> dict[str, Any]:
    person = row.get("player") if isinstance(row.get("player"), dict) else row
    return {
        "player_name": person.get("full_name") or person.get("first_initial_and_last_name") or person.get("name") or "Player",
        "headshot": _team_headshot(person),
        "position": person.get("position_abbreviation") or person.get("position") or "",
    }


def _compact_team_statistics(rows: Any) -> list[dict[str, Any]]:
    result = []
    for row in _team_collection(rows)[:80]:
        if not row:
            continue
        person = _team_person(row)
        label = row.get("category") or row.get("stat_name") or row.get("stat") or row.get("name")
        value = row.get("value") or row.get("display_value") or row.get("stat_value") or ""
        if not label and not value and person["player_name"] == "Player":
            continue
        result.append({
            **person,
            "name": person["player_name"],
            "label": label or "Season statistic",
            "value": value,
        })
    return result


def _compact_team_leaders(rows: Any) -> list[dict[str, Any]]:
    result = []
    for row in _team_collection(rows)[:24]:
        if not row:
            continue
        person = _team_person(row)
        label = row.get("category") or row.get("label") or row.get("stat_name")
        value = row.get("stat") or row.get("value") or row.get("display_value") or row.get("stat_value") or ""
        if not label and not value and person["player_name"] == "Player":
            continue
        result.append({
            **person,
            "name": person["player_name"],
            "label": label or "Leader",
            "value": value,
        })
    return result


def _compact_team_injuries(rows: Any) -> list[dict[str, Any]]:
    result = []
    for row in _team_collection(rows)[:40]:
        if not row:
            continue
        person = _team_person(row)
        status = row.get("status") or row.get("injury_status") or row.get("injury")
        if not status and person["player_name"] == "Player":
            continue
        result.append({
            **person,
            "name": person["player_name"],
            "status": status or "Injury report",
            "note": row.get("description") or row.get("injury_note") or "",
        })
    return result


def normalize_ts_team_detail(
    league: str,
    profile: Any,
    squad: Any,
    statistics: Any,
    leaders: Any,
    injuries: Any,
) -> dict[str, Any]:
    """Normalize one team's dedicated TS endpoints into stable panel data."""
    profile = profile if isinstance(profile, dict) else {}
    standing = profile.get("standing") if isinstance(profile.get("standing"), dict) else {}
    compact_squad = []
    for player in _team_collection(squad):
        compact_squad.append(
            {
                "player_id": str(player.get("id") or ""),
                "name": player.get("full_name") or player.get("first_initial_and_last_name") or "Player",
                "number": player.get("number"),
                "position": player.get("position") or player.get("position_abbreviation") or "",
                "position_abbreviation": player.get("position_abbreviation") or "",
                "headshot": _team_headshot(player),
                "injury": player.get("injury") if isinstance(player.get("injury"), dict) else None,
                "season_stats": player.get("season_stats") if isinstance(player.get("season_stats"), dict) else {},
            }
        )
    return {
        "profile": {
            "team_id": str(profile.get("id") or ""),
            "name": profile.get("full_name") or profile.get("name") or "Team",
            "abbreviation": profile.get("abbreviation") or profile.get("short_name") or "",
            "logo": _logo(profile),
            "conference": profile.get("conference"),
            "division": profile.get("division"),
            "location": profile.get("location"),
            "colour_1": profile.get("colour_1"),
            "colour_2": profile.get("colour_2"),
            "standing": standing,
            "extra": _team_collection(profile.get("team_extra_info")),
        },
        "squad": compact_squad,
        "statistics": _compact_team_statistics(statistics),
        "leaders": _compact_team_leaders(leaders),
        "injuries": _compact_team_injuries(injuries),
        "league": league.upper(),
    }
def normalize_ts_event(event: dict[str, Any], league: str) -> dict[str, Any]:
    home = event.get("home_team") if isinstance(event.get("home_team"), dict) else {}
    away = event.get("away_team") if isinstance(event.get("away_team"), dict) else {}
    box = event.get("box_score") if isinstance(event.get("box_score"), dict) else {}
    progress = box.get("progress") if isinstance(box.get("progress"), dict) else {}
    score = box.get("score") if isinstance(box.get("score"), dict) else {}
    home_score = score.get("home") if isinstance(score.get("home"), dict) else {}
    away_score = score.get("away") if isinstance(score.get("away"), dict) else {}
    state = _status_key(event.get("event_status") or event.get("status"))
    progress_state = _status_key(progress.get("event_status") or progress.get("status"))
    final = state in {"final", "completed", "complete"} or progress_state in {"final", "completed", "complete"}

    # Some league feeds report the event itself as pre-game while the nested
    # box-score progress object already shows an active period/clock. Treat
    # either source as authoritative for live state so live games are not lost.
    has_live_progress = bool(
        progress
        and not final
        and (
            progress_state in LIVE_STATES
            or progress.get("clock") not in (None, "")
            or progress.get("segment") not in (None, "", 0)
            or progress.get("segment_string")
            or progress.get("segment_description")
        )
    )
    is_live = (state in LIVE_STATES or progress_state in LIVE_STATES or has_live_progress) and not final

    tv = event.get("tv_listings_by_country_code")
    broadcasts: list[str] = []
    if isinstance(tv, dict):
        for listings in tv.values():
            if isinstance(listings, list):
                for item in listings:
                    if isinstance(item, dict):
                        name = item.get("long_name") or item.get("short_name")
                        if name and name not in broadcasts:
                            broadcasts.append(str(name))

    standings = event.get("standings") if isinstance(event.get("standings"), dict) else {}
    odd = event.get("odd") if isinstance(event.get("odd"), dict) else {}
    stadium = event.get("stadium_details") if isinstance(event.get("stadium_details"), dict) else {}

    return {
        "game_id": str(event.get("id") or ""),
        "sport": league,
        "league": league.upper(),
        "home_team": home.get("full_name") or home.get("name") or "Home",
        "home_team_id": str(home.get("id") or ""),
        "home_abbreviation": home.get("abbreviation") or home.get("short_name") or "",
        "home_logo": _logo(home),
        "home_colour": home.get("colour_1"),
        "home_score": _number(home_score.get("score")),
        "away_team": away.get("full_name") or away.get("name") or "Away",
        "away_team_id": str(away.get("id") or ""),
        "away_abbreviation": away.get("abbreviation") or away.get("short_name") or "",
        "away_logo": _logo(away),
        "away_colour": away.get("colour_1"),
        "away_score": _number(away_score.get("score")),
        "status": event.get("event_status") or event.get("status") or "pre_game",
        "status_detail": progress.get("clock_label") or progress.get("string") or event.get("game_description") or str(event.get("event_status") or "Pre Game"),
        "is_live": is_live,
        "is_final": final,
        "start_time": event.get("game_date"),
        "game_type": event.get("game_type"),
        "period": progress.get("segment"),
        "period_label": progress.get("segment_string") or progress.get("segment_description"),
        "clock": progress.get("clock"),
        "overtime": bool(progress.get("overtime")),
        "shootout": bool(progress.get("shootout")),
        "venue": event.get("stadium"),
        "location": event.get("location"),
        "broadcasts": broadcasts,
        "has_lineups": bool(event.get("has_lineups")),
        "has_injuries": bool(event.get("has_injuries")),
        "has_pitcher_and_batter": bool(event.get("has_pitcher_and_batter")),
        "has_play_by_play_records": bool(event.get("has_play_by_play_records")),
        "box_score_id": box.get("id"),
        "box_score_uri": box.get("api_uri"),
        "has_statistics": bool(box.get("has_statistics")),
        "balls": box.get("balls"),
        "strikes": box.get("strikes"),
        "outs": box.get("outs"),
        "first_base": box.get("first_base"),
        "second_base": box.get("second_base"),
        "third_base": box.get("third_base"),
        "home_strength": box.get("home_strength"),
        "away_strength": box.get("away_strength"),
        "team_on_power_play": box.get("team_on_power_play"),
        "home_standing": standings.get("home"),
        "away_standing": standings.get("away"),
        "odds": {
            "line": odd.get("line"),
            "over_under": odd.get("over_under"),
            "closing": odd.get("closing"),
            "api_uri": odd.get("api_uri"),
        } if odd else {},
        "stadium_details": {
            "id": stadium.get("id"),
            "name": stadium.get("name"),
            "city": stadium.get("city"),
            "state": stadium.get("state"),
            "api_uri": stadium.get("api_uri"),
            "diagrams": stadium.get("diagrams"),
        } if stadium else {},
        "preview": event.get("preview_data") or {},
        "recap": event.get("recap_data") or {},
        "api_uri": event.get("api_uri"),
    }


def normalize_ts_standing(row: dict[str, Any], league: str) -> dict[str, Any]:
    team = row.get("team") if isinstance(row.get("team"), dict) else {}
    normalized_team = normalize_ts_team(team)
    record = row.get("short_record")
    if not record:
        wins, losses = row.get("wins"), row.get("losses")
        overtime_losses = row.get("overtime_losses")
        if overtime_losses is not None:
            record = f"{wins or 0}-{losses or 0}-{overtime_losses or 0}"
        elif wins is not None or losses is not None:
            record = f"{wins or 0}-{losses or 0}"

    return {
        "id": str(row.get("id") or ""),
        "team": normalized_team["name"],
        "team_id": normalized_team["id"],
        "abbreviation": normalized_team["abbreviation"],
        "logo": normalized_team["logo"],
        "rank": row.get("place") or row.get("league_rank") or row.get("conference_rank") or row.get("division_rank"),
        "formatted_rank": row.get("formatted_rank"),
        "record": record or "",
        "wins": row.get("wins"),
        "losses": row.get("losses"),
        "overtime_losses": row.get("overtime_losses"),
        "points": row.get("points"),
        "winning_percentage": row.get("winning_percentage"),
        "conference": row.get("conference"),
        "conference_rank": row.get("conference_rank") or row.get("conference_ranking"),
        "division": row.get("division"),
        "division_rank": row.get("division_rank") or row.get("division_ranking"),
        "games_back": row.get("games_back"),
        "wild_card_games_back": row.get("wc_games_back"),
        "is_wild_card": row.get("is_wild_card"),
        "playoff_seed": row.get("playoff_seed"),
        "clinched_division": bool(row.get("clinched_division")),
        "clinched_playoffs": bool(row.get("clinched_playoffs") or row.get("clinched_playoff_spot")),
        "eliminated_from_playoffs": row.get("eliminated_from_playoffs"),
        "last_ten": row.get("last_ten_games_record"),
        "streak": row.get("streak"),
        "home_record": row.get("short_home_record"),
        "away_record": row.get("short_away_record") or row.get("short_road_record"),
        "runs_scored": row.get("runs_scored"),
        "runs_allowed": row.get("runs_allowed"),
        "runs_differential": row.get("runs_differential"),
        "goals_for": row.get("goals_for") or row.get("goal_for"),
        "goals_against": row.get("goals_against"),
        "goal_differential": row.get("goal_differential"),
        "season_type": row.get("season_type"),
        "season": (row.get("season") or {}).get("short_name") if isinstance(row.get("season"), dict) else None,
        "api_uri": row.get("api_uri"),
        "league": league.upper(),
    }


def compact_ts_news(events: list[dict[str, Any]]) -> list[dict[str, Any]]:
    """Build recorder-safe preview/recap cards from event metadata."""
    result: list[dict[str, Any]] = []
    seen: set[str] = set()
    for event in reversed(events):
        if not isinstance(event, dict):
            continue
        for key, uri_key, kind in (
            ("recap_data", "recap", "recap"),
            ("preview_data", "preview", "preview"),
        ):
            article = event.get(key)
            if not isinstance(article, dict):
                continue
            title = str(article.get("headline") or "").strip()
            if not title or title in seen:
                continue
            seen.add(title)
            uri = event.get(uri_key)
            result.append(
                {
                    "title": title,
                    "summary": str(article.get("abstract") or "")[:400],
                    "url": "https://www." + "the" + "score.com" + uri if isinstance(uri, str) and uri.startswith("/") else None,
                    "kind": kind,
                    "game_id": str(event.get("id") or ""),
                    "published": event.get("updated_at"),
                }
            )
            if len(result) >= 20:
                return result
    return result
