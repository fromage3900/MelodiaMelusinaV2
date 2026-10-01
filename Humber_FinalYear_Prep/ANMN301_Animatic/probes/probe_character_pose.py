"""Is the animatic character actually POSED, or is it sitting in rest position?

The decisive question from the panel review: shots 16 and 17 read as a T-pose
with the head cropped. That is either

  (a) a FRAMING problem - the pose is fine but the camera crops it, or
  (b) a POSING problem - there is no pose, just the armature's rest position.

This probes the saved v04 blend and answers it with numbers, not a render.

Read-only. Opens the file in its own process, writes nothing, touches no
existing scene.

Usage:
  blender -b --factory-startup --python probe_character_pose.py -- \
      /path/to/SHOREWAKE_VSE_animatic_v04.blend
"""
import sys

import bpy
from mathutils import Vector

argv = sys.argv[sys.argv.index("--") + 1:] if "--" in sys.argv else []
BLEND = argv[0] if argv else None
if not BLEND:
    print("PROBE no blend path given")
    sys.exit(2)

bpy.ops.wm.open_mainfile(filepath=BLEND)
scene = bpy.context.scene

print("PROBE blend=%s" % BLEND)
print("PROBE frame range %d..%d  fps=%d" % (scene.frame_start, scene.frame_end,
                                            scene.render.fps))

# ---- find the character: an armature + the mesh deformed by it -------------
arms = [o for o in scene.objects if o.type == 'ARMATURE']
meshes = [o for o in scene.objects if o.type == 'MESH']
print("PROBE armatures=%d meshes=%d" % (len(arms), len(meshes)))
for a in arms:
    print("PROBE armature name=%r bones=%d" % (a.name, len(a.data.bones)))
    print("PROBE armature loc=%s scale=%s"
          % ([round(v, 3) for v in a.location], [round(v, 3) for v in a.scale]))

deformed = [o for o in meshes if o.modifiers and any(
    m.type == 'ARMATURE' for m in o.modifiers)]
print("PROBE meshes with armature modifier: %s"
      % [(o.name, len(o.data.vertices)) for o in deformed])

if not arms:
    print("PROBE RESULT NO_ARMATURE - character is not in this file")
    sys.exit(0)

arm = arms[0]

# ---- is any bone actually rotated away from rest? --------------------------
# Compare each pose bone's matrix against the REST bone matrix. An unposed
# rig has pose_bone.matrix == bone.matrix_local for every bone. This is the
# number that separates (a) from (b) with no rendering involved.
pb = arm.pose.bones
moved = []
for bone in pb:
    rest = arm.data.bones[bone.name].matrix_local
    delta = max(abs(bone.matrix[r][c] - rest[r][c])
                for r in range(4) for c in range(4))
    if delta > 1e-4:
        moved.append((bone.name, delta))
moved.sort(key=lambda kv: -kv[1])
print("PROBE bones moved from rest: %d / %d" % (len(moved), len(pb)))
for name, d in moved[:12]:
    print("PROBE   moved %-28s delta %.5f" % (name, d))

# A T-pose specifically: are the shoulder/upper-arm bones rotated outward?
for side in ("L", "R"):
    for bn in ("upper_arm", "upperarm", "shoulder", "deltoid"):
        cand = [b for b in pb if bn in b.name.lower() and side.lower() in b.name.lower()]
        for c in cand[:1]:
            print("PROBE %s: location=%s rotation_mode=%s"
                  % (c.name, [round(v, 3) for v in c.location], c.rotation_mode))

# ---- is the character in frame for the cameras? ---------------------------
def world_bbox(obj):
    mw = obj.matrix_world
    pts = [mw @ Vector(c) for c in obj.bound_box]
    return (Vector((min(p.x for p in pts), min(p.y for p in pts), min(p.z for p in pts))),
            Vector((max(p.x for p in pts), max(p.y for p in pts), max(p.z for p in pts))))


cams = [o for o in scene.objects if o.type == 'CAMERA']
print("PROBE cameras: %s" % [c.name for c in cams])

if deformed:
    lo, hi = world_bbox(deformed[0])
    print("PROBE character world bbox: %s .. %s"
          % ([round(v, 3) for v in lo], [round(v, 3) for v in hi]))
    height = hi.z - lo.z
    print("PROBE character height %.3f units" % height)

    from bpy_extras.object_utils import world_to_camera_view
    for cam in cams:
        ndc = [world_to_camera_view(scene, cam, Vector(p))
               for p in (lo, hi, (lo + hi) * 0.5)]
        xs = [n.x for n in ndc]
        ys = [n.y for n in ndc]
        inside = all(0.0 <= n.x <= 1.0 for n in ndc) and all(0.0 <= n.y <= 1.0 for n in ndc)
        print("PROBE cam %-22s ndc x %.3f..%.3f  y %.3f..%.3f  z %.2f..%.2f  %s"
              % (cam.name, min(xs), max(xs), min(ys), max(ys),
                 ndc[0].z, ndc[2].z,
                 "BOTH CORNERS IN FRAME" if inside else "CROPPED"))

print("PROBE RESULT %s"
      % ("POSED" if moved else "REST_POSITION_NO_POSE"))