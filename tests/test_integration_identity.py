import unittest
from pathlib import Path


class IntegrationIdentityTests(unittest.TestCase):
    def test_usa_sports_hub_identity(self):
        source = Path("custom_components/usa_sports_hub/const.py").read_text(encoding="utf-8")

        self.assertIn('DOMAIN = "usa_sports_hub"', source)
        self.assertIn('NAME = "USA Sports Hub"', source)

    def test_live_details_are_cached_by_game_id(self):
        source = Path("custom_components/usa_sports_hub/coordinator.py").read_text(encoding="utf-8")

        self.assertIn('"details": {}', source)
        self.assertIn('details[str(game_id)] = detail', source)
        self.assertIn('(item.get("details") or {}).get(selected_detail_id)', source)

    def test_selected_game_failure_does_not_refresh_every_sport(self):
        source = Path("custom_components/usa_sports_hub/coordinator.py").read_text(encoding="utf-8")
        selection = source[source.index("async def async_set_selected_live_match"):]

        self.assertIn("GAME_DETAIL_TIMEOUT_SECONDS", selection)
        self.assertNotIn("await self.async_request_refresh()", selection)

    def test_selected_game_accepts_the_sport_sent_by_the_panel(self):
        source = Path("custom_components/usa_sports_hub/coordinator.py").read_text(encoding="utf-8")

        self.assertIn("async_set_selected_live_match(self, fixture_id, sport=None)", source)
        self.assertIn("requested_sport", source)

    def test_team_data_is_cached_and_favourites_are_persistent(self):
        coordinator = Path("custom_components/usa_sports_hub/coordinator.py").read_text(encoding="utf-8")
        setup = Path("custom_components/usa_sports_hub/__init__.py").read_text(encoding="utf-8")

        self.assertIn('"team_details": {}', coordinator)
        self.assertIn("async_add_team_favourite", coordinator)
        self.assertIn("async_remove_team_favourite", coordinator)
        self.assertIn('"team_favourites"', coordinator)
        self.assertIn('"add_team_favourite"', setup)
        self.assertIn('"remove_team_favourite"', setup)

    def test_cache_schema_remains_compatible_with_existing_installations(self):
        source = Path("custom_components/usa_sports_hub/coordinator.py").read_text(encoding="utf-8")
        self.assertIn("CACHE_VERSION = 1", source)

    def test_team_selection_returns_before_background_refresh(self):
        source = Path("custom_components/usa_sports_hub/coordinator.py").read_text(encoding="utf-8")
        selection = source[source.index("async def async_select_team"):source.index("async def async_add_team_favourite")]
        self.assertIn("async_create_task", selection)
        self.assertIn("_async_refresh_team", selection)
