#!/usr/bin/env python
"""Cos_FlowerSpring — per-variant map bake for Substance staging.

Extends flowerspring_fabric_kit.py (v1, FlowerSpring-only) to a variant baker:
every dress colorway gets a complete, Substance-Painter-ready map set at 2048:

  T_<Variant>_BaseColor.png        (sRGB-space authored colour)
  T_<Variant>_Normal.png
  T_<Variant>_ORM.png              (R=AO, G=Roughness, B=Metallic — UE packing)
  T_<Variant>_Height.png
  T_<Variant>_Emissive.png
  T_<Variant>_Iridescence.png
  T_<Variant>_Sheen.png

Variants reuse the five cymatic colour families already present in
Saved/Audit/copernicus_cymatic/ so the dress reads with the project's world:

  FlowerSpring      cream/butter/gold/peach/blush + spring accents (v1 kit)
  GildedLoom        champagne -> deep gold, bronze thread
  SilkWaterfall     pearl/ice/silver-blue satin
  CherryBlossomWood petal blush/rose with warm wood
  StarlitAbyss      deep indigo with star-silver emissive

Output: Saved/Audit/melusina_lookdev/substance_staging/FlowerSpring/textures/<Variant>/
Run: python Tools/Houdini/sea_above_reef/flowerspring_variant_maps.py
"""
import json
import sys
from pathlib import Path

import numpy as np
from PIL import Image, ImageFilter

PROJECT = Path(__file__).resolve().parents[3]
sys.path.insert(0, str(PROJECT / "Tools" / "Houdini" / "sea_above_reef"))
import reef_common as rc  # noqa: E402

STAGE = PROJECT / "Saved" / "Audit" / "melusina_lookdev" / "substance_staging" / "FlowerSpring"
TEX = STAGE / "textures"
SEED = 20260831
SIZE = 2048


def V(*c):
    return [np.array(c[i : i + 3]) for i in range(0, len(c), 3)]


VARIANTS = {
    #                   chladni  thread  dark        mid        light       accent1     accent2     emissive
    "FlowerSpring":      dict(ch=(3, 4), thread=44, dark=[0.72, 0.55, 0.38], mid=[1.00, 0.88, 0.60],
                              light=[1.00, 0.95, 0.84], acc1=[0.95, 0.63, 0.66], acc2=[0.66, 0.85, 0.42],
                              em=0.06, emc=[1.0, 0.9, 0.6], metal=0.10),
    "GildedLoom":        dict(ch=(5, 2), thread=36, dark=[0.42, 0.30, 0.12], mid=[0.91, 0.72, 0.29],
                              light=[1.00, 0.90, 0.62], acc1=[0.80, 0.55, 0.20], acc2=[1.00, 0.96, 0.90],
                              em=0.05, emc=[1.0, 0.8, 0.35], metal=0.45),
    "SilkWaterfall":     dict(ch=(2, 6), thread=52, dark=[0.45, 0.55, 0.68], mid=[0.85, 0.90, 0.95],
                              light=[1.00, 1.00, 1.00], acc1=[0.60, 0.75, 0.88], acc2=[0.75, 0.85, 0.92],
                              em=0.04, emc=[0.7, 0.85, 1.0], metal=0.15),
    "CherryBlossomWood": dict(ch=(3, 3), thread=40, dark=[0.40, 0.26, 0.20], mid=[0.95, 0.63, 0.66],
                              light=[1.00, 0.88, 0.86], acc1=[0.85, 0.40, 0.48], acc2=[0.55, 0.38, 0.28],
                              em=0.05, emc=[1.0, 0.7, 0.7], metal=0.05),
    "StarlitAbyss":      dict(ch=(6, 4), thread=48, dark=[0.05, 0.07, 0.18], mid=[0.16, 0.20, 0.42],
                              light=[0.55, 0.65, 0.90], acc1=[0.75, 0.85, 1.00], acc2=[0.30, 0.80, 0.85],
                              em=0.55, emc=[0.65, 0.80, 1.0], metal=0.30),
}


def fbm(size, octaves=5, base=4, seed=0):
    out = np.zeros((size, size), np.float32)
    amp, tot = 1.0, 0.0
    r = np.random.default_rng(seed)
    for o in range(octaves):
        f = base * (2 ** o)
        grid = r.random((f, f)).astype(np.float32)
        img = Image.fromarray((grid * 255).astype(np.uint8)).resize((size, size), Image.BICUBIC)
        out += amp * (np.asarray(img, np.float32) / 255.0)
        tot += amp
        amp *= 0.5
    return out / tot


def norm_from_height(h, strength=2.0):
    gx = (np.roll(h, -1, 1) - np.roll(h, 1, 1)) * 0.5
    gy = (np.roll(h, -1, 0) - np.roll(h, 1, 0)) * 0.5
    n = np.dstack([-gx * strength, gy * strength, np.ones_like(h)])
    n /= np.linalg.norm(n, axis=2, keepdims=True)
    return n * 0.5 + 0.5


def hsv_to_rgb(h, s, v):
    i = np.floor(h * 6.0).astype(int) % 6
    f = h * 6.0 - np.floor(h * 6.0)
    p = v * (1 - s)
    q = v * (1 - f * s)
    t = v * (1 - (1 - f) * s)
    r = np.select([i == 0, i == 1, i == 2, i == 3, i == 4, i == 5], [v, q, p, p, t, v])
    g = np.select([i == 0, i == 1, i == 2, i == 3, i == 4, i == 5], [t, v, v, q, p, p])
    b = np.select([i == 0, i == 1, i == 2, i == 3, i == 4, i == 5], [p, p, t, v, v, q])
    return np.dstack([r, g, b])


def bake_variant(name: str, P: dict) -> list:
    s = SIZE
    files = []
    vdir = TEX / name
    vdir.mkdir(parents=True, exist_ok=True)
    dark, mid, light = (np.array(P[k], np.float32) for k in ("dark", "mid", "light"))
    acc1, acc2 = np.array(P["acc1"], np.float32), np.array(P["acc2"], np.float32)
    n_ch, m_ch = P["ch"]
    thread = float(P["thread"])

    # ---- weave height (satin thread + petal dimple) -------------------------
    y, x = np.mgrid[0:s, 0:s].astype(np.float32)
    xi, yi = x / thread, y / thread
    warp_over = (((np.floor(xi).astype(int) - 2 * np.floor(yi).astype(int)) % 5) == 0)
    fx, fy = xi % 1.0, yi % 1.0
    tube_x, tube_y = np.sin(np.pi * fx) ** 2, np.sin(np.pi * fy) ** 2
    h = np.where(warp_over, 0.6 + 0.4 * tube_x, 0.6 + 0.4 * tube_y)
    petal = np.exp(-(((fx - 0.5) ** 2 + (fy - 0.5) ** 2) / 0.09))
    h -= 0.22 * petal
    h += 0.05 * (fbm(s, octaves=4, base=16, seed=SEED + 1) - 0.5)
    h = (h - h.min()) / (h.max() - h.min())

    files.append(rc.save_image(vdir / f"T_{name}_Height.png", h, "gray"))
    files.append(rc.save_image(vdir / f"T_{name}_Normal.png", norm_from_height(h, 1.4), "rgb"))
    hb = Image.fromarray((h * 255).astype(np.uint8)).filter(ImageFilter.MaxFilter(7))
    ao = 1.0 - 0.55 * (np.asarray(hb, np.float32) / 255.0 - h)
    rough = 0.34 + 0.30 * (1.0 - h) + 0.10 * fbm(s, octaves=4, base=8, seed=SEED + 2)

    # ---- ORM (R=AO, G=Roughness, B=Metallic) --------------------------------
    gold_thread = np.where(warp_over, 1.0, 0.0) * petal
    metal = np.clip(P["metal"] * (0.3 + 0.7 * gold_thread), 0, 1)
    orm = np.dstack([ao, np.clip(rough, 0, 1), metal])
    files.append(rc.save_image(vdir / f"T_{name}_ORM.png", orm, "rgb"))

    # ---- chladni motif normal ------------------------------------------------
    yy, xx = np.mgrid[0:s, 0:s].astype(np.float32) / s
    t = np.abs(np.cos(n_ch * 2 * np.pi * xx) * np.cos(m_ch * 2 * np.pi * yy)
               - np.cos(m_ch * 2 * np.pi * xx) * np.cos(n_ch * 2 * np.pi * yy))
    h_ch = np.clip(h + 0.08 * (t - 0.5), 0, 1)
    files.append(rc.save_image(vdir / f"T_{name}_Motif_N.png", norm_from_height(h_ch, 1.4), "rgb"))

    # ---- iridescence (soft-hex hue, 90px plates) ------------------------------
    scale = 90.0
    row = np.floor(yy * s / (scale * 0.866))
    off = (row % 2) * 0.5
    cx = (np.floor(xx * s / scale) + off) * scale + scale * 0.5
    cy = row * scale * 0.866 + scale * 0.5
    hx = np.floor(np.mod(cx / scale, 4096)).astype(int)
    hy = np.floor(np.mod(cy / (scale * 0.866), 4096)).astype(int)
    hsh = (hx * 73856093) ^ (hy * 19349663)
    hue = ((hsh % 360) / 360.0).astype(np.float32)
    hue = np.asarray(Image.fromarray((hue * 255).astype(np.uint8)).resize((s, s), Image.BILINEAR),
                     np.float32) / 255.0
    hue = np.asarray(Image.fromarray((hue * 255).astype(np.uint8)).filter(ImageFilter.GaussianBlur(18)),
                     np.float32) / 255.0
    aurora = fbm(s, octaves=4, base=3, seed=SEED + 3)
    hue2 = np.clip(hue + 0.10 * (aurora - 0.5), 0, 1)
    iri = hsv_to_rgb(hue2, 0.45, 0.88 * (0.7 + 0.3 * aurora))
    files.append(rc.save_image(vdir / f"T_{name}_Iridescence.png", iri, "rgb"))
    rim = 1.0 - np.abs(h - 0.72) * 3.5
    sheen = np.clip(0.4 * np.clip(rim, 0, 1) + 0.65 * aurora, 0, 1)
    files.append(rc.save_image(vdir / f"T_{name}_Sheen.png", sheen, "gray"))

    # ---- painterly base colour ------------------------------------------------
    strokes = fbm(s, octaves=6, base=6, seed=SEED + 4)
    sm = np.asarray(Image.fromarray((strokes * 255).astype(np.uint8)).filter(ImageFilter.GaussianBlur(2)),
                    np.float32) / 255.0
    drag = np.roll(sm, 12, axis=1) * 0.5 + sm * 0.5
    tt2 = np.clip(drag * 0.75 + 0.25 * t, 0, 1)
    c1 = dark[None, None] * (1 - tt2[..., None]) + mid[None, None] * tt2[..., None]
    base = c1 * (1 - (tt2 ** 2)[..., None]) + light[None, None] * (tt2 ** 2)[..., None]
    fleck = (fbm(s, octaves=3, base=40, seed=SEED + 5) > 0.78).astype(np.float32)
    base = base * (1 - 0.25 * fleck[..., None]) + acc2[None, None] * (0.25 * fleck[..., None])
    dab = (fbm(s, octaves=3, base=30, seed=SEED + 6) > 0.82).astype(np.float32)
    base = base * (1 - 0.30 * dab[..., None]) + acc1[None, None] * (0.30 * dab[..., None])
    files.append(rc.save_image(vdir / f"T_{name}_BaseColor.png", base, "rgb"))

    # ---- emissive (subtle for cloth; star field for StarlitAbyss) -------------
    em = np.clip(aurora * 1.2 - 0.35, 0, 1) ** 1.5
    if name == "StarlitAbyss":
        stars = (fbm(s, octaves=2, base=90, seed=SEED + 8) > 0.88).astype(np.float32)
        stars = np.asarray(Image.fromarray((stars * 255).astype(np.uint8))
                           .filter(ImageFilter.GaussianBlur(1)), np.float32) / 255.0
        em = np.clip(em * 0.4 + stars, 0, 1)
    emissive = em[..., None] * np.array(P["emc"], np.float32)[None, None]
    files.append(rc.save_image(vdir / f"T_{name}_Emissive.png", emissive, "rgb"))

    return [Path(f).name for f in files]


def main():
    all_files = {}
    for name, P in VARIANTS.items():
        all_files[name] = bake_variant(name, P)
        print(f"[variant] {name}: {len(all_files[name])} maps")

    rc.write_manifest(
        STAGE / "flowerpring_variant_maps_manifest.json".replace("flowerpring", "flowerspring"),
        "melodia.flowerspring_variant_maps.v1",
        SEED,
        {
            "tiling_size": SIZE,
            "orm_packing": "R=AO G=Roughness B=Metallic (UE)",
            "variants": {n: {"chladni": P["ch"], "thread_pitch_px": P["thread"],
                              "metallic": P["metal"], "emissive_scale": P["em"]}
                          for n, P in VARIANTS.items()},
            "notes": "colour families reuse the cymatic variant palettes; owner paints over these in Substance",
        },
        {n: len(f) for n, f in all_files.items()},
    )
    print("VARIANT_MAPS_DONE " + json.dumps({n: len(f) for n, f in all_files.items()}))


if __name__ == "__main__":
    main()
