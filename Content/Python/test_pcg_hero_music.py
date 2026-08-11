"""Pure regression tests for the reusable hero graph contracts."""
from __future__ import annotations

import unittest
from math import dist

import pcg_hero_music_control as control
from build_pcg_hero_arpeggio_bridge import C_MAJOR_ARPEGGIO, build_bridge_curve_points, build_bridge_layout
from build_pcg_hero_bell_tree_garden import build_bell_garden_layout
from pcg_crystal_harp_layout import build_crystal_harp_layout, crystal_harp_midi_pattern, validate_crystal_harp_layout
from build_pcg_hero_resonance_cathedral import build_cathedral_layout, build_cathedral_vault_curve_points, build_piano_roll_detail_points, build_piano_roll_positions, chord_for_station


class HeroMusicContractTests(unittest.TestCase):
    def test_driver_bridge_keeps_all_eleven_properties_and_proof_preset(self):
        snapshot = control.sanitize_snapshot()
        self.assertEqual(tuple(snapshot.__dict__.keys()), control.CONTROL_PROPERTIES)
        payload = control.regression_payload()
        self.assertTrue(payload["all_properties_present"])
        self.assertEqual(payload["proof_preset"], {"CullDistance": 0.0, "WriteCustomDepth": True, "StencilValue": 3})
        self.assertEqual(payload["alias_count"], 11)
        self.assertEqual(control.CONTROL_ALIAS_TARGETS["ArraySpacing"], "CellSize")
        self.assertEqual(control.CONTROL_ALIAS_TARGETS["CullDistance"], "InstanceEndCullDistance")
        self.assertEqual(control.CONTROL_ALIAS_TARGETS["WriteCustomDepth"], "RenderCustomDepth")
        self.assertEqual(control.map_control_aliases(snapshot, "ResonanceCathedral")["Depth"], "VaultHeight")
        bell_aliases = control.map_control_aliases(snapshot, "BellTreeGarden")
        self.assertEqual(bell_aliases["ArrayCount"], "BellCount")
        self.assertEqual(bell_aliases["WalkWidth"], "GardenPathWidth")
        xylophone_aliases = control.map_control_aliases(snapshot, "XylophoneTrail")
        self.assertEqual(xylophone_aliases["ArrayCount"], "BarSectionCount")
        self.assertEqual(xylophone_aliases["ArraySpacing"], "BarSpacing")
        self.assertEqual(xylophone_aliases["Depth"], "TrailRise")
        harp_aliases = control.map_control_aliases(snapshot, "CrystalHarpGrove")
        self.assertEqual(harp_aliases["ArrayCount"], "StringCount")
        self.assertEqual(harp_aliases["WalkWidth"], "StringBankWidth")

    def test_authoring_baselines_are_independent_per_instrument(self):
        self.assertEqual(control.authoring_overrides("ResonanceCathedral")["ArrayCount"], 4)
        self.assertEqual(control.authoring_overrides("ArpeggioBridge")["ArrayCount"], 24)
        self.assertEqual(control.authoring_overrides("BellTreeGarden")["ArrayCount"], 18)
        self.assertEqual(control.authoring_overrides("XylophoneTrail")["ArrayCount"], 4)
        self.assertEqual(control.authoring_overrides("CrystalHarpGrove")["ArrayCount"], 20)
        self.assertEqual(control.authoring_overrides("BellTreeGarden")["Depth"], 900.0)

    def test_cathedral_has_twelve_unique_seeded_chord_pads(self):
        pads, _ = build_cathedral_layout()
        self.assertEqual(len(pads), 12)
        seeds = [(node_index << 16) | (degree << 8) | midi for _, _, _, node_index, degree, midi in pads]
        self.assertEqual(len(seeds), len(set(seeds)))
        self.assertEqual([midi for *_, midi in pads[:3]], list(chord_for_station(0)))
        self.assertEqual([degree for *_, degree, _ in pads], list(range(3)) * 4)

    def test_cathedral_is_a_measured_piano_roll_not_isolated_pads(self):
        positions = build_piano_roll_positions()
        keybed, ebony = build_piano_roll_detail_points(4, 480.0, 220.0)
        self.assertEqual(len(positions), 12)
        self.assertTrue(all(a[0] < b[0] for a, b in zip(positions, positions[1:])))
        self.assertAlmostEqual(positions[1][0] - positions[0][0], 160.0)
        self.assertEqual(len(ebony), 8)
        for x, y, z, _ in ebony:
            self.assertTrue(any(a[0] < x < b[0] for a, b in zip(positions, positions[1:])))
        self.assertEqual(keybed[:3], (0.0, 0.0, 0.0))

    def test_bridge_has_twenty_four_unique_seeded_notes(self):
        nodes, _ = build_bridge_layout()
        self.assertEqual(len(nodes), 24)
        seeds = [(node_index << 16) | ((lane + 1) << 8) | midi for _, _, _, node_index, lane, midi in nodes]
        self.assertEqual(len(seeds), len(set(seeds)))
        self.assertEqual(tuple(midi for *_, midi in nodes), C_MAJOR_ARPEGGIO)
        self.assertEqual(C_MAJOR_ARPEGGIO, (60, 64, 67, 72, 76, 79, 84, 79) * 3)
        self.assertTrue(all(midi % 12 in {0, 4, 7} for midi in C_MAJOR_ARPEGGIO))
        self.assertLessEqual(max(C_MAJOR_ARPEGGIO) - min(C_MAJOR_ARPEGGIO), 24)

    def test_both_heroes_have_measured_curve_contracts(self):
        vault = build_cathedral_vault_curve_points()
        bridge = build_bridge_curve_points()
        self.assertGreaterEqual(len(vault), 5)
        self.assertEqual(len(bridge), 24)
        self.assertTrue(all(a[0] < b[0] for a, b in zip(vault, vault[1:])))
        self.assertTrue(all(a[0] < b[0] for a, b in zip(bridge, bridge[1:])))
        self.assertGreater(vault[len(vault) // 2][2], vault[0][2])
        self.assertGreater(bridge[-1][2], bridge[0][2])

    def test_bell_garden_is_evenly_spaced_and_height_aware(self):
        nodes, _ = build_bell_garden_layout()
        self.assertEqual(len(nodes), 18)
        distances = [dist(nodes[index][:3], nodes[index + 1][:3]) for index in range(len(nodes) - 1)]
        self.assertLess(max(distances) - min(distances), 1.0)
        self.assertTrue(all(nodes[index + 1][2] > nodes[index][2] for index in range(len(nodes) - 1)))

    def test_crystal_harp_has_five_four_string_gates_and_press_contract(self):
        nodes, landmarks = build_crystal_harp_layout()
        self.assertEqual(len(nodes), 20)
        self.assertEqual(len(landmarks), 5)
        self.assertEqual(len({(node[3], node[5]) for node in nodes}), 20)
        self.assertEqual(validate_crystal_harp_layout(nodes), [])
        self.assertEqual(tuple(node[5] for node in nodes), crystal_harp_midi_pattern())
        self.assertTrue(all(nodes[index + 4][2] > nodes[index][2] for index in range(len(nodes) - 4)))


if __name__ == "__main__":
    unittest.main()
