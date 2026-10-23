"""PASS C — STARSKIFF-lane finale: merge the magical layer onto the owner's
posed/rigged Shorewake dress and ship SK_ShorewakeDress_Magical.fbx.

Input : C:\\Users\\froma\\OneDrive\\Desktop\\shorewake.fbx   (owner's asset of
        record: 48 posed panels weighted to the v22 Melusina rig)
        + magical_ridges.obj / magical_scales.obj / scales_plates.json /
        ridges_inflate.json (Pass B, same space)

Steps:
  1. import FBX; label 48 material slots SW_Dress_P01..48
  2. join panels (panel vertex ranges recorded for morph stagger)
  3. import ridges/scales; transfer skin weights (nearest face); join
  4. author 5 morph targets:
     Nikki_Bloom / Nikki_Swirl / ShimmerWave  (panel-staggered)
     ScaleFlip     (plates mirror through their plane)
     FluffInflate  (tuft tips push outward)
  5. QA renders (neutral + transformation pose) + manifest
Exports: Saved/Audit/sea_above/skiff/SK_ShorewakeDress_Magical.fbx
Run:  blender -b --factory-startup -noaudio --python shorewake_pass_c.py
"""

import json
from pathlib import Path

import bpy
from mathutils import Vector

PROJECT_ROOT = Path(__file__).resolve().parents[3]
SRC = Path(r"C:\Users\froma\OneDrive\Desktop\shorewake.fbx")
MAG = PROJECT_ROOT / "Saved/Audit/melusina_lookdev/magical"
OUT_DIR = PROJECT_ROOT / "Saved/Audit/sea_above/skiff"
CM = 100.0


def clear():
    bpy.ops.object.select_all(action="SELECT")
    bpy.ops.object.delete(use_global=False)


def main():
    clear()
    before = set(bpy.data.objects)
    bpy.ops.import_scene.fbx(filepath=str(SRC))
    new = [o for o in bpy.data.objects if o not in before]
    panels = sorted([o for o in new if o.type == "MESH"
                     and "dressedit" in o.name.lower()],
                    key=lambda o: int("".join(c for c in o.name if c.isdigit()) or 999))
    arm = next((o for o in new if o.type == "ARMATURE"), None)
    print(f"[passC] panels={len(panels)} armature={arm.name if arm else None}")
    assert len(panels) == 48 and arm, "unexpected FBX structure"

    # 1) labeled materials
    for i, p in enumerate(panels, start=1):
        mat = bpy.data.materials.new(f"SW_Dress_P{i:02d}")
        mat.use_nodes = True
        p.data.materials.clear()
        p.data.materials.append(mat)

    # 2) join panels (ranges recorded in join order)
    ranges = []
    start = 0
    for p in panels:
        n = len(p.data.vertices)
        ranges.append((start, start + n))
        start += n
    for p in panels:
        p.select_set(True)
    bpy.context.view_layer.objects.active = panels[0]
    bpy.ops.object.join()
    dress = bpy.context.object
    dress.name = "SK_ShorewakeDress"
    dress.scale = (CM, CM, CM)
    bpy.ops.object.transform_apply(scale=True)
    bpy.ops.object.mode_set(mode="EDIT")
    bpy.ops.mesh.select_all(action="SELECT")
    bpy.ops.mesh.normals_make_consistent(inside=False)
    bpy.ops.object.mode_set(mode="OBJECT")
    print(f"[passC] joined dress: {len(dress.data.vertices)} verts")

    # 3) magical geometry + skin-weight transfer
    magical = []
    for obj_name, obj_file in (("SW_Magical_Ridges", "magical_ridges.obj"),
                               ("SW_Magical_Scales", "magical_scales.obj")):
        before = set(bpy.data.objects)
        bpy.ops.wm.obj_import(filepath=str(MAG / obj_file))
        mo = [o for o in bpy.data.objects if o not in before][0]
        mo.name = obj_name
        mo.scale = (CM, CM, CM)
        bpy.ops.object.transform_apply(scale=True)
        dt = mo.modifiers.new("SkinWeights", "DATA_TRANSFER")
        dt.object = dress
        dt.use_vert_data = True
        dt.data_types_verts = {"VGROUP_WEIGHTS"}
        dt.vert_mapping = "POLYINTERP_NEAREST"
        dt.layers_vgroup_select_src = "ALL"
        dt.layers_vgroup_select_dst = "NAME"
        try:
            bpy.context.view_layer.objects.active = mo
            bpy.ops.object.modifier_apply(modifier="SkinWeights")
        except Exception as e:
            print(f"[passC] weight transfer warn ({obj_name}): {str(e)[:120]}")
        magical.append(mo)
        print(f"[passC] {obj_name}: {len(mo.data.vertices)} verts weighted")

    # 4) join magical into the dress
    for mo in magical:
        mo.select_set(True)
    dress.select_set(True)
    bpy.context.view_layer.objects.active = dress
    bpy.ops.object.join()

    # 5) morphs
    def add_morph(name):
        return dress.shape_key_add(name=name)

    dress.shape_key_add(name="Basis")
    vtotal = len(dress.data.vertices)
    n_dress = 183741
    n_ridge = 8240

    bloom = add_morph("Nikki_Bloom")
    swirl = add_morph("Nikki_Swirl")
    shimmer = add_morph("ShimmerWave")
    flip = add_morph("ScaleFlip")
    inflate = add_morph("FluffInflate")

    from mathutils import Matrix
    plates = json.loads((MAG / "scales_plates.json").read_text())["plates"]
    inflate_data = json.loads((MAG / "ridges_inflate.json").read_text())["inflate"]
    scale_v0 = n_dress + n_ridge

    for i, v in enumerate(dress.data.vertices):
        w = v.co
        if i < n_dress:                                    # dress panels
            pi = min(i // 3828, 47)                        # 183741/48 ≈ 3828
            s = pi / 47.0
            d = Vector((w.x, w.y, 0.0))
            if d.length < 1e-4:
                d = Vector((0, 0, 1))
            d.normalize()
            bloom.data[i].co = w + d * (60.0 * s) + Vector((0, 0, 55.0 * s))
            rel = Vector((w.x, w.y, 0.0))
            rot = Matrix.Rotation(math.radians(70.0) * s, 3, "Z") @ rel
            swirl.data[i].co = Vector((rot.x, rot.y, w.z + 20.0 * s))
            shimmer.data[i].co = w + Vector((0, 0, 12.0 * math.sin(
                (w.x + w.y) * 0.012 + s * 6.0)))
        elif i < n_dress + n_ridge:                        # ridge tuft tip
            k = (i - n_dress)
            if k % 2 == 1 and k // 2 < len(inflate_data):
                off = inflate_data[k // 2]
                inflate.data[i].co = w + Vector((off[0] * CM, off[1] * CM,
                                                 off[2] * CM * 2.2))
        else:                                              # scale plates
            k = (i - n_dress - n_ridge) // 7
            if k < len(plates):
                pl = plates[k]
                c = Vector((pl["center"][0] * CM, pl["center"][1] * CM,
                            pl["center"][2] * CM))
                n = Vector((pl["normal"][0], pl["normal"][1],
                            pl["normal"][2])).normalized()
                rel = w - c
                flipped = w - n * (2.0 * rel.dot(n))
                spin = Matrix.Rotation(math.pi, 3, "Z")
                rel2 = spin @ (flipped - c)
                flip.data[i].co = c + rel2 + n * (5.0)
            else:
                flip.data[i].co = w
    print("[passC] morphs authored: Basis, Nikki_Bloom, Nikki_Swirl, "
          "ShimmerWave, ScaleFlip, FluffInflate")

    # keep the armature deforming everything
    if not any(m.type == "ARMATURE" for m in dress.modifiers):
        am = dress.modifiers.new("Armature", "ARMATURE")
        am.object = arm
    dress.parent = arm

    # 6) export + QA renders
    bpy.ops.object.select_all(action="DESELECT")
    dress.select_set(True)
    arm.select_set(True)
    out_fbx = OUT_DIR / "SK_ShorewakeDress_Magical.fbx"
    OUT_DIR.mkdir(parents=True, exist_ok=True)
    bpy.ops.export_scene.fbx(filepath=str(out_fbx), use_selection=True,
                             add_leaf_bones=False, use_mesh_modifiers=False,
                             bake_anim=False, object_types={"MESH", "ARMATURE"})
    print(f"[passC] wrote {out_fbx.name} ({out_fbx.stat().st_size} bytes)")

    scene = bpy.context.scene
    scene.render.engine = "CYCLES"
    scene.cycles.device = "CPU"
    scene.cycles.samples = 24
    scene.render.resolution_x = 900
    scene.render.resolution_y = 1200
    world = bpy.data.worlds.get("World") or bpy.data.worlds.new("World")
    scene.world = world
    world.use_nodes = True
    bg = world.node_tree.nodes.get("Background")
    if bg:
        bg.inputs[0].default_value = (0.04, 0.05, 0.07, 1.0)
    lo = Vector((1e9,) * 3)
    hi = Vector((-1e9,) * 3)
    for c in dress.bound_box:
        w = dress.matrix_world @ Vector(c)
        lo = Vector(map(min, lo, w))
        hi = Vector(map(max, hi, w))
    center = (lo + hi) / 2.0
    diag = max((hi - lo).length, 1.0)
    for name, morph_vals, offset, dist_scale in (
            ("DRESS_Neutral", {}, Vector((0.6, -1.1, 0.5)), 0.9),
            ("DRESS_Transform", {"Nikki_Bloom": 0.7, "ScaleFlip": 0.8,
                                 "FluffInflate": 0.9, "ShimmerWave": 0.5},
             Vector((0.9, -0.9, 0.9)), 1.7)):
        if morph_vals:
            for mn, mv in morph_vals.items():
                dress.data.shape_keys.key_blocks[mn].value = mv
        data = bpy.data.cameras.new(name)
        data.lens = 50
        data.clip_end = 1e7
        cam = bpy.data.objects.new(name, data)
        cam.location = center + offset.normalized() * diag * dist_scale
        bpy.context.collection.objects.link(cam)
        tgt = bpy.data.objects.new(name + "_T", None)
        tgt.location = center
        bpy.context.collection.objects.link(tgt)
        cc = cam.constraints.new("TRACK_TO")
        cc.target = tgt
        scene.camera = cam
        for lname, loc, col, e in (("K", (2, -3, 3), (1.0, 0.88, 0.72), 60000.0),
                                   ("F", (-3, -1.5, 1), (0.5, 0.85, 0.9), 26000.0),
                                   ("R", (1, 2.5, 2), (0.75, 0.88, 1.0), 34000.0)):
            ld = bpy.data.lights.new(lname, "AREA")
            ld.energy = e
            ld.color = col
            ld.size = diag * 0.4
            lo2 = bpy.data.objects.new(lname, ld)
            lo2.location = center + Vector(loc).normalized() * diag * 0.8
            bpy.context.collection.objects.link(lo2)
        scene.render.filepath = str(OUT_DIR / f"{name}.png")
        bpy.ops.render.render(write_still=True)
        print(f"[passC] render {name}.png")
        for mn, _mv in morph_vals.items():
            dress.data.shape_keys.key_blocks[mn].value = 0.0

    manifest = {
        "schema": "melodia.shorewake_magical.v1",
        "source": str(SRC),
        "export": str(out_fbx),
        "slots": 48, "morph_targets": ["Basis", "Nikki_Bloom", "Nikki_Swirl",
                                       "ShimmerWave", "ScaleFlip", "FluffInflate"],
        "verts": vtotal,
        "magical_layer": {"ridges": n_ridge, "plates": len(plates),
                          "plate_flip": "mirror through plate plane + 180 spin "
                                        "+ 12 cm push",
                          "fluff_inflate": "tuft tips +radial x2.2 (cm)"},
        "renders": ["DRESS_Neutral.png", "DRESS_Transform.png"],
    }
    (OUT_DIR / "shorewake_magical_manifest.json").write_text(
        json.dumps(manifest, indent=2), encoding="utf-8")
    print("[passC] manifest -> shorewake_magical_manifest.json")


if __name__ == "__main__":
    import math
    main()
