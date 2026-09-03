"""Test contract verification for Sea Above text injection Blueprint systems."""
from __future__ import annotations

import importlib.util
import json
import re
import unittest
from pathlib import Path


# Import melodia_water_gameplay_t3d
import sys
PROJECT_ROOT = Path(__file__).resolve().parents[3]
SPECS_DIR = PROJECT_ROOT / "specs"
PATTERNS_DIR = PROJECT_ROOT / "Docs" / "T3D_Patterns" / "patterns"
TOOLS_DIR = PROJECT_ROOT / "Tools"
if str(TOOLS_DIR) not in sys.path:
    sys.path.insert(0, str(TOOLS_DIR))

import melodia_water_gameplay_t3d as water_t3d


class TestSeaAboveT3DContract(unittest.TestCase):
    def test_sea_above_patterns_exist_and_format(self):
        """Sea Above T3D pattern files must exist and declare valid K2Nodes."""
        expected_patterns = [
            "sea_above_pulse_hook.t3d",
            "sea_above_anomaly_trigger.t3d",
            "sea_above_membrane_sheen.t3d",
        ]
        for pat_name in expected_patterns:
            pat_path = PATTERNS_DIR / pat_name
            self.assertTrue(pat_path.is_file(), f"Missing pattern: {pat_path}")
            text = pat_path.read_text(encoding="utf-8")
            self.assertIn("Begin Object Class=/Script/BlueprintGraph.", text)
            self.assertIn("End Object", text)
            # Ensure placeholders are formatted with {{...}}
            placeholders = re.findall(r"\{\{([A-Za-z0-9_:]+)\}\}", text)
            self.assertTrue(len(placeholders) > 0, f"Pattern {pat_name} has no placeholders")

    def test_sea_above_mutation_requests_conform_to_schema(self):
        """Sea Above T3D mutation request specs must conform to schema and declare postconditions."""
        schema_path = SPECS_DIR / "schemas" / "t3d_mutation_request.v1.json"
        self.assertTrue(schema_path.exists(), f"Missing schema: {schema_path}")

        req_files = [
            SPECS_DIR / "t3d" / "sea_above_pulse_driver.json",
            SPECS_DIR / "t3d" / "sea_above_anomaly_burst.json",
        ]
        for req_path in req_files:
            self.assertTrue(req_path.is_file(), f"Missing mutation request: {req_path}")
            data = json.loads(req_path.read_text(encoding="utf-8"))
            self.assertEqual(data.get("schema"), "melodia.t3d_mutation_request.v1")
            self.assertTrue(data.get("request_id", "").startswith("t3d-sea-above-"))
            self.assertIsInstance(data.get("operations"), list)
            self.assertTrue(len(data["operations"]) > 0)

            post = data.get("expected_postconditions", {})
            self.assertIsInstance(post.get("required_nodes"), list)
            self.assertTrue(len(post["required_nodes"]) > 0)
            self.assertEqual(post.get("compile_error_count"), 0)
            self.assertTrue(post.get("reexport_after_save"))

            verification = data.get("verification", {})
            self.assertTrue(verification.get("compile_zero_errors"))
            self.assertTrue(verification.get("assert_graph_match"))

    def test_water_gameplay_t3d_targets_include_sea_above(self):
        """melodia_water_gameplay_t3d must include Sea Above targets."""
        sea_above_targets = [
            "sea_above_pulse_cycle",
            "sea_above_anomaly_burst",
            "sea_above_membrane_sheen",
        ]
        manifest = water_t3d.target_manifest()
        manifest_ids = [t["target_id"] for t in manifest]

        for target_id in sea_above_targets:
            self.assertIn(target_id, manifest_ids, f"Target {target_id} missing from manifest")
            target = water_t3d.get_target(target_id)
            self.assertEqual(target.target_id, target_id)
            self.assertTrue(len(target.required_nodes) > 0)

    def test_sea_above_stage_manifest_invariants(self):
        """Sea Above stage manifest must enforce biological pulse & presentation ranges."""
        from stage_seaabove_slice import build_stage_manifest, SEA_ABOVE_PULSE_CONFIG

        manifest = build_stage_manifest()
        self.assertEqual(manifest["schema"], "melodia.sea_above_slice_stage.v1")
        self.assertEqual(manifest["slice_id"], "P0_SeaAbove_FirstDream")

        pulse = SEA_ABOVE_PULSE_CONFIG
        self.assertGreaterEqual(pulse["pulse_period_seconds_min"], 12.0)
        self.assertLessEqual(pulse["pulse_period_seconds_max"], 20.0)
        self.assertTrue(pulse["pulse_period_seconds_min"] <= pulse["pulse_period_default"] <= pulse["pulse_period_seconds_max"])
        self.assertEqual(pulse["membrane_sheen_pristine"], 0.18)
        self.assertEqual(pulse["membrane_sheen_healed"], 0.32)


if __name__ == "__main__":
    unittest.main()
