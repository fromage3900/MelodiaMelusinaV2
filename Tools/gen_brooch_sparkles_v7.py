"""gen_brooch_sparkles_v7.py -- v7 companion: GN_Brooch_Sparkles_v7.

A togglable sparkle field that rides the finished brooch (the genome's cosmic_influence
register, made literal): 4-point star instances distributed around the bloom with per-point
random size/rotation and a scene-time twinkle. Built as a SECOND modifier so the main
generator stays clean and the stars never enter the bevel/outline passes.

Tree interface:
    Geometry (passthrough) | Sparkle Count | Sparkle Radius | Sparkle Height
    Sparkle Size (mm) | Twinkle Speed | Seed
Output: joined [input geometry + realized star instances], MID_Bead material.

Run (live session):  bridge --file Tools/gen_brooch_sparkles_v7.py
The script builds the tree, attaches/reuses the "GN_Sparkles" modifier at the END of the
stack, sizes the field from the object's current evaluated dimensions, and does NOT save.
"""
import math
import time
import traceback

import bpy

TREE = "GN_Brooch_Sparkles_v7"
OBJ_NAME = "FlowerBrooch"
MOD = "GN_Sparkles"
TAU = 6.283185307179586


def mk(tree, bl_id, name, loc):
    n = tree.nodes.new(bl_id)
    n.name = name
    n.location = loc
    return n


def d0(node, idx, value):
    try:
        node.inputs[idx].default_value = value
    except Exception as exc:
        print("  warn: set %s[%d] (%r)" % (node.name, idx, exc))
    return node


def dn(node, name, value):
    try:
        node.inputs[name].default_value = value
    except Exception as exc:
        print("  warn: set %s['%s'] (%r)" % (node.name, name, exc))
    return node


def L(tree, src, src_sock, dst, dst_sock):
    return tree.links.new(src.outputs[src_sock], dst.inputs[dst_sock])


def mathx(tree, name, op, loc, a=None, b=None):
    n = mk(tree, 'ShaderNodeMath', name, loc)
    n.operation = op
    if a is not None:
        d0(n, 0, a)
    if b is not None:
        d0(n, 1, b)
    return n


def combine(tree, name, loc):
    return mk(tree, 'ShaderNodeCombineXYZ', name, loc)


def rv(tree, name, loc, seed):
    n = None
    for bl in ('FunctionNodeRandomValue', 'GeometryNodeRandomValue'):
        try:
            n = mk(tree, bl, name, loc)
            break
        except Exception:
            n = None
    if n is None:
        raise RuntimeError("no Random Value node class")
    try:
        n.data_type = 'FLOAT'
    except Exception:
        pass
    for s in n.inputs:
        if s.name.lower() == 'seed' or s.identifier.lower().endswith('seed'):
            d0(n, list(n.inputs).index(s), int(seed))
    return n


print("=== gen_brooch_sparkles_v7 ===")
ob = bpy.data.objects.get(OBJ_NAME)
if ob is None:
    print("ERROR: object %r not found" % OBJ_NAME)
else:
    old = bpy.data.node_groups.get(TREE)
    if old is not None:
        try:
            bpy.data.node_groups.remove(old)
            print("removed previous", TREE)
        except Exception as exc:
            print("warn: could not remove old tree (%r)" % (exc,))

    tree = bpy.data.node_groups.new(TREE, 'GeometryNodeTree')

    def iface(name, stype, default, mn=None, mx=None):
        s = tree.interface.new_socket(name=name, in_out='INPUT', socket_type=stype)
        try:
            s.default_value = default
        except Exception:
            pass
        if mn is not None:
            try:
                s.min_value = mn
            except Exception:
                pass
        if mx is not None:
            try:
                s.max_value = mx
            except Exception:
                pass
        return s

    iface("Geometry", 'NodeSocketGeometry', None)
    iface("Sparkle Count", 'NodeSocketInt', 26, 0, 400)
    iface("Sparkle Radius", 'NodeSocketFloat', 0.30, 0.001, 50.0)
    iface("Sparkle Height", 'NodeSocketFloat', 0.22, 0.0, 50.0)
    iface("Sparkle Size (mm)", 'NodeSocketFloat', 1.1, 0.05, 20.0)
    iface("Twinkle Speed", 'NodeSocketFloat', 0.35, 0.0, 5.0)
    iface("Seed", 'NodeSocketInt', 7)
    tree.interface.new_socket(name="Geometry", in_out='OUTPUT', socket_type='NodeSocketGeometry')

    gin = mk(tree, 'NodeGroupInput', "Group Input", (-2200, 0))
    gout = mk(tree, 'NodeGroupOutput', "Group Output", (1200, 0))

    # ---- star proto: 8-vert circle, odd verts pulled inward (4-point sparkle) ----
    star = mk(tree, 'GeometryNodeMeshCircle', "star circle", (-2000, -450))
    try:
        star.vertices = 8
    except Exception:
        d0(star, 0, 8)
    try:
        star.fill_type = 'NGON'
    except Exception as exc:
        print("  warn: circle fill (%r)" % (exc,))
    try:
        star.radius = 1.0
    except Exception:
        dn(star, "Radius", 1.0)
    ix = mk(tree, 'GeometryNodeInputIndex', "index i", (-2200, -650))
    odd = mathx(tree, "i mod 2", 'MODULO', (-2000, -650), b=2.0)
    L(tree, ix, "Index", odd, 0)
    cmp = mk(tree, 'FunctionNodeCompare', "is odd", (-1850, -650))
    try:
        cmp.data_type = 'FLOAT'
        cmp.operation = 'EQUAL'
    except Exception as exc:
        print("  warn: compare setup (%r)" % (exc,))
    L(tree, odd, "Value", cmp, "A")
    dn(cmp, "B", 1.0)
    m1 = mathx(tree, "odd * -0.72", 'MULTIPLY', (-1700, -700), b=-0.72)
    L(tree, cmp, "Result", m1, 0)
    f1 = mathx(tree, "factor", 'ADD', (-1550, -700), b=1.0)
    L(tree, m1, "Value", f1, 0)
    posf = mk(tree, 'GeometryNodeInputPosition', "circle position", (-2000, -850))
    vs = mk(tree, 'ShaderNodeVectorMath', "star pos scale", (-1400, -800))
    vs.operation = 'SCALE'
    L(tree, posf, "Position", vs, "Vector")
    L(tree, f1, "Value", vs, "Scale")
    setp = mk(tree, 'GeometryNodeSetPosition', "star points", (-1200, -700))
    L(tree, star, "Mesh", setp, "Geometry")
    L(tree, cmp, "Result", setp, "Selection")
    L(tree, vs, "Vector", setp, "Position")

    # ---- instance field: random polar positions + per-point size/rot/twinkle ----
    pts = mk(tree, 'GeometryNodePoints', "sparkle points", (-1200, -300))
    L(tree, gin, "Sparkle Count", pts, "Count")
    r1 = rv(tree, "rand r", (-2000, -100), 11)
    a1 = rv(tree, "rand angle", (-2000, 100), 23)
    z1 = rv(tree, "rand z", (-2000, 300), 37)
    s1 = rv(tree, "rand size", (-2000, 500), 51)
    q1 = rv(tree, "rand rot", (-2000, 700), 67)
    p1 = rv(tree, "rand phase", (-2000, 900), 83)

    rr = mathx(tree, "r = R*(0.35+0.85r)", 'MULTIPLY', (-1800, -100), b=0.85)
    L(tree, r1, "Value", rr, 0)
    rr2 = mathx(tree, "  +0.35", 'ADD', (-1650, -100), b=0.35)
    L(tree, rr, "Value", rr2, 0)
    rr3 = mathx(tree, "* Sparkle Radius", 'MULTIPLY', (-1500, -100))
    L(tree, rr2, "Value", rr3, 0)
    L(tree, gin, "Sparkle Radius", rr3, 1)

    th = mathx(tree, "angle", 'MULTIPLY', (-1800, 100), b=TAU)
    L(tree, a1, "Value", th, 0)
    cosv = mathx(tree, "cos", 'COSINE', (-1650, 40))
    L(tree, th, "Value", cosv, 0)
    sinv = mathx(tree, "sin", 'SINE', (-1650, 160))
    L(tree, th, "Value", sinv, 0)
    px = mathx(tree, "x", 'MULTIPLY', (-1500, 40))
    L(tree, rr3, "Value", px, 0)
    L(tree, cosv, "Value", px, 1)
    py = mathx(tree, "y", 'MULTIPLY', (-1500, 160))
    L(tree, rr3, "Value", py, 0)
    L(tree, sinv, "Value", py, 1)
    zz = mathx(tree, "z = H*(0.05+0.95r)", 'MULTIPLY', (-1800, 300), b=0.95)
    L(tree, z1, "Value", zz, 0)
    zz2 = mathx(tree, "  +0.05", 'ADD', (-1650, 300), b=0.05)
    L(tree, zz, "Value", zz2, 0)
    zz3 = mathx(tree, "* Sparkle Height", 'MULTIPLY', (-1500, 300))
    L(tree, zz2, "Value", zz3, 0)
    L(tree, gin, "Sparkle Height", zz3, 1)
    pos = combine(tree, "sparkle position", (-1330, 200))
    L(tree, px, "Value", pos, "X")
    L(tree, py, "Value", pos, "Y")
    L(tree, zz3, "Value", pos, "Z")
    L(tree, pos, "Vector", pts, "Position")

    rot = combine(tree, "sparkle rotation", (-1330, 420))
    d0(rot, 0, 0.0)
    d0(rot, 1, 0.0)
    rotz = mathx(tree, "rot z", 'MULTIPLY', (-1500, 620), b=TAU)
    L(tree, q1, "Value", rotz, 0)
    L(tree, rotz, "Value", rot, "Z")

    # twinkle: size = mm/100 * (0.6+0.8 r) * (0.75 + 0.25 sin(2pi*(frame*speed)/60 + phase))
    sz1 = mathx(tree, "0.6+0.8r", 'MULTIPLY', (-1800, 520), b=0.8)
    L(tree, s1, "Value", sz1, 0)
    sz2 = mathx(tree, "  +0.6", 'ADD', (-1650, 520), b=0.6)
    L(tree, sz1, "Value", sz2, 0)
    sz3 = mathx(tree, "* Sparkle Size", 'MULTIPLY', (-1500, 520))
    L(tree, sz2, "Value", sz3, 0)
    L(tree, gin, "Sparkle Size (mm)", sz3, 1)
    sz4 = mathx(tree, "-> units (/100)", 'MULTIPLY', (-1350, 520), b=0.01)
    L(tree, sz3, "Value", sz4, 0)
    st = mk(tree, 'GeometryNodeInputSceneTime', "sparkle time", (-2000, 1100))
    t1 = mathx(tree, "frame * speed", 'MULTIPLY', (-1800, 1100))
    L(tree, st, "Frame", t1, 0)
    L(tree, gin, "Twinkle Speed", t1, 1)
    t2 = mathx(tree, "phase t", 'MULTIPLY', (-1650, 1100), b=TAU / 60.0)
    L(tree, t1, "Value", t2, 0)
    ph = mathx(tree, "rand phase * TAU", 'MULTIPLY', (-1800, 900), b=TAU)
    L(tree, p1, "Value", ph, 0)
    t3 = mathx(tree, "+ phase", 'ADD', (-1500, 1050))
    L(tree, t2, "Value", t3, 0)
    L(tree, ph, "Value", t3, 1)
    tw1 = mathx(tree, "sin(..)", 'SINE', (-1350, 1050))
    L(tree, t3, "Value", tw1, 0)
    tw2 = mathx(tree, "0.75+0.25", 'MULTIPLY', (-1200, 1050), b=0.25)
    L(tree, tw1, "Value", tw2, 0)
    tw3 = mathx(tree, "  +0.75", 'ADD', (-1050, 1050), b=0.75)
    L(tree, tw2, "Value", tw3, 0)
    sc = mathx(tree, "size * twinkle", 'MULTIPLY', (-900, 700))
    L(tree, sz4, "Value", sc, 0)
    L(tree, tw3, "Value", sc, 1)
    sv = combine(tree, "sparkle scale", (-750, 640))
    L(tree, sc, "Value", sv, "X")
    L(tree, sc, "Value", sv, "Y")
    L(tree, sc, "Value", sv, "Z")

    iop = mk(tree, 'GeometryNodeInstanceOnPoints', "instance stars", (-550, -300))
    L(tree, pts, "Geometry", iop, "Points")
    L(tree, setp, "Geometry", iop, "Instance")
    L(tree, rot, "Vector", iop, "Rotation")
    L(tree, sv, "Vector", iop, "Scale")
    real = mk(tree, 'GeometryNodeRealizeInstances', "realize stars", (-350, -300))
    L(tree, iop, "Instances", real, "Geometry")
    mat = bpy.data.materials.get("MID_Sparkle")
    if mat is None:
        mat = bpy.data.materials.new("MID_Sparkle")
        mat.use_nodes = True
        nt = mat.node_tree
        for n in list(nt.nodes):
            nt.nodes.remove(n)
        mout = nt.nodes.new('ShaderNodeOutputMaterial')
        pb = nt.nodes.new('ShaderNodeBsdfPrincipled')
        try:
            pb.inputs["Base Color"].default_value = (0.95, 0.55, 0.72, 1.0)
        except Exception:
            pass
        try:
            pb.inputs["Emission Color"].default_value = (1.0, 0.62, 0.78, 1.0)
        except Exception:
            pass
        try:
            pb.inputs["Emission Strength"].default_value = 4.0
        except Exception:
            pass
        nt.links.new(pb.outputs["BSDF"], mout.inputs["Surface"])
        print("created MID_Sparkle (emissive)")
    star_out, star_sock = real, "Geometry"
    if mat is not None:
        try:
            sm = mk(tree, 'GeometryNodeSetMaterial', "star material", (-200, -300))
            L(tree, real, "Geometry", sm, "Geometry")
            dn(sm, "Material", mat)
            star_out, star_sock = sm, "Geometry"
        except Exception as exc:
            print("  warn: star material (%r)" % (exc,))
    # ---- standalone output: stars only (no passthrough geometry — lives on own object) ----
    L(tree, star_out, star_sock, gout, "Geometry")

    tree.use_fake_user = True
    print("built %s: %d nodes, %d links" % (TREE, len(tree.nodes), len(tree.links)))

    # ---- attach as the LAST modifier + size the field from the current piece ----
    ob = bpy.data.objects.get(OBJ_NAME)
    if ob is not None:
        sparkle_ob_name = "FlowerBrooch_Sparkles"
        sparkle_ob = bpy.data.objects.get(sparkle_ob_name)
        if sparkle_ob is None:
            from mathutils import Matrix
            me = bpy.data.meshes.new(sparkle_ob_name)
            sparkle_ob = bpy.data.objects.new(sparkle_ob_name, me)
            bpy.context.scene.collection.objects.link(sparkle_ob)
            sparkle_ob.parent = ob
            sparkle_ob.matrix_parent_inverse = Matrix.Identity(4)
            sparkle_ob.location = (0.0, 0.0, 0.0)
            print("created sparkle object:", sparkle_ob_name)
        # remove old modifier from hero if present
        old_hero_mod = ob.modifiers.get(MOD)
        if old_hero_mod is not None:
            ob.modifiers.remove(old_hero_mod)
            print("removed old GN_Sparkles from hero")
        mod = sparkle_ob.modifiers.get(MOD)
        if mod is None:
            mod = sparkle_ob.modifiers.new(MOD, 'NODES')
            print("created modifier", MOD, "on", sparkle_ob_name)
        mod.node_group = tree
        try:
            have = list(sparkle_ob.modifiers).index(mod)
            want = len(sparkle_ob.modifiers) - 1
            if have != want:
                sparkle_ob.modifiers.move(have, want)
                print("GN_Sparkles moved to end of sparkle object stack")
        except Exception as exc:
            print("warn: reorder (%r)" % (exc,))
        mod.show_viewport = True
        mod.show_render = True

    bpy.context.view_layer.update()
    dg = bpy.context.evaluated_depsgraph_get()
    me = ob.evaluated_get(dg).data
    dims = [0.0, 0.0, 0.0]
    if len(me.vertices):
        for i, ax in enumerate("xyz"):
            vals = [getattr(v.co, ax) for v in me.vertices]
            dims[i] = max(vals) - min(vals)
    half_w = max(dims[0], dims[1]) * 0.5 if any(dims) else 0.30
    print("object eval dims (units):", [round(d, 4) for d in dims])

    values = {
        "Sparkle Count": 26,
        "Sparkle Radius": round(half_w * 0.95, 4),
        "Sparkle Height": round(max(dims[2], 0.1) * 0.9, 4),
        "Sparkle Size (mm)": 1.1,
        "Twinkle Speed": 0.35,
        "Seed": 7,
    }
    synced = 0
    for item in tree.interface.items_tree:
        if getattr(item, "in_out", "") != "INPUT":
            continue
        if item.name not in values:
            continue
        val = values[item.name]
        done = False
        try:
            mod.properties.inputs[item.identifier]["value"] = val
            done = True
        except Exception:
            try:
                mod[item.identifier] = val
                done = True
            except Exception:
                try:
                    mod[item.name] = val
                    done = True
                except Exception as exc:
                    print("  warn: %s (%r)" % (item.name, exc))
        synced += 1 if done else 0
    print("modifier inputs synced: %d | radius=%.3f height=%.3f" % (
        synced, values["Sparkle Radius"], values["Sparkle Height"]))

print("=== done (not saved) ===")
