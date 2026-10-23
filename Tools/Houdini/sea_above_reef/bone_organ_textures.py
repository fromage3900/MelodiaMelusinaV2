"""Bone + organ-pipe textures for the Leviathan and the Drowned Organ.

  T_Leviathan_Bone_BaseColor / _Normal / _Roughness   (tilable, eroded bone:
      pale base, sediment staining, thin cracks, barnacle clusters)
  T_Organ_Pipe_BaseColor / _Normal / _Emissive        (tilable, vertical brushed
      brass with green patina streaks; emissive = soft vertical glow streaks —
      mouths get their extra boost from uv.y in the material recipe)

Outputs: Saved/Audit/sea_above/houdini_variants/ + manifest.
Run:  python Tools/Houdini/sea_above_reef/bone_organ_textures.py
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

BONE = np.array([226, 219, 199], np.float32) / 255.0
STAIN = np.array([126, 112, 92], np.float32) / 255.0
BRASS = np.array([186, 152, 92], np.float32) / 255.0
PATINA = np.array([96, 142, 122], np.float32) / 255.0


def bone_suite(seed, size):
    rng = np.random.default_rng(seed)
    # sediment staining (large soft blotches)
    stain = rc.fbm(size, 8, 4, rng, gain=0.55)
    stain = np.clip((stain - 0.42) / 0.35, 0, 1) ** 1.2
    # cracks: sharpened ridge noise
    ridge_src = rc.fbm(size, 32, 3, rng, gain=0.5)
    cracks = np.clip(1.0 - np.abs(ridge_src - 0.5) * 9.0, 0, 1) ** 2.0
    # barnacle clusters (reuse crust math)
    f1 = rc.periodic_voronoi_f1(size, 64, 0.85, np.random.default_rng(seed + 1))
    barn = np.clip(1.0 - f1 * 3.4, 0, 1) ** 1.6
    barn *= (0.3 + 0.7 * np.clip((stain - 0.3) / 0.7, 0, 1))   # barnacles like stains

    albedo = BONE[None, None, :] * (1.0 - 0.55 * stain[..., None]) \
        + STAIN[None, None, :] * (0.55 * stain[..., None])
    albedo *= (1.0 - 0.35 * cracks[..., None])
    albedo = albedo * (1.0 - 0.45 * barn[..., None]) \
        + np.array([0.90, 0.89, 0.84], np.float32)[None, None, :] * (0.45 * barn[..., None])
    albedo = np.clip(albedo, 0, 1)

    height = 0.5 * (1.0 - cracks) + 0.3 * barn + 0.2 * stain
    normal = rc.normal_from_height(height, strength=2.2)
    rough = np.clip(0.72 + 0.16 * stain[..., None] - 0.22 * barn[..., None]
                    + 0.08 * (cracks[..., None] - 0.5), 0.25, 1.0)
    return {
        "T_Leviathan_Bone_BaseColor": (albedo, "rgb"),
        "T_Leviathan_Bone_Normal": (normal, "rgb"),
        "T_Leviathan_Bone_Roughness": (np.clip(rough[..., 0], 0, 1), "gray"),
    }


def organ_suite(seed, size):
    rng = np.random.default_rng(seed)
    # vertical brushed metal: high-frequency vertical streaks
    brush_warp = rc.fbm(size, 32, 2, rng, gain=0.5)
    brush = rc.tileable_sine(size, 180, 3, phase=0.2, warp=brush_warp, warp_amp=0.4)
    # patina: soft green blotches, stronger in crevices
    patina = rc.fbm(size, 16, 4, np.random.default_rng(seed + 5), gain=0.55)
    patina = np.clip((patina - 0.45) / 0.35, 0, 1) ** 1.2
    # horizontal seams every 1/8 (pipe sections) — smooth cosine, no cusps
    ys, _xs = np.mgrid[0:size, 0:size].astype(np.float32)
    v = ys / size
    seam = 0.5 - 0.5 * np.cos(2.0 * np.pi * v * 8.0)

    base = BRASS[None, None, :] * (0.85 + 0.15 * brush[..., None])
    base = base * (1.0 - 0.5 * patina[..., None]) + PATINA[None, None, :] * (0.5 * patina[..., None])
    base *= (1.0 - 0.22 * (1.0 - seam)[..., None] * 0.0 + 0.10 * (seam[..., None] - 0.5))
    albedo = np.clip(base, 0, 1)

    height = 0.45 * brush + 0.30 * (1.0 - seam) + 0.25 * patina
    normal = rc.normal_from_height(height, strength=1.8)

    # emissive: soft vertical glow streaks (tilable); mouths boost via uv.y in material
    glow_src = rc.fbm(size, 64, 2, np.random.default_rng(seed + 6), gain=0.6)
    glow = np.clip((glow_src - 0.55) / 0.45, 0, 1) ** 1.5
    emissive = np.clip(glow * 0.6 + 0.4 * brush * glow, 0, 1)

    return {
        "T_Organ_Pipe_BaseColor": (albedo, "rgb"),
        "T_Organ_Pipe_Normal": (normal, "rgb"),
        "T_Organ_Pipe_Emissive": (emissive, "gray"),
    }


def main():
    OUT.mkdir(parents=True, exist_ok=True)
    ap = argparse.ArgumentParser()
    ap.add_argument("--seed", type=int, default=SEED)
    ap.add_argument("--size", type=int, default=SIZE)
    args = ap.parse_args()

    images = {}
    images.update(bone_suite(args.seed, args.size))
    images.update(organ_suite(args.seed, args.size))
    files = []
    for name, (arr, kind) in images.items():
        p = rc.save_image(OUT / f"{name}.png", arr, kind)
        files.append({"name": name, "path": str(p), "kind": kind,
                      "size": args.size, "seed": args.seed})
        print(f"[bone-organ] wrote {p.name}")

    manifest = rc.write_manifest(
        OUT / "bone_organ_manifest.json",
        "melodia.sea_above_reef_textures.v1",
        args.seed,
        {
            "generator": "bone_organ_textures.py",
            "runtime": "python+numpy+PIL",
            "organ_emissive_note": "tilable glow; mouth boost = x smoothstep(0.9,1.0,uv.y) "
                                   "in material; tint by T_SeaAbove_PulseBand_LUT (uv.x band)",
        },
        files,
    )
    print(f"[bone-organ] manifest -> {manifest}")


if __name__ == "__main__":
    main()
