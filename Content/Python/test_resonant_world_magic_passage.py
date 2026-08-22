import json
import sys
import unittest
from pathlib import Path


PYTHON_DIR = Path(__file__).resolve().parent
if str(PYTHON_DIR) not in sys.path:
    sys.path.insert(0, str(PYTHON_DIR))
PROJECT_ROOT = PYTHON_DIR.parents[1]

from resonant_world_magic_passage import (  # noqa: E402
    build_magic_passage,
    build_magic_passage_portfolio,
    validate_magic_passage,
    validate_magic_passage_portfolio,
)


class ResonantWorldMagicPassageTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        atlas_path = PROJECT_ROOT / "Saved" / "Audit" / "resonant_world_asset_atlas.json"
        phrase_path = PROJECT_ROOT / "Saved" / "Audit" / "resonant_world_phrase_128bpm.json"
        cls.atlas = json.loads(atlas_path.read_text(encoding="utf-8")) if atlas_path.exists() else None
        cls.phrase = json.loads(phrase_path.read_text(encoding="utf-8")) if phrase_path.exists() else None

    def test_petal_passage_stages_existing_magic_inputs(self):
        passage = build_magic_passage(
            3900,
            movement_id="petal_cantata",
            archetype_id="SakuraDreamer",
            atlas=self.atlas,
            phrase=self.phrase,
        )

        self.assertEqual(passage["premise"]["world_verb"], "bloom")
        self.assertEqual([stage["world_action"] for stage in passage["response_choreography"]], [
            "germinate", "open_flora", "draw_petal_route", "leave_a_bloom_rest",
        ])
        self.assertEqual(passage["response_choreography"][0]["water_profile"], "pond_shrine")
        self.assertEqual(passage["collection_affordance"]["currency_id"], "Radiant")
        self.assertTrue(passage["collection_affordance"]["does_not_grant_currency"])
        self.assertTrue(passage["scene_preview"]["photo_spot"]["scene_preview_only"])
        self.assertEqual(len(passage["scene_preview"]["photo_spot"]["lighting_presets"]), 4)
        self.assertTrue(passage["runtime_boundary"]["does_not_grant_capability"])
        self.assertEqual(validate_magic_passage(passage), [])

    def test_portfolio_covers_all_six_authored_movements(self):
        portfolio = build_magic_passage_portfolio(3900, atlas=self.atlas, phrase=self.phrase)

        self.assertEqual(portfolio["passage_count"], 6)
        self.assertEqual(validate_magic_passage_portfolio(portfolio), [])
        movement_ids = {passage["world"]["movement_id"] for passage in portfolio["passages"]}
        self.assertEqual(movement_ids, {
            "petal_cantata", "star_loom", "liquid_cathedral",
            "cadence_cathedral", "mirage_gala", "dissonant_expanse",
        })
        self.assertEqual(
            {
                passage["world"]["movement_id"]: passage["collection_affordance"]["currency_id"]
                for passage in portfolio["passages"]
            },
            {
                "petal_cantata": "Radiant",
                "star_loom": "Arcane",
                "liquid_cathedral": "Tide",
                "cadence_cathedral": "Forte",
                "mirage_gala": "Gale",
                "dissonant_expanse": "Umbral",
            },
        )

    def test_same_seed_and_sources_reproduce_the_same_passage(self):
        first = build_magic_passage(3900, movement_id="star_loom", atlas=self.atlas, phrase=self.phrase)
        second = build_magic_passage(3900, movement_id="star_loom", atlas=self.atlas, phrase=self.phrase)

        self.assertEqual(first, second)
        self.assertEqual(first["quantum_setup"]["selection_stage"], "world_preparation_only")
        self.assertTrue(first["quantum_setup"]["backend_policy"]["requires_exactly_two_candidates_for_qsharp"])
        self.assertEqual(first["quantum_setup"]["rank_preview"]["backend_requested"], "qsharp-simulator")
        json.dumps(first)


if __name__ == "__main__":
    unittest.main()
