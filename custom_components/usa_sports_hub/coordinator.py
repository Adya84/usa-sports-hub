"""Coordinator for the USA Sports Hub TS provider set."""
from __future__ import annotations

import asyncio
import logging
from datetime import timedelta

from homeassistant.helpers.aiohttp_client import async_get_clientsession
from homeassistant.helpers.update_coordinator import DataUpdateCoordinator

from .providers.base import ProviderError
from .providers.ts import MlbProvider, NbaProvider, NflProvider, NhlProvider

_LOGGER = logging.getLogger(__name__)
SPORTS = ("nfl", "nba", "mlb", "nhl")


class UsaSportsCoordinator(DataUpdateCoordinator):
    """Refresh TS independently for each sport and retain last good data."""

    def __init__(self, hass, entry):
        self.entry = entry
        self.selected_live_game_id = None
        self.selected_live_sport = None
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

            self.cache[sport] = {
                "games": games,
                "standings": table,
                "news": news,
                "teams": teams,
                "ticker": ticker,
                "detail": detail,
                "error": None,
            }
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
            detail = item.get("detail") or {}
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
            }
        return {
            "sports": sports,
            "live_polling": live_any,
            "provider": "TS",
        }

    async def async_set_selected_live_match(self, fixture_id):
        """Select a game and load only that game's detail feed."""
        game_id = str(fixture_id or "").strip()
        if not game_id:
            self.selected_live_game_id = None
            self.selected_live_sport = None
            return

        matched_sport = None
        for sport, item in self.cache.items():
            if any(str(game.get("game_id") or "") == game_id for game in item.get("games", []) or []):
                matched_sport = sport
                break

        self.selected_live_game_id = game_id
        self.selected_live_sport = matched_sport
        if matched_sport:
            try:
                detail = await self.providers[matched_sport].async_game_detail(game_id)
                self.cache[matched_sport] = {
                    **self.cache[matched_sport],
                    "detail": detail,
                    "error": None,
                }
                self.async_set_updated_data(self._compose_data())
                return
            except (ProviderError, ValueError, KeyError, TypeError) as err:
                _LOGGER.warning("%s selected game detail failed: %s", matched_sport.upper(), err)

        # Fallback only when the selected game cannot be found in the cache.
        await self.async_request_refresh()

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
                    detail = await self.providers[sport].async_game_detail(self.selected_live_game_id)
                    self.cache[sport] = {
                        **self.cache[sport],
                        "detail": detail,
                        "error": None,
                    }
                except (ProviderError, ValueError, KeyError, TypeError) as err:
                    _LOGGER.debug("%s live game detail refresh failed: %s", sport.upper(), err)
                data = self._compose_data()
                self.update_interval = timedelta(seconds=8)
                return data

        await asyncio.gather(*(self._refresh_sport(sport) for sport in SPORTS))
        data = self._compose_data()
        self.update_interval = timedelta(seconds=20 if data["live_polling"] else 300)
        return data
