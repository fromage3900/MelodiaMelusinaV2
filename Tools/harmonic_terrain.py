#!/usr/bin/env python3
"""Harmonic terrain -- chords carve valleys, arpeggios raise ridges.

Optional World Compiler stage (recipe key ``harmony``). Pure Python, deterministic,
never imports unreal. Emits a feature graph (nodes + edges) for PCG/PCGEx and a raw
uint16 heightmap (``.r16``, little-endian) that UE Landscape and Houdini HeightField
File both import directly.

Musical mapping:
    chord root      -> position on a circle-of-fifths ring around the chunk centre
    chord quality   -> valley profile (maj U-bowl, min V, dim canyon, aug crater, sus terrace)
    chord beats     -> valley length (stretched toward the next chord)
    7th chords      -> one tributary branch
    voice leading   -> a channel between consecutive chord valleys
    arpeggio note   -> a peak; pitch sets height, interval size sets slope
    arpeggio motion -> ridge edges; stepwise motion keeps the ridge, leaps cut a col
    drone           -> low-frequency macro swell
"""
from __future__ import annotations

import json
import math
import struct
from typing import Any, Callable

QUALITIES: dict[str, dict[str, Any]] = {
    "maj":  {"intervals": [0, 4, 7],     "profile": "u",       "width": 1.00, "depth": 1.00},
    "min":  {"intervals": [0, 3, 7],     "profile": "v",       "width": 0.80, "depth": 1.15},
    "dim":  {"intervals": [0, 3, 6],     "profile": "canyon",  "width": 0.45, "depth": 1.60},
    "aug":  {"intervals": [0, 4, 8],     "profile": "crater",  "width": 0.90, "depth": 1.30},
    "sus2": {"intervals": [0, 2, 7],     "profile": "terrace", "width": 1.15, "depth": 0.60},
    "sus4": {"intervals": [0, 5, 7],     "profile": "terrace", "width": 1.10, "depth": 0.70},
    "maj7": {"intervals": [0, 4, 7, 11], "profile": "u",       "width": 1.20, "depth": 1.00},
    "min7": {"intervals": [0, 3, 7, 10], "profile": "v",       "width": 0.90, "depth": 1.15},
    "dom7": {"intervals": [0, 4, 7, 10], "profile": "v",       "width": 0.95, "depth": 1.25},
}

NODE_COLUMNS = [
    "node_id", "kind", "x", "y", "z", "pitch", "degree", "chord_index", "quality", "beat",
    "radius_cm", "depth_cm", "height_cm", "hue_seed", "Position",
]
EDGE_COLUMNS = [
    "edge_id", "kind", "start_node", "end_node", "x0", "y0", "z0", "x1", "y1", "z1",
    "width_cm", "interval", "Start", "End",
]


def _smoothstep(e0: float, e1: float, x: float) -> float:
    t = min(1.0, max(0.0, (x - e0) / (e1 - e0)))
    return t * t * (3.0 - 2.0 * t)


def _profile(kind: str, t: float) -> float:
    """Carve depth fraction at normalised distance t (0 centre, 1 rim)."""
    if kind == "u":
        return 1.0 - _smoothstep(0.55, 1.0, t)
    if kind == "v":
        return max(0.0, 1.0 - t) ** 1.2
    if kind == "canyon":
        return 1.0 - _smoothstep(0.30, 0.45, t)
    if kind == "crater":
        return (1.0 - _smoothstep(0.0, 0.9, t)) - 0.25 * math.exp(-((t - 1.0) / 0.15) ** 2)
    if kind == "terrace":
        base = 1.0 - _smoothstep(0.0, 1.0, t)
        step = math.floor(base * 3.0) / 3.0
        return step + (base - step) * 0.25
    raise ValueError(f"unknown valley profile {kind!r}")


def _seg(px: float, py: float, ax: float, ay: float, bx: float, by: float) -> tuple[float, float]:
    """Distance from p to segment ab, and the parameter t of the closest point."""
    dx, dy = bx - ax, by - ay
    ll = dx * dx + dy * dy
    t = 0.0 if ll == 0.0 else min(1.0, max(0.0, ((px - ax) * dx + (py - ay) * dy) / ll))
    return math.hypot(px - (ax + t * dx), py - (ay + t * dy)), t


def validate(harmony: dict[str, Any]) -> list[str]:
    errors: list[str] = []
    res = harmony.get("resolution", 505)
    if not isinstance(res, int) or res < 33 or res % 2 == 0:
        errors.append("harmony.resolution must be an odd integer >= 33")
    for i, chord in enumerate(harmony.get("progression") or []):
        if chord.get("quality") not in QUALITIES:
            errors.append(f"harmony.progression[{i}].quality {chord.get('quality')!r} not in {sorted(QUALITIES)}")
    if not harmony.get("progression"):
        errors.append("harmony.progression must contain at least one chord")
    for i, arp in enumerate(harmony.get("arpeggios") or []):
        if len(arp.get("notes") or []) < 2:
            errors.append(f"harmony.arpeggios[{i}].notes needs at least two notes")
    return errors


def compile_harmony(harmony: dict[str, Any], *, seed: int, anchor: list[float], scale_intervals: list[int],
                    rand: Callable[..., float]) -> dict[str, Any]:
    size = float(harmony.get("size_cm", 25600.0))
    res = int(harmony.get("resolution", 505))
    ax, ay, az = (float(v) for v in anchor)
    base_z = float(harmony.get("base_z_cm", 0.0))
    vcfg = harmony.get("valleys", {})
    ring = float(vcfg.get("ring_radius_cm", size * 0.28))
    v_radius = float(vcfg.get("radius_cm", size * 0.07))
    v_depth = float(vcfg.get("depth_cm", 1400.0))
    ch_ratio = float(vcfg.get("channel_depth_ratio", 0.35))
    ch_width = float(vcfg.get("channel_width_cm", v_radius * 0.3))
    macro = harmony.get("macro", {})
    m_amp = float(macro.get("amplitude_cm", 0.0))
    m_wave = float(macro.get("wavelength_cm", size * 0.5))
    ring_rot = rand(seed, "harmony", "ring_rotation") * 2.0 * math.pi
    m_phase = [rand(seed, "harmony", "macro", k) * 2.0 * math.pi for k in range(4)]

    def degree_of(pitch: int) -> int:
        pc = pitch % 12
        return scale_intervals.index(pc) if pc in scale_intervals else -1

    # ------------------------------------------------------------- valleys (chords)
    valleys: list[dict[str, Any]] = []   # carve features: centre segment + profile
    nodes: list[dict[str, Any]] = []
    edges: list[dict[str, Any]] = []
    prog = harmony["progression"]
    beat = 0.0
    centres = []
    for ci, chord in enumerate(prog):
        root = int(chord["root"])
        fifths = (root * 7) % 12
        ang = ring_rot + fifths * (math.pi / 6.0) + (rand(seed, "harmony", "chord_jitter", ci) - 0.5) * 0.2
        centres.append((ax + ring * math.cos(ang), ay + ring * math.sin(ang)))
    for ci, chord in enumerate(prog):
        q = QUALITIES[chord["quality"]]
        beats = float(chord.get("beats", 4))
        cx, cy = centres[ci]
        nx, ny = centres[(ci + 1) % len(prog)]
        dx, dy = nx - cx, ny - cy
        dl = math.hypot(dx, dy) or 1.0
        ux, uy = dx / dl, dy / dl
        radius = v_radius * q["width"]
        length = dl * 0.5 * min(1.0, beats / 8.0)        # held chords run further toward the next
        depth = v_depth * q["depth"]
        valleys.append({"a": (cx, cy), "b": (cx + ux * length, cy + uy * length), "r": radius,
                        "d": depth, "p": q["profile"], "ci": ci})
        nodes.append({"kind": "valley", "x": cx, "y": cy, "pitch": int(chord["root"]), "degree": degree_of(int(chord["root"])),
                      "chord_index": ci, "quality": chord["quality"], "beat": beat, "radius_cm": radius,
                      "depth_cm": depth, "height_cm": 0.0})
        for bi in range(len(q["intervals"]) - 3):   # 7ths (and beyond) branch a tributary
            side = 1.0 if rand(seed, "harmony", "tributary", ci, bi) < 0.5 else -1.0
            tx, ty = -uy * side, ux * side
            tl = radius * 1.6
            valleys.append({"a": (cx, cy), "b": (cx + tx * tl, cy + ty * tl), "r": radius * 0.5,
                            "d": depth * 0.5, "p": "v", "ci": ci})
        beat += beats
    channel_depth = min(v["d"] for v in valleys) * ch_ratio
    for ci in range(len(prog)):
        a, b = centres[ci], centres[(ci + 1) % len(prog)]
        if len(prog) > 1 and not (len(prog) == 2 and ci == 1):
            valleys.append({"a": a, "b": b, "r": ch_width, "d": channel_depth, "p": "v", "ci": -1})

    # ------------------------------------------------------------- ridges (arpeggios)
    peaks: list[dict[str, Any]] = []
    ridges: list[dict[str, Any]] = []
    for arp in harmony.get("arpeggios") or []:
        notes = [int(n) for n in arp["notes"]]
        su, sv = arp.get("start_uv", [0.0, 0.0])
        px, py = ax + su * size, ay + sv * size
        heading = math.radians(float(arp.get("heading_deg", 0.0)))
        step = float(arp.get("step_cm", size * 0.1))
        base_h = float(arp.get("peak_base_cm", 1800.0))
        per_st = float(arp.get("cm_per_semitone", 250.0))
        turn = math.radians(float(arp.get("turn_deg_per_semitone", 6.0)))
        ridge_scale = float(arp.get("ridge_width_scale", 0.45))
        lo = min(notes)
        first = len(peaks)
        for ni, pitch in enumerate(notes):
            interval = 0 if ni == 0 else pitch - notes[ni - 1]
            if ni > 0:
                heading += turn * interval
                px += step * math.cos(heading)
                py += step * math.sin(heading)
            h = base_h + (pitch - lo) * per_st
            leap = abs(notes[ni + 1] - pitch) if ni + 1 < len(notes) else abs(interval)
            radius = step * (0.7 - 0.3 * min(leap, 12) / 12.0)   # peaks spaced by the beat; leaps steepen
            peaks.append({"x": px, "y": py, "h": h, "r": radius})
            nodes.append({"kind": "peak", "x": px, "y": py, "pitch": pitch, "degree": degree_of(pitch), "chord_index": -1,
                          "quality": "none", "beat": float(ni) * float(arp.get("beats_per_note", 0.5)),
                          "radius_cm": radius, "depth_cm": 0.0, "height_cm": h, "_peak": len(peaks) - 1})
            if ni > 0:
                p0, p1 = peaks[first + ni - 1], peaks[first + ni]
                saddle = min(0.6, abs(interval) / 12.0)        # leaps cut a col
                ridges.append({"p0": p0, "p1": p1, "w": ridge_scale * (p0["r"] + p1["r"]) / 2.0, "s": saddle,
                               "interval": interval, "n0": len(nodes) - 2, "n1": len(nodes) - 1})

    # ------------------------------------------------------------- height field
    def fields(x: float, y: float) -> tuple[float, float, float, int]:
        """(height, mountain, carve, chord index of the deepest carve or -1)."""
        h = base_z
        if m_amp:
            k = 2.0 * math.pi / m_wave
            h += m_amp * 0.5 * (math.sin(k * x + m_phase[0]) * math.cos(k * 0.7 * y + m_phase[1])
                                + 0.5 * math.sin(k * 1.9 * (x + y) + m_phase[2]))
        mount = 0.0
        for p in peaks:
            d = math.hypot(x - p["x"], y - p["y"])
            if d < p["r"] * 2.5:
                mount = max(mount, p["h"] * math.exp(-2.0 * (d / p["r"]) ** 2))
        for r in ridges:
            p0, p1 = r["p0"], r["p1"]
            d, t = _seg(x, y, p0["x"], p0["y"], p1["x"], p1["y"])
            if d < r["w"] * 2.5:
                hr = (p0["h"] + (p1["h"] - p0["h"]) * t) * (1.0 - r["s"] * 4.0 * t * (1.0 - t))
                mount = max(mount, hr * math.exp(-2.0 * (d / r["w"]) ** 2))
        carve, chord = 0.0, -1
        for v in valleys:
            d, _ = _seg(x, y, v["a"][0], v["a"][1], v["b"][0], v["b"][1])
            if d < v["r"] * 1.3:
                c = v["d"] * _profile(v["p"], d / v["r"])
                if c > carve:
                    carve, chord = c, v["ci"]
        return h + mount - carve, mount, carve, chord

    def height(x: float, y: float) -> float:
        return fields(x, y)[0]

    half = size / 2.0
    cell = size / (res - 1)
    border = float(harmony.get("border_falloff_cm", 0.0))
    drop = float(harmony.get("border_drop_cm", 0.0))
    round_border = harmony.get("border_shape", "square") == "round"

    def tile_height(x: float, y: float) -> float:
        """Ease the tile border to base_z - border_drop_cm. A round border with a drop makes a floating island:
        the rim plunges away and keeps falling past the inscribed circle into the corners."""
        h = height(x, y)
        if border <= 0.0:
            return h
        if round_border:
            edge = half - math.hypot(x - ax, y - ay)
        else:
            edge = min(half - abs(x - ax), half - abs(y - ay))
        floor = base_z - drop * (1.0 + max(0.0, -edge) / border)
        return floor + (h - floor) * _smoothstep(0.0, border, edge)

    grid = [tile_height(ax - half + i * cell, ay - half + j * cell) for j in range(res) for i in range(res)]
    z_min, z_max = min(grid), max(grid)
    span = max(z_max - z_min, 1.0)
    r16 = struct.pack(f"<{len(grid)}H", *(int(round((h - z_min) / span * 65535.0)) for h in grid))

    # ------------------------------------------------------------- tables
    node_rows, edge_rows = [], []
    for nid, n in enumerate(nodes):
        z = az + tile_height(n["x"], n["y"])
        n["z"] = z
        node_rows.append({**{k: v for k, v in n.items() if not k.startswith("_")}, "node_id": nid,
                          "hue_seed": rand(seed, "harmony", "hue", n["kind"], nid),
                          "Position": (n["x"], n["y"], z)})
    eid = 0
    for r in ridges:
        a, b = nodes[r["n0"]], nodes[r["n1"]]
        edge_rows.append({"edge_id": eid, "kind": "ridge", "start_node": r["n0"], "end_node": r["n1"],
                          "a": a, "b": b, "width_cm": r["w"], "interval": r["interval"]})
        eid += 1
    valley_ids = [i for i, n in enumerate(nodes) if n["kind"] == "valley"]
    for k in range(len(valley_ids) if len(valley_ids) > 2 else len(valley_ids) - 1):
        i0, i1 = valley_ids[k], valley_ids[(k + 1) % len(valley_ids)]
        a, b = nodes[i0], nodes[i1]
        edge_rows.append({"edge_id": eid, "kind": "voice_leading", "start_node": i0, "end_node": i1, "a": a, "b": b,
                          "width_cm": ch_width, "interval": ((b["pitch"] - a["pitch"] + 6) % 12) - 6})
        eid += 1
    for e in edge_rows:
        a, b = e.pop("a"), e.pop("b")
        e.update({"x0": a["x"], "y0": a["y"], "z0": a["z"], "x1": b["x"], "y1": b["y"], "z1": b["z"],
                  "Start": (a["x"], a["y"], a["z"]), "End": (b["x"], b["y"], b["z"])})

    biome_rows = _biomes(harmony.get("biomes"), seed=seed, rand=rand, ax=ax, ay=ay, az=az, half=half, border=border,
                         round_border=round_border, fields=fields, tile_height=tile_height, prog=prog,
                         degree_of=degree_of, peaks=peaks)

    meta = {
        "schema": "melodia.harmonic_terrain.v1",
        "size_cm": size,
        "resolution": res,
        "cell_cm": cell,
        "anchor_cm": [ax, ay, az],
        "z_min_cm": az + z_min,
        "z_max_cm": az + z_max,
        "heightmap": {"file": "harmony_height.r16", "format": "uint16_le_raw", "rows": res, "cols": res,
                      "origin": "min-x,min-y corner, row-major +x then +y"},
        "ue_landscape_import": {
            "location_cm": [ax - half, ay - half, az + (z_min + z_max) / 2.0],
            "scale": [cell, cell, span / 512.0],
            "note": "UE landscape: 32768 = location z; full uint16 range spans 512 * scale.z cm",
        },
        "counts": {"chords": len(prog), "valley_features": len(valleys), "peaks": len(peaks), "ridges": len(ridges),
                   "biome_points": {b: sum(1 for r in biome_rows if r["biome"] == b) for b in BIOMES}},
    }
    return {"nodes": node_rows, "edges": edge_rows, "r16": r16, "meta": meta, "biomes": biome_rows}


BIOMES = ("basin", "meadow", "cliff", "crest")


def _biomes(cfg: dict[str, Any] | None, *, seed: int, rand: Callable[..., float], ax: float, ay: float, az: float,
            half: float, border: float, round_border: bool, fields: Callable, tile_height: Callable,
            prog: list[dict[str, Any]], degree_of: Callable[[int], int], peaks: list[dict[str, Any]]) -> list[dict[str, Any]]:
    """Classify a jittered grid over the tile into musical biomes.

    basin  -- inside a chord valley: rainbow flora tinted by the chord root's scale degree (degree -> band)
    meadow -- gentle open ground: flora tinted by the nearest arpeggio note's degree
    cliff  -- steep slopes: rocks
    crest  -- high on the arpeggio ridge: crystals, larger toward the top note
    """
    if not cfg:
        return []
    spacing = float(cfg.get("spacing_cm", 250.0))
    cliff_slope = float(cfg.get("cliff_slope", 0.7))
    crest_frac = float(cfg.get("crest_fraction", 0.55))
    dens = cfg.get("density", {})
    top = max((p["h"] for p in peaks), default=1.0)
    n = int(2 * half // spacing)
    rows: list[dict[str, Any]] = []
    for j in range(n):
        for i in range(n):
            x = ax - half + (i + rand(seed, "biome", "jx", i, j)) * spacing
            y = ay - half + (j + rand(seed, "biome", "jy", i, j)) * spacing
            edge = half - math.hypot(x - ax, y - ay) if round_border else min(half - abs(x - ax), half - abs(y - ay))
            if edge < border:
                continue                                  # the rim falls away; nothing grows on the drop
            h, mount, carve, chord = fields(x, y)
            e = spacing * 0.5
            gx = (tile_height(x + e, y) - tile_height(x - e, y)) / (2 * e)
            gy = (tile_height(x, y + e) - tile_height(x, y - e)) / (2 * e)
            slope = math.hypot(gx, gy)
            near = min(peaks, key=lambda p: math.hypot(x - p["x"], y - p["y"])) if peaks else None
            if near is not None and mount > crest_frac * near["h"] and carve == 0.0:
                biome = "crest"                           # the ridge itself, however steep
            elif slope > cliff_slope:
                biome = "cliff"
            elif chord >= 0 and carve > float(cfg.get("basin_min_depth_cm", 400.0)):
                biome = "basin"
            elif slope < 0.45:
                biome = "meadow"
            else:
                continue
            if rand(seed, "biome", "keep", i, j) > float(dens.get(biome, 0.3)):
                continue
            spec = cfg[{"basin": "flora", "meadow": "flora", "cliff": "rocks", "crest": "crystals"}[biome]]
            k = int(rand(seed, "biome", "variant", i, j) * len(spec["meshes"])) % len(spec["meshes"])
            if biome == "basin":
                degree = degree_of(int(prog[chord]["root"]))
            elif near is not None:
                degree = near.get("degree", 0)
            else:
                degree = 0
            band = max(0, degree)
            lo, hi = spec.get("scale_range", [1.0, 1.0])
            grow = near["h"] / top if (biome == "crest" and near is not None) else 1.0
            rows.append({"biome": biome, "x": x, "y": y, "z": az + tile_height(x, y), "band": band, "variant": k,
                         "mesh_index": k, "spec": spec, "scale": (lo + (hi - lo) * rand(seed, "biome", "scale", i, j)) * grow,
                         "yaw": rand(seed, "biome", "yaw", i, j) * 360.0,
                         "pitch": (rand(seed, "biome", "pitch", i, j) - 0.5) * 30.0 if biome == "cliff" else 0.0,
                         "slope": slope, "hue": rand(seed, "biome", "hue", i, j),
                         "resonance": min(1.0, max(0.0, mount / top))})
    return rows


def vec(v: tuple[float, float, float], fmt: Callable[[float], str]) -> str:
    return f"(X={fmt(v[0])},Y={fmt(v[1])},Z={fmt(v[2])})"


def to_json(meta: dict[str, Any]) -> bytes:
    return (json.dumps(meta, indent=2, sort_keys=True) + "\n").encode("utf-8")
