import json
import sys
import unittest
from pathlib import Path


PYTHON_DIR = Path(__file__).resolve().parent
if str(PYTHON_DIR) not in sys.path:
    sys.path.insert(0, str(PYTHON_DIR))
PROJECT_ROOT = PYTHON_DIR.parents[1]

from resonant_world_pcg_adapter import (  # noqa: E402
    ADAPTER_VERSION,
    build_resonant_pcg_plan,
    hero_graph_specs_from_resonant_plan,
    validate_resonant_pcg_plan,
)
from resonant_world_phrase_bridge import build_phrase_manifest  # noqa: E402


class ResonantWorldPCGAdapterTests(unittest.TestCase):
    def test_plan_reuses_existing_graph_owner_and_decorates_every_spec(self):
        plan = build_resonant_pcg_plan(3900, radius=1)

        self.assertTrue(plan["ok"], plan["validation_errors"])
        self.assertEqual(plan["adapter_version"], ADAPTER_VERSION)
        self.assertEqual(plan["chunk_count"], 9)
        self.assertTrue(plan["graph_reuse"])
        self.assertEqual(plan["pcg_owner"], "existing pcg_scale_world_pipeline + pcg_visual_chunk_builder")
        self.assertTrue(plan["production_maps_touched"] is False)
        self.assertGreater(plan["hero_volume_count"], 0)
        self.assertGreater(plan["static_spec_count"], 0)
        self.assertTrue(all(spec["resonant_world"]["movement_id"] for spec in plan["hero_volume_specs"]))
        self.assertTrue(all(spec["resonant_world"]["motif_id"] for spec in plan["static_specs"]))
        self.assertTrue(all(str(spec["graph"]).startswith("/Game/") for spec in plan["hero_volume_specs"]))

    def test_origin_preserves_seed_headline_movement_and_landmark_fallback(self):
        plan = build_resonant_pcg_plan(3900, radius=1)
        origin = next(chunk for chunk in plan["chunks"] if (chunk["chunk_x"], chunk["chunk_y"]) == (0, 0))

        self.assertEqual(origin["movement_id"], plan["world"]["movement_id"])
        self.assertEqual(origin["landmark_id"], "ResonanceCathedral")
        self.assertEqual(origin["visual_graph_slot"], "ResonanceCathedral")
        self.assertIn("ResonantMovement_", next(
            tag for tag in plan["hero_volume_specs"][0]["tags"] if tag.startswith("ResonantMovement_")
        ))

    def test_optional_atlas_summary_is_embedded_without_copying_all_file_rows(self):
        atlas = {
            "format": "melodia_resonant_world_asset_atlas",
            "atlas_version": "resonant_asset_atlas_v1",
            "ok": True,
            "scan": {"scanned_file_count": 59291},
        }
        plan = build_resonant_pcg_plan(3900, radius=0, atlas=atlas)
        self.assertTrue(plan["ok"], plan["validation_errors"])
        self.assertEqual(plan["asset_atlas"]["scanned_file_count"], 59291)
        self.assertNotIn("asset_files", plan["asset_atlas"])
        json.dumps(plan)
        self.assertEqual(validate_resonant_pcg_plan(plan), [])

    def test_existing_proof_setup_can_consume_the_decorated_specs(self):
        plan = build_resonant_pcg_plan(3900, radius=1)
        specs = hero_graph_specs_from_resonant_plan(plan)

        self.assertEqual(len(specs), plan["hero_volume_count"])
        self.assertTrue(all(label.startswith("PCG ScaleWorld ") for label, *_ in specs))
        self.assertTrue(all(graph.startswith("/Game/") for _, graph, *_ in specs))
        self.assertTrue(all(spec.get("resonant_world", {}).get("movement_id") for *_, spec in specs))

    def test_existing_midi_phrase_can_be_carried_into_the_pcg_handoff(self):
        midi_path = PROJECT_ROOT / "Content" / "MelodiaIntegration" / "MIDI" / "128BPMarpeggiomelody.mid"
        phrase = build_phrase_manifest(midi_path, 3900)
        plan = build_resonant_pcg_plan(3900, radius=0, phrase=phrase)

        self.assertTrue(plan["ok"], plan["validation_errors"])
        self.assertEqual(plan["phrase_source"]["midi_file_name"], "128BPMarpeggiomelody.mid")
        self.assertEqual(plan["phrase_source"]["note_count"], 192)
        self.assertEqual(validate_resonant_pcg_plan(plan), [])

    def test_wardrobe_voicing_preview_can_be_carried_as_a_non_granting_summary(self):
        wardrobe = {
            "format": "melodia_resonant_world_wardrobe_voicing",
            "voicing_version": "resonant_wardrobe_voicing_v1",
            "request_id": "0123456789abcdef",
            "ok": True,
            "world": {"world_seed": 3900, "movement_id": "petal_cantata"},
            "layers": {
                "cosmetic": {
                    "catalog_asset": "/MelodiaWardrobe/Catalog/DA_MelodiaCosmeticCatalog",
                    "records": [{"cosmetic_id": "Cos_Accessories_MelusinaV2"}],
                },
                "form": {"requested_resonant_form_id": "ResonantForm_PetalRipple"},
                "style": {"archetype_id": "SakuraDreamer", "voicing": {"active_axes": ["resonance", "lilt"]}},
            },
            "world_response": {"verb": "bloom"},
            "runtime_boundary": {"does_not_grant_capability": True, "does_not_write_save": True},
        }
        plan = build_resonant_pcg_plan(3900, radius=0, wardrobe=wardrobe)

        self.assertTrue(plan["ok"], plan["validation_errors"])
        self.assertEqual(plan["wardrobe_voicing"]["archetype_id"], "SakuraDreamer")
        self.assertTrue(plan["wardrobe_voicing"]["does_not_grant_capability"])
        self.assertEqual(validate_resonant_pcg_plan(plan), [])

    def test_magic_passage_can_be_carried_as_a_four_stage_non_mutating_summary(self):
        passage = {
            "format": "melodia_resonant_world_magic_passage",
            "passage_version": "resonant_magic_passage_v1",
            "passage_id": "0123456789abcdef",
            "world": {"world_seed": 3900, "movement_id": "petal_cantata"},
            "premise": {"world_verb": "bloom"},
            "response_choreography": [{"stage_id": str(index)} for index in range(4)],
            "scene_preview": {"photo_spot": {"scene_preview_only": True}},
            "quantum_setup": {"selection_stage": "world_preparation_only"},
            "runtime_boundary": {"does_not_grant_capability": True, "does_not_write_save": True},
        }
        plan = build_resonant_pcg_plan(3900, radius=0, magic_passage=passage)

        self.assertTrue(plan["ok"], plan["validation_errors"])
        self.assertEqual(plan["magic_passage"]["world_verb"], "bloom")
        self.assertEqual(plan["magic_passage"]["stage_count"], 4)
        self.assertEqual(validate_resonant_pcg_plan(plan), [])


if __name__ == "__main__":
    unittest.main()
