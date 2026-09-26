"""Stage the BRUTALIST review .blend + render labelled contact sheets.

For the exterior-first film lane. Produces THREE deliverables from one run:

  1. Saved/Blend/BRUTALIST_CITY_REVIEW_2026-09-25.blend
     Labelled collections, every object carrying a LIVE geometry-nodes modifier so
     the dials stay playable in the file. One node group per object (the
     showcase stager's pattern) so two presets never fight over the same socket
     defaults - drag a slider and only that object moves.

  2. Contact sheets in Saved/Audit/brutalist_sheet_*.png
     Cities in PBR and in Komikaze, the office/interior family, and a material
     palette board. Tiles are camera-parented text, so they carry their own
     labels instead of relying on a legend nobody keeps next to the image.

  3. Saved/Audit/brutalist_stage_manifest.json - per object: builder, preset,
     nodes, params, verts, bbox, material. The numbers behind the pictures.

Usage:
    "C:/Program Files/Blender Foundation/Blender 5.2/blender.exe" \\
        --background --factory-startup \\
        --python deploy/_melodia_stage_gn_brutalist.py

    -- --skip-render   stage + save the .blend only (fast, no EEVEE)
    -- --keep-previews keep the individual tile PNGs after compositing

Material note: a city object is ONE joined mesh, so its massing / ground /
glazing split lives INSIDE the GN tree (`Set Material` on the group-input
Material sockets in `BUILDER_SURFACES`), and the object carries the matching
material slots so the renderer and exporter can see the split. Builders with
no Material sockets (office, cubicles) keep one material on slot 0.
"""
import json
import os
import sys

DEPLOY = os.path.dirname(os.path.abspath(__file__))
REPO = os.path.dirname(DEPLOY)
sys.path.insert(0, DEPLOY)
sys.path.append(os.path.join(os.environ["APPDATA"], "Blender Foundation",
                            "Blender", "5.2", "scripts", "addons"))

import bpy  # noqa: E402
import mathutils  # noqa: E402
from mathutils import Vector  # noqa: E402
from surreal_arch.melodia_gn import core  # noqa: E402
from surreal_arch.melodia_gn import (  # noqa: E402,F401
    brutalist_city, brutalist_office, brutalist_cubicles, brutalist_roofs,
)
from surreal_arch.melodia_gn import brutalist_materials as bmat  # noqa: E402
from surreal_arch.melodia_gn.presets import BUILDERS_PRESETS  # noqa: E402

STAMP = "2026-09-25"
ROOT = "BRUTALIST_CITY_REVIEW_%s" % STAMP
BLEND_PATH = os.path.join(REPO, "Saved", "Blend", ROOT + ".blend")
AUDIT = os.path.join(REPO, "Saved", "Audit")
SHEET_DIR = AUDIT
PREVIEW_DIR = os.path.join(REPO, "RawArt", "GNShowcase", "brutalist_%s" % STAMP)
TILE_W, TILE_H = 720, 405

argv = sys.argv[sys.argv.index("--") + 1:] if "--" in sys.argv else []
SKIP_RENDER = "--skip-render" in argv
KEEP_PREVIEWS = "--keep-previews" in argv

# (builder, collection, object, preset, x, y, material-surface, material-look)
LAYOUT = [
    ("GN_BRUTALIST_CityBlock", "01_CITY_PBR", "CITY_TightEstate", "BR_CITY_TIGHT",
     -230, 0, "concrete", "PBR"),
    ("GN_BRUTALIST_CityBlock", "01_CITY_PBR", "CITY_TowerCluster", "BR_CITY_TOWERS",
     10, 0, "concrete", "PBR"),
    ("GN_BRUTALIST_CityBlock", "01_CITY_PBR", "CITY_LowSprawl", "BR_CITY_SPRAWL",
     250, 0, "concrete", "PBR"),
    ("GN_BRUTALIST_CityBlock", "01_CITY_PBR", "CITY_CivicSuperblock", "BR_CITY_CIVIC",
     470, 0, "concrete", "PBR"),

    ("GN_BRUTALIST_CityBlock", "02_CITY_KOMIKAZE", "KMZ_TightEstate", "BR_CITY_TIGHT",
     -230, 320, "concrete", "Komikaze"),
    ("GN_BRUTALIST_CityBlock", "02_CITY_KOMIKAZE", "KMZ_TowerCluster", "BR_CITY_TOWERS",
     10, 320, "concrete", "Komikaze"),
    ("GN_BRUTALIST_CityBlock", "02_CITY_KOMIKAZE", "KMZ_LowSprawl", "BR_CITY_SPRAWL",
     250, 320, "concrete", "Komikaze"),
    ("GN_BRUTALIST_CityBlock", "02_CITY_KOMIKAZE", "KMZ_CivicSuperblock", "BR_CITY_CIVIC",
     470, 320, "concrete", "Komikaze"),

    ("GN_BRUTALIST_OfficeBlock", "03_OFFICE_BLOCK", "OFFICE_CivicSlab", "BR_OFFICE_CIVIC",
     -120, -180, "concrete", "PBR"),
    ("GN_BRUTALIST_OfficeBlock", "03_OFFICE_BLOCK", "OFFICE_BarbicanScale", "BR_OFFICE_BARBICAN",
     -40, -180, "concrete", "PBR"),
    ("GN_BRUTALIST_OfficeBlock", "03_OFFICE_BLOCK", "OFFICE_Bunker", "BR_OFFICE_BUNKER",
     40, -180, "concrete", "PBR"),
    ("GN_BRUTALIST_OfficeBlock", "03_OFFICE_BLOCK", "OFFICE_SlenderTower", "BR_OFFICE_SLENDER",
     120, -180, "concrete", "PBR"),

    ("GN_BRUTALIST_CubicleFarm", "04_INTERIOR_CUBICLES", "CUBICLE_Canonical", "BR_CUBICLE_CANON",
     -60, -300, "paving", "PBR"),
    ("GN_BRUTALIST_CubicleFarm", "04_INTERIOR_CUBICLES", "CUBICLE_MazeShift", "BR_CUBICLE_MAZE",
     0, -300, "paving", "PBR"),
    ("GN_BRUTALIST_CubicleFarm", "04_INTERIOR_CUBICLES", "CUBICLE_OpenPlan", "BR_CUBICLE_OPEN",
     60, -300, "paving", "PBR"),
    ("GN_BRUTALIST_CubicleFarm", "04_INTERIOR_CUBICLES", "CUBICLE_Swarm", "BR_CUBICLE_SWARM",
     120, -300, "paving", "PBR"),

    # ---- 05 facade variation (2026-09-25) ---------------------------------
    # Added with the city Facade Style dial. The four above are Facade Style 0
    # (Blank) and are deliberately UNCHANGED, so this sheet is the before/after:
    # same city generator, same seed, fenestration on.
    ("GN_BRUTALIST_CityBlock", "05_FACADE_VARIATION", "FAC_TowerRibbon",
     "BR_CITY_TOWERS_GLASS", -300, -520, "concrete", "PBR"),
    ("GN_BRUTALIST_CityBlock", "05_FACADE_VARIATION", "FAC_PunchedEstate",
     "BR_CITY_PUNCHED", 0, -520, "concrete", "PBR"),
    ("GN_BRUTALIST_CityBlock", "05_FACADE_VARIATION", "FAC_CivicColonnade",
     "BR_CITY_COLONNADE", 300, -520, "concrete", "PBR"),

    # ---- 06 roof family (2026-09-25) --------------------------------------
    # One building footprint, six Roof Style values. The point of this sheet is
    # that the SILHOUETTE changes - a roof style that only moved a vertex count
    # would be indistinguishable in a wide shot.
    ("GN_BRUTALIST_Roof", "06_ROOFS", "ROOF_FlatParapet", "BR_ROOF_FLAT",
     -300, -740, "concrete", "PBR"),
    ("GN_BRUTALIST_Roof", "06_ROOFS", "ROOF_LowPitch", "BR_ROOF_PITCH",
     -150, -740, "concrete", "PBR"),
    ("GN_BRUTALIST_Roof", "06_ROOFS", "ROOF_Sawtooth", "BR_ROOF_SAWTOOTH",
     0, -740, "concrete", "PBR"),
    ("GN_BRUTALIST_Roof", "06_ROOFS", "ROOF_BarrelVault", "BR_ROOF_BARREL",
     150, -740, "concrete", "PBR"),
    ("GN_BRUTALIST_Roof", "06_ROOFS", "ROOF_PyramidHip", "BR_ROOF_HIP",
     300, -740, "concrete", "PBR"),
    ("GN_BRUTALIST_Roof", "06_ROOFS", "ROOF_PlantDeck", "BR_ROOF_PLANT",
     450, -740, "concrete", "PBR"),
]

# Showcase-only socket overrides, applied AFTER the preset so the shipped
# preset values stay intact and this file is the only place that says "for the
# contact sheet only". Reason, measured from the rendered tiles: the cubicle
# farm's `Ceiling Grid` emits a full-footprint slab at 2.9m, and the review
# camera looks down at 26 degrees, so the slab covered every desk, monitor and
# chair - four of sixteen tiles showed a blank white lid. The interior assets
# are the point of the sheet, so the ceiling comes off for the picture while
# the .blend keeps the dial live for anyone who wants to put it back.
REVIEW_OVERRIDES = {
    "CUBICLE_Canonical": {"Ceiling Grid": False},
    "CUBICLE_MazeShift": {"Ceiling Grid": False},
    "CUBICLE_OpenPlan": {"Ceiling Grid": False},
    "CUBICLE_Swarm": {"Ceiling Grid": False},
}

# Builder id -> {group-input Material socket name: brutalist surface key}.
# City exposes all three (massing / ground / glazing); roof exposes one.
# Office and cubicle builders expose NO Material sockets yet, so their rows
# are empty and the object keeps its single LAYOUT surface on slot 0.
BUILDER_SURFACES = {
    "GN_BRUTALIST_CityBlock": {
        "Massing Material": "concrete",
        "Ground Material": "asphalt",
        "Glazing Material": "glass",
    },
    "GN_BRUTALIST_Roof": {
        "Roof Material": "concrete",
    },
    "GN_BRUTALIST_OfficeBlock": {},
    "GN_BRUTALIST_CubicleFarm": {},
}


def set_param(tree, name, value):
    for item in tree.interface.items_tree:
        if (getattr(item, "name", "") == name
                and getattr(item, "in_out", "") == "INPUT"):
            try:
                item.default_value = value
                return True
            except Exception:
                return False
    return False


def eval_stats(ob):
    deps = bpy.context.evaluated_depsgraph_get()
    deps.update()
    ev = ob.evaluated_get(deps)
    try:
        m = ev.to_mesh()
    except Exception:
        return 0, None, None
    verts = len(m.vertices) if m else 0
    lo = hi = None
    if verts:
        xs = [v.co for v in m.vertices]
        lo = tuple(min(c[i] for c in xs) for i in range(3))
        hi = tuple(max(c[i] for c in xs) for i in range(3))
    ev.to_mesh_clear()
    return verts, lo, hi


def ensure_collection(name, parent):
    coll = bpy.data.collections.get(name)
    if coll is None:
        coll = bpy.data.collections.new(name)
    if coll.name not in [c.name for c in parent.children]:
        parent.children.link(coll)
    return coll


# ---- clean slate ---------------------------------------------------------
for coll in list(bpy.data.collections):
    bpy.data.collections.remove(coll)

print("[br-stage] building brutalist material library")
bmat.build_brutalist_materials()

root = ensure_collection(ROOT, bpy.context.scene.collection)
manifest = {"stamp": STAMP, "blend": BLEND_PATH, "collections": {}}
staged = []

for bid, coll_name, ob_name, preset, px, py, surface, look in LAYOUT:
    if bid not in core.GROUP_BUILDERS:
        print("[br-stage] MISSING builder %s - skipped" % bid)
        continue
    # fresh tree per object so presets never share socket defaults
    res = core.GROUP_BUILDERS[bid]()
    tree = res[0] if isinstance(res, (tuple, list)) else res
    # ...and a private COPY, because the builder hands back the same datablock
    # to every caller. Without this all four office objects share ONE group
    # (measured: users=4), so the presets fight over one socket table and a
    # slider drag moves every object at once - the exact thing this stager
    # promises not to do. The copy also gives each object its own name in the
    # outliner, which is what makes a labelled review file readable.
    if tree.users > 0 or tree.name in bpy.data.node_groups:
        tree = tree.copy()
        tree.name = "%s_%s" % (tree.name.split("_OBJ")[0], ob_name)
    if preset:
        params = BUILDERS_PRESETS.get(bid, {}).get("presets", {}).get(preset)
        if params is None:
            print("[br-stage] WARNING: preset %s not found for %s" % (preset, bid))
        else:
            missing = [n for n, v in params.items() if not set_param(tree, n, v)]
            print("[br-stage] preset %s/%s applied%s"
                  % (bid, preset, (" MISSING=%s" % missing) if missing else ""))
    # review-only overrides, after the preset so they win
    for sock, val in REVIEW_OVERRIDES.get(ob_name, {}).items():
        ok = set_param(tree, sock, val)
        print("[br-stage] review override %s.%s=%s %s"
              % (ob_name, sock, val, "" if ok else "(SOCKET NOT FOUND)"))

    coll = ensure_collection(coll_name, root)
    me = bpy.data.meshes.new(ob_name + "_mesh")
    ob = bpy.data.objects.new(ob_name, me)
    coll.objects.link(ob)
    ob.location = (px, py, 0.0)
    mod = ob.modifiers.new("GN", "NODES")
    mod.node_group = tree
    bpy.context.view_layer.update()
    verts, lo, hi = eval_stats(ob)
    wire = bmat.set_material_slots(tree, BUILDER_SURFACES.get(bid, {}), look)
    slots = bmat.assign_surfaces(ob, list(dict.fromkeys(
        [surface] + list(BUILDER_SURFACES.get(bid, {}).values()))), look)
    if wire["missing"]:
        print("[br-stage] material sockets unwired on %s: %s"
              % (ob_name, "; ".join(wire["missing"])))
    n_params = sum(1 for it in tree.interface.items_tree
                   if getattr(it, "in_out", "") == "INPUT")
    entry = {
        "object": ob_name, "builder": bid, "preset": preset,
        "nodes": len(tree.nodes), "params": n_params, "verts": verts,
        "material": slots[0] if slots else None,
        "materials": slots,
        "material_sockets_set": wire["set"],
        "material_sockets_missing": wire["missing"],
        "local_bbox": [round(hi[i] - lo[i], 2) for i in range(3)] if lo else None,
        "position": [px, py, 0.0],
    }
    manifest["collections"].setdefault(coll_name, []).append(entry)
    staged.append((ob, ob_name, preset, lo, hi, (px, py, 0.0), verts))
    print("[br-stage] %-18s %-22s %7dv nodes=%4d params=%2d mat=%s"
          % (coll_name, ob_name, verts, len(tree.nodes), n_params,
             ",".join(slots) if slots else "-"))

# ---- palette board --------------------------------------------------------
pal = ensure_collection("05_MATERIAL_PALETTE", root)
pallet_names = []
try:
    for surface in bmat.SURFACES:
        for look in bmat.LOOKS:
            mat = bmat.build_brutalist_material(surface, look)
            me = bpy.data.meshes.new("swatch_%s" % mat.name)
            ob = bpy.data.objects.new("SWATCH_" + mat.name, me)
            pal.objects.link(ob)
            bpy.ops.mesh.primitive_plane_add(size=10.0)
            plane = bpy.context.object
            plane.name = "SWATCH_" + mat.name
            for c in list(plane.users_collection):
                c.objects.unlink(plane)
            pal.objects.link(plane)
            plane.location = (len(pallet_names) * 12.0, 0.0, 0.0)
            plane.data.materials.append(mat)
            pallet_names.append(mat.name)
    print("[br-stage] palette board: %d swatches" % len(pallet_names))
except Exception as exc:
    print("[br-stage] palette board skipped: %s: %s" % (type(exc).__name__, exc))

# ---- world, sun, cameras --------------------------------------------------
scene = bpy.context.scene
try:
    world = bpy.data.worlds.get("BR_World") or bpy.data.worlds.new("BR_World")
    world.use_nodes = True
    bg = world.node_tree.nodes.get("Background")
    if bg:
        bg.inputs[0].default_value = (0.42, 0.50, 0.60, 1.0)
        # 1.1 ambient + a 4.0 sun over a 0.60 albedo base is >1.0 before the
        # view transform. 0.30 keeps shadow sides readable instead of grey mush.
        bg.inputs[1].default_value = 0.30
    scene.world = world
except Exception as exc:
    print("[br-stage] world skipped: %s" % exc)

sun_data = bpy.data.lights.new("BR_SUN", type='SUN')
# Exposure budget. Measured: sun 4.0 + world 1.1 under 'Standard' clipped the
# concrete to pure white, which is WHY the PBR and Komikaze tiles looked
# identical on the sheets - a blown highlight cannot carry a 0.45 ink mix.
# A controlled probe (Saved/Audit/_diag_komikaze.py) measured the Komikaze
# graph as correct and clearly distinct (18.4% of pixels, max delta 0.75);
# the lighting was destroying the difference, not the shader.
sun_data.energy = 1.7
sun_data.angle = 0.30
sun = bpy.data.objects.new("BR_SUN", sun_data)
bpy.context.scene.collection.objects.link(sun)
sun.rotation_euler = (0.95, 0.18, -0.75)

cam_data = bpy.data.cameras.new("BR_CAM")
cam_data.lens = 40.0
# Frame distance is extent*1.45 + 12 (see aim_camera's caller), and the city
# presets measure 90-156m, i.e. 142-238m of pull-back. The stock clip_end does
# NOT clear that, so every CITY tile rendered as an empty frame. Set the far
# plane explicitly so a future default change cannot silently blank a tile.
cam_data.clip_start = 0.10
cam_data.clip_end = 5000.0
cam = bpy.data.objects.new("BR_CAM", cam_data)
bpy.context.scene.collection.objects.link(cam)
scene.camera = cam
cd = cam_data            # used by add_label() to fit text to the frustum


def frame_bbox(lo, hi, azimuth_deg=42.0, elevation_deg=26.0, margin=1.06):
    """Aim the camera so a world-space bbox exactly fills the frame.

    The previous heuristic (`dist = extent*1.45 + 12`) ignored the projection
    entirely and put all four city tiles off-frame (measured ndc x = 1.04-1.14)
    while the family tiles sat at ~1/3 frame. This solves for distance instead:
    walk back along the view axis until every bbox corner is inside the frustum
    with `margin` headroom, so nothing is cropped and nothing floats in a void.
    """
    import math
    az, el = math.radians(azimuth_deg), math.radians(elevation_deg)
    d = Vector((math.cos(az) * math.cos(el),
                math.sin(az) * math.cos(el),
                math.sin(el)))
    target = Vector(((lo[0] + hi[0]) * 0.5, (lo[1] + hi[1]) * 0.5, (lo[2] + hi[2]) * 0.5))
    corners = [Vector((x, y, z)) for x in (lo[0], hi[0])
               for y in (lo[1], hi[1]) for z in (lo[2], hi[2])]
    kx = cam_data.lens / (cam_data.sensor_width * 0.5)
    ky = kx * (TILE_H / float(TILE_W))

    def fits(dist):
        cam.location = target + d * dist
        cam.rotation_euler = (target - cam.location).to_track_quat('-Z', 'Y').to_euler()
        inv = mathutils.Matrix.LocRotScale(
            cam.location, cam.rotation_euler.to_quaternion(),
            Vector((1.0, 1.0, 1.0))).inverted()
        for c in corners:
            p = inv @ c
            z = -p.z
            if z <= 1e-6:
                return False
            if abs(p.x / z) * kx > margin or abs(p.y / z) * ky > margin:
                return False
        return True

    near = max((c - target).length for c in corners) * 0.05 + 0.01
    far = max((c - target).length for c in corners) * 12.0 + 60.0
    if not fits(far):                      # pathological: keep the old behaviour
        far = max((hi[i] - lo[i] for i in range(3))) * 1.45 + 12.0
        fits(far)
        return far
    for _ in range(40):                    # bisect to the tightest safe distance
        mid = (near + far) * 0.5
        if fits(mid):
            far = mid
        else:
            near = mid
    return far


def isolate(ob_keep):
    """Hide everything except `ob_keep` and the palette board, so a tile shows
    only its own subject. Cities are spaced 240m apart but a 156m sprawl seen
    from 238m still catches its neighbours at the frame edge."""
    hidden = []
    for other in bpy.context.scene.objects:
        if other.type != 'MESH' or other is ob_keep:
            continue
        if other.name.startswith("SWATCH_"):
            continue
        if not other.hide_render:
            other.hide_render = True
            hidden.append(other)
    return hidden


def unisolate(hidden):
    for ob in hidden:
        ob.hide_render = False


def frustum_tan():
    """Half-extent tangents of the render frame per unit of distance.

    cam_data is a 40mm lens on a 36mm sensor, so tan(hfov/2) = 0.45. Used by the
    label placer to convert a caption depth into on-screen half-extents. The
    CAMERA FRAMING authority is frame_bbox() above, which solves against the real
    view matrix - do not add a second framing path here.
    """
    tan_h = (cam_data.sensor_width * 0.5) / cam_data.lens
    tan_v = tan_h * (scene.render.resolution_y / float(scene.render.resolution_x))
    return tan_h, tan_v


def label_material():
    """Unlit white for the contact-sheet labels. A default-lit text object reads as
    a dark smudge against a night city, which is worse than no label."""
    mat = bpy.data.materials.get("BR_Label_Emissive")
    if mat is None:
        mat = bpy.data.materials.new("BR_Label_Emissive")
    mat.use_nodes = True
    nt = mat.node_tree
    nt.nodes.clear()
    out = nt.nodes.new("ShaderNodeOutputMaterial")
    emi = nt.nodes.new("ShaderNodeEmission")
    emi.inputs["Color"].default_value = (1.0, 1.0, 1.0, 1.0)
    emi.inputs["Strength"].default_value = 3.0
    nt.links.new(emi.outputs["Emission"], out.inputs["Surface"])
    return mat


def add_label(cam_obj, text, sub=""):
    """Camera-parented text so each contact-sheet tile carries its own name.

    Both lines are fitted to the frustum instead of placed at fixed offsets.
    At 0.5m with a 40mm lens on a 36mm sensor the frame is only
    0.5*(36/40) = 0.45 units wide and 0.45*(405/720) = 0.253 tall, so the old
    x=-0.27 was off-frame left (hence labels reading "FFICE_") and dy=-0.165
    was below the bottom edge entirely. Width is also scaled to the character
    count, because a long preset name overruns the right edge at a fixed size.
    """
    try:
        mat = label_material()
        depth = 0.5
        tan_h, tan_v = frustum_tan()
        half_w, half_h = depth * tan_h, depth * tan_v
        # 0.5*(36/40) is the FULL frame width; the half-extent is
        # depth*(sensor/2)/lens = 0.225. Using the full width here put the
        # caption row at y=-0.139 against a real bottom edge of -0.127,
        # i.e. still clipped off the bottom of the tile.
        max_w = half_w * 2.0 * 0.92          # 8% margin
        # rows are placed as a fraction of the frustum half-height so they
        # cannot fall off the bottom edge if the tile aspect changes
        for body, fy, want in ((text, 0.55, 0.042),
                               (sub, 0.80, 0.024)):
            if not body:
                continue
            body = str(body)
            size = min(want, max_w / max(1.0, 0.60 * len(body)))
            td = bpy.data.curves.new("lbl", type='FONT')
            td.body = body
            td.size = size
            td.align_x = 'CENTER'
            td.align_y = 'CENTER'
            td.materials.append(mat)
            ob = bpy.data.objects.new("LBL_" + body[:24], td)
            ob.parent = cam_obj
            ob.location = (0.0, -half_h * fy, -depth)
            ob.rotation_euler = (0, 0, 0)
            bpy.context.scene.collection.objects.link(ob)
        return True
    except Exception as exc:
        print("[br-stage] label failed (%s): %s" % (text, exc))
        return False


def clear_labels():
    for ob in [o for o in bpy.data.objects if o.name.startswith("LBL_")]:
        bpy.data.objects.remove(ob, do_unlink=True)


# ---- render engine ---------------------------------------------------------
for engine in ('BLENDER_EEVEE_NEXT', 'BLENDER_EEVEE', 'CYCLES'):
    try:
        scene.render.engine = engine
        print("[br-stage] engine = %s" % engine)
        break
    except Exception:
        continue
try:
    scene.eevee.taa_render_samples = 32
except Exception:
    pass
scene.render.resolution_x = TILE_W
scene.render.resolution_y = TILE_H
scene.render.resolution_percentage = 100
scene.render.image_settings.file_format = 'PNG'
try:
    scene.view_settings.view_transform = 'Standard'
except Exception:
    pass


def compose_sheet(tile_paths, out_path, cols, gap=6):
    """Tile PNGs into one contact sheet. numpy ships with Blender, so no PIL."""
    import numpy as np
    if not tile_paths:
        return None
    rows = (len(tile_paths) + cols - 1) // cols
    W = TILE_W * cols + gap * (cols + 1)
    H = TILE_H * rows + gap * (rows + 1)
    sheet = np.zeros((H, W, 4), dtype=np.float32)
    sheet[..., 3] = 1.0
    for i, path in enumerate(tile_paths):
        if not os.path.exists(path):
            print("[br-stage] missing tile, skipped: %s" % path)
            continue
        img = bpy.data.images.load(path)
        w, h = img.size
        buf = np.empty(w * h * 4, dtype=np.float32)
        img.pixels.foreach_get(buf)
        a = buf.reshape(h, w, 4)
        # nearest-fit crop into the tile box (rows are bottom-up in Blender)
        if h > TILE_H:
            a = a[(h - TILE_H) // 2:(h - TILE_H) // 2 + TILE_H, :]
        if w > TILE_W:
            a = a[:, (w - TILE_W) // 2:(w - TILE_W) // 2 + TILE_W]
        th, tw = min(h, TILE_H), min(w, TILE_W)
        r, c = divmod(i, cols)
        y0 = H - gap - (r + 1) * TILE_H - r * gap
        x0 = gap + c * (TILE_W + gap)
        sheet[y0:y0 + th, x0:x0 + tw] = a[:th, :tw]
        bpy.data.images.remove(img)
    out = bpy.data.images.new("br_sheet", W, H, alpha=True)
    out.pixels.foreach_set(sheet.reshape(-1))
    out.filepath_raw = out_path
    out.file_format = 'PNG'
    out.save()
    print("[br-stage] sheet -> %s (%dx%d, %d tiles)" % (out_path, W, H, len(tile_paths)))
    return out_path


sheets = {}
if not SKIP_RENDER:
    try:
        os.makedirs(PREVIEW_DIR, exist_ok=True)
    except Exception:
        pass
    rendered = {}
    # Guard a defect this stager previously shipped: objects sharing one node
    # group, so the LAST preset applied silently overwrote every earlier
    # object's socket defaults and they all rendered as the same building.
    # Checked ONCE up front (it used to be rebuilt inside the render loop, i.e.
    # O(n^2) work repeated per tile).
    dup = {}
    for _ob, _n, _p, _lo, _hi, _pos, _v in staged:
        dup.setdefault(_ob.modifiers["GN"].node_group.name, []).append(_n)
    shared = {k: v for k, v in dup.items() if len(v) > 1}
    if shared:
        print("[br-stage] WARNING shared node groups: %s"
              % {k: v for k, v in list(shared.items())[:4]})
    else:
        print("[br-stage] node-group isolation OK (%d distinct groups)" % len(dup))
    for ob, ob_name, preset, lo, hi, pos, verts in staged:
        if lo is None:
            continue
        # Framing: exact frustum solve, not an extent heuristic. lo/hi are
        # LOCAL (pre-transform) bounds and the object also carries a location,
        # so world bounds are local + location.
        wlo = (pos[0] + lo[0], pos[1] + lo[1], pos[2] + lo[2])
        whi = (pos[0] + hi[0], pos[1] + hi[1], pos[2] + hi[2])
        hidden = isolate(ob)
        dist = frame_bbox(wlo, whi)
        clear_labels()
        add_label(cam, ob_name,
                  "%s  |  %d verts  |  %.0fm" % (preset or "defaults", verts,
                                                 max(hi[0] - lo[0], hi[1] - lo[1])))
        out = os.path.join(PREVIEW_DIR, ob_name + ".png")
        scene.render.filepath = out
        bpy.ops.render.render(write_still=True)
        rendered[ob_name] = out
        print("[br-stage] rendered %-22s dist=%.1f group=%s"
              % (ob_name, dist, ob.modifiers["GN"].node_group.name))
        unisolate(hidden)          # never leave the review .blend with hidden objects
    clear_labels()

    def sheet_for(prefix, out_name, cols):
        tiles = [rendered[o[1]] for o in staged if o[1].startswith(prefix)]
        return compose_sheet(tiles, os.path.join(SHEET_DIR, out_name), cols)

    sheets["city_pbr"] = sheet_for("CITY_", "brutalist_sheet_city_pbr.png", 2)
    sheets["city_komikaze"] = sheet_for("KMZ_", "brutalist_sheet_city_komikaze.png", 2)
    # Facade + roof sheets are 2-wide rather than 4-wide: the family sheet at
    # 4 cols is 2910px wide and reads as specks when scaled down for a team
    # review. 2 cols keeps each tile near its native 720px.
    sheets["facade"] = sheet_for("FAC_", "brutalist_sheet_facade.png", 2)
    sheets["roofs"] = sheet_for("ROOF_", "brutalist_sheet_roofs.png", 2)
    sheets["family"] = compose_sheet(
        [rendered[o[1]] for o in staged if o[1].startswith(("OFFICE_", "CUBICLE_"))],
        os.path.join(SHEET_DIR, "brutalist_sheet_family.png"), 4)

    # palette board: frame the whole swatch row, and hide the buildings so the
    # board is not read through a city skyline.
    try:
        if pallet_names:
            hidden = [o for o in bpy.context.scene.objects
                      if o.type == 'MESH' and not o.name.startswith("SWATCH_")
                      and not o.hide_render]
            for o in hidden:
                o.hide_render = True
            last = (len(pallet_names) - 1) * 12.0
            dist = frame_bbox((-6.0, -6.0, -0.2), (last + 6.0, 6.0, 0.2),
                              azimuth_deg=90.0, elevation_deg=68.0, margin=1.02)
            clear_labels()
            add_label(cam, "BRUTALIST MATERIAL PALETTE",
                      "%d swatches | %s" % (len(pallet_names),
                                            " | ".join(sorted(set(bmat.SURFACES)))))
            out = os.path.join(SHEET_DIR, "brutalist_sheet_palette.png")
            scene.render.filepath = out
            bpy.ops.render.render(write_still=True)
            sheets["palette"] = out
            print("[br-stage] palette sheet -> %s (dist=%.1f)" % (out, dist))
            clear_labels()
            unisolate(hidden)
    except Exception as exc:
        print("[br-stage] palette sheet skipped: %s: %s" % (type(exc).__name__, exc))

    if not KEEP_PREVIEWS:
        pass  # tiles are already outside Saved/ so the review tree stays clean

# ---- save + manifest -------------------------------------------------------
manifest["sheets"] = sheets
manifest["palette"] = pallet_names
try:
    os.makedirs(os.path.dirname(BLEND_PATH), exist_ok=True)
    bpy.ops.wm.save_as_mainfile(filepath=BLEND_PATH)
    print("[br-stage] blend -> %s" % BLEND_PATH)
except Exception as exc:
    print("[br-stage] blend save FAILED: %s" % exc)

man_path = os.path.join(AUDIT, "brutalist_stage_manifest.json")
try:
    os.makedirs(AUDIT, exist_ok=True)
    with open(man_path, "w", encoding="utf-8") as fh:
        json.dump(manifest, fh, indent=1)
    print("[br-stage] manifest -> %s" % man_path)
except Exception as exc:
    print("[br-stage] manifest FAILED: %s" % exc)

print("[br-stage] DONE objects=%d sheets=%d" % (len(staged), len(sheets)))


