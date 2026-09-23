"""Official NHL API adapter."""
from .base import ProviderClient
from .models import standing
class NhlProvider(ProviderClient):
    async def async_schedule(self):
        data=await self.async_get_json("https://api-web.nhle.com/v1/score/now")
        return [{"game_id":str(g.get("id")),"sport":"nhl","league":"NHL","home_team":g.get("homeTeam",{}).get("commonName",{}).get("default",g.get("homeTeam",{}).get("abbrev","Home")),"away_team":g.get("awayTeam",{}).get("commonName",{}).get("default",g.get("awayTeam",{}).get("abbrev","Away")),"home_score":g.get("homeTeam",{}).get("score"),"away_score":g.get("awayTeam",{}).get("score"),"status":g.get("gameState","Scheduled"),"status_detail":g.get("gameState","Scheduled"),"is_live":g.get("gameState") in {"LIVE","CRIT"},"is_final":g.get("gameState") in {"OFF","FINAL"},"start_time":g.get("startTimeUTC"),"period":g.get("period"),"clock":g.get("clock",{}).get("timeRemaining"),"venue":g.get("venue",{}).get("default"),"broadcasts":[]} for g in data.get("games",[])]
    async def async_standings(self):
        data=await self.async_get_json("https://api-web.nhle.com/v1/standings/now"); return [standing(t.get("teamName",{}).get("default",t.get("teamAbbrev",{}).get("default","Team")),t.get("leagueSequence"),f"{t.get('wins',0)}-{t.get('losses',0)}-{t.get('otLosses',0)}",t.get("teamLogo")) for t in data.get("standings",[])]
    async def async_news(self): return []
    async def async_teams(self):
        data=await self.async_get_json("https://api-web.nhle.com/v1/standings/now"); return [{"name":team.get("teamName",{}).get("default",team.get("teamAbbrev",{}).get("default")),"id":team.get("teamAbbrev",{}).get("default",""),"country":"canada" if team.get("placeName",{}).get("default") in {"Calgary","Edmonton","Montréal","Ottawa","Toronto","Vancouver","Winnipeg"} else "usa"} for team in data.get("standings",[])]
    async def async_game_detail(self, game_id): return await self.async_get_json(f"https://api-web.nhle.com/v1/gamecenter/{game_id}/landing")
