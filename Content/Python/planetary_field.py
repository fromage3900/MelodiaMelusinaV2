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
