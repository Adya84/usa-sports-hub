"""Coordinator for the USA Sports Hub TS provider set."""
from __future__ import annotations

import asyncio
import logging
from datetime import datetime, timedelta, timezone

from homeassistant.helpers.aiohttp_client import async_get_clientsession
from homeassistant.helpers.storage import Store
from homeassistant.helpers.update_coordinator import DataUpdateCoordinator

from .providers.base import ProviderError
from .providers.ts import MlbProvider, NbaProvider, NflProvider, NhlProvider

_LOGGER = logging.getLogger(__name__)
SPORTS = ("nfl", "nba", "mlb", "nhl")
# Keep the existing on-disk cache readable. New team keys have safe defaults
# during restore, so a storage migration is not required for this additive schema.
CACHE_VERSION = 1
CACHE_SAVE_DELAY_SECONDS = 15
GAME_DETAIL_TIMEOUT_SECONDS = 8


class UsaSportsCoordinator(DataUpdateCoordinator):
    """Refresh TS independently for each sport and retain last good data."""

    def __init__(self, hass, entry):
        self.entry = entry
        self._store = Store(hass, CACHE_VERSION, f"{entry.entry_id}_sports_cache")
        self.selected_live_game_id = None
        self.selected_live_sport = None
        stored_favourites = entry.options.get("team_favourites", [])
        self.team_favourites = [
            {"sport": str(item.get("sport") or "").lower(), "team_id": str(item.get("team_id") or ""), "team": str(item.get("team") or "")}
            for item in stored_favourites
            if isinstance(item, dict) and str(item.get("sport") or "").lower() in SPORTS and str(item.get("team_id") or "").strip()
        ][:3]
        self.selected_team_ids = {
            item["sport"]: item["team_id"] for item in self.team_favourites
        }
        session = async_get_clientsession(hass)
        self.providers = {
            "nfl": NflProvider(session),
            "nba": NbaProvider(session),
            "mlb": MlbProvider(session),
            "nhl": NhlProvider(session),
        }
        self.cache = {
            sport: {
                "games": [],
                "standings": [],
                "news": [],
                "teams": [],
                "ticker": [],
                "detail": {},
                "details": {},
                "team_details": {},
                "error": None,
            }
            for sport in SPORTS
        }
        super().__init__(
            hass,
            _LOGGER,
            name="USA Sports Hub",
            update_interval=timedelta(minutes=10),
        )

    async def async_restore_cache(self) -> bool:
        """Restore the last successful sports payload before polling again."""
        stored = await self._store.async_load()
        cached_sports = stored.get("sports") if isinstance(stored, dict) else None
        if not isinstance(cached_sports, dict):
            return False

        restored = 0
        for sport in SPORTS:
            item = cached_sports.get(sport)
            if not isinstance(item, dict):
                continue
            self.cache[sport] = {
                **self.cache[sport],
                **{key: item.get(key, self.cache[sport][key]) for key in self.cache[sport]},
                "error": None,
            }
            restored += 1

        if not restored:
            return False
        self.async_set_updated_data(self._compose_data())
        _LOGGER.debug("Restored USA Sports Hub cache for %s sports", restored)
        return True

    def _schedule_cache_save(self) -> None:
        """Persist successful data without making the update loop wait on disk."""
        self._store.async_delay_save(
            lambda: {"sports": self.cache}, CACHE_SAVE_DELAY_SECONDS
        )

    def _store_game_detail(self, sport: str, game_id: str, detail: dict) -> None:
        """Keep a bounded, per-game snapshot without sharing one game's data."""
        details = dict(self.cache[sport].get("details") or {})
        details[str(game_id)] = detail
        # Retain recent opened games, while keeping Home Assistant state/cache small.
        while len(details) > 12:
            details.pop(next(iter(details)))
        self.cache[sport] = {**self.cache[sport], "detail": detail, "details": details}

    def _team_cache_key(self, sport: str, team_id: str) -> tuple[str, str]:
        sport = str(sport or "").lower()
        team_id = str(team_id or "").strip()
        if sport not in SPORTS or not team_id:
            raise ValueError("Supported sport and team ID are required")
        return sport, team_id

    def _store_team_detail(self, sport: str, team_id: str, detail: dict, error: str | None = None) -> None:
        details = dict(self.cache[sport].get("team_details") or {})
        previous = details.get(team_id) or {}
        details[team_id] = {
            **previous,
            **(detail or {}),
            "updated": datetime.now(timezone.utc).isoformat(),
            "error": error,
        }
        while len(details) > 6:
            details.pop(next(iter(details)))
        self.cache[sport] = {**self.cache[sport], "team_details": details}

    def _save_team_favourites(self) -> None:
        self.hass.config_entries.async_update_entry(
            self.entry,
            options={**self.entry.options, "team_favourites": self.team_favourites},
        )

    async def async_select_team(self, sport: str, team_id: str) -> None:
        sport, team_id = self._team_cache_key(sport, team_id)
        self.selected_team_ids[sport] = team_id
        self.async_set_updated_data(self._compose_data())
        try:
            detail = await self.providers[sport].async_team_detail(team_id)
            self._store_team_detail(sport, team_id, detail)
        except (ProviderError, ValueError, KeyError, TypeError) as err:
            self._store_team_detail(sport, team_id, {}, str(err))
        self._schedule_cache_save()
        self.async_set_updated_data(self._compose_data())

    async def async_add_team_favourite(self, sport: str, team_id: str, team: str) -> None:
        sport, team_id = self._team_cache_key(sport, team_id)
        record = {"sport": sport, "team_id": team_id, "team": str(team or "").strip() or "Team"}
        if not any(item["sport"] == sport and item["team_id"] == team_id for item in self.team_favourites):
            if len(self.team_favourites) >= 3:
                raise ValueError("A maximum of three favourite teams is supported")
            self.team_favourites.append(record)
            self._save_team_favourites()
        await self.async_select_team(sport, team_id)

    async def async_remove_team_favourite(self, sport: str, team_id: str) -> None:
        sport, team_id = self._team_cache_key(sport, team_id)
        self.team_favourites = [item for item in self.team_favourites if (item["sport"], item["team_id"]) != (sport, team_id)]
        self.cache[sport] = {
            **self.cache[sport],
            "team_details": {key: value for key, value in (self.cache[sport].get("team_details") or {}).items() if key != team_id},
        }
        if self.selected_team_ids.get(sport) == team_id:
            self.selected_team_ids.pop(sport, None)
        self._save_team_favourites()
        self._schedule_cache_save()
        self.async_set_updated_data(self._compose_data())

    async def _refresh_sport(self, sport):
        provider = self.providers[sport]
        try:
            games, table, news, teams, ticker = await asyncio.gather(
                provider.async_schedule(),
                provider.async_standings(),
                provider.async_news(),
                provider.async_teams(),
                provider.async_ticker(),
            )

            live = [game for game in games if game.get("is_live")]
            upcoming = [
                game for game in games
                if not game.get("is_live") and not game.get("is_final")
            ]
            finished = [game for game in games if game.get("is_final")]
            selected = None
            if self.selected_live_sport == sport and self.selected_live_game_id:
                selected = next(
                    (game for game in games if str(game.get("game_id")) == str(self.selected_live_game_id)),
                    None,
                )
            detail_target = (
                selected if selected
                else live[0] if live
                else upcoming[0] if upcoming
                else finished[-1] if finished
                else None
            )
            detail = {}
            if detail_target and detail_target.get("game_id"):
                try:
                    detail = await provider.async_game_detail(detail_target["game_id"])
                except (ProviderError, ValueError, KeyError, TypeError) as err:
                    _LOGGER.debug(
                        "%s detailed game refresh failed: %s", sport.upper(), err
                    )

            previous_details = self.cache[sport].get("details") or {}
            previous_team_details = self.cache[sport].get("team_details") or {}
            self.cache[sport] = {
                "games": games,
                "standings": table,
                "news": news,
                "teams": teams,
                "ticker": ticker,
                "detail": detail,
                "details": previous_details,
                "team_details": previous_team_details,
                "error": None,
            }
            if detail and detail_target and detail_target.get("game_id"):
                self._store_game_detail(sport, str(detail_target["game_id"]), detail)
            self._schedule_cache_save()
        except (ProviderError, ValueError, KeyError, TypeError) as err:
            self.cache[sport] = {**self.cache[sport], "error": str(err)}
            _LOGGER.warning("%s TS refresh failed: %s", sport.upper(), err)

    def _compose_data(self):
        """Build coordinator output from the current cache without network I/O."""
        sports = {}
        live_any = False
        for sport, item in self.cache.items():
            games = item["games"]
            live = [game for game in games if game.get("is_live")]
            upcoming = [
                game for game in games
                if not game.get("is_live") and not game.get("is_final")
            ]
            finished = [game for game in games if game.get("is_final")]
            live_any |= bool(live)
            selected_detail_id = (
                str(self.selected_live_game_id)
                if self.selected_live_sport == sport and self.selected_live_game_id
                else ""
            )
            detail = (
                (item.get("details") or {}).get(selected_detail_id)
                or item.get("detail")
                or {}
            )
            selected_team_id = self.selected_team_ids.get(sport, "")
            selected_team = (item.get("team_details") or {}).get(selected_team_id) or {}
            sports[sport] = {
                **item,
                "live": live,
                "fixtures": upcoming,
                "results": finished,
                "next_game": upcoming[0] if upcoming else None,
                "latest_result": finished[-1] if finished else None,
                "game_detail": detail.get("event") or {},
                "box_score": detail.get("box_score") or {},
                "play_by_play": detail.get("play_by_play") or [],
                "drives": detail.get("drives") or [],
                "scoring": detail.get("scoring") or [],
                "players": detail.get("players") or [],
                "injuries": detail.get("injuries") or [],
                "lineups": detail.get("lineups") or [],
                "statistics": detail.get("statistics") or [],
                "leaders": detail.get("leaders") or [],
                "periods": detail.get("periods") or [],
                "officials": detail.get("officials") or [],
                "situations": detail.get("situations") or [],
                "related": detail.get("related") or [],
                "odds": detail.get("odds") or {},
                "stadium": detail.get("stadium") or {},
                "team_profile": selected_team.get("profile") or {},
                "team_squad": selected_team.get("squad") or [],
                "team_statistics": selected_team.get("statistics") or [],
                "team_leaders": selected_team.get("leaders") or [],
                "team_injuries": selected_team.get("injuries") or [],
                "team_selected_id": selected_team_id,
                "team_error": selected_team.get("error"),
                "team_updated": selected_team.get("updated"),
            }
        return {
            "sports": sports,
            "live_polling": live_any,
            "provider": "TS",
        }

    async def async_set_selected_live_match(self, fixture_id, sport=None):
        """Select a game and load only that game's detail feed."""
        game_id = str(fixture_id or "").strip()
        if not game_id:
            self.selected_live_game_id = None
            self.selected_live_sport = None
            return

        requested_sport = str(sport or "").strip().lower()
        matched_sport = requested_sport if requested_sport in self.providers else None
        if not matched_sport:
            for candidate_sport, item in self.cache.items():
                if any(str(game.get("game_id") or "") == game_id for game in item.get("games", []) or []):
                    matched_sport = candidate_sport
                    break

        self.selected_live_game_id = game_id
        self.selected_live_sport = matched_sport
        if matched_sport:
            # Render this game's own stored snapshot when it exists. Otherwise
            # clear detail while it loads; never show another fixture's data.
            cached_detail = (self.cache[matched_sport].get("details") or {}).get(game_id) or {}
            self.cache[matched_sport] = {
                **self.cache[matched_sport],
                "detail": cached_detail,
                "error": None,
            }
            self.async_set_updated_data(self._compose_data())
            try:
                detail = await asyncio.wait_for(
                    self.providers[matched_sport].async_game_detail(game_id),
                    timeout=GAME_DETAIL_TIMEOUT_SECONDS,
                )
                self._store_game_detail(matched_sport, game_id, detail)
                self.cache[matched_sport] = {**self.cache[matched_sport], "error": None}
                self._schedule_cache_save()
                self.async_set_updated_data(self._compose_data())
                return
            except (ProviderError, ValueError, KeyError, TypeError, asyncio.TimeoutError) as err:
                _LOGGER.warning("%s selected game detail failed: %s", matched_sport.upper(), err)
                self.cache[matched_sport] = {
                    **self.cache[matched_sport],
                    "error": f"Selected game detail timed out or failed: {err}",
                }
                self.async_set_updated_data(self._compose_data())
                return

        # Do not turn a single unknown fixture into a full-sport refresh. The
        # next regular poll will repopulate its schedule without blocking UI.
        _LOGGER.warning("Selected game %s has no supported sport context", game_id)

    async def _async_update_data(self):
        # When the user has a live game open, refresh only that game's rich
        # detail feed. This keeps count, bases and current batter/pitcher moving
        # without waiting on four complete league refreshes.
        if self.selected_live_sport and self.selected_live_game_id:
            sport = self.selected_live_sport
            selected = next(
                (
                    game for game in self.cache.get(sport, {}).get("games", []) or []
                    if str(game.get("game_id") or "") == str(self.selected_live_game_id)
                ),
                None,
            )
            if selected and selected.get("is_live"):
                try:
                    detail = await asyncio.wait_for(
                        self.providers[sport].async_game_detail(self.selected_live_game_id),
                        timeout=GAME_DETAIL_TIMEOUT_SECONDS,
                    )
                    self._store_game_detail(sport, str(self.selected_live_game_id), detail)
                    self.cache[sport] = {**self.cache[sport], "error": None}
                    self._schedule_cache_save()
                except (ProviderError, ValueError, KeyError, TypeError, asyncio.TimeoutError) as err:
                    _LOGGER.debug("%s live game detail refresh failed: %s", sport.upper(), err)
                data = self._compose_data()
                self.update_interval = timedelta(seconds=8)
                return data

        await asyncio.gather(*(self._refresh_sport(sport) for sport in SPORTS))
        data = self._compose_data()
        self.update_interval = timedelta(seconds=20 if data["live_polling"] else 300)
        return data
