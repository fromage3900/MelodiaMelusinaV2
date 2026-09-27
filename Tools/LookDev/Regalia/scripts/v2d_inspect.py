import bpy
from mathutils import Vector
for c in bpy.data.collections:
    print("COLL", c.name, [ch.name for ch in c.children], c.hide_render)
    for o in c.objects:
        if o.type in ("MESH","CURVE","FONT","EMPTY"):
            pts=[o.matrix_world @ Vector(b) for b in o.bound_box]
            mn=[min(p[i] for p in pts) for i in range(3)]; mx=[max(p[i] for p in pts) for i in range(3)]
            print("OBJ", c.name, o.name, o.type, "par", o.parent.name if o.parent else None,
                  "loc", tuple(round(v,4) for v in o.location), "scl", tuple(round(v,3) for v in o.scale),
                  "bb_mm", tuple(round((mx[i]-mn[i])*1000,1) for i in range(3)), "min", tuple(round(v,4) for v in mn), "max", tuple(round(v,4) for v in mx),
                  "mods", [m.type for m in o.modifiers])
