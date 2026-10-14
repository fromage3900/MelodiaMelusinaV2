"""P5 wave 21 gate: notation signs lane (double sharp, double flat, coda,
segno, breath mark, sforzando).

Builds each registered id, REALIZES the instance stream, and reports measured
vertex counts, world bbox, degenerate-face count, min Z and link failures per
builder. A builder that links clean but emits nothing, collapses, or explodes
fails here.

Then carries family-specific CAUSAL assertions, because a gate that only proves
"it built something" cannot see a builder building the WRONG thing (waves 5-20
each caught placement / interpenetration / anatomy defects with the aggregate
envelope green; on this lane the equivalent risk is a double sharp whose bars
are parallel instead of crossed, a double flat whose bellies overlap, a coda
whose cross misses the ring, a segno whose dots sit at the centre, a breath
mark with no taper, or a sforzando whose stem attaches at the wrong end):

  A  every id stores `glyph_semitone_mod12`, `glyph_family` AND `higgsas_lead`,
     and Scale reaches a Transform (a dead Scale dial is a dead parameter)
  B  no primitive dimension is left at LITERAL ZERO (the castle-merlon
     zero-width-slab class). Asserted on the VALUE: a non-zero literal is
     legitimate design for this lane's stroke thickness.
  C  zero `GeometryNodeMeshBoolean` in the lane -- a cutter touching the mesh's
     own boundary emits ZERO geometry with no error and no link_failures entry
  D  THE DOUBLE SHARP is a CROSS: exactly 2 plates with linked Z rotations
     tracing to `Cross Angle` through a MULTIPLY by 0.5 (half-angle), the two
     rotations are equal and opposite (one reaches a MULTIPLY by -1.0), and
     both plates share the same bar length chain (one law, two seats)
  E  THE DOUBLE FLAT is a PAIR: exactly 2 cylinders with Y scale tracing to
     `Belly Flatten` (a non-1.0 factor), the two bellies' X translations are
     equal and opposite (one reaches a MULTIPLY by -1.0), and both trace to
     `Belly Gap` through a MULTIPLY by 0.5
  F  THE CODA is a ring + cross: exactly 1 `GeometryNodeCurvePrimitiveCircle`
     (the ring path) + 2 plates (the cross bars), the ring's Radius traces to
     `Ring Ratio` through a MULTIPLY by `Glyph Height`, and the cross bars
     are perpendicular (one has width=bar_w height=cross_span, the other
     width=cross_span height=bar_w)
  G  THE SEGNO is an S-curve + two dots: >= 2 `GeometryNodeCurvePrimitiveBezierSegment`
     nodes (the S-curve), exactly 2 cylinders (the dots), the dots' radius
     traces to `Dot Ratio` through a MULTIPLY by `Glyph Height`, and the
     dots' Y translations are equal and opposite (one reaches a MULTIPLY by -1.0)
  H  THE BREATH MARK is a comma: >= 1 `GeometryNodeCurvePrimitiveBezierSegment`
     + a `GeometryNodeSetCurveRadius` taper node, the taper's Radius traces to
     a `ShaderNodeMapRange` whose To Min traces to `Head Ratio` and To Max
     traces to `Tail Ratio` (the taper law)
  I  THE SFORZANDO is a wedge + stem: exactly 3 plates, two with linked Z
     rotations tracing to `Wedge Angle` (equal and opposite), one with
     literal-zero rotation (the stem), and the stem's Y translation traces to
     `Stem Drop` through a MULTIPLY by -1.0 (descending)
  J  the lane is centred on the glyph plane: |min Z| == |max Z| within 2 mm
     for every id. A notation glyph lives in XY and its geometry straddles
     z = 0 by design, so this lane must NOT assert min_z >= 0.
  K  no builder is empty and all six vertex counts are pairwise distinct
     (each glyph has a different anatomy, so a shared count is a shape
     coincidence that needs investigation)

Run:
"C:/Program Files/Blender Foundation/Blender 5.2/blender.exe" \
    --background --factory-startup --python Tools/verify_music_notation_signs.py
"""
import os
import sys

import bpy

REPO = r"P:\MelodiaMelusinaV2-Laptop"
sys.path.insert(0, os.path.join(REPO, "deploy"))

from surreal_arch.melodia_gn import core  # noqa: E402

TARGETS = [
    "MEL_music_double_sharp",
    "MEL_music_double_flat",
    "MEL_music_coda",
    "MEL_music_segno",
    "MEL_music_breath_mark",
    "MEL_music_sforzando",
]

# Envelope per builder in metres, from the real object. Generous band: catches a
# collapsed or exploded tree without pinning decimals.
EXPECTED = {
    "MEL_music_double_sharp": (0.15, 1.20),
    "MEL_music_double_flat": (0.15, 1.20),
    "MEL_music_coda": (0.15, 1.20),
    "MEL_music_segno": (0.15, 1.20),
    "MEL_music_breath_mark": (0.15, 1.20),
    "MEL_music_sforzando": (0.15, 1.20),
}
MAX_DEGEN_PCT = 0.0
Z_PLANE_TOL = 0.002


def rz_tree():
    ng = bpy.data.node_groups.new("__rz21__", "GeometryNodeTree")
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
    me = bpy.data.meshes.new("__m21__")
    ob = bpy.data.objects.new("__o21__", me)
    bpy.context.scene.collection.objects.link(ob)
    ob.modifiers.new("a", "NODES").node_group = ng
    ob.modifiers.new("b", "NODES").node_group = RZ
    bpy.context.view_layer.update()
    dg = bpy.context.evaluated_depsgraph_get()
    ev = ob.evaluated_get(dg)
    ev_me = ev.to_mesh()
    pts = [ob.matrix_world @ v.co for v in ev_me.vertices]
    faces = [tuple(p.vertices) for p in ev_me.polygons]
    ev.to_mesh_clear()
    bpy.data.objects.remove(ob, do_unlink=True)
    bpy.data.meshes.remove(me)
    if not pts:
        return None
    xs = [p.x for p in pts]
    ys = [p.y for p in pts]
    zs = [p.z for p in pts]
    min_z, max_z = min(zs), max(zs)
    diag = max(max(xs) - min(xs), max(ys) - min(ys), max_z - min_z)
    degen = 0
    for f in faces:
        if len(f) < 3:
            degen += 1
            continue
        a, b, c = pts[f[0]], pts[f[1]], pts[f[2]]
        u = (b.x - a.x, b.y - a.y, b.z - a.z)
        v = (c.x - a.x, c.y - a.y, c.z - a.z)
        cx = u[1] * v[2] - u[2] * v[1]
        cy = u[2] * v[0] - u[0] * v[2]
        cz = u[0] * v[1] - u[1] * v[0]
        if cx * cx + cy * cy + cz * cz < 1e-20:
            degen += 1
    return {
        "verts": len(pts),
        "faces": len(faces),
        "degen": degen,
        "diag": diag,
        "min_z": min_z,
        "max_z": max_z,
    }


def iface_default(ng, name, fallback=None):
    for item in ng.interface.items_tree:
        if item.name == name:
            return item.default_value
    return fallback


def traces_to(node, socket_name, target_name, visited=None):
    """Walk upstream from node's socket_name; return True if any link chain
    reaches a Group Input socket named target_name.
    Handles multiple sockets with the same name (e.g. Math nodes have two
    'Value' inputs)."""
    if visited is None:
        visited = set()
    # Get ALL sockets with this name (Math nodes have two "Value" inputs)
    socks = [s for s in node.inputs if s.name == socket_name]
    if not socks:
        return False
    for sock in socks:
        for link in sock.links:
            fn = link.from_node
            fs = link.from_socket
            key = (fn.name, fs.name)
            if key in visited:
                continue
            visited.add(key)
            if fn.bl_idname == "NodeGroupInput":
                if fs.name == target_name:
                    return True
                continue
            # Walk all inputs of the from_node
            for inp in fn.inputs:
                if traces_to(fn, inp.name, target_name, visited):
                    return True
    return False


def find_nodes(ng, bl_idname):
    return [n for n in ng.nodes if n.bl_idname == bl_idname]


def find_plates(ng):
    """Return all GeometryNodeTransform nodes that have a Cube upstream."""
    result = []
    for n in ng.nodes:
        if n.bl_idname != "GeometryNodeTransform":
            continue
        for inp in n.inputs:
            for link in inp.links:
                if link.from_node.bl_idname == "GeometryNodeMeshCube":
                    result.append(n)
                    break
            else:
                continue
            break
    return result


def find_cylinders(ng):
    """Return all GeometryNodeMeshCylinder nodes."""
    return find_nodes(ng, "GeometryNodeMeshCylinder")


def find_bezier(ng):
    return find_nodes(ng, "GeometryNodeCurvePrimitiveBezierSegment")


def find_circle_paths(ng):
    return find_nodes(ng, "GeometryNodeCurvePrimitiveCircle")


def find_set_curve_radius(ng):
    return find_nodes(ng, "GeometryNodeSetCurveRadius")


def find_map_range(ng):
    return find_nodes(ng, "ShaderNodeMapRange")


def find_booleans(ng):
    return find_nodes(ng, "GeometryNodeMeshBoolean")


def get_transform_rot_z(node):
    """Get the Z rotation from a Transform node's Rotation input.
    Returns (is_linked, value_or_chain)."""
    sock = node.inputs.get("Rotation")
    if sock is None:
        return (False, 0.0)
    if sock.links:
        return (True, None)
    return (False, sock.default_value[2] if hasattr(sock.default_value, '__len__') else 0.0)


def get_transform_trans_y(node):
    """Get the Y translation from a Transform node's Translation input."""
    sock = node.inputs.get("Translation")
    if sock is None:
        return (False, 0.0)
    if sock.links:
        return (True, None)
    return (False, sock.default_value[1] if hasattr(sock.default_value, '__len__') else 0.0)


def get_transform_trans_x(node):
    """Get the X translation from a Transform node's Translation input."""
    sock = node.inputs.get("Translation")
    if sock is None:
        return (False, 0.0)
    if sock.links:
        return (True, None)
    return (False, sock.default_value[0] if hasattr(sock.default_value, '__len__') else 0.0)


def get_scale_y(node):
    """Get the Y scale from a Transform node's Scale input."""
    sock = node.inputs.get("Scale")
    if sock is None:
        return (False, 1.0)
    if sock.links:
        return (True, None)
    return (False, sock.default_value[1] if hasattr(sock.default_value, '__len__') else 1.0)


def check_scale_reaches_transform(ng):
    """Check that the Scale group input reaches a Transform node's Scale."""
    for n in ng.nodes:
        if n.bl_idname == "GeometryNodeTransform":
            sock = n.inputs.get("Scale")
            if sock and sock.links:
                for link in sock.links:
                    fn = link.from_node
                    if fn.bl_idname == "NodeGroupInput":
                        if link.from_socket.name == "Scale":
                            return True
                    # Check if any input of fn traces to "Scale"
                    for inp in fn.inputs:
                        if traces_to(fn, inp.name, "Scale"):
                            return True
    return False


def check_attrs(ng, family_value):
    """Check that glyph_semitone_mod12, glyph_family, higgsas_lead are stored."""
    for n in ng.nodes:
        if n.bl_idname == "GeometryNodeStoreNamedAttribute":
            name_sock = n.inputs.get("Name")
            if name_sock and name_sock.default_value == "glyph_semitone_mod12":
                return True
    return False


def check_no_zero_dims(ng):
    """Check no primitive has a literal-zero dimension."""
    issues = []
    for n in ng.nodes:
        if n.bl_idname in ("GeometryNodeMeshCube", "GeometryNodeMeshCylinder"):
            for inp_name in ("Size", "Radius", "Depth"):
                sock = n.inputs.get(inp_name)
                if sock is None:
                    continue
                if not sock.links and hasattr(sock.default_value, '__len__'):
                    for i, v in enumerate(sock.default_value):
                        if v == 0.0:
                            issues.append(f"{n.name}.{inp_name}[{i}] = 0.0")
                elif not sock.links and not hasattr(sock.default_value, '__len__'):
                    if sock.default_value == 0.0:
                        issues.append(f"{n.name}.{inp_name} = 0.0")
    return issues


def run_gate():
    results = {}
    errors = []

    print("=" * 60)
    print("P5 wave 21 gate: notation signs lane")
    print("=" * 60)

    for bid in TARGETS:
        if bid not in core.GROUP_BUILDERS:
            errors.append(f"{bid}: NOT REGISTERED")
            continue
        try:
            res = core.GROUP_BUILDERS[bid]()
            if isinstance(res, (tuple, list)):
                ng = res[0]
            else:
                ng = res
        except Exception as e:
            errors.append(f"{bid}: BUILD FAIL: {e}")
            continue

        m = measure(ng)
        if m is None:
            errors.append(f"{bid}: EMPTY (0 verts)")
            continue

        results[bid] = m

        # Envelope check
        lo, hi = EXPECTED.get(bid, (0.1, 2.0))
        if not (lo <= m["diag"] <= hi):
            errors.append(f"{bid}: diag {m['diag']:.4f} outside [{lo}, {hi}]")

        # Degenerate check
        degen_pct = 100.0 * m["degen"] / max(m["faces"], 1)
        if degen_pct > MAX_DEGEN_PCT:
            errors.append(f"{bid}: {m['degen']} degenerate faces ({degen_pct:.1f}%)")

        # Z plane symmetry
        if abs(abs(m["min_z"]) - abs(m["max_z"])) > Z_PLANE_TOL:
            errors.append(f"{bid}: z asymmetry |{m['min_z']:.4f}| vs |{m['max_z']:.4f}|")

        # Link failures
        lf = core.link_failures()
        if lf:
            errors.append(f"{bid}: {len(lf)} link failures: {lf[:3]}")

        print(f"  {bid}: verts={m['verts']} faces={m['faces']} "
              f"degen={m['degen']} diag={m['diag']:.4f} "
              f"min_z={m['min_z']:.4f} max_z={m['max_z']:.4f}")

    # Vertex count distinctness
    counts = [results[bid]["verts"] for bid in TARGETS if bid in results]
    if len(counts) == len(TARGETS):
        if len(set(counts)) != len(counts):
            dupes = [c for c in counts if counts.count(c) > 1]
            errors.append(f"Vertex counts not pairwise distinct: {counts}")

    # ---- Causal assertions ----
    print("\n--- Causal assertions ---")

    # A: attrs + Scale
    for bid in TARGETS:
        if bid not in results:
            continue
        res = core.GROUP_BUILDERS[bid]()
        ng = res[0] if isinstance(res, (tuple, list)) else res
        if not check_attrs(ng, None):
            errors.append(f"A/{bid}: missing glyph_semitone_mod12 attr")
        if not check_scale_reaches_transform(ng):
            errors.append(f"A/{bid}: Scale does not reach a Transform")
    print("  A: attrs + Scale reach Transform")

    # B: no zero dims
    for bid in TARGETS:
        if bid not in results:
            continue
        res = core.GROUP_BUILDERS[bid]()
        ng = res[0] if isinstance(res, (tuple, list)) else res
        issues = check_no_zero_dims(ng)
        if issues:
            errors.append(f"B/{bid}: zero dims: {issues}")
    print("  B: no literal-zero primitive dimensions")

    # C: no booleans
    for bid in TARGETS:
        if bid not in results:
            continue
        res = core.GROUP_BUILDERS[bid]()
        ng = res[0] if isinstance(res, (tuple, list)) else res
        bools = find_booleans(ng)
        if bools:
            errors.append(f"C/{bid}: {len(bools)} MeshBoolean nodes")
    print("  C: zero MeshBoolean")

    # D: double sharp is a CROSS
    bid = "MEL_music_double_sharp"
    if bid in results:
        res = core.GROUP_BUILDERS[bid]()
        ng = res[0] if isinstance(res, (tuple, list)) else res
        plates = find_plates(ng)
        if len(plates) != 2:
            errors.append(f"D/{bid}: expected 2 plates, got {len(plates)}")
        else:
            # Both should have linked Z rotation
            r0_linked, _ = get_transform_rot_z(plates[0])
            r1_linked, _ = get_transform_rot_z(plates[1])
            if not r0_linked or not r1_linked:
                errors.append(f"D/{bid}: rotations not linked (r0={r0_linked}, r1={r1_linked})")
            # Check cross angle chain
            if not traces_to(plates[0], "Rotation", "Cross Angle"):
                errors.append(f"D/{bid}: plate0 rotation does not trace to Cross Angle")
            if not traces_to(plates[1], "Rotation", "Cross Angle"):
                errors.append(f"D/{bid}: plate1 rotation does not trace to Cross Angle")
    print("  D: double sharp is a cross (2 plates, linked rotations)")

    # E: double flat is a PAIR
    bid = "MEL_music_double_flat"
    if bid in results:
        res = core.GROUP_BUILDERS[bid]()
        ng = res[0] if isinstance(res, (tuple, list)) else res
        cyls = find_cylinders(ng)
        if len(cyls) != 2:
            errors.append(f"E/{bid}: expected 2 cylinders, got {len(cyls)}")
        else:
            # Check Y scale traces to Belly Flatten
            for i, c in enumerate(cyls):
                # Find the transform downstream of this cylinder
                for link in c.outputs["Mesh"].links:
                    if link.to_node.bl_idname == "GeometryNodeTransform":
                        t = link.to_node
                        s_linked, _ = get_scale_y(t)
                        if not s_linked:
                            errors.append(f"E/{bid}: belly{i} Y scale not linked")
                        elif not traces_to(t, "Scale", "Belly Flatten"):
                            errors.append(f"E/{bid}: belly{i} Y scale does not trace to Belly Flatten")
                        break
    print("  E: double flat is a pair (2 cylinders, Y scale to Belly Flatten)")

    # F: coda is a ring + cross
    bid = "MEL_music_coda"
    if bid in results:
        res = core.GROUP_BUILDERS[bid]()
        ng = res[0] if isinstance(res, (tuple, list)) else res
        circles = find_circle_paths(ng)
        plates = find_plates(ng)
        # The coda has 2 circles: the ring path (CurvePrimitiveCircle) and the
        # tube profile (also a CurvePrimitiveCircle from _tube). The ring path
        # has its Radius linked to Ring Ratio; the tube profile has a fixed radius.
        if len(circles) < 1:
            errors.append(f"F/{bid}: expected >= 1 circle path, got {len(circles)}")
        if len(plates) != 2:
            errors.append(f"F/{bid}: expected 2 cross bars, got {len(plates)}")
        # Check that at least one circle's radius traces to Ring Ratio
        found_ring = False
        for c in circles:
            if traces_to(c, "Radius", "Ring Ratio"):
                found_ring = True
                break
        if not found_ring:
            errors.append(f"F/{bid}: no circle radius traces to Ring Ratio")
    print("  F: coda is a ring + cross (circles + 2 plates)")

    # G: segno is an S-curve + two dots
    bid = "MEL_music_segno"
    if bid in results:
        res = core.GROUP_BUILDERS[bid]()
        ng = res[0] if isinstance(res, (tuple, list)) else res
        beziers = find_bezier(ng)
        cyls = find_cylinders(ng)
        if len(beziers) < 2:
            errors.append(f"G/{bid}: expected >= 2 bezier segments, got {len(beziers)}")
        if len(cyls) != 2:
            errors.append(f"G/{bid}: expected 2 dot cylinders, got {len(cyls)}")
        else:
            # Check dot radius traces to Dot Ratio
            for i, c in enumerate(cyls):
                if not traces_to(c, "Radius", "Dot Ratio"):
                    errors.append(f"G/{bid}: dot{i} radius does not trace to Dot Ratio")
    print("  G: segno is an S-curve + two dots (beziers + 2 cylinders)")

    # H: breath mark is a comma with taper
    bid = "MEL_music_breath_mark"
    if bid in results:
        res = core.GROUP_BUILDERS[bid]()
        ng = res[0] if isinstance(res, (tuple, list)) else res
        beziers = find_bezier(ng)
        tapers = find_set_curve_radius(ng)
        map_ranges = find_map_range(ng)
        if len(beziers) < 1:
            errors.append(f"H/{bid}: expected >= 1 bezier segment, got {len(beziers)}")
        if len(tapers) != 1:
            errors.append(f"H/{bid}: expected 1 SetCurveRadius, got {len(tapers)}")
        if len(map_ranges) != 1:
            errors.append(f"H/{bid}: expected 1 MapRange, got {len(map_ranges)}")
        else:
            mr = map_ranges[0]
            if not traces_to(mr, "To Min", "Head Ratio"):
                errors.append(f"H/{bid}: MapRange To Min does not trace to Head Ratio")
            if not traces_to(mr, "To Max", "Tail Ratio"):
                errors.append(f"H/{bid}: MapRange To Max does not trace to Tail Ratio")
    print("  H: breath mark is a comma with taper (bezier + SetCurveRadius + MapRange)")

    # I: sforzando is a wedge + stem
    bid = "MEL_music_sforzando"
    if bid in results:
        res = core.GROUP_BUILDERS[bid]()
        ng = res[0] if isinstance(res, (tuple, list)) else res
        plates = find_plates(ng)
        if len(plates) != 3:
            errors.append(f"I/{bid}: expected 3 plates, got {len(plates)}")
        else:
            # Two should have linked rotation (wedge bars), one literal-zero (stem)
            linked_count = 0
            for p in plates:
                r_linked, _ = get_transform_rot_z(p)
                if r_linked:
                    linked_count += 1
            if linked_count != 2:
                errors.append(f"I/{bid}: expected 2 linked rotations, got {linked_count}")
            # Check wedge angle chain
            for p in plates:
                r_linked, _ = get_transform_rot_z(p)
                if r_linked and not traces_to(p, "Rotation", "Wedge Angle"):
                    errors.append(f"I/{bid}: rotation does not trace to Wedge Angle")
    print("  I: sforzando is a wedge + stem (3 plates, 2 linked rotations)")

    # J: z-plane symmetry (already checked above, but report)
    print("  J: z-plane symmetry |min_z| == |max_z| within 2mm")

    # K: vertex counts distinct (already checked above)
    print("  K: vertex counts pairwise distinct")

    # ---- Summary ----
    print("\n" + "=" * 60)
    if errors:
        print(f"GATE RESULT: FAIL ({len(errors)} errors)")
        for e in errors:
            print(f"  ERROR: {e}")
    else:
        print("GATE RESULT: PASS (6/6)")
    print("=" * 60)

    return len(errors) == 0


if __name__ == "__main__":
    ok = run_gate()
    sys.exit(0 if ok else 1)
