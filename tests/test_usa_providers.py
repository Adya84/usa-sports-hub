"""Provider normalization contracts for TS-backed USA Sports Hub."""

import importlib.util
import unittest
from pathlib import Path


SPEC = importlib.util.spec_from_file_location(
    "usa_provider_models", Path("custom_components/usa_sports_hub/providers/models.py")
)
models = importlib.util.module_from_spec(SPEC)
SPEC.loader.exec_module(models)

normalize_event = models.normalize_ts_event
normalize_standing = models.normalize_ts_standing
compact_news = models.compact_ts_news
normalize_team_detail = models.normalize_ts_team_detail


class ProviderModelTests(unittest.TestCase):
    def test_team_detail_normalizes_profile_and_squad(self):
        detail = normalize_team_detail(
            "mlb",
            {
                "id": 11,
                "full_name": "Los Angeles Angels",
                "standing": {"short_record": "60-98"},
                "logos": {"small": "team.png"},
                "team_extra_info": [{"label": "Park", "value": "Angel Stadium"}],
            },
            [{
                "id": 7,
                "full_name": "Player One",
                "number": 9,
                "position_abbreviation": "OF",
                "headshots": {"small": "player.png"},
                "injury": {"status": "Day-to-day"},
                "season_stats": {"home_runs": 20},
            }],
            [{"name": "Runs", "value": 4}],
            [{"name": "Top hitter", "value": "Player One"}],
            None,
        )
        self.assertEqual(detail["profile"]["team_id"], "11")
        self.assertEqual(detail["profile"]["logo"], "team.png")
        self.assertEqual(detail["squad"][0]["headshot"], "player.png")
        self.assertEqual(detail["squad"][0]["season_stats"]["home_runs"], 20)
        self.assertEqual(detail["injuries"], [])

    def test_team_detail_compacts_nested_leader_stat_and_injury_rows(self):
        detail = normalize_team_detail(
            "mlb", {"id": 1}, [],
            [{"player": {"full_name": "CJ Abrams"}, "stat": "Batting average", "value": ".281"}],
            [{"category": "Home runs", "stat": 24, "player": {"full_name": "James Wood", "headshots": {"small": "wood.png"}}}],
            [{"status": "60-Day IL", "player": {"full_name": "Josiah Gray"}}],
        )
        self.assertEqual(detail["leaders"][0]["player_name"], "James Wood")
        self.assertEqual(detail["leaders"][0]["value"], 24)
        self.assertEqual(detail["statistics"][0]["player_name"], "CJ Abrams")
        self.assertEqual(detail["injuries"][0]["player_name"], "Josiah Gray")

    def test_team_detail_drops_empty_provider_stat_rows(self):
        detail = normalize_team_detail("mlb", {"id": 1}, [], [{}, {}], [{}, {}], [{}, {}])
        self.assertEqual(detail["statistics"], [])
        self.assertEqual(detail["leaders"], [])
        self.assertEqual(detail["injuries"], [])

    def test_provider_has_dedicated_team_data_endpoints(self):
        source = Path("custom_components/usa_sports_hub/providers/ts.py").read_text(encoding="utf-8")
        self.assertIn("async def async_team_detail", source)
        for suffix in ("/players", "/statistics", "/leaders", "/injuries"):
            self.assertIn(f'{{self.base}}/teams/{{team_id}}{suffix}', source)

    def test_mlb_detail_does_not_make_unscoped_fallback_requests(self):
        source = Path("custom_components/usa_sports_hub/providers/ts.py").read_text(encoding="utf-8")

        self.assertIn('selected_related_uris = [] if self.league == "mlb" else [', source)

    def test_ts_event_keeps_live_detail(self):
        event = {
            "id": 123,
            "event_status": "in_progress",
            "game_date": "2026-09-24T00:00:00Z",
            "stadium": "Test Arena",
            "has_play_by_play_records": True,
            "home_team": {
                "id": 1, "full_name": "Home Team", "abbreviation": "HOM",
                "logos": {"w72xh72": "home.png"}, "colour_1": "111111",
            },
            "away_team": {
                "id": 2, "full_name": "Away Team", "abbreviation": "AWY",
                "logos": {"w72xh72": "away.png"}, "colour_1": "222222",
            },
            "box_score": {
                "id": 99,
                "has_statistics": True,
                "api_uri": "/nfl/box_scores/99",
                "progress": {"clock_label": "Q2 04:12", "segment": 2, "clock": "4:12"},
                "score": {"home": {"score": 21}, "away": {"score": 14}},
            },
        }
        game = normalize_event(event, "nfl")
        self.assertEqual(game["home_team"], "Home Team")
        self.assertEqual(game["away_score"], 14)
        self.assertTrue(game["is_live"])
        self.assertTrue(game["has_play_by_play_records"])
        self.assertEqual(game["box_score_uri"], "/nfl/box_scores/99")
        self.assertEqual(game["clock"], "4:12")

    def test_ts_standing_keeps_sport_specific_fields(self):
        row = {
            "id": 3227,
            "wins": 97,
            "losses": 60,
            "short_record": "97-60",
            "division_rank": 1,
            "formatted_rank": "1st NL West",
            "runs_differential": 200,
            "clinched_playoffs": True,
            "team": {
                "id": 26,
                "full_name": "Los Angeles Dodgers",
                "abbreviation": "LAD",
                "logos": {"small": "lad.png"},
            },
        }
        item = normalize_standing(row, "mlb")
        self.assertEqual(item["team"], "Los Angeles Dodgers")
        self.assertEqual(item["record"], "97-60")
        self.assertEqual(item["runs_differential"], 200)
        self.assertTrue(item["clinched_playoffs"])

    def test_news_is_built_from_ts_event_articles(self):
        items = compact_news([
            {
                "id": 1,
                "updated_at": "now",
                "recap": "/articles/1",
                "recap_data": {"headline": "Game recap", "abstract": "Summary"},
            }
        ])
        self.assertEqual(items[0]["title"], "Game recap")
        self.assertEqual(items[0]["kind"], "recap")
        self.assertIn("score.com/articles/1", items[0]["url"])


if __name__ == "__main__":
    unittest.main()
