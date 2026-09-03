"""Roll field exporter - MIDI -> walkable note-field JSON for GN/UE consumers.

Single source of truth so Blender GN (music_terrain.py) and UE PCG instance
the SAME walkable piano-roll. Delegates the heightfield build to
core.field.build_field() so every cell is standable and slope-limited.

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
import math
import os
from pathlib import Path

FORMAT_ID = "melodia_roll_field_v1"


def build_roll_field(midi_path: str, preset_id: str = "walkable_valley") -> dict:
    """MIDI -> walkable roll field dict. Raises on bad input."""
    from .core.field import build_field, load_voxel_module
    from . import walkable_world as ww

    result = build_field(midi_path, preset_id, source="walkable")
    if not result["ok"]:
        raise ValueError(result.get("reason", "build_field failed"))

    field = result["field"]
    grid_w = result["grid_w"]
    metrics = result["metrics"]
    notes = result["notes"]
    preset = result["preset"]

    # Check if beatgrid was actually used (build_field doesn't expose this)
    stem, ext = os.path.splitext(midi_path)
    used_bg = os.path.exists(stem + "_beatgrid" + ext)

    # We need tpb for pitch mapping; re-parse to get it
    mv = load_voxel_module()
    tracks, tpb = mv.parse_midi(midi_path)

    # Map each cell back to a representative pitch: nearest melody onset cell.
    # The serpentine fold maps onset index -> (cx, cy); recompute that map.
    max_tick = max((n[0] for n in notes), default=0)
    total_cells = max(1, int((max_tick / float(tpb)) * preset.get("cells_per_beat", 2)) + 1)
    gw = max(4, int(round(math.sqrt(total_cells))))
    pitch_at_cell: dict[tuple[int, int], int] = {}
    vel_at_cell: dict[tuple[int, int], int] = {}
    for n in notes:
        onset, pitch, vel = n[0], n[1], n[2]
        cell = int((onset / float(tpb)) * preset.get("cells_per_beat", 2))
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


def write_roll_field(midi_path: str, out_json: str | Path,
                     preset_id: str = "walkable_valley") -> Path:
    data = build_roll_field(midi_path, preset_id)
    p = Path(out_json)
    p.parent.mkdir(parents=True, exist_ok=True)
    p.write_text(json.dumps(data, indent=1), encoding="utf-8")
    return p


if __name__ == "__main__":
    import sys
    root = Path(__file__).resolve().parents[3]
    midi = root / "Content" / "MelodiaIntegration" / "MIDI" / "128BPMarpeggiomelody.mid"
    if len(sys.argv) > 1:
        midi = Path(sys.argv[1])
    out = root / "Saved" / "Audit" / f"roll_field_{Path(midi).stem}.json"
    p = write_roll_field(str(midi), str(out))
    d = json.loads(Path(p).read_text(encoding="utf-8"))
    print("cells=%d grid=%s walk=%.2f -> %s" % (
        d["cell_count"], d["grid"], d["walkable_fraction"], p))
