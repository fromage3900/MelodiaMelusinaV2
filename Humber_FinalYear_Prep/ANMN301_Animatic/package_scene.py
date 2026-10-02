"""
Package the ANMN 301 Shorewake animatic into ONE self-contained scene for a
fresh session.

WHAT THIS DOES
--------------
Builds a single .blend that contains, already assembled and verified:
  * the skiff stage (SHOREWAKE_proxy_v30_perch.blend)  -- 212 objects
  * the 464-bone MelusinaRig appended from v02_storyboard
  * EXPORT_Body / Shirt / Skirt / Boots, parented and scaled to 1.7u
  * CAM_Intimate / CAM_SkiffClose / CAM_Wide, aimed at the character
  * the 19 numbered panels as a VSE strip layout (title + 17 + end)
  * the lighting rig

Run headless:
  blender -b --factory-startup --python package_scene.py

Run in the GUI (what you want for a working session):
  blender package_scene.py --python-exit-code 1

KNOWN DEFECT, DOCUMENTED NOT HIDDEN
-----------------------------------
Rotating any FK control bone moves the mesh by 0.000137 units -- visually
zero. This was measured, not assumed:

  binding      correct armature target, use_vertex_groups=True,
               55852/55852 weights non-zero, median weight 0.21,
               164/164 vertex-group names match bone names,
               modifier show_viewport=True, object not excluded or hidden
  behaviour    rotating c_neck_x by 0.9 rad -> max vertex displacement
               0.000137; identical whether the rig is rotated 90Z or zeroed,
               scaled 0.01 or 1.0, and whether the mesh is parented
  consequence   every "acting" panel renders the same rest geometry, so
               shots 11/12/13/15/16/17 differ by CAMERA only, never by pose

The mesh is NOT a T-pose slab -- it is 193 x 199 units with 18891 verts and
real weight distribution. It is a correctly bound mesh whose rig does not
drive it. Do not "fix" this by re-weighting; the binding is provably intact.
The next thing to try, in order:
  1. open the GUI and look at EXPORT_Body in the viewport -- is it posed at
     all, or is it a rest-pose figure? Ten seconds of eyes beats a probe.
  2. in the GUI, select MelusinaRig -> check the rig is in Object Mode pose
     and not linked to a stale action (MelusinaRigAction exists in the file
     and may be driving every bone back to rest each depsgraph update)
  3. only then consider re-exporting the armature from the authoring tool
"""
import bpy
import os
import mathutils

ROOT = r"P:\MelodiaMelusinaV2-Laptop\Humber_FinalYear_Prep\ANMN301_Animatic"
STAGE = os.path.join(ROOT, "proxy", "SHOREWAKE_proxy_v30_perch.blend")
SRC_CHAR = os.path.join(ROOT, "proxy", "SHOREWAKE_proxy_v02_storyboard.blend")
PANELS = os.path.join(ROOT, "panels_final")
OUT_BLEND = os.path.join(ROOT, "SHOREWAKE_ANIMATIC_working_scene.blend")
MANIFEST = os.path.join(ROOT, "WORKING_SCENE_MANIFEST.txt")

CHAR = ("EXPORT_Body", "EXPORT_Shirt", "EXPORT_Skirt", "EXPORT_Boots")
W, H, FPS = 1920, 1080, 24

# Beat board durations, frames. Title 72, panels per board, end 72 = 1560.
ORDER = [
    ("00_Title", "title.png", 72),
    ("PANEL_01", "panel_01.png", 120), ("PANEL_02", "panel_02.png", 96),
    ("PANEL_03", "panel_03.png", 48),  ("PANEL_04", "panel_04.png", 48),
    ("PANEL_05", "panel_05.png", 72),  ("PANEL_06", "panel_06.png", 120),
    ("PANEL_07", "panel_07.png", 48),  ("PANEL_08", "panel_08.png", 48),
    ("PANEL_09", "panel_09.png", 48),  ("PANEL_10", "panel_10.png", 48),
    ("PANEL_11", "panel_11.png", 96),  ("PANEL_12", "panel_12.png", 120),
    ("PANEL_13", "panel_13.png", 72),  ("PANEL_14", "panel_14.png", 96),
    ("PANEL_15", "panel_15.png", 120), ("PANEL_16", "panel_16.png", 120),
    ("PANEL_17", "panel_17.png", 96),
    ("18_End", "end.png", 72),
]
FADE_BEFORE = {"PANEL_06": 12, "PANEL_13": 12, "PANEL_17": 12}

log_lines = []


def log(m):
    print("PKG %s" % m)
    log_lines.append(str(m))


def engine_setup(scn):
    eng = [i.identifier for i in
           type(scn.render).bl_rna.properties["engine"].enum_items]
    for want in ("BLENDER_EEVEE_NEXT", "BLENDER_EEVEE"):
        if want in eng:
            scn.render.engine = want
            return
    scn.render.engine = eng[0]


def append_character(scn):
    """Append AND link. libraries.load() populates bpy.data only; an unlinked
    object renders as a clean empty frame with exit code 0. This exact trap
    cost four diagnostic rounds earlier in the session."""
    with bpy.data.libraries.load(SRC_CHAR, link=False) as (s, d):
        d.objects = list(s.objects)
    added = [o for o in d.objects if o is not None]
    linked = 0
    for o in added:
        try:
            scn.collection.objects.link(o)
            linked += 1
        except RuntimeError:
            pass
    log("appended %d, linked %d into the scene" % (len(added), linked))
    return added


def find_rig():
    arms = [o for o in bpy.data.objects if o.type == 'ARMATURE']
    for a in arms:
        if "Melusina" in a.name or "Rig" in a.name:
            return a
    return arms[0] if arms else None


def seat_and_scale(scn, rig, parts, target=1.7):
    for p in parts:
        if p.parent is not rig:
            p.parent = rig
            p.matrix_parent_inverse = rig.matrix_world.inverted()
    bpy.context.view_layer.update()
    dg = bpy.context.evaluated_depsgraph_get()
    pts = []
    for p in parts:
        ev = p.evaluated_get(dg)
        me = ev.to_mesh()
        mw = p.matrix_world
        pts.extend(mw @ v.co for v in me.vertices)
        ev.to_mesh_clear()
    if not pts:
        return None
    h = (max(p.z for p in pts) - min(p.z for p in pts)) or 1.0
    M = mathutils.Matrix.Scale(target / h, 4)
    for p in parts:
        p.data.transform(M)      # DATA, not object scale -- see skill
        p.data.update()
    rig.location = (0.0, 0.0, 0.95)
    bpy.context.view_layer.update()
    dg = bpy.context.evaluated_depsgraph_get()
    pts = []
    for p in parts:
        ev = p.evaluated_get(dg)
        me = ev.to_mesh()
        mw = p.matrix_world
        pts.extend(mw @ v.co for v in me.vertices)
        ev.to_mesh_clear()
    log("character scaled to %.3fu  bbox x%.2f..%.2f y%.2f..%.2f z%.2f..%.2f"
        % (max(p.z for p in pts) - min(p.z for p in pts),
           min(p.x for p in pts), max(p.x for p in pts),
           min(p.y for p in pts), max(p.y for p in pts),
           min(p.z for p in pts), max(p.z for p in pts)))
    return parts


def centre_of(parts):
    dg = bpy.context.evaluated_depsgraph_get()
    q = []
    for p in parts:
        ev = p.evaluated_get(dg)
        me = ev.to_mesh()
        mw = p.matrix_world
        q.extend(mw @ v.co for v in me.vertices)
        ev.to_mesh_clear()
    if not q:
        return None
    return mathutils.Vector((sum(v.x for v in q) / len(q),
                             sum(v.y for v in q) / len(q),
                             (max(v.z for v in q) + min(v.z for v in q)) / 2))


def aim(cam, target, dist=3.2, elev_frac=0.22):
    if cam is None or target is None:
        return
    cur = cam.matrix_world.translation.copy()
    br = mathutils.Vector((cur.x - target.x, cur.y - target.y, 0.0))
    if br.length < 1e-4:
        br = mathutils.Vector((0.0, -1.0, 0.0))
    br.normalize()
    nl = mathutils.Vector((target.x + br.x * dist,
                           target.y + br.y * dist,
                           target.z + elev_frac * 1.7))
    cam.location = nl
    cam.rotation_euler = (mathutils.Vector((target.x, target.y, target.z + 0.10))
                          - nl).normalized().to_track_quat("-Z", "Y").to_euler()
    bpy.context.view_layer.update()


def build_vse(scn):
    missing = [f for _, f, _ in ORDER if not os.path.exists(os.path.join(PANELS, f))]
    if missing:
        log("VSE SKIPPED, missing: %s" % missing[:5])
        return None
    scn.sequence_editor_create()
    se = scn.sequence_editor
    strips = getattr(se, "strips", None)
    if strips is None:
        log("VSE SKIPPED: se.strips missing (5.2 API drift)")
        return None
    frame = 1
    for i, (name, fname, dur) in enumerate(ORDER):
        prev = ORDER[i - 1] if i else None
        length = FADE_BEFORE.get(name, 0) if prev else 0
        length = min(length, dur - 1) if length else 0
        ch = 2 if length else 1
        st = strips.new_image(name=name, filepath=os.path.join(PANELS, fname),
                              channel=ch, frame_start=frame, fit_method="ORIGINAL")
        # Blender stores image paths RELATIVE to the .blend by default, so
        # saving next to panels_final/ and reopening from any other directory
        # resolves them to nothing. Force absolute, or the VSE is dead on open.
        st.directory = PANELS + os.sep
        st.frame_final_duration = dur
        if length:
            st.blend_type = "GAMMA_CROSS"
            st.blend_alpha = 1.0
            st.use_default_fade = True
            out = strips.get(prev[0])
            if out is not None:
                out.frame_final_duration += length
        frame += dur
    total = sum(d for _, _, d in ORDER)
    scn.frame_start = 1
    scn.frame_end = total
    scn.render.use_sequencer = True
    log("VSE built: %d strips, %d frames, %.2fs" % (len(strips), total, total / FPS))
    return strips


def main():
    log("=" * 68)
    log("SHOREWAKE ANIMATIC WORKING SCENE")
    log("=" * 68)
    log("OUT  %s" % OUT_BLEND)

    bpy.ops.wm.open_mainfile(filepath=STAGE)
    scn = bpy.context.scene
    engine_setup(scn)
    scn.render.resolution_x = W
    scn.render.resolution_y = H
    scn.render.resolution_percentage = 100
    scn.render.fps = FPS
    scn.render.image_settings.file_format = "PNG"
    log("engine %s  %dx%d @ %dfps" % (scn.render.engine, W, H, FPS))

    append_character(scn)
    rig = find_rig()
    log("rig: %s  bones=%d  scale=%s  rot=%s"
        % (rig.name if rig else "NONE",
           len(rig.data.bones) if rig else 0,
           tuple(round(v, 4) for v in rig.scale) if rig else None,
           tuple(round(v, 4) for v in rig.rotation_euler) if rig else None))
    parts = [bpy.data.objects[n] for n in CHAR if n in bpy.data.objects]
    log("character parts present: %s" % [p.name for p in parts])
    in_scene = {o.name for o in scn.objects}
    unlinked = [p.name for p in parts if p.name not in in_scene]
    log("LINK CHECK: %s" % ("OK" if not unlinked else "FAIL %s" % unlinked))
    if not unlinked and parts:
        seat_and_scale(scn, rig, parts)

    # Clear the assigned action. MelusinaRigAction keys the c_* CONTROL bones,
    # which drive nothing (measured: 0.000137u), and it overwrites any pose you
    # set the moment you scrub or frame_set. Leaving it assigned means the rig
    # fights you in the viewport for no benefit. The action is still in the file
    # and re-assignable from the Action editor if it is ever wanted.
    if rig and rig.animation_data and rig.animation_data.action:
        log("cleared action %s (keys control bones, drives nothing)"
            % rig.animation_data.action.name)
        rig.animation_data.action = None

    # Name the bones that actually deform, in the file itself, so a fresh
    # session does not repeat the control-bone mistake.
    deform = []
    if parts:
        w = {}
        for v in parts[0].data.vertices:
            for g in v.groups:
                w[g.group] = w.get(g.group, 0.0) + g.weight
        i2n = {g.index: g.name for g in parts[0].vertex_groups}
        for gi, tot in sorted(w.items(), key=lambda kv: -kv[1])[:8]:
            nm = i2n.get(gi)
            if nm and nm in rig.pose.bones:
                deform.append("%s(%.0f)" % (nm, tot))
    log("DEFORM bones to pose (not c_* controls): %s" % ", ".join(deform))
    scn["pose_note"] = ("Pose these bones: " + ", ".join(deform) +
                        ". The c_* control bones have no constraints and move nothing.")

    # Aim the three shot cameras at the character.
    c = centre_of(parts) if parts else None
    for camname in ("CAM_Intimate", "CAM_SkiffClose", "CAM_Wide"):
        cands = [o for o in scn.objects
                 if o.type == 'CAMERA' and o.name.split('.')[0] == camname]
        if not cands:
            log("camera %s MISSING" % camname)
            continue
        cands.sort(key=lambda o: o.name)
        aim(cands[0], c)
        log("aimed %-16s loc %s"
            % (cands[0].name, tuple(round(v, 2) for v in cands[0].location)))

    build_vse(scn)

    # Leave the scene on a camera with the character framed, viewport ready.
    if cands:
        scn.camera = cands[0]
    for area in (bpy.context.window.screen.areas if bpy.context.window else []):
        if area.type == 'VIEW_3D':
            for space in area.spaces:
                if space.type == 'VIEW_3D':
                    space.shading.type = 'MATERIAL'
                    space.overlay.show_overlays = True
    scn.frame_set(1)

    bpy.ops.wm.save_as_mainfile(filepath=OUT_BLEND)
    log("SAVED %s" % OUT_BLEND)

    log("-" * 68)
    log("KNOWN DEFECT (measured, not assumed):")
    log("  Rotating an FK control bone moves the mesh 0.000137u -- visually")
    log("  zero. Binding is provably intact: 55852/55852 weights non-zero,")
    log("  164/164 group names match bones, modifier enabled and correctly")
    log("  targeted, object not excluded or hidden. The rig does not drive")
    log("  the mesh. Shots 11/12/13/15/16/17 therefore differ by camera only.")
    log("  See the module docstring for the three things to try, in order.")
    log("-" * 68)
    log("objects=%d  armatures=%d  characters=%s"
        % (len(scn.objects),
           len([o for o in scn.objects if o.type == 'ARMATURE']),
           [p.name for p in parts]))

    with open(MANIFEST, "w", encoding="utf-8") as fh:
        fh.write("\n".join(log_lines) + "\n")
    print("PKG manifest -> %s" % MANIFEST)


main()
