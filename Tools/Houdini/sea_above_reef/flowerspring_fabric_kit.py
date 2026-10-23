#!/usr/bin/env python
"""Cos_FlowerSpring — warm/spring tiling fabric kit (shorewake pearl-weave pattern).

Palette contrast: butter/cream, gold, peach, blush + spring-green accents
(vs shorewake seafoam->teal). Iridescence plate scale fixed (26px -> 90px,
softened hue field) per 2026-08-31 QA critique.

Outputs -> Saved/Audit/melusina_lookdev/flowers_outfit/
  T_FlowerSpring_Weave_{Height,Normal,AO,Roughness}
  T_FlowerSpring_PetalWeave_N        (Chladni n=3,m=4 soft motif)
  T_FlowerSpring_Iridescence, T_FlowerSpring_Sheen_Strength
  T_FlowerSpring_Painterly_{BaseColor,Height}

Run: python Tools/Houdini/sea_above_reef/flowerspring_fabric_kit.py
"""
import json
import sys
from pathlib import Path

import numpy as np
from PIL import Image, ImageFilter

PROJECT = Path(__file__).resolve().parents[3]
sys.path.insert(0, str(PROJECT / "Tools" / "Houdini" / "sea_above_reef"))
import reef_common as rc  # noqa: E402

OUT = PROJECT / "Saved" / "Audit" / "melusina_lookdev" / "flowers_outfit"
OUT.mkdir(parents=True, exist_ok=True)
SEED = 20260831
SIZE = 2048
rng = np.random.default_rng(SEED)

# warm-spring palette
CREAM = np.array([1.00, 0.95, 0.84])
BUTTER = np.array([0.99, 0.88, 0.60])
GOLD = np.array([0.91, 0.72, 0.29])
PEACH = np.array([1.00, 0.70, 0.48])
BLUSH = np.array([0.95, 0.63, 0.66])
SPRING = np.array([0.66, 0.85, 0.42])


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


def main():
    s = SIZE
    files = []

    # ---- weave (looser, silk-satin: 44px pitch, softer tubes) -----------------
    y, x = np.mgrid[0:s, 0:s].astype(np.float32)
    thread = 44.0
    xi, yi = x / thread, y / thread
    warp_over = (((np.floor(xi).astype(int) - 2 * np.floor(yi).astype(int)) % 5) == 0)
    fx, fy = xi % 1.0, yi % 1.0
    tube_x, tube_y = np.sin(np.pi * fx) ** 2, np.sin(np.pi * fy) ** 2
    h = np.where(warp_over, 0.6 + 0.4 * tube_x, 0.6 + 0.4 * tube_y)
    petal = np.exp(-(((fx - 0.5) ** 2 + (fy - 0.5) ** 2) / 0.09))
    h -= 0.22 * petal
    h += 0.05 * (fbm(s, octaves=4, base=16, seed=SEED + 1) - 0.5)
    h = (h - h.min()) / (h.max() - h.min())

    files.append(rc.save_image(OUT / "T_FlowerSpring_Weave_Height.png", h, "gray"))
    files.append(rc.save_image(OUT / "T_FlowerSpring_Weave_Normal.png", norm_from_height(h, 1.4), "rgb"))
    hb = Image.fromarray((h * 255).astype(np.uint8)).filter(ImageFilter.MaxFilter(7))
    ao = 1.0 - 0.55 * (np.asarray(hb, np.float32) / 255.0 - h)
    files.append(rc.save_image(OUT / "T_FlowerSpring_Weave_AO.png", ao, "gray"))
    rough = 0.34 + 0.30 * (1.0 - h) + 0.10 * fbm(s, octaves=4, base=8, seed=SEED + 2)
    files.append(rc.save_image(OUT / "T_FlowerSpring_Weave_Roughness.png", rough, "gray"))

    # Chladni n=3,m=4 (softer, spring-chime motif)
    yy, xx = np.mgrid[0:s, 0:s].astype(np.float32) / s
    t = np.abs(np.cos(3 * 2 * np.pi * xx) * np.cos(4 * 2 * np.pi * yy)
               - np.cos(4 * 2 * np.pi * xx) * np.cos(3 * 2 * np.pi * yy))
    h_ch = np.clip(h + 0.08 * (t - 0.5), 0, 1)
    files.append(rc.save_image(OUT / "T_FlowerSpring_PetalWeave_N.png", norm_from_height(h_ch, 1.4), "rgb"))

    # ---- iridescence: FIXED plate scale (90px) + softened hue ----------------
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
    i6 = hue2 * 6.0
    ii = np.floor(i6).astype(int) % 6
    f = i6 - np.floor(i6)
    v = 0.88 * (0.7 + 0.3 * aurora)
    p = v * (1 - 0.45)
    q = v * (1 - f * 0.45)
    tt = v * (1 - (1 - f) * 0.45)
    r = np.select([ii == 0, ii == 1, ii == 2, ii == 3, ii == 4, ii == 5], [v, q, p, p, tt, v])
    g = np.select([ii == 0, ii == 1, ii == 2, ii == 3, ii == 4, ii == 5], [tt, v, v, q, p, p])
    b = np.select([ii == 0, ii == 1, ii == 2, ii == 3, ii == 4, ii == 5], [p, p, tt, v, v, q])
    iri = np.dstack([r, g, b])
    files.append(rc.save_image(OUT / "T_FlowerSpring_Iridescence.png", iri, "rgb"))
    rim = 1.0 - np.abs(h - 0.72) * 3.5
    sheen = np.clip(0.4 * np.clip(rim, 0, 1) + 0.65 * aurora, 0, 1)
    files.append(rc.save_image(OUT / "T_FlowerSpring_Sheen_Strength.png", sheen, "gray"))

    # ---- painterly base: cream->butter strokes, blush/spring accents ---------
    strokes = fbm(s, octaves=6, base=6, seed=SEED + 4)
    sm = np.asarray(Image.fromarray((strokes * 255).astype(np.uint8)).filter(ImageFilter.GaussianBlur(2)),
                    np.float32) / 255.0
    drag = np.roll(sm, 12, axis=1) * 0.5 + sm * 0.5
    tt2 = np.clip(drag * 0.75 + 0.25 * t, 0, 1)
    c1 = CREAM[None, None] * (1 - tt2[..., None]) + BUTTER[None, None] * tt2[..., None]
    base = c1 * (1 - (tt2 ** 2)[..., None]) + PEACH[None, None] * (tt2 ** 2)[..., None]
    # spring-green stroke flecks + blush dabs
    fleck = (fbm(s, octaves=3, base=40, seed=SEED + 5) > 0.78).astype(np.float32)
    base = base * (1 - 0.25 * fleck[..., None]) + SPRING[None, None] * (0.25 * fleck[..., None])
    dab = (fbm(s, octaves=3, base=30, seed=SEED + 6) > 0.82).astype(np.float32)
    base = base * (1 - 0.30 * dab[..., None]) + BLUSH[None, None] * (0.30 * dab[..., None])
    files.append(rc.save_image(OUT / "T_FlowerSpring_Painterly_BaseColor.png", base, "rgb"))
    imp = np.clip(0.6 * drag + 0.4 * (fbm(s, octaves=3, base=24, seed=SEED + 7)), 0, 1)
    files.append(rc.save_image(OUT / "T_FlowerSpring_Painterly_Height.png", imp, "gray"))

    rc.write_manifest(
        OUT / "flowerspring_fabric_kit_manifest.json",
        "melodia.flowerspring_fabric_kit.v1",
        SEED,
        {
            "tiling_size": s,
            "thread_pitch_px": 44,
            "chladni_mode": [3, 4],
            "iridescence_plate_px": 90,
            "iridescence_fix": "plate scale 26->90px + gaussian-softened hue (2026-08-31 QA critique)",
            "palette": {"cream": list(CREAM), "butter": list(BUTTER), "gold": list(GOLD),
                        "peach": list(PEACH), "blush": list(BLUSH), "spring": list(SPRING)},
        },
        [Path(f).name for f in files],
    )
    print("FS_KIT " + json.dumps({"files": len(files)}))


if __name__ == "__main__":
    main()
