"""Nikki Iridescent Motif lookdev - Infinity-Nikki-style pearlescent texture family.

Deterministic + tileable (reef_common conventions), reuses the proven Sea Above
math (fbm / periodic Voronoi / tileable sine / normal-from-height). No new
texture system.

Set (T_Nikki_*):
  T_Nikki_Iridescence_LUT     - aurora phase LUT (violet->pink->peach->gold->teal->blue)
                                authoring reference for UE iridescence ramp tuning
  T_Nikki_Motif_BaseColor     - pale mother-of-pearl + soft aurora mottle + fine film stripes
  T_Nikki_Motif_Normal        - pearl dimples + soap-film ridges
  T_Nikki_Motif_Roughness     - wet-gloss pearl (mostly smooth)
  T_Nikki_Motif_Emissive      - soft static aurora glow (tasteful, static)

Outputs: Saved/Audit/sea_above/houdini_variants/ + sha256 manifest.
Run:  python Tools/Houdini/sea_above_reef/nikki_iridescent_lookdev.py
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

# Aurora stops (sRGB): violet -> pink -> peach -> gold -> teal -> blue
AURORA = np.array([
    [0.55, 0.34, 0.85],
    [0.95, 0.55, 0.78],
    [1.00, 0.80, 0.65],
    [0.98, 0.90, 0.60],
    [0.50, 0.85, 0.80],
    [0.40, 0.60, 0.95],
], np.float32)

PEARL_BASE = np.array([0.93, 0.90, 0.94], np.float32)


def _palette_sample(t):
    """t in [0,1] -> smoothstep-interpolated aurora color (n x n x 3)."""
    n_stops = len(AURORA) - 1
    x = np.clip(t, 0.0, 1.0) * n_stops
    i0 = np.floor(x).astype(np.int32)
    i1 = np.minimum(i0 + 1, n_stops)
    f = (x - i0).astype(np.float32)
    s = f * f * (3.0 - 2.0 * f)
    c0 = AURORA[i0]
    c1 = AURORA[i1]
    return c0 * (1.0 - s[..., None]) + c1 * s[..., None]


def build(seed, size):
    rng = np.random.default_rng(seed)
    ys, xs = np.mgrid[0:size, 0:size].astype(np.float32)

    # ---------- iridescence LUT (vertical phase bands, horizontally tileable) ----------
    lut_t = ys / size
    warp = rc.fbm(size, 32, 3, rng, gain=0.5)
    phase = np.clip(lut_t + (warp - 0.5) * 0.06, 0.0, 1.0)
    shimmer = rc.tileable_sine(size, 6, 0, phase=0.0, warp=warp, warp_amp=0.08)
    phase = np.clip(phase + (shimmer - 0.5) * 0.04, 0.0, 1.0)
    lut = _palette_sample(phase)

    # ---------- mother-of-pearl base: pale pearl + large soft aurora cells ----------
    f1 = rc.periodic_voronoi_f1(size, 16, 0.8, np.random.default_rng(seed + 1))
    cell_t = np.clip((1.0 - f1) * 1.15, 0.0, 1.0)          # cell interiors brighter
    cell_color = _palette_sample(cell_t)
    cell_mask = np.clip((1.0 - f1) * 2.2 - 0.4, 0.0, 1.0) ** 1.4  # soft cell falloff
    fine_warp = rc.fbm(size, 32, 3, np.random.default_rng(seed + 2), gain=0.5)
    film = rc.tileable_sine(size, 6, 120, phase=0.4, warp=fine_warp, warp_amp=0.7)
    speckle = rc.fbm(size, 128, 2, np.random.default_rng(seed + 3), gain=0.5)

    base = PEARL_BASE[None, None, :] * np.ones((size, size, 1), np.float32)
    base = base * (1.0 - 0.55 * cell_mask[..., None]) + cell_color * (0.55 * cell_mask[..., None])
    base += (film - 0.5)[..., None] * 0.10 * (1.0 - cell_mask[..., None])
    base += (speckle - 0.5)[..., None] * 0.06
    albedo = np.clip(base, 0.0, 1.0)

    # ---------- normal: pearl dimples + fine soap-film ridges ----------
    f2 = rc.periodic_voronoi_f1(size, 32, 0.9, np.random.default_rng(seed + 4))
    dimple = np.clip((0.45 - f2) * 2.0, 0.0, 1.0) ** 2.0          # dimple bowls
    ridge_warp = rc.fbm(size, 64, 3, np.random.default_rng(seed + 5), gain=0.5)
    ridge = np.abs(np.sin((xs * 9.0 + ridge_warp * 40.0) / size * 2.0 * np.pi)) ** 3.0
    height = 0.45 * dimple + 0.55 * ridge + 0.25 * speckle
    normal = rc.normal_from_height(height, strength=2.6)

    # ---------- roughness: wet gloss, slightly higher in cell centers ----------
    rough = np.clip(0.16 + 0.14 * cell_mask + 0.10 * speckle - 0.05 * film, 0.05, 0.55)

    # ---------- emissive: soft static aurora glow at cell edges + film ----------
    edge = np.clip((0.9 - f1) * 1.6, 0.0, 1.0) ** 2.0 * (1.0 - cell_mask)
    emissive = np.clip(0.22 * edge + 0.10 * film * (1.0 - cell_mask), 0.0, 0.40)

    return {
        "T_Nikki_Iridescence_LUT": (lut, "rgb"),
        "T_Nikki_Motif_BaseColor": (albedo, "rgb"),
        "T_Nikki_Motif_Normal": (normal, "rgb"),
        "T_Nikki_Motif_Roughness": (rough, "gray"),
        "T_Nikki_Motif_Emissive": (emissive, "gray"),
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
        print(f"[nikki] wrote {p.name}")

    manifest = rc.write_manifest(
        OUT / "nikki_iridescent_lookdev_manifest.json",
        "melodia.nikki_iridescent_lookdev.v1",
        args.seed,
        {
            "generator": "nikki_iridescent_lookdev.py",
            "runtime": "python+PIL",
            "asset": "Nikki Iridescent Motif Set (pearl / shell / bubble / ribbon)",
            "reuses": "fbm / periodic_voronoi_f1 / tileable_sine / normal_from_height (reef suite)",
            "lut": "authoring reference for UE iridescence ramp (M_Master_Toon_Universal Iridescence*)",
            "all": "static lookdev; no MPC writer, no runtime animation",
        },
        files,
    )
    print(f"[nikki] manifest -> {manifest}")


if __name__ == "__main__":
    main()