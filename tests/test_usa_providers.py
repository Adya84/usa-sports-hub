"""Provider normalization contracts for USA Sports Hub."""

import importlib.util
import unittest
from pathlib import Path


SPEC = importlib.util.spec_from_file_location(
    "usa_provider_models", Path("custom_components/usa_sports_hub/providers/models.py")
)
models = importlib.util.module_from_spec(SPEC)
SPEC.loader.exec_module(models)
game_from_espn = models.game_from_espn
mlb_standings = models.mlb_standings
compact_news = models.compact_news


class ProviderModelTests(unittest.TestCase):
    def test_espn_event_becomes_a_compact_game(self):
        event = {
            "id": "1", "date": "2026-09-24T18:00Z", "status": {"type": {"state": "in", "shortDetail": "Q2 04:12", "completed": False}},
            "competitions": [{"venue": {"fullName": "Test Arena"}, "competitors": [
                {"homeAway": "home", "team": {"id": "10", "displayName": "Home", "abbreviation": "HOM", "logos": [{"href": "home.png"}]}, "score": "21"},
                {"homeAway": "away", "team": {"id": "20", "displayName": "Away", "abbreviation": "AWY", "logos": [{"href": "away.png"}]}, "score": "14"},
            ]}],
        }
        game = game_from_espn(event, "nfl", "NFL")
        self.assertEqual(game["home_team"], "Home")
        self.assertEqual(game["away_score"], 14)
        self.assertTrue(game["is_live"])
        self.assertNotIn("plays", game)

    def test_mlb_standings_accepts_list_records(self):
        rows = mlb_standings({"records": [{"teamRecords": [{"team": {"name": "Rays"}, "divisionRank": "1", "wins": 90, "losses": 70, "records": []}]}]})
        self.assertEqual(rows, [{"team": "Rays", "rank": "1", "record": "90-70", "logo": None}])

    def test_news_removes_large_article_body(self):
        items = compact_news([{"headline": "Headline", "description": "Summary", "link": {"web": "https://example.test"}, "story": "x" * 20000}])
        self.assertEqual(items, [{"title": "Headline", "summary": "Summary", "url": "https://example.test", "published": None}])
