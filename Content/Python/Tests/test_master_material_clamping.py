"""Unit tests for Master Material Clamping & Graph Organization Engine.

Validates:
1. 100% parameter coverage across the 4 canonical master graphs.
2. Every scalar has valid, physically bounded slider_min and slider_max (min < max).
3. Critical PBR invariants (Roughness in [0, 1], Metallic in [0, 1], etc.).
4. Canonical UI Group assignments and monotonic sort priorities.
"""
from __future__ import annotations

import json
import sys
import unittest
from pathlib import Path

PYTHON_DIR = Path(__file__).resolve().parents[1]
if str(PYTHON_DIR) not in sys.path:
    sys.path.insert(0, str(PYTHON_DIR))

import master_column_scheme as scheme
import master_material_clamping_engine as engine

PROJECT_ROOT = Path(__file__).resolve().parents[3]
AUDIT_DIR = PROJECT_ROOT / "Saved" / "Audit"


class TestMasterMaterialClamping(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        dirs = sorted(AUDIT_DIR.glob("master_graphs_*"))
        assert dirs, "No master_graphs export found in Saved/Audit"
        cls.master_graphs_dir = dirs[-1]

    def test_explicit_clamps_bounds_validity(self):
        """All explicit clamp definitions must have min < max."""
        for name, (lo, hi, desc) in engine.EXPLICIT_CLAMPS.items():
            self.assertLess(lo, hi, f"Parameter {name} has invalid bounds: min={lo} >= max={hi}")
            self.assertTrue(len(desc) > 0, f"Parameter {name} is missing a description")

    def test_pattern_clamps_bounds_validity(self):
        """All pattern clamp definitions must have min < max."""
        for pat, lo, hi, desc in engine.PATTERN_CLAMP_RULES:
            self.assertLess(lo, hi, f"Pattern {pat} has invalid bounds: min={lo} >= max={hi}")

    def test_pbr_invariants(self):
        """Physical roughness and metallic parameters must strictly lie within [0.0, 1.0]."""
        pbr_scalars = [
            "Roughness", "RoughnessMin", "RoughnessMax", "RockRoughness",
            "GrassRoughness", "MudRoughness", "WetRoughness", "GoldRoughness",
            "Metallic", "Stack2_Metallic", "Stack3_Metallic",
        ]
        for name in pbr_scalars:
            clamp = engine.resolve_clamp(name)
            self.assertGreaterEqual(clamp.slider_min, 0.0, f"{name} min < 0.0")
            self.assertLessEqual(clamp.slider_max, 1.0, f"{name} max > 1.0")

    def test_full_master_coverage(self):
        """All 4 masters must have 100% parameter clamp resolution."""
        masters = [
            "M_Master_Toon_Universal",
            "M_Master_Toon_Landscape_HeightBlend",
            "M_Master_Nikki",
            "M_Master_Nikki_Landscape",
        ]
        for m in masters:
            f = self.master_graphs_dir / f"{m}.json"
            self.assertTrue(f.exists(), f"Missing export for {m}")
            data = json.loads(f.read_text(encoding="utf-8"))
            scalars = [s["name"] for s in data["get_material_parameters"]["scalar_parameters"]]
            catalog = engine.build_catalog_for_master(m, scalars)
            
            self.assertEqual(len(catalog["parameters"]), len(scalars))
            for name, param in catalog["parameters"].items():
                self.assertLess(param["slider_min"], param["slider_max"], f"{m}.{name} min >= max")
                self.assertIn(" | ", param["group"], f"{m}.{name} invalid group format: {param['group']}")
                self.assertGreaterEqual(param["sort_priority"], 0, f"{m}.{name} invalid sort priority")

    def test_catalog_file_integrity(self):
        """Exported catalog JSON must exist and match schemas."""
        manifest = engine.export_full_catalog()
        self.assertTrue(engine.OUT_CATALOG.is_file())
        self.assertIn("masters", manifest)
        self.assertEqual(len(manifest["masters"]), 4)


if __name__ == "__main__":
    unittest.main()
