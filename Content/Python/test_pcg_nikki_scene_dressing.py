import unittest

import pcg_nikki_scene_dressing as dressing


class TestPCGNikkiSceneDressing(unittest.TestCase):
    def test_manifest_is_proof_only(self):
        manifest = dressing.recipe_manifest()
        self.assertTrue(manifest["proof_only"])
        self.assertFalse(manifest["production_maps_touched"])
        self.assertFalse(manifest["water_masters_modified"])

    def test_all_hero_recipes_have_distinct_proof_levels(self):
        recipes = dressing.recipe_manifest()["recipes"]
        self.assertEqual(set(recipes), {"ResonanceCathedral", "ArpeggioBridge", "BellTreeGarden", "XylophoneTrail", "CrystalHarpGrove"})
        levels = [recipe["level"] for recipe in recipes.values()]
        self.assertEqual(len(levels), len(set(levels)))
        self.assertTrue(all(path.startswith(dressing.PROOF_ROOT) for path in levels))

    def test_recipes_use_existing_nikki_and_water_instances(self):
        for recipe in dressing.recipe_manifest()["recipes"].values():
            for key in ("architecture_material", "hero_material", "accent_material", "water_material"):
                self.assertIn("/Game/EnvSandbox/Materials/Instances/", recipe[key])
                self.assertNotIn("M_Water_Master", recipe[key])


if __name__ == "__main__":
    unittest.main()
