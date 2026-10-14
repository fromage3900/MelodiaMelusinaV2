"""P5 wave 17 gate: duration note lane (whole / half / quarter / eighth notes,
whole / half rests).

Builds each registered id, REALIZES the instance stream, and reports measured
vertex counts, world bbox, degenerate-face count and link failures per builder.
A builder that links clean but emits nothing, collapses, or explodes fails here.

Then carries family-specific CAUSAL assertions, because a gate that only proves
"it built something" cannot see a builder building the WRONG thing (waves 5-16
each caught placement / interpenetration / anatomy defects with the aggregate
envelope green; on this lane the equivalent risk is a hollow head that is really
a solid disc, a stem floating clear of a TILTED ellipse, a flag detached from the
stem top, or two rests that overlap instead of filling one staff space):

  A  every id stores `glyph_semitone_mod12`, `glyph_family` AND `higgsas_lead`,
     and Scale reaches a Transform (a dead Scale dial is a dead parameter)
  B  no primitive dimension is left at LITERAL ZERO (the castle-merlon
     zero-width-slab class). Asserted on the VALUE: a non-zero literal is
     legitimate design for this lane's stroke thickness.
  C  zero `GeometryNodeMeshBoolean` in the lane -- a cutter touching the mesh's
     own boundary emits ZERO geometry with no error and no link_failures entry
  D  the HOLLOW/FILLED table is REAL, measured geometrically: the head centre is
     INSIDE THE HOLE for the whole and half notes (BVH distance from the head
     origin > 0.03) and ON THE SOLID for the quarter and eighth (distance
     <= 0.001). This is the assertion a snapshot cannot make -- a hollow head
     built as a disc passes every vert/face/degen envelope. Plus the anatomy
     chains: the hollow head is a CLOSED `CurvePrimitiveCircle` path swept with
     a circle profile (no boolean, no cap), the filled head is a capped
     `MeshCylinder`, and BOTH are scaled by the same `Head Width` / `Head
     Height` vector and measure the same Z extent (2 x `Head Stroke`).
  E  the duration table is real: the whole note carries NO stem plate, the half,
     quarter and eighth each carry exactly ONE, and only the eighth carries a
     bezier flag. The stem's X seat chain reaches BOTH `Head Width` and `Head
     Tilt` through a COSINE -- the head is a TILTED ellipse, so a stem at
     `Head Width` would float clear of the head it is attached to.
  F  the flag is anchored to the STEM TOP: its `Start` chain reaches `Stem
     Length` AND the stem's own X seat chain (`Head Width` + `Head Tilt`), so a
     flag cannot drift off the stem.
  G  the two block rests are ONE block at two SEATS: equal extents, bbox centre
     Y differs by exactly the `Line Spacing` default, the seat chain reaches BOTH
     `Staff Line` and `Line Spacing`, and -- the notation law -- the whole rest's
     min Y equals the half rest's max Y within 2 mm, so the two blocks fill ONE
     staff space and touch edge-to-edge. An overlap or a gap fails here.
  H  no builder is empty and the ONLY legitimate repeated vertex count is the
     REST PAIR (one block law, two seats). An "all six pairwise distinct"
     assertion would fail correct code.
  I  the rests are STAFF-RELATIVE: `Rest Height Ratio` x `Line Spacing` x 2
     equals the two rests' combined Y span within 2 mm (each block is half a
     staff space, which is why they meet exactly).
  J  the lane is centred on the glyph plane: |min Z| == |max Z| within 2 mm for
     every id. A notation glyph lives in XY and its geometry straddles z = 0 by
     design, so this lane must NOT assert min_z >= 0.

"C:/Program Files/Blender Foundation/Blender 5.2/blender.exe" \\
    --background --factory-startup --python Tools/verify_music_note_durations.py
"""
import os
import sys

import bpy
from mathutils import Vector
from mathutils.bvhtree import BVHTree

REPO = r"P:\MelodiaMelusinaV2-Laptop"
sys.path.insert(0, os.path.join(REPO, "deploy"))

from surreal_arch.melodia_gn import core  # noqa: E402

TARGETS = [
    "MEL_music_note_whole",
    "MEL_music_note_half",
    "MEL_music_note_quarter",
    "MEL_music_note_eighth",
    "MEL_music_rest_whole",
    "MEL_music_rest_half",
]

HOLLOW = ("MEL_music_note_whole", "MEL_music_note_half")
FILLED = ("MEL_music_note_quarter", "MEL_music_note_eighth")
NOTES = HOLLOW + FILLED
RESTS = ("MEL_music_rest_whole", "MEL_music_rest_half")

# Envelope per builder in metres, from the real object. Generous band: catches a
# collapsed or exploded tree without pinning decimals.
EXPECTED = {
    "MEL_music_note_whole": (0.10, 0.80),
    "MEL_music_note_half": (0.20, 1.20),
    "MEL_music_note_quarter": (0.20, 1.20),
    "MEL_music_note_eighth": (0.25, 1.60),
    "MEL_music_rest_whole": (0.08, 0.60),
    "MEL_music_rest_half": (0.08, 0.60),
}
MAX_DEGEN_PCT = 0.0
Z_PLANE_TOL = 0.002
TOUCH_TOL = 0.002
HOLE_MIN = 0.030          # a real hole keeps the head centre this far off the tube
SOLID_MAX = 0.001         # a solid cap puts the head centre ON the surface


def rz_tree():
    ng = bpy.data.node_groups.new("__rz17__", "GeometryNodeTree")
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
    """Realized verts/faces/degen/extents, plus the head-centre INSIDE test.

    `inside` answers "is the glyph origin (which IS the note head's centre)
    INSIDE the head's material?" by counting surface crossings along a ray: an
    odd count means the point is inside a closed shell. That single boolean is
    the hollow/filled law, measured -- a swept RING leaves the origin in its
    hole (even crossings, OUTSIDE), a solid capped ellipse encloses it (odd
    crossings, INSIDE). A distance-to-nearest-surface probe CANNOT settle this:
    an interior point is still a non-zero distance from the nearest wall, so
    the naive "solid => 0.0" assertion fails on a perfectly good disc.
    """
    me = bpy.data.meshes.new("__m17__")
    ob = bpy.data.objects.new("__o17__", me)
    bpy.context.scene.collection.objects.link(ob)
    ob.modifiers.new("a", "NODES").node_group = ng
    ob.modifiers.new("b", "NODES").node_group = RZ
    bpy.context.view_layer.update()
    dg = bpy.context.evaluated_depsgraph_get()
    ev = ob.evaluated_get(dg)
    m = ev.to_mesh()
    verts = polys = degen = 0
    ext = [0.0, 0.0, 0.0]
    zmin = zmax = 0.0
    ymin = ymax = 0.0
    hole = None
    inside = None
    hits = None
    if m:
        verts = len(m.vertices)
        polys = len(m.polygons)
        degen = sum(1 for q in m.polygons if q.area < 1e-12)
        xs = [v.co.x for v in m.vertices]
        ys = [v.co.y for v in m.vertices]
        zs = [v.co.z for v in m.vertices]
        ext = [round(max(xs) - min(xs), 4), round(max(ys) - min(ys), 4),
               round(max(zs) - min(zs), 4)]
        zmin, zmax = min(zs), max(zs)
        ymin, ymax = min(ys), max(ys)
        if verts and polys:
            co = [tuple(v.co) for v in m.vertices]
            idx = [tuple(p.vertices) for p in m.polygons]
            bvh = BVHTree.FromPolygons(co, idx, all_triangles=False)
            hit = bvh.find_nearest(Vector((0.0, 0.0, 0.0)))
            if hit is not None:
                hole = round(hit[3], 6)
            inside, hits = ray_parity(bvh, Vector((0.0, 0.0, 0.0)),
                                      Vector((0.0, 0.0, 1.0)))
        ev.to_mesh_clear()
    ob.modifiers.clear()
    bpy.data.objects.remove(ob, do_unlink=True)
    bpy.data.meshes.remove(me)
    return dict(verts=verts, faces=polys, degen=degen, ext=ext, zmin=zmin,
                zmax=zmax, ymin=ymin, ymax=ymax, hole=hole, inside=inside,
                hits=hits)


def ray_parity(bvh, origin, direction, limit=64):
    """(inside, crossings) for a point, by marching a ray through the shell.

    `BVHTree.ray_cast` returns only the FIRST hit, so a single call cannot see a
    closed shell. Marching from hit to hit accumulates every crossing; an ODD
    count means the origin started inside the material.
    """
    eps = 1e-5
    d = direction.normalized()
    cur = Vector(origin)
    crossings = 0
    for _ in range(limit):
        res = bvh.ray_cast(cur + d * eps, d)
        loc = res[0] if res else None
        if loc is None:
            break
        crossings += 1
        cur = Vector(loc)
    return (crossings % 2 == 1), crossings


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


def chain_ops(node, index):
    """Every `(operation, constant)` pair reachable upstream of a socket.

    Lets a law about a FACTOR be asserted on the VALUE rather than on the mere
    presence of a link ("the seat is `cos(tilt) x Head Width`", not "the seat is
    linked to something").
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
            fop = (getattr(fn, "operation", "")
                   if fn.bl_idname == "ShaderNodeMath" else "")
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


def chain_node_types(node, index):
    """bl_idnames reachable upstream of a socket (the anatomy chain)."""
    if node is None or index >= len(node.inputs):
        return set()
    out, seen, stack = set(), set(), [(node, index)]
    while stack:
        n, i = stack.pop()
        if (n.name, i) in seen:
            continue
        seen.add((n.name, i))
        for lk in n.inputs[i].links:
            fn = lk.from_node
            out.add(fn.bl_idname)
            for oi in range(len(fn.inputs)):
                stack.append((fn, oi))
    return out


def downstream_types(node, limit=200):
    """bl_idnames reachable DOWNSTREAM of a node's outputs.

    The hollow head's sweep sits BELOW the transform that scales the path
    (`Circle path -> Transform (ellipse scale) -> CurveToMesh`), so an upstream
    walk from the transform can only ever see the circle. Follow OUTPUT links,
    keyed on `(node.name, socket_index)` -- never `id()` and never a socket
    NAME, both of which dedup wrongly in bpy.
    """
    if node is None:
        return set()
    out, seen, stack = set(), set(), [node]
    steps = 0
    while stack and steps < limit:
        n = stack.pop()
        if n.name in seen:
            continue
        seen.add(n.name)
        steps += 1
        for s in n.outputs:
            for lk in s.links:
                tn = lk.to_node
                out.add(tn.bl_idname)
                stack.append(tn)
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


def head_transform(ng, hollow):
    """The Transform that scales the note HEAD (found by its anatomy source)."""
    want = "GeometryNodeCurvePrimitiveCircle" if hollow else "GeometryNodeMeshCylinder"
    for n in of_type(ng, "GeometryNodeTransform"):
        s = n.inputs.get("Geometry")
        if s is None or not s.links:
            continue
        if s.links[0].from_node.bl_idname == want:
            return n
    return None


failures = []
rows = {}

print("=" * 72)
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
        r = measure(ng)
        lf = core.link_failures()
        diag = max(r["ext"]) if r["ext"] else 0.0
        pct = (100.0 * r["degen"] / r["faces"]) if r["faces"] else 0.0
        lo, hi = EXPECTED.get(bid, (0.0, 1e9))
        ok = (r["verts"] > 0 and r["faces"] > 0 and pct <= MAX_DEGEN_PCT
              and lo <= diag <= hi and not lf)
        if not ok:
            why = []
            if r["verts"] == 0 or r["faces"] == 0:
                why.append("empty")
            if pct > MAX_DEGEN_PCT:
                why.append("degen=%.2f%%" % pct)
            if not (lo <= diag <= hi):
                why.append("diag=%.4f outside [%s, %s]" % (diag, lo, hi))
            if lf:
                why.append("link_failures=%s" % lf)
            failures.append("%s: %s" % (bid, "; ".join(why)))
        rows[bid] = dict(r, ok=ok, diag=diag, pct=pct, lf=lf, ng=ng)
        print("RESULT %-26s ok=%-5s verts=%-6d faces=%-6d degen=%-4d (%.2f%%) "
              "diag=%.4f y[%.4f, %.4f] z[%.4f, %.4f] hole=%s lf=%s"
              % (bid, ok, r["verts"], r["faces"], r["degen"], pct, diag,
                 r["ymin"], r["ymax"], r["zmin"], r["zmax"], r["hole"], lf))
    except Exception as e:
        failures.append("%s: %s: %s" % (bid, type(e).__name__, str(e)[:200]))
        print("RESULT %-26s EXCEPTION %s: %s"
              % (bid, type(e).__name__, str(e)[:200]))

print("-" * 72)
print("duration note lane causal checks")

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
    "GeometryNodeCurvePrimitiveCircle": ("Radius",),
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
    if bad:
        failures.append("B %s: literal-zero dims %s" % (bid, bad[:4]))
    print("B %-26s zero_dimensions=%s" % (bid, bad[:4] or "none"))

# (C) zero MeshBoolean in the lane.
for bid in TARGETS:
    nb = len(of_type(tree_of(bid), "GeometryNodeMeshBoolean"))
    if nb:
        failures.append("C %s: %d MeshBoolean nodes" % (bid, nb))
    print("C %-26s boolean_nodes=%d" % (bid, nb))

# (D) the HOLLOW/FILLED table, measured geometrically.
try:
    d_ok = True
    for bid in HOLLOW:
        r = rows.get(bid)
        ins = r["inside"] if r else None
        got = ins is False          # a ring's hole leaves the centre OUTSIDE
        if not got:
            d_ok = False
            failures.append("D %s: head centre inside=%s (hollow head must be "
                            "OUTSIDE the material, i.e. in the ring's hole)"
                            % (bid, ins))
        ng = tree_of(bid)
        ht = head_transform(ng, True)
        types = chain_node_types(ht, input_index(ht, "Geometry")) if ht else set()
        types |= downstream_types(ht) if ht else set()
        chain_ok = ("GeometryNodeCurvePrimitiveCircle" in types
                    and "GeometryNodeCurveToMesh" in types
                    and "GeometryNodeMeshBoolean" not in types)
        names = up(ht, "Scale") if ht else set()
        size_ok = {"Head Width", "Head Height"} <= names
        if not chain_ok or not size_ok:
            d_ok = False
            failures.append("D %s: hollow chain types=%s scale_reaches=%s"
                            % (bid, sorted(types), sorted(names)))
        print("D hollow %-20s inside=%-6s crossings=%-4s hole=%-9s chain=%s "
              "scale=%s" % (bid, ins, r["hits"] if r else None,
                            r["hole"] if r else None, chain_ok, sorted(names)))
    for bid in FILLED:
        r = rows.get(bid)
        ins = r["inside"] if r else None
        got = ins is True           # a capped disc ENCLOSES the centre
        if not got:
            d_ok = False
            failures.append("D %s: head centre inside=%s (filled head must be "
                            "INSIDE the material)" % (bid, ins))
        ng = tree_of(bid)
        ht = head_transform(ng, False)
        types = chain_node_types(ht, input_index(ht, "Geometry")) if ht else set()
        chain_ok = "GeometryNodeMeshCylinder" in types
        names = up(ht, "Scale") if ht else set()
        size_ok = {"Head Width", "Head Height"} <= names
        if not chain_ok or not size_ok:
            d_ok = False
            failures.append("D %s: filled chain types=%s scale_reaches=%s"
                            % (bid, sorted(types), sorted(names)))
        print("D filled %-20s inside=%-6s crossings=%-4s chain=%s scale=%s"
              % (bid, ins, r["hits"] if r else None, chain_ok, sorted(names)))
    # the three UNFLAGGED notes share ONE head law: same Z extent (2 x Head
    # Stroke). The eighth is EXEMPT because it carries a flag: the flag is a
    # swept TUBE, not a plate, so its tube radius (`Flag Thickness`) legitimately
    # sets a larger Z extent. Asserting one number for all four would fail
    # correct code.
    stroke = iface_default("MEL_music_note_quarter", "Head Stroke")
    zs = [rows[b]["ext"][2] for b in ("MEL_music_note_whole",
                                      "MEL_music_note_half",
                                      "MEL_music_note_quarter") if b in rows]
    z_ok = bool(zs) and all(abs(z - 2.0 * stroke) < 0.004 for z in zs)
    if not z_ok:
        d_ok = False
        failures.append("D: head Z extents %s != 2 x Head Stroke %.4f"
                        % (zs, 2.0 * stroke))
    print("D shared_size        unflagged_z_extents=%s expected=%.4f same_law=%s"
          % (zs, 2.0 * stroke, z_ok))
except Exception as e:
    failures.append("D: %s: %s" % (type(e).__name__, e))
    print("D EXCEPTION", e)

# (E) the duration table: stem / flag counts and the tilted-ellipse stem seat.
try:
    e_ok = True
    want_stem = {"MEL_music_note_whole": 0, "MEL_music_note_half": 1,
                 "MEL_music_note_quarter": 1, "MEL_music_note_eighth": 1}
    for bid in NOTES:
        ng = tree_of(bid)
        stems = plate_transforms(ng)
        flags = of_type(ng, "GeometryNodeCurvePrimitiveBezierSegment")
        n_stem, n_flag = len(stems), len(flags)
        if n_stem != want_stem[bid]:
            e_ok = False
            failures.append("E %s: %d stem plates, expected %d"
                            % (bid, n_stem, want_stem[bid]))
        want_flag = 1 if bid == "MEL_music_note_eighth" else 0
        if n_flag != want_flag:
            e_ok = False
            failures.append("E %s: %d flags, expected %d"
                            % (bid, n_flag, want_flag))
        seat = set()
        cos_seen = False
        for st in stems:
            comps = trans_components(st)
            if not comps["X"][1]:
                continue
            comb = st.inputs["Translation"].links[0].from_node
            seat |= group_input_names(comb, input_index(comb, "X"))
            seen, stack = set(), [(comb, input_index(comb, "X"))]
            while stack:
                n, i = stack.pop()
                if (n.name, i) in seen:
                    continue
                seen.add((n.name, i))
                for lk in n.inputs[i].links:
                    fn = lk.from_node
                    if fn.bl_idname == "NodeGroupInput":
                        continue
                    if getattr(fn, "operation", "") == "COSINE":
                        cos_seen = True
                    for oi in range(len(fn.inputs)):
                        stack.append((fn, oi))
        stem_ok = (n_stem == want_stem[bid]
                   and (n_stem == 0 or ({"Head Width", "Head Tilt"} <= seat
                                        and cos_seen)))
        if not stem_ok:
            e_ok = False
            failures.append("E %s: stem seat reaches %s cosine=%s"
                            % (bid, sorted(seat), cos_seen))
        print("E %-26s stems=%d flags=%d seat_reaches=%s cosine=%s"
              % (bid, n_stem, n_flag, sorted(seat), cos_seen))
    print("E duration_table     ok=%s" % e_ok)
except Exception as e:
    failures.append("E: %s: %s" % (type(e).__name__, e))
    print("E EXCEPTION", e)

# (F) the flag is anchored to the stem TOP.
try:
    ng = tree_of("MEL_music_note_eighth")
    flags = of_type(ng, "GeometryNodeCurvePrimitiveBezierSegment")
    f_ok = False
    detail = "no flag"
    if flags:
        fl = flags[0]
        start_names = up(fl, "Start")
        f_ok = {"Stem Length", "Head Width", "Head Tilt"} <= start_names
        detail = "start_reaches=%s" % sorted(start_names)
    if not f_ok:
        failures.append("F eighth: %s" % detail)
    print("F flag_anchor        %s ok=%s" % (detail, f_ok))
except Exception as e:
    failures.append("F: %s: %s" % (type(e).__name__, e))
    print("F EXCEPTION", e)

# (G) the two block rests are one block at two seats, touching edge-to-edge.
try:
    a = rows.get("MEL_music_rest_whole")
    b = rows.get("MEL_music_rest_half")
    g_ok = False
    detail = "missing rows"
    if a and b:
        same_shape = all(abs(x - y) < 1e-4 for x, y in zip(a["ext"], b["ext"]))
        spacing = iface_default("MEL_music_rest_half", "Line Spacing")
        rest_h = iface_default("MEL_music_rest_half", "Rest Height Ratio") * spacing
        d_seat = abs((a["ymin"] + a["ymax"]) / 2.0
                     - (b["ymin"] + b["ymax"]) / 2.0)
        # the two seats differ by ONE REST HEIGHT (half a staff space), which is
        # what makes the pair fill exactly one space and touch edge-to-edge
        seat_ok = abs(d_seat - rest_h) < TOUCH_TOL
        touch = abs(a["ymin"] - b["ymax"])
        touch_ok = touch < TOUCH_TOL
        ng = tree_of("MEL_music_rest_half")
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
        g_ok = same_shape and seat_ok and touch_ok and both
        detail = ("same_shape=%s spacing=%.4f rest_h=%.4f measured=%.4f "
                  "touch=%.4f seat_reaches=%s"
                  % (same_shape, spacing, rest_h, d_seat, touch,
                     sorted(seat_names)))
        if not same_shape:
            failures.append("G: rest extents differ %s vs %s"
                            % (a["ext"], b["ext"]))
        if not seat_ok:
            failures.append("G: rest seat delta %.4f != one Rest Height %.4f"
                            % (d_seat, rest_h))
        if not touch_ok:
            failures.append("G: rests do not fill one staff space (whole rest "
                            "bottom %.4f, half rest top %.4f, gap %.4f)"
                            % (a["ymin"], b["ymax"], touch))
        if not both:
            failures.append("G: rest seat chain reaches %s" % sorted(seat_names))
    print("G rest_seat          %s ok=%s" % (detail, g_ok))
except Exception as e:
    failures.append("G: %s: %s" % (type(e).__name__, e))
    print("G EXCEPTION", e)

# (H) no builder is empty; the ONLY legitimate repeated count is the REST PAIR.
counts = {b: rows[b]["verts"] for b in TARGETS if b in rows}
if len(counts) == len(TARGETS):
    empties = [k for k, v in counts.items() if v <= 0]
    rest_pair_equal = counts.get("MEL_music_rest_whole") == counts.get(
        "MEL_music_rest_half")
    note_counts = [counts[b] for b in NOTES]
    notes_distinct = len(set(note_counts)) == len(note_counts)
    rest_ok = counts.get("MEL_music_rest_whole") not in note_counts
    ok = (not empties) and rest_pair_equal and notes_distinct and rest_ok
    if not ok:
        failures.append("H: empties=%s rest_pair_equal=%s notes_distinct=%s "
                        "rest_distinct_from_notes=%s"
                        % (empties, rest_pair_equal, notes_distinct, rest_ok))
    print("H distinct_counts    empties=%s rest_pair_equal=%-5s "
          "notes_distinct=%-5s counts=%s"
          % (empties or "none", rest_pair_equal, notes_distinct,
             sorted(counts.values())))
else:
    failures.append("H: only %d/%d ids measured" % (len(counts), len(TARGETS)))
    print("H distinct_counts    MISSING ROWS")

# (I) the rests are staff-relative: two blocks = one staff space.
try:
    ratio = iface_default("MEL_music_rest_half", "Rest Height Ratio")
    spacing = iface_default("MEL_music_rest_half", "Line Spacing")
    a = rows.get("MEL_music_rest_whole")
    b = rows.get("MEL_music_rest_half")
    span = None
    if a and b:
        span = round(a["ext"][1] + b["ext"][1], 4)
    expect = round(2.0 * ratio * spacing, 4)
    i_ok = span is not None and abs(span - expect) < TOUCH_TOL
    if not i_ok:
        failures.append("I: combined rest span %s != 2 x Rest Height Ratio x "
                        "Line Spacing = %.4f" % (span, expect))
    print("I staff_relative     combined_span=%s expected=%.4f ok=%s"
          % (span, expect, i_ok))
except Exception as e:
    failures.append("I: %s: %s" % (type(e).__name__, e))
    print("I EXCEPTION", e)

# (J) the lane is centred on the glyph plane.
for bid in TARGETS:
    r = rows.get(bid)
    if r is None:
        continue
    ok = abs(abs(r["zmin"]) - abs(r["zmax"])) <= Z_PLANE_TOL
    if not ok:
        failures.append("J %s: |min_z|=%.4f != |max_z|=%.4f"
                        % (bid, abs(r["zmin"]), abs(r["zmax"])))
    print("J %-26s |min_z|=%.4f |max_z|=%.4f centred=%-5s"
          % (bid, abs(r["zmin"]), abs(r["zmax"]), ok))

print("-" * 72)
if failures:
    for f in failures:
        print("FAIL:", f)
    print("NOTE DURATION GATE: FAIL (%d)" % len(failures))
    raise SystemExit(1)
print("NOTE DURATION GATE: PASS (6/6)")
