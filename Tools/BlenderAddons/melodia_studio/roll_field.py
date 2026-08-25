"""Roll field exporter - MIDI -> walkable note-field JSON for GN/UE consumers.

Single source of truth so Blender GN (music_terrain.py) and UE PCG instance
the SAME walkable piano-roll. Reuses the proven walkable_world chain
(build_heightfield -> fill_gaps -> limit_slope) plus per-cell pitch mapping
from the serpentine fold, so every cell is standable and slope-limited.

Pure Python, no bpy. Deterministic for a given (midi, preset).

Schema: melodia_roll_field_v1
{
  "format": ..., "preset": ..., "grid": {"w": int, "d": int},
  "walkable_fraction": float,
  "cells": [{"x","y","h","velocity","pitch","semitone_mod12"} ...],
  "notes": [{"onset_beat","pitch","velocity","x","y","h"} ...]  # ordered
}
"""

from __future__ import annotations

import json
import os
from pathlib import Path

FORMAT_ID = "melodia_roll_field_v1"


def _addon_dir() -> str:
    return os.path.dirname(os.path.abspath(__file__))


def build_roll_field(midi_path: str, preset_id: str = "walkable_valley") -> dict:
    """MIDI -> walkable roll field dict. Raises on bad input."""
    here = _addon_dir()
    if here not in os.sys.path:
        os.sys.path.insert(0, here)
    import walkable_world as ww  # type: ignore

    mv = ww.load_voxel_module()
    preset = ww.WALKABLE_PRESETS.get(preset_id) or ww.WALKABLE_PRESETS["walkable_valley"]

    tracks, tpb = mv.parse_midi(midi_path)
    if not tracks:
        raise ValueError("no tracks in %s" % midi_path)

    notes = list(tracks[0])
    stem, ext = os.path.splitext(midi_path)
    bg = stem + "_beatgrid" + ext
    used_bg = False
    if os.path.exists(bg):
        try:
            b_tracks, b_tpb = mv.parse_midi(bg)
            if b_tracks and b_tpb:
                s = float(tpb) / float(b_tpb)
                notes.extend((int(n[0] * s), n[1] + 36, n[2]) for n in b_tracks[0])
                notes.sort()
                used_bg = True
        except Exception:
            pass

    # Melody notes carry pitch; beatgrid notes were transposed +36 by the chain.
    # Track per-note pitch so cells know their semitone.
    melody_only, _, _tpb1 = (None, None, None)
    field, grid_w = ww.build_heightfield(
        notes, preset["cells_per_beat"], preset["height_scale"],
        preset["plateau_radius"], tpb, preset.get("fold", "serpentine"),
    )
    field = ww.fill_gaps(field)
    field = ww.limit_slope(field, preset["max_slope"], preset["smooth_passes"])
    metrics = ww.walkability(field, preset["max_slope"])

    # Map each cell back to a representative pitch: nearest melody onset cell.
    # The serpentine fold maps onset index -> (cx, cy); recompute that map.
    max_tick = max((n[0] for n in notes), default=0)
    total_cells = max(1, int((max_tick / float(tpb)) * preset["cells_per_beat"]) + 1)
    gw = max(4, int(round(math_sqrt(total_cells))))
    pitch_at_cell: dict[tuple[int, int], int] = {}
    vel_at_cell: dict[tuple[int, int], int] = {}
    for n in notes:
        onset, pitch, vel = n[0], n[1], n[2]
        cell = int((onset / float(tpb)) * preset["cells_per_beat"])
        cx, cy = ww.fold_xy(cell, gw, preset.get("fold", "serpentine"))
        key = (cx, cy)
        # keep the highest-velocity claim; ties keep first (sorted order stable)
        if key not in vel_at_cell or vel > vel_at_cell[key]:
            vel_at_cell[key] = vel
            pitch_at_cell[key] = pitch

    cells_out = []
    for (x, y), (h, v) in sorted(field.items()):
        pitch = pitch_at_cell.get((x, y), 60)
        vel = vel_at_cell.get((x, y), v)
        cells_out.append({
            "x": int(x), "y": int(y), "h": int(h),
            "velocity": int(vel),
            "pitch": int(pitch),
            "semitone_mod12": int(pitch % 12),
            "is_accidental": 1 if (pitch % 12) in (1, 3, 6, 8, 10) else 0,
        })

    return {
        "format": FORMAT_ID,
        "midi": os.path.basename(midi_path),
        "preset": preset_id,
        "used_beatgrid": used_bg,
        "grid": {"w": int(grid_w), "d": int(max((k[1] for k in field), default=0) + 1)},
        "walkable_fraction": metrics.get("walkable_fraction", 0.0),
        "aspect_ratio": metrics.get("aspect_ratio", 1.0),
        "cell_count": len(cells_out),
        "cells": cells_out,
    }


def math_sqrt(v: float) -> float:
    return float(v) ** 0.5


def write_roll_field(midi_path: str, out_json: str | Path,
                     preset_id: str = "walkable_valley") -> Path:
    data = build_roll_field(midi_path, preset_id)
    p = Path(out_json)
    p.parent.mkdir(parents=True, exist_ok=True)
    p.write_text(json.dumps(data, indent=1), encoding="utf-8")
    return p


if __name__ == "__main__":
    import sys
    root = Path(_addon_dir()).parents[2]
    midi = root / "Content" / "MelodiaIntegration" / "MIDI" / "128BPMarpeggiomelody.mid"
    if len(sys.argv) > 1:
        midi = Path(sys.argv[1])
    out = root / "Saved" / "Audit" / f"roll_field_{Path(midi).stem}.json"
    p = write_roll_field(str(midi), str(out))
    d = json.loads(Path(p).read_text(encoding="utf-8"))
    print("cells=%d grid=%s walk=%.2f -> %s" % (
        d["cell_count"], d["grid"], d["walkable_fraction"], p))
