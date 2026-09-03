"""Contract and Unit Test Suite for Melodia Optical LOD & LookDev Pipeline."""

import json
import unittest
from pathlib import Path

import numpy as np

PROJECT_ROOT = Path(__file__).resolve().parents[1]
import sys
sys.path.insert(0, str(PROJECT_ROOT))
sys.path.insert(0, str(PROJECT_ROOT / "Content" / "Python"))

from Tools.LookDev.build_optical_lod_matrix import (
    apply_toksvig_roughness,
    generate_bayer_matrix_8x8,
    generate_blue_noise_64x64,
    generate_chladni_heightfield,
    generate_thin_film_iridescence_lut,
    height_to_normal_map,
    validate_manifest,
)
from Content.Python.melodia_optical_lod_pipeline import (
    evaluate_dither_threshold,
    evaluate_lod_crossfade,
    synthesize_material_instances,
)


class TestOpticalLODLookDev(unittest.TestCase):
    def setUp(self):
        self.manifest_path = PROJECT_ROOT / "specs" / "lookdev" / "optical_lod_manifest.v1.json"

    def test_manifest_schema_and_integrity(self):
        self.assertTrue(self.manifest_path.is_file(), f"Manifest missing: {self.manifest_path}")
        ok, errs = validate_manifest(self.manifest_path)
        self.assertTrue(ok, f"Manifest validation errors: {errs}")

        data = json.loads(self.manifest_path.read_text(encoding="utf-8"))
        self.assertEqual(data.get("schema"), "melodia.optical_lod_manifest.v1")
        self.assertGreaterEqual(data.get("total_assets", 0), 3)
        self.assertGreaterEqual(data.get("total_textures_generated", 0), 50)

        # Check all 4 tiers exist for each asset
        for a_name, a_rec in data.get("assets", {}).items():
            lod_tiers = a_rec.get("lod_tiers", {})
            self.assertEqual(len(lod_tiers), 4)
            for tier_key in ["LOD0", "LOD1", "LOD2", "LOD3"]:
                self.assertIn(tier_key, lod_tiers)
                maps = lod_tiers[tier_key].get("maps", {})
                for map_key in ["base_color", "normal", "orm_packed", "height"]:
                    p_str = maps.get(map_key)
                    self.assertTrue(Path(p_str).is_file(), f"Texture file missing: {p_str}")

    def test_bayer_and_blue_noise_generation(self):
        bayer = generate_bayer_matrix_8x8()
        self.assertEqual(bayer.shape, (8, 8))
        self.assertAlmostEqual(float(bayer.min()), 0.0, places=2)
        self.assertAlmostEqual(float(bayer.max()), 63.0 / 64.0, places=2)

        blue_noise = generate_blue_noise_64x64(seed=42)
        self.assertEqual(blue_noise.shape, (64, 64))
        self.assertGreaterEqual(float(blue_noise.min()), 0.0)
        self.assertLessEqual(float(blue_noise.max()), 1.0)
        # Verify non-trivial frequency distribution
        self.assertAlmostEqual(float(blue_noise.mean()), 0.5, delta=0.15)

    def test_toksvig_roughness_adjustment(self):
        height = generate_chladni_heightfield(128, n=3, m=5, seed=42)
        normal = height_to_normal_map(height, strength=3.0)
        base_rough = np.ones((128, 128), dtype=np.float32) * 0.3

        # Test zero factor preserves roughness
        r_zero = apply_toksvig_roughness(base_rough, normal, toksvig_weight=0.0)
        np.testing.assert_allclose(r_zero, base_rough, rtol=1e-5)

        # Test positive factor increases roughness where normals disperse
        r_adj = apply_toksvig_roughness(base_rough, normal, toksvig_weight=1.0)
        self.assertTrue(np.all(r_adj >= base_rough))
        self.assertGreater(float(r_adj.mean()), float(base_rough.mean()))

    def test_iridescence_lut_properties(self):
        lut = generate_thin_film_iridescence_lut(width=128, height=512)
        self.assertEqual(lut.shape, (512, 128, 3))
        self.assertGreaterEqual(float(lut.min()), 0.0)
        self.assertLessEqual(float(lut.max()), 1.0)

        # Grazing angle (right column, index 127) should have higher intensity than facing (left column, index 0)
        facing_intensity = float(lut[:, 0, :].mean())
        grazing_intensity = float(lut[:, 127, :].mean())
        self.assertGreater(grazing_intensity, facing_intensity)

    def test_crossfade_and_pipeline_synthesis(self):
        # Test crossfade math
        self.assertEqual(evaluate_lod_crossfade(10.0, 10.0, 20.0), 0.0)
        self.assertEqual(evaluate_lod_crossfade(15.0, 10.0, 20.0), 0.5)
        self.assertEqual(evaluate_lod_crossfade(25.0, 10.0, 20.0), 1.0)
        self.assertEqual(evaluate_lod_crossfade(5.0, 10.0, 20.0), 0.0)

        # Test dither threshold
        self.assertFalse(evaluate_dither_threshold(0, 0, 0.0))
        self.assertTrue(evaluate_dither_threshold(0, 0, 1.0))

        # Test pipeline report — 44 after surreal fabric expansion (11 assets ×4 LODs); allow >=12
        report = synthesize_material_instances(str(self.manifest_path))
        self.assertTrue(report.ok, f"Pipeline synthesis failed: {report.errors}")
        self.assertGreaterEqual(report.total_material_instances, 12)
        self.assertEqual(len(report.instances), report.total_material_instances)
        self.assertEqual(report.total_material_instances % 4, 0)

        # Verify instance binding contents
        for inst in report.instances:
            self.assertTrue(inst.instance_name.startswith("MI_"))
            self.assertIn("LOD_Tier_Index", inst.scalar_parameters)
            self.assertIn("BaseColorMap", inst.texture_parameters)
            self.assertIn("NormalMap", inst.texture_parameters)
            self.assertIn("ORMMap", inst.texture_parameters)
            self.assertIn("HeightMap", inst.texture_parameters)


if __name__ == "__main__":
    unittest.main()
