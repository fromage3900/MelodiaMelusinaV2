"""Coral skin textures — tilable albedo / normal / emissive-pore mask.

Feeds the R1 coral meshes (SM_Coral_*): albedo is tint-neutral pastel rose→
lavender patches (per-pitch-class tint happens in the MI), the emissive mask
glows at pore centres and is scaled by User.SeaAbovePulse in the material.

Outputs (Saved/Audit/sea_above/houdini_variants/):
  T_SeaAbove_CoralSkin_Albedo.png     sRGB colour
  T_SeaAbove_CoralSkin_Normal.png     data, OpenGL Y+
  T_SeaAbove_CoralSkin_EmissiveMask.png  data (pore glow)
  _CoralSkin_ContactSheet.png

Run:  python Tools/Houdini/sea_above_reef/coral_textures.py
"""

import argparse
import sys
from pathlib import Path

import numpy as np

sys.path.insert(0, str(Path(__file__).resolve().parent))
import reef_common as rc  # noqa: E402

SIZE = 1024
SEED = 20260828

PALE_ROSE = np.array([233, 199, 199], np.float32) / 255.0
PALE_LAVENDER = np.array([201, 190, 227], np.float32) / 255.0
CREVICE = np.array([120, 96, 118], np.float32) / 255.0


def build(seed, size):
    rng = np.random.default_rng(seed)
    # pastel patch blend
    patches = rc.fbm(size, 8, 4, rng, gain=0.55)
    patches = (patches - patches.min()) / (patches.max() - patches.min())
    # skin bump height + pore dots at jittered Voronoi centres
    bump = rc.fbm(size, 64, 2, rng, gain=0.6)
    f1 = rc.periodic_voronoi_f1(size, 128, 0.8, np.random.default_rng(seed + 4))
    pore = np.clip(1.0 - f1 * 5.5, 0.0, 1.0) ** 1.6          # dot at cell centre
    rim = np.clip(1.0 - f1 * 1.4, 0.0, 1.0) ** 3.0 - pore     # rim ring around pore
    height = np.clip(0.55 * bump + 0.30 * pore + 0.15 * patches, 0, 1)
    # albedo: patch blend, crest lightening, pore rim darkening
    albedo = PALE_ROSE[None, None, :] * (1.0 - patches[..., None]) \
        + PALE_LAVENDER[None, None, :] * patches[..., None]
    albedo *= (1.0 + (height - 0.5)[..., None] * 0.18)
    albedo = albedo * (1.0 - 0.45 * np.clip(rim, 0, 1)[..., None]) \
        + CREVICE[None, None, :] * (0.45 * np.clip(rim, 0, 1)[..., None])
    albedo = np.clip(albedo, 0.0, 1.0)
    # emissive: pore centres glow (data map; material scales by SeaAbovePulse)
    emissive = np.clip(pore * 1.15 - 0.15, 0.0, 1.0) ** 1.3
    return {
        "T_SeaAbove_CoralSkin_Albedo": (albedo, "rgb"),
        "T_SeaAbove_CoralSkin_Normal": (rc.normal_from_height(height, strength=3.2), "rgb"),
        "T_SeaAbove_CoralSkin_EmissiveMask": (emissive, "gray"),
    }


def main():
    out = rc.ensure_out_dir()
    seed, size = SEED, SIZE
    if not rc.IS_BLENDER:
        ap = argparse.ArgumentParser()
        ap.add_argument("--seed", type=int, default=SEED)
        ap.add_argument("--size", type=int, default=SIZE)
        args = ap.parse_args()
        seed, size = args.seed, args.size

    images = build(seed, size)
    files = []
    for name, (arr, kind) in images.items():
        p = rc.save_image(out / f"{name}.png", arr, kind)
        files.append({"name": name, "path": str(p), "kind": kind,
                      "size": int(size), "seed": seed})
        print(f"[coral-tex] wrote {p.name}")

    # contact sheet
    from PIL import Image
    sheet = Image.new("RGB", (size * 3, size), (30, 34, 38))
    for i, (name, (arr, kind)) in enumerate(images.items()):
        a = np.clip(arr, 0, 1)
        if kind == "gray":
            rgb = np.dstack([a, a, a])
        else:
            rgb = a[..., :3]
        sheet.paste(Image.fromarray((rgb * 255).round().astype(np.uint8), "RGB"), (i * size, 0))
    sheet_path = out / "_CoralSkin_ContactSheet.png"
    sheet.save(str(sheet_path), format="PNG")
    files.append({"name": sheet_path.stem, "path": str(sheet_path),
                  "kind": "contact_sheet", "size": size, "seed": seed})
    print(f"[coral-tex] wrote {sheet_path.name}")

    manifest = rc.write_manifest(
        out / "coral_skin_manifest.json",
        "melodia.sea_above_reef_textures.v1",
        seed,
        {
            "generator": "coral_textures.py",
            "runtime": "python+PIL",
            "tiling": "lattice-periodic",
            "emissive_usage": "multiply by User.SeaAbovePulse in MI; per-PC tint on albedo",
        },
        files,
    )
    print(f"[coral-tex] manifest -> {manifest}")


if __name__ == "__main__":
    main()
