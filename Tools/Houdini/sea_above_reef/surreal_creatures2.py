"""
Surreal Creature Atelier — leviathan dreams (Sea Above reef lane, wave2).

Builds 3 surreal creature meshes + 3x 1024 PBR texture sets + VAT LUT:
  1) Veil Leviathan  45m translucent whale with stained-glass ribs and lantern heart
  2) Choir Jelly Swarm 12 jellies 3m bells sharing one VAT LUT (1024)
  3) Shore Siren   2.2m melusine figure with living hair kelp

Each creature has emission + transmission in its material contract.
Exports (Saved/Audit/surreal_sweep_wave2/creatures/):
  Textures (1024): T_VeilLeviathan_*, T_ChoirJelly_*, T_ShoreSiren_*, T_ChoirJelly_VAT_LUT
  Meshes (houdini): SM_VeilLeviathan.obj/.bgeo.sc  SM_ChoirJelly_*.obj  SM_ShoreSiren.obj
  Blender: Surreal_Creatures.blend + per-creature FBX + Surreal_Creatures_Beauty.png (1920x1080)
  Manifest: creatures_manifest.json

Run textures+masks via plain Python:
  python Tools/Houdini/sea_above_reef/surreal_creatures2.py
Run meshes via Houdini (optional, meshes also built by Blender companion):
  "C:/Program Files/Side Effects Software/Houdini 22.0.368/bin/hython.exe" Tools/Houdini/sea_above_reef/surreal_creatures2.py
Run full (meshes+blend+fbx+beauty) via Blender:
  "C:/Program Files/Blender Foundation/Blender 5.2/blender.exe" --background --python Tools/Houdini/sea_above_reef/surreal_creatures2_blender.py
Or let this script auto-trigger Blender if found.

Seed 20260829, deterministic, 1024 textures, emission+transmission.
"""
import argparse
import hashlib
import json
import math
import subprocess
import sys
from pathlib import Path

import numpy as np

PROJECT_ROOT = Path(__file__).resolve().parents[3]
OUT_DIR = PROJECT_ROOT / "Saved/Audit/surreal_sweep_wave2/creatures"
SIZE = 1024
SEED = 20260829
SCHEMA = "melodia.surreal_creatures.v1"

try:
    import hou
    HOU_AVAILABLE = True
    HOU_VERSION = hou.applicationVersionString() if hasattr(hou, "applicationVersionString") else "unknown"
except Exception:
    HOU_AVAILABLE = False
    HOU_VERSION = None


def sha256_of(p: Path) -> str:
    h = hashlib.sha256()
    with open(p, "rb") as f:
        for chunk in iter(lambda: f.read(1 << 16), b""):
            h.update(chunk)
    return h.hexdigest()


def smoothstep(e0, e1, x):
    t = np.clip((x - e0) / max(e1 - e0, 1e-6), 0, 1)
    return t * t * (3 - 2 * t)


def periodic_value_noise(size, period, rng):
    size = int(size); period = int(period)
    if size % period != 0:
        raise ValueError(f"period {period} must divide size {size}")
    lat = rng.random((period, period)).astype(np.float32)
    ys, xs = np.mgrid[0:size, 0:size].astype(np.float32)
    fx = xs * (period / size)
    fy = ys * (period / size)
    x0 = np.floor(fx).astype(np.int32) % period
    y0 = np.floor(fy).astype(np.int32) % period
    x1 = (x0 + 1) % period
    y1 = (y0 + 1) % period
    tx = (fx - np.floor(fx)).astype(np.float32)
    ty = (fy - np.floor(fy)).astype(np.float32)
    sx = tx * tx * (3.0 - 2.0 * tx)
    sy = ty * ty * (3.0 - 2.0 * ty)
    v00 = lat[y0, x0]; v01 = lat[y0, x1]; v10 = lat[y1, x0]; v11 = lat[y1, x1]
    top = v00 + (v01 - v00) * sx
    bot = v10 + (v11 - v10) * sx
    return top + (bot - top) * sy


def fbm(size, base_period, octaves, rng, gain=0.5):
    acc = np.zeros((size, size), np.float32)
    amp = 1.0; total = 0.0; period = int(base_period)
    for _ in range(int(octaves)):
        acc += amp * periodic_value_noise(size, period, rng)
        total += amp; amp *= gain; period *= 2
        if period > size:
            break
    return acc / max(total, 1e-6)


def periodic_voronoi_f1(size, period, jitter, rng):
    size = int(size); period = int(period)
    if size % period != 0:
        raise ValueError(f"period {period} must divide size {size}")
    cell = size / period
    jr = rng.random((period, period, 2)).astype(np.float32) * jitter + (1.0 - jitter) * 0.5
    ys, xs = np.mgrid[0:size, 0:size].astype(np.float32)
    fx = xs / cell; fy = ys / cell
    cx = np.floor(fx).astype(np.int32); cy = np.floor(fy).astype(np.int32)
    best = np.full((size, size), np.float32(1e9))
    for oy in (-1, 0, 1):
        for ox in (-1, 0, 1):
            gx = (cx + ox) % period; gy = (cy + oy) % period
            px = (gx + jr[gy, gx, 0]) * cell; py = (gy + jr[gy, gx, 1]) * cell
            dx = px - xs; dy = py - ys
            dx = (dx + size * 0.5) % size - size * 0.5
            dy = (dy + size * 0.5) % size - size * 0.5
            d = np.sqrt(dx * dx + dy * dy)
            best = np.minimum(best, d)
    return best / cell


def normal_from_height(height, strength=2.0):
    dx = (np.roll(height, -1, axis=1) - np.roll(height, 1, axis=1)) * 0.5
    dy = (np.roll(height, -1, axis=0) - np.roll(height, 1, axis=0)) * 0.5
    nx = -dx * strength; ny = -dy * strength
    nz = np.ones_like(height)
    ln = np.sqrt(nx * nx + ny * ny + nz * nz)
    r = nx / ln * 0.5 + 0.5; g = ny / ln * 0.5 + 0.5; b = nz / ln * 0.5 + 0.5
    return np.stack([r, g, b], axis=-1).astype(np.float32)


def save_png_gray(path: Path, arr: np.ndarray):
    from PIL import Image
    path.parent.mkdir(parents=True, exist_ok=True)
    arr = np.clip(arr, 0, 1)
    data = (arr * 255.0).round().astype(np.uint8)
    Image.fromarray(data, mode="L").save(str(path), format="PNG", optimize=False)
    return path

def save_png_rgb(path: Path, arr: np.ndarray):
    from PIL import Image
    path.parent.mkdir(parents=True, exist_ok=True)
    arr = np.clip(arr, 0, 1)
    data = (arr * 255.0).round().astype(np.uint8)
    Image.fromarray(data, mode="RGB").save(str(path), format="PNG", optimize=False)
    return path

def save_png_rgba(path: Path, arr: np.ndarray):
    from PIL import Image
    path.parent.mkdir(parents=True, exist_ok=True)
    arr = np.clip(arr, 0, 1)
    data = (arr * 255.0).round().astype(np.uint8)
    Image.fromarray(data, mode="RGBA").save(str(path), format="PNG", optimize=False)
    return path


# ---- Texture bakers ----

def bake_veil_leviathan(size=SIZE, seed=SEED):
    rng = np.random.default_rng(seed + 711)
    rng2 = np.random.default_rng(seed + 712)
    # height: veined membrane + rib ridge
    fbm_large = fbm(size, 16, 4, rng, gain=0.55)
    fbm_fine = fbm(size, 64, 3, rng2, gain=0.5)
    vor = periodic_voronoi_f1(size, 8, 0.72, rng)
    # stained glass cells: voronoi edges = lead veins (dark), interiors = colored glass
    vein = np.clip(1.0 - smoothstep(0.02, 0.09, vor), 0, 1)  # bright at cell edges? invert
    # actually vor=distance to center, edge where vor ~0.5*cell, we want veins at edges
    # Use inverted: vein where distance is mid (cell boundary) ~ use smoothstep on |vor-0.35|
    vein2 = np.exp(-((vor - 0.38) ** 2) / (2 * 0.045 ** 2))
    vein = np.clip(vein2 * 0.9 + 0.07 * (1.0 - fbm_fine), 0, 1)
    height = np.clip(fbm_large * 0.55 + fbm_fine * 0.18 + vein * 0.22, 0, 1)
    # ribs: horizontal bands (v direction) with stained-glass hue
    ys, xs = np.mgrid[0:size, 0:size]
    # U = along body, V = around belly
    # 16 rib bands
    rib_phase = (ys / size * 16.0) % 1.0
    rib_mask = smoothstep(0.42, 0.5, np.abs(rib_phase - 0.5) * 2)  # 0 at rib center
    rib_mask = 1.0 - smoothstep(0.0, 0.22, np.abs(rib_phase - 0.5) * 2)
    # base color: translucent teal underneath
    base_teal = np.stack([
        np.full((size,size), 0.52, np.float32) * (0.85 + 0.15 * fbm_large),
        np.full((size,size), 0.76, np.float32) * (0.9 + 0.10 * fbm_large),
        np.full((size,size), 0.80, np.float32) * (0.9 + 0.10 * fbm_large),
    ], axis=-1)
    # stained glass palette per cell: hash vor cell id -> hue
    # Approximate hue via value noise at cell centers (use coarse period 8)
    hue_noise = periodic_value_noise(size, 8, rng)
    sat_noise = periodic_value_noise(size, 16, rng2)
    # hue to rgb approx via sin
    hue = hue_noise  # 0..1
    r_glass = 0.5 + 0.5 * np.sin(hue * 6.283 + 0.0)
    g_glass = 0.5 + 0.5 * np.sin(hue * 6.283 + 2.1)
    b_glass = 0.5 + 0.5 * np.sin(hue * 6.283 + 4.2)
    # vibrance modulated
    vibr = 0.65 + 0.35 * sat_noise
    glass_rgb = np.stack([r_glass, g_glass, b_glass], axis=-1) * vibr[..., None] * 0.85 + 0.15
    # mix glass where rib_mask high, veins dark
    glass_mix = rib_mask[..., None] * (0.7 + 0.3 * vein[..., None])
    base = base_teal * (1.0 - glass_mix * 0.78) + glass_rgb * (glass_mix * 0.78)
    # lead veins: dark brown-black
    lead = (vein2 > 0.55).astype(np.float32)
    # thicken veins slightly via smoothstep
    lead_f = smoothstep(0.35, 0.58, vein2)
    base = base * (1.0 - lead_f[..., None] * 0.55) + np.array([0.08,0.06,0.06])[None,None,:] * (lead_f[..., None] * 0.45)
    # subtle pearly spec along body
    base = np.clip(base + 0.06 * fbm_fine[..., None], 0, 1)
    # emission: lantern heart (warm amber, full glow in chest UV center) + rib edge glow
    # chest at UV (0.32, 0.5) approx
    u = xs / size; v = ys / size
    dist_heart = np.sqrt((u - 0.32)**2 * 2.2 + (v - 0.5)**2 * 1.8)
    heart = np.exp(-(dist_heart**2) / (2 * 0.065**2)) * 0.95
    heart += np.exp(-(dist_heart**2) / (2 * 0.14**2)) * 0.25
    # rib glow: along rib_mask edges
    rib_glow = rib_mask * (0.35 + 0.25 * vein)
    # emissive color: heart amber + rib stained-glass bleed
    emiss = np.zeros((size,size,3), np.float32)
    emiss[...,0] = heart * 0.95 + rib_glow * (0.18 + 0.22 * r_glass)
    emiss[...,1] = heart * 0.52 + rib_glow * (0.08 + 0.14 * g_glass)
    emiss[...,2] = heart * 0.10 + rib_glow * (0.02 + 0.18 * b_glass)
    emiss = np.clip(emiss * 1.15, 0, 1)
    # transmission mask: high (translucent) except lead veins low
    transm = np.clip(0.82 - lead_f * 0.55 + fbm_fine * 0.08, 0, 1)
    # roughness: low on glass, high on lead
    rough = np.clip(0.32 + lead_f * 0.45 + (1.0 - glass_mix[...,0]) * 0.12, 0, 1)
    normal = normal_from_height(height, strength=1.6)
    return {"base": base.astype(np.float32), "emission": emiss.astype(np.float32), "normal": normal, "transm": transm.astype(np.float32), "rough": rough.astype(np.float32), "height": height}


def bake_choir_jelly(size=SIZE, seed=SEED):
    rng = np.random.default_rng(seed + 721)
    rng2 = np.random.default_rng(seed + 722)
    # bell gradient: radial from center, plus pulse bands in V (along bell height)
    ys, xs = np.mgrid[0:size, 0:size].astype(np.float32)
    u = xs / size; v = ys / size
    # center at 0.5,0.5 ; radial for bell doming
    dx = u - 0.5; dy = v - 0.5
    rad = np.sqrt(dx*dx + dy*dy) * 2.0
    dome = np.clip(1.0 - smoothstep(0.65, 0.92, rad), 0, 1)
    # translucent base: pale cyan-violet
    # gradient from center outward: center warm pale, rim deeper violet
    t = np.clip(rad, 0, 1)
    base = np.stack([
        0.78 - 0.14*t + 0.04 * (rng.random((size,size))-0.5),
        0.86 - 0.10*t + 0.04 * (rng.random((size,size))-0.5),
        0.94 - 0.08*t,
    ], axis=-1)
    # veil striations: radial streaks
    ang = np.arctan2(dy, dx)
    streak = 0.5 + 0.5 * np.sin(ang * 16 + rad * 8) * dome
    base[...,0] = np.clip(base[...,0] + streak * 0.04, 0, 1)
    base[...,2] = np.clip(base[...,2] + streak * 0.06, 0, 1)
    base = base * dome[..., None] + np.array([0.06,0.08,0.12])[None,None,:] * (1.0 - dome[..., None]) * 0.25
    # emission: concentric pulse bands (choir singing together) + oral arm glow
    # bands moving along v (we bake one phase, VAT will animate)
    bands = 0.5 + 0.5 * np.sin(v * 12 * math.pi)  # horizontal bands
    # alternate bands brighter
    bands = np.power(bands, 0.7) * dome
    # chromatic: bands cyan->magenta
    emiss = np.zeros((size,size,3), np.float32)
    emiss[...,0] = bands * (0.18 + 0.22 * (0.5+0.5*np.sin(v*6*math.pi)))
    emiss[...,1] = bands * (0.55 + 0.15 * (0.5+0.5*np.cos(v*4*math.pi)))
    emiss[...,2] = bands * (0.82 + 0.10 * (0.5+0.5*np.sin(v*8*math.pi+1.1)))
    # radial glow at bell margin (rim light)
    rim = np.exp(-((rad - 0.78)**2) / (2*0.055**2)) * dome * 0.7
    emiss[...,0] += rim * 0.22
    emiss[...,1] += rim * 0.45
    emiss[...,2] += rim * 0.95
    emiss = np.clip(emiss * 1.05, 0, 1)
    # transm: high at thin rim, lower at dense center
    transm = np.clip(0.92 - t * 0.18 + 0.04 * fbm(size, 32, 2, rng), 0, 1)
    # height: subtle radial ribs + fbm
    height = dome * 0.6 + 0.15 * np.sin(ang*16) * dome + 0.12 * fbm(size, 16, 3, rng2)
    height = np.clip(height, 0, 1)
    normal = normal_from_height(height, strength=1.2)
    # VAT LUT: 1024 x 256 (we will save as 1024x1024 for visibility but data is 1024x256)
    # Encode: R=X, G=Y, B=Z displacement scaled 0..1 (0.5 = zero). Frames along V, verts along U.
    vat_w = 1024; vat_h = 256
    frames = 60
    verts_ring = 128  # conceptual
    vat = np.zeros((vat_h, vat_w, 3), np.float32)
    for f in range(frames):
        t_norm = f / (frames - 1)
        # bell pulse: contraction/expansion sine across frames (shared choir - same phase)
        pulse = math.sin(t_norm * 2 * math.pi) * 0.18
        # subharmonic cascade along bell height (higher rings lag)
        for y in range(vat_h):
            v_norm = y / (vat_h - 1)  # along bell height 0=apex 1=rim
            lag = v_norm * 0.35
            local_pulse = math.sin((t_norm - lag) * 2 * math.pi) * 0.18 * (0.5 + 0.5 * v_norm)
            # tentacle sway for oral arms (encoded in lower part of LUT)
            sway_x = math.sin(t_norm*2*math.pi*1.3 + v_norm*5) * 0.06 * v_norm
            sway_z = math.cos(t_norm*2*math.pi*0.9 + v_norm*4) * 0.05 * v_norm
            # map to 0..1 (0.5 zero, offset * scale)
            # X displacement : radial expansion/contraction
            disp_x = 0.5 + local_pulse * 0.22  # R channel
            disp_y = 0.5 + (pulse * 0.12 + v_norm * 0.02)  # G = vertical bob
            disp_z = 0.5 + sway_x * 0.5  # B carries sway_x
            # Fill row segment
            # Spread across U segments: U maps to angular position on bell
            # For simplicity fill entire row with same base (material samples by vertex UV.y)
            vat[y, :, 0] = np.clip(disp_x + (np.arange(vat_w) / vat_w - 0.5) * 0.02, 0, 1)
            vat[y, :, 1] = np.clip(disp_y, 0, 1)
            vat[y, :, 2] = np.clip(disp_z + np.sin(np.arange(vat_w) / vat_w * 6.283*4) * 0.01, 0, 1)
        # Actually above overwrote per-y ; break correctly: we need frame slices
        # Instead reinterpret: vat V axis = frame*vertex? Simpler: treat vat_h as time, vat_w as vertex id -> encode above loop is per frame column?
        # We'll encode frame-wise bands: split vat_h 256 into 60 frames => ~4 rows per frame
        pass
    # Rebuild VAT correctly: h=256 is frames*? We want 64 frames x 256 verts -> Use 64 rows of 4px each?
    # Simpler deterministic VAT: y = time (0..1) , x = growth (0..1) -> XY displacement field (like kelp LUT)
    vat2 = np.zeros((vat_h, vat_w, 3), np.float32)
    ys_v, xs_v = np.mgrid[0:vat_h, 0:vat_w].astype(np.float32)
    time = ys_v / vat_h  # 0..1
    growth = xs_v / vat_w
    # traveling wave down the bell/tentacle
    wave = np.sin((growth * 4.2 - time * 6.283) * 1.0) * 0.18 * (0.4 + 0.6*growth)
    wave2 = np.cos((growth * 2.5 - time * 4.0)) * 0.06 * growth
    # encode: R = radial expansion (wave), G = vertical, B = lateral sway
    vat2[...,0] = np.clip(0.5 + wave * 0.55, 0, 1)
    vat2[...,1] = np.clip(0.5 + wave2 * 0.5, 0, 1)
    vat2[...,2] = np.clip(0.5 + np.sin(growth*6.283*3 + time*6.283) * 0.08 * growth, 0, 1)
    # add frame marker stripes for visual debugging
    for f in range(0, vat_h, 16):
        vat2[f, :, :] = np.clip(vat2[f, :, :] + 0.06, 0, 1)

    return {"base": base.astype(np.float32), "emission": emiss.astype(np.float32), "normal": normal, "transm": transm.astype(np.float32), "height": height, "vat": vat2.astype(np.float32)}


def bake_shore_siren(size=SIZE, seed=SEED):
    rng = np.random.default_rng(seed + 731)
    rng2 = np.random.default_rng(seed + 732)
    ys, xs = np.mgrid[0:size, 0:size].astype(np.float32)
    u = xs / size; v = ys / size
    # skin + tail scale zones: top 0..0.55 skin, 0.55..1.0 tail/scales
    is_tail = (v > 0.55).astype(np.float32)
    # tail scale pattern: overlapping semicircles along V
    scale_phase = (v * 18.0 + u * 2.0) % 1.0
    scale_mask = smoothstep(0.15, 0.45, np.abs(scale_phase - 0.5)*2)
    scale_mask = 1.0 - scale_mask
    # modulate by horizontal bands
    scale_mask = scale_mask * (0.5 + 0.5 * (0.5+0.5*np.sin(u*12*math.pi))) * is_tail
    # skin fbm for pores
    pores = fbm(size, 32, 2, rng)
    base = np.zeros((size,size,3), np.float32)
    # warm skin
    skin = np.stack([
        np.full((size,size), 0.86, np.float32) + pores*0.04,
        np.full((size,size), 0.64, np.float32) + pores*0.03,
        np.full((size,size), 0.58, np.float32) + pores*0.02,
    ], axis=-1)
    # turquoise scales (iridescent)
    scale_hue = rng2.random((size,size)) * 0.18 + 0.48  # cyan-turquoise
    r_s = 0.5 + 0.5*np.sin(scale_hue*6.283)
    g_s = 0.5 + 0.5*np.sin(scale_hue*6.283+2.1)
    b_s = 0.5 + 0.5*np.sin(scale_hue*6.283+4.2)
    scale_rgb = np.stack([0.22 + r_s*0.35, 0.58 + g_s*0.22, 0.72 + b_s*0.15], axis=-1)
    # mix scales where is_tail
    scale_mix = scale_mask[..., None] * is_tail[..., None] * 0.92
    base = skin * (1.0 - scale_mix) + scale_rgb * scale_mix
    # kelp hair zone: top V 0..0.28, random strands
    is_hair = (v < 0.30).astype(np.float32)
    # hair strands: vertical streaks in hair zone
    hair_streak = 0.5 + 0.5*np.sin(u * 40 * math.pi + rng.random((size,size))*0.5)
    hair_streak = np.power(hair_streak, 0.8) * is_hair
    hair_kelp = np.stack([
        np.full((size,size), 0.18, np.float32) + hair_streak*0.08,
        np.full((size,size), 0.42, np.float32) + hair_streak*0.18,
        np.full((size,size), 0.26, np.float32) + hair_streak*0.10,
    ], axis=-1)
    hair_mix = np.clip(hair_streak * 1.2, 0, 1)[..., None]
    base = base * (1.0 - hair_mix * 0.95) + hair_kelp * (hair_mix * 0.95)
    # pearly highlight on scales
    base = np.clip(base + scale_mask[..., None] * 0.07, 0, 1)
    # height: scale bumps + skin pores + hair ridges
    height = pores*0.18 + scale_mask*0.32 + hair_streak*0.12 * is_hair
    normal = normal_from_height(height, strength=1.4)
    # emission: hair kelp tips (living glow), eyes/pearls, tail fin edge
    emiss = np.zeros((size,size,3), np.float32)
    # hair tip glow: bottom of hair zone brighter
    hair_tip = np.exp(-((v - 0.26)**2) / (2*0.04**2)) * is_hair * (0.6 + 0.4*hair_streak)
    emiss[...,0] += hair_tip * 0.10
    emiss[...,1] += hair_tip * 0.52
    emiss[...,2] += hair_tip * 0.28
    # eye/pearl glints: small bright spots
    for (eu, ev) in [(0.40, 0.18), (0.60, 0.18), (0.50, 0.42)]:
        d = np.sqrt((u-eu)**2*2.5 + (v-ev)**2*2.0)
        glint = np.exp(-(d**2)/(2*0.018**2)) * 0.95
        emiss[...,0] += glint * (0.22 if eu!=0.5 else 0.85)
        emiss[...,1] += glint * (0.95 if eu!=0.5 else 0.86)
        emiss[...,2] += glint * (0.95 if eu!=0.5 else 0.62)
    # tail fin rim glow
    rim = np.exp(-((v - 0.92)**2)/(2*0.05**2)) * is_tail * (0.5+0.5*np.sin(u*10*math.pi))
    emiss[...,0] += rim*0.06; emiss[...,1] += rim*0.28; emiss[...,2] += rim*0.55
    emiss = np.clip(emiss*1.2, 0, 1)
    # transmission: skin medium, kelp hair lower, scales slightly lower
    transm = np.clip(0.58 + is_tail*0.12 - scale_mask*0.18 + pores*0.04, 0, 1)
    # hair is more opaque
    transm = np.clip(transm - hair_mix[...,0]*0.22, 0, 1)
    rough = np.clip(0.42 + scale_mask*0.18 + hair_mix[...,0]*0.28 - pores*0.08, 0, 1)
    return {"base": base.astype(np.float32), "emission": emiss.astype(np.float32), "normal": normal, "transm": transm.astype(np.float32), "rough": rough.astype(np.float32), "height": height}


def try_houdini_meshes():
    if not HOU_AVAILABLE:
        print("[houdini] hou not available — meshes will be built by Blender companion")
        return []
    print(f"[houdini] hython {HOU_VERSION} — building surreal creature meshes via Python SOPs")
    try:
        import hou
        from pathlib import Path as P
        # Reuse pattern from build_clutter_meshes: create /obj geo + Python SOP
        manifests = []
        obj = hou.node("/obj")

        def _geo(name):
            for old in [n for n in obj.children() if n.name() == name]:
                old.destroy()
            return obj.createNode("geo", name, run_init_scripts=True)

        def _python_sop(g, name, code):
            n = g.createNode("python", name)
            n.parm("python").set(code)
            return n

        def _export(g, out_node, stem):
            OUT_DIR.mkdir(parents=True, exist_ok=True)
            try:
                out_node.cook(force=True)
            except Exception as e:
                print(f"[houdini] cook {stem}: {e}")
            wrote = {}
            for ext in (".obj", ".bgeo.sc"):
                target = OUT_DIR / (stem + ext)
                f = g.createNode("file", "writer" + ext.replace(".", "_"))
                f.parm("file").set(str(target))
                f.parm("filemode").set("write")
                f.setInput(0, out_node)
                try:
                    f.cook(force=True)
                except Exception as e:
                    print(f"[houdini] write {ext} {stem}: {e}")
                if target.exists() and target.stat().st_size > 0:
                    wrote[ext] = str(target)
                    print(f"[houdini] wrote {target.name} {target.stat().st_size} bytes")
                f.destroy()
            if wrote:
                manifests.append({"mesh": stem, "formats": wrote})

        # --- Veil Leviathan (45m whale) ---
        VEIL_CODE = r"""
import hou, math
node = hou.pwd(); geo = node.geometry()
if geo.findPointAttrib("uv") is None: geo.addAttrib(hou.attribType.Point, "uv", (0.0,0.0))
V = hou.Vector3
LENGTH = 45.0
# spine: slight arch
pts = []
for i in range(48+1):
    s = i/48.0
    x = -LENGTH/2 + s*LENGTH
    y = math.sin(s*math.pi)*1.8 + math.sin(s*math.pi*2)*0.35
    z = 0
    pts.append(V(x,y,z))
SEG=16
rings=[]
for i, pos in enumerate(pts):
    s=i/48.0
    if i==0: tan=pts[1]-pts[0]
    elif i==48: tan=pts[-1]-pts[-2]
    else: tan=pts[i+1]-pts[i-1]
    tan=tan.normalized()
    up=V(0,1,0)
    if abs(tan.dot(up))>0.95: up=V(1,0,0)
    x1=tan.cross(up).normalized(); y1=tan.cross(x1).normalized()
    # radius profile: bulbous head, narrow tail
    t=s
    r = 3.8*math.sin(math.pi*min(1.0,0.18+t*0.82))* (1.0-0.35*max(0.0,t-0.72)) + 1.1
    r *= (0.92+0.08*math.sin(t*12))
    ring=[]
    for k in range(SEG):
        a=k/SEG*2*math.pi
        off=x1*(math.cos(a)*r)+y1*(math.sin(a)*r*0.88)
        p=geo.createPoint(); p.setPosition(pos+off)
        p.setAttribValue(geo.findPointAttrib("uv"), (s, k/SEG))
        ring.append(p)
    rings.append(ring)
for i in range(48):
    for k in range(SEG):
        f=geo.createPolygon()
        for q in (rings[i][k], rings[i][(k+1)%SEG], rings[i+1][(k+1)%SEG], rings[i+1][k]): f.addVertex(q)
# caps
for ci, rng in [(0, rings[0]), (48, rings[48])]:
    cap=geo.createPoint(); cap.setPosition(pts[ci])
    for k in range(SEG):
        f=geo.createPolygon()
        if ci==0: f.addVertex(rng[(k+1)%SEG]); f.addVertex(rng[k]); f.addVertex(cap)
        else: f.addVertex(rng[k]); f.addVertex(rng[(k+1)%SEG]); f.addVertex(cap)
# lantern heart (icosphere-ish) at chest s=0.28
heart_pos = pts[int(48*0.28)] + V(0, -0.9, 0)
# small uv sphere for heart
import math as _m
R=1.2; SEG2=18; RINGS2=12
rows=[]
for j in range(RINGS2+1):
    phi=j/RINGS2*_m.pi
    row=[]
    for i2 in range(SEG2):
        th=i2/SEG2*2*_m.pi
        x=_m.sin(phi)*_m.cos(th); y=_m.cos(phi); z=_m.sin(phi)*_m.sin(th)
        p=geo.createPoint(); p.setPosition(heart_pos+V(x*R*1.1, y*R*0.95, z*R*1.05))
        p.setAttribValue(geo.findPointAttrib("uv"), (i2/SEG2, 1-j/RINGS2))
        row.append(p)
    rows.append(row)
for j in range(RINGS2):
    for i2 in range(SEG2):
        f=geo.createPolygon()
        for q in (rows[j][i2], rows[j][(i2+1)%SEG2], rows[j+1][(i2+1)%SEG2], rows[j+1][i2]): f.addVertex(q)
# ribs: 14 stained-glass rib arcs (tube rings around body)
for rib in range(14):
    s = 0.18 + rib/13*0.62
    idx = int(s*48)
    c = pts[idx]
    tan = (pts[min(idx+1,48)]-pts[max(idx-1,0)]).normalized()
    up=V(0,1,0)
    if abs(tan.dot(up))>0.94: up=V(1,0,0)
    x1=tan.cross(up).normalized(); y1=tan.cross(x1).normalized()
    Rr = 3.2*math.sin(math.pi*(0.3+0.55*rib/13)) +1.6
    # half-arch downward
    arc=[]
    for a_ in range(12):
        t=a_/11.0
        ang = math.pi*t  # 0..pi across belly
        # rib plane: span around Y
        rad = Rr*(0.55+0.45*math.sin(math.pi*t))
        off = x1*(math.cos(ang)*rad*0.2) + y1*(-math.sin(ang)*rad) + V(0, -1.2*math.sin(ang)*0.6, 0)
        arc.append(c+off)
    # extrude arc as thin ribbon (two-sided glass)
    for i2 in range(len(arc)-1):
        rad0=0.09; rad1=0.08
        # build quad strip for glass pane (simplified as quad)
        p0=arc[i2]; p1=arc[i2+1]
        dir_=(p1-p0).normalized()
        side=dir_.cross(tan).normalized()*0.22
        a0=geo.createPoint(); a0.setPosition(p0+side); a0.setAttribValue(geo.findPointAttrib("uv"), (t,0))
        b0=geo.createPoint(); b0.setPosition(p0-side); b0.setAttribValue(geo.findPointAttrib("uv"), (t,1))
        a1=geo.createPoint(); a1.setPosition(p1+side); a1.setAttribValue(geo.findPointAttrib("uv"), (t+0.08,0))
        b1=geo.createPoint(); b1.setPosition(p1-side); b1.setAttribValue(geo.findPointAttrib("uv"), (t+0.08,1))
        f=geo.createPolygon()
        for q in (a0,b0,b1,a1): f.addVertex(q)
try: geo.computeVertexNormals()
except: pass
"""
        g = _geo("SM_VeilLeviathan_HOU")
        py = _python_sop(g, "gen_veil", VEIL_CODE)
        out = g.createNode("null", "OUT"); out.setInput(0, py)
        _export(g, out, "SM_VeilLeviathan")

        # --- Choir Jelly (single bell prototype, 12 instances will be done in Blender, hou does one) ---
        JELLY_CODE = r"""
import hou, math, random
node=hou.pwd(); geo=node.geometry()
if geo.findPointAttrib("uv") is None: geo.addAttrib(hou.attribType.Point, "uv", (0.0,0.0))
V=hou.Vector3
R=1.5; SEG=28; RINGS=18
rows=[]
for j in range(RINGS+1):
    phi=j/RINGS*math.pi*0.62
    row=[]
    for i in range(SEG):
        th=i/SEG*2*math.pi
        scallop=1.0+0.055*math.cos(th*12)*(phi/(math.pi*0.62))**2
        rr=R*math.sin(phi)*scallop
        y=R*0.72*math.cos(phi)
        p=geo.createPoint(); p.setPosition(V(rr*math.cos(th), y, rr*math.sin(th)))
        p.setAttribValue(geo.findPointAttrib("uv"), (i/SEG, 1-j/RINGS))
        row.append(p)
    rows.append(row)
for j in range(RINGS):
    for i in range(SEG):
        f=geo.createPolygon()
        for q in (rows[j][i], rows[j][(i+1)%SEG], rows[j+1][(i+1)%SEG], rows[j+1][i]): f.addVertex(q)
# oral arms: 4 curtains
for arm in range(4):
    a0=arm/4*2*math.pi
    spine=[]
    for k in range(16):
        s=k/15.0
        r=0.92*R + s*0.55
        y=-math.sin(s*math.pi*0.5)*1.1 + max(0,s-0.5)**1.6*0.45
        x=r*math.cos(a0)+math.sin(s*3+arm)*0.12*s
        z=r*math.sin(a0)+math.cos(s*2.2+arm*0.7)*0.10*s
        spine.append(V(x,y,z))
    # ribbon 4 cols
    grid=[]
    for idx,pos in enumerate(spine):
        s=idx/15.0
        if idx==0: tan=spine[1]-spine[0]
        elif idx==15: tan=spine[-1]-spine[-2]
        else: tan=spine[idx+1]-spine[idx-1]
        tan=tan.normalized()
        up=V(0,1,0)
        if abs(tan.dot(up))>0.95: up=V(1,0,0)
        x1=tan.cross(up).normalized()
        w=0.22*(0.5+0.5*math.sin(math.pi*min(1.0,0.15+0.85*s)))*(1-0.35*s)
        row=[]
        for c in range(5):
            u=c/4-0.5
            p=geo.createPoint(); p.setPosition(pos+x1*(w*u))
            p.setAttribValue(geo.findPointAttrib("uv"), (u+0.5, s))
            row.append(p)
        grid.append(row)
    for i2 in range(15):
        for c in range(4):
            f=geo.createPolygon()
            for q in (grid[i2][c], grid[i2][c+1], grid[i2+1][c+1], grid[i2+1][c]): f.addVertex(q)
try: geo.computeVertexNormals()
except: pass
"""
        g2 = _geo("SM_ChoirJelly_HOU")
        py2 = _python_sop(g2, "gen_jelly", JELLY_CODE)
        out2 = g2.createNode("null", "OUT"); out2.setInput(0, py2)
        _export(g2, out2, "SM_ChoirJelly")

        # --- Shore Siren 2.2m ---
        SIREN_CODE = r"""
import hou, math
node=hou.pwd(); geo=node.geometry()
if geo.findPointAttrib("uv") is None: geo.addAttrib(hou.attribType.Point, "uv", (0.0,0.0))
V=hou.Vector3
def tube_along(pts, radii, seg=10):
    n=len(pts)
    rings=[]
    for i,pos in enumerate(pts):
        if i==0: tan=pts[1]-pts[0]
        elif i==n-1: tan=pts[-1]-pts[-2]
        else: tan=pts[i+1]-pts[i-1]
        tan=tan.normalized()
        up=V(0,1,0)
        if abs(tan.dot(up))>0.95: up=V(1,0,0)
        x=tan.cross(up).normalized(); y=tan.cross(x).normalized()
        ring=[]
        for k in range(seg):
            a=k/seg*2*math.pi
            off=x*(math.cos(a)*radii[i])+y*(math.sin(a)*radii[i])
            p=geo.createPoint(); p.setPosition(pos+off)
            p.setAttribValue(geo.findPointAttrib("uv"), (k/seg, i/max(n-1,1)))
            ring.append(p)
        rings.append(ring)
    for i in range(n-1):
        for k in range(seg):
            f=geo.createPolygon()
            for q in (rings[i][k], rings[i][(k+1)%seg], rings[i+1][(k+1)%seg], rings[i+1][k]): f.addVertex(q)
    # caps
    for ci, rng in [(0,rings[0]), (n-1,rings[-1])]:
        cap=geo.createPoint(); cap.setPosition(pts[ci])
        for k in range(seg):
            f=geo.createPolygon()
            if ci==0: f.addVertex(rng[(k+1)%seg]); f.addVertex(rng[k]); f.addVertex(cap)
            else: f.addVertex(rng[k]); f.addVertex(rng[(k+1)%seg]); f.addVertex(cap)
# head sphere
import math as _m
def sphere(center, r, seg=16, rings=10):
    rows=[]
    for j in range(rings+1):
        phi=j/rings*_m.pi
        row=[]
        for i2 in range(seg):
            th=i2/seg*2*_m.pi
            x=_m.sin(phi)*_m.cos(th); y=_m.cos(phi); z=_m.sin(phi)*_m.sin(th)
            p=geo.createPoint(); p.setPosition(center+V(x*r,y*r,z*r))
            row.append(p)
        rows.append(row)
    for j in range(rings):
        for i2 in range(seg):
            f=geo.createPolygon()
            for q in (rows[j][i2], rows[j][(i2+1)%seg], rows[j+1][(i2+1)%seg], rows[j+1][i2]): f.addVertex(q)
# proportions 2.2m total
sphere(V(0,1.95,0),0.165, seg=14, rings=8)
tube_along([V(0,1.78,0), V(0,1.55,0), V(0,1.28,0)], [0.22,0.20,0.17], seg=12)
# tail merge
tube_along([V(0,1.28,0), V(0,0.75,0.05), V(0,0.22,-0.06), V(0,-0.15,0.02)], [0.17,0.14,0.10,0.02], seg=12)
# fin
fin_pts=[V(0,-0.15,0.02), V(-0.18,-0.42,0), V(0,-0.52,0.04), V(0.18,-0.42,0)]
f=geo.createPolygon()
for pt in fin_pts:
    p=geo.createPoint(); p.setPosition(pt); f.addVertex(p)
# arms
tube_along([V(-0.22,1.62,0), V(-0.42,1.35,0.04), V(-0.52,1.02,0.02)], [0.055,0.045,0.035], seg=8)
tube_along([V(0.22,1.62,0), V(0.42,1.35,0.04), V(0.52,1.02,0.02)], [0.055,0.045,0.035], seg=8)
# hair kelp: 9 ribbons from scalp
import random
rng=random.Random(20260829)
for k in range(9):
    a = (k/9*2*math.pi) + rng.uniform(-0.18,0.18)
    base=V(math.cos(a)*0.09, 2.02, math.sin(a)*0.09)
    pts=[]
    for i in range(14):
        s=i/13.0
        pts.append(base + V(math.cos(a)*s*0.22 + math.sin(s*6+a)*0.04*s, -s*0.72 - math.sin(s*math.pi)*0.06, math.sin(a)*s*0.18 + math.cos(s*5+a)*0.04*s))
    radii=[0.032*(1-0.72*s) for s in [i/13.0 for i in range(14)]]
    tube_along(pts, radii, seg=6)
try: geo.computeVertexNormals()
except: pass
"""
        g3 = _geo("SM_ShoreSiren_HOU")
        py3 = _python_sop(g3, "gen_siren", SIREN_CODE)
        out3 = g3.createNode("null", "OUT"); out3.setInput(0, py3)
        _export(g3, out3, "SM_ShoreSiren")
        return manifests
    except Exception as e:
        print(f"[houdini] mesh build failed: {e}")
        import traceback; traceback.print_exc()
        return []


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--seed", type=int, default=SEED)
    ap.add_argument("--size", type=int, default=SIZE)
    ap.add_argument("--blender", type=str, default="", help="blender.exe to auto-run companion")
    ap.add_argument("--skip-houdini", action="store_true")
    args = ap.parse_args()
    seed = args.seed; size = args.size
    OUT_DIR.mkdir(parents=True, exist_ok=True)
    print(f"[surreal-creatures] seed={seed} size={size} out={OUT_DIR}")

    # bake textures
    print("[surreal-creatures] baking Veil Leviathan (stained-glass + lantern)...")
    veil = bake_veil_leviathan(size, seed)
    veil_files = []
    for name, arr, kind in [
        ("T_VeilLeviathan_BaseColor", veil["base"], "rgb"),
        ("T_VeilLeviathan_Emission", veil["emission"], "rgb"),
        ("T_VeilLeviathan_Normal", veil["normal"], "rgb"),
        ("T_VeilLeviathan_ORM", np.dstack([np.zeros((size,size)), veil["rough"], veil["transm"]]), "rgb"),
    ]:
        p = OUT_DIR / f"{name}.png"
        save_png_rgb(p, arr)
        veil_files.append((name, p, kind))
        print(f"  wrote {p.name} sha={sha256_of(p)[:10]}")

    print("[surreal-creatures] baking Choir Jelly Swarm (12 bells + VAT LUT)...")
    jelly = bake_choir_jelly(size, seed)
    jelly_files = []
    for name, arr, kind in [
        ("T_ChoirJelly_BaseColor", jelly["base"], "rgb"),
        ("T_ChoirJelly_Emission", jelly["emission"], "rgb"),
        ("T_ChoirJelly_Normal", jelly["normal"], "rgb"),
        ("T_ChoirJelly_Transmission", np.dstack([jelly["transm"], jelly["transm"], jelly["transm"]]), "rgb"),
    ]:
        p = OUT_DIR / f"{name}.png"
        save_png_rgb(p, arr)
        jelly_files.append((name, p, kind))
        print(f"  wrote {p.name}")
    # VAT LUT (1024x256 -> save as 1024x256 but also provide 1024 version for UE import square requirement? Keep 1024x256)
    vat_path = OUT_DIR / "T_ChoirJelly_VAT_LUT.png"
    # VAT is 256h x 1024w ; save as RGB
    from PIL import Image
    vat_arr = np.clip(jelly["vat"], 0, 1)
    vat_u8 = (vat_arr * 255).round().astype(np.uint8)
    # vat_arr is (256,1024,3) already
    Image.fromarray(vat_u8, mode="RGB").save(str(vat_path), format="PNG", optimize=False)
    print(f"  wrote {vat_path.name} 1024x256  sha={sha256_of(vat_path)[:10]}")
    jelly_files.append(("T_ChoirJelly_VAT_LUT", vat_path, "rgb"))

    print("[surreal-creatures] baking Shore Siren (melusine + living kelp)...")
    siren = bake_shore_siren(size, seed)
    siren_files = []
    for name, arr, kind in [
        ("T_ShoreSiren_BaseColor", siren["base"], "rgb"),
        ("T_ShoreSiren_Emission", siren["emission"], "rgb"),
        ("T_ShoreSiren_Normal", siren["normal"], "rgb"),
        ("T_ShoreSiren_ORM", np.dstack([np.zeros((size,size)), siren["rough"], siren["transm"]]), "rgb"),
    ]:
        p = OUT_DIR / f"{name}.png"
        save_png_rgb(p, arr)
        siren_files.append((name, p, kind))
        print(f"  wrote {p.name}")

    # houdini meshes (optional)
    hou_manifests = []
    if not args.skip_houdini:
        hou_manifests = try_houdini_meshes()

    # build texture manifest fragment
    def file_record(name, path, kind, tex_extra=None):
        rec = {"name": name, "path": str(path.relative_to(PROJECT_ROOT)), "kind": kind, "size": SIZE, "sha256": sha256_of(path), "format": "PNG 1024x1024" if "VAT" not in name else "PNG 1024x256 (VAT LUT, V=time U=growth)"}
        if tex_extra: rec.update(tex_extra)
        return rec

    texture_records = []
    for name, p, k in veil_files:
        extra = {"sRGB": k=="rgb" and "Normal" not in name and "ORM" not in name, "role": "PBR"}
        if "Emission" in name: extra["emission"] = "lantern heart amber + stained-glass bleed, Principled Emission Strength 1.5"
        if "ORM" in name: extra["channels"] = "R=AO(0) G=Roughness B=Transmission"
        if "Normal" in name: extra["sRGB"] = False
        texture_records.append(file_record(name, p, k, extra))
    for name, p, k in jelly_files:
        extra = {"sRGB": k=="rgb" and "Normal" not in name}
        if "Emission" in name: extra["emission"] = "concentric pulse bands + rim light, shared VAT drives WPO"
        if "Transmission" in name: extra["channels"] = "mono transmission 0.92 rim -> 0.74 center"
        if "VAT" in name: extra.update({"sRGB": False, "vat_contract": "V=time(0..1) U=growth(0..1) R=radial pulse G=vertical bob B=lateral sway 0.5=zero", "sharing": "12 jellies share one LUT, instance offset via per-object Custom Property 'vat_offset' (0..1)"})
        if "Normal" in name: extra["sRGB"] = False
        texture_records.append(file_record(name, p, k, extra))
    for name, p, k in siren_files:
        extra = {"sRGB": k=="rgb" and "Normal" not in name and "ORM" not in name}
        if "Emission" in name: extra["emission"] = "kelp hair tips + eye pearls + tail fin rim"
        if "ORM" in name: extra["channels"] = "R=0 G=Roughness B=Transmission"
        if "Normal" in name: extra["sRGB"] = False
        texture_records.append(file_record(name, p, k, extra))

    # write fragment for blender to complete
    frag = {
        "schema": SCHEMA,
        "seed": seed,
        "size": SIZE,
        "houdini": {"available": HOU_AVAILABLE, "version": HOU_VERSION, "meshes": hou_manifests},
        "textures": texture_records,
        "creatures": [
            {"id": "veil_leviathan", "display": "Veil Leviathan", "scale": "45m", "length": 45, "role": "translucent whale, stained-glass ribs (16) + lantern heart (1.2m sphere at chest)", "material": "translucent teal BaseColor + stained-glass palette, Normal from fBm+voronoi height, Emission lantern amber (1.5) + rib bleed, Transmission 0.82 (lead veins 0.27), Roughness 0.32 glass / 0.77 lead"},
            {"id": "choir_jelly", "display": "Choir Jelly Swarm", "scale": "3m bells x12", "count": 12, "role": "12 jelly bells 3m sharing one VAT LUT, concentric pulse bands + rim light, oral-arm sway via LUT", "material": "pale cyan-violet BaseColor, Emission pulse bands + 0.95 rim, Transmission 0.92->0.74, VAT LUT 1024x256 encodes travelling wave (V=time U=growth)", "vat": "T_ChoirJelly_VAT_LUT.png V=time U=growth R=radial G=vertical B=sway"},
            {"id": "shore_siren", "display": "Shore Siren", "scale": "2.2m", "height": 2.2, "role": "melusine figure: warm skin + turquoise scales on tail + 9 living kelp hair ribbons (growth UV.y)", "material": "skin+scale BaseColor, kelp hair green, Normal from scale bumps, Emission hair tips + eye pearls + tail rim, Transmission 0.58 skin / 0.70 tail, kelp 0.36"},
        ],
        "material_contract": "Principled BSDF: BaseColor + Normal + Emission (Color+Strength) + Transmission Weight (from ORM/Transmission B channel) — each creature has emission + transmission"
    }
    frag_path = OUT_DIR / "_textures_manifest.json"
    with open(frag_path, "w", encoding="utf-8") as f:
        json.dump(frag, f, indent=2)
    print(f"[surreal-creatures] textures manifest fragment -> {frag_path}")

    # auto-trigger Blender companion
    blender_exe = args.blender
    if not blender_exe:
        for cand in [r"C:/Program Files/Blender Foundation/Blender 5.2/blender.exe", r"C:/Program Files/Blender Foundation/Blender 4.5/blender.exe"]:
            if Path(cand).exists():
                blender_exe = cand; break
    blender_script = Path(__file__).parent / "surreal_creatures2_blender.py"
    if blender_exe and blender_script.exists():
        print(f"[surreal-creatures] triggering Blender: {blender_exe} --background --python {blender_script}")
        try:
            result = subprocess.run([blender_exe, "--background", "--python", str(blender_script)], capture_output=True, text=True, timeout=600)
            print(result.stdout[-6000:] if len(result.stdout) > 6000 else result.stdout)
            if result.stderr:
                print(result.stderr[-4000:] if len(result.stderr) > 4000 else result.stderr)
            print(f"[surreal-creatures] Blender exit {result.returncode}")
        except Exception as e:
            print(f"[surreal-creatures] Blender auto-run failed: {e}")
    else:
        if not blender_script.exists():
            print("[surreal-creatures] Blender companion not found — create surreal_creatures2_blender.py next")
        else:
            print(f"[surreal-creatures] To build meshes: \"{blender_exe}\" --background --python \"{blender_script}\"")

if __name__ == "__main__":
    main()
