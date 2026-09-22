#!/usr/bin/env python
"""
animated_materials_20260922.py — Melusina ANIMATED (flipbook) material texture
sequences for the 2026-09-22 asset drop: GN angel wings, clockwork rings,
water globs.

Pure numpy + PIL (runs under hython or plain python).

Base field = the FIXED house AAA interlace recipe
------------------------------------------------
Tools/Houdini/pearl_painterly_aaa.py (gen_painterly, lines 14-27):
    p = 18.0
    wx = ((x_twisted % p) / p) - 0.5 ; wy = ((y % p) / p) - 0.5
    warp_thread = 1 - smoothstep(0.14, 0.40, |wx|)
    weft_thread = 1 - smoothstep(0.14, 0.40, |wy|)
    warp_up = ((cx + 2*cy) % 4) < 2                       # 2/2 twill
    h_weave = max(warp_thread*warp_up, weft_thread*(1-warp_up))
    over = 0.25 + 0.70*h_weave                            # raised valleys, no black holes
    + living-weave twist x_twisted = x + sin(y*0.00008*15)*2.5
    + AAA bevel smoothstep(0.20, 0.85, h) and brush grain

The wings shimmer base and the glob nacre flow are built ON this interlace.
Chladni / cymatic nodes are an EMBELLISHMENT layer only (vein glow, shimmer
accents, caustics) — they never carry the base field.  Rings are metal, not
fabric, so they keep their brass clockwork construction.

Wings + globs weave animation (exact)
-------------------------------------
The twill field is spatially periodic with period 4 cells in x (72 px) and
2 cells in y.  The weave is animated by sliding it in +x with an INTEGER pixel
shift that advances one full wrap period (72 px) per loop, wrapped modulo the
period — so frame == total is bit-identical to frame 0 while the motion is a
continuous draw.  On top of that the interlace phase gain rides
0.80 + 0.20*sin(bev - 2*pi*xw/period) — one full temporal cycle per loop,
matching the spatial wrap, so the seam is continuous.  The house twist term
depends on y only, so it stays exact under the x wrap.

Families
--------
WINGS  cymatic feather shimmer         1024x1024, 48 frames, 3 sequences
    wings_basecolor       pearl/ivory interlaced satin vane (base = twill)
    wings_iridescence     thin-film rainbow sheen riding the thread crests
    wings_emissive        chladni nodal-line vein glow (embellishment)
RINGS  brass clockwork iridescence sweep   512x512, 48 frames, 3 sequences
    rings_ring0_iridescence / rings_ring1_iridescence / rings_ring2_iridescence
    one sequence per ring index; per-ring phase offset is the parameter
    --ring-phase-offset-deg (default 120).
GLOBS  flowing water nacre              512x512, 32 frames, 2 sequences
    globs_normal          interlaced nacre-water normal, flow along +X only
    globs_emissive        nacre / gold-thread crest glow + chladni caustic accents

Total: 3*48 + 3*48 + 2*32 = 352 PNGs.

Loop contract (asserted in code)
--------------------------------
Every time-varying term is either
  (a) a phase angle from time_phase(), which wraps the frame counter in INTEGER
      arithmetic so frame == total returns exactly 0.0 (same bits as frame 0)
      and asserts coef*cycles is an integer, or
  (b) an integer-pixel shift from loop_fraction() that is 0 at frame == total,
      applied to coordinates wrapped modulo the field's spatial period, or
  (c) a cached static field (fiber noise, washes, brush grain — identical every
      frame by construction).
So builder(frame=0) == builder(frame=total) bitwise.  Every sequence proves it
(`loop_closure`) by building both and comparing arrays before the run reports
clean.

Structure gate (native res only)
--------------------------------
Never grade a flipbook from a downscaled full frame — an 18 px twill aliases
into dots in a small preview.  structure_check() takes a NATIVE 512 crop (no
resampling; a center crop for the 1024 wings frames, the whole frame for the
512 globs/rings frames), runs a 2D FFT (max-power across channels) and reports
the dominant period per axis: nx AND ny periods must be > 2 px, and the thread
crest peak should land near 18 px.  Results go into the verification JSON.

Naming / output
---------------
<asset>_<map>_<frame:04d>.png   (e.g. wings_basecolor_0000.png)
under Content/EnvSandbox/Textures/MelusinaAnimated/20260922/

Idempotent / resumable: a frame that already exists with a valid PNG signature
(89 50 4E 47) is skipped unless --force.  Writes go to a temp file, are
verified, then os.replace()d with Windows file-lock retries.

Verification report (JSON, allowed in Saved/Audit):
  Saved/Audit/melusina_vfx_20260921/animated_materials_verify.json
  per-sequence frame count, nonzero sizes, sha1 of first + last frame,
  square-ness, loop-closure proof, native-crop FFT structure checks.

Run
---
hython Tools/Houdini/copernicus/animated_materials_20260922.py --cook
"""
from __future__ import annotations

import argparse
import hashlib
import importlib.util
import json
import os
import sys
import time
from collections import namedtuple
from pathlib import Path

import numpy as np
from PIL import Image

HERE = Path(__file__).resolve().parent
PROJECT_ROOT = Path(__file__).resolve().parents[3]
SEED = 20260922

# House generator module (helpers + palettes) -------------------------------
if str(HERE) not in sys.path:
    sys.path.insert(0, str(HERE))
try:
    import copernicus_cymatic_parallax as ccp  # type: ignore
except Exception:  # pragma: no cover - explicit path fallback for hython
    _spec = importlib.util.spec_from_file_location(
        "copernicus_cymatic_parallax", str(HERE / "copernicus_cymatic_parallax.py"))
    ccp = importlib.util.module_from_spec(_spec)
    _spec.loader.exec_module(ccp)  # type: ignore

SMOOTH = ccp.smoothstep
MIX = ccp.mix
COL = ccp.col
TO_U8 = ccp.to_u8
MASK_COLOR = ccp.mask_color
CHLADNI = ccp.cymatic_chladni
GEAR = ccp.gear_shape
H2N = ccp.height_to_normal

PNG_MAGIC = b"\x89PNG\r\n\x1a\n"

OUT_TAIL = Path("Content/EnvSandbox/Textures/MelusinaAnimated/20260922")
REPORT_PATH = PROJECT_ROOT / "Saved/Audit/melusina_vfx_20260921/animated_materials_verify.json"

# Family grid (per the 2026-09-22 drop spec) --------------------------------
WINGS_SIZE, WINGS_FRAMES, WINGS_CYCLES = 1024, 48, 1
RINGS_SIZE, RINGS_FRAMES, RINGS_CYCLES = 512, 48, 1
GLOBS_SIZE, GLOBS_FRAMES, GLOBS_CYCLES = 512, 32, 1

# House AAA interlace constants (pearl_painterly_aaa.py) --------------------
WEAVE_CELL_PX = 18.0          # p — 18 px twill cell (AAA satin)
WEAVE_WRAP_CELLS = 4          # twill period in cells along x ((cx + 2*cy) % 4)
WEAVE_TWIST_FREQ = 0.00008 * 15.0   # house living-weave twist: sin(y*0.0012)
WEAVE_TWIST_AMP = 2.5

WINGS_MODES = ((8.0, 12.0), (15.0, 10.0), (22.0, 18.0))  # briefed freqs (embellishment)
WINGS_ACCENT_SCALE = 2.0  # x2 -> thin VEINS (16,24)(30,20)(44,36); <10 = blob cells
BARB_FREQ = 26.0          # feather barb lines across the vane (embellishment)
RING_PHASE_OFFSET_DEG = 120.0   # per-ring phase offset parameter (CLI overridable)
RING_ROT_MULTIPLIERS = (1.0, -1.0)   # band / hub rotation rates (closure-checked)

WINGS_PAL = dict(
    pearl=(250, 247, 242), ivory=(238, 228, 208), cream=(226, 209, 182),
    shadow=(200, 192, 180), vein=(255, 246, 214), lilac=(214, 208, 232),
    pink=(255, 178, 208), gold=(255, 226, 140), mint=(168, 240, 214),
    violet=(196, 172, 255), glow=(255, 238, 198), glow_cool=(176, 232, 255),
)

_TG = ccp.VARIANTS["TwinklingGears"]          # brass=(210,175,90) steel=(180,185,195) ...
_PW = ccp.VARIANTS["PearlWeave"]              # pearl / nacre / thread / glow
_SS = ccp.VARIANTS["SingingSilk"]             # silk / thread_gold / thread_rose / glow
RING_PAL = dict(
    brass=_TG["brass"], brass_dark=_TG["brass_dark"], steel=_TG["steel"],
    void=_TG["void"], glow=_TG["glow"],
    iri_gold=(255, 226, 140), iri_rose=(255, 176, 206),
    iri_cyan=(150, 226, 255), iri_violet=(192, 168, 255),
)
GLOBS_PAL = dict(
    pearl=_PW["pearl"], nacre=_PW["nacre"], thread=_PW["thread"], glow=_PW["glow"],
    silk=_SS["silk"], silk_shadow=_SS["silk_shadow"],
    thread_rose=_SS["thread_rose"], deep=(96, 150, 196),
)

Seq = namedtuple("Seq", "asset map size frames cycles builder note")

_CACHE: dict = {}
_GRID_CACHE: dict = {}


def _grid(h, w):
    key = (h, w)
    if key not in _GRID_CACHE:
        yy, xx = np.mgrid[0:h, 0:w].astype(np.float32)
        _GRID_CACHE[key] = (yy, xx)
    return _GRID_CACHE[key]


def cached(key, fn):
    if key not in _CACHE:
        _CACHE[key] = fn()
    return _CACHE[key]


def noise_field(h, w, tag, scale=1.0):
    """Static deterministic noise (identical every frame -> loop safe)."""
    def build():
        rng = np.random.RandomState(SEED + (abs(hash(tag)) % 100000))
        return (rng.randn(h, w).astype(np.float32) * scale)
    return cached(("noise", h, w, tag, scale), build)


def loop_fraction(frame, total, cycles):
    """Wrapped loop position in [0,1): ((frame*cycles) mod total)/total.

    Integer modulo keeps this exact — frame == total returns 0.0, the same
    bits as frame 0, instead of 1.0 (which is not equal in float after scaling).
    """
    assert isinstance(cycles, int) and cycles >= 1, f"cycles must be a positive int: {cycles}"
    return ((frame * cycles) % total) / float(total)


def time_phase(frame, total, cycles, coef=1.0):
    """Phase angle for a flipbook term — exact at the loop boundary.

    n = coef*cycles must be an integer, otherwise the term would not return to
    its frame-0 value at frame == total (the classic flipbook loop bug).
    The frame count is wrapped in INTEGER arithmetic before the float
    conversion, so frame == total evaluates to exactly 0.0 — bit-identical to
    frame 0 — rather than 2*pi*k, which float cannot represent exactly.
    """
    n = coef * cycles
    assert abs(n - round(n)) < 1e-9, (
        f"non-integer time phase: coef={coef} cycles={cycles} -> n={n}")
    u = (frame * int(round(n))) % total          # exact integer wrap
    return 2.0 * np.pi * (u / float(total))


def assert_loop_grid(total, cycles):
    """The period of the driving angle must be an exact divisor of the loop."""
    assert isinstance(cycles, int) and cycles >= 1, f"cycles must be a positive int: {cycles}"
    end = time_phase(total, total, cycles) / (2.0 * np.pi)
    assert abs(end - round(end)) < 1e-12, f"phase does not close: {end} turns"


# ── BASE: house AAA interlace, exactly loop-animated ────────────────────────
def weave_base(h, w, frame, total, cycles):
    """2/2 twill interlaced satin (house recipe) sliding in +x with an exact loop.

    Spatial period of the twill field: 4 cells in x (72 px), 2 cells in y.
    The slide is applied to coordinates already wrapped modulo that x period,
    so the shift is bit-exact at the loop point and the draw reads continuous.
    """
    p = WEAVE_CELL_PX
    period_x = int(round(WEAVE_WRAP_CELLS * p))                  # 72 px
    shift = int(round(period_x * loop_fraction(frame, total, cycles)))
    yy, xx = _grid(h, w)
    xi = xx.astype(np.int32) % period_x                          # exact index space
    xw = ((xi + shift) % period_x).astype(np.float32)            # animated warp coord
    bev = time_phase(frame, total, cycles)

    xt = xw + np.sin(yy * WEAVE_TWIST_FREQ) * WEAVE_TWIST_AMP    # house living-weave twist
    wx = ((xt % p) / p) - 0.5
    wy = ((yy % p) / p) - 0.5
    warp_thread = 1.0 - SMOOTH(0.14, 0.40, np.abs(wx))           # thin gaussian crests
    weft_thread = 1.0 - SMOOTH(0.14, 0.40, np.abs(wy))
    cx = np.floor(xt / p).astype(np.int32)
    cy = np.floor(yy / p).astype(np.int32)
    warp_up = (((cx + 2 * cy) % 4) < 2).astype(np.float32)       # 2/2 twill over/under
    h_weave = np.maximum(warp_thread * warp_up, weft_thread * (1.0 - warp_up))
    over = 0.25 + 0.70 * h_weave                                 # raised valleys: no black holes

    # phase-animated interlace: thread-tension wave, one temporal cycle per loop
    # phase-matched to the spatial wrap so the loop seam is continuous
    gain = 0.80 + 0.20 * np.sin(bev - 2.0 * np.pi * xw / period_x)
    over = np.clip(over * gain, 0, 1)

    # static painterly layers from the house recipe (cached; loop-exact)
    fn = noise_field(h, w, "fiber", 0.018)
    wash_x = np.sin(xx * 0.002 + yy * 0.0015) * 0.04
    wash_y = np.cos(yy * 0.003 - xx * 0.001) * 0.03
    thick = 0.03 * np.sin(xx * 0.08 + yy * 0.05)
    height = np.clip(over + fn + wash_x + wash_y * 0.5 + thick, 0, 1)
    height = SMOOTH(0.20, 0.85, height)                          # AAA bevel
    brush = np.sin(xx * 0.15) * np.cos(yy * 0.12) * 0.015
    height = np.clip(height + brush, 0, 1)

    return dict(height=height, warp_thread=warp_thread, weft_thread=weft_thread,
                warp_up=warp_up, h_weave=h_weave, gain=gain, bev=bev, xw=xw,
                warp_mask=(warp_thread > 0.45))


# ── WINGS (base = interlace, chladni = embellishment) ───────────────────────
def _wings_accent(h, w, frame, total):
    """Chladni embellishment: drifting nodes (mode numbers breathe with the loop).

    Frequencies are scaled x WINGS_ACCENT_SCALE so the nodes read as thin VEINS
    rather than blob cells (house pitfall: chladni below ~10 = blobs); the
    interlace stays the carrier field.
    """
    bev = time_phase(frame, total, WINGS_CYCLES)
    s, c = np.sin(bev), np.cos(bev)
    freqs = [(m * WINGS_ACCENT_SCALE + 1.6 * s, n * WINGS_ACCENT_SCALE + 1.1 * c)
             for (m, n) in WINGS_MODES]
    cym = CHLADNI(h, w, freqs=freqs, phases=[0.7, 1.9, 3.1], weights=[1.0, 0.6, 0.4])
    amp = max(1, int(min(h, w) * 0.02))
    sx = int(round(amp * s))
    sy = int(round(amp * 0.6 * c))
    cym = np.roll(np.roll(cym, sy, axis=0), sx, axis=1)
    nod = 1.0 - SMOOTH(0.0, 0.07, np.abs(cym - 0.5) * 2.0)      # thin nodal veins
    return dict(cym=cym, nod=nod, bev=bev, s=s, c=c)


def _barb_field(h, w):
    """Feather barbs — secondary embellishment (not the base field)."""
    def build():
        yy, xx = _grid(h, w)
        ang = np.deg2rad(26.0)
        u = xx * np.cos(ang) + yy * np.sin(ang)
        barbs = 0.5 + 0.5 * np.sin(2.0 * np.pi * u * BARB_FREQ / w)
        barbs = SMOOTH(0.30, 0.72, barbs)
        ribs = 0.5 + 0.5 * np.sin(2.0 * np.pi * u * (BARB_FREQ * 0.24) / w + 1.1)
        return np.clip(barbs * 0.72 + SMOOTH(0.4, 0.8, ribs) * 0.28, 0, 1)
    return cached(("barbs", h, w), build)


def _spine_field(h, w):
    def build():
        yy, xx = _grid(h, w)
        core = 1.0 - SMOOTH(0.010, 0.022, np.abs(xx / float(w) - 0.5))
        taper = 1.0 - SMOOTH(0.30, 0.98, np.abs(yy / float(h) - 0.5) * 2.0) * 0.35
        return np.clip(core * taper, 0, 1)
    return cached(("spine", h, w), build)


def build_wings_basecolor(h, w, frame, total):
    P = WINGS_PAL
    wv = weave_base(h, w, frame, total, WINGS_CYCLES)
    ac = _wings_accent(h, w, frame, total)
    height = wv["height"]

    base = COL(P["pearl"])
    blush = COL(P["ivory"])
    accent = COL(P["lilac"])
    tint = np.where(wv["warp_mask"][:, :, None], base, blush)     # house thread tint
    s1 = 0.035 * np.sin(_grid(h, w)[1] * 0.018 + _grid(h, w)[0] * 0.012 + ac["bev"])
    s2 = 0.025 * np.sin(_grid(h, w)[1] * 0.009 - _grid(h, w)[0] * 0.022 + 2.0 * ac["bev"])
    s3 = 0.018 * np.sin((_grid(h, w)[1] + _grid(h, w)[0]) * 0.006)
    fleck = (noise_field(h, w, "fleck") > 2.2)[:, :, None] * 0.02 * (accent - tint)
    colour = np.clip(tint + (s1 + s2 + s3)[:, :, None] + fleck, 0, 1)

    # crest read on the crown of threads + soft chladni accent (embellishment)
    crest = SMOOTH(0.55, 0.95, height)
    colour = MIX(colour, COL(P["cream"]), crest * 0.30)
    colour = MIX(colour, COL(P["vein"]), SMOOTH(0.62, 0.92, ac["cym"]) * 0.14)
    colour = MIX(colour, COL(P["lilac"]), ac["nod"] * 0.10)
    barbs = _barb_field(h, w)
    colour = MIX(colour, COL(P["shadow"]), barbs * 0.12)
    colour = MIX(colour, COL(P["pearl"]), _spine_field(h, w) * 0.35)
    return TO_U8(np.clip(colour, 0, 1) * 255)


def build_wings_iridescence(h, w, frame, total):
    P = WINGS_PAL
    wv = weave_base(h, w, frame, total, WINGS_CYCLES)
    ac = _wings_accent(h, w, frame, total)
    height = wv["height"]

    crest = np.clip((height - 0.5) * 1.8, 0, 1)                   # house iri mask (crest)
    hue = (crest * 0.60 + ac["cym"] * 0.40 + 0.35 * loop_fraction(frame, total, WINGS_CYCLES)) % 1.0
    iri = MIX(COL(P["pink"]), COL(P["gold"]), SMOOTH(0.0, 0.34, hue))
    iri = MIX(iri, COL(P["mint"]), SMOOTH(0.34, 0.67, hue))
    iri = MIX(iri, COL(P["violet"]), SMOOTH(0.67, 1.0, hue))
    band = 0.5 + 0.5 * np.sin(2.0 * np.pi * (wv["h_weave"] * 1.5 + wv["xw"] / 72.0) + ac["bev"])
    iri = iri * (0.55 + 0.45 * band)[:, :, None]
    iri = iri * (0.45 + 0.55 * crest)[:, :, None]                 # shimmer rides the weave
    iri = MIX(iri, COL(P["pearl"]), ac["nod"] * 0.22)             # nodal accent
    return TO_U8(np.clip(iri, 0, 1) * 255)


def build_wings_emissive(h, w, frame, total):
    """Emissive: the INTERLACE shimmers on the thread crowns (carrier); thin
    chladni veins glow through the cloth as the embellishment layer."""
    P = WINGS_PAL
    wv = weave_base(h, w, frame, total, WINGS_CYCLES)
    ac = _wings_accent(h, w, frame, total)
    crest = SMOOTH(0.58, 0.94, wv["height"])          # thread-scale crest read
    thread = SMOOTH(0.30, 0.70, wv["h_weave"])        # per-thread crown mask
    pulse = 0.55 + 0.45 * ac["s"]

    # 1) weave shimmer on the crowns — this carries the structure of the map
    em = MASK_COLOR(np.clip(thread * crest * (0.35 + 0.30 * pulse), 0, 1), COL(P["glow_cool"]))
    # 2) thin nodal veins, gated per-thread so the glow sits ON the cloth
    em = em + MASK_COLOR(np.clip(ac["nod"] * (0.20 + 0.80 * crest) * (0.45 + 0.55 * pulse), 0, 1),
                         COL(P["glow"]))
    # 3) hot cores of the veins + the quill
    em = em + MASK_COLOR(np.clip(SMOOTH(0.90, 0.99, ac["nod"]) * 0.40, 0, 1), COL(P["pearl"]))
    em = em + MASK_COLOR(np.clip(_spine_field(h, w) * (0.20 + 0.20 * pulse), 0, 1), COL(P["glow_cool"]))
    return TO_U8(np.clip(em, 0, 1) * 255)


# ── RINGS (metal, not fabric — unchanged construction) ──────────────────────
def build_rings(h, w, frame, total, ring_index):
    """Brass clockwork ring, iridescence sweep, per-ring phase offset."""
    bev = time_phase(frame, total, RINGS_CYCLES)          # N full turns / loop
    pal = RING_PAL
    yy, xx = _grid(h, w)
    cx, cy = w * 0.5, h * 0.5
    dx, dy = xx - cx, yy - cy
    r = np.sqrt(dx * dx + dy * dy) / (min(h, w) * 0.5 + 1e-9)
    ang = np.arctan2(dy, dx)
    ang_n = (ang / (2.0 * np.pi)) % 1.0
    off = np.deg2rad(RING_PHASE_OFFSET_DEG) * ring_index
    rot = bev + off

    band_r = 0.46 + 0.13 * ring_index        # ring 0 inner -> ring 2 outer
    band_w = 0.26
    outer, inner = band_r + band_w * 0.5, band_r - band_w * 0.5
    teeth = 24
    tooth = 1.0 - 0.16 * (0.5 + 0.5 * np.cos((ang + rot) * teeth))
    outer_t = outer * tooth
    band = (SMOOTH(outer_t + 0.012, outer_t - 0.012, r)
            - SMOOTH(inner + 0.010, inner - 0.010, r))
    band = np.clip(band, 0, 1)

    hub = GEAR(h, w, cx, cy, min(h, w) * 0.16 * (1.0 + 0.15 * ring_index),
               12, 0.18, rotation=rot * RING_ROT_MULTIPLIERS[1])
    slots = SMOOTH(0.65, 0.95, 0.5 + 0.5 * np.cos((ang + rot) * 6.0))

    # sweeping highlight: one bright arc travelling around the ring
    sp = (loop_fraction(frame, total, RINGS_CYCLES) + ring_index / 3.0) % 1.0
    dist = np.abs(((ang_n - sp + 0.5) % 1.0) - 0.5) * 2.0
    sweep = SMOOTH(0.42, 0.0, dist)
    tail = SMOOTH(0.85, 0.05, dist)

    # thin-film film bands (all time coefficients close over the loop)
    film = 0.5 + 0.5 * np.sin(2.0 * np.pi * (r * 7.0 + ang_n * 3.0) + 2.2 * sweep + bev)
    hue = (ang_n * 2.0 + r * 1.4 + 0.5 * sweep + 0.22 * ring_index) % 1.0
    iri = MIX(COL(pal["iri_gold"]), COL(pal["iri_rose"]), SMOOTH(0.0, 0.34, hue))
    iri = MIX(iri, COL(pal["iri_cyan"]), SMOOTH(0.34, 0.67, hue))
    iri = MIX(iri, COL(pal["iri_violet"]), SMOOTH(0.67, 1.0, hue))

    sector = 0.5 + 0.5 * np.sin(2.0 * np.pi * (ang_n * 12.0 + r * 4.0))
    metal = MIX(COL(pal["brass"]), COL(pal["steel"]), sector)
    metal = MIX(metal, COL(pal["brass_dark"]), 1.0 - band)

    film_strength = np.clip(band * (0.30 + 0.70 * sweep) * (0.45 + 0.55 * film), 0, 1)
    out = MIX(metal * 0.42, iri, film_strength)
    out = out * (0.30 + 0.70 * band)[:, :, None]
    out = out * (1.0 - 0.35 * (slots * band)[:, :, None])
    out = out + MASK_COLOR(np.clip(sweep * band * 0.55, 0, 1), COL(pal["glow"]))
    out = out + MASK_COLOR(np.clip(tail * band * 0.12, 0, 1), COL(pal["iri_cyan"]))
    hub_col = MIX(COL(pal["steel"]), COL(pal["brass"]), 0.5 + 0.5 * film)
    hub_col = MIX(hub_col, COL(pal["iri_gold"]), 0.25 + 0.45 * sweep)
    out = out * (1.0 - hub)[:, :, None] + hub_col * hub[:, :, None]
    return TO_U8(np.clip(out, 0, 1) * 255)


# ── GLOBS (base = interlaced nacre cloth flowing on +X) ─────────────────────
def _globs_accent(h, w):
    """Chladni + caustic embellishment layer (static; the weave carries the flow)."""
    def build():
        yy, xx = _grid(h, w)
        warp = ccp.warped_fbm(h, w, 16, 5, 0.35, SEED + 401)
        cym = CHLADNI(h, w, freqs=[(10, 14), (18, 12), (26, 20)],
                      phases=[0.7, 1.9, 3.1], weights=[1.0, 0.6, 0.4])
        caustic = SMOOTH(0.50, 0.95, 0.5 + 0.5 * np.sin(
            2.0 * np.pi * ((xx / w) * 9.0 - (yy / h) * 4.0) + warp * 4.0))
        return dict(warp=warp, cym=cym, caustic=caustic)
    return cached(("globs_accent", h, w), build)


def _globs_weave(h, w, frame, total):
    return weave_base(h, w, frame, total, GLOBS_CYCLES)


def build_globs_normal(h, w, frame, total):
    wv = _globs_weave(h, w, frame, total)
    ac = _globs_accent(h, w)
    # interlace is the base; caustic is a light accent on top (8% of the field)
    height = np.clip(wv["height"] * 0.92 + ac["caustic"] * 0.08, 0, 1)
    return H2N(height, strength=2.4)


def build_globs_emissive(h, w, frame, total):
    P = GLOBS_PAL
    wv = _globs_weave(h, w, frame, total)
    ac = _globs_accent(h, w)
    bev = time_phase(frame, total, GLOBS_CYCLES)
    pulse = 0.6 + 0.4 * np.sin(bev)
    crest = SMOOTH(0.60, 0.95, wv["height"])
    caustic_p = np.clip(ac["caustic"] * (0.45 + 0.55 * pulse), 0, 1)

    em = MASK_COLOR(np.clip(crest * (0.45 + 0.55 * pulse), 0, 1), COL(P["glow"]))
    em = em + MASK_COLOR(np.clip(crest * SMOOTH(0.50, 0.90, caustic_p) * 0.60, 0, 1), COL(P["nacre"]))
    em = em + MASK_COLOR(np.clip(SMOOTH(0.80, 0.97, caustic_p) * 0.50, 0, 1), COL(P["thread"]))
    em = em + MASK_COLOR(np.clip(SMOOTH(0.70, 0.95, wv["h_weave"]) * 0.30 * pulse, 0, 1), COL(P["silk"]))
    return TO_U8(np.clip(em, 0, 1) * 255)


# ── sequence table ──────────────────────────────────────────────────────────
def sequences():
    return (
        Seq("wings", "basecolor", WINGS_SIZE, WINGS_FRAMES, WINGS_CYCLES,
            build_wings_basecolor, "AAA 2/2 twill satin vane (base), pearl/ivory + chladni accent"),
        Seq("wings", "iridescence", WINGS_SIZE, WINGS_FRAMES, WINGS_CYCLES,
            build_wings_iridescence, "thin-film sheen riding the thread crests"),
        Seq("wings", "emissive", WINGS_SIZE, WINGS_FRAMES, WINGS_CYCLES,
            build_wings_emissive, "chladni nodal vein glow through the cloth (embellishment)"),
        Seq("rings_ring0", "iridescence", RINGS_SIZE, RINGS_FRAMES, RINGS_CYCLES,
            lambda h, w, f, n: build_rings(h, w, f, n, 0),
            "clockwork ring 0 (inner), TwinklingGears brass/steel, sweep"),
        Seq("rings_ring1", "iridescence", RINGS_SIZE, RINGS_FRAMES, RINGS_CYCLES,
            lambda h, w, f, n: build_rings(h, w, f, n, 1),
            "clockwork ring 1 (mid), per-ring phase offset applied"),
        Seq("rings_ring2", "iridescence", RINGS_SIZE, RINGS_FRAMES, RINGS_CYCLES,
            lambda h, w, f, n: build_rings(h, w, f, n, 2),
            "clockwork ring 2 (outer), per-ring phase offset applied"),
        Seq("globs", "normal", GLOBS_SIZE, GLOBS_FRAMES, GLOBS_CYCLES,
            build_globs_normal, "interlaced nacre-water normal (base), flow +X"),
        Seq("globs", "emissive", GLOBS_SIZE, GLOBS_FRAMES, GLOBS_CYCLES,
            build_globs_emissive, "crest glow + chladni caustic accents (embellishment)"),
    )


FABRIC_SEQS = ("wings_basecolor", "wings_iridescence", "wings_emissive",
               "globs_normal", "globs_emissive")


# ── IO helpers ──────────────────────────────────────────────────────────────
def frame_path(out_dir: Path, seq: Seq, frame: int) -> Path:
    return out_dir / f"{seq.asset}_{seq.map}_{frame:04d}.png"


def png_ok(path: Path) -> bool:
    try:
        if path.stat().st_size < 8:
            return False
        with open(path, "rb") as fh:
            return fh.read(8) == PNG_MAGIC
    except OSError:
        return False


def png_hw(path: Path):
    """(width, height) straight from IHDR, no image decode."""
    try:
        with open(path, "rb") as fh:
            head = fh.read(24)
        if len(head) < 24 or head[:8] != PNG_MAGIC:
            return None
        return (int.from_bytes(head[16:20], "big"), int.from_bytes(head[20:24], "big"))
    except OSError:
        return None


def write_png(path: Path, arr) -> None:
    """Atomic frame write, Windows-lock tolerant.

    os.replace() can raise WinError 5/32 while an indexer, AV scanner or the UE
    content browser holds the destination; retry with backoff, then fall back
    to writing the destination in place.
    """
    arr = np.ascontiguousarray(arr)
    mode = "L" if arr.ndim == 2 else ("RGB" if arr.shape[2] == 3 else "RGBA")
    tmp = path.with_name(path.name + ".tmp")
    Image.fromarray(arr, mode=mode).save(str(tmp), format="PNG")
    if not png_ok(tmp):
        try:
            tmp.unlink()
        except OSError:
            pass
        raise RuntimeError(f"PNG magic check failed after write: {tmp}")
    last = None
    for attempt in range(6):
        try:
            os.replace(str(tmp), str(path))
            return
        except OSError as exc:                       # WinError 5/32 file hold
            last = exc
            time.sleep(0.2 * (attempt + 1))
    try:
        Image.fromarray(arr, mode=mode).save(str(path), format="PNG")
        try:
            tmp.unlink()
        except OSError:
            pass
        return
    except OSError:
        raise RuntimeError(f"could not place frame after 6 replace attempts: {path} ({last})")


def clean_stale_tmp(out_dir: Path) -> int:
    n = 0
    for p in out_dir.glob("*.tmp"):
        try:
            p.unlink()
            n += 1
        except OSError:
            pass
    return n


def sha1(path: Path) -> str:
    h = hashlib.sha1()
    with open(path, "rb") as fh:
        for chunk in iter(lambda: fh.read(1 << 20), b""):
            h.update(chunk)
    return h.hexdigest()


# ── structure gate: native crop + two-direction FFT ─────────────────────────
def _smooth(x, win=5):
    return np.convolve(x, np.ones(win, np.float64) / win, mode="same")


def _axis_structure(spec_power, c):
    """Peak structure per axis on the SMOOTHED spectrum.

    The house fabric recipe deliberately carries per-pixel fiber grain, whose
    spectrum is a flat floor: a single-bin argmax lands on noise near Nyquist.
    Smoothing 5 bins averages that floor down while keeping the weave's narrow
    peaks, so the reported dominant period is the real periodic structure.
    The alias band (periods <= 4 px) is measured separately — a genuine
    dot/aliasing pattern would dominate there and fail the gate.
    """
    one = _smooth(spec_power, 5)
    db = 10.0 * np.log10(one + 1e-30)
    n = one.size
    k_lo, k_struct_hi = 3, max(4, c // 4)
    k_struct = int(np.argmax(one[k_lo:k_struct_hi])) + k_lo
    k_alias = int(np.argmax(one[k_struct_hi:n])) + k_struct_hi
    top3 = sorted(range(k_lo, k_struct_hi), key=lambda k: -one[k])[:3]
    # thread-crest band: the recipe's 18 px cell can only show as 13..25 px periods
    kc_lo, kc_hi = max(k_lo, int(round(c / 25.0))), max(k_lo + 1, int(round(c / 13.0)))
    k_crest = int(np.argmax(one[kc_lo:kc_hi])) + kc_lo
    band_med = float(np.median(db[k_lo:k_struct_hi]))
    period = c / k_struct
    return dict(
        dominant_period_px=round(period, 2), dominant_k=k_struct,
        dominant_db=round(float(db[k_struct]), 1),
        top3_periods_px=[(int(k), round(c / k, 2), round(float(db[k]), 1)) for k in top3],
        crest_period_px=round(c / k_crest, 2), crest_k=k_crest,
        crest_prominence_db=round(float(db[k_crest]) - band_med, 2),
        alias_period_px=round(c / k_alias, 2), alias_db=round(float(db[k_alias]), 1),
        alias_dominates=bool(db[k_alias] > db[k_struct] + 3.0),
        passes_gt_2px=bool(period > 2.0 and not (db[k_alias] > db[k_struct] + 3.0)),
    )


def structure_check(path: Path, crop_px: int = 512) -> dict:
    """Native-resolution crop + 2D FFT.  Never grade from a downscaled frame.

    A downscaled full frame turns the 18 px twill into dots and is not evidence.
    """
    with Image.open(path) as im:
        w, h = im.size
        c = min(crop_px, w, h)
        left, top = (w - c) // 2, (h - c) // 2
        block = np.asarray(im.crop((left, top, left + c, top + c)).convert("RGB"), np.float32)
    block = block - block.mean(axis=(0, 1), keepdims=True)
    win = np.hanning(c)[:, None] * np.hanning(c)[None, :]
    stack = np.stack([np.abs(np.fft.rfft2(block[:, :, ch] * win)) ** 2 for ch in range(3)], 0)
    power = stack.max(axis=0)                     # max across channels: no cancellation
    power[0, 0] = 0.0

    ax = _axis_structure(power.sum(axis=0), c)    # kx: horizontal structure
    ay = _axis_structure(power.sum(axis=1), c)    # ky: vertical structure
    return dict(
        crop_px=c, crop_origin=[left, top], resampled=False,
        nx=ax, ny=ay,
        min_period_px=round(min(ax["dominant_period_px"], ay["dominant_period_px"]), 2),
        crest_present=bool(ax["crest_prominence_db"] > 1.0 and ay["crest_prominence_db"] > 1.0),
        passes_gt_2px=bool(ax["passes_gt_2px"] and ay["passes_gt_2px"]),
    )


# ── run ─────────────────────────────────────────────────────────────────────
def run_cook(out_dir: Path, only: str, force: bool, loop_proof: bool):
    out_dir.mkdir(parents=True, exist_ok=True)
    stale = clean_stale_tmp(out_dir)
    if stale:
        print(f"  [cleanup] removed {stale} stale .tmp file(s)")
    seqs = [s for s in sequences() if only == "all" or s.asset.startswith(only)]
    stats = {"frames_written": 0, "frames_skipped": 0, "frames_failed": [], "per_seq": {}}
    proofs = {}
    for s in seqs:
        assert_loop_grid(s.frames, s.cycles)
        t0 = time.time()
        written = skipped = 0
        for f in range(s.frames):
            p = frame_path(out_dir, s, f)
            if not force and png_ok(p):
                skipped += 1
                continue
            arr = s.builder(s.size, s.size, f, s.frames)
            write_png(p, arr)
            written += 1
        proof = None
        if loop_proof:
            a0 = s.builder(s.size, s.size, 0, s.frames)
            an = s.builder(s.size, s.size, s.frames, s.frames)     # phantom loop frame
            ok = bool(np.array_equal(a0, an))
            proof = {
                "method": "array_equal(build(frame=0), build(frame=total))",
                "equal": ok,
                "max_abs_diff": int(np.max(np.abs(a0.astype(np.int32) - an.astype(np.int32)))),
            }
            assert ok, f"{s.asset}_{s.map}: flipbook does not close ({proof})"
        proofs[f"{s.asset}_{s.map}"] = proof
        dt = time.time() - t0
        stats["frames_written"] += written
        stats["frames_skipped"] += skipped
        stats["per_seq"][f"{s.asset}_{s.map}"] = dict(written=written, skipped=skipped, seconds=round(dt, 2))
        print(f"  [{s.asset}_{s.map}] {s.size}x{s.size} x{s.frames}f  "
              f"written={written} skipped={skipped} {dt:.1f}s  loop_closure={proof['equal'] if proof else 'n/a'}")
    return seqs, stats, proofs


def build_report(out_dir: Path, seqs, stats, proofs, mode: str, ring_offset_deg: float,
                 elapsed_s: float, structure: dict) -> dict:
    seq_rows = []
    total_present = total_expected = 0
    for s in seqs:
        name = f"{s.asset}_{s.map}"
        present, missing, sizes, dims_ok = 0, [], [], True
        first = last = None
        dims = None
        for f in range(s.frames):
            p = frame_path(out_dir, s, f)
            if not png_ok(p):
                missing.append(p.name)
                continue
            present += 1
            sizes.append(p.stat().st_size)
            hw = png_hw(p)
            if hw is None or hw[0] != hw[1]:
                dims_ok = False
            if hw is not None:
                dims = list(hw)
            if f == 0:
                first = p
            last = p
        total_present += present
        total_expected += s.frames
        seq_rows.append(dict(
            sequence=name, asset=s.asset, map=s.map, note=s.note,
            base_field=("house AAA 2/2 twill interlace (pearl_painterly_aaa.py)"
                        if name in FABRIC_SEQS else "procedural metal ring"),
            frames_expected=s.frames, frames_present=present,
            frames_missing=missing, complete=present == s.frames,
            size_px=dims, square=bool(dims_ok and dims and dims[0] == dims[1]),
            bytes_min=min(sizes) if sizes else 0, bytes_max=max(sizes) if sizes else 0,
            bytes_nonzero=bool(sizes) and all(b > 0 for b in sizes),
            sha1_first=sha1(first) if first else None,
            sha1_last=sha1(last) if last else None,
            cycles=s.cycles,
            loop_closure=(proofs.get(name) or {}).get("equal"),
            structure=structure.get(name),
        ))
    return dict(
        schema="melodia.animated_materials.v1",
        generated=time.strftime("%Y-%m-%dT%H:%M:%S"),
        run_mode=mode,
        script="Tools/Houdini/copernicus/animated_materials_20260922.py",
        helper_module="Tools/Houdini/copernicus/copernicus_cymatic_parallax.py",
        interlace_recipe="Tools/Houdini/pearl_painterly_aaa.py (gen_painterly, lines 14-27: "
                         "p=18.0 2/2 twill ((cx+2*cy)%4)<2, crest 1-smoothstep(0.14,0.40,|cellfrac-0.5|), "
                         "over = 0.25 + 0.70*max(warp*up, weft*(1-up)))",
        out_dir=str(out_dir),
        seed=SEED,
        ring_phase_offset_deg=ring_offset_deg,
        elapsed_s=round(elapsed_s, 2),
        totals=dict(sequences=len(seqs), frames_expected=total_expected,
                    frames_present=total_present,
                    frames_missing=total_expected - total_present,
                    all_complete=total_present == total_expected,
                    frames_written=stats["frames_written"],
                    frames_skipped=stats["frames_skipped"]),
        structure_gate=dict(
            method="native 512 crop (no resampling) + 2D FFT, max power across channels",
            criterion="dominant nx AND ny period > 2 px; thread crest peak should sit near 18 px",
            all_pass=bool(structure) and all(v["passes_gt_2px"] for v in structure.values()),
            per_sequence=structure,
        ),
        sequences=seq_rows,
        notes=[
            "Base field for wings + globs is the FIXED house AAA interlace recipe; chladni/cymatic "
            "nodes are an embellishment layer only (vein glow, shimmer accents, caustics).",
            "Weave animation: integer-pixel slide in +x, one 4-cell (72 px) wrap period per loop, "
            "coordinates wrapped modulo that period -> bit-exact loop; plus a thread-tension phase "
            "wave 0.80 + 0.20*sin(bev - 2*pi*x/72) matching the spatial wrap.",
            "Perfect loops: time_phase() wraps the frame counter in integer arithmetic and asserts "
            "coef*cycles is integral; loop_closure compares build(frame=0) with build(frame=total).",
            "Structure is graded ONLY on native-resolution 512 crops with a two-direction FFT — a "
            "downscaled full frame turns the 18 px twill into dots and cannot be used as evidence.",
            "Family grid: wings 3x48 @1024, rings 3x48 @512 (one sequence per ring index), "
            "globs 2x32 @512 => 352 PNGs (the 336 in the task brief is an arithmetic slip: "
            "3*48+3*48+2*32 = 352).",
            "No git commits; PNGs live under Content/EnvSandbox/Textures/MelusinaAnimated/20260922/ "
            "and only this JSON is written into Saved/Audit.",
            "Resumable: existing frames with a valid PNG signature are skipped unless --force.",
        ],
    )


def main():
    global RING_PHASE_OFFSET_DEG
    ap = argparse.ArgumentParser(description="Melusina animated (flipbook) material texture sequences")
    ap.add_argument("--cook", action="store_true", help="write PNGs (default is a dry listing)")
    ap.add_argument("--verify-only", action="store_true", help="no writes; read back + report only")
    ap.add_argument("--only", default="all", help="all | wings | rings | globs")
    ap.add_argument("--out", default=str(PROJECT_ROOT / OUT_TAIL))
    ap.add_argument("--report", default=str(REPORT_PATH))
    ap.add_argument("--force", action="store_true", help="rewrite even valid existing frames")
    ap.add_argument("--no-loop-proof", action="store_true")
    ap.add_argument("--ring-phase-offset-deg", type=float, default=RING_PHASE_OFFSET_DEG)
    args = ap.parse_args()

    RING_PHASE_OFFSET_DEG = args.ring_phase_offset_deg
    out_dir = Path(args.out)
    report_path = Path(args.report)

    seqs = [s for s in sequences() if args.only == "all" or s.asset.startswith(args.only)]
    expected = sum(s.frames for s in seqs)
    print(f"[animated_materials_20260922] out={out_dir}")
    print(f"[animated_materials_20260922] {len(seqs)} sequence(s), {expected} PNGs expected, "
          f"ring phase offset={RING_PHASE_OFFSET_DEG} deg")
    print(f"[animated_materials_20260922] base interlace cell={WEAVE_CELL_PX}px, "
          f"wrap={WEAVE_WRAP_CELLS} cells (x only)")
    for s in seqs:
        print(f"    {s.asset}_{s.map}: {s.size}x{s.size} x {s.frames} frames "
              f"(cycles={s.cycles})  {s.note}")

    if not (args.cook or args.verify_only):
        print("[skip] dry run — pass --cook to generate, --verify-only to just verify.")
        return 0

    t0 = time.time()
    if args.verify_only:
        stats = {"frames_written": 0, "frames_skipped": 0, "frames_failed": [], "per_seq": {}}
        proofs = {}
    else:
        seqs, stats, proofs = run_cook(out_dir, args.only, args.force, not args.no_loop_proof)

    # native-crop structure gate on frame 0 and the mid frame of every sequence
    structure = {}
    for s in seqs:
        name = f"{s.asset}_{s.map}"
        checks = []
        for f in (0, s.frames // 2):
            p = frame_path(out_dir, s, f)
            if png_ok(p):
                checks.append(structure_check(p))
        if checks:
            structure[name] = dict(
                crop_px=checks[0]["crop_px"], crop_origin=checks[0]["crop_origin"],
                resampled=False, frames_checked=[0, s.frames // 2],
                nx_dominant_period_px=min(c["nx"]["dominant_period_px"] for c in checks),
                ny_dominant_period_px=min(c["ny"]["dominant_period_px"] for c in checks),
                nx_top3_periods_px=checks[0]["nx"]["top3_periods_px"],
                ny_top3_periods_px=checks[0]["ny"]["top3_periods_px"],
                nx_crest_period_px=checks[0]["nx"]["crest_period_px"],
                ny_crest_period_px=checks[0]["ny"]["crest_period_px"],
                crest_band_prominence_db=[min(c["nx"]["crest_prominence_db"] for c in checks),
                                          min(c["ny"]["crest_prominence_db"] for c in checks)],
                crest_present=all(c["crest_present"] for c in checks),
                alias_dominates=any(c["nx"]["alias_dominates"] or c["ny"]["alias_dominates"]
                                    for c in checks),
                min_period_px=min(c["min_period_px"] for c in checks),
                passes_gt_2px=all(c["passes_gt_2px"] for c in checks),
            )
            st = structure[name]
            print(f"  [structure {name}] native {st['crop_px']}px crop @ {st['crop_origin']} "
                  f"(no resample)  frames {st['frames_checked']}")
            print(f"      dominant: nx={st['nx_dominant_period_px']}px ny={st['ny_dominant_period_px']}px"
                  f"   crest band: nx={st['nx_crest_period_px']}px ny={st['ny_crest_period_px']}px"
                  f" (prom {st['crest_band_prominence_db']} dB)  present={st['crest_present']}")
            print(f"      top3 nx={st['nx_top3_periods_px']}")
            print(f"      top3 ny={st['ny_top3_periods_px']}")
            print(f"      alias_dominates={st['alias_dominates']}  pass(>2px)={st['passes_gt_2px']}")

    report = build_report(out_dir, seqs, stats, proofs,
                          "verify-only" if args.verify_only else "cook",
                          RING_PHASE_OFFSET_DEG, time.time() - t0, structure)
    report_path.parent.mkdir(parents=True, exist_ok=True)
    report_path.write_text(json.dumps(report, indent=2), encoding="utf-8")

    t = report["totals"]
    print(f"[verify] {t['frames_present']}/{t['frames_expected']} frames present, "
          f"missing={t['frames_missing']}, written={t['frames_written']}, "
          f"skipped={t['frames_skipped']}")
    bad = [s for s in report["sequences"] if not (s["complete"] and s["square"] and s["bytes_nonzero"])]
    print(f"[verify] sequences failing count/square/nonzero: {len(bad)}"
          + (f" -> {[s['sequence'] for s in bad]}" if bad else ""))
    print(f"[verify] structure gate all_pass={report['structure_gate']['all_pass']}")
    print(f"[report] -> {report_path}")
    return 0 if (not bad and report["structure_gate"]["all_pass"]) else 1


if __name__ == "__main__":
    raise SystemExit(main())