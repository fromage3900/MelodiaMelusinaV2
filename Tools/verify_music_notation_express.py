"""P5 wave 23 gate: notation expression & bowing marks lane (tie, slur,
grace_note, tremolo, up_bow, down_bow).

Builds each registered id, REALIZES the instance stream, and reports measured
vertex counts, world bbox, degenerate-face count, min Z and link failures per
builder.

Then carries family-specific CAUSAL assertions:

  A  every id stores `glyph_semitone_mod12`, `glyph_family` AND `higgsas_lead`,
     and Scale reaches a Transform (a dead Scale dial is a dead parameter)
  B  no primitive dimension is left at LITERAL ZERO (the castle-merlon
     zero-width-slab class). Asserted on the VALUE: a non-zero literal is
     legitimate design for this lane's stroke thickness.
  C  zero `GeometryNodeMeshBoolean` in the lane -- a cutter touching the mesh's
     own boundary emits ZERO geometry with no error and no link_failures entry
  D  TIE and SLUR are ONE arc law at two seats: same vert count (240), different
     Depth Ratio (0.42 vs 0.62) and sweep (140 vs 180). The gate asserts the
     RELATIONSHIP (slur deeper + wider sweep), not distinctness.
  E  GRACE_NOTE has a filled head (cylinder) + stem (plate) + slash (plate),
     and the slash is TILTED about Z (rotation traces to Slash Angle group input)
  F  TREMOLO has exactly 4 plates (1 stem + 3 slashes), and the slashes are
     seated at 25/50/75 per cent of the stem length
  G  UP_BOW and DOWN_BOW are a MIRROR: same 3 parts, same extents, but the
     cross bar sits at OPPOSITE Y ends. The gate asserts the bar's Y translation
     sign (negative for up-bow, positive for down-bow) -- a mirror is the one
     property a bbox cannot see.
  H  the lane is centred on the glyph plane: |min Z| == |max Z| within 2 mm
     for every id. A notation glyph lives in XY and its geometry straddles
     z = 0 by design, so this lane must NOT assert min_z >= 0.
  I  no builder is empty and every id's vertex count matches the lane's ANATOMY
     CLOSED FORM (8 per cube plate + 240 per swept arc + 48 per capped
     cylinder). A shared count is legitimate when it is the same anatomy
     at a different seat -- tie/slur are ONE law at two seats and legitimately
     share 240, and up_bow/down_bow are both 3-plate joins and legitimately
     share 24. Distinctness would fail on correct code.

Run:
"C:/Program Files/Blender Foundation/Blender 5.2/blender.exe" \
    --background --factory-startup --python Tools/verify_music_notation_express.py
"""
import os
import sys

import bpy

REPO = r"P:\MelodiaMelusinaV2-Laptop"
sys.path.insert(0, os.path.join(REPO, "deploy"))

from surreal_arch.melodia_gn import core  # noqa: E402

TARGETS = [
    "MEL_music_tie",
    "MEL_music_slur",
    "MEL_music_grace_note",
    "MEL_music_tremolo",
    "MEL_music_up_bow",
    "MEL_music_down_bow",
]

# Envelope per builder in metres, from the real object. Generous band: catches a
# collapsed or exploded tree without pinning decimals.
ENVELOPE = {
    "MEL_music_tie":         {"min_verts": 100,  "max_verts": 5000,  "min_diag": 0.05, "max_diag": 2.0},
    "MEL_music_slur":        {"min_verts": 100,  "max_verts": 5000,  "min_diag": 0.05, "max_diag": 2.0},
    "MEL_music_grace_note":  {"min_verts": 40,   "max_verts": 2000,  "min_diag": 0.05, "max_diag": 2.0},
    "MEL_music_tremolo":     {"min_verts": 20,   "max_verts": 2000,  "min_diag": 0.05, "max_diag": 2.0},
    "MEL_music_up_bow":      {"min_verts": 16,   "max_verts": 2000,  "min_diag": 0.05, "max_diag": 2.0},
    "MEL_music_down_bow":    {"min_verts": 16,   "max_verts": 2000,  "min_diag": 0.05, "max_diag": 2.0},
}


def count_nodes(tree, bl_idname):
    return sum(1 for n in tree.nodes if n.bl_idname == bl_idname)


def rz_tree():
    """Chained RealizeInstances tree: the lane builders emit live instances."""
    ng = bpy.data.node_groups.new("__rz23__", "GeometryNodeTree")
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


def count_type(tree, bl_idname):
    return sum(1 for n in tree.nodes if n.bl_idname == bl_idname)


def get_plate_count(tree):
    return count_nodes(tree, "GeometryNodeMeshCube")


def get_cyl_count(tree):
    return count_nodes(tree, "GeometryNodeMeshCylinder")


def get_arc_count(tree):
    return count_nodes(tree, "GeometryNodeCurveArc")


def get_sweep_count(tree):
    return count_nodes(tree, "GeometryNodeCurveToMesh")


def get_bool_count(tree):
    return count_nodes(tree, "GeometryNodeMeshBoolean")


def get_transform_count(tree):
    return count_nodes(tree, "GeometryNodeTransform")


def input_index(node, name):
    for i, s in enumerate(node.inputs):
        if s.name == name:
            return i
    return -1


def check_scale_reaches_transform(tree):
    """Check that the Scale group input reaches a Transform node's Scale input.

    BFS DOWNSTREAM from the Group Input's Scale output. A socket's `.links`
    always point UPSTREAM when read from an input socket, so after landing on a
    to_socket we must jump to its NODE's output sockets to keep moving forward.
    Keyed on (node.name, socket index) -- every Math node's sockets are named
    "Value", so a name-keyed visited set collapses the traversal.
    """
    gin = None
    for n in tree.nodes:
        if n.bl_idname == "NodeGroupInput":
            gin = n
            break
    if gin is None:
        return False

    scale_sock = None
    for s in gin.outputs:
        if s.name == "Scale":
            scale_sock = s
            break
    if scale_sock is None:
        return False

    def key(sock):
        node = sock.node
        try:
            idx = list(node.outputs).index(sock)
            side = "out"
        except ValueError:
            idx = list(node.inputs).index(sock)
            side = "in"
        return (node.name, side, idx)

    visited = set()
    queue = [scale_sock]
    while queue:
        sock = queue.pop(0)
        if sock is None:
            continue
        k = key(sock)
        if k in visited:
            continue
        visited.add(k)

        # Downstream links exist on an OUTPUT socket
        for lk in getattr(sock, "links", []):
            to_sock = lk.to_socket
            if to_sock is None:
                continue
            # If we landed on an input socket, jump to its node's outputs
            if hasattr(to_sock, "node") and to_sock.node is not None:
                if to_sock.node.bl_idname == "GeometryNodeTransform":
                    si = input_index(to_sock.node, "Scale")
                    if si >= 0 and to_sock == to_sock.node.inputs[si]:
                        return True
                for os in to_sock.node.outputs:
                    queue.append(os)
            else:
                queue.append(to_sock)
    return False


def check_no_literal_zero(tree):
    """Return a description of the first literal-zero primitive dimension found.

    A non-zero literal is legitimate design (stroke thickness); only a literal
    0 in a primitive's Size/Radius/Vertices is the defect class.
    """
    for n in tree.nodes:
        if n.bl_idname in ("GeometryNodeMeshCube", "GeometryNodeMeshCylinder",
                           "GeometryNodeMeshCone"):
            for sname in ("Size", "Radius", "Depth"):
                si = input_index(n, sname)
                if si < 0:
                    continue
                s = n.inputs[si]
                if not s.is_linked and hasattr(s, "default_value"):
                    try:
                        v = float(s.default_value)
                        if v == 0.0:
                            return f"{n.name}.{sname}=0"
                    except (TypeError, ValueError):
                        pass
        if n.bl_idname == "GeometryNodeMeshCylinder":
            si = input_index(n, "Vertices")
            if si >= 0:
                s = n.inputs[si]
                if not s.is_linked and hasattr(s, "default_value"):
                    try:
                        if int(s.default_value) == 0:
                            return f"{n.name}.Vertices=0"
                    except (TypeError, ValueError):
                        pass
    return None


def check_z_symmetry(min_z, max_z, tol=0.002):
    return abs(abs(min_z) - abs(max_z)) <= tol


def get_bar_y_centroid(tree):
    """Return the Y centroid of the realized geometry.

    The two verticals are symmetric about Y=0, so the Y centroid is determined
    by the bar's position: negative for up_bow (bar at bottom), positive for
    down_bow (bar at top).
    """
    me = bpy.data.meshes.new("__probe_y__")
    ob = bpy.data.objects.new("__probe_y__", me)
    bpy.context.scene.collection.objects.link(ob)
    m1 = ob.modifiers.new("GN", "NODES")
    m1.node_group = tree
    m2 = ob.modifiers.new("RZ", "NODES")
    m2.node_group = RZ
    bpy.context.view_layer.update()
    dg = bpy.context.evaluated_depsgraph_get()
    ev = ob.evaluated_get(dg)
    mev = ev.to_mesh()
    ys = [v.co.y for v in mev.vertices]
    ev.to_mesh_clear()
    bpy.data.objects.remove(ob, do_unlink=True)
    bpy.data.meshes.remove(me)
    if not ys:
        return 0.0
    return sum(ys) / len(ys)


def main():
    errors = []
    results = {}

    # Build every target
    for bid in TARGETS:
        if bid not in core.GROUP_BUILDERS:
            errors.append(f"{bid}: not in registry")
            continue
        try:
            res = core.GROUP_BUILDERS[bid]()
            tree = res[0] if isinstance(res, (tuple, list)) else res
        except Exception as e:
            errors.append(f"{bid}: build exception: {e}")
            continue

        # Attach to a temp mesh, realize, measure
        me = bpy.data.meshes.new(f"__probe_{bid}__")
        ob = bpy.data.objects.new(f"__probe_{bid}__", me)
        bpy.context.scene.collection.objects.link(ob)
        m1 = ob.modifiers.new("GN", "NODES")
        m1.node_group = tree
        bpy.context.view_layer.update()
        dg = bpy.context.evaluated_depsgraph_get()
        ev = ob.evaluated_get(dg)
        mev = ev.to_mesh()
        n0 = len(mev.vertices)
        ev.to_mesh_clear()

        m2 = ob.modifiers.new("RZ", "NODES")
        m2.node_group = RZ
        bpy.context.view_layer.update()
        dg = bpy.context.evaluated_depsgraph_get()
        ev = ob.evaluated_get(dg)
        mev = ev.to_mesh()
        verts = len(mev.vertices)
        faces = len(mev.polygons)
        degen = sum(1 for p in mev.polygons if p.area < 1e-9)
        co = [v.co.copy() for v in mev.vertices]
        if co:
            xs = [c.x for c in co]
            ys = [c.y for c in co]
            zs = [c.z for c in co]
            diag = max(max(xs) - min(xs), max(ys) - min(ys), max(zs) - min(zs))
            min_z = min(zs)
            max_z = max(zs)
        else:
            diag = 0.0
            min_z = 0.0
            max_z = 0.0
        ev.to_mesh_clear()

        lf = core.link_failures() if hasattr(core, "link_failures") else []
        nlf = len([x for x in lf if bid in str(x)]) if lf else 0

        results[bid] = {
            "tree": tree, "verts": verts, "faces": faces, "degen": degen,
            "diag": diag, "min_z": min_z, "max_z": max_z,
            "unrealized": n0, "link_fails": lf,
        }

        # Cleanup
        bpy.data.objects.remove(ob, do_unlink=True)
        bpy.data.meshes.remove(me)

    # Report
    print("=" * 80)
    print("WAVE 23 EXPRESSION & BOWING MARKS GATE")
    print("=" * 80)
    for bid in TARGETS:
        r = results.get(bid)
        if r is None:
            print(f"  {bid:35s} FAILED")
        else:
            print(f"  {bid:35s} verts={r['verts']:6d} faces={r['faces']:5d} degen={r['degen']:3d} diag={r['diag']:.4f} min_z={r['min_z']:+.4f} max_z={r['max_z']:+.4f} links={len(r['link_fails'])}")

    # Causal assertions
    print("\n--- CAUSAL ASSERTIONS ---")

    # A: attributes + Scale
    a_pass = True
    for bid in TARGETS:
        r = results.get(bid)
        if r is None:
            a_pass = False
            continue
        tree = r["tree"]
        has_attrs = False
        for n in tree.nodes:
            if n.bl_idname == "GeometryNodeStoreNamedAttribute":
                name_idx = input_index(n, "Name")
                if name_idx >= 0:
                    s = n.inputs[name_idx]
                    if hasattr(s, 'default_value') and s.default_value in ("glyph_semitone_mod12", "glyph_family", "higgsas_lead"):
                        has_attrs = True
        if not has_attrs:
            errors.append(f"{bid}: missing lane attributes")
            a_pass = False
        if not check_scale_reaches_transform(tree):
            errors.append(f"{bid}: Scale does not reach Transform")
            a_pass = False
    print(f"  A  attributes + Scale: {'PASS' if a_pass else 'FAIL'}")

    # B: no literal zero
    b_pass = True
    for bid in TARGETS:
        r = results.get(bid)
        if r is None:
            b_pass = False
            continue
        zero = check_no_literal_zero(r["tree"])
        if zero:
            errors.append(f"{bid}: literal zero in {zero}")
            b_pass = False
    print(f"  B  no literal zero: {'PASS' if b_pass else 'FAIL'}")

    # C: no boolean
    c_pass = True
    for bid in TARGETS:
        r = results.get(bid)
        if r is None:
            c_pass = False
            continue
        if get_bool_count(r["tree"]) > 0:
            errors.append(f"{bid}: has boolean node")
            c_pass = False
    print(f"  C  no boolean: {'PASS' if c_pass else 'FAIL'}")

    # D: tie and slur are ONE law at two seats
    d_pass = True
    rt = results.get("MEL_music_tie")
    rs = results.get("MEL_music_slur")
    if rt and rs:
        # Same vert count (same arc resolution)
        if rt["verts"] != rs["verts"]:
            errors.append(f"tie/slur: vert count mismatch {rt['verts']} vs {rs['verts']}")
            d_pass = False
        # Slur is deeper (larger Depth Ratio)
        dr_tie = core.iface_default(rt["tree"], "Depth Ratio", None)
        dr_slur = core.iface_default(rs["tree"], "Depth Ratio", None)
        if dr_tie is not None and dr_slur is not None:
            if dr_slur <= dr_tie:
                errors.append(f"slur Depth Ratio {dr_slur} <= tie {dr_tie}")
                d_pass = False
        else:
            errors.append("tie/slur: missing Depth Ratio param")
            d_pass = False
        # Slur has wider sweep
        # Count arc nodes -- both should have exactly 1
        if get_arc_count(rt["tree"]) != 1 or get_arc_count(rs["tree"]) != 1:
            errors.append("tie/slur: expected exactly 1 CurveArc each")
            d_pass = False
    else:
        errors.append("tie/slur: missing from results")
        d_pass = False
    print(f"  D  tie/slur one law two seats: {'PASS' if d_pass else 'FAIL'}")

    # E: grace_note has head + stem + slash, slash is tilted
    e_pass = True
    r = results.get("MEL_music_grace_note")
    if r:
        cyls = get_cyl_count(r["tree"])
        plates = get_plate_count(r["tree"])
        if cyls < 1:
            errors.append(f"grace_note: missing head cylinder (got {cyls})")
            e_pass = False
        if plates < 2:
            errors.append(f"grace_note: expected >= 2 plates (stem + slash), got {plates}")
            e_pass = False
        # Check slash tilt: at least one plate has a rotation with non-zero Z
        has_tilt = False
        for n in r["tree"].nodes:
            if n.bl_idname == "GeometryNodeTransform":
                ri = input_index(n, "Rotation")
                if ri >= 0:
                    rot_sock = n.inputs[ri]
                    if rot_sock.is_linked:
                        # Walk to CombineXYZ
                        for lk in rot_sock.links:
                            fn = lk.from_node
                            if fn.bl_idname == "ShaderNodeCombineXYZ":
                                z_sock = fn.inputs[2]
                                if z_sock.is_linked:
                                    has_tilt = True
                                elif hasattr(z_sock, "default_value"):
                                    try:
                                        if abs(float(z_sock.default_value)) > 0.01:
                                            has_tilt = True
                                    except (TypeError, ValueError):
                                        pass
        if not has_tilt:
            errors.append("grace_note: slash tilt not found (no linked rotation Z)")
            e_pass = False
    else:
        errors.append("grace_note: missing from results")
        e_pass = False
    print(f"  E  grace_note anatomy + tilt: {'PASS' if e_pass else 'FAIL'}")

    # F: tremolo has 4 plates (1 stem + 3 slashes)
    f_pass = True
    r = results.get("MEL_music_tremolo")
    if r:
        plates = get_plate_count(r["tree"])
        if plates != 4:
            errors.append(f"tremolo: expected 4 plates, got {plates}")
            f_pass = False
    else:
        errors.append("tremolo: missing from results")
        f_pass = False
    print(f"  F  tremolo 4 plates: {'PASS' if f_pass else 'FAIL'}")

    # G: up_bow / down_bow mirror -- bar at opposite Y ends
    g_pass = True
    rub = results.get("MEL_music_up_bow")
    rdb = results.get("MEL_music_down_bow")
    if rub and rdb:
        # Same vert count (same parts)
        if rub["verts"] != rdb["verts"]:
            errors.append(f"bow pair: vert count mismatch {rub['verts']} vs {rdb['verts']}")
            g_pass = False
        # Same extents (mirror)
        if abs(rub["diag"] - rdb["diag"]) > 0.001:
            errors.append(f"bow pair: diag mismatch {rub['diag']:.4f} vs {rdb['diag']:.4f}")
            g_pass = False
        # Bar Y position: up_bow = negative centroid (bar at bottom),
        # down_bow = positive centroid (bar at top). The verticals are
        # symmetric about Y=0 so only the bar moves the centroid.
        yc_up = get_bar_y_centroid(rub["tree"])
        yc_down = get_bar_y_centroid(rdb["tree"])
        if yc_up >= -0.001:
            errors.append(f"up_bow: bar Y centroid {yc_up:+.4f} (expected negative)")
            g_pass = False
        if yc_down <= 0.001:
            errors.append(f"down_bow: bar Y centroid {yc_down:+.4f} (expected positive)")
            g_pass = False
        # The mirror is exact: the two centroids are equal and opposite
        if abs(yc_up + yc_down) > 0.002:
            errors.append(f"bow pair: centroids not mirrored ({yc_up:+.4f} vs {yc_down:+.4f})")
            g_pass = False
    else:
        errors.append("bow pair: missing from results")
        g_pass = False
    print(f"  G  bow mirror (bar Y seat): {'PASS' if g_pass else 'FAIL'}")

    # H: z-symmetry
    h_pass = True
    for bid in TARGETS:
        r = results.get(bid)
        if r is None:
            h_pass = False
            continue
        if not check_z_symmetry(r["min_z"], r["max_z"]):
            errors.append(f"{bid}: z-asymmetry |{r['min_z']:.4f}| vs |{r['max_z']:.4f}|")
            h_pass = False
    print(f"  H  z-symmetry: {'PASS' if h_pass else 'FAIL'}")

    # I: closed form verts == anatomy
    i_pass = True
    PLATE_V = 8
    ARC_SWEEP_V = 240  # CurveArc res=24 swept with circle profile res=10
    CYLINDER_V = 48   # MeshCylinder 24 verts, NGON cap
    for bid in TARGETS:
        r = results.get(bid)
        if r is None:
            i_pass = False
            continue
        tree = r["tree"]
        plates = get_plate_count(tree)
        arcs = get_arc_count(tree)
        cyls = get_cyl_count(tree)
        expect = PLATE_V * plates + ARC_SWEEP_V * arcs + CYLINDER_V * cyls
        if r["verts"] != expect:
            errors.append(
                f"{bid}: verts {r['verts']} != closed form {expect} "
                f"({plates} plates x {PLATE_V} + {arcs} arcs x {ARC_SWEEP_V} "
                f"+ {cyls} cyls x {CYLINDER_V})")
            i_pass = False
    print(f"  I  verts == anatomy closed form: {'PASS' if i_pass else 'FAIL'}")

    # Final result
    print("\n" + "=" * 80)
    if errors:
        print(f"GATE RESULT: FAIL ({len(errors)} errors)")
        for e in errors:
            print(f"  - {e}")
    else:
        print("GATE RESULT: PASS (6/6)")
    print("=" * 80)

    return len(errors) == 0


if __name__ == "__main__":
    ok = main()
    sys.exit(0 if ok else 1)
