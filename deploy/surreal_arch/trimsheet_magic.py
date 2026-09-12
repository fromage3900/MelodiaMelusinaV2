"""Magical trim-sheet generator for surreal lookdev — Melodia Studio build-time tool.

Extends the existing trim-sheet contract rather than replacing it. The three sheets
produced by ``Saved/TrimSheets/bake_trimsheets.py`` (TS_Melodia_Stone / Music / Dream)
define the band layout that ONE master material swaps between; the two sheets baked
here reuse that exact layout so a material can swap onto them with no UV work:

    HERO        0..192     zone 6   variant_hero
    CORNICE   192..320     zone 13  cornice_shelf
    BODY      320..736     zone 1   wall_panel_recess (tiles_u 4)
    WAINSCOT  736..832     zone 20  wainscot
    BASEBOARD 832..984     zone 11  baseboard
    FLOOR     984..1024    zone 2   floor_ledge

``assert_band_contract()`` re-reads a previously baked layout JSON and fails loudly if
the two ever drift, so the shared-master claim stays true.

New here relative to the existing sheets: a normal map derived from an accumulated
height field, and an emission map for the magical glow. Both are per-variant PNGs
alongside the existing albedo / ORM / zone / layout set.

Outputs per variant into ``Saved/TrimSheets/magic/out``:
    <name>_albedo.png    sRGB base colour
    <name>_orm.png       R=AO  G=roughness  B=metallic   (Non-Color)
    <name>_normal.png    tangent-space normal, OpenGL (+Y up)   (Non-Color)
    <name>_emission.png  emissive RGB, sRGB, black where no glow
    <name>_zone.png      R = band zone id * 30      (Non-Color)
    <name>_layout.json   band table + colourspace/normal-convention hints

Runs on the repo venv (``.venv/Scripts/python.exe``) which carries numpy + PIL.
Deliberately does NOT import bpy, so it is unit-testable offline and can run while
Blender is open. It is therefore not imported by ``surreal_arch/__init__.py`` —
Blender's bundled Python has numpy but no PIL.

Variants:
    TS_Melodia_Magic  crystal facets, glowing rune rows, violet->teal->gold wash
    TS_Melodia_Bloom  petal shingles, heart/star motif rows, pink->sky wash
"""

from __future__ import annotations

import json
import os
import sys

import numpy as np
from PIL import Image

OUT = r"P:/MelodiaMelusinaV2-Laptop/Saved/TrimSheets/magic/out"
REFERENCE_LAYOUT = r"P:/MelodiaMelusinaV2-Laptop/Saved/TrimSheets/out/TS_Melodia_Dream_layout.json"

S = 1024
NORMAL_STRENGTH = 2.2

# ---- palette (scene-linear) ----
ONYX = np.array([0.045, 0.043, 0.055])
STONE = np.array([0.78, 0.76, 0.72])
MARBLE = np.array([0.80, 0.80, 0.80])
GOLD = np.array([0.95, 0.85, 0.20])
GOLD_PALE = np.array([0.98, 0.92, 0.62])
VIOLET = np.array([0.42, 0.24, 0.72])
TEAL = np.array([0.16, 0.62, 0.68])
CYAN_GLOW = np.array([0.45, 0.92, 1.00])
PINK = np.array([0.92, 0.70, 0.86])
SKY = np.array([0.62, 0.80, 0.98])
ROSE_GLOW = np.array([1.00, 0.62, 0.86])
DARK = np.array([0.045, 0.040, 0.055])

# ---- band rows (V measured from the TOP of the image, matching the existing sheets) ----
Y_HERO = (0, 192)
Y_CORNICE = (192, 320)
Y_BODY = (320, 736)
Y_WAIN = (736, 832)
Y_BASE = (832, 984)
Y_FLOOR = (984, 1024)

BANDS = [
    {"v_px": list(Y_HERO), "zone_id": 6, "role": "variant_hero", "ue_slots": ["M_Trim_Hero"]},
    {"v_px": list(Y_CORNICE), "zone_id": 13, "role": "cornice_shelf", "ue_slots": ["M_Trim_Cornice"]},
    {"v_px": list(Y_BODY), "zone_id": 1, "role": "wall_panel_recess", "tiles_u": 4,
     "ue_slots": ["M_Trim_Panel_Recess"]},
    {"v_px": list(Y_WAIN), "zone_id": 20, "role": "wainscot", "ue_slots": ["M_Trim_Wainscot"]},
    {"v_px": list(Y_BASE), "zone_id": 11, "role": "baseboard", "ue_slots": ["M_Trim_Baseboard"]},
    {"v_px": list(Y_FLOOR), "zone_id": 2, "role": "floor_ledge", "ue_slots": ["M_Trim_Floor"]},
]


# --------------------------------------------------------------------------
# contract check
# --------------------------------------------------------------------------

def assert_band_contract():
    """Fail loudly if this module's band table drifts from an already-baked sheet."""
    if not os.path.exists(REFERENCE_LAYOUT):
        print("CONTRACT: reference layout absent (%s) - skipped" % REFERENCE_LAYOUT)
        return True
    with open(REFERENCE_LAYOUT, "r", encoding="utf-8") as fh:
        ref = json.load(fh)
    ref_bands = ref.get("bands", [])
    mine = [(b["v_px"][0], b["v_px"][1], b["zone_id"], b["role"]) for b in BANDS]
    theirs = [(b["v_px"][0], b["v_px"][1], b["zone_id"], b["role"]) for b in ref_bands]
    if mine != theirs:
        print("CONTRACT MISMATCH")
        print("  mine  :", mine)
        print("  theirs:", theirs)
        return False
    if int(ref.get("size", 0)) != S:
        print("CONTRACT MISMATCH: reference size %s != %d" % (ref.get("size"), S))
        return False
    print("CONTRACT OK: band table matches %s" % os.path.basename(REFERENCE_LAYOUT))
    return True


# --------------------------------------------------------------------------
# encoding + noise
# --------------------------------------------------------------------------

def l2s(a):
    """Linear -> sRGB-encoded uint8."""
    a = np.clip(a, 0.0, 1.0)
    s = np.where(a <= 0.0031308, a * 12.92, 1.055 * np.power(a, 1 / 2.4) - 0.055)
    return (s * 255 + 0.5).astype(np.uint8)


def u8(a):
    return (np.clip(a, 0.0, 1.0) * 255 + 0.5).astype(np.uint8)


def value_noise(size, cells, seed):
    r = np.random.default_rng(seed)
    g = r.random((cells + 1, cells + 1))
    ys, xs = np.mgrid[0:size, 0:size]
    fx, fy = xs / size * cells, ys / size * cells
    x0, y0 = fx.astype(int), fy.astype(int)
    tx, ty = fx - x0, fy - y0
    sx, sy = tx * tx * (3 - 2 * tx), ty * ty * (3 - 2 * ty)
    top = g[y0, x0] * (1 - sx) + g[y0, x0 + 1] * sx
    bot = g[y0 + 1, x0] * (1 - sx) + g[y0 + 1, x0 + 1] * sx
    return top * (1 - sy) + bot * sy


def fbm(size, seed, octaves=4):
    out = np.zeros((size, size), dtype=float)
    amp = 0.5
    for i in range(octaves):
        out += amp * value_noise(size, 4 * 2 ** i, seed + 7 * i)
        amp *= 0.5
    return out


def edge_dist(h, w):
    ys = np.minimum(np.arange(h), h - 1 - np.arange(h))[:, None] * np.ones((1, w))
    xs = np.ones((h, 1)) * np.minimum(np.arange(w), w - 1 - np.arange(w))[None, :]
    return np.minimum(ys, xs)


# --------------------------------------------------------------------------
# stamping primitives — every stamp also writes the height field
# --------------------------------------------------------------------------

def stamp(base, height, x, y, w, h, color, lift=0.0, groove=6, dark=0.45, bevel=1.0):
    """Rectangle with a bevel-groove edge ramp; `lift` raises it in the height field."""
    x, y = int(x), int(y)
    w, h = int(min(w, S - x)), int(min(h, S - y))
    if w <= 0 or h <= 0:
        return
    patch = np.tile(np.asarray(color, dtype=float), (h, w, 1))
    d = np.clip(edge_dist(h, w) / max(1, groove), 0.0, 1.0)
    shade = 1.0 - (1.0 - d)[..., None] * dark
    base[y:y + h, x:x + w] = patch * shade
    if lift != 0.0:
        height[y:y + h, x:x + w] += lift * d * bevel


def band_fill(base, height, y0, y1, color, lift=0.0):
    base[y0:y1] = np.asarray(color, dtype=float)
    if lift:
        height[y0:y1] += lift


def disc(base, height, cx, cy, r, color, lift=0.0, ring=None):
    ys, xs = np.mgrid[0:S, 0:S]
    d2 = (xs - cx) ** 2 + (ys - cy) ** 2
    m = d2 <= r * r
    base[m] = np.asarray(color, dtype=float)
    if lift:
        height[m] += lift
    if ring:
        rr, rc, rl = ring
        m2 = (d2 > rr[0] ** 2) & (d2 <= rr[1] ** 2)
        base[m2] = np.asarray(rc, dtype=float)
        if rl:
            height[m2] += rl


def _clip_xy(cx, cy, margin):
    cx = int(np.clip(cx, margin, S - 1 - margin))
    cy = int(np.clip(cy, margin, S - 1 - margin))
    return cx, cy


def glyph_dot(base, height, emis, cx, cy, r, color, glow, lift=0.0):
    """A glowing round rune dot."""
    cx, cy = _clip_xy(cx, cy, int(r) + 1)
    ys, xs = np.mgrid[0:S, 0:S]
    d2 = (xs - cx) ** 2 + (ys - cy) ** 2
    m = d2 <= r * r
    base[m] = np.asarray(color, dtype=float)
    emis[m] = np.asarray(glow, dtype=float)
    core = d2 <= (r * 0.45) ** 2
    emis[core] = np.clip(np.asarray(glow, dtype=float) * 1.6, 0, 1)
    if lift:
        height[m] += lift


def glyph_star(base, height, emis, cx, cy, arm, color, glow=None, lift=0.0):
    cx, cy = _clip_xy(cx, cy, int(arm) + 2)
    for d in range(1, arm + 1):
        base[cy, cx - d:cx + d + 1] = color
        base[cy - d:cy + d + 1, cx] = color
        if lift:
            height[cy, cx - d:cx + d + 1] += lift
            height[cy - d:cy + d + 1, cx] += lift
        if glow is not None:
            emis[cy, cx - d:cx + d + 1] = glow
            emis[cy - d:cy + d + 1, cx] = glow
    base[cy - 1:cy + 2, cx - 1:cx + 2] = np.array([1.0, 1.0, 0.97])
    if glow is not None:
        emis[cy - 1:cy + 2, cx - 1:cx + 2] = np.clip(np.asarray(glow) * 1.4, 0, 1)


def glyph_heart(base, height, cx, cy, size, color, lift=0.0):
    """Plump heart glyph built from two lobes and a point, in the style of the decor."""
    ys, xs = np.mgrid[0:S, 0:S]
    lx, ly, lr = size * 0.40, size * 0.22, size * 0.52
    d = np.minimum((xs - (cx - lx)) ** 2 + (ys - (cy - ly)) ** 2,
                   (xs - (cx + lx)) ** 2 + (ys - (cy - ly)) ** 2)
    m = d <= lr * lr
    tri_h = size * 1.35
    t = np.clip((xs - (cx - size * 0.86)) / (size * 1.72), 0.0, 1.0)
    width = (1.0 - t) * size * 0.90
    m |= (ys > cy - ly) & (ys < (cy - ly) + tri_h) & (np.abs(xs - cx) <= width)
    base[m] = np.asarray(color, dtype=float)
    if lift:
        height[m] += lift


def magic_veins(base, height, emis, y0, y1, color, glow, count=9, seed=5, thick=2):
    r = np.random.default_rng(seed)
    for _ in range(count):
        y = int(r.integers(y0 + 3, y1 - 3))
        amp = r.uniform(2.0, 6.0)
        freq = r.uniform(0.006, 0.018)
        ph = r.uniform(0.0, 6.283)
        xs = np.arange(0, S)
        yy = np.clip((y + amp * np.sin(xs * freq + ph)).astype(int), y0, y1 - 1)
        base[yy, xs] = color
        height[yy, xs] += 0.35
        if glow is not None and r.random() < 0.55:
            emis[yy, xs] = glow


# --------------------------------------------------------------------------
# architecture bands (magic flavour)
# --------------------------------------------------------------------------

def draw_architecture(base, height, emis, rough, metal, tint, glow_rgb):
    # CORNICE: stepped crystal shelf with prism dentils
    y0, y1 = Y_CORNICE
    band_fill(base, height, y0, y0 + 38, MARBLE * tint, lift=0.55)
    stamp(base, height, 0, y0, S, 38, MARBLE * tint, lift=0.10, groove=4)
    stamp(base, height, 0, y0 + 38, S, 26, STONE * tint * 1.02, lift=0.30, groove=6)
    for px in range(0, S, 64):
        stamp(base, height, px + 12, y0 + 64, 40, (y1 - y0) - 64, STONE * tint * 0.86,
              lift=-0.35, groove=5)
        if (px // 64) % 2 == 0:
            emis[y0 + 70:y1 - 8, px + 26:px + 30] = np.asarray(glow_rgb) * 0.85
    rough[y0:y1] = 0.42

    # BODY: four recessed panels carrying a facet diamond + a glowing centre seam
    y0, y1 = Y_BODY
    band_fill(base, height, y0, y1, STONE * tint * 0.78)
    for px in range(0, S, 256):
        m = 56
        stamp(base, height, px + m, y0 + 26, 256 - 2 * m, (y1 - y0) - 52,
              STONE * tint, lift=-0.55, groove=9, dark=0.35)
        stamp(base, height, px + m + 16, y0 + 42, 256 - 2 * (m + 16), (y1 - y0) - 84,
              STONE * tint * 0.93, lift=-0.20, groove=6, dark=0.30)
        cx = px + 128
        cy = y0 + (y1 - y0) // 2
        # facet diamond: four triangles read as a cut gem face
        ys, xs = np.mgrid[0:S, 0:S]
        half = 52
        dx = np.abs(xs - cx) / half
        dy = np.abs(ys - cy) / half
        face = (dx + dy) <= 1.0
        base[face] = STONE * tint * 0.72
        height[face] += 0.30
        inner = (dx + dy) <= 0.55
        base[inner] = STONE * tint * 0.62
        height[inner] += 0.30
        core = (dx + dy) <= 0.20
        base[core] = GOLD_PALE * 0.9
        emis[core] = np.asarray(glow_rgb) * 0.55
        height[core] += 0.40
    g = np.clip(fbm(S, 3)[y0:y1], 0, 1)
    base[y0:y1] *= (0.95 + 0.10 * g)[..., None]
    rough[y0:y1] = 0.72 - 0.10 * g
    magic_veins(base, height, emis, y0, y1, STONE * tint * 0.66, np.asarray(glow_rgb) * 0.5,
                count=6, seed=17)

    # WAINSCOT: a rune arcade
    y0, y1 = Y_WAIN
    band_fill(base, height, y0, y1, STONE * tint * 0.90)
    for px in range(0, S, 128):
        stamp(base, height, px + 8, y0 + 8, 112, (y1 - y0) - 16, STONE * tint * 0.98,
              lift=-0.18, groove=5, dark=0.30)
        glyph_dot(base, height, emis, px + 64, y0 + (y1 - y0) // 2, 9,
                  GOLD_PALE * 0.95, np.asarray(glow_rgb) * 0.45, lift=0.25)
    rough[y0:y1] = 0.62

    # BASEBOARD: moulded shelf with a recessed glow line
    y0, y1 = Y_BASE
    band_fill(base, height, y0, y1, STONE * tint * 0.85)
    stamp(base, height, 0, y0, S, int((y1 - y0) * 0.18), STONE * tint * 0.66,
          lift=-0.45, groove=4)
    stamp(base, height, 0, y0 + int((y1 - y0) * 0.45), S, int((y1 - y0) * 0.22),
          STONE * tint, lift=0.35, groove=5)
    gy = y0 + int((y1 - y0) * 0.74)
    base[gy:gy + 3, :] = GOLD_PALE * 0.85
    emis[gy:gy + 3, :] = np.asarray(glow_rgb) * 0.40
    rough[y0:y1] = 0.55

    # FLOOR LEDGE: dark polished slab with gold veins
    y0, y1 = Y_FLOOR
    band_fill(base, height, y0, y1, ONYX * 2.4, lift=0.15)
    magic_veins(base, height, emis, y0, y1, GOLD * 0.70, np.asarray(glow_rgb) * 0.75,
                count=7, seed=41, thick=1)
    rough[y0:y1] = 0.18


# --------------------------------------------------------------------------
# hero painters
# --------------------------------------------------------------------------

def hero_magic(base, height, emis, rough, metal, tint):
    """Violet -> teal -> gold vertical wash, crystal facets, glowing rune row."""
    y0, y1 = Y_HERO
    h = y1 - y0
    for y in range(h):
        t = y / h
        if t < 0.55:
            c = VIOLET * (1 - t / 0.55) + TEAL * (t / 0.55)
        else:
            c = TEAL * (1 - (t - 0.55) / 0.45) + GOLD * 0.75 * ((t - 0.55) / 0.45)
        base[y0 + y] = c
    # faceted crystal row: alternating rhombi with a bright core
    ys, xs = np.mgrid[0:S, 0:S]
    for i, cx in enumerate(range(48, S, 96)):
        cy = y0 + 74
        half = 34
        dx = np.abs(xs - cx) / half
        dy = np.abs(ys - cy) / (half * 1.35)
        m = (dx + dy) <= 1.0
        base[m] = STONE * 0.55 + VIOLET * 0.35
        height[m] += 0.85
        inner = (dx + dy) <= 0.45
        base[inner] = GOLD_PALE * 0.92
        emis[inner] = np.array([0.85, 0.95, 1.00])
        height[inner] += 0.5
    # glowing rune dots between the crystals
    for cx in range(96, S, 96):
        glyph_dot(base, height, emis, cx, y0 + 140, 7, GOLD_PALE,
                  np.array([0.70, 0.95, 1.00]), lift=0.30)
    # star dither confined to a clean row, not a haze
    r = np.random.default_rng(9)
    for i in range(10):
        cx = int((i + 0.5) * S / 10 + r.integers(-12, 13))
        glyph_star(base, height, emis, cx, y0 + 30, 3, np.array([1.0, 0.99, 0.94]),
                   glow=np.array([0.85, 0.92, 1.0]), lift=0.25)
    rough[y0:y1] = 0.30
    metal[y0:y1] = 0.15


def hero_bloom(base, height, emis, rough, metal, tint):
    """Pink -> sky wash with petal shingles, a heart motif row and gold rim."""
    y0, y1 = Y_HERO
    h = y1 - y0
    for y in range(h):
        t = y / h
        base[y0 + y] = PINK * (1 - t) + SKY * t
    # petal shingles: overlapping arcs
    ys, xs = np.mgrid[0:h, 0:S]
    for row in range(4):
        yb = row * 46
        phase = (row % 2) * 32
        arc = np.sin((xs + phase) / 64.0 * 2 * np.pi) * 12 + yb + 34
        line = np.abs(ys - arc) < 2.5
        idx = np.where(line & (ys < h))
        base[y0 + idx[0], idx[1]] = PINK * 0.62 + SKY * 0.20
        height[y0 + idx[0], idx[1]] += 0.35
    # heart motif row (ties to the hanging heart filigree decor)
    for cx in range(64, S, 128):
        glyph_heart(base, height, cx, y0 + 132, 30, PINK * 0.72, lift=0.55)
        glyph_star(base, height, emis, cx + 64, y0 + 132, 3, GOLD_PALE,
                   glow=np.array([1.0, 0.72, 0.88]), lift=0.3)
    rough[y0:y1] = 0.38
    metal[y0:y1] = 0.05


# --------------------------------------------------------------------------
# normal from height
# --------------------------------------------------------------------------

def normal_from_height(height, strength=NORMAL_STRENGTH):
    """Sobel-free central differences -> tangent-space normal, OpenGL (+Y up)."""
    gy, gx = np.gradient(height.astype(np.float64))
    nz = np.ones_like(gx)
    nx = -gx * strength * S / 64.0
    ny = gy * strength * S / 64.0
    ln = np.sqrt(nx * nx + ny * ny + nz * nz)
    return np.dstack([nx / ln * 0.5 + 0.5, ny / ln * 0.5 + 0.5, nz / ln * 0.5 + 0.5])


# --------------------------------------------------------------------------
# assemble
# --------------------------------------------------------------------------

def variant(name, hero, tint, glow_rgb):
    base = np.zeros((S, S, 3))
    height = np.zeros((S, S))
    emis = np.zeros((S, S, 3))
    rough = np.zeros((S, S))
    metal = np.zeros((S, S))
    zone = np.zeros((S, S), dtype=np.uint8)

    hero(base, height, emis, rough, metal, tint)
    draw_architecture(base, height, emis, rough, metal, tint, glow_rgb)

    for b in BANDS:
        zone[b["v_px"][0]:b["v_px"][1]] = b["zone_id"]

    # band separators (2 px silhouette lines, texel-snapped reads)
    for y0, _ in (Y_CORNICE, Y_BODY, Y_WAIN, Y_BASE, Y_FLOOR):
        base[y0:y0 + 2] = np.array([0.03, 0.03, 0.035])
        height[y0:y0 + 2] -= 0.6
    # unified gold hairline above the hero/cornice separator
    base[188:191, :] = GOLD
    metal[188:191, :] = 1.0
    rough[188:191] = 0.26
    emis[188:191, :] = np.asarray(glow_rgb) * 0.25

    os.makedirs(OUT, exist_ok=True)
    files = {}

    p = os.path.join(OUT, f"{name}_albedo.png")
    Image.fromarray(l2s(base)).save(p)
    files["albedo"] = os.path.basename(p)

    ao = np.ones((S, S))
    p = os.path.join(OUT, f"{name}_orm.png")
    Image.fromarray(np.dstack([u8(ao), u8(rough), u8(metal)])).save(p)
    files["orm"] = os.path.basename(p)

    p = os.path.join(OUT, f"{name}_normal.png")
    Image.fromarray(u8(normal_from_height(height))).save(p)
    files["normal"] = os.path.basename(p)

    p = os.path.join(OUT, f"{name}_emission.png")
    Image.fromarray(l2s(emis)).save(p)
    files["emission"] = os.path.basename(p)

    p = os.path.join(OUT, f"{name}_zone.png")
    Image.fromarray(zone * 30).save(p)
    files["zone"] = os.path.basename(p)

    meta = {
        "sheet": name,
        "size": S,
        "v_up": "top_of_image",
        "master_hint": "one master material, swap albedo+orm; zone R/30 = band id",
        "maps": files,
        "map_notes": {
            "albedo": "sRGB",
            "orm": "Non-Color, R=AO G=roughness B=metallic",
            "normal": "Non-Color, tangent space, OpenGL (+Y up)",
            "emission": "sRGB, black where no glow",
            "zone": "Non-Color, R = zone_id * 30",
        },
        "height_normal_strength": NORMAL_STRENGTH,
        "bands": BANDS,
    }
    p = os.path.join(OUT, f"{name}_layout.json")
    with open(p, "w", encoding="utf-8") as fh:
        json.dump(meta, fh, indent=1)
    files["layout"] = os.path.basename(p)

    print("BAKED %-20s albedo=%7d  normal=%7d  emission=%7d bytes"
          % (name,
             os.path.getsize(os.path.join(OUT, files["albedo"])),
             os.path.getsize(os.path.join(OUT, files["normal"])),
             os.path.getsize(os.path.join(OUT, files["emission"]))))
    return files


def contact_sheet(names):
    mont = Image.new("RGB", (S + 16, len(names) * (S // 2 + 14)), (24, 24, 28))
    for i, n in enumerate(names):
        im = Image.open(os.path.join(OUT, f"{n}_albedo.png")).resize((S, S // 2))
        mont.paste(im, (8, 4 + i * (S // 2 + 14)))
    p = os.path.join(OUT, "contact_magic_trimsheets.png")
    mont.save(p)
    print("CONTACT", p)


def main():
    ok = assert_band_contract()
    names = []
    variant("TS_Melodia_Magic", hero_magic, tint=np.ones(3), glow_rgb=CYAN_GLOW)
    names.append("TS_Melodia_Magic")
    variant("TS_Melodia_Bloom", hero_bloom, tint=np.array([1.0, 0.98, 1.0]), glow_rgb=ROSE_GLOW)
    names.append("TS_Melodia_Bloom")
    contact_sheet(names)
    print("MAGIC TRIMSHEETS DONE contract_ok=%s" % ok)
    return 0 if ok else 1


if __name__ == "__main__":
    sys.exit(main())
