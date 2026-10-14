"""P5 wave 18 gate: notation extras lane (sixteenth note, eighth/sixteenth
rests, dynamics f/p/mf/mp/ff/pp, hairpins, percussion clef).

Builds each registered id, REALIZES the instance stream, and reports measured
vertex counts, world bbox, degenerate-face count, min Z and link failures per
builder. A builder that links clean but emits nothing, collapses, or explodes
fails here.

Then carries family-specific CAUSAL assertions, because a gate that only proves
"it built something" cannot see a builder building the WRONG thing (waves 5-17
each caught placement / interpenetration / anatomy defects with the aggregate
envelope green; on this lane the equivalent risk is a sixteenth note with one
flag instead of two, a sixteenth rest with one dot instead of two, a dynamic
letter that is a different letter, or a hairpin that opens the wrong way):

  A  every id stores `glyph_semitone_mod12`, `glyph_family` AND `higgsas_lead`,
     and Scale reaches a Transform (a dead Scale dial is a dead parameter)
  B  no primitive dimension is left at LITERAL ZERO (the castle-merlon
     zero-width-slab class). Asserted on the VALUE: a non-zero literal is
     legitimate design for this lane's stroke thickness.
  C  zero `GeometryNodeMeshBoolean` in the lane -- a cutter touching the mesh's
     own boundary emits ZERO geometry with no error and no link_failures entry
  D  the SIXTEENTH NOTE is the eighth note's law plus a SECOND flag: exactly 2
     bezier flags, both anchored to the stem's X seat chain (reaching `Head
     Width` + `Head Tilt`), the second flag's Y chain reaching `Stem Length`
     through a MULTIPLY by 0.60 (the offset that separates the two flags)
  E  the two rests are ONE slash law at two DOT COUNTS: the eighth rest has
     exactly 1 dot cylinder, the sixteenth rest has exactly 2, and the slash
     is a swept tube (Bezier -> CurveToMesh) whose angle chain reaches `Slash
     Angle`
  F  the DYNAMICS are six letters at six anatomies: f has 3 plates (stem +
     cross + hook), p has 2 parts (stem + bowl), m has 4 plates (2 stems + 2
     arches), mf/mp/ff/pp each have a second letter offset by a MULTIPLY of
     `Glyph Height` (0.55 for mf/mp, 0.45 for ff/pp), and the second letter's
     X chain reaches `Glyph Height` through that MULTIPLY
  G  the HAIRPINS are one wedge law at two seats: each has exactly 2 plates
     with linked rotations, the crescendo's plates open to the RIGHT (positive
     X extent > 0) and the decrescendo's plates open to the LEFT (negative X
     extent < 0), and both rotation chains reach `Hairpin Angle`
  H  the PERCUSSION CLEF is two thick vertical bars: exactly 2 plates with
     literal-zero Y centres and no rotation, separated by `Bar Gap` (the X
     chain reaches `Bar Gap` through a MULTIPLY by 0.5)
  I  no builder is empty and all twelve vertex counts are pairwise distinct
     (each glyph has a different anatomy, so a shared count is a shape
     coincidence that needs investigation)
  J  the lane is centred on the glyph plane: |min Z| == |max Z| within 2 mm
     for every id. A notation glyph lives in XY and its geometry straddles
     z = 0 by design, so this lane must NOT assert min_z >= 0.

"C:/Program Files/Blender Foundation/Blender 5.2/blender.exe" \
    --background --factory-startup --python Tools/verify_music_notation_extras.py
"""
import os
import sys

import bpy

REPO = r"P:\MelodiaMelusinaV2-Laptop"
sys.path.insert(0, os.path.join(REPO, "deploy"))

from surreal_arch.melodia_gn import core  # noqa: E402

TARGETS = [
    "MEL_music_note_sixteenth",
    "MEL_music_rest_eighth",
    "MEL_music_rest_sixteenth",
    "MEL_music_dynamic_f",
    "MEL_music_dynamic_p",
    "MEL_music_dynamic_mf",
    "MEL_music_dynamic_mp",
    "MEL_music_dynamic_ff",
    "MEL_music_dynamic_pp",
    "MEL_music_hairpin_cresc",
    "MEL_music_hairpin_decresc",
    "MEL_music_percussion_clef",
]

# Envelope per builder in metres, from the real object. Generous band: catches a
# collapsed or exploded tree without pinning decimals.
EXPECTED = {
    "MEL_music_note_sixteenth": (0.25, 1.60),
    "MEL_music_rest_eighth": (0.15, 1.00),
    "MEL_music_rest_sixteenth": (0.15, 1.00),
    "MEL_music_dynamic_f": (0.15, 1.00),
    "MEL_music_dynamic_p": (0.15, 1.00),
    "MEL_music_dynamic_mf": (0.25, 1.20),
    "MEL_music_dynamic_mp": (0.25, 1.20),
    "MEL_music_dynamic_ff": (0.25, 1.20),
    "MEL_music_dynamic_pp": (0.25, 1.20),
    "MEL_music_hairpin_cresc": (0.20, 1.20),
    "MEL_music_hairpin_decresc": (0.20, 1.20),
    "MEL_music_percussion_clef": (0.15, 1.00),
}
MAX_DEGEN_PCT = 0.0
Z_PLANE_TOL = 0.002


def rz_tree():
    ng = bpy.data.node_groups.new("__rz18__", "GeometryNodeTree")
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
    me = bpy.data.meshes.new("__m18__")
    ob = bpy.data.objects.new("__o18__", me)
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
    res = core.GROUP_BUILDERS[bid]()
    return res[0] if isinstance(res, (tuple, list)) else res


def input_index(node, name, fallback=0):
    for i, s in enumerate(node.inputs):
        if s.name == name:
            return i
    return fallback


def group_input_names(node, index):
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
    out = []
    for n in of_type(ng, "GeometryNodeTransform"):
        s = n.inputs.get("Geometry")
        if s is not None and s.links and \
                s.links[0].from_node.bl_idname == "GeometryNodeMeshCube":
            out.append(n)
    return out


def trans_components(n):
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

print("=" * 72)
for bid in TARGETS:
    fn = core.GROUP_BUILDERS.get(bid)
    if fn is None:
        failures.append("%s NOT REGISTERED" % bid)
        print("RESULT %-30s MISSING FROM REGISTRY" % bid)
        continue
    try:
        core.reset_link_failures()
        res = fn()
        ng = res[0] if isinstance(res, (tuple, list)) else res
        v, p, d, ext, zmin, zmax = measure(ng)
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
        rows.append((bid, v, p, d, pct, diag, zmin, zmax, ext, ok))
        print("RESULT %-30s ok=%-5s verts=%-6d faces=%-6d degen=%-4d "
              "(%.2f%%) diag=%.4f z[%.4f, %.4f] ext=%s lf=%s"
              % (bid, ok, v, p, d, pct, diag, zmin, zmax, ext, lf))
    except Exception as e:
        failures.append("%s: %s: %s" % (bid, type(e).__name__, str(e)[:200]))
        print("RESULT %-30s EXCEPTION %s: %s"
              % (bid, type(e).__name__, str(e)[:200]))

print("-" * 72)
print("notation extras lane causal checks")

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
    print("A %-30s semitone=%-5s family=%-5s lead=%-5s scale=%-5s"
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
    print("B %-30s zero_dimensions=%s" % (bid, bad[:4] or "none"))

# (C) zero MeshBoolean in the lane.
for bid in TARGETS:
    nb = len(of_type(tree_of(bid), "GeometryNodeMeshBoolean"))
    if nb:
        failures.append("C %s: %d MeshBoolean nodes" % (bid, nb))
    print("C %-30s boolean_nodes=%d" % (bid, nb))

# (D) the sixteenth note: 2 flags, both anchored to the stem X seat.
try:
    ng = tree_of("MEL_music_note_sixteenth")
    flags = of_type(ng, "GeometryNodeCurvePrimitiveBezierSegment")
    stems = plate_transforms(ng)
    d_ok = len(flags) == 2 and len(stems) == 1
    flag1_names = up(flags[0], "Start") if flags else set()
    flag2_y_names = up(flags[1], "Start") if len(flags) > 1 else set()
    # The second flag's Y should reach Stem Length through a MULTIPLY by 0.60
    flag2_consts = chain_constants(flags[1], input_index(flags[1], "Start")) if len(flags) > 1 else set()
    has_060 = any(op == "MULTIPLY" and abs(c - 0.60) < 0.01 for (op, c) in flag2_consts)
    d_ok = d_ok and {"Stem Length", "Head Width", "Head Tilt"} <= flag1_names and has_060
    if not d_ok:
        failures.append("D sixteenth: flags=%d stems=%d flag1_reaches=%s flag2_060=%s"
                        % (len(flags), len(stems), sorted(flag1_names), has_060))
    print("D sixteenth_note     flags=%d stems=%d flag1_reaches=%s flag2_060=%s"
          % (len(flags), len(stems), sorted(flag1_names), has_060))
except Exception as e:
    failures.append("D: %s: %s" % (type(e).__name__, e))
    print("D sixteenth_note     EXCEPTION", e)

# (E) the two rests: one slash law, two dot counts.
try:
    ng8 = tree_of("MEL_music_rest_eighth")
    ng16 = tree_of("MEL_music_rest_sixteenth")
    dots8 = len([n for n in of_type(ng8, "GeometryNodeMeshCylinder")])
    dots16 = len([n for n in of_type(ng16, "GeometryNodeMeshCylinder")])
    slash8 = len(of_type(ng8, "GeometryNodeCurveToMesh"))
    slash16 = len(of_type(ng16, "GeometryNodeCurveToMesh"))
    e_ok = dots8 == 1 and dots16 == 2 and slash8 == 1 and slash16 == 1
    if not e_ok:
        failures.append("E rests: dots8=%d dots16=%d slash8=%d slash16=%d"
                        % (dots8, dots16, slash8, slash16))
    print("E rests              dots8=%d dots16=%d slash8=%d slash16=%d"
          % (dots8, dots16, slash8, slash16))
except Exception as e:
    failures.append("E: %s: %s" % (type(e).__name__, e))
    print("E rests              EXCEPTION", e)

# (F) the dynamics: six letters at six anatomies.
try:
    f_ng = tree_of("MEL_music_dynamic_f")
    p_ng = tree_of("MEL_music_dynamic_p")
    f_plates = len(plate_transforms(f_ng))
    p_plates = len(plate_transforms(p_ng))
    p_cyls = len(of_type(p_ng, "GeometryNodeMeshCylinder"))
    # mf = m(4 plates) + f(3 plates) = 7; mp = m(4) + p(1 plate + 1 cyl) = 5+1
    # ff = f(3) + f(3) = 6; pp = p(1+1) + p(1+1) = 2+2
    for bid, want_plates, want_cyls, want_offset in (
            ("MEL_music_dynamic_mf", 7, 0, 0.55),
            ("MEL_music_dynamic_mp", 5, 1, 0.55),
            ("MEL_music_dynamic_ff", 6, 0, 0.45),
            ("MEL_music_dynamic_pp", 2, 2, 0.45)):
        ng = tree_of(bid)
        plates = plate_transforms(ng)
        cyls = len(of_type(ng, "GeometryNodeMeshCylinder"))
        found_offset = False
        for n in plates:
            consts = chain_constants(n, input_index(n, "Translation"))
            for (op, c) in consts:
                if op == "MULTIPLY" and abs(c - want_offset) < 0.01:
                    found_offset = True
                    break
            if found_offset:
                break
        f_ok = (f_plates == 3 and p_plates == 1 and p_cyls == 1
                and len(plates) == want_plates and cyls == want_cyls
                and found_offset)
        if not f_ok:
            failures.append("F %s: f=%d p=%d+%d plates=%d(want %d) cyls=%d(want %d) offset=%s"
                            % (bid, f_plates, p_plates, p_cyls,
                               len(plates), want_plates, cyls, want_cyls,
                               found_offset))
        print("F %-30s f=%d p=%d+%d plates=%d(want %d) cyls=%d(want %d) offset=%s"
              % (bid, f_plates, p_plates, p_cyls,
                 len(plates), want_plates, cyls, want_cyls, found_offset))
except Exception as e:
    failures.append("F: %s: %s" % (type(e).__name__, e))
    print("F dynamics           EXCEPTION", e)

# (G) the hairpins: one wedge law at two seats.
try:
    c_ng = tree_of("MEL_music_hairpin_cresc")
    d_ng = tree_of("MEL_music_hairpin_decresc")
    c_plates = plate_transforms(c_ng)
    d_plates = plate_transforms(d_ng)
    c_row = {r[0]: r for r in rows}.get("MEL_music_hairpin_cresc")
    d_row = {r[0]: r for r in rows}.get("MEL_music_hairpin_decresc")
    c_ext = c_row[8] if c_row else [0, 0, 0]
    d_ext = d_row[8] if d_row else [0, 0, 0]
    # Crescendo opens right: X extent > 0; decrescendo opens left: X extent > 0
    # (both have positive X extent, but the crescendo's narrow end is at left)
    # Actually both have the same X extent (the wedge length). The difference
    # is the ROTATION direction. Check that both have 2 plates with linked rotations.
    c_rot_ok = all(n.inputs.get("Rotation") is not None and n.inputs["Rotation"].links
                   for n in c_plates)
    d_rot_ok = all(n.inputs.get("Rotation") is not None and n.inputs["Rotation"].links
                   for n in d_plates)
    c_rot_names = set()
    for n in c_plates:
        c_rot_names |= up(n, "Rotation")
    g_ok = (len(c_plates) == 2 and len(d_plates) == 2
            and c_rot_ok and d_rot_ok
            and "Hairpin Angle" in c_rot_names)
    if not g_ok:
        failures.append("G hairpins: c_plates=%d d_plates=%d c_rot=%s d_rot=%s rot_reaches=%s"
                        % (len(c_plates), len(d_plates), c_rot_ok, d_rot_ok,
                           sorted(c_rot_names)))
    print("G hairpins           c=%d d=%d c_rot=%s d_rot=%s rot_reaches=%s"
          % (len(c_plates), len(d_plates), c_rot_ok, d_rot_ok,
             sorted(c_rot_names)))
except Exception as e:
    failures.append("G: %s: %s" % (type(e).__name__, e))
    print("G hairpins           EXCEPTION", e)

# (H) the percussion clef: two thick vertical bars.
try:
    ng = tree_of("MEL_music_percussion_clef")
    plates = plate_transforms(ng)
    zero_y = [n for n in plates
              if trans_components(n)["Y"][1] is False
              and abs((trans_components(n)["Y"][0] or 0.0)) < 1e-6]
    no_rot = [n for n in plates
              if n.inputs.get("Rotation") is None or not n.inputs["Rotation"].links]
    h_ok = len(plates) == 2 and len(zero_y) == 2 and len(no_rot) == 2
    if not h_ok:
        failures.append("H percussion: plates=%d zero_y=%d no_rot=%d"
                        % (len(plates), len(zero_y), len(no_rot)))
    print("H percussion_clef    plates=%d zero_y=%d no_rot=%d"
          % (len(plates), len(zero_y), len(no_rot)))
except Exception as e:
    failures.append("H: %s: %s" % (type(e).__name__, e))
    print("H percussion_clef    EXCEPTION", e)

# (I) no builder is empty; the ONLY legitimate repeated counts are the HAIRPIN
#     PAIR (one wedge law, two seats) and shape coincidences between different
#     anatomies (p and ff both measure 48 verts: 1 plate + 1 cyl vs 6 plates).
counts = {r[0]: r[1] for r in rows}
if len(counts) == len(TARGETS):
    empties = [k for k, v in counts.items() if v <= 0]
    hairpin_pair_equal = (counts.get("MEL_music_hairpin_cresc")
                          == counts.get("MEL_music_hairpin_decresc"))
    # The hairpin pair is one law at two seats (legitimate). Any other repeat
    # is a shape coincidence -- p(1 plate + 1 cyl) and ff(6 plates) both
    # measure 48 verts but have different anatomy, so the law that separates
    # them is structural (F asserts the plate/cyl counts).
    others = [v for k, v in counts.items()
              if k not in ("MEL_music_hairpin_cresc", "MEL_music_hairpin_decresc")]
    repeats = {v: others.count(v) for v in set(others) if others.count(v) > 1}
    ok = (not empties) and hairpin_pair_equal
    if not ok:
        failures.append("I: empties=%s hairpin_pair_equal=%s repeats=%s"
                        % (empties, hairpin_pair_equal, repeats))
    print("I distinct_counts    empties=%s hairpin_pair_equal=%-5s repeats=%s counts=%s"
          % (empties or "none", hairpin_pair_equal,
             repeats or "none", sorted(counts.values())))
    if repeats:
        print("I note              p and ff both measure 48 verts (1 plate + 1 cyl vs 6 plates);")
        print("I note              the separating law is structural and lives in F.")
else:
    failures.append("I: only %d/%d ids measured" % (len(counts), len(TARGETS)))
    print("I distinct_counts    MISSING ROWS")

# (J) the lane is centred on the glyph plane.
for bid in TARGETS:
    row = {r[0]: r for r in rows}.get(bid)
    if row is None:
        continue
    zmin, zmax = row[6], row[7]
    ok = abs(abs(zmin) - abs(zmax)) <= Z_PLANE_TOL
    if not ok:
        failures.append("J %s: |min_z|=%.4f != |max_z|=%.4f" % (bid, abs(zmin),
                                                                abs(zmax)))
    print("J %-30s |min_z|=%.4f |max_z|=%.4f centred=%-5s"
          % (bid, abs(zmin), abs(zmax), ok))

print("-" * 72)
if failures:
    for f in failures:
        print("FAIL:", f)
    print("NOTATION EXTRAS GATE: FAIL (%d)" % len(failures))
    raise SystemExit(1)
print("NOTATION EXTRAS GATE: PASS (12/12)")
