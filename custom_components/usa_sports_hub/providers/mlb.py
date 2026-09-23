"""MLB Stats API adapter."""
from .base import ProviderClient
from .models import mlb_standings
class MlbProvider(ProviderClient):
    async def async_schedule(self):
        data=await self.async_get_json("https://statsapi.mlb.com/api/v1/schedule?sportId=1")
        return [{"game_id":str(g.get("gamePk")),"sport":"mlb","league":"MLB","home_team":g.get("teams",{}).get("home",{}).get("team",{}).get("name","Home"),"away_team":g.get("teams",{}).get("away",{}).get("team",{}).get("name","Away"),"home_score":g.get("teams",{}).get("home",{}).get("score"),"away_score":g.get("teams",{}).get("away",{}).get("score"),"status":g.get("status",{}).get("abstractGameState","Scheduled"),"status_detail":g.get("status",{}).get("detailedState","Scheduled"),"is_live":g.get("status",{}).get("abstractGameState")=="Live","is_final":g.get("status",{}).get("abstractGameState")=="Final","start_time":g.get("gameDate"),"period":g.get("linescore",{}).get("currentInning"),"clock":None,"venue":g.get("venue",{}).get("name"),"broadcasts":[]} for d in data.get("dates",[]) for g in d.get("games",[])]
    async def async_standings(self):
        return mlb_standings(await self.async_get_json("https://statsapi.mlb.com/api/v1/standings?leagueId=103,104"))
    async def async_news(self): return []
    async def async_teams(self):
        data=await self.async_get_json("https://statsapi.mlb.com/api/v1/teams?sportId=1"); return [{"name":team.get("name"),"id":str(team.get("id") or ""),"country":"canada" if team.get("name")=="Toronto Blue Jays" else "usa"} for team in data.get("teams",[])]
    async def async_game_detail(self, game_id): return await self.async_get_json(f"https://statsapi.mlb.com/api/v1.1/game/{game_id}/feed/live")
