"""Parity checks for the authored first-20-minute opening contract."""

import json
from pathlib import Path
import unittest

from gmm.game.rules_generated import RULES


class OpeningFlowContractTests(unittest.TestCase):
    def setUp(self):
        self.opening = RULES["opening_flow"]

    def test_generated_contract_matches_authoritative_json(self):
        root = Path(__file__).resolve().parents[4]
        source = json.loads(
            (root / "Plugins/MelodiaCore/Rules/melodia_rules.json").read_text(encoding="utf-8")
        )
        self.assertEqual(self.opening, source["opening_flow"])

    def test_opening_route_is_explicit(self):
        self.assertTrue(self.opening["morning_level"].endswith("L_MelusinaMorning"))
        self.assertTrue(self.opening["dreamstate_level"].endswith("L_Melodia_Dreamstate"))
        self.assertEqual(self.opening["zen_level"], "/Game/ZenForestTest")

    def test_first_unlock_is_deterministic(self):
        self.assertEqual(self.opening["tutorial_enemy_id"], "SakuraPhantom")
        self.assertGreater(self.opening["first_dungeon_seed"], 0)
        self.assertEqual(self.opening["heart_tokens_on_unlock"], 1)


if __name__ == "__main__":
    unittest.main()
