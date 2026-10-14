"""MEL_bloom_* — musical flower builders (Resonant Rose, Cadence Peony) + MEL_petal.

Design (see Docs plan "Melusina Blooms"):
  * A bloom is whorls of one shared petal mesh. Each whorl k is rotated by the golden angle relative to the previous
    one (phyllotaxis) and carries a Fibonacci petal count (rose 5/8/13 = triad whorls, peony 5/8/13/21/21 = pentatonic layers).
  * `Growth` (0 bud .. 1 full bloom) opens each whorl: outer whorls open first, inner ones later (open-time per whorl).
  * Every realized vertex gets a `GrowthCol` colour attribute (R open-time, G whorl 0..1, B radius 0..1, A 1) — the Blender
    FBX exporter keeps colour attributes and UV maps, so UE/Niagara can drive the same bloom from the baked mesh.
  * Material index: 0 petals (Body), 1 stamens / receptacle (Accent), 2 stem + leaves (Stem).

Rules from melodia-gn-builder-workflow honoured: builders return `tree` (no auto music pass), binary Math nodes always get
both operands written, ShaderNodeMapRange does the clamping, Rotation sockets are fed from Euler-to-Rotation.
"""
from __future__ import annotations

import math

import bpy

try:                                    # inside the Melodia add-on the builders register themselves
    from .core import register_builder
except ImportError:                     # standalone (packaged product): no registry
    def register_builder(*_a, **_k):
        return None

GOLDEN = math.radians(137.5077)

# per species: whorls from INNER (first to form) to OUTER. r = radius, z = base height, s = petal scale,
# c = closed tilt (deg, bud), o = open tilt (deg, bloom), t0 = Growth at which the whorl starts to open.
SPECIES = {
    "rose": dict(
        counts=(3, 5, 8, 13),
        r=(0.012, 0.028, 0.046, 0.066), z=(0.070, 0.050, 0.030, 0.008),
        s=(0.55, 0.78, 0.95, 1.10), c=(2, 3, 5, 8), o=(4, 9, 15, 24),
        t0=(0.62, 0.42, 0.22, 0.00),
        petal=dict(length=0.075, width=1.25, cup=1.3, bend=0.22, bend_closed=-0.14, recurve=0.38, ruffle=0.012, tip=1.5),
    ),
    "peony": dict(
        counts=(5, 8, 13, 21, 21),
        r=(0.018, 0.034, 0.052, 0.074, 0.098), z=(0.034, 0.028, 0.020, 0.010, 0.000),
        s=(0.62, 0.76, 0.90, 1.04, 1.18), c=(3, 6, 10, 14, 18), o=(8, 16, 26, 38, 52),
        t0=(0.60, 0.46, 0.32, 0.16, 0.00),
        petal=dict(length=0.10, width=0.95, cup=0.55, bend=0.26, bend_closed=-0.08, recurve=0.30, ruffle=0.07, tip=0.8),
    ),
}


class _Proxy:
    def __init__(self, store):
        self.s = store

    @property
    def default_value(self):
        return self.s.inputs["Value"].default_value

    @default_value.setter
    def default_value(self, v):
        self.s.inputs["Value"].default_value = int(v)


class _PartNode:
    """Stands in for GeometryNodeSetMaterialIndex: tags faces with a 'part_mat' id that survives Join Geometry.
    _G.apply_parts() turns the id into the real material index once, after the final join."""

    def __init__(self, store):
        self.inputs = {"Geometry": store.inputs["Geometry"], "Material Index": _Proxy(store)}
        self.outputs = store.outputs


class _G:
    """Tiny node DSL: every operand is a float (written to the default) or a socket (linked)."""

    def __init__(self, tree):
        self.t = tree
        self.n = 0

    def apply_parts(self, geo):
        nm = self.node("GeometryNodeInputNamedAttribute", data_type="INT")
        nm.inputs["Name"].default_value = "part_mat"
        sm = self.node("GeometryNodeSetMaterialIndex", _real=True)
        self.t.links.new(geo, sm.inputs["Geometry"])
        self.t.links.new(nm.outputs[0], sm.inputs["Material Index"])
        return sm.outputs[0]

    def apply_materials(self, geo, gin, names):
        """Set Material per part id (0 petals, 1 accent, 2 stem) from material sockets on the group interface."""
        for k, nm in enumerate(names):
            at = self.node("GeometryNodeInputNamedAttribute", data_type="INT")
            at.inputs["Name"].default_value = "part_mat"
            sel = self.m("COMPARE", at.outputs[0], float(k), 0.1)
            sm = self.node("GeometryNodeSetMaterial")
            self.t.links.new(geo, sm.inputs["Geometry"])
            self.t.links.new(sel, sm.inputs["Selection"])
            self.t.links.new(gin.outputs[nm], sm.inputs["Material"])
            geo = sm.outputs[0]
        return geo

    def node(self, idname, **props):
        if idname == "GeometryNodeSetMaterialIndex" and not props.get("_real"):
            st = self.node("GeometryNodeStoreNamedAttribute", data_type="INT", domain="FACE")
            st.inputs["Name"].default_value = "part_mat"
            return _PartNode(st)
        props.pop("_real", None)
        nd = self.t.nodes.new(idname)
        nd.location = (200 * (self.n % 14), -140 * (self.n // 14))
        self.n += 1
        for k, v in props.items():
            setattr(nd, k, v)
        return nd

    def put(self, inp, v):
        if isinstance(v, (int, float)):
            inp.default_value = v
        else:
            self.t.links.new(v, inp)

    def m(self, op, a, b=0.0, c=0.0):
        nd = self.node("ShaderNodeMath", operation=op)
        for i, v in enumerate((a, b, c)):
            if i < len(nd.inputs):
                self.put(nd.inputs[i], v)
        return nd.outputs[0]

    def vec(self, x, y, z):
        nd = self.node("ShaderNodeCombineXYZ")
        for i, v in enumerate((x, y, z)):
            self.put(nd.inputs[i], v)
        return nd.outputs[0]

    def maprange(self, v, a0, a1, b0=0.0, b1=1.0, smooth=True):
        nd = self.node("ShaderNodeMapRange", data_type="FLOAT", interpolation_type="SMOOTHSTEP" if smooth else "LINEAR",
                       clamp=True)
        for name, val in (("Value", v), ("From Min", a0), ("From Max", a1), ("To Min", b0), ("To Max", b1)):
            self.put(nd.inputs[name], val)
        return nd.outputs["Result"]

    def euler(self, x, y, z):
        nd = self.node("FunctionNodeEulerToRotation")
        self.put(nd.inputs[0], self.vec(x, y, z))
        return nd.outputs[0]

    def link(self, a, b):
        self.t.links.new(a, b)


def _tree(name, params):
    """Fresh geometry tree + interface. params = [(name, type, default, min, max)]; returns (tree, group_input_node, G)."""
    old = bpy.data.node_groups.get(name)
    if old:
        bpy.data.node_groups.remove(old)
    tree = bpy.data.node_groups.new(name, "GeometryNodeTree")
    tree.interface.new_socket("Geometry", in_out="OUTPUT", socket_type="NodeSocketGeometry")
    for (pn, pt, dv, lo, hi) in params:
        s = tree.interface.new_socket(pn, in_out="INPUT", socket_type=pt)
        if dv is not None:
            s.default_value = dv
        if lo is not None:
            s.min_value, s.max_value = lo, hi
    gin = tree.nodes.new("NodeGroupInput")
    gin.location = (-400, 0)
    return tree, gin, _G(tree)


def _petal(g, gin, p):
    """Petal surface along +Z (base at origin, width on X, cup toward -Y), solidified. Returns geometry socket."""
    grid = g.node("GeometryNodeMeshGrid")
    grid.inputs["Vertices X"].default_value = 9
    grid.inputs["Vertices Y"].default_value = 15
    grid.inputs["Size X"].default_value = 1.0
    grid.inputs["Size Y"].default_value = 1.0
    pos = g.node("GeometryNodeInputPosition")
    xyz = g.node("ShaderNodeSeparateXYZ")
    g.link(pos.outputs[0], xyz.inputs[0])
    s = g.m("MULTIPLY", xyz.outputs["X"], 2.0)                       # across, -1..1
    u = g.m("SUBTRACT", 0.5, g.m("MULTIPLY", g.m("COSINE", g.m("MULTIPLY", g.m("ADD", xyz.outputs["Y"], 0.5), math.pi)), 0.5))   # along 0..1, rows dense at base + tip (round tip)
    # width profile: rounded superellipse over u^tip (zero width, vertical tangent at base and tip = no needle spikes)
    ut = g.m("POWER", u, p["tip"])
    prof = g.m("MAXIMUM", g.m("POWER", g.m("MAXIMUM", g.m("SUBTRACT", 1.0, g.m("POWER", g.m("ABSOLUTE", g.m("SUBTRACT", g.m("MULTIPLY", ut, 2.0), 1.0)), 2.4)), 0.0), 0.5), 0.03)
    w = g.m("MULTIPLY", g.m("MULTIPLY", prof, p["width"]), gin.outputs["Width"])
    L = gin.outputs["Length"]
    x = g.m("MULTIPLY", g.m("MULTIPLY", s, w), g.m("MULTIPLY", L, 0.5))
    # spine curl: outward bend + recurved tip (u^2, u^4)
    curl = g.m("ADD", g.m("MULTIPLY", g.m("POWER", u, 2.0), g.maprange(gin.outputs["Growth"], 0.05, 0.85, p["bend_closed"], p["bend"])),
               g.m("MULTIPLY", g.m("POWER", u, 4.0), p["recurve"]))
    # cup: edges lift toward the flower axis; margin ruffle: sin along u on the rim
    edge = g.m("POWER", g.m("ABSOLUTE", s), 2.0)
    cup = g.m("MULTIPLY", g.m("MULTIPLY", edge, p["cup"]), g.m("MULTIPLY", g.m("SUBTRACT", 1.0, g.m("MULTIPLY", u, 0.4)), 0.35))
    ruf = g.m("MULTIPLY", g.m("MULTIPLY", g.m("SINE", g.m("MULTIPLY", u, 6.0 * math.pi)), edge), g.m("MULTIPLY", gin.outputs["Ruffle"], 1.0))
    y = g.m("MULTIPLY", g.m("SUBTRACT", curl, cup), L)               # +curl leans outward (+Y), cup pulls -Y
    z = g.m("MULTIPLY", g.m("ADD", u, g.m("MULTIPLY", ruf, 0.5)), L)
    y = g.m("ADD", y, g.m("MULTIPLY", ruf, g.m("MULTIPLY", L, 0.4)))
    sp = g.node("GeometryNodeSetPosition")
    g.link(grid.outputs["Mesh"], sp.inputs["Geometry"])
    g.link(g.vec(x, y, z), sp.inputs["Position"])
    # keep the grid's UV as UV0 (u across, v along)
    uvs = g.node("GeometryNodeStoreNamedAttribute", data_type="FLOAT2", domain="CORNER")
    uvs.inputs["Name"].default_value = "UVMap"
    g.link(sp.outputs[0], uvs.inputs["Geometry"])
    g.link(grid.outputs["UV Map"], uvs.inputs["Value"])
    ext = g.node("GeometryNodeExtrudeMesh", mode="FACES")
    g.link(uvs.outputs[0], ext.inputs["Mesh"])
    g.put(ext.inputs["Offset Scale"], gin.outputs["Thickness"])
    ext.inputs["Individual"].default_value = False
    sm = g.node("GeometryNodeSetShadeSmooth")
    g.link(ext.outputs["Mesh"], sm.inputs["Geometry"])
    return sm.outputs[0]


def _whorl(g, gin, petal, p, spec, k):
    n = spec["counts"][k]
    line = g.node("GeometryNodeMeshLine")
    line.inputs["Count"].default_value = n
    idx = g.node("GeometryNodeInputIndex")
    rnd_yaw = g.node("FunctionNodeRandomValue", data_type="FLOAT")
    rnd_yaw.inputs["Min"].default_value = -1.0
    rnd_yaw.inputs["Max"].default_value = 1.0
    g.link(idx.outputs[0], rnd_yaw.inputs["ID"])
    g.put(rnd_yaw.inputs["Seed"], g.m("ADD", gin.outputs["Seed"], float(k * 17)))
    rnd_tilt = g.node("FunctionNodeRandomValue", data_type="FLOAT")
    rnd_tilt.inputs["Min"].default_value = -1.0
    rnd_tilt.inputs["Max"].default_value = 1.0
    g.link(idx.outputs[0], rnd_tilt.inputs["ID"])
    g.put(rnd_tilt.inputs["Seed"], g.m("ADD", gin.outputs["Seed"], float(k * 17 + 5)))
    # open amount for this whorl: smoothstep(Growth, t0 .. t0+0.45) (inner whorls open later, outer first)
    t0 = spec["t0"][k]
    e = g.maprange(gin.outputs["Growth"], t0, t0 + 0.6)
    tilt_deg = g.m("MULTIPLY_ADD", e, spec["o"][k] - spec["c"][k], spec["c"][k])
    tilt_deg = g.m("ADD", tilt_deg, g.m("MULTIPLY", rnd_tilt.outputs[0], 5.0))
    tilt = g.m("RADIANS", tilt_deg)
    ang = g.m("ADD", g.m("MULTIPLY", idx.outputs[0], 2.0 * math.pi / n), k * GOLDEN)
    ang = g.m("ADD", ang, g.m("MULTIPLY", rnd_yaw.outputs[0], 0.18))
    r = g.m("MULTIPLY_ADD", e, spec["r"][k] * 0.55, spec["r"][k] * 0.45)
    r = g.m("MULTIPLY", r, gin.outputs["Scale"])
    z0 = g.m("MULTIPLY", g.m("MULTIPLY_ADD", e, -0.5, 1.0), g.m("MULTIPLY", spec["z"][k], gin.outputs["Scale"]))
    px = g.m("MULTIPLY", g.m("MULTIPLY", g.m("SINE", ang), r), -1.0)
    py = g.m("MULTIPLY", g.m("COSINE", ang), r)
    sp = g.node("GeometryNodeSetPosition")
    g.link(line.outputs["Mesh"], sp.inputs["Geometry"])
    g.link(g.vec(px, py, z0), sp.inputs["Position"])
    inst = g.node("GeometryNodeInstanceOnPoints")
    g.link(sp.outputs[0], inst.inputs["Points"])
    g.link(petal, inst.inputs["Instance"])
    g.link(g.euler(g.m("MULTIPLY", tilt, -1.0), 0.0, ang), inst.inputs["Rotation"])
    sc = g.m("MULTIPLY", gin.outputs["Scale"], spec["s"][k])
    g.link(g.vec(sc, sc, sc), inst.inputs["Scale"])
    # per-instance growth data, then material 0
    st = g.node("GeometryNodeStoreNamedAttribute", data_type="FLOAT", domain="INSTANCE")
    st.inputs["Name"].default_value = "bloom_open_time"
    g.link(inst.outputs[0], st.inputs["Geometry"])
    g.put(st.inputs["Value"], t0)
    st2 = g.node("GeometryNodeStoreNamedAttribute", data_type="FLOAT", domain="INSTANCE")
    st2.inputs["Name"].default_value = "bloom_whorl"
    g.link(st.outputs[0], st2.inputs["Geometry"])
    g.put(st2.inputs["Value"], k / max(1, len(spec["counts"]) - 1))
    return st2.outputs[0]


def _stem_leaves(g, gin, spec):
    """Receptacle + stem (material 2) and a small stamen crown (material 1)."""
    cyl = g.node("GeometryNodeMeshCylinder")
    cyl.inputs["Vertices"].default_value = 10
    g.put(cyl.inputs["Radius"], g.m("MULTIPLY", gin.outputs["Stem Radius"], 1.0))
    g.put(cyl.inputs["Depth"], gin.outputs["Stem Length"])
    tr = g.node("GeometryNodeTransform")
    g.link(cyl.outputs["Mesh"], tr.inputs["Geometry"])
    g.put(tr.inputs["Translation"], g.vec(0.0, 0.0, g.m("MULTIPLY", gin.outputs["Stem Length"], -0.5)))
    mat = g.node("GeometryNodeSetMaterialIndex")
    g.link(tr.outputs[0], mat.inputs["Geometry"])
    mat.inputs["Material Index"].default_value = 2
    rec = g.node("GeometryNodeMeshUVSphere")
    rec.inputs["Segments"].default_value = 16
    rec.inputs["Rings"].default_value = 10
    g.put(rec.inputs["Radius"], g.m("MULTIPLY", gin.outputs["Scale"], 0.022))
    rtr = g.node("GeometryNodeTransform")
    g.link(rec.outputs["Mesh"], rtr.inputs["Geometry"])
    g.link(g.vec(1.0, 1.0, 0.7), rtr.inputs["Scale"])
    g.put(rtr.inputs["Translation"], g.vec(0.0, 0.0, g.m("MULTIPLY", gin.outputs["Scale"], -0.012)))
    rmat = g.node("GeometryNodeSetMaterialIndex")
    g.link(rtr.outputs[0], rmat.inputs["Geometry"])
    rmat.inputs["Material Index"].default_value = 2
    stemj = g.node("GeometryNodeJoinGeometry")
    g.link(mat.outputs[0], stemj.inputs[0])
    g.link(rmat.outputs[0], stemj.inputs[0])
    # stamen crown: ring of small cones at the heart, shown as the bloom opens
    n = 24
    line = g.node("GeometryNodeMeshLine")
    line.inputs["Count"].default_value = n
    idx = g.node("GeometryNodeInputIndex")
    ang = g.m("MULTIPLY", idx.outputs[0], GOLDEN)
    rad = g.m("MULTIPLY", g.m("SQRT", g.m("DIVIDE", idx.outputs[0], float(n))), g.m("MULTIPLY", gin.outputs["Scale"], 0.012 * 3))
    sp = g.node("GeometryNodeSetPosition")
    g.link(line.outputs["Mesh"], sp.inputs["Geometry"])
    g.link(g.vec(g.m("MULTIPLY", g.m("COSINE", ang), rad), g.m("MULTIPLY", g.m("SINE", ang), rad),
                 g.m("MULTIPLY", gin.outputs["Scale"], 0.03)), sp.inputs["Position"])
    cone = g.node("GeometryNodeMeshCone")
    cone.inputs["Vertices"].default_value = 5
    g.put(cone.inputs["Radius Bottom"], g.m("MULTIPLY", gin.outputs["Scale"], 0.0016))
    cone.inputs["Radius Top"].default_value = 0.0
    g.put(cone.inputs["Depth"], g.m("MULTIPLY", gin.outputs["Scale"], 0.018))
    inst = g.node("GeometryNodeInstanceOnPoints")
    g.link(sp.outputs[0], inst.inputs["Points"])
    g.link(cone.outputs["Mesh"], inst.inputs["Instance"])
    # stamens appear as the bloom opens
    vis = g.maprange(gin.outputs["Growth"], 0.35, 0.8)
    g.link(g.vec(vis, vis, vis), inst.inputs["Scale"])
    real = g.node("GeometryNodeRealizeInstances")
    g.link(inst.outputs[0], real.inputs[0])
    m1 = g.node("GeometryNodeSetMaterialIndex")
    g.link(real.outputs[0], m1.inputs["Geometry"])
    m1.inputs["Material Index"].default_value = 1
    return stemj.outputs[0], m1.outputs[0]


def _build(species, name):
    spec = SPECIES[species]
    params = [("Growth", "NodeSocketFloat", 1.0, 0.0, 1.0), ("Seed", "NodeSocketFloat", 1.0, 0.0, 10000.0),
              ("Scale", "NodeSocketFloat", 1.0, 0.05, 10.0), ("Length", "NodeSocketFloat", spec["petal"]["length"], 0.01, 1.0),
              ("Width", "NodeSocketFloat", 1.0, 0.1, 3.0), ("Ruffle", "NodeSocketFloat", spec["petal"]["ruffle"], 0.0, 0.3),
              ("Thickness", "NodeSocketFloat", 0.0035, 0.0005, 0.02),
              ("Stem Length", "NodeSocketFloat", 0.22, 0.02, 2.0), ("Stem Radius", "NodeSocketFloat", 0.0045, 0.001, 0.05)] + [("Petal Material", "NodeSocketMaterial", None, None, None), ("Accent Material", "NodeSocketMaterial", None, None, None), ("Stem Material", "NodeSocketMaterial", None, None, None)]
    tree, gin, g = _tree(name, params)
    petal = _petal(g, gin, spec["petal"])
    parts = []
    for k in range(len(spec["counts"])):
        parts.append(_whorl(g, gin, petal, spec["petal"], spec, k))
    join = g.node("GeometryNodeJoinGeometry")
    for pt in parts:
        g.link(pt, join.inputs[0])
    real = g.node("GeometryNodeRealizeInstances")
    g.link(join.outputs[0], real.inputs[0])
    mat0 = g.node("GeometryNodeSetMaterialIndex")
    g.link(real.outputs[0], mat0.inputs["Geometry"])
    mat0.inputs["Material Index"].default_value = 0
    # GrowthCol colour attribute from the stored per-instance data (R open-time, G whorl, B radius 0..1)
    pos = g.node("GeometryNodeInputPosition")
    xyz = g.node("ShaderNodeSeparateXYZ")
    g.link(pos.outputs[0], xyz.inputs[0])
    rad = g.m("DIVIDE", g.m("SQRT", g.m("ADD", g.m("POWER", xyz.outputs["X"], 2.0), g.m("POWER", xyz.outputs["Y"], 2.0))),
              spec["r"][-1] + spec["petal"]["length"])
    ot = g.node("GeometryNodeInputNamedAttribute", data_type="FLOAT")
    ot.inputs["Name"].default_value = "bloom_open_time"
    wh = g.node("GeometryNodeInputNamedAttribute", data_type="FLOAT")
    wh.inputs["Name"].default_value = "bloom_whorl"
    col = g.node("FunctionNodeCombineColor")
    g.link(ot.outputs[0], col.inputs[0])
    g.link(wh.outputs[0], col.inputs[1])
    g.put(col.inputs[2], g.maprange(rad, 0.0, 1.0, 0.0, 1.0, smooth=False))
    col.inputs[3].default_value = 1.0
    gc = g.node("GeometryNodeStoreNamedAttribute", data_type="FLOAT_COLOR", domain="POINT")
    gc.inputs["Name"].default_value = "GrowthCol"
    g.link(mat0.outputs[0], gc.inputs["Geometry"])
    g.link(col.outputs[0], gc.inputs["Value"])
    stem, stamens = _stem_leaves(g, gin, spec)
    out = g.node("GeometryNodeJoinGeometry")
    g.link(gc.outputs[0], out.inputs[0])
    g.link(stamens, out.inputs[0])
    g.link(stem, out.inputs[0])
    gout = tree.nodes.new("NodeGroupOutput")
    gout.location = (3000, 0)
    tree.links.new(g.apply_materials(g.apply_parts(out.outputs[0]), gin, ("Petal Material", "Accent Material", "Stem Material")), gout.inputs[0])
    return tree


LEAF = dict(length=0.10, width=0.9, cup=0.25, bend=0.25, bend_closed=-0.05, recurve=0.15, ruffle=0.01, tip=1.2)


def _vine(name):
    """MEL_vine_melody: a swaying vine whose length is Growth (0..1), leaves on 'Notes' along the arclength.
    vine_arc (0 root .. 1 tip) is stored and packed into GrowthCol.R so UE/Niagara can drive the same growth."""
    params = [("Growth", "NodeSocketFloat", 1.0, 0.0, 1.0), ("Seed", "NodeSocketFloat", 1.0, 0.0, 10000.0),
              ("Vine Length", "NodeSocketFloat", 1.2, 0.1, 6.0), ("Vine Radius", "NodeSocketFloat", 0.006, 0.001, 0.05),
              ("Notes", "NodeSocketInt", 9, 2, 40), ("Sway", "NodeSocketFloat", 0.07, 0.0, 0.5),
              ("Length", "NodeSocketFloat", LEAF["length"], 0.01, 0.5), ("Width", "NodeSocketFloat", 1.0, 0.1, 3.0),
              ("Ruffle", "NodeSocketFloat", LEAF["ruffle"], 0.0, 0.3), ("Thickness", "NodeSocketFloat", 0.002, 0.0005, 0.02)] + [("Petal Material", "NodeSocketMaterial", None, None, None), ("Accent Material", "NodeSocketMaterial", None, None, None), ("Stem Material", "NodeSocketMaterial", None, None, None)]
    tree, gin, g = _tree(name, params)
    line = g.node("GeometryNodeCurvePrimitiveLine")
    g.link(g.vec(0.0, 0.0, 0.0), line.inputs["Start"])
    g.link(g.vec(0.0, 0.0, gin.outputs["Vine Length"]), line.inputs["End"])
    rs = g.node("GeometryNodeResampleCurve")
    rs.inputs["Mode"].default_value = "Count"
    rs.inputs["Count"].default_value = 64
    g.link(line.outputs["Curve"], rs.inputs["Curve"])
    arc = g.node("GeometryNodeSplineParameter").outputs["Factor"]
    pos = g.node("GeometryNodeInputPosition")
    xyz = g.node("ShaderNodeSeparateXYZ")
    g.link(pos.outputs[0], xyz.inputs[0])
    ph = g.m("MULTIPLY", gin.outputs["Seed"], 1.7)
    wob = g.m("MULTIPLY", arc, gin.outputs["Sway"])
    sx = g.m("MULTIPLY", wob, g.m("SINE", g.m("ADD", g.m("MULTIPLY", arc, 14.0), ph)))
    sy = g.m("MULTIPLY", wob, g.m("COSINE", g.m("ADD", g.m("MULTIPLY", arc, 11.0), ph)))
    setp = g.node("GeometryNodeSetPosition")
    g.link(rs.outputs[0], setp.inputs["Geometry"])
    g.link(g.vec(sx, sy, xyz.outputs["Z"]), setp.inputs["Position"])
    trim = g.node("GeometryNodeTrimCurve")                              # growth = trim the vine to Growth
    g.link(setp.outputs[0], trim.inputs["Curve"])
    g.link(gin.outputs["Growth"], trim.inputs["End"])
    arc2 = g.node("GeometryNodeSplineParameter").outputs["Factor"]
    sr = g.node("GeometryNodeSetCurveRadius")
    g.link(trim.outputs[0], sr.inputs["Curve"])
    g.put(sr.inputs["Radius"], g.m("MULTIPLY", gin.outputs["Vine Radius"], g.m("SUBTRACT", 1.0, g.m("MULTIPLY", arc2, 0.7))))
    arcs = g.node("GeometryNodeStoreNamedAttribute", data_type="FLOAT", domain="POINT")
    arcs.inputs["Name"].default_value = "vine_arc"
    g.link(sr.outputs[0], arcs.inputs["Geometry"])
    g.put(arcs.inputs["Value"], g.node("GeometryNodeSplineParameter").outputs["Factor"])
    circ = g.node("GeometryNodeCurvePrimitiveCircle")
    circ.inputs["Resolution"].default_value = 8
    g.put(circ.inputs["Radius"], gin.outputs["Vine Radius"])
    c2m = g.node("GeometryNodeCurveToMesh")
    g.put(c2m.inputs["Scale"], g.m("SUBTRACT", 1.0, g.m("MULTIPLY", g.node("GeometryNodeSplineParameter").outputs["Factor"], 0.7)))
    g.link(arcs.outputs[0], c2m.inputs["Curve"])
    g.link(circ.outputs["Curve"], c2m.inputs["Profile Curve"])
    c2m.inputs["Fill Caps"].default_value = True
    stem_mat = g.node("GeometryNodeSetMaterialIndex")
    g.link(c2m.outputs[0], stem_mat.inputs["Geometry"])
    stem_mat.inputs["Material Index"].default_value = 2
    pts = g.node("GeometryNodeResampleCurve")             # leaves at the note positions
    pts.inputs["Mode"].default_value = "Count"
    g.link(sr.outputs[0], pts.inputs["Curve"])
    g.link(gin.outputs["Notes"], pts.inputs["Count"])
    c2p = g.node("GeometryNodeCurveToPoints", mode="EVALUATED")
    g.link(pts.outputs[0], c2p.inputs["Curve"])
    idx = g.node("GeometryNodeInputIndex")
    yaw = g.m("ADD", g.m("MULTIPLY", idx.outputs[0], GOLDEN), g.m("MULTIPLY", gin.outputs["Seed"], 0.31))
    leaf = _petal(g, gin, LEAF)
    inst = g.node("GeometryNodeInstanceOnPoints")
    g.link(c2p.outputs["Points"], inst.inputs["Points"])
    g.link(leaf, inst.inputs["Instance"])
    g.link(g.euler(-0.9, 0.0, yaw), inst.inputs["Rotation"])
    ap = g.m("DIVIDE", idx.outputs[0], g.m("MAXIMUM", g.m("SUBTRACT", gin.outputs["Notes"], 1.0), 1.0))
    unf = g.maprange(gin.outputs["Growth"], g.m("MULTIPLY", ap, 0.9), g.m("ADD", g.m("MULTIPLY", ap, 0.9), 0.15))
    g.link(g.vec(unf, unf, unf), inst.inputs["Scale"])
    st = g.node("GeometryNodeStoreNamedAttribute", data_type="FLOAT", domain="INSTANCE")
    st.inputs["Name"].default_value = "vine_arc"
    g.link(inst.outputs[0], st.inputs["Geometry"])
    g.put(st.inputs["Value"], ap)
    real = g.node("GeometryNodeRealizeInstances")
    g.link(st.outputs[0], real.inputs[0])
    leaf_mat = g.node("GeometryNodeSetMaterialIndex")
    g.link(real.outputs[0], leaf_mat.inputs["Geometry"])
    leaf_mat.inputs["Material Index"].default_value = 2
    # tendrils: a small coil at every note, opposite the leaf, uncoiling in with the growth
    sprl = g.node("GeometryNodeCurveSpiral")
    sprl.inputs["Resolution"].default_value = 24
    sprl.inputs["Rotations"].default_value = 2.5
    sprl.inputs["Start Radius"].default_value = 0.002
    sprl.inputs["End Radius"].default_value = 0.022
    sprl.inputs["Height"].default_value = 0.035
    tprof = g.node("GeometryNodeCurvePrimitiveCircle")
    tprof.inputs["Resolution"].default_value = 5
    tprof.inputs["Radius"].default_value = 0.0016
    tmesh = g.node("GeometryNodeCurveToMesh")
    g.link(sprl.outputs["Curve"], tmesh.inputs["Curve"])
    g.link(tprof.outputs["Curve"], tmesh.inputs["Profile Curve"])
    tinst = g.node("GeometryNodeInstanceOnPoints")
    g.link(c2p.outputs["Points"], tinst.inputs["Points"])
    g.link(tmesh.outputs[0], tinst.inputs["Instance"])
    g.link(g.euler(-1.2, 0.0, g.m("ADD", yaw, math.pi)), tinst.inputs["Rotation"])
    tg = g.maprange(gin.outputs["Growth"], g.m("MULTIPLY", ap, 0.9), g.m("ADD", g.m("MULTIPLY", ap, 0.9), 0.2))
    g.link(g.vec(tg, tg, tg), tinst.inputs["Scale"])
    treal = g.node("GeometryNodeRealizeInstances")
    g.link(tinst.outputs[0], treal.inputs[0])
    tmat = g.node("GeometryNodeSetMaterialIndex")
    g.link(treal.outputs[0], tmat.inputs["Geometry"])
    tmat.inputs["Material Index"].default_value = 2
    join = g.node("GeometryNodeJoinGeometry")
    g.link(stem_mat.outputs[0], join.inputs[0])
    g.link(leaf_mat.outputs[0], join.inputs[0])
    g.link(tmat.outputs[0], join.inputs[0])
    va = g.node("GeometryNodeInputNamedAttribute", data_type="FLOAT")
    va.inputs["Name"].default_value = "vine_arc"
    col = g.node("FunctionNodeCombineColor")
    g.link(va.outputs[0], col.inputs[0])
    col.inputs[1].default_value = 0.0
    col.inputs[2].default_value = 0.0
    col.inputs[3].default_value = 1.0
    gc = g.node("GeometryNodeStoreNamedAttribute", data_type="FLOAT_COLOR", domain="POINT")
    gc.inputs["Name"].default_value = "GrowthCol"
    g.link(join.outputs[0], gc.inputs["Geometry"])
    g.link(col.outputs[0], gc.inputs["Value"])
    gout = tree.nodes.new("NodeGroupOutput")
    tree.links.new(g.apply_materials(g.apply_parts(gc.outputs[0]), gin, ("Petal Material", "Accent Material", "Stem Material")), gout.inputs[0])
    return tree


def _petal_only(name):
    """MEL_petal: one solid petal for Niagara petal-shed meshes; GrowthCol.R = along-petal factor."""
    params = [("Growth", "NodeSocketFloat", 1.0, 0.0, 1.0), ("Seed", "NodeSocketFloat", 1.0, 0.0, 10000.0),
              ("Length", "NodeSocketFloat", 0.075, 0.01, 0.5), ("Width", "NodeSocketFloat", 1.2, 0.1, 3.0),
              ("Ruffle", "NodeSocketFloat", 0.02, 0.0, 0.3), ("Thickness", "NodeSocketFloat", 0.0025, 0.0005, 0.02)] + [("Petal Material", "NodeSocketMaterial", None, None, None), ("Accent Material", "NodeSocketMaterial", None, None, None), ("Stem Material", "NodeSocketMaterial", None, None, None)]
    tree, gin, g = _tree(name, params)
    petal = _petal(g, gin, dict(SPECIES["rose"]["petal"], bend=0.6, bend_closed=0.05, recurve=0.5))
    pos = g.node("GeometryNodeInputPosition")
    xyz = g.node("ShaderNodeSeparateXYZ")
    g.link(pos.outputs[0], xyz.inputs[0])
    col = g.node("FunctionNodeCombineColor")
    g.put(col.inputs[0], g.m("DIVIDE", xyz.outputs["Z"], gin.outputs["Length"]))
    col.inputs[1].default_value = 0.0
    col.inputs[2].default_value = 0.0
    col.inputs[3].default_value = 1.0
    gc = g.node("GeometryNodeStoreNamedAttribute", data_type="FLOAT_COLOR", domain="POINT")
    gc.inputs["Name"].default_value = "GrowthCol"
    g.link(petal, gc.inputs["Geometry"])
    g.link(col.outputs[0], gc.inputs["Value"])
    gout = tree.nodes.new("NodeGroupOutput")
    tree.links.new(gc.outputs[0], gout.inputs[0])
    return tree


def build_vine_melody(name="MEL_vine_melody"):
    return _vine(name)


def build_petal(name="MEL_petal"):
    return _petal_only(name)


def build_bloom_rose(name="MEL_bloom_rose"):
    return _build("rose", name)


def build_bloom_peony(name="MEL_bloom_peony"):
    return _build("peony", name)


register_builder("MEL_bloom_rose", build_bloom_rose, "Resonant Rose",
                 "Triad rose: 3/5/8/13 petals, golden-angle whorls, Growth 0=bud..1=bloom, GrowthCol attribute.",
                 category="Flora", hidden=False, role="hero", params=None)
register_builder("MEL_bloom_peony", build_bloom_peony, "Cadence Peony",
                 "Pentatonic peony: 5/8/13/21/21 ruffled layers, Growth 0=bud..1=bloom, GrowthCol attribute.",
                 category="Flora", hidden=False, role="hero", params=None)
register_builder("MEL_vine_melody", build_vine_melody, "Melody Vine",
                 "Swaying vine whose length is Growth, leaves on 'Notes' along arclength, vine_arc/GrowthCol attributes.",
                 category="Flora", hidden=False, role="hero", params=None)
register_builder("MEL_petal", build_petal, "Bloom Petal",
                 "Single curled petal for Niagara petal shed; GrowthCol.R = along-petal factor.",
                 category="Flora", hidden=False, role="hero", params=None)
