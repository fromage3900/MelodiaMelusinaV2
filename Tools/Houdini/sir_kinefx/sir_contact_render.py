"""Sir KineFX contact sheets (Blender 4.5 headless EEVEE + Houdini-side data).

Why Blender pixels in a KineFX lane: the OpenGL ROP segfaults headless on
this GPU-less workstation (see cathedral/shot_cathedral_ogl.py docstring —
verified backtrace, environmental). Mantra CPU is 5-9 min/frame. EEVEE
headless is proven here (eevee_probe.png). So: KineFX/Houdini owns the
instrumentation (intake, wingtip travel, Wingbeat phase selection), Blender
owns the pixels, PIL owns the sheets. On a GPU machine, swap this renderer
for the OpenGL ROP with identical frame picks.

Per clip: import SKM mesh FBX once, attach each clip FBX action to the rig,
frame an ortho side camera on the cycle bounds, render 6 phases (frames
picked from Wingbeat_curves_v5 peaks where available, else even spacing),
assemble one labeled contact sheet per clip + a v5-vs-v6 Fly pair sheet.

  blender --background --python Tools/Houdini/sir_kinefx/sir_contact_render.py
"""
import bpy
import json
import math
from mathutils import Vector
from pathlib import Path

REPO = Path("C:/EnvironmentPortfolio/BS_GodFile")
AUDIT = REPO / "Saved/Audit/SirMelodious_FlightUnit_20261003"
DOCTOR = REPO / "Saved/Audit/sirmelodious_kinefx_doctor"
SKM = AUDIT / "exports/ue_arp/SKM_SirMelodious_ARP_CrestTie_v5.fbx"
CLIP_DIR = AUDIT / "exports/ue_arp"
OUT = DOCTOR / "contact"
OUT.mkdir(parents=True, exist_ok=True)

CLIPS = ["A_Sir_Fly_Loop_v6_ARP", "A_Sir_Hover_Idle_v6_ARP", "A_Sir_Glide_v6_ARP",
         "A_Sir_Takeoff_v6_ARP", "A_Sir_Land_v6_ARP", "A_Sir_Fly_Loop_v5_ARP"]

WING = json.loads((CLIP_DIR / "Wingbeat_curves_v5.json").read_text())
WT = json.loads((DOCTOR / "wingtip_probe.json").read_text())["clips"]


def pick_frames(clip: str, f0: int, f1: int) -> list[int]:
    base = clip.replace("_v6_ARP", "").replace("_ARP", "")
    keys = None
    for k, v in WING.items():
        if base.startswith(k.split("_v")[0]) or k.startswith(base.split("_v")[0]):
            keys = v["keys"]
            break
    if keys:
        peaks = [f for f, val in keys if val > 0.9]
        v = sorted(set([f0] + peaks[:4] + [f1]))
        return [x for x in v if f0 <= x <= f1][:6]
    n = f1 - f0
    return [f0 + int(n * t) for t in (0, 0.2, 0.4, 0.6, 0.8, 1.0)]


def attach_action(rig, action):
    """Blender 4.4+ layered actions: assigning .action is NOT enough when the
    action was imported onto a different armature — the slot must follow."""
    if rig.animation_data is None:
        rig.animation_data_create()
    rig.animation_data.action = action
    slots = list(action.slots)
    slot = next((s for s in slots if s.target_id_type == "ARMATURE"), None)
    if slot is None and slots:
        slot = slots[0]
    if slot is not None:
        try:
            rig.animation_data.action_slot = slot
        except Exception:
            pass
    return slot.name_display if slot is not None else None


def wipe():
    bpy.ops.object.select_all(action="SELECT")
    bpy.ops.object.delete(use_global=False)
    for dbs in (bpy.data.meshes, bpy.data.armatures, bpy.data.actions):
        for b in list(dbs):
            dbs.remove(b)


def setup_stage():
    sc = bpy.context.scene
    wipe()
    bpy.ops.import_scene.fbx(filepath=str(SKM))
    rig = next(o for o in sc.objects if o.type == "ARMATURE")
    meshes = [o for o in sc.objects if o.type == "MESH"]
    for o in list(sc.objects):
        if o.type in ("CURVE", "LIGHT", "CAMERA"):
            bpy.data.objects.remove(o, do_unlink=True)
    cam_d = bpy.data.cameras.new("SIR_Cam")
    cam_d.type = "ORTHO"
    cam = bpy.data.objects.new("SIR_Cam", cam_d)
    sc.collection.objects.link(cam)
    sc.camera = cam
    for n, e, r in (("SIR_Key", 3.0, (55, 0, -35)), ("SIR_Fill", 1.0, (60, 0, 40))):
        ld = bpy.data.lights.new(n, "SUN")
        ld.energy = e
        lo = bpy.data.objects.new(n, ld)
        sc.collection.objects.link(lo)
        lo.rotation_euler = tuple(math.radians(x) for x in r)
    w = sc.world or bpy.data.worlds.new("SIR_W")
    sc.world = w
    w.use_nodes = True
    bg = w.node_tree.nodes.get("Background")
    if bg:
        bg.inputs[0].default_value = (0.10, 0.09, 0.12, 1)
        bg.inputs[1].default_value = 1.0
    engines = [i.identifier for i in
               bpy.types.RenderSettings.bl_rna.properties["engine"].enum_items]
    sc.render.engine = ("BLENDER_EEVEE_NEXT" if "BLENDER_EEVEE_NEXT" in engines
                        else "BLENDER_EEVEE")
    sc.render.resolution_x, sc.render.resolution_y = 960, 540
    sc.render.resolution_percentage = 100
    sc.render.film_transparent = False
    sc.render.image_settings.file_format = "PNG"
    try:
        sc.view_settings.view_transform = "Standard"
    except Exception:
        pass
    return sc, rig, meshes


def frame_camera(sc, cam, rig, meshes, action):
    attach_action(rig, action)
    f0, f1 = int(action.frame_range[0]), int(action.frame_range[1])
    # Frame on BONE bounds (pose-driven), not mesh bounds: the v5 body mesh
    # carries stray verts ~3.5 m out at rest, which would shrink the bird to
    # a dot (seen 2026-10-07). Mesh-vs-bone extent check is banked below.
    lo = Vector((1e9,) * 3)
    hi = Vector((-1e9,) * 3)
    bones = [b.name for b in rig.data.bones]
    for f in range(f0, f1 + 1, max(1, (f1 - f0) // 8)):
        sc.frame_set(f)
        bpy.context.view_layer.update()
        for bn in bones:
            for p in (rig.matrix_world @ rig.pose.bones[bn].head,
                      rig.matrix_world @ rig.pose.bones[bn].tail):
                lo = Vector(map(min, lo, p))
                hi = Vector(map(max, hi, p))
    bone_span = hi - lo
    sc.frame_set(f0)
    bpy.context.view_layer.update()
    mesh_lo = Vector((1e9,) * 3)
    mesh_hi = Vector((-1e9,) * 3)
    dg = bpy.context.evaluated_depsgraph_get()
    for o in meshes:
        try:
            for c in o.evaluated_get(dg).bound_box:
                w = o.matrix_world @ Vector(c)
                mesh_lo = Vector(map(min, mesh_lo, w))
                mesh_hi = Vector(map(max, mesh_hi, w))
        except Exception:
            continue
    mesh_span = mesh_hi - mesh_lo
    stray = max(mesh_span) / max(max(bone_span), 1e-6)
    ctr = (lo + hi) / 2
    span = max(bone_span.x, bone_span.y, bone_span.z, 0.01)
    cam.data.ortho_scale = span * 2.0
    # Side profile: wingspan runs along X, flap travels in Z — park the
    # camera on +X looking down -X so the stroke reads vertically.
    cam.location = (ctr.x + 3 * span, ctr.y, ctr.z)
    cam.rotation_mode = "QUATERNION"
    cam.rotation_quaternion = Vector((-1, 0, 0)).to_track_quat("-Z", "Y")
    cam.data.clip_end = 100 * span
    return f0, f1, {"bone_span": [round(v, 3) for v in bone_span],
                   "mesh_span": [round(v, 3) for v in mesh_span],
                   "mesh_vs_bone": round(stray, 2)}


rep = {"clips": {}}
sc, rig, meshes = setup_stage()
for clip in CLIPS:
    try:
        before = set(bpy.data.actions)
        bpy.ops.import_scene.fbx(filepath=str(CLIP_DIR / (clip + ".fbx")))
        new_actions = [a for a in bpy.data.actions if a not in before]
        if not new_actions:
            rep["clips"][clip] = {"error": "no action on clip import"}
            continue
        action = sorted(new_actions, key=lambda a: len(a.fcurves or []))[-1]
        # drop the clip's own armature, keep its action on our SKM rig
        for o in [o for o in sc.objects if o.type == "ARMATURE" and o is not rig]:
            bpy.data.objects.remove(o, do_unlink=True)
        f0, f1, span_check = frame_camera(sc, sc.camera, rig, meshes, action)
        attach_action(rig, action)
        frames = pick_frames(clip, f0, f1)
        shots = []
        for i, f in enumerate(frames):
            sc.frame_set(f)
            bpy.context.view_layer.update()
            fp = str(OUT / f"sir_{clip}_f{f:03d}.png")
            sc.render.filepath = fp
            bpy.ops.render.render(write_still=True)
            shots.append({"frame": f, "path": fp})
        rep["clips"][clip] = {"frames": [f0, f1], "shots": shots,
                              "action": action.name, "status": "DONE",
                              "span_check": span_check}
        bpy.data.actions.remove(action)
        print(f"[sir] {clip}: {len(shots)} frames DONE")
    except Exception:
        import traceback
        rep["clips"][clip] = {"error": traceback.format_exc()[-1200:]}
        print(f"[sir] {clip}: EXCEPTION")
json.dump(rep, open(OUT / "render_report.json", "w"), indent=1)
print("wrote", OUT / "render_report.json")
