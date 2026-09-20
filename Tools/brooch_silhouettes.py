# brooch_silhouettes.py — canonical home for brooch silhouette variant builders (v11.3).
# Ported 2026-09-19 from Saved/Audit/v11_variant_spike.py (spike = historical record; the
# construction is proven there: citadel + veil rendered clean on the repaired base).
#
# Consumers:
#   - Tools/gen_flower_brooch_v10.py builds the genome-selected preset after the standard parts.
#   - Saved/Audit/render_sil_icons.py builds each preset runtime-only for the icon contact sheet.
#
# Ownership: variants are ADDITIVE objects (like dangles/sparkles), never in-place swaps of the
# flower crown. "flower" (default) = no extra object. Trees are GN_BroochSil_*; objects are
# FlowerBrooch_Sil*. Scale-to-plate and placement are object-level (no tree interface changes).
#
# Nothing here executes at import time.
import math

import bpy
from mathutils import Vector


# ------------------------------------------------------------ node helpers ----
def mk(tree, t, name, loc):
    n = tree.nodes.new(t)
    n.name = name
    n.location = loc
    return n


def L(a, sa, b, sb):
    return a.id_data.links.new(a.outputs[sa], b.inputs[sb])


def dn(n, k, v):
    try:
        n.inputs[k].default_value = v
    except Exception as exc:
        print("  warn dn %s.%s (%r)" % (n.name, k, exc))


def mth(tree, name, op, loc, a=None, b=None):
    n = mk(tree, 'ShaderNodeMath', name, loc)
    n.operation = op
    if a is not None:
        n.inputs[0].default_value = a
    if b is not None:
        n.inputs[1].default_value = b
    return n


def tree_new(name):
    t = bpy.data.node_groups.new(name, 'GeometryNodeTree')
    t.interface.new_socket("Geometry", in_out='INPUT', socket_type='NodeSocketGeometry')
    t.interface.new_socket("Geometry", in_out='OUTPUT', socket_type='NodeSocketGeometry')
    gi = mk(t, 'NodeGroupInput', "in", (0, 0))
    go = mk(t, 'NodeGroupOutput', "out", (0, -400))
    return t, gi, go


def obj_new(name, tree):
    me = bpy.data.meshes.new(name)
    ob = bpy.data.objects.new(name, me)
    bpy.context.scene.collection.objects.link(ob)
    mod = ob.modifiers.new("GN", 'NODES')
    mod.node_group = tree
    return ob


def mat_simple(name, color, metallic=0.0, rough=0.5, emission=None, strength=0.0,
               specular=None):
    m = bpy.data.materials.get(name)
    if m is None:
        m = bpy.data.materials.new(name)
    m.use_nodes = True
    for n in m.node_tree.nodes:
        if n.type == 'BSDF_PRINCIPLED':
            n.inputs['Base Color'].default_value = (*color, 1)
            n.inputs['Metallic'].default_value = metallic
            n.inputs['Roughness'].default_value = rough
            if specular is not None:
                for key in ('Specular IOR Level', 'Specular'):
                    try:
                        n.inputs[key].default_value = specular
                        break
                    except Exception:
                        continue
            if emission:
                n.inputs['Emission Color'].default_value = (*emission, 1)
                n.inputs['Emission Strength'].default_value = strength
    return m


def add_set_material(tree, mat):
    go = next(n for n in tree.nodes if n.type == 'GROUP_OUTPUT')
    links = list(go.inputs['Geometry'].links)
    if not links:
        return
    src = links[0].from_socket
    for l in links:
        tree.links.remove(l)
    sm = tree.nodes.new('GeometryNodeSetMaterial')
    sm.name = "set material"
    sm.location = (go.location.x - 220, go.location.y + 60)
    sm.inputs['Material'].default_value = mat
    tree.links.new(src, sm.inputs['Geometry'])
    tree.links.new(sm.outputs['Geometry'], go.inputs['Geometry'])


# ---------------------------------------------------------------- citadel ----
def build_citadel():
    """8 pyramidal hard-surface rays + shoulder blocks + pylons + ring (flat facets)."""
    t, gi, go = tree_new("GN_BroochSil_Citadel")
    parts = []
    for i in range(8):
        th = math.radians(i * 45.0)
        el = math.radians(38.0)
        col = 200 * (i % 4)
        row = -160 * (i // 4)
        c = mk(t, 'GeometryNodeMeshCone', "ray %d" % i, (col, row))
        dn(c, "Vertices", 4)
        dn(c, "Radius Bottom", 0.050)
        dn(c, "Radius Top", 0.006)
        dn(c, "Depth", 0.34)
        tr = mk(t, 'GeometryNodeTransform', "ray %d xf" % i, (col + 160, row))
        L(c, "Mesh", tr, "Geometry")
        r0 = 0.150
        dn(tr, "Translation", (r0 * math.cos(th) * math.cos(el),
                               r0 * math.sin(th) * math.cos(el),
                               0.012 + 0.17 * math.sin(el)))
        dn(tr, "Rotation", (math.radians(90.0) - el, 0.0, th))
        parts.append((tr, "Geometry"))
        s = mk(t, 'GeometryNodeMeshCone', "shoulder %d" % i, (col, row - 160))
        dn(s, "Vertices", 4)
        dn(s, "Radius Bottom", 0.085)
        dn(s, "Radius Top", 0.052)
        dn(s, "Depth", 0.075)
        st = mk(t, 'GeometryNodeTransform', "shoulder %d xf" % i, (col + 160, row - 160))
        L(s, "Mesh", st, "Geometry")
        dn(st, "Translation", (0.135 * math.cos(th), 0.135 * math.sin(th), 0.010))
        dn(st, "Rotation", (math.radians(22.0), 0.0, th))
        parts.append((st, "Geometry"))
        p = mk(t, 'GeometryNodeMeshCone', "pylon %d" % i, (col, row - 320))
        dn(p, "Vertices", 4)
        dn(p, "Radius Bottom", 0.040)
        dn(p, "Radius Top", 0.006)
        dn(p, "Depth", 0.13)
        pt = mk(t, 'GeometryNodeTransform', "pylon %d xf" % i, (col + 160, row - 320))
        L(p, "Mesh", pt, "Geometry")
        pa = th + math.radians(22.5)
        dn(pt, "Translation", (0.165 * math.cos(pa), 0.165 * math.sin(pa), 0.055))
        dn(pt, "Rotation", (math.radians(14.0), 0.0, pa))
        parts.append((pt, "Geometry"))
    j = mk(t, 'GeometryNodeJoinGeometry', "join parts", (1400, -300))
    for src, ss in parts:
        L(src, ss, j, "Geometry")
    ring = mk(t, 'GeometryNodeCurvePrimitiveCircle', "ring path", (900, -600))
    dn(ring, "Radius", 0.150)
    dn(ring, "Resolution", 64)
    prof = mk(t, 'GeometryNodeCurvePrimitiveCircle', "ring prof", (900, -760))
    dn(prof, "Radius", 0.014)
    dn(prof, "Resolution", 8)
    c2m = mk(t, 'GeometryNodeCurveToMesh', "ring mesh", (1100, -680))
    L(ring, "Curve", c2m, "Curve")
    L(prof, "Curve", c2m, "Profile Curve")
    j2 = mk(t, 'GeometryNodeJoinGeometry', "join all", (1600, -300))
    L(j, "Geometry", j2, "Geometry")
    L(c2m, "Mesh", j2, "Geometry")
    L(j2, "Geometry", go, "Geometry")
    return t


# ------------------------------------------------------------------- veil ----
def build_veil():
    """Three woven 3D lissajous wires (3:2:5) + beads at every 12th node + a base ring.

    The manual 3D lissajous is the deterministic path; the Higgsas 'Lissajous Curve'
    node is attempted via the bridge and skipped cleanly when unavailable.
    """
    t, gi, go = tree_new("GN_BroochSil_Veil")
    try:
        from surreal_arch.higgsas_bridge import load_node
        hg = load_node("Lissajous Curve")
        print("VEIL: higgsas Lissajous Curve loaded:", hg is not None)
    except Exception as exc:
        print("VEIL: higgsas bridge unavailable (%r) -- manual lissajous" % (exc,))

    def manual_veil(i, delta, radius, z0, ampz, n=240):
        line = mk(t, 'GeometryNodeMeshLine', "m line %d" % i, (300, -200 - 300 * i))
        dn(line, "Count", n)
        dn(line, "Start Location", (0, 0, 0))
        dn(line, "Offset", (1, 0, 0))
        idx = mk(t, 'GeometryNodeInputIndex', "idx %d" % i, (300, -360 - 300 * i))
        tn = mth(t, "t %d" % i, 'DIVIDE', (480, -360 - 300 * i))
        L(idx, "Index", tn, 0)
        tn.inputs[1].default_value = float(n - 1)
        t2 = mth(t, "t*2pi %d" % i, 'MULTIPLY', (640, -360 - 300 * i), b=math.tau)
        L(tn, "Value", t2, 0)
        # x = radius*sin(3t+delta); y = radius*sin(2t); z = z0 + ampz*sin(5t+delta)
        xa = mth(t, "3t %d" % i, 'MULTIPLY', (800, -280 - 300 * i), b=3.0)
        L(t2, "Value", xa, 0)
        xb = mth(t, "3t+d %d" % i, 'ADD', (960, -280 - 300 * i), b=delta)
        L(xa, "Value", xb, 0)
        xs = mth(t, "sinx %d" % i, 'SINE', (1120, -280 - 300 * i))
        L(xb, "Value", xs, 0)
        xr = mth(t, "x %d" % i, 'MULTIPLY', (1280, -280 - 300 * i), b=radius)
        L(xs, "Value", xr, 0)
        ya = mth(t, "2t %d" % i, 'MULTIPLY', (800, -440 - 300 * i), b=2.0)
        L(t2, "Value", ya, 0)
        ys = mth(t, "siny %d" % i, 'SINE', (960, -440 - 300 * i))
        L(ya, "Value", ys, 0)
        yr = mth(t, "y %d" % i, 'MULTIPLY', (1120, -440 - 300 * i), b=radius)
        L(ys, "Value", yr, 0)
        za = mth(t, "5t %d" % i, 'MULTIPLY', (800, -600 - 300 * i), b=5.0)
        L(t2, "Value", za, 0)
        zb = mth(t, "5t+d %d" % i, 'ADD', (960, -600 - 300 * i), b=delta)
        L(za, "Value", zb, 0)
        zs = mth(t, "sinz %d" % i, 'SINE', (1120, -600 - 300 * i))
        L(zb, "Value", zs, 0)
        zr = mth(t, "z %d" % i, 'MULTIPLY', (1280, -600 - 300 * i), b=ampz)
        L(zs, "Value", zr, 0)
        zz = mth(t, "z0 %d" % i, 'ADD', (1440, -600 - 300 * i), b=z0)
        L(zr, "Value", zz, 0)
        comb = mk(t, 'ShaderNodeCombineXYZ', "pos %d" % i, (1600, -440 - 300 * i))
        L(xr, "Value", comb, "X")
        L(yr, "Value", comb, "Y")
        L(zz, "Value", comb, "Z")
        sp = mk(t, 'GeometryNodeSetPosition', "setpos %d" % i, (1780, -300 - 300 * i))
        L(line, "Mesh", sp, "Geometry")
        L(comb, "Vector", sp, "Position")
        return sp, idx

    veils = []
    for i, delta in enumerate((0.0, math.tau / 3.0, 2.0 * math.tau / 3.0)):
        sp, idx = manual_veil(i, delta, 0.165, 0.085, 0.055)
        c2c = mk(t, 'GeometryNodeMeshToCurve', "wire curve %d" % i, (2000, -300 - 300 * i))
        L(sp, "Geometry", c2c, "Mesh")
        prof = mk(t, 'GeometryNodeCurvePrimitiveCircle', "wire prof %d" % i, (2000, -440 - 300 * i))
        dn(prof, "Radius", 0.0045)
        dn(prof, "Resolution", 4)
        c2m = mk(t, 'GeometryNodeCurveToMesh', "wire mesh %d" % i, (2180, -360 - 300 * i))
        L(c2c, "Curve", c2m, "Curve")
        L(prof, "Curve", c2m, "Profile Curve")
        veils.append((c2m, "Mesh"))
        bead = mk(t, 'GeometryNodeMeshUVSphere', "bead %d" % i, (2000, -620 - 300 * i))
        dn(bead, "Radius", 0.0085)
        dn(bead, "Segments", 12)
        dn(bead, "Rings", 8)
        every = mth(t, "mod %d" % i, 'MODULO', (2000, -760 - 300 * i))
        L(idx, "Index", every, 0)
        every.inputs[1].default_value = 12.0
        eq = mth(t, "eq %d" % i, 'COMPARE', (2160, -760 - 300 * i))
        L(every, "Value", eq, 0)
        eq.inputs[1].default_value = 0.0
        inst = mk(t, 'GeometryNodeInstanceOnPoints', "bead inst %d" % i, (2360, -560 - 300 * i))
        L(sp, "Geometry", inst, "Points")
        L(bead, "Mesh", inst, "Instance")
        L(eq, "Value", inst, "Selection")
        veils.append((inst, "Instances"))
    ring = mk(t, 'GeometryNodeCurvePrimitiveCircle', "veil ring", (2000, -1500))
    dn(ring, "Radius", 0.165)
    dn(ring, "Resolution", 64)
    rprof = mk(t, 'GeometryNodeCurvePrimitiveCircle', "veil ring prof", (2000, -1640))
    dn(rprof, "Radius", 0.012)
    dn(rprof, "Resolution", 8)
    rc2m = mk(t, 'GeometryNodeCurveToMesh', "veil ring mesh", (2180, -1560))
    L(ring, "Curve", rc2m, "Curve")
    L(rprof, "Curve", rc2m, "Profile Curve")
    j = mk(t, 'GeometryNodeJoinGeometry', "veil join", (2600, -600))
    for src, ss in veils:
        L(src, ss, j, "Geometry")
    L(rc2m, "Mesh", j, "Geometry")
    L(j, "Geometry", go, "Geometry")
    return t


# ----------------------------------------------------------------- solving ----
PRESETS = {
    "star_citadel": build_citadel,
    "lissajous_veil": build_veil,
}

SIL_GOLD = "SIL_Gold"


def measured_bbox(objs):
    """World-space evaluated bbox across objs -> (lo, hi) Vectors."""
    dg = bpy.context.evaluated_depsgraph_get()
    lo = Vector((1e9, 1e9, 1e9))
    hi = Vector((-1e9, -1e9, -1e9))
    for ob in objs:
        if ob is None:
            continue
        ev = ob.evaluated_get(dg)
        for c in ev.bound_box:
            wv = ev.matrix_world @ Vector(c)
            lo = Vector((min(lo[i], wv[i]) for i in range(3)))
            hi = Vector((max(hi[i], wv[i]) for i in range(3)))
    return lo, hi


def plate_metrics(hero):
    """(center_xy, top_z, xy_span) of the hero brooch, evaluated."""
    lo, hi = measured_bbox([hero])
    ctr = ((lo.x + hi.x) * 0.5, (lo.y + hi.y) * 0.5)
    span = max(hi.x - lo.x, hi.y - lo.y)
    return ctr, hi.z, span


def build_silhouette(preset, hero=None, span_factor=1.15, sink=0.03):
    """Build the preset as an additive object, scale it to the plate, seat it on the flower.

    Returns a dict: {preset, tree, object, scale, span_before, span_after} or raises
    KeyError for an unknown preset. Object-level transform only (trees stay authored).
    """
    builder = PRESETS[preset]
    hero = hero or bpy.data.objects.get("FlowerBrooch")
    if hero is None:
        raise RuntimeError("hero FlowerBrooch not found; cannot solve silhouette")
    ctr, top_z, span = plate_metrics(hero)
    gold = mat_simple(SIL_GOLD, (1.0, 0.766, 0.336), metallic=1.0, rough=0.22)
    tree = builder()
    add_set_material(tree, gold)
    ob = obj_new("FlowerBrooch_Sil" + preset.split("_")[-1].title(), tree)
    ob.data.materials.append(gold)
    bpy.context.view_layer.update()
    lo, hi = measured_bbox([ob])
    span_before = max(hi.x - lo.x, hi.y - lo.y)
    k = (span * span_factor) / span_before if span_before > 1e-6 else 1.0
    ob.scale = (k, k, k)
    bpy.context.view_layer.update()
    lo, hi = measured_bbox([ob])
    bcx, bcy = (lo.x + hi.x) * 0.5, (lo.y + hi.y) * 0.5
    ob.location.x += ctr[0] - bcx
    ob.location.y += ctr[1] - bcy
    ob.location.z += (top_z - sink) - lo.z
    bpy.context.view_layer.update()
    lo, hi = measured_bbox([ob])
    span_after = max(hi.x - lo.x, hi.y - lo.y)
    print("[sil] preset=%s scale=%.4f span %.3f -> %.3f (plate %.3f, want %.3f)"
          % (preset, k, span_before, span_after, span, span * span_factor))
    return {"preset": preset, "tree": tree, "object": ob, "scale": k,
            "span_before": span_before, "span_after": span_after}


def active_preset(genome):
    """Read the genome's silhouette block -> preset name ('flower' = none)."""
    if not isinstance(genome, dict):
        return "flower"
    sil = genome.get("silhouette")
    if not isinstance(sil, dict):
        return "flower"
    a = sil.get("active", "flower")
    return a if a in PRESETS else "flower"
