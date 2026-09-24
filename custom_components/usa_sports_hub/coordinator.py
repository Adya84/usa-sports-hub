"""Coordinator for the USA Sports Hub theScore provider set."""
from __future__ import annotations

import asyncio
import logging
from datetime import timedelta

from homeassistant.helpers.aiohttp_client import async_get_clientsession
from homeassistant.helpers.update_coordinator import DataUpdateCoordinator

from .providers.base import ProviderError
from .providers.thescore import MlbProvider, NbaProvider, NflProvider, NhlProvider

_LOGGER = logging.getLogger(__name__)
SPORTS = ("nfl", "nba", "mlb", "nhl")


class UsaSportsCoordinator(DataUpdateCoordinator):
    """Refresh theScore independently for each sport and retain last good data."""

    def __init__(self, hass, entry):
        self.entry = entry
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
            detail_target = (
                live[0] if live
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
            _LOGGER.warning("%s theScore refresh failed: %s", sport.upper(), err)

    async def _async_update_data(self):
        await asyncio.gather(*(self._refresh_sport(sport) for sport in SPORTS))
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
                "odds": detail.get("odds") or {},
                "stadium": detail.get("stadium") or {},
            }

        self.update_interval = timedelta(seconds=20 if live_any else 300)
        return {
            "sports": sports,
            "live_polling": live_any,
            "provider": "theScore",
        }
