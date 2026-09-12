"""Trim Sheet Lab — painterly trim-sheet baker + UE-emulating proxy materials.

Bakes the shared-band trim sheets (hero / cornice+dentils / 4 recessed panels /
wainscot / baseboard / floor ledge) against the CURRENT scene palette: base
colors are sampled from SurrealArch_Stone / SurrealArch_Marble / MH_MAT_Roof
when present, so the sheets track the meshes as art lands.

Outputs per variant into Saved/TrimSheets/out (PNG through bpy image IO —
works in any Blender, no external Pillow):
  <name>_albedo.png  sRGB   <name>_height.png <name>_normal.png <name>_orm.png
  <name>_zone.png    band ids matching trim_bake.TRIM_COLOR_MAP zones
  trimsheet_manifest.json   bands + UE scalar/vector recipe per sheet;
    consumed by Content/Python/melodia_trimsheet_ue.py (MI creation in UE)
    and by the proxy operator below (Blender-side look match).

Proxy materials emulate the project's trim-sheet MIs on
M_Master_Toon_Universal (setup_trimsheet_instances.py recipes): BaseTint
multiply, 3-step toon N·L ramp, ORM rough/metal, normal + height bump.
Look-match, not shading-match: POM and height-compete are engine-side and
are deliberately NOT rebuilt here.
"""

from __future__ import annotations

import json
import os

import bpy
import numpy as np

from .branding import N_PANEL_CATEGORY

TRIM_VARIANTS = ("TS_Melodia_Stone", "TS_Melodia_Music", "TS_Melodia_Dream",
                 "TS_Melodia_Salon", "TS_Melodia_Reverie")

FALLBACK_PALETTE = {
    "stone": (0.78, 0.76, 0.72),
    "marble": (0.80, 0.80, 0.80),
    "roof_blue": (0.611, 0.776, 0.901),
    "gold": (0.95, 0.85, 0.20),
    "pink": (0.94, 0.55, 0.82),
    "dark": (0.05, 0.045, 0.06),
}
SCENE_MAT_SOURCES = {
    "stone": "SurrealArch_Stone",
    "marble": "SurrealArch_Marble",
    "roof_blue": "MH_MAT_Roof",
}

S = 1024
Y_HERO, Y_CORNICE, Y_BODY = (0, 192), (192, 320), (320, 736)
Y_WAIN, Y_BASE, Y_FLOOR = (736, 832), (832, 984), (984, 1024)
BANDS = [
    {"v_px": list(Y_HERO), "zone_id": 6, "role": "variant_hero"},
    {"v_px": list(Y_CORNICE), "zone_id": 13, "role": "cornice_shelf"},
    {"v_px": list(Y_BODY), "zone_id": 1, "role": "wall_panel_recess", "tiles_u": 4},
    {"v_px": list(Y_WAIN), "zone_id": 20, "role": "wainscot"},
    {"v_px": list(Y_BASE), "zone_id": 11, "role": "baseboard"},
    {"v_px": list(Y_FLOOR), "zone_id": 2, "role": "floor_ledge"},
]
KEY = np.array([0.42, -0.18, 0.89], dtype=np.float32)
KEY /= np.linalg.norm(KEY)

# UE-side recipe mirrored from setup_trimsheet_instances.py (MI_Trimsheet_* family)
UE_RECIPES = {
    "TS_Melodia_Stone": {
        "profile": "TP_Stone",
        "vectors": {"BaseTint": (1.0, 1.0, 1.0, 1.0)},
        "scalars": {"LayerBlend": 0.30, "Roughness": 0.68, "Metallic": 0.04,
                    "NormalStrength": 1.15, "MacroVariationStrength": 0.22},
    },
    "TS_Melodia_Music": {
        "profile": "TP_Default",
        "vectors": {"BaseTint": (1.0, 0.97, 1.0, 1.0)},
        "scalars": {"LayerBlend": 0.25, "Roughness": 0.55, "Metallic": 0.03,
                    "NormalStrength": 1.0, "MacroVariationStrength": 0.18},
    },
    "TS_Melodia_Dream": {
        "profile": "TP_Default",
        "vectors": {"BaseTint": (0.95, 0.92, 1.0, 1.0)},
        "scalars": {"LayerBlend": 0.28, "Roughness": 0.50, "Metallic": 0.05,
                    "NormalStrength": 1.1, "MacroVariationStrength": 0.20},
    },
}


def sample_palette():
    pal = dict(FALLBACK_PALETTE)
    for key, mat_name in SCENE_MAT_SOURCES.items():
        m = bpy.data.materials.get(mat_name)
        if m is None or not m.use_nodes:
            continue
        for node in m.node_tree.nodes:
            if node.type == 'BSDF_PRINCIPLED' and "Base Color" in node.inputs:
                rgb = tuple(float(v) for v in node.inputs["Base Color"].default_value[:3])
                if max(rgb) > 0.0:
                    pal[key] = rgb
                break
    return pal


def _snoise(size, cells, seed):
    r = np.random.default_rng(seed)
    g = r.random((cells + 1, cells + 1)).astype(np.float32)
    ys, xs = np.mgrid[0:size, 0:size]
    fx, fy = xs / size * cells, ys / size * cells
    x0, y0 = np.floor(fx).astype(int), np.floor(fy).astype(int)
    tx, ty = fx - x0, fy - y0
    sx, sy = tx * tx * (3 - 2 * tx), ty * ty * (3 - 2 * ty)
    top = g[y0, x0] * (1 - sx) + g[y0, x0 + 1] * sx
    bot = g[y0 + 1, x0] * (1 - sx) + g[y0 + 1, x0 + 1] * sx
    return (top * (1 - sy) + bot * sy).astype(np.float32)


def _fbm(size, seed, octaves=4, base_cells=4):
    out = np.zeros((size, size), dtype=np.float32)
    amp = np.float32(0.5)
    for i in range(octaves):
        out += amp * _snoise(size, base_cells * 2 ** i, seed + 7 * i)
        amp *= np.float32(0.5)
    return out


class Canvas:
    def __init__(self, pal):
        self.pal = {k: np.array(v, dtype=np.float32) for k, v in pal.items()}
        self.alb = np.zeros((S, S, 3), dtype=np.float32)
        self.h = np.full((S, S), 0.5, dtype=np.float32)
        self.rough = np.full((S, S), 0.6, dtype=np.float32)
        self.metal = np.zeros((S, S), dtype=np.float32)

    def fill(self, y0, y1, color, h=0.5, rough=0.6, metal=0.0):
        self.alb[y0:y1] = color
        self.h[y0:y1] = h
        self.rough[y0:y1] = rough
        self.metal[y0:y1] = metal

    def block(self, x0, y0, w, hgt, color, hh, bevel=4, rough=0.6, metal=0.0):
        w = min(w, S - x0); hgt = min(hgt, S - y0)
        if w <= 0 or hgt <= 0:
            return
        y1 = y0 + hgt
        self.alb[y0:y1, x0:x0 + w] = color
        self.h[y0:y1, x0:x0 + w] = hh
        self.rough[y0:y1, x0:x0 + w] = rough
        self.metal[y0:y1, x0:x0 + w] = metal
        sub = self.h[y0:y1, x0:x0 + w].copy()
        base = hh - 0.10
        for i in range(min(bevel, hgt)):
            t = i / bevel
            sub[i, :] = np.maximum(sub[i, :], base + (hh - base) * t)
            sub[hgt - 1 - i, :] = np.minimum(sub[hgt - 1 - i, :], hh - (hh - base) * (1 - t))
        for j in range(min(bevel, w)):
            t = j / bevel
            sub[:, j] = np.maximum(sub[:, j], base + (hh - base) * t)
            sub[:, w - 1 - j] = np.minimum(sub[:, w - 1 - j], hh - (hh - base) * (1 - t))
        self.h[y0:y1, x0:x0 + w] = sub

    def recess(self, x0, y0, w, hgt, floor_h, color, rim_h, bevel=5):
        w = min(w, S - x0); hgt = min(hgt, S - y0)
        if w <= 0 or hgt <= 0:
            return
        y1 = y0 + hgt
        self.alb[y0:y1, x0:x0 + w] = color
        self.h[y0:y1, x0:x0 + w] = rim_h
        sub = self.h[y0:y1, x0:x0 + w].copy()
        for i in range(min(bevel, hgt // 2)):
            val = rim_h - (rim_h - floor_h) * i / bevel
            sub[i, :] = val; sub[hgt - 1 - i, :] = val
        for j in range(min(bevel, w // 2)):
            val = rim_h - (rim_h - floor_h) * j / bevel
            sub[:, j] = np.minimum(sub[:, j], val)
            sub[:, w - 1 - j] = np.minimum(sub[:, w - 1 - j], val)
        sub[bevel:hgt - bevel, bevel:w - bevel] = floor_h
        self.h[y0:y1, x0:x0 + w] = sub
        self.alb[y0 + bevel:y1 - bevel, x0 + bevel:x0 + w - bevel] *= 0.94

    def veins(self, y0, y1, color, count=12, seed=2, alpha=0.55, width=1.5):
        r = np.random.default_rng(seed)
        for _ in range(count):
            y = float(r.integers(y0 + 2, y1 - 2))
            amp = r.uniform(2.0, 6.0)
            f1, f2 = r.uniform(0.006, 0.014), r.uniform(0.02, 0.05)
            ph1, ph2 = r.uniform(0, 6.3), r.uniform(0, 6.3)
            xs = np.arange(S)
            yy = np.clip((y + amp * np.sin(xs * f1 + ph1) + amp * 0.4 * np.sin(xs * f2 + ph2)).round().astype(int), y0, y1 - 1)
            self.alb[yy, xs] = self.alb[yy, xs] * (1 - alpha) + color * alpha
            self.h[yy, xs] = np.maximum(self.h[yy, xs], self.h[yy, xs].mean() + 0.04)

    def stroke(self, y0, y1, seed, strength=0.06):
        n1 = _fbm(S, seed)[y0:y1]
        n1 = (n1 - n1.min()) / max(1e-6, float(n1.max() - n1.min()))
        streak = _snoise(S, 96, seed + 3)[y0:y1]
        streak = (streak - streak.min()) / max(1e-6, float(streak.max() - streak.min()))
        wob = (1.0 - strength * n1 - strength * 0.6 * streak)[..., None]
        self.alb[y0:y1] *= wob.astype(np.float32)
        self.h[y0:y1] += ((n1 - 0.5) * 0.015).astype(np.float32)

    def sparkles(self, y0, y1, count=24, seed=9, size=3):
        r = np.random.default_rng(seed)
        cols, rows = 8, max(1, count // 8)
        star = np.array([1.0, 0.985, 0.93], dtype=np.float32)
        for i in range(cols):
            for j in range(rows):
                cx = int((i + 0.5) * S / cols + r.integers(-12, 13))
                cy = int(y0 + 6 + (j + 0.5) * (y1 - y0 - 12) / rows + r.integers(-6, 7))
                cx = int(np.clip(cx, size + 1, S - size - 2))
                cy = int(np.clip(cy, y0 + size + 1, y1 - size - 2))
                for d in range(1, size + 1):
                    self.alb[cy, cx - d:cx + d + 1] = star
                    self.alb[cy - d:cy + d + 1, cx] = star
                    self.h[cy, cx - d:cx + d + 1] += 0.02
                    self.h[cy - d:cy + d + 1, cx] += 0.02
                self.alb[cy - 1:cy + 2, cx - 1:cx + 2] = np.array([1.0, 1.0, 0.97], dtype=np.float32)


def _architecture(c: Canvas, tint):
    st, mb = c.pal["stone"] * tint, c.pal["marble"] * tint
    y0, y1 = Y_CORNICE
    c.fill(y0, y0 + 26, mb, h=0.78, rough=0.45)
    c.recess(0, y0 + 26, S, 20, 0.40, st * 0.96, rim_h=0.62, bevel=4)
    c.fill(y0 + 46, y0 + 98, st * 0.90, h=0.40, rough=0.70)
    for px in range(8, S, 64):
        c.block(px, y0 + 46, 44, 52, st * 0.985, 0.72, bevel=4, rough=0.55)
        c.recess(px + 44, y0 + 46, 20, 52, 0.30, st * 0.86, rim_h=0.52, bevel=3)
    c.fill(y0 + 98, y1, st * 0.94, h=0.55, rough=0.60)
    c.stroke(y0, y1, 41)

    y0, y1 = Y_BODY
    c.fill(y0, y1, st * 0.88, h=0.50, rough=0.80)
    for px in range(0, S, 256):
        m = 52
        c.recess(px + m, y0 + 30, 256 - 2 * m, (y1 - y0) - 60, 0.28, st * 0.94, rim_h=0.56, bevel=7)
        c.recess(px + m + 22, y0 + 52, 256 - 2 * (m + 22), (y1 - y0) - 104, 0.42, st, rim_h=0.60, bevel=4)
        c.block(px + m + 22, y0 + 52, 256 - 2 * (m + 22), 6, st * 1.04, 0.66, bevel=2)
        c.block(px + m + 22, y1 - 58, 256 - 2 * (m + 22), 6, st * 1.02, 0.64, bevel=2)
    c.stroke(y0, y1, 43, strength=0.07)

    y0, y1 = Y_WAIN
    c.fill(y0, y1, st * 0.92, h=0.55, rough=0.70)
    for px in range(0, S, 128):
        c.recess(px + 10, y0 + 10, 108, (y1 - y0) - 20, 0.40, st * 0.99, rim_h=0.58, bevel=4)
    c.block(0, y0 - 6, S, 8, mb, 0.70, bevel=3, rough=0.35)
    c.stroke(y0, y1, 47)

    y0, y1 = Y_BASE
    c.fill(y0, y1, st * 0.90, h=0.52, rough=0.60)
    c.block(0, y0 + 4, S, 16, st * 1.03, 0.72, bevel=4)
    c.recess(0, y0 + 26, S, 12, 0.34, st * 0.84, rim_h=0.52, bevel=3)
    c.block(0, y0 + 44, S, 26, st, 0.68, bevel=5)
    c.stroke(y0, y1, 51)

    y0, y1 = Y_FLOOR
    c.fill(y0, y1, mb, h=0.60, rough=0.25)
    for jx in range(0, S, 256):
        c.recess(max(0, jx - 2), y0, 5 if jx else 3, y1 - y0, 0.30, mb * 0.8, rim_h=0.5, bevel=2)
    c.veins(y0, y1, st * 0.66, count=8, seed=61, alpha=0.45)


def _hero_stone(c: Canvas, tint):
    y0, y1 = Y_HERO
    c.fill(y0, y1, c.pal["marble"], h=0.52, rough=0.30)
    for y in range(y0, y1):
        t = np.float32(y - y0) / (y1 - y0)
        c.alb[y] = c.pal["marble"] * (1 - 0.18 * t) + c.pal["stone"] * 0.92 * (0.18 * t)
    c.veins(y0 + 8, y1 - 8, c.pal["stone"] * 0.60, count=16, seed=12, alpha=0.5, width=1.2)
    yy, xx = np.mgrid[y0:y1, 0:S]
    for j, px in enumerate(range(32, S, 64)):
        d2 = (xx - px) ** 2 + ((yy - (y0 + 30)) * 1.25) ** 2
        m = (d2 < 130); c.alb[y0:y1][m] = c.pal["stone"] * 0.82; c.h[y0:y1][m] = 0.62
        r = (d2 >= 150) & (d2 < 205); c.h[y0:y1][r] = 0.34; c.alb[y0:y1][r] *= 0.74
        if j % 2:
            dd = (np.abs(xx - px - 32) + np.abs(yy - (y0 + 30)) * 1.4) < 16
            c.alb[y0:y1][dd] = c.pal["stone"] * 0.88; c.h[y0:y1][dd] = 0.58
    for px in range(128, S, 256):
        d2 = (xx - px) ** 2 + (yy - (y0 + 112)) ** 2
        for r_in, r_out, h_add, tone in ((0, 11, 0.18, 1.14), (11, 18, -0.12, 0.70),
                                          (18, 25, 0.14, 1.06), (25, 31, -0.10, 0.74),
                                          (31, 38, 0.08, 0.98)):
            m = (d2 >= r_in * r_in) & (d2 < r_out * r_out)
            c.alb[y0:y1][m] = (c.alb[y0:y1][m] * tone).clip(0, 1)
            c.h[y0:y1][m] += h_add
    c.stroke(y0, y1, 23)


def _hero_music(c: Canvas, tint):
    y0, y1 = Y_HERO
    c.fill(y0, y1, c.pal["pink"], h=0.50, rough=0.45)
    ink = np.array([0.12, 0.07, 0.14], dtype=np.float32)
    xs = np.arange(S)
    for i in range(5):
        y = y0 + 26 + i * 24
        yy = np.clip((y + 2.0 * np.sin(xs * 0.02 + i) + 1.5 * np.sin(xs * 0.071 + 2)).astype(int), y0, y0 + 120)
        c.alb[yy, xs] = ink
        c.alb[np.clip(yy + 1, y0, y1 - 1), xs] = ink * 1.6
        c.h[yy, xs] = 0.44
    for x in range(0, S, 256):
        c.alb[y0 + 26:y0 + 122, x:x + 4] = ink
        c.h[y0 + 26:y0 + 122, x:x + 4] = 0.42
        for nx, ny in [(x + 78, y0 + 74), (x + 140, y0 + 50), (x + 196, y0 + 98)]:
            yy, xx = np.mgrid[ny - 12:ny + 12, nx - 15:nx + 15]
            m = (((xx - nx) / 13) ** 2 + ((yy - ny) / 10) ** 2) <= 1
            reg = c.alb[ny - 12:ny + 12, nx - 15:nx + 15]
            rh = c.h[ny - 12:ny + 12, nx - 15:nx + 15]
            reg[m] = ink * 0.85; rh[m] = 0.66
            c.alb[ny - 12:ny + 12, nx - 15:nx + 15] = reg
            c.h[ny - 12:ny + 12, nx - 15:nx + 15] = rh
            c.alb[ny - 36:ny - 10, nx + 12:nx + 15] = ink
    ky0 = y1 - 46
    c.fill(ky0, y1, np.array([0.95, 0.92, 0.88], dtype=np.float32), h=0.66, rough=0.32)
    for x in range(0, S, 128):
        c.recess(x + 126, ky0, 3, y1 - ky0, 0.30, np.array([0.5, 0.47, 0.44], dtype=np.float32), rim_h=0.5, bevel=1)
        for i in range(5):
            if i in (2, 4):
                continue
            kx = x + int((i + 1) * 128 / 5) - 7
            c.alb[ky0 + 2:ky0 + 28, kx:kx + 13] = c.pal["dark"]
            c.h[ky0 + 2:ky0 + 28, kx:kx + 13] = 0.40
            c.rough[ky0 + 2:ky0 + 28, kx:kx + 13] = 0.22
    c.sparkles(y0 + 2, ky0 - 12, count=16, seed=17, size=2)
    c.stroke(y0, ky0, 29)


def _hero_dream(c: Canvas, tint):
    y0, y1 = Y_HERO
    hgt = y1 - y0
    t = np.linspace(0, 1, hgt, dtype=np.float32)[:, None, None]
    c.alb[y0:y1] = c.pal["roof_blue"][None, None, :] * (1 - t) + c.pal["pink"][None, None, :] * t
    ys, xs = np.mgrid[0:hgt, 0:S].astype(np.float32)
    c.h[y0:y1] = 0.50
    c.rough[y0:y1] = 0.40
    for row in range(3):
        yb = row * 64
        phase = (row % 2) * 32
        arc = np.sin((xs + phase) / 64.0 * 2 * np.pi) * 14 + (yb + 42)
        band = np.abs(ys - arc) < 3.0
        rr, cc = np.where(band)
        c.alb[y0 + rr, cc] = c.pal["roof_blue"] * 0.50
        c.h[y0 + rr, cc] = 0.36
        crest = (ys - arc >= 3.0) & (ys - arc < 5.5)
        rr, cc = np.where(crest)
        c.alb[y0 + rr, cc] = np.array([0.94, 0.92, 0.96], dtype=np.float32)
        c.h[y0 + rr, cc] = 0.58
    c.sparkles(y0 + 4, y0 + 92, count=24, seed=9, size=3)
    c.stroke(y0, y1, 37)


HEROES = {"TS_Melodia_Stone": _hero_stone, "TS_Melodia_Music": _hero_music,
          "TS_Melodia_Dream": _hero_dream}


def _shade(c: Canvas):
    dhdx = (np.roll(c.h, -1, 1) - np.roll(c.h, 1, 1)) * 0.5 * 6.0
    dhdy = (np.roll(c.h, -1, 0) - np.roll(c.h, 1, 0)) * 0.5 * 6.0
    nrm = np.stack([-dhdx, dhdy, np.ones_like(c.h)], axis=-1).astype(np.float32)
    nrm /= np.linalg.norm(nrm, axis=-1, keepdims=True)
    ndl = (nrm * KEY[None, None, :]).sum(-1).clip(0, 1)
    lp = c.h.copy()
    for _ in range(8):
        lp = (np.roll(lp, -1, 0) + np.roll(lp, 1, 0) + np.roll(lp, -1, 1) + np.roll(lp, 1, 1) + 4 * lp) / 8.0
    cav = (lp - c.h).clip(0, 0.12)[..., None] / 0.12
    edge = (c.h - lp).clip(0, 0.12)[..., None] / 0.12
    light = 1.0 + 0.45 * (ndl[..., None] - 0.55)
    cool = np.array([0.62, 0.68, 0.85], dtype=np.float32)
    warm = np.array([0.98, 0.93, 0.86], dtype=np.float32)
    out = c.alb * light
    out = out * (1 - cav * 0.45) + (c.alb * cool) * (cav * 0.45)
    out = (out + edge * 0.10 * warm).clip(0, 1)
    c.alb = out
    c.rough = (c.rough - edge[..., 0] * 0.06 + cav[..., 0] * 0.05).clip(0.05, 0.95)
    c.ao = (1.0 - cav[..., 0] / 1.0 * 0.80).clip(0.2, 1.0)
    c.nrm = nrm


def _l2s(a):
    a = np.clip(a, 0, 1)
    s = np.where(a <= 0.0031308, a * 12.92, 1.055 * np.power(a, 1 / 2.4) - 0.055)
    return (s * 255 + 0.5).astype(np.uint8)


def _save_png(arr, path, srgb):
    h, w = arr.shape[:2]
    img = bpy.data.images.new(os.path.basename(path), w, h, alpha=False, float_buffer=False)
    # colorspace FIRST, then pixels: re-assigning colorspace after foreach_set
    # reconverts the buffer and wipes it (headless Blender 5.2 — verified probe).
    img.colorspace_settings.name = 'sRGB' if srgb else 'Non-Color'
    rgba = np.empty((h, w, 4), dtype=np.float32)
    if arr.ndim == 2:
        rgba[..., :3] = (arr[..., None] / 255.0).astype(np.float32)
    else:
        rgba[..., :3] = arr.astype(np.float32) / 255.0
    rgba[..., 3] = 1.0
    # bpy pixels are BOTTOM-up; our canvas rows are top-down -> flip to match
    img.pixels.foreach_set(np.ascontiguousarray(rgba[::-1].ravel(), dtype=np.float32))
    img.filepath_raw = path
    img.file_format = 'PNG'
    img.save()
    bpy.data.images.remove(img)


def bake_all(out_dir, size_note=S):
    pal = sample_palette()
    os.makedirs(out_dir, exist_ok=True)
    mpath = os.path.join(out_dir, "trimsheet_manifest.json")
    existing = {}
    if os.path.exists(mpath):
        try:
            existing = json.load(open(mpath))
        except (ValueError, OSError):
            existing = {}
    manifest = existing
    manifest["size"] = size_note
    manifest["v_up"] = "top_of_image"
    manifest["bands"] = BANDS
    manifest["palette_sampled_from"] = {
        k: bpy.data.materials.get(v) is not None for k, v in SCENE_MAT_SOURCES.items()}
    # preserve hybrid/wear entries authored by other tools; replace only the
    # three base sheets this operator actually bakes.
    sheets = manifest.setdefault("sheets", {})
    tints = {"TS_Melodia_Stone": np.ones(3, dtype=np.float32),
             "TS_Melodia_Music": np.array([1.0, 0.97, 1.0], dtype=np.float32),
             "TS_Melodia_Dream": np.ones(3, dtype=np.float32)}
    for name, hero in HEROES.items():
        c = Canvas(pal)
        hero(c, tints[name])
        _architecture(c, tints[name])
        c.fill(Y_HERO[1] - 4, Y_HERO[1], c.pal["gold"], h=0.70, rough=0.24, metal=1.0)
        for y in (192, 320, 736, 832, 984):
            c.alb[y:y + 2] = np.array([0.10, 0.10, 0.12], dtype=np.float32)
            c.h[y:y + 2] = 0.20
        _shade(c)
        base = os.path.join(out_dir, name)
        _save_png(_l2s(c.alb), base + "_albedo.png", True)
        _save_png((c.h * 255).astype(np.uint8), base + "_height.png", False)
        _save_png(((c.nrm * 0.5 + 0.5) * 255).astype(np.uint8), base + "_normal.png", False)
        orm = np.dstack([(c.ao * 255).astype(np.uint8),
                         (c.rough * 255).astype(np.uint8),
                         (c.metal * 255).astype(np.uint8)])
        _save_png(orm, base + "_orm.png", False)
        zone = np.zeros((S, S), dtype=np.uint8)
        for b in BANDS:
            zone[b["v_px"][0]:b["v_px"][1]] = b["zone_id"]
        _save_png(zone * 30, base + "_zone.png", False)
        manifest["sheets"][name] = {
            "maps": ["albedo", "height", "normal", "orm", "zone"],
            "ue": UE_RECIPES[name],
            "ue_target_master": "/Game/EnvSandbox/Materials/Masters/M_Master_Toon_Universal",
            "ue_folder": "/Game/EnvSandbox/Materials/Instances/Environment/Stylized",
        }
    with open(os.path.join(out_dir, "trimsheet_manifest.json"), "w") as f:
        json.dump(manifest, f, indent=1)
    return manifest


# ------------------------------------------------------ proxy materials ---
def _recipe_for(name, out_dir=None):
    """UE recipe from the manifest (schema 2 SSOT) if present, else builtin."""
    base = UE_RECIPES.get(name)
    roots = [out_dir] if out_dir else []
    roots.append(_default_out_dir())
    for r in roots:
        if not r:
            continue
        mp = os.path.join(r, "trimsheet_manifest.json")
        if os.path.exists(mp):
            try:
                m = json.load(open(mp))
                info = m.get("sheets", {}).get(name)
                if info and "ue" in info:
                    rec = dict(info["ue"])
                    rec.setdefault("vectors", {})
                    rec.setdefault("scalars", base["scalars"] if base else {})
                    return rec
            except (ValueError, OSError):
                pass
    return base


def make_proxy_material(name, out_dir, true_color=False):
    """Blender-side stand-in for the UE MI built from the sheet's recipe.
    Mirrors M_Master_Toon_Universal behavior: BaseTint * albedo, 3-step toon
    N·L ramp, ORM channels, normal + height bump. Returns the material."""
    d = os.path.join(out_dir, f"{name}_")
    recipe = _recipe_for(name, out_dir) or UE_RECIPES["TS_Melodia_Stone"]
    mat = bpy.data.materials.get(f"PROXY_{name}")
    if mat:
        bpy.data.materials.remove(mat)
    mat = bpy.data.materials.new(f"PROXY_{name}")
    mat.use_nodes = True
    nt = mat.node_tree
    bsdf = next(n for n in nt.nodes if n.type == 'BSDF_PRINCIPLED')
    out = next(n for n in nt.nodes if n.type == 'OUTPUT_MATERIAL')

    def load(png, srgb):
        im = bpy.data.images.load(png, check_existing=False)
        im.colorspace_settings.name = 'sRGB' if srgb else 'Non-Color'
        return im

    uv = nt.nodes.new('ShaderNodeUVMap'); uv.location = (-1500, 200)
    mapn = nt.nodes.new('ShaderNodeMapping'); mapn.location = (-1300, 200)
    nt.links.new(uv.outputs['UV'], mapn.inputs['Vector'])

    tex = nt.nodes.new('ShaderNodeTexImage'); tex.location = (-900, 500)
    tex.image = load(d + "albedo.png", True)
    nt.links.new(mapn.outputs['Vector'], tex.inputs['Vector'])
    orm_n = nt.nodes.new('ShaderNodeTexImage'); orm_n.location = (-900, 150)
    orm_n.image = load(d + "orm.png", False)
    nt.links.new(mapn.outputs['Vector'], orm_n.inputs['Vector'])
    sep = nt.nodes.new('ShaderNodeSeparateColor'); sep.location = (-620, 150)
    nt.links.new(orm_n.outputs['Color'], sep.inputs['Color'])
    tint = (recipe.get("vectors") or {}).get("BaseTint", (1.0, 1.0, 1.0, 1.0))[:3]
    mul = nt.nodes.new('ShaderNodeMixRGB'); mul.location = (-620, 500)
    mul.blend_type = 'MULTIPLY'; mul.inputs['Fac'].default_value = 1.0
    mul.inputs['Color2'].default_value = (*tint, 1.0)
    nt.links.new(tex.outputs['Color'], mul.inputs['Color1'])
    scalars = recipe.get("scalars") or {}
    nt.links.new(mul.outputs['Color'], bsdf.inputs['Base Color'])
    rr = nt.nodes.new('ShaderNodeMapRange'); rr.location = (-620, -120)
    rr.inputs['To Min'].default_value = scalars.get("Roughness", 0.6) * 0.82
    rr.inputs['To Max'].default_value = min(1.0, scalars.get("Roughness", 0.6) * 1.1)
    nt.links.new(sep.outputs['Green'], rr.inputs['Value'])
    nt.links.new(rr.outputs['Result'], bsdf.inputs['Roughness'])
    mm = nt.nodes.new('ShaderNodeMath'); mm.location = (-620, -320)
    mm.operation = 'MULTIPLY'
    mm.inputs[1].default_value = scalars.get("Metallic", 0.04) * 20.0  # sheet metal bits are 1.0 in B
    nt.links.new(sep.outputs['Blue'], mm.inputs[0])
    nt.links.new(mm.outputs[0], bsdf.inputs['Metallic'])
    if os.path.exists(d + "normal.png"):
        nrm = nt.nodes.new('ShaderNodeTexImage'); nrm.location = (-900, -250)
        nrm.image = load(d + "normal.png", False)
        nt.links.new(mapn.outputs['Vector'], nrm.inputs['Vector'])
        nm = nt.nodes.new('ShaderNodeNormalMap'); nm.location = (-620, -250)
        nm.inputs['Strength'].default_value = scalars.get("NormalStrength", 1.0)
        nt.links.new(nrm.outputs['Color'], nm.inputs['Color'])
        nt.links.new(nm.outputs['Normal'], bsdf.inputs['Normal'])
    if os.path.exists(d + "height.png"):
        htx = nt.nodes.new('ShaderNodeTexImage'); htx.location = (-900, -600)
        htx.image = load(d + "height.png", False)
        nt.links.new(mapn.outputs['Vector'], htx.inputs['Vector'])
        bp = nt.nodes.new('ShaderNodeBump'); bp.location = (-620, -550)
        bp.inputs['Strength'].default_value = 0.25
        bp.inputs['Distance'].default_value = 0.02
        nt.links.new(htx.outputs['Color'], bp.inputs['Height'])
        nt.links.new(bp.outputs['Normal'], bsdf.inputs['Normal'])
    if true_color:
        # unlit proof: albedo -> emission straight to surface
        emit_p = nt.nodes.new('ShaderNodeEmission'); emit_p.location = (0, 700)
        emit_p.inputs['Strength'].default_value = 1.0
        nt.links.new(tex.outputs['Color'], emit_p.inputs['Color'])
        nt.links.new(emit_p.outputs['Emission'], out.inputs['Surface'])
        return mat
    # 3-step toon ramp stand-in (matches TP_Stone-style banding, not POM).
    # Mix lit BSDF with an emission ramp keyed off a fixed view-space key.
    geom = nt.nodes.new('ShaderNodeNewGeometry'); geom.location = (-900, 800)
    dot = nt.nodes.new('ShaderNodeVectorMath'); dot.operation = 'DOT_PRODUCT'; dot.location = (-620, 800)
    dot.inputs[1].default_value = (0.42, -0.18, 0.89)
    nt.links.new(geom.outputs['Normal'], dot.inputs[0])
    ramp = nt.nodes.new('ShaderNodeValToRGB'); ramp.location = (-400, 800)
    ramp.color_ramp.interpolation = 'CONSTANT'
    els = ramp.color_ramp.elements
    els[0].position = 0.0
    els[0].color = (*tuple(float(v) * 0.55 for v in tint), 1.0)
    mid = els.new(0.5)
    mid.color = (0.75, 0.78, 0.9, 1.0)
    els[2].position = 0.9
    els[2].color = (1.0, 1.0, 1.0, 1.0)
    nt.links.new(dot.outputs['Value'], ramp.inputs['Fac'])
    mul2 = nt.nodes.new('ShaderNodeMixRGB'); mul2.location = (-150, 800)
    mul2.blend_type = 'MULTIPLY'; mul2.inputs['Fac'].default_value = 1.0
    nt.links.new(tex.outputs['Color'], mul2.inputs['Color1'])
    nt.links.new(ramp.outputs['Color'], mul2.inputs['Color2'])
    toon = nt.nodes.new('ShaderNodeEmission'); toon.location = (0, 800)
    nt.links.new(mul2.outputs['Color'], toon.inputs['Color'])
    mix = nt.nodes.new('ShaderNodeMixShader'); mix.location = (150, 400)
    mix.inputs['Fac'].default_value = 0.55  # toon amount dial
    nt.links.new(bsdf.outputs['BSDF'], mix.inputs[1])
    nt.links.new(toon.outputs['Emission'], mix.inputs[2])
    nt.links.new(mix.outputs['Shader'], out.inputs['Surface'])
    return mat


# ------------------------------------------------------------- operators ---
def _default_out_dir():
    rel = os.path.join("Saved", "TrimSheets", "out")
    if bpy.data.filepath:
        proj = os.path.dirname(bpy.data.filepath)
        while proj and os.path.dirname(proj) != proj:
            cand = os.path.join(proj, rel)
            if os.path.isdir(os.path.dirname(cand)) or os.path.basename(proj).lower().startswith("melodia"):
                return cand
            proj = os.path.dirname(proj)
    return os.path.join(os.path.expanduser("~"), "melodia_trimsheets", "out")


class MELTS_OT_bake(bpy.types.Operator):
    """Bake the 3 trim-sheet variants against the current scene palette"""
    bl_idname = "melodia_ts.bake"
    bl_label = "Bake Trim Sheet Variants"
    bl_options = {"REGISTER", "UNDO"}

    resolution: bpy.props.EnumProperty(
        name="Resolution", items=[("1024", "1024", ""), ("2048", "2048 (slow)", "")],
        default="1024")
    out_dir: bpy.props.StringProperty(name="Out Dir", subtype='DIR_PATH', default="")

    def execute(self, context):
        global S
        out = self.out_dir or _default_out_dir()
        target = int(self.resolution)
        if target != S:
            self.report({'WARNING'}, f"resolution {target} not wired; baking at {S}")
        manifest = bake_all(out)
        context.scene["melodia_ts_manifest_path"] = os.path.join(out, "trimsheet_manifest.json")
        self.report({'INFO'}, f"BAKED {len(manifest['sheets'])} sheets -> {out}")
        return {'FINISHED'}


class MELTS_OT_apply_proxy(bpy.types.Operator):
    """Assign UE-emulating proxy materials (toon ramp + ORM) to selected meshes"""
    bl_idname = "melodia_ts.apply_proxy"
    bl_label = "Apply UE Proxy Materials"
    bl_options = {"REGISTER", "UNDO"}

    true_color: bpy.props.BoolProperty(
        name="True Color", default=False,
        description="Unlit albedo (proofing) instead of the toon-ramp proxy")
    out_dir: bpy.props.StringProperty(name="Out Dir", subtype='DIR_PATH', default="")

    def execute(self, context):
        out = self.out_dir or context.scene.get("melodia_ts_manifest_path")
        if out:
            out = os.path.dirname(out) if out.endswith(".json") else out
        else:
            out = _default_out_dir()
        made = 0
        for obj in context.selected_editable_objects or []:
            if obj.type != 'MESH':
                continue
            slot_hint = obj.name
            name = next((v for v in TRIM_VARIANTS if v.split("_")[-1].lower() in slot_hint.lower()),
                        TRIM_VARIANTS[0])
            png = os.path.join(out, f"{name}_albedo.png")
            if not os.path.exists(png):
                self.report({'ERROR'}, f"No baked sheet at {out}; run Bake first")
                return {'CANCELLED'}
            mat = make_proxy_material(name, out, true_color=self.true_color)
            obj.data.materials.clear()
            obj.data.materials.append(mat)
            made += 1
        self.report({'INFO'}, f"PROXY applied to {made} object(s)")
        return {'FINISHED'} if made else {'CANCELLED'}


class MELTS_PT_panel(bpy.types.Panel):
    bl_label = "Trim Sheet Lab"
    bl_idname = "MELTS_PT_panel"
    bl_space_type = 'VIEW_3D'
    bl_region_type = 'UI'
    bl_category = N_PANEL_CATEGORY
    bl_options = {'DEFAULT_CLOSED'}

    def draw(self, context):
        layout = self.layout
        col = layout.column(align=True)
        col.operator(MELTS_OT_bake.bl_idname, icon='RENDER_STILL')
        col.operator(MELTS_OT_apply_proxy.bl_idname, icon='MATERIAL')
        row = layout.row()
        row.label(text="Proxy = look-match (toon ramp, ORM).")
        row.label(text="POM/height-compete stay engine-side.")


MELTS_CLASSES = (MELTS_OT_bake, MELTS_OT_apply_proxy, MELTS_PT_panel)


def register():
    for cls in MELTS_CLASSES:
        bpy.utils.register_class(cls)


def unregister():
    for cls in reversed(MELTS_CLASSES):
        bpy.utils.unregister_class(cls)
