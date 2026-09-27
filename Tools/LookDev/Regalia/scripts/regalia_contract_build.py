"""Build + stage + SAVE the circlet to a small standalone .blend, headless.

Why a new small file instead of saving the 2.4 GB harp WIP:
  * `blender -b` on Melusina_Harp_HERO01_*.blend and Melusina_DollKit_*.blend
    dies with EXCEPTION_ACCESS_VIOLATION inside blo_read_file_internal
    (crash 2026-09-25 19:08, stack: main_args_handle_load_file ->
    BKE_blendfile_read -> BLI_mmap_read). Reading those files headless is
    unsafe, so the regalia contract file must NOT be one of them.
  * Instead: take the measured head landmarks + the GN tree + one staged object
    and write a ~MB-scale .blend that opens headless. That file is the standing
    Phase-A contract every later regalia piece reuses.

Run:  blender -b --factory-startup --python regalia_contract_build.py
"""

import bpy
import json
import math
import os
import sys

HERE = os.path.dirname(os.path.abspath(__file__))
REG = r"C:\Users\froma\AppData\Roaming\Blender Foundation\Blender\5.2\scripts\addons"
if REG not in sys.path:
    sys.path.append(REG)

OUT_BLEND = os.path.join(HERE, "regalia_contract.blend")
OUT_JSON = os.path.join(HERE, "regalia_landmarks.json")

# ---- measured on the live head, Melusina_Base (z -0.187 .. 1.836) ----------
LANDMARKS = {
    "source": "Melusina_Base, live session MCP 9876, 18891 verts",
    "measured_utc_date": "2026-09-25",
    "overall": {"z_min": -0.1867, "z_max": 1.8356},
    "she_faces": "-Y",
    "brow": {"z": 1.560, "width": 0.4084, "depth": 0.4594,
             "centre": [-0.0044, -0.1335]},
    "crown": {"z": 1.80, "width": 0.2265},
    "neck": {"z": 1.368, "width": 0.1425},
    "ear_bones_world": {"c_ear_01.l": [0.1369, -0.1635, 1.5316],
                        "c_ear_01.r": [-0.1449, -0.1629, 1.5292]},
    "rig": {"armature": "character_rig", "bones": 1124,
            "anchor_bones": ["c_head.x", "c_neck.x", "c_shoulder.l", "c_shoulder.r",
                             "c_ear_01.l", "c_ear_01.r"]},
    "NOTE": ("BONE PARENTING IS UNSAFE HERE: parenting the circlet to c_head.x "
             "threw it to y=-1.72, about 1.5 m off the skull. Parent to the rig "
             "OBJECT (identity transform) instead -- the tree bakes world space."),
}


def main():
    import importlib.util
    # 1. build the tree (it only needs the addon, not the 2.4 GB file)
    P = os.path.join(HERE, "melusina_regalia_circlet.py")
    spec = importlib.util.spec_from_file_location("regalia_circlet", P)
    mod = importlib.util.module_from_spec(spec)
    sys.modules["regalia_circlet"] = mod
    spec.loader.exec_module(mod)
    tree = mod.build()

    # 2. A proxy head from the MEASURED landmarks -- no dependency on the 2.4 GB
    #    file, so this contract opens headless forever.
    #
    #    Built as a SCALED UV SPHERE, not a curve with a bevel. A curve's
    #    bevel_depth inflates the surface OUTWARD by that radius, which buried the
    #    circlet inside the proxy in the first render pass (nothing visible). A
    #    sphere's surface is exactly its scale, so half-width 0.204 puts the skin
    #    on the measured line and the circlet at radius*1.03 stands 6 mm proud.
    HEAD_HW = 0.204          # measured half-width at the brow
    HEAD_HD = 0.2295         # half-depth  (0.4594 / 2)
    HEAD_HH = 0.260          # half-height, roughly the z 1.42..1.835 span / 2
    bpy.ops.mesh.primitive_uv_sphere_add(segments=48, ring_count=24, radius=1.0,
                                         location=(0.0, 0.0, 0.0))
    prof_ob = bpy.context.active_object
    prof_ob.name = "Melusina_HeadProxy"
    prof_ob.data.name = "Melusina_HeadProxy"
    prof_ob.scale = (HEAD_HW, HEAD_HD, HEAD_HH)
    # place it on the measured head axis, brow height at its centre
    prof_ob.location = (LANDMARKS["brow"]["centre"][0],
                        LANDMARKS["brow"]["centre"][1],
                        LANDMARKS["brow"]["z"])
    bpy.ops.object.transform_apply(location=False, rotation=False, scale=True)

    # 3. the staged circlet
    coll = bpy.data.collections.new("REGALIA")
    bpy.context.scene.collection.children.link(coll)
    ob = bpy.data.objects.new("Melusina_Circlet", bpy.data.meshes.new("Melusina_Circlet"))
    coll.objects.link(ob)
    md = ob.modifiers.new("Circlet", "NODES")
    md.node_group = tree
    for it in tree.interface.items_tree:
        if getattr(it, "item_type", "") == "SOCKET" \
                and getattr(it, "in_out", "") == "INPUT" and hasattr(it, "default_value"):
            try:
                md.properties.inputs[it.identifier].update(value=it.default_value)
            except Exception:
                pass
    ob.location = (0.0, 0.0, 0.0)
    ob.rotation_euler = (0.0, 0.0, 0.0)
    ob.scale = (1.0, 1.0, 1.0)

    bpy.context.view_layer.update()
    bpy.context.scene.update_tag()
    dg = bpy.context.evaluated_depsgraph_get()
    oe = ob.evaluated_get(dg)
    me = oe.to_mesh()
    verts = len(me.vertices)
    mn = [round(min(v.co[i] for v in me.vertices), 4) for i in range(3)] if verts else None
    mx = [round(max(v.co[i] for v in me.vertices), 4) for i in range(3)] if verts else None
    oe.to_mesh_clear()

    LANDMARKS["circlet"] = {"tree": tree.name, "verts": verts,
                            "min": mn, "max": mx,
                            "dials": len([i for i in tree.interface.items_tree
                                          if getattr(i, "item_type", "") == "SOCKET"
                                          and getattr(i, "in_out", "") == "INPUT"])}

    # Disable version backups for this save: the existing regalia_contract.blend1 is
    # Perforce read-only, so Blender fails with "Unable to make version backup" and
    # refuses to save. Save WITHOUT a backup rather than running a broad p4/attrib
    # sweep (per the p4 traps: never attrib -R).
    try:
        bpy.context.preferences.filepaths.save_version = 0
    except Exception:
        pass
    bpy.ops.wm.save_as_mainfile(filepath=OUT_BLEND, copy=False)
    with open(OUT_JSON, "w", encoding="utf-8") as f:
        json.dump(LANDMARKS, f, indent=1)
    print("SAVED", OUT_BLEND, os.path.getsize(OUT_BLEND), "bytes")
    print("CIRCLET verts=%s min=%s max=%s" % (verts, mn, mx))


if __name__ == "__main__":
    main()
