#!/usr/bin/env python3
"""Melodic archipelago -- islands placed along a level's arpeggio contour.

Optional World Compiler stage (recipe key ``archipelago``). Pure Python, deterministic, never imports unreal.

A level has a mode (Lydian, Aeolian, ...). An arpeggio walks that mode's scale; every note becomes one floating island:
    pitch              -> island height (z)
    interval size      -> spacing to the previous island (leaps spread the archipelago) and the heading turn
    diatonic triad     -> biome and size (major = meadow, minor = grove, diminished/augmented = crystal)
    first note (tonic) -> the hero island, the largest
Consecutive islands are joined by a bridge row (the melodic line), so the chain is walkable / readable as a phrase.
The UE lane (Content/Python/world_compiler_archipelago_ue.py) spawns the island actors and one PCG biome volume each.
"""
from __future__ import annotations

import math
from typing import Any, Callable

QUALITY = {  # (third, fifth) semitones above the chord root -> (quality, radius scale, biome)
    (4, 7): ("maj", 1.00, "meadow"),
    (3, 7): ("min", 0.82, "grove"),
    (3, 6): ("dim", 0.62, "crystal"),
    (4, 8): ("aug", 0.72, "crystal"),
}
PATTERNS = {
    "arpeggio_up": [0, 2, 4, 7, 9, 11, 14],
    "arpeggio_arch": [0, 2, 4, 7, 4, 2, 5, 9, 7, 4],
    "wave_harp": [0, 2, 4, 6, 7],          # the Melusina WaveHarp chord (0/4/7/11/12 in Lydian steps)
    "prism_arch": [0, 3, 4, 2, 7, 3, 5, 9],  # touches the tritone degree: a diminished triad => a crystal island
}
COLUMNS = ["island_id", "x", "y", "z", "yaw", "scale", "mesh", "degree", "pitch", "quality", "biome", "beat",
           "radius_cm", "top_z_cm", "next_island", "bridge_len_cm"]


def validate(cfg: dict[str, Any], mode_ids: set[str]) -> list[str]:
    errors: list[str] = []
    if cfg.get("mode") not in mode_ids:
        errors.append(f"archipelago.mode {cfg.get('mode')!r} not in {sorted(mode_ids)}")
    if cfg.get("pattern", "arpeggio_arch") not in PATTERNS:
        errors.append(f"archipelago.pattern must be one of {sorted(PATTERNS)}")
    if not cfg.get("pool"):
        errors.append("archipelago.pool needs at least one island mesh")
    for i, m in enumerate(cfg.get("pool") or []):
        for k in ("mesh", "radius_cm", "top_z_cm"):
            if k not in m:
                errors.append(f"archipelago.pool[{i}].{k} is required")
    if int(cfg.get("count", 0)) < 2:
        errors.append("archipelago.count must be >= 2")
    return errors


def _triad(scale: list[int], degree: int) -> tuple[str, float, str]:
    root = scale[degree % 7] + 12 * (degree // 7)
    third = scale[(degree + 2) % 7] + 12 * ((degree + 2) // 7)
    fifth = scale[(degree + 4) % 7] + 12 * ((degree + 4) // 7)
    return QUALITY.get((third - root, fifth - root), ("sus", 0.7, "meadow"))


def compile_archipelago(cfg: dict[str, Any], *, scale: list[int], anchor: list[float], seed: int,
                        rand: Callable[..., float]) -> list[dict[str, Any]]:
    ax, ay, az = (float(v) for v in anchor)
    count = int(cfg["count"])
    pattern = PATTERNS[cfg.get("pattern", "arpeggio_arch")]
    gap = float(cfg.get("gap_cm", 9000.0))
    cm_per_st = float(cfg.get("cm_per_semitone", 420.0))
    turn = math.radians(float(cfg.get("turn_deg_per_semitone", 7.0)))
    heading = math.radians(float(cfg.get("heading_deg", 0.0))) + (rand(seed, "arch", "h0") - 0.5) * 0.4
    pool = sorted(cfg["pool"], key=lambda m: float(m["radius_cm"]))
    hero_scale = float(cfg.get("hero_scale", 1.25))
    heading_axis = math.radians(float(cfg.get("heading_deg", 0.0)))
    x, y = ax, ay
    px, py = ax, ay
    prev_pitch, prev = 0, None
    rows: list[dict[str, Any]] = []
    for i in range(count):
        deg = pattern[i % len(pattern)] + 7 * ((i // len(pattern)) % 2)
        pitch = scale[deg % 7] + 12 * (deg // 7)
        quality, rscale, biome = _triad(scale, deg)
        want = float(cfg.get("base_radius_cm", 3200.0)) * rscale * (hero_scale if i == 0 else 1.0)
        m = min(pool, key=lambda p: abs(float(p["radius_cm"]) - want))
        sc = want / float(m["radius_cm"]) * (0.92 + 0.16 * rand(seed, "arch", i, "sc"))
        radius = float(m["radius_cm"]) * sc
        interval = pitch - prev_pitch
        if prev is not None:
            heading += turn * interval + (rand(seed, "arch", i, "hd") - 0.5) * 0.35
            step = prev["radius_cm"] + radius + gap * (1.0 + 0.10 * min(abs(interval), 12) / 12.0)
            x, y = px + step * math.cos(heading), py + step * math.sin(heading)
        z = az + pitch * cm_per_st + (rand(seed, "arch", i, "z") - 0.5) * 600.0
        lat = float(cfg.get("lateral_alternate_cm", 0.0)) * (1.0 if i % 2 else -1.0)   # keep a central axis clear (nave, route)
        row = {"island_id": i, "x": x - lat * math.sin(heading_axis), "y": y + lat * math.cos(heading_axis), "z": z, "yaw": rand(seed, "arch", i, "yaw") * 360.0, "scale": sc,
               "mesh": m["mesh"], "degree": deg % 7, "pitch": pitch, "quality": quality, "biome": biome,
               "beat": float(i) * float(cfg.get("beats_per_note", 1.0)), "radius_cm": radius,
               "top_z_cm": z + float(m["top_z_cm"]) * sc, "next_island": i + 1 if i + 1 < count else -1, "bridge_len_cm": 0.0}
        if prev is not None:
            prev["bridge_len_cm"] = math.hypot(x - prev["x"], y - prev["y"])
        rows.append(row)
        px, py = x, y
        prev, prev_pitch = row, pitch
    return rows
