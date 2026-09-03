"""Shared field-building utilities for Melodia Studio.

Deduplicates the MIDI -> heightfield pipeline that was previously
implemented independently in 6 different modules (roll_field, smooth_terrain,
tandem_bridge, studio_panel, midi_bridge, world_streaming).

Pure Python, no bpy. Offline-safe.
"""

from __future__ import annotations

import os
import sys

# Resolve paths so this works whether imported as melodia_studio.core.field
# or run directly. The melodia_studio/ directory is the parent of core/.
_HERE = os.path.dirname(os.path.abspath(__file__))
_STUDIO_ROOT = os.path.dirname(_HERE)

if _STUDIO_ROOT not in sys.path:
    sys.path.insert(0, _STUDIO_ROOT)


def load_voxel_module():
    """Import midi_voxel_v3."""
    import walkable_world
    return walkable_world.load_voxel_module()


def get_preset(preset_id: str, source: str = "walkable") -> dict:
    """Get a preset dict from the named source.

    Args:
        preset_id: Preset identifier (e.g. 'walkable_valley', 'resonant_default')
        source: 'walkable' for WALKABLE_PRESETS, 'midi_bridge' for DEFAULT_PRESETS
    """
    if source == "walkable":
        import walkable_world
        return walkable_world.WALKABLE_PRESETS.get(
            preset_id, walkable_world.WALKABLE_PRESETS["walkable_valley"]
        )
    elif source == "midi_bridge":
        import midi_bridge
        presets = midi_bridge.load_presets()
        return presets.get(preset_id, presets.get("resonant_default"))
    else:
        raise ValueError(f"Unknown preset source: {source}")


def merge_beatgrid(notes: list, midi_path: str, mv, tpb: int) -> list:
    """Merge beatgrid notes into the note list if a beatgrid file exists.

    Beatgrid notes are transposed +36 semitones so they sit above the melody.
    Returns the merged note list (sorted by onset).
    """
    stem, ext = os.path.splitext(midi_path)
    bg_path = stem + "_beatgrid" + ext
    if os.path.exists(bg_path):
        try:
            b_tracks, b_tpb = mv.parse_midi(bg_path)
            if b_tracks and b_tpb:
                scale = float(tpb) / float(b_tpb)
                notes.extend(
                    (int(n[0] * scale), n[1] + 36, n[2]) for n in b_tracks[0]
                )
                notes.sort()
        except Exception:
            pass
    return notes


def build_field(
    midi_path: str,
    preset_id: str = "walkable_valley",
    source: str = "walkable",
) -> dict:
    """Build a walkable heightfield from MIDI.

    Single source of truth for the MIDI -> notes -> heightfield pipeline.
    All 6 previous implementations (roll_field, smooth_terrain, tandem_bridge,
    studio_panel, midi_bridge, world_streaming) are callers of this function.

    Args:
        midi_path: Path to a .mid file
        preset_id: Preset identifier
        source: 'walkable' or 'midi_bridge'

    Returns dict with:
        ok: bool
        field: {(x,y): (height, velocity)} heightfield
        grid_w: grid width
        preset: preset dict used
        metrics: walkability metrics dict
        notes: final note list (including beatgrid if present)
    """
    import walkable_world as ww

    mv = load_voxel_module()
    preset = get_preset(preset_id, source)

    tracks, tpb = mv.parse_midi(midi_path)
    if not tracks:
        return {"ok": False, "reason": "no tracks"}

    notes = list(tracks[0])
    merge_beatgrid(notes, midi_path, mv, tpb)

    field, grid_w = ww.build_heightfield(
        notes,
        cells_per_beat=preset.get("cells_per_beat", 2),
        height_scale=preset.get("height_scale", 1.9),
        plateau_radius=preset.get("plateau_radius", 2),
        tpb=tpb,
        fold=preset.get("fold", "serpentine"),
    )
    field = ww.fill_gaps(field)
    field = ww.limit_slope(
        field, preset.get("max_slope", 1), preset.get("smooth_passes", 3)
    )

    metrics = ww.walkability(field, preset.get("max_slope", 1))
    metrics["largest_region"] = ww.largest_connected_region(
        field, preset.get("max_slope", 1)
    )
    metrics["largest_region_fraction"] = round(
        metrics["largest_region"] / float(max(1, metrics["cells"])), 3
    )

    return {
        "ok": True,
        "field": field,
        "grid_w": grid_w,
        "preset": preset,
        "metrics": metrics,
        "notes": notes,
    }
