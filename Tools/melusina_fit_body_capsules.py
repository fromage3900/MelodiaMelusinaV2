"""H3: fit body collision capsules from Melusina_Base weights (headless, working copy only).

Per deform bone: verts whose dominant weight is that bone, expressed in bone space at rest.
Capsule axis = bone Y, radius = 70th percentile perpendicular distance, length = vert extent on Y.
Writes the list to a text block 'MELUSINA_BODY_CAPSULES' in the blend and to Saved/Audit as JSON.
"""
import bpy, json, os, sys
from mathutils import Vector

RIG, BODY = "character_rig", "Melusina_Base"
# Limbs subdivided into ARP's stretch + twist segments: one capsule per segment.
LIMB_SEGMENTS = ["{0}_stretch", "{0}_twist", "{0}_twist_2"]
BONES = ["root.x", "spine_01.x", "spine_02.x", "spine_03.x", "subneck_twist_1.x", "neck.x", "head.x"] + [
    seg.format(limb) + side for limb in ("thigh", "leg", "arm", "forearm") for side in (".l", ".r")
    for seg in LIMB_SEGMENTS]
OUT = "C:/EnvironmentPortfolio/BS_GodFile/Saved/Audit/p0_closeout_2026-09-24/h3_body_capsules.json"

rig, body = bpy.data.objects[RIG], bpy.data.objects[BODY]
gi = {g.index: g.name for g in body.vertex_groups}
buckets = {b: [] for b in BONES}
for v in body.data.vertices:
    if not v.groups:
        continue
    g = max(v.groups, key=lambda x: x.weight)
    name = gi.get(g.group)
    if name in buckets and g.weight > 0.5:
        buckets[name].append(body.matrix_world @ v.co)

caps = []
for name in BONES:
    bone = rig.data.bones.get(name)
    pts = buckets[name]
    if bone is None or len(pts) < 8:
        print(f"CAPSULE_SKIP {name} bone={'ok' if bone else 'missing'} verts={len(pts)}")
        continue
    inv = (rig.matrix_world @ bone.matrix_local).inverted()
    local = [inv @ p for p in pts]
    ys = sorted(p.y for p in local)
    rs = sorted(Vector((p.x, p.z)).length for p in local)
    r = rs[int(len(rs) * 0.7)]
    y0, y1 = ys[int(len(ys) * 0.05)], ys[int(len(ys) * 0.95)]
    s = rig.matrix_world.to_scale().x * 100.0  # metres -> cm
    caps.append({"bone": name, "radius_cm": round(r * s, 2), "length_cm": round(max(0.0, y1 - y0 - 2 * r) * s, 2),
                 "center_y_cm": round((y0 + y1) * 0.5 * s, 2), "verts": len(pts)})
    print(f"CAPSULE {caps[-1]}")

txt = bpy.data.texts.get("MELUSINA_BODY_CAPSULES") or bpy.data.texts.new("MELUSINA_BODY_CAPSULES")
txt.from_string(json.dumps(caps, indent=1))
with open(OUT, "w") as f:
    json.dump(caps, f, indent=1)
if "--save" in sys.argv:
    bpy.ops.wm.save_mainfile()
    print("SAVED")
print(f"CAPSULES_DONE {len(caps)}")
sys.stdout.flush(); os._exit(0)  # ARP leaves threads that hang -b exit
