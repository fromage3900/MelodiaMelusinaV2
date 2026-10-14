"""MIDI discovery cache + picker helpers for Melodia Studio.

Split out of studio_panel.py on 2026-10-04 (monolith split, no logic change).
Holds the 4s discovery cache, the "which MIDI does the user actually mean"
resolver, and the one-line preview. Used by properties, operators, panel
and (via studio_panel facade) tandem_bridge.
"""

import os
import time

try:
    import bpy  # type: ignore
except Exception:
    bpy = None  # type: ignore

from . import midi_bridge

# ------------------------------------------------------------- caching

_MIDI_CACHE: list[str] = []
_MIDI_CACHE_TIME: float = 0.0
_MIDI_CACHE_TTL = 4.0  # seconds - avoids scanning on every draw, still live


def _discover_cached() -> list[str]:
    global _MIDI_CACHE, _MIDI_CACHE_TIME
    now = time.time()
    if _MIDI_CACHE and (now - _MIDI_CACHE_TIME) < _MIDI_CACHE_TTL:
        return _MIDI_CACHE
    # honour AddonPreferences midi_extra_dirs (semicolon-separated)
    extra = None
    if bpy is not None:
        try:
            prefs = bpy.context.preferences.addons.get("melodia_studio")
            if prefs and hasattr(prefs, "preferences"):
                raw = getattr(prefs.preferences, "midi_extra_dirs", "") or ""
                if raw.strip():
                    extra = [p.strip() for p in raw.split(";") if p.strip()]
        except Exception:
            extra = None
    found = midi_bridge.discover_midi(extra_dirs=extra)
    _MIDI_CACHE = found
    _MIDI_CACHE_TIME = now
    return found


def _selected_midi(props):
    if props.custom_midi:
        try:
            path = bpy.path.abspath(props.custom_midi)
        except Exception:
            path = props.custom_midi
        if os.path.exists(path):
            return path
    # Enum may be "" when filtered to no match
    val = getattr(props, "midi_file", "") or ""
    if val and os.path.exists(val):
        return val
    # Fallback: first discovered file so the button still works with a filter
    disc = _discover_cached()
    if disc:
        return disc[0]
    return None


def _midi_preview_lines(midi_path: str) -> str:
    """One-line summary: notes, beatgrid, size. Never throws."""
    try:
        mv = midi_bridge.load_voxel_module()
        tracks, tpb = mv.parse_midi(midi_path)
        if not tracks:
            return "No notes parsed"
        n = len(tracks[0])
        bg = midi_bridge.beatgrid_for(midi_path)
        bg_txt = " + beatgrid" if bg else ""
        size = ""
        try:
            kb = os.path.getsize(midi_path) / 1024.0
            size = f" - {kb:.0f} KB"
        except Exception:
            pass
        return f"{n} notes - TPB {tpb}{bg_txt}{size}"
    except Exception as exc:
        return f"Preview unavailable: {exc}"
