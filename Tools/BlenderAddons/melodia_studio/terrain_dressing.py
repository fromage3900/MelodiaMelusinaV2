"""Terrain dressing and magical systems for Resonant World v5.

Adds the layer that was missing from v4: the ground was walkable but bare.
Everything here is derived from the musical heightfield, so dressing is a
readable consequence of the score rather than random decoration.

Also exposes surface_height_at(), which fixes the v4 render bugs where
Melusina floated and eye-level cameras sat below the ground -- both caused by
using global bounding-box height instead of the specific column being stood on.

Pure Python. No bpy.
"""

import os
import math
import random

# Musical roles for dressed props, keyed by what the score is doing.
# (name, min_height_frac, block_hint, density, scale_range)
DRESSING_KINDS = {
    "resonance_crystal": {
        "label": "Resonance Crystal",
        "on": "peak",
        "density": 0.28,
        "scale": (0.35, 0.85),
        "emissive": True,
        "colour": (0.35, 0.70, 1.00),
        "description": "Grows on high-velocity peaks; marks loud notes.",
    },
    "chime_pillar": {
        "label": "Chime Pillar",
        "on": "ridge",
        "density": 0.16,
        "scale": (0.8, 2.2),
        "emissive": True,
        "colour": (1.00, 0.82, 0.35),
        "description": "Tall verticals on ridgelines; marks sustained pitch.",
    },
    "moss_cluster": {
        "label": "Moss Cluster",
        "on": "valley",
        "density": 0.42,
        "scale": (0.2, 0.5),
        "emissive": False,
        "colour": (0.25, 0.55, 0.30),
        "description": "Fills low ground; softens flat walkable areas.",
    },
    "songstone": {
        "label": "Songstone",
        "on": "path",
        "density": 0.22,
        "scale": (0.25, 0.6),
        "emissive": False,
        "colour": (0.55, 0.50, 0.62),
        "description": "Scattered along traversable routes.",
    },
    "note_bloom": {
        "label": "Note Bloom",
        "on": "slope",
        "density": 0.34,
        "scale": (0.18, 0.42),
        "emissive": True,
        "colour": (1.00, 0.55, 0.85),
        "description": "Flowers on transitions; marks melodic movement.",
    },
}

# Magical systems: volumetric / particle / light phenomena tied to the score.
MAGIC_SYSTEMS = {
    "aurora_veil": {
        "label": "Aurora Veil",
        "kind": "volume",
        "height_mult": 2.4,
        "colour": (0.35, 0.75, 1.00),
        "strength": 0.035,
        "description": "Sky curtain above the whole world; keyed to tonal centre.",
    },
    "motif_wisps": {
        "label": "Motif Wisps",
        "kind": "particles",
        "count": 420,
        "colour": (1.00, 0.75, 0.45),
        "strength": 4.0,
        "description": "Drifting emissive motes following the melody path.",
    },
    "cadence_pool": {
        "label": "Cadence Pool",
        "kind": "water",
        "colour": (0.20, 0.55, 0.85),
        "strength": 1.0,
        "description": "Reflective water filling the lowest basin.",
    },
    "harmonic_rings": {
        "label": "Harmonic Rings",
        "kind": "rings",
        "count": 5,
        "colour": (0.85, 0.60, 1.00),
        "strength": 6.0,
        "description": "Concentric emissive rings on the strongest chord.",
    },
    "ground_glow": {
        "label": "Ground Glow",
        "kind": "underlight",
        "colour": (0.45, 0.85, 1.00),
        "strength": 3.0,
        "description": "Light seeping between voxels from below.",
    },
}

# Named dressing recipes so renders are reproducible.
DRESSING_STYLES = {
    "bare": {
        "label": "Bare",
        "dressing": [],
        "magic": [],
        "description": "Control case: v4 terrain with no dressing.",
    },
    "verdant": {
        "label": "Verdant Resonance",
        "dressing": ["moss_cluster", "note_bloom", "songstone"],
        "magic": ["motif_wisps", "ground_glow"],
        "description": "Lush walkable ground, soft magic.",
    },
    "crystalline": {
        "label": "Crystalline Choir",
        "dressing": ["resonance_crystal", "chime_pillar", "songstone"],
        "magic": ["aurora_veil", "harmonic_rings"],
        "description": "Hard glowing mineral world, dramatic sky.",
    },
    "cathedral": {
        "label": "Sunken Cathedral",
        "dressing": ["chime_pillar", "moss_cluster", "resonance_crystal"],
        "magic": ["cadence_pool", "aurora_veil", "ground_glow"],
        "description": "Flooded basin, tall pillars, reflective water.",
    },
    "full_bloom": {
        "label": "Full Bloom",
        "dressing": list(DRESSING_KINDS.keys()),
        "magic": list(MAGIC_SYSTEMS.keys()),
        "description": "Everything on; stress test for density and cost.",
    },
    "waltz_garden": {
        "label": "Waltz Garden",
        "dressing": ["note_bloom", "moss_cluster", "songstone"],
        "magic": ["motif_wisps", "cadence_pool"],
        "description": "Triple-meter flow; soft paths with gentle water.",
    },
    "ballad_plaza": {
        "label": "Ballad Plaza",
        "dressing": ["songstone", "chime_pillar"],
        "magic": ["harmonic_rings", "ground_glow"],
        "description": "Slow open ground; sparse, monumental markers.",
    },
    "toccata_surface": {
        "label": "Toccata Surface",
        "dressing": ["resonance_crystal", "note_bloom"],
        "magic": ["harmonic_rings", "aurora_veil"],
        "description": "Fast, dense ornament; exposed sky effects.",
    },
    "lullaby_cave": {
        "label": "Lullaby Cave",
        "dressing": ["moss_cluster"],
        "magic": ["ground_glow", "aurora_veil"],
        "description": "Soft underground feel; minimal objects, ambient light.",
    },
    "fugue_maze": {
        "label": "Fugue Maze",
        "dressing": ["chime_pillar", "resonance_crystal", "songstone"],
        "magic": ["motif_wisps", "harmonic_rings", "ground_glow"],
        "description": "Dense layered walk; repeating markers and light.",
    },
    "nocturne_reflection": {
        "label": "Nocturne Reflection",
        "dressing": ["songstone", "moss_cluster"],
        "magic": ["cadence_pool", "aurora_veil"],
        "description": "Single reflective route; quiet and minimal.",
    },
    "pavane_grotto": {
        "label": "Pavane Grotto",
        "dressing": ["moss_cluster", "chime_pillar"],
        "magic": ["cadence_pool", "ground_glow"],
        "description": "Slow processional route; flooded chambers and underlight.",
    },
    "saltarello_ledges": {
        "label": "Saltarello Ledges",
        "dressing": ["resonance_crystal", "note_bloom", "songstone"],
        "magic": ["harmonic_rings", "motif_wisps"],
        "description": "Leaping rhythmic motion; exposed sky and bright markers.",
    },
    "madrigal_canopy": {
        "label": "Madrigal Canopy",
        "dressing": ["note_bloom", "moss_cluster"],
        "magic": ["aurora_veil", "motif_wisps"],
        "description": "Layered vocal richness; soft growths and drifting light.",
    },
    "chaconne_weave": {
        "label": "Chaconne Weave",
        "dressing": ["chime_pillar", "songstone", "resonance_crystal"],
        "magic": ["harmonic_rings", "ground_glow", "cadence_pool"],
        "description": "Repeating ground bass; monumental route with water and light.",
    },
    "aria_mist": {
        "label": "Aria Mist",
        "dressing": ["note_bloom", "songstone"],
        "magic": ["motif_wisps", "aurora_veil"],
        "description": "Solo vocal clarity; sparse, atmospheric, and vertical.",
    },
}


def load_styles():
    return dict(DRESSING_STYLES)


# ------------------------------------------------------------- terrain query

def surface_height_at(field, x, y, default=None):
    """Height of the column at (x, y).

    This is the fix for v4's floating character and sunken cameras: callers
    must ask for the height of the cell they occupy, not the height of the
    whole bounding box.
    """
    # A cell (cx, cy) covers the square [cx, cx+1) x [cy, cy+1), so the
    # owning cell is floor(), not round(). Rounding sent points at *.5 to a
    # neighbouring column and reported false height errors.
    cell = field.get((int(math.floor(x)), int(math.floor(y))))
    if cell is not None:
        return cell[0]
    if default is not None:
        return default
    # Nearest occupied column, so a query just off the mesh still lands.
    if not field:
        return 0
    best, best_d = 0, None
    for (fx, fy), (h, _v) in field.items():
        d = (fx - x) ** 2 + (fy - y) ** 2
        if best_d is None or d < best_d:
            best_d, best = d, h
    return best


def classify_cells(field, max_slope=1):
    """Tag every cell peak / ridge / slope / valley / path.

    Drives where dressing is allowed to appear so props follow the music.
    """
    if not field:
        return {}

    heights = [v[0] for v in field.values()]
    h_lo, h_hi = min(heights), max(heights)
    h_range = max(1, h_hi - h_lo)

    tags = {}
    for (x, y), (h, vel) in field.items():
        nbrs = []
        for dx, dy in ((1, 0), (-1, 0), (0, 1), (0, -1)):
            nb = field.get((x + dx, y + dy))
            if nb:
                nbrs.append(nb[0])

        norm = (h - h_lo) / float(h_range)
        higher = sum(1 for n in nbrs if n > h)
        lower = sum(1 for n in nbrs if n < h)
        flat = sum(1 for n in nbrs if n == h)

        if higher == 0 and norm > 0.72:
            tag = "peak"
        elif norm > 0.45 and (lower >= 1 or higher <= 1):
            tag = "ridge"
        elif norm < 0.28 and higher >= 2:
            tag = "valley"
        elif flat >= 3:
            tag = "path"
        else:
            tag = "slope"

        tags[(x, y)] = {"tag": tag, "height": h, "velocity": vel,
                        "norm": round(norm, 3)}
    return tags


def basin_cells(field, depth_frac=0.18):
    """Lowest cells, used to seat water for cadence_pool."""
    if not field:
        return [], 0
    heights = [v[0] for v in field.values()]
    h_lo, h_hi = min(heights), max(heights)
    cutoff = h_lo + max(1, int((h_hi - h_lo) * depth_frac))
    cells = [(k, v[0]) for k, v in field.items() if v[0] <= cutoff]
    return cells, cutoff


# ------------------------------------------------------------- placement

def plan_dressing(field, style_id="verdant", seed=7, budget=1400):
    """Deterministic prop placement plan.

    Returns a list of dicts ready for a renderer to instance. Deterministic
    for a given (field, style, seed) so renders are reproducible.
    """
    style = load_styles().get(style_id, DRESSING_STYLES["verdant"])
    kinds = style.get("dressing", [])
    if not kinds:
        return [], {"placed": 0, "by_kind": {}, "by_tag": {}}

    rng = random.Random(seed)
    tags = classify_cells(field)

    buckets = {}
    for cell, info in tags.items():
        buckets.setdefault(info["tag"], []).append((cell, info))

    placed = []
    by_kind = {}
    by_tag = {}

    for kind_id in kinds:
        spec = DRESSING_KINDS.get(kind_id)
        if not spec:
            continue
        target_tag = spec["on"]
        candidates = buckets.get(target_tag, [])
        if not candidates:
            continue

        rng.shuffle(candidates)
        remaining = budget - len(placed)
        if remaining <= 0:
            break
        want = int(len(candidates) * spec["density"])
        # max(1, ...) here used to override the budget, letting each kind add
        # one more prop past the cap.
        want = min(max(1, want), remaining)

        s_lo, s_hi = spec["scale"]
        for (cell, info) in candidates[:want]:
            x, y = cell
            jx = rng.uniform(0.18, 0.82)
            jy = rng.uniform(0.18, 0.82)
            # Jitter can push a prop over a cell that has no column at all
            # (an edge or gap), which leaves it hovering. Only keep the
            # offset when it still lands on real ground; otherwise sit at
            # the cell centre.
            if (int(math.floor(x + jx)), int(math.floor(y + jy))) not in field:
                jx, jy = 0.5, 0.5
            ground = surface_height_at(field, x + jx, y + jy,
                                       default=info["height"])
            placed.append({
                "kind": kind_id,
                "cell": [x, y],
                "location": [x + jx, y + jy, ground],
                "scale": round(rng.uniform(s_lo, s_hi), 3),
                "rotation_z": round(rng.uniform(0, math.tau), 3),
                "emissive": spec["emissive"],
                "colour": spec["colour"],
                "tag": target_tag,
                "velocity": info["velocity"],
            })
            by_kind[kind_id] = by_kind.get(kind_id, 0) + 1
            by_tag[target_tag] = by_tag.get(target_tag, 0) + 1

    stats = {"placed": len(placed), "by_kind": by_kind, "by_tag": by_tag,
             "style": style_id}
    return placed, stats


def plan_magic(field, style_id="verdant"):
    """Magical system plan derived from terrain extents."""
    style = load_styles().get(style_id, DRESSING_STYLES["verdant"])
    wanted = style.get("magic", [])
    if not field or not wanted:
        return [], {"systems": 0}

    xs = [k[0] for k in field]
    ys = [k[1] for k in field]
    hs = [v[0] for v in field.values()]
    mn = (min(xs), min(ys), 0)
    mx = (max(xs) + 1, max(ys) + 1, max(hs))
    centre = ((mn[0] + mx[0]) / 2.0, (mn[1] + mx[1]) / 2.0)
    span = max(mx[0] - mn[0], mx[1] - mn[1])

    out = []
    for sys_id in wanted:
        spec = MAGIC_SYSTEMS.get(sys_id)
        if not spec:
            continue
        entry = {"system": sys_id, "kind": spec["kind"],
                 "colour": spec["colour"], "strength": spec["strength"]}

        if spec["kind"] == "volume":
            entry["bounds_min"] = [mn[0], mn[1], mx[2]]
            entry["bounds_max"] = [mx[0], mx[1],
                                   mx[2] + span * 0.55 * spec["height_mult"] / 2.4]
        elif spec["kind"] == "particles":
            entry["count"] = spec["count"]
            entry["bounds_min"] = [mn[0], mn[1], 1]
            entry["bounds_max"] = [mx[0], mx[1], mx[2] + span * 0.25]
        elif spec["kind"] == "water":
            cells, cutoff = basin_cells(field)
            entry["level"] = cutoff
            entry["cells"] = len(cells)
            entry["bounds_min"] = [mn[0], mn[1]]
            entry["bounds_max"] = [mx[0], mx[1]]
        elif spec["kind"] == "rings":
            entry["count"] = spec["count"]
            entry["centre"] = [round(centre[0], 2), round(centre[1], 2)]
            entry["base_height"] = surface_height_at(field, centre[0], centre[1])
            entry["radius_step"] = round(span * 0.11, 3)
        elif spec["kind"] == "underlight":
            entry["centre"] = [round(centre[0], 2), round(centre[1], 2)]
            entry["height"] = -max(1, int(span * 0.05))
            entry["radius"] = round(span * 0.5, 2)

        out.append(entry)

    return out, {"systems": len(out), "style": style_id}
