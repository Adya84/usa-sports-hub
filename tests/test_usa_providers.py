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
