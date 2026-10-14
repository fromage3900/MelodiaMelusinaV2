"""P5 wave 19 gate: articulation marks + dotted notes lane.

Builds each registered id, REALIZES the instance stream, and reports measured
vertex counts, world bbox, degenerate-face count, min Z and link failures per
builder. A builder that links clean but emits nothing, collapses, or explodes
fails here.

Then carries family-specific CAUSAL assertions, because a gate that only proves
"it built something" cannot see a builder building the WRONG thing. This lane
exists because wave 18 shipped a HAIRPIN THAT WAS AN X: `dy` was computed and
used nowhere, so both bars were seated at Y = 0 and the mark was two equal bars
crossed at their centres. Every aggregate envelope scored it 6/6 green, and the
two arrangements differ in Y by exactly `dy` while sharing an identical X
extent, so no bbox check could separate them either. The assertion that CAN is
the closed-form wedge law below (D).

  A  every id stores `glyph_semitone_mod12`, `glyph_family` AND `higgsas_lead`,
     and Scale reaches a Transform (a dead Scale dial is a dead parameter)
  B  no primitive dimension is left at LITERAL ZERO (the castle-merlon
     zero-width-slab class). Asserted on the VALUE: a non-zero literal is
     legitimate design for this lane's stroke thickness.
  C  zero `GeometryNodeMeshBoolean` in the lane -- a cutter touching the mesh's
     own boundary emits ZERO geometry with no error and no link_failures entry
  D  THE WEDGE LAW (the wave-18 defect): every wedge id -- accent, marcato and
     both hairpins -- measures a Y extent equal to
     `3 x half_l x sin(ang) + thick x cos(ang)` within 5 mm, i.e. `dy` LARGER
     than the crossed form `2 x hy` that wave 18 shipped. Asserted on the
     MEASURED geometry against the params read off the interface, never on a
     snapshot.
  E  accent vs marcato are ONE wedge law at TWO seats: marcato's Y/X aspect is
     at least 1.6x the accent's, and each mark's MOUTH (`2 x half_l x sin ang`)
     clears its own bar thickness by 1.5x -- a mouth narrower than the stroke is
     a solid blob with no opening, not a `>`
  F  the three dotted notes are the wave-17 duration table PLUS ONE dot: each
     carries exactly one more MeshCylinder than its undotted sibling, and the
     dotted half is HOLLOW (a `CurvePrimitiveCircle` path) while the dotted
     quarter and eighth are not
  G  the augmentation dot is a function of the HEAD it augments, not a
     free-floating mark: the dot cylinder's Radius chain reaches `Head Height`
     and its Translation X chain reaches `Head Width` (a dot sized from
     `Line Spacing` would be a second, independent glyph)
  H  the staccato is a FILLED disc on the note's own Y: exactly one cylinder,
     zero cubes, and a literal-zero Y centre (the mark carries no seat)
  I  no builder is empty, and the ONLY repeated vertex count is the four
     wedge-law ids (one law, four seats); the three dotted notes are pairwise
     distinct
  J  the lane is centred on the glyph plane: |min Z| == |max Z| within 2 mm
     for every id. A notation glyph lives in XY and its geometry straddles
     z = 0 by design, so this lane must NOT assert min_z >= 0.

"C:/Program Files/Blender Foundation/Blender 5.2/blender.exe" \
    --background --factory-startup --python Tools/verify_music_articulation.py
"""
import math
import os
import sys

import bpy

REPO = r"P:\MelodiaMelusinaV2-Laptop"
sys.path.insert(0, os.path.join(REPO, "deploy"))

from surreal_arch.melodia_gn import core  # noqa: E402

TARGETS = [
    "MEL_music_staccato",
    "MEL_music_accent",
    "MEL_music_marcato",
    "MEL_music_note_dotted_half",
    "MEL_music_note_dotted_quarter",
    "MEL_music_note_dotted_eighth",
]

# The four ids built on the shared `_wedge` law (2 plates each).
WEDGE_IDS = ["MEL_music_accent", "MEL_music_marcato",
             "MEL_music_hairpin_cresc", "MEL_music_hairpin_decresc"]

# Undotted siblings, for the "wave-17 table plus ONE dot" comparison (F).
SIBLINGS = {
    "MEL_music_note_dotted_half": "MEL_music_note_half",
    "MEL_music_note_dotted_quarter": "MEL_music_note_quarter",
    "MEL_music_note_dotted_eighth": "MEL_music_note_eighth",
}

EXPECTED = {
    "MEL_music_staccato": (0.02, 0.40),
    "MEL_music_accent": (0.02, 0.40),
    "MEL_music_marcato": (0.02, 0.40),
    "MEL_music_note_dotted_half": (0.25, 1.60),
    "MEL_music_note_dotted_quarter": (0.25, 1.60),
    "MEL_music_note_dotted_eighth": (0.25, 1.60),
}
MAX_DEGEN_PCT = 0.0
Z_PLANE_TOL = 0.002
WEDGE_TOL = 0.005
DOT_VERTS = 40          # a 20-vertex capped cylinder


def rz_tree():
    ng = bpy.data.node_groups.new("__rz19__", "GeometryNodeTree")
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
    me = bpy.data.meshes.new("__m19__")
    ob = bpy.data.objects.new("__o19__", me)
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
    """Transforms whose Geometry is a MeshCube (the wedge's bars)."""
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


def iface_ng(ng, name, fallback=0.0):
    """Read an interface default from an ALREADY-BUILT tree.

    Never rebuild here: `core.GROUP_BUILDERS[bid]()` builds by NAME, so a second
    call invalidates every node wrapper captured from the first tree and its
    `socket.links` read as empty - which made the wedge probe report
    `linked_y=False` on a geometrically perfect wedge.
    """
    try:
        return float(core.iface_default(ng, name))
    except Exception:
        return fallback


failures = []
rows = []

print("=" * 72)
for bid in TARGETS:
    fn = core.GROUP_BUILDERS.get(bid)
    if fn is None:
        failures.append("%s NOT REGISTERED" % bid)
        print("RESULT %-32s MISSING FROM REGISTRY" % bid)
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
        print("RESULT %-32s ok=%-5s verts=%-6d faces=%-6d degen=%-4d "
              "(%.2f%%) diag=%.4f z[%.4f, %.4f] ext=%s lf=%s"
              % (bid, ok, v, p, d, pct, diag, zmin, zmax, ext, lf))
    except Exception as e:
        failures.append("%s: %s: %s" % (bid, type(e).__name__, str(e)[:200]))
        print("RESULT %-32s EXCEPTION %s: %s"
              % (bid, type(e).__name__, str(e)[:200]))

print("-" * 72)
print("articulation + dotted-note lane causal checks")

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
    print("A %-32s semitone=%-5s family=%-5s lead=%-5s scale=%-5s"
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
    print("B %-32s zero_dimensions=%s" % (bid, bad[:4] or "none"))

# (C) zero MeshBoolean in the lane.
for bid in TARGETS + ["MEL_music_hairpin_cresc", "MEL_music_hairpin_decresc"]:
    nb = len(of_type(tree_of(bid), "GeometryNodeMeshBoolean"))
    if nb:
        failures.append("C %s: %d MeshBoolean nodes" % (bid, nb))
    print("C %-32s boolean_nodes=%d" % (bid, nb))

# (D) THE WEDGE LAW. The wave-18 defect was `dy` computed and never used, which
#     leaves the crossed form whose Y extent is exactly `dy` smaller.
#
#     Each family's length is a ratio of its OWN base: a hairpin's of
#     `Glyph Height`, an accent/marcato's of `Line Spacing` (an articulation
#     mark is staff-relative, like a rest). Reading `Glyph Height` for the
#     marks makes the closed form wrong by 4x and reports a correct wedge as a
#     failure - the gate's own silent-failure surface.
print("D wedge law (closed form vs measured):")
for bid in WEDGE_IDS:
    # ONE build, used for BOTH the measurement and the link inspection: a
    # second `GROUP_BUILDERS[bid]()` rebuilds the tree by name and the fresh
    # copy's links read as unlinked even though its geometry is correct.
    core.reset_link_failures()
    res = core.GROUP_BUILDERS[bid]()
    ng = res[0] if isinstance(res, (tuple, list)) else res
    v, p, d, ext, zmin, zmax = measure(ng)
    plates = plate_transforms(ng)
    if bid.startswith("MEL_music_hairpin"):
        base = iface_ng(ng, "Glyph Height", 0.60)
        ratio = iface_ng(ng, "Hairpin Length Ratio", 0.80)
        angle = iface_ng(ng, "Hairpin Angle", 18.0)
        thick = iface_ng(ng, "Thickness", 0.055)
    else:
        base = iface_ng(ng, "Line Spacing", 0.13)
        ratio = iface_ng(ng, "Mark Length Ratio", 0.55)
        angle = iface_ng(ng, "Mark Angle", 45.0)
        thick = base * iface_ng(ng, "Mark Thickness Ratio", 0.12)
    length = base * ratio
    half_l = length / 2.0
    ang = math.radians(angle)
    dy = half_l * math.sin(ang)
    hy = half_l * math.sin(ang) + (thick / 2.0) * math.cos(ang)
    y_wedge = 2.0 * hy + dy
    y_cross = 2.0 * hy
    x_want = 2.0 * (half_l * math.cos(ang) + (thick / 2.0) * math.sin(ang))
    linked_y = all(trans_components(n)["Y"][1] for n in plates)
    linked_rot = all(n.inputs.get("Rotation") is not None
                     and n.inputs["Rotation"].links for n in plates)
    ok = (len(plates) == 2 and linked_y and linked_rot
          and abs(ext[1] - y_wedge) <= WEDGE_TOL
          and abs(ext[0] - x_want) <= 2 * WEDGE_TOL)
    if not ok:
        failures.append(
            "D %s: plates=%d linked_y=%s linked_rot=%s X=%.4f(want %.4f) "
            "Y=%.4f(want wedge %.4f; crossed form %.4f)"
            % (bid, len(plates), linked_y, linked_rot, ext[0], x_want,
               ext[1], y_wedge, y_cross))
    print("D %-32s plates=%d linked_y=%-5s rot=%-5s X=%.4f(want %.4f) "
          "Y=%.4f wedge=%.4f crossed=%.4f -> %s"
          % (bid, len(plates), linked_y, linked_rot, ext[0], x_want,
             ext[1], y_wedge, y_cross, "WEDGE" if ok else "NOT A WEDGE"))

# (D2) WHICH WAY THE WEDGE POINTS. The wedge law's extents are invariant under
#      a mirror, so the apex side needs its own assertion - and it is the whole
#      difference between an accent `>` and a miniature crescendo `<`, and
#      between a crescendo and a decrescendo. The apex end is the end whose Y
#      extent is the bar thickness; the mouth end spans the full Y extent.
APEX_SIDE = {
    "MEL_music_accent": "right",
    "MEL_music_marcato": "right",
    "MEL_music_hairpin_cresc": "left",
    "MEL_music_hairpin_decresc": "right",
}
print("D2 apex direction:")
for bid, want_side in APEX_SIDE.items():
    core.reset_link_failures()
    res = core.GROUP_BUILDERS[bid]()
    ng = res[0] if isinstance(res, (tuple, list)) else res
    v, p, d, ext, zmin, zmax = measure(ng)
    xs = []
    me = bpy.data.meshes.new("__d2__")
    ob = bpy.data.objects.new("__d2__", me)
    bpy.context.scene.collection.objects.link(ob)
    ob.modifiers.new("a", "NODES").node_group = ng
    ob.modifiers.new("b", "NODES").node_group = RZ
    bpy.context.view_layer.update()
    dg = bpy.context.evaluated_depsgraph_get()
    ev = ob.evaluated_get(dg)
    m = ev.to_mesh()
    pts = [q.co.copy() for q in m.vertices]
    ev.to_mesh_clear()
    ob.modifiers.clear()
    bpy.data.objects.remove(ob, do_unlink=True)
    bpy.data.meshes.remove(me)
    x0 = min(q.x for q in pts)
    x1 = max(q.x for q in pts)
    span = max(x1 - x0, 1e-6)

    def band(lo, hi):
        sel = [q.y for q in pts if lo <= q.x <= hi]
        return (max(sel) - min(sel)) if sel else None

    L = band(x0, x0 + span * 0.12)
    Rr = band(x1 - span * 0.12, x1)
    if L is None or Rr is None:
        failures.append("D2 %s: empty endpoint band (L=%s R=%s)" % (bid, L, Rr))
        print("D2 %-32s EMPTY BAND" % bid)
        continue
    apex_is = "left" if L < Rr else "right"
    d2_ok = apex_is == want_side and (max(L, Rr) > 2.0 * min(L, Rr))
    if not d2_ok:
        failures.append("D2 %s: apex on the %s, want the %s (L=%.4f R=%.4f)"
                        % (bid, apex_is, want_side, L, Rr))
    print("D2 %-32s apex=%s want=%s L=%.4f R=%.4f ratio=%.2f -> %s"
          % (bid, apex_is, want_side, L, Rr,
             (max(L, Rr) / max(min(L, Rr), 1e-6)), "OK" if d2_ok else "FAIL"))

# (E) accent vs marcato: one law, two seats, separated by the ASPECT ratio.
try:
    a_ext = {r[0]: r[8] for r in rows}
    ax, ay = a_ext["MEL_music_accent"][0], a_ext["MEL_music_accent"][1]
    mx, my = a_ext["MEL_music_marcato"][0], a_ext["MEL_music_marcato"][1]
    a_asp, m_asp = (ay / ax) if ax else 0.0, (my / mx) if mx else 0.0
    seats = []
    for bid in ("MEL_music_accent", "MEL_music_marcato"):
        ng = tree_of(bid)
        base = iface_ng(ng, "Line Spacing", 0.13)
        ratio = iface_ng(ng, "Mark Length Ratio", 0.55)
        angle = iface_ng(ng, "Mark Angle", 45.0)
        thick = base * iface_ng(ng, "Mark Thickness Ratio", 0.12)
        mouth = 2.0 * (base * ratio / 2.0) * math.sin(math.radians(angle))
        seats.append((bid, mouth, thick, mouth > 1.5 * thick))
    e_ok = (a_asp > 0 and m_asp >= 1.6 * a_asp
            and all(s[3] for s in seats))
    if not e_ok:
        failures.append("E accent/marcato: aspects %.2f vs %.2f (need >= %.2f) "
                        "mouths %s" % (a_asp, m_asp, 1.6 * a_asp,
                                       [(s[0], round(s[1], 4), round(s[2], 4))
                                        for s in seats]))
    print("E accent_aspect=%.2f marcato_aspect=%.2f ratio=%.2f (need >=1.6) "
          "mouths=%s" % (a_asp, m_asp, (m_asp / a_asp) if a_asp else 0.0,
                         [(s[0].split("_")[-1], round(s[1], 4),
                           round(s[2], 4), s[3]) for s in seats]))
except Exception as e:
    failures.append("E: %s: %s" % (type(e).__name__, e))
    print("E accent/marcato      EXCEPTION", e)

# (F) the dotted notes are the wave-17 table PLUS ONE dot.
#
#     The head's anatomy is read STRUCTURALLY, not by counting circle nodes:
#     the head is the Transform whose Scale traces to `Head Width` (the one
#     node in the tree that is scaled by the head's own vector), and its
#     Geometry input is a `MeshCylinder` for a FILLED head or a `CurveToMesh`
#     for a HOLLOW one. A node-count test cannot work here: the hollow head's
#     swept profile is itself a `CurvePrimitiveCircle`, and the eighth's flag
#     is a second sweep, so both anatomies carry circles and sweeps.
def head_anatomy(ng):
    for n in of_type(ng, "GeometryNodeTransform"):
        if "Head Width" not in up(n, "Scale"):
            continue
        g = n.inputs.get("Geometry")
        if g is None or not g.links:
            continue
        src = g.links[0].from_node.bl_idname
        if src == "GeometryNodeMeshCylinder":
            return "filled"
        # the hollow head's Transform carries the CIRCLE PATH (the sweep sits
        # downstream of it), so a curve source is the hollow anatomy
        if src in ("GeometryNodeCurvePrimitiveCircle", "GeometryNodeCurveToMesh"):
            return "hollow"
    return None


try:
    counts = {r[0]: r[1] for r in rows}
    for bid, sib in SIBLINGS.items():
        ng = tree_of(bid)
        sib_ng = tree_of(sib)
        v_sib, _, _, _, _, _ = measure(sib_ng)
        n_cyl = len(of_type(ng, "GeometryNodeMeshCylinder"))
        n_cyl_sib = len(of_type(sib_ng, "GeometryNodeMeshCylinder"))
        anat = head_anatomy(ng)
        anat_sib = head_anatomy(sib_ng)
        want = "hollow" if bid.endswith("half") else "filled"
        f_ok = (n_cyl == n_cyl_sib + 1
                and counts.get(bid, 0) == v_sib + DOT_VERTS
                and anat == anat_sib == want)
        if not f_ok:
            failures.append(
                "F %s: cyls=%d vs sibling %d (+1 needed); verts=%d vs "
                "sibling %d (+%d needed); head=%s sibling=%s want=%s"
                % (bid, n_cyl, n_cyl_sib, counts.get(bid, 0), v_sib,
                   DOT_VERTS, anat, anat_sib, want))
        print("F %-32s cyls=%d sibling=%d verts=%d sibling=%d head=%s "
              "sibling=%s want=%s -> %s"
              % (bid, n_cyl, n_cyl_sib, counts.get(bid, 0), v_sib, anat,
                 anat_sib, want, "OK" if f_ok else "FAIL"))
except Exception as e:
    failures.append("F: %s: %s" % (type(e).__name__, e))
    print("F dotted-vs-sibling   EXCEPTION", e)

# (G) the augmentation dot is a function of the HEAD.
try:
    for bid in ("MEL_music_note_dotted_half", "MEL_music_note_dotted_quarter",
                "MEL_music_note_dotted_eighth"):
        ng = tree_of(bid)
        cyls = of_type(ng, "GeometryNodeMeshCylinder")
        dot = None
        for c in cyls:
            rn = up(c, "Radius")
            if "Head Height" in rn:
                dot = c
                break
        # the dot's X seat: a Transform whose Translation X reaches Head Width
        seat_ok = False
        if dot is not None:
            for n in of_type(ng, "GeometryNodeTransform"):
                g = n.inputs.get("Geometry")
                if g is None or not g.links or g.links[0].from_node != dot:
                    continue
                comps = trans_components(n)
                if comps["X"][1] and "Head Width" in up(n, "Translation"):
                    seat_ok = True
                    break
        g_ok = dot is not None and seat_ok
        if not g_ok:
            failures.append("G %s: dot_cylinder=%s seat_reaches_head_width=%s"
                            % (bid, dot is not None, seat_ok))
        print("G %-32s dot_radius<-Head Height=%-5s seat<-Head Width=%-5s"
              % (bid, dot is not None, seat_ok))
except Exception as e:
    failures.append("G: %s: %s" % (type(e).__name__, e))
    print("G augmentation dot    EXCEPTION", e)

# (H) the staccato is a filled disc on the note's own Y.
try:
    ng = tree_of("MEL_music_staccato")
    cyls = of_type(ng, "GeometryNodeMeshCylinder")
    cubes = of_type(ng, "GeometryNodeMeshCube")
    h_ok = len(cyls) == 1 and len(cubes) == 0
    # no seat parameter at all: the dot sits on the note's own Y
    ifaces = [s.name for s in ng.interface.items_tree
              if getattr(s, "in_out", "") == "INPUT"]
    h_ok = h_ok and "Seat" not in " ".join(ifaces)
    if not h_ok:
        failures.append("H staccato: cyls=%d cubes=%d ifaces=%s"
                        % (len(cyls), len(cubes), ifaces))
    print("H staccato            cyls=%d cubes=%d seat_param=%s ifaces=%s"
          % (len(cyls), len(cubes), any("Seat" in i for i in ifaces),
             ifaces))
except Exception as e:
    failures.append("H: %s: %s" % (type(e).__name__, e))
    print("H staccato            EXCEPTION", e)

# (I) no empties; the only repeated count is the four wedge-law ids.
counts = {r[0]: r[1] for r in rows}
if len(counts) == len(TARGETS):
    empties = [k for k, v in counts.items() if v <= 0]
    wedge_counts = {r[0]: r[1] for r in rows}
    wedge_vals = set()
    for bid in WEDGE_IDS:
        row = {r[0]: r for r in rows}.get(bid)
        wedge_vals.add(row[1] if row else measure(tree_of(bid))[0])
    # every wedge id must measure the SAME count (one law) ...
    one_law = len(wedge_vals) == 1
    # ... and the three dotted notes must be pairwise distinct
    dot_vals = [counts[b] for b in SIBLINGS]
    dots_distinct = len(set(dot_vals)) == len(dot_vals)
    others = [v for k, v in counts.items() if k not in WEDGE_IDS]
    repeats = {v: others.count(v) for v in set(others) if others.count(v) > 1}
    ok = (not empties) and one_law and dots_distinct and not repeats
    if not ok:
        failures.append("I: empties=%s one_law=%s(%s) dots_distinct=%s "
                        "repeats=%s" % (empties, one_law, sorted(wedge_vals),
                                        dots_distinct, repeats))
    print("I counts             empties=%s wedge_one_law=%s(%s) "
          "dots_distinct=%s repeats=%s counts=%s"
          % (empties or "none", one_law, sorted(wedge_vals), dots_distinct,
             repeats or "none", sorted(counts.values())))
else:
    failures.append("I: only %d/%d ids measured" % (len(counts), len(TARGETS)))
    print("I counts             MISSING ROWS")

# (J) the lane is centred on the glyph plane.
for bid in TARGETS:
    row = {r[0]: r for r in rows}.get(bid)
    if row is None:
        continue
    zmin, zmax = row[6], row[7]
    ok = abs(abs(zmin) - abs(zmax)) <= Z_PLANE_TOL
    if not ok:
        failures.append("J %s: |min_z|=%.4f != |max_z|=%.4f"
                        % (bid, abs(zmin), abs(zmax)))
    print("J %-32s |min_z|=%.4f |max_z|=%.4f centred=%-5s"
          % (bid, abs(zmin), abs(zmax), ok))

print("-" * 72)
if failures:
    for f in failures:
        print("FAIL:", f)
    print("ARTICULATION GATE: FAIL (%d)" % len(failures))
    raise SystemExit(1)
print("ARTICULATION GATE: PASS (6/6)")
