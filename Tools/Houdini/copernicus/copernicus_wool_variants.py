#!/usr/bin/env python
"""
Copernicus wool variants - 2K tileable wool fabric family (Melodia wool/cloth).

Five variants, each a distinct wool construction + colorway:
  WoolKnit   - stockinette V-stitch columns, undyed oatmeal cream
  WoolCable  - 3-strand twisted cable columns, warm honey amber
  WoolTweed  - herringbone twill, sage/ochre Donegal heather with nep flecks
  WoolFelt   - matted directional fibres, dusty rose mauve (structureless)
  WoolBoucle - dense loop nubs, ecru off-white

Same lane contract as copernicus_film_tilables.py (imported, not copied):
Houdini 22.0.368 Apprentice caps COP rop writes at 1920x1080, so the 2048^2
maps use the proven numpy+PIL path (cymatic precedent); COP graphs stay
available for true-COP 2K cooks once the license allows Indie/Commercial.

Tiling by construction: modulo-wrapped value-noise/Worley (inherited),
integer-period sinusoids only, integer cell counts that divide the extent
(power-of-two sizes), np.roll wrap-around normals. The manifest seam metric
is a smoke check, construction is the proof.

Maps per surface (4): BaseColor (sRGB), Normal (BC5), ORM (R=AO, G=Roughness,
B=Metallic), Height. Seed 20260828 locked (lane seed discipline).

Output: <out>/T_<Surface>_<Map>.png + copernicus_wool_variants_manifest.json
(sha256, seam metric, UE import hints). Verify re-opens every PNG from disk:
PNG magic, exact size, seam metric. Exit 1 on any failure.

Run:
  hython Tools/Houdini/copernicus/copernicus_wool_variants.py --surface all
  hython Tools/Houdini/copernicus/copernicus_wool_variants.py --surface WoolCable \
      --size 2048 --out <dir>
"""
from __future__ import annotations

import argparse
import hashlib
import json
import sys
from pathlib import Path

import numpy as np
from PIL import Image

# Shared tileable primitives + assemble/verify from the film tilables script.
# Import is safe: that module only defines under __main__.
from copernicus_film_tilables import (
    MAPS,
    SEED,
    UE_IMPORT_HINTS,
    _fbm,
    _to_u8,
    _worley,
    assemble,
    seam_metric,
    verify_png,
)

DEFAULT_OUT = Path(__file__).resolve().parents[3] / "Saved" / "GeneratedTextures" / "Copernicus"


# ---------- wool surface builders ----------

def build_wool_knit(size: int, rng: np.random.Generator) -> dict:
    """Stockinette V-stitch columns - undyed oatmeal cream."""
    st_w = size // 32  # 64 px stitches @2048
    st_h = size // 64  # 32 px rows
    y = np.arange(size, dtype=np.float32)[:, None]
    x = np.arange(size, dtype=np.float32)[None, :]
    cx = (x % st_w) / st_w  # 0..1 within stitch
    cy = (y % st_h) / st_h  # 0..1 within row, 0 = row top
    # two yarn legs from the top corners converging at bottom-centre = the V
    leg_l = np.abs(cx - (0.5 - 0.5 * (1.0 - cy)))
    leg_r = np.abs(cx - (0.5 + 0.5 * (1.0 - cy)))
    w = 0.20
    ridge = np.maximum(
        np.clip(1.0 - leg_l / w, 0.0, 1.0) ** 0.8,
        np.clip(1.0 - leg_r / w, 0.0, 1.0) ** 0.8,
    )
    # loop head along the row boundary, only where the V does not cover
    dc = np.minimum(cy, 1.0 - cy)
    head = np.clip(1.0 - dc / 0.14, 0.0, 1.0) * (1.0 - ridge) * 0.75
    relief = np.maximum(ridge, head)
    # subtle 2-ply twist along the yarn (integer periods -> still tileable)
    twist = 0.92 + 0.10 * np.sin(2.0 * np.pi * (2.0 * cy + cx))
    fuzz = _fbm(size, 64, 64, 2, rng)
    heather = _fbm(size, 10, 10, 3, rng)
    height = 0.34 + 0.42 * relief * twist + 0.14 * fuzz
    height = np.clip(height, 0.0, 1.0)
    base = np.array([0.76, 0.70, 0.60], np.float32)  # oatmeal cream
    tint = (0.88 + 0.24 * heather)[..., None]
    color = base[None, None, :] * tint + 0.05 * (fuzz - 0.5)[..., None]
    color *= (0.82 + 0.18 * relief)[..., None]  # groove definition for toon read
    rough = 0.96 - 0.06 * relief
    return dict(color=np.clip(color, 0, 1), height=height, rough=np.clip(rough, 0, 1),
                metal=np.zeros_like(height))


def build_wool_cable(size: int, rng: np.random.Generator) -> dict:
    """3-strand twisted cable columns - warm honey amber, purl background."""
    col_w = size // 8
    period = size // 4  # full twists per period, integer -> exact wrap
    y = np.arange(size, dtype=np.float32)[:, None]
    x = np.arange(size, dtype=np.float32)[None, :]
    u = (x % col_w) / col_w - 0.5  # -0.5..0.5 within column
    cy = y / period
    ridge = np.zeros((size, size), np.float32)
    for i in range(3):
        path = 0.30 * np.sin(2.0 * np.pi * (cy + i / 3.0))
        ridge = np.maximum(ridge, np.clip(1.0 - np.abs(u - path) / 0.16, 0.0, 1.0) ** 0.7)
    gap = 1.0 - np.clip(ridge * 3.0, 0, 1)  # purl field between strands/columns
    purl = _fbm(size, 48, 48, 3, rng)
    fuzz = _fbm(size, 64, 64, 2, rng)
    height = 0.30 + 0.46 * ridge + 0.16 * purl * gap + 0.10 * fuzz
    height = np.clip(height, 0.0, 1.0)
    lo = np.array([0.55, 0.38, 0.16], np.float32)
    hi = np.array([0.80, 0.62, 0.30], np.float32)
    g = np.clip(0.30 + 0.60 * ridge + 0.20 * (purl - 0.5) + 0.10 * (fuzz - 0.5), 0, 1)
    color = lo[None, None, :] + (hi - lo)[None, None, :] * g[..., None]
    color += (0.05 * ridge)[..., None]  # strands catch light
    rough = 0.94 - 0.05 * ridge
    return dict(color=np.clip(color, 0, 1), height=height, rough=np.clip(rough, 0, 1),
                metal=np.zeros_like(height))


def build_wool_tweed(size: int, rng: np.random.Generator) -> dict:
    """Herringbone twill - sage/ochre Donegal heather with nep flecks."""
    y = np.arange(size, dtype=np.float32)[:, None]
    x = np.arange(size, dtype=np.float32)[None, :]
    block = size // 8
    sign = 1.0 - 2.0 * (((x // block) + (y // block)) % 2.0)  # +1/-1 per block
    # stripe period 16 px -> full period 32 divides every power-of-two size
    stripe = ((sign * x + y) // 16.0) % 2.0
    tw = max(size // 128, 4)
    over = ((x // tw) + (y // tw)) % 2.0  # plain-weave over/under bump
    heather = _fbm(size, 12, 12, 3, rng)
    macro = _fbm(size, 3, 3, 2, rng)
    fuzz = _fbm(size, 64, 64, 2, rng)
    # Donegal neps: sparse worley dots in clustered patches
    f1, _f2 = _worley(size, cells=64, rng=rng)
    nep = np.clip(1.0 - f1 * 9.0, 0.0, 1.0) ** 1.2
    nep *= np.clip((_fbm(size, 6, 6, 2, rng) - 0.55) * 7.0, 0.0, 1.0)
    hue = _fbm(size, 4, 4, 1, rng)
    nep_rust = np.clip((hue - 0.5) * 4.0, 0, 1)
    nep_col = (np.array([0.85, 0.82, 0.72], np.float32)[None, None, :] * (1 - nep_rust)[..., None]
               + np.array([0.65, 0.30, 0.20], np.float32)[None, None, :] * nep_rust[..., None])
    height = 0.42 + 0.16 * stripe + 0.06 * over + 0.10 * heather + 0.12 * nep + 0.06 * fuzz
    height = np.clip(height, 0.0, 1.0)
    sage = np.array([0.40, 0.46, 0.37], np.float32)
    ochre = np.array([0.52, 0.44, 0.26], np.float32)
    yarn = sage[None, None, :] * (1 - stripe)[..., None] + ochre[None, None, :] * stripe[..., None]
    t = (0.86 + 0.28 * heather + 0.10 * (macro - 0.5))[..., None]
    color = yarn * t + 0.04 * (fuzz - 0.5)[..., None]
    m = np.clip(nep * 1.4, 0, 1)[..., None]
    color = color * (1.0 - m) + nep_col * m
    rough = 0.92 - 0.04 * stripe
    return dict(color=np.clip(color, 0, 1), height=height, rough=np.clip(rough, 0, 1),
                metal=np.zeros_like(height))


def build_wool_felt(size: int, rng: np.random.Generator) -> dict:
    """Matted directional fibres - dusty rose mauve, no weave structure."""
    soft = _fbm(size, 6, 6, 4, rng)
    streak = _fbm(size, 160, 24, 2, rng)  # horizontal matted fibres
    fine = _fbm(size, 96, 96, 2, rng)
    height = 0.50 + 0.16 * soft + 0.14 * streak + 0.10 * fine
    height = np.clip(height, 0.0, 1.0)
    lo = np.array([0.55, 0.38, 0.40], np.float32)
    hi = np.array([0.72, 0.52, 0.54], np.float32)
    g = np.clip(0.40 + 0.50 * soft + 0.30 * (streak - 0.5), 0, 1)
    color = lo[None, None, :] + (hi - lo)[None, None, :] * g[..., None]
    color += (0.05 * (fine - 0.5))[..., None]
    rough = 0.98 - 0.03 * streak
    return dict(color=np.clip(color, 0, 1), height=height, rough=np.clip(rough, 0, 1),
                metal=np.zeros_like(height))


def build_wool_boucle(size: int, rng: np.random.Generator) -> dict:
    """Dense loop nubs - ecru off-white (two overlapping Worley loop lattices)."""
    f1a, _ = _worley(size, cells=40, rng=rng)
    f1b, _ = _worley(size, cells=40, rng=rng)  # second lattice, independent draw
    ring_a = np.clip(1.0 - np.abs(f1a - 0.18) * 6.0, 0.0, 1.0) ** 1.1  # ring = yarn loop
    ring_b = np.clip(1.0 - np.abs(f1b - 0.15) * 6.5, 0.0, 1.0) ** 1.1
    loop = np.maximum(ring_a, ring_b * 0.9)
    core = np.clip(1.0 - f1a * 5.0, 0.0, 1.0) * 0.8
    fuzz = _fbm(size, 64, 64, 2, rng)
    patch = _fbm(size, 6, 6, 3, rng)
    height = 0.36 + 0.36 * loop + 0.16 * core + 0.14 * fuzz  # fuzz lifts the ground too
    height = np.clip(height, 0.0, 1.0)
    base = np.array([0.86, 0.81, 0.72], np.float32)  # ecru
    g = np.clip(0.90 + 0.24 * loop + 0.10 * (patch - 0.5) + 0.08 * (fuzz - 0.5), 0, 1)
    color = base[None, None, :] * g[..., None]
    color *= (0.94 + 0.06 * np.clip(loop + core, 0, 1))[..., None]  # gentle gap shadow
    rough = 0.95 - 0.05 * loop
    return dict(color=np.clip(color, 0, 1), height=height, rough=np.clip(rough, 0, 1),
                metal=np.zeros_like(height))


SURFACES = {
    "WoolKnit": build_wool_knit,
    "WoolCable": build_wool_cable,
    "WoolTweed": build_wool_tweed,
    "WoolFelt": build_wool_felt,
    "WoolBoucle": build_wool_boucle,
}


def main() -> int:
    ap = argparse.ArgumentParser(description="2K tileable wool variants + ORM (Copernicus lane)")
    ap.add_argument("--surface", default="all", choices=list(SURFACES) + ["all"])
    ap.add_argument("--size", type=int, default=2048)
    ap.add_argument("--seed", type=int, default=SEED)
    ap.add_argument("--out", type=str, default=str(DEFAULT_OUT))
    args = ap.parse_args()

    size = args.size
    if size < 256 or size & (size - 1):
        print(f"[WOOL] size must be a power of two >= 256, got {size}")
        return 1
    out_dir = Path(args.out)
    out_dir.mkdir(parents=True, exist_ok=True)
    names = list(SURFACES) if args.surface == "all" else [args.surface]

    results, ok_all = [], True
    for i, name in enumerate(names):
        rng = np.random.default_rng(args.seed + i * 1009)
        maps = assemble(SURFACES[name](size, rng))
        for map_name in MAPS:
            path = out_dir / f"T_{name}_{map_name}.png"
            Image.fromarray(maps[map_name]).save(str(path))
            v = verify_png(path, size)
            v["surface"] = name
            v["map"] = map_name
            results.append(v)
            ok_all = ok_all and v["ok"]
            print(f"[WOOL] {path.name} {v['w']}x{v['h']} "
                  f"seam_ratio={v['seam']['ratio']} ok={v['ok']}")

    manifest = {
        "generator": "Tools/Houdini/copernicus/copernicus_wool_variants.py",
        "seed": args.seed, "size": size, "surfaces": names,
        "license": "Houdini 22.0.368 Apprentice - COP rop writes capped at 1920x1080; "
                   "2K maps use the lane's numpy+PIL path (cymatic precedent)",
        "orm_pack": "R=AO G=Roughness B=Metallic",
        "ue_import_hints": UE_IMPORT_HINTS,
        "out_dir": str(out_dir),
        "files": results, "ok": ok_all,
    }
    mpath = out_dir / "copernicus_wool_variants_manifest.json"
    mpath.write_text(json.dumps(manifest, indent=2), encoding="utf-8")
    print(f"[WOOL] wrote {mpath} files={len(results)} ok={ok_all}")
    return 0 if ok_all else 1


if __name__ == "__main__":
    sys.exit(main())
