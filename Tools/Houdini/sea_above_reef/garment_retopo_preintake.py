#!/usr/bin/env python
"""Garment retopo PRE-INTAKE — Quadriflow + Smart Project (Blender 5.2.1 headless).

Dense triangulated market meshes (AntiqueDoll 180k v, ButterflyWing 818k v,
UV overlaps 75/11) cannot go straight into garment_intake_prep.py. This stage
runs FIRST: import -> join -> transform_apply -> Quadriflow remesh (FACES mode)
-> Smart UV Project -> export retopo'd FBX back into Imports/GarmentIntake/
for the canonical intake script to consume. Stage 0 is a bmesh clean
(remove doubles 0.0001, delete loose, recalc normals) plus a Voxel bridge:
market "_thick" meshes carry ~5k multi-face edges, which Quadriflow refuses
headless (warning, 0.0 s no-op, verified with/without weld and solidify), so
a calibrated Voxel fallback iterates to ~= target_faces quads when Quadriflow
no-ops (manifest "engine" records which ran). Slot NAMES are preserved in the
manifest for Substance ID reassignment (5.2.1 voxel path kept all 20).

Run (Blender 5.2, from repo):
  "C:/Program Files/Blender Foundation/Blender 5.2/blender.exe" -b --factory-startup \\
    -noaudio --python Tools/Houdini/sea_above_reef/garment_retopo_preintake.py \\
    -- --source Imports/GarmentIntake/AntiqueDoll_Dress_fbx_thick.fbx \\
       --out AntiqueDoll_Dress_retopo.fbx --target_faces 9000

CLI args after -- are parsed manually (Blender strips them at #-comment boundary).
Outputs: Imports/GarmentIntake/<out> + <out>.retopo_manifest.json (seed + sha256).
Test ONLY on scratch copies (e.g. %LOCALAPPDATA%/Temp/retopo_*) — never overwrite
canonical intake FBX in place; pass --outdir for scratch runs.
"""
import bpy
import hashlib
import json
import sys
import time
from pathlib import Path

PROJECT = Path(__file__).resolve().parents[3]
DEFAULT_OUT_ROOT = PROJECT / "Imports" / "GarmentIntake"
SEED = 20260902


# --- parse args (after "-- ") -------------------------------------------------
def arg(name, dflt=None):
    for i, a in enumerate(sys.argv):
        if a == "--" + name:
            return sys.argv[i + 1] if i + 1 < len(sys.argv) else dflt
    return dflt


SRC = arg("source")
OUT_NAME = arg("out", "Retopo_preintake.fbx")
TARGET_FACES = int(arg("target_faces", "9000"))
OUTDIR = Path(arg("outdir", str(DEFAULT_OUT_ROOT)))
if not SRC:
    print("NO_SOURCE: pass --source <fbx|obj>")
    raise SystemExit(2)
SRC = (PROJECT / SRC) if not Path(SRC).is_absolute() else Path(SRC)
if not SRC.exists():
    print(f"SOURCE_MISSING {SRC}")
    raise SystemExit(2)
OUTDIR.mkdir(parents=True, exist_ok=True)
OUT = OUTDIR / OUT_NAME

t_all = time.perf_counter()

# --- 1. import ----------------------------------------------------------------
ext = SRC.suffix.lower()
if ext == ".fbx":
    bpy.ops.import_scene.fbx(filepath=str(SRC), axis_forward="-Y", axis_up="Z")
elif ext == ".obj":
    bpy.ops.wm.obj_import(filepath=str(SRC))
else:
    print("UNSUPPORTED_EXT", ext)
    raise SystemExit(2)

meshes = [o for o in bpy.data.objects if o.type == "MESH"]
if not meshes:
    print("NO_MESH after import")
    raise SystemExit(2)
bpy.ops.object.select_all(action="DESELECT")
bpy.context.view_layer.objects.active = meshes[0]
for o in meshes:
    o.select_set(True)
bpy.ops.object.join()
obj = bpy.context.view_layer.objects.active

# --- 2. normalize --------------------------------------------------------------
bpy.ops.object.transform_apply(location=True, rotation=True, scale=True)

# --- 2b. manifold clean (Quadriflow refuses non-manifold market meshes) --------
import bmesh
bm = bmesh.new()
bm.from_mesh(obj.data)
bmesh.ops.remove_doubles(bm, verts=list(bm.verts), dist=0.0001)
bmesh.ops.delete(bm, geom=[v for v in bm.verts if not v.link_faces],
                 context="VERTS")
bmesh.ops.recalc_face_normals(bm, faces=list(bm.faces))
bm.to_mesh(obj.data)
bm.free()
obj.data.update()
verts_in = len(obj.data.vertices)
polys_in = len(obj.data.polygons)
slots_in = [ms.material.name if ms.material else "NONE"
            for ms in obj.material_slots]

# --- 3. Quadriflow first (FACES mode, seeded); voxel fallback --------------------
# Quadriflow takes only manifold input. Market "_thick" meshes carry boundary
# rims + multi-face edges (AntiqueDoll: 5118) and are refused headless
# (warning, 0.0 s no-op) with or without welding/solidify. So: try Quadriflow
# on the cleaned mesh; if it no-ops (poly count unchanged), fall back to a
# calibrated Voxel remesh whose size iterates to ~= target_faces quads.
dims = obj.dimensions
MAXD = max(dims.x, dims.y, dims.z)
ENGINE = "quadriflow"
VOX = None
t_voxel = 0.0
t0 = time.perf_counter()
polys_before = len(obj.data.polygons)
bpy.ops.object.quadriflow_remesh(
    mode="FACES",
    target_faces=TARGET_FACES,
    seed=SEED,
    use_preserve_sharp=True,
    use_preserve_boundary=True,
    preserve_attributes=True,
    smooth_normals=True,
)
t_remesh = time.perf_counter() - t0

if len(obj.data.polygons) == polys_before:
    # --- 3b. calibrated voxel fallback ---------------------------------------
    ENGINE = "voxel_fallback"
    t0 = time.perf_counter()
    base_data = obj.data.copy()
    vox = MAXD / 60.0
    best = None  # (distance_to_target, object)
    for attempt in range(5):
        cand = obj.copy()
        cand.data = base_data.copy()
        bpy.context.collection.objects.link(cand)
        bpy.context.view_layer.update()
        bpy.ops.object.select_all(action="DESELECT")
        cand.select_set(True)
        bpy.context.view_layer.objects.active = cand
        vmod = cand.modifiers.new("RetopoVoxel", "REMESH")
        vmod.mode = "VOXEL"
        vmod.voxel_size = vox
        vmod.adaptivity = 0.0
        vmod.use_smooth_shade = True
        bpy.ops.object.modifier_apply(modifier=vmod.name)
        n = len(cand.data.polygons)
        print(f"VOXEL_ATTEMPT {attempt} size={vox:.6f} polys={n}")
        if best is None or abs(n - TARGET_FACES) < abs(best[0] - TARGET_FACES):
            if best is not None:
                bpy.data.objects.remove(best[1], do_unlink=True)
            best = (n, cand)
            VOX = vox
        else:
            bpy.data.objects.remove(cand, do_unlink=True)
        if TARGET_FACES * 0.7 <= n <= TARGET_FACES * 1.3:
            break
        vox *= (n / TARGET_FACES) ** 0.5 if n > 0 else 1.5
        vox = min(max(vox, MAXD / 500.0), MAXD / 10.0)
    bpy.data.objects.remove(obj, do_unlink=True)
    obj = best[1]
    obj.name = "RetopoPreintake"
    t_voxel = time.perf_counter() - t0
    print(f"VOXEL_FALLBACK engaged size={VOX:.6f} polys={best[0]}")
mesh = obj.data
verts_out = len(mesh.vertices)
polys_out = len(mesh.polygons)
quads = sum(1 for p in mesh.polygons if len(p.loop_indices) == 4)
quad_ratio = quads / polys_out if polys_out else 0.0

# --- 5. Smart UV Project (66 deg, island margin 0.02) -----------------------------
t0 = time.perf_counter()
bpy.ops.object.mode_set(mode="EDIT")
bpy.ops.mesh.select_all(action="SELECT")
bpy.ops.uv.smart_project(angle_limit=66, island_margin=0.02,
                         area_weight=0.0, correct_aspect=True,
                         scale_to_bounds=False)
bpy.ops.object.mode_set(mode="OBJECT")
t_uv = time.perf_counter() - t0

# --- 6. export FBX ---------------------------------------------------------------
bpy.ops.object.select_all(action="DESELECT")
obj.select_set(True)
bpy.context.view_layer.objects.active = obj
bpy.ops.export_scene.fbx(filepath=str(OUT), use_selection=True,
                         mesh_smooth_type="FACE", add_leaf_bones=False,
                         bake_anim=False, path_mode="ABSOLUTE",
                         axis_forward="-Y", axis_up="Z")

# --- 7. manifest (seed + sha256) --------------------------------------------------
t_all = time.perf_counter() - t_all
slots_out = [ms.material.name if ms.material else "NONE"
             for ms in obj.material_slots]
manifest = {
    "schema": "melodia.garment_retopo_preintake.v1",
    "seed": SEED,
    "source": str(SRC),
    "output": str(OUT),
    "target_faces": TARGET_FACES,
    "engine": ENGINE,
    "voxel_size": round(VOX, 6) if VOX else None,
    "verts_in": verts_in,
    "polys_in": polys_in,
    "slots_in": slots_in,
    "verts_out": verts_out,
    "polys_out": polys_out,
    "quad_ratio": round(quad_ratio, 4),
    "slots_out": slots_out,
    "seconds_voxel": round(t_voxel, 1),
    "seconds_remesh": round(t_remesh, 1),
    "seconds_uv": round(t_uv, 1),
    "seconds_total": round(t_all, 1),
    "fbx_sha256": hashlib.sha256(OUT.read_bytes()).hexdigest(),
    "next": "garment_intake_prep.py --source <this output>",
}
mfile = OUT.with_suffix(OUT.suffix + ".retopo_manifest.json")
mfile.write_text(json.dumps(manifest, indent=1))
print("RETOPO_DONE " + json.dumps(manifest, indent=1))
