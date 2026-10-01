"""
Shorewake animatic repair — restore the character, re-render the duplicate panels.

WHY THIS EXISTS
---------------
panels_v3 was rendered from SHOREWAKE_proxy_v27_deck.blend, which has ZERO
armatures: the MelusinaRig (464 bones) lived in proxy_v02_storyboard.blend and
was dropped when the MK38 skiff was appended at v03. Every "acting" shot in the
beat board therefore rendered the same empty deck, and 6 of 17 panels came out
pixel-identical (11/12/17 and 13/15/16).

This script appends the rigged character from v02_storyboard into the current
v30 scene, then re-renders ONLY the panels that were duplicates, each with the
camera + pose + light state the beat board actually specifies.

Run:  blender -b --factory-startup --python animatic_fix.py
"""

import bpy
import os
import sys
import math
import mathutils

ROOT = r"P:\MelodiaMelusinaV2-Laptop\Humber_FinalYear_Prep\ANMN301_Animatic"
SRC_CHAR = os.path.join(ROOT, "proxy", "SHOREWAKE_proxy_v02_storyboard.blend")
STAGE = os.path.join(ROOT, "proxy", "SHOREWAKE_proxy_v30_perch.blend")
OUT_PANELS = os.path.join(ROOT, "proxy", "panels_v4")

# Panels that came out pixel-identical in panels_v3, and what the beat board
# says each one should actually show. Duration is carried by the VSE, not here.
#
# POSE FORMAT: bone -> (x, y, z) euler. Every control in this rig is a
# single-axis "_x" bone — there is no c_neck_y. The beat board's "neck Y"
# means rotate c_head_x on its Y euler, not that a Y bone exists.
REDO = {
    "11": dict(  # doubt beat — she almost stops, then plays on
        cam="CAM_Intimate",
        pose={"c_neck_x": (0.45, 0, 0), "c_spine_03_x": (0.20, 0, 0),
              "c_arm_fk_l": (-0.27, 0, 0), "c_arm_fk_r": (-0.27, 0, 0)},
        sun=5.0, water=1.5, lantern=0.0,
    ),
    "12": dict(  # second phrase, full — head up, phrase completes, light spreads
        cam="CAM_Intimate",
        pose={"c_neck_x": (-0.25, 0, 0), "c_spine_03_x": (-0.10, 0, 0),
              "c_arm_fk_l": (-0.60, 0, 0), "c_arm_fk_r": (-0.60, 0, 0),
              "c_forearm_fk_l": (-0.45, 0, 0), "c_forearm_fk_r": (-0.45, 0, 0)},
        sun=6.0, water=4.0, lantern=4.0,
    ),
    "13": dict(  # skiff wakes — hull lifts, rope taut
        cam="CAM_SkiffClose",
        pose={}, hull_z=0.30,
        sun=6.0, water=4.0, lantern=4.0,
    ),
    "15": dict(  # crossing — skiff glides through the lit reef
        cam="CAM_Wide",
        pose={}, glide_x=-1.2,
        sun=6.0, water=4.0, lantern=4.0,
    ),
    "16": dict(  # shore route opens — dark water parts, far shore glows
        cam="CAM_Wide",
        # Two defects, both proven by this script's own log:
        #  * "c_head_x" is NOT a bone in this rig. Probed all 464: the neck
        #    controls are c_neck_x / c_neck_master_x / c_subneck_1_x / neck_x.
        #    apply_pose() logged nothing for it, so the head stayed in REST.
        #  * no arm was posed at all, and this rig's rest pose is a T-POSE —
        #    which is exactly what the panel review saw.
        # She reaches toward the far shore as it lights.
        pose={"c_neck_x": (-0.10, -0.18, 0.0),
              "c_spine_03_x": (0.10, 0, 0),
              "c_arm_fk_l": (0.18, 0.0, 0.30),
              "c_arm_fk_r": (0.34, 0.0, -0.55),
              "c_forearm_fk_l": (-0.30, 0, 0),
              "c_forearm_fk_r": (-0.72, 0, 0),
              "c_hand_fk_l": (0.10, 0, 0),
              "c_hand_fk_r": (0.20, 0, 0)},
        glide_x=-2.4,
        sun=6.0, water=4.0, lantern=4.0,
    ),
    "17": dict(  # arrival look-back — mooring behind, awake
        cam="CAM_Intimate",
        # Same two defects. The beat board says "awake" — she has just arrived
        # and is looking back at the mooring, so the arms come down and hold,
        # and the neck carries the look.
        pose={"c_neck_x": (0.0, -0.30, 0.0),
              "c_spine_02_x": (-0.06, 0, 0),
              "c_arm_fk_l": (0.30, 0.0, 0.22),
              "c_arm_fk_r": (0.22, 0.0, -0.26),
              "c_forearm_fk_l": (-0.55, 0, 0),
              "c_forearm_fk_r": (-0.42, 0, 0),
              "c_hand_fk_l": (0.15, 0, 0),
              "c_hand_fk_r": (0.10, 0, 0)},
        sun=6.0, water=4.0, lantern=4.0,
    ),
}


def log(msg):
    print("ANIMFIX %s" % msg)
    sys.stdout.flush()


def append_character():
    """Bring the 464-bone MelusinaRig across from the v02 storyboard blend.

    Two defects make a naive append silently useless:

    1. SCALE. The storyboard rig is authored in centimetres (~183 units tall)
       while the skiff scene is in metres (hull spans 7.6u). Appending as-is
       puts her ~100x oversized, outside every camera frustum — the panels
       come out clean, empty, and correct-looking. Rescale the rig AND its
       meshes together, or the modifier binding breaks.

    2. PARENTING. Only EXPORT_Body carries the Armature modifier in the source
       file. EXPORT_Shirt / Skirt / Boots arrive with parent=None, so posing the
       rig moves one mesh and leaves the other three behind. Parent them
       explicitly or she comes apart at the first pose.
    """
    before = set(o.name for o in bpy.data.objects)
    with bpy.data.libraries.load(SRC_CHAR, link=False) as (src, dst):
        dst.objects = list(src.objects)
    added = [o for o in dst.objects if o is not None and o.name not in before]
    log("appended %d objects from v02" % len(added))

    # CRITICAL: bpy.data.libraries.load() populates bpy.data but does NOT link
    # anything into the scene collection. An unlinked object is invisible to
    # the renderer — it produces a perfectly clean, correctly lit, completely
    # EMPTY frame with no error and exit code 0. Verified: `body in
    # scn.objects` was False, vertex groups matched bones 164/164, evaluated
    # vert count was correct, and the render was still black.
    # Link every appended object into the active scene collection.
    scene_coll = bpy.context.scene.collection
    linked = 0
    for o in added:
        try:
            scene_coll.objects.link(o)
            linked += 1
        except RuntimeError:
            pass  # already linked
    log("linked %d/%d appended objects into the scene" % (linked, len(added)))

    missing = [o.name for o in added
               if o.name not in {x.name for x in bpy.context.scene.objects}]
    if missing:
        log("UNLINKED after link pass: %s" % missing[:8])

    rig = find_rig()
    if rig is None:
        log("NO RIG after append")
        return None, []

    # Character meshes that must ride the rig.
    parts = []
    for name in ("EXPORT_Body", "EXPORT_Shirt", "EXPORT_Skirt", "EXPORT_Boots"):
        o = bpy.data.objects.get(name)
        if o is None:
            log("  part MISSING %s" % name)
            continue
        if o.parent is not rig:
            o.parent = rig
            o.matrix_parent_inverse = rig.matrix_world.inverted()
            log("  parented %s -> %s" % (name, rig.name))
        if not o.modifiers:
            log("  part %s has NO Armature modifier (add one)" % name)
        parts.append(o)

    # Rescale the character to the skiff scene.
    #
    # CRITICAL: scaling `rig.scale` does NOT scale the mesh. The Armature
    # modifier deforms vertices in the MESH's own local space, and the mesh
    # object sits at the world origin with an identity matrix_world — so the
    # rig's 0.01 scale never reaches the geometry. Verified: after setting
    # rig.scale=(0.01,)*3 the evaluated world extent was still
    # x -96..96, z -15..183, i.e. unscaled, next to a 3.7u hull.
    #
    # The only thing that works is scaling the vertex DATA itself
    # (mesh.transform(Matrix.Scale(...))), which the armature then deforms in
    # the already-correct space. Do this on every part.
    hull = None
    for o in bpy.data.objects:
        if o.type == "MESH" and "hull" in o.name.lower():
            hull = o
            break
    if hull is None:
        log("no hull found - cannot derive scene scale")
        return rig, parts

    bpy.context.view_layer.update()
    co = [hull.matrix_world @ v.co for v in hull.data.vertices]
    if not co:
        log("hull has no verts")
        return rig, parts
    hull_len = (max(co, key=lambda c: c.length) -
                min(co, key=lambda c: c.length)).length

    # Measure her from the evaluated (armature-deformed) mesh, since that is
    # the geometry the camera will actually see.
    dg = bpy.context.evaluated_depsgraph_get()
    pts = []
    for p in parts:
        ev = p.evaluated_get(dg)
        me = ev.to_mesh()
        mw = p.matrix_world
        pts.extend(mw @ v.co for v in me.vertices)
        ev.to_mesh_clear()
    if not pts:
        log("no character verts to measure")
        return rig, parts
    char_h = (max(p.z for p in pts) - min(p.z for p in pts)) or 1.0

    target = 1.7          # a seated figure reads correctly at ~1.7u
    scale = target / char_h
    log("scale: hull_len=%.3f char_h=%.3f -> MESH scale=%.6f"
        % (hull_len, char_h, scale))

    M = mathutils.Matrix.Scale(scale, 4)
    for p in parts:
        p.data.transform(M)
        p.data.update()
    # Keep the rig at whatever the source had; it now only drives deformation.
    bpy.context.view_layer.update()

    # Prove it against the evaluated mesh, not the bounding box.
    dg = bpy.context.evaluated_depsgraph_get()
    pts = []
    for p in parts:
        ev = p.evaluated_get(dg)
        me = ev.to_mesh()
        mw = p.matrix_world
        pts.extend(mw @ v.co for v in me.vertices)
        ev.to_mesh_clear()
    got = max(p.z for p in pts) - min(p.z for p in pts)
    log("post-scale EVALUATED height = %.3f (target %.2f)" % (got, target))

    # Seat her on the deck, in the boat's local frame, at a scale that now
    # actually applies. The hull deck sits around z=1.0 in world space.
    rig.location = (0.0, 0.0, 0.95)
    bpy.context.view_layer.update()
    pts = []
    for p in parts:
        ev = p.evaluated_get(dg)
        me = ev.to_mesh()
        mw = p.matrix_world
        pts.extend(mw @ v.co for v in me.vertices)
        ev.to_mesh_clear()
    log("seated: x %.2f..%.2f  y %.2f..%.2f  z %.2f..%.2f"
        % (min(p.x for p in pts), max(p.x for p in pts),
           min(p.y for p in pts), max(p.y for p in pts),
           min(p.z for p in pts), max(p.z for p in pts)))
    return rig, parts


def find_rig():
    for o in bpy.data.objects:
        if o.type == "ARMATURE" and ("Melusina" in o.name or "Rig" in o.name):
            return o
    arms = [o for o in bpy.data.objects if o.type == "ARMATURE"]
    return arms[0] if arms else None


def seat_character(rig, hull_obj):
    """Put the character at the proxy seat recorded in the v02 storyboard plan.

    The plan says boarding is a root glide, not a stand — the sit stays seated
    throughout, which reads correctly at storyboard distance and is honest
    about what the rig can actually do.
    """
    if rig is None:
        log("NO RIG — cannot pose")
        return
    log("rig=%s bones=%d" % (rig.name, len(rig.data.bones)))
    names = {b.name for b in rig.data.bones}
    for want in ("c_neck_x", "c_spine_03_x", "c_arm_fk_l", "c_thigh_fk"):
        log("  bone %-16s %s" % (want, "present" if want in names else "MISSING"))
    if hull_obj is not None:
        rig.location = (hull_obj.location.x, hull_obj.location.y,
                        hull_obj.location.z + 0.35)
        log("seated rig at %s" % (tuple(round(v, 3) for v in rig.location),))


def apply_pose(rig, pose):
    """Drive FK bones by euler. Bone-level only, never mixed with an object-level
    move on the same frame (a trap the v02 plan already recorded).

    Poses are ABSOLUTE, not cumulative: every panel starts from the rest pose,
    so panel 17 cannot inherit panel 12's arms. That inheritance is exactly
    what made 12 and 17 render identical the first time.
    """
    if rig is None:
        return
    if rig.animation_data and rig.animation_data.action:
        rig.animation_data.action = None
    for pb in rig.pose.bones:
        pb.rotation_mode = "XYZ"
        pb.rotation_euler = (0.0, 0.0, 0.0)
    for bone_name, euler in (pose or {}).items():
        if bone_name not in rig.pose.bones:
            log("  pose skip %s (no such bone)" % bone_name)
            continue
        pb = rig.pose.bones[bone_name]
        pb.rotation_euler = euler
        log("  pose %-16s euler=%s" % (bone_name, tuple(round(v, 3) for v in euler)))
    bpy.context.view_layer.update()


def apply_moves(rig, hull_z=None, glide_x=None):
    """Object-level moves. Kept separate from apply_pose on purpose — the v02
    plan records that mixing a bone-level pose and an object-level move on one
    frame is a staging bug, not a feature."""
    if rig is not None and glide_x is not None:
        rig.location.x += glide_x
        log("  glide rig.x -> %.3f" % rig.location.x)
    if glide_x is not None:
        # The boat travels WITH her — gliding only the rig would slide the
        # character off the deck and leave both wide shots framing the same
        # empty hull. hull_z and glide_x are mutually exclusive by design:
        # the v02 plan forbids a bone pose and an object move on one frame.
        moved = 0
        for o in bpy.data.objects:
            if o.type == "MESH" and ("hull" in o.name.lower()
                                     or "skiff" in o.name.lower()):
                o.location.x += glide_x
                moved += 1
        log("  glide hull/skiff x%+.2f on %d objects" % (glide_x, moved))
    if hull_z is not None:
        hits = 0
        for o in bpy.data.objects:
            if o.type == "MESH" and ("hull" in o.name.lower()
                                     or "skiff" in o.name.lower()):
                o.location.z += hull_z
                hits += 1
        log("  hull lift z%+.2f on %d objects" % (hull_z, hits))


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
    # Materials live on o.data.materials, which is a plain collection with no
    # .active in 5.2 — read slot 0 directly instead.
    for o in bpy.data.objects:
        if o.type != "MESH" or "water" not in o.name.lower():
            continue
        slots = getattr(o.data, "materials", None)
        if not slots or len(slots) == 0:
            continue
        m = slots[0]
        if not m or not m.use_nodes:
            continue
        for nd in m.node_tree.nodes:
            if nd.type == "EMISSION":
                nd.inputs["Strength"].default_value = water
                log("water emission %s -> %s" % (o.name, water))
                break
    log("light sun=%s water=%s lantern=%s" % (sun, water, lantern))


def aim_camera(cam, target, distance=None):
    """Point the camera at the character and frame her properly.

    History of this function, because both earlier versions were wrong:
      v1 kept the camera's original Z offset. After the character was scaled
         to 1.7u she sits far below a hull authored around 1.0u, so every shot
         framed her low and left, clipped by the bottom edge.
      v2 aimed at her centre but never checked the result. Measured coverage
         was 3-8% with every bounding box anchored to the lower-left.

    What actually works: place the camera at a fixed elevation above her
    mid-height, at `distance` on a horizontal bearing derived from the
    camera's ORIGINAL position (so each shot keeps its authored side), and
    aim at her chest. Then verify.
    """
    import mathutils
    if cam is None or target is None:
        return
    dist = distance if distance else 3.2
    # Bearing from the camera's authored position, so CAM_Intimate stays on
    # its side of the boat and CAM_SkiffClose keeps its low, close angle.
    cur = cam.matrix_world.translation.copy()
    bearing = mathutils.Vector((cur.x - target.x, cur.y - target.y, 0.0))
    if bearing.length < 1e-4:
        bearing = mathutils.Vector((0.0, -1.0, 0.0))
    bearing.normalize()

    # Elevation is a FRACTION OF HER HEIGHT, not an absolute offset. A seated
    # 1.7u figure read from slightly above the eyeline puts her head near the
    # upper third and her whole body inside the frame.
    elev = 0.22 * 1.7
    new_loc = mathutils.Vector((
        target.x + bearing.x * dist,
        target.y + bearing.y * dist,
        target.z + elev,
    ))
    cam.location = new_loc
    aim = mathutils.Vector((target.x, target.y, target.z + 0.10))
    d = (aim - new_loc).normalized()
    cam.rotation_euler = d.to_track_quat("-Z", "Y").to_euler()
    bpy.context.view_layer.update()
    log("  aim %s -> loc %s, chest %s, dist %.2f"
        % (cam.name, tuple(round(v, 2) for v in new_loc),
           tuple(round(v, 2) for v in aim), dist))


def character_centre(parts):
    """World-space centre of the character, for camera aiming."""
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
    return mathutils.Vector((
        sum(p.x for p in pts) / len(pts),
        sum(p.y for p in pts) / len(pts),
        (max(p.z for p in pts) + min(p.z for p in pts)) / 2.0,
    ))


def frustum_half_extent(cam, depth):
    """Actual half-width/half-height of the view frustum at `depth`.

    The earlier version hardcoded x<18 / y<10.125, which are the sensor
    half-dimensions at UNIT distance. At a 2-3 unit subject distance the real
    half-width is sensor/2 * depth / lens ~= 1.0u, so the old check passed a
    character who was almost entirely off the left edge of frame. That is why
    the gate went green while every panel came out empty.
    """
    sw = cam.data.sensor_width
    lens = cam.data.lens or 50.0
    half_w = (sw / 2.0) * depth / lens
    # sensor fit is AUTO by default -> the 36mm dimension maps to the larger
    # of resolution_x/resolution_y, which is width in a 1920x1080 frame.
    ar = 1080.0 / 1920.0
    return half_w, half_w * ar


def verify_framing(rig, cam):
    """Prove the character is inside the active camera frustum BEFORE rendering.

    A 100x scale error or a bad seat position produces a clean, well-lit,
    completely empty frame — indistinguishable from success by exit code. So
    project her bounding box into camera space and assert she is in front of
    the lens AND overlaps the sensor at her own depth.
    """
    if rig is None or cam is None:
        log("  FRAMING CHECK skipped (rig or cam missing)")
        return False
    bpy.context.view_layer.update()
    mw = cam.matrix_world.inverted()
    dg = bpy.context.evaluated_depsgraph_get()
    pts = []
    for o in bpy.data.objects:
        if o.type != "MESH":
            continue
        if not any(o.name.startswith(p) for p in
                   ("EXPORT_Body", "EXPORT_Shirt", "EXPORT_Skirt", "EXPORT_Boots")):
            continue
        # Evaluated verts, not bound_box: bound_box is cached on the object and
        # stays stale after a mesh-data transform, which is exactly the change
        # that moved her. Measuring the box would report the pre-move extent.
        ev = o.evaluated_get(dg)
        me = ev.to_mesh()
        pts.extend(mw @ (o.matrix_world @ v.co) for v in me.vertices)
        ev.to_mesh_clear()
    if not pts:
        log("  FRAMING CHECK no character verts found")
        return False
    zmin = min(p.z for p in pts)
    zmax = max(p.z for p in pts)
    xmin = min(p.x for p in pts); xmax = max(p.x for p in pts)
    ymin = min(p.y for p in pts); ymax = max(p.y for p in pts)
    # Blender camera looks down -Z; anything with z<0 is in front of the lens.
    in_front = zmax < 0
    depth = -sum(p.z for p in pts) / len(pts)
    half_w, half_h = frustum_half_extent(cam, depth)
    # Require real overlap, and a meaningful share of the frame, not a sliver.
    overlap_w = min(xmax, half_w) - max(xmin, -half_w)
    overlap_h = min(ymax, half_h) - max(ymin, -half_h)
    on_screen = overlap_w > 0 and overlap_h > 0
    fill = (100.0 * overlap_w * overlap_h) / (2 * half_w * 2 * half_h)
    log("  FRAMING cam z %.2f..%.2f x %.2f..%.2f y %.2f..%.2f | depth %.2f "
        "frustum %.2fx%.2f | overlap %.2fx%.2f = %.1f%% of frame | "
        "in_front=%s on_screen=%s"
        % (zmin, zmax, xmin, xmax, ymin, ymax, depth, half_w, half_h,
           overlap_w, overlap_h, fill, in_front, on_screen))
    if not in_front:
        log("  FRAMING FAIL character is BEHIND the camera")
        return False
    if not on_screen:
        log("  FRAMING FAIL character is entirely OFF-FRAME (x %.2f..%.2f vs "
            "+-%.2f, y %.2f..%.2f vs +-%.2f)"
            % (xmin, xmax, half_w, ymin, ymax, half_h))
        return False
    if fill < 2.0:
        log("  FRAMING FAIL character occupies only %.1f%% of frame - too small "
            "to read as a character" % fill)
        return False
    # Centering: a subject hugging an edge reads as an accident even when the
    # coverage number looks fine. Both earlier aim versions produced boxes
    # pinned to the lower-left corner. Require the centre of her extent to sit
    # near the middle of the frame.
    cx = (xmin + xmax) / 2.0
    cy = (ymin + ymax) / 2.0
    offx = abs(cx) / half_w
    offy = abs(cy) / half_h
    log("  FRAMING centre offset x=%.0f%% y=%.0f%% of half-frame" % (offx * 100, offy * 100))
    if offx > 0.85 or offy > 0.85:
        log("  FRAMING FAIL character is off-centre (%.0f%%, %.0f%%) - she "
            "reads as clipped by the frame edge" % (offx * 100, offy * 100))
        return False
    return True


def check_scene_linked(parts):
    """An object that exists in bpy.data but is not linked into the scene
    collection is invisible to the renderer while passing every geometry
    check. Assert linkage explicitly — this is the defect that made a whole
    character render as a clean empty frame with exit code 0."""
    in_scene = {o.name for o in bpy.context.scene.objects}
    bad = [p.name for p in parts if p.name not in in_scene]
    if bad:
        log("LINK FAIL not in scene.objects: %s" % bad)
        return False
    log("link check OK: %s" % [p.name for p in parts])
    return True


def set_camera(name):
    # The append creates CAM_Intimate.001 etc alongside the originals. A plain
    # bpy.data.objects.get() can land on either, and the .001 copy is the one
    # that was just imported — pick the ORIGINAL explicitly, lowest suffix.
    cands = [o for o in bpy.data.objects
             if o.type == "CAMERA" and o.name.split(".")[0] == name]
    if not cands:
        log("camera %s MISSING" % name)
        return None
    cands.sort(key=lambda o: o.name)
    cam = cands[0]
    bpy.context.scene.camera = cam
    log("camera -> %s (of %s)" % (cam.name, [c.name for c in cands]))
    return cam


def main():
    os.makedirs(OUT_PANELS, exist_ok=True)
    # panels_v4 is OUR render output, but it sits inside an LFS-tracked tree and
    # burn_cards.py's copy step re-applies git's read-only flag to everything it
    # touches. A read-only target makes bpy.ops.render.render() raise
    # "cannot save" AFTER the frame is computed, so the run dies on shot one
    # having logged a passing FRAMING line. Clear the flag up front and assert
    # it, rather than discovering it one wasted render at a time.
    for f in os.listdir(OUT_PANELS):
        fp = os.path.join(OUT_PANELS, f)
        try:
            os.chmod(fp, 0o666)
        except OSError as e:
            log("chmod failed %s: %s" % (fp, e))
    probe = os.path.join(OUT_PANELS, ".writable")
    try:
        with open(probe, "w") as fh:
            fh.write("ok")
        os.remove(probe)
        log("output dir writable: %s" % OUT_PANELS)
    except OSError as e:
        log("FATAL output dir NOT writable: %s" % e)
        raise SystemExit(1)

    bpy.ops.wm.open_mainfile(filepath=STAGE)
    scn = bpy.context.scene
    # 5.2 exposes the legacy EEVEE identifier; the *_NEXT enum arrived in 4.2
    # and was folded back. Probe rather than assume, or the run dies on line 1.
    engines = [i.identifier for i in
               type(scn.render).bl_rna.properties["engine"].enum_items]
    for want in ("BLENDER_EEVEE_NEXT", "BLENDER_EEVEE"):
        if want in engines:
            scn.render.engine = want
            break
    log("engine=%s" % scn.render.engine)
    scn.render.resolution_x = 1920
    scn.render.resolution_y = 1080
    scn.render.resolution_percentage = 100
    scn.render.image_settings.file_format = "PNG"
    scn.render.film_transparent = False

    rig, parts = append_character()
    if not check_scene_linked(parts):
        log("ABORT - character not linked into the scene")
        return
    seat_character(rig, None)

    for num, spec in sorted(REDO.items()):
        cam = set_camera(spec["cam"])
        apply_pose(rig, spec.get("pose"))
        apply_moves(rig, hull_z=spec.get("hull_z"), glide_x=spec.get("glide_x"))
        set_light(spec.get("sun", 6.0), spec.get("water", 4.0),
                  spec.get("lantern", 4.0))
        # Aim at the character AFTER posing/moving, so the aim uses her final
        # position. Re-aim per shot: shots 15/16 glide her across the frame.
        centre = character_centre(parts)
        aim_camera(cam, centre, distance=spec.get("cam_dist", 3.2))
        if not verify_framing(rig, cam):
            log("rendered %s SKIPPED - character not usably in frame" % num)
            continue
        out = os.path.join(OUT_PANELS, "panel_%s.png" % num)
        scn.render.filepath = out
        bpy.ops.render.render(write_still=True)
        exists = os.path.exists(out)
        log("rendered %s -> %s (%s)" % (num, out, "OK" if exists else "MISSING"))

    log("DONE")


main()
