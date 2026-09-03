#!/usr/bin/env python
"""Seasonal lace Opacity maps for the masked Alpha master (2026-09-02 closeout).

Resolves polish finding P2: the masked M_Master_Toon_Universal_Alpha needs an
explicit per-season Opacity map for the lace/ornament layers (Collar /
Shoulder_Trim / Shoulder_Ornament), which the seasonal variants left implicit.
This emits 4 seasons x 3 layers = 12 Opacity maps (lacy coverage, seeded).

Recipe: per lace kind (floral/eyelet/dotgrid) -> lace overlay -> opacity = clip(
lace*0.95+0.08+fray, 0,1), exactly the fabric-cops recipe. Deterministic
SEED 20260902.

Run: ./.venv/Scripts/python.exe Tools/Houdini/sea_above_reef/shorewake_seasonal_opacity.py
"""
from __future__ import annotations

import sys
from pathlib import Path

import numpy as np
from PIL import Image

PROJECT = Path(__file__).resolve().parents[3]
sys.path.insert(0, str(PROJECT / "Tools" / "Houdini" / "sea_above_reef"))
import reef_common as rc  # noqa: E402
import shorewake_seasonal_variants as seas  # noqa: E402  (SEASONS reuse via module name only)

OUT = PROJECT / "Saved/Audit/melusina_lookdev/garment_refresh/seasons/opacity"
OUT.mkdir(parents=True, exist_ok=True)
SEED = 20260902
SIZE = 2048

# copied minimal lace overlay (kind -> formula) so the script is self-contained
def smoothstep(a, b, x):
    t = np.clip((x - a) / (b - a), 0, 1)
    return t * t * (3 - 2 * t)


def lace_overlay(kind, rng):
    s = SIZE
    y, x = np.mgrid[0:s, 0:s].astype(np.float32)
    fx, fy = (x / s * 8) % 1, (y / s * 8) % 1
    tx, ty = fx * 2 - 1, fy * 2 - 1
    dist = np.sqrt(tx * tx + ty * ty)
    ang = np.arctan2(ty, tx)
    if kind == "dotgrid":
        dot = smoothstep(0.6, 0.95, np.clip(1 - dist * 3.0, 0, 1))
        lat = smoothstep(0.45, 0.85, abs(np.sin(fx * np.pi * 2) * np.sin(fy * np.pi * 2)))
        lace = np.maximum(dot * 0.7, lat * 0.45)
    elif kind == "eyelet":
        flower = smoothstep(0.35, 0.72, np.clip(1 - dist * 1.4 + np.cos(ang * 5) * 0.18, 0, 1))
        vine = smoothstep(0.45, 0.85, abs(np.sin(fx * np.pi * 2) * np.sin(fy * np.pi * 2)))
        eyelet = smoothstep(0.55, 0.9, np.clip(1 - dist * 2.2, 0, 1)) * 0.85
        lace = np.maximum(flower * 0.95, np.maximum(vine * 0.75, eyelet * 0.3))
    else:  # floral
        flower = smoothstep(0.35, 0.72, np.clip(1 - dist * 1.4 + np.cos(ang * 5) * 0.18, 0, 1))
        vine = smoothstep(0.45, 0.85, abs(np.sin(fx * np.pi * 2) * np.sin(fy * np.pi * 2)))
        eyelet = smoothstep(0.55, 0.9, np.clip(1 - dist * 2.2, 0, 1)) * 0.85
        lace = np.maximum(flower * 0.95, np.maximum(vine * 0.75, eyelet * 0.3))
    lace = np.clip(lace, 0, 1) * (0.92 + 0.08 * np.sin(x * 0.015 + y * 0.013))
    return lace


LACE_KIND = {
    "M_Collar": "floral",
    "M_Shoulder_Trim": "eyelet",
    "M_Shoulder_Ornament": "dotgrid",
}
LACE_LAYERS = ["M_Collar", "M_Shoulder_Trim", "M_Shoulder_Ornament"]


def main():
    files = []
    for season in seas.SEASONS:
        rng = np.random.default_rng(SEED + abs(hash(season)) % 1000)
        for layer in LACE_LAYERS:
            lc = lace_overlay(LACE_KIND[layer], rng)
            fray = rng.normal(size=(SIZE, SIZE)) * 0.012
            opacity = np.clip(lc * 0.95 + 0.08 + fray, 0, 1)
            f = rc.save_image(OUT / f"T_Shorewake_Season_{season}_{layer}_Opacity.png",
                              opacity, "gray")
            files.append(f)
        print(f"[opacity] {season}: 3 lace layers")
    names = [Path(f).name for f in files]
    rc.write_manifest(
        OUT / "seasonal_opacity_manifest.json",
        "melodia.shorewake_seasonal_opacity.v1",
        SEED,
        {"size": SIZE, "layers": LACE_LAYERS,
         "seasons": list(seas.SEASONS.keys()),
         "recipe": "lace kind per layer (floral/eyelet/dotgrid) -> opacity "
                   "clip(lace*0.95+0.08+fray,0,1); explicit masked-Alpha cutout "
                   "for M_Master_Toon_Universal_Alpha",
         "audio_contract": "texture-only"},
        names,
    )
    print(f"[opacity] {len(files)} maps -> {OUT}")


if __name__ == "__main__":
    main()