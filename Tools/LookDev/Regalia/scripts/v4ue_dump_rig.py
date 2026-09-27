"""Read-only: open Melusina R09 source (never saved), dump armature bone rest positions (world, Blender metres/BU)
plus ARP export settings, for the Blender->UE component-space similarity solve."""
import bpy, json, sys
from mathutils import Vector
OUT = r"C:\EnvironmentPortfolio\_lookdev_work\regalia_v2\ue_export_v4\melusina_rig_dump_v4.json"
sc = bpy.context.scene
R = {"src": bpy.data.filepath, "unit_scale": sc.unit_settings.scale_length, "unit_system": sc.unit_settings.system,
     "arp_props": {k: str(getattr(sc, k)) for k in dir(sc) if k.startswith("arp_") and not callable(getattr(sc, k, None))}, "armatures": {}}
body = bpy.data.objects.get("Melusina_Base")
R["body"] = None
if body:
    R["body"] = {"name": body.name, "mods": [(m.type, m.name, getattr(getattr(m, "object", None), "name", None)) for m in body.modifiers],
                 "parent": body.parent.name if body.parent else None, "matrix_world": [list(r) for r in body.matrix_world]}
for ob in bpy.data.objects:
    if ob.type != "ARMATURE": continue
    a = ob.data; mw = ob.matrix_world
    keys = [b for b in a.bones if any(t in b.name.lower() for t in ("head", "neck", "spine", "root", "eye", "jaw", "ear", "clav", "hand", "foot", "pelvis", "hips"))]
    R["armatures"][ob.name] = {"data": a.name, "n_bones": len(a.bones), "matrix_world": [list(r) for r in mw],
        "hidden": ob.hide_get() if ob.name in bpy.context.view_layer.objects else None,
        "bones": {b.name: {"head": list(mw @ b.head_local), "tail": list(mw @ b.tail_local), "roll_mat": [list(r) for r in (mw @ b.matrix_local)]} for b in keys}}
json.dump(R, open(OUT, "w"), indent=1)
print("V4UE-RIG", {k: (v["n_bones"], len(v["bones"])) for k, v in R["armatures"].items()}, "unit", R["unit_scale"], "body", R["body"] and R["body"]["mods"])
