"""FL state snapshot builder for the Jev FL conductor bridge.

Reads ONLY through the external bridge's MIDI/SysEx connection (the
fl-studio-mcp FLBridge.call interface): transport, tempo, song position,
master + whitelisted stem peaks, mixer mute states. No audio
transcription, no frame sampling — one snapshot per phrase boundary.

Bar math assumes 4/4 (beats // 4 + 1). If the test cue uses another
meter, set time_signature_beats in the cue config and the math follows it.

Everything unknown stays None; the conductor drops Nones so missing data
reads as missing, never as zero.
"""

from __future__ import annotations

from collections import deque
from typing import Any, Protocol


class BridgeLike(Protocol):
    def call(self, command: str, params: dict | None = None) -> Any: ...


def _safe(bridge: BridgeLike, command: str, params: dict | None = None) -> Any:
    try:
        return bridge.call(command, params or {})
    except Exception:
        return None


def read_transport(bridge: BridgeLike) -> dict[str, Any]:
    pos = _safe(bridge, "get_song_position") or {}
    play = _safe(bridge, "get_play_state") or {}
    tempo = _safe(bridge, "get_tempo") or {}
    beats = pos.get("position_beats")
    return {
        "playing": bool(play.get("playing", False)),
        "recording": bool(play.get("recording", False)),
        "tempo_bpm": tempo.get("bpm"),
        "position_beats": beats,
        "position_ticks": pos.get("position_ticks"),
        "position_ms": pos.get("position_ms"),
    }


def bar_of(beats: float | None, beats_per_bar: int = 4) -> tuple[int, float | None]:
    """(1-based bar, beat-in-bar). Unknown position -> (1, None)."""
    if beats is None or beats < 0:
        return 1, None
    return int(beats // beats_per_bar) + 1, round(beats % beats_per_bar, 3)


def read_peaks(
    bridge: BridgeLike, master_track: int, stem_tracks: dict[str, list[int]]
) -> tuple[float | None, dict[str, float | None]]:
    """Master peak + per-group peak (max over the group's tracks)."""

    def peak(track: int) -> float | None:
        data = _safe(bridge, "mixer_get_peaks", {"track": track})
        if not data:
            return None
        v = data.get("peak_max")
        return float(v) if v is not None else None

    master = peak(master_track)
    groups: dict[str, float | None] = {}
    for group, tracks in stem_tracks.items():
        vals = [peak(t) for t in tracks]
        vals = [v for v in vals if v is not None]
        groups[group] = max(vals) if vals else None
    return master, groups


def read_group_active(
    bridge: BridgeLike, stem_tracks: dict[str, list[int]]
) -> dict[str, bool]:
    """Per-group active flag: a group reads active when any of its tracks
    is unmuted. Track mute state comes from mixer_get_track (single-item
    get keeps full names; paged lists truncate)."""
    active: dict[str, bool] = {}
    for group, tracks in stem_tracks.items():
        audible = False
        for t in tracks:
            data = _safe(bridge, "mixer_get_track", {"index": t})
            if data and not data.get("mute", False):
                audible = True
                break
        active[group] = audible
    return active


class EnergyTracker:
    """EMA smoothing + trend over recent master peaks."""

    def __init__(self, alpha: float = 0.35, window: int = 8) -> None:
        self.alpha = alpha
        self.recent: deque[float] = deque(maxlen=window)
        self._ema: float | None = None

    def update(self, peak: float | None) -> tuple[float | None, str]:
        if peak is None:
            level = self._ema
        else:
            level = peak if self._ema is None else self.alpha * peak + (1 - self.alpha) * self._ema
            self._ema = level
            self.recent.append(level)
        if len(self.recent) < 3 or level is None:
            return (round(level, 3) if level is not None else None, "unknown")
        head = sum(list(self.recent)[-3:]) / 3
        tail = sum(list(self.recent)[:3]) / 3
        span = max(head, tail, 1e-6)
        delta = (head - tail) / span
        if delta > 0.15:
            trend = "rising"
        elif delta < -0.15:
            trend = "falling"
        else:
            trend = "steady"
        return round(level, 3), trend
