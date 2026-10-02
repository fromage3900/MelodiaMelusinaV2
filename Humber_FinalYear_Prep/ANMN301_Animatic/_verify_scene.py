"""Independent verification: reopen the packaged scene from disk and assert
everything the manifest claims. Never trust the build script's own report."""
import bpy
import os

OUT = (r"P:\MelodiaMelusinaV2-Laptop\Humber_FinalYear_Prep\ANMN301_Animatic"
       r"\SHOREWAKE_ANIMATIC_working_scene.blend")
bpy.ops.wm.open_mainfile(filepath=OUT)
scn = bpy.context.scene
CHAR = ("EXPORT_Body", "EXPORT_Shirt", "EXPORT_Skirt", "EXPORT_Boots")

checks = []


def chk(name, ok, detail=""):
    checks.append((name, bool(ok), detail))


in_scene = {o.name for o in scn.objects}
arms = [o for o in scn.objects if o.type == 'ARMATURE']
parts = [bpy.data.objects.get(n) for n in CHAR]

chk("file reopens", True, OUT)
chk("engine EEVEE", scn.render.engine == "BLENDER_EEVEE", scn.render.engine)
chk("1920x1080", scn.render.resolution_x == 1920 and scn.render.resolution_y == 1080)
chk("24 fps", scn.render.fps == 24, str(scn.render.fps))
chk("exactly 1 armature", len(arms) == 1, str([a.name for a in arms]))
chk("rig has 464 bones", arms and len(arms[0].data.bones) == 464,
    str(len(arms[0].data.bones)) if arms else "0")
chk("all 4 char parts present", all(parts))
chk("all 4 char parts LINKED", all(p and p.name in in_scene for p in parts),
    str([p.name for p in parts if p and p.name not in in_scene]))
chk("all 4 parented to rig", all(p and p.parent is arms[0] for p in parts))

# Character size, measured on the evaluated mesh
dg = bpy.context.evaluated_depsgraph_get()
pts = []
for p in parts:
    if not p:
        continue
    ev = p.evaluated_get(dg)
    me = ev.to_mesh()
    mw = p.matrix_world
    pts.extend(mw @ v.co for v in me.vertices)
    ev.to_mesh_clear()
if pts:
    h = max(v.z for v in pts) - min(v.z for v in pts)
    chk("character ~1.7-2.1u tall", 1.5 < h < 2.2, "%.3fu" % h)
    chk("character above deck (z>0.5)", min(v.z for v in pts) > 0.5,
        "zmin %.2f" % min(v.z for v in pts))

cams = [o for o in scn.objects if o.type == 'CAMERA']
chk("3+ cameras", len(cams) >= 3, str([c.name for c in cams]))
chk("scene camera set", scn.camera is not None,
    scn.camera.name if scn.camera else "None")

se = scn.sequence_editor
if se and getattr(se, "strips", None) is not None:
    st = se.strips
    chk("VSE 19 strips", len(st) == 19, str(len(st)))
    chk("VSE covers 1560 frames", scn.frame_end == 1560, str(scn.frame_end))
    gammas = [s.name for s in st if getattr(s, "blend_type", "") == "GAMMA_CROSS"]
    chk("3 gamma-cross dissolves", len(gammas) == 3, str(gammas))
    chk("use_sequencer on", scn.render.use_sequencer)
else:
    chk("VSE present", False, "no sequence editor")

# Every referenced panel file must exist on disk.
# NOTE: ImageStrip has no `.filepath` attribute in 5.2 — a verifier that reads
# it gets None and reports every strip as missing, which looks exactly like a
# broken VSE. The real path is directory + elements[0].filename.
missing = []
if se and getattr(se, "strips", None) is not None:
    for s in se.strips:
        if s.type == 'IMAGE':
            full = os.path.join(s.directory, s.elements[0].filename)
            if not os.path.exists(full):
                missing.append(s.name)
chk("all 19 panel files on disk", not missing, str(missing[:5]))

print("VERIFY " + "=" * 60)
fails = 0
for name, ok, detail in checks:
    if not ok:
        fails += 1
    print("VERIFY %-34s %s  %s" % (name, "PASS" if ok else "FAIL", detail))
print("VERIFY " + "=" * 60)
print("VERIFY %d checks, %d failed" % (len(checks), fails))
print("VERIFY objects=%d  armatures=%d" % (len(scn.objects), len(arms)))
print("VERIFY DONE")
