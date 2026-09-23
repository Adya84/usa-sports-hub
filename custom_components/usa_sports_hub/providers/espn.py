"""ESPN adapter shared by NFL and NBA."""
from __future__ import annotations
from .base import ProviderClient
from .models import game_from_espn, standing

class EspnProvider(ProviderClient):
    def __init__(self, session, sport_path: str, sport: str, league: str): super().__init__(session); self.base=f"https://site.api.espn.com/apis/site/v2/sports/{sport_path}"; self.sport=sport; self.league=league
    async def async_schedule(self):
        payload=await self.async_get_json(f"{self.base}/scoreboard"); return [game_from_espn(event,self.sport,self.league) for event in payload.get("events",[]) if event.get("id")]
    async def async_standings(self):
        payload=await self.async_get_json(self.base.replace("site/v2","v2")+"/standings")
        rows=[]
        for group in payload.get("children",[]) or [payload]:
            for item in group.get("standings",{}).get("entries",[]):
                team=item.get("team",{}); stats={x.get("name"):x.get("displayValue") for x in item.get("stats",[])}
                rows.append(standing(team.get("displayName") or team.get("name") or "Team", stats.get("playoffSeed") or stats.get("rank"), stats.get("overall"), (team.get("logos") or [{}])[0].get("href")))
        return rows
    async def async_news(self):
        return (await self.async_get_json(f"{self.base}/news")).get("articles",[])[:20]
    async def async_teams(self):
        data=await self.async_get_json(f"{self.base}/teams")
        return [{"name":team.get("displayName") or team.get("name"),"id":str(team.get("id") or ""),"country":"canada" if team.get("location") in {"Toronto","Vancouver","Montreal"} else "usa"} for sport in data.get("sports",[]) for league in sport.get("leagues",[]) for item in league.get("teams",[]) for team in [item.get("team",{})] if team.get("displayName") or team.get("name")]
    async def async_game_detail(self, game_id): return await self.async_get_json(f"{self.base}/summary?event={game_id}")
