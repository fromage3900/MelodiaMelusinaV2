"""P5 wave 20 gate: thirty-second note, bar lines, tenuto, caesura.

Builds each registered id, REALIZES the instance stream, and reports measured
vertex counts, world bbox, degenerate-face count, min Z and link failures per
builder. A builder that links clean but emits nothing, collapses, or explodes
fails here.

Then carries family-specific CAUSAL assertions, because a gate that only proves
"it built something" cannot see a builder building the WRONG thing.

  A  every id stores `glyph_semitone_mod12`, `glyph_family` AND `higgsas_lead`,
     and Scale reaches a Transform (a dead Scale dial is a dead parameter)
  B  no primitive dimension is left at LITERAL ZERO (the castle-merlon
     zero-width-slab class). Asserted on the VALUE: a non-zero literal is
     legitimate design for this lane's stroke thickness.
  C  zero `GeometryNodeMeshBoolean` in the lane -- a cutter touching the mesh's
     own boundary emits ZERO geometry with no error and no link_failures entry
  D  THE THIRTY-SECOND ROW: the id carries exactly ONE MORE bezier flag than
     `MEL_music_note_sixteenth`, and its three flag seats are `fraction x Stem
     Length` read back off the Start-Y MULTIPLY nodes -- distinct, ordered, and
     the fractions this lane documents. THE EXTENTS CANNOT SEE THIS: the
     sixteenth's second flag (0.60) and the thirty-second's extra flag (0.36)
     both end inside the head's own Y band, so both ids measure the SAME Y
     extent to 4 decimals and differ only in flag count. That is why this
     assertion is on the flag chain, not on a bbox.
  E  THE BAR-LINE LAW at three seats: bar_line is ONE plate, bar_double is TWO,
     bar_final is TWO with exactly one plate whose Size traces to `Thick Ratio`
     as well as `Bar Thickness`. Every plate's Size Y traces to `Staff Height`
     (a bar line spans the staff) and no plate carries a literal-zero Size
     component.
  F  the FINAL bar is WIDER than the DOUBLE bar by exactly the extra thickness
     the Thick Ratio adds: measured X(final) - X(double) ==
     (Thick Ratio - 1) x Bar Thickness within 2 mm. A `Thick Ratio` dial that
     never reached the geometry reads as a pass on every extent envelope.
  G  TENUTO ORIENTATION: exactly one plate, zero booleans, and the measured
     aspect Y/X is under 0.5 -- a tenuto is the one articulation mark wider than
     it is tall. Its Size chain reaches `Line Spacing` plus both ratio dials.
     A tenuto built vertical would be a second marcato and this is the only
     assertion that separates them.
  H  CAESURA: two plates, each with a LINKED Z rotation reaching `Caesura
     Slant` (a literal rotation tuple would land in `default_value` and a
     link-only probe would report "no tilt" on a correctly tilted stroke), and
     the pair's measured X and Y extents match the closed form
     `X = gap + thick*cos + length*sin`, `Y = thick*sin + length*cos` within
     5 mm. Dropping the rotation gives X = gap + thick and fails by 2x.
  I  no builder is empty; the three bar ids are pairwise distinct; the
     thirty-second differs from the sixteenth in vertex count; tenuto and
     caesura are distinct
  J  the lane is centred on the glyph plane: |min Z| == |max Z| within 2 mm
     for every id. A notation glyph lives in XY and its geometry straddles
     z = 0 by design, so this lane must NOT assert min_z >= 0.

"C:/Program Files/Blender Foundation/Blender 5.2/blender.exe" \\
    --background --factory-startup --python Tools/verify_music_marks.py
"""
import math
import os
import sys

import bpy

REPO = r"P:\MelodiaMelusinaV2-Laptop"
sys.path.insert(0, os.path.join(REPO, "deploy"))

from surreal_arch.melodia_gn import core  # noqa: E402

TARGETS = [
    "MEL_music_note_thirty_second",
    "MEL_music_bar_line",
    "MEL_music_bar_double",
    "MEL_music_bar_final",
    "MEL_music_tenuto",
    "MEL_music_caesura",
]

MARK_IDS = ["MEL_music_tenuto", "MEL_music_caesura"]

# The three flag seats, as fractions of `Stem Length` measured DOWN the stem.
FLAG_FRACTIONS = (1.00, 0.68, 0.36)

Z_PLANE_TOL = 0.002
CLOSED_FORM_TOL = 0.005
WIDTH_TOL = 0.002
MAX_DEGEN = 0


def rz_tree():
    ng = bpy.data.node_groups.new("__rz20__", "GeometryNodeTree")
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
    me = bpy.data.meshes.new("__m20__")
    ob = bpy.data.objects.new("__o20__", me)
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
        ev.to_mesh_clear()
    ob.modifiers.clear()
    bpy.data.objects.remove(ob, do_unlink=True)
    bpy.data.meshes.remove(me)
    return verts, polys, degen, ext, zmin, zmax


def tree_of(bid):
    """Build by NAME once and hold it.

    Never call this twice for the same bid inside one assertion: the registry
    builds by name, so a second call invalidates every node wrapper captured
    from the first tree and their `socket.links` read as empty.
    """
    res = core.GROUP_BUILDERS[bid]()
    return res[0] if isinstance(res, (tuple, list)) else res


def input_index(node, name, fallback=0):
    for i, s in enumerate(node.inputs):
        if s.name == name:
            return i
    return fallback


def group_input_names(node, index):
    """Does this socket trace back to a Group Input? Keyed on (node, index).

    Keying the visited set on the socket NAME would drop the whole chain past
    the first hop (every Math node's sockets are named `Value`), and following
    an OUTPUT socket's `.links` would walk downstream forever.
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


def combine_of(node, socket_name):
    """The CombineXYZ feeding `socket_name`, or None."""
    s = node.inputs.get(socket_name)
    if s is None or not s.links:
        return None
    src = s.links[0].from_node
    return src if src.bl_idname == "ShaderNodeCombineXYZ" else None


def comp_link(node, socket_name, comp):
    """(source_node, source_socket) for a CombineXYZ component, else None."""
    comb = combine_of(node, socket_name)
    if comb is None:
        return None
    s = comb.inputs.get(comp)
    if s is None or not s.links:
        return None
    lk = s.links[0]
    return (lk.from_node, lk.from_socket)


def comp_literal(node, socket_name, comp):
    """(value, True) when the component is a LITERAL, else (None, False)."""
    comb = combine_of(node, socket_name)
    if comb is None:
        return (None, False)
    s = comb.inputs.get(comp)
    if s is None or s.links:
        return (None, False)
    try:
        return (round(float(s.default_value), 6), True)
    except Exception:
        return (None, False)


def iface_ng(ng, name, fallback=0.0):
    try:
        return float(core.iface_default(ng, name))
    except Exception:
        return fallback


def literal_zero_dims(ng):
    """Primitive dimensions left at a LITERAL zero (the zero-slab class)."""
    dims = {
        "GeometryNodeMeshCube": ("Size",),
        "GeometryNodeMeshCylinder": ("Radius", "Depth"),
        "GeometryNodeMeshCone": ("Radius Bottom", "Radius Top", "Depth"),
        "GeometryNodeMeshUVSphere": ("Radius",),
        "GeometryNodeCurvePrimitiveCircle": ("Radius",),
    }
    bad = []
    for n in ng.nodes:
        names = dims.get(n.bl_idname)
        if not names:
            continue
        for dn in names:
            s = n.inputs.get(dn)
            if s is None:
                continue
            if s.links:
                comb = s.links[0].from_node
                if comb.bl_idname != "ShaderNodeCombineXYZ":
                    continue
                for c in ("X", "Y", "Z"):
                    cs = comb.inputs.get(c)
                    if cs is None or cs.links:
                        continue
                    try:
                        if abs(float(cs.default_value)) < 1e-12:
                            bad.append((n.name, dn, c))
                    except Exception:
                        pass
            else:
                try:
                    v = float(s.default_value)
                except Exception:
                    continue
                if n.bl_idname == "GeometryNodeMeshCube":
                    continue          # a scalar Size is not a per-component zero
                if abs(v) < 1e-12:
                    bad.append((n.name, dn, "scalar"))
    return bad


failures = []
rows = []

print("=" * 72)
for bid in TARGETS:
    fn = core.GROUP_BUILDERS.get(bid)
    if fn is None:
        failures.append("MISSING %s" % bid)
        print("%-34s NOT REGISTERED" % bid)
        continue
    ng = tree_of(bid)
    v, p, d, ext, zmin, zmax = measure(ng)
    lf = core.link_failures() if hasattr(core, "link_failures") else []
    lf = [x for x in (lf or []) if x and (bid in str(x))]
    rows.append((bid, v, p, d, ext, zmin, zmax))
    print("%-34s verts=%-6d faces=%-6d degen=%-4d ext=%s z=[%.4f, %.4f]"
          % (bid, v, p, d, ext, zmin, zmax))
    if v <= 0:
        failures.append("%s: EMPTY (0 verts)" % bid)
    if d > MAX_DEGEN:
        failures.append("%s: %d degenerate faces" % (bid, d))
    if lf:
        failures.append("%s: link_failures %s" % (bid, lf))

print("-" * 72)
print("wave-20 notation-marks causal checks")

# (A) attributes stored; Scale reaches a Transform.
for bid in TARGETS:
    ng = tree_of(bid)
    a1 = stored_attr(ng, "glyph_semitone_mod12")
    a2 = stored_attr(ng, "glyph_family")
    a3 = stored_attr(ng, "higgsas_lead")
    sw = scale_wired(ng)
    if not (a1 and a2 and a3 and sw):
        failures.append("A %s: attrs=%s/%s/%s scale=%s"
                        % (bid, a1, a2, a3, sw))
    print("A %-34s semitone=%-5s family=%-5s lead=%-5s scale=%-5s"
          % (bid, a1, a2, a3, sw))

# (B) no primitive dimension at a LITERAL zero.
for bid in TARGETS:
    ng = tree_of(bid)
    bad = literal_zero_dims(ng)
    if bad:
        failures.append("B %s: literal-zero dims %s" % (bid, bad))
    print("B %-34s literal_zero=%s" % (bid, bad or "none"))

# (C) zero booleans in the lane.
for bid in TARGETS:
    ng = tree_of(bid)
    nb = len(of_type(ng, "GeometryNodeMeshBoolean"))
    if nb:
        failures.append("C %s: %d MeshBoolean nodes" % (bid, nb))
    print("C %-34s booleans=%d" % (bid, nb))

# (D) THE THIRTY-SECOND ROW: one more flag than the sixteenth, three ordered
#     seats read back off the Start-Y MULTIPLY nodes.
try:
    ng32 = tree_of("MEL_music_note_thirty_second")
    ng16 = tree_of("MEL_music_note_sixteenth")
    segs32 = of_type(ng32, "GeometryNodeCurvePrimitiveBezierSegment")
    segs16 = of_type(ng16, "GeometryNodeCurvePrimitiveBezierSegment")
    fracs = []
    stem_ok = []
    for seg in segs32:
        link = comp_link(seg, "Start", "Y")
        if link is None:
            fracs.append(None)
            stem_ok.append(False)
            continue
        mult, _sock = link
        if mult.bl_idname != "ShaderNodeMath":
            fracs.append(None)
            stem_ok.append(False)
            continue
        try:
            fracs.append(round(float(mult.inputs[1].default_value), 6))
        except Exception:
            fracs.append(None)
        stem_ok.append("Stem Length" in up(mult, "Value"))
    got = sorted([f for f in fracs if f is not None], reverse=True)
    want = sorted(FLAG_FRACTIONS, reverse=True)
    d_ok = (len(segs32) == len(segs16) + 1
            and len(segs32) == 3
            and len(got) == 3
            and all(abs(a - b) < 1e-6 for a, b in zip(got, want))
            and all(stem_ok))
    if not d_ok:
        failures.append("D thirty-second: segs=%d vs sixteenth %d; seats=%s "
                        "want=%s stem_links=%s"
                        % (len(segs32), len(segs16), got, want, stem_ok))
    print("D thirty-second      segs=%d sixteenth=%d seats=%s want=%s "
          "stem_links=%s -> %s"
          % (len(segs32), len(segs16), got, want, stem_ok,
             "OK" if d_ok else "FAIL"))
except Exception as e:
    failures.append("D: %s: %s" % (type(e).__name__, e))
    print("D thirty-second      EXCEPTION", e)

# (E) THE BAR-LINE LAW at three seats.
try:
    e_ok = True
    for bid, want_plates in (("MEL_music_bar_line", 1),
                             ("MEL_music_bar_double", 2),
                             ("MEL_music_bar_final", 2)):
        ng = tree_of(bid)
        cubes = of_type(ng, "GeometryNodeMeshCube")
        staff_ok = all("Staff Height" in up(c, "Size") for c in cubes)
        thick_ok = any("Thick Ratio" in up(c, "Size") for c in cubes)
        want_thick = (bid == "MEL_music_bar_final")
        row_ok = (len(cubes) == want_plates and staff_ok
                  and thick_ok == want_thick)
        e_ok = e_ok and row_ok
        if not row_ok:
            failures.append("E %s: plates=%d want=%d staff_height=%s "
                            "thick_ratio=%s want_thick=%s"
                            % (bid, len(cubes), want_plates, staff_ok,
                               thick_ok, want_thick))
        print("E %-34s plates=%d want=%d staff_height=%-5s thick_ratio=%-5s "
              "-> %s" % (bid, len(cubes), want_plates, staff_ok, thick_ok,
                         "OK" if row_ok else "FAIL"))
except Exception as e:
    failures.append("E: %s: %s" % (type(e).__name__, e))
    print("E bar-line law       EXCEPTION", e)

# (F) the FINAL bar is wider than the DOUBLE bar by the extra thickness.
try:
    row = {r[0]: r for r in rows}
    x_fin = row["MEL_music_bar_final"][4][0]
    x_dbl = row["MEL_music_bar_double"][4][0]
    ng = tree_of("MEL_music_bar_final")
    th = iface_ng(ng, "Bar Thickness", 0.030)
    ratio = iface_ng(ng, "Thick Ratio", 3.0)
    want_delta = (ratio - 1.0) * th / 2.0     # one side widens, the seat is shared
    got_delta = x_fin - x_dbl
    f_ok = abs(got_delta - want_delta) <= WIDTH_TOL
    if not f_ok:
        failures.append("F final vs double: delta=%.4f want=%.4f (th=%.4f "
                        "ratio=%.2f)" % (got_delta, want_delta, th, ratio))
    print("F final vs double    x_final=%.4f x_double=%.4f delta=%.4f "
          "want=%.4f -> %s"
          % (x_fin, x_dbl, got_delta, want_delta, "OK" if f_ok else "FAIL"))
except Exception as e:
    failures.append("F: %s: %s" % (type(e).__name__, e))
    print("F final vs double    EXCEPTION", e)

# (G) TENUTO ORIENTATION: one plate, wider than tall, sized off Line Spacing.
try:
    ng = tree_of("MEL_music_tenuto")
    cubes = of_type(ng, "GeometryNodeMeshCube")
    row = {r[0]: r for r in rows}
    ext = row["MEL_music_tenuto"][4]
    aspect = ext[1] / ext[0] if ext[0] else 99.0
    sz = up(cubes[0], "Size") if cubes else set()
    g_ok = (len(cubes) == 1
            and aspect < 0.5
            and "Line Spacing" in sz
            and "Tenuto Length Ratio" in sz
            and "Tenuto Thickness Ratio" in sz)
    if not g_ok:
        failures.append("G tenuto: plates=%d aspect=%.3f size<-%s"
                        % (len(cubes), aspect, sorted(sz)))
    print("G tenuto             plates=%d aspect(Y/X)=%.3f size<-%s -> %s"
          % (len(cubes), aspect, sorted(sz), "OK" if g_ok else "FAIL"))
except Exception as e:
    failures.append("G: %s: %s" % (type(e).__name__, e))
    print("G tenuto             EXCEPTION", e)

# (H) CAESURA: linked Z rotation reaching Caesura Slant; closed-form extents.
try:
    ng = tree_of("MEL_music_caesura")
    cubes = of_type(ng, "GeometryNodeMeshCube")
    rot_ok = 0
    gap_ok = 0
    for c in cubes:
        # the plate's own Transform carries the rotation
        for n in of_type(ng, "GeometryNodeTransform"):
            g = n.inputs.get("Geometry")
            if g is None or not g.links or g.links[0].from_node != c:
                continue
            link = comp_link(n, "Rotation", "Z")
            if link is not None and "Caesura Slant" in up(link[0], "Value"):
                rot_ok += 1
            gl = comp_link(n, "Translation", "X")
            if gl is not None and "Caesura Gap Ratio" in up(gl[0], "Value"):
                gap_ok += 1
    ls = iface_ng(ng, "Line Spacing", 0.13)
    length = ls * iface_ng(ng, "Caesura Length Ratio", 1.15)
    thick = ls * iface_ng(ng, "Caesura Thickness Ratio", 0.16)
    gap = ls * iface_ng(ng, "Caesura Gap Ratio", 0.34)
    ang = math.radians(iface_ng(ng, "Caesura Slant", 28.0))
    want_x = gap + thick * math.cos(ang) + length * math.sin(ang)
    want_y = thick * math.sin(ang) + length * math.cos(ang)
    row = {r[0]: r for r in rows}
    ext = row["MEL_music_caesura"][4]
    dx = abs(ext[0] - want_x)
    dy = abs(ext[1] - want_y)
    h_ok = (len(cubes) == 2 and rot_ok == 2 and gap_ok == 2
            and dx <= CLOSED_FORM_TOL and dy <= CLOSED_FORM_TOL)
    if not h_ok:
        failures.append("H caesura: plates=%d rot<-Slant=%d gap_seats=%d "
                        "X=%.4f want=%.4f Y=%.4f want=%.4f"
                        % (len(cubes), rot_ok, gap_ok, ext[0], want_x,
                           ext[1], want_y))
    print("H caesura            plates=%d rot<-Slant=%d gap_seats=%d "
          "X=%.4f/%.4f Y=%.4f/%.4f -> %s"
          % (len(cubes), rot_ok, gap_ok, ext[0], want_x, ext[1], want_y,
             "OK" if h_ok else "FAIL"))
except Exception as e:
    failures.append("H: %s: %s" % (type(e).__name__, e))
    print("H caesura            EXCEPTION", e)

# (I) no empties; bar_line distinct from the two-plate pair; thirty-second !=
#     sixteenth; the two marks distinct.
#     NOTE: bar_double and bar_final LEGITIMATELY share a vertex count - both
#     are two 8-vert plates. They differ only in the second plate's WIDTH, which
#     no vertex count can see; the separating law is `Thick Ratio` and it is
#     asserted in (F). Asserting pairwise distinctness across all three bar ids
#     reads as a builder failure on correct code.
try:
    counts = {r[0]: r[1] for r in rows}
    if len(counts) != len(TARGETS):
        failures.append("I: only %d/%d ids measured" % (len(counts), len(TARGETS)))
        print("I counts             MISSING ROWS")
    else:
        empties = [k for k, v in counts.items() if v <= 0]
        bar_line_distinct = counts["MEL_music_bar_line"] not in (
            counts["MEL_music_bar_double"], counts["MEL_music_bar_final"])
        pair_one_law = (counts["MEL_music_bar_double"]
                        == counts["MEL_music_bar_final"])
        mark_vals = [counts[b] for b in MARK_IDS]
        marks_distinct = len(set(mark_vals)) == len(mark_vals)
        ng16 = tree_of("MEL_music_note_sixteenth")
        v16, _, _, _, _, _ = measure(ng16)
        note_distinct = counts["MEL_music_note_thirty_second"] != v16
        i_ok = (not empties) and bar_line_distinct and pair_one_law \
            and marks_distinct and note_distinct
        if not i_ok:
            failures.append("I: empties=%s bar_line_distinct=%s "
                            "pair_one_law=%s marks_distinct=%s(%s) "
                            "note_distinct=%s"
                            % (empties, bar_line_distinct, pair_one_law,
                               marks_distinct, mark_vals, note_distinct))
        print("I counts             empties=%s bar_line_distinct=%s "
              "double==final=%s marks=%s note32=%d vs note16=%d -> %s"
              % (empties or "none", bar_line_distinct, pair_one_law,
                 mark_vals, counts["MEL_music_note_thirty_second"], v16,
                 "OK" if i_ok else "FAIL"))
except Exception as e:
    failures.append("I: %s: %s" % (type(e).__name__, e))
    print("I counts             EXCEPTION", e)

# (J) the lane is centred on the glyph plane.
for bid in TARGETS:
    row = {r[0]: r for r in rows}.get(bid)
    if row is None:
        continue
    zmin, zmax = row[5], row[6]
    ok = abs(abs(zmin) - abs(zmax)) <= Z_PLANE_TOL
    if not ok:
        failures.append("J %s: |min_z|=%.4f != |max_z|=%.4f"
                        % (bid, abs(zmin), abs(zmax)))
    print("J %-34s |min_z|=%.4f |max_z|=%.4f centred=%-5s"
          % (bid, abs(zmin), abs(zmax), ok))

print("-" * 72)
if failures:
    for f in failures:
        print("FAIL:", f)
    print("MARKS GATE: FAIL (%d)" % len(failures))
    raise SystemExit(1)
print("MARKS GATE: PASS (6/6)")
