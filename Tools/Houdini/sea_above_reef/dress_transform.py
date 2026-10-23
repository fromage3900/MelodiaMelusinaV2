"""INFINITY NIKKI TRANSFORMATION — Melusina's Shorewake dress (45 USDZ panels).

Imports the downloaded melusinashorewake.usdz, joins the panels into one
garment, and authors three transformation morphs (per-panel stagger = the
"cascade" feel Nikki transformations have):

  Nikki_Bloom      panels flare outward from the garment heart + lift
  Nikki_Swirl      panels rotate around the vertical axis, staggered
  ShimmerWave      a vertex wave sweeps across the cloth (static shimmer pose)

Exports SK_ShorewakeDress.fbx (morph targets + root armature) + QA render +
transformation parameter manifest. Scale-shimmer material = jelly Iridescence
LUT + Nematocyst glints (reuse — convergence).
Run:  blender -b --factory-startup -noaudio --python dress_transform.py
"""

import json
from pathlib import Path

import bpy
from mathutils import Vector

PROJECT_ROOT = Path(__file__).resolve().parents[3]
USDZ = Path(r"C:\Users\froma\Downloads\melusinashorewake.usdz")
OUT_DIR = PROJECT_ROOT / "Saved/Audit/melusina_lookdev"
RENDER_DIR = PROJECT_ROOT / "Saved/Audit/sea_above/renders/skiff"


def main():
    clear()
    before = set(bpy.data.objects)
    try:
        bpy.ops.wm.usd_import(filepath=str(USDZ))
    except AttributeError:
        bpy.ops.import_scene.usd(filepath=str(USDZ))
    panels = sorted([o for o in bpy.data.objects if o not in before and o.type == "MESH"],
                    key=lambda o: o.name)
    print(f"[nikki] panels: {len(panels)}")
    total = sum(len(o.data.vertices) for o in panels)

    # per-panel vertex ranges BEFORE join (join concatenates in join order)
    ranges, start = [], 0
    for p in panels:
        n = len(p.data.vertices)
        ranges.append((start, start + n))
        start += n

    # garment center + panel centers
    lo = Vector((1e9,) * 3)
    hi = Vector((-1e9,) * 3)
    for p in panels:
        for c in p.bound_box:
            w = p.matrix_world @ Vector(c)
            lo = Vector(map(min, lo, w))
            hi = Vector(map(max, hi, w))
    center = (lo + hi) / 2.0
    panel_centers = []
    for p in panels:
        pc = Vector((0, 0, 0))
        for v in p.data.vertices:
            pc += p.matrix_world @ v.co
        panel_centers.append(pc / max(len(p.data.vertices), 1))

    for p in panels:
        p.select_set(True)
    bpy.context.view_layer.objects.active = panels[0]
    bpy.ops.object.join()
    dress = bpy.context.object
    dress.name = "SK_ShorewakeDress"
    dress.scale = (100.0, 100.0, 100.0)          # m -> cm
    bpy.ops.object.transform_apply(scale=True)
    bpy.ops.object.mode_set(mode="EDIT")
    bpy.ops.mesh.select_all(action="SELECT")
    bpy.ops.mesh.normals_make_consistent(inside=False)   # panels import face-down
    bpy.ops.object.mode_set(mode="OBJECT")
    bpy.ops.object.shade_smooth()
    print(f"[nikki] joined: {len(dress.data.vertices)} verts, "
          f"{len(dress.data.polygons)} polys")

    # ---- morphs (per-vertex offsets, panel-staggered) -------------------------
    def stagger(vert_index):
        for pi, (a, b) in enumerate(ranges):
            if a <= vert_index < b:
                return pi / max(len(ranges) - 1, 1)
        return 0.0

    def add_morph(name):
        return dress.shape_key_add(name=name)

    dress.shape_key_add(name="Basis")
    base = dress.data.vertices

    # Nikki_Bloom: radial flare + lift, staggered by panel
    bloom = add_morph("Nikki_Bloom")
    for i, v in enumerate(base.data.vertices):
        w = v.co
        d = Vector((w.x - center.x * 100.0, w.y - center.y * 100.0, 0.0))
        if d.length < 1e-4:
            d = Vector((0, 0, 1))
        d.normalize()
        s = stagger(i)
        v2 = w + d * (60.0 * s) + Vector((0, 0, 55.0 * s))
        bloom.data[i].co = v2

    # Nikki_Swirl: rotate around the vertical axis through center, staggered
    from mathutils import Matrix
    swirl = add_morph("Nikki_Swirl")
    for i, v in enumerate(base.data.vertices):
        w = v.co
        s = stagger(i)
        ang = math.radians(70.0) * s
        rel = Vector((w.x - center.x * 100.0, w.y - center.y * 100.0, 0.0))
        rot = Matrix.Rotation(ang, 3, 'Z') @ rel
        swirl.data[i].co = Vector((center.x * 100.0 + rot.x,
                                   center.y * 100.0 + rot.y,
                                   w.z + 20.0 * s))

    # ShimmerWave: diagonal vertex wave (static pose; loop in material for live)
    shimmer = add_morph("ShimmerWave")
    for i, v in enumerate(base.data.vertices):
        w = v.co
        off = Vector((0, 0, 12.0 * math.sin((w.x + w.y) * 0.012 + stagger(i) * 6.0)))
        shimmer.data[i].co = w + off
    _ = math

    # ---- root armature ---------------------------------------------------------
    ad = bpy.data.armatures.new("Dress_Root")
    arm = bpy.data.objects.new("Dress_Root", ad)
    bpy.context.collection.objects.link(arm)
    bpy.context.view_layer.objects.active = arm
    bpy.ops.object.mode_set(mode="EDIT")
    bone = ad.edit_bones.new("root")
    bone.head = (0, 0, 0)
    bone.tail = (0, 0, 200.0)
    bpy.ops.object.mode_set(mode="OBJECT")
    dress.parent = arm
    mod = dress.modifiers.new("Armature", "ARMATURE")
    mod.object = arm

    # ---- export ----------------------------------------------------------------
    bpy.ops.object.select_all(action="DESELECT")
    dress.select_set(True)
    arm.select_set(True)
    out_fbx = OUT_DIR / "SK_ShorewakeDress.fbx"
    bpy.ops.export_scene.fbx(filepath=str(out_fbx), use_selection=True,
                             add_leaf_bones=False, use_mesh_modifiers=False,
                             bake_anim=False, object_types={"MESH", "ARMATURE"})
    print(f"[nikki] wrote {out_fbx.name} ({out_fbx.stat().st_size} bytes)")

    # ---- QA render ---------------------------------------------------------------
    scene = bpy.context.scene
    scene.render.engine = "CYCLES"
    scene.cycles.device = "CPU"
    scene.cycles.samples = 24
    scene.render.resolution_x = 720
    scene.render.resolution_y = 960
    world = bpy.data.worlds.get("World") or bpy.data.worlds.new("World")
    scene.world = world
    world.use_nodes = True
    bg = world.node_tree.nodes.get("Background")
    if bg:
        bg.inputs[0].default_value = (0.03, 0.04, 0.06, 1.0)
    meshes = [dress]
    cam = autofit_cam(meshes, "DressQA", Vector((0.35, -0.75, 1.05)))
    scene.camera = cam
    for lname, loc, col, e in (("K", (2, -3, 3), (1.0, 0.88, 0.72), 36000.0),
                               ("F", (-3, -1.5, 1), (0.5, 0.85, 0.9), 17000.0),
                               ("R", (1, 2.5, 2), (0.75, 0.88, 1.0), 22000.0)):
        ld = bpy.data.lights.new(lname, "AREA")
        ld.energy = e
        ld.color = col
        ld.size = 120
        lo2 = bpy.data.objects.new(lname, ld)
        lo2.location = Vector(loc) * 40.0
        bpy.context.collection.objects.link(lo2)
    RENDER_DIR.mkdir(parents=True, exist_ok=True)
    scene.render.filepath = str(RENDER_DIR / "SHOREWAKE_TRANSFORM_QA.png")
    bpy.ops.render.render(write_still=True)
    print("[nikki] QA render -> SHOREWAKE_TRANSFORM_QA.png")

    manifest = {
        "schema": "melodia.shorewake_transform.v1",
        "source": str(USDZ), "panels": len(panels),
        "verts": len(dress.data.vertices), "polys": len(dress.data.polygons),
        "morph_targets": ["Basis", "Nikki_Bloom", "Nikki_Swirl", "ShimmerWave"],
        "transformation_sequence": {
            "1_gather": "Basis at 0.25 Hz micro-shimmer (ShimmerWave 10% loop)",
            "2_bloom": "Nikki_Bloom 0->1 over 0.8 s (panels cascade by stagger)",
            "3_swirl": "Nikki_Swirl 0->1 over 0.6 s while Bloom holds 0.5",
            "4_settle": "both back to 0 over 1.2 s; iridescent scale-shimmer "
                        "material carries the afterglow",
        },
        "material_recipe": "T_MelusinaC_DressShorewake_* base set + iridescent "
                           "shimmer = T_Jelly_Iridescence_LUT (fresnel -> U, "
                           "Irid_Mottle-style panner -> V) + T_Jelly_Nematocyst_Glints "
                           "sparkle; the dress wears the leviathan's legacy",
        "scale": "cm applied (x100)",
    }
    (OUT_DIR / "shorewake_transform_manifest.json").write_text(
        json.dumps(manifest, indent=2), encoding="utf-8")
    print("[nikki] manifest -> shorewake_transform_manifest.json")


def clear():
    bpy.ops.object.select_all(action="SELECT")
    bpy.ops.object.delete(use_global=False)


def autofit_cam(objs, name, offset_dir):
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
    data.clip_start = 0.1
    data.clip_end = 1e7
    cam = bpy.data.objects.new(name, data)
    cam.location = center + offset_dir.normalized() * diag * 1.35
    bpy.context.collection.objects.link(cam)
    tgt = bpy.data.objects.new(name + "_T", None)
    tgt.location = center
    bpy.context.collection.objects.link(tgt)
    c = cam.constraints.new("TRACK_TO")
    c.target = tgt
    return cam


if __name__ == "__main__":
    import math
    main()
