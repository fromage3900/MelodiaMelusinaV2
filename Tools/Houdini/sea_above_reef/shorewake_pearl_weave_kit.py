#!/usr/bin/env python
"""Shorewake pearl-woven fabric + painterly base kit (tiling, deterministic).

Research-informed (2026-08-31 session):
  - pearl weave      : satin warp/weft lattice + pearl dimples
                       (nikki_iridescent_lookdev mother-of-pearl family)
  - Chladni motif    : n=5,m=7 standing-wave pattern woven into the height
                       (P2_AUDIO_REACTIVE_FABRIC_MOUNTAINS_2026-08-31 fold table;
                        texture-only — reads no audio, MPC writer contract intact)
  - iridescence/sheen: per-plate spectral hue lattice (dress_shine_kit) +
                       aurora mottle + NikkiPearlSheen 0.4 / PastelStrength 0.65
  - painterly base   : gesso/impasto strokes, seafoam->teal palette
                       (dress_lookdev), foam-crest mask modulated by the dress
                       curvature bake; draped 4K dress-space variant projected
                       through the slotted-mesh UVs.

Outputs (tiling 2048 unless noted) -> Saved/Audit/melusina_lookdev/bake/night_pkg_2026-08-31/
  T_Shorewake_PearlWeave_Height/N/AO/Roughness
  T_Shorewake_ChladniWeave_N            (weave normal with standing-wave motif)
  T_Shorewake_PearlSheen_Iridescence    (spectral hue, sRGB)
  T_Shorewake_PearlSheen_Strength       (gray sheen weight mask)
  T_Shorewake_Painterly_BaseColor       (seafoam->teal strokes, sRGB)
  T_Shorewake_Painterly_Height          (gesso/impasto)
  T_DressShorewake_Painterly_Drape_4K   (dress-space projected painterly base)
  T_DressShorewake_FoamCrest_Mask_4K    (curvature-driven edge/foam mask, dress space)

Run: python Tools/Houdini/sea_above_reef/shorewake_pearl_weave_kit.py
"""
import colorsys
import sys
from pathlib import Path

import numpy as np

PROJECT = Path(__file__).resolve().parents[3]
sys.path.insert(0, str(PROJECT / "Tools" / "Houdini" / "sea_above_reef"))
import reef_common as rc  # noqa: E402

PKG = PROJECT / "Saved" / "Audit" / "melusina_lookdev" / "bake" / "night_pkg_2026-08-31"
PKG.mkdir(parents=True, exist_ok=True)
SEED = 20260831
SIZE = 2048

rng = np.random.default_rng(SEED)


def norm_from_height(h, strength=2.0):
    """Tangent-space normal (OpenGL Y+) from a height field, tileable."""
    gx = (np.roll(h, -1, 1) - np.roll(h, 1, 1)) * 0.5
    gy = (np.roll(h, -1, 0) - np.roll(h, 1, 0)) * 0.5
    n = np.dstack([-gx * strength, gy * strength, np.ones_like(h)])
    n /= np.linalg.norm(n, axis=2, keepdims=True)
    return n * 0.5 + 0.5


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


from PIL import Image  # noqa: E402


# ---------------------------------------------------------------- pearl weave
def pearl_weave():
    """Satin weave: 8-thread satin lattice + pearl dimples on knot points."""
    s = SIZE
    y, x = np.mgrid[0:s, 0:s].astype(np.float32)
    thread = 64.0                      # thread pitch in px
    xi, yi = x / thread, y / thread
    # satin interlace: warp over weft where (i - 3*j) mod 8 == 0
    warp_over = (((np.floor(xi).astype(int) - 3 * np.floor(yi).astype(int)) % 8) == 0)
    # thread profile: rounded tubes
    fx, fy = xi % 1.0, yi % 1.0
    tube_x = np.sin(np.pi * fx) ** 2
    tube_y = np.sin(np.pi * fy) ** 2
    h = np.where(warp_over, 0.55 + 0.45 * tube_x, 0.55 + 0.45 * tube_y)
    # pearl dimples at cell centers
    dimple = np.exp(-(((fx - 0.5) ** 2 + (fy - 0.5) ** 2) / 0.06))
    h -= 0.35 * dimple
    # pearlescent micro-mottle
    h += 0.05 * (fbm(s, octaves=4, base=16, seed=SEED + 1) - 0.5)
    h = (h - h.min()) / (h.max() - h.min())
    return h


def chladni(s, n, m, size):
    """Chladni standing wave |cos(n px)cos(m py) - cos(m px)cos(n py)|, tileable."""
    y, x = np.mgrid[0:s, 0:s].astype(np.float32) / s
    t = np.abs(np.cos(n * 2 * np.pi * x) * np.cos(m * 2 * np.pi * y)
               - np.cos(m * 2 * np.pi * x) * np.cos(n * 2 * np.pi * y))
    img = Image.fromarray((np.clip(t, 0, 1) * 255).astype(np.uint8)).resize((size, size), Image.BICUBIC)
    return np.asarray(img, np.float32) / 255.0


# ---------------------------------------------------------------- iridescence
def spectral_lattice(s):
    """Per-plate spectral hue over a toroidal hex lattice (dress_shine_kit style)."""
    scale = 26.0
    yy, xx = np.mgrid[0:s, 0:s].astype(np.float32)
    # hex lattice
    row = np.floor(yy / (scale * 0.866))
    off = (row % 2) * 0.5
    cx = (np.floor(xx / scale) + off) * scale + scale * 0.5
    cy = row * scale * 0.866 + scale * 0.5
    cx = np.mod(cx, s)
    cy = np.mod(cy, s)
    # deterministic hue per plate from hashed center
    hx = np.floor(np.mod(cx / scale, 4096)).astype(int)
    hy = np.floor(np.mod(cy / (scale * 0.866), 4096)).astype(int)
    hsh = (hx * 73856093) ^ (hy * 19349663)
    hue = ((hsh % 360) / 360.0).astype(np.float32)
    hue_img = Image.fromarray((hue * 255).astype(np.uint8)).resize((s, s), Image.NEAREST)
    return np.asarray(hue_img, np.float32) / 255.0


def hsv_to_rgb_arr(h, s, v):
    """Vectorized HSV->RGB."""
    i = np.floor(h * 6.0)
    f = h * 6.0 - i
    p = v * (1 - s)
    q = v * (1 - f * s)
    t = v * (1 - (1 - f) * s)
    i = i.astype(int) % 6
    r = np.select([i == 0, i == 1, i == 2, i == 3, i == 4, i == 5], [v, q, p, p, t, v])
    g = np.select([i == 0, i == 1, i == 2, i == 3, i == 4, i == 5], [t, v, v, q, p, p])
    b = np.select([i == 0, i == 1, i == 2, i == 3, i == 4, i == 5], [p, p, t, v, v, q])
    return np.dstack([r, g, b])


def main():
    s = SIZE
    files = []

    # ---- pearl weave family -------------------------------------------------
    h = pearl_weave()
    # Chladni n=5,m=7 standing-wave motif woven in (subtle, "sung fabric")
    ch = chladni(s, 5, 7, s)
    h_ch = np.clip(h + 0.10 * (ch - 0.5), 0, 1)

    files.append(rc.save_image(PKG / "T_Shorewake_PearlWeave_Height.png", h, "gray"))
    n_base = norm_from_height(h, strength=1.6)
    files.append(rc.save_image(PKG / "T_Shorewake_PearlWeave_Normal.png", n_base, "rgb"))
    n_ch = norm_from_height(h_ch, strength=1.6)
    files.append(rc.save_image(PKG / "T_Shorewake_ChladniWeave_N.png", n_ch, "rgb"))
    # AO: cavity = local minimum of height (dilate max - h); PIL path (no scipy dep)
    hb = Image.fromarray((h * 255).astype(np.uint8)).filter(ImageFilter.MaxFilter(9))
    h_blur = np.asarray(hb, np.float32) / 255.0
    ao = 1.0 - 0.65 * (h_blur - h)
    files.append(rc.save_image(PKG / "T_Shorewake_PearlWeave_AO.png", ao, "gray"))
    rough = 0.30 + 0.35 * (1.0 - h) + 0.10 * fbm(s, octaves=4, base=8, seed=SEED + 2)
    files.append(rc.save_image(PKG / "T_Shorewake_PearlWeave_Roughness.png", rough, "gray"))

    # ---- iridescence / sheen ------------------------------------------------
    hue = spectral_lattice(s)
    aurora = fbm(s, octaves=5, base=3, seed=SEED + 3)          # large soft aurora cells
    hue_shift = np.clip(hue + 0.15 * (aurora - 0.5), 0, 1)
    iri = hsv_to_rgb_arr(hue_shift, 0.35 + 0.30 * aurora, 0.85)
    files.append(rc.save_image(PKG / "T_Shorewake_PearlSheen_Iridescence.png", iri, "rgb"))
    # sheen weight: grazing ridges (thread tops) + pearl dimple rims, pastel
    rim = 1.0 - np.abs(h - 0.72) * 3.5
    sheen = np.clip(0.4 * np.clip(rim, 0, 1) + 0.65 * aurora, 0, 1)  # NikkiPearlSheen .4 / Pastel .65
    files.append(rc.save_image(PKG / "T_Shorewake_PearlSheen_Strength.png", sheen, "gray"))

    # ---- painterly base -------------------------------------------------------
    # brush strokes: directional smeared noise (seafoam -> deep teal palette)
    strokes = fbm(s, octaves=6, base=6, seed=SEED + 4)
    sm = Image.fromarray((strokes * 255).astype(np.uint8)).filter(ImageFilter.GaussianBlur(2))
    # directional smear (horizontal stroke drag)
    sm = np.asarray(sm, np.float32) / 255.0
    drag = np.roll(sm, 12, axis=1) * 0.5 + sm * 0.5
    t = np.clip(drag * 0.75 + 0.25 * ch, 0, 1)                  # Chladni-guided stroke flow
    seafoam = np.array([0.72, 0.93, 0.86])
    mid = np.array([0.23, 0.62, 0.66])
    deep = np.array([0.06, 0.22, 0.38])
    c1 = seafoam[None, None] * (1 - t[..., None]) + mid[None, None] * t[..., None]
    base = c1 * (1 - (t ** 2)[..., None]) + deep[None, None] * (t ** 2)[..., None]
    files.append(rc.save_image(PKG / "T_Shorewake_Painterly_BaseColor.png", base, "rgb"))
    # gesso / impasto: stroke ridges
    imp = np.clip(0.6 * drag + 0.4 * (fbm(s, octaves=3, base=24, seed=SEED + 5)), 0, 1)
    files.append(rc.save_image(PKG / "T_Shorewake_Painterly_Height.png", imp, "gray"))

    # ---- dress-space draped variants (projected through slotted UVs) ---------
    npz = np.load(PKG / "face_uv_data.npz")
    loop_uv = npz["loop_uv"].astype(np.float64)
    loop_total = npz["loop_total"]
    RES = 4096
    img = Image.new("RGB", (RES, RES), (0, 0, 0))
    from PIL import ImageDraw
    draw = ImageDraw.Draw(img)
    t_img = Image.fromarray((t * 255).astype(np.uint8)).resize((RES, RES), Image.BICUBIC)
    t_big = np.asarray(t_img, np.float32) / 255.0
    # precompute palette at dress res
    tt = np.clip(t_big, 0, 1)
    c1 = seafoam[None, None] * (1 - tt[..., None]) + mid[None, None] * tt[..., None]
    drape = c1 * (1 - (tt ** 2)[..., None]) + deep[None, None] * (tt ** 2)[..., None]
    drape_u8 = (np.clip(drape, 0, 1) * 255).astype(np.uint8)
    # per-pixel projection: rasterize mesh coverage mask, then sample the tiling field
    starts = np.concatenate([[0], np.cumsum(loop_total)[:-1]])
    mask = Image.new("L", (RES, RES), 0)
    md = ImageDraw.Draw(mask)
    for f in range(len(loop_total)):
        s0, e0 = starts[f], starts[f] + loop_total[f]
        uvf = loop_uv[s0:e0]
        pts = [(float(uv) * (RES - 1), float(1.0 - vv) * (RES - 1)) for uv, vv in uvf]
        md.polygon(pts, fill=255)
    m_arr = np.asarray(mask, np.float32) / 255.0
    out = drape_u8 * m_arr[..., None]
    files.append(rc.save_image(PKG / "T_DressShorewake_Painterly_Drape_4K.png",
                               out.astype(np.float32) / 255.0, "rgb"))

    # foam-crest mask from the existing curvature bake (edge/wear logic)
    curv_src = PKG.parent / "sbs" / "SM_ShorewakeDress_48MAT_v2_low_curvature.png"
    if curv_src.exists():
        curv = np.asarray(Image.open(curv_src).convert("L").resize((RES, RES), Image.BICUBIC), np.float32) / 255.0
        foam = np.clip((curv - 0.45) * 2.6, 0, 1) * m_arr
        files.append(rc.save_image(PKG / "T_DressShorewake_FoamCrest_Mask_4K.png", foam, "gray"))
    else:
        foam = None

    rc.write_manifest(
        PKG / "pearl_weave_kit_manifest.json",
        "melodia.shorewake_pearl_weave_kit.v1",
        SEED,
        {
            "tiling_size": SIZE,
            "drape_res": RES,
            "chladni_mode": [5, 7],
            "thread_pitch_px": 64,
            "nikki_sheen_params": {"NikkiPearlSheen": 0.4, "NikkiPastelStrength": 0.65},
            "palette": {"seafoam": list(seafoam), "mid": list(mid), "deep": list(deep)},
            "audio_contract": "texture-only; no audio reader — single audio writer "
                              "(MelodiaAudioReactivePresentationSubsystem) untouched",
            "foam_crest_source": str(curv_src) if curv_src.exists() else None,
        },
        [str(Path(f).name) for f in files],
    )
    print("PEARL_KIT " + json.dumps({"files": len(files)}))


import json  # noqa: E402
from PIL import ImageFilter  # noqa: E402

if __name__ == "__main__":
    main()
