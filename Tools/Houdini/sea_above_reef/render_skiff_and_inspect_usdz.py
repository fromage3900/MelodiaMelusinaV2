"""Two jobs in one headless Blender pass:
1. BOAT: render SM_Starskiff_MK2 from the owner's work-copy blend (their lights).
2. OUTFIT: inspect melusinashorewake.usdz — objects, meshes, materials, UVs,
   skeletons — and dump outfits_inspect.json so the transformation pass is
   evidence-based.
Run:  blender -b --factory-startup -noaudio --python render_skiff_and_inspect_usdz.py
"""

import json
from pathlib import Path

import bpy
from mathutils import Vector

PROJECT_ROOT = Path(__file__).resolve().parents[3]
WORK_COPY = PROJECT_ROOT / "Saved/Audit/sea_above/skiff/Starskiff_Shorewake_Project_copy.blend"
USDZ = Path(r"C:\Users\froma\Downloads\melusinashorewake.usdz")
OUT_DIR = PROJECT_ROOT / "Saved/Audit/sea_above/renders/skiff"
INSPECT_OUT = PROJECT_ROOT / "Saved/Audit/melusina_lookdev/outfits_inspect.json"


def setup_cpu():
    scene = bpy.context.scene
    scene.render.engine = "CYCLES"
    scene.cycles.device = "CPU"
    scene.cycles.samples = 24
    scene.render.resolution_x = 960
    scene.render.resolution_y = 540
    return scene


def autofit_cam(objs, name, offset_dir, dist_scale=1.35):
    lo = Vector((1e9,) * 3)
    hi = Vector((-1e9,) * 3)
    for ob in objs:
        if ob.type != "MESH":
            continue
        for c in ob.bound_box:
            w = ob.matrix_world @ Vector(c)
            lo = Vector(map(min, lo, w))
            hi = Vector(map(max, hi, w))
    center = (lo + hi) / 2.0
    diag = max((hi - lo).length, 1.0)
    data = bpy.data.cameras.new(name)
    data.lens = 50
    data.clip_start = 0.01
    data.clip_end = 1e7
    cam = bpy.data.objects.new(name, data)
    cam.location = center + offset_dir.normalized() * diag * dist_scale
    bpy.context.collection.objects.link(cam)
    tgt = bpy.data.objects.new(name + "_T", None)
    tgt.location = center
    bpy.context.collection.objects.link(tgt)
    c = cam.constraints.new("TRACK_TO")
    c.target = tgt
    return cam


def render_to(path):
    bpy.context.scene.render.filepath = str(path)
    bpy.ops.render.render(write_still=True)


def boat():
    bpy.ops.wm.open_mainfile(filepath=str(WORK_COPY))
    scene = setup_cpu()
    # hide text/debug objects (the desktop project's WakeFoam is 3D text)
    for o in bpy.data.objects:
        if o.type == "FONT":
            o.hide_render = True
            o.hide_viewport = True
    meshes = [o for o in bpy.data.objects if o.type == "MESH"
              and o.name.startswith(("Starskiff", "Gunwale", "MastLantern"))]
    print(f"[boat] scene meshes: {[o.name for o in meshes]}")
    cam = autofit_cam(meshes, "SkiffQA", Vector((1.1, -1.5, 0.7)))
    scene.camera = cam
    OUT_DIR.mkdir(parents=True, exist_ok=True)
    render_to(OUT_DIR / "STARSKIFF_MK2_show.png")
    print("[boat] render -> STARSKIFF_MK2_show.png")


def inspect_usdz():
    clear_scene()
    before = set(bpy.data.objects)
    try:
        bpy.ops.wm.usd_import(filepath=str(USDZ))
    except AttributeError:
        bpy.ops.import_scene.usd(filepath=str(USDZ))
    new = [o for o in bpy.data.objects if o not in before]
    info = {"source": str(USDZ), "objects": [], "materials": [],
            "armatures": [], "mesh_stats": {}}
    for o in new:
        info["objects"].append({"name": o.name, "type": o.type,
                                "verts": len(o.data.vertices) if o.type == "MESH" else 0})
        if o.type == "ARMATURE":
            info["armatures"].append(o.name)
    for m in bpy.data.materials:
        if m.users:
            info["materials"].append(m.name)
    for o in new:
        if o.type == "MESH":
            uv_names = [u.name for u in o.data.uv_layers]
            info["mesh_stats"][o.name] = {
                "polys": len(o.data.polygons), "uvs": uv_names,
                "shape_keys": bool(o.data.shape_keys),
                "materials": [s.material.name if s.material else None
                              for s in o.material_slots]}
    INSPECT_OUT.parent.mkdir(parents=True, exist_ok=True)
    INSPECT_OUT.write_text(json.dumps(info, indent=2), encoding="utf-8")
    print(f"[usdz] objects: {[o['name'] for o in info['objects']]}")
    print(f"[usdz] materials: {info['materials']}")
    print(f"[usdz] armatures: {info['armatures']}")
    print(f"[usdz] inspect -> {INSPECT_OUT.name}")
    return new


def clear_scene():
    bpy.ops.object.select_all(action="SELECT")
    bpy.ops.object.delete(use_global=False)


def main():
    boat()
    clear_scene()
    inspect_usdz()


if __name__ == "__main__":
    main()
