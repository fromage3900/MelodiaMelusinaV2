"""battle_osc.py — OSC bridge from GMM battle engine to TouchDesigner.

Lightweight UDP OSC sender that fires game events to TD on port 9000.
No Unreal dependency — uses raw sockets, same protocol as td_bridge.py.

Each battle event maps to a TD visual response:
  - perfect → sparkle burst + gold flash
  - enemy_broken → wish burst + screen shake
  - combo 10+ → increasing particle density
  - victory → finale VFX
"""

import socket
import struct
import json
from datetime import datetime

TD_OSC_HOST = "127.0.0.1"
TD_OSC_PORT = 9000
ENABLED = True  # Toggle to disable OSC during testing


def _pad(data: bytes) -> bytes:
    """Pad to 4-byte boundary."""
    r = len(data) % 4
    return data if r == 0 else data + b"\x00" * (4 - r)


def _osc_msg(address: str, *values) -> bytes:
    """Build raw OSC message."""
    addr = _pad(address.encode("utf-8"))
    types = b","
    payload = b""
    for v in values:
        if isinstance(v, float):
            types += b"f"
            payload += struct.pack(">f", v)
        elif isinstance(v, int):
            types += b"i"
            payload += struct.pack(">i", v)
        elif isinstance(v, str):
            types += b"s"
            s = v.encode("utf-8")
            payload += _pad(s)
        elif isinstance(v, bool):
            types += b"i" if v else b"f"
            payload += struct.pack(">i", 1 if v else 0)
    return addr + _pad(types) + payload


def _send(address: str, *values):
    """Send one OSC message to TD. No-op if disabled."""
    if not ENABLED:
        return
    try:
        msg = _osc_msg(address, *values)
        with socket.socket(socket.AF_INET, socket.SOCK_DGRAM) as s:
            s.sendto(msg, (TD_OSC_HOST, TD_OSC_PORT))
    except Exception:
        pass  # TD not running — silently skip


# ── Public API — called from battle_manager ──────────────────────────

def on_encounter_start(enemy_id: str, bpm: float, element: str):
    """Fired when a battle encounter begins."""
    _send("/battle/encounter", f"{enemy_id}|{bpm}|{element}")
    _send("/rhythm/bpm", bpm)


def on_beat(beat_number: int, beat_progress: float, measure: int):
    """Fired on each beat from MelodiaRhythmClock."""
    _send("/rhythm/beat", beat_number)
    _send("/rhythm/beat_progress", beat_progress)
    _send("/rhythm/measure", measure)


def on_beat_pulse(beat_pulse: float, beat_phase: float):
    """Fired continuously from MelodiaRhythmReactivitySubsystem::Publish().
    
    beat_pulse: 0-1 envelope peaking at each beat (sawtooth/smooth).
    beat_phase: 0-1 phase within current beat.
    """
    _send("/rhythm/beat_pulse", beat_pulse)
    _send("/rhythm/beat_phase", beat_phase)


def on_hit_result(grade: str, error_ms: float, combo: int,
                  damage_dealt: float, enemy_hp: float,
                  enemy_broken: bool, ult_gauge: float):
    """Fired after resolve_rhythm — the richest event for TD VFX."""
    _send("/battle/grade", grade)
    _send("/battle/combo", combo)
    _send("/battle/damage", damage_dealt, enemy_hp)
    _send("/battle/ult_gauge", ult_gauge)
    if enemy_broken:
        _send("/battle/enemy_broken", 1)
        _send("/niagara/burst", 1)  # Wish burst on break


def on_phase_change(phase: str):
    """Fired on any phase transition."""
    _send("/battle/phase", phase)


def on_battle_end(result: str):
    """Fired when battle ends."""
    _send("/battle/result", result)
    if result == "victory":
        _send("/niagara/burst", 1)  # Victory finale VFX


def on_audio_bands(bass: float, mid: float, treble: float):
    """CHOP-equivalent sender for headless/CI validation (no TD running).

    In production these three are sent by TD's /project1/melodia_audio/osc_out
    CHOP chain (spectrum → 3 bands → math → lag → OSC). This helper lets
    Python drive the same addresses for loopback tests and for UE PIE without TD.
    """
    _send("/melodia/audio/bass", float(bass))
    _send("/melodia/audio/mid", float(mid))
    _send("/melodia/audio/treble", float(treble))


def on_audio_beat_alias(beat_pulse: float, beat_phase: float):
    """Alias sender for /melodia/audio/beat/* (mirrors on_beat_pulse).

    TD's sel_beat_pulse / sel_beat_phase listen on both namespaces.
    Kept separate so callers can use the sprint-documented /melodia/audio/beat/* prefix.
    """
    _send("/melodia/audio/beat/pulse", float(beat_pulse))
    _send("/melodia/audio/beat/phase", float(beat_phase))


def status():
    """Return bridge status for external inspection."""
    return {
        "enabled": ENABLED,
        "target": f"{TD_OSC_HOST}:{TD_OSC_PORT}",
        "timestamp": datetime.now().isoformat(),
        "audio_reactive_routes": [
            "/melodia/audio/bass",
            "/melodia/audio/mid",
            "/melodia/audio/treble",
            "/melodia/audio/beat/pulse",
            "/melodia/audio/beat/phase",
        ],
        "rhythm_routes": [
            "/rhythm/beat_pulse",
            "/rhythm/beat_phase",
        ],
    }
