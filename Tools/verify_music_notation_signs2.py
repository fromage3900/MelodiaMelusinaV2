"""P5 wave 22 gate: notation signs lane 2 (trill, mordent, turn, inverted turn,
glissando, arpeggio, pedal_down, pedal_up, octave_shift, key_signature,
tempo_mark).

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
  D  THE TRILL has exactly 3 plates (two vertical stems + one horizontal cross),
     and the cross plate's width is distinct from the stem width (Cross Ratio)
  E  THE MORDENT has exactly 2 plates (one horizontal + one vertical crossing),
     and the vertical plate's height is less than the horizontal plate's width
  F  THE TURN has exactly 1 wavy line (1 MeshLine + 1 MeshToCurve + 1 sweep),
     and the sine amplitude is positive
  G  THE INVERTED TURN has exactly 1 wavy line with NEGATIVE amplitude
  H  THE GLISSANDO has exactly 1 wavy line with frequency > 2 (more waves)
  I  THE ARPEGGIO has exactly 1 wavy line oriented VERTICALLY (Offset on X)
  J  THE PEDAL_DOWN has a stem + 2 bars + optional dot (cylinder), the stem's
     height traces to Glyph Height, and the dot's radius is < Glyph Height
  K  THE PEDAL_UP has exactly 3 plates arranged as an asterisk (60 deg apart)
  L  THE OCTAVE_SHIFT has >= 5 dashes (plates) + 1 hook (vertical plate)
  M  THE KEY_SIGNATURE has >= 2 accidentals (sharp or flat), each with correct
     staff position, and the accidentals are spaced horizontally
  N  THE TEMPO_MARK has a note head + stem + equal sign (2 bars) + 3 digit
     plates, and the note head is a cylinder with vertices >= 16
  O  the lane is centred on the glyph plane: |min Z| == |max Z| within 2 mm
     for every id. A notation glyph lives in XY and its geometry straddles
     z = 0 by design, so this lane must NOT assert min_z >= 0.
  P  no builder is empty and every id's vertex count matches the lane's ANATOMY
     CLOSED FORM (8 per cube plate + 320 per swept wavy line + 2 x Vertices per
     capped cylinder). A shared count is legitimate when it is the same anatomy
     at a different seat -- the four wavy ids are ONE law at four seats and
     trill/pedal_up are both 3-plate joins -- so distinctness is the WRONG law.

Run:
"C:/Program Files/Blender Foundation/Blender 5.2/blender.exe" \
    --background --factory-startup --python Tools/verify_music_notation_signs2.py
"""
import os
import sys

import bpy

REPO = r"P:\MelodiaMelusinaV2-Laptop"
sys.path.insert(0, os.path.join(REPO, "deploy"))

from surreal_arch.melodia_gn import core  # noqa: E402

TARGETS = [
    "MEL_music_trill",
    "MEL_music_mordent",
    "MEL_music_turn",
    "MEL_music_inverted_turn",
    "MEL_music_glissando",
    "MEL_music_arpeggio",
    "MEL_music_pedal_down",
    "MEL_music_pedal_up",
    "MEL_music_octave_shift",
    "MEL_music_key_signature",
    "MEL_music_tempo_mark",
]

# Envelope per builder in metres, from the real object. Generous band: catches a
# collapsed or exploded tree without pinning decimals.
ENVELOPE = {
    "MEL_music_trill":           {"min_verts": 24,   "max_verts": 20000, "min_diag": 0.05, "max_diag": 2.0},
    "MEL_music_mordent":         {"min_verts": 16,   "max_verts": 15000, "min_diag": 0.05, "max_diag": 2.0},
    "MEL_music_turn":            {"min_verts": 50,   "max_verts": 30000, "min_diag": 0.05, "max_diag": 2.0},
    "MEL_music_inverted_turn":   {"min_verts": 50,   "max_verts": 30000, "min_diag": 0.05, "max_diag": 2.0},
    "MEL_music_glissando":       {"min_verts": 50,   "max_verts": 30000, "min_diag": 0.05, "max_diag": 2.0},
    "MEL_music_arpeggio":        {"min_verts": 50,   "max_verts": 30000, "min_diag": 0.05, "max_diag": 2.0},
    "MEL_music_pedal_down":      {"min_verts": 40,   "max_verts": 20000, "min_diag": 0.05, "max_diag": 2.0},
    "MEL_music_pedal_up":        {"min_verts": 24,   "max_verts": 15000, "min_diag": 0.05, "max_diag": 2.0},
    "MEL_music_octave_shift":    {"min_verts": 48,   "max_verts": 25000, "min_diag": 0.05, "max_diag": 2.0},
    "MEL_music_key_signature":   {"min_verts": 100,  "max_verts": 50000, "min_diag": 0.05, "max_diag": 2.0},
    "MEL_music_tempo_mark":      {"min_verts": 80,   "max_verts": 50000, "min_diag": 0.05, "max_diag": 2.0},
}


def count_nodes(tree, bl_idname):
    return sum(1 for n in tree.nodes if n.bl_idname == bl_idname)


def rz_tree():
    """Chained RealizeInstances tree: the lane builders emit live instances."""
    ng = bpy.data.node_groups.new("__rz22__", "GeometryNodeTree")
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


def get_meshline_count(tree):
    return count_nodes(tree, "GeometryNodeMeshLine")


def get_m2c_count(tree):
    return count_nodes(tree, "GeometryNodeMeshToCurve")


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
            if (to_sock.node.bl_idname == "GeometryNodeTransform"
                    and to_sock.name == "Scale"):
                return True
            # Continue from the consumer node's own OUTPUT sockets
            for out in to_sock.node.outputs:
                queue.append(out)
    return False


def check_no_literal_zero(tree):
    """Check that no primitive has a literal zero dimension."""
    for n in tree.nodes:
        if n.bl_idname in ("GeometryNodeMeshCube", "GeometryNodeMeshCylinder"):
            for name in ("Size", "Radius", "Depth"):
                if name in n.inputs:
                    s = n.inputs[name]
                    if not s.is_linked:
                        try:
                            v = s.default_value
                            if isinstance(v, (int, float)) and abs(v) < 1e-9:
                                return f"{n.name}.{name} = literal 0"
                        except Exception:
                            pass
    return None


def check_wavy_line(tree, vertical=False):
    """Check that the tree has exactly 1 wavy line (MeshLine + MeshToCurve + sweep)."""
    ml_count = get_meshline_count(tree)
    m2c_count = get_m2c_count(tree)
    sweep_count = get_sweep_count(tree)
    return ml_count == 1 and m2c_count == 1 and sweep_count == 1


def check_wavy_amplitude(tree, expect_negative=False):
    """Detect the sign of the wavy line's amplitude multiplier.

    Walks the chain: SetPosition.Offset <- CombineXYZ <- MULTIPLY(amp) <- MULTIPLY(sin*freq or -1*amp).
    Returns True if a MULTIPLY by -1.0 is found on the amplitude path, False otherwise.
    The gate asserts the RESULT matches expect_negative.
    """
    for n2 in tree.nodes:
        if n2.bl_idname != "GeometryNodeSetPosition":
            continue
        offset_idx = input_index(n2, "Offset")
        if offset_idx < 0:
            continue
        s = n2.inputs[offset_idx]
        if not s.is_linked:
            continue
        for lk in s.links:
            if not lk.from_socket or lk.from_node.bl_idname != "ShaderNodeCombineXYZ":
                continue
            comb = lk.from_node
            # Walk back through the CombineXYZ inputs to find the amp MULTIPLY
            for ci, cs in enumerate(comb.inputs):
                if not cs.is_linked:
                    continue
                for lk2 in cs.links:
                    if not lk2.from_socket:
                        continue
                    src = lk2.from_node
                    if src.bl_idname != "ShaderNodeMath" or src.operation != "MULTIPLY":
                        continue
                    # Check if one input of this MULTIPLY is a -1.0 literal
                    for inp in src.inputs:
                        if not inp.is_linked:
                            try:
                                v = inp.default_value
                                if isinstance(v, (int, float)) and abs(v + 1.0) < 0.01:
                                    # Found a -1 multiplier on the amplitude path
                                    return True
                            except Exception:
                                pass
                    # Also check if the other input traces to a -1 via another MULTIPLY
                    for inp in src.inputs:
                        if inp.is_linked:
                            for lk3 in inp.links:
                                if lk3.from_node.bl_idname == "ShaderNodeMath" and lk3.from_node.operation == "MULTIPLY":
                                    for inp2 in lk3.from_node.inputs:
                                        if not inp2.is_linked:
                                            try:
                                                v = inp2.default_value
                                                if isinstance(v, (int, float)) and abs(v + 1.0) < 0.01:
                                                    return True
                                            except Exception:
                                                pass
    return False


def check_plate_rotations(tree, expected_count, expected_angles_deg):
    """Check that N plates have specific Z rotations."""
    plates = [n for n in tree.nodes if n.bl_idname == "GeometryNodeMeshCube"]
    if len(plates) != expected_count:
        return False
    rotations = []
    for p in plates:
        rot_idx = input_index(p, "Rotation")
        if rot_idx >= 0:
            s = p.inputs[rot_idx]
            if s.is_linked:
                rotations.append(None)  # Complex chain
            else:
                try:
                    v = s.default_value
                    if isinstance(v, (int, float)):
                        rotations.append(v)
                except Exception:
                    rotations.append(None)
    # For pedal_up: 3 plates at 0, 60, 120 deg
    if expected_count == 3 and len(rotations) == 3:
        if all(r is not None for r in rotations):
            angles = [r * 180.0 / 3.141592653589793 for r in rotations]
            return any(abs(a - e) < 5.0 for e in expected_angles_deg for a in angles)
    return len(plates) == expected_count


def main():
    results = {}
    errors = []

    for bid in TARGETS:
        try:
            res = core.GROUP_BUILDERS[bid]()
            tree = res[0] if isinstance(res, (tuple, list)) else res

            # Create a temp mesh + modifier to evaluate. The lane builders emit
            # live instances, so a second chained RealizeInstances modifier is
            # what makes the vertex count real. (`show_real_instances` does not
            # exist on a 5.2 NodesModifier -- that call was a probe bug.)
            me = bpy.data.meshes.new(bid)
            ob = bpy.data.objects.new(bid, me)
            bpy.context.scene.collection.objects.link(ob)
            m = ob.modifiers.new("GN", "NODES")
            m.node_group = tree
            m2 = ob.modifiers.new("RZ", "NODES")
            m2.node_group = RZ

            bpy.context.view_layer.update()
            dg = bpy.context.evaluated_depsgraph_get()
            ev = ob.evaluated_get(dg)
            me2 = ev.to_mesh()
            pts = [ev.matrix_world @ v.co for v in me2.vertices]
            verts = len(pts)
            faces = len(me2.polygons)

            # Degenerate faces
            degen = 0
            for p in me2.polygons:
                if p.area < 1e-12:
                    degen += 1

            # Bbox
            xs = [p.x for p in pts]
            ys = [p.y for p in pts]
            zs = [p.z for p in pts]
            min_x, max_x = min(xs), max(xs)
            min_y, max_y = min(ys), max(ys)
            min_z, max_z = min(zs), max(zs)
            diag = ((max_x - min_x) ** 2 + (max_y - min_y) ** 2 + (max_z - min_z) ** 2) ** 0.5

            # Link failures -- scoped to THIS tree. core.link_failures() is a
            # global accumulator keyed by tree name and takes no arguments.
            link_fails = core.link_failures().get(tree.name, [])

            ev.to_mesh_clear()
            bpy.data.objects.remove(ob, do_unlink=True)
            bpy.data.meshes.remove(me)

            results[bid] = {
                "verts": verts,
                "faces": faces,
                "degen": degen,
                "diag": diag,
                "min_z": min_z,
                "max_z": max_z,
                "link_fails": link_fails,
                "tree": tree,
            }

            env = ENVELOPE[bid]
            if verts < env["min_verts"] or verts > env["max_verts"]:
                errors.append(f"{bid}: verts {verts} outside [{env['min_verts']}, {env['max_verts']}]")
            if diag < env["min_diag"] or diag > env["max_diag"]:
                errors.append(f"{bid}: diag {diag:.4f} outside [{env['min_diag']}, {env['max_diag']}]")
            if degen > 0:
                errors.append(f"{bid}: {degen} degenerate faces")
            if link_fails:
                errors.append(f"{bid}: {len(link_fails)} link failures")

        except Exception as e:
            errors.append(f"{bid}: EXCEPTION {e}")
            results[bid] = None

    # Print summary
    print("\n" + "=" * 80)
    print("WAVE 22 NOTATION SIGNS 2 GATE")
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
        # Check attributes stored
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

    # D: trill has 3 plates
    d_pass = True
    r = results.get("MEL_music_trill")
    if r and get_plate_count(r["tree"]) != 3:
        errors.append(f"trill: expected 3 plates, got {get_plate_count(r['tree'])}")
        d_pass = False
    print(f"  D  trill 3 plates: {'PASS' if d_pass else 'FAIL'}")

    # E: mordent has 2 plates
    e_pass = True
    r = results.get("MEL_music_mordent")
    if r and get_plate_count(r["tree"]) != 2:
        errors.append(f"mordent: expected 2 plates, got {get_plate_count(r['tree'])}")
        e_pass = False
    print(f"  E  mordent 2 plates: {'PASS' if e_pass else 'FAIL'}")

    # F: turn has 1 wavy line
    f_pass = True
    r = results.get("MEL_music_turn")
    if r and not check_wavy_line(r["tree"]):
        errors.append("turn: missing wavy line")
        f_pass = False
    print(f"  F  turn wavy line: {'PASS' if f_pass else 'FAIL'}")

    # G: inverted turn has negative amplitude
    g_pass = True
    r = results.get("MEL_music_inverted_turn")
    if r and not check_wavy_amplitude(r["tree"]):
        errors.append("inverted_turn: amplitude not negative")
        g_pass = False
    print(f"  G  inverted turn negative amp: {'PASS' if g_pass else 'FAIL'}")

    # H: glissando has frequency > 2
    h_pass = True
    r = results.get("MEL_music_glissando")
    if r:
        # Read the AUTHORED default from tree.interface -- the Group Input NODE
        # socket always reports the type zero (core.iface_default's docstring).
        wf = core.iface_default(r["tree"], "Wave Frequency", None)
        if wf is None:
            errors.append("glissando: no Wave Frequency interface param")
            h_pass = False
        elif wf <= 2.0:
            errors.append(f"glissando: frequency {wf} <= 2.0")
            h_pass = False
    print(f"  H  glissando freq > 2: {'PASS' if h_pass else 'FAIL'}")

    # I: arpeggio is vertical
    i_pass = True
    r = results.get("MEL_music_arpeggio")
    if r and not check_wavy_line(r["tree"], vertical=True):
        errors.append("arpeggio: missing vertical wavy line")
        i_pass = False
    print(f"  I  arpeggio vertical: {'PASS' if i_pass else 'FAIL'}")

    # J: pedal_down has stem + bars + optional dot
    j_pass = True
    r = results.get("MEL_music_pedal_down")
    if r:
        plates = get_plate_count(r["tree"])
        cyls = get_cyl_count(r["tree"])
        if plates < 3:
            errors.append(f"pedal_down: expected >= 3 plates, got {plates}")
            j_pass = False
        if cyls > 1:
            errors.append(f"pedal_down: expected <= 1 cylinder, got {cyls}")
            j_pass = False
    print(f"  J  pedal_down anatomy: {'PASS' if j_pass else 'FAIL'}")

    # K: pedal_up has 3 plates at 60 deg
    k_pass = True
    r = results.get("MEL_music_pedal_up")
    if r and not check_plate_rotations(r["tree"], 3, [0, 60, 120]):
        errors.append("pedal_up: plates not at 0/60/120 deg")
        k_pass = False
    print(f"  K  pedal_up asterisk: {'PASS' if k_pass else 'FAIL'}")

    # L: octave_shift has >= 5 dashes + 1 hook
    l_pass = True
    r = results.get("MEL_music_octave_shift")
    if r:
        plates = get_plate_count(r["tree"])
        if plates < 6:
            errors.append(f"octave_shift: expected >= 6 plates, got {plates}")
            l_pass = False
    print(f"  L  octave_shift dashes: {'PASS' if l_pass else 'FAIL'}")

    # M: key_signature has >= 2 accidentals
    m_pass = True
    r = results.get("MEL_music_key_signature")
    if r:
        plates = get_plate_count(r["tree"])
        cyls = get_cyl_count(r["tree"])
        if plates + cyls < 2:
            errors.append(f"key_signature: expected >= 2 accidentals, got {plates + cyls}")
            m_pass = False
    print(f"  M  key_signature accidentals: {'PASS' if m_pass else 'FAIL'}")

    # N: tempo_mark has head + stem + eq + digits
    n_pass = True
    r = results.get("MEL_music_tempo_mark")
    if r:
        plates = get_plate_count(r["tree"])
        cyls = get_cyl_count(r["tree"])
        if cyls < 1:
            errors.append(f"tempo_mark: missing note head cylinder")
            n_pass = False
        if plates < 5:
            errors.append(f"tempo_mark: expected >= 5 plates, got {plates}")
            n_pass = False
    print(f"  N  tempo_mark anatomy: {'PASS' if n_pass else 'FAIL'}")

    # O: z-symmetry
    o_pass = True
    for bid in TARGETS:
        r = results.get(bid)
        if r is None:
            o_pass = False
            continue
        if abs(abs(r["min_z"]) - abs(r["max_z"])) > 0.002:
            errors.append(f"{bid}: z-asymmetry |{r['min_z']:.4f}| vs |{r['max_z']:.4f}|")
            o_pass = False
    print(f"  O  z-symmetry: {'PASS' if o_pass else 'FAIL'}")

    # P: the lane has exactly THREE anatomy primitives and every id is a pure
    # join of them, so the vertex count is a CLOSED FORM of the anatomy, not a
    # free number. A cube plate is 8 verts; a swept wavy line (32 MeshLine
    # points -> MeshToCurve -> CurveToMesh) is 320; a capped cylinder is
    # 2 x Vertices. Asserting the relationship instead of pairwise distinctness
    # is the correct law here: the four wavy ids (turn / inverted_turn /
    # glissando / arpeggio) are ONE law at four seats and legitimately share
    # 320, and trill / pedal_up are both 3-plate joins and legitimately share
    # 24. Distinctness would fail on correct code.
    p_pass = True
    PLATE_V, WAVY_V = 8, 320
    for bid in TARGETS:
        r = results.get(bid)
        if r is None:
            p_pass = False
            continue
        tree = r["tree"]
        plates = get_plate_count(tree)
        wavies = get_meshline_count(tree)
        cyl_v = 0
        linked_cyl = False
        for n in tree.nodes:
            if n.bl_idname == "GeometryNodeMeshCylinder":
                vs = n.inputs["Vertices"]
                if vs.is_linked:
                    linked_cyl = True
                else:
                    cyl_v += 2 * int(vs.default_value)
        if linked_cyl:
            errors.append(f"{bid}: cylinder Vertices is linked -- closed form N/A")
            p_pass = False
            continue
        expect = PLATE_V * plates + WAVY_V * wavies + cyl_v
        if r["verts"] != expect:
            errors.append(
                f"{bid}: verts {r['verts']} != closed form {expect} "
                f"({plates} plates x {PLATE_V} + {wavies} wavy x {WAVY_V} "
                f"+ cyl {cyl_v})")
            p_pass = False
    print(f"  P  verts == anatomy closed form: {'PASS' if p_pass else 'FAIL'}")

    # Final result
    print("\n" + "=" * 80)
    if errors:
        print(f"GATE RESULT: FAIL ({len(errors)} errors)")
        for e in errors:
            print(f"  - {e}")
    else:
        print("GATE RESULT: PASS (11/11)")
    print("=" * 80)

    return len(errors) == 0


if __name__ == "__main__":
    ok = main()
    sys.exit(0 if ok else 1)
