"""Render ALL 17 Shorewake panels with the CANONICAL rigged Melusina.

Why all 17 and not just the six: panels_v3 was rendered from a deck scene with
ZERO armatures, so every acting shot in the beat board (02, 04, 05, 06, 07, 08,
14) rendered an EMPTY DECK. Only 11/12/13/15/16/17 were ever re-rendered, and
those carried the untextured EXPORT_* character. This renders the whole board
against the canonical rig.

Pose vocabulary is measured — see CANONICAL_RIG_CONTROL_MAP.md.
Camera distance is derived from the lens and her height, never hardcoded.

Run: blender -b --factory-startup <swap blend> --python render_all_panels.py
"""
import bpy, os, sys, math, mathutils

ROOT = r"P:\MelodiaMelusinaV2-Laptop\Humber_FinalYear_Prep\ANMN301_Animatic"
OUTDIR = os.path.join(ROOT, "proxy", "panels_v5")
BODY = "Melusina"

def log(m):
    print("PANEL %s" % m); sys.stdout.flush()

# --------------------------------------------------------------- base poses
# Measured axis meanings (all verified numerically):
#   c_spine_0N.x / c_neck.x / c_head.x  +X = lean/bow FORWARD (-Y)
#   c_head.x Y  +Y = turn toward -X      c_head.x Z = roll
#   c_hand_ik.l/r  loc Z negative = arm lowers;  X = swing fore/aft
#   c_foot_ik.l/r  loc Y positive = foot forward;  Z positive = foot lifts
#   c_root.x       loc Y positive = body lowers (seated)
SEATED = {
    "c_root.x":     dict(loc=(0.0, 0.42, 0.0)),
    "c_foot_ik.l":  dict(loc=(0.0, 0.46, 0.30)),
    "c_foot_ik.r":  dict(loc=(0.0, 0.46, 0.30)),
    "c_hand_ik.l":  dict(loc=(0.10, 0.0, -0.58)),
    "c_hand_ik.r":  dict(loc=(0.10, 0.0, -0.58)),
    "c_shoulder.l": dict(rot=(0.0, 0.0, -0.10)),
    "c_shoulder.r": dict(rot=(0.0, 0.0,  0.10)),
}
STANDING = {
    "c_hand_ik.l":  dict(loc=(0.10, 0.0, -0.52)),
    "c_hand_ik.r":  dict(loc=(0.10, 0.0, -0.52)),
    "c_shoulder.l": dict(rot=(0.0, 0.0, -0.08)),
    "c_shoulder.r": dict(rot=(0.0, 0.0,  0.08)),
}

def merge(*layers):
    out = {}
    for L in layers:
        for k, v in L.items():
            cur = dict(out.get(k, {})); cur.update(v); out[k] = cur
    return out

# --------------------------------------------------------------- the board
# cam / margin / pose / light. margin 1.22-1.30 intimate, 1.5+ wide.
SHOTS = {
    "01": dict(cam="CAM_Wide", margin=1.30, frame="boat", sun=1.5, water=0.0, lantern=0.0,
               pose=merge(STANDING, {})),
    "02": dict(cam="CAM_Intimate",   margin=1.30, sun=2.5, water=0.0, lantern=0.0,
               pose=merge(SEATED, {
                   "c_head.x":  dict(rot=(0.22, 0.0, 0.0)),
                   "c_neck.x":  dict(rot=(0.10, 0.0, 0.0)),
                   "c_spine_02.x": dict(rot=(0.08, 0.0, 0.0))})),
    "03": dict(cam="CAM_SkiffClose", margin=1.30, frame="boat", sun=2.5, water=0.0, lantern=0.0,
               pose=merge(STANDING, {})),
    "04": dict(cam="CAM_Intimate",   margin=1.35, sun=4.0, water=1.0, lantern=3.0,
               pose=merge(SEATED, {
                   "c_head.x":  dict(rot=(-0.10, 0.0, 0.0)),
                   "c_hand_ik.l": dict(loc=(0.22, 0.0, -0.30)),
                   "c_hand_ik.r": dict(loc=(0.06, 0.0, -0.52))})),
    "05": dict(cam="CAM_Wide",       margin=1.60, sun=2.0, water=0.5, lantern=0.5,
               pose=merge(SEATED, {
                   "c_head.x":  dict(rot=(0.16, 0.0, 0.0)),
                   "c_spine_02.x": dict(rot=(0.06, 0.0, 0.0))})),
    "06": dict(cam="CAM_Intimate",   margin=1.32, sun=4.0, water=1.0, lantern=1.0,
               pose=merge(SEATED, {
                   "c_head.x":  dict(rot=(-0.06, 0.0, 0.0)),
                   "c_hand_ik.l": dict(loc=(0.24, 0.0, -0.22)),
                   "c_hand_ik.r": dict(loc=(0.20, 0.0, -0.26))})),
    "07": dict(cam="CAM_Intimate",   margin=1.30, sun=4.5, water=2.0, lantern=2.0,
               pose=merge(SEATED, {
                   "c_head.x":  dict(rot=(0.10, 0.0, 0.0)),
                   "c_hand_ik.l": dict(loc=(0.26, 0.0, -0.20)),
                   "c_hand_ik.r": dict(loc=(0.22, 0.0, -0.24))})),
    "08": dict(cam="CAM_Wide",       margin=1.55, sun=5.0, water=3.0, lantern=3.0,
               pose=merge(SEATED, {
                   "c_head.x":  dict(rot=(-0.04, 0.0, 0.0)),
                   "c_hand_ik.l": dict(loc=(0.26, 0.0, -0.18)),
                   "c_hand_ik.r": dict(loc=(0.22, 0.0, -0.22))})),
    "09": dict(cam="CAM_Wide", margin=1.30, frame="boat", sun=5.5, water=3.5, lantern=4.0,
               pose=merge(STANDING, {})),
    "10": dict(cam="CAM_Wide", margin=1.30, frame="boat", sun=6.0, water=4.0, lantern=4.0,
               pose=merge(STANDING, {})),
    "11": dict(cam="CAM_Intimate",   margin=1.24, sun=5.0, water=1.5, lantern=0.0,
               pose=merge(SEATED, {
                   "c_head.x":  dict(rot=(0.42, 0.0, 0.0)),
                   "c_neck.x":  dict(rot=(0.20, 0.0, 0.0)),
                   "c_subneck_1.x": dict(rot=(0.10, 0.0, 0.0)),
                   "c_spine_02.x": dict(rot=(0.14, 0.0, 0.0)),
                   "c_spine_01.x": dict(rot=(0.07, 0.0, 0.0)),
                   "c_hand_ik.l": dict(loc=(0.10, 0.0, -0.62)),
                   "c_hand_ik.r": dict(loc=(0.10, 0.0, -0.62))})),
    "12": dict(cam="CAM_Intimate",   margin=1.26, sun=6.0, water=4.0, lantern=4.0,
               pose=merge(SEATED, {
                   "c_head.x":  dict(rot=(-0.26, 0.0, 0.0)),
                   "c_neck.x":  dict(rot=(-0.12, 0.0, 0.0)),
                   "c_spine_02.x": dict(rot=(-0.08, 0.0, 0.0)),
                   "c_hand_ik.l": dict(loc=(0.16, 0.0, -0.40)),
                   "c_hand_ik.r": dict(loc=(0.16, 0.0, -0.40))})),
    "13": dict(cam="CAM_SkiffClose", margin=1.30, frame="boat", hull_z=0.30,
               pose=merge(STANDING, {}), sun=6.0, water=4.0, lantern=4.0),
    "14": dict(cam="CAM_SkiffClose", margin=1.40, sun=6.0, water=4.0, lantern=4.0,
               pose=merge(STANDING, {
                   "c_head.x":  dict(rot=(0.08, 0.0, 0.0)),
                   "c_root_master.x": dict(loc=(0.0, 0.0, 0.0))})),
    "15": dict(cam="CAM_Wide", margin=1.45, frame="boat", glide_x=-1.2,
               pose=merge(STANDING, {}), sun=6.0, water=4.0, lantern=4.0),
    "16": dict(cam="CAM_Wide",       margin=1.55, sun=6.0, water=4.0, lantern=4.0,
               pose=merge(SEATED, {
                   "c_head.x":  dict(rot=(0.0, -0.42, 0.0)),
                   "c_neck.x":  dict(rot=(0.0, -0.20, 0.0)),
                   "c_spine_02.x": dict(rot=(0.0, 0.0, 0.12))})),
    "17": dict(cam="CAM_Intimate",   margin=1.28, sun=6.0, water=4.0, lantern=4.0,
               pose=merge(SEATED, {
                   "c_head.x":  dict(rot=(0.0, 0.44, 0.0)),
                   "c_neck.x":  dict(rot=(0.0, 0.22, 0.0)),
                   "c_spine_02.x": dict(rot=(-0.06, 0.0, 0.0)),
                   "c_hand_ik.l": dict(loc=(0.12, 0.0, -0.50)),
                   "c_hand_ik.r": dict(loc=(0.12, 0.0, -0.50))})),
}

def find_rig():
    for o in bpy.data.objects:
        if o.type == "ARMATURE" and o.name == "character_rig":
            return o
    return None

def apply_pose(rig, pose):
    if rig is None:
        return
    if rig.animation_data and rig.animation_data.action:
        rig.animation_data.action = None
    for pb in rig.pose.bones:
        pb.rotation_mode = "XYZ"
        pb.rotation_euler = (0.0, 0.0, 0.0)
        pb.location = (0.0, 0.0, 0.0)
    for name, spec in (pose or {}).items():
        pb = rig.pose.bones.get(name)
        if pb is None:
            log("  SKIP %s (no such bone)" % name); continue
        if "rot" in spec:
            pb.rotation_mode = "XYZ"; pb.rotation_euler = spec["rot"]
        if "loc" in spec:
            pb.location = spec["loc"]
    bpy.context.view_layer.update()

def body_bounds():
    o = bpy.data.objects[BODY]
    dg = bpy.context.evaluated_depsgraph_get()
    ev = o.evaluated_get(dg); me = ev.to_mesh(); mw = ev.matrix_world
    pts = [mw @ v.co for v in me.vertices]
    lo = mathutils.Vector((min(p.x for p in pts), min(p.y for p in pts), min(p.z for p in pts)))
    hi = mathutils.Vector((max(p.x for p in pts), max(p.y for p in pts), max(p.z for p in pts)))
    ev.to_mesh_clear()
    return lo, hi

# Hull only. Including mast/boom/sail makes the bounding box tall and thin, so
# fitting that box leaves the hull small and the frame mostly empty.
BOAT_KEYS = ("hull", "skiff", "gunwale", "floorboard", "deckwell")

def boat_bounds():
    """Bounds of the vessel itself, for the establishing shots.

    Those shots are about the mooring, not the character: framing her puts a
    standing figure in a shot the beat board calls 'skiff tethered, no light'.
    """
    pts = []
    dg = bpy.context.evaluated_depsgraph_get()
    for o in bpy.data.objects:
        if o.type != "MESH":
            continue
        n = o.name.lower()
        if not any(k in n for k in BOAT_KEYS):
            continue
        ev = o.evaluated_get(dg); me = ev.to_mesh(); mw = ev.matrix_world
        for v in me.vertices:
            pts.append(mw @ v.co)
        ev.to_mesh_clear()
    if not pts:
        return None, None
    lo = mathutils.Vector((min(p.x for p in pts), min(p.y for p in pts), min(p.z for p in pts)))
    hi = mathutils.Vector((max(p.x for p in pts), max(p.y for p in pts), max(p.z for p in pts)))
    return lo, hi

def fit_distance_box(cam, width, height, margin):
    """Distance that fits BOTH the width and the height of a bounding box.

    The hull is 7.68 long but only 1.21 tall. Fitting only the height put the
    camera so close that the boat ran off both sides of the frame.
    """
    scn = bpy.context.scene
    lens = cam.data.lens
    sw = cam.data.sensor_width
    aspect = scn.render.resolution_x / scn.render.resolution_y
    if cam.data.sensor_fit == 'VERTICAL':
        sh = cam.data.sensor_height; swid = sh * aspect
    elif cam.data.sensor_fit == 'HORIZONTAL':
        swid = sw; sh = sw / aspect
    else:
        if aspect >= 1.0:
            swid = sw; sh = sw / aspect
        else:
            sh = sw; swid = sw * aspect
    vfov = 2.0 * math.atan((sh * 0.5) / lens)
    hfov = 2.0 * math.atan((swid * 0.5) / lens)
    dv = (height * margin * 0.5) / math.tan(vfov * 0.5)
    dh = (width * margin * 0.5) / math.tan(hfov * 0.5)
    return max(dv, dh)

def fit_distance(cam, height, margin):
    scn = bpy.context.scene
    lens = cam.data.lens
    sw = cam.data.sensor_width
    if cam.data.sensor_fit == 'VERTICAL':
        sh = cam.data.sensor_height
    elif cam.data.sensor_fit == 'HORIZONTAL':
        sh = sw * (scn.render.resolution_y / scn.render.resolution_x)
    else:
        sh = (sw * (scn.render.resolution_y / scn.render.resolution_x)
              if scn.render.resolution_x >= scn.render.resolution_y else sw)
    vfov = 2.0 * math.atan((sh * 0.5) / lens)
    return (height * margin * 0.5) / math.tan(vfov * 0.5)

def aim(cam, centre, height, margin, box=None):
    cur = cam.matrix_world.translation.copy()
    bearing = mathutils.Vector((cur.x - centre.x, cur.y - centre.y, 0.0))
    if bearing.length < 1e-4:
        bearing = mathutils.Vector((0.0, -1.0, 0.0))
    bearing.normalize()
    if box is not None:
        # horizontal extent as seen from this bearing, not just the max axis
        width = abs(box.x * bearing.y) + abs(box.y * bearing.x)
        dist = fit_distance_box(cam, width, box.z, margin)
    else:
        dist = fit_distance(cam, height, margin)
    elev = 0.10 * height
    loc = mathutils.Vector((centre.x + bearing.x * dist,
                            centre.y + bearing.y * dist,
                            centre.z + elev))
    cam.location = loc
    aimpt = mathutils.Vector((centre.x, centre.y, centre.z))
    cam.rotation_euler = (aimpt - loc).normalized().to_track_quat("-Z", "Y").to_euler()
    bpy.context.view_layer.update()
    return dist

def verify(cam):
    from bpy_extras.object_utils import world_to_camera_view
    scn = bpy.context.scene
    o = bpy.data.objects[BODY]
    dg = bpy.context.evaluated_depsgraph_get()
    ev = o.evaluated_get(dg); me = ev.to_mesh(); mw = ev.matrix_world
    uv = [world_to_camera_view(scn, cam, mw @ v.co) for v in me.vertices]
    ev.to_mesh_clear()
    inside = sum(1 for c in uv if 0.0 <= c.x <= 1.0 and 0.0 <= c.y <= 1.0 and c.z > 0)
    pct = 100.0 * inside / max(1, len(uv))
    vs = [c.y for c in uv]
    log("  VERIFY %s inside=%.1f%% v=[%.2f..%.2f] %s" % (
        cam.name, pct, min(vs), max(vs), "PASS" if pct > 97.0 else "FAIL-CLIPPED"))
    return pct > 97.0

def set_light(sun, water, lantern):
    for o in bpy.data.objects:
        if o.type != "LIGHT":
            continue
        n = o.name.lower()
        if "sun" in n:
            o.data.energy = sun
        elif "lantern" in n:
            o.data.energy = lantern
            if o.data.type == "POINT":
                o.data.color = (1.0, 0.82, 0.55)
    for o in bpy.data.objects:
        if o.type != "MESH" or "water" not in o.name.lower():
            continue
        slots = getattr(o.data, "materials", None)
        if not slots or not slots[0] or not slots[0].use_nodes:
            continue
        for nd in slots[0].node_tree.nodes:
            if nd.type == "EMISSION":
                nd.inputs["Strength"].default_value = water
                break

def apply_moves(hull_z=None, glide_x=None):
    if glide_x is not None:
        for o in bpy.data.objects:
            if o.type == "MESH" and ("hull" in o.name.lower() or "skiff" in o.name.lower()):
                o.location.x += glide_x
    if hull_z is not None:
        for o in bpy.data.objects:
            if o.type == "MESH" and ("hull" in o.name.lower() or "skiff" in o.name.lower()):
                o.location.z += hull_z

def main():
    os.makedirs(OUTDIR, exist_ok=True)
    scn = bpy.context.scene
    scn.render.use_sequencer = False
    scn.render.resolution_x = 1920
    scn.render.resolution_y = 1080
    scn.render.image_settings.file_format = "PNG"
    rig = find_rig()
    log("rig=%s objects=%d" % (rig.name if rig else None, len(bpy.data.objects)))
    # trial filter: ONLY_SHOTS=11,16 renders a subset. TRIAL=1 writes to a
    # separate folder so a test can never overwrite good panels.
    _only = [s for s in os.environ.get("ONLY_SHOTS", "").split(",") if s]
    shots = [s for s in sorted(SHOTS) if (not _only or s in _only)]
    outdir = OUTDIR + "_trial" if os.environ.get("TRIAL") else OUTDIR
    os.makedirs(outdir, exist_ok=True)
    log("rendering %d shots: %s -> %s" % (len(shots), shots, outdir))
    for n in ("L_Cornea", "R_Cornea"):
        o = bpy.data.objects.get(n)
        if o and o.hide_render:
            o.hide_render = False
    fails = []
    for shot in shots:
        spec = SHOTS[shot]
        apply_pose(rig, spec["pose"])
        apply_moves(spec.get("hull_z"), spec.get("glide_x"))
        if spec.get("frame") == "boat":
            lo, hi = boat_bounds()
            if lo is None:
                lo, hi = body_bounds()
            else:
                log("  shot %s framing the BOAT" % shot)
        else:
            lo, hi = body_bounds()
        ctr = (lo + hi) * 0.5
        h = hi.z - lo.z
        cam = bpy.data.objects.get(spec["cam"]) or scn.camera
        scn.camera = cam
        if spec.get("frame") == "boat":
            d = aim(cam, ctr, h, spec["margin"], box=(hi - lo))
        else:
            d = aim(cam, ctr, h, spec["margin"])
        if spec.get("frame") == "boat":
            log("  (establishing shot - character framing not asserted)")
        else:
            if not verify(cam):
                fails.append(shot)
        set_light(spec["sun"], spec["water"], spec["lantern"])
        scn.render.filepath = os.path.join(outdir, "panel_%s.png" % shot)
        log("shot %s h=%.2f dist=%.2f -> %s" % (shot, h, d, scn.render.filepath))
        bpy.ops.render.render(write_still=True)
    log("DONE fails=%s -> %s" % (fails, OUTDIR))

main()