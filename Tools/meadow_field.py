#!/usr/bin/env python3
"""Houdini-driven meadow -- a cooked health field becomes deterministic grass points.

Optional World Compiler stage (recipe key ``meadow``). Pure Python, never imports unreal or hou.
The field is the CSV written by ``Tools/Houdini/foundry/morning_meadow_field.py`` (a hython cook of the ground
probe: slope, concavity, moisture, health, tuft per lattice cell). This module only *reads* that cache, so the
compile stays offline and byte-reproducible; the field file's sha256 is recorded in the bundle.

Mapping:
    health   -> density (a cell below ``health_min`` grows nothing), scale, and species affinity
    tuft     -> tall tufts vs short ground cover (species ``tuft_range``)
    ground   -> only probed BrushifyIsland soil carries grass (marble floors, bed, etc. never do)
"""
from __future__ import annotations

import csv
import math
from pathlib import Path
from typing import Any, Callable

FIELD_COLUMNS = ["ix", "iy", "x", "y", "z", "soil", "slope", "concavity", "moisture", "health", "tuft"]


def _clamp01(v: float) -> float:
    return 0.0 if v < 0.0 else 1.0 if v > 1.0 else v


def _lerp(a: float, b: float, t: float) -> float:
    return a + (b - a) * t


class Field:
    """Bilinear sampler over the Houdini lattice."""

    def __init__(self, cells: dict[tuple[int, int], dict[str, float]], x0: float, y0: float, step: float, nx: int, ny: int):
        self.cells, self.x0, self.y0, self.step, self.nx, self.ny = cells, x0, y0, step, nx, ny

    @classmethod
    def load(cls, path: Path) -> "Field":
        with path.open(encoding="utf-8", newline="") as fh:
            rows = list(csv.DictReader(fh))
        missing = [c for c in FIELD_COLUMNS if rows and c not in rows[0]]
        if not rows or missing:
            raise ValueError(f"meadow field {path.name}: empty or missing columns {missing}")
        xs = sorted({float(r["x"]) for r in rows})
        ys = sorted({float(r["y"]) for r in rows})
        step = (xs[1] - xs[0]) if len(xs) > 1 else 100.0
        cells: dict[tuple[int, int], dict[str, float]] = {}
        for r in rows:
            ix, iy = int(r["ix"]), int(r["iy"])
            cells[(ix, iy)] = {k: (float(r[k]) if r[k] != "" else 0.0) for k in FIELD_COLUMNS[4:]}
        return cls(cells, xs[0], ys[0], step, len(xs), len(ys))

    def sample(self, x: float, y: float, key: str) -> float:
        fx, fy = (x - self.x0) / self.step, (y - self.y0) / self.step
        i, j = math.floor(fx), math.floor(fy)
        tx, ty = fx - i, fy - j
        def v(a: int, b: int) -> float:
            c = self.cells.get((a, b))
            return c[key] if c else 0.0
        return (v(i, j) * (1 - tx) * (1 - ty) + v(i + 1, j) * tx * (1 - ty)
                + v(i, j + 1) * (1 - tx) * ty + v(i + 1, j + 1) * tx * ty)

    def extent(self) -> tuple[float, float, float, float]:
        return self.x0, self.y0, self.x0 + (self.nx - 1) * self.step, self.y0 + (self.ny - 1) * self.step


def validate(meadow: dict[str, Any]) -> list[str]:
    errors: list[str] = []
    if not meadow.get("field"):
        errors.append("meadow.field (path to the Houdini field CSV) is required")
    if not meadow.get("species"):
        errors.append("meadow.species must contain at least one species")
    for i, sp in enumerate(meadow.get("species") or []):
        for key in ("species_id", "meshes", "material"):
            if not sp.get(key):
                errors.append(f"meadow.species[{i}].{key} is required")
        if sp.get("weight", 1.0) <= 0:
            errors.append(f"meadow.species[{i}].weight must be > 0")
    return errors


def compile_meadow(cfg: dict[str, Any], *, field: Field, ground: Any, clearance: Any, seed: int, up_cm: float,
                   rand: Callable[..., float]) -> list[dict[str, Any]]:
    """Return abstract grass samples; the World Compiler turns them into points.csv-format rows."""
    spacing = float(cfg.get("spacing_cm", 40.0))
    jitter = float(cfg.get("jitter", 0.45))
    h_min = float(cfg.get("health_min", 0.2))
    gamma = float(cfg.get("density_gamma", 1.3))
    dscale = float(cfg.get("density_scale", 1.0))
    cap = int(cfg.get("max_points", 60000))
    species = cfg["species"]
    x0, y0, x1, y1 = field.extent()
    nx, ny = int((x1 - x0) // spacing), int((y1 - y0) // spacing)
    out: list[dict[str, Any]] = []
    for j in range(ny):
        for i in range(nx):
            x = x0 + (i + 0.5 + (rand(seed, "meadow", i, j, "jx") - 0.5) * 2.0 * jitter) * spacing
            y = y0 + (j + 0.5 + (rand(seed, "meadow", i, j, "jy") - 0.5) * 2.0 * jitter) * spacing
            z = ground.ground_z(x, y) if ground is not None else field.sample(x, y, "z")
            if z is None or (clearance is not None and clearance.blocked(x, y)):
                continue
            h = field.sample(x, y, "health")
            h2 = _clamp01(h + (rand(seed, "meadow", i, j, "d") - 0.5) * 0.30)
            if h2 < h_min:
                continue
            p = min(1.0, ((h2 - h_min) / (1.0 - h_min)) ** gamma * dscale)
            if rand(seed, "meadow", i, j, "keep") > p:
                continue
            tuft = _clamp01(field.sample(x, y, "tuft"))
            weights = []
            for sp in species:
                hlo, hhi = sp.get("health_range", [0.0, 1.0])
                tlo, thi = sp.get("tuft_range", [0.0, 1.0])
                aff = (1.0 if hlo <= h2 <= hhi else 0.15) * (1.0 if tlo <= tuft <= thi else 0.25)
                weights.append(float(sp.get("weight", 1.0)) * aff)
            total = sum(weights)
            pick, acc, chosen = rand(seed, "meadow", i, j, "sp") * total, 0.0, species[-1]
            for sp, w in zip(species, weights):
                acc += w
                if pick <= acc:
                    chosen = sp
                    break
            meshes = chosen["meshes"]
            lo, hi = chosen.get("scale_range", [0.9, 1.4])
            out.append({
                "x": x, "y": y, "z": float(z) + up_cm, "species": chosen["species_id"],
                "mesh": meshes[int(rand(seed, "meadow", i, j, "mesh") * len(meshes)) % len(meshes)],
                "material": chosen["material"],
                "scale": _lerp(float(lo), float(hi), rand(seed, "meadow", i, j, "sc")) * (0.8 + 0.4 * h2),
                "yaw": rand(seed, "meadow", i, j, "yaw") * 360.0,
                "health": h2, "tuft": tuft,
                "hue": (h2 * 0.85 + rand(seed, "meadow", i, j, "hue") * 0.15) % 1.0,
            })
            if len(out) >= cap:
                return out
    return out
