from __future__ import annotations

import json
import math
import sys
import tempfile
import unittest
from pathlib import Path

HERE = Path(__file__).resolve().parent
PROJECT_ROOT = HERE.parent
sys.path.insert(0, str(PROJECT_ROOT))
sys.path.insert(0, str(PROJECT_ROOT / "Content" / "Python"))

from Tools.PCG.build_faraway_mother_pcg_ecosystem import (
    BIOME_BUILDER_MAP,
    BIOME_MATERIAL_MAP,
    SCHEMA as PCG_SCHEMA,
    classify_biome,
    evaluate_chladni,
    evaluate_tension,
    export_manifest,
    generate_faraway_pcg_ecosystem,
    validate_manifest_schema,
)
from faraway_mother_pcg_assembly import (
    REQUIRED_PCG_GRAPHS,
    TARGET_LEVEL_PATH,
    verify_assembly,
)


class FarawayMotherPCGTests(unittest.TestCase):
    def test_chladni_math_and_symmetry(self):
        # Center sample (0.5, 0.5)
        val_center = evaluate_chladni(0.5, 0.5, 3, 5)
        self.assertIsInstance(val_center, float)
        # Bounded amplitude between -2 and +2 for a=1, b=1
        self.assertTrue(-2.01 <= val_center <= 2.01)

        # Boundary checks
        val_zero = evaluate_chladni(0.0, 0.0, 3, 5)
        self.assertAlmostEqual(val_zero, 0.0, delta=1e-5)

    def test_tension_gradient_computation(self):
        tension = evaluate_tension(0.25, 0.25)
        self.assertTrue(0.0 <= tension <= 1.0)
        tension_center = evaluate_tension(0.5, 0.5)
        self.assertTrue(0.0 <= tension_center <= 1.0)

    def test_biome_classification_logic(self):
        # Near zero Chladni nodal line -> ResonantSeamWay
        self.assertEqual(classify_biome(0.0, 0.0, 0.0, 0.5, 0.05), "ResonantSeamWay")
        # High altitude and high tension -> WeaveRidge
        self.assertEqual(classify_biome(0.5, 0.5, 3000.0, 0.8, 0.5), "WeaveRidge")
        # Low altitude and lower tension -> FrillValley
        self.assertEqual(classify_biome(0.1, 0.1, -2000.0, 0.3, 0.5), "FrillValley")
        # Intermediate -> LaceCanopy
        self.assertEqual(classify_biome(0.3, 0.7, 500.0, 0.5, 0.5), "LaceCanopy")

    def test_pcg_ecosystem_generation_and_manifest_export(self):
        manifest = generate_faraway_pcg_ecosystem(points_per_biome=15, seed=123)
        self.assertEqual(manifest.schema, PCG_SCHEMA)
        self.assertEqual(manifest.total_points, 60)
        self.assertEqual(len(manifest.biome_summaries), 4)

        for b_name, summ in manifest.biome_summaries.items():
            self.assertEqual(summ.point_count, 15)
            self.assertIn(b_name, BIOME_BUILDER_MAP)
            self.assertEqual(summ.material_instance, BIOME_MATERIAL_MAP[b_name])

        with tempfile.TemporaryDirectory() as tmpdir:
            tmp_path = Path(tmpdir) / "test_manifest.json"
            export_manifest(manifest, tmp_path)
            self.assertTrue(tmp_path.is_file())

            data = json.loads(tmp_path.read_text(encoding="utf-8"))
            ok, errors = validate_manifest_schema(data)
            self.assertTrue(ok, f"Validation failed: {errors}")
            self.assertEqual(len(errors), 0)

    def test_level_assembly_verification(self):
        manifest = generate_faraway_pcg_ecosystem(points_per_biome=10, seed=99)
        with tempfile.TemporaryDirectory() as tmpdir:
            tmp_path = Path(tmpdir) / "test_manifest.json"
            export_manifest(manifest, tmp_path)

            res = verify_assembly(str(tmp_path))
            self.assertTrue(res.ok, f"Assembly verify failed: {res.errors}")
            self.assertEqual(res.total_staged_points, 40)
            self.assertEqual(len(res.biomes_verified), 4)
            self.assertEqual(res.pcg_graphs_staged, REQUIRED_PCG_GRAPHS)
            self.assertEqual(len(res.world_fields_connected), 4)
            self.assertEqual(res.narrative_challenge["challenge_id"], "challenge.mother_heart_gate")


if __name__ == "__main__":
    unittest.main()
