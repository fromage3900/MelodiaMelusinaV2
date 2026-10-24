"""Deterministic planetary heightfield math for the World Compiler.

Offline (pure stdlib, no ``hou``) extraction of the Melodia Planetary Lab
heightfield formula (``Tools/Houdini/build_melodia_planetary_lab.py`` ``_field``).
The Houdini lab stays the authoring / technical-review lane; this module lets the
World Compiler regenerate the SAME multi-mask field from a recipe seed, so the
lab's procedural terrain becomes a self-contained, reproducible compiler terrain
stage. Convergence rule: reuse the recipe, do not rewrite the generator.

Contract: Docs/WorldGen/WORLD_COMPILER_CONTRACT.md. Stage: ``stage_terrain``
``kind == "planetary_lab"`` in ``Tools/world_compiler.py``.
"""
from __future__ import annotations

import hashlib
import math
from typing import Any

SCHEMA = "melodia.houdini.planetary_lab.v1"
MASKS = ("height", "slope", "cavity", "shoreline", "biome", "traversal")


def field(size: int, seed: int, tile_x: int = 0, tile_y: int = 0) -> dict[str, list[list[float]]]:
    """Return ``{role: [[value...]]}`` -- byte-faithful to the lab's ``_field``."""
    values = {name: [] for name in MASKS}
    for y in range(size):
        row = {name: [] for name in MASKS}
        for x in range(size):
            wx = tile_x * (size - 1) + x
            wy = tile_y * (size - 1) + y
            macro = 0.5 + 0.25 * math.sin((wx + seed * 0.17) * 0.071) + 0.25 * math.cos((wy - seed * 0.11) * 0.053)
            mid = 0.5 + 0.5 * math.sin((wx + wy + seed) * 0.19)
            h = max(0.0, min(1.0, macro * 0.78 + mid * 0.22))
            slope = min(1.0, abs(math.cos((wx + seed) * 0.071)) * 0.55 + abs(math.sin((wy - seed) * 0.053)) * 0.45)
            cavity = max(0.0, min(1.0, 0.5 + (macro - mid)))
            shore = max(0.0, 1.0 - abs(h - 0.48) * 12.0)
            biome = max(0.0, min(1.0, macro))
            traversal = max(0.0, 1.0 - abs((y / max(1, size - 1)) - 0.5) * 12.0)
            for name, value in (("height", h), ("slope", slope), ("cavity", cavity),
                                ("shoreline", shore), ("biome", biome), ("traversal", traversal)):
                row[name].append(value)
        for name in MASKS:
            values[name].append(row[name])
    return values


# --- v2: fBm + domain warping (NMS-style "uber noise"). Deterministic in
# (size, seed, tile, octaves); shares the v1 mask vocabulary and compiler stage.
def _hash2(ix: int, iy: int, seed: int) -> float:
    """Deterministic pseudo-random in [0,1) from an integer lattice + seed."""
    h = (ix * 374761393 + iy * 668265263 + seed * 2246822519) & 0xFFFFFFFF
    h = (h ^ (h >> 13)) * 1274126177 & 0xFFFFFFFF
    return (h ^ (h >> 16)) / 4294967296.0


def _smooth(t: float) -> float:
    return t * t * (3.0 - 2.0 * t)


def value_noise(x: float, y: float, seed: int) -> float:
    """Continuous value noise on an integer lattice (0..1)."""
    ix = math.floor(x)
    iy = math.floor(y)
    fx = x - ix
    fy = y - iy
    a = _hash2(ix, iy, seed)
    b = _hash2(ix + 1, iy, seed)
    c = _hash2(ix, iy + 1, seed)
    d = _hash2(ix + 1, iy + 1, seed)
    ux = _smooth(fx)
    uy = _smooth(fy)
    return (a + (b - a) * ux) * (1.0 - uy) + (c + (d - c) * ux) * uy


def fbm(x: float, y: float, seed: int, octaves: int = 5, lacunarity: float = 2.0, gain: float = 0.5) -> float:
    """Fractional Brownian motion, normalised to 0..1."""
    total = 0.0
    norm = 0.0
    amp = 1.0
    freq = 1.0
    for _ in range(max(1, octaves)):
        total += value_noise(x * freq, y * freq, seed) * amp
        norm += amp
        amp *= gain
        freq *= lacunarity
    return total / norm if norm else 0.0


def field_v2(size: int, seed: int, tile_x: int = 0, tile_y: int = 0,
             octaves: int = 5, warp_strength: float = 1.0) -> dict[str, list[list[float]]]:
    """fBm terrain with domain warping + ridge emphasis, 0..1 normalised.

    Richer successor to ``field`` (the lab's single-scale extract). Same mask
    vocabulary; a distinct seed stream drives the warp displacement so height and
    warp never phase-lock. Deterministic in (size, seed, tile, octaves).
    """
    values = {name: [] for name in MASKS}
    warp_seed = seed + 77701
    scale = 0.01
    for y in range(size):
        row = {name: [] for name in MASKS}
        for x in range(size):
            wx = tile_x * (size - 1) + x
            wy = tile_y * (size - 1) + y
            # domain warp: displace the sample coordinate by a low-freq noise field
            wxs = wx + warp_strength * 240.0 * (value_noise(wx * scale, wy * scale, warp_seed) - 0.5)
            wys = wy + warp_strength * 240.0 * (value_noise(wx * scale + 100.0, wy * scale + 50.0, warp_seed + 1) - 0.5)
            h = fbm(wxs * scale, wys * scale, seed, octaves)
            ridge = (1.0 - abs(2.0 * h - 1.0)) ** 2  # NMS-style ridge modifier
            h = 0.65 * h + 0.35 * ridge
            slope = min(1.0, fbm(wx * scale * 2.0, wy * scale * 2.0, seed + 11111, 4))
            cavity = max(0.0, min(1.0, fbm(wx * scale * 0.8, wy * scale * 0.8, seed + 22222, 4)))
            shore = max(0.0, 1.0 - abs(h - 0.5) * 6.0)
            biome = max(0.0, min(1.0, fbm(wx * scale * 0.6, wy * scale * 0.6, seed + 33333, 3)))
            traversal = max(0.0, 1.0 - abs((y / max(1, size - 1)) - 0.5) * 2.0)
            for name, value in (("height", h), ("slope", slope), ("cavity", cavity),
                                ("shoreline", shore), ("biome", biome), ("traversal", traversal)):
                row[name].append(value)
        for name in MASKS:
            values[name].append(row[name])
    return values


def _flat(grid: list[list[float]]) -> list[float]:
    return [v for row in grid for v in row]


def r16_bytes(grid: list[list[float]]) -> bytes:
    """16-bit big-endian raw, byte-faithful to the lab's PGM P5 writer."""
    body = bytearray()
    for v in _flat(grid):
        sample = round(max(0.0, min(1.0, v)) * 65535)
        body.append((sample >> 8) & 255)
        body.append(sample & 255)
    return bytes(body)


def sha_r16(grid: list[list[float]]) -> str:
    return hashlib.sha256(r16_bytes(grid)).hexdigest()


def stats(grid: list[list[float]]) -> dict[str, float]:
    flat = _flat(grid)
    return {"min": min(flat), "max": max(flat), "mean": sum(flat) / len(flat)}


def fraction_above(grid: list[list[float]], thresh: float) -> float:
    flat = _flat(grid)
    return sum(1 for v in flat if v > thresh) / len(flat)


def biome_classes(grid: list[list[float]], bins: int = 4) -> dict[str, Any]:
    """Discretize the biome mask into labelled value bins (0..bins-1)."""
    counts = [0] * bins
    for v in _flat(grid):
        counts[min(bins - 1, int(v * bins))] += 1
    return {"bins": bins, "counts": counts}
