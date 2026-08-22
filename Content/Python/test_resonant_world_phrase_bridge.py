import json
import sys
import unittest
from pathlib import Path


PYTHON_DIR = Path(__file__).resolve().parent
if str(PYTHON_DIR) not in sys.path:
    sys.path.insert(0, str(PYTHON_DIR))

from resonant_world_phrase_bridge import (  # noqa: E402
    PHRASE_GENERATOR_VERSION,
    build_phrase_manifest,
    validate_phrase_manifest,
)


PROJECT_ROOT = PYTHON_DIR.parents[1]
MIDI_PATH = PROJECT_ROOT / "Content" / "MelodiaIntegration" / "MIDI" / "128BPMarpeggiomelody.mid"


class ResonantWorldPhraseBridgeTests(unittest.TestCase):
    def test_existing_midi_becomes_a_valid_stable_phrase_manifest(self):
        manifest = build_phrase_manifest(MIDI_PATH, 3900)

        self.assertEqual(manifest["phrase_generator_version"], PHRASE_GENERATOR_VERSION)
        self.assertGreater(manifest["note_count"], 0)
        self.assertEqual(manifest["note_count"], manifest["voxel_count"])
        self.assertEqual(validate_phrase_manifest(manifest), [])
        self.assertTrue(all(voxel["cell_id"].startswith(f"{PHRASE_GENERATOR_VERSION}:") for voxel in manifest["voxels"]))
        self.assertIn(manifest["movement"]["movement_id"], {"cadence_cathedral", "dissonant_expanse", "mirage_gala"})

    def test_same_midi_and_seed_reproduce_exactly(self):
        first = build_phrase_manifest(MIDI_PATH, 3900)
        second = build_phrase_manifest(MIDI_PATH, 3900)
        other = build_phrase_manifest(MIDI_PATH, 3901)

        self.assertEqual(first, second)
        self.assertNotEqual(first["source"]["phrase_id"], other["source"]["phrase_id"])
        self.assertNotEqual(first["world"], other["world"])

    def test_phrase_voxels_expose_consonant_and_dissonant_material_categories(self):
        manifest = build_phrase_manifest(MIDI_PATH, 3900)
        self.assertTrue(any(voxel["material_id"] == "dissonant_note" for voxel in manifest["voxels"]))
        json.dumps(manifest)


if __name__ == "__main__":
    unittest.main()
