"""Pure tests for the reusable walkable Xylophone Trail layout."""
from __future__ import annotations

import unittest

from pcg_xylophone_layout import build_xylophone_path_specs, validate_xylophone_layout


class XylophonePathTests(unittest.TestCase):
    def test_default_layout_is_a_walkable_ascending_path(self):
        specs = build_xylophone_path_specs()
        self.assertEqual(len(specs), 24)
        self.assertEqual(validate_xylophone_layout(specs), [])
        self.assertLess(specs[0].z, specs[-1].z)
        self.assertTrue(all(spec.bar_length > 0.0 for spec in specs))

    def test_seed_identity_is_stable_and_midi_is_pentatonic(self):
        first = build_xylophone_path_specs()
        second = build_xylophone_path_specs()
        self.assertEqual(first, second)
        self.assertEqual(len({spec.seed for spec in first}), len(first))
        self.assertTrue(all(spec.midi_note in range(60, 97) for spec in first))

    def test_count_and_spacing_are_generation_time_controls(self):
        specs = build_xylophone_path_specs(note_count=30, step_spacing=420.0)
        self.assertEqual(len(specs), 30)
        self.assertAlmostEqual(specs[1].x - specs[0].x, 420.0)


if __name__ == "__main__":
    unittest.main()
