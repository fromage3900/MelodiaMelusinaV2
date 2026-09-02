"""Test contract verification for Sea Above Level Loop, Blueprints, PCG Arpeggio Bridge, and Heatmaps."""
from __future__ import annotations

import json
from pathlib import Path
import unittest

PROJECT_ROOT = Path(__file__).resolve().parents[3]
CONTENT_DIR = PROJECT_ROOT / "Content"
PYTHON_DIR = CONTENT_DIR / "Python"

import sys
if str(PYTHON_DIR) not in sys.path:
    sys.path.insert(0, str(PYTHON_DIR))

import stage_seaabove_level_loop as level_loop
from build_pcg_hero_arpeggio_bridge import C_MAJOR_ARPEGGIO, build_bridge_layout, build_bridge_curve_points


class TestSeaAboveLevelLoopContract(unittest.TestCase):
    def test_required_blueprints_assets_exist(self):
        """All Blueprints required for the Sea Above level loop must exist on disk."""
        required_bps = [
            "MelodiaIntegration/Blueprints/BP_MelusinaJRPGCharacter.uasset",
            "MelodiaIntegration/Blueprints/Opening/BP_KaleidoNaveArrivalTrigger.uasset",
            "MelodiaIntegration/Blueprints/BP_Starskiff_MK2.uasset",
            "MelodiaIntegration/Water/Blueprints/BP_MelodiaWaterSimulationZone.uasset",
            "MelodiaIntegration/Blueprints/BP_MelodiaPortal_LockedTraversal.uasset",
            "MelodiaIntegration/Blueprints/BP_MelodiaTraversalGate_HoverFixture.uasset",
        ]
        for bp_rel in required_bps:
            bp_path = CONTENT_DIR / bp_rel
            self.assertTrue(bp_path.is_file(), f"Missing required Sea Above Blueprint: {bp_path}")

    def test_arpeggio_bridge_pitch_classes_and_geometry(self):
        """PCG Arpeggio Bridge must conform to 24-node C-Major arpeggio progression and rise."""
        self.assertEqual(len(C_MAJOR_ARPEGGIO), 24)
        # All pitches must belong to C Major triad (C, E, G -> 0, 4, 7 modulo 12)
        for midi in C_MAJOR_ARPEGGIO:
            self.assertIn(midi % 12, {0, 4, 7}, f"MIDI pitch {midi} is not in C Major triad")

        interactive, decorations = build_bridge_layout(
            note_count=24, step_spacing=180.0, bridge_rise=1800.0, walk_width=220.0
        )
        self.assertEqual(len(interactive), 24)
        self.assertGreater(len(decorations), 0)

        # Check monotonic ascent along Z
        z_coords = [node[2] for node in interactive]
        for i in range(len(z_coords) - 1):
            self.assertLess(z_coords[i], z_coords[i + 1], "Bridge step Z must strictly ascend")

        # Total rise must be 1800 units (+18m)
        total_rise = z_coords[-1] - z_coords[0]
        self.assertAlmostEqual(total_rise, 1800.0, delta=1.0)

        # Traversal curve points must match interactive count
        curve = build_bridge_curve_points(note_count=24, step_spacing=180.0, bridge_rise=1800.0)
        self.assertEqual(len(curve), 24)

    def test_core_level_loop_zones_and_scale_contract(self):
        """Sea Above 5-zone level loop must satisfy corridor scale and exclusion contracts."""
        manifest = level_loop.layout_core_level_loop_and_export_heatmaps()
        self.assertEqual(manifest.get("schema"), "melodia.sea_above_pcg_heatmap.v1")
        self.assertEqual(manifest.get("level"), "LV_SeaAbove_Prototype")

        zones = manifest.get("level_loop_zones", [])
        self.assertEqual(len(zones), 5)

        zone_ids = [z["id"] for z in zones]
        expected_zones = [
            "zone_1_littoral_basin",
            "zone_2_arpeggio_bridge",
            "zone_3_celestial_overlook",
            "zone_4_starskiff_waterway",
            "zone_5_perimeter_barrier_reef",
        ]
        for ez in expected_zones:
            self.assertIn(ez, zone_ids)

        # Verify scale contract
        scale = manifest.get("scale_contract", {})
        self.assertGreaterEqual(scale.get("corridor_width_cm", 0), 300.0)
        self.assertGreaterEqual(scale.get("clear_height_cm", 0), 240.0)
        self.assertGreaterEqual(scale.get("hall_width_cm", 0), 1200.0)
        self.assertGreaterEqual(scale.get("skiff_channel_width_cm", 0), 800.0)

        # Verify traversal flow
        flow = manifest.get("traversal_loop_flow", [])
        self.assertEqual(len(flow), 6)
        self.assertEqual(flow[0]["node"], "Shorewake Littoral Spawn")
        self.assertEqual(flow[1]["node"], "Arpeggio Bridge Entry")
        self.assertEqual(flow[2]["node"], "Arpeggio Far Gate")
        self.assertEqual(flow[3]["node"], "Celestial Coral Spire Arena")
        self.assertEqual(flow[4]["node"], "Starskiff Mooring / Gliding")
        self.assertEqual(flow[5]["node"], "Return Current to Dock")

    def test_heatmap_plate_and_audit_artifacts_generated(self):
        """Heatmap PNG plate and audit report must be valid and non-empty."""
        png_path = PROJECT_ROOT / "Saved" / "Portfolio" / "PCG" / "LV_SeaAbove_Prototype_pcg_heatmap.png"
        audit_path = PROJECT_ROOT / "Saved" / "Audit" / "sea_above_level_loop_audit.json"

        self.assertTrue(png_path.is_file(), f"Missing heatmap PNG: {png_path}")
        self.assertGreater(png_path.stat().st_size, 1000, "Heatmap PNG is too small or corrupted")

        self.assertTrue(audit_path.is_file(), f"Missing audit report: {audit_path}")
        audit_data = json.loads(audit_path.read_text(encoding="utf-8"))
        self.assertEqual(audit_data.get("status"), "PASS")
        self.assertTrue(audit_data.get("heatmap_contract_present"))
        self.assertEqual(audit_data.get("zones_count"), 5)


if __name__ == "__main__":
    unittest.main()
