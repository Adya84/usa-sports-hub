import unittest
from pathlib import Path


class IntegrationIdentityTests(unittest.TestCase):
    def test_usa_sports_hub_identity(self):
        source = Path("custom_components/usa_sports_hub/const.py").read_text(encoding="utf-8")

        self.assertIn('DOMAIN = "usa_sports_hub"', source)
        self.assertIn('NAME = "USA Sports Hub"', source)
