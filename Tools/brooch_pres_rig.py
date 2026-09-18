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

    # ---------------- polish pass (2026-09-17, owner: "needs lighting polish + detailing") -----
    # Problems found in review: key/gem-point blowout on the right petals, muddy left/inner
    # shadows, uniform "plastic" metal reflections, flat matte pearls.
    # Lights: soften the key, tame the gem point, lift the shadow side with a broad front fill,
    # strengthen the rim for edge definition.
    ensure_light("PRES_Key_Soft", coll, 'AREA', 16.0, (-0.62, -0.62, 0.62), size=2.0)
    ensure_light("PRES_Gem_Point", coll, 'POINT', 5.0, (0.10, -0.38, 0.42), radius=0.02)
    ensure_light("PRES_Rim", coll, 'AREA', 16.0, (0.72, 0.35, 0.55), size=0.55,
                 color=(1.0, 0.96, 0.9))
    ensure_light("PRES_Fill_Soft", coll, 'AREA', 9.0, (-0.25, -0.95, 0.52), size=2.2,
                 color=(0.96, 0.97, 1.0))
    ensure_light("PRES_Kick_Low", coll, 'POINT', 1.8, (-0.20, -0.42, 0.12), radius=0.07)

    # Materials: micro-contrast on the metals (noise -> roughness + a faint bump), lustre on the
    # pearls (coat + sheen + a touch of subsurface). Render-side only -- the asset is untouched.
    def _set_inp(node, key, val):
        for k in (key,):
            try:
                node.inputs[k].default_value = val
                return True
            except Exception:
                continue
        return False

    _polished = []
    for m in bpy.data.materials:
        if not m.use_nodes or not m.node_tree:
            continue
        nm = m.name
        if not (nm.startswith("MID_") or nm.startswith("MEL_") or "Petal" in nm):
            continue
        nt = m.node_tree
        for n in nt.nodes:
            if n.type != 'BSDF_PRINCIPLED':
                continue
            if "Bead" in nm or "Pearl" in nm:
                _set_inp(n, "Coat Weight", 0.5)
                _set_inp(n, "Coat Roughness", 0.08)
                _set_inp(n, "Sheen Weight", 0.35)
                _set_inp(n, "Subsurface Weight", 0.12)
                _set_inp(n, "Roughness", 0.10)
                try:
                    n.inputs["Emission Color"].default_value = (0.9, 0.88, 0.86, 1.0)
                    n.inputs["Emission Strength"].default_value = 0.015
                except Exception:
                    pass
                try:
                    n.inputs["Subsurface Radius"].default_value = (0.004, 0.003, 0.003)
                except Exception:
                    pass
                _polished.append(nm + ":pearl")
            elif "Metal" in nm:
                try:
                    n.inputs["Roughness"].default_value = 0.26
                except Exception:
                    pass
                nz = nt.nodes.new('ShaderNodeTexNoise')
                nz.name = "POLISH noise"
                nz.inputs['Scale'].default_value = 55.0
                nz.inputs['Detail'].default_value = 3.0
                mr = nt.nodes.new('ShaderNodeMapRange')
                mr.name = "POLISH rough"
                mr.inputs['From Min'].default_value = 0.0
                mr.inputs['From Max'].default_value = 1.0
                mr.inputs['To Min'].default_value = 0.30
                mr.inputs['To Max'].default_value = 0.44
                nt.links.new(nz.outputs['Fac'], mr.inputs['Value'])
                try:
                    nt.links.new(mr.outputs['Result'], n.inputs['Roughness'])
                except Exception:
                    pass
                bp = nt.nodes.new('ShaderNodeBump')
                bp.name = "POLISH bump"
                bp.inputs['Strength'].default_value = 0.012
                bp.inputs['Distance'].default_value = 0.0004
                nt.links.new(nz.outputs['Fac'], bp.inputs['Height'])
                try:
                    nt.links.new(bp.outputs['Normal'], n.inputs['Normal'])
                except Exception:
                    pass
                _polished.append(nm + ":metal")
    print("polish: %d material(s) -> %s" % (len(_polished), ", ".join(sorted(set(_polished)))))

    # ---------------- magic pass + per-object materials (2026-09-17 late, owner asks) ---------
    # (a) materials are separated PER OBJECT by copying them per GN tree (each object owns its
    #     own tree, so retargeting the tree's Set Material nodes gives independent materials);
    # (b) the Melusina magic: gem fire, pearl iridescence (thin film), sparkle glow, faint
    #     metal warmth. All render-side; the saved asset keeps the authored materials.
    _magic = []
    _seen = set()
    for ob, suffix in ((bpy.data.objects.get("FlowerBrooch"), "_hero"),
                       (bpy.data.objects.get("FlowerBrooch_Dangles"), "_dang")):
        if ob is None:
            continue
        for mod in ob.modifiers:
            ng = getattr(mod, "node_group", None)
            if ng is None:
                continue
            for n in ng.nodes:
                if n.bl_idname != 'GeometryNodeSetMaterial':
                    continue
                src = n.inputs['Material'].default_value
                if src is None:
                    continue
                mc = bpy.data.materials.get(src.name + suffix)
                if mc is None:
                    mc = src.copy()
                    mc.name = src.name + suffix
                n.inputs['Material'].default_value = mc
                if mc.name in _seen:
                    continue
                _seen.add(mc.name)
                _magic.append(mc.name)
                for nn in mc.node_tree.nodes:
                    if nn.type != 'BSDF_PRINCIPLED':
                        continue
                    if mc.name.startswith("MID_Gem"):
                        _set_inp(nn, "Emission Strength", 0.8)
                        _set_inp(nn, "Coat Weight", 0.4)
                    elif "Sparkle" in mc.name:
                        _set_inp(nn, "Emission Strength", 6.0)
                    elif "Bead" in mc.name or "Pearl" in mc.name:
                        _set_inp(nn, "Thin Film Thickness", 420.0)
                        _set_inp(nn, "Thin Film IOR", 1.6)
                        _set_inp(nn, "Emission Strength", 0.03)
                    elif "Metal" in mc.name:
                        _set_inp(nn, "Emission Strength", 0.006)
    print("magic: %d per-object materials -> %s" % (len(_magic), ", ".join(sorted(_magic))))

    # view/render settings for the stills
    scn = bpy.context.scene
    scn.render.engine = 'BLENDER_EEVEE'
    try:
        scn.eevee.taa_render_samples = 96
        scn.eevee.use_raytracing = True
    except Exception:
        pass
    try:
        scn.view_settings.look = 'AgX - Base Contrast'
    except Exception:
        pass
    print("PRES_RIG ready: %d objects" % len(coll.objects))


main()
print("done pres rig")
