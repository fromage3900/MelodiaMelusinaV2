"""Unit tests for Melusina Transforming WaveHarp, Real-Time Archery Combat & Overworld HUD Bridge.

Verifies:
1. Default stance & WaveHarp transformation state machine (Harp <-> Bow).
2. Transformation duration, cooldown gates, and mesh/socket switching.
3. Real-time archery combat: aiming, draw tension progression, crystal arrow firing.
4. Real-time harp playing: 7 diatonic strings, MIDI pitches, chord resonance.
5. Live Jev Bow Conductor integration (with fallback support).
6. Overworld HUD data contract & switch button state.
"""
from __future__ import annotations

import os
import unittest

from gmm.melodia.jev_weapon_bridge import (
    HARP_STRINGS,
    MESH_BOW,
    MESH_HARP,
    WEAPON_SOCKET_BOW_HELD,
    WEAPON_SOCKET_HARP_HELD,
    MelusinaWeaponStanceManager,
    WeaponStance,
    get_melusina_weapon_manager,
    reset_melusina_weapon_manager,
)


class TestMelusinaWeaponBridge(unittest.TestCase):

    def setUp(self):
        reset_melusina_weapon_manager()
        self.mgr = MelusinaWeaponStanceManager()

    def tearDown(self):
        reset_melusina_weapon_manager()

    # -----------------------------------------------------------------------
    # Stance & Transformation Tests
    # -----------------------------------------------------------------------

    def test_initial_stance_is_harp_exploration(self):
        self.assertEqual(self.mgr.current_stance, WeaponStance.HARP_EXPLORATION)
        self.assertFalse(self.mgr.is_transforming)
        hud = self.mgr.get_hud_view_data(now=10.0)
        self.assertEqual(hud["current_stance"], WeaponStance.HARP_EXPLORATION)
        self.assertTrue(hud["is_harp"])
        self.assertFalse(hud["is_bow"])
        self.assertEqual(hud["stance_label"], "HARP [EXPLORATION]")
        self.assertEqual(hud["switch_button_label"], "SWITCH TO BOW")
        self.assertTrue(hud["switch_button_enabled"])
        self.assertTrue(hud["stave_visible"])
        self.assertFalse(hud["reticle_visible"])

    def test_toggle_to_bow_combat_and_cooldown_gate(self):
        t0 = 100.0
        # First toggle: Harp -> Bow
        event = self.mgr.toggle_weapon_mode(now=t0)
        self.assertTrue(event["ok"])
        self.assertEqual(event["new_stance"], WeaponStance.BOW_COMBAT)
        self.assertEqual(event["active_mesh"], MESH_BOW)
        self.assertEqual(event["socket"], WEAPON_SOCKET_BOW_HELD)
        self.assertTrue(self.mgr.is_transforming)

        # Immediate second toggle must be rejected (transformation in progress)
        event2 = self.mgr.toggle_weapon_mode(now=t0 + 0.2)
        self.assertFalse(event2["ok"])
        self.assertIn("in progress", event2["error"])

        # Complete transformation at t0 + 0.8
        comp = self.mgr.complete_transformation(now=t0 + 0.8)
        self.assertTrue(comp["ok"])
        self.assertFalse(self.mgr.is_transforming)

        # Still on cooldown until t0 + 1.2
        event3 = self.mgr.toggle_weapon_mode(now=t0 + 0.9)
        self.assertFalse(event3["ok"])
        self.assertIn("cooldown", event3["error"])

        # After cooldown (t0 + 1.5): can toggle back to Harp
        event4 = self.mgr.toggle_weapon_mode(now=t0 + 1.5)
        self.assertTrue(event4["ok"])
        self.assertEqual(event4["new_stance"], WeaponStance.HARP_EXPLORATION)
        self.assertEqual(event4["active_mesh"], MESH_HARP)
        self.assertEqual(event4["socket"], WEAPON_SOCKET_HARP_HELD)

    # -----------------------------------------------------------------------
    # Real-Time Archery Combat Tests
    # -----------------------------------------------------------------------

    def test_archery_actions_restricted_in_harp_mode(self):
        # Cannot aim or draw while in Harp stance
        self.assertEqual(self.mgr.current_stance, WeaponStance.HARP_EXPLORATION)
        aim_res = self.mgr.start_aim()
        self.assertFalse(aim_res["ok"])
        draw_res = self.mgr.start_draw()
        self.assertFalse(draw_res["ok"])
        fire_res = self.mgr.release_arrow()
        self.assertFalse(fire_res["ok"])

    def test_archery_aim_draw_and_release_in_bow_mode(self):
        # Switch to Bow and complete transform
        self.mgr.toggle_weapon_mode(now=10.0)
        self.mgr.complete_transformation(now=10.8)

        # Aim
        aim_res = self.mgr.start_aim()
        self.assertTrue(aim_res["ok"])
        self.assertTrue(self.mgr.is_aiming)

        # Start draw at t = 20.0
        draw_res = self.mgr.start_draw(now=20.0)
        self.assertTrue(draw_res["ok"])
        self.assertTrue(self.mgr.is_drawing)

        # Check half tension at t = 20.5 (max_draw_duration = 1.0s)
        tension_half = self.mgr.update_draw(now=20.5)
        self.assertAlmostEqual(tension_half, 0.5, delta=0.05)

        # Release arrow at t = 21.0 (full tension)
        fire_res = self.mgr.release_arrow(now=21.0)
        self.assertTrue(fire_res["ok"])
        self.assertEqual(fire_res["event"], "ArrowReleased")
        self.assertAlmostEqual(fire_res["tension"], 1.0, delta=0.01)
        self.assertGreaterEqual(fire_res["speed_cms"], 8000.0)
        self.assertGreaterEqual(fire_res["damage"], 100.0)
        self.assertEqual(self.mgr.loose_count, 1)
        self.assertFalse(self.mgr.is_drawing)

        # Stop aim
        stop_res = self.mgr.stop_aim()
        self.assertTrue(stop_res["ok"])
        self.assertFalse(self.mgr.is_aiming)

    # -----------------------------------------------------------------------
    # Real-Time Harp Exploration Tests
    # -----------------------------------------------------------------------

    def test_harp_plucking_and_chord_resonance(self):
        self.assertEqual(self.mgr.current_stance, WeaponStance.HARP_EXPLORATION)

        # Pluck String 0 (C4 / Do / MIDI 60)
        pluck0 = self.mgr.pluck_harp_string(0, velocity=0.8, now=5.0)
        self.assertTrue(pluck0["ok"])
        self.assertEqual(pluck0["note"], "C4")
        self.assertEqual(pluck0["midi_pitch"], 60)
        self.assertEqual(pluck0["solfege"], "Do")

        # Pluck String 4 (G4 / Sol / MIDI 67)
        pluck4 = self.mgr.pluck_harp_string(4, velocity=1.0, now=5.2)
        self.assertTrue(pluck4["ok"])
        self.assertEqual(pluck4["note"], "G4")
        self.assertEqual(pluck4["midi_pitch"], 67)

        # Invalid string index
        pluck_err = self.mgr.pluck_harp_string(99)
        self.assertFalse(pluck_err["ok"])

        # Play C Major chord (C4, E4, G4 -> indices 0, 2, 4)
        chord_res = self.mgr.play_harp_chord([0, 2, 4], velocity=0.9, now=6.0)
        self.assertTrue(chord_res["ok"])
        self.assertEqual(chord_res["chord_size"], 3)
        self.assertGreater(self.mgr.active_resonance_score, 0.4)

    def test_harp_plucking_restricted_in_bow_mode(self):
        self.mgr.toggle_weapon_mode(now=10.0)
        self.mgr.complete_transformation(now=10.8)
        self.assertEqual(self.mgr.current_stance, WeaponStance.BOW_COMBAT)

        pluck_res = self.mgr.pluck_harp_string(0)
        self.assertFalse(pluck_res["ok"])
        self.assertIn("not in HARP_EXPLORATION", pluck_res["error"])

    # -----------------------------------------------------------------------
    # Jev Conductor Integration Tests
    # -----------------------------------------------------------------------

    def test_conduct_frame_evaluates_options(self):
        # Switch to Bow Combat
        self.mgr.toggle_weapon_mode(now=10.0)
        self.mgr.complete_transformation(now=10.8)

        # Conduct frame with combat telemetry
        res = self.mgr.conduct_frame(
            telemetry={
                "bpm_intensity": 0.85,
                "beat_energy": 0.9,
                "target_distance_m": 12.0,
                "movement_speed": 180.0,
                "wind_strength": 0.1,
            },
            now=15.0,
        )
        self.assertTrue(res["ok"])
        self.assertIn("bow_choice", res["decision"])
        self.assertIn(res["decision"]["source"], ("jev-live", "classical-fallback"))

        # Verify HUD view data reflects conductor decision
        hud = self.mgr.get_hud_view_data(now=15.0)
        self.assertEqual(hud["conductor_choice"], res["decision"]["bow_choice"])
        self.assertIn("JEV BOW CONDUCTOR", hud["conductor_hud_summary"])

    def test_live_key_evaluates_jev_live(self):
        if not os.environ.get("TYPESAFE_API_KEY"):
            self.skipTest("TYPESAFE_API_KEY not in environment")

        res = self.mgr.conduct_frame(
            telemetry={"bpm_intensity": 0.7, "beat_energy": 0.75, "target_distance_m": 10.0},
            now=20.0,
        )
        self.assertTrue(res["ok"])
        self.assertEqual(res["decision"]["source"], "jev-live")


if __name__ == "__main__":
    unittest.main()
