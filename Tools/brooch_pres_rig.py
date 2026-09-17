"""brooch_pres_rig.py — presentation rig for luxury stills (idempotent).

Builds/refreshes a PRES_RIG collection: dark-field backdrop, a soft key (metal gradients), a hard
gem point (fire), a rim, and two reflection cards (white window / black window -- the luxury tell).
Run inside the FlowerBrooch file (headless or GUI). Re-running refreshes values, never duplicates.

Usage:  blender -b FlowerBrooch.blend --python Tools/brooch_pres_rig.py
Then:   blender -b FlowerBrooch.blend --python Tools/brooch_pres_shot.py   (renders the set)
"""
import bpy
import math
from mathutils import Vector

COLL = "PRES_RIG"
TARGET = Vector((0.0, 0.0, 0.16))  # visual center of the hero, local units


def _arg(name, default=None):
    import sys
    a = sys.argv
    if name in a:
        i = a.index(name)
        if i + 1 < len(a):
            return a[i + 1]
    return default


SKY_VARIANT = _arg("--sky", "auto")  # "auto" = derive from the hero genome; "none" = flat world


def link_coll():
    c = bpy.data.collections.get(COLL)
    if c is None:
        c = bpy.data.collections.new(COLL)
        bpy.context.scene.collection.children.link(c)
        print("created collection", COLL)
    return c


def mat_simple(name, base, rough, spec=0.3, emit=None, emit_str=0.0):
    m = bpy.data.materials.get(name)
    if m is None:
        m = bpy.data.materials.new(name)
        print("created material", name)
    m.use_nodes = True
    bsdf = None
    for n in m.node_tree.nodes:
        if n.type == 'BSDF_PRINCIPLED':
            bsdf = n
            break
    if bsdf:
        try:
            bsdf.inputs["Base Color"].default_value = (*base, 1.0)
            bsdf.inputs["Roughness"].default_value = rough
            bsdf.inputs["Specular IOR Level"].default_value = spec
            if emit:
                bsdf.inputs["Emission Color"].default_value = (*emit, 1.0)
                bsdf.inputs["Emission Strength"].default_value = emit_str
        except Exception as exc:
            print("  mat warn", name, repr(exc)[:60])
    return m


def place_plane(name, coll, size, loc, rot_deg, mat):
    ob = bpy.data.objects.get(name)
    if ob is None:
        me = bpy.data.meshes.new(name)
        bm_verts = [(-1, -1, 0), (1, -1, 0), (1, 1, 0), (-1, 1, 0)]
        me.from_pydata(bm_verts, [], [(0, 1, 2, 3)])
        me.update()
        ob = bpy.data.objects.new(name, me)
        coll.objects.link(ob)
        print("created", name)
    ob.scale = (size[0], size[1], 1.0)
    ob.location = loc
    ob.rotation_euler = tuple(math.radians(a) for a in rot_deg)
    if ob.data.materials:
        ob.data.materials[0] = mat
    else:
        ob.data.materials.append(mat)
    return ob


def ensure_light(name, coll, ltype, energy, loc, aim_at=TARGET, size=None, radius=None, color=(1, 1, 1)):
    ld = bpy.data.lights.get(name)
    if ld is None:
        ld = bpy.data.lights.new(name, ltype)
        print("created light", name)
    ob = bpy.data.objects.get(name)
    if ob is None:
        ob = bpy.data.objects.new(name, ld)
        coll.objects.link(ob)
    ob.data = ld
    ld.type = ltype
    ld.energy = energy
    ld.color = color
    if size is not None and hasattr(ld, "size"):
        ld.size = size
    if size is not None and hasattr(ld, "shape"):
        try:
            ld.shape = 'RECTANGLE'
            ld.size_y = size * 0.6
        except Exception:
            pass
    if radius is not None and hasattr(ld, "shadow_soft_size"):
        ld.shadow_soft_size = radius
    ob.location = loc
    d = (Vector(aim_at) - Vector(loc)).normalized()
    ob.rotation_euler = d.to_track_quat('-Z', 'Y').to_euler()
    return ob


def main():
    coll = link_coll()

    # backdrop: dark field (back + floor, matte near-black)
    back_mat = mat_simple("PRES_Backdrop_Mat", (0.006, 0.008, 0.014), 0.72, spec=0.15)
    place_plane("PRES_Back", coll, (3.0, 3.0), (0.0, 0.85, 0.15), (90.0, 0.0, 0.0), back_mat)
    place_plane("PRES_Floor", coll, (3.0, 3.0), (0.0, 0.0, -0.55), (0.0, 0.0, 0.0), back_mat)

    # reflection cards (what the metal mirrors): white window lower-left, black window right
    card_w = mat_simple("PRES_Card_White", (0.9, 0.9, 0.9), 0.5, emit=(1.0, 1.0, 1.0), emit_str=1.0)
    card_b = mat_simple("PRES_Card_Black", (0.002, 0.002, 0.002), 0.92, spec=0.02)
    place_plane("PRES_Card_White_L", coll, (0.42, 0.9), (-0.55, -0.28, 0.18), (78.0, 0.0, 58.0), card_w)
    place_plane("PRES_Card_Black_R", coll, (0.5, 0.9), (0.62, -0.22, 0.16), (78.0, 0.0, -52.0), card_b)

    # lights: soft key (metal), hard gem point (fire), rim (edge separation)
    ensure_light("PRES_Key_Soft", coll, 'AREA', 26.0, (-0.62, -0.62, 0.62), size=1.1)
    ensure_light("PRES_Gem_Point", coll, 'POINT', 8.0, (0.10, -0.38, 0.42), radius=0.02)
    ensure_light("PRES_Rim", coll, 'AREA', 13.0, (0.72, 0.35, 0.55), size=0.5,
                 color=(1.0, 0.96, 0.9))
    ensure_light("PRES_Kick", coll, 'POINT', 2.5, (-0.25, -0.30, 0.02), radius=0.05)

    # Melusina Sky v3 (2026-09-17): the graded world + the PRES_Back card carry one stack.
    # Variant: `-- --sky <name>`; `--sky auto` (default) derives from the hero genome;
    # `--sky none` keeps the old flat world (A/B baseline).
    if SKY_VARIANT != "none":
        import os as _os
        import sys as _sys
        _sys.path.insert(0, _os.path.dirname(_os.path.abspath(__file__)))
        import brooch_sky
        _v = SKY_VARIANT
        if _v == "auto":
            _v, _gid = brooch_sky.sky_for_object(bpy.data.objects.get("FlowerBrooch"))
            print("sky auto -> %s (genome %s)" % (_v, _gid))
        _info = brooch_sky.apply_sky(bpy.context.scene, variant=_v, with_card=True)
        print("sky applied:", _info["variant"], "world nodes:", _info["nodes_world"])
    else:
        w = bpy.context.scene.world
        if w is None:
            w = bpy.data.worlds.new("World")
            bpy.context.scene.world = w
        w.use_nodes = True
        for n in w.node_tree.nodes:
            if n.type == 'BACKGROUND':
                try:
                    n.inputs["Color"].default_value = (0.004, 0.006, 0.012, 1.0)
                    n.inputs["Strength"].default_value = 1.0
                except Exception:
                    pass
        print("sky: disabled (--sky none)")

    # view/render settings for the stills
    scn = bpy.context.scene
    scn.render.engine = 'BLENDER_EEVEE'
    try:
        scn.eevee.taa_render_samples = 96
        scn.eevee.use_raytracing = True
    except Exception:
        pass
    try:
        scn.view_settings.look = 'AgX - Medium High Contrast'
    except Exception:
        pass
    print("PRES_RIG ready: %d objects" % len(coll.objects))


main()
print("done pres rig")
