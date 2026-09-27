"""Render the Baroque circlet + tiara against the measured head contract.

Uses the house stone material (Aquamarine Dream / Void Orchid) so the proof shows
what a person sees, not a wireframe. View transform is Standard -- AgX desaturates
the surreal palette, which cost an earlier round of gem re-authoring.
"""

import bpy
import os
import sys
import math
import json

HERE = r"C:\EnvironmentPortfolio\BS_GodFile\Saved\Audit\regalia"
sys.path.insert(0, HERE)

import regalia_baroque_build as RB  # noqa: E402

RB._import_house()

OUT = os.path.join(HERE, "baroque")
os.makedirs(OUT, exist_ok=True)


def clear():
    for o in list(bpy.data.objects):
        bpy.data.objects.remove(o, do_unlink=True)


def head_proxy(name, hw, hd, cz, cx, cy):
    """A measured egg, so the render shows the real fit rather than a sphere."""
    bpy.ops.mesh.primitive_uv_sphere_add(segments=64, ring_count=32,
                                         radius=1.0,
                                         location=(cx, cy, cz))
    ob = bpy.context.active_object
    ob.name = name
    # A head is ~1.2x taller than it is wide and sits ABOVE the band, not
    # centred on it. Centring the egg on the band made a tall frame show an
    # empty dome; offset it so the crown reads against a skull.
    # The proxy is the HEAD, and the band sits at her BROW, not her equator.
    # Centring a full egg on the band put the entire 45 mm crest inside the
    # dome: measured present (192-vert shell, 97 mm rise) yet invisible in every
    # render. Shrink it to a shallow cranial cap that stops just under the band
    # top, so the crown is silhouetted against air.
    for v in ob.data.vertices:
        v.co.x *= hw
        v.co.y *= hd
        v.co.z *= hw * 0.42
    for v in ob.data.vertices:
        if v.co.z > 0:
            v.co.z -= hw * 0.30 * 0.42
    ob.data.materials.clear()
    m = bpy.data.materials.get("HEAD_SKIN") or bpy.data.materials.new("HEAD_SKIN")
    m.use_nodes = True
    b = m.node_tree.nodes.get("Principled BSDF")
    if b:
        b.inputs["Base Color"].default_value = (0.14, 0.13, 0.17, 1.0)
        b.inputs["Roughness"].default_value = 0.62
    ob.data.materials.append(m)
    return ob


def gold(name):
    m = bpy.data.materials.get(name) or bpy.data.materials.new(name)
    m.use_nodes = True
    b = m.node_tree.nodes.get("Principled BSDF")
    if b:
        # A pure metal's colour IS its reflection tint, so a bright base colour
        # plus a hot key just reads white. Real 24k gold sits near (1.0, 0.78, 0.34)
        # but needs roughness high enough to break the specular into a gradient.
        b.inputs["Base Color"].default_value = (0.96, 0.74, 0.30, 1.0)
        b.inputs["Metallic"].default_value = 1.0
        b.inputs["Roughness"].default_value = 0.34
    return m


def setup_scene(cz, cx=0.0, cy=0.0):
    scn = bpy.context.scene
    # 5.2's enum is ('BLENDER_EEVEE', 'BLENDER_WORKBENCH', 'CYCLES') -- there is
    # no BLENDER_EEVEE_NEXT any more, and CYCLES is far too slow for a proof loop.
    scn.render.engine = "BLENDER_EEVEE"
    scn.view_settings.view_transform = "Standard"
    scn.view_settings.look = "None"
    scn.render.film_transparent = False
    w = scn.world
    w.use_nodes = True
    bg = w.node_tree.nodes.get("Background")
    if bg:
        # A metal with nothing to reflect renders BLACK. The first tiara proof was
        # warm gold on the lit side and near-black on the other, which read as a
        # material fault rather than a lighting one. Lift the world to a dim
        # plum-grey so the gold has a floor value, and keep the surreal gem
        # ceiling in mind: the stones are calibrated to peak <=0.85.
        bg.inputs[0].default_value = (0.085, 0.075, 0.115, 1.0)
        bg.inputs[1].default_value = 1.0

    def lamp(name, loc, energy, size, col=(1, 1, 1)):
        d = bpy.data.lights.new(name, "AREA")
        d.energy = energy
        d.size = size
        d.color = col
        o = bpy.data.objects.new(name, d)
        scn.collection.objects.link(o)
        o.location = loc
        fz = (cz - o.location.z)
        fl = math.hypot(fz, 0.35)
        o.rotation_euler = (math.atan2(fz, fl), 0, 0)
        return o

    # Energy matters: a 48 W key 0.45 m from a 1.0-metallic gold with roughness
    # 0.28 clips every channel and the gold renders WHITE, which is what the first
    # proof showed. The surreal gem palette is calibrated to peak <=0.85, so the
    # lights have to stay under that ceiling or the stones go white too.
    lamp("KEY", (0.42, -0.55, cz + 0.42), 14, 0.45)
    lamp("FILL", (-0.55, -0.34, cz + 0.12), 5, 0.7, (0.72, 0.80, 1.0))
    lamp("RIM", (0.10, 0.62, cz + 0.34), 11, 0.3, (0.86, 0.72, 1.0))
    # a broad softbox directly above: the band's top surface needs a wide, even
    # source or a thin metal ring just alternates light/dark along its length.
    lamp("TOP", (cx, cy, cz + 0.55), 9, 0.9, (1.0, 0.97, 0.92))
    return scn


def shoot(tag, ob, cz, cx, cy, dist, azim, elev, ortho):
    scn = bpy.context.scene
    cam_d = bpy.data.cameras.new("C")
    cam_d.lens = 85
    cam = bpy.data.objects.new("C", cam_d)
    scn.collection.objects.link(cam)
    a, e = math.radians(azim), math.radians(elev)
    cam.location = (cx + math.sin(a) * dist,
                    cy - math.cos(a) * dist,
                    cz + math.sin(e) * dist)
    tgt = bpy.data.objects.new("T", bpy.data.cameras.new("T"))
    scn.collection.objects.link(tgt)
    tgt.location = (cx, cy, cz)
    from mathutils import Vector
    d = tgt.location - cam.location
    cam.rotation_euler = d.to_track_quat("-Z", "Y").to_euler()
    cam_d.type = "ORTHO"
    cam_d.ortho_scale = ortho
    scn.camera = cam
    scn.render.resolution_x = 900
    scn.render.resolution_y = 900
    scn.render.image_settings.file_format = "PNG"
    path = os.path.join(OUT, "%s.png" % tag)
    scn.render.filepath = path
    bpy.ops.render.render(write_still=True)
    bpy.data.objects.remove(cam, do_unlink=True)
    bpy.data.objects.remove(tgt, do_unlink=True)
    bpy.data.cameras.remove(cam_d)
    print("RENDERED %s -> %s" % (tag, path))
    return path


def build(piece, crown):
    name = "MEL_regalia_tiara" if crown else "MEL_regalia_circlet"
    tree = RB.build_piece(name)
    ob = bpy.data.objects.new(name, bpy.data.meshes.new(name))
    bpy.context.scene.collection.objects.link(ob)
    m = ob.modifiers.new("regalia", "NODES")
    m.node_group = tree
    return ob, tree


def main():
    clear()
    L = json.load(open(os.path.join(HERE, "regalia_landmarks.json"),
                       encoding="utf-8"))
    h = L.get("head", L)   # the landmark file stores brow/crown at top level
    for piece, crown, key in (("circlet", False, "brow"),
                             ("tiara", True, "crown")):
        if key not in h:
            continue
        # landmarks store FULL width/depth plus an explicit centre; the builders
        # take HALF widths, and the crown section reuses the brow centre X/Y.
        c = h[key].get("centre", [-0.0044, -0.1335])
        hw = h[key]["width"] * 0.5
        hd = (h[key].get("depth", h[key]["width"] * 1.125)) * 0.5
        cz = h[key]["z"]
        cx, cy = c[0], c[1]
        print("%s: half %.4f x %.4f at z %.3f centre (%.4f, %.4f)" % (
            piece, hw, hd, cz, cx, cy))
        clear()
        head_proxy("HEAD", hw, hd, cz, cx, cy)
        ob, tree = build(piece, crown)
        # The GN tree emits TWO material slots: index 0 (the stone, set inside the
        # nested MEL_nikki_crystal) and index 1 (SurrealArch_Gold, set by the
        # piece's own Set Material). Blender does NOT create object slots for
        # geometry-node materials on its own -- measured, the evaluated mesh had
        # materials [None, 'SurrealArch_Gold'] and ALL 6176 faces pointed at
        # index 1, so the gem rendered as bare gold. The object must therefore
        # carry BOTH, in the same order the tree emits them.
        bpy.context.view_layer.update()
        dg0 = bpy.context.evaluated_depsgraph_get()
        dg0.update()
        oe0 = ob.evaluated_get(dg0)
        probe = oe0.to_mesh()
        emitted = [m.name if m else None for m in (probe.materials or [])]
        oe0.to_mesh_clear()
        print("%s tree emits material slots: %s" % (piece, emitted))
        # Blender does not create OBJECT slots for geometry-node materials, and
        # the tree's own Set Material left the gem's slot as None (measured
        # materials [None, 'SurrealArch_Gold'] with all 6176 faces on index 1).
        # So: give the object both materials, then assign per-face by GEOMETRY
        # -- the gem is the material that sits proud of the band above z_top and
        # within 30 mm of the front axis. That is deterministic and does not
        # depend on the tree's slot bookkeeping at all.
        ob.data.materials.clear()
        ob.data.materials.append(bpy.data.materials["REGALIA_STONE"])   # index 0
        ob.data.materials.append(bpy.data.materials["SurrealArch_Gold"])  # index 1
        # Realize the modifier into the object's OWN mesh so the per-face
        # assignment persists into the render.
        #
        # The tree CANNOT deliver the stone material itself: its Set Material
        # emits the slot order on the evaluated mesh, the OBJECT gets no slots,
        # and measured materials came back [None, 'SurrealArch_Gold'] with all
        # 6176 faces on index 1. So the stone is identified GEOMETRICALLY here.
        #
        # The first geometric test ("proud of the band and within 32 mm of the
        # front axis") also caught the CREST once it existed -- 101 stone faces
        # on the tiara against 13 on the flat circlet -- and painted the gold
        # crest icy blue. Narrow it to the stone's own signature: a bicone of
        # the measured height whose centre sits at the band top, offset outward
        # along the band's front normal, NOT displaced in Y like the crest is.
        # Identify the stone by CONNECTED COMPONENT, not by a hand-tuned window.
        # Three geometric windows were tried and each was wrong in a different
        # direction (286 faces = the whole front filigree; 101 = the crest;
        # 2/10 = almost nothing). The stone is the only separate shell in the
        # piece: the band, scrolls, volutes, beads and crest all touch, because
        # Merge by Distance welds them into one body. A flood fill over shared
        # vertices finds it exactly, with no thresholds to get wrong.
        gem_w = 0.024 * (0.5546 if crown else 1.0)

        bpy.context.view_layer.update()
        dg1 = bpy.context.evaluated_depsgraph_get()
        dg1.update()
        oe1 = ob.evaluated_get(dg1)
        new_mesh = bpy.data.meshes.new_from_object(oe1)
        new_mesh.materials.clear()
        new_mesh.materials.append(bpy.data.materials["REGALIA_STONE"])
        new_mesh.materials.append(bpy.data.materials["SurrealArch_Gold"])

        # union-find over vertices sharing an edge, seeded from the vertex nearest
        # the stone's expected position (band front, band top + one stone height)
        seed_x, seed_y = cx, cy - hd - gem_w * 1.1
        seed_z = cz + 0.011 + 0.0045 + gem_w * 1.2
        verts = new_mesh.vertices
        best = min(range(len(verts)),
                   key=lambda i: ((verts[i].co.x - seed_x) ** 2
                                  + (verts[i].co.y - seed_y) ** 2
                                  + (verts[i].co.z - seed_z) ** 2))
        parent = list(range(len(verts)))

        def find(a):
            while parent[a] != a:
                parent[a] = parent[parent[a]]
                a = parent[a]
            return a

        def union(a, b):
            ra, rb = find(a), find(b)
            if ra != rb:
                parent[rb] = ra

        for e in new_mesh.edges:
            union(e.vertices[0], e.vertices[1])
        target = find(best)
        n_gem = 0
        for p_ in new_mesh.polygons:
            if find(p_.vertices[0]) == target:
                p_.material_index = 0
                n_gem += 1
            else:
                p_.material_index = 1

        old_mesh = ob.data
        ob.data = new_mesh
        ob.modifiers.remove(ob.modifiers[0])
        if old_mesh.users == 0:
            bpy.data.meshes.remove(old_mesh)
        print("%s: %d stone faces in a realized %d-face mesh" % (
            piece, n_gem, len(new_mesh.polygons)))

        # give the stone real colour on the gem branch
        setup_scene(cz, cx, cy)
        bpy.context.view_layer.update()
        dg = bpy.context.evaluated_depsgraph_get()
        dg.update()
        oe = ob.evaluated_get(dg)
        me = oe.to_mesh()
        if me and len(me.vertices):
            xs = [v.co.x for v in me.vertices]
            ys = [v.co.y for v in me.vertices]
            print("%s evaluated v=%d width=%.4f depth=%.4f" % (
                piece, len(me.vertices), max(xs) - min(xs), max(ys) - min(ys)))
        else:
            print("%s evaluated EMPTY" % piece)
        oe.to_mesh_clear()
        # Frame on the evaluated extent, not a fixed multiple of the band half
        # width. The first tiara shot was framed at hw*2.7 = 0.31 m, which CROPPED
        # the 45 mm crest -- and vision correctly reported "no vertical rise" for a
        # piece that had 66.7 mm of it. A framing fault read as a design fault.
        bpy.context.view_layer.update()
        dgf = bpy.context.evaluated_depsgraph_get()
        dgf.update()
        oef = ob.evaluated_get(dgf)
        mef = oef.to_mesh()
        if mef and len(mef.vertices):
            ztop = max(v.co.z for v in mef.vertices)
            zbot = min(v.co.z for v in mef.vertices)
            zmid = (ztop + zbot) * 0.5
            rise = max(0.0, ztop - cz)
            print("%s framing: z %.4f..%.4f  rise above band %.4f m" % (
                piece, zbot, ztop, rise))
        else:
            zmid = cz
            rise = 0.0
        oef.to_mesh_clear()
        frame = max(hw * 2.7, (ztop - zbot) * 1.25, rise * 2.2)
        for tag, az, el, sc in (("front", 0, 0, frame),
                                ("threequarter", 34, 14, frame * 1.06),
                                ("side", 90, 4, frame * 1.04),
                                ("top", 0, 74, frame * 1.06)):
            shoot("%s_%s" % (piece, tag), ob, zmid, cx, cy,
                  hw * 5.0, az, el, sc)
        # a MACRO on the centre stone. At 5% of frame width the gem cannot be
        # judged in a full-piece shot, and a "no gem visible" reading from one
        # wide render is not evidence the stone is missing or the wrong colour.
        macro = os.path.join(OUT, "%s_gem_macro.png" % piece)
        mm = bpy.data.materials.get("REGALIA_STONE")
        scn = bpy.context.scene
        cam_d = bpy.data.cameras.new("M")
        cam = bpy.data.objects.new("M", cam_d)
        scn.collection.objects.link(cam)
        cam_d.type = "ORTHO"
        gem_w = 0.024 * (0.5546 if crown else 1.0)
        # The first macro put the camera INSIDE the gem: measured gem half-height
        # is ~0.034 m (a bicone is 2.8x its nominal radius) and the camera sat
        # gem_w*0.7 = 0.019 m above the band, so the frame was filled by dark
        # interior faces. Stand well off and look slightly DOWN at the stone.
        cam_d.ortho_scale = gem_w * 7.0
        cam.location = (cx + gem_w * 0.5, cy - hw - gem_w * 5.0,
                        cz + gem_w * 4.0)
        tgt = bpy.data.objects.new("MT", bpy.data.cameras.new("MT"))
        scn.collection.objects.link(tgt)
        tgt.location = (cx, cy - hw, cz + gem_w * 0.9)
        from mathutils import Vector
        d2 = tgt.location - cam.location
        cam.rotation_euler = d2.to_track_quat("-Z", "Y").to_euler()
        scn.camera = cam
        scn.render.resolution_x = 900
        scn.render.resolution_y = 900
        scn.render.filepath = macro
        bpy.ops.render.render(write_still=True)
        bpy.data.objects.remove(cam, do_unlink=True)
        bpy.data.objects.remove(tgt, do_unlink=True)
        print("RENDERED %s_gem_macro" % piece)
    print("BAROQUE-RENDER-COMPLETE")


main()
