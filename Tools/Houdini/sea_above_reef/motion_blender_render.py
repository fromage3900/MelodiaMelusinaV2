"""Motion beauty renders — surreal Motion Lab

Renders each frozen cloth drape + silk strip + VAT preview
Uses Cycles CPU, 3-point SeaAbove rig, fixed camera.
Produces high-quality 1024 PNGs in surreal_sweep_wave2/motion/renders/

Run:
  "C:/Program Files/Blender Foundation/Blender 5.2/blender.exe" --background --python Tools/Houdini/sea_above_reef/motion_blender_render.py
"""
import json
import math
import sys
from pathlib import Path

import bpy
from mathutils import Vector

PROJECT_ROOT = Path(__file__).resolve().parents[3]
MOTION_DIR = PROJECT_ROOT / "surreal_sweep_wave2" / "motion"
RENDER_DIR = MOTION_DIR / "renders"

KEY = (1.0, 0.88, 0.72)
FILL = (0.50, 0.85, 0.90)
RIM = (0.75, 0.88, 1.0)
WORLD = (0.03, 0.035, 0.058)

def clear():
    bpy.ops.object.select_all(action="SELECT")
    bpy.ops.object.delete(use_global=False)
    for coll in [bpy.data.meshes, bpy.data.materials, bpy.data.lights, bpy.data.cameras, bpy.data.images]:
        for it in list(coll):
            if getattr(it, "users", 0) == 0:
                try:
                    coll.remove(it)
                except: pass

def light(name, loc, color, energy, size=1.2):
    data = bpy.data.lights.new(name, type="AREA")
    data.energy = energy
    data.color = color
    data.size = size
    ob = bpy.data.objects.new(name, data)
    ob.location = loc
    bpy.context.collection.objects.link(ob)
    return ob

def rig(center, diag):
    d = max(diag, 1.0)
    light("Key", center + Vector((1.0,-1.1,1.3)).normalized()*d*1.05, KEY, 850*d*d)
    light("Fill", center + Vector((-1.25,-0.7,0.5)).normalized()*d*1.25, FILL, 360*d*d, 2.0*d)
    light("Rim", center + Vector((0.15,1.05,0.85)).normalized()*d*1.2, RIM, 480*d*d, 1.6*d)
    cam_data = bpy.data.cameras.new("Cam")
    cam_data.lens = 52
    cam_data.clip_start = 0.01
    cam_data.clip_end = 1e6
    cam = bpy.data.objects.new("Cam", cam_data)
    direction = Vector((1.0,-1.2,0.68)).normalized()
    cam.location = center + direction * (d*1.55 + 0.4)
    bpy.context.collection.objects.link(cam)
    tgt = bpy.data.objects.new("Tgt", None)
    tgt.location = center
    bpy.context.collection.objects.link(tgt)
    c = cam.constraints.new(type="TRACK_TO")
    c.target = tgt
    c.track_axis = "TRACK_NEGATIVE_Z"
    c.up_axis = "UP_Y"
    return cam

def setup_render(size=1024, samples=64):
    s = bpy.context.scene
    s.render.engine = "CYCLES"
    s.cycles.device = "CPU"
    s.cycles.samples = samples
    s.render.resolution_x = size
    s.render.resolution_y = size
    s.render.film_transparent = False
    s.render.image_settings.file_format = "PNG"
    s.render.image_settings.color_depth = "8"
    s.render.image_settings.compression = 15
    world = bpy.data.worlds.get("World") or bpy.data.worlds.new("World")
    s.world = world
    world.use_nodes = True
    bg = world.node_tree.nodes.get("Background")
    if bg:
        bg.inputs[0].default_value = (*WORLD, 1.0)
        bg.inputs[1].default_value = 1.0

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

def import_fbx(path):
    before = set(bpy.data.objects)
    bpy.ops.import_scene.fbx(filepath=str(path))
    return [o for o in bpy.data.objects if o not in before]

def silk_material(name, tint):
    mat = bpy.data.materials.new(name)
    mat.use_nodes = True
    bsdf = mat.node_tree.nodes.get("Principled BSDF")
    if bsdf:
        bsdf.inputs["Base Color"].default_value = (*tint, 1.0)
        bsdf.inputs["Roughness"].default_value = 0.52
        try:
            bsdf.inputs["Sheen Weight"].default_value = 0.42
            bsdf.inputs["Transmission Weight"].default_value = 0.10
        except: pass
        # subtle subsurface for silk
        try:
            bsdf.inputs["Subsurface Weight"].default_value = 0.08
            bsdf.inputs["Subsurface Color"].default_value = (*tint, 1.0)
        except: pass
    return mat

def build_cloth_mesh(name, points, faces, uvs, tint):
    mesh = bpy.data.meshes.new(name)
    verts = [tuple(c*100.0 for c in p) for p in points]
    mesh.from_pydata(verts, [], [tuple(f) for f in faces])
    mesh.update()
    uv = mesh.uv_layers.new(name="UVMap")
    for poly in mesh.polygons:
        for li in poly.loop_indices:
            vi = mesh.loops[li].vertex_index
            uv.data[li].uv = uvs[vi]
    for poly in mesh.polygons:
        poly.use_smooth = True
    obj = bpy.data.objects.new(name, mesh)
    bpy.context.collection.objects.link(obj)
    obj.data.materials.append(silk_material(name+"_Mat", tint))
    return obj

def render_obj(name, obj, out_path):
    setup_render(size=1024, samples=64)
    bpy.context.view_layer.update()
    center, diag = bbox_center_diag([obj])
    cam = rig(center, diag)
    bpy.context.scene.camera = cam
    bpy.context.scene.render.filepath = str(out_path)
    bpy.ops.render.render(write_still=True)
    print(f"[render] {name} -> {out_path.name}")

def main():
    MOTION_DIR.mkdir(parents=True, exist_ok=True)
    RENDER_DIR.mkdir(parents=True, exist_ok=True)
    cloth_json = MOTION_DIR / "frozen_cloth_meshes.json"
    anim_json = MOTION_DIR / "silk_strip_anim.json"
    if not cloth_json.exists():
        print("[render] missing cloth json — run surreal_motion2.py first")
        return
    records = []

    # cloth drapes
    payload = json.loads(cloth_json.read_text(encoding="utf-8"))
    tint_map = {"veil": (0.90,0.88,0.92), "sail": (0.82,0.78,0.70)}
    for key in ["veil","sail"]:
        c = payload["cloths"][key]
        clear()
        obj = build_cloth_mesh(c["name"], c["points"], c["faces"], c["uvs"], tint_map[key])
        # double-sided for sail (single sheet)
        try:
            obj.data.materials[0].use_backface_culling = False
        except: pass
        out = RENDER_DIR / f"{c['name']}_beauty.png"
        render_obj(c["name"], obj, out)
        records.append({"asset": c["name"], "render": f"renders/{out.name}", "type":"frozen_cloth_beauty", "verts": len(c["points"]), "faces": len(c["faces"])})

    # silk strip — render 3 moments + VAT LUT preview composite handled separately
    if anim_json.exists():
        anim = json.loads(anim_json.read_text(encoding="utf-8"))
        strip = anim["strip"]
        frames = strip["frames"]
        uvs = strip["uvs"]
        faces = strip["faces"]
        for frame_idx, suffix in [(0,"f00"), (16,"f16"), (32,"f32")]:
            clear()
            pts = frames[frame_idx]
            obj = build_cloth_mesh(f"{strip['name']}_{suffix}", pts, faces, uvs, (0.92,0.85,0.90))
            out = RENDER_DIR / f"{strip['name']}_{suffix}_beauty.png"
            render_obj(f"{strip['name']} {suffix}", obj, out)
            records.append({"asset": f"{strip['name']} {suffix}", "render": f"renders/{out.name}", "type":"vertex_anim_frame", "frame": frame_idx})
        # also a loop contact frame via python imaging will be done in system python, but we note here
        records.append({"asset": strip["name"], "fbx": "SM_SilkStrip_64f.fbx", "frames": 64, "type":"vertex_anim_fbx"})

    # VAT LUT beauty: render a deformed ribbon preview using banner LUT logic (sin deform)
    # Build a small demo ribbon and displace by sampling a VAT column visually — we fake by deforming in python and rendering
    # create a banner-like plane and apply a wind pose
    for vat_name, amp in [("T_VAT_Banner_LUT",0.55), ("T_VAT_Kelp_LUT",0.48), ("T_VAT_Hair_LUT",0.38)]:
        vat_path = MOTION_DIR / f"{vat_name}.png"
        if not vat_path.exists():
            continue
        # preview: simple flat PNG copy as lut preview (we just note it; the actual LUT is the beauty)
        # we create a contact-style render: a displaced strip preview
        clear()
        # create preview strip deformed as if reading middle column of LUT
        # deform points: similar to vat logic at time = 0.25
        import math
        W, H = 1.2, 3.0
        COLS, ROWS = 10, 28
        pts = []
        faces = []
        idx_grid=[]
        for r in range(ROWS+1):
            t = r/ROWS
            row=[]
            for c in range(COLS+1):
                u = c/COLS-0.5
                x = u*W + 0.35*t*math.sin(t*3.0 + 0.5) * t
                y = -H*t + 1.5
                z = 0.28*W*t*math.sin(u*2.0 + t*2.0 + 0.8)
                pts.append((x,y,z))
                row.append(len(pts)-1)
            idx_grid.append(row)
        for r in range(ROWS):
            for c in range(COLS):
                faces.append([idx_grid[r][c], idx_grid[r][c+1], idx_grid[r+1][c+1], idx_grid[r+1][c]])
        uvs = [(c/COLS, r/ROWS) for r in range(ROWS+1) for c in range(COLS+1)]
        tint = (0.88,0.86,0.82) if "Banner" in vat_name else (0.70,0.85,0.78) if "Kelp" in vat_name else (0.88,0.80,0.75)
        obj = build_cloth_mesh(f"{vat_name}_preview", pts, faces, uvs, tint)
        out = RENDER_DIR / f"{vat_name}_preview_beauty.png"
        render_obj(f"{vat_name} preview", obj, out)
        records.append({"asset": vat_name, "render": f"renders/{out.name}", "type":"vat_preview", "lut": vat_name+".png"})

    # write render manifest fragment (full manifest assembled in phase 5)
    (RENDER_DIR / "_render_records.json").write_text(json.dumps(records, indent=2), encoding="utf-8")
    print(f"[render] done {len(records)} renders -> {RENDER_DIR}")

if __name__ == "__main__":
    main()
