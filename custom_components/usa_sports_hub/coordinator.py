"""Coordinator for the USA Sports Hub provider set."""
from __future__ import annotations
import asyncio
import logging
from datetime import timedelta
from homeassistant.helpers.aiohttp_client import async_get_clientsession
from homeassistant.helpers.update_coordinator import DataUpdateCoordinator, UpdateFailed
from .providers.base import ProviderError
from .providers.espn_nfl import NflProvider
from .providers.espn_nba import NbaProvider
from .providers.mlb import MlbProvider
from .providers.nhl import NhlProvider

_LOGGER=logging.getLogger(__name__)
SPORTS=("nfl","nba","mlb","nhl")

class UsaSportsCoordinator(DataUpdateCoordinator):
    """Refresh providers independently and retain their last good response."""
    def __init__(self,hass,entry):
        self.entry=entry; session=async_get_clientsession(hass)
        self.providers={"nfl":NflProvider(session),"nba":NbaProvider(session),"mlb":MlbProvider(session),"nhl":NhlProvider(session)}
        self.cache={sport:{"games":[],"standings":[],"news":[],"teams":[],"error":None} for sport in SPORTS}
        super().__init__(hass,_LOGGER,name="USA Sports Hub",update_interval=timedelta(minutes=10))
    async def _refresh_sport(self,sport):
        provider=self.providers[sport]
        try:
            games,table,news,teams=await asyncio.gather(provider.async_schedule(),provider.async_standings(),provider.async_news(),provider.async_teams())
            self.cache[sport]={"games":games,"standings":table,"news":news,"teams":teams,"error":None}
        except (ProviderError,ValueError,KeyError,TypeError) as err:
            self.cache[sport]={**self.cache[sport],"error":str(err)}
            _LOGGER.warning("%s provider refresh failed: %s",sport.upper(),err)
    async def _async_update_data(self):
        await asyncio.gather(*(self._refresh_sport(sport) for sport in SPORTS))
        sports={}
        live_any=False
        for sport,item in self.cache.items():
            games=item["games"]
            live=[game for game in games if game.get("is_live")]
            upcoming=[game for game in games if not game.get("is_live") and not game.get("is_final")]
            finished=[game for game in games if game.get("is_final")]
            live_any|=bool(live)
            sports[sport]={**item,"live":live,"fixtures":upcoming,"results":finished,"next_game":upcoming[0] if upcoming else None,"latest_result":finished[-1] if finished else None}
        self.update_interval=timedelta(seconds=30 if live_any else 600)
        return {"sports":sports,"live_polling":live_any}
