"""Tests for MelodiaRhythmClock — BPM, timing windows, hit testing, beat tracking."""
from __future__ import annotations

import time
import unittest

from gmm.game.rhythm_clock import MelodiaRhythmClock
from gmm.game.config import GAME_CFG


class TestBPM(unittest.TestCase):
    def setUp(self):
        self.clock = MelodiaRhythmClock(bpm=120)

    def test_default_bpm(self):
        self.assertEqual(self.clock.bpm, 120)

    def test_set_bpm(self):
        self.clock.set_bpm(140)
        self.assertEqual(self.clock.bpm, 140)

    def test_beat_interval_at_120(self):
        self.assertAlmostEqual(self.clock.beat_interval_ms, 500.0)

    def test_beat_interval_at_60(self):
        self.clock.set_bpm(60)
        self.assertAlmostEqual(self.clock.beat_interval_ms, 1000.0)

    def test_beat_interval_at_140(self):
        self.clock.set_bpm(140)
        self.assertAlmostEqual(self.clock.beat_interval_ms, 60000.0 / 140)


class TestTimingWindows(unittest.TestCase):
    def setUp(self):
        from gmm.core.settings import GmmSettings
        self.settings = GmmSettings()
        self.backup_data = self.settings.data.copy()
        self.settings.reset_defaults()
        self.clock = MelodiaRhythmClock(bpm=120)

    def tearDown(self):
        self.settings.data = self.backup_data
        self.settings.save()

    def test_perfect_window_default(self):
        self.assertAlmostEqual(self.clock.timing_windows["perfect"], 90.0)

    def test_great_window_default(self):
        self.assertAlmostEqual(self.clock.timing_windows["great"], 120.0)

    def test_good_window_default(self):
        self.assertAlmostEqual(self.clock.timing_windows["good"], 160.0)

    def test_window_override_from_settings(self):
        self.settings.set("perfect_accuracy_window_s", 0.05)
        clock2 = MelodiaRhythmClock(bpm=120)
        self.assertAlmostEqual(clock2.timing_windows["perfect"], 50.0)


class TestHitTesting(unittest.TestCase):
    def setUp(self):
        self.clock = MelodiaRhythmClock(bpm=120)

    def test_perfect_hit(self):
        grade, error = self.clock.hit_test(50.0)
        self.assertEqual(grade, "perfect")
        self.assertAlmostEqual(error, 50.0)

    def test_great_hit(self):
        grade, error = self.clock.hit_test(100.0)
        self.assertEqual(grade, "great")

    def test_good_hit(self):
        grade, error = self.clock.hit_test(140.0)
        self.assertEqual(grade, "good")

    def test_miss(self):
        grade, error = self.clock.hit_test(300.0)
        self.assertEqual(grade, "miss")

    def test_negative_input_is_perfect(self):
        grade, error = self.clock.hit_test(-5.0)
        self.assertEqual(grade, "perfect")

    def test_zero_input_is_perfect(self):
        grade, error = self.clock.hit_test(0.0)
        self.assertEqual(grade, "perfect")


class TestGradeMultipliers(unittest.TestCase):
    def setUp(self):
        self.clock = MelodiaRhythmClock(bpm=120)

    def test_perfect_multiplier(self):
        self.assertAlmostEqual(self.clock.grade_multiplier("perfect"), GAME_CFG.grade_multipliers.perfect)

    def test_great_multiplier(self):
        self.assertAlmostEqual(self.clock.grade_multiplier("great"), GAME_CFG.grade_multipliers.great)

    def test_good_multiplier(self):
        self.assertAlmostEqual(self.clock.grade_multiplier("good"), GAME_CFG.grade_multipliers.good)

    def test_miss_multiplier(self):
        self.assertAlmostEqual(self.clock.grade_multiplier("miss"), GAME_CFG.grade_multipliers.miss)

    def test_unknown_grade_multiplier(self):
        self.assertAlmostEqual(self.clock.grade_multiplier("unknown"), 0.0)


class TestElapsedTime(unittest.TestCase):
    def setUp(self):
        self.clock = MelodiaRhythmClock(bpm=120)

    def test_elapsed_ms_starts_zero(self):
        self.assertAlmostEqual(self.clock.elapsed_ms, 0.0)

    def test_elapsed_increases_after_start(self):
        self.clock.start()
        time.sleep(0.05)
        self.assertGreater(self.clock.elapsed_ms, 30)

    def test_elapsed_stops_after_stop(self):
        self.clock.start()
        time.sleep(0.02)
        self.clock.stop()
        frozen = self.clock.elapsed_ms
        time.sleep(0.02)
        self.assertAlmostEqual(self.clock.elapsed_ms, frozen)

    def test_reset_sets_elapsed_to_zero(self):
        self.clock.start()
        time.sleep(0.02)
        self.clock.reset()
        self.assertAlmostEqual(self.clock.elapsed_ms, 0.0)


class TestBeatTracking(unittest.TestCase):
    def setUp(self):
        self.clock = MelodiaRhythmClock(bpm=120)

    def test_current_beat_starts_zero(self):
        self.assertEqual(self.clock.current_beat, 0)

    def test_beats_accumulate(self):
        self.clock.start()
        time.sleep(0.55)
        self.assertGreaterEqual(self.clock.current_beat, 1)


class TestTick(unittest.TestCase):
    def setUp(self):
        self.calls = []
        self.clock = MelodiaRhythmClock(bpm=120, beat_callback=lambda b: self.calls.append(b))

    def test_first_tick_returns_beat_zero(self):
        self.clock.start()
        result = self.clock.tick()
        self.assertEqual(result, 0)

    def test_tick_returns_none_on_subsequent_same_beat(self):
        self.clock.start()
        self.clock.tick()
        result = self.clock.tick()
        self.assertIsNone(result)

    def test_tick_detects_beat_change(self):
        self.clock.start()
        time.sleep(0.55)
        result = self.clock.tick()
        self.assertIsNotNone(result)

    def test_beat_callback_fires(self):
        self.clock.start()
        time.sleep(0.55)
        self.clock.tick()
        self.assertGreater(len(self.calls), 0)


class TestLaneMapping(unittest.TestCase):
    def setUp(self):
        self.clock = MelodiaRhythmClock(bpm=120)

    def test_lane_from_element(self):
        lane = self.clock.lane_from_element("Forte")
        self.assertEqual(lane, 0)

    def test_lane_from_element_known(self):
        mapping = {"Forte": 0, "Radiant": 0, "Tide": 1, "Gale": 1,
                   "Umbral": 2, "Arcane": 2, "Stone": 3}
        for elem, expected in mapping.items():
            self.assertEqual(self.clock.lane_from_element(elem), expected)

    def test_lane_from_element_unknown_returns_zero(self):
        lane = self.clock.lane_from_element("Unknown")
        self.assertEqual(lane, 0)


class TestNoteSchedule(unittest.TestCase):
    def setUp(self):
        self.clock = MelodiaRhythmClock(bpm=120)

    def test_note_schedule_empty(self):
        notes = self.clock.note_schedule([])
        self.assertEqual(len(notes), 0)

    def test_note_schedule_single(self):
        notes = self.clock.note_schedule([0.0])
        self.assertEqual(len(notes), 1)
        self.assertAlmostEqual(notes[0]["time_ms"], 0.0)

    def test_note_schedule_multiple(self):
        notes = self.clock.note_schedule([0.0, 0.5, 1.0, 2.0])
        self.assertEqual(len(notes), 4)
        self.assertAlmostEqual(notes[1]["time_ms"], 250.0)
        self.assertAlmostEqual(notes[2]["time_ms"], 500.0)


class TestUtility(unittest.TestCase):
    def setUp(self):
        self.clock = MelodiaRhythmClock(bpm=120)

    def test_describe(self):
        d = self.clock.describe()
        self.assertIn("bpm", d)
        self.assertEqual(d["bpm"], 120)

    def test_time_until_next_beat(self):
        self.assertAlmostEqual(self.clock.time_until_next_beat(), 500.0)

    def test_time_since_last_beat(self):
        self.assertAlmostEqual(self.clock.time_since_last_beat(), 0.0)

    def test_beat_progress(self):
        self.assertAlmostEqual(self.clock.beat_progress, 0.0)

    def test_current_measure(self):
        self.assertEqual(self.clock.current_measure, 0)

    def test_grade_color(self):
        color = self.clock.grade_color("perfect")
        self.assertEqual(len(color), 4)

    def test_pause_resume(self):
        self.clock.start()
        time.sleep(0.05)
        self.clock.pause()
        frozen = self.clock.elapsed_ms
        time.sleep(0.05)
        self.clock.resume()
        time.sleep(0.05)
        self.clock.stop()
        self.assertGreater(self.clock.elapsed_ms, frozen)


if __name__ == "__main__":
    unittest.main()
