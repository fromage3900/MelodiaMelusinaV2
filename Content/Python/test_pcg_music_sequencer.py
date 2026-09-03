import unittest

from build_pcg_music_sequencer import build_step_specs


class PCGMusicSequencerTests(unittest.TestCase):
    def test_default_grid_count(self):
        specs = build_step_specs()
        self.assertEqual(len(specs), 64)
        self.assertEqual(len({spec.seed for spec in specs}), 64)

    def test_step_and_lane_ranges(self):
        specs = build_step_specs()
        self.assertEqual({spec.step for spec in specs}, set(range(16)))
        self.assertEqual({spec.lane for spec in specs}, set(range(4)))

    def test_step_rows_are_spatially_ordered(self):
        specs = build_step_specs()
        for lane in range(4):
            row = [spec for spec in specs if spec.lane == lane]
            self.assertEqual([spec.step for spec in row], list(range(16)))
            self.assertLess(row[0].x, row[-1].x)
        rows = [next(spec for spec in specs if spec.step == 0 and spec.lane == lane).y for lane in range(4)]
        self.assertEqual(rows, sorted(rows))


if __name__ == "__main__":
    unittest.main()
