import json
import sys
import unittest
from pathlib import Path

PYTHON_DIR = Path(__file__).resolve().parent
sys.path.insert(0, str(PYTHON_DIR))

from resonant_world_asset_atlas import ATLAS_VERSION, build_asset_atlas
from resonant_world_generator import WORLD_MOVEMENT_LIBRARY


PROJECT_ROOT = Path(__file__).resolve().parents[2]


class ResonantWorldAssetAtlasTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.atlas = build_asset_atlas(PROJECT_ROOT)

    def test_atlas_is_valid_and_covers_cross_system_families(self):
        self.assertEqual(self.atlas["atlas_version"], ATLAS_VERSION)
        self.assertTrue(self.atlas["ok"], self.atlas["validation_errors"])
        self.assertGreater(self.atlas["scan"]["scanned_file_count"], 1000)
        for family in ("musical_pcg", "wardrobe", "water", "niagara_nikki", "quantum"):
            self.assertGreater(self.atlas["scan"]["family_counts"][family], 0)

    def test_every_authored_movement_resolves_required_families(self):
        self.assertEqual(set(self.atlas["world_movements"]), set(WORLD_MOVEMENT_LIBRARY))
        for movement in self.atlas["world_movements"].values():
            self.assertEqual(movement["missing_required_families"], [])
            self.assertGreater(movement["asset_counts"]["pcg"], 0)
            self.assertGreater(movement["asset_counts"]["musical"], 0)
            self.assertGreater(movement["asset_counts"]["vfx"], 0)

    def test_named_manifests_are_loaded(self):
        for source in self.atlas["manifest_sources"].values():
            self.assertTrue(source["loaded"], source)
        archetypes = self.atlas["manifest_summary"]["archetypes"]
        self.assertIn("SakuraDreamer", archetypes)
        self.assertIn("CosmicWeaver", archetypes)
        self.assertIn("MirageDancer", archetypes)

    def test_output_is_json_serialisable(self):
        encoded = json.dumps(self.atlas)
        self.assertIn("melodia_resonant_world_asset_atlas", encoded)


if __name__ == "__main__":
    unittest.main()
