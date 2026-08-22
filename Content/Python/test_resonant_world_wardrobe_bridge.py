import json
import sys
import unittest
from pathlib import Path


PYTHON_DIR = Path(__file__).resolve().parent
if str(PYTHON_DIR) not in sys.path:
    sys.path.insert(0, str(PYTHON_DIR))
PROJECT_ROOT = PYTHON_DIR.parents[1]

from resonant_world_asset_atlas import build_asset_atlas  # noqa: E402
from resonant_world_phrase_bridge import build_phrase_manifest  # noqa: E402
from resonant_world_wardrobe_bridge import (  # noqa: E402
    VOICING_VERSION,
    build_wardrobe_voicing_preview,
    validate_wardrobe_voicing_preview,
)


class ResonantWorldWardrobeBridgeTests(unittest.TestCase):
    def test_default_preview_uses_real_first_outfit_and_seed_movement(self):
        preview = build_wardrobe_voicing_preview(3900)

        self.assertTrue(preview["layers"]["cosmetic"]["records"])
        self.assertEqual(preview["layers"]["cosmetic"]["outfit_id"], "MelusinaV2")
        self.assertEqual(preview["world"]["movement_id"], "cadence_cathedral")
        self.assertEqual(preview["voicing_version"], VOICING_VERSION)
        self.assertEqual(validate_wardrobe_voicing_preview(preview), [])

    def test_petal_archetype_resolves_authored_palette_vfx_water_and_pieces(self):
        preview = build_wardrobe_voicing_preview(
            3900,
            movement_id="petal_cantata",
            archetype_id="SakuraDreamer",
        )

        style = preview["layers"]["style"]
        self.assertEqual(style["archetype_id"], "SakuraDreamer")
        self.assertEqual(style["palette"]["name"], "SakuraDreamer")
        self.assertEqual(len(style["outfit_pieces"]), 4)
        self.assertIn("NS_Nikki_FlowerPetals", [item["system_id"] for item in preview["world_response"]["presentation"]["vfx_systems"]])
        self.assertEqual(preview["world_response"]["presentation"]["water_profiles"][0]["profile_id"], "pond_shrine")
        self.assertEqual(preview["world"]["movement_id"], "petal_cantata")
        self.assertEqual(preview["challenge_hook"]["enabled_for_proof_preview"], False)

    def test_atlas_and_phrase_are_summarized_without_becoming_authorities(self):
        atlas = build_asset_atlas(PROJECT_ROOT)
        midi_path = PROJECT_ROOT / "Content" / "MelodiaIntegration" / "MIDI" / "128BPMarpeggiomelody.mid"
        phrase = build_phrase_manifest(midi_path, 3900)
        preview = build_wardrobe_voicing_preview(
            3900,
            movement_id="cadence_cathedral",
            atlas=atlas,
            phrase=phrase,
        )

        self.assertEqual(preview["asset_binding"]["atlas_version"], "resonant_asset_atlas_v1")
        self.assertEqual(preview["world_response"]["presentation"]["phrase"]["note_count"], 192)
        self.assertTrue(preview["runtime_boundary"]["does_not_write_save"])
        self.assertEqual(preview["challenge_hook"]["challenge_id"], "challenge.first_resonance_echo")
        json.dumps(preview)

    def test_unknown_cosmetic_fails_closed(self):
        with self.assertRaises(ValueError):
            build_wardrobe_voicing_preview(3900, cosmetic_ids=["Cos_NotInSourceManifest"])

    def test_preview_is_not_allowed_to_turn_the_form_into_a_grant(self):
        preview = build_wardrobe_voicing_preview(3900, movement_id="liquid_cathedral")

        form = preview["layers"]["form"]
        self.assertTrue(form["declares_only"])
        self.assertFalse(form["grants_capability"])
        self.assertEqual(validate_wardrobe_voicing_preview(preview), [])


if __name__ == "__main__":
    unittest.main()
