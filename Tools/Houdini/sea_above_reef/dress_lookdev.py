"""Shorewake dress lookdev textures (Cos_ShorewakeDress) — fitted cloth set.

Convention: T_MelusinaC_DressShorewake_{BaseColor,Normal,Emission,Roughness}
(matches the Melusina clothes convention T_MelusinaC_<piece>_<Map> from
Docs/Plans/MELUSINA_ANIM_NEXT_LEVEL_AND_OUTFIT_CORE_2026-08-16.md Phase A2).

Design: seafoam-to-deep-teal vertical gradient, foam crest streaks concentrated
near the hem (bottom ~20%), Worley silk mottle at 12%, wet-silk roughness ramp.
Authored so it works fitted OR tiled; the emissive is STATIC (the dress binds no
MPC writer — pulse reactivity stays a Sea Above director exclusivity).

Outputs: Saved/Audit/melusina_lookdev/houdini_variants/ + manifest.
Run:  python Tools/Houdini/sea_above_reef/dress_lookdev.py
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

SEAFOAM = np.array([168, 216, 206], np.float32) / 255.0
DEEP_TEAL = np.array([24, 74, 88], np.float32) / 255.0
SILK_SHINE = np.array([214, 240, 232], np.float32) / 255.0


def build(seed, size):
    rng = np.random.default_rng(seed)
    ys, _xs = np.mgrid[0:size, 0:size].astype(np.float32)
    prof = ys[:, 0] / size                       # 1D vertical profile: 0 = top, 1 = hem
    grad = prof[:, None, None]                   # broadcasts over (size, size, 3)

    # silk mottle (Worley-ish via wrapped voronoi, low contrast)
    f1 = rc.periodic_voronoi_f1(size, 32, 0.85, np.random.default_rng(seed + 1))
    mottle = np.clip(1.0 - f1 * 2.2, 0, 1) ** 1.4
    # silk fold structure: vertical wavy folds (normal + base shading)
    folds_warp = rc.fbm(size, 16, 3, rng, gain=0.5)
    folds = rc.tileable_sine(size, 9, 2, phase=1.1, warp=folds_warp, warp_amp=1.2)

    # base: seafoam (top) -> deep teal (hem)
    base = SEAFOAM[None, None, :] * (1.0 - grad) + DEEP_TEAL[None, None, :] * grad
    base = np.broadcast_to(base, (size, size, 3)).copy()   # materialize full width
    base *= (1.0 + (folds - 0.5)[..., None] * 0.16)          # fold shading
    base *= (1.0 + (mottle - 0.5)[..., None] * 0.10)         # silk mottle

    # foam crest streaks near hem: horizontal streaks, vertical falloff
    streak_warp = rc.fbm(size, 32, 3, rng, gain=0.5)
    streaks = rc.tileable_sine(size, 3, 22, phase=0.4, warp=streak_warp, warp_amp=0.9)
    hem_band = np.clip((prof - 0.72) / 0.28, 0, 1) ** 1.3    # bottom 28%
    crest = np.clip((streaks - 0.55) / 0.45, 0, 1) ** 1.5 * hem_band[:, None]

    albedo = np.clip(base + SILK_SHINE[None, None, :] * (crest[..., None] * 0.85), 0, 1)

    # height -> normal: folds + crest ridges
    height = 0.5 * folds + 0.35 * crest + 0.15 * mottle
    normal = rc.normal_from_height(height, strength=2.8)

    # emission: foam lines only (static glow)
    emission = np.clip(crest * 1.25 - 0.18, 0, 1) ** 1.2

    # roughness: wet silk — smooth at hem/foam, satin above
    rough = np.clip(0.62 - 0.28 * hem_band[:, None] - 0.18 * crest
                    + 0.10 * (mottle - 0.5), 0.05, 1.0)
    return {
        "T_MelusinaC_DressShorewake_BaseColor": (albedo, "rgb"),
        "T_MelusinaC_DressShorewake_Normal": (normal, "rgb"),
        "T_MelusinaC_DressShorewake_Emission": (emission, "gray"),
        "T_MelusinaC_DressShorewake_Roughness": (rough, "gray"),
    }


def main():
    OUT.mkdir(parents=True, exist_ok=True)
    seed, size = SEED, SIZE
    ap = argparse.ArgumentParser()
    ap.add_argument("--seed", type=int, default=SEED)
    ap.add_argument("--size", type=int, default=SIZE)
    args = ap.parse_args()
    seed, size = args.seed, args.size

    images = build(seed, size)
    files = []
    for name, (arr, kind) in images.items():
        p = rc.save_image(OUT / f"{name}.png", arr, kind)
        files.append({"name": name, "path": str(p), "kind": kind,
                      "size": int(size), "seed": seed})
        print(f"[dress] wrote {p.name}")

    manifest = rc.write_manifest(
        OUT / "dress_shorewake_manifest.json",
        "melodia.melusina_lookdev_textures.v1",
        seed,
        {
            "generator": "dress_lookdev.py",
            "runtime": "python+PIL",
            "cosmetic": "Cos_ShorewakeDress",
            "convention": "T_MelusinaC_<piece>_<Map> (Phase A2 authority)",
            "binding": "MI instance layer only; melusina_v2_material_map.json is the "
                       "approved map; M_Master_Toon_Universal never edited",
            "emission": "STATIC (no MPC writer)",
            "fitted_or_tiled": "works either; hem = texture bottom (v=1)",
        },
        files,
    )
    print(f"[dress] manifest -> {manifest}")


if __name__ == "__main__":
    main()
