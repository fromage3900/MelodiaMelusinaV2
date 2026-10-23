"""Surreal Master Material Forge — wave 2 (6 insane shader libraries).

Cooks 6 x 1024 tilable PBR master sets (BaseColor + Normal + Roughness + Masks)
off-line with numpy+Pillow only, no Houdini/engine dependency. Every map is
lattice-periodic — seams <0.03 by ingest metric — so each tiles clean as a UE
master material.

Masters (prefix T_Surreal2_):
  1) OpalFlesh        — skin with opal veins (warm skin + iridescent fissures)
  2) LiquidMercuryLace— liquid mercury filigree over dark moire cloth
  3) FrostBloom       — ice flowers / frost dendrites forming on glass
  4) InkBloom         — ink bloom diffusing in deep water (marbled turbulence)
  5) ShatteredRainbowGlass — fractured rainbow glass with beveled shards
  6) LivingMossSilk   — living moss veins crawling through sheer silk

Per-master outputs (all 1024x1024 tileable):
  *_BaseColor.png  sRGB colour (import sRGB=true)
  *_Normal.png     OpenGL Y+ (import sRGB=false, BC5/Normal)
  *_Roughness.png  single channel (sRGB=false)
  *_Masks.png      RGB packed data (sRGB=false) — see MASKS legend per master

Additional:
  _SurrealMasters2_ContactSheet.png
  surreal_masters2_manifest.json  (sha256 + seams + params)
  surreal_masters_recipe.json     (UE master MI recipe per master)

Design rules (reef_common):
 - deterministic under SEED; call order is seed contract
 - tileable: periodic_value_noise / fbm / periodic_voronoi_f1 / tileable_sine only
 - Normal via rc.normal_from_height (wrap Sobel, OpenGL Y+)
 - seam metric mean(|opposite edges|) must be <0.03

Run:
  python Tools/Houdini/sea_above_reef/surreal_masters2.py
  python Tools/Houdini/sea_above_reef/surreal_masters2.py --seed 42 --size 1024 --out surreal_sweep_wave2/masters

Offline-first: plain Python + numpy + Pillow.
"""

import argparse
import hashlib
import json
import math
from pathlib import Path
import sys

import numpy as np

sys.path.insert(0, str(Path(__file__).resolve().parent))
import reef_common as rc  # noqa: E402

rc.require_pil()
from PIL import Image  # noqa: E402

# ---------------------------------------------------------------------------
SEED = 20260830
SIZE = 1024
PROJECT_ROOT = Path(__file__).resolve().parents[3]
DEFAULT_OUT = PROJECT_ROOT / "surreal_sweep_wave2" / "masters"

# ---------------------------------------------------------------------------
# helpers
# ---------------------------------------------------------------------------

def _clip01(a):
    return np.clip(a, 0.0, 1.0).astype(np.float32)

def _norm01(a):
    a = a.astype(np.float32)
    mn, mx = float(a.min()), float(a.max())
    if mx - mn < 1e-6:
        return np.zeros_like(a, dtype=np.float32)
    return ((a - mn) / (mx - mn)).astype(np.float32)

def _lerp(a, b, t):
    return a * (1.0 - t) + b * t

def _palette_sample_stops(stops, t):
    """stops: (N,3) sRGB float, t: (H,W) in [0,1] -> (H,W,3)"""
    n = len(stops) - 1
    x = np.clip(t, 0.0, 1.0) * n
    i0 = np.floor(x).astype(np.int32)
    i1 = np.minimum(i0 + 1, n)
    f = (x - i0).astype(np.float32)
    s = f * f * (3.0 - 2.0 * f)
    c0 = stops[i0]
    c1 = stops[i1]
    return c0 * (1.0 - s[..., None]) + c1 * s[..., None]

def _seam_metric(arr):
    """mean abs opposite-edge diff, normalized 0..1. For RGB returns mean over channels."""
    if arr.ndim == 3:
        lr = np.mean(np.abs(arr[:, 0, :].astype(np.float32) - arr[:, -1, :].astype(np.float32)))
        tb = np.mean(np.abs(arr[0, :, :].astype(np.float32) - arr[-1, :, :].astype(np.float32)))
    else:
        lr = np.mean(np.abs(arr[:, 0].astype(np.float32) - arr[:, -1].astype(np.float32)))
        tb = np.mean(np.abs(arr[0, :].astype(np.float32) - arr[-1, :].astype(np.float32)))
    return float(lr), float(tb)

def _hsv_to_rgb_vec(h, s, v):
    """h,s,v in [0,1] arrays -> rgb (H,W,3) float"""
    # vectorized hsv->rgb
    hi = (h * 6.0).astype(np.float32)
    i = np.floor(hi).astype(np.int32) % 6
    f = hi - np.floor(hi)
    p = v * (1.0 - s)
    q = v * (1.0 - f * s)
    t = v * (1.0 - (1.0 - f) * s)
    r = np.choose(i, [v, q, p, p, t, v])
    g = np.choose(i, [t, v, v, q, p, p])
    b = np.choose(i, [p, p, t, v, v, q])
    return np.stack([r, g, b], axis=-1).astype(np.float32)

# ---------------------------------------------------------------------------
# 1) Opal Flesh — skin with opal veins
# ---------------------------------------------------------------------------
def build_opal_flesh(seed, size):
    rng0 = np.random.default_rng(seed + 10)
    rng1 = np.random.default_rng(seed + 11)
    rng2 = np.random.default_rng(seed + 12)
    rng3 = np.random.default_rng(seed + 13)

    # skin pore field + large lobe variation
    lobes = rc.fbm(size, 8, 4, rng0, gain=0.55)          # large skin undulation
    pores = rc.fbm(size, 64, 3, rng1, gain=0.6)          # fine pores
    f1 = rc.periodic_voronoi_f1(size, 16, 0.78, rng2)    # opal vein cells
    f1b = rc.periodic_voronoi_f1(size, 32, 0.85, rng3)
    # veins = cell edges (thin, branching)
    edge = np.clip(1.0 - f1 * 2.8, 0.0, 1.0) ** 1.8
    edge_fine = np.clip(1.0 - f1b * 3.4, 0.0, 1.0) ** 2.0
    veins = np.clip(edge * 0.85 + edge_fine * 0.45, 0.0, 1.0)
    # droplet opal centres: bright inclusions at cell centres
    inclusion = np.clip(1.0 - f1 * 1.2, 0.0, 1.0) ** 3.2 * (1.0 - edge)

    # skin base: warm peach -> dusky rose by lobes
    SKIN_A = np.array([0.94, 0.80, 0.72], np.float32)
    SKIN_B = np.array([0.86, 0.62, 0.62], np.float32)
    SKIN_C = np.array([0.58, 0.46, 0.44], np.float32)  # crevice
    # opal spectrum: violet->cyan->lime->peach via hue sweep
    OPAL_STOPS = np.array([
        [0.62, 0.38, 0.92], [0.28, 0.68, 0.95], [0.38, 0.92, 0.68],
        [0.98, 0.86, 0.62], [0.95, 0.58, 0.72],
    ], np.float32)

    skin_mix = _clip01(lobes * 0.9 + pores * 0.1)
    base_skin = SKIN_A[None,None,:] * (1 - skin_mix[...,None]) + SKIN_B[None,None,:] * skin_mix[...,None]
    base_skin += (pores - 0.5)[...,None] * 0.06
    # rim darkening at vein edges
    rim = np.clip(edge * 2.0 - 0.3, 0, 1) ** 1.5
    base_skin = base_skin * (1 - rim[...,None]*0.42) + SKIN_C[None,None,:] * (rim[...,None]*0.42)

    # opal colour field along veins: phase by large fbm warp
    phase = _clip01(rc.fbm(size, 16, 3, rng0, gain=0.5) * 0.55 + lobes * 0.25 + pores * 0.12)
    opal_col = _palette_sample_stops(OPAL_STOPS, phase)
    # veins reveal opal; boost saturation inside inclusion dots
    vein_alpha = _clip01(veins * 1.15)
    albedo = base_skin * (1 - vein_alpha[...,None]*0.72) + opal_col * (vein_alpha[...,None]*0.72)
    # bright sparkle dots
    albedo = np.clip(albedo + inclusion[...,None] * 0.32, 0, 1)
    # subtle subsurface pepper: warmer subsurface where thin
    albedo = _clip01(albedo)

    # height: skin pores shallow, veins as slight ridges + inclusion dome
    height = _clip01(0.30 * pores + 0.38 * (edge * 0.65) + 0.18 * inclusion + 0.14 * lobes)
    normal = rc.normal_from_height(height, strength=2.8)

    # roughness: skin ~0.55, veins polished opal ~0.18, inclusion glossy ~0.12
    rough = _clip01(0.58 - 0.32 * vein_alpha - 0.18 * inclusion + (pores - 0.5)*0.06)
    rough = np.clip(rough, 0.08, 0.85)

    # masks: R=vein mask, G=inclusion/height mask, B=skin cavity
    cavity = _clip01(1.0 - pores)
    masks = np.stack([vein_alpha, _clip01(inclusion*1.2), cavity], axis=-1).astype(np.float32)

    return {
        "BaseColor": albedo.astype(np.float32),
        "Normal": normal.astype(np.float32),
        "Roughness": rough.astype(np.float32),
        "Masks": masks.astype(np.float32),
        "height": height,
        "meta": {"legend": "Masks R=opal vein, G=inclusion dome, B=cavity/pore inverse"}
    }

# ---------------------------------------------------------------------------
# 2) Liquid Mercury Lace
# ---------------------------------------------------------------------------
def build_mercury_lace(seed, size):
    rng0 = np.random.default_rng(seed + 20)
    rng1 = np.random.default_rng(seed + 21)
    rng2 = np.random.default_rng(seed + 22)
    ys, xs = np.mgrid[0:size, 0:size].astype(np.float32)

    base_fbm = rc.fbm(size, 8, 4, rng0, gain=0.55)
    warp = rc.fbm(size, 32, 3, rng1, gain=0.5)
    # lace filigree: Voronoi edges + warped sine lace
    f1 = rc.periodic_voronoi_f1(size, 16, 0.82, rng2)
    f1f = rc.periodic_voronoi_f1(size, 32, 0.80, np.random.default_rng(seed+23))
    edge = np.clip(1.0 - f1 * 2.6, 0, 1) ** 1.9
    edge2 = np.clip(1.0 - f1f * 3.2, 0, 1) ** 2.2
    lace_sine = rc.tileable_sine(size, 10, 6, phase=0.3, warp=warp, warp_amp=0.9)
    lace_sine2 = rc.tileable_sine(size, 7, 14, phase=1.1, warp=warp, warp_amp=0.6)
    # thin lace from sine crests, intersected with voronoi edges
    lace_thin = (np.clip((lace_sine - 0.62)/0.38,0,1) ** 1.5) * 0.55 + (np.clip((lace_sine2 - 0.58)/0.42,0,1) ** 1.4)*0.45
    filigree = _clip01(edge * 0.70 + edge2 * 0.35 + lace_thin * 0.55)
    filigree = _clip01((filigree - 0.28)/0.72)  # threshold thin
    # mercury beads at cell centres
    beads = np.clip(1.0 - f1 * 1.3, 0,1) ** 3.0
    # cloth weave base: fine diagonal
    weave = rc.tileable_sine(size, 0, 8, phase=0, warp=None)
    weave = np.abs(weave - 0.5)*2.0  # ridges

    FABRIC = np.array([0.14, 0.14, 0.16], np.float32)  # dark charcoal silk
    FABRIC2 = np.array([0.22, 0.22, 0.26], np.float32)
    MERCURY = np.array([0.92, 0.93, 0.94], np.float32)
    MERCURY_TINT = np.array([0.72, 0.78, 0.86], np.float32)

    cloth = FABRIC[None,None,:] * (1 - base_fbm[...,None]*0.35) + FABRIC2[None,None,:] * (base_fbm[...,None]*0.35)
    cloth += (weave - 0.5)[...,None] * 0.06
    # mercury lace: very bright, slight blue tint by beads
    mercury_col = _lerp(MERCURY[None,None,:] * np.ones((size,size,1), dtype=np.float32),
                        MERCURY_TINT[None,None,:] * np.ones((size,size,1), dtype=np.float32),
                        beads[...,None]*0.6)
    # specular breakup along lace
    highlight = np.clip((lace_sine - 0.5),0,1) * 0.18
    albedo = cloth * (1 - filigree[...,None]) + (mercury_col + highlight[...,None]) * filigree[...,None]
    # beads extra bright centre
    albedo = np.clip(albedo + beads[...,None]*0.35*filigree[...,None], 0, 1)
    albedo = _clip01(albedo)

    # height: lace is raised ridge, beads are domes, cloth has soft weave
    height = _clip01(0.40*filigree + 0.28*beads*filigree + 0.12*weave*0.5 + 0.10*warp)
    normal = rc.normal_from_height(height, strength=3.4)

    # roughness: cloth ~0.72, mercury ~0.12-0.22 (varies with curvature)
    rough = _clip01(0.72 * (1 - filigree) + (0.14 + 0.08*warp + 0.05*beads) * filigree)
    rough = np.clip(rough, 0.06, 0.92)

    # masks: R=filigree, G=beads, B=weave/height
    masks = np.stack([_clip01(filigree), _clip01(beads), _clip01(weave)], axis=-1).astype(np.float32)
    return {"BaseColor": albedo, "Normal": normal, "Roughness": rough, "Masks": masks, "height": height,
            "meta": {"legend": "Masks R=lace filigree, G=mercury beads, B=cloth weave"}}

# ---------------------------------------------------------------------------
# 3) Frost Bloom (ice flowers forming)
# ---------------------------------------------------------------------------
def build_frost_bloom(seed, size):
    rng0 = np.random.default_rng(seed + 30)
    rng1 = np.random.default_rng(seed + 31)
    rng2 = np.random.default_rng(seed + 32)
    ys, xs = np.mgrid[0:size, 0:size].astype(np.float32)

    base = rc.fbm(size, 8, 4, rng0, gain=0.55)  # glass undulation
    warp = rc.fbm(size, 32, 4, rng1, gain=0.52)
    # Voronoi bloom centres (ice flower rosettes)
    f1 = rc.periodic_voronoi_f1(size, 8, 0.84, rng2)
    f1s = rc.periodic_voronoi_f1(size, 16, 0.78, np.random.default_rng(seed+33))
    # large bloom: cell centre radius
    bloom = np.clip(1.0 - f1 * 1.45, 0, 1) ** 1.8   # soft disc
    bloom_fine = np.clip(1.0 - f1s * 2.2, 0,1) ** 2.0
    # dendrite petals: radial sine around each cell centre — approximate via domain warp
    # use tileable sines to carve petal spokes, modulated by bloom
    petal_a = rc.tileable_sine(size, 8, 0, phase=0.0, warp=warp, warp_amp=0.8)
    petal_b = rc.tileable_sine(size, 0, 8, phase=0.5, warp=warp, warp_amp=0.8)
    petal = (np.abs(petal_a - 0.5)*2.0) * (np.abs(petal_b - 0.5)*2.0)  # cross
    petal = np.clip((petal - 0.18)/0.82, 0,1) ** 1.3
    # frost density: petals only where bloom exists
    frost = _clip01(bloom * (0.65 + 0.35*petal) + bloom_fine*0.35)
    # secondary feathering / needle frost at edges
    feather = np.clip(1.0 - f1 * 2.4, 0,1) ** 2.2 * petal * 0.7
    frost = _clip01(frost + feather)
    frost = _clip01((frost - 0.08)/0.92)  # clean

    # glass base vs ice
    GLASS = np.array([0.06, 0.08, 0.11], np.float32)  # dark glass
    FROST_A = np.array([0.92, 0.96, 1.00], np.float32) # white-blue
    FROST_B = np.array([0.62, 0.82, 0.95], np.float32) # icy blue
    FROST_C = np.array([0.78, 0.92, 0.98], np.float32)
    # subtle rainbow at bloom edges (thin-film)
    edge_phase = _clip01((f1*2.2 - 0.2) + warp*0.15)
    RAINBOW = np.array([[0.95,0.55,0.95],[0.60,0.70,1.0],[0.60,0.95,0.90],[0.95,0.92,0.62]], np.float32)
    rainbow = _palette_sample_stops(RAINBOW, edge_phase)

    # base glass dark, modulated by base fbm
    albedo = GLASS[None,None,:] * (1 + (base-0.5)[...,None]*0.35)
    # frost colour: blend by bloom radius (centre whiter, edge bluer) + petal sparkle
    frost_mix = _clip01(bloom*0.7 + petal*0.3)
    frost_col = _lerp(FROST_B[None,None,:] * np.ones((size,size,1),dtype=np.float32),
                      FROST_A[None,None,:] * np.ones((size,size,1),dtype=np.float32),
                      frost_mix[...,None])
    frost_col = _lerp(frost_col, FROST_C[None,None,:]*np.ones((size,size,1),dtype=np.float32), (petal[...,None]*0.25))
    # add rainbow sheen only at frost edge (thin rim)
    rim = np.clip(1.0 - np.abs(f1*2.0 - 0.75)*1.8, 0,1) * frost * 0.45
    albedo = albedo * (1 - frost[...,None]*0.92) + frost_col * (frost[...,None]*0.92)
    albedo = albedo + rainbow * (rim[...,None]*0.35)
    albedo = _clip01(albedo)
    # sparkles: random ice glitter inside frost
    glitter = np.clip((rc.fbm(size, 128, 2, np.random.default_rng(seed+34), gain=0.6) - 0.82)/0.18,0,1)
    albedo = np.clip(albedo + glitter[...,None]*0.18*frost[...,None],0,1)

    height = _clip01(0.55*frost + 0.20*petal*frost + 0.10*base + 0.08*glitter*frost)
    normal = rc.normal_from_height(height, strength=3.0)

    # roughness: glass 0.08, frost 0.38-0.55, glitter facets lower
    rough = _clip01(0.07*(1-frost) + (0.42 + 0.12*petal - 0.10*glitter)*frost)
    rough = np.clip(rough, 0.05, 0.95)

    # masks: R=frost, G=petal structure, B=rim/bloom
    masks = np.stack([_clip01(frost), _clip01(petal*frost), _clip01(rim + bloom_fine)], axis=-1).astype(np.float32)
    return {"BaseColor": albedo, "Normal": normal, "Roughness": rough, "Masks": masks, "height": height,
            "meta": {"legend": "Masks R=frost coverage, G=petal spokes, B=rim/bloom fine"}}

# ---------------------------------------------------------------------------
# 4) Ink Bloom in Water
# ---------------------------------------------------------------------------
def build_ink_bloom(seed, size):
    rng0 = np.random.default_rng(seed + 40)
    rng1 = np.random.default_rng(seed + 41)
    rng2 = np.random.default_rng(seed + 42)
    ys, xs = np.mgrid[0:size, 0:size].astype(np.float32)

    fbm0 = rc.fbm(size, 4, 5, rng0, gain=0.58)   # large water murk
    fbm1 = rc.fbm(size, 16, 4, rng1, gain=0.52)  # medium turbulence
    fbm2 = rc.fbm(size, 64, 3, rng2, gain=0.58)  # fine ink tendrils
    warp = fbm0 * 0.6 + fbm1 * 0.4
    # ink cores: Voronoi centres as bloom origins, stretched by warp
    f1 = rc.periodic_voronoi_f1(size, 16, 0.80, np.random.default_rng(seed+43))
    f1m = rc.periodic_voronoi_f1(size, 32, 0.82, np.random.default_rng(seed+44))
    # tendrils: fBm warps the distance field
    wdist = _clip01(f1 + (warp - 0.5)*0.22)
    tendril = np.clip(1.0 - wdist*1.9, 0,1) ** 1.6
    tendril_fine = np.clip(1.0 - f1m*2.6, 0,1) ** 2.0 * np.clip((fbm2 - 0.40)/0.60,0,1)
    ink = _clip01(tendril*0.75 + tendril_fine*0.55 + fbm1*0.18)
    # turbulent edge curls: sine filaments modulated by warp
    curl = rc.tileable_sine(size, 6, 10, phase=0.8, warp=warp, warp_amp=1.1)
    filaments = np.clip((np.abs(curl-0.5)*2.0 -0.20)/0.80,0,1) ** 1.5
    ink = _clip01(ink * (0.55 + 0.45*filaments) + filaments*0.08)
    ink = _clip01((ink - 0.06)/0.94)
    # invert some areas: ink suspended at different depths
    wisps = np.clip((fbm2 - 0.55)/0.45,0,1) * (1.0 - tendril) * 0.45
    ink = _clip01(ink + wisps)

    WATER = np.array([0.06, 0.12, 0.22], np.float32)
    WATER2 = np.array([0.10, 0.18, 0.28], np.float32)
    INK_A = np.array([0.04, 0.02, 0.08], np.float32)  # deep violet-black
    INK_B = np.array([0.12, 0.07, 0.18], np.float32)
    INK_C = np.array([0.20, 0.10, 0.30], np.float32)
    SHEEN = np.array([0.18, 0.42, 0.58], np.float32)  # water sheen
    # water base with murk variation
    water = WATER[None,None,:]*(1 - fbm0[...,None]*0.35) + WATER2[None,None,:]*(fbm0[...,None]*0.35)
    water += (fbm1 - 0.5)[...,None]*0.05
    # ink colour grades by thickness (core darker, edge lighter with scatter)
    ink_thick = _clip01(tendril + tendril_fine*0.5)
    ink_col = _lerp(INK_C[None,None,:]*np.ones((size,size,1),dtype=np.float32),
                    INK_A[None,None,:]*np.ones((size,size,1),dtype=np.float32),
                    ink_thick[...,None])
    ink_col = _lerp(ink_col, INK_B[None,None,:]*np.ones((size,size,1),dtype=np.float32), wisps[...,None]*0.6)
    albedo = water*(1 - ink[...,None]*0.88) + ink_col*(ink[...,None]*0.88)
    # subtle teal sheen where filaments curl
    albedo += SHEEN[None,None,:]* (filaments[...,None]*0.08*(1-ink[...,None])*0.5)
    albedo = _clip01(albedo)

    height = _clip01(0.35*ink + 0.25*filaments*0.6 + 0.18*fbm2*0.4 + 0.12*fbm1*0.3)
    normal = rc.normal_from_height(height, strength=2.2)

    # roughness: water 0.18, ink more matte 0.55, silhouette shimmer
    rough = _clip01(0.18*(1-ink) + (0.52 + 0.10*fbm2 - 0.08*filaments)*ink)
    rough = np.clip(rough, 0.06, 0.88)

    masks = np.stack([_clip01(ink), _clip01(ink_thick), _clip01(filaments)], axis=-1).astype(np.float32)
    return {"BaseColor": albedo, "Normal": normal, "Roughness": rough, "Masks": masks, "height": height,
            "meta": {"legend": "Masks R=ink density, G=ink thickness, B=filament curl"}}

# ---------------------------------------------------------------------------
# 5) Shattered Rainbow Glass
# ---------------------------------------------------------------------------
def build_shattered_rainbow(seed, size):
    rng0 = np.random.default_rng(seed + 50)
    rng1 = np.random.default_rng(seed + 51)
    rng2 = np.random.default_rng(seed + 52)
    rng3 = np.random.default_rng(seed + 53)

    base = rc.fbm(size, 8, 3, rng0, gain=0.55)
    warp = rc.fbm(size, 32, 3, rng1, gain=0.5)
    f1 = rc.periodic_voronoi_f1(size, 8, 0.88, rng2)  # big shards
    f1m = rc.periodic_voronoi_f1(size, 16, 0.78, rng3)
    # cell id colour via quantized fbm (approx shard tint)
    shard_id = np.floor(rc.fbm(size, 8, 2, np.random.default_rng(seed+54), gain=0.5) * 12.0) / 12.0
    # crack lines: voronoi edges
    crack = np.clip(1.0 - f1*2.9, 0,1) ** 1.7  # thin edge -> but we want crack dark lines
    crack_fine = np.clip(1.0 - f1m*3.4,0,1) ** 2.0
    # invert: cracks are where edge is high, keep as narrow lines
    cracks = np.clip((crack*0.9 + crack_fine*0.5) ,0,1)
    # make cracks narrow dark lines: keep only the peaks
    cracks_narrow = _clip01((cracks - 0.62)/0.38)  # threshold
    # alternative: use cracks_narrow as the dark line mask, cracks_soft for cavity

    # rainbow hue per shard: hue = shard_id + warp tweak + base
    hue = np.mod(shard_id + warp*0.18 + base*0.08, 1.0)
    sat = 0.85 + 0.10*warp - 0.10*cracks_narrow
    val = 0.92 + 0.08*base
    shard_col = _hsv_to_rgb_vec(_clip01(hue), _clip01(sat), _clip01(val))
    # desaturate slightly at crack proximity
    # glass base between cracks: shard_col, cracks: near-black with blue tint
    CRACK_COL = np.array([0.04, 0.05, 0.08], np.float32)
    EDGE_HIGHLIGHT = np.array([1.0, 1.0, 1.0], np.float32)
    # bevel highlight at crack rim (1px side)
    rim = np.clip(cracks*2.2 - 0.3,0,1) * (1 - cracks_narrow) * 0.85
    albedo = shard_col * (1 - cracks_narrow[...,None]*0.92) + CRACK_COL[None,None,:] * (cracks_narrow[...,None]*0.92)
    albedo = albedo + EDGE_HIGHLIGHT[None,None,:]* (rim[...,None]*0.38)
    # subtle refraction caustic inside shards
    caustic = np.clip((rc.tileable_sine(size, 5, 7, phase=0.2, warp=warp, warp_amp=0.5) -0.62)/0.38,0,1) ** 1.6
    albedo = albedo + 0.07*caustic[...,None] * (1 - cracks_narrow[...,None])
    albedo = _clip01(albedo)

    # height: shards flat with beveled edges (rim raised), cracks recessed
    height = _clip01(0.50 - cracks_narrow*0.38 + rim*0.42 + 0.08*base)
    # add subtle shard curvature (dome)
    dome = np.clip(1.0 - f1*1.4, 0,1) ** 1.2 * 0.12
    height = _clip01(height + dome)
    normal = rc.normal_from_height(height, strength=3.2)

    # roughness: glass 0.06, cracks 0.78, rim 0.18
    rough = _clip01(0.06*(1-cracks_narrow) + 0.78*cracks_narrow - rim*0.18 + 0.04*caustic*(1-cracks_narrow))
    rough = np.clip(rough, 0.04, 0.92)

    masks = np.stack([_clip01(1 - cracks_narrow), _clip01(rim), _clip01(dome*4.0)], axis=-1).astype(np.float32)
    # R=shard face, G=bevel rim, B=dome
    return {"BaseColor": albedo, "Normal": normal, "Roughness": rough, "Masks": masks, "height": height,
            "meta": {"legend": "Masks R=shard face, G=bevel rim, B=shard dome"}}

# ---------------------------------------------------------------------------
# 6) Living Moss Silk
# ---------------------------------------------------------------------------
def build_moss_silk(seed, size):
    rng0 = np.random.default_rng(seed + 60)
    rng1 = np.random.default_rng(seed + 61)
    rng2 = np.random.default_rng(seed + 62)
    ys, xs = np.mgrid[0:size, 0:size].astype(np.float32)

    lobes = rc.fbm(size, 8, 4, rng0, gain=0.55)
    weave_warp = rc.fbm(size, 32, 3, rng1, gain=0.5)
    f1 = rc.periodic_voronoi_f1(size, 16, 0.80, rng2)
    f1s = rc.periodic_voronoi_f1(size, 32, 0.84, np.random.default_rng(seed+63))
    # moss veins: voronoi edges branching + thresholded fbm
    edge = np.clip(1.0 - f1*2.7,0,1) ** 1.8
    edge2 = np.clip(1.0 - f1s*3.0,0,1) ** 2.0
    moss_noise = rc.fbm(size, 16, 4, np.random.default_rng(seed+64), gain=0.54)
    moss_threshold = _clip01((moss_noise - 0.48)/0.52)  # bias to lacy
    veins = _clip01(edge*0.72 + edge2*0.38 + moss_threshold*0.45 - 0.18)
    veins = _clip01((veins - 0.28)/0.72) ** 0.95
    # moss caps: cell centres where moss is thick
    caps = np.clip(1.0 - f1*1.2,0,1) ** 2.8 * veins
    # silk weave: fine anisotropic sine
    silk_u = rc.tileable_sine(size, 0, 8, phase=0.0, warp=weave_warp, warp_amp=0.35)
    silk_v = rc.tileable_sine(size, 8, 0, phase=0.4, warp=weave_warp, warp_amp=0.35)
    weave = (np.abs(silk_u - 0.5)*2.0 * 0.5 + np.abs(silk_v - 0.5)*2.0 * 0.5)
    weave = _clip01(weave)
    # silk sheen anisotropy streak
    sheen_streak = rc.tileable_sine(size, 8, 2, phase=0.6, warp=weave_warp, warp_amp=0.6)
    sheen = np.clip((sheen_streak - 0.55)/0.45,0,1) ** 1.4

    SILK_A = np.array([0.94, 0.88, 0.86], np.float32)  # pale blush silk
    SILK_B = np.array([0.98, 0.92, 0.88], np.float32)
    SILK_SHADOW = np.array([0.62, 0.58, 0.62], np.float32)
    MOSS_A = np.array([0.18, 0.42, 0.22], np.float32)  # living moss
    MOSS_B = np.array([0.28, 0.58, 0.30], np.float32)
    MOSS_C = np.array([0.42, 0.72, 0.38], np.float32)
    BLOOM = np.array([0.92, 0.96, 0.42], np.float32)  # tiny flower bloom on caps

    silk = SILK_A[None,None,:]*(1 - lobes[...,None]*0.28) + SILK_B[None,None,:]*(lobes[...,None]*0.28)
    silk += (weave -0.5)[...,None]*0.09
    silk += sheen[...,None]*0.12  # sheen highlight
    silk = silk * (1 - 0.18* (1-lobes)[...,None])  # cavity subtle
    # moss colour lerp by caps (thicker = brighter) + noise
    moss_col = _lerp(MOSS_A[None,None,:]*np.ones((size,size,1),dtype=np.float32),
                     MOSS_B[None,None,:]*np.ones((size,size,1),dtype=np.float32),
                     caps[...,None]*1.2)
    moss_col = _lerp(moss_col, MOSS_C[None,None,:]*np.ones((size,size,1),dtype=np.float32), (moss_noise[...,None]-0.5)*0.4)
    # tiny blooms on thickest caps
    bloom = np.clip((caps - 0.55)/0.45,0,1) * np.clip((rc.fbm(size, 64, 2, np.random.default_rng(seed+65), gain=0.5)-0.72)/0.28,0,1)
    albedo = silk * (1 - veins[...,None]*0.92) + moss_col * (veins[...,None]*0.92)
    albedo = albedo + BLOOM[None,None,:]* (bloom[...,None]*0.55)
    albedo = _clip01(albedo)

    height = _clip01(0.18*weave*0.5 + 0.42*veins + 0.22*caps + 0.08*lobes)
    normal = rc.normal_from_height(height, strength=2.6)

    # roughness: silk 0.42-0.52, moss 0.82-0.92, bloom waxy 0.35
    rough = _clip01(0.44*(1-veins) + 0.84*veins + 0.08*weave*(1-veins) - bloom*0.28)
    rough = np.clip(rough, 0.22, 0.94)

    masks = np.stack([_clip01(veins), _clip01(caps), _clip01(sheen)], axis=-1).astype(np.float32)
    return {"BaseColor": albedo, "Normal": normal, "Roughness": rough, "Masks": masks, "height": height,
            "meta": {"legend": "Masks R=moss veins, G=moss caps/bloom, B=silk sheen"}}

# ---------------------------------------------------------------------------
# registry
# ---------------------------------------------------------------------------
MASTERS = [
    ("OpalFlesh", "Opal flesh — skin with iridescent opal fissures", build_opal_flesh),
    ("LiquidMercuryLace", "Liquid mercury lace — molten filigree on charcoal silk", build_mercury_lace),
    ("FrostBloom", "Frost bloom — ice flowers forming on dark glass", build_frost_bloom),
    ("InkBloom", "Ink bloom in water — violet-black tendrils in deep teal", build_ink_bloom),
    ("ShatteredRainbowGlass", "Shattered rainbow glass — beveled prism shards", build_shattered_rainbow),
    ("LivingMossSilk", "Living moss silk — moss veins crawling through sheer silk", build_moss_silk),
]

RECIPE = {
    "OpalFlesh": {
        "ue_master": "M_Surreal_OpalFlesh",
        "instance_prefix": "MI_OpalFlesh",
        "material_model": "Subsurface / thin translucent skin with iridescent crack layer",
        "parameters": {
            "BaseColor": "T_Surreal2_OpalFlesh_BaseColor (sRGB)",
            "Normal": "T_Surreal2_OpalFlesh_Normal (BC5, OpenGL Y+)",
            "Roughness": "T_Surreal2_OpalFlesh_Roughness (R channel)",
            "Masks": "T_Surreal2_OpalFlesh_Masks: R=opal vein, G=inclusion dome, B=cavity",
            "Opacity_Mask": "Masks.R as subsurface crack alpha",
            "SubsurfaceColor": "lerp warm peach (0.94,0.62,0.58) -> opal spectrum by Masks.R",
            "Specular": "0.35 + 0.15*Masks.G (opal domes extra gloss)",
            "Emissive": "Masks.G * 0.12 * opal_col (soft inclusions)",
            "Height_for_POM": "luma of Masks.B + Masks.G*0.5",
        },
        "instance_ideas": [
            "MI_OpalFlesh_BossSkin — full body, high SSS, vein emissive pulse tied to gameplay tag Melodia.Elegance",
            "MI_OpalFlesh_PropVein — tiling 2x on weapon/armor trim, roughness 0.28 locked",
            "MI_OpalFlesh_Wounded — vertex-color modulate Masks.R for damage spread"
        ],
        "notes": "Use Substrate SSS slab for skin; feed Masks.R into second slab's thin-film iridescence. Tile 1.0 for character UVs, 2.0-4.0 for architecture."
    },
    "LiquidMercuryLace": {
        "ue_master": "M_Surreal_LiquidMercuryLace",
        "instance_prefix": "MI_MercuryLace",
        "material_model": "Metallic cloth — cloth base (non-metal) + mercury lace (metal=1) via mask",
        "parameters": {
            "BaseColor": "T_Surreal2_LiquidMercuryLace_BaseColor (sRGB)",
            "Normal": "T_Surreal2_LiquidMercuryLace_Normal (BC5)",
            "Roughness": "T_Surreal2_LiquidMercuryLace_Roughness",
            "Masks": "T_Surreal2_LiquidMercuryLace_Masks: R=filigree, G=beads, B=weave",
            "Metallic": "Masks.R (mercury lace is metal)",
            "Specular_Aniso": "Masks.B drives anisotropy 0.6 along lace tangent",
            "ClearCoat": "Masks.G * 0.5 (beads)",
        },
        "instance_ideas": [
            "MI_MercuryLace_DressOverlay — lace over sheer fabric, masked opacity by Masks.R, wavy WPO",
            "MI_MercuryLace_ArmorTrim — metal=1 where Masks.R>0.5, high contrast polish",
            "MI_MercuryLace_Fluid — panner on Masks.G beads for molten flow"
        ],
        "notes": "In master, lerp Metallic 0->1 by Masks.R; keep base cloth roughness 0.72. For Nanite tessellated lace, feed height = Masks.R*0.4 + Masks.G*0.2 into displacement."
    },
    "FrostBloom": {
        "ue_master": "M_Surreal_FrostBloom",
        "instance_prefix": "MI_FrostBloom",
        "material_model": "Glass + frost growth — translucent glass base, frost as opacity/SSS layer",
        "parameters": {
            "BaseColor": "T_Surreal2_FrostBloom_BaseColor (sRGB)",
            "Normal": "T_Surreal2_FrostBloom_Normal",
            "Roughness": "T_Surreal2_FrostBloom_Roughness",
            "Masks": "T_Surreal2_FrostBloom_Masks: R=frost, G=petal spokes, B=rim/bloom",
            "Opacity": "lerp 0.22 (glass) -> 0.98 (frost) by Masks.R",
            "Transmission": "glass base 0.9, frost 0.25",
            "Fuzz / SSS": "Masks.G as frost depth for subsurface",
            "IceSparkle": "Masks.B as glitter mask * time sine",
        },
        "instance_ideas": [
            "MI_FrostBloom_Window — growth param scalar drives Masks.R threshold (level puzzle: music warms it)",
            "MI_FrostBloom_Ground — planar mapping 0.5x, frost only in shadows via AO multiply",
            "MI_FrostBloom_Crystal — fully frosted (R forced 1), emissive rim by Masks.B"
        ],
        "notes": "Animate growth by lerping a Growth scalar (0..1) against Masks.R threshold: frost = smoothstep(Growth-0.08, Growth+0.08, Masks.R). Drive Growth from BP or curve."
    },
    "InkBloom": {
        "ue_master": "M_Surreal_InkBloom",
        "instance_prefix": "MI_InkBloom",
        "material_model": "Fluid diffusion — water base with ink as decal-like darkening + depth",
        "parameters": {
            "BaseColor": "T_Surreal2_InkBloom_BaseColor",
            "Normal": "T_Surreal2_InkBloom_Normal (gentle, for liquid parallax)",
            "Roughness": "T_Surreal2_InkBloom_Roughness",
            "Masks": "T_Surreal2_InkBloom_Masks: R=ink density, G=thickness, B=filament curl",
            "Depth_Fade": "Masks.G drives depth darken and absorption tint",
            "Flow_UV": "panner on Masks.B (filaments) at 0.06 speed for drift",
            "Chroma_Fringe": "Masks.B * 0.04 edge tint for underwater scatter",
        },
        "instance_ideas": [
            "MI_InkBloom_FloorPool — world-aligned UV, flow panner, ink as gameplay ink-trail",
            "MI_InkBloom_Curtain — vertical UV, ink blooms downward, opacity by Masks.R",
            "MI_InkBloom_Nightmare — invert water/ink, high contrast, emissive filaments"
        ],
        "notes": "For performance, skip POM; use bump offset only. Ink density (Masks.R) can drive a post-process ink vignette via MPC."
    },
    "ShatteredRainbowGlass": {
        "ue_master": "M_Surreal_ShatteredRainbowGlass",
        "instance_prefix": "MI_RainbowGlass",
        "material_model": "Prismatic glass — per-shard hue, beveled edges, crack occlusion",
        "parameters": {
            "BaseColor": "T_Surreal2_ShatteredRainbowGlass_BaseColor (prismatic)",
            "Normal": "T_Surreal2_ShatteredRainbowGlass_Normal (bevel)",
            "Roughness": "T_Surreal2_ShatteredRainbowGlass_Roughness (glass 0.06 vs cracks 0.78)",
            "Masks": "T_Surreal2_ShatteredRainbowGlass_Masks: R=shard face, G=bevel rim, B=dome",
            "Opacity": "0.86 + 0.14*Masks.R (cracks slightly more transparent)",
            "Refraction": "IOR 1.52, chromatic offset 0.004 * hue variance",
            "EdgeWear": "Masks.G as bevel highlight / wear scalar",
        },
        "instance_ideas": [
            "MI_RainbowGlass_Pane — single-sided glass, two-sided refraction, crack opacity clipped",
            "MI_RainbowGlass_Floor — thick prism, ContactHard shadow, shard parallax",
            "MI_RainbowGlass_ShardDecal — deferred decal, only cracks (Masks.R < 0.3) punch alpha"
        ],
        "notes": "In Substrate use Thin Glass slab; feed Masks.G into second slab's edge fuzz for bevel. For cheap mobile fallback, collapse Masks.G into Normal alpha and skip refraction."
    },
    "LivingMossSilk": {
        "ue_master": "M_Surreal_LivingMossSilk",
        "instance_prefix": "MI_MossSilk",
        "material_model": "Sheer silk + living moss — silk clearcoat sheen, moss as fuzz/SSS",
        "parameters": {
            "BaseColor": "T_Surreal2_LivingMossSilk_BaseColor",
            "Normal": "T_Surreal2_LivingMossSilk_Normal",
            "Roughness": "T_Surreal2_LivingMossSilk_Roughness (silk 0.44 vs moss 0.84)",
            "Masks": "T_Surreal2_LivingMossSilk_Masks: R=veins, G=caps/bloom, B=sheen",
            "FuzzAmount": "Masks.R * 0.7 (moss fuzz)",
            "Subsurface": "Masks.R * moss green SSS, Masks.G bloom as emissive 0.06",
            "Sheen / ClearCoat": "Masks.B as silk clearcoat 0-0.6",
            "Wind": "SimpleGrassWind on Masks.R for living crawl (WPO)",
        },
        "instance_ideas": [
            "MI_MossSilk_Gown — gown fabric, moss veins as trim, growth scalar on Masks.R",
            "MI_MossSilk_Tapestry — wall hanging, no wind, high fuzz",
            "MI_MossSilk_Bloom — flower-burst variant, Masks.G emissive pulse on beat"
        ],
        "notes": "Growth scalar: moss = smoothstep(1-Growth, 1-Growth+0.12, Masks.R). Sheen uses cloth shading model; keep BaseColor desaturated where Masks.B high for true silk highlight."
    },
}

# ---------------------------------------------------------------------------
def cook_one(name, builder, seed, size):
    res = builder(seed, size)
    return res

def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--seed", type=int, default=SEED)
    ap.add_argument("--size", type=int, default=SIZE)
    ap.add_argument("--out", type=str, default=str(DEFAULT_OUT))
    args = ap.parse_args()

    out = Path(args.out)
    out.mkdir(parents=True, exist_ok=True)
    size = int(args.size)
    seed = int(args.seed)

    print(f"[surreal_masters2] seed={seed} size={size} out={out}")
    all_files = []
    seam_rows = []
    per_master_meta = {}

    for idx, (key, desc, builder) in enumerate(MASTERS):
        # per-master deterministic seed offset to keep streams independent
        mseed = seed + idx * 1000
        print(f"[surreal_masters2] cooking {key} ({desc}) mseed={mseed} ...")
        res = cook_one(key, builder, mseed, size)

        maps = {
            f"T_Surreal2_{key}_BaseColor": (res["BaseColor"], "rgb"),
            f"T_Surreal2_{key}_Normal": (res["Normal"], "rgb"),
            f"T_Surreal2_{key}_Roughness": (res["Roughness"], "gray"),
            f"T_Surreal2_{key}_Masks": (res["Masks"], "rgb"),
        }
        per_master_meta[key] = res.get("meta", {})

        for mname, (arr, kind) in maps.items():
            arr_f = np.clip(np.asarray(arr, np.float32), 0.0, 1.0)
            p = rc.save_image(out / f"{mname}.png", arr_f, kind)
            sha = rc.sha256_of(p)
            lr, tb = _seam_metric((arr_f*255.0).round().astype(np.uint8) if False else (arr_f*255.0))
            # compute seam on normalized float scaled to 0..1 (same as ingest: peak diff/255)
            # ingest metric is mean abs diff of uint8 levels /255; we replicate
            if arr_f.ndim == 3:
                a8 = (np.clip(arr_f,0,1)*255.0).round().astype(np.uint8)
                lr8 = np.mean(np.abs(a8[:,0,:].astype(np.int16) - a8[:,-1,:].astype(np.int16))) / 255.0
                tb8 = np.mean(np.abs(a8[0,:,:].astype(np.int16) - a8[-1,:,:].astype(np.int16))) / 255.0
            else:
                a8 = (np.clip(arr_f,0,1)*255.0).round().astype(np.uint8)
                lr8 = np.mean(np.abs(a8[:,0].astype(np.int16) - a8[:,-1].astype(np.int16))) / 255.0
                tb8 = np.mean(np.abs(a8[0,:].astype(np.int16) - a8[-1,:].astype(np.int16))) / 255.0

            status = "OK" if max(lr8, tb8) < 0.03 else "SEAM FAIL"
            print(f"  wrote {p.name} kind={kind} seam LR={lr8:.4f} TB={tb8:.4f} [{status}] sha={sha[:10]}...")
            if max(lr8, tb8) >= 0.03:
                print(f"    WARNING: seam >= 0.03 — check {mname}")
            all_files.append({
                "name": mname,
                "path": str(p),
                "kind": kind,
                "size": size,
                "seed": mseed,
                "sha256": sha,
                "seam_left_right": round(float(lr8), 6),
                "seam_top_bottom": round(float(tb8), 6),
                "tileable": bool(max(lr8, tb8) < 0.03),
            })
            seam_rows.append((mname, lr8, tb8))

    # ---- contact sheet (one row per master: BaseColor | Normal | Roughness | Masks) ----
    thumb = 256
    cols = 4
    rows = len(MASTERS)
    sheet_w = thumb * cols
    sheet_h = thumb * rows + 28
    sheet = Image.new("RGB", (sheet_w, sheet_h), (18, 18, 22))
    from PIL import ImageDraw, ImageFont
    draw = ImageDraw.Draw(sheet)
    try:
        font = ImageFont.load_default()
    except Exception:
        font = None

    def _thumb(arr, kind):
        a = np.clip(arr, 0, 1)
        if kind == "gray":
            rgb = np.dstack([a, a, a])
        else:
            rgb = a[..., :3] if a.ndim == 3 else np.dstack([a,a,a])
        im = Image.fromarray((rgb * 255).round().astype(np.uint8), "RGB")
        return im.resize((thumb, thumb), Image.LANCZOS)

    # reload thumbs from disk for contact accuracy (avoid holding all in RAM)
    for r, (key, _desc, _b) in enumerate(MASTERS):
        for c, suffix in enumerate(["_BaseColor", "_Normal", "_Roughness", "_Masks"]):
            mname = f"T_Surreal2_{key}{suffix}"
            kind = "rgb" if suffix != "_Roughness" else "gray"
            # we already have arr in last loop but re-derive from builder would repeat; instead load PNG
            p = out / f"{mname}.png"
            im = Image.open(str(p)).convert("RGB")
            im = im.resize((thumb, thumb), Image.LANCZOS)
            sheet.paste(im, (c * thumb, r * thumb))
        # label row
        label = f"{key}"
        draw.text((6, r * thumb + thumb - 14), label, fill=(220, 220, 230), font=font)
        # seam badge
        # find max seam for this master
        m_seams = [max(lr,tb) for nm, lr, tb in seam_rows if key in nm]
        ms = max(m_seams) if m_seams else 0
        draw.text((thumb*cols - 70, r * thumb + thumb - 14), f"seam {ms:.3f}", fill=(160, 220, 160) if ms < 0.03 else (255,120,120), font=font)

    # header
    draw.text((6, sheet_h - 18), f"Surreal Masters 2 — 6x4 tileable 1024  seed={seed}  seams<0.03  |  BaseColor  Normal  Roughness  Masks", fill=(180,180,190), font=font)
    sheet_path = out / "_SurrealMasters2_ContactSheet.png"
    sheet.save(str(sheet_path), format="PNG")
    print(f"[surreal_masters2] contact sheet -> {sheet_path}")

    # ---- manifests ----
    worst = max(max(lr,tb) for _, lr, tb in seam_rows) if seam_rows else 0
    manifest = {
        "schema": "melodia.surreal_masters2.v1",
        "seed": seed,
        "size": size,
        "generator": "surreal_masters2.py",
        "runtime": "python+PIL (numpy)",
        "tiling": "lattice-periodic; seam metric mean(|opposite edges|)/255 <0.03",
        "normal_convention": "OpenGL Y+ (flip G in UE if BC5 DirectX)",
        "output_dir": str(out),
        "contact_sheet": str(sheet_path),
        "masters": [k for k,_,_ in MASTERS],
        "per_master": per_master_meta,
        "seam_summary": {"worst": round(float(worst), 6), "all_below_0_03": bool(worst < 0.03)},
        "files": all_files,
    }
    mpath = out / "surreal_masters2_manifest.json"
    mpath.write_text(json.dumps(manifest, indent=2), encoding="utf-8")
    print(f"[surreal_masters2] manifest -> {mpath} worst seam {worst:.4f} {'PASS' if worst < 0.03 else 'FAIL'}")

    # ---- recipe json ----
    recipe_path = out / "surreal_masters_recipe.json"
    recipe_payload = {
        "schema": "melodia.surreal_masters_recipe.v1",
        "seed": seed,
        "masters_dir": str(out),
        "notes": "Each master is a tilable PBR set. Create one UE master material per entry, then instances as listed. Masks are data (sRGB=false). Import normals as Normalmap, Roughness as masks, Masks as masks.",
        "masters": RECIPE,
    }
    recipe_path.write_text(json.dumps(recipe_payload, indent=2), encoding="utf-8")
    print(f"[surreal_masters2] recipe -> {recipe_path}")

    # also write a light copy at project root for discoverability if different from out
    # copy recipe to surreal_sweep_wave2/ (as requested "Also write surreal_masters_recipe.json")
    alt = PROJECT_ROOT / "surreal_sweep_wave2" / "surreal_masters_recipe.json"
    if alt != recipe_path:
        alt.parent.mkdir(parents=True, exist_ok=True)
        alt.write_text(json.dumps(recipe_payload, indent=2), encoding="utf-8")
        print(f"[surreal_masters2] recipe copy -> {alt}")

    # summary
    print(f"[surreal_masters2] DONE {len(all_files)} maps + sheet + 2 jsons  worst seam {worst:.4f}")

if __name__ == "__main__":
    main()
