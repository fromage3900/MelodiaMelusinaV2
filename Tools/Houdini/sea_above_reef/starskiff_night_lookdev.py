"""Starskiff NIGHT lookdev — Sea Above night pass (bioluminescent).

Same deterministic structure as the day pass (starskiff_lookdev.py) so the
plank/barnacle/brass design language is preserved, but re-lit for night:
  - deep teal-astral plank palette (reads as moonlit Sea Above water)
  - bioluminescent Worley mottle across the hull (MPC palette teal)
  - brass trim reads warm (catches moon/emissive)
  - wet-slick roughness (lower near waterline)
  - wake emission = foam streaks + STAR MOTES (voronoi points, additive)

Reuses reef_common only — convergence, no new texture system.
Outputs: Saved/Audit/sea_above/houdini_variants/ + manifest (sha256).
Run:  python Tools/Houdini/sea_above_reef/starskiff_night_lookdev.py
"""

import argparse
import sys
from pathlib import Path

import numpy as np

sys.path.insert(0, str(Path(__file__).resolve().parent))
import reef_common as rc  # noqa: E402

SIZE = 1024
SEED = 20260829
OUT = rc.PROJECT_ROOT / "Saved" / "Audit" / "sea_above" / "houdini_variants"

# Night palette (sRGB authored)
PLANK_NIGHT = np.array([32, 46, 58], np.float32) / 255.0     # deep teal plank
PLANK_DARK = np.array([16, 24, 34], np.float32) / 255.0      # shadowed seam-plank
BRASS_NIGHT = np.array([216, 178, 108], np.float32) / 255.0  # warm moonlit brass
BARNACLE = np.array([104, 112, 116], np.float32) / 255.0     # pale crust, low light
BIOLUM = np.array([96, 226, 214], np.float32) / 255.0        # Sea Above teal glow


def build(seed, size):
    rng = np.random.default_rng(seed)
    ys, xs = np.mgrid[0:size, 0:size].astype(np.float32)
    v = ys / size  # v=1 bottom = waterline

    # --- planks: 14-per-loop horizontal bands, per-plank value ---
    plank_freq = 14
    plank_row = np.floor(v * plank_freq).astype(np.int32) % plank_freq
    pv1d = np.random.default_rng(seed + 1).random(plank_freq).astype(np.float32)
    plank_val = pv1d[plank_row]
    grain_warp = rc.fbm(size, 64, 2, rng, gain=0.55)
    grain = rc.tileable_sine(size, 2, 160, phase=0.3, warp=grain_warp, warp_amp=0.5)
    fade = rc.fbm(size, 8, 4, rng, gain=0.5)

    hull = PLANK_NIGHT[None, None, :] * (1.0 - plank_val[..., None] * 0.6) \
        + PLANK_DARK[None, None, :] * (plank_val[..., None] * 0.6)
    hull *= (1.0 + (grain - 0.5)[..., None] * 0.18)
    hull *= (1.0 + (fade - 0.5)[..., None] * 0.22)

    # --- bioluminescent mottle (Worley cells, additive teal) ---
    mottle_f1 = rc.periodic_voronoi_f1(size, 32, 0.8, np.random.default_rng(seed + 4))
    mottle = np.clip((1.0 - mottle_f1 - 0.82) / 0.18, 0, 1) ** 1.6
    hull = hull + BIOLUM[None, None, :] * (mottle[..., None] * 0.35)

    # --- barnacle crust band near waterline (bottom ~18%) ---
    band = np.clip((v - 0.80) / 0.20, 0, 1) ** 1.2
    f1 = rc.periodic_voronoi_f1(size, 64, 0.85, np.random.default_rng(seed + 2))
    crust = np.clip(1.0 - f1 * 3.0, 0, 1) ** 1.3 * band
    hull = hull * (1.0 - 0.50 * crust[..., None]) + BARNACLE[None, None, :] * (0.50 * crust[..., None])

    # --- brass trim stripes (warm; two horizontal lines) ---
    trim = np.exp(-((v - 0.22) / 0.010) ** 2) + np.exp(-((v - 0.62) / 0.010) ** 2)
    trim = np.clip(trim, 0, 1)
    hull = hull * (1.0 - trim[..., None] * 0.75) + BRASS_NIGHT[None, None, :] * (trim[..., None] * 0.75)

    albedo = np.clip(hull, 0, 1)

    # --- height -> normal: plank seams + grain + crust bumps ---
    seam = np.abs(((v * plank_freq) % 1.0) - 0.5) * 2.0
    height = 0.45 * seam + 0.30 * grain + 0.25 * crust
    normal = rc.normal_from_height(height, strength=3.0)

    # --- roughness: wet night (darker/sheener toward waterline) ---
    rough = np.clip(0.72 - 0.25 * crust[..., None] - 0.30 * trim[..., None]
                    - 0.25 * band[..., None] + 0.06 * (fade - 0.5)[..., None], 0.08, 1.0)

    # --- wake emission: foam streaks + STAR MOTES (the glow) ---
    streak_warp = rc.fbm(size, 32, 3, np.random.default_rng(seed + 3), gain=0.5)
    streaks = rc.tileable_sine(size, 4, 26, phase=0.9, warp=streak_warp, warp_amp=0.8)
    wake = np.clip((streaks - 0.52) / 0.48, 0, 1) ** 1.4 * band
    wake = np.clip(wake * 1.3 - 0.15, 0, 1) ** 1.2
    f2 = rc.periodic_voronoi_f1(size, 64, 0.9, np.random.default_rng(seed + 5))
    motes = np.clip(1.0 - f2 * 14.0, 0, 1) ** 2.4 * band
    wake = np.clip(wake + motes * 1.6, 0, 1)
    wake = np.clip(wake * 1.1, 0, 1)

    return {
        "T_Starskiff_Night_BaseColor": (albedo, "rgb"),
        "T_Starskiff_Night_Normal": (normal, "rgb"),
        "T_Starskiff_Night_Roughness": (np.clip(rough[..., 0], 0, 1), "gray"),
        "T_Starskiff_Night_Wake_Emission": (wake, "gray"),
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
                      "size": int(args.size), "seed": args.seed,
                      "sha256": rc.sha256_of(p)})
        print(f"[skiff-night] wrote {p.name}")

    manifest = rc.write_manifest(
        OUT / "starskiff_night_lookdev_manifest.json",
        "melodia.sea_above_night_lookdev_textures.v1",
        args.seed,
        {
            "generator": "starskiff_night_lookdev.py",
            "runtime": "python+PIL",
            "asset": "Starskiff (rigid hull - NIGHT lookdev pass, no weight paint)",
            "day_pass": "starskiff_lookdev.py (same plank/barnacle/brass structure)",
            "reuses": "BarnacleCrust/WetRock/Foam/Voronoi math from the reef suite",
            "bioluminescence": "Worley mottle tinted to MPC_Melodia_Palette teal",
            "wake_emission": "foam streaks + star motes (static; v=1 bottom = waterline)",
        },
        files,
    )
    print(f"[skiff-night] manifest -> {manifest}")


if __name__ == "__main__":
    main()