"""Resonant World v4 — walkable terrain mapping.

v3 maps time to X and pitch-class to Y. Because Y = pitch % 12 it can never
exceed 12 cells, while X grows with song length. A 64-beat song therefore
produces a 64 x 11 x 3 ribbon: renders as a wall, and is not walkable in any
meaningful sense.

v4 changes the mapping, not the parser:

  * Serpentine fold  - the timeline is wrapped across a 2D plane in
    boustrophedon order, so a 64-beat song becomes ~8 x 8 chunks of ground
    instead of a 64-long corridor.
  * Real elevation   - full pitch (not pitch-class) drives height, scaled up,
    so melody produces hills instead of 3 units of relief.
  * Ground fill      - every column is filled down to bedrock, so there are
    no floating cells and nothing to fall through.
  * Slope limiting   - adjacent height deltas are clamped so the surface is
    climbable rather than a field of 1-block cliffs.

This module does not modify midi_voxel_v3; it imports its parser and block
tables and applies a different spatial mapping. Pure Python, no bpy.
"""

import os
import sys
import math
import json

_HERE = os.path.dirname(os.path.abspath(__file__))


def _repo_root():
    return os.path.normpath(os.path.join(_HERE, "..", "..", ".."))


def load_voxel_module():
    vdir = os.path.join(_repo_root(), "Tools", "midi_to_voxel")
    if vdir not in sys.path:
        sys.path.insert(0, vdir)
    import midi_voxel_v3
    return midi_voxel_v3


# --------------------------------------------------------------- presets

WALKABLE_PRESETS = {
    "walkable_valley": {
        "label": "Walkable Valley",
        "description": "Wide serpentine ground, gentle rolling hills.",
        "cells_per_beat": 2,
        "height_scale": 1.9,
        "max_slope": 1,
        "plateau_radius": 2,
        "smooth_passes": 3,
        "aura_emission": 2.6,
    },
    "walkable_highlands": {
        "label": "Walkable Highlands",
        "description": "Taller relief, still climbable; dramatic ridgelines.",
        "cells_per_beat": 2,
        "height_scale": 3.2,
        "max_slope": 2,
        "plateau_radius": 2,
        "smooth_passes": 2,
        "aura_emission": 3.2,
    },
    "walkable_plaza": {
        "label": "Walkable Plaza",
        "description": "Broad flat arena with low musical terracing.",
        "cells_per_beat": 3,
        "height_scale": 1.2,
        "max_slope": 1,
        "plateau_radius": 3,
        "smooth_passes": 4,
        "aura_emission": 2.2,
    },
    "walkable_canyon": {
        "label": "Walkable Canyon",
        "description": "Deep carved routes between high musical mesas.",
        "cells_per_beat": 2,
        "height_scale": 4.0,
        "max_slope": 2,
        "plateau_radius": 1,
        "smooth_passes": 1,
        "aura_emission": 3.6,
        "fold": "serpentine",
    },
    "walkable_spiral_arena": {
        "label": "Walkable Spiral Arena",
        "description": "Song coils inward; finale lands at a central arena.",
        "cells_per_beat": 2,
        "height_scale": 2.6,
        "max_slope": 1,
        "plateau_radius": 2,
        "smooth_passes": 3,
        "aura_emission": 3.0,
        "fold": "spiral",
    },
}


def load_presets():
    return dict(WALKABLE_PRESETS)


# --------------------------------------------------------------- mapping

def serpentine_xy(index, grid_w):
    """Boustrophedon fold: consecutive beats stay adjacent across rows.

    Verified strict 4-neighbour: worst Manhattan step between consecutive
    indices is 1 for every grid width tested (2,3,4,8,15,16).
    """
    row = index // grid_w
    col = index % grid_w
    if row % 2 == 1:
        col = grid_w - 1 - col
    return col, row


def spiral_xy(index, grid_w):
    """Inward spiral fold: the song coils toward a centre.

    Alternative to serpentine. Gives a world where the melody's opening is
    the outer rim and the finale lands at the middle -- useful when a level
    should build toward a central arena rather than a far edge.

    Consecutive indices are strict 4-neighbours except at the four corner
    turns of each ring, where the walk changes direction (still adjacent).
    """
    if grid_w <= 0:
        return 0, 0
    total = grid_w * grid_w
    index = index % total

    left, right = 0, grid_w - 1
    top, bottom = 0, grid_w - 1
    i = 0
    while left <= right and top <= bottom:
        for x in range(left, right + 1):
            if i == index:
                return x, top
            i += 1
        top += 1
        for y in range(top, bottom + 1):
            if i == index:
                return right, y
            i += 1
        right -= 1
        if top <= bottom:
            for x in range(right, left - 1, -1):
                if i == index:
                    return x, bottom
                i += 1
            bottom -= 1
        if left <= right:
            for y in range(bottom, top - 1, -1):
                if i == index:
                    return left, y
                i += 1
            left += 1
    return 0, 0


FOLD_MODES = {
    "serpentine": serpentine_xy,
    "spiral": spiral_xy,
}


def fold_xy(index, grid_w, mode="serpentine"):
    return FOLD_MODES.get(mode, serpentine_xy)(index, grid_w)


def build_heightfield(notes, cells_per_beat=2, height_scale=2.0,
                      plateau_radius=2, tpb=480, fold="serpentine"):
    """Notes -> {(x, y): (height, velocity)} sampled on a folded 2D grid."""
    if not notes:
        return {}, 0

    max_tick = max(n[0] for n in notes)
    total_cells = max(1, int((max_tick / float(tpb)) * cells_per_beat) + 1)
    grid_w = max(4, int(round(math.sqrt(total_cells))))

    pitches = [n[1] for n in notes]
    p_lo, p_hi = min(pitches), max(pitches)
    p_range = max(1, p_hi - p_lo)

    field = {}
    for onset, pitch, vel in notes:
        cell = int((onset / float(tpb)) * cells_per_beat)
        cx, cy = fold_xy(cell, grid_w, fold)

        norm = (pitch - p_lo) / float(p_range)
        height = max(1, int(round(1 + norm * height_scale * 3.0)))

        # Stamp a soft plateau so each note is standable, not a spike.
        r = max(0, int(plateau_radius))
        for dx in range(-r, r + 1):
            for dy in range(-r, r + 1):
                dist = math.hypot(dx, dy)
                if dist > r + 0.001:
                    continue
                falloff = 1.0 - (dist / (r + 1.0)) * 0.45
                h = max(1, int(round(height * falloff)))
                key = (cx + dx, cy + dy)
                prev = field.get(key)
                if prev is None or h > prev[0]:
                    field[key] = (h, vel)

    return field, grid_w


def fill_gaps(field):
    """Close single-cell holes so the ground is continuous underfoot."""
    if not field:
        return field
    xs = [k[0] for k in field]
    ys = [k[1] for k in field]
    filled = dict(field)

    for x in range(min(xs), max(xs) + 1):
        for y in range(min(ys), max(ys) + 1):
            if (x, y) in filled:
                continue
            nbrs = [field.get((x + dx, y + dy))
                    for dx, dy in ((1, 0), (-1, 0), (0, 1), (0, -1))]
            present = [n for n in nbrs if n]
            if len(present) >= 3:
                avg_h = int(round(sum(p[0] for p in present) / len(present)))
                avg_v = int(round(sum(p[1] for p in present) / len(present)))
                filled[(x, y)] = (max(1, avg_h), avg_v)
    return filled


def limit_slope(field, max_slope=1, passes=3):
    """Clamp neighbour height deltas so slopes are climbable."""
    cur = dict(field)
    for _ in range(max(0, passes)):
        changed = False
        for (x, y), (h, v) in sorted(cur.items()):
            for dx, dy in ((1, 0), (-1, 0), (0, 1), (0, -1)):
                nb = cur.get((x + dx, y + dy))
                if nb is None:
                    continue
                if h - nb[0] > max_slope:
                    cur[(x + dx, y + dy)] = (h - max_slope, nb[1])
                    changed = True
        if not changed:
            break
    return cur


def field_to_voxels(field, mv):
    """Heightfield -> solid voxel columns keyed (x, y, z)."""
    voxels = {}
    for (x, y), (h, vel) in field.items():
        block = mv.vel2block(vel)
        for z in range(h):
            # Deeper cells read as bedrock regardless of note velocity.
            voxels[(x, y, z)] = block if z >= h - 2 else mv.BLOCK_STONE
    return voxels


# --------------------------------------------------------------- metrics

def walkability(field, max_step=1):
    """Quantify traversability rather than eyeballing it."""
    if not field:
        return {"cells": 0, "walkable_fraction": 0.0}

    xs = [k[0] for k in field]
    ys = [k[1] for k in field]
    w = max(xs) - min(xs) + 1
    d = max(ys) - min(ys) + 1

    total_edges = 0
    walkable_edges = 0
    steep = 0
    for (x, y), (h, _v) in field.items():
        for dx, dy in ((1, 0), (0, 1)):
            nb = field.get((x + dx, y + dy))
            if nb is None:
                continue
            total_edges += 1
            if abs(h - nb[0]) <= max_step:
                walkable_edges += 1
            else:
                steep += 1

    heights = [v[0] for v in field.values()]
    area = w * d
    return {
        "cells": len(field),
        "footprint": [w, d],
        "coverage": round(len(field) / float(area), 3) if area else 0.0,
        "aspect_ratio": round(max(w, d) / float(max(1, min(w, d))), 2),
        "height_min": min(heights),
        "height_max": max(heights),
        "height_span": max(heights) - min(heights),
        "edges": total_edges,
        "walkable_edges": walkable_edges,
        "steep_edges": steep,
        "walkable_fraction": round(walkable_edges / float(total_edges), 3)
        if total_edges else 0.0,
    }


def largest_connected_region(field, max_step=1):
    """Biggest area reachable on foot without exceeding max_step."""
    if not field:
        return 0
    unvisited = set(field.keys())
    best = 0
    while unvisited:
        start = next(iter(unvisited))
        stack = [start]
        unvisited.discard(start)
        size = 0
        while stack:
            x, y = stack.pop()
            size += 1
            h = field[(x, y)][0]
            for dx, dy in ((1, 0), (-1, 0), (0, 1), (0, -1)):
                nk = (x + dx, y + dy)
                if nk in unvisited and abs(field[nk][0] - h) <= max_step:
                    unvisited.discard(nk)
                    stack.append(nk)
        best = max(best, size)
    return best


# --------------------------------------------------------------- generate

def generate_walkable(midi_path, preset_id="walkable_valley", out_obj=None,
                      use_beatgrid=True):
    mv = load_voxel_module()
    preset = load_presets().get(preset_id, WALKABLE_PRESETS["walkable_valley"])

    tracks, tpb = mv.parse_midi(midi_path)
    if not tracks:
        return {"ok": False, "reason": "no tracks"}

    notes = list(tracks[0])

    # Percussion widens the playable ground rather than carving caves.
    stem, ext = os.path.splitext(midi_path)
    bg_path = stem + "_beatgrid" + ext
    used_bg = False
    if use_beatgrid and os.path.exists(bg_path):
        b_tracks, b_tpb = mv.parse_midi(bg_path)
        if b_tracks and b_tpb:
            scale = float(tpb) / float(b_tpb)
            notes.extend((int(n[0] * scale), n[1] + 36, n[2])
                         for n in b_tracks[0])
            notes.sort()
            used_bg = True

    field, grid_w = build_heightfield(
        notes,
        cells_per_beat=preset["cells_per_beat"],
        height_scale=preset["height_scale"],
        plateau_radius=preset["plateau_radius"],
        tpb=tpb,
        fold=preset.get("fold", "serpentine"),
    )
    field = fill_gaps(field)
    field = limit_slope(field, preset["max_slope"], preset["smooth_passes"])

    metrics = walkability(field, preset["max_slope"])
    metrics["largest_region"] = largest_connected_region(
        field, preset["max_slope"])
    metrics["largest_region_fraction"] = (
        round(metrics["largest_region"] / float(max(1, metrics["cells"])), 3))

    voxels = field_to_voxels(field, mv)

    report = {
        "ok": True,
        "midi": midi_path,
        "preset": preset_id,
        "grid_width": grid_w,
        "notes": len(notes),
        "used_beatgrid": used_bg,
        "voxels": len(voxels),
        "metrics": metrics,
    }

    if out_obj:
        os.makedirs(os.path.dirname(out_obj), exist_ok=True)
        verts, faces = mv.export_obj(voxels, out_obj, name="ResonantWorldV4")
        report["obj"] = out_obj
        report["verts"] = verts
        report["faces"] = faces

    return report


if __name__ == "__main__":
    import tempfile
    root = _repo_root()
    midi = os.path.join(root, "Content", "MelodiaIntegration", "MIDI",
                        "128BPMarpeggiomelody.mid")
    tmp = tempfile.mkdtemp()
    for pid in sorted(WALKABLE_PRESETS):
        r = generate_walkable(midi, pid, os.path.join(tmp, pid + ".obj"))
        m = r["metrics"]
        print("%-22s foot=%-9s aspect=%-5s h=%-3d walk=%-6s region=%s" % (
            pid, "x".join(map(str, m["footprint"])), m["aspect_ratio"],
            m["height_span"], m["walkable_fraction"],
            m["largest_region_fraction"]))
