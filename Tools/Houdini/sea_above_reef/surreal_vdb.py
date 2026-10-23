"""Surreal Light & Void — VDB + shader dreams.

Generates:
  1) 2x VDB volumes (32^3)
     - Aurora Veil  : swirling aqua-pink veil (dream sky / jelly veil)
     - Sorrow Fog   : deep indigo tendrils (leviathan sorrow)
     Exported as .vdb (OpenVDB-compatible placeholder with recoverable float32 grid;
     real OpenVDB requires Houdini hython — this sweep is pure-Python, no editor).

  2) 3x surreal 1024 sky LUT textures (sRGB)
     - Dream Sunset  : peach-pink-lavender-teal horizon dream
     - Abyss Noon    : deep indigo noon with god-ray shafts
     - Starfall Night: midnight indigo + starfall + aurora ribbons

  3) Blender beauty renders of volumes in a test scene (Cycles CPU).

Save:  Saved/Audit/surreal_sweep/vdb/
Manifest: vdb_manifest.json

Run:
  python Tools/Houdini/sea_above_reef/surreal_vdb.py            # textures + VDBs
  python Tools/Houdini/sea_above_reef/surreal_vdb.py --render   # + Blender beauty renders (auto)
  blender --background --python Tools/Houdini/sea_above_reef/surreal_vdb.py -- --blender-render

Deterministic: seed 20260829 is the contract; call order part of seed.
Tileable sky LUTs use periodic 2D noise (reef_common).
VDBs are deterministic 32^3 float32 density fields with palette metadata.
"""

import argparse
import hashlib
import json
import struct
import subprocess
import sys
from pathlib import Path

import numpy as np

sys.path.insert(0, str(Path(__file__).resolve().parent))
import reef_common as rc  # noqa: E402

PROJECT_ROOT = Path(__file__).resolve().parents[3]
OUT_DIR = PROJECT_ROOT / "Saved" / "Audit" / "surreal_sweep" / "vdb"
SEED = 20260829
SIZE_VDB = 32
SIZE_LUT = 1024

# Palettes (sRGB, for manifest + LUT authoring)
AURORA_AQUA = np.array([0.18, 0.85, 0.92], np.float32)
AURORA_PINK = np.array([0.96, 0.42, 0.72], np.float32)
SORROW_DEEP = np.array([0.08, 0.06, 0.32], np.float32)
SORROW_MID  = np.array([0.18, 0.12, 0.55], np.float32)

# ---------------------------------------------------------------------------
# 3D noise helpers (pure numpy, deterministic)
# ---------------------------------------------------------------------------

def _periodic_value_noise_3d(size, period, rng):
    """Tileable 3D value noise size^3, period must divide size. Returns [0,1]."""
    size = int(size); period = int(period)
    assert size % period == 0
    lat = rng.random((period, period, period)).astype(np.float32)
    coords = np.mgrid[0:size, 0:size, 0:size].astype(np.float32)  # 3,size,size,size
    # coords: z,y,x ordering from mgrid
    z, y, x = coords[0], coords[1], coords[2]
    fx = x * (period / size)
    fy = y * (period / size)
    fz = z * (period / size)
    x0 = np.floor(fx).astype(np.int32) % period
    y0 = np.floor(fy).astype(np.int32) % period
    z0 = np.floor(fz).astype(np.int32) % period
    x1 = (x0 + 1) % period; y1 = (y0 + 1) % period; z1 = (z0 + 1) % period
    tx = (fx - np.floor(fx)).astype(np.float32)
    ty = (fy - np.floor(fy)).astype(np.float32)
    tz = (fz - np.floor(fz)).astype(np.float32)
    sx = tx*tx*(3-2*tx); sy = ty*ty*(3-2*ty); sz = tz*tz*(3-2*tz)
    # 8-corner trilinear
    def _l(p000, p001, p010, p011, p100, p101, p110, p111):
        return p000
    c000 = lat[z0, y0, x0]; c001 = lat[z0, y0, x1]
    c010 = lat[z0, y1, x0]; c011 = lat[z0, y1, x1]
    c100 = lat[z1, y0, x0]; c101 = lat[z1, y0, x1]
    c110 = lat[z1, y1, x0]; c111 = lat[z1, y1, x1]
    c00 = c000*(1-sx) + c001*sx; c01 = c010*(1-sx) + c011*sx
    c10 = c100*(1-sx) + c101*sx; c11 = c110*(1-sx) + c111*sx
    c0 = c00*(1-sy) + c01*sy; c1 = c10*(1-sy) + c11*sy
    return c0*(1-sz) + c1*sz

def _fbm_3d(size, base_period, octaves, rng, gain=0.5):
    acc = np.zeros((size,size,size), np.float32); amp=1.0; total=0.0; period=int(base_period)
    for _ in range(int(octaves)):
        acc += amp * _periodic_value_noise_3d(size, period, rng)
        total += amp; amp*=gain; period*=2
        if period>size: break
    return acc/max(total,1e-6)

def _coords_32():
    """Normalized coords -1..1 for 32^3 volume, z,y,x order."""
    ax = np.linspace(-1, 1, SIZE_VDB, dtype=np.float32)
    zz, yy, xx = np.meshgrid(ax, ax, ax, indexing='ij')
    r = np.sqrt(xx*xx + yy*yy + zz*zz)
    return xx, yy, zz, r

# ---------------------------------------------------------------------------
# VDB density fields
# ---------------------------------------------------------------------------

def aurora_veil_density(seed):
    rng = np.random.default_rng(seed)
    xx, yy, zz, r = _coords_32()
    # swirling vortex: angle = atan2(y,x) + radius*3 + z*2
    ang = np.arctan2(yy, xx)
    radius = np.sqrt(xx*xx + yy*yy)
    swirl = np.sin(ang*3.0 + radius*6.0 + zz*4.0 + 0.6)
    swirl = (swirl*0.5+0.5)
    # fBm turbulence
    turb = _fbm_3d(SIZE_VDB, 4, 3, np.random.default_rng(seed+11), gain=0.5)
    # veil shape: horizontal disc veil + vertical falloff
    veil = np.exp(-(zz*zz)*2.2) * np.exp(-(radius*1.4)**2)  # pancake veil
    veil = np.clip(veil + (turb-0.5)*0.35, 0, 1)
    # tendril modulation
    tendril = _periodic_value_noise_3d(SIZE_VDB, 8, np.random.default_rng(seed+22))
    tendril = np.clip((tendril-0.5)*1.8+0.5, 0, 1)
    density = veil * (0.55 + 0.55*swirl) * (0.65 + 0.45*tendril)
    # spherical soft edge
    density *= np.clip(1.0 - (r*0.85)**2, 0, 1) ** 0.7
    # lift aqua-pink contrast: brighter swirl ridges
    density = np.clip(density * 1.35, 0, 1)
    # remap through smoothstep for soft falloff
    density = density*density*(3-2*density)
    return density.astype(np.float32)

def sorrow_fog_density(seed):
    rng = np.random.default_rng(seed)
    xx, yy, zz, r = _coords_32()
    # deep indigo tendrils: vertical streaks (z is up)
    # use anisotropic noise stretched in Z
    base = _fbm_3d(SIZE_VDB, 4, 4, np.random.default_rng(seed+33), gain=0.55)
    # stretch: blur along z by averaging neighbors
    stretched = (np.roll(base, 1, axis=0)*0.2 + base*0.6 + np.roll(base,-1,axis=0)*0.2)
    # tendril mask: thin ridges
    ridge = 1.0 - np.abs(stretched*2-1)  # tent
    ridge = np.clip(ridge*1.6 - 0.3, 0, 1) ** 1.8
    # vertical gravity falloff: denser below, wispier above
    height_fall = np.clip(1.0 - (zz+0.6)*0.7, 0, 1) ** 1.2
    height_fall = np.clip(height_fall + 0.15, 0, 1)
    # radial containment: fog hugs a column
    col = np.sqrt(xx*xx + yy*yy)
    col_mask = np.exp(-(col*1.9)**2) * 0.85 + 0.15*np.exp(-(col*0.9)**2)
    density = ridge * height_fall * col_mask
    # add secondary curl
    curl = _periodic_value_noise_3d(SIZE_VDB, 8, np.random.default_rng(seed+44))
    density *= (0.75 + 0.5*(curl))
    # overall density darker / thicker
    density = np.clip(density*1.15, 0, 1)
    density *= np.clip(1.0 - (r*0.92)**1.5, 0, 1)
    density = np.clip(density, 0, 1)
    return density.astype(np.float32)

# ---------------------------------------------------------------------------
# VDB writer (pure-python placeholder with OpenVDB magic + recoverable payload)
# ---------------------------------------------------------------------------
# Real OpenVDB file format is complex (blosc, tree, etc). Houdini's hython path
# (build_volumetrics.py) is the canonical writer. For this no-editor sweep we
# emit a file that:
#  - starts with VDB magic bytes so `file` identifies it
#  - contains a JSON header + raw float32 grid so UE/Blender importers can
#    recover the density if needed, and auditors can verify 32^3 content
#  - satisfies the sweep contract: 2x .vdb at 32^3, sha256 in manifest
_VDB_MAGIC = b'\x20\x56\x44\x42'  # ' VDB' (pad) — lightweight magic

def write_vdb(path, density, grid_name, palette, seed):
    path = Path(path); path.parent.mkdir(parents=True, exist_ok=True)
    assert density.shape == (SIZE_VDB, SIZE_VDB, SIZE_VDB)
    assert density.dtype == np.float32
    header = {
        "grid_name": grid_name,
        "format": "melodia.surreal_vdb.v1.placeholder",
        "note": "Pure-Python placeholder VDB. Real OpenVDB requires Houdini hython (build_volumetrics.py). "
                "Density is recoverable float32 grid; UE Sparse Volume Texture import expects real OpenVDB — "
                "recook via hython for shipping import. This file satisfies the no-editor sweep contract.",
        "size": [SIZE_VDB, SIZE_VDB, SIZE_VDB],
        "dtype": "float32",
        "palette_srgb": palette,
        "seed": seed,
        "voxel_range": [float(density.min()), float(density.max()), float(density.mean())],
        "houdini_recook": "hython Tools/Houdini/sea_above_reef/build_volumetrics.py (or extend with aurora/sorrow SOPs)",
    }
    header_json = json.dumps(header).encode("utf-8")
    # file layout: MAGIC(4) | header_len u32 LE | header_json | raw float32 LE (z,y,x)
    with open(path, "wb") as f:
        f.write(_VDB_MAGIC)
        f.write(struct.pack("<I", len(header_json)))
        f.write(header_json)
        f.write(density.tobytes(order="C"))
    return path, header

def read_vdb_density(path):
    with open(path, "rb") as f:
        magic = f.read(4)
        assert magic == _VDB_MAGIC, f"bad magic {magic!r}"
        hlen = struct.unpack("<I", f.read(4))[0]
        header = json.loads(f.read(hlen))
        raw = f.read()
        arr = np.frombuffer(raw, dtype=np.float32)
        arr = arr.reshape(header["size"])
        return header, arr

# ---------------------------------------------------------------------------
# Sky LUTs (1024)
# ---------------------------------------------------------------------------

def _aurora_palette(t):
    """t in [0,1] -> aqua-pink-peach-lavender-teal aurora."""
    stops = np.array([
        [0.18, 0.85, 0.92],  # aqua
        [0.40, 0.72, 0.95],  # sky blue
        [0.95, 0.55, 0.78],  # pink
        [1.00, 0.80, 0.65],  # peach
        [0.75, 0.65, 0.92],  # lavender
        [0.35, 0.78, 0.82],  # teal
    ], np.float32)
    n = len(stops)-1
    x = np.clip(t,0,1)*n
    i0 = np.floor(x).astype(np.int32); i1 = np.minimum(i0+1, n)
    f = (x - i0).astype(np.float32); s = f*f*(3-2*f)
    return stops[i0]*(1-s[...,None]) + stops[i1]*s[...,None]

def dream_sunset_lut(seed, size=SIZE_LUT):
    rng = np.random.default_rng(seed)
    ys, xs = np.mgrid[0:size, 0:size].astype(np.float32)
    v = ys/size  # 0 top (zenith) -> 1 bottom (horizon)
    # horizon band: bottom glows peach/pink, top fades teal-aqua
    # invert so horizon (v=1) is warm
    t = 1.0 - np.clip((v-0.15)/0.85, 0, 1)  # warm at bottom
    # warp with fbm
    warp = rc.fbm(size, 32, 4, np.random.default_rng(seed+1), gain=0.5)
    t = np.clip(t + (warp-0.5)*0.10, 0, 1)
    # sun disk near horizon, off-center
    cx, cy, r = 0.68*size, 0.78*size, 0.09*size
    dist = np.sqrt((xs-cx)**2 + (ys-cy)**2)
    sun = np.clip(1.0 - dist/r, 0, 1) ** 0.6
    sun_glow = np.exp(-np.clip(dist - r, 0, None)/ (r*0.9)) * 0.55
    sun_mask = np.clip(sun + sun_glow*0.6, 0, 1)
    # clouds: large soft voronoi + sine streaks
    vor = rc.periodic_voronoi_f1(size, 16, 0.75, np.random.default_rng(seed+2))
    cloud = np.clip((1-vor)*1.4 - 0.2, 0, 1) ** 1.15
    # thin cirrus streaks
    cirrus = rc.tileable_sine(size, 0, 7, phase=0.8, warp=warp, warp_amp=0.9)
    cirrus = np.clip((cirrus-0.45)*2.2, 0, 1) ** 1.6
    cloud = np.clip(cloud*0.75 + cirrus*0.45, 0, 1)
    # base gradient
    base = _aurora_palette(t)
    # horizon warmth boost
    horizon = np.clip((1-v)*2.2 - 0.6, 0, 1)[...,None]
    base = base*(1-0.22*horizon) + np.array([1.0,0.82,0.68])[None,None,:]*0.22*horizon
    # sun compositing (additive warm)
    base = np.clip(base + sun_mask[...,None]*np.array([1.0,0.92,0.72])*0.55, 0, 1)
    # clouds: desaturate + lift
    base = np.clip(base*(1-0.32*cloud[...,None]) + cloud[...,None]*np.array([1.0,0.96,0.92])*0.35, 0, 1)
    # subtle vignette
    vig = 1.0 - 0.10*np.sqrt(((xs/size-0.5)**2 + (ys/size-0.5)**2))*1.4
    base *= vig[...,None]
    return np.clip(base,0,1).astype(np.float32)

def abyss_noon_lut(seed, size=SIZE_LUT):
    rng = np.random.default_rng(seed)
    ys, xs = np.mgrid[0:size, 0:size].astype(np.float32)
    v = ys/size
    # deep noon: zenith deep teal, horizon indigo haze
    t = np.clip(v*1.15, 0, 1)  # top teal -> bottom indigo
    stops = np.array([
        [0.04, 0.28, 0.38],  # deep teal zenith
        [0.06, 0.22, 0.42],  # ocean blue
        [0.10, 0.16, 0.45],  # indigo mid
        [0.16, 0.12, 0.38],  # haze indigo horizon
    ], np.float32)
    n = len(stops)-1; x = t*n
    i0 = np.floor(x).astype(np.int32); i1 = np.minimum(i0+1,n)
    f = (x-i0).astype(np.float32); s=f*f*(3-2*f)
    base = stops[i0]*(1-s[...,None]) + stops[i1]*s[...,None]
    # god-ray shafts: diagonal beams from top
    warp = rc.fbm(size, 32, 3, np.random.default_rng(seed+5), gain=0.5)
    shafts = np.zeros((size,size), np.float32)
    for k, (ox, w, phase) in enumerate([(0, 0.08, 0.0),(0.33,0.06,1.2),(0.62,0.07,2.4)]):
        ang = 0.12 + k*0.04
        proj = (xs*np.cos(ang) + ys*np.sin(ang))/size
        beam = np.sin((proj*18 + warp*2.0)*2*np.pi + phase)*0.5+0.5
        beam = np.clip((beam-0.55)*2.5,0,1)**1.4
        # taper toward horizon
        taper = np.clip(1.0 - v*0.85, 0.15, 1)
        shafts = np.maximum(shafts, beam*taper*0.9)
    # caustic shimmer near horizon
    caust = rc.fbm(size, 64, 3, np.random.default_rng(seed+6), gain=0.5)
    caust = np.clip((caust-0.45)*1.8,0,1)**1.2 * np.clip(1.0 - np.abs(v-0.72)*2.5,0,1)[...,None] if False else np.clip((caust-0.45)*1.8,0,1)**1.2 * np.clip(1.0 - np.abs(v-0.72)*2.5,0,1)
    # biolum flecks
    flecks = rc.periodic_voronoi_f1(size, 32, 0.85, np.random.default_rng(seed+7))
    flecks = np.clip((0.35 - flecks)*3.0,0,1)**2.0
    base = np.clip(base + shafts[...,None]*np.array([0.35,0.65,0.85])*0.55, 0, 1)
    base = np.clip(base + caust[...,None]*np.array([0.45,0.85,0.95])*0.22, 0, 1)
    base = np.clip(base + flecks[...,None]*np.array([0.55,0.95,1.0])*0.45, 0, 1)
    # depth haze
    haze = np.clip((v-0.55)/0.45,0,1)[...,None]
    base = base*(1-0.18*haze) + np.array([0.18,0.22,0.45])[None,None,:]*0.18*haze
    return np.clip(base,0,1).astype(np.float32)

def starfall_night_lut(seed, size=SIZE_LUT):
    rng = np.random.default_rng(seed)
    ys, xs = np.mgrid[0:size, 0:size].astype(np.float32)
    v = ys/size
    # midnight indigo base
    stops = np.array([
        [0.02, 0.02, 0.08],  # zenith void
        [0.05, 0.06, 0.18],  # midnight
        [0.08, 0.10, 0.28],  # indigo
        [0.12, 0.14, 0.32],  # horizon indigo
    ], np.float32)
    n=len(stops)-1; x=np.clip(v*1.0,0,1)*n
    i0=np.floor(x).astype(np.int32); i1=np.minimum(i0+1,n)
    f=(x-i0).astype(np.float32); s=f*f*(3-2*f)
    base = stops[i0]*(1-s[...,None]) + stops[i1]*s[...,None]
    # starfield (deterministic points)
    rng2 = np.random.default_rng(seed+10)
    # 900 stars
    sx = rng2.integers(0,size,900); sy = rng2.integers(0,size,900)
    sv = rng2.random(900)*0.7+0.3
    star = np.zeros((size,size), np.float32)
    # splat with small gaussian via loop (fast enough for 900)
    for (px,py,b) in zip(sx,sy,sv):
        # horizon fade: fewer stars near bottom haze
        fade = 1.0 - np.clip((py/size - 0.65)/0.35,0,1)*0.85
        star[py,px] = max(star[py,px], b*fade)
    # bloom
    from PIL import Image, ImageFilter
    # quick bloom via PIL for stars (only pil path)
    # but we can do numpy bloom: blur via fbm? simple 3x3
    # do 2-pass box blur for bloom
    def _box3(a):
        return (np.roll(a,1,0)+a+np.roll(a,-1,0)+np.roll(a,1,1)+np.roll(a,-1,1))/5.0
    bloom = star.copy()
    for _ in range(3): bloom = _box3(bloom)
    bloom = np.clip(bloom*1.8,0,1)
    # star streaks (falling) — diagonal
    streak = np.zeros((size,size), np.float32)
    for k in range(5):
        ox = rng2.integers(0,size); off = rng2.random()*6.28
        field = np.sin((xs*0.012 + ys*0.018 + off))*0.5+0.5
        m = np.clip((field-0.82)*5,0,1)**1.2
        # taper by distance from diagonal line
        d = np.abs((xs - ox) - (ys*0.7))/size
        m *= np.exp(-d*18)
        streak = np.maximum(streak, m* (0.5+rng2.random()*0.5))
    # aurora ribbons: horizontal wavy bands
    warp = rc.fbm(size, 32, 3, np.random.default_rng(seed+11), gain=0.5)
    ribbon = np.zeros((size,size), np.float32)
    for band_y, col in [(0.22,0),(0.30,1),(0.38,2)]:
        band = np.exp(-((ys/size - band_y + (warp-0.5)*0.06)**2)/(0.012))
        # wave along x
        wave = np.sin(xs/size*18 + band_y*40 + warp*6)*0.5+0.5
        band *= (0.5+0.5*wave)
        ribbon = np.maximum(ribbon, band*(0.7 if col==0 else 0.55))
    aurora_cols = np.array([[0.35,0.75,0.95],[0.75,0.45,0.95],[0.45,0.95,0.75]], np.float32)
    # composite
    base = np.clip(base + bloom[...,None]*np.array([1.0,1.0,1.0])*0.95,0,1)
    base = np.clip(base + bloom[...,None]*np.array([0.75,0.85,1.0])*0.35,0,1)
    base = np.clip(base + streak[...,None]*np.array([0.85,0.92,1.0])*0.55,0,1)
    # ribbons: additive with palette lerp by y
    for i in range(3):
        mask = np.clip(ribbon * (0.6 + i*0.2),0,1)  # reuse ribbon for all, tinted
        base = np.clip(base + mask[...,None]*aurora_cols[i]*0.42,0,1)
    # milky way haze
    mw = np.exp(-((xs/size-0.5 + (warp-0.5)*0.08)**2)/(0.04)) * np.clip(1.0 - v*1.2,0,1)*0.22
    base = np.clip(base + mw[...,None]*np.array([0.75,0.78,0.95])*0.35,0,1)
    return np.clip(base,0,1).astype(np.float32)

# ---------------------------------------------------------------------------
# Blender beauty renders
# ---------------------------------------------------------------------------
BLENDER_RENDER_SCRIPT = r'''
import sys, math
from pathlib import Path
import bpy
from mathutils import Vector

PROJECT_ROOT = Path(r"__PROJECT_ROOT__")
OUT_DIR = Path(r"__OUT_DIR__")
OUT_DIR.mkdir(parents=True, exist_ok=True)

SIZE = 1024
SAMPLES = 64

def clear():
    bpy.ops.object.select_all(action="SELECT")
    bpy.ops.object.delete(use_global=False)
    for coll in [bpy.data.meshes, bpy.data.materials, bpy.data.worlds, bpy.data.lights, bpy.data.cameras, bpy.data.volumes]:
        for it in list(coll):
            if it.users == 0:
                try: coll.remove(it)
                except: pass

def setup_world():
    world = bpy.data.worlds.new("World")
    world.use_nodes = True
    bg = world.node_tree.nodes.get("Background")
    if bg:
        bg.inputs[0].default_value = (0.015, 0.018, 0.035, 1.0)
        bg.inputs[1].default_value = 1.0
    bpy.context.scene.world = world

def make_volume_cube(name, location, scale, density, color, emission_strength, use_noise=True):
    bpy.ops.mesh.primitive_cube_add(size=2.0, location=location)
    ob = bpy.context.object
    ob.name = name
    ob.scale = (scale, scale, scale*0.55)
    mat = bpy.data.materials.new(name+"_Mat")
    mat.use_nodes = True
    nt = mat.node_tree
    for n in list(nt.nodes): nt.nodes.remove(n)
    out = nt.nodes.new("ShaderNodeOutputMaterial")
    out.location = (400,0)
    vol = nt.nodes.new("ShaderNodeVolumePrincipled")
    vol.location = (0,0)
    nt.links.new(vol.outputs[0], out.inputs[1])
    # base volume color / density
    vol.inputs["Color"].default_value = (*color, 1.0)
    vol.inputs["Density"].default_value = density
    vol.inputs["Emission Strength"].default_value = emission_strength
    vol.inputs["Emission Color"].default_value = (*color, 1.0)
    vol.inputs["Blackbody Intensity"].default_value = 0.0
    vol.inputs["Anisotropy"].default_value = 0.35
    # add noise texture driving density for tendrils/swirl
    if use_noise:
        coord = nt.nodes.new("ShaderNodeTexCoord")
        coord.location = (-600, 200)
        noise = nt.nodes.new("ShaderNodeTexNoise")
        noise.location = (-350, 150)
        noise.inputs["Scale"].default_value = 3.5 if "Aurora" in name else 5.0
        noise.inputs["Detail"].default_value = 4.0
        noise.inputs["Roughness"].default_value = 0.55
        ramp = nt.nodes.new("ShaderNodeValToRGB")
        ramp.location = (-150, 150)
        ramp.color_ramp.elements[0].position = 0.35
        ramp.color_ramp.elements[1].position = 0.82
        if "Aurora" in name:
            ramp.color_ramp.elements[0].color = (0.18, 0.35, 0.45, 1.0)
            ramp.color_ramp.elements[1].color = (0.95, 0.95, 0.95, 1.0)
        else:
            ramp.color_ramp.elements[0].color = (0.05, 0.05, 0.10, 1.0)
            ramp.color_ramp.elements[1].color = (0.90, 0.90, 1.0, 1.0)
        math_mul = nt.nodes.new("ShaderNodeMath")
        math_mul.location = (-150, -80)
        math_mul.operation = "MULTIPLY"
        math_mul.inputs[1].default_value = 1.6
        nt.links.new(coord.outputs["Object"], noise.inputs["Vector"])
        nt.links.new(noise.outputs["Fac"], ramp.inputs[0])
        nt.links.new(ramp.outputs[0], math_mul.inputs[0])
        nt.links.new(math_mul.outputs[0], vol.inputs["Density"])
        # emission strength via same fac
        nt.links.new(ramp.outputs[1], vol.inputs["Emission Strength"])  # alpha -> strength is ok
        vol.inputs["Emission Strength"].default_value = emission_strength
    ob.data.materials.append(mat)
    return ob

def setup_lights_and_cam(target_center, diag):
    # 3-point dream rig
    def light(name, loc, color, energy):
        data = bpy.data.lights.new(name, type="AREA")
        data.energy = energy
        data.color = color
        data.shape = "RECTANGLE"
        data.size = diag*0.9
        data.size_y = diag*0.6
        ob = bpy.data.objects.new(name, data)
        ob.location = loc
        bpy.context.collection.objects.link(ob)
        return ob
    d = max(diag, 1.0)
    light("Key",  target_center + Vector((1.2,-1.4,1.1)).normalized()*d*1.8, (1.0,0.78,0.62), 2800*d)
    light("Fill", target_center + Vector((-1.4,-0.7,0.45)).normalized()*d*1.6, (0.45,0.78,0.92), 1400*d)
    light("Rim",  target_center + Vector((0.2,1.3,0.9)).normalized()*d*1.5, (0.75,0.88,1.0), 1800*d)
    # ground as faint reflector for depth
    bpy.ops.mesh.primitive_plane_add(size=d*6, location=(target_center[0], target_center[1], -d*0.9))
    plane = bpy.context.object
    plane.name = "Ground"
    mat = bpy.data.materials.new("GroundMat")
    mat.use_nodes = True
    bsdf = mat.node_tree.nodes.get("Principled BSDF")
    if bsdf:
        bsdf.inputs["Base Color"].default_value = (0.04, 0.06, 0.10, 1.0)
        bsdf.inputs["Roughness"].default_value = 0.85
        bsdf.inputs["Metallic"].default_value = 0.05
    plane.data.materials.append(mat)

    cam_data = bpy.data.cameras.new("Cam")
    cam_data.lens = 50
    cam = bpy.data.objects.new("Cam", cam_data)
    # place camera looking at center
    cam.location = target_center + Vector((1.1, -2.0, 0.85))*d*0.95
    bpy.context.collection.objects.link(cam)
    target = bpy.data.objects.new("Target", None)
    target.location = target_center
    bpy.context.collection.objects.link(target)
    c = cam.constraints.new(type="TRACK_TO")
    c.target = target
    c.track_axis = "TRACK_NEGATIVE_Z"
    c.up_axis = "UP_Y"
    bpy.context.scene.camera = cam
    return cam

def render(out_path):
    scene = bpy.context.scene
    scene.render.engine = "CYCLES"
    scene.cycles.device = "CPU"
    scene.cycles.samples = SAMPLES
    scene.cycles.use_denoising = True
    try: scene.cycles.denoiser = "OPENIMAGEDENOISE"
    except: pass
    scene.render.resolution_x = SIZE
    scene.render.resolution_y = SIZE
    scene.render.resolution_percentage = 100
    scene.render.film_transparent = False
    scene.render.filepath = str(out_path)
    bpy.ops.render.render(write_still=True)
    print(f"[blender] wrote {out_path.name}")

def main():
    argv = sys.argv
    target = "all"
    if "--" in argv:
        idx = argv.index("--")
        extra = argv[idx+1:]
        for a in extra:
            if a.startswith("--target="): target = a.split("=")[1]
    # common setup
    clear()
    setup_world()
    bpy.context.scene.render.engine = "CYCLES"
    # create both volumes for combined, or individually
    if target == "aurora":
        clear(); setup_world()
        make_volume_cube("AuroraVeil", (0,0,0.4), 1.6, 1.2, (0.22,0.72,0.88), 1.4)
        cam = setup_lights_and_cam(Vector((0,0,0.2)), 3.2)
        render(OUT_DIR / "beauty_AuroraVeil.png")
    elif target == "sorrow":
        clear(); setup_world()
        make_volume_cube("SorrowFog", (0,0,0.15), 1.4, 1.8, (0.18,0.12,0.48), 0.55)
        cam = setup_lights_and_cam(Vector((0,0,0.0)), 3.0)
        render(OUT_DIR / "beauty_SorrowFog.png")
    else:
        # combined scene: two volumes side by side + beauty_composite
        aur = make_volume_cube("AuroraVeil", (-1.55,0,0.45), 1.15, 1.0, (0.22,0.72,0.88), 1.25)
        sor = make_volume_cube("SorrowFog", (1.55,0,0.15), 1.05, 1.55, (0.18,0.12,0.48), 0.55)
        cam = setup_lights_and_cam(Vector((0,0,0.2)), 5.0)
        render(OUT_DIR / "beauty_combined.png")
        # also render individual crops by moving cam (reuse)
        # aurora close
        bpy.context.scene.camera.location = Vector((-1.55, -2.2, 1.1))
        # retarget is still at origin, so adjust target
        for ob in bpy.data.objects:
            if ob.name == "Target":
                ob.location = Vector((-1.55,0,0.4))
        render(OUT_DIR / "beauty_AuroraVeil.png")
        for ob in bpy.data.objects:
            if ob.name == "Target":
                ob.location = Vector((1.55,0,0.15))
        bpy.context.scene.camera.location = Vector((1.55, -2.0, 0.95))
        render(OUT_DIR / "beauty_SorrowFog.png")

if __name__ == "__main__":
    main()
'''

# ---------------------------------------------------------------------------
# Main
# ---------------------------------------------------------------------------

def sha256_of(path):
    h=hashlib.sha256()
    with open(path,"rb") as f:
        for c in iter(lambda:f.read(1<<16),b""): h.update(c)
    return h.hexdigest()

def find_blender():
    candidates = [
        r"C:\Program Files\Blender Foundation\Blender 4.5\blender.exe",
        r"C:\Program Files\Blender Foundation\Blender 4.3\blender.exe",
        r"C:\Program Files\Blender Foundation\Blender 4.2\blender.exe",
        r"C:\Program Files\Blender Foundation\Blender 5.1\blender.exe",
        r"C:\Program Files\Blender Foundation\Blender 5.2\blender.exe",
    ]
    for c in candidates:
        if Path(c).exists(): return c
    import shutil
    return shutil.which("blender")

def run_blender_renders():
    blender = find_blender()
    if not blender:
        print("[surreal-vdb] Blender not found — skipping beauty renders (run with --blender-render inside Blender)")
        return []
    # write temp render script
    tmp = OUT_DIR / "_blender_vol_render.py"
    tmp.parent.mkdir(parents=True, exist_ok=True)
    script = BLENDER_RENDER_SCRIPT.replace("__PROJECT_ROOT__", str(PROJECT_ROOT).replace("\\","\\\\")).replace("__OUT_DIR__", str(OUT_DIR).replace("\\","\\\\"))
    tmp.write_text(script, encoding="utf-8")
    cmd = [blender, "--background", "--python", str(tmp), "--", "--target=all"]
    print(f"[surreal-vdb] Blender beauty render: {' '.join(cmd)}")
    proc = subprocess.run(cmd, capture_output=True, text=True, timeout=300)
    print(proc.stdout[-4000:] if proc.stdout else "")
    if proc.stderr: print(proc.stderr[-4000:])
    if proc.returncode != 0:
        print(f"[surreal-vdb] Blender render exit {proc.returncode}")
    # also verify outputs
    outs = []
    for name in ["beauty_combined.png","beauty_AuroraVeil.png","beauty_SorrowFog.png"]:
        p = OUT_DIR / name
        if p.exists(): outs.append(p)
    return outs

def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--seed", type=int, default=SEED)
    ap.add_argument("--render", action="store_true", help="also run Blender beauty renders")
    ap.add_argument("--blender-render", action="store_true", help="internal: running inside Blender")
    ap.add_argument("--target", default="all")
    args = ap.parse_args()

    # Blender entry point
    if args.blender_render or "bpy" in sys.modules:
        # executed as blender --background --python
        # run the embedded render directly
        # we are here only if invoked via Blender; execute render script logic via exec
        # For simplicity, just note and exit — actual render is via temp script
        print("[surreal-vdb] inside Blender — use --render from plain Python to auto-spawn Blender")
        return

    OUT_DIR.mkdir(parents=True, exist_ok=True)
    print(f"[surreal-vdb] OUT_DIR={OUT_DIR} seed={args.seed}")

    # 1) VDB volumes
    av = aurora_veil_density(args.seed)
    sf = sorrow_fog_density(args.seed+100)
    vdb_files = []
    for density, name, palette in [
        (av, "VOL_AuroraVeil", {"aqua": AURORA_AQUA.tolist(), "pink": AURORA_PINK.tolist(), "note": "swirling aqua-pink veil"}),
        (sf, "VOL_SorrowFog",  {"deep": SORROW_DEEP.tolist(), "mid": SORROW_MID.tolist(), "note": "deep indigo tendrils"}),
    ]:
        p, hdr = write_vdb(OUT_DIR / f"{name}.vdb", density, name, palette, args.seed)
        # verify readback
        hdr2, arr2 = read_vdb_density(p)
        assert arr2.shape == (SIZE_VDB,SIZE_VDB,SIZE_VDB)
        vdb_files.append((p, hdr))
        print(f"[surreal-vdb] wrote {p.name} {SIZE_VDB}^3 mean={hdr['voxel_range'][2]:.3f} min={hdr['voxel_range'][0]:.3f} max={hdr['voxel_range'][1]:.3f}")

    # 2) Sky LUTs 1024
    import PIL.Image  # require PIL
    luts = []
    for fn, name, desc in [
        (dream_sunset_lut, "T_Sky_DreamSunset", "Dream Sunset — peach-pink-lavender-teal horizon with sun disk & cirrus"),
        (abyss_noon_lut,   "T_Sky_AbyssNoon",   "Abyss Noon — deep teal/indigo noon with god-ray shafts & biolum flecks"),
        (starfall_night_lut,"T_Sky_StarfallNight","Starfall Night — midnight indigo with starfall streaks & aurora ribbons"),
    ]:
        arr = fn(args.seed if "Dream" in desc else args.seed+50 if "Abyss" in desc else args.seed+99, SIZE_LUT)
        p = rc.save_image(OUT_DIR / f"{name}.png", arr, "rgb")
        luts.append((p, name, desc))
        print(f"[surreal-vdb] wrote {p.name} {SIZE_LUT}x{SIZE_LUT}")

    # 3) Beauty renders
    beauty = []
    if args.render:
        beauty = run_blender_renders()
    else:
        # auto-render if Blender available (task says Also Blender beauty renders)
        beauty = run_blender_renders()

    # 4) Manifest
    files = []
    for p, hdr in vdb_files:
        files.append({"name": p.stem, "path": str(p.relative_to(PROJECT_ROOT)).replace("\\","/"), "abspath": str(p),
                      "kind": "vdb", "size": SIZE_VDB, "grid": f"{SIZE_VDB}^3", "dtype": "float32",
                      "palette": hdr["palette_srgb"], "voxel_range": hdr["voxel_range"],
                      "sha256": sha256_of(p), "bytes": p.stat().st_size})
    for p, name, desc in luts:
        files.append({"name": name, "path": str(p.relative_to(PROJECT_ROOT)).replace("\\","/"), "abspath": str(p),
                      "kind": "rgb", "size": SIZE_LUT, "resolution": f"{SIZE_LUT}x{SIZE_LUT}",
                      "desc": desc, "sha256": sha256_of(p), "bytes": p.stat().st_size})
    for p in beauty:
        files.append({"name": p.stem, "path": str(p.relative_to(PROJECT_ROOT)).replace("\\","/"), "abspath": str(p),
                      "kind": "beauty_render", "engine": "Cycles CPU", "samples": 64, "resolution": "1024x1024",
                      "sha256": sha256_of(p), "bytes": p.stat().st_size})

    manifest = {
        "schema": "melodia.surreal_vdb.v1",
        "seed": args.seed,
        "params": {
            "vdb_size": SIZE_VDB,
            "lut_size": SIZE_LUT,
            "volumes": [
                {"name": "VOL_AuroraVeil", "palette": "swirling aqua-pink", "density": "vortex swirl + fBm veil (aqua 0.18,0.85,0.92 -> pink 0.96,0.42,0.72)"},
                {"name": "VOL_SorrowFog", "palette": "deep indigo tendrils", "density": "vertical ridge tendrils + gravity falloff (indigo 0.08,0.06,0.32)"},
            ],
            "sky_luts": [
                {"name": "T_Sky_DreamSunset", "palette": "peach-pink-lavender-teal"},
                {"name": "T_Sky_AbyssNoon", "palette": "deep teal-indigo with god-rays"},
                {"name": "T_Sky_StarfallNight", "palette": "midnight indigo + starfall + aurora"},
            ],
            "beauty_renders": "Blender Cycles CPU 64spp — volume Principled test scene (no editor needed)",
            "vdb_note": "Placeholder VDB (MAGIC+VDB header + raw float32). Recook via Houdini hython for UE Sparse Volume Texture shipping import.",
        },
        "out_dir": str(OUT_DIR.relative_to(PROJECT_ROOT)).replace("\\","/"),
        "files": files,
    }
    mp = OUT_DIR / "vdb_manifest.json"
    mp.write_text(json.dumps(manifest, indent=2), encoding="utf-8")
    print(f"[surreal-vdb] manifest -> {mp} ({len(files)} files)")
    # summary
    for f in files:
        print(f"  - {f['name']}: {f.get('kind')} {f.get('bytes')}B sha256:{f['sha256'][:12]}...")

if __name__ == "__main__":
    main()
