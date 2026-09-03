"""Audio Engine — simple beep-based rhythm feedback for the CLI battle game.

Uses winsound.Beep() on Windows (stdlib, no dependencies).
Provides beat ticks, grade feedback, and a metronome thread.

Usage:
    ae = AudioEngine()
    ae.start_metronome(120)
    ae.play_grade("perfect")
    ae.beep(440, 100)
    ae.stop()
"""
from __future__ import annotations

import atexit
import threading
import time
from typing import Optional


# Frequency (Hz) and duration (ms) presets for different events
GRADE_SOUNDS = {
    "perfect": (880, 150),
    "great": (660, 120),
    "good": (440, 100),
    "miss": (220, 200),
}

BEAT_TICK_FREQ = 600
BEAT_TICK_DURATION = 30
MEASURE_ACCENT_FREQ = 800
MEASURE_ACCENT_DURATION = 50


class AudioEngine:
    """Lightweight audio engine using winsound.Beep().

    Can run a background metronome thread for beat ticks.
    Thread-safe start/stop.
    """

    def __init__(self, enabled: bool = True):
        self.enabled = enabled
        self._metronome_thread: Optional[threading.Thread] = None
        self._stop_event = threading.Event()
        self._bpm: float = 120.0
        self._running = False
        self._module = None
        self._try_load()
        atexit.register(self.stop)

    def _try_load(self):
        try:
            import winsound
            self._module = winsound
        except ImportError:
            self.enabled = False

    def beep(self, frequency: int, duration: int):
        """Play a single beep."""
        if not self.enabled or not self._module:
            return
        try:
            self._module.Beep(frequency, duration)
        except Exception:
            pass

    def play_grade(self, grade: str):
        """Play the sound associated with a timing grade."""
        freq, dur = GRADE_SOUNDS.get(grade, (440, 100))
        self.beep(freq, dur)

    def play_beat_tick(self, beat: int):
        """Play a metronome tick (accented on beat 0)."""
        if beat % 4 == 0:
            self.beep(MEASURE_ACCENT_FREQ, MEASURE_ACCENT_DURATION)
        else:
            self.beep(BEAT_TICK_FREQ, BEAT_TICK_DURATION)

    def play_victory(self):
        """Ascending victory chime."""
        for freq in (523, 659, 784, 1047):
            self.beep(freq, 150)
            time.sleep(0.08)

    def play_defeat(self):
        """Descending defeat tone."""
        for freq in (400, 350, 300, 200):
            self.beep(freq, 200)
            time.sleep(0.1)

    def play_flee(self):
        self.beep(300, 100)
        time.sleep(0.05)
        self.beep(500, 100)

    # -- Metronome --

    def start_metronome(self, bpm: float):
        """Start background metronome thread at given BPM."""
        self.stop()
        self._bpm = bpm
        self._stop_event.clear()
        self._running = True
        self._metronome_thread = threading.Thread(target=self._metronome_loop, daemon=True)
        self._metronome_thread.start()

    def stop_metronome(self):
        """Stop the metronome thread."""
        self._stop_event.set()
        if self._metronome_thread:
            self._metronome_thread.join(timeout=1.0)
            self._metronome_thread = None
        self._running = False

    def stop(self):
        """Shut down all audio."""
        self.stop_metronome()

    def _metronome_loop(self):
        beat = 0
        interval = 60.0 / self._bpm
        while not self._stop_event.is_set():
            if not self.enabled:
                time.sleep(0.1)
                continue
            self.play_beat_tick(beat)
            beat += 1
            self._stop_event.wait(interval)

    def toggle(self) -> bool:
        """Toggle audio on/off. Returns new state."""
        self.enabled = not self.enabled
        if not self.enabled:
            self.stop_metronome()
        return self.enabled

    def describe(self) -> dict:
        return {
            "enabled": self.enabled,
            "available": self._module is not None,
            "bpm": self._bpm,
            "metronome_running": self._running,
        }
