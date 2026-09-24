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
