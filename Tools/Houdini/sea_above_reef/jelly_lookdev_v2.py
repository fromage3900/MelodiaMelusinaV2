"""Jellyfish lookdev v2 — iridescence + veil + canal glow + nematocyst glints.

The surreal-beautiful pass for the R6 structure. Everything feeds the material
recipe in IMPORT_QUEUE.md ("Iridescent bell recipe" + arms effects parameters).

New textures (Saved/Audit/sea_above/houdini_variants/):
  T_Jelly_Bell_BaseColor      translucent veil: radial canals, spot rows,
                              subtle baked edge-spectral tint (sRGB)
  T_Jelly_Bell_Opacity        gauzy falloff: opaque core -> gossamer margin,
                              canals more opaque (data)
  T_Jelly_Bell_CanalMask      emissive canal channels (data)
  T_Jelly_Bell_Normal         gentle veil folds (data, OpenGL Y+)
  T_Jelly_Bell_Irid_Mottle    thin-film thickness variation -> drives the
                              iridescence LUT's V coordinate (data)
  T_Jelly_Iridescence_LUT     THE iridescence ramp: U = N·V facing amount,
                              V = film phase (spectral sine palette, pastel
                              toward facing, spectral at grazing) (sRGB)
  T_Jelly_Nematocyst_Glints   tilable sparkle field for the arms (data)

Run:  python Tools/Houdini/sea_above_reef/jelly_lookdev_v2.py
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


def spectral(phase, pastel=0.38):
    """Phase-shifted sine spectrum (dreamy oil-slick), mixed toward white."""
    ph = np.asarray(phase, np.float32) % 1.0
    r = 0.5 + 0.5 * np.sin(2 * np.pi * ph)
    g = 0.5 + 0.5 * np.sin(2 * np.pi * (ph + 0.33))
    b = 0.5 + 0.5 * np.sin(2 * np.pi * (ph + 0.67))
    rgb = np.stack([r, g, b], axis=-1)
    return rgb * (1.0 - pastel) + pastel


def build(seed, size):
    # ---------- shared fields ----------
    ys, xs = np.mgrid[0:size, 0:size].astype(np.float32)
    u = xs / size
    v = ys / size
    th = u * 2.0 * np.pi
    rng = np.random.default_rng(seed)

    # radial distance from bell apex (top-centre) -> margin (bottom). The bell
    # mesh uv: u = around, v = apex(1) .. margin(0). Work with m = 1 - v.
    m = (1.0 - v).astype(np.float32)
    m2 = m ** 2

    folds_warp = rc.fbm(size, 16, 3, rng, gain=0.5)
    folds = rc.tileable_sine(size, 12, 3, phase=0.8, warp=folds_warp, warp_amp=1.0)
    canals = np.abs(np.sin(th * 16.0)) ** 24.0                     # 32 meridian lines
    canal_soft = np.abs(np.sin(th * 16.0)) ** 3.0
    spots_f1 = rc.periodic_voronoi_f1(size, 64, 0.85,
                                      np.random.default_rng(seed + 1))
    spots = np.clip(1.0 - spots_f1 * 5.0, 0, 1) ** 1.8
    spots *= (0.35 + 0.65 * canal_soft)                            # spots along canals

    # ---------- BaseColor ----------
    veil = np.array([0.86, 0.93, 0.95], np.float32)
    core = np.array([0.62, 0.82, 0.88], np.float32)
    deep = np.array([0.30, 0.52, 0.66], np.float32)
    base = core[None, None, :] * (1.0 - m2[..., None]) + veil[None, None, :] * m2[..., None]
    base = base * (1.0 - 0.18 * (folds - 0.5)[..., None])
    base = base * (1.0 - 0.30 * canals[..., None]) + deep[None, None, :] * (0.30 * canals[..., None])
    base += np.array([0.9, 0.97, 1.0], np.float32)[None, None, :] * (spots[..., None] * 0.25)
    # baked edge spectral whisper (full iridescence comes from the LUT in-engine)
    edge_spec = spectral(m * 0.85 + 0.05 * folds, pastel=0.62)
    edge_w = (m2 * 0.55)[..., None]
    base = base * (1.0 - edge_w) + edge_spec * edge_w
    albedo = np.clip(base, 0, 1)

    # ---------- Normal ----------
    height = 0.55 * folds + 0.25 * canal_soft + 0.20 * spots
    normal = rc.normal_from_height(height, strength=1.6)           # veil is soft

    # ---------- Opacity ----------
    opacity = np.clip(0.30 + 0.60 * m2 + 0.18 * canals + 0.10 * spots
                      + 0.08 * (folds - 0.5), 0.12, 1.0)

    # ---------- CanalMask (emissive) ----------
    canal_mask = np.clip(canals * (0.45 + 0.55 * m2) + 0.15 * spots * m2, 0, 1) ** 1.3

    # ---------- Iridescence mottle (film thickness variation) ----------
    mottle = rc.fbm(size, 16, 4, np.random.default_rng(seed + 2), gain=0.55)
    mottle = np.clip((mottle - 0.5) * 1.6 + 0.5, 0, 1)
    mottle = mottle * (0.35 + 0.65 * m2)                            # strongest near margin

    # ---------- Iridescence LUT ----------
    # U (x) = N·V facing amount: 1 = facing, 0 = grazing
    # V (y) = film phase (wrap); pastel near facing, full spectral at grazing,
    # grazing edge gets a brightness lift so rims bloom.
    facing = np.linspace(1.0, 0.0, 128, dtype=np.float32)[None, :]
    film_phase = np.linspace(0.0, 1.0, 512, dtype=np.float32)[:, None]
    spec = spectral(film_phase + (1.0 - facing) * 0.18,
                    pastel=(0.30 + 0.42 * facing)[..., None])
    glow = (1.0 + 0.55 * (1.0 - facing))[..., None]
    iri = np.clip(spec * glow, 0, 1)
    iri = np.transpose(iri, (0, 1, 2))                              # (512 phase, 128 facing, 3)

    # ---------- Nematocyst glints (tilable) ----------
    g1 = rc.periodic_voronoi_f1(size, 128, 0.9, np.random.default_rng(seed + 3))
    glint = np.clip(1.0 - g1 * 7.0, 0, 1) ** 2.2
    aniso = np.maximum(np.abs(np.sin(np.pi * u * 64.0)), np.abs(np.sin(np.pi * v * 64.0)))
    glint = glint * (0.55 + 0.45 * aniso)

    return {
        "T_Jelly_Bell_BaseColor": (albedo, "rgb"),
        "T_Jelly_Bell_Normal": (normal, "rgb"),
        "T_Jelly_Bell_Opacity": (opacity, "gray"),
        "T_Jelly_Bell_CanalMask": (canal_mask, "gray"),
        "T_Jelly_Bell_Irid_Mottle": (mottle, "gray"),
        "T_Jelly_Iridescence_LUT": (iri, "rgb"),
        "T_Jelly_Nematocyst_Glints": (np.clip(glint, 0, 1), "gray"),
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
                      "size": args.size if "LUT" not in name else 512, "seed": args.seed})
        print(f"[jelly-v2] wrote {p.name}")

    manifest = rc.write_manifest(
        OUT / "jelly_lookdev_v2_manifest.json",
        "melodia.sea_above_reef_textures.v1",
        args.seed,
        {
            "generator": "jelly_lookdev_v2.py",
            "runtime": "python+numpy+PIL",
            "iridescence_lut": {"U": "N·V facing amount (1 facing -> 0 grazing)",
                                "V": "film phase; pan with Irid_Mottle as offset; "
                                     "pastel near facing, spectral at grazing",
                                "recipe": "IMPORT_QUEUE.md 'Iridescent bell recipe'"},
            "palette": {"veil": [0.86, 0.93, 0.95], "core": [0.62, 0.82, 0.88],
                        "deep": [0.30, 0.52, 0.66]},
        },
        files,
    )
    print(f"[jelly-v2] manifest -> {manifest}")


if __name__ == "__main__":
    main()
