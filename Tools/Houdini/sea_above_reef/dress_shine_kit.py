"""Shorewake shine kit — iridescent scale-shimmer overlay for the dress.

Two tilable maps that turn the Shorewake dress into leviathan-legacy couture
when layered in the UE material (recipe in Reef/IMPORT_QUEUE.md):

  T_DressShorewake_ScaleShimmer  RGB  - hex scale plates, each carrying a
      spectral gradient (hue drifts across the garment); used as an
      overlay/lerp layer with intensity driven by Nikki morph weight
  T_DressShorewake_ScaleMask     gray - scale coverage mask (plates vs cloth)

Deterministic (seed 20260828). Outputs to the reef audit dir + manifest.
Run:  python Tools/Houdini/sea_above_reef/dress_shine_kit.py
"""

import argparse
import sys
from pathlib import Path

import numpy as np

sys.path.insert(0, str(Path(__file__).resolve().parent))
import reef_common as rc  # noqa: E402

SIZE = 1024
SEED = 20260828
OUT = rc.PROJECT_ROOT / "Saved" / "Audit" / "sea_above" / "houdini_variants"


def spectral(ph, pastel):
    ph = np.asarray(ph, np.float32) % 1.0
    r = 0.5 + 0.5 * np.sin(2 * np.pi * ph)
    g = 0.5 + 0.5 * np.sin(2 * np.pi * (ph + 0.33))
    b = 0.5 + 0.5 * np.sin(2 * np.pi * (ph + 0.67))
    rgb = np.stack([r, g, b], axis=-1)
    return rgb * (1.0 - pastel) + pastel


def build(seed, size):
    ys, xs = np.mgrid[0:size, 0:size].astype(np.float32)
    u, v = xs / size, ys / size

    # hex-scale grid, TOROIDAL in both axes (rows wrap via min(|d|, 1-|d|))
    rows, cols = 22, 16
    cell_h, cell_w = 1.0 / rows, 1.0 / cols
    best = np.full((size, size), 9.9, np.float32)
    hue_grid = np.zeros((size, size), np.float32)
    for row in range(rows):
        y0 = (row + 0.5) / rows
        dy = np.abs(v - y0)
        dy = np.minimum(dy, 1.0 - dy)                 # wrap V
        off = cell_w * 0.5 if row % 2 else 0.0
        ci_base = np.floor((u - off) * cols + 0.5).astype(np.int32)
        for dc in (-1, 0, 1):                         # consider wrapped neighbours
            ci = (ci_base + dc) % cols
            x0 = ((ci + 0.5) / cols + off) % 1.0
            dx = np.abs(u - x0)
            dx = np.minimum(dx, 1.0 - dx)             # wrap U
            d = np.sqrt((dx / (cell_w * 1.35)) ** 2 + (dy / (cell_h * 1.35)) ** 2)
            upd = d < best
            hue = ((ci / cols) * 0.9 + row * 0.022) % 1.0
            hue_grid = np.where(upd, hue, hue_grid)
            best = np.where(upd, d, best)

    # plate shading: soft dome + dark rim separation
    dome = np.clip(1.0 - best * 2.2, 0, 1) ** 0.8
    rim = np.clip(1.0 - best * 1.15, 0, 1) - dome
    coverage = np.clip(1.0 - best * 1.05, 0, 1)          # scale vs cloth mask

    # spectral shimmer across each plate + slow global drift
    spec = spectral(hue_grid + 0.06 * np.sin(v * 12.0), pastel=0.30)
    shimmer_rgb = spec * (0.55 + 0.45 * dome[..., None])
    shimmer_rgb = np.clip(shimmer_rgb + rim[..., None] * 0.25, 0, 1)

    # glitter: sparse bright specks inside plates
    g1 = rc.periodic_voronoi_f1(size, 128, 0.9, np.random.default_rng(seed + 3))
    glint = np.clip(1.0 - g1 * 6.0, 0, 1) ** 2.4 * coverage
    shimmer_rgb = np.clip(shimmer_rgb + glint[..., None] * 0.55, 0, 1)

    mask = np.clip(coverage * 0.85 + glint * 0.3, 0, 1)
    return {
        "T_DressShorewake_ScaleShimmer": (shimmer_rgb, "rgb"),
        "T_DressShorewake_ScaleMask": (mask, "gray"),
    }


def main():
    OUT.mkdir(parents=True, exist_ok=True)
    ap = argparse.ArgumentParser()
    ap.add_argument("--seed", type=int, default=SEED)
    ap.add_argument("--size", type=int, default=SIZE)
    args = ap.parse_args()

    images = build(args.seed, args.size)
    files = []
    for name, (arr, kind) in images.items():
        p = rc.save_image(OUT / f"{name}.png", arr, kind)
        files.append({"name": name, "path": str(p), "kind": kind,
                      "size": args.size, "seed": args.seed})
        print(f"[shine] wrote {p.name}")

    manifest = rc.write_manifest(
        OUT / "dress_shine_kit_manifest.json",
        "melodia.sea_above_reef_textures.v1",
        args.seed,
        {
            "generator": "dress_shine_kit.py",
            "runtime": "python+numpy+PIL",
            "usage": "overlay layer: Lerp(cloth, ScaleShimmer, ScaleMask * "
                     "NikkiMorphWeight); hue drifts across plates; glints "
                     "from T_Jelly_Nematocyst_Glints also available",
            "tiling": "hex lattice periodic (2-axis wrap verified by ingest)",
        },
        files,
    )
    print(f"[shine] manifest -> {manifest}")


if __name__ == "__main__":
    main()
