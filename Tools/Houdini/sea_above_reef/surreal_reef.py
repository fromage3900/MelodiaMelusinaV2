"""Surreal Reef Wonders — impossible coral architecture.

Bakes 3 tilable 1024 PBR texture sets (void coral, molten shell, abyss sponge)
+ Blender builder for 3 surreal reef meshes:

  1) Leaning Cathedral Coral 18m arches (sailable)
  2) Floating Brain Atoll honeycomb 12m inverted
  3) Glass Spire Forest 20m transparent spires with internal filaments

Each mesh gets a PBR material with emission + transmission.

Outputs:
  Textures (Saved/Audit/surreal_sweep/reef/textures/):
    T_Surreal_VoidCoral_Albedo.png       sRGB
    T_Surreal_VoidCoral_Normal.png       data OpenGL Y+
    T_Surreal_VoidCoral_Emissive.png     data
    T_Surreal_MoltenShell_Albedo.png     sRGB
    T_Surreal_MoltenShell_Normal.png     data
    T_Surreal_MoltenShell_Emissive.png   data
    T_Surreal_AbyssSponge_Albedo.png     sRGB
    T_Surreal_AbyssSponge_Normal.png     data
    T_Surreal_AbyssSponge_Emissive.png   data
    _SurrealReef_ContactSheet.png
  Meshes + beauty (Saved/Audit/surreal_sweep/reef/):
    surreal_reef.blend
    SM_Surreal_CathedralCoral.fbx
    SM_Surreal_BrainAtoll.fbx
    SM_Surreal_GlassSpireForest.fbx
    beauty_*.png (Cycles renders)
    reef_manifest.json

Run textures:  python Tools/Houdini/sea_above_reef/surreal_reef.py
Run meshes:    \"C:/Program Files/Blender Foundation/Blender 5.2/blender.exe\" --background --python Tools/Houdini/sea_above_reef/surreal_reef.py
Run all:       python Tools/Houdini/sea_above_reef/surreal_reef.py --all
               (textures in place, then spawns Blender headless)

Offline only. Deterministic. Tileable via lattice-periodic noise.
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
OUT_ROOT = PROJECT_ROOT / "Saved" / "Audit" / "surreal_sweep" / "reef"
TEX_DIR = OUT_ROOT / "textures"
SIZE = 1024
SEED = 20260828

# try reef_common, fallback to local impl if not importable in blender bundle
try:
    sys.path.insert(0, str(Path(__file__).resolve().parent))
    import reef_common as rc
    HAS_RC = True
except Exception:
    HAS_RC = False

IS_BLENDER = "bpy" in sys.modules

# ---------------------------------------------------------------------------
# Minimal periodic helpers if reef_common unavailable (duplicated for blender)
# ---------------------------------------------------------------------------
def _periodic_value_noise(size, period, rng):
    size = int(size); period = int(period)
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
    sx = tx*tx*(3-2*tx); sy = ty*ty*(3-2*ty)
    v00 = lat[y0, x0]; v01 = lat[y0, x1]; v10 = lat[y1, x0]; v11 = lat[y1, x1]
    top = v00 + (v01 - v00)*sx
    bot = v10 + (v11 - v10)*sx
    return top + (bot - top)*sy

def _fbm(size, base_period, octaves, rng, gain=0.5):
    acc = np.zeros((size, size), np.float32); amp=1.0; total=0.0; period=int(base_period)
    for _ in range(int(octaves)):
        acc += amp*_periodic_value_noise(size, period, rng)
        total+=amp; amp*=gain; period*=2
        if period>size: break
    return acc/max(total,1e-6)

def _voronoi_f1(size, period, jitter, rng):
    size=int(size); period=int(period); cell=size/period
    jr=rng.random((period,period,2)).astype(np.float32)*jitter+(1-jitter)*0.5
    ys,xs=np.mgrid[0:size,0:size].astype(np.float32)
    fx=xs/cell; fy=ys/cell
    cx=np.floor(fx).astype(np.int32); cy=np.floor(fy).astype(np.int32)
    best=np.full((size,size),1e9,dtype=np.float32)
    for oy in (-1,0,1):
        for ox in (-1,0,1):
            gx=(cx+ox)%period; gy=(cy+oy)%period
            px=(gx+jr[gy,gx,0])*cell; py=(gy+jr[gy,gx,1])*cell
            dx=px-xs; dy=py-ys
            dx=(dx+size*0.5)%size - size*0.5
            dy=(dy+size*0.5)%size - size*0.5
            d=np.sqrt(dx*dx+dy*dy)
            best=np.minimum(best,d)
    return best/cell

def _normal_from_height(h, strength=2.0):
    dx=(np.roll(h,-1,axis=1)-np.roll(h,1,axis=1))*0.5
    dy=(np.roll(h,-1,axis=0)-np.roll(h,1,axis=0))*0.5
    nx=-dx*strength; ny=-dy*strength; nz=np.ones_like(h)
    ln=np.sqrt(nx*nx+ny*ny+nz*nz)
    return np.stack([nx/ln*0.5+0.5, ny/ln*0.5+0.5, nz/ln*0.5+0.5],axis=-1).astype(np.float32)

def _save_image(path, arr, kind):
    """Save float 0..1 as PNG. Prefer reef_common if available, else PIL/bpy."""
    if HAS_RC:
        return rc.save_image(path, arr, kind)
    arr=np.clip(np.asarray(arr,np.float32),0,1)
    path=Path(path); path.parent.mkdir(parents=True,exist_ok=True)
    if IS_BLENDER:
        import bpy
        h,w=arr.shape[:2]
        if kind=="gray":
            rgba=np.dstack([arr,arr,arr,np.ones_like(arr)])
        elif kind=="rgb":
            rgba=np.dstack([arr,np.ones_like(arr[...,:1])])
        else:
            rgba=arr
        rgba=rgba[::-1]
        name=path.stem
        if name in bpy.data.images:
            bpy.data.images.remove(bpy.data.images[name])
        img=bpy.data.images.new(name,width=w,height=h,alpha=True)
        try: img.colorspace_settings.name="Non-Color"
        except: pass
        flat=rgba.reshape(-1).astype(np.float32)
        try: img.pixels.foreach_set(flat)
        except: img.pixels[:]=flat.tolist()
        img.filepath_raw=str(path); img.file_format="PNG"; img.save()
        bpy.data.images.remove(img)
        return path
    else:
        from PIL import Image
        mode={"gray":"L","rgb":"RGB","rgba":"RGBA"}[kind]
        data=(arr*255).round().astype(np.uint8)
        Image.fromarray(data,mode=mode).save(str(path),format="PNG",optimize=False)
        return path

def _sha256(p):
    h=hashlib.sha256()
    with open(p,"rb") as f:
        for c in iter(lambda: f.read(1<<16),b""): h.update(c)
    return h.hexdigest()

# ---------------------------------------------------------------------------
# Texture builders
# ---------------------------------------------------------------------------
VOID_BASE = np.array([14, 10, 28], np.float32)/255.0
VOID_RIM  = np.array([38, 28, 66], np.float32)/255.0
VOID_VEIN = np.array([80, 240, 255], np.float32)/255.0
VOID_VEIN2= np.array([255, 90, 200], np.float32)/255.0

MOLTEN_BASE = np.array([42, 28, 22], np.float32)/255.0
MOLTEN_PEARL= np.array([235, 210, 185], np.float32)/255.0
MOLTEN_LAVA = np.array([255, 110, 22], np.float32)/255.0
MOLTEN_LAVA2= np.array([255, 220, 80], np.float32)/255.0

SPONGE_BASE = np.array([18, 24, 30], np.float32)/255.0
SPONGE_BODY = np.array([62, 78, 72], np.float32)/255.0
SPONGE_GLOW = np.array([255, 180, 60], np.float32)/255.0

def build_void_coral(seed, size):
    rng=np.random.default_rng(seed)
    base = _fbm(size, 8, 4, rng, 0.55)
    base = (base-base.min())/(base.max()-base.min())
    # vein network: sharpened voronoi edges
    f1 = _voronoi_f1(size, 32, 0.85, np.random.default_rng(seed+11))
    # distance to edge: voronoi edge is where F1 gradient high -> approximate with F1 ridge
    # second voronoi at different period for branching veins
    f1b = _voronoi_f1(size, 16, 0.9, np.random.default_rng(seed+12))
    veins = np.clip(1.0 - np.abs(f1 - f1b)*8.0, 0, 1) ** 1.8
    # thin vein mask
    vein_thin = np.clip(1.0 - f1*14.0, 0, 1)**1.2 * 0.6 + veins*0.4
    vein_thin = np.clip(vein_thin,0,1)
    # pores on coral surface
    f_pore = _voronoi_f1(size, 96, 0.7, np.random.default_rng(seed+13))
    pores = np.clip(1.0 - f_pore*5.0, 0, 1)**1.5
    # height
    height = 0.4*base + 0.35*pores + 0.25*vein_thin
    # albedo: dark void base, slightly lifted by pores
    albedo = VOID_BASE[None,None,:]*(1 - base[...,None]*0.3) + VOID_RIM[None,None,:]*(base[...,None]*0.5)
    albedo = np.clip(albedo + pores[...,None]*0.08, 0, 1)
    # vein tint alternation
    tint = _periodic_value_noise(size, 4, np.random.default_rng(seed+14))
    vein_col = VOID_VEIN[None,None,:]*(1-tint[...,None]) + VOID_VEIN2[None,None,:]*tint[...,None]
    albedo = albedo*(1 - 0.85*vein_thin[...,None]) + vein_col*0.85*vein_thin[...,None]
    albedo = np.clip(albedo,0,1)
    emissive = np.clip(vein_thin*1.2 + pores*0.35, 0, 1) **1.1
    normal = _normal_from_height(height, strength=3.0)
    return albedo, normal, emissive, height

def build_molten_shell(seed, size):
    rng=np.random.default_rng(seed)
    # pearlescent mottling
    pearl = _fbm(size, 16, 4, rng, 0.55)
    pearl = (pearl-pearl.min())/(pearl.max()-pearl.min())
    # cracks: voronoi edge network + fbm ridges
    f1 = _voronoi_f1(size, 24, 0.8, np.random.default_rng(seed+21))
    crack = np.clip(1.0 - f1*3.2, 0, 1)**0.9
    # sharpen cracks
    crack = np.clip((crack-0.35)/0.65,0,1)**1.4
    # secondary fine cracks
    ridge = _fbm(size, 64, 2, np.random.default_rng(seed+22), 0.6)
    fine = np.clip(1.0 - np.abs(ridge-0.5)*10,0,1)**2
    cracks = np.clip(crack*0.85 + fine*0.25,0,1)
    # shell undulation height
    height = 0.45*pearl + 0.35*(1-cracks) + 0.2*_fbm(size, 32, 2, np.random.default_rng(seed+23),0.5)
    # albedo: pearlescent base darkened in cracks, cracks glow internally
    base_col = MOLTEN_PEARL[None,None,:]*(0.6+0.4*pearl[...,None])*(1-0.5*cracks[...,None]) + MOLTEN_BASE[None,None,:]*(0.5*cracks[...,None])
    # iridescent shift
    hue_shift = _periodic_value_noise(size, 8, np.random.default_rng(seed+24))
    base_col[...,0] += (hue_shift-0.5)*0.08
    base_col = np.clip(base_col,0,1)
    # emissive: lava in cracks with gradient
    lava_mix = _periodic_value_noise(size, 2, np.random.default_rng(seed+25))
    lava_col = MOLTEN_LAVA[None,None,:]*(1-lava_mix[...,None]) + MOLTEN_LAVA2[None,None,:]*lava_mix[...,None]
    emissive = np.clip(cracks*1.15,0,1)**0.95
    albedo = np.clip(base_col + lava_col*0.0,0,1)  # albedo stays pearl; lava via emissive
    normal = _normal_from_height(height, strength=2.4)
    return albedo, normal, emissive, height, lava_col

def build_abyss_sponge(seed, size):
    rng=np.random.default_rng(seed)
    # honeycomb pores large
    f1 = _voronoi_f1(size, 20, 0.85, np.random.default_rng(seed+31))
    pores = np.clip(1.0 - f1*2.2, 0, 1) **0.85
    # wall thickness
    wall = 1.0 - pores
    # smaller sponge holes inside walls
    f_small = _voronoi_f1(size, 80, 0.7, np.random.default_rng(seed+32))
    small = np.clip(1.0 - f_small*4.0,0,1)**1.3 * wall
    # organic fibrous noise
    fib = _fbm(size, 32, 3, rng, 0.5)
    height = 0.5*wall + 0.3*(1-f_small) + 0.2*fib
    height = np.clip(height,0,1)
    # albedo: dark abyssal walls, sponge body, fibrous variation
    albedo = SPONGE_BASE[None,None,:]*(1-wall[...,None]*0.5) + SPONGE_BODY[None,None,:]*(wall[...,None]*0.7 + fib[...,None]*0.15)
    albedo = np.clip(albedo*(1 - small[...,None]*0.35) + SPONGE_BODY[None,None,:]*small[...,None]*0.2,0,1)
    # internal glow from deep pores (amber pits)
    depth = pores * (0.5+0.5*fib)
    emissive = np.clip(depth**1.2 * 0.95 + small*0.3,0,1)
    normal = _normal_from_height(height, strength=2.8)
    return albedo, normal, emissive, height

def bake_textures(seed=SEED, size=SIZE):
    TEX_DIR.mkdir(parents=True, exist_ok=True)
    OUT_ROOT.mkdir(parents=True, exist_ok=True)
    files=[]
    # Void Coral
    alb, nrm, emi, _h = build_void_coral(seed, size)
    for name, arr, kind in [
        ("T_Surreal_VoidCoral_Albedo", alb, "rgb"),
        ("T_Surreal_VoidCoral_Normal", nrm, "rgb"),
        ("T_Surreal_VoidCoral_Emissive", emi, "gray"),
    ]:
        p=_save_image(TEX_DIR/f"{name}.png", arr, kind)
        files.append({"name":name,"path":str(p.relative_to(PROJECT_ROOT)).replace("\\","/"),"kind":kind,"size":size,"seed":seed})
        print(f"[surreal-reef] wrote {p.name}")
    # Molten Shell
    alb2, nrm2, emi2, _h2, _lava = build_molten_shell(seed+100, size)
    for name, arr, kind in [
        ("T_Surreal_MoltenShell_Albedo", alb2, "rgb"),
        ("T_Surreal_MoltenShell_Normal", nrm2, "rgb"),
        ("T_Surreal_MoltenShell_Emissive", emi2, "gray"),
    ]:
        p=_save_image(TEX_DIR/f"{name}.png", arr, kind)
        files.append({"name":name,"path":str(p.relative_to(PROJECT_ROOT)).replace("\\","/"),"kind":kind,"size":size,"seed":seed})
        print(f"[surreal-reef] wrote {p.name}")
    # Abyss Sponge
    alb3, nrm3, emi3, _h3 = build_abyss_sponge(seed+200, size)
    for name, arr, kind in [
        ("T_Surreal_AbyssSponge_Albedo", alb3, "rgb"),
        ("T_Surreal_AbyssSponge_Normal", nrm3, "rgb"),
        ("T_Surreal_AbyssSponge_Emissive", emi3, "gray"),
    ]:
        p=_save_image(TEX_DIR/f"{name}.png", arr, kind)
        files.append({"name":name,"path":str(p.relative_to(PROJECT_ROOT)).replace("\\","/"),"kind":kind,"size":size,"seed":seed})
        print(f"[surreal-reef] wrote {p.name}")

    # Contact sheet
    try:
        from PIL import Image
        sheet = Image.new("RGB", (size*3, size*3), (18, 20, 24))
        all_albs = [alb, alb2, alb3]
        all_emis = [emi, emi2, emi3]
        all_nrms = [nrm, nrm2, nrm3]
        labels = ["VoidCoral","MoltenShell","AbyssSponge"]
        for col, (a, e, n) in enumerate(zip(all_albs, all_emis, all_nrms)):
            # row0 albedo
            im_a = Image.fromarray((np.clip(a,0,1)*255).round().astype(np.uint8), "RGB")
            sheet.paste(im_a, (col*size, 0))
            # row1 normal
            im_n = Image.fromarray((np.clip(n,0,1)*255).round().astype(np.uint8), "RGB")
            sheet.paste(im_n, (col*size, size))
            # row2 emissive
            eg = np.clip(e,0,1)
            im_e = Image.fromarray((np.dstack([eg,eg,eg])*255).round().astype(np.uint8), "RGB")
            sheet.paste(im_e, (col*size, size*2))
        sheet_path = TEX_DIR / "_SurrealReef_ContactSheet.png"
        sheet.save(str(sheet_path), format="PNG")
        print(f"[surreal-reef] wrote {sheet_path.name}")
        files.append({"name":"_SurrealReef_ContactSheet","path":str(sheet_path.relative_to(PROJECT_ROOT)).replace("\\","/"),"kind":"contact_sheet","size":size,"seed":seed})
    except Exception as e:
        print(f"[surreal-reef] contact sheet failed: {e}")

    return files

# ---------------------------------------------------------------------------
# Blender mesh builders
# ---------------------------------------------------------------------------
def _clear_scene():
    import bpy
    bpy.ops.wm.read_factory_settings(use_empty=True)

def _make_pbr_mat(name, albedo_path=None, normal_path=None, emissive_path=None,
                   base_color=(0.8,0.8,0.8,1), emission_color=(0,0.2,0.4,1), emission_strength=2.0,
                   transmission=0.0, ior=1.45, roughness=0.45, metallic=0.0, alpha=1.0):
    import bpy
    mat = bpy.data.materials.new(name=name)
    mat.use_nodes = True
    nt = mat.node_tree
    nt.nodes.clear()
    out = nt.nodes.new("ShaderNodeOutputMaterial")
    out.location = (600, 0)
    bsdf = nt.nodes.new("ShaderNodeBsdfPrincipled")
    bsdf.location = (0, 0)
    # principled settings
    bsdf.inputs["Base Color"].default_value = base_color
    bsdf.inputs["Roughness"].default_value = roughness
    bsdf.inputs["Metallic"].default_value = metallic
    bsdf.inputs["IOR"].default_value = ior
    if "Transmission Weight" in bsdf.inputs:
        bsdf.inputs["Transmission Weight"].default_value = transmission
    elif "Transmission" in bsdf.inputs:
        bsdf.inputs["Transmission"].default_value = transmission
    if alpha < 1.0:
        bsdf.inputs["Alpha"].default_value = alpha
        mat.blend_method = 'BLEND'
    # Emission
    if "Emission Color" in bsdf.inputs:
        bsdf.inputs["Emission Color"].default_value = emission_color
    if "Emission Strength" in bsdf.inputs:
        bsdf.inputs["Emission Strength"].default_value = emission_strength
    elif "Emission" in bsdf.inputs:
        bsdf.inputs["Emission"].default_value = emission_color[:3] + (1,)
    nt.links.new(bsdf.outputs["BSDF"], out.inputs["Surface"])

    x = -400
    # albedo texture
    if albedo_path and Path(albedo_path).exists():
        tex = nt.nodes.new("ShaderNodeTexImage")
        tex.location = (x, 200)
        try:
            img = bpy.data.images.load(str(albedo_path), check_existing=True)
            img.colorspace_settings.name = 'sRGB'
            tex.image = img
            nt.links.new(tex.outputs["Color"], bsdf.inputs["Base Color"])
        except Exception as e:
            print(f"[mat] albedo load fail {albedo_path}: {e}")
    # normal map
    if normal_path and Path(normal_path).exists():
        texn = nt.nodes.new("ShaderNodeTexImage")
        texn.location = (x, -100)
        nm = nt.nodes.new("ShaderNodeNormalMap")
        nm.location = (-150, -150)
        try:
            img = bpy.data.images.load(str(normal_path), check_existing=True)
            img.colorspace_settings.name = 'Non-Color'
            texn.image = img
            nt.links.new(texn.outputs["Color"], nm.inputs["Color"])
            nt.links.new(nm.outputs["Normal"], bsdf.inputs["Normal"])
        except Exception as e:
            print(f"[mat] normal load fail: {e}")
    # emissive texture -> emission color/strength
    if emissive_path and Path(emissive_path).exists():
        texe = nt.nodes.new("ShaderNodeTexImage")
        texe.location = (x, -350)
        try:
            img = bpy.data.images.load(str(emissive_path), check_existing=True)
            img.colorspace_settings.name = 'Non-Color'
            texe.image = img
            # multiply emission color
            mix = nt.nodes.new("ShaderNodeMixRGB")
            mix.blend_type = 'MULTIPLY'
            mix.location = (-150, -350)
            mix.inputs["Color1"].default_value = emission_color
            mix.inputs["Fac"].default_value = 1.0
            nt.links.new(texe.outputs["Color"], mix.inputs["Color2"])
            if "Emission Color" in bsdf.inputs:
                nt.links.new(mix.outputs["Color"], bsdf.inputs["Emission Color"])
        except Exception as e:
            print(f"[mat] emissive load fail: {e}")
    return mat

def build_cathedral_coral():
    """Leaning Cathedral Coral 18m arches sailable (3 grand arches)."""
    import bpy, bmesh
    from mathutils import Vector
    import math, random
    rng = random.Random(SEED)
    # Create collection
    col = bpy.data.collections.new("CathedralCoral")
    bpy.context.scene.collection.children.link(col)

    mats = {}
    # material with void coral textures
    mats['coral'] = _make_pbr_mat("M_Surreal_VoidCoral",
        albedo_path=TEX_DIR/"T_Surreal_VoidCoral_Albedo.png",
        normal_path=TEX_DIR/"T_Surreal_VoidCoral_Normal.png",
        emissive_path=TEX_DIR/"T_Surreal_VoidCoral_Emissive.png",
        base_color=(0.18,0.14,0.28,1), emission_color=(0.2,0.9,1.0,1), emission_strength=3.5,
        transmission=0.15, roughness=0.6, metallic=0.0)

    # Build 3 leaning arches. Each is a bent tube with varying radius.
    # Arch dimensions: span ~8-10m, height 18m, thickness 0.6-1.1m, leaning 12-18 deg
    for idx in range(3):
        span = 7.5 + rng.uniform(0, 2.5)
        height = 18.0
        lean_deg = 12 + idx*3 + rng.uniform(-2,2)
        lean = math.radians(lean_deg)
        x_off = (idx - 1) * 6.0 + rng.uniform(-0.6, 0.6)
        z_off = rng.uniform(-1.5, 1.5)

        # arch centerline: half-ellipse leaning
        steps = 28
        pts = []
        for i in range(steps+1):
            t = i/steps
            # semi-ellipse x = cos, y = sin
            ang = math.pi * t
            # local arch coords before lean
            lx = math.cos(ang) * (span*0.5)
            ly = math.sin(ang) * height
            # lean: rotate around Z? actually lean in X direction
            # rotate point around origin by lean angle (tilt toward +X)
            rx = lx*math.cos(lean) - ly*math.sin(lean)
            ry = lx*math.sin(lean) + ly*math.cos(lean)
            pts.append(Vector((x_off + rx, ry, z_off + math.sin(t*math.pi*2)*0.3)))

        # create curve -> mesh tube
        curve = bpy.data.curves.new(f"CathedralArch_{idx}", type='CURVE')
        curve.dimensions = '3D'
        curve.resolution_u = 12
        curve.bevel_depth = 0.0
        spline = curve.splines.new('BEZIER')
        spline.bezier_points.add(len(pts)-1)
        for i, p in enumerate(pts):
            bp = spline.bezier_points[i]
            bp.co = p
            bp.handle_left_type = 'AUTO'
            bp.handle_right_type = 'AUTO'

        # tube profile via bevel
        curve.bevel_depth = 0.55 + rng.uniform(-0.08, 0.12)
        curve.bevel_resolution = 8
        # taper: thinner at apex
        # use map via radius? set per point radius
        for i, bp in enumerate(spline.bezier_points):
            t = i/steps
            taper = 1.0 - 0.25*math.sin(t*math.pi)
            bp.radius = taper

        obj = bpy.data.objects.new(f"SM_Surreal_CathedralCoral_Arch{idx}", curve)
        # convert to mesh for FBX stability
        bpy.context.scene.collection.objects.link(obj)
        # add subdiv + displacement for organic surface
        # We'll convert curve to mesh via object convert
        bpy.context.view_layer.objects.active = obj
        obj.select_set(True)
        try:
            bpy.ops.object.convert(target='MESH')
        except: pass
        obj.select_set(False)
        # decimate check
        if obj.type == 'MESH':
            # add solidify-ish organic wobble via simple deform already baked by curve shape
            # ensure shade smooth
            for poly in obj.data.polygons:
                poly.use_smooth = True
            if mats['coral'] not in obj.data.materials.values():
                obj.data.materials.append(mats['coral'])
        # link to collection, unlink from scene collection if needed
        try:
            bpy.context.scene.collection.objects.unlink(obj)
            col.objects.link(obj)
        except: pass

        # add coral growth detail: small branching tubes on arch surface (extra meshes)
        for b in range(6):
            sx = rng.uniform(-span*0.35, span*0.35)
            sy = rng.uniform(3.0, 12.0)
            # random mesh cone as detail
            bpy.ops.mesh.primitive_cone_add(radius1=0.12+rng.uniform(0,0.08), depth=0.7+rng.uniform(0,0.5), location=(x_off+sx*0.5, sy*math.cos(lean)+sx*math.sin(lean), z_off+rng.uniform(-0.4,0.4)))
            detail = bpy.context.active_object
            detail.rotation_euler = (rng.uniform(-0.5,0.5), rng.uniform(-0.3,0.3), rng.uniform(0,6.28))
            try:
                bpy.context.scene.collection.objects.unlink(detail)
                col.objects.link(detail)
                detail.data.materials.append(mats['coral'])
                for poly in detail.data.polygons: poly.use_smooth=True
            except: pass

    # ground anchor plate (reef base)
    bpy.ops.mesh.primitive_plane_add(size=36, location=(0,0,0))
    plate = bpy.context.active_object
    try: bpy.context.scene.collection.objects.unlink(plate); col.objects.link(plate)
    except: pass
    plate.data.materials.append(mats['coral'])
    # scale UV
    return col

def build_brain_atoll():
    """Floating Brain Atoll honeycomb 12m inverted (floating island, underside exposed)."""
    import bpy, bmesh
    from mathutils import Vector
    import math, random
    rng = random.Random(SEED+1)
    col = bpy.data.collections.new("BrainAtoll")
    bpy.context.scene.collection.children.link(col)

    mat = _make_pbr_mat("M_Surreal_AbyssSponge",
        albedo_path=TEX_DIR/"T_Surreal_AbyssSponge_Albedo.png",
        normal_path=TEX_DIR/"T_Surreal_AbyssSponge_Normal.png",
        emissive_path=TEX_DIR/"T_Surreal_AbyssSponge_Emissive.png",
        base_color=(0.22,0.28,0.26,1), emission_color=(1.0,0.72,0.18,1), emission_strength=2.8,
        transmission=0.08, roughness=0.75)

    # Main atoll body: inverted dome + honeycomb cells
    # Create icosphere base, deform to atoll
    bpy.ops.mesh.primitive_ico_sphere_add(subdivisions=4, radius=6.0, location=(0, 12.0, 0))
    atoll = bpy.context.active_object
    try: bpy.context.scene.collection.objects.unlink(atoll); col.objects.link(atoll)
    except: pass

    # deform: flatten bottom, fold brains, invert so honeycomb faces down
    import bmesh as bm
    me = atoll.data
    bm_mesh = bmesh.new()
    bm_mesh.from_mesh(me)
    for v in bm_mesh.verts:
        # flatten top -> make inverted bowl: pull y down for upper hemisphere
        if v.co.y > 0:
            v.co.y *= 0.35
            # brain folds: sin displacement
            v.co.x += 0.35*math.sin(v.co.x*1.8)*math.sin(v.co.z*1.5)
            v.co.z += 0.35*math.sin(v.co.z*1.8)
            v.co.y += 0.6*math.sin(v.co.x*2.2)*math.sin(v.co.z*2.2)
        else:
            # underside: extrude honeycomb depth
            v.co.y *= 1.15
            # honeycomb dimpling
            d = math.sin(v.co.x*2.0)*math.sin(v.co.z*2.0)
            v.co.y -= 0.5*max(0,d)
    bm_mesh.to_mesh(me)
    bm_mesh.free()
    me.update()
    for poly in me.polygons: poly.use_smooth=True
    me.materials.append(mat)

    # Honeycomb cells on underside: add ~90 hexagonal prisms hanging down
    # distribute on lower hemisphere projection
    cells_added = 0
    for _ in range(140):
        # random point on disk
        ang = rng.uniform(0, 6.28)
        rad = rng.uniform(0.5, 5.6)
        cx = math.cos(ang)*rad
        cz = math.sin(ang)*rad
        # check if inside atoll radius (rough)
        if rad > 5.4: continue
        depth = rng.uniform(0.5, 1.8)
        rad_cell = rng.uniform(0.28, 0.55)
        # hex prism
        bpy.ops.mesh.primitive_cylinder_add(vertices=6, radius=rad_cell, depth=depth, location=(cx, 12.0 - 3.0 - depth*0.5, cz))
        cell = bpy.context.active_object
        try: bpy.context.scene.collection.objects.unlink(cell); col.objects.link(cell)
        except: pass
        cell.rotation_euler = (0,0, rng.uniform(0,6.28))
        cell.data.materials.append(mat)
        for poly in cell.data.polygons: poly.use_smooth=True
        cells_added += 1
        if cells_added >= 90:
            break

    # Floating effect: small stalactite roots on top rim
    for i in range(8):
        ang = i/8*6.28
        x = math.cos(ang)*5.8; z=math.sin(ang)*5.8
        bpy.ops.mesh.primitive_cone_add(radius1=0.18, depth=1.2, location=(x, 12.0-1.0, z))
        cone = bpy.context.active_object
        cone.rotation_euler = (math.radians(180),0,0)
        try: bpy.context.scene.collection.objects.unlink(cone); col.objects.link(cone)
        except: pass
        cone.data.materials.append(mat)

    return col

def build_glass_spire_forest():
    """Glass Spire Forest 20m transparent spires with internal filaments."""
    import bpy, bmesh
    from mathutils import Vector
    import math, random
    rng = random.Random(SEED+2)
    col = bpy.data.collections.new("GlassSpireForest")
    bpy.context.scene.collection.children.link(col)

    glass_mat = _make_pbr_mat("M_Surreal_GlassSpire",
        albedo_path=TEX_DIR/"T_Surreal_MoltenShell_Albedo.png",
        normal_path=TEX_DIR/"T_Surreal_MoltenShell_Normal.png",
        emissive_path=TEX_DIR/"T_Surreal_MoltenShell_Emissive.png",
        base_color=(0.82,0.92,1.0,1), emission_color=(1.0,0.45,0.12,1), emission_strength=4.0,
        transmission=0.92, ior=1.52, roughness=0.08, metallic=0.0, alpha=0.55)
    # internal filament mat (thin inner tubes, stronger emission)
    fil_mat = _make_pbr_mat("M_Surreal_Filament",
        base_color=(1.0,0.35,0.15,1), emission_color=(1.0,0.6,0.18,1), emission_strength=8.0,
        transmission=0.25, roughness=0.35)

    # base plate
    bpy.ops.mesh.primitive_plane_add(size=32, location=(0,0,0))
    plate = bpy.context.active_object
    try: bpy.context.scene.collection.objects.unlink(plate); col.objects.link(plate)
    except: pass
    plate.data.materials.append(glass_mat)

    # 18 spires of varying height 12-20m
    for i in range(18):
        ang = rng.uniform(0, 6.28)
        rad = rng.uniform(1.0, 12.0)
        cx = math.cos(ang)*rad
        cz = math.sin(ang)*rad
        h = rng.uniform(12.0, 20.0)
        r_base = rng.uniform(0.35, 0.75)
        r_top = r_base * rng.uniform(0.12, 0.28)
        # sway/curve
        bend = rng.uniform(-1.2, 1.2)
        # create mesh spire: lathe of profile using cylinder with scaled top
        bpy.ops.mesh.primitive_cone_add(radius1=r_base, radius2=r_top, depth=h, location=(cx, h*0.5 + rng.uniform(-0.5,0.5), cz))
        spire = bpy.context.active_object
        try: bpy.context.scene.collection.objects.unlink(spire); col.objects.link(spire)
        except: pass
        # deform vertices for curvature and faceting
        me = spire.data
        for v in me.vertices:
            # bend along height
            t = (v.co.z + h*0.5)/h  # 0..1
            v.co.x += bend * (t**2)
            # subtle twist
            th = math.atan2(v.co.y, v.co.x)
            r = math.hypot(v.co.x - bend*(t**2), v.co.y)
            # add 6-sided faceting for crystal look (snap angle)
            sides = 6
            snapped = round(th/(2*math.pi/sides))*(2*math.pi/sides)
            blend = 0.35 * t
            th2 = th*(1-blend) + snapped*blend
            v.co.x = bend*(t**2) + math.cos(th2)*r
            v.co.y = math.sin(th2)*r
        me.update()
        for poly in me.polygons: poly.use_smooth=False  # faceted glass
        me.materials.append(glass_mat)

        # internal filament: thin curved tube inside
        # use small icosphere chain or curve
        fi_h = h * rng.uniform(0.6, 0.85)
        fi_pts = []
        for k in range(6):
            t = k/5
            y = t*fi_h
            off = math.sin(t*math.pi*2 + rng.uniform(0,6.28))*0.08
            fi_pts.append(Vector((cx+off, y+2.0, cz+off*0.5)))
        # filament as small cylinders
        for k in range(len(fi_pts)-1):
            a = fi_pts[k]; b = fi_pts[k+1]
            mid = (a+b)*0.5
            vec = b - a
            length = vec.length
            if length < 1e-4: continue
            bpy.ops.mesh.primitive_cylinder_add(radius=0.025, depth=length, location=mid)
            fil = bpy.context.active_object
            try: bpy.context.scene.collection.objects.unlink(fil); col.objects.link(fil)
            except: pass
            # orient
            # align Z axis to vec
            import mathutils
            # set rotation via quaternion
            quat = Vector((0,0,1)).rotation_difference(vec.normalized())
            fil.rotation_mode = 'QUATERNION'
            fil.rotation_quaternion = quat
            fil.data.materials.append(fil_mat)

    return col

def blender_build():
    import bpy
    TEX_DIR.mkdir(parents=True, exist_ok=True)
    OUT_ROOT.mkdir(parents=True, exist_ok=True)

    # If textures missing, bake them first inside blender (reuse numpy PIL path via bpy fallback)
    need = ["T_Surreal_VoidCoral_Albedo.png","T_Surreal_MoltenShell_Albedo.png","T_Surreal_AbyssSponge_Albedo.png"]
    if not all((TEX_DIR/n).exists() for n in need):
        print("[surreal-reef] textures missing — baking inside Blender")
        bake_textures()

    _clear_scene()
    scene = bpy.context.scene
    scene.render.engine = 'CYCLES'
    try: scene.cycles.device = 'CPU'
    except: pass
    scene.cycles.samples = 64
    scene.render.resolution_x = 1920
    scene.render.resolution_y = 1080
    scene.render.film_transparent = True
    scene.render.image_settings.file_format = 'PNG'
    scene.render.image_settings.color_mode = 'RGBA'
    scene.display_settings.display_device = 'sRGB'
    try: scene.view_settings.view_transform = 'Filmic'
    except: pass

    # Build all three reef types
    col_cat = build_cathedral_coral()
    col_brain = build_brain_atoll()
    col_glass = build_glass_spire_forest()

    # Lighting + camera
    # Sun
    sun_data = bpy.data.lights.new(name="Sun", type='SUN')
    sun_data.energy = 6.0
    sun_data.angle = 0.5
    sun_obj = bpy.data.objects.new(name="Sun", object_data=sun_data)
    bpy.context.scene.collection.objects.link(sun_obj)
    sun_obj.location = (12, 22, 18)
    sun_obj.rotation_euler = (math.radians(52), math.radians(12), math.radians(35))
    # Fill area
    area = bpy.data.lights.new(name="Fill", type='AREA')
    area.energy = 180.0
    area.size = 12
    area_obj = bpy.data.objects.new("Fill", area)
    bpy.context.scene.collection.objects.link(area_obj)
    area_obj.location = (-10, 14, 10)
    area_obj.rotation_euler = (math.radians(-30),0,math.radians(20))
    # World: deep teal + dense fog vibe
    world = bpy.context.scene.world
    if world is None:
        world = bpy.data.worlds.new("World")
        bpy.context.scene.world = world
    world.use_nodes = True
    nt = world.node_tree
    nt.nodes.clear()
    out = nt.nodes.new("ShaderNodeOutputWorld")
    bg = nt.nodes.new("ShaderNodeBackground")
    bg.inputs["Color"].default_value = (0.015, 0.045, 0.08, 1)
    bg.inputs["Strength"].default_value = 0.6
    nt.links.new(bg.outputs["Background"], out.inputs["Surface"])

    # Camera: wide beauty covering all three installations
    cam_data = bpy.data.cameras.new("Cam")
    cam_data.lens = 26
    cam_obj = bpy.data.objects.new("Cam", cam_data)
    bpy.context.scene.collection.objects.link(cam_obj)
    cam_obj.location = (22, 10, 14)
    # look-at center
    import mathutils
    target = mathutils.Vector((0, 6, 0))
    direction = target - cam_obj.location
    rot_quat = direction.to_track_quat('-Z', 'Y')
    cam_obj.rotation_euler = rot_quat.to_euler()
    scene.camera = cam_obj

    # Save blend
    blend_path = OUT_ROOT / "surreal_reef.blend"
    bpy.ops.wm.save_as_mainfile(filepath=str(blend_path))
    print(f"[surreal-reef] wrote {blend_path}")

    # Export FBX per collection (each surreal type isolated)
    def export_collection(col, fname):
        # select only that collection's objects
        bpy.ops.object.select_all(action='DESELECT')
        for o in col.objects:
            o.select_set(True)
        fbx_path = OUT_ROOT / fname
        bpy.ops.export_scene.fbx(filepath=str(fbx_path), use_selection=True, apply_scale_options='FBX_SCALE_ALL', object_types={'MESH'}, use_mesh_modifiers=True, bake_space_transform=True, axis_forward='-Z', axis_up='Y')
        print(f"[surreal-reef] wrote {fbx_path} ({fbx_path.stat().st_size} bytes)")
        bpy.ops.object.select_all(action='DESELECT')
        return fbx_path

    fbx_cat = export_collection(col_cat, "SM_Surreal_CathedralCoral.fbx")
    fbx_brain = export_collection(col_brain, "SM_Surreal_BrainAtoll.fbx")
    fbx_glass = export_collection(col_glass, "SM_Surreal_GlassSpireForest.fbx")

    # Also export full scene FBX
    bpy.ops.object.select_all(action='SELECT')
    bpy.ops.export_scene.fbx(filepath=str(OUT_ROOT/"SM_Surreal_Reef_Combined.fbx"), use_selection=True, object_types={'MESH','LIGHT','CAMERA'}, use_mesh_modifiers=True, bake_space_transform=True, axis_forward='-Z', axis_up='Y')
    print(f"[surreal-reef] wrote combined FBX")

    # Beauty renders: 3 closeups + 1 wide
    renders = []
    # wide
    scene.render.filepath = str(OUT_ROOT / "beauty_wide.png")
    bpy.ops.render.render(write_still=True)
    renders.append("beauty_wide.png")
    # closeup cathedral
    cam_obj.location = (8, 5, 6)
    direction = mathutils.Vector((0, 6, 0)) - cam_obj.location
    cam_obj.rotation_euler = direction.to_track_quat('-Z','Y').to_euler()
    scene.render.filepath = str(OUT_ROOT / "beauty_cathedral.png")
    bpy.ops.render.render(write_still=True)
    renders.append("beauty_cathedral.png")
    # closeup brain
    cam_obj.location = (6, 14, 4)
    direction = mathutils.Vector((0, 10, 0)) - cam_obj.location
    cam_obj.rotation_euler = direction.to_track_quat('-Z','Y').to_euler()
    scene.render.filepath = str(OUT_ROOT / "beauty_brain.png")
    bpy.ops.render.render(write_still=True)
    renders.append("beauty_brain.png")
    # closeup glass
    cam_obj.location = (-8, 4, 5)
    direction = mathutils.Vector((0, 7, 0)) - cam_obj.location
    cam_obj.rotation_euler = direction.to_track_quat('-Z','Y').to_euler()
    scene.render.filepath = str(OUT_ROOT / "beauty_glass.png")
    bpy.ops.render.render(write_still=True)
    renders.append("beauty_glass.png")

    # Re-save blend with final camera positions? keep current wide is fine; restore wide cam for save
    cam_obj.location = (22, 10, 14)
    direction = mathutils.Vector((0, 6, 0)) - cam_obj.location
    cam_obj.rotation_euler = direction.to_track_quat('-Z','Y').to_euler()
    bpy.ops.wm.save_as_mainfile(filepath=str(blend_path))

    print(f"[surreal-reef] renders done: {renders}")
    return blend_path, [fbx_cat, fbx_brain, fbx_glass], renders

def write_manifest(tex_files, blend_path=None, fbx_paths=None, renders=None):
    OUT_ROOT.mkdir(parents=True, exist_ok=True)
    # collect file entries with sha256
    def entry(p, kind, extra=None):
        rp = Path(p)
        try: rel = str(rp.relative_to(PROJECT_ROOT)).replace("\\","/")
        except: rel = str(rp)
        e = {"path": rel, "kind": kind, "bytes": rp.stat().st_size if rp.exists() else 0}
        if rp.exists():
            e["sha256"] = _sha256(rp)
        if extra: e.update(extra)
        return e

    files = []
    for f in (tex_files or []):
        # f already has relative path dict; enrich with bytes/sha
        abs_p = PROJECT_ROOT / f["path"]
        if abs_p.exists():
            f["bytes"] = abs_p.stat().st_size
            f["sha256"] = _sha256(abs_p)
        files.append(f)
    if blend_path and Path(blend_path).exists():
        files.append(entry(blend_path, "blend", {"role":"scene","unit":"m"}))
    if fbx_paths:
        roles = ["cathedral_coral","brain_atoll","glass_spire_forest"]
        for p, r in zip(fbx_paths, roles):
            if Path(p).exists():
                files.append(entry(p, "fbx", {"role":r,"export":"Blender FBX (selection, modifiers applied, bake transform)"}))
        combined = OUT_ROOT/"SM_Surreal_Reef_Combined.fbx"
        if combined.exists():
            files.append(entry(combined, "fbx", {"role":"combined","note":"all collections + lights + cam"}))
    if renders:
        for rn in renders:
            rp = OUT_ROOT/rn
            if rp.exists():
                files.append(entry(rp, "beauty_png", {"resolution":"1920x1080","engine":"Cycles","samples":64}))

    manifest = {
        "schema": "melodia.surreal_reef.v1",
        "seed": SEED,
        "size": SIZE,
        "tiling": "lattice-periodic (period divides size, wrapped Voronoi, tileable_sine with integer freq)",
        "offline": True,
        "textures": {
            "count": 3,
            "sets": [
                {"name":"void_coral","desc":"dark void coral with cyan/magenta bioluminescent vein network + pores","maps":["Albedo sRGB","Normal OpenGL Y+","Emissive (veins+pores)"]},
                {"name":"molten_shell","desc":"pearlescent shell with molten lava crack network, iridescent mottle","maps":["Albedo sRGB","Normal","Emissive (lava cracks)"]},
                {"name":"abyss_sponge","desc":"abyssal honeycomb sponge, amber internal glow from deep pores","maps":["Albedo sRGB","Normal","Emissive (deep-pore amber)"]},
            ],
            "resolution": f"{SIZE}x{SIZE}",
            "import": {"albedo":"sRGB true","normal":"sRGB false, OpenGL","emissive":"sRGB false, multiply into Emission Strength"}
        },
        "meshes": [
            {"id":"SM_Surreal_CathedralCoral","desc":"Leaning Cathedral Coral 18m arches (3 arches, span 7.5-10m, lean 12-18deg, sailable)","arch_count":3,"height_m":18,"sailable_clearance_m":"~7m span x 18m height","material":"M_Surreal_VoidCoral (emission cyan/magenta, transmission 0.15)","fbx": "SM_Surreal_CathedralCoral.fbx"},
            {"id":"SM_Surreal_BrainAtoll","desc":"Floating Brain Atoll honeycomb 12m inverted (diameter ~12m, floats at y=12m, ~90 hex cells underneath)","diameter_m":12,"height_m":12,"cells":90,"material":"M_Surreal_AbyssSponge (amber emission, transmission 0.08)","fbx":"SM_Surreal_BrainAtoll.fbx"},
            {"id":"SM_Surreal_GlassSpireForest","desc":"Glass Spire Forest 20m transparent spires with internal filaments (18 spires, 12-20m, 6-sided crystal faceting)","spire_count":18,"height_m":"12-20","material":"M_Surreal_GlassSpire (transmission 0.92, IOR 1.52, molten emissive) + M_Surreal_Filament (internal)","fbx":"SM_Surreal_GlassSpireForest.fbx"},
        ],
        "materials": "Principled BSDF: BaseColor←Albedo, Normal←NormalMap, EmissionColor←Emissive*EmissionStrength, Transmission Weight set per type. UE import: replicate with MI, connect Emissive to Emissive Color and multiply by scalar param.",
        "scene": {"units":"metres (Blender), FBX bake transform (UE import 100x cm or keep m)","blend":"surreal_reef.blend","lights":"Sun 6.0 + Area fill 180 + dark teal world","camera":"26mm, 1920x1080, film_transparent, 64 samples Cycles CPU"},
        "files": files
    }
    mp = OUT_ROOT / "reef_manifest.json"
    with open(mp,"w",encoding="utf-8") as f:
        json.dump(manifest,f,indent=2)
    print(f"[surreal-reef] manifest -> {mp}")
    return mp

def main():
    global OUT_ROOT, TEX_DIR
    # Blender passes its own args (--background etc) before "--"; filter them
    argv = sys.argv
    if "--" in argv:
        argv = argv[argv.index("--")+1:]
    else:
        # strip blender args: keep only known script args
        argv = [a for a in argv if a.startswith("--") and a.split("=")[0] in ("--seed","--size","--all","--blender-only")]
    ap = argparse.ArgumentParser()
    ap.add_argument("--seed", type=int, default=SEED)
    ap.add_argument("--size", type=int, default=SIZE)
    ap.add_argument("--all", action="store_true", help="bake textures then spawn Blender headless for meshes")
    ap.add_argument("--blender-only", action="store_true", help="only blender mesh build (called inside blender)")
    args, _ = ap.parse_known_args(argv)

    if IS_BLENDER:
        blend_path, fbx_paths, renders = blender_build()
        # write manifest from inside blender (collect tex file list from disk)
        tex_files = []
        for n in TEX_DIR.glob("T_Surreal_*.png"):
            tex_files.append({"name":n.stem,"path":str(n.relative_to(PROJECT_ROOT)).replace("\\","/"),"kind":"rgb" if "Albedo" in n.name or "Normal" in n.name else "gray","size":SIZE,"seed":SEED,"bytes":n.stat().st_size,"sha256":_sha256(n)})
        cs = TEX_DIR/"_SurrealReef_ContactSheet.png"
        if cs.exists():
            tex_files.append({"name":cs.stem,"path":str(cs.relative_to(PROJECT_ROOT)).replace("\\","/"),"kind":"contact_sheet","size":SIZE,"seed":SEED,"bytes":cs.stat().st_size,"sha256":_sha256(cs)})
        write_manifest(tex_files, blend_path, fbx_paths, renders)
        return

    # Plain python path
    if not args.blender_only:
        tex_files = bake_textures(seed=args.seed, size=args.size)
        # write partial manifest now (meshes pending)
        # full manifest will be overwritten after blender run
        write_manifest(tex_files, None, None, None)
        print(f"[surreal-reef] textures baked. Manifest at {OUT_ROOT/'reef_manifest.json'}")
        if args.all:
            blender_exe = Path("C:/Program Files/Blender Foundation/Blender 5.2/blender.exe")
            if not blender_exe.exists():
                print(f"[surreal-reef] blender not found at {blender_exe}, try blender in PATH")
                blender_exe = Path("blender")
            cmd = [str(blender_exe), "--background", "--python", str(Path(__file__).resolve())]
            print(f"[surreal-reef] spawning Blender: {' '.join(cmd)}")
            result = subprocess.run(cmd, capture_output=True, text=True, timeout=600)
            print(result.stdout[-4000:] if len(result.stdout)>4000 else result.stdout)
            if result.stderr:
                print(result.stderr[-4000:] if len(result.stderr)>4000 else result.stderr)
            if result.returncode != 0:
                print(f"[surreal-reef] blender exited {result.returncode}")
            else:
                print(f"[surreal-reef] all done -> {OUT_ROOT}")

if __name__ == "__main__":
    main()
