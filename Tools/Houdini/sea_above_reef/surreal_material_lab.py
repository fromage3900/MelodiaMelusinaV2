"""Surreal Material Lab — 6 insane tilable PBR experiments (1024).

COPs-equivalent cooks via periodic value noise / fBm / wrapped Voronoi / tileable
sines — every map is lattice-periodic, so opposite edges differ only by local
gradient (seam < 0.03 in normalized 0..1).

Materials:
  1) Holographic Mother-of-Pearl   (rainbow iridescence, nacre layers)
  2) Molten Gold Veins              (liquid metal in pearl)
  3) Void Velvet                    (deep black + star speckles)
  4) Biolum Dream Skin              (aqua-pink jellyfish bell veins)
  5) Stained Glass Memory           (fractured pastel glass + lead)
  6) Wet Marble Sorrow              (weeping water streaks on sorrow marble)

Each material emits 4 maps: BaseColor (sRGB, RGB), Normal (data, RGB OpenGL Y+),
Roughness (data, gray), Emissive (sRGB-ish, RGB; keep sRGB=true for tinted glow,
import note flags it as emissive).

Outputs: Saved/Audit/surreal_sweep/material_lab/
  T_Surreal_<Material>_{BaseColor,Normal,Roughness,Emissive}.png  (24 files)
  material_lab_manifest.json   schema melodia.surreal_material_lab.v1

Seam guarantee: every height/albedo field is built only from rc.periodic_*
/ rc.fbm / rc.tileable_sine / toroidal Voronoi — all period|size. No PIL
WrappedDraw seams; no random-dot scatter without wrapping. Manifest records
per-file seam levels and a normalized seam value; PASS < 0.03.

Run:
  python Tools/Houdini/sea_above_reef/surreal_material_lab.py
  python Tools/Houdini/sea_above_reef/surreal_material_lab.py --seed 1337 --size 1024
"""

import argparse
import colorsys
import math
import sys
from pathlib import Path
import datetime

import numpy as np

sys.path.insert(0, str(Path(__file__).resolve().parent))
import reef_common as rc  # noqa: E402

rc.require_pil()
from PIL import Image  # noqa: E402

SIZE = 1024
SEED = 20260829

PROJECT_ROOT = Path(__file__).resolve().parents[3]
OUT_DIR = PROJECT_ROOT / "Saved" / "Audit" / "surreal_sweep" / "material_lab"

# ---------------------------------------------------------------------------
# helpers
# ---------------------------------------------------------------------------

def _smoothstep(x):
    x = np.clip(x, 0.0, 1.0)
    return (x * x * (3.0 - 2.0 * x)).astype(np.float32)

def _hsv_to_rgb_vec(h, s, v):
    """Vectorized HSV->RGB h,s,v in [0,1] -> rgb float32 HxWx3."""
    # Use numpy vectorize via colorsys would be slow; use standard formula
    # hsv to rgb via 6 sectors
    h6 = (h * 6.0) % 6.0
    i = np.floor(h6).astype(np.int32)
    f = h6 - i
    p = v * (1.0 - s)
    q = v * (1.0 - s * f)
    t = v * (1.0 - s * (1.0 - f))
    # select per sector
    r = np.choose(i, [v, q, p, p, t, v])
    g = np.choose(i, [t, v, v, q, p, p])
    b = np.choose(i, [p, p, t, v, v, q])
    return np.stack([r, g, b], axis=-1).astype(np.float32)

def _seam_normalized(arr01):
    """Mean abs wrap-step in normalized 0..1; max of lr/tb. PASS <0.03."""
    a = arr01
    if a.ndim == 3:
        a = a.mean(axis=2)
    lr = float(np.mean(np.abs(a[:, 0] - a[:, -1])))
    tb = float(np.mean(np.abs(a[0, :] - a[-1, :])))
    return max(lr, tb), lr, tb

# ---------------------------------------------------------------------------
# Voronoi color-cell fill for stained glass (tileable, deterministic)
# ---------------------------------------------------------------------------

def _voronoi_cell_colors(size, period, jitter, hue_rng):
    """Return rgb pastel per-pixel by nearest jittered lattice point.

    size 1024, period 8..16 typical. Each lattice cell gets a pastel hue from
    hue_rng (numpy Generator, pre-seeded). Tileable via toroidal distance.
    Vectorized in tiles to avoid O(period^2) Python loops per pixel in pure numpy?
    We use block iteration with numpy broadcasting per chunk of rows to keep memory sane.
    """
    cell = size / period
    jr = hue_rng.random((period, period, 2)).astype(np.float32) * jitter + (1.0 - jitter) * 0.5
    # pastel per cell: hue from rng, sat 0.32 val 0.92
    hues = hue_rng.random((period, period)).astype(np.float32)
    # build rgb per cell
    cell_rgb = np.zeros((period, period, 3), np.float32)
    for y in range(period):
        for x in range(period):
            h = float(hues[y, x])
            r, g, b = colorsys.hsv_to_rgb(h, 0.32, 0.92)
            cell_rgb[y, x] = (r, g, b)
    # pastel tint variation: precomputed

    ys, xs = np.mgrid[0:size, 0:size].astype(np.float32)
    # For each pixel find nearest lattice point. Brute but with period<=16 it's 256 candidates
    # Vectorized: we compare in chunked row bands to keep memory < 256*1024*1024 floats
    out_rgb = np.zeros((size, size, 3), np.float32)
    best_d2 = np.full((size, size), 1e9, np.float32)
    best_y = np.zeros((size, size), np.int32)
    best_x = np.zeros((size, size), np.int32)
    # iterate over all lattice points, updating nearest
    for gy in range(period):
        for gx in range(period):
            px = (gx + jr[gy, gx, 0]) * cell
            py = (gy + jr[gy, gx, 1]) * cell
            dx = px - xs
            dy = py - ys
            dx = (dx + size * 0.5) % size - size * 0.5
            dy = (dy + size * 0.5) % size - size * 0.5
            d2 = dx * dx + dy * dy
            # also need to consider wrapped copies offset? toroidal dx already handles main wrap,
            # but Voronoi needs 9-neighbor search because nearest may be across tile edge via copy
            # Our toroidal dx/dy already maps to shortest wrapped distance, so single copy suffices.
            mask = d2 < best_d2
            best_d2[mask] = d2[mask]
            best_y[mask] = gy
            best_x[mask] = gx
    out_rgb = cell_rgb[best_y, best_x]
    # also return nearest distance normalized for lead generation
    dist = np.sqrt(best_d2) / cell
    # Also need second-nearest for edge width? We only have best; compute edge via distance field?
    # We'll compute a simple edge via fbm ridge later combined; dist alone suffices for lead thickness via threshold.
    return out_rgb, dist

# ---------------------------------------------------------------------------
# 1) Holographic Mother-of-Pearl
# ---------------------------------------------------------------------------

def _mat_mother_of_pearl(seed, size):
    rng = np.random.default_rng(seed + 11)
    # fbm base undulation
    dunes = rc.fbm(size, 8, 4, rng, gain=0.55)
    warp = rc.fbm(size, 16, 3, np.random.default_rng(seed + 12), gain=0.5)
    s1 = rc.tileable_sine(size, 7, 5, phase=0.3, warp=warp, warp_amp=0.9)
    s2 = rc.tileable_sine(size, 5, 9, phase=1.7, warp=warp, warp_amp=0.7)
    # nacre layers: fine interference
    fine = rc.fbm(size, 128, 2, np.random.default_rng(seed + 13), gain=0.6)
    # hue: iridescence = frac of weighted sum
    hue_field = (dunes * 0.55 + s1 * 0.40 + s2 * 0.35 + fine * 0.15) % 1.0
    # sweep hue slightly for rainbow
    hue_field = (hue_field * 0.85 + dunes * 0.15) % 1.0
    sat = np.clip(0.22 + 0.22 * s1 + 0.14 * (fine - 0.5), 0.18, 0.52).astype(np.float32)
    val = np.clip(0.88 + 0.10 * dunes + 0.06 * fine, 0.0, 1.0).astype(np.float32)
    # gentle pearlescent desaturation toward warm pearl in troughs
    pearl = np.array([0.94, 0.90, 0.88], np.float32)
    irid = _hsv_to_rgb_vec(hue_field, sat, val)
    # mix irid with pearl by a soft mask (highlights stay iridescent)
    mix = np.clip((dunes - 0.35) / 0.45, 0.0, 1.0)[..., None]
    albedo = irid * (0.55 + 0.45 * mix) + pearl[None, None, :] * (0.45 - 0.35 * mix)
    albedo = np.clip(albedo, 0.0, 1.0)
    # height: nacre layers + gentle warp
    height = (0.50 * dunes + 0.25 * s1 + 0.15 * s2 + 0.10 * fine).astype(np.float32)
    height = (height - height.min()) / (height.max() - height.min() + 1e-6)
    normal = rc.normal_from_height(height, strength=1.6)
    # roughness: mother-of-pearl is smooth, slight variation with interference
    rough = np.clip(0.28 + 0.10 * (s1 - 0.5) + 0.06 * (fine - 0.5), 0.18, 0.42).astype(np.float32)
    # emissive: faint pastel echo of iridescence (very dim)
    emissive = np.clip(irid * 0.12 * (0.6 + 0.4 * s1[..., None]), 0.0, 1.0)
    return {
        "T_Surreal_MotherPearl_BaseColor": (albedo, "rgb"),
        "T_Surreal_MotherPearl_Normal": (normal, "rgb"),
        "T_Surreal_MotherPearl_Roughness": (rough, "gray"),
        "T_Surreal_MotherPearl_Emissive": (emissive, "rgb"),
        "_height": height,
    }

# ---------------------------------------------------------------------------
# 2) Molten Gold Veins
# ---------------------------------------------------------------------------

def _mat_molten_gold(seed, size):
    rng = np.random.default_rng(seed + 21)
    pearl_base = np.array([0.91, 0.88, 0.83], np.float32)
    gold = np.array([0.83, 0.68, 0.22], np.float32)
    gold_hot = np.array([1.00, 0.84, 0.42], np.float32)
    dunes = rc.fbm(size, 8, 4, rng, gain=0.55)
    # gold veins: Voronoi edges at two scales
    f1a = rc.periodic_voronoi_f1(size, 16, 0.88, np.random.default_rng(seed + 22))
    f1b = rc.periodic_voronoi_f1(size, 32, 0.86, np.random.default_rng(seed + 23))
    edge_a = np.clip(1.0 - f1a * 3.4, 0.0, 1.0) ** 2.2
    edge_b = np.clip(1.0 - f1b * 4.0, 0.0, 1.0) ** 2.6
    # ridge veins from fbm
    ridge_src = rc.fbm(size, 32, 3, np.random.default_rng(seed + 24), gain=0.5)
    ridge = np.clip(1.0 - np.abs(ridge_src - 0.5) * 7.0, 0.0, 1.0) ** 1.8
    vein = np.clip(edge_a * 0.85 + edge_b * 0.55 + ridge * 0.45, 0.0, 1.0) ** 1.15
    vein = _smoothstep(np.clip((vein - 0.32) / 0.55, 0.0, 1.0))
    # liquid metal flow variation: warp veins with sine
    flow_warp = rc.fbm(size, 16, 2, np.random.default_rng(seed + 25), gain=0.5)
    # secondary hot core inside veins
    core = np.clip((vein - 0.55) / 0.45, 0.0, 1.0) ** 1.5
    albedo = pearl_base[None, None, :] * (1.0 - vein[..., None]) \
        + gold[None, None, :] * ((vein - core)[..., None]) \
        + gold_hot[None, None, :] * (core[..., None])
    # pearl tint variation
    albedo = albedo * (0.96 + 0.08 * dunes[..., None])
    albedo = np.clip(albedo, 0.0, 1.0)
    height = np.clip(dunes * 0.35 + vein * 0.65, 0.0, 1.0).astype(np.float32)
    normal = rc.normal_from_height(height, strength=2.8)
    rough = np.clip(0.42 - 0.26 * vein, 0.14, 0.50).astype(np.float32)
    # emissive: gold veins glow, hotter core brighter
    emissive = (gold[None, None, :] * (0.28 * vein[..., None]) +
                gold_hot[None, None, :] * (0.35 * core[..., None])).astype(np.float32)
    emissive = np.clip(emissive, 0.0, 1.0)
    return {
        "T_Surreal_MoltenGold_BaseColor": (albedo, "rgb"),
        "T_Surreal_MoltenGold_Normal": (normal, "rgb"),
        "T_Surreal_MoltenGold_Roughness": (rough, "gray"),
        "T_Surreal_MoltenGold_Emissive": (emissive, "rgb"),
        "_height": height,
    }

# ---------------------------------------------------------------------------
# 3) Void Velvet
# ---------------------------------------------------------------------------

def _mat_void_velvet(seed, size):
    rng = np.random.default_rng(seed + 31)
    # deep void base with subtle blue-black undulation
    base_noise = rc.fbm(size, 8, 4, rng, gain=0.55)
    base = np.array([0.03, 0.03, 0.07], np.float32)
    # stars: two scales of Voronoi minima (centers)
    f1s_small = rc.periodic_voronoi_f1(size, 64, 0.92, np.random.default_rng(seed + 32))
    f1s_large = rc.periodic_voronoi_f1(size, 16, 0.92, np.random.default_rng(seed + 33))
    # star mask: bright where very close to center (small F1)
    star_small = np.clip(1.0 - f1s_small * 6.0, 0.0, 1.0) ** 2.4
    star_large = np.clip(1.0 - f1s_large * 5.2, 0.0, 1.0) ** 2.8
    # threshold to keep stars sparse and crisp
    star_small = np.where(star_small > 0.58, star_small, 0.0)
    star_large = np.where(star_large > 0.62, star_large, 0.0)
    # twinkle variation: modulate by noise
    tw = rc.fbm(size, 32, 2, np.random.default_rng(seed + 34), gain=0.5)
    star_small *= (0.7 + 0.6 * tw)
    star_large *= (0.75 + 0.5 * tw)
    star = np.clip(star_small * 0.9 + star_large, 0.0, 1.0)
    star = np.clip(star, 0.0, 1.0)
    # color: stars pale blue-white with occasional warm
    warm = rc.fbm(size, 128, 1, np.random.default_rng(seed + 35), gain=0.5)
    star_cold = np.array([0.92, 0.94, 1.0], np.float32)
    star_warm = np.array([1.0, 0.92, 0.78], np.float32)
    star_tint = star_cold[None, None, :] * (1.0 - warm[..., None] * 0.35) + star_warm[None, None, :] * (warm[..., None] * 0.35)
    albedo = np.tile(base[None, None, :], (size, size, 1)) * (1.0 + (base_noise - 0.5)[..., None] * 0.35)
    albedo = albedo + star[..., None] * star_tint * (0.85 + 0.15 * tw[..., None])
    albedo = np.clip(albedo, 0.0, 1.0)
    # velvet microfiber: faint crosshatch via sines (very low amplitude)
    weave_warp = rc.fbm(size, 32, 2, np.random.default_rng(seed + 36), gain=0.5)
    weave_x = rc.tileable_sine(size, 64, 0, phase=0.0, warp=weave_warp, warp_amp=0.3)
    weave_y = rc.tileable_sine(size, 0, 64, phase=0.7, warp=weave_warp, warp_amp=0.3)
    weave = (weave_x * 0.5 + weave_y * 0.5) * 0.04
    height = np.clip(base_noise * 0.20 + weave * 0.80 + star * 0.15, 0.0, 1.0).astype(np.float32)
    normal = rc.normal_from_height(height, strength=0.9)
    rough = np.clip(0.92 - 0.55 * star, 0.25, 0.96).astype(np.float32)
    emissive = np.clip(star[..., None] * star_tint * (0.85 + 0.15 * tw[..., None]), 0.0, 1.0)
    return {
        "T_Surreal_VoidVelvet_BaseColor": (albedo, "rgb"),
        "T_Surreal_VoidVelvet_Normal": (normal, "rgb"),
        "T_Surreal_VoidVelvet_Roughness": (rough, "gray"),
        "T_Surreal_VoidVelvet_Emissive": (emissive, "rgb"),
        "_height": height,
    }

# ---------------------------------------------------------------------------
# 4) Biolum Dream Skin
# ---------------------------------------------------------------------------

def _mat_biolum_skin(seed, size):
    rng = np.random.default_rng(seed + 41)
    # translucent jelly base: aqua-pink blend
    base_aqua = np.array([0.62, 0.86, 0.84], np.float32)
    base_pink = np.array([0.92, 0.68, 0.78], np.float32)
    tint_noise = rc.fbm(size, 8, 4, rng, gain=0.55)
    warp = rc.fbm(size, 16, 3, np.random.default_rng(seed + 42), gain=0.5)
    # veins: ridge + Voronoi edges warped
    ridge_src = rc.fbm(size, 16, 4, np.random.default_rng(seed + 43), gain=0.55)
    ridge = np.clip(1.0 - np.abs(ridge_src - 0.5) * 7.5, 0.0, 1.0) ** 1.9
    # warp ridge by sine for organic curl
    curl = rc.tileable_sine(size, 6, 8, phase=0.9, warp=warp, warp_amp=0.8)
    ridge = np.clip(ridge * (0.65 + 0.70 * curl), 0.0, 1.0)
    f1 = rc.periodic_voronoi_f1(size, 32, 0.88, np.random.default_rng(seed + 44))
    edge = np.clip(1.0 - f1 * 3.6, 0.0, 1.0) ** 2.0
    # combine: ridge dominates, edge adds branching
    vein = np.clip(ridge * 0.75 + edge * 0.45, 0.0, 1.0)
    vein = _smoothstep(np.clip((vein - 0.28) / 0.55, 0.0, 1.0))
    # slight thickness variation with second sine
    thick = rc.tileable_sine(size, 12, 7, phase=2.1, warp=warp, warp_amp=0.5)
    vein = np.clip(vein * (0.85 + 0.30 * thick), 0.0, 1.0)
    # base blend
    base = base_aqua[None, None, :] * (1.0 - tint_noise[..., None] * 0.35) + base_pink[None, None, :] * (tint_noise[..., None] * 0.35)
    base = base * (0.92 + 0.08 * warp[..., None])
    # vein colors alternate aqua/pink along vein length
    aqua_vein = np.array([0.30, 0.92, 0.82], np.float32)
    pink_vein = np.array([1.00, 0.55, 0.78], np.float32)
    vein_hue = rc.fbm(size, 16, 2, np.random.default_rng(seed + 45), gain=0.5)
    vein_col = aqua_vein[None, None, :] * (1.0 - vein_hue[..., None]) + pink_vein[None, None, :] * (vein_hue[..., None])
    albedo = base * (1.0 - 0.55 * vein[..., None]) + vein_col * (0.55 * vein[..., None])
    # subsurface translucency hint: brighten slightly around veins
    albedo = albedo + 0.08 * (vein[..., None] * 0.5) * np.array([0.2, 0.4, 0.5], np.float32)
    albedo = np.clip(albedo, 0.0, 1.0)
    height = np.clip(vein * 0.85 + tint_noise * 0.15, 0.0, 1.0).astype(np.float32)
    normal = rc.normal_from_height(height, strength=2.2)
    rough = np.clip(0.26 + 0.12 * (1.0 - vein) - 0.08 * vein, 0.16, 0.42).astype(np.float32)
    # emissive: veins glow strongly, pulsing implied via brightness
    emissive = np.clip(vein[..., None] * vein_col * 0.72, 0.0, 1.0)
    # add soft bloom around veins
    bloom = np.clip(vein * 0.6, 0.0, 0.5)
    emissive = np.clip(emissive + bloom[..., None] * vein_col * 0.18, 0.0, 1.0)
    return {
        "T_Surreal_BiolumSkin_BaseColor": (albedo, "rgb"),
        "T_Surreal_BiolumSkin_Normal": (normal, "rgb"),
        "T_Surreal_BiolumSkin_Roughness": (rough, "gray"),
        "T_Surreal_BiolumSkin_Emissive": (emissive, "rgb"),
        "_height": height,
    }

# ---------------------------------------------------------------------------
# 5) Stained Glass Memory
# ---------------------------------------------------------------------------

def _mat_stained_glass(seed, size):
    # Voronoi cell colors + lead lines
    rng_cells = np.random.default_rng(seed + 51)
    cell_rgb, cell_dist = _voronoi_cell_colors(size, 12, 0.88, rng_cells)
    # cell_rgb is already pastel per-cell; add subtle mottle inside cells
    mottle = rc.fbm(size, 64, 2, np.random.default_rng(seed + 52), gain=0.5)
    cell_rgb = cell_rgb * (0.94 + 0.12 * mottle[..., None])
    cell_rgb = np.clip(cell_rgb, 0.0, 1.0)
    # lead lines: combination of cell boundary distance + fbm ridge
    f1 = rc.periodic_voronoi_f1(size, 16, 0.88, np.random.default_rng(seed + 53))
    # interior dist small; boundary ~0.5*cell where F1 large. Lead where F1 is in a band
    # Use band around F1 = 0.35..0.45
    def _band(f, c, w):
        return _smoothstep(1.0 - np.abs(f - c) / w)
    lead_voronoi = _band(f1, 0.38, 0.09) * 0.95
    # fbm crack lead for irregularity
    crack_src = rc.fbm(size, 32, 3, np.random.default_rng(seed + 54), gain=0.5)
    crack = np.clip(1.0 - np.abs(crack_src - 0.5) * 8.0, 0.0, 1.0) ** 1.7
    lead = np.clip(lead_voronoi * 0.85 + crack * 0.35, 0.0, 1.0)
    lead = _smoothstep(np.clip((lead - 0.25) / 0.60, 0.0, 1.0))
    # thickness control: sharpen
    lead = np.clip((lead - 0.30) / 0.70, 0.0, 1.0) ** 0.9
    lead = np.clip(lead, 0.0, 1.0)
    # lead color: dark aged lead, slight variation
    lead_col = np.array([0.11, 0.10, 0.09], np.float32)
    albedo = cell_rgb * (1.0 - lead[..., None]) + lead_col[None, None, :] * (lead[..., None])
    # add highlight bloom at glass centers (subtle)
    center_glow = np.clip(1.0 - f1 * 4.0, 0.0, 1.0) ** 2.2
    albedo = albedo + center_glow[..., None] * 0.07 * cell_rgb * (1.0 - lead[..., None])
    albedo = np.clip(albedo, 0.0, 1.0)
    # height: lead slightly raised (or recessed) - here lead is raised
    height = np.clip((1.0 - lead) * 0.55 + center_glow * 0.15 + mottle * 0.10, 0.0, 1.0).astype(np.float32)
    # invert so lead is valley: cracks carved
    height = 1.0 - height
    # soften height at lead for bevel
    height = np.clip(height + lead * 0.25, 0.0, 1.0)
    normal = rc.normal_from_height(height, strength=2.0)
    # roughness: glass smooth, lead rough
    rough = np.clip(0.14 + 0.62 * lead, 0.12, 0.80).astype(np.float32)
    # emissive: faint light leak at lead edges + glass translucency
    edge_light = _band(f1, 0.33, 0.07) * (1.0 - lead) * 0.5
    emissive = cell_rgb * (edge_light[..., None] * 0.18)
    # also slight overall glass glow
    emissive = emissive + cell_rgb * (center_glow[..., None] * 0.06) * 0.5
    emissive = np.clip(emissive, 0.0, 1.0)
    return {
        "T_Surreal_StainedGlass_BaseColor": (albedo, "rgb"),
        "T_Surreal_StainedGlass_Normal": (normal, "rgb"),
        "T_Surreal_StainedGlass_Roughness": (rough, "gray"),
        "T_Surreal_StainedGlass_Emissive": (emissive, "rgb"),
        "_height": height,
    }

# ---------------------------------------------------------------------------
# 6) Wet Marble Sorrow
# ---------------------------------------------------------------------------

def _mat_wet_marble(seed, size):
    rng = np.random.default_rng(seed + 61)
    # marble veins: warped diagonal sine + fbm
    warp = rc.fbm(size, 16, 4, np.random.default_rng(seed + 62), gain=0.55)
    marble_src = rc.tileable_sine(size, 5, 9, phase=0.4, warp=warp, warp_amp=1.2)
    # add second marble field
    marble_src2 = rc.tileable_sine(size, 8, 3, phase=1.9, warp=warp, warp_amp=0.9)
    marble = (marble_src * 0.6 + marble_src2 * 0.4)
    # sharpen into veins
    veins = np.clip(1.0 - np.abs(marble - 0.5) * 6.0, 0.0, 1.0) ** 1.6
    # add fbm veining
    fbm_v = rc.fbm(size, 32, 3, np.random.default_rng(seed + 63), gain=0.5)
    fbm_vein = np.clip(1.0 - np.abs(fbm_v - 0.5) * 7.0, 0.0, 1.0) ** 1.8
    veins = np.clip(veins * 0.65 + fbm_vein * 0.45, 0.0, 1.0)
    veins = _smoothstep(np.clip((veins - 0.22) / 0.65, 0.0, 1.0))
    # water streaks: vertical streaks (strongly anisotropic)
    # build stretched noise: compress y in noise lookup via indexing
    streak_base = rc.fbm(size, 32, 4, np.random.default_rng(seed + 64), gain=0.55)
    # shear to vertical: row-wise index shift using periodic row selection
    ys = np.arange(size)
    # Create vertical streaks by sampling streak_base with y-stretched coordinate
    # Use numpy indexing to stretch in y: repeat pattern vertically with scale 0.25
    # Instead do: generate stretched noise via tileable_sine vertical + fbm
    streak_sine = rc.tileable_sine(size, 28, 2, phase=0.6, warp=warp, warp_amp=0.6)
    streak = (streak_base * 0.45 + streak_sine * 0.55)
    # threshold to streaks
    streak_mask = np.clip((streak - 0.62) / 0.28, 0.0, 1.0) ** 1.4
    # elongate vertically: blur vertically via rolling average (periodic)
    # vertical elongation by averaging with shifted copies (periodic wrap, so tileable)
    streak_mask = (streak_mask * 0.50 +
                   np.roll(streak_mask, 4, axis=0) * 0.18 +
                   np.roll(streak_mask, -4, axis=0) * 0.18 +
                   np.roll(streak_mask, 9, axis=0) * 0.07 +
                   np.roll(streak_mask, -9, axis=0) * 0.07)
    streak_mask = np.clip(streak_mask * 1.35, 0.0, 1.0)
    streak_mask = _smoothstep(streak_mask)
    # drip tips: occasional teardrop at streak ends via small Voronoi dots at streak locations
    drip_noise = rc.periodic_voronoi_f1(size, 64, 0.88, np.random.default_rng(seed + 65))
    drips = np.clip(1.0 - drip_noise * 5.0, 0.0, 1.0) ** 2.2
    drips = drips * (streak_mask > 0.35).astype(np.float32) * 0.6
    streak_mask = np.clip(streak_mask + drips * 0.5, 0.0, 1.0)
    # colors
    marble_white = np.array([0.96, 0.95, 0.93], np.float32)
    marble_grey = np.array([0.78, 0.78, 0.80], np.float32)
    vein_dark = np.array([0.52, 0.52, 0.55], np.float32)
    water_tint = np.array([0.68, 0.78, 0.86], np.float32)
    # albedo: white/grey marble with dark veins
    base = marble_white[None, None, :] * (1.0 - veins[..., None] * 0.5) + marble_grey[None, None, :] * (veins[..., None] * 0.35) + vein_dark[None, None, :] * (veins[..., None] * 0.28)
    # water streaks darken and add bluish sheen, with streaks more translucent
    albedo = base * (1.0 - 0.32 * streak_mask[..., None]) + water_tint[None, None, :] * (0.20 * streak_mask[..., None])
    # streaks leave a slightly darker wet trail
    albedo = np.clip(albedo, 0.0, 1.0)
    height = np.clip(veins * 0.45 + streak_mask * 0.35 + warp * 0.10 + 0.10, 0.0, 1.0).astype(np.float32)
    normal = rc.normal_from_height(height, strength=2.0)
    # roughness: marble ~0.38, veins slightly rougher, water streaks very glossy
    rough = np.clip(0.38 + 0.12 * veins - 0.24 * streak_mask, 0.14, 0.88).astype(np.float32)
    # emissive: almost none — just faint wet sheen at streaks (cool, very dim)
    emissive = water_tint[None, None, :] * (0.045 * streak_mask[..., None])
    emissive = np.clip(emissive, 0.0, 1.0)
    return {
        "T_Surreal_WetMarble_BaseColor": (albedo, "rgb"),
        "T_Surreal_WetMarble_Normal": (normal, "rgb"),
        "T_Surreal_WetMarble_Roughness": (rough, "gray"),
        "T_Surreal_WetMarble_Emissive": (emissive, "rgb"),
        "_height": height,
    }

# ---------------------------------------------------------------------------
# Build registry
# ---------------------------------------------------------------------------

MATERIALS = [
    ("Mother-of-Pearl", "holographic iridescence, nacre layers, rainbow interference", _mat_mother_of_pearl),
    ("Molten Gold Veins", "liquid metal in pearl, hot gold cores", _mat_molten_gold),
    ("Void Velvet", "deep black velvet + star speckles", _mat_void_velvet),
    ("Biolum Dream Skin", "aqua-pink jellyfish bell veins", _mat_biolum_skin),
    ("Stained Glass Memory", "fractured pastel glass + dark lead", _mat_stained_glass),
    ("Wet Marble Sorrow", "weeping water streaks on sorrow marble", _mat_wet_marble),
]

CONTRACT = {
    "BaseColor": (True, "TEXTUREGROUP_World", "sRGB colour; tiling wrap"),
    "Normal": (False, "TEXTUREGROUP_World", "normal map, OpenGL Y+; sRGB off; tiling wrap"),
    "Roughness": (False, "TEXTUREGROUP_World", "data; roughness 0=gloss 1=matte; sRGB off; tiling wrap"),
    "Emissive": (True, "TEXTUREGROUP_Effects", "emissive tint; sRGB handling per emissive; tiling wrap"),
}

def main():
    ap = argparse.ArgumentParser(description="Surreal Material Lab — 6x tilable PBR (1024)")
    ap.add_argument("--seed", type=int, default=SEED)
    ap.add_argument("--size", type=int, default=SIZE)
    ap.add_argument("--out", default=str(OUT_DIR))
    args = ap.parse_args()

    out = Path(args.out)
    out.mkdir(parents=True, exist_ok=True)

    seed, size = args.seed, args.size
    all_files = []
    seam_rows = []

    for idx, (label, desc, fn) in enumerate(MATERIALS):
        mat_seed = seed + idx * 100
        result = fn(mat_seed, size)
        # result contains 4 maps + _height
        for suffix in ("BaseColor", "Normal", "Roughness", "Emissive"):
            # find key
            key = [k for k in result if k.endswith(suffix)]
            if not key:
                continue
            k = key[0]
            arr, kind = result[k]
            arr = np.clip(np.asarray(arr, np.float32), 0.0, 1.0)
            p = rc.save_image(out / f"{k}.png", arr, kind)
            seam_max, seam_lr, seam_tb = _seam_normalized(arr)
            # also compute levels for ingest compat
            lr_l = seam_lr * 255.0
            tb_l = seam_tb * 255.0
            # import contract
            srgb, lod, note = CONTRACT[suffix]
            # For emissive of VoidVelvet/Biolum, emissive is tinted but still sRGB import for correct color
            sha = rc.sha256_of(p)
            entry = {
                "name": k,
                "path": str(p),
                "kind": kind,
                "suffix": suffix,
                "material": label,
                "size": size,
                "seed": mat_seed,
                "sha256": sha,
                "bytes": p.stat().st_size,
                "seam_normalized_max": round(float(seam_max), 5),
                "seam_lr_norm": round(float(seam_lr), 5),
                "seam_tb_norm": round(float(seam_tb), 5),
                "seam_lr_levels": round(float(lr_l), 3),
                "seam_tb_levels": round(float(tb_l), 3),
                "tileable": bool(seam_max < 0.03),
                "import": {"sRGB": srgb, "lod_group": lod, "tiling": "wrap", "note": note},
            }
            all_files.append(entry)
            seam_rows.append((k, seam_max, entry["tileable"]))
            flag = "OK" if seam_max < 0.03 else "SEAM"
            print(f"[{flag}] {k:<40} seam_max={seam_max:.5f} (lr {seam_lr:.5f} tb {seam_tb:.5f}) {kind} {size}x{size}")

    # summary
    n = len(all_files)
    n_pass = sum(1 for _, s, ok in seam_rows if ok)
    n_fail = n - n_pass
    worst = max(s for _, s, _ in seam_rows) if seam_rows else 0.0

    manifest_path = out / "material_lab_manifest.json"
    payload = {
        "schema": "melodia.surreal_material_lab.v1",
        "seed": seed,
        "size": size,
        "generated_utc": datetime.datetime.now(datetime.timezone.utc).isoformat(),
        "output_dir": str(out),
        "generator": "surreal_material_lab.py",
        "runtime": "python+PIL+numpy (COPs-equivalent periodic noise)",
        "tiling": "lattice-periodic (period|size); all fields via rc.periodic_* / fbm / tileable_sine / toroidal Voronoi",
        "seam_rule": "normalized seam (mean abs wrap-step in 0..1) < 0.03 on both axes; max(lr,tb) reported as seam_normalized_max",
        "materials": [{"label": m[0], "description": m[1], "seed": seed + i * 100} for i, m in enumerate(MATERIALS)],
        "suffix_contract": {k: {"sRGB": v[0], "lod_group": v[1], "note": v[2]} for k, v in CONTRACT.items()},
        "summary": {
            "files": n,
            "materials": len(MATERIALS),
            "maps_per_material": 4,
            "tiling_targets": n,
            "tileable_pass": n_pass,
            "tileable_fail": n_fail,
            "worst_seam_normalized": round(float(worst), 5),
            "pass_threshold": 0.03,
        },
        "seam_rows": [{"name": k, "seam_max": round(float(s), 5), "pass": bool(ok)} for k, s, ok in seam_rows],
        "files": all_files,
    }
    with open(manifest_path, "w", encoding="utf-8") as f:
        import json
        json.dump(payload, f, indent=2)
    print(f"[material_lab] manifest -> {manifest_path}")
    print(f"[material_lab] {n} files, {n_pass}/{n} seams <0.03, worst={worst:.5f}")
    if n_fail:
        print(f"[material_lab] WARNING: {n_fail} seam failures — inspect manifest")
        sys.exit(1)
    # contact sheet for QA (optional, not counted)
    try:
        thumb = 256
        cols = 4
        rows = len(MATERIALS)
        sheet = Image.new("RGB", (cols * thumb, rows * thumb), (18, 18, 22))
        # Re-load basecolors for sheet
        for r, (label, _, _) in enumerate(MATERIALS):
            for c, suffix in enumerate(("BaseColor", "Normal", "Roughness", "Emissive")):
                name = f"T_Surreal_{label.replace(' ', '').replace('-', '').replace('VoidVelvet','VoidVelvet').replace('BiolumDreamSkin','BiolumSkin').replace('StainedGlassMemory','StainedGlass').replace('WetMarbleSorrow','WetMarble').replace('Mother-of-Pearl','MotherPearl').replace('MoltenGoldVeins','MoltenGold')}_{suffix}"
                # fallback: find by suffix search
                candidates = [e for e in all_files if e["material"] == label and e["suffix"] == suffix]
                if not candidates:
                    continue
                pname = candidates[0]["path"]
                im = Image.open(pname)
                if im.mode != "RGB":
                    im = im.convert("RGB")
                im = im.resize((thumb, thumb), Image.LANCZOS)
                sheet.paste(im, (c * thumb, r * thumb))
        sheet_path = out / "_SurrealMaterialLab_ContactSheet.png"
        sheet.save(str(sheet_path), format="PNG")
        print(f"[material_lab] contact sheet -> {sheet_path}")
    except Exception as e:
        print(f"[material_lab] contact sheet skipped: {e}")

if __name__ == "__main__":
    main()
