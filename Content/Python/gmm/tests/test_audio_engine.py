"""Tests for AudioEngine — beep generation, metronome, grade sounds."""
from __future__ import annotations

import unittest

from gmm.game.audio_engine import AudioEngine, GRADE_SOUNDS, BEAT_TICK_FREQ, MEASURE_ACCENT_FREQ


class TestAudioEngineInit(unittest.TestCase):
    def test_create_with_defaults(self):
        ae = AudioEngine()
        self.assertIsNotNone(ae)
        self.assertIn(ae.enabled, (True, False))

    def test_toggle_changes_state(self):
        ae = AudioEngine()
        initial = ae.enabled
        new_state = ae.toggle()
        self.assertNotEqual(initial, new_state)

    def test_toggle_twice_returns_original(self):
        ae = AudioEngine()
        initial = ae.enabled
        ae.toggle()
        ae.toggle()
        self.assertEqual(ae.enabled, initial)

    def test_describe(self):
        ae = AudioEngine()
        d = ae.describe()
        self.assertIn("enabled", d)
        self.assertIn("available", d)
        self.assertIn("bpm", d)

    def test_stop_does_not_raise(self):
        ae = AudioEngine()
        ae.stop()
        ae.stop()


class TestGradeSounds(unittest.TestCase):
    def test_all_grades_have_sound(self):
        for grade in ("perfect", "great", "good", "miss"):
            self.assertIn(grade, GRADE_SOUNDS)
            freq, dur = GRADE_SOUNDS[grade]
            self.assertGreater(freq, 0)
            self.assertGreater(dur, 0)

    def test_perfect_highest_pitch(self):
        perfect_freq = GRADE_SOUNDS["perfect"][0]
        miss_freq = GRADE_SOUNDS["miss"][0]
        self.assertGreater(perfect_freq, miss_freq)


class TestMetronome(unittest.TestCase):
    def test_start_stop(self):
        ae = AudioEngine(enabled=False)
        ae.start_metronome(120)
        self.assertTrue(ae._running)
        ae.stop_metronome()
        self.assertFalse(ae._running)

    def test_restart_stops_previous(self):
        ae = AudioEngine(enabled=False)
        ae.start_metronome(120)
        t1 = ae._metronome_thread
        ae.start_metronome(140)
        self.assertNotEqual(ae._metronome_thread, t1)
        ae.stop()


class TestBeepNoError(unittest.TestCase):
    def test_beep_without_winsound(self):
        ae = AudioEngine(enabled=True)
        ae._module = None
        ae.beep(440, 100)
        ae.play_grade("perfect")
        ae.play_victory()
        ae.play_defeat()
        ae.play_flee()
        ae.play_beat_tick(0)


if __name__ == "__main__":
    unittest.main()
