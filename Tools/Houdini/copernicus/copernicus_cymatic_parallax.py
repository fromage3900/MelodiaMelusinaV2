#!/usr/bin/env python
"""
Copernicus Cymatic Parallax — surreal singing/twinkling/dancing PBR map families.

Pure numpy pipeline. Produces parallax-ready height + 9 PBR maps per variant:
  CymaticMarble   — Chladni-veined singing stone
  GildedLoom      — fabric with moving gears
  SilkWaterfall   — silk with flowing water
  CavernWeave     — cavern rock + marble + crystals
  DancingCrystals — inlaid dancing twinkling crystals
  CherryBlossomWood — cherry wood with sakura flowers growing out
  GildedCoral     — coral branches with mother-of-pearl nacre + gold
  StarlitAbyss    — deep ocean bioluminescent abyss
  FrozenFracture  — cracked ice with frost crystals + air bubbles
  SingingConstellations — living star-map with singing nodes + nebula veins
  FinalDreamweaver — IMPOSSIBLE: fabric woven from frozen moonlight + living shadows
"""

from __future__ import annotations
import argparse
import json
from pathlib import Path
import numpy as np
from PIL import Image, ImageFilter

PROJECT_ROOT = Path(__file__).resolve().parents[3]
SEED = 20260831

VARIANTS = {
    "CymaticMarble": dict(
        marble_light=(250, 246, 236), marble_dark=(180, 168, 150),
        vein=(60, 52, 44), glow=(180, 220, 255),
        rough_marble=0.15, rough_vein=0.50,
        glow_intensity=0.5, phase_speed=0.7,
    ),
    "GildedLoom": dict(
        fabric=(48, 24, 28), fabric_hi=(72, 36, 38),
        gear=(220, 184, 96), gear_shadow=(160, 128, 64),
        thread=(190, 170, 140),
        rough_fabric=0.55, rough_gear=0.22, rough_thread=0.40,
        gear_teeth=12, gear_depth=0.18, rot_speed=0.1,
    ),
    "SilkWaterfall": dict(
        silk=(244, 240, 232), silk_shadow=(220, 214, 204),
        water=(140, 190, 220), water_deep=(80, 140, 190),
        foam=(255, 255, 255),
        rough_silk=0.25, rough_water=0.08, rough_foam=0.15,
        flow_angle=0.4, flow_speed=1.0,
    ),
    "CavernWeave": dict(
        rock=(36, 32, 30), rock_hi=(58, 52, 48),
        marble=(220, 210, 196), crystal=(180, 230, 255),
        rough_rock=0.78, rough_marble=0.28, rough_crystal=0.12,
        crystal_glow=0.7, phase_speed=0.3,
    ),
    "DancingCrystals": dict(
        base=(28, 24, 36), fabric=(52, 36, 64),
        crystal=(220, 180, 255), crystal_alt=(180, 220, 255),
        glow=(255, 240, 200),
        rough_base=0.50, rough_crystal=0.10, rough_fabric=0.45,
        twinkle_speed=0.3, dance_amount=0.05,
    ),
    "CherryBlossomWood": dict(
        wood_dark=(120, 70, 40), wood_mid=(180, 120, 80), wood_hi=(220, 170, 120),
        bark=(80, 50, 30), blossom=(255, 200, 220), blossom_dark=(230, 160, 190),
        leaf=(120, 180, 100), leaf_dark=(80, 140, 70),
        glow=(255, 230, 200),
        rough_wood=0.45, rough_bark=0.75, rough_blossom=0.25, rough_leaf=0.35,
        glow_intensity=0.35, sway_speed=0.2,
    ),
    "GildedCoral": dict(
        coral=(255, 140, 120), coral_dark=(200, 90, 80), coral_hi=(255, 180, 160),
        nacre=(220, 230, 255), nacre_alt=(200, 220, 245),
        gold=(220, 184, 96), gold_shadow=(160, 128, 64),
        rough_coral=0.55, rough_nacre=0.15, rough_gold=0.22,
        glow_intensity=0.45, pulse_speed=0.5,
    ),
    "StarlitAbyss": dict(
        deep=(15, 20, 40), mid=(30, 50, 90), surface=(60, 100, 160),
        biolum=(100, 220, 255), biolum_alt=(150, 100, 200),
        glow=(200, 240, 255),
        rough_deep=0.85, rough_biolum=0.10,
        glow_intensity=0.6, twinkle_speed=1.5, current_speed=0.3,
    ),
    "FrozenFracture": dict(
        ice=(220, 240, 255), ice_shadow=(180, 210, 240),
        crack=(80, 140, 200), crack_deep=(40, 80, 140),
        frost=(240, 250, 255), bubble=(200, 230, 255),
        glow=(180, 220, 255),
        rough_ice=0.08, rough_crack=0.65, rough_frost=0.25,
        glow_intensity=0.3, shimmer_speed=0.4,
    ),
    "SingingConstellations": dict(
        void=(8, 10, 22), nebula=(40, 20, 80), star_core=(255, 250, 230),
        star_halo=(180, 200, 255), constellation=(100, 180, 255),
        singing_node=(255, 200, 100), glow=(200, 220, 255),
        rough_void=0.90, rough_star=0.05, rough_nebula=0.70,
        glow_intensity=0.8, sing_speed=2.0, twinkle_speed=1.2,
    ),
    "FinalDreamweaver": dict(
        moonlight=(200, 220, 255), shadow=(20, 15, 30), void=(5, 5, 15),
        dream=(255, 180, 220), nightmare=(180, 50, 100), gold_thread=(255, 220, 150),
        living_shadow=(40, 20, 60), glow=(220, 200, 255),
        rough_moonlight=0.12, rough_shadow=0.95, rough_dream=0.20,
        glow_intensity=0.55, weave_speed=0.8, breathe_speed=0.4,
    ),
    # === Glitter pile materials ===
    "GlitterRainbow": dict(
        bg=(15, 15, 20), flake_colors=[(255, 50, 80), (255, 150, 50), (255, 220, 50),
                                        (50, 255, 100), (50, 150, 255), (150, 50, 255),
                                        (255, 100, 200), (100, 255, 220)],
        rough_bg=0.60, rough_flake=0.05, metallic_flake=1.0,
        glow_intensity=0.7, flake_density=120, flake_size_range=(3, 12),
    ),
    "GlitterHolographic": dict(
        bg=(10, 10, 15), flake_colors=[(255, 80, 120), (255, 180, 80), (220, 255, 100),
                                        (80, 255, 180), (100, 180, 255), (180, 100, 255),
                                        (255, 150, 220), (150, 255, 255)],
        rough_bg=0.55, rough_flake=0.03, metallic_flake=1.0,
        glow_intensity=0.9, flake_density=150, flake_size_range=(2, 10),
    ),
    "GlitterGold": dict(
        bg=(25, 15, 5), flake_colors=[(255, 215, 100), (255, 235, 150), (255, 195, 70),
                                       (255, 250, 200), (220, 180, 60), (255, 225, 130)],
        rough_bg=0.50, rough_flake=0.04, metallic_flake=1.0,
        glow_intensity=0.6, flake_density=100, flake_size_range=(4, 14),
    ),
    "GlitterIridescent": dict(
        bg=(12, 12, 18), flake_colors=[(200, 220, 255), (255, 200, 220), (220, 255, 200),
                                        (255, 240, 180), (200, 200, 255), (255, 200, 255)],
        rough_bg=0.45, rough_flake=0.02, metallic_flake=1.0,
        glow_intensity=1.0, flake_density=130, flake_size_range=(2, 8),
    ),
    "GlitterCrystal": dict(
        bg=(18, 18, 22), flake_colors=[(255, 255, 255), (240, 245, 255), (255, 240, 250),
                                        (240, 255, 245), (250, 245, 255), (255, 255, 240)],
        rough_bg=0.40, rough_flake=0.01, metallic_flake=0.95,
        glow_intensity=0.8, flake_density=80, flake_size_range=(5, 18),
    ),
    "FractalCathedral": dict(
        stone=(45, 42, 50), gold=(220, 184, 96), glow=(180, 220, 255),
        void=(15, 12, 20), accent=(150, 50, 255),
        rough_stone=0.55, rough_gold=0.20, fractal_depth=5,
        glow_intensity=0.7, branch_count=5, scale_factor=0.618,
    ),
    "GoldenSpiralGrove": dict(
        base=(25, 20, 15), gold=(255, 215, 100), glow=(255, 200, 150),
        void=(10, 8, 12), accent=(255, 180, 50),
        rough_base=0.45, rough_gold=0.15, spiral_turns=8,
        glow_intensity=0.6, phi=1.61803398875,
    ),
    "VoronoiSacredGeometry": dict(
        bg=(12, 10, 18), cell_a=(220, 180, 255), cell_b=(180, 220, 255),
        edge=(255, 255, 255), glow=(200, 220, 255),
        rough_bg=0.50, rough_edge=0.10, cell_count=36,
        glow_intensity=0.8, symmetry=6,
    ),
    "TessellationSanctum": dict(
        bg=(18, 15, 22), tile_a=(255, 200, 150), tile_b=(150, 200, 255),
        grout=(30, 25, 35), glow=(255, 240, 200),
        rough_bg=0.40, rough_tile=0.25, tile_size=32,
        glow_intensity=0.5, pattern="penrose",
    ),
    "SpiralMonument": dict(
        stone=(35, 32, 40), gold=(255, 220, 130), glow=(255, 255, 200),
        void=(10, 8, 15), accent=(200, 150, 255),
        rough_stone=0.35, rough_gold=0.12, spiral_count=3,
        glow_intensity=0.9, growth_rate=0.3063489, turns=6.28318,
    ),
    # === P4 overnight — 8 new tileable cymatics (21 -> 29) ===
    "TwinklingGears": dict(
        brass=(210, 175, 90), brass_dark=(160, 125, 60), steel=(180, 185, 195),
        void=(18, 16, 22), glow=(255, 240, 180),
        rough_brass=0.25, rough_steel=0.35, glow_intensity=0.6, gear_count=7,
    ),
    "EnchantedTome": dict(
        parchment=(235, 220, 185), ink=(35, 30, 45), gold_leaf=(255, 215, 100),
        leather=(80, 45, 30), glow=(255, 230, 180),
        rough_parchment=0.65, rough_ink=0.80, glow_intensity=0.4, script_density=0.5,
    ),
    "SingingSilk": dict(
        silk=(245, 235, 225), silk_shadow=(220, 210, 195), thread_gold=(255, 220, 140),
        thread_rose=(255, 180, 200), glow=(255, 240, 220),
        rough_silk=0.20, rough_thread=0.35, glow_intensity=0.5, weave_tightness=0.7,
    ),
    "MoltenCore": dict(
        basalt=(25, 22, 30), magma=(255, 80, 30), magma_hi=(255, 180, 80),
        crust=(60, 35, 25), glow=(255, 120, 40),
        rough_basalt=0.75, rough_magma=0.15, glow_intensity=0.9, crack_scale=0.6,
    ),
    "PearlWeave": dict(
        pearl=(240, 235, 245), pearl_shadow=(210, 205, 225), nacre=(200, 220, 255),
        thread=(255, 215, 150), glow=(220, 240, 255),
        rough_pearl=0.12, rough_thread=0.30, glow_intensity=0.55, weave_scale=0.5,
    ),
    "StarlitLoom": dict(
        void=(12, 14, 28), loom_wood=(80, 60, 45), star=(255, 250, 230),
        nebula=(60, 40, 120), glow=(180, 200, 255),
        rough_void=0.85, rough_wood=0.55, glow_intensity=0.7, loom_count=9,
    ),
    "FrostBloom": dict(
        frost=(230, 245, 255), ice=(180, 220, 245), bloom=(255, 200, 230),
        stem=(120, 180, 140), glow=(200, 230, 255),
        rough_frost=0.18, rough_bloom=0.30, glow_intensity=0.5, bloom_scale=0.6,
    ),
    "ChoirStone": dict(
        stone=(50, 48, 58), stone_hi=(75, 72, 85), gold_vein=(255, 220, 130),
        resonance=(180, 200, 255), glow=(255, 240, 200),
        rough_stone=0.50, rough_vein=0.20, glow_intensity=0.6, choir_count=12,
    ),
    "CrystalCathedral": dict(
        stone=(28, 30, 38), stone_hi=(55, 58, 70), crystal=(220, 240, 255),
        crystal_facet=(180, 205, 255), irid=(200, 180, 255), glow=(180, 210, 255),
        void=(10, 12, 18), gold_trim=(255, 220, 140),
        rough_stone=0.45, rough_crystal=0.12, rough_facet=0.08, glow_intensity=0.85, crystal_count=16,
    ),
}

# === Math helpers ===

def smoothstep(edge0, edge1, x):
    t = np.clip((x - edge0) / (edge1 - edge0 + 1e-9), 0.0, 1.0)
    return t * t * (3.0 - 2.0 * t)

def mix(a, b, t):
    a = np.asarray(a, np.float32)
    b = np.asarray(b, np.float32)
    t = np.asarray(t, np.float32)
    if a.ndim == 1 and a.shape[0] == 3 and t.ndim >= 2:
        a = a[None, None, :]
    if b.ndim == 1 and b.shape[0] == 3 and t.ndim >= 2:
        b = b[None, None, :]
    if t.ndim == 2 and a.ndim == 3:
        t = t[:, :, None]
    return a * (1.0 - t) + b * t

def mask_color(mask, color):
    return mask[:, :, None] * np.asarray(color, np.float32)

def to_u8(arr):
    return np.clip(arr, 0, 255).astype(np.uint8)

def col(t):
    return np.array(t, np.float32) / 255.0

# === Noise ===

def tileable_value_noise(h, w, period, seed=0):
    rng = np.random.RandomState(seed)
    grid = rng.rand(period, period).astype(np.float32)
    y = np.linspace(0, period, h, endpoint=False)
    x = np.linspace(0, period, w, endpoint=False)
    yi = np.floor(y).astype(int) % period
    xi = np.floor(x).astype(int) % period
    yf = y - np.floor(y)
    xf = x - np.floor(x)
    g00 = grid[yi][:, xi]
    g01 = grid[yi][:, (xi + 1) % period]
    g10 = grid[(yi + 1) % period][:, xi]
    g11 = grid[(yi + 1) % period][:, (xi + 1) % period]
    g0 = g00 * (1 - xf) + g01 * xf
    g1 = g10 * (1 - xf) + g11 * xf
    return g0 * (1 - yf[:, None]) + g1 * yf[:, None]

def fbm_noise(h, w, base_period, octaves, seed=0):
    result = np.zeros((h, w), np.float32)
    amp, period, total = 1.0, base_period, 0.0
    for o in range(octaves):
        result += tileable_value_noise(h, w, max(2, period), seed + o * 100) * amp
        total += amp
        amp *= 0.5
        period = max(2, period // 2)
    return result / total

def warped_fbm(h, w, base_period, octaves, warp_amount, seed=0):
    """fBm with domain warping for more organic flow. Tileable-safe: wraps edges."""
    base = fbm_noise(h, w, base_period, octaves, seed)
    warp_x = fbm_noise(h, w, base_period * 2, octaves - 1, seed + 100) * warp_amount
    warp_y = fbm_noise(h, w, base_period * 2, octaves - 1, seed + 200) * warp_amount
    yy, xx = np.mgrid[0:h, 0:w].astype(np.float32)
    # Tileable: wrap with modulo instead of clip (clipping creates seams)
    warped_xx = (xx.astype(int) + (warp_x * w * 0.1).astype(int)) % w
    warped_yy = (yy.astype(int) + (warp_y * h * 0.1).astype(int)) % h
    return base[warped_yy, warped_xx]

# === Pattern generators ===

def cymatic_chladni(h, w, freqs, phases, weights):
    """Authentic Chladni rectangular-plate formula. Tileable: uses 2*pi periodicity."""
    yy, xx = np.mgrid[0:h, 0:w].astype(np.float32)
    # Tileable: use 2*pi*m*xx/w so sin(0) = sin(2*pi*m) = 0 at edges
    nx = xx / w
    ny = yy / h
    pattern = np.zeros((h, w), np.float32)
    for (m, n), phase, weight in zip(freqs, phases, weights):
        term1 = np.sin(2 * np.pi * m * nx + phase) * np.sin(2 * np.pi * n * ny + phase * 0.3)
        term2 = np.sin(2 * np.pi * n * nx + phase * 0.7) * np.sin(2 * np.pi * m * ny + phase)
        pattern += (term1 - term2) * weight
    pmin, pmax = pattern.min(), pattern.max()
    return (pattern - pmin) / (pmax - pmin + 1e-9)

def gear_shape(h, w, cx, cy, radius, teeth, tooth_depth, rotation=0):
    yy, xx = np.mgrid[0:h, 0:w].astype(np.float32)
    dx, dy = xx - cx, yy - cy
    dist = np.sqrt(dx * dx + dy * dy)
    angle = np.arctan2(dy, dx) + rotation
    tooth_profile = 1.0 - tooth_depth * (0.5 + 0.5 * np.cos(angle * teeth))
    outer_r = radius * tooth_profile
    inner_r = radius * 0.15
    return smoothstep(outer_r + 2, outer_r - 2, dist) * (1.0 - smoothstep(inner_r + 1, inner_r - 1, dist))

def crystal_shape(h, w, cx, cy, size, sides=6, rotation=0):
    yy, xx = np.mgrid[0:h, 0:w].astype(np.float32)
    dx, dy = xx - cx, yy - cy
    dist = np.sqrt(dx * dx + dy * dy)
    angle = np.arctan2(dy, dx) + rotation
    sector = np.abs((angle % (2 * np.pi / sides)) - np.pi / sides)
    polygon_r = size * np.cos(np.pi / sides) / (np.cos(sector) + 1e-9)
    return smoothstep(polygon_r, polygon_r * 0.55, dist)

def water_stream(h, w, flow_angle, warp_seed=0, time_phase=0):
    noise = fbm_noise(h, w, 8, 5, warp_seed)
    yy, xx = np.mgrid[0:h, 0:w].astype(np.float32)
    flow = np.cos(flow_angle) * xx + np.sin(flow_angle) * yy
    channel = np.sin(flow * 0.008 + noise * 5 + time_phase * 2)
    return smoothstep(0.2, 0.8, channel)

def height_to_normal(height, strength=2.0):
    dx = (np.roll(height, -1, axis=1) - np.roll(height, 1, axis=1)) * strength
    dy = (np.roll(height, -1, axis=0) - np.roll(height, 1, axis=0)) * strength
    normal = np.dstack((-dx, -dy, np.ones(height.shape, np.float32)))
    length = np.sqrt(np.sum(normal * normal, axis=2) + 1e-9)
    normal = normal / length[:, :, None]
    return np.clip((normal * 0.5 + 0.5) * 255, 0, 255).astype(np.uint8)

def _assemble(h, w, basecolor, rough, metallic, height, emissive, iri, opacity):
    if basecolor.ndim == 2:
        basecolor = np.dstack([basecolor] * 3)
    if emissive.ndim == 2:
        emissive = np.dstack([emissive] * 3)
    if iri.ndim == 2:
        iri = np.dstack([iri] * 3)

    rough = np.clip(rough, 0, 1)
    metallic = np.clip(metallic, 0, 1)
    height = np.clip(height, 0, 1)
    emissive = np.clip(emissive, 0, 1)
    iri = np.clip(iri, 0, 1)
    opacity = np.clip(opacity, 0, 1)

    normal = height_to_normal(height, strength=2.0)
    ao = 1.0 - height * 0.6
    orm = np.dstack([to_u8(ao * 255), to_u8(rough * 255), to_u8(metallic * 255)])

    return {
        "BaseColor": to_u8(basecolor * 255),
        "Normal": normal,
        "Roughness": to_u8(rough * 255),
        "Metallic": to_u8(metallic * 255),
        "Height": to_u8(np.dstack([height] * 3) * 255),
        "ORM": orm,
        "Emissive": to_u8(emissive * 255),
        "Iridescence": to_u8(iri * 255),
        "Opacity": to_u8(opacity * 255),
    }

# === Variant builders ===

def build_cymatic_marble(h, w, frame, total_frames):
    p = VARIANTS["CymaticMarble"]
    phase = frame / max(total_frames, 1) * 2 * np.pi
    cym = cymatic_chladni(h, w, freqs=[(12, 18), (22, 14), (35, 28), (16, 40), (44, 36)],
                          phases=[phase * p["phase_speed"] + i * 1.3 for i in range(5)],
                          weights=[1.0, 0.7, 0.5, 0.4, 0.3])
    vein_raw = 1.0 - np.abs(cym - 0.5) * 2.0
    vein = smoothstep(0.82, 0.97, vein_raw)
    marble = warped_fbm(h, w, 16, 5, 0.3, SEED)
    height = vein * 0.65 + marble * 0.12 + cym * 0.08
    base = mix(col(p["marble_dark"]), col(p["marble_light"]), marble * 0.7 + 0.3)
    base = mix(base, col(p["vein"]), vein * 0.92)
    rough = mix(p["rough_marble"], p["rough_vein"], vein)
    emissive = mask_color(smoothstep(0.6, 0.9, vein_raw), col(p["glow"]) * p["glow_intensity"])
    iri = vein * 0.45 + marble * 0.12
    return _assemble(h, w, base, rough, np.zeros((h, w), np.float32), height, emissive, iri, np.ones((h, w), np.float32))

def build_gilded_loom(h, w, frame, total_frames):
    p = VARIANTS["GildedLoom"]
    rot = frame / max(total_frames, 1) * 2 * np.pi * p["rot_speed"]
    weave = warped_fbm(h, w, 64, 3, 0.2, SEED) * 0.5 + warped_fbm(h, w, 128, 2, 0.2, SEED + 1) * 0.5
    gear_mask = np.zeros((h, w), np.float32)
    gear_r = min(h, w) // 8
    spacing = gear_r * 2.2
    for gy in range(int(h / spacing) + 1):
        for gx in range(int(w / spacing) + 1):
            cx = gx * spacing + (gy % 2) * spacing * 0.5
            cy = gy * spacing
            gear_mask += gear_shape(h, w, cx, cy, gear_r, p["gear_teeth"], p["gear_depth"],
                                   rot * (1 if (gx + gy) % 2 == 0 else -1))
    gear_mask = np.clip(gear_mask, 0, 1)
    gear_detail = fbm_noise(h, w, 32, 3, SEED + 5) * gear_mask
    height = weave * 0.12 + gear_mask * 0.72 + gear_detail * 0.16
    base = mix(col(p["fabric"]), col(p["fabric_hi"]), weave)
    base = mix(base, col(p["gear"]), gear_mask * 0.92)
    base = mix(base, col(p["gear_shadow"]), gear_detail * 0.3 * gear_mask)
    base = mix(base, col(p["thread"]), weave * gear_mask * 0.2)
    rough = mix(p["rough_fabric"], p["rough_gear"], gear_mask)
    rough = mix(rough, p["rough_thread"], weave * 0.3)
    metallic = gear_mask * 0.85
    edge = smoothstep(0.6, 0.8, gear_mask) * (1 - smoothstep(0.8, 1.0, gear_mask))
    emissive = mask_color(edge, col(p["gear"]) * 0.15)
    iri = gear_mask * 0.2
    return _assemble(h, w, base, rough, metallic, height, emissive, iri, np.ones((h, w), np.float32))

def build_silk_waterfall(h, w, frame, total_frames):
    p = VARIANTS["SilkWaterfall"]
    phase = frame / max(total_frames, 1) * 2 * np.pi
    weave = warped_fbm(h, w, 96, 3, 0.15, SEED)
    water = water_stream(h, w, p["flow_angle"], SEED, phase * p["flow_speed"])
    water2 = water_stream(h, w, p["flow_angle"] + 1.2, SEED + 50, phase * p["flow_speed"] * 0.7)
    water = np.clip(water + water2 * 0.5, 0, 1)
    foam = smoothstep(0.45, 0.55, water) * (1 - smoothstep(0.55, 0.65, water))
    foam += smoothstep(0.75, 0.85, water) * (1 - smoothstep(0.85, 0.95, water))
    foam = np.clip(foam, 0, 1)
    height = weave * 0.08 + (1 - water) * 0.52 + foam * 0.3
    base = mix(col(p["silk"]), col(p["silk_shadow"]), weave)
    base = mix(base, col(p["water"]), water * 0.82)
    base = mix(base, col(p["water_deep"]), water * water * 0.5)
    base = mix(base, col(p["foam"]), foam * 0.92)
    rough = mix(p["rough_silk"], p["rough_water"], water)
    rough = mix(rough, p["rough_foam"], foam)
    caustic = warped_fbm(h, w, 4, 4, 0.5, SEED + int(phase * 5)) * water
    emissive = mask_color(smoothstep(0.6, 0.9, caustic), col(p["water"]) * 0.1)
    iri = water * 0.35
    return _assemble(h, w, base, rough, np.zeros((h, w), np.float32), height, emissive, iri, np.ones((h, w), np.float32))

def build_cavern_weave(h, w, frame, total_frames):
    p = VARIANTS["CavernWeave"]
    phase = frame / max(total_frames, 1) * 2 * np.pi
    rock = warped_fbm(h, w, 32, 6, 0.4, SEED)
    rock_detail = fbm_noise(h, w, 8, 4, SEED + 3)
    cym = cymatic_chladni(h, w, freqs=[(10, 14), (18, 12), (26, 20)],
                          phases=[phase * p["phase_speed"] + i for i in range(3)],
                          weights=[1.0, 0.6, 0.4])
    vein_raw = 1.0 - np.abs(cym - 0.5) * 2.0
    vein = smoothstep(0.75, 0.95, vein_raw)
    crystal_mask = np.zeros((h, w), np.float32)
    rng = np.random.RandomState(SEED + 42)
    for _ in range(24):
        cx, cy = rng.randint(0, w), rng.randint(0, h)
        size = rng.randint(min(h, w) // 15, min(h, w) // 5)
        sides = rng.choice([4, 5, 6, 8])
        rot = rng.rand() * 2 * np.pi
        crystal_mask += crystal_shape(h, w, cx, cy, size, sides, rot)
    crystal_mask = np.clip(crystal_mask, 0, 1)
    height = rock * 0.35 + rock_detail * 0.12 + vein * 0.28 + crystal_mask * 0.55
    base = mix(col(p["rock"]), col(p["rock_hi"]), rock)
    base = mix(base, col(p["marble"]), vein * 0.88)
    base = mix(base, col(p["crystal"]), crystal_mask * 0.92)
    rough = mix(p["rough_rock"], p["rough_marble"], vein)
    rough = mix(rough, p["rough_crystal"], crystal_mask)
    glow_noise = fbm_noise(h, w, 4, 3, SEED + 7)
    emissive = mask_color(crystal_mask * smoothstep(0.25, 0.6, glow_noise), col(p["crystal"]) * p["crystal_glow"])
    iri = crystal_mask * 0.55 + vein * 0.12
    return _assemble(h, w, base, rough, np.zeros((h, w), np.float32), height, emissive, iri, np.ones((h, w), np.float32))

def build_dancing_crystals(h, w, frame, total_frames):
    p = VARIANTS["DancingCrystals"]
    phase = frame / max(total_frames, 1) * 2 * np.pi
    fabric = warped_fbm(h, w, 64, 3, 0.2, SEED)
    crystal_mask = np.zeros((h, w), np.float32)
    crystal_color = np.zeros((h, w, 3), np.float32)
    rng = np.random.RandomState(SEED + 99)
    for i in range(30):
        base_cx = rng.randint(0, w)
        base_cy = rng.randint(0, h)
        dance_x = int(np.sin(phase * p["twinkle_speed"] + i * 0.7) * min(h, w) * p["dance_amount"])
        dance_y = int(np.cos(phase * p["twinkle_speed"] * 1.3 + i * 0.5) * min(h, w) * p["dance_amount"])
        cx = (base_cx + dance_x) % w
        cy = (base_cy + dance_y) % h
        size = rng.randint(min(h, w) // 25, min(h, w) // 10)
        sides = rng.choice([4, 5, 6, 7, 8])
        rot = rng.rand() * 2 * np.pi + phase * 0.2
        cm = crystal_shape(h, w, cx, cy, size, sides, rot)
        crystal_mask = np.clip(crystal_mask + cm, 0, 1)
        c = col(p["crystal"]) if i % 2 == 0 else col(p["crystal_alt"])
        crystal_color = np.clip(crystal_color + mask_color(cm, c), 0, 1)
    twinkle_field = warped_fbm(h, w, 8, 3, 0.3, SEED + int(phase * 10))
    height = fabric * 0.08 + crystal_mask * 0.78
    base = mix(col(p["base"]), col(p["fabric"]), fabric * 0.5)
    base = np.clip(base * (1 - crystal_mask[:, :, None]) + crystal_color * crystal_mask[:, :, None] * 2, 0, 1)
    rough = mix(p["rough_base"], p["rough_fabric"], fabric * 0.3)
    rough = mix(rough, p["rough_crystal"], crystal_mask)
    twinkle_bright = smoothstep(0.3, 0.7, twinkle_field) * crystal_mask
    emissive = mask_color(twinkle_bright, col(p["glow"]) * 1.2)
    iri = crystal_mask * 0.65 * twinkle_field
    return _assemble(h, w, base, rough, np.zeros((h, w), np.float32), height, emissive, iri, np.ones((h, w), np.float32))

def build_cherry_blossom_wood(h, w, frame, total_frames):
    p = VARIANTS["CherryBlossomWood"]
    phase = frame / max(total_frames, 1) * 2 * np.pi
    yy, xx = np.mgrid[0:h, 0:w].astype(np.float32)
    grain_noise = warped_fbm(h, w, 32, 5, 0.3, SEED)
    ring_pattern = np.sin((yy / h * 8 + grain_noise * 2) * np.pi) * 0.5 + 0.5
    wood_grain = warped_fbm(h, w, 64, 4, 0.25, SEED + 1) * 0.3 + ring_pattern * 0.7
    crack_noise = fbm_noise(h, w, 16, 3, SEED + 2)
    bark_cracks = smoothstep(0.55, 0.75, crack_noise) * (1 - smoothstep(0.75, 0.95, crack_noise))
    # ANIMATED blossom clusters
    blossom_mask = np.zeros((h, w), np.float32)
    rng = np.random.RandomState(SEED + 10)
    for i in range(18):
        base_cx = rng.randint(0, w)
        base_cy = rng.randint(0, h)
        drift_x = int(np.sin(phase * p["sway_speed"] + i * 0.9) * min(h, w) * 0.04)
        drift_y = int(np.cos(phase * p["sway_speed"] * 0.8 + i * 1.1) * min(h, w) * 0.03)
        cx = (base_cx + drift_x) % w
        cy = (base_cy + drift_y) % h
        size = rng.randint(min(h, w) // 30, min(h, w) // 12)
        sides = rng.choice([5, 6, 8])
        rot = rng.rand() * 2 * np.pi + phase * 0.05
        blossom_mask += crystal_shape(h, w, cx, cy, size, sides, rot)
    blossom_mask = np.clip(blossom_mask, 0, 1)
    # ANIMATED leaves
    leaf_mask = np.zeros((h, w), np.float32)
    for i in range(12):
        base_cx = rng.randint(0, w)
        base_cy = rng.randint(0, h)
        drift_x = int(np.sin(phase * p["sway_speed"] * 1.2 + i * 1.3) * min(h, w) * 0.025)
        drift_y = int(np.cos(phase * p["sway_speed"] + i * 0.7) * min(h, w) * 0.02)
        cx = (base_cx + drift_x) % w
        cy = (base_cy + drift_y) % h
        size = rng.randint(min(h, w) // 40, min(h, w) // 20)
        leaf_mask += crystal_shape(h, w, cx, cy, size, 3, rng.rand() * 2 * np.pi + phase * 0.03) * 0.7
    leaf_mask = np.clip(leaf_mask, 0, 1)
    height = wood_grain * 0.25 + bark_cracks * 0.35 + blossom_mask * 0.45 + leaf_mask * 0.25
    base = mix(col(p["wood_dark"]), col(p["wood_hi"]), wood_grain)
    base = mix(base, col(p["bark"]), bark_cracks * 0.7)
    base = mix(base, col(p["blossom"]), blossom_mask * 0.9)
    base = mix(base, col(p["leaf"]), leaf_mask * 0.85)
    rough = mix(p["rough_wood"], p["rough_bark"], bark_cracks)
    rough = mix(rough, p["rough_blossom"], blossom_mask)
    rough = mix(rough, p["rough_leaf"], leaf_mask)
    glow_field = fbm_noise(h, w, 8, 3, SEED + 5)
    emissive = mask_color(blossom_mask * smoothstep(0.4, 0.8, glow_field), col(p["glow"]) * p["glow_intensity"])
    iri = blossom_mask * 0.3 + wood_grain * 0.05
    return _assemble(h, w, base, rough, np.zeros((h, w), np.float32), height, emissive, iri, np.ones((h, w), np.float32))

def build_gilded_coral(h, w, frame, total_frames):
    p = VARIANTS["GildedCoral"]
    phase = frame / max(total_frames, 1) * 2 * np.pi
    coral_pattern = cymatic_chladni(h, w, freqs=[(8, 12), (14, 10), (20, 16)],
                                    phases=[phase * p["pulse_speed"] + i * 1.1 for i in range(3)],
                                    weights=[1.0, 0.7, 0.5])
    coral_mask = smoothstep(0.35, 0.65, coral_pattern)
    nacre_mask = smoothstep(0.2, 0.5, 1.0 - coral_pattern) * (1 - coral_mask)
    gold_edges = smoothstep(0.6, 0.8, coral_pattern) * (1 - smoothstep(0.8, 0.95, coral_pattern))
    height = coral_mask * 0.55 + nacre_mask * 0.15 + gold_edges * 0.35
    base = mix(col(p["coral_dark"]), col(p["coral_hi"]), coral_pattern)
    base = mix(base, col(p["nacre"]), nacre_mask * 0.85)
    base = mix(base, col(p["gold"]), gold_edges * 0.9)
    rough = mix(p["rough_coral"], p["rough_nacre"], nacre_mask)
    rough = mix(rough, p["rough_gold"], gold_edges)
    metallic = gold_edges * 0.85
    tip_glow = warped_fbm(h, w, 4, 3, 0.6, SEED + 8)
    emissive = mask_color(coral_mask * smoothstep(0.5, 0.9, tip_glow), col(p["coral"]) * p["glow_intensity"])
    iri = nacre_mask * 0.6 + gold_edges * 0.25
    return _assemble(h, w, base, rough, metallic, height, emissive, iri, np.ones((h, w), np.float32))

def build_starlit_abyss(h, w, frame, total_frames):
    p = VARIANTS["StarlitAbyss"]
    phase = frame / max(total_frames, 1) * 2 * np.pi
    yy = np.linspace(0, 1, h).astype(np.float32)[:, None]
    depth = np.broadcast_to(yy, (h, w))
    current = warped_fbm(h, w, 16, 5, 0.4, SEED + int(phase * p["current_speed"] * 10))
    # ANIMATED bioluminescent nodes
    biolum_mask = np.zeros((h, w), np.float32)
    rng = np.random.RandomState(SEED + 20)
    for i in range(35):
        base_cx = rng.randint(0, w)
        base_cy = rng.randint(0, h)
        drift_x = int(np.sin(phase * p["current_speed"] + i * 1.3) * min(h, w) * 0.03)
        drift_y = int(np.cos(phase * p["current_speed"] * 0.7 + i * 0.9) * min(h, w) * 0.02)
        cx = (base_cx + drift_x) % w
        cy = (base_cy + drift_y) % h
        size = rng.randint(min(h, w) // 50, min(h, w) // 15)
        biolum_mask += crystal_shape(h, w, cx, cy, size, rng.choice([4, 5, 6, 8]), rng.rand() * 2 * np.pi + phase * 0.1)
    biolum_mask = np.clip(biolum_mask, 0, 1)
    height = depth * 0.2 + current * 0.15 + biolum_mask * 0.65
    base = mix(col(p["deep"]), col(p["surface"]), depth)
    base = mix(base, col(p["biolum"]), biolum_mask * 0.9)
    rough = mix(p["rough_deep"], p["rough_biolum"], biolum_mask)
    twinkle = warped_fbm(h, w, 8, 3, 0.5, SEED + int(phase * p["twinkle_speed"] * 10))
    node_twinkle = np.sin(phase * p["twinkle_speed"] * 3 + np.arange(h * w).reshape(h, w) * 0.01) * 0.3 + 0.7
    emissive = mask_color(biolum_mask * smoothstep(0.3, 0.8, twinkle) * node_twinkle, col(p["glow"]) * p["glow_intensity"] * 1.5)
    iri = biolum_mask * 0.4 + depth * 0.1
    return _assemble(h, w, base, rough, np.zeros((h, w), np.float32), height, emissive, iri, np.ones((h, w), np.float32))

def build_frozen_fracture(h, w, frame, total_frames):
    p = VARIANTS["FrozenFracture"]
    phase = frame / max(total_frames, 1) * 2 * np.pi
    ice_variation = warped_fbm(h, w, 32, 4, 0.2, SEED)
    crack_pattern = cymatic_chladni(h, w, freqs=[(6, 8), (10, 12), (14, 10)],
                                    phases=[phase * p["shimmer_speed"] + i * 1.5 for i in range(3)],
                                    weights=[1.0, 0.8, 0.6])
    crack_lines = smoothstep(0.7, 0.95, 1.0 - np.abs(crack_pattern - 0.5) * 2)
    frost_mask = np.zeros((h, w), np.float32)
    rng = np.random.RandomState(SEED + 30)
    for _ in range(20):
        cx, cy = rng.randint(0, w), rng.randint(0, h)
        size = rng.randint(min(h, w) // 35, min(h, w) // 15)
        sides = rng.choice([4, 6, 8])
        frost_mask += crystal_shape(h, w, cx, cy, size, sides, rng.rand() * 2 * np.pi)
    frost_mask = np.clip(frost_mask, 0, 1)
    bubble_mask = np.zeros((h, w), np.float32)
    for _ in range(15):
        cx, cy = rng.randint(0, w), rng.randint(0, h)
        size = rng.randint(min(h, w) // 60, min(h, w) // 30)
        bubble_mask += crystal_shape(h, w, cx, cy, size, 8, rng.rand() * 2 * np.pi) * 0.5
    bubble_mask = np.clip(bubble_mask, 0, 1)
    height = ice_variation * 0.08 + crack_lines * 0.55 + frost_mask * 0.45 + bubble_mask * 0.2
    base = mix(col(p["ice_shadow"]), col(p["ice"]), ice_variation)
    base = mix(base, col(p["crack"]), crack_lines * 0.8)
    base = mix(base, col(p["frost"]), frost_mask * 0.9)
    base = mix(base, col(p["bubble"]), bubble_mask * 0.7)
    rough = mix(p["rough_ice"], p["rough_crack"], crack_lines)
    rough = mix(rough, p["rough_frost"], frost_mask)
    glow_field = fbm_noise(h, w, 4, 3, SEED + 12)
    emissive = mask_color(crack_lines * smoothstep(0.3, 0.7, glow_field), col(p["glow"]) * p["glow_intensity"])
    iri = frost_mask * 0.5 + crack_lines * 0.2
    return _assemble(h, w, base, rough, np.zeros((h, w), np.float32), height, emissive, iri, np.ones((h, w), np.float32))

def build_singing_constellations(h, w, frame, total_frames):
    p = VARIANTS["SingingConstellations"]
    phase = frame / max(total_frames, 1) * 2 * np.pi
    nebula = warped_fbm(h, w, 24, 5, 0.5, SEED)
    void_base = mix(col(p["void"]), col(p["nebula"]), nebula * 0.4)
    star_mask = np.zeros((h, w), np.float32)
    rng = np.random.RandomState(SEED + 50)
    for _ in range(40):
        cx, cy = rng.randint(0, w), rng.randint(0, h)
        size = rng.randint(2, min(h, w) // 20)
        star_mask += crystal_shape(h, w, cx, cy, size, rng.choice([4, 6, 8]), rng.rand() * 2 * np.pi)
    star_mask = np.clip(star_mask, 0, 1)
    sing_mask = np.zeros((h, w), np.float32)
    rng2 = np.random.RandomState(SEED + 60)
    sing_positions = []
    for i in range(8):
        base_cx = rng2.randint(0, w)
        base_cy = rng2.randint(0, h)
        drift_x = int(np.sin(phase * p["sing_speed"] + i * 0.7) * min(h, w) * 0.04)
        drift_y = int(np.cos(phase * p["sing_speed"] * 0.8 + i * 1.1) * min(h, w) * 0.03)
        cx = (base_cx + drift_x) % w
        cy = (base_cy + drift_y) % h
        size = rng2.randint(min(h, w) // 25, min(h, w) // 12)
        sing_mask += crystal_shape(h, w, cx, cy, size, 6, rng2.rand() * 2 * np.pi + phase * 0.15)
        sing_positions.append((cx, cy, size))
    sing_mask = np.clip(sing_mask, 0, 1)
    # Constellation lines
    constellation_lines = np.zeros((h, w), np.float32)
    for i in range(len(sing_positions)):
        for j in range(i + 1, min(i + 3, len(sing_positions))):
            x1, y1, _ = sing_positions[i]
            x2, y2, _ = sing_positions[j]
            steps = max(abs(x2 - x1), abs(y2 - y1), 1)
            for t in range(steps):
                px = int(x1 + (x2 - x1) * t / steps)
                py = int(y1 + (y2 - y1) * t / steps)
                if 0 <= px < w and 0 <= py < h:
                    constellation_lines[py, px] = 1.0
    # Box blur
    kernel_size = 3
    padded = np.pad(constellation_lines, kernel_size // 2, mode='edge')
    blurred = np.zeros_like(constellation_lines)
    for dy in range(kernel_size):
        for dx in range(kernel_size):
            blurred += padded[dy:dy+h, dx:dx+w]
    blurred /= kernel_size * kernel_size
    constellation_lines = np.clip(blurred * 3, 0, 1)
    height = nebula * 0.1 + star_mask * 0.4 + sing_mask * 0.7 + constellation_lines * 0.25
    base = void_base.copy()
    base = mix(base, col(p["star_halo"]), star_mask * 0.8)
    base = mix(base, col(p["constellation"]), constellation_lines * 0.7)
    base = mix(base, col(p["singing_node"]), sing_mask * 0.95)
    rough = mix(p["rough_void"], p["rough_star"], star_mask)
    rough = mix(rough, p["rough_star"] * 0.5, sing_mask)
    sing_pulse = np.sin(phase * p["sing_speed"]) * 0.5 + 0.5
    twinkle = warped_fbm(h, w, 8, 3, 0.4, SEED + int(phase * p["twinkle_speed"] * 5))
    emissive = mask_color(sing_mask * sing_pulse * smoothstep(0.3, 0.9, twinkle), col(p["singing_node"]) * p["glow_intensity"] * 1.8)
    emissive += mask_color(star_mask * smoothstep(0.5, 0.9, twinkle), col(p["star_halo"]) * p["glow_intensity"] * 0.8)
    emissive = np.clip(emissive, 0, 1)
    iri = sing_mask * 0.7 + nebula * 0.15
    return _assemble(h, w, base, rough, np.zeros((h, w), np.float32), height, emissive, iri, np.ones((h, w), np.float32))

def build_final_dreamweaver(h, w, frame, total_frames):
    p = VARIANTS["FinalDreamweaver"]
    phase = frame / max(total_frames, 1) * 2 * np.pi
    breathe = np.sin(phase * p["breathe_speed"]) * 0.5 + 0.5
    shadow_flow = warped_fbm(h, w, 20, 5, 0.6, SEED + int(phase * 2))
    living_shadow = mix(col(p["void"]), col(p["shadow"]), shadow_flow * 0.7 + breathe * 0.3)
    weave_pattern = cymatic_chladni(h, w, freqs=[(5, 7), (9, 6), (12, 10)],
                                    phases=[phase * p["weave_speed"] + i * 1.2 for i in range(3)],
                                    weights=[1.0, 0.6, 0.4])
    moonlight_threads = smoothstep(0.55, 0.75, weave_pattern)
    weave_pattern2 = cymatic_chladni(h, w, freqs=[(7, 5), (6, 9), (10, 12)],
                                     phases=[phase * p["weave_speed"] * 0.8 + i * 1.5 for i in range(3)],
                                     weights=[1.0, 0.6, 0.4])
    moonlight_threads2 = smoothstep(0.55, 0.75, weave_pattern2)
    combined_weave = np.clip(moonlight_threads + moonlight_threads2 * 0.7, 0, 1)
    dream_mask = np.zeros((h, w), np.float32)
    rng = np.random.RandomState(SEED + 70)
    for i in range(15):
        base_cx = rng.randint(0, w)
        base_cy = rng.randint(0, h)
        drift_x = int(np.sin(phase * p["breathe_speed"] + i * 0.9) * min(h, w) * 0.02)
        drift_y = int(np.cos(phase * p["breathe_speed"] * 0.7 + i * 1.3) * min(h, w) * 0.015)
        cx = (base_cx + drift_x) % w
        cy = (base_cy + drift_y) % h
        size = rng.randint(min(h, w) // 40, min(h, w) // 15)
        dream_mask += crystal_shape(h, w, cx, cy, size, rng.choice([5, 6, 7, 8]), rng.rand() * 2 * np.pi + phase * 0.1)
    dream_mask = np.clip(dream_mask, 0, 1)
    nightmare_mask = np.zeros((h, w), np.float32)
    for _ in range(8):
        cx, cy = rng.randint(0, w), rng.randint(0, h)
        size = rng.randint(min(h, w) // 50, min(h, w) // 25)
        nightmare_mask += crystal_shape(h, w, cx, cy, size, rng.choice([3, 4, 5]), rng.rand() * 2 * np.pi) * 0.5
    nightmare_mask = np.clip(nightmare_mask, 0, 1)
    gold_mask = np.zeros((h, w), np.float32)
    for _ in range(6):
        cx, cy = rng.randint(0, w), rng.randint(0, h)
        size = rng.randint(min(h, w) // 60, min(h, w) // 30)
        gold_mask += crystal_shape(h, w, cx, cy, size, 4, rng.rand() * 2 * np.pi) * 0.4
    gold_mask = np.clip(gold_mask, 0, 1)
    height = shadow_flow * 0.15 + combined_weave * 0.55 + dream_mask * 0.45 + gold_mask * 0.3
    base = living_shadow.copy()
    base = mix(base, col(p["moonlight"]), combined_weave * 0.9)
    base = mix(base, col(p["dream"]), dream_mask * 0.85)
    base = mix(base, col(p["nightmare"]), nightmare_mask * 0.6)
    base = mix(base, col(p["gold_thread"]), gold_mask * 0.8)
    rough = mix(p["rough_shadow"], p["rough_moonlight"], combined_weave)
    rough = mix(rough, p["rough_dream"], dream_mask)
    moon_glow = np.sin(phase * p["weave_speed"] * 1.5) * 0.3 + 0.7
    dream_pulse = warped_fbm(h, w, 6, 3, 0.5, SEED + int(phase * 8))
    emissive = mask_color(combined_weave * moon_glow, col(p["moonlight"]) * p["glow_intensity"] * 1.2)
    emissive += mask_color(dream_mask * smoothstep(0.4, 0.8, dream_pulse), col(p["dream"]) * p["glow_intensity"] * 0.9)
    emissive += mask_color(gold_mask * 0.5, col(p["gold_thread"]) * p["glow_intensity"] * 0.6)
    emissive = np.clip(emissive, 0, 1)
    iri = combined_weave * 0.5 + dream_mask * 0.35 + gold_mask * 0.2
    return _assemble(h, w, base, rough, gold_mask * 0.7, height, emissive, iri, np.ones((h, w), np.float32))


def _build_glitter_pile(h, w, frame, total_frames, variant_name):
    """Generic glitter pile builder — realistic scattered metallic flakes."""
    p = VARIANTS[variant_name]
    phase = frame / max(total_frames, 1) * 2 * np.pi

    # Dark background base
    bg = np.broadcast_to(col(p["bg"]), (h, w, 3)).copy()

    # Create scattered flake positions
    rng = np.random.RandomState(abs(hash(variant_name)) % 10000 + frame)
    n_flakes = p["flake_density"]
    flake_min, flake_max = p["flake_size_range"]

    flake_mask = np.zeros((h, w), np.float32)
    flake_color = np.zeros((h, w, 3), np.float32)

    for i in range(n_flakes):
        # Position with slight drift for animation
        base_cx = rng.randint(0, w)
        base_cy = rng.randint(0, h)
        drift_x = int(np.sin(phase * 0.5 + i * 0.7) * min(h, w) * 0.008)
        drift_y = int(np.cos(phase * 0.4 + i * 1.1) * min(h, w) * 0.006)
        cx = (base_cx + drift_x) % w
        cy = (base_cy + drift_y) % h

        size = rng.randint(flake_min, flake_max)
        sides = rng.choice([4, 5, 6, 8])  # glitter flakes are polygonal
        rot = rng.rand() * 2 * np.pi + phase * 0.1

        cm = crystal_shape(h, w, cx, cy, size, sides, rot)
        flake_mask = np.clip(flake_mask + cm, 0, 1)

        # Pick a random color from the palette
        color_idx = rng.randint(0, len(p["flake_colors"]))
        c = col(p["flake_colors"][color_idx])
        flake_color = np.clip(flake_color + mask_color(cm, c), 0, 1)

    # Height: flat bg + raised flakes
    height = flake_mask * 0.85

    # BaseColor: bg + flake colors
    base = bg * (1 - flake_mask[:, :, None]) + flake_color * flake_mask[:, :, None]

    # Roughness: bg rough, flakes mirror-smooth
    rough = mix(p["rough_bg"], p["rough_flake"], flake_mask)

    # Metallic: flakes are fully metallic
    metallic = flake_mask * p["metallic_flake"]

    # Emissive: subtle sparkle on flakes
    sparkle = warped_fbm(h, w, 8, 3, 0.4, abs(hash(variant_name)) % 10000 + frame)
    emissive = mask_color(flake_mask * smoothstep(0.4, 0.9, sparkle),
                          col(p["flake_colors"][0]) * p["glow_intensity"] * 0.6)

    # Iridescence: strong on flakes
    iri = flake_mask * 0.8

    return _assemble(h, w, base, rough, metallic, height, emissive, iri, np.ones((h, w), np.float32))


def build_glitter_rainbow(h, w, frame, total_frames):
    return _build_glitter_pile(h, w, frame, total_frames, "GlitterRainbow")


def build_glitter_holographic(h, w, frame, total_frames):
    return _build_glitter_pile(h, w, frame, total_frames, "GlitterHolographic")


def build_glitter_gold(h, w, frame, total_frames):
    return _build_glitter_pile(h, w, frame, total_frames, "GlitterGold")


def build_glitter_iridescent(h, w, frame, total_frames):
    return _build_glitter_pile(h, w, frame, total_frames, "GlitterIridescent")


def build_glitter_crystal(h, w, frame, total_frames):
    return _build_glitter_pile(h, w, frame, total_frames, "GlitterCrystal")


def _build_architectural_variant(h, w, frame, total_frames, variant_name):
    """Generic architectural landscape builder — mathematical grandeur."""
    p = VARIANTS[variant_name]
    phase = frame / max(total_frames, 1) * 2 * np.pi
    yy, xx = np.mgrid[0:h, 0:w].astype(np.float32)
    nx = xx / w
    ny = yy / h
    
    # Shared: domain warping for organic feel
    warp = warped_fbm(h, w, 16, 4, 0.3, SEED)
    
    if variant_name == "FractalCathedral":
        # Recursive fractal branching pattern
        pattern = np.zeros((h, w), np.float32)
        rng = np.random.RandomState(SEED + 100)
        for level in range(p["fractal_depth"]):
            scale = p["scale_factor"] ** level
            freq = 2 ** level
            for _ in range(p["branch_count"]):
                cx, cy = rng.rand(), rng.rand()
                branch = np.sin((nx - cx) * freq * 10 + phase * 0.1 * level) * np.cos((ny - cy) * freq * 8)
                branch *= smoothstep(0.3, 0.7, 1 - np.sqrt((nx - cx)**2 + (ny - cy)**2) * freq)
                pattern += branch * scale
        
        # Gold filigree at branch intersections
        gold_mask = smoothstep(0.6, 0.8, np.abs(pattern))
        
        # Height: stone base + raised gold
        height = (1 - np.abs(pattern)) * 0.6 + gold_mask * 0.8 + warp * 0.1
        
        # BaseColor: dark stone + gold filigree
        base = mix(col(p["stone"]), col(p["gold"]), gold_mask)
        base = mix(base, col(p["accent"]), smoothstep(0.7, 0.9, np.abs(pattern)) * 0.3)
        
        # Roughness: stone rough, gold smooth
        rough = mix(p["rough_stone"], p["rough_gold"], gold_mask)
        
        # Emissive: glowing accents
        emissive = mask_color(smoothstep(0.7, 1.0, np.abs(pattern)), col(p["glow"]) * p["glow_intensity"])
        
        iri = gold_mask * 0.6 + warp * 0.1
        metallic = gold_mask * 0.9
        
    elif variant_name == "GoldenSpiralGrove":
        # Logarithmic spiral pattern (phi-based)
        cx, cy = 0.5, 0.5
        dx, dy = nx - cx, ny - cy
        r = np.sqrt(dx**2 + dy**2)
        theta = np.arctan2(dy, dx)
        
        # Logarithmic spiral: r = a * e^(b*theta)
        b = np.log(p["phi"]) / (2 * np.pi)
        spiral = np.sin(p["spiral_turns"] * (theta + np.log(r + 0.001) / b) + phase)
        
        # Multiple spirals radiating from center
        spiral_mask = np.zeros((h, w), np.float32)
        for i in range(p["spiral_turns"]):
            offset = i * 2 * np.pi / p["spiral_turns"]
            sp = np.sin(p["spiral_turns"] * (theta + offset + np.log(r + 0.001) / b))
            spiral_mask += smoothstep(0.3, 0.7, sp * 0.5 + 0.5)
        spiral_mask = np.clip(spiral_mask, 0, 1)
        
        # Height: raised spiral ridges
        height = spiral_mask * 0.7 + warp * 0.2
        
        # BaseColor: dark wood + gold spirals
        base = mix(col(p["base"]), col(p["gold"]), spiral_mask)
        base = mix(base, col(p["accent"]), smoothstep(0.6, 0.9, spiral_mask) * 0.2)
        
        # Roughness: wood rough, gold smooth
        rough = mix(p["rough_base"], p["rough_gold"], spiral_mask)
        
        # Emissive: gold glow
        emissive = mask_color(smoothstep(0.5, 1.0, spiral_mask), col(p["glow"]) * p["glow_intensity"])
        
        iri = spiral_mask * 0.5
        metallic = spiral_mask * 0.95
        
    elif variant_name == "VoronoiSacredGeometry":
        # Sacred geometry: Voronoi with 6-fold symmetry
        rng = np.random.RandomState(SEED + 200)
        points = []
        for i in range(p["symmetry"]):
            angle = i * 2 * np.pi / p["symmetry"]
            for r in [0.2, 0.35, 0.5]:
                points.append([0.5 + r * np.cos(angle), 0.5 + r * np.sin(angle)])
        # Center point
        points.append([0.5, 0.5])
        
        # Compute Voronoi
        dist = np.full((h, w), 1e9, np.float32)
        dist2 = np.full((h, w), 1e9, np.float32)
        cell_idx = np.zeros((h, w), np.int32)
        
        for idx, (px, py) in enumerate(points):
            d = (nx - px)**2 + (ny - py)**2
            mask = d < dist
            dist2[mask] = dist[mask]
            dist[mask] = d[mask]
            cell_idx[mask] = idx
        
        # Edge detection: where dist ≈ dist2
        edge = smoothstep(0.001, 0.005, np.sqrt(dist2) - np.sqrt(dist))
        
        # Cell coloring based on index parity + distance variation
        cell_color = cell_idx % 2
        # Normalize distance for variation
        max_dist = np.max(np.sqrt(dist))
        cell_depth = np.sqrt(dist) / (max_dist + 0.001)
        
        # Height: raised cells, recessed edges
        height = (1 - edge) * 0.6 + warp * 0.15
        
        # BaseColor: two-tone cells + white edges + depth variation
        base = mix(col(p["cell_a"]), col(p["cell_b"]), cell_color)
        base = base * (1 - cell_depth * 0.4)  # darken by distance
        base = mix(base, col(p["edge"]), edge * 0.9)
        
        # Roughness: cells medium, edges smooth
        rough = mix(p["rough_bg"], p["rough_edge"], edge)
        
        # Emissive: edge glow
        emissive = mask_color(edge, col(p["glow"]) * p["glow_intensity"])
        
        iri = edge * 0.8 + cell_color * 0.2
        metallic = edge * 0.5
        
    elif variant_name == "TessellationSanctum":
        # Penrose-like tessellation pattern
        tile_size = max(4, p["tile_size"] // 2)  # smaller tiles for visible pattern
        tx = (xx / w * tile_size).astype(int)
        ty = (yy / h * tile_size).astype(int)
        
        # Diamond/rhombus pattern (simplified Penrose)
        diamond = ((tx + ty) % 2).astype(float)
        
        # Add edge grout
        fx = (xx / w * tile_size) % 1.0
        fy = (yy / h * tile_size) % 1.0
        edge_x = smoothstep(0.15, 0.25, fx) * smoothstep(0.85, 0.75, fx)
        edge_y = smoothstep(0.15, 0.25, fy) * smoothstep(0.85, 0.75, fy)
        grout = np.clip(edge_x + edge_y, 0, 1)
        
        # Height: raised tiles, recessed grout
        height = (1 - grout) * 0.5 + warp * 0.1
        
        # BaseColor: two-tone tiles + dark grout
        base = mix(col(p["tile_a"]), col(p["tile_b"]), diamond)
        base = mix(base, col(p["grout"]), grout * 0.9)
        
        # Roughness: tiles medium, grout rough
        rough = mix(p["rough_tile"], p["rough_bg"], grout)
        
        # Emissive: subtle glow on tile centers
        center_glow = (1 - grout) * smoothstep(0.3, 0.5, diamond + warp)
        emissive = mask_color(center_glow, col(p["glow"]) * p["glow_intensity"] * 0.5)
        
        iri = (1 - grout) * 0.3
        metallic = np.zeros((h, w), np.float32)
        
    elif variant_name == "SpiralMonument":
        # Monumental spiral pillars
        cx, cy = 0.5, 0.5
        r = np.sqrt((nx - cx)**2 + (ny - cy)**2)
        theta = np.arctan2(ny - cy, nx - cx)
        
        # Multiple interlocking spirals
        spiral_sum = np.zeros((h, w), np.float32)
        for i in range(p["spiral_count"]):
            offset = i * 2 * np.pi / p["spiral_count"]
            spiral = np.sin(p["turns"] * (theta + offset) + r * 20 * np.pi + phase * 0.5)
            spiral *= smoothstep(0.1, 0.5, r) * smoothstep(0.9, 0.6, r)
            spiral_sum += spiral
        
        # Monumental step pattern
        steps = np.floor(np.abs(spiral_sum) * 5) / 5
        step_mask = smoothstep(0.1, 0.3, steps)
        
        # Gold trim at spiral crests
        crest = smoothstep(0.5, 1.0, np.abs(spiral_sum))
        
        # Height: stepped monument
        height = step_mask * 0.7 + crest * 0.5 + warp * 0.1
        
        # BaseColor: dark stone + gold crests
        base = mix(col(p["stone"]), col(p["gold"]), crest)
        base = mix(base, col(p["accent"]), smoothstep(0.7, 1.0, np.abs(spiral_sum)) * 0.25)
        
        # Roughness: stone rough, gold smooth
        rough = mix(p["rough_stone"], p["rough_gold"], crest)
        
        # Emissive: golden monument glow
        emissive = mask_color(crest, col(p["glow"]) * p["glow_intensity"])
        
        iri = crest * 0.7
        metallic = crest * 0.9
    
    return _assemble(h, w, base, rough, metallic, height, emissive, iri, np.ones((h, w), np.float32))


def build_fractal_cathedral(h, w, frame, total_frames):
    return _build_architectural_variant(h, w, frame, total_frames, "FractalCathedral")


def build_golden_spiral_grove(h, w, frame, total_frames):
    return _build_architectural_variant(h, w, frame, total_frames, "GoldenSpiralGrove")


def build_voronoi_sacred_geometry(h, w, frame, total_frames):
    return _build_architectural_variant(h, w, frame, total_frames, "VoronoiSacredGeometry")


def build_tessellation_sanctum(h, w, frame, total_frames):
    return _build_architectural_variant(h, w, frame, total_frames, "TessellationSanctum")


def build_spiral_monument(h, w, frame, total_frames):
    return _build_architectural_variant(h, w, frame, total_frames, "SpiralMonument")


# === P4 overnight — 8 new builders (generic cymatic + fbm path) ===
def _build_new_variant(h, w, frame, total_frames, variant_name):
    """Generic builder for P4 variants — cymatic Chladni + warped fBm + palette."""
    p = VARIANTS[variant_name]
    phase = frame / max(total_frames, 1) * 2 * np.pi
    # Chladni field
    cym = cymatic_chladni(h, w, freqs=[(8, 12), (15, 10), (22, 18)], phases=[phase*0.5, phase*0.7+1.1, phase*0.3+2.2], weights=[1.0, 0.6, 0.4])
    warp = warped_fbm(h, w, 12, 4, 0.25, SEED + hash(variant_name) % 1000)
    yy, xx = np.mgrid[0:h, 0:w].astype(np.float32)
    nx, ny = xx / w, yy / h

    if variant_name == "TwinklingGears":
        # Gear lattice
        gear_field = np.zeros((h, w), np.float32)
        for i in range(p["gear_count"]):
            cx = (0.15 + 0.7 * (i % 3) / 2) * w
            cy = (0.2 + 0.6 * (i // 3) / 2) * h
            gear_field = np.maximum(gear_field, gear_shape(h, w, cx, cy, min(h,w)*0.12, 12, 0.18, rotation=phase*0.5+i))
        height = gear_field * 0.7 + cym * 0.2 + warp * 0.1
        base = mix(col(p["brass"]), col(p["steel"]), gear_field)
        base = mix(base, col(p["void"]), (1-gear_field)*0.15)
        rough = mix(p["rough_steel"], p["rough_brass"], gear_field)
        metallic = gear_field * 0.85
        emissive = mask_color(gear_field * smoothstep(0.6, 1.0, cym), col(p["glow"]) * p["glow_intensity"])
        iri = gear_field * 0.4
    elif variant_name == "EnchantedTome":
        script = smoothstep(0.4, 0.7, tileable_value_noise(h, w, 16, SEED+10))
        height = script * 0.5 + cym * 0.15 + warp * 0.1
        base = mix(col(p["parchment"]), col(p["ink"]), script*0.15)
        base = mix(base, col(p["gold_leaf"]), smoothstep(0.7, 0.95, cym) * 0.6)
        rough = mix(p["rough_parchment"], p["rough_ink"], script*0.3)
        metallic = smoothstep(0.7, 0.95, cym) * 0.9
        emissive = mask_color(smoothstep(0.7, 0.95, cym), col(p["glow"]) * p["glow_intensity"] * 0.5)
        iri = smoothstep(0.7, 0.95, cym) * 0.5
    elif variant_name == "SingingSilk":
        weave = (np.sin(nx*40*np.pi) * np.sin(ny*30*np.pi) * 0.5 + 0.5)
        height = weave * 0.3 + cym * 0.2 + warp * 0.15
        base = mix(col(p["silk"]), col(p["silk_shadow"]), weave*0.3)
        base = mix(base, col(p["thread_gold"]), smoothstep(0.6, 0.9, cym) * 0.5)
        rough = mix(p["rough_silk"], p["rough_thread"], weave)
        metallic = smoothstep(0.6, 0.9, cym) * 0.4
        emissive = mask_color(smoothstep(0.6, 0.9, cym), col(p["glow"]) * p["glow_intensity"] * 0.4)
        iri = weave * 0.5 + cym * 0.3
    elif variant_name == "MoltenCore":
        crack = smoothstep(0.3, 0.7, np.abs(cym - 0.5) * 2)
        height = crack * 0.6 + warp * 0.2 + cym * 0.1
        base = mix(col(p["basalt"]), col(p["magma"]), crack)
        base = mix(base, col(p["magma_hi"]), smoothstep(0.7, 0.95, cym) * crack)
        rough = mix(p["rough_basalt"], p["rough_magma"], crack)
        metallic = crack * 0.2
        emissive = mask_color(crack * (0.5 + cym * 0.5), col(p["glow"]) * p["glow_intensity"])
        iri = crack * 0.3
    elif variant_name == "PearlWeave":
        pearls = crystal_shape(h, w, w*0.3, h*0.3, min(h,w)*0.08, 12) + crystal_shape(h, w, w*0.7, h*0.7, min(h,w)*0.06, 12)
        pearls = np.clip(pearls + warp*0.2, 0, 1)
        height = pearls * 0.5 + cym * 0.15 + warp * 0.1
        base = mix(col(p["pearl"]), col(p["pearl_shadow"]), warp*0.3)
        base = mix(base, col(p["nacre"]), pearls * 0.7)
        rough = mix(p["rough_pearl"], p["rough_thread"], pearls)
        metallic = pearls * 0.1
        emissive = mask_color(pearls * smoothstep(0.5, 1.0, cym), col(p["glow"]) * p["glow_intensity"] * 0.5)
        iri = pearls * 0.8 + cym * 0.2
    elif variant_name == "StarlitLoom":
        loom = (np.sin(nx * p["loom_count"] * 2 * np.pi) > 0).astype(float) * 0.3
        stars = smoothstep(0.92, 0.98, tileable_value_noise(h, w, 32, SEED+20))
        height = loom * 0.4 + stars * 0.6 + cym * 0.1 + warp * 0.05
        base = mix(col(p["void"]), col(p["loom_wood"]), loom)
        base = mix(base, col(p["star"]), stars)
        rough = mix(p["rough_void"], p["rough_wood"], loom)
        metallic = stars * 0.3
        emissive = mask_color(stars, col(p["glow"]) * p["glow_intensity"]) + mask_color(loom * 0.3, col(p["nebula"]) * 0.3)
        iri = stars * 0.6
    elif variant_name == "FrostBloom":
        frost = smoothstep(0.5, 0.85, warp)
        bloom = smoothstep(0.6, 0.9, cym) * (1 - frost*0.5)
        height = frost * 0.3 + bloom * 0.5 + warp * 0.1
        base = mix(col(p["frost"]), col(p["ice"]), frost*0.5)
        base = mix(base, col(p["bloom"]), bloom)
        rough = mix(p["rough_frost"], p["rough_bloom"], bloom)
        metallic = bloom * 0.05
        emissive = mask_color(bloom, col(p["glow"]) * p["glow_intensity"] * 0.4)
        iri = bloom * 0.6 + frost * 0.2
    elif variant_name == "CrystalCathedral":
        # Gothic stone + crystal facets — Chladni drives crystal growth on ribs
        crystal_mask = smoothstep(0.55, 0.85, cym) * (0.6 + warp*0.4)
        facet = smoothstep(0.7, 0.92, np.abs(cym - 0.5)*2) * crystal_mask
        arch = smoothstep(0.3, 0.7, 1 - np.abs(nx*2-1))  # nave arch silhouette
        height = crystal_mask * 0.55 + facet * 0.35 + warp * 0.08 + arch * 0.05
        base = mix(col(p["stone"]), col(p["stone_hi"]), warp*0.35)
        base = mix(base, col(p["crystal"]), crystal_mask*0.85)
        base = mix(base, col(p["crystal_facet"]), facet*0.7)
        base = mix(base, col(p["gold_trim"]), smoothstep(0.8, 0.95, cym)*facet*0.4)
        rough = mix(p["rough_stone"], p["rough_crystal"], crystal_mask)
        rough = mix(rough, p["rough_facet"], facet*0.8)
        metallic = facet * 0.15 + crystal_mask * 0.05
        emissive = mask_color(facet * smoothstep(0.5, 1.0, cym), col(p["glow"]) * p["glow_intensity"] * 0.7)
        iri = facet * 0.85 + crystal_mask * 0.4 + cym * 0.15
    else:  # ChoirStone
        veins = smoothstep(0.65, 0.85, np.abs(cym - 0.5) * 2)
        height = veins * 0.6 + warp * 0.15 + cym * 0.1
        base = mix(col(p["stone"]), col(p["stone_hi"]), warp*0.3)
        base = mix(base, col(p["gold_vein"]), veins)
        rough = mix(p["rough_stone"], p["rough_vein"], veins)
        metallic = veins * 0.85
        emissive = mask_color(veins * smoothstep(0.5, 1.0, cym), col(p["resonance"]) * p["glow_intensity"] * 0.5)
        iri = veins * 0.4

    return _assemble(h, w, base, rough, metallic, height, emissive, iri, np.ones((h, w), np.float32))

def build_twinkling_gears(h, w, frame, total_frames): return _build_new_variant(h, w, frame, total_frames, "TwinklingGears")
def build_enchanted_tome(h, w, frame, total_frames): return _build_new_variant(h, w, frame, total_frames, "EnchantedTome")
def build_singing_silk(h, w, frame, total_frames): return _build_new_variant(h, w, frame, total_frames, "SingingSilk")
def build_molten_core(h, w, frame, total_frames): return _build_new_variant(h, w, frame, total_frames, "MoltenCore")
def build_pearl_weave(h, w, frame, total_frames): return _build_new_variant(h, w, frame, total_frames, "PearlWeave")
def build_starlit_loom(h, w, frame, total_frames): return _build_new_variant(h, w, frame, total_frames, "StarlitLoom")
def build_frost_bloom(h, w, frame, total_frames): return _build_new_variant(h, w, frame, total_frames, "FrostBloom")
def build_choir_stone(h, w, frame, total_frames): return _build_new_variant(h, w, frame, total_frames, "ChoirStone")
def build_crystal_cathedral(h, w, frame, total_frames): return _build_new_variant(h, w, frame, total_frames, "CrystalCathedral")


# === Main ===

BUILDERS = {
    "CymaticMarble": build_cymatic_marble,
    "GildedLoom": build_gilded_loom,
    "SilkWaterfall": build_silk_waterfall,
    "CavernWeave": build_cavern_weave,
    "DancingCrystals": build_dancing_crystals,
    "CherryBlossomWood": build_cherry_blossom_wood,
    "GildedCoral": build_gilded_coral,
    "StarlitAbyss": build_starlit_abyss,
    "FrozenFracture": build_frozen_fracture,
    "SingingConstellations": build_singing_constellations,
    "FinalDreamweaver": build_final_dreamweaver,
    "GlitterRainbow": build_glitter_rainbow,
    "GlitterHolographic": build_glitter_holographic,
    "GlitterGold": build_glitter_gold,
    "GlitterIridescent": build_glitter_iridescent,
    "GlitterCrystal": build_glitter_crystal,
    "FractalCathedral": build_fractal_cathedral,
    "GoldenSpiralGrove": build_golden_spiral_grove,
    "VoronoiSacredGeometry": build_voronoi_sacred_geometry,
    "TessellationSanctum": build_tessellation_sanctum,
    "SpiralMonument": build_spiral_monument,
    "TwinklingGears": build_twinkling_gears,
    "EnchantedTome": build_enchanted_tome,
    "SingingSilk": build_singing_silk,
    "MoltenCore": build_molten_core,
    "PearlWeave": build_pearl_weave,
    "StarlitLoom": build_starlit_loom,
    "FrostBloom": build_frost_bloom,
    "ChoirStone": build_choir_stone,
    "CrystalCathedral": build_crystal_cathedral,
}

def main():
    ap = argparse.ArgumentParser(description="Copernicus cymatic parallax surreal PBR map families")
    ap.add_argument("--variant", default="CymaticMarble", choices=list(VARIANTS.keys()) + ["all"])
    ap.add_argument("--size", type=str, default="1024x1024")
    ap.add_argument("--frames", type=int, default=1)
    ap.add_argument("--cook", action="store_true")
    args = ap.parse_args()

    if not args.cook:
        print("[skip] --cook not set. Use --cook to generate maps.")
        return

    variants = list(VARIANTS.keys()) if args.variant == "all" else [args.variant]
    w, h = (int(x) for x in args.size.split("x"))

    out_dir = PROJECT_ROOT / "Saved" / "Audit" / "copernicus_cymatic"
    out_dir.mkdir(parents=True, exist_ok=True)

    manifest = {
        "schema": "melodia.copernatic_cymatic_parallax.v2",
        "seed": SEED,
        "size": f"{w}x{h}",
        "frames": args.frames,
        "variants": {},
        "maps": ["BaseColor", "Normal", "Roughness", "Metallic", "Height",
                 "ORM", "Emissive", "Iridescence", "Opacity"],
        "pipeline": "pure numpy (cymatic trig interference + tileable fBm + domain warping)",
    }

    for v in variants:
        print(f"\n=== {v} ({w}x{h}, {args.frames} frame(s)) ===")
        vdir = out_dir / v
        vdir.mkdir(exist_ok=True)

        for f in range(args.frames):
            maps = BUILDERS[v](h, w, f, args.frames)
            frame_token = f".{f + 1}" if args.frames > 1 else ""
            for mname, arr in maps.items():
                path = vdir / f"T_Cymatic_{v}_{mname}{frame_token}.png"
                if arr.ndim == 2:
                    Image.fromarray(arr).save(str(path))
                elif arr.ndim == 3 and arr.shape[2] == 1:
                    Image.fromarray(arr[:, :, 0]).save(str(path))
                else:
                    Image.fromarray(arr).save(str(path))
            if args.frames > 1:
                print(f"  frame {f + 1}/{args.frames} done")

        manifest["variants"][v] = {
            "outputs": [f"Saved/Audit/copernicus_cymatic/{v}/T_Cymatic_{v}_{m}.png" for m in manifest["maps"]],
        }
        print(f"  -> {vdir}")

    man = PROJECT_ROOT / "Saved" / "Audit" / "copernicus_cymatic_manifest.json"
    man.write_text(json.dumps(manifest, indent=2), encoding="utf-8")
    print(f"\n[manifest] -> {man}")
    print(f"[done] {len(variants)} variant(s), {args.frames} frame(s) each")


if __name__ == "__main__":
    main()
