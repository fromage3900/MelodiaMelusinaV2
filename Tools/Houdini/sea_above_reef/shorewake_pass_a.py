"""PASS A — Starskiff-lane dress: inspect the owner's posed shorewake.fbx and
export posed dress meshes as OBJ for the Houdini magical pass.

Read-only on the owner's file. Exports:
  Saved/Audit/melusina_lookdev/magical/passA_inventory.json
  Saved/Audit/melusina_lookdev/magical/posed/<MeshName>.obj   (world space, Y-up)
Run:  blender -b --factory-startup -noaudio --python shorewake_pass_a.py
"""

import json
from pathlib import Path

import bpy
from mathutils import Vector

PROJECT_ROOT = Path(__file__).resolve().parents[3]
SRC = Path(r"C:\Users\froma\OneDrive\Desktop\shorewake.fbx")
OUT = PROJECT_ROOT / "Saved/Audit/melusina_lookdev/magical"
POSED = OUT / "posed"


def main():
    assert SRC.exists(), f"missing {SRC}"
    bpy.ops.wm.open_mainfile(filepath=str(SRC)) if SRC.suffix == ".blend" else None
    if SRC.suffix == ".fbx":
        clear()
        before = set(bpy.data.objects)
        bpy.ops.import_scene.fbx(filepath=str(SRC))
        new = [o for o in bpy.data.objects if o not in before]
    else:
        new = list(bpy.data.objects)

    meshes = [o for o in new if o.type == "MESH"]
    armatures = [o for o in new if o.type == "ARMATURE"]
    morphs = {}
    for o in meshes:
        if o.data.shape_keys:
            morphs[o.name] = [k.name for k in o.data.shape_keys.key_blocks]
    inv = {
        "source": str(SRC),
        "objects": [{"name": o.name, "type": o.type,
                     "verts": len(o.data.vertices) if o.type == "MESH" else 0,
                     "polys": len(o.data.polygons) if o.type == "MESH" else 0,
                     "materials": [s.material.name if s.material else None
                                   for s in o.material_slots]}
                    for o in new],
        "armatures": [a.name for a in armatures],
        "morphs": morphs,
        "materials": [m.name for m in bpy.data.materials if m.users],
    }
    OUT.mkdir(parents=True, exist_ok=True)
    (OUT / "passA_inventory.json").write_text(json.dumps(inv, indent=2),
                                              encoding="utf-8")
    print(f"[passA] objects={len(new)} meshes={len(meshes)} "
          f"armatures={len(armatures)} morphed={list(morphs.keys())}")

    # export every mesh as posed OBJ (world space); Houdini picks the dress set
    POSED.mkdir(parents=True, exist_ok=True)
    bpy.ops.object.select_all(action="DESELECT")
    for o in meshes:
        o.select_set(True)
    bpy.context.view_layer.objects.active = meshes[0]
    bpy.ops.wm.obj_export(filepath=str(POSED / "shorewake_all_meshes.obj"),
                          export_selected_objects=True,
                          forward_axis="NEGATIVE_Z", up_axis="Y")
    print(f"[passA] posed OBJ -> shorewake_all_meshes.obj "
          f"({(POSED / 'shorewake_all_meshes.obj').stat().st_size} bytes)")


def clear():
    bpy.ops.object.select_all(action="SELECT")
    bpy.ops.object.delete(use_global=False)


if __name__ == "__main__":
    main()
