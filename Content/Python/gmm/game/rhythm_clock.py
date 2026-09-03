"""Rhythm Clock — BPM-driven beat clock with timing windows and note resolution.

Pure-Python implementation that mirrors the planned C++ Quartz beat driver.
Works standalone (no audio, no UE editor) for testing rhythm mechanics.

Timing windows (configurable, in milliseconds):
    perfect: ≤90ms from beat
    great:  ≤120ms
    good:   ≤160ms
    miss:   >160ms or no input

Usage:
    clock = MelodiaRhythmClock(bpm=128)
    clock.start()
    # ... wait some time ...
    result = clock.hit_test()  # returns grade
    elapsed = clock.elapsed_ms
    beat = clock.current_beat
"""
from __future__ import annotations

import math
import time
from typing import Callable, Optional

from gmm.game.config import GAME_CFG


# ---------------------------------------------------------------------------
# Default timing windows (ms) — matches Figma game-ui.js
# ---------------------------------------------------------------------------
DEFAULT_WINDOWS: dict[str, float] = {
    "perfect": GAME_CFG.timing_windows.perfect,
    "great": GAME_CFG.timing_windows.great,
    "good": GAME_CFG.timing_windows.good,
}

DEFAULT_GRADE_ORDER = ("perfect", "great", "good", "miss")

GRADE_MULTIPLIERS = {
    "perfect": GAME_CFG.grade_multipliers.perfect,
    "great": GAME_CFG.grade_multipliers.great,
    "good": GAME_CFG.grade_multipliers.good,
    "miss": GAME_CFG.grade_multipliers.miss,
}

GRADE_COLORS = {
    "perfect": (1.0, 0.902, 0.4, 1.0),
    "great": (0.4, 0.851, 1.0, 1.0),
    "good": (0.941, 0.863, 0.941, 1.0),
    "miss": (1.0, 0.431, 0.698, 1.0),
}


class MelodiaRhythmClock:
    """BPM-driven beat clock with configurable timing windows.

    Tracks elapsed time, current beat, and provides hit-testing
    against the nearest beat boundary.

    Can optionally accept a beat callback for synchronized events.
    """

    def __init__(self, bpm: float = 120.0,
                 timing_windows: Optional[dict[str, float]] = None,
                 beat_callback: Optional[Callable[[int], None]] = None):
        self.bpm = bpm
        self.beat_interval_ms: float = 60000.0 / bpm
        
        if timing_windows is None:
            try:
                from gmm.core.settings import GmmSettings
                settings = GmmSettings()
                self.timing_windows = {
                    "perfect": settings.get("perfect_accuracy_window_s") * 1000.0,
                    "great": settings.get("great_accuracy_window_s") * 1000.0,
                    "good": settings.get("good_accuracy_window_s") * 1000.0,
                }
            except Exception:
                self.timing_windows = dict(DEFAULT_WINDOWS)
        else:
            self.timing_windows = timing_windows
            
        self.beat_callback: Optional[Callable[[int], None]] = beat_callback

        self._start_time: Optional[float] = None
        self._paused_time: float = 0.0
        self._pause_start: Optional[float] = None
        self._running: bool = False
        self._last_beat: int = -1
        self._total_elapsed: float = 0.0

    # -- Lifecycle --

    @property
    def running(self) -> bool:
        return self._running

    @property
    def elapsed_ms(self) -> float:
        """Milliseconds since clock start (excluding pauses)."""
        if not self._running:
            return self._total_elapsed
        now = time.perf_counter()
        raw = (now - self._start_time) * 1000.0
        if self._pause_start is not None:
            raw -= (now - self._pause_start) * 1000.0
        return raw

    @property
    def current_beat(self) -> int:
        """Current integer beat (0-based)."""
        return int(self.elapsed_ms / self.beat_interval_ms)

    @property
    def beat_progress(self) -> float:
        """Progress within the current beat (0.0–1.0)."""
        t = self.elapsed_ms % self.beat_interval_ms
        return t / self.beat_interval_ms

    @property
    def beats_per_measure(self) -> int:
        return 4

    @property
    def current_measure(self) -> int:
        return self.current_beat // self.beats_per_measure

    def start(self):
        """Start or resume the clock."""
        if self._running:
            return
        self._start_time = time.perf_counter()
        self._pause_start = None
        self._running = True

    def stop(self):
        """Stop the clock and record elapsed time."""
        if not self._running:
            return
        self._total_elapsed = self.elapsed_ms
        self._running = False
        self._pause_start = None

    def reset(self):
        """Reset clock to zero."""
        self._running = False
        self._start_time = None
        self._pause_start = None
        self._total_elapsed = 0.0
        self._last_beat = -1

    def pause(self):
        """Pause the clock."""
        if not self._running or self._pause_start is not None:
            return
        self._pause_start = time.perf_counter()

    def resume(self):
        """Resume from pause."""
        if self._pause_start is None:
            return
        pause_duration = (time.perf_counter() - self._pause_start) * 1000.0
        self._start_time += pause_duration / 1000.0
        self._pause_start = None

    # -- Beat tracking --

    def tick(self) -> Optional[int]:
        """Advance the clock and return the new beat if crossed.

        Call this in your game loop. Returns the beat number if a
        new beat was crossed, or None if still within the same beat.
        Also fires beat_callback if set.
        """
        if not self._running:
            return None
        beat = self.current_beat
        if beat != self._last_beat:
            self._last_beat = beat
            if self.beat_callback:
                self.beat_callback(beat)
            return beat
        return None

    # -- Hit testing --

    def hit_test(self, input_time_ms: Optional[float] = None) -> tuple[str, float]:
        """Test a player input against the nearest beat.

        Args:
            input_time_ms: Player input timestamp (ms since clock start).
                           If None, uses current clock time.

        Returns:
            (grade, error_ms) where grade is "perfect", "great", "good", or "miss".
            error_ms is the absolute distance from the nearest beat (negative = early).
        """
        t = input_time_ms if input_time_ms is not None else self.elapsed_ms

        nearest_beat = round(t / self.beat_interval_ms)
        beat_time = nearest_beat * self.beat_interval_ms
        error_ms = t - beat_time
        abs_error = abs(error_ms)

        for grade, window_ms in sorted(self.timing_windows.items(),
                                       key=lambda x: x[1]):
            if abs_error <= window_ms:
                return grade, error_ms

        return "miss", error_ms

    def time_until_next_beat(self) -> float:
        """Milliseconds until the next beat."""
        return self.beat_interval_ms - (self.elapsed_ms % self.beat_interval_ms)

    def time_since_last_beat(self) -> float:
        """Milliseconds since the last beat."""
        return self.elapsed_ms % self.beat_interval_ms

    # -- Chart / note helpers --

    def note_schedule(self, beat_offsets: list[float]) -> list[dict]:
        """Convert beat offsets to absolute timestamps.

        Args:
            beat_offsets: List of beat positions (e.g. [0, 0.5, 1, 2])

        Returns:
            List of {"beat": float, "time_ms": float} dicts
        """
        return [
            {"beat": off, "time_ms": off * self.beat_interval_ms}
            for off in beat_offsets
        ]

    def lane_from_element(self, element: str) -> int:
        """Map an element type to a lane index (0-3).

        Matches the 4-lane Figma layout: A=gold, B=cyan, C=magenta, D=pearl.
        """
        element_map = {
            "Forte": 0, "Radiant": 0,
            "Tide": 1, "Gale": 1,
            "Umbral": 2, "Arcane": 2,
            "Stone": 3,
        }
        return element_map.get(element, 0)

    def set_bpm(self, bpm: float):
        """Change BPM mid-performance (resets beat interval)."""
        self.bpm = bpm
        self.beat_interval_ms = 60000.0 / bpm

    # -- Utility --

    def grade_multiplier(self, grade: str) -> float:
        return GRADE_MULTIPLIERS.get(grade, 0.0)

    def grade_color(self, grade: str) -> tuple:
        return GRADE_COLORS.get(grade, (1.0, 1.0, 1.0, 1.0))

    def describe(self) -> dict:
        return {
            "bpm": self.bpm,
            "beat_interval_ms": self.beat_interval_ms,
            "running": self._running,
            "elapsed_ms": round(self.elapsed_ms, 2),
            "current_beat": self.current_beat,
            "beat_progress": round(self.beat_progress, 3),
            "current_measure": self.current_measure,
            "windows": dict(self.timing_windows),
        }
