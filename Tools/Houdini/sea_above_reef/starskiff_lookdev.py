"""Starskiff lookdev textures — rigid hull (lookdev-only; no weight paint).

Convention-faithful to the reef suite style but named for the skiff:
  T_Starskiff_Hull_BaseColor / _Normal / _Roughness, T_Starskiff_Wake_Emission

Design: weathered pale planks (horizontal stripes + grain + salt fade),
barnacle-encrusted waterline band (reuses the R5 barnacle-crust math), brass/
rope trim accent stripes, wake emissive strip (reuses foam-streak math).
Convergence rule: reuses reef_common + proven reef texture math — no new
parallel texture system.

Outputs: Saved/Audit/melusina_lookdev/houdini_variants/ + manifest.
Run:  python Tools/Houdini/sea_above_reef/starskiff_lookdev.py
"""

import argparse
import sys
from pathlib import Path

import numpy as np

sys.path.insert(0, str(Path(__file__).resolve().parent))
import reef_common as rc  # noqa: E402

SIZE = 1024
SEED = 20260828
OUT = rc.PROJECT_ROOT / "Saved" / "Audit" / "melusina_lookdev" / "houdini_variants"

PLANK_PALE = np.array([214, 202, 178], np.float32) / 255.0
PLANK_DARK = np.array([150, 132, 106], np.float32) / 255.0
BRASS = np.array([184, 150, 88], np.float32) / 255.0
BARNACLE = np.array([226, 222, 210], np.float32) / 255.0


def build(seed, size):
    rng = np.random.default_rng(seed)
    ys, xs = np.mgrid[0:size, 0:size].astype(np.float32)
    v = ys / size  # 0 = keel? convention: v=1 waterline band at BOTTOM

    # planks: horizontal bands with per-plank value variation (14 planks = 1 loop)
    plank_freq = 14
    plank_row = np.floor(v * plank_freq).astype(np.int32) % plank_freq
    pv1d = np.random.default_rng(seed + 1).random(plank_freq).astype(np.float32)
    plank_val = pv1d[plank_row]
    grain_warp = rc.fbm(size, 64, 2, rng, gain=0.55)
    grain = rc.tileable_sine(size, 2, 160, phase=0.3, warp=grain_warp, warp_amp=0.5)

    # weathering + salt fade (big soft patches)
    fade = rc.fbm(size, 8, 4, rng, gain=0.5)

    hull = PLANK_PALE[None, None, :] * (1.0 - plank_val[..., None] * 0.5) \
        + PLANK_DARK[None, None, :] * (plank_val[..., None] * 0.5)
    hull *= (1.0 + (grain - 0.5)[..., None] * 0.22)
    hull *= (1.0 + (fade - 0.5)[..., None] * 0.24)

    # barnacle crust band near waterline (bottom ~18%)
    band = np.clip((v - 0.80) / 0.20, 0, 1) ** 1.2
    f1 = rc.periodic_voronoi_f1(size, 64, 0.85, np.random.default_rng(seed + 2))
    crust = np.clip(1.0 - f1 * 3.0, 0, 1) ** 1.3 * band
    hull = hull * (1.0 - 0.55 * crust[..., None]) + BARNACLE[None, None, :] * (0.55 * crust[..., None])

    # brass trim stripes (two horizontal lines)
    trim = np.exp(-((v - 0.22) / 0.008) ** 2) + np.exp(-((v - 0.62) / 0.008) ** 2)
    hull = hull * (1.0 - np.clip(trim, 0, 1)[..., None] * 0.6) \
        + BRASS[None, None, :] * (np.clip(trim, 0, 1)[..., None] * 0.6)
    albedo = np.clip(hull, 0, 1)

    # height: plank grooves (dark seams) + grain + crust bumps
    seam = np.abs(((v * plank_freq) % 1.0) - 0.5) * 2.0     # 0 at seam
    height = 0.45 * seam + 0.30 * grain + 0.25 * crust
    normal = rc.normal_from_height(height, strength=3.0)

    # roughness: weathered wood high, crust lower/rougher-sheen mix, brass smooth
    rough = np.clip(0.78 - 0.20 * crust[..., None] - 0.35 * np.clip(trim, 0, 1)[..., None]
                    + 0.08 * (fade - 0.5)[..., None], 0.1, 1.0)

    # wake emissive strip: bright foam lines for the waterline band (static)
    streak_warp = rc.fbm(size, 32, 3, np.random.default_rng(seed + 3), gain=0.5)
    streaks = rc.tileable_sine(size, 4, 26, phase=0.9, warp=streak_warp, warp_amp=0.8)
    wake = np.clip((streaks - 0.52) / 0.48, 0, 1) ** 1.4 * band
    wake = np.clip(wake * 1.3 - 0.15, 0, 1) ** 1.2

    return {
        "T_Starskiff_Hull_BaseColor": (albedo, "rgb"),
        "T_Starskiff_Hull_Normal": (normal, "rgb"),
        "T_Starskiff_Hull_Roughness": (np.clip(rough[..., 0], 0, 1), "gray"),
        "T_Starskiff_Wake_Emission": (wake, "gray"),
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
                      "size": int(args.size), "seed": args.seed})
        print(f"[skiff] wrote {p.name}")

    manifest = rc.write_manifest(
        OUT / "starskiff_lookdev_manifest.json",
        "melodia.melusina_lookdev_textures.v1",
        args.seed,
        {
            "generator": "starskiff_lookdev.py",
            "runtime": "python+PIL",
            "asset": "Starskiff (rigid hull - lookdev only, no weight paint)",
            "reuses": "BarnacleCrust/WetRock/Foam math from the reef suite (convergence)",
            "wake_emission": "STATIC strip; v=1 bottom band = waterline",
        },
        files,
    )
    print(f"[skiff] manifest -> {manifest}")


if __name__ == "__main__":
    main()
