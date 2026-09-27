# READ-ONLY inspection of the Melusina source blend. Never saves.
import bpy
from mathutils import Vector
print("V3I-FILE", bpy.data.filepath, "scene", bpy.context.scene.name, "unit", bpy.context.scene.unit_settings.scale_length)
for c in bpy.data.collections:
    print("V3I-COLL", c.name, "objs", len(c.objects), "hide_r", c.hide_render)
rows = []
for o in bpy.data.objects:
    if o.type not in ("MESH", "CURVES", "CURVE", "ARMATURE", "EMPTY"): continue
    try:
        pts = [o.matrix_world @ Vector(b) for b in o.bound_box]
        mn = [min(p[i] for p in pts) for i in range(3)]; mx = [max(p[i] for p in pts) for i in range(3)]
    except Exception: mn = mx = [0, 0, 0]
    nv = len(o.data.vertices) if o.type == "MESH" else (len(o.data.points) if o.type == "CURVES" else -1)
    mods = ",".join(m.type for m in o.modifiers) if hasattr(o, "modifiers") else ""
    mats = ",".join((s.material.name if s.material else "-") for s in o.material_slots)[:120] if hasattr(o, "material_slots") else ""
    rows.append((o.name, o.type, nv, o.parent.name if o.parent else "", o.hide_render, o.hide_get() if o.name in bpy.context.view_layer.objects else "nvl",
                 [round(v, 3) for v in mn], [round(v, 3) for v in mx], mods, mats, [c.name for c in o.users_collection]))
for r in rows: print("V3I-OBJ", r)
