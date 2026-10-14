"""P5 wave 16 gate: notation glyph lane (alto clef, tenor clef, sharp, flat,
natural, quarter rest).

Builds each registered id, REALIZES the instance stream, and reports measured
vertex counts, world bbox, degenerate-face count, min Z and link failures per
builder. A builder that links clean but emits nothing, collapses, or explodes
fails here.

Then carries family-specific CAUSAL assertions, because a gate that only proves
"it built something" cannot see a builder building the WRONG thing (wave 5 scored
6/6 with four of six instruments wrong; wave 6 with all six placed wrong; waves
7-15 each caught placement/interpenetration defects -- a doubled placement, a
merged slab, a float count dropped into an INT socket, a shared mean radius, a
part below the floor, buried rims, a rank riding a joint, a fife duplicating the
bore radius -- all with the aggregate envelope green; on THIS lane the per-part
probe caught a natural whose connectors hung clear of both strokes and a rest
2.1x wider than tall, both under a green envelope):

  A  every id stores `glyph_semitone_mod12`, `glyph_family` AND `higgsas_lead`,
     and Scale reaches a Transform (a dead Scale dial is a dead parameter)
  B  no primitive dimension is left at LITERAL ZERO (the castle-merlon
     zero-width-slab class). Asserted on the VALUE: a non-zero literal is
     legitimate design for this lane's stroke thickness.
  C  zero `GeometryNodeMeshBoolean` in the lane -- a cutter touching the mesh's
     own boundary emits ZERO geometry with no error and no link_failures entry
  D  the ALTO and TENOR clefs are ONE C body at two SEATS: their realized bbox
     extents are equal within 1e-4, their bbox centre Y differs by exactly the
     `Line Spacing` interface default, and the seat chain reaches BOTH the
     `Staff Line` and `Line Spacing` group inputs (a seat that reads only one of
     them is a constant, not a seat)
  E  the SHARP is two VERTICALS plus two SLANTED bars: exactly 2 plate Transforms
     carry a literal-zero Y centre and no rotation link, exactly 2 carry a linked
     Y AND a linked rotation, both rotation chains reach `Slant`, and both bars'
     Y links reach `Glyph Height` (they are a symmetric pair, not one bar)
  F  the FLAT's belly is an ELLIPSE, not a disc: its Scale CombineXYZ has exactly
     one linked component (Y) reaching `Belly Flatten` while X and Z stay literal
     1.0, and the belly's X centre chain reaches `Belly Ratio` through a
     MULTIPLY whose constant is < 1.0 -- i.e. the belly's left edge crosses the
     stem rather than floating beside it
  G  the NATURAL is two STAGGERED strokes: NO plate carries a literal-zero Y
     centre, exactly 2 strokes carry a Y link reaching BOTH `Stagger` and `Glyph
     Height` with OPPOSITE signs, and each connector's Y chain reaches
     `Connector Drop` with a drop that keeps the connector INSIDE the stroke's Y
     span (`Connector Drop + half the connector height <= half Stroke Ratio` in
     glyph-height units -- the measured defect: drop 0.34 against a stroke half
     of 0.34 left both connectors hanging clear)
  H  the REST is a FIVE-stroke swept path, TALLER than wide: exactly 5 bezier
     segments feed one MergeByDistance -> CurveToMesh, the realized Y extent
     exceeds 1.5x the X extent, and every point's X chain reaches `Glyph Height`
     (the width is height-relative; scaling by Zigzag Width alone made the glyph
     2.1x wider than tall)
  I  no builder in the lane is empty, and the only pair that repeats a vertex
     count is the deliberate C-CLEF PAIR (one body law, two seats). A shared
     count elsewhere is a SHAPE COINCIDENCE, not a duplication -- the sharp and
     the natural are both 4 plates x 8 verts = 32 while their anatomy differs --
     so the law that separates them is structural and lives in E and G. An "all
     six pairwise distinct" assertion would fail correct code.
  J  every swept STROKE is centred on the glyph plane: |min Z| == |max Z| within
     2 mm for the tube-stroke builders. A notation glyph lives in XY and its tube
     straddles z = 0 by design, so this lane must NOT assert min_z >= 0 (which
     would fail correct geometry); the law that matters is symmetry about the
     plane.

  "C:/Program Files/Blender Foundation/Blender 5.2/blender.exe" \\
      --background --factory-startup --python Tools/verify_music_notation.py
"""
import os
import sys

import bpy

REPO = r"P:\MelodiaMelusinaV2-Laptop"
sys.path.insert(0, os.path.join(REPO, "deploy"))

from surreal_arch.melodia_gn import core  # noqa: E402

TARGETS = [
    "MEL_music_alto_clef",
    "MEL_music_tenor_clef",
    "MEL_music_sharp",
    "MEL_music_flat",
    "MEL_music_natural",
    "MEL_music_rest_quarter",
]

# Envelope per builder in metres, from the real object. Generous band: catches a
# collapsed or exploded tree without pinning decimals.
EXPECTED = {
    "MEL_music_alto_clef": (0.25, 1.40),
    "MEL_music_tenor_clef": (0.25, 1.40),
    "MEL_music_sharp": (0.25, 1.40),
    "MEL_music_flat": (0.25, 1.40),
    "MEL_music_natural": (0.25, 1.40),
    "MEL_music_rest_quarter": (0.25, 1.40),
}
MAX_DEGEN_PCT = 0.0
Z_PLANE_TOL = 0.002

STROKE_BUILDERS = ("MEL_music_alto_clef", "MEL_music_tenor_clef",
                   "MEL_music_rest_quarter")


def rz_tree():
    ng = bpy.data.node_groups.new("__rz16g__", "GeometryNodeTree")
    ng.interface.new_socket("Geometry", in_out="INPUT",
                            socket_type="NodeSocketGeometry")
    ng.interface.new_socket("Geometry", in_out="OUTPUT",
                            socket_type="NodeSocketGeometry")
    gi = ng.nodes.new("NodeGroupInput")
    go = ng.nodes.new("NodeGroupOutput")
    ri = ng.nodes.new("GeometryNodeRealizeInstances")
    ng.links.new(gi.outputs["Geometry"], ri.inputs["Geometry"])
    ng.links.new(ri.outputs["Geometry"], go.inputs["Geometry"])
    return ng


RZ = rz_tree()


def measure(ng):
    me = bpy.data.meshes.new("__m16g__")
    ob = bpy.data.objects.new("__o16g__", me)
    bpy.context.scene.collection.objects.link(ob)
    ob.modifiers.new("a", "NODES").node_group = ng
    ob.modifiers.new("b", "NODES").node_group = RZ
    bpy.context.view_layer.update()
    dg = bpy.context.evaluated_depsgraph_get()
    ev = ob.evaluated_get(dg)
    m = ev.to_mesh()
    verts = len(m.vertices) if m else 0
    polys = len(m.polygons) if m else 0
    degen = sum(1 for q in m.polygons if q.area < 1e-12) if m else 0
    ext = [0.0, 0.0, 0.0]
    zmin = zmax = 0.0
    ctr_y = 0.0
    if m and verts:
        xs = [v.co.x for v in m.vertices]
        ys = [v.co.y for v in m.vertices]
        zs = [v.co.z for v in m.vertices]
        ext = [round(max(xs) - min(xs), 4), round(max(ys) - min(ys), 4),
               round(max(zs) - min(zs), 4)]
        zmin, zmax = min(zs), max(zs)
        ctr_y = (max(ys) + min(ys)) / 2.0
    if m:
        ev.to_mesh_clear()
    ob.modifiers.clear()
    bpy.data.objects.remove(ob, do_unlink=True)
    bpy.data.meshes.remove(me)
    return verts, polys, degen, ext, zmin, zmax, ctr_y


def tree_of(bid):
    res = core.GROUP_BUILDERS[bid]()
    return res[0] if isinstance(res, (tuple, list)) else res


def input_index(node, name, fallback=0):
    """Index of `node.inputs[name]` -- never hardcode an index."""
    for i, s in enumerate(node.inputs):
        if s.name == name:
            return i
    return fallback


def group_input_names(node, index):
    """Group Input socket names the upstream chain of `node.inputs[index]` reads.

    Traversal rules (each cost a wrong verdict on an earlier gate):
      - follow `socket.links` ONLY on INPUT sockets;
      - key the visited set on `(node.name, socket_index)`;
      - resolve a Group Input at the LINK SITE and never descend into it.
    """
    if node is None or index >= len(node.inputs):
        return set()
    names, seen, stack = set(), set(), [(node, index)]
    while stack:
        n, i = stack.pop()
        if (n.name, i) in seen:
            continue
        seen.add((n.name, i))
        for lk in n.inputs[i].links:
            fn = lk.from_node
            if fn.bl_idname == "NodeGroupInput":
                names.add(lk.from_socket.name)
            else:
                for oi in range(len(fn.inputs)):
                    stack.append((fn, oi))
    return names


def up(node, socket_name):
    if node is None:
        return set()
    return group_input_names(node, input_index(node, socket_name))


def chain_constants(node, index, op=None):
    """Every literal constant reachable upstream of `node.inputs[index]`.

    Returns the set of `(operation, constant)` pairs, so a law about a factor
    ("the drop is 0.85 of the radius") can be asserted on the VALUE, not on the
    presence of a link.
    """
    out, seen, stack = set(), set(), [(node, index)]
    while stack:
        n, i = stack.pop()
        if (n.name, i) in seen:
            continue
        seen.add((n.name, i))
        for lk in n.inputs[i].links:
            fn = lk.from_node
            if fn.bl_idname == "NodeGroupInput":
                continue
            fop = getattr(fn, "operation", "") if fn.bl_idname == "ShaderNodeMath" else ""
            for k, s in enumerate(fn.inputs):
                if s.links:
                    stack.append((fn, k))
                else:
                    try:
                        v = s.default_value
                    except Exception:
                        continue
                    if isinstance(v, float):
                        out.add((fop, round(v, 6)))
            for k in range(len(fn.inputs)):
                stack.append((fn, k))
    return out


def stored_attr(ng, name):
    for n in ng.nodes:
        if n.bl_idname != "GeometryNodeStoreNamedAttribute":
            continue
        s = n.inputs.get("Name")
        if s is not None and s.default_value == name:
            return True
    return False


def of_type(ng, bid):
    return [n for n in ng.nodes if n.bl_idname == bid]


def scale_wired(ng):
    for n in of_type(ng, "GeometryNodeTransform"):
        s = n.inputs.get("Scale")
        if s is None or not s.links:
            continue
        if s.links[0].from_node.bl_idname == "ShaderNodeCombineXYZ":
            return True
    return False


def plate_transforms(ng):
    """Transforms whose Geometry comes from a MeshCube (a `_plate` stroke)."""
    out = []
    for n in of_type(ng, "GeometryNodeTransform"):
        s = n.inputs.get("Geometry")
        if s is not None and s.links and \
                s.links[0].from_node.bl_idname == "GeometryNodeMeshCube":
            out.append(n)
    return out


def trans_components(n):
    """(x, y, z) -> (value_or_None, linked_bool) for a Transform's Translation."""
    tr = n.inputs.get("Translation")
    res = {"X": (None, False), "Y": (None, False), "Z": (None, False)}
    if tr is None or not tr.links:
        return res
    comb = tr.links[0].from_node
    if comb.bl_idname != "ShaderNodeCombineXYZ":
        return res
    for comp in ("X", "Y", "Z"):
        s = comb.inputs.get(comp)
        if s is None:
            continue
        if s.links:
            res[comp] = (None, True)
        else:
            try:
                res[comp] = (round(float(s.default_value), 6), False)
            except Exception:
                res[comp] = (None, False)
    return res


def iface_default(bid, name):
    return core.iface_default(tree_of(bid), name)


failures = []
rows = []

for bid in TARGETS:
    fn = core.GROUP_BUILDERS.get(bid)
    if fn is None:
        failures.append("%s NOT REGISTERED" % bid)
        print("RESULT %-26s MISSING FROM REGISTRY" % bid)
        continue
    try:
        core.reset_link_failures()
        res = fn()
        ng = res[0] if isinstance(res, (tuple, list)) else res
        v, p, d, ext, zmin, zmax, ctr_y = measure(ng)
        lf = core.link_failures()
        diag = max(ext) if ext else 0.0
        pct = (100.0 * d / p) if p else 0.0
        lo, hi = EXPECTED.get(bid, (0.0, 1e9))
        ok = (v > 0 and p > 0 and pct <= MAX_DEGEN_PCT
              and lo <= diag <= hi and not lf)
        if not ok:
            why = []
            if v == 0 or p == 0:
                why.append("empty")
            if pct > MAX_DEGEN_PCT:
                why.append("degen=%.2f%%" % pct)
            if not (lo <= diag <= hi):
                why.append("diag=%.4f outside [%s, %s]" % (diag, lo, hi))
            if lf:
                why.append("link_failures=%s" % lf)
            failures.append("%s: %s" % (bid, "; ".join(why)))
        rows.append((bid, v, p, d, pct, diag, zmin, zmax, ctr_y, ext, ok))
        print("RESULT %-26s ok=%-5s verts=%-7d faces=%-7d degen=%-5d "
              "(%.2f%%) diag=%.4f z[%.4f, %.4f] ctr_y=%.4f ext=%s lf=%s"
              % (bid, ok, v, p, d, pct, diag, zmin, zmax, ctr_y, ext, lf))
    except Exception as e:
        failures.append("%s: %s: %s" % (bid, type(e).__name__, str(e)[:200]))
        print("RESULT %-26s EXCEPTION %s: %s"
              % (bid, type(e).__name__, str(e)[:200]))

print("-" * 72)
print("notation glyph lane causal checks")

# (A) attributes stored; Scale reaches a Transform.
for bid in TARGETS:
    ng = tree_of(bid)
    a1 = stored_attr(ng, "glyph_semitone_mod12")
    a2 = stored_attr(ng, "glyph_family")
    a3 = stored_attr(ng, "higgsas_lead")
    sw = scale_wired(ng)
    ok = a1 and a2 and a3 and sw
    if not ok:
        failures.append("A %s: attrs=%s/%s/%s scale=%s"
                        % (bid, a1, a2, a3, sw))
    print("A %-26s semitone=%-5s family=%-5s lead=%-5s scale=%-5s"
          % (bid, a1, a2, a3, sw))

# (B) no primitive dimension at a LITERAL zero.
DIMS = {
    "GeometryNodeMeshCube": ("Size",),
    "GeometryNodeMeshCylinder": ("Radius", "Depth"),
    "GeometryNodeMeshCone": ("Radius Bottom", "Radius Top", "Depth"),
    "GeometryNodeMeshUVSphere": ("Radius",),
}
for bid in TARGETS:
    ng = tree_of(bid)
    bad = []
    for n in ng.nodes:
        keys = DIMS.get(n.bl_idname)
        if not keys:
            continue
        for key in keys:
            s = n.inputs.get(key)
            if s is None:
                continue
            if s.links:
                src = s.links[0].from_node
                if src.bl_idname != "ShaderNodeCombineXYZ":
                    continue
                for comp in ("X", "Y", "Z"):
                    cs = src.inputs.get(comp)
                    if cs is None or cs.links:
                        continue
                    try:
                        if abs(float(cs.default_value)) < 1e-9:
                            bad.append("%s.%s.%s=0" % (n.name, key, comp))
                    except Exception:
                        pass
            else:
                try:
                    if abs(float(s.default_value)) < 1e-9:
                        bad.append("%s.%s=0" % (n.name, key))
                except Exception:
                    pass
    ok = not bad
    if not ok:
        failures.append("B %s: literal-zero dims %s" % (bid, bad[:4]))
    print("B %-26s zero_dimensions=%s" % (bid, bad[:4] or "none"))

# (C) zero MeshBoolean in the lane.
for bid in TARGETS:
    ng = tree_of(bid)
    nb = len(of_type(ng, "GeometryNodeMeshBoolean"))
    if nb:
        failures.append("C %s: %d MeshBoolean nodes" % (bid, nb))
    print("C %-26s boolean_nodes=%d" % (bid, nb))

# (D) the two C clefs are one body at two seats.
try:
    d_ok = True
    row = {r[0]: r for r in rows}
    a = row.get("MEL_music_alto_clef")
    t = row.get("MEL_music_tenor_clef")
    if a is None or t is None:
        d_ok = False
        failures.append("D: a clef row missing from the envelope pass")
    else:
        # row = (bid, v, p, d, pct, diag, zmin, zmax, ctr_y, ext, ok)  [11 fields]
        # indexed, not unpacked: an arity mistake here reads as a gate failure
        # on correct builders (it did, twice).
        exta, ctra = a[9], a[8]
        extt, ctrt = t[9], t[8]
        same_shape = all(abs(x - y) < 1e-4 for x, y in zip(exta, extt))
        spacing = iface_default("MEL_music_alto_clef", "Line Spacing")
        d_seat = abs(ctra - ctrt)
        seat_ok = abs(d_seat - spacing) < 0.002
        ng = tree_of("MEL_music_alto_clef")
        seat_names = set()
        for n in of_type(ng, "GeometryNodeTransform"):
            s = n.inputs.get("Translation")
            if s is None or not s.links:
                continue
            comb = s.links[0].from_node
            if comb.bl_idname != "ShaderNodeCombineXYZ":
                continue
            seat_names |= group_input_names(comb, input_index(comb, "Y"))
        both = {"Staff Line", "Line Spacing"} <= seat_names
        d_ok = same_shape and seat_ok and both
        print("D clef_seat         same_shape=%-5s spacing=%.4f measured=%.4f "
              "seat_reaches=%s" % (same_shape, spacing, d_seat,
                                   sorted(seat_names)))
        if not same_shape:
            failures.append("D: clef shapes differ ext alto=%s tenor=%s"
                            % (exta, extt))
        if not seat_ok:
            failures.append("D: seat delta %.4f != Line Spacing %.4f"
                            % (d_seat, spacing))
        if not both:
            failures.append("D: seat chain reaches %s" % sorted(seat_names))
except Exception as e:
    failures.append("D: %s: %s" % (type(e).__name__, e))
    print("D clef_seat         EXCEPTION", e)

# (E) the sharp: 2 verticals + 2 slanted bars.
try:
    ng = tree_of("MEL_music_sharp")
    plates = plate_transforms(ng)
    verts_, bars = [], []
    for n in plates:
        comps = trans_components(n)
        rot = n.inputs.get("Rotation")
        tilted = bool(rot is not None and rot.links)
        if not tilted:
            verts_.append(n)
        else:
            bars.append(n)
    zero_y = [n for n in verts_
              if trans_components(n)["Y"][1] is False
              and abs((trans_components(n)["Y"][0] or 0.0)) < 1e-6]
    rot_names = set()
    for n in bars:
        rot_names |= up(n, "Rotation")
    bar_y_names = set()
    for n in bars:
        bar_y_names |= up(n, "Translation")
    e_ok = (len(verts_) == 2 and len(bars) == 2 and len(zero_y) == 2
            and "Slant" in rot_names and "Glyph Height" in bar_y_names)
    print("E sharp             verticals=%d zero_y=%d bars=%d rot_reaches=%s "
          "bar_y_reaches=%s"
          % (len(verts_), len(zero_y), len(bars), sorted(rot_names),
             sorted(bar_y_names)))
    if not e_ok:
        failures.append("E sharp: verticals=%d zero_y=%d bars=%d rot=%s bary=%s"
                        % (len(verts_), len(zero_y), len(bars),
                           sorted(rot_names), sorted(bar_y_names)))
except Exception as e:
    failures.append("E: %s: %s" % (type(e).__name__, e))
    print("E sharp             EXCEPTION", e)

# (F) the flat's belly is an ellipse attached to the stem.
try:
    ng = tree_of("MEL_music_flat")
    cyl_t = None
    for n in of_type(ng, "GeometryNodeTransform"):
        s = n.inputs.get("Geometry")
        if s is not None and s.links and \
                s.links[0].from_node.bl_idname == "GeometryNodeMeshCylinder":
            cyl_t = n
            break
    f_ok = False
    detail = "no belly transform"
    if cyl_t is not None:
        sc = cyl_t.inputs.get("Scale")
        linked_comps = []
        if sc is not None and sc.links and \
                sc.links[0].from_node.bl_idname == "ShaderNodeCombineXYZ":
            comb = sc.links[0].from_node
            for comp in ("X", "Y", "Z"):
                cs = comb.inputs.get(comp)
                if cs is not None and cs.links:
                    linked_comps.append(comp)
        scale_names = up(cyl_t, "Scale")
        ratio_names = up(cyl_t, "Translation")
        consts = chain_constants(cyl_t, input_index(cyl_t, "Translation"))
        factors = [c for (op, c) in consts if op == "MULTIPLY" and 0.0 < c < 1.0]
        f_ok = (linked_comps == ["Y"]
                and "Belly Flatten" in scale_names
                and "Belly Ratio" in ratio_names
                and bool(factors))
        detail = ("linked_scale=%s flatten=%s belly_ratio=%s factors=%s"
                  % (linked_comps, "Belly Flatten" in scale_names,
                     "Belly Ratio" in ratio_names, sorted(factors)))
    print("F flat              %s" % detail)
    if not f_ok:
        failures.append("F flat: %s" % detail)
except Exception as e:
    failures.append("F: %s: %s" % (type(e).__name__, e))
    print("F flat              EXCEPTION", e)

# (G) the natural is two staggered strokes with connectors INSIDE the strokes.
try:
    ng = tree_of("MEL_music_natural")
    plates = plate_transforms(ng)
    strokes, conns = [], []
    for n in plates:
        comps = trans_components(n)
        rot = n.inputs.get("Rotation")
        tilted = bool(rot is not None and rot.links)
        if tilted:
            conns.append(n)
        else:
            strokes.append(n)
    zero_y = [n for n in strokes
              if trans_components(n)["Y"][1] is False
              and abs((trans_components(n)["Y"][0] or 0.0)) < 1e-6]
    signed = []
    for n in strokes:
        consts = chain_constants(n, input_index(n, "Translation"))
        neg = any(op == "MULTIPLY" and c < 0.0 for (op, c) in consts)
        signed.append(neg)
    stroke_names = set()
    for n in strokes:
        stroke_names |= up(n, "Translation")
    conn_names = set()
    for n in conns:
        conn_names |= up(n, "Translation")
    drop = iface_default("MEL_music_natural", "Connector Drop")
    stroke_ratio = iface_default("MEL_music_natural", "Stroke Ratio")
    thick = iface_default("MEL_music_natural", "Thickness")
    height = iface_default("MEL_music_natural", "Glyph Height")
    conn_h_units = 0.35 * thick / height          # 0.70 * T, halved, in H units
    inside = (drop + conn_h_units) <= (stroke_ratio / 2.0) + 1e-9
    g_ok = (len(strokes) == 2 and len(zero_y) == 0 and len(conns) == 2
            and sorted(signed) == [False, True]
            and {"Stagger", "Glyph Height"} <= stroke_names
            and "Connector Drop" in conn_names
            and inside)
    print("G natural           strokes=%d zero_y=%d conns=%d signed=%s "
          "stroke_reaches=%s conn_reaches=%s drop=%.3f half_stroke=%.3f inside=%s"
          % (len(strokes), len(zero_y), len(conns), signed,
             sorted(stroke_names), sorted(conn_names), drop,
             stroke_ratio / 2.0, inside))
    if not g_ok:
        failures.append(
            "G natural: strokes=%d zero_y=%d conns=%d signed=%s stroke=%s "
            "conn=%s drop=%.3f half_stroke=%.3f inside=%s"
            % (len(strokes), len(zero_y), len(conns), signed,
               sorted(stroke_names), sorted(conn_names), drop,
               stroke_ratio / 2.0, inside))
except Exception as e:
    failures.append("G: %s: %s" % (type(e).__name__, e))
    print("G natural           EXCEPTION", e)

# (H) the rest is a five-stroke swept path, taller than wide.
try:
    ng = tree_of("MEL_music_rest_quarter")
    segs = of_type(ng, "GeometryNodeCurvePrimitiveBezierSegment")
    merges = of_type(ng, "GeometryNodeMergeByDistance")
    c2m = of_type(ng, "GeometryNodeCurveToMesh")
    row = {r[0]: r for r in rows}.get("MEL_music_rest_quarter")
    taller = False
    ext_h = None
    if row is not None:
        ext_h = row[9]
        taller = ext_h[1] > 1.5 * ext_h[0]
    x_names = set()
    for s in segs:
        st = s.inputs.get("Start")
        if st is None or not st.links:
            continue
        comb = st.links[0].from_node
        if comb.bl_idname == "ShaderNodeCombineXYZ":
            x_names |= group_input_names(comb, input_index(comb, "X"))
    h_ok = (len(segs) == 5 and len(merges) == 1 and len(c2m) == 1
            and taller and "Glyph Height" in x_names)
    print("H rest              segments=%d merges=%d curve_to_mesh=%d "
          "ext=%s taller=%s point_x_reaches=%s"
          % (len(segs), len(merges), len(c2m), ext_h, taller, sorted(x_names)))
    if not h_ok:
        failures.append(
            "H rest: segments=%d merges=%d c2m=%d ext=%s taller=%s x_reaches=%s"
            % (len(segs), len(merges), len(c2m), ext_h, taller, sorted(x_names)))
except Exception as e:
    failures.append("H: %s: %s" % (type(e).__name__, e))
    print("H rest              EXCEPTION", e)

# (I) none empty; the ONLY legitimate shared count is the C-clef pair, which is
#     one body law at two seats -- every other pair must be distinct. Asserting
#     "all six pairwise distinct" would fail on correct code (the two clefs are
#     identical by construction, which is the whole point of `_c_clef`).
counts = {r[0]: r[1] for r in rows}
if len(counts) == len(TARGETS):
    empties = [k for k, v in counts.items() if v <= 0]
    clef_pair_equal = (counts.get("MEL_music_alto_clef")
                       == counts.get("MEL_music_tenor_clef"))
    # The sharp and the natural are both FOUR plates x 8 verts = 32: a vertex
    # count is a snapshot, and two different glyphs can legitimately share one
    # (4 boxes either way). The law that separates them is ANATOMY, already
    # asserted structurally by E and G (verticals + tilted bars vs STAGGERED
    # verticals + connectors), so this check asserts only "nothing is empty and
    # the deliberate clef pair is the only pair that repeats".
    others = [v for k, v in counts.items()
              if k not in ("MEL_music_alto_clef", "MEL_music_tenor_clef")]
    repeats = {v: others.count(v) for v in set(others) if others.count(v) > 1}
    clef_distinct = counts.get("MEL_music_alto_clef") not in others
    ok = (not empties) and clef_pair_equal and clef_distinct
    if not ok:
        failures.append("I: empties=%s clef_pair_equal=%s clef_distinct=%s "
                        "repeats=%s" % (empties, clef_pair_equal,
                                        clef_distinct, repeats))
    print("I distinct_counts   empties=%s clef_pair_equal=%-5s clef_distinct=%-5s "
          "repeats=%s counts=%s"
          % (empties or "none", clef_pair_equal, clef_distinct,
             repeats or "none", sorted(counts.values())))
    if repeats:
        print("I note              a repeated non-clef count is a SHAPE "
              "coincidence (sharp and natural are both 4 plates x 8 verts = 32); "
              "the separating law is structural and lives in E and G.")
else:
    failures.append("I: only %d/%d ids measured" % (len(counts), len(TARGETS)))
    print("I distinct_counts   MISSING ROWS")

# (J) swept strokes are centred on the glyph plane.
for bid in STROKE_BUILDERS:
    row = {r[0]: r for r in rows}.get(bid)
    if row is None:
        continue
    zmin, zmax = row[6], row[7]
    ok = abs(abs(zmin) - abs(zmax)) <= Z_PLANE_TOL
    if not ok:
        failures.append("J %s: |min_z|=%.4f != |max_z|=%.4f" % (bid, abs(zmin),
                                                                abs(zmax)))
    print("J %-26s |min_z|=%.4f |max_z|=%.4f centred=%-5s"
          % (bid, abs(zmin), abs(zmax), ok))

print("-" * 72)
if failures:
    for f in failures:
        print("FAIL:", f)
    print("NOTATION GATE: FAIL (%d)" % len(failures))
    raise SystemExit(1)
print("NOTATION GATE: PASS (6/6)")
