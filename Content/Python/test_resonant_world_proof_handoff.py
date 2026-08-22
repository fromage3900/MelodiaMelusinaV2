import json
import sys
import unittest
from pathlib import Path


PYTHON_DIR = Path(__file__).resolve().parent
if str(PYTHON_DIR) not in sys.path:
    sys.path.insert(0, str(PYTHON_DIR))
PROJECT_ROOT = PYTHON_DIR.parents[1]

from resonant_world_pcg_adapter import build_resonant_pcg_plan  # noqa: E402
from resonant_world_proof_handoff import (  # noqa: E402
    build_proof_handoff,
    validate_proof_handoff,
)


class ResonantWorldProofHandoffTests(unittest.TestCase):
    def test_handoff_flattens_existing_graph_specs_and_keeps_editor_apply_false(self):
        plan = build_resonant_pcg_plan(3900, radius=1)
        handoff = build_proof_handoff(plan, source_path="memory-plan.json")

        self.assertEqual(handoff["hero_input_count"], plan["hero_volume_count"])
        self.assertTrue(all(item["graph"].startswith("/Game/") for item in handoff["hero_inputs"]))
        self.assertTrue(all(item["resonant_world"]["movement_id"] for item in handoff["hero_inputs"]))
        self.assertFalse(handoff["editor_apply"]["performed"])
        self.assertFalse(handoff["editor_apply"]["production_maps_touched"])
        self.assertEqual(validate_proof_handoff(handoff), [])
        json.dumps(handoff)

    def test_handoff_preserves_wardrobe_and_magic_summaries(self):
        plan = build_resonant_pcg_plan(
            3900,
            radius=0,
            wardrobe={
                "format": "melodia_resonant_world_wardrobe_voicing",
                "world": {"world_seed": 3900, "movement_id": "petal_cantata"},
                "layers": {"style": {"archetype_id": "SakuraDreamer", "voicing": {"active_axes": ["resonance"]}}, "cosmetic": {"catalog_asset": "x", "records": []}},
                "world_response": {"verb": "bloom"},
                "runtime_boundary": {"does_not_grant_capability": True, "does_not_write_save": True},
                "request_id": "0123456789abcdef",
            },
            magic_passage={
                "format": "melodia_resonant_world_magic_passage",
                "world": {"world_seed": 3900, "movement_id": "petal_cantata"},
                "premise": {"world_verb": "bloom"},
                "passage_id": "fedcba9876543210",
                "response_choreography": [{}, {}, {}, {}],
                "scene_preview": {"photo_spot": {"scene_preview_only": True}},
                "quantum_setup": {"selection_stage": "world_preparation_only"},
                "runtime_boundary": {"does_not_grant_capability": True, "does_not_write_save": True},
            },
        )
        handoff = build_proof_handoff(plan)

        self.assertEqual(handoff["wardrobe_voicing"]["archetype_id"], "SakuraDreamer")
        self.assertEqual(handoff["magic_passage"]["stage_count"], 4)
        self.assertTrue(handoff["magic_passage"]["does_not_write_save"])
        self.assertEqual(validate_proof_handoff(handoff), [])


if __name__ == "__main__":
    unittest.main()
