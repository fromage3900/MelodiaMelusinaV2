import unittest

from pcg_piano_layout import (
    build_layout,
    expected_counts,
    is_black_midi,
    note_name,
    pack_seed,
    split_layout,
    unpack_seed,
)


class PCGPianoLayoutTests(unittest.TestCase):
    def test_full_keyboard_counts(self):
        self.assertEqual(expected_counts(), (88, 52, 36))

    def test_midi_extremes_and_names(self):
        specs = build_layout()
        self.assertEqual(specs[0].midi_note, 21)
        self.assertEqual(specs[-1].midi_note, 108)
        self.assertEqual(specs[0].note_name, "A0")
        self.assertEqual(specs[-1].note_name, "C8")

    def test_black_pattern(self):
        self.assertTrue(all(is_black_midi(midi) for midi in (22, 25, 27, 30, 32)))
        self.assertFalse(any(is_black_midi(midi) for midi in (21, 23, 24, 26, 28, 29, 31)))

    def test_indices_and_seed_round_trip(self):
        specs = build_layout()
        for spec in specs:
            self.assertEqual(unpack_seed(spec.seed), (spec.key_index, spec.midi_note))
        self.assertEqual(pack_seed(0, 21), specs[0].seed)
        self.assertEqual(pack_seed(87, 108), specs[-1].seed)

    def test_black_keys_are_rear_aligned_and_between_whites(self):
        specs = build_layout()
        whites, blacks = split_layout(specs)
        self.assertEqual(len(whites), 52)
        self.assertEqual(len(blacks), 36)
        self.assertTrue(all(spec.y > 0.0 for spec in blacks))
        self.assertTrue(all(spec.z > whites[0].z for spec in blacks))
        for black in blacks:
            lower = max((spec for spec in whites if spec.midi_note < black.midi_note), key=lambda spec: spec.midi_note)
            upper = min((spec for spec in whites if spec.midi_note > black.midi_note), key=lambda spec: spec.midi_note)
            self.assertGreater(black.x, lower.x)
            self.assertLess(black.x, upper.x)


if __name__ == "__main__":
    unittest.main()
