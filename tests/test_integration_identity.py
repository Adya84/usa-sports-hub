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
