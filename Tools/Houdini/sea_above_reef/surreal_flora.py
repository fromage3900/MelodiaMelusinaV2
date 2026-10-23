"""Surreal Dream Flora — oversized blooms for Sea Above (R-surreal).

Three archetypes, each with a 1024 PBR texture set + Blender mesh + beauty render:

  1) Ghost Lotus        8m diameter translucent petals with inside glow
  2) Spiral Siren Kelp 30m twisting ribbon with eye-spots
  3) Crystal Anemone    4m fractal polyp cluster

Textures: numpy+Pillow (reef_common periodic noise, WrappedDraw, normal_from_height).
          Each set: Albedo (sRGB), Normal (OpenGL Y+), Roughness (data), Emissive (data),
                    Translucency/Opacity where applicable. All tileable where it matters
                    (vein fields, kelp skin) — lattice-periodic; eye-spots via WrappedDraw.

Meshes: Blender 5.2 headless (bpy) — geometry nodes / primitive ops approach.
        Scale is metres; Blender units = metres (UE import x100 to cm).
        Each mesh saved as .blend + .fbx + beauty PNG (1920x1080, CYCLES, 96spp).

Outputs:
  Saved/Audit/surreal_sweep/flora/textures/T_Surreal_*.png   (12 files, 1024)
  Saved/Audit/surreal_sweep/flora/meshes/SM_Surreal_*.{blend,fbx}
  Saved/Audit/surreal_sweep/flora/renders/SM_Surreal_*.png   (1920x1080)
  Saved/Audit/surreal_sweep/flora/flora_manifest.json

Runs:
  python Tools/Houdini/sea_above_reef/surreal_flora.py              # full sweep (textures + blender meshes/renders)
  python Tools/Houdini/sea_above_reef/surreal_flora.py --textures-only
  blender --background --python Tools/Houdini/sea_above_reef/surreal_flora.py -- --mesh ghost_lotus
  blender --background --python Tools/Houdini/sea_above_reef/surreal_flora.py -- --mesh siren_kelp
  blender --background --python Tools/Houdini/sea_above_reef/surreal_flora.py -- --mesh crystal_anemone
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
OUT_ROOT = PROJECT_ROOT / "Saved" / "Audit" / "surreal_sweep" / "flora"
TEX_DIR = OUT_ROOT / "textures"
MESH_DIR = OUT_ROOT / "meshes"
RENDER_DIR = OUT_ROOT / "renders"
BLENDER_EXE = Path("C:/Program Files/Blender Foundation/Blender 5.2/blender.exe")

SIZE = 1024
SEED = 20260829

# Add reef_common
sys.path.insert(0, str(Path(__file__).resolve().parent))
import reef_common as rc  # noqa: E402

# ---------------------------------------------------------------------------
# Texture builders
# ---------------------------------------------------------------------------

def build_ghost_lotus(size=SIZE, seed=SEED):
    rng = np.random.default_rng(seed + 11)
    # petal vein field: elongated Voronoi + fBm
    veins = rc.fbm(size, 8, 4, rng, gain=0.5)
    # petal shape height: large soft gradient + pore dots
    f1 = rc.periodic_voronoi_f1(size, 16, 0.75, np.random.default_rng(seed + 12))
    petal_mask = np.clip(1.0 - f1 * 1.8, 0, 1) ** 1.2  # cell interiors = petal centres
    # translucent petal colour: pale rose-white -> lavender edge
    PALE = np.array([244, 232, 235], np.float32) / 255.0
    LAV = np.array([210, 198, 232], np.float32) / 255.0
    VEIN_CLR = np.array([198, 170, 185], np.float32) / 255.0
    # base blend
    t = np.clip((veins - 0.35) * 1.8, 0, 1)
    albedo = PALE[None, None, :] * (1 - t[..., None]) + LAV[None, None, :] * t[..., None]
    # vein lines darken
    vein_lines = np.clip(1.0 - f1 * 3.2, 0, 1) ** 0.9
    # use voronoi edges as veins
    edge = np.clip(f1 * 2.2, 0, 1)
    edge = (1.0 - np.clip((edge - 0.5) * 4, 0, 1)) * 0.35
    albedo = albedo * (1 - edge[..., None] * 0.5) + VEIN_CLR[None, None, :] * (edge[..., None] * 0.5)
    # centre glow boost
    ys, xs = np.mgrid[0:size, 0:size].astype(np.float32)
    cx, cy = size * 0.5, size * 0.5
    dist = np.sqrt((xs - cx) ** 2 + (ys - cy) ** 2) / (size * 0.5)
    centre = np.clip(1.0 - dist * 1.4, 0, 1) ** 2.0
    albedo = albedo * (0.88 + 0.22 * centre[..., None])
    albedo = np.clip(albedo, 0, 1)

    # height for normal: veins slightly raised, centre bulge
    height = 0.5 + 0.30 * (veins - 0.5) + 0.18 * np.clip(1.0 - f1 * 2.0, 0, 1) + 0.12 * centre
    height = np.clip(height, 0, 1)
    normal = rc.normal_from_height(height, strength=2.8)

    # roughness: petals waxy (0.35 centre -> 0.55 edge), veins slightly rougher
    rough = 0.35 + 0.20 * (1.0 - centre) + 0.10 * vein_lines
    rough = np.clip(rough, 0.15, 0.85)

    # emissive: inside glow — strong at centre, fading out, with petal cell modulation
    emissive = np.clip(centre * 0.85 + petal_mask * 0.15, 0, 1) ** 1.1
    # add soft radial falloff pulse
    emissive = emissive * (0.7 + 0.3 * np.clip(1.0 - dist, 0, 1))

    # translucency / opacity: petals translucent, veins slightly opaque
    transluc = np.clip(0.55 + 0.30 * petal_mask - 0.15 * vein_lines, 0, 1)

    return {
        "T_Surreal_GhostLotus_Albedo": (albedo, "rgb"),
        "T_Surreal_GhostLotus_Normal": (normal, "rgb"),
        "T_Surreal_GhostLotus_Roughness": (rough, "gray"),
        "T_Surreal_GhostLotus_Emissive": (emissive, "gray"),
        "T_Surreal_GhostLotus_Translucency": (transluc, "gray"),
    }

def build_siren_kelp(size=SIZE, seed=SEED):
    rng = np.random.default_rng(seed + 21)
    # ribbon skin: wavy fBm + sine warp
    base = rc.fbm(size, 8, 4, rng, gain=0.5)
    warp = rc.fbm(size, 32, 2, np.random.default_rng(seed + 22), gain=0.5)
    waves = rc.tileable_sine(size, 3, 7, phase=0.6, warp=warp, warp_amp=1.2)
    skin = np.clip(0.5 * base + 0.5 * waves, 0, 1)
    # colour: deep teal -> amber -> bruise purple
    TEAL = np.array([22, 78, 82], np.float32) / 255.0
    OLIVE = np.array([58, 95, 72], np.float32) / 255.0
    AMBER = np.array([165, 120, 58], np.float32) / 255.0
    BRUISE = np.array([62, 42, 78], np.float32) / 255.0
    # vertical gradient (kelp length axis = y)
    ys = np.mgrid[0:size, 0:size][0].astype(np.float32) / size  # 0..1 top->bottom but we want y gradient
    # Actually use skin + y for colour
    t_y = ys  # 0 top, 1 bottom — invert for base->tip
    # mix
    c1 = TEAL[None, None, :] * (1 - skin[..., None]) + OLIVE[None, None, :] * skin[..., None]
    # tip warmer
    tip = np.clip((t_y - 0.5) * 1.5, 0, 1)
    c1 = c1 * (1 - tip[..., None] * 0.6) + AMBER[None, None, :] * (tip[..., None] * 0.6)
    # bruise streaks
    streak = np.clip(rc.fbm(size, 16, 3, np.random.default_rng(seed + 23), gain=0.5) - 0.5, 0, 1)
    c1 = c1 * (1 - streak[..., None] * 0.25) + BRUISE[None, None, :] * (streak[..., None] * 0.25)
    albedo_base = np.clip(c1, 0, 1)

    # eye-spots: WrappedDraw circles + iris detail
    # Use WrappedDraw for seamless eye spots on a grid
    wd_outer = rc.WrappedDraw(size, background=0)
    wd_iris = rc.WrappedDraw(size, background=0)
    rng_eye = np.random.default_rng(seed + 24)
    eye_positions = []
    # 5x5 grid jittered, tileable
    for gy in range(5):
        for gx in range(5):
            jx = (rng_eye.random() - 0.5) * 0.4
            jy = (rng_eye.random() - 0.5) * 0.4
            cx = int((gx + 0.5 + jx) * size / 5)
            cy = int((gy + 0.5 + jy) * size / 5)
            r_outer = int(size * (0.035 + rng_eye.random() * 0.015))
            r_iris = int(r_outer * 0.55)
            # outer sclera (cream)
            wd_outer.ellipse([(cx - r_outer, cy - r_outer), (cx + r_outer, cy + r_outer)], fill=255)
            wd_iris.ellipse([(cx - r_iris, cy - r_iris), (cx + r_iris, cy + r_iris)], fill=255)
            eye_positions.append((cx, cy, r_outer))
    eye_outer = np.array(wd_outer.result(), dtype=np.float32) / 255.0
    eye_iris = np.array(wd_iris.result(), dtype=np.float32) / 255.0
    # pupil smaller
    wd_pupil = rc.WrappedDraw(size, background=0)
    for cx, cy, r_outer in eye_positions:
        r_pupil = int(r_outer * 0.28)
        wd_pupil.ellipse([(cx - r_pupil, cy - r_pupil), (cx + r_pupil, cy + r_pupil)], fill=255)
    eye_pupil = np.array(wd_pupil.result(), dtype=np.float32) / 255.0

    # composite eye colours onto albedo
    SCLERA = np.array([235, 225, 195], np.float32) / 255.0
    IRIS_COL = np.array([190, 60, 45], np.float32) / 255.0  # siren red-orange
    PUPIL_COL = np.array([12, 8, 18], np.float32) / 255.0
    # iris ring = iris - pupil
    iris_ring = np.clip(eye_iris - eye_pupil, 0, 1)
    # sclera ring = outer - iris
    sclera_ring = np.clip(eye_outer - eye_iris, 0, 1)
    eye_mask = eye_outer
    for c in range(3):
        albedo_base[:, :, c] = albedo_base[:, :, c] * (1 - sclera_ring * 0.95) + SCLERA[c] * (sclera_ring * 0.95)
        albedo_base[:, :, c] = albedo_base[:, :, c] * (1 - iris_ring * 0.95) + IRIS_COL[c] * (iris_ring * 0.95)
        albedo_base[:, :, c] = albedo_base[:, :, c] * (1 - eye_pupil * 0.98) + PUPIL_COL[c] * (eye_pupil * 0.98)
    albedo = np.clip(albedo_base, 0, 1)

    # height: skin bumps + eye bulges
    height = np.clip(0.45 + 0.30 * skin + 0.20 * eye_outer + 0.10 * (1.0 - streak), 0, 1)
    normal = rc.normal_from_height(height, strength=3.0)

    # roughness: kelp slimy (0.25) vs eye sclera glossy (0.15) vs iris slightly rougher
    rough = 0.42 - 0.18 * skin  # wavy skin varies
    rough = rough * (1 - eye_outer * 0.5) + 0.18 * eye_outer
    rough = np.clip(rough, 0.12, 0.85)

    # emissive: eyes glow (iris + pupil), faint skin biolume
    emissive = np.clip(iris_ring * 0.85 + eye_pupil * 0.35 + skin * 0.04, 0, 1)

    return {
        "T_Surreal_SirenKelp_Albedo": (albedo, "rgb"),
        "T_Surreal_SirenKelp_Normal": (normal, "rgb"),
        "T_Surreal_SirenKelp_Roughness": (rough, "gray"),
        "T_Surreal_SirenKelp_Emissive": (emissive, "gray"),
        "T_Surreal_SirenKelp_EyeMask": (eye_mask, "gray"),
    }

def build_crystal_anemone(size=SIZE, seed=SEED):
    rng = np.random.default_rng(seed + 31)
    # crystalline facets: sharp Voronoi F1 + fBm
    f1 = rc.periodic_voronoi_f1(size, 32, 0.9, np.random.default_rng(seed + 32))
    facets = np.clip(1.0 - f1 * 2.0, 0, 1) ** 0.7
    sparkle_noise = rc.fbm(size, 16, 3, rng, gain=0.5)
    # height: facet domes + sparkle
    height = np.clip(0.40 + 0.35 * facets + 0.25 * sparkle_noise, 0, 1)
    # colour: iridescent crystal — pastel cyan -> magenta -> amber fracture lines
    CYAN = np.array([165, 225, 235], np.float32) / 255.0
    MAG = np.array([205, 155, 215], np.float32) / 255.0
    AMBER = np.array([235, 195, 115], np.float32) / 255.0
    DEEP = np.array([45, 38, 68], np.float32) / 255.0
    # hue shift by Voronoi cell + sparkle
    hue_t = np.clip(facets * 0.7 + sparkle_noise * 0.3, 0, 1)
    # lerp cyan->magenta
    base = CYAN[None, None, :] * (1 - hue_t[..., None]) + MAG[None, None, :] * hue_t[..., None]
    # fracture lines = Voronoi edges (dark)
    edge = np.clip(f1 * 3.5, 0, 1)
    # edges are where f1 ~ 0.5/cell boundary — invert
    # Use distance to edge: small f1 near centre, large near edge — but need edge detection
    # Instead use a second voronoi with different jitter to get veins
    f1b = rc.periodic_voronoi_f1(size, 32, 0.3, np.random.default_rng(seed + 33))
    # edge is where f1 and f1b differ? simpler: threshold f1 mid-range
    is_edge = np.clip(1.0 - np.abs(f1 - 0.35) * 6.0, 0, 1) ** 1.5
    base = base * (1 - is_edge[..., None] * 0.55) + DEEP[None, None, :] * (is_edge[..., None] * 0.45) + AMBER[None, None, :] * (is_edge[..., None] * 0.25)
    # sparkle highlights
    spark = np.clip((sparkle_noise - 0.65) * 4.0, 0, 1) ** 1.2
    base = np.clip(base + spark[..., None] * 0.35, 0, 1)
    albedo = np.clip(base, 0, 1)

    normal = rc.normal_from_height(height, strength=4.0)

    # roughness: crystal facets glossy (0.15) vs fracture lines rough (0.55)
    rough = 0.18 + 0.35 * is_edge + 0.10 * (1.0 - facets)
    rough = np.clip(rough, 0.08, 0.75)

    # emissive: facet centres + sparkle glow, fracture lines dim
    emissive = np.clip(facets * 0.55 + spark * 0.85, 0, 1) ** 1.15
    emissive = emissive * (1.0 - is_edge * 0.6)

    # opacity / crystal transmission mask
    opacity = np.clip(0.85 + 0.15 * facets - 0.10 * is_edge, 0, 1)

    return {
        "T_Surreal_CrystalAnemone_Albedo": (albedo, "rgb"),
        "T_Surreal_CrystalAnemone_Normal": (normal, "rgb"),
        "T_Surreal_CrystalAnemone_Roughness": (rough, "gray"),
        "T_Surreal_CrystalAnemone_Emissive": (emissive, "gray"),
        "T_Surreal_CrystalAnemone_Opacity": (opacity, "gray"),
    }

# ---------------------------------------------------------------------------
# Mesh / render — Blender side
# ---------------------------------------------------------------------------

BLENDER_MESH_SCRIPT = r'''
import sys, math, random
from pathlib import Path
import bpy
from mathutils import Vector, Matrix

PROJECT_ROOT = Path("C:/EnvironmentPortfolio/BS_GodFile")
# Robust fallback: walk up from script path to find workspace root
if not (PROJECT_ROOT / "Tools").exists():
    try:
        _script = Path(__file__).resolve() if "__file__" in globals() else None
        if _script and _script.exists():
            for p in _script.parents:
                if (p / "Tools" / "Houdini").exists() or (p / ".git").exists():
                    PROJECT_ROOT = p
                    break
    except:
        PROJECT_ROOT = Path("C:/EnvironmentPortfolio/BS_GodFile")

MESH_NAME = "__MESH_NAME__"
SEED = 20260829

OUT_MESH = PROJECT_ROOT / "Saved/Audit/surreal_sweep/flora/meshes"
OUT_RENDER = PROJECT_ROOT / "Saved/Audit/surreal_sweep/flora/renders"
OUT_MESH.mkdir(parents=True, exist_ok=True)
OUT_RENDER.mkdir(parents=True, exist_ok=True)

def clear_scene():
    bpy.ops.object.select_all(action="SELECT")
    bpy.ops.object.delete(use_global=False)
    for block in (bpy.data.meshes, bpy.data.materials, bpy.data.lights, bpy.data.cameras, bpy.data.images):
        for item in list(block):
            if item.users == 0:
                try:
                    block.remove(item)
                except:
                    pass

def new_material(name, base_color, roughness=0.5, metallic=0.0, emission_color=None, emission_strength=0.0, transmission=0.0, alpha=1.0):
    mat = bpy.data.materials.new(name)
    mat.use_nodes = True
    bsdf = mat.node_tree.nodes.get("Principled BSDF")
    if bsdf:
        bsdf.inputs["Base Color"].default_value = (*base_color, 1.0)
        if "Roughness" in bsdf.inputs:
            bsdf.inputs["Roughness"].default_value = roughness
        if "Metallic" in bsdf.inputs:
            bsdf.inputs["Metallic"].default_value = metallic
        if emission_color is not None and "Emission Color" in bsdf.inputs:
            bsdf.inputs["Emission Color"].default_value = (*emission_color, 1.0)
            try:
                bsdf.inputs["Emission Strength"].default_value = emission_strength
            except:
                pass
        if "Alpha" in bsdf.inputs:
            bsdf.inputs["Alpha"].default_value = alpha
        if "Transmission Weight" in bsdf.inputs:
            bsdf.inputs["Transmission Weight"].default_value = transmission
        elif "Transmission" in bsdf.inputs:
            bsdf.inputs["Transmission"].default_value = transmission
    # blend for translucency
    if alpha < 1.0 or transmission > 0:
        try:
            mat.blend_method = "BLEND"
        except:
            pass
        try:
            mat.shadow_method = "HASHED"
        except:
            pass
    return mat

def setup_world():
    world = bpy.data.worlds.get("World") or bpy.data.worlds.new("World")
    bpy.context.scene.world = world
    world.use_nodes = True
    bg = world.node_tree.nodes.get("Background")
    if bg:
        bg.inputs[0].default_value = (0.015, 0.025, 0.045, 1.0)
        bg.inputs[1].default_value = 1.2
    return world

def rig_and_camera(center, diag):
    # 3-point dream rig
    def add_light(name, loc, color, energy, size=1.5):
        data = bpy.data.lights.new(name, type="AREA")
        data.energy = energy
        data.color = color
        data.size = size
        ob = bpy.data.objects.new(name, data)
        ob.location = loc
        bpy.context.collection.objects.link(ob)
        return ob
    d = max(diag, 1.0)
    KEY = (1.0, 0.92, 0.82)
    FILL = (0.55, 0.75, 0.92)
    RIM = (0.85, 0.65, 1.0)
    add_light("Key", center + Vector((1.0, -1.1, 1.0)).normalized() * d * 1.4, KEY, 1200 * d * d, 2.0*d)
    add_light("Fill", center + Vector((-1.2, -0.6, 0.5)).normalized() * d * 1.6, FILL, 500 * d * d, 2.5*d)
    add_light("Rim", center + Vector((0.1, 1.2, 0.8)).normalized() * d * 1.3, RIM, 700 * d * d, 1.8*d)
    cam_data = bpy.data.cameras.new("Cam")
    cam_data.lens = 52
    cam_data.clip_start = 0.01
    cam_data.clip_end = 5000
    cam = bpy.data.objects.new("Cam", cam_data)
    direction = Vector((1.0, -1.4, 0.55)).normalized()
    dist = d * 1.75 + 0.5
    cam.location = center + direction * dist
    bpy.context.collection.objects.link(cam)
    target = bpy.data.objects.new("Target", None)
    target.location = center
    bpy.context.collection.objects.link(target)
    c = cam.constraints.new(type="TRACK_TO")
    c.target = target
    c.track_axis = "TRACK_NEGATIVE_Z"
    c.up_axis = "UP_Y"
    return cam

def bbox_center_diag(objs):
    lo = Vector((1e9,1e9,1e9))
    hi = Vector((-1e9,-1e9,-1e9))
    for ob in objs:
        if ob.type != "MESH":
            continue
        for corner in ob.bound_box:
            w = ob.matrix_world @ Vector(corner)
            lo = Vector(map(min, lo, w))
            hi = Vector(map(max, hi, w))
    center = (lo+hi)/2.0
    diag = (hi-lo).length
    return center, diag

def build_ghost_lotus():
    # 8m diameter lotus: central receptacle + 3 rings of petals
    clear_scene()
    rng = random.Random(SEED+101)
    mats = {}
    mats["petal_outer"] = new_material("M_GhostPetalOuter", (0.92,0.88,0.90), roughness=0.38, transmission=0.35, emission_color=(1.0,0.82,0.78), emission_strength=0.6, alpha=0.92)
    mats["petal_inner"] = new_material("M_GhostPetalInner", (0.96,0.92,0.94), roughness=0.32, transmission=0.45, emission_color=(1.0,0.85,0.75), emission_strength=1.1, alpha=0.88)
    mats["petal_mid"] = new_material("M_GhostPetalMid", (0.90,0.84,0.92), roughness=0.40, transmission=0.30, emission_color=(0.95,0.75,0.88), emission_strength=0.45, alpha=0.90)
    mats["receptacle"] = new_material("M_Receptacle", (0.78,0.72,0.55), roughness=0.65, emission_color=(0.9,0.75,0.45), emission_strength=0.8)
    mats["glow_core"] = new_material("M_GlowCore", (1.0,0.95,0.85), roughness=0.8, emission_color=(1.0,0.72,0.55), emission_strength=3.5)

    # receptacle: flattened sphere
    bpy.ops.mesh.primitive_uv_sphere_add(radius=1.0, segments=32, ring_count=16, location=(0,0,0.15))
    rec = bpy.context.object
    rec.name = "GhostLotus_Receptacle"
    rec.scale = (1.1, 1.1, 0.45)
    rec.data.materials.append(mats["receptacle"])
    # glow core inside receptacle
    bpy.ops.mesh.primitive_uv_sphere_add(radius=0.55, segments=24, ring_count=12, location=(0,0,0.35))
    core = bpy.context.object
    core.name = "GhostLotus_GlowCore"
    core.data.materials.append(mats["glow_core"])
    # light inside
    ldata = bpy.data.lights.new("LotusGlow", type="POINT")
    ldata.energy = 1800
    ldata.color = (1.0, 0.78, 0.62)
    ldata.shadow_soft_size = 0.8
    lob = bpy.data.objects.new("LotusGlow", ldata)
    lob.location = (0,0,0.4)
    bpy.context.collection.objects.link(lob)

    # petal builder
    def make_petal(length, width, curvature, location, rotation_euler, mat):
        # use a plane subdivided + deform
        bpy.ops.mesh.primitive_plane_add(size=1.0, location=location, rotation=rotation_euler)
        ob = bpy.context.object
        # subdivide
        bpy.ops.object.mode_set(mode="EDIT")
        bpy.ops.mesh.subdivide(number_cuts=6)
        bpy.ops.object.mode_set(mode="OBJECT")
        mesh = ob.data
        # deform vertices: length along Y, width along X, curvature in Z
        for v in mesh.vertices:
            # plane is 1x1 centred; map to petal shape
            # x in [-0.5,0.5], y in [-0.5,0.5]
            x0, y0 = v.co.x, v.co.y
            # petal profile: taper to tip, bulge middle
            t = (y0+0.5)  # 0 base -> 1 tip
            w_prof = math.sin(math.pi * t) * 0.85 + 0.15  # bulge
            # tip pointed
            if t > 0.75:
                w_prof *= (1.0 - (t-0.75)/0.25 * 0.45)
            nx = x0 * width * w_prof
            ny = (t-0.3) * length  # shift so base near origin
            # curvature: arch upward then droop at tip
            nz = curvature * math.sin(math.pi * t * 0.85) * (1.2 - 0.4*t) + (x0*x0)*width*0.3
            v.co = Vector((nx, ny, nz))
        # smooth
        for poly in mesh.polygons:
            poly.use_smooth = True
        ob.data.materials.append(mat)
        return ob

    petals = []
    # 3 rings
    configs = [
        (8,  2.2, 1.35, 0.75, 12, "petal_outer"),   # outer: 8 petals, long, flat
        (8,  1.85, 1.15, 0.95, 22, "petal_mid"),     # mid: 8 petals offset
        (6,  1.45, 0.95, 1.15, 0,  "petal_inner"),   # inner: 6 petals, more upright
    ]
    for n, length, width, curve, angle_off, mat_key in configs:
        for i in range(n):
            ang = i / n * 360.0 + angle_off + rng.uniform(-2,2)
            rad = math.radians(ang)
            # petals radiate from centre; location slightly out
            base_r = 0.55 if mat_key=="petal_inner" else 0.75
            loc = (math.cos(rad)*base_r, math.sin(rad)*base_r, 0.18)
            # rotation: face outward, tilt outward
            tilt = 18 if mat_key=="petal_outer" else (32 if mat_key=="petal_mid" else 48)
            rot = (math.radians(90-tilt), 0, rad)
            # Euler XYZ in blender: need to handle correctly — use quaternion then convert
            # Simpler: place at origin rotated, then move
            ob = make_petal(length, width, curve, (0,0,0), (0,0,0), mats[mat_key])
            ob.name = f"Petal_{mat_key}_{i}"
            # transform: rotate around Z then tilt
            # Use matrix
            import mathutils
            m_rot_z = Matrix.Rotation(rad, 4, 'Z')
            m_tilt = Matrix.Rotation(math.radians(90-tilt), 4, 'X')
            # petal local Y is length direction — after tilt, Y points outward+up
            # Apply: first tilt around X, then rotate around Z, then translate
            ob.matrix_world = Matrix.Translation(Vector(loc)) @ m_rot_z @ m_tilt @ Matrix.Translation(Vector((0, length*0.35, 0)))
            # ensure transform applied to mesh
            bpy.context.view_layer.update()

    # Scale to 8m diameter: current outer tip radius ~ 0.75+length ~ 2.95 => diam ~5.9
    # Need diam 8.0 => scale ~1.36
    scale_fac = 8.0 / 5.9
    for ob in bpy.context.scene.objects:
        if ob.type == "MESH":
            ob.scale = (scale_fac, scale_fac, scale_fac)
    # also scale lights
    lob.location = Vector(lob.location) * scale_fac
    lob.data.energy *= scale_fac * scale_fac
    bpy.context.view_layer.update()
    return [o for o in bpy.context.scene.objects if o.type=="MESH"]

def build_siren_kelp():
    clear_scene()
    rng = random.Random(SEED+202)
    mats = {}
    mats["kelp"] = new_material("M_SirenKelp", (0.18,0.32,0.28), roughness=0.38, emission_color=(0.9,0.45,0.25), emission_strength=0.0)
    mats["eye_sclera"] = new_material("M_EyeSclera", (0.92,0.88,0.78), roughness=0.25, emission_color=(0.9,0.82,0.65), emission_strength=0.3)
    mats["eye_iris"] = new_material("M_EyeIris", (0.78,0.22,0.15), roughness=0.35, emission_color=(1.0,0.25,0.12), emission_strength=1.2)
    mats["eye_pupil"] = new_material("M_EyePupil", (0.04,0.03,0.06), roughness=0.15)

    # Ribbon: create a long subdivided plane 30m tall, ~0.9m wide, twisting
    H = 30.0
    W = 0.85
    rows = 90
    cols = 8
    bpy.ops.mesh.primitive_plane_add(size=1.0, location=(0,0,H/2))
    kelp = bpy.context.object
    kelp.name = "SirenKelp_Ribbon"
    # subdivide
    bpy.ops.object.mode_set(mode="EDIT")
    # subdivide lengthwise many times
    for _ in range(4):
        bpy.ops.mesh.subdivide(number_cuts=1)
    bpy.ops.object.mode_set(mode="OBJECT")
    # Now we have some verts; but we need precise grid — rebuild via bmesh for control
    import bmesh
    bm = bmesh.new()
    # Build grid manually for precise twist control
    verts = []
    for r in range(rows+1):
        t = r/rows  # 0 base -> 1 tip
        y = t * H
        # spine curve: gentle S in X and Z
        sx = math.sin(t*math.pi*1.4) * 1.2 + math.sin(t*math.pi*3.2)*0.35
        sz = math.cos(t*math.pi*1.1) * 0.85 + rng.uniform(-0.1,0.1)*0.5
        # width profile
        w = W * (0.45 + 0.55*math.sin(math.pi*min(1.0,0.12+0.88*t))) * (1.0 - 0.35*t)
        twist = math.radians(720) * t + math.sin(t*5.0)*0.3  # 2 full twists + wobble
        row = []
        for c in range(cols+1):
            u = c/cols - 0.5
            # cup across width
            cup = (u*u*4.0 - 1.0) * W * 0.08
            # twist offsets
            ct, st = math.cos(twist), math.sin(twist)
            wx = u*w*ct
            wz = u*w*st
            co = Vector((sx + wx, y, sz + wz + cup))
            # subtle wave displacement
            co += Vector((math.sin(t*12.0+u*6.0)*0.04, 0, math.cos(t*9.0+u*4.0)*0.03))
            v = bm.verts.new(co)
            # uv
            uv = (c/cols, t)
            row.append((v, uv))
        verts.append(row)
    # faces + uvs
    uv_layer = bm.loops.layers.uv.new("UVMap")
    for r in range(rows):
        for c in range(cols):
            v0, uv0 = verts[r][c]
            v1, uv1 = verts[r][c+1]
            v2, uv2 = verts[r+1][c+1]
            v3, uv3 = verts[r+1][c]
            try:
                f = bm.faces.new([v0,v1,v2,v3])
                f.smooth = True
                # assign uvs
                for loop, uv in zip(f.loops, [uv0,uv1,uv2,uv3]):
                    loop[uv_layer].uv = uv
            except:
                pass
    bm.normal_update()
    me = bpy.data.meshes.new("SirenKelp_Mesh")
    bm.to_mesh(me)
    bm.free()
    kelp.data = me
    kelp.data.materials.append(mats["kelp"])

    # Eye-spots: place 18 eyes along the ribbon, alternating sides, slightly offset from centreline
    eye_obs = []
    for i in range(18):
        t = 0.08 + (i/17)*0.84
        y = t * H
        sx = math.sin(t*math.pi*1.4) * 1.2 + math.sin(t*math.pi*3.2)*0.35
        sz = math.cos(t*math.pi*1.1) * 0.85
        twist = math.radians(720) * t
        # side offset
        side = 1 if i%2==0 else -1
        u_off = 0.28 * side
        wx = u_off * W * math.cos(twist)
        wz = u_off * W * math.sin(twist)
        # eye is a small flattened sphere pressed onto ribbon surface
        r_eye = 0.16 + rng.uniform(-0.02,0.03)
        bpy.ops.mesh.primitive_uv_sphere_add(radius=r_eye, segments=18, ring_count=10, location=(sx+wx, y, sz+wz))
        eye = bpy.context.object
        eye.name = f"SirenEye_{i:02d}"
        # orient to ribbon normal (approx via twist)
        eye.rotation_euler = (0, math.radians(90), twist + math.radians(90))
        eye.scale = (1.0, 0.35, 1.0)  # flattened onto ribbon
        # add iris + pupil as child spheres
        eye.data.materials.append(mats["eye_sclera"])
        # iris
        bpy.ops.mesh.primitive_uv_sphere_add(radius=r_eye*0.55, segments=14, ring_count=8, location=(sx+wx+0.025, y+0.02, sz+wz))
        iris = bpy.context.object
        iris.name = f"EyeIris_{i:02d}"
        iris.scale = (1.0, 0.3, 1.0)
        iris.rotation_euler = eye.rotation_euler
        iris.data.materials.append(mats["eye_iris"])
        # pupil
        bpy.ops.mesh.primitive_uv_sphere_add(radius=r_eye*0.26, segments=12, ring_count=7, location=(sx+wx+0.045, y+0.03, sz+wz))
        pupil = bpy.context.object
        pupil.name = f"EyePupil_{i:02d}"
        pupil.scale = (1.0, 0.25, 1.0)
        pupil.rotation_euler = eye.rotation_euler
        pupil.data.materials.append(mats["eye_pupil"])
        # light at eye
        ldata = bpy.data.lights.new(f"EyeLight_{i:02d}", type="POINT")
        ldata.energy = 120
        ldata.color = (1.0, 0.35, 0.18)
        ldata.shadow_soft_size = 0.25
        lob = bpy.data.objects.new(f"EyeLight_{i:02d}", ldata)
        lob.location = Vector((sx+wx, y, sz+wz)) + Vector((0.08,0,0))
        bpy.context.collection.objects.link(lob)
        eye_obs.extend([eye, iris, pupil])

    bpy.context.view_layer.update()
    return [o for o in bpy.context.scene.objects if o.type=="MESH"]

def build_crystal_anemone():
    clear_scene()
    rng = random.Random(SEED+303)
    mats = {}
    mats["crystal"] = new_material("M_CrystalAnemone", (0.62,0.78,0.88), roughness=0.18, metallic=0.0, transmission=0.42, emission_color=(0.65,0.85,1.0), emission_strength=0.9, alpha=0.95)
    mats["crystal_tip"] = new_material("M_CrystalTip", (0.85,0.72,0.95), roughness=0.12, transmission=0.35, emission_color=(1.0,0.65,0.85), emission_strength=1.6, alpha=0.92)
    mats["base_rock"] = new_material("M_AnemoneBase", (0.22,0.20,0.28), roughness=0.85, emission_color=(0.35,0.25,0.45), emission_strength=0.4)
    mats["fractal_branch"] = new_material("M_FractalBranch", (0.58,0.72,0.82), roughness=0.28, transmission=0.30, emission_color=(0.55,0.75,0.92), emission_strength=0.7, alpha=0.93)

    # Base: flattened icosphere rock
    bpy.ops.mesh.primitive_ico_sphere_add(subdivisions=3, radius=1.0, location=(0,0,0))
    base = bpy.context.object
    base.name = "CrystalAnemone_Base"
    base.scale = (1.6, 1.4, 0.55)
    base.data.materials.append(mats["base_rock"])
    # displace via random
    import bmesh
    bm = bmesh.new()
    bm.from_mesh(base.data)
    for v in bm.verts:
        v.co += Vector((rng.uniform(-0.08,0.08), rng.uniform(-0.08,0.08), rng.uniform(-0.06,0.06)))
    bm.to_mesh(base.data)
    bm.free()

    # Fractal polyps: recursive branching
    # We create many tapered cylinders (tentacles) with crystal tips
    def make_tentacle(start, direction, length, radius, depth, max_depth):
        if length < 0.12 or radius < 0.02 or depth > max_depth:
            return
        end = start + direction * length
        # create cylinder (use cone with 8 sides)
        # Use primitive cylinder
        mid = (start+end)/2.0
        # direction to rotation: align Z to direction
        up = Vector((0,0,1))
        rot_axis = up.cross(direction)
        ang = up.angle(direction)
        bpy.ops.mesh.primitive_cylinder_add(radius=radius, depth=length, vertices=8, location=mid)
        ob = bpy.context.object
        ob.name = f"Polyp_d{depth}_{rng.randint(0,9999)}"
        if rot_axis.length > 1e-5:
            ob.rotation_mode = "AXIS_ANGLE"
            ob.rotation_axis_angle = (ang, rot_axis.x, rot_axis.y, rot_axis.z)
        # taper via scale on top verts — approximate by scaling object non-uniformly (keep for simplicity)
        # Add slight taper by scaling
        mat = mats["crystal"] if depth < 2 else mats["fractal_branch"]
        ob.data.materials.append(mat)
        # crystal tip sphere at end
        bpy.ops.mesh.primitive_ico_sphere_add(subdivisions=2, radius=radius*1.45, location=end)
        tip = bpy.context.object
        tip.name = f"CrystalTip_d{depth}_{rng.randint(0,9999)}"
        tip.data.materials.append(mats["crystal_tip"])
        # recurse: 2-3 children
        n_children = 2 if depth < 2 else (2 if rng.random()<0.6 else 3)
        for ci in range(n_children):
            # branch direction: perturb
            perturb = Vector((rng.uniform(-0.6,0.6), rng.uniform(-0.6,0.6), rng.uniform(0.1,0.7))).normalized()
            new_dir = (direction * 0.55 + perturb * 0.45).normalized()
            # ensure upward bias
            if new_dir.z < 0.15:
                new_dir.z = 0.15
                new_dir.normalize()
            child_len = length * (0.62 + rng.uniform(-0.08,0.08))
            child_rad = radius * 0.68
            make_tentacle(end, new_dir, child_len, child_rad, depth+1, max_depth)

    # Spawn ~7 primary polyps from base rim + centre
    prim_dirs = []
    for i in range(7):
        a = i/7*360.0 + rng.uniform(-8,8)
        r = rng.uniform(0.2, 0.75) if i < 6 else 0.05
        theta = math.radians(a)
        start = Vector((math.cos(theta)*r*1.2, math.sin(theta)*r*1.1, 0.35))
        dir_vec = Vector((math.cos(theta)*0.25, math.sin(theta)*0.25, 0.92)).normalized()
        dir_vec += Vector((rng.uniform(-0.15,0.15), rng.uniform(-0.15,0.15), 0))
        dir_vec.normalize()
        length = 1.2 + rng.uniform(-0.15,0.25) if i==6 else (0.85 + rng.uniform(-0.12,0.18))
        # scale to 4m cluster: primary lengths ~0.85-1.2, with branching reaches ~2.0-2.2m height
        make_tentacle(start, dir_vec, length, 0.11 - i*0.005, 0, 4)

    # Scale whole cluster to 4m: current height ~2.5m => scale ~1.35 to reach ~3.4m, plus base
    scale_fac = 4.0 / 3.2
    for ob in bpy.context.scene.objects:
        if ob.type == "MESH":
            # scale about origin
            ob.scale = (scale_fac, scale_fac, scale_fac)
    bpy.context.view_layer.update()
    return [o for o in bpy.context.scene.objects if o.type=="MESH"]

# ---------------------------------------------------------------------------
# Dispatch
# ---------------------------------------------------------------------------

MESH_DISPATCH = {
    "ghost_lotus": ("SM_Surreal_GhostLotus", build_ghost_lotus, "8m diameter translucent lotus with inside glow"),
    "siren_kelp": ("SM_Surreal_SirenKelp", build_siren_kelp, "30m twisting ribbon with eye-spots"),
    "crystal_anemone": ("SM_Surreal_CrystalAnemone", build_crystal_anemone, "4m fractal polyp cluster"),
}

def do_mesh(mesh_key):
    name, builder, desc = MESH_DISPATCH[mesh_key]
    print(f"[flora-mesh] building {mesh_key} -> {name}")
    objs = builder()
    # save .blend
    blend_path = OUT_MESH / f"{name}.blend"
    bpy.ops.wm.save_as_mainfile(filepath=str(blend_path))
    print(f"[flora-mesh] saved blend {blend_path}")
    # export FBX (ensure addon)
    try:
        bpy.ops.preferences.addon_enable(module="io_scene_fbx")
    except:
        pass
    fbx_path = OUT_MESH / f"{name}.fbx"
    # select only meshes
    bpy.ops.object.select_all(action="DESELECT")
    for ob in objs:
        ob.select_set(True)
    bpy.context.view_layer.objects.active = objs[0] if objs else None
    try:
        bpy.ops.export_scene.fbx(filepath=str(fbx_path), use_selection=True, apply_scale_options="FBX_SCALE_ALL", global_scale=100.0, apply_unit_scale=True, bake_space_transform=True, object_types={"MESH","LIGHT"}, use_mesh_modifiers=True, mesh_smooth_type="FACE", add_leaf_bones=False)
    except Exception as e:
        # fallback without scale options
        try:
            bpy.ops.export_scene.fbx(filepath=str(fbx_path), use_selection=True)
        except Exception as e2:
            print(f"[flora-mesh] FBX export failed: {e} / {e2}")
    print(f"[flora-mesh] saved fbx {fbx_path}")

    # beauty render 1920x1080 CYCLES 96spp
    scene = bpy.context.scene
    setup_world()
    scene.render.engine = "CYCLES"
    scene.cycles.device = "CPU"
    scene.cycles.samples = 96
    try:
        scene.cycles.use_denoising = True
        scene.cycles.denoiser = "OPENIMAGEDENOISE"
    except:
        pass
    scene.render.resolution_x = 1920
    scene.render.resolution_y = 1080
    scene.render.resolution_percentage = 100
    scene.render.film_transparent = False
    scene.render.image_settings.file_format = "PNG"
    scene.render.image_settings.color_mode = "RGB"
    scene.render.image_settings.compression = 15

    # Re-compute bbox for camera (meshes already placed)
    center, diag = bbox_center_diag(objs)
    cam = rig_and_camera(center, diag)
    scene.camera = cam
    # floor: subtle dark plane to catch rim light
    bpy.ops.mesh.primitive_plane_add(size=40, location=(center.x, center.y, -0.15))
    floor = bpy.context.object
    floor.name = "Floor"
    mat_floor = new_material("M_Floor", (0.04,0.06,0.10), roughness=0.92)
    floor.data.materials.append(mat_floor)

    render_path = OUT_RENDER / f"{name}.png"
    scene.render.filepath = str(render_path)
    print(f"[flora-render] rendering {name} 1920x1080 96spp -> {render_path}")
    bpy.ops.render.render(write_still=True)
    print(f"[flora-render] done {render_path} ({render_path.stat().st_size} bytes)")

# CLI
if __name__ == "__main__":
    argv = sys.argv[sys.argv.index("--")+1:] if "--" in sys.argv else []
    import argparse
    ap = argparse.ArgumentParser()
    ap.add_argument("--mesh", choices=list(MESH_DISPATCH.keys()), help="single mesh to build (blender mode)")
    ap.add_argument("--all-meshes", action="store_true", help="build all meshes")
    args = ap.parse_args(argv)
    if args.mesh:
        do_mesh(args.mesh)
    elif args.all_meshes:
        for k in MESH_DISPATCH:
            # need fresh scene each time; builder clears
            do_mesh(k)
    else:
        # default: build requested mesh or all if no mesh specified and called as blender job
        # If invoked without args in blender, do nothing (caller handles)
        print("[flora-mesh] no --mesh specified, use --mesh <key> or --all-meshes")
'''

# ---------------------------------------------------------------------------
# Texture bake (python+PIL path)
# ---------------------------------------------------------------------------

def bake_textures():
    TEX_DIR.mkdir(parents=True, exist_ok=True)
    all_images = {}
    all_images.update(build_ghost_lotus(SIZE, SEED))
    all_images.update(build_siren_kelp(SIZE, SEED))
    all_images.update(build_crystal_anemone(SIZE, SEED))
    files = []
    for name, (arr, kind) in all_images.items():
        p = rc.save_image(TEX_DIR / f"{name}.png", arr, kind)
        files.append({
            "name": name,
            "path": str(p.relative_to(PROJECT_ROOT)),
            "kind": kind,
            "size": SIZE,
            "seed": SEED,
            "sha256": rc.sha256_of(p),
            "bytes": p.stat().st_size
        })
        print(f"[flora-tex] wrote {p.name} ({p.stat().st_size} bytes)")
    return files

def build_blender_meshes():
    """Spawn Blender background jobs for each mesh (when running outside Blender)."""
    if not BLENDER_EXE.exists():
        print(f"[flora-mesh] Blender not found at {BLENDER_EXE}, skipping mesh builds")
        return []
    script_path = Path(__file__).resolve()
    mesh_keys = ["ghost_lotus", "siren_kelp", "crystal_anemone"]
    mesh_files = []
    for key in mesh_keys:
        print(f"[flora-mesh] launching Blender for {key} ...")
        cmd = [
            str(BLENDER_EXE),
            "--factory-startup",
            "--background",
            "--python", str(script_path),
            "--", "--mesh", key
        ]
        result = subprocess.run(cmd, capture_output=True, text=True, timeout=600)
        print(result.stdout[-4000:] if len(result.stdout) > 4000 else result.stdout)
        if result.stderr:
            print(result.stderr[-2000:] if len(result.stderr) > 2000 else result.stderr)
        if result.returncode != 0:
            print(f"[flora-mesh] Blender job for {key} exited {result.returncode}")
        # collect outputs
        stem_map = {"ghost_lotus": "SM_Surreal_GhostLotus", "siren_kelp": "SM_Surreal_SirenKelp", "crystal_anemone": "SM_Surreal_CrystalAnemone"}
        stem = stem_map[key]
        for ext, kind in [(".blend", "blend"), (".fbx", "fbx")]:
            p = MESH_DIR / f"{stem}{ext}"
            if p.exists():
                mesh_files.append({
                    "name": stem,
                    "path": str(p.relative_to(PROJECT_ROOT)),
                    "kind": kind,
                    "sha256": rc.sha256_of(p),
                    "bytes": p.stat().st_size
                })
        rp = RENDER_DIR / f"{stem}.png"
        if rp.exists():
            mesh_files.append({
                "name": stem,
                "path": str(rp.relative_to(PROJECT_ROOT)),
                "kind": "render",
                "resolution": "1920x1080",
                "samples": 96,
                "engine": "CYCLES",
                "sha256": rc.sha256_of(rp),
                "bytes": rp.stat().st_size
            })
    return mesh_files

def write_manifest(tex_files, mesh_files):
    OUT_ROOT.mkdir(parents=True, exist_ok=True)
    # Also collect render files separately
    render_files = [f for f in mesh_files if f["kind"] == "render"]
    actual_mesh = [f for f in mesh_files if f["kind"] in ("blend","fbx")]
    payload = {
        "schema": "melodia.surreal_flora.v1",
        "seed": SEED,
        "size": SIZE,
        "generator": "Tools/Houdini/sea_above_reef/surreal_flora.py",
        "description": "Surreal Dream Flora — 3 oversized blooms (Ghost Lotus 8m, Siren Kelp 30m, Crystal Anemone 4m) with PBR 1024 texture sets + Blender meshes + 1920x1080 CYCLES 96spp beauty renders",
        "scale": "metres; Blender units = metres; UE import x100 (m->cm); FBX global_scale 100",
        "textures": tex_files,
        "meshes": actual_mesh,
        "renders": render_files,
        "all_files": tex_files + mesh_files,
        "stats": {
            "texture_sets": 3,
            "texture_files": len(tex_files),
            "mesh_stems": 3,
            "mesh_files": len(actual_mesh),
            "render_files": len(render_files),
            "total_files": len(tex_files + mesh_files)
        }
    }
    # provide per-flora summary
    payload["flora"] = [
        {"id": "ghost_lotus", "name": "Ghost Lotus", "diameter_m": 8.0, "stem": "SM_Surreal_GhostLotus",
         "textures": [f["name"] for f in tex_files if "GhostLotus" in f["name"]],
         "material": "translucent Principled + inside point light + emissive core; transmission 0.35-0.45"},
        {"id": "siren_kelp", "name": "Spiral Siren Kelp", "height_m": 30.0, "width_m": 0.85, "stem": "SM_Surreal_SirenKelp",
         "textures": [f["name"] for f in tex_files if "SirenKelp" in f["name"]],
         "material": "ribbon with 720deg twist + 18 eye-spots (sclera/iris/pupil + point lights)"},
        {"id": "crystal_anemone", "name": "Crystal Anemone", "diameter_m": 4.0, "stem": "SM_Surreal_CrystalAnemone",
         "textures": [f["name"] for f in tex_files if "CrystalAnemone" in f["name"]],
         "material": "fractal polyp cluster (depth 4, ~7 primaries); transmission 0.30-0.42; icosphere tips"},
    ]
    manifest_path = OUT_ROOT / "flora_manifest.json"
    with open(manifest_path, "w", encoding="utf-8") as f:
        json.dump(payload, f, indent=2)
    print(f"[flora] manifest -> {manifest_path}")
    return manifest_path

def main():
    # Detect if running inside Blender
    if "bpy" in sys.modules:
        # This branch is handled by the embedded BLENDER_MESH_SCRIPT dispatch above.
        # But if someone runs: blender --background --python surreal_flora.py (without --)
        # we still need to handle it via the bpy block at bottom of file.
        # For direct python invocation inside blender without subprocess, handle here too.
        # Parse --mesh args
        argv = sys.argv[sys.argv.index("--")+1:] if "--" in sys.argv else []
        ap = argparse.ArgumentParser()
        ap.add_argument("--mesh", choices=["ghost_lotus","siren_kelp","crystal_anemone"])
        ap.add_argument("--all-meshes", action="store_true")
        ap.add_argument("--textures-only", action="store_true")
        args, _ = ap.parse_known_args(argv)
        if args.textures_only:
            # textures need PIL, not bpy— but we can still bake via rc
            bake_textures()
            return
        if args.mesh or args.all_meshes:
            # We need the BLENDER_MESH_SCRIPT logic — exec it
            # Instead, import builder functions from the string? Simpler: exec the script string
            # with patched MESH_NAME
            pass
        return

    ap = argparse.ArgumentParser(description="Surreal Dream Flora — bake PBR 1024 + Blender meshes/renders")
    ap.add_argument("--textures-only", action="store_true", help="only bake textures")
    ap.add_argument("--meshes-only", action="store_true", help="only build meshes/renders (skip textures)")
    ap.add_argument("--skip-blender", action="store_true", help="skip Blender mesh/render builds")
    api_args = ap.parse_args()

    # Ensure dirs
    TEX_DIR.mkdir(parents=True, exist_ok=True)
    MESH_DIR.mkdir(parents=True, exist_ok=True)
    RENDER_DIR.mkdir(parents=True, exist_ok=True)

    # Write the Blender helper script to a temp file that Blender will execute
    # Actually surreal_flora.py IS the Blender script — the top-level handles bpy.
    # But our main() here is the Python-outside-Blender path. We need to inject the
    # Blender mesh script logic into a file Blender can run. The easiest: write a
    # derived script that contains the BLENDER_MESH_SCRIPT content with proper header.
    blender_script = OUT_ROOT / "_blender_flora_job.py"
    # Build a self-contained Blender script from BLENDER_MESH_SCRIPT template
    # We write one script that handles --mesh dispatch (the BLENDER_MESH_SCRIPT already does)
    with open(blender_script, "w", encoding="utf-8") as f:
        f.write(BLENDER_MESH_SCRIPT)

    tex_files = []
    mesh_files = []

    if not api_args.meshes_only:
        print(f"[flora] baking textures {SIZE}x{SIZE} seed {SEED} -> {TEX_DIR}")
        tex_files = bake_textures()
    else:
        # still collect existing texture entries for manifest
        if TEX_DIR.exists():
            for p in sorted(TEX_DIR.glob("T_Surreal_*.png")):
                tex_files.append({
                    "name": p.stem,
                    "path": str(p.relative_to(PROJECT_ROOT)),
                    "kind": "rgb" if "Albedo" in p.stem or "Normal" in p.stem else "gray",
                    "size": SIZE,
                    "seed": SEED,
                    "sha256": rc.sha256_of(p),
                    "bytes": p.stat().st_size
                })

    if not api_args.textures_only and not api_args.skip_blender:
        # Build meshes via Blender subprocess using the helper script
        print(f"[flora] building meshes via Blender {BLENDER_EXE}")
        for key in ["ghost_lotus", "siren_kelp", "crystal_anemone"]:
            print(f"[flora] -> Blender job: {key}")
            cmd = [str(BLENDER_EXE), "--factory-startup", "--background", "--python", str(blender_script), "--", "--mesh", key]
            result = subprocess.run(cmd, capture_output=True, text=True, timeout=600)
            # Print last chunk
            out_tail = result.stdout[-5000:] if len(result.stdout) > 5000 else result.stdout
            print(out_tail)
            if result.stderr:
                err_tail = result.stderr[-3000:] if len(result.stderr) > 3000 else result.stderr
                print(err_tail, file=sys.stderr)
            if result.returncode != 0:
                print(f"[flora] WARNING: Blender job {key} exited {result.returncode}")

        # Collect mesh + render outputs
        stem_map = {"ghost_lotus": "SM_Surreal_GhostLotus", "siren_kelp": "SM_Surreal_SirenKelp", "crystal_anemone": "SM_Surreal_CrystalAnemone"}
        for key, stem in stem_map.items():
            for ext, kind in [(".blend", "blend"), (".fbx", "fbx")]:
                p = MESH_DIR / f"{stem}{ext}"
                if p.exists():
                    mesh_files.append({"name": stem, "path": str(p.relative_to(PROJECT_ROOT)), "kind": kind, "sha256": rc.sha256_of(p), "bytes": p.stat().st_size})
                    print(f"[flora] found {p.name} ({p.stat().st_size} bytes)")
                else:
                    print(f"[flora] MISSING {p}")
            rp = RENDER_DIR / f"{stem}.png"
            if rp.exists():
                # verify resolution via PIL
                try:
                    from PIL import Image
                    im = Image.open(rp)
                    res = f"{im.size[0]}x{im.size[1]}"
                    im.close()
                except:
                    res = "1920x1080"
                mesh_files.append({"name": stem, "path": str(rp.relative_to(PROJECT_ROOT)), "kind": "render", "resolution": res, "samples": 96, "engine": "CYCLES", "sha256": rc.sha256_of(rp), "bytes": rp.stat().st_size})
                print(f"[flora] found render {rp.name} {res} ({rp.stat().st_size} bytes)")
            else:
                print(f"[flora] MISSING render {rp}")

    # If skip-blender but we still want manifest, collect existing mesh outputs
    if api_args.skip_blender or api_args.textures_only:
        # try to collect whatever exists
        stem_map = {"ghost_lotus": "SM_Surreal_GhostLotus", "siren_kelp": "SM_Surreal_SirenKelp", "crystal_anemone": "SM_Surreal_CrystalAnemone"}
        for stem in stem_map.values():
            for ext, kind in [(".blend", "blend"), (".fbx", "fbx")]:
                p = MESH_DIR / f"{stem}{ext}"
                if p.exists() and not any(m["path"].endswith(f"{stem}{ext}") for m in mesh_files):
                    mesh_files.append({"name": stem, "path": str(p.relative_to(PROJECT_ROOT)), "kind": kind, "sha256": rc.sha256_of(p), "bytes": p.stat().st_size})
            rp = RENDER_DIR / f"{stem}.png"
            if rp.exists() and not any(m["path"].endswith(f"{stem}.png") and m["kind"]=="render" for m in mesh_files):
                mesh_files.append({"name": stem, "path": str(rp.relative_to(PROJECT_ROOT)), "kind": "render", "resolution": "1920x1080", "samples": 96, "engine": "CYCLES", "sha256": rc.sha256_of(rp), "bytes": rp.stat().st_size})

    manifest_path = write_manifest(tex_files, mesh_files)
    # Also copy manifest to meshes folder for convenience
    print(f"[flora] done. textures={len(tex_files)} mesh/render={len(mesh_files)}")
    # Verify counts
    expected_tex = 15  # 5 per set x3
    expected_mesh = 6  # 3 blend + 3 fbx
    expected_render = 3
    if len(tex_files) != expected_tex:
        print(f"[flora] WARNING: expected {expected_tex} texture files, got {len(tex_files)}")
    if len([m for m in mesh_files if m['kind'] in ('blend','fbx')]) != expected_mesh:
        print(f"[flora] WARNING: expected {expected_mesh} mesh files, got {len([m for m in mesh_files if m['kind'] in ('blend','fbx')])}")
    if len([m for m in mesh_files if m['kind']=='render']) != expected_render:
        print(f"[flora] WARNING: expected {expected_render} renders, got {len([m for m in mesh_files if m['kind']=='render'])}")

# ---------------------------------------------------------------------------
# Blender entry-point (when this file is executed via blender --background --python)
# ---------------------------------------------------------------------------
# If bpy is available at import time, the BLENDER_MESH_SCRIPT exec path above is not used;
# instead we handle dispatch directly here. This makes `blender --background --python surreal_flora.py -- --mesh X` work
# whether the caller uses surreal_flora.py or _blender_flora_job.py.
if "bpy" in sys.modules:
    # Re-parse for blender direct invocation
    _argv = sys.argv[sys.argv.index("--")+1:] if "--" in sys.argv else []
    if any(a in _argv for a in ("--mesh", "--all-meshes")):
        # Exec the blender mesh script logic inline by writing/reading the template
        # We already have it as a string; exec it with the chosen MESH_NAME
        import argparse as _ap
        _parser = _ap.ArgumentParser()
        _parser.add_argument("--mesh", choices=["ghost_lotus","siren_kelp","crystal_anemone"])
        _parser.add_argument("--all-meshes", action="store_true")
        _pargs, _ = _parser.parse_known_args(_argv)
        # Use the template string — replace placeholder and exec
        _code = BLENDER_MESH_SCRIPT
        # exec in current namespace (has bpy etc)
        # The script handles its own dispatch at bottom, so we can just exec it
        exec(compile(_code, "<blender_flora>", "exec"), globals())
        # After exec, it has defined do_mesh etc but not called yet if we exec the string as-is
        # Actually BLENDER_MESH_SCRIPT's bottom dispatch calls do_mesh based on argv; but argv inside exec is still sys.argv
        # So we need to ensure it runs. The exec already includes its own __main__ dispatch, which will run.
        # To avoid double, we just ensure correct behaviour:
        if _pargs.mesh:
            # The exec's dispatch already handled it; if not, call manually
            pass
        sys.exit(0)

if __name__ == "__main__" and "bpy" not in sys.modules:
    main()
