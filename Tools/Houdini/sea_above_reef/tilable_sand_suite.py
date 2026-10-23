"""Tilable sand material suite + caustics for LV_SeaAbove_Prototype.

Outputs (Saved/Audit/sea_above/houdini_variants/):
  T_SeaAbove_Sand_Albedo.png    (sRGB colour)
  T_SeaAbove_Sand_Height.png    (data)
  T_SeaAbove_Sand_Normal.png    (data, OpenGL Y+)
  T_SeaAbove_Sand_WetMask.png   (data)
  T_SeaAbove_Sand_RippleMask.png(data)
  T_SeaAbove_Caustics.png       (data; pan/blend two copies in material)

Everything is lattice-periodic -> seam-free tiling; the ingest script measures the
seam metric to prove it. Deterministic under SEED; call order is part of the seed
contract.

Run:
  python Tools/Houdini/sea_above_reef/tilable_sand_suite.py
  blender --background --python Tools/Houdini/sea_above_reef/tilable_sand_suite.py
"""

import argparse
import sys
from pathlib import Path

import numpy as np

sys.path.insert(0, str(Path(__file__).resolve().parent))
import reef_common as rc  # noqa: E402

SIZE = 1024
SEED = 20260828

# sRGB-space palette (authored dreamy sea-sand, dusty Nikki-adjacent):
PAL_BASE = np.array([228, 216, 196], np.float32) / 255.0   # warm ivory
PAL_WET = np.array([122, 158, 158], np.float32) / 255.0    # cool aquamarine shadow
PAL_SPECK = np.array([246, 240, 226], np.float32) / 255.0  # shell-hash brights


def build(seed, size):
    rng = np.random.default_rng(seed)

    # --- macro dunes + medium undulation + fine grain (all periodic) ----------
    dunes = rc.fbm(size, 8, 4, rng, gain=0.55)
    medium = rc.fbm(size, 32, 3, rng, gain=0.5)
    grain = rc.fbm(size, 128, 2, rng, gain=0.6)
    grain2 = rc.fbm(size, 256, 1, rng, gain=0.5)

    # --- ripple field: integer-frequency diagonal sine, warped by medium ------
    ripple_src = rc.tileable_sine(size, 6, 10, phase=0.7, warp=medium, warp_amp=0.55)
    # sharpen into ripple crests
    ripple = np.clip((ripple_src - 0.35) / 0.65, 0.0, 1.0) ** 1.6

    # --- height: dunes dominate, ripples carve, grain textures the surface ---
    height = (
        0.52 * dunes
        + 0.28 * medium
        + 0.12 * ripple
        + 0.05 * grain
        + 0.03 * grain2
    )
    height = (height - height.min()) / (height.max() - height.min())

    # --- wet mask: low-frequency pooling (smooth, non-grainy) -----------------
    wet = rc.fbm(size, 4, 3, np.random.default_rng(seed + 1), gain=0.5)
    wet = np.clip((wet - 0.52) / 0.30, 0.0, 1.0)  # only the lowest areas stay wet
    wet = wet ** 1.3

    # --- albedo ---------------------------------------------------------------
    crest = (height - 0.5) * 0.5  # -0.25 .. +0.25
    albedo = PAL_BASE[None, None, :] * (1.0 + crest)[..., None]
    # wet zones: darken + cool tint
    albedo = albedo * (1.0 - 0.38 * wet[..., None]) + PAL_WET[None, None, :] * (0.38 * wet[..., None])
    # shell-hash specks: bright warm flecks from thresholded fine noise
    speck = np.clip((grain2 - 0.84) / 0.16, 0.0, 1.0)
    speck *= (1.0 - wet)  # no bright flecks inside wet pools
    albedo = albedo * (1.0 - 0.55 * speck[..., None]) + PAL_SPECK[None, None, :] * (0.55 * speck[..., None])
    # subtle ripple shading
    albedo *= (1.0 + (ripple - 0.5)[..., None] * 0.06)
    albedo = np.clip(albedo, 0.0, 1.0)

    # --- caustics: two scales of wrapped Voronoi edges ------------------------
    f1a = rc.periodic_voronoi_f1(size, 8, 0.85, np.random.default_rng(seed + 2))
    f1b = rc.periodic_voronoi_f1(size, 32, 0.85, np.random.default_rng(seed + 3))
    edge_a = np.clip(1.0 - f1a * 3.2, 0.0, 1.0) ** 2.0
    edge_b = np.clip(1.0 - f1b * 3.6, 0.0, 1.0) ** 2.2
    caustics = np.clip(edge_a * 0.72 + edge_b * 0.55, 0.0, 1.0) ** 1.25

    return {
        "T_SeaAbove_Sand_Albedo": (albedo, "rgb"),
        "T_SeaAbove_Sand_Height": (height, "gray"),
        "T_SeaAbove_Sand_Normal": (rc.normal_from_height(height, strength=2.4), "rgb"),
        "T_SeaAbove_Sand_WetMask": (wet, "gray"),
        "T_SeaAbove_Sand_RippleMask": (ripple, "gray"),
        "T_SeaAbove_Caustics": (caustics, "gray"),
    }


def main():
    out = rc.ensure_out_dir()
    if rc.IS_BLENDER:
        seed, size = SEED, SIZE
    else:
        ap = argparse.ArgumentParser()
        ap.add_argument("--seed", type=int, default=SEED)
        ap.add_argument("--size", type=int, default=SIZE)
        ap.add_argument("--out", default=None)
        args = ap.parse_args()
        seed, size = args.seed, args.size
        if args.out:
            rc.OUT_DIR = Path(args.out)
            out = rc.ensure_out_dir()

    images = build(seed, size)

    files = []
    for name, (arr, kind) in images.items():
        p = rc.save_image(out / f"{name}.png", arr, kind)
        files.append({"name": name, "path": str(p), "kind": kind,
                      "size": int(size), "seed": seed})
        print(f"[sand] wrote {p.name} ({kind} {size}x{size})")

    manifest = rc.write_manifest(
        out / "sand_suite_manifest.json",
        "melodia.sea_above_reef_textures.v1",
        seed,
        {
            "generator": "tilable_sand_suite.py",
            "runtime": "blender-bpy" if rc.IS_BLENDER else "python+PIL",
            "tiling": "lattice-periodic (seam metric via ingest_reef_textures.py)",
            "normal_convention": "OpenGL Y+ (flip Y in UE import if DirectX target)",
            "palette_srgb": {"base": [228, 216, 196], "wet": [122, 158, 158],
                             "speck": [246, 240, 226]},
        },
        files,
    )
    print(f"[sand] manifest -> {manifest}")


if __name__ == "__main__":
    main()
