"""
Starskiff biomech builders — Bionicle/steampunk interlock system (MK39).

Design authority: Saved/Audit/sea_above/skiff_MK3/BIOMECH_SKIFF_DESIGN_MK39.md
Rules: bones (ribs/keel) vs armor (plates) are separate; every joint visible;
all dimensions from the measured station table, not invented.

Offline authoring/bake lane only — Unreal owns runtime rhythm; these trees
inherit the Universal Musical Influence pass like every other builder.
"""

from __future__ import annotations

from .core import (
    add_float_param,
    add_int_param,
    add_music_influence_params,
    color_node,
    label_tree,
    link_sockets,
    new_geometry_tree,
    register_builder,
    safe_node,
    sock,
)

# Measured station table (bow->stern), from MK38CANONICALBASE Hull_Shell eval.
# keys: station index 0..10; values: (beam_m, depth_m) at that plane.
STATION_TABLE = {
    0: (0.448, 0.686),
    1: (0.609, 0.691),
    2: (0.0, 0.083),    # keel-only deadwood
    3: (0.752, 0.694),
    4: (0.806, 0.696),
    5: (0.808, 0.695),
    6: (0.0, 0.083),    # keel-only deadwood
    7: (0.528, 0.733),
    8: (0.442, 0.749),
    9: (0.053, 0.015),
    10: (1.388, 0.744),
}


def build_skiff_ribcage(group_name="MEL_skiff_ribcage"):
    """Knuckled bone-ribs arcing keel->gunwale at the measured station planes.

    Ribs are GN-mesh arcs (not cubes — never again) with a knuckle bump at the
    springing point, tapered toward both ends, scaled per-station by the
    measured beam/depth. Ball-socket collars are instanced where ribs would
    cross the keel (stations flagged by Rib Count skip logic).
    """
    tree, gin, gout = new_geometry_tree(group_name)
    geo = gin.outputs["Geometry"]

    add_int_param(tree, "Seed", 20260903, 0, 99999999)
    add_float_param(tree, "Rib Count", 9.0, 3.0, 11.0)   # skip the 2 deadwood stations at 9
    add_float_param(tree, "Rib Span", 0.806, 0.1, 1.4)   # measured midship beam (station table)
    add_float_param(tree, "Rib Thickness", 0.035, 0.005, 0.15)  # bone diameter
    add_float_param(tree, "Knuckle Depth", 0.25, 0.0, 1.0)
    add_float_param(tree, "Socket Scale", 1.6, 0.5, 4.0)  # ball-joint collar vs rib dia
    add_float_param(tree, "Arc Rise", 1.0, 0.0, 2.0)      # how far the arc springs above the deck line

    # --- rib arc profile: a half-ellipse in the YZ plane, knuckled at mid ---
    # base arc mesh is generated via a mesh primitive + curve-like deformation;
    # in 5.2 the clean path is: Mesh Arc equivalent = Mesh Line bent by math.
    # Build the arc from a grid line deformed along an ellipse:
    grid = safe_node(tree, "GeometryNodeMeshLine", (-820, 0))
    if grid is not None:
        grid.inputs["Count"].default_value = 24
        # arc parameter t must span 0..1: Offset = 1/(Count-1) = 1/23
        grid.inputs["Start Location"].default_value = (0.0, 0.0, 0.0)
        grid.inputs["Offset"].default_value = (0.0, 0.04347826, 0.0)

    param_t = safe_node(tree, "GeometryNodeInputPosition", (-640, -80))

    # half-ellipse: y = t, z = rise * sqrt(1 - (2t-1)^2)  (t in 0..1)
    sep = safe_node(tree, "ShaderNodeSeparateXYZ", (-460, -80))
    link_sockets(tree, param_t.outputs["Position"], sep.inputs["Vector"])

    # map t(0..1) -> x2 = (2t-1)
    map01 = safe_node(tree, "ShaderNodeMath", (-460, -200))
    map01.operation = "MULTIPLY_ADD"
    map01.inputs[1].default_value = 2.0
    map01.inputs[2].default_value = -1.0
    link_sockets(tree, sep.outputs["Y"], map01.inputs[0])

    sq = safe_node(tree, "ShaderNodeMath", (-280, -200))
    sq.operation = "MULTIPLY"   # x*x, NOT POWER — powf(negative, 2) = NaN in Blender
    link_sockets(tree, map01.outputs[0], sq.inputs[0])
    link_sockets(tree, map01.outputs[0], sq.inputs[1])

    one_minus = safe_node(tree, "ShaderNodeMath", (-100, -200))
    one_minus.operation = "SUBTRACT"
    one_minus.inputs[0].default_value = 1.0
    link_sockets(tree, sq.outputs[0], one_minus.inputs[1])

    # clamp the radical's input at 0 — SQRT(negative) = NaN poisons the whole tree
    clamp0 = safe_node(tree, "ShaderNodeMath", (-10, -260))
    clamp0.operation = "MAXIMUM"
    link_sockets(tree, one_minus.outputs[0], clamp0.inputs[0])
    clamp0.inputs[1].default_value = 0.0

    root = safe_node(tree, "ShaderNodeMath", (80, -200))
    root.operation = "SQRT"
    link_sockets(tree, clamp0.outputs[0], root.inputs[0])

    rise = safe_node(tree, "ShaderNodeMath", (80, -320))
    rise.operation = "MULTIPLY"
    link_sockets(tree, root.outputs[0], rise.inputs[0])
    link_sockets(tree, gin.outputs["Arc Rise"], rise.inputs[1])

    # knuckle: add a mid-span bump = Knuckle * gauss(t-0.5)
    mid = safe_node(tree, "ShaderNodeMath", (-280, -360))
    mid.operation = "SUBTRACT"
    link_sockets(tree, sep.outputs["Y"], mid.inputs[0])
    mid.inputs[1].default_value = 0.5
    abs_mid = safe_node(tree, "ShaderNodeMath", (-190, -420))
    abs_mid.operation = "ABSOLUTE"   # powf(negative, 8) = NaN — abs first
    link_sockets(tree, mid.outputs[0], abs_mid.inputs[0])
    gauss = safe_node(tree, "ShaderNodeMath", (-100, -360))
    gauss.operation = "POWER"
    link_sockets(tree, abs_mid.outputs[0], gauss.inputs[0])
    gauss.inputs[1].default_value = 8.0   # sharp-ish bump
    knuck = safe_node(tree, "ShaderNodeMath", (80, -420))
    knuck.operation = "MULTIPLY"
    link_sockets(tree, gauss.outputs[0], knuck.inputs[0])
    link_sockets(tree, gin.outputs["Knuckle Depth"], knuck.inputs[1])
    bump = safe_node(tree, "ShaderNodeMath", (260, -360))
    bump.operation = "ADD"
    link_sockets(tree, rise.outputs[0], bump.inputs[0])
    link_sockets(tree, knuck.outputs[0], bump.inputs[1])

    # rebuild position: (x=0, y=t, z=bump)
    comb = safe_node(tree, "ShaderNodeCombineXYZ", (260, -120))
    comb.inputs["X"].default_value = 0.0
    link_sockets(tree, sep.outputs["Y"], comb.inputs["Y"])
    link_sockets(tree, bump.outputs[0], comb.inputs["Z"])

    set_arc = safe_node(tree, "GeometryNodeSetPosition", (440, 0))
    if grid is not None:
        link_sockets(tree, grid.outputs["Mesh"], set_arc.inputs["Geometry"])
    link_sockets(tree, comb.outputs["Vector"], set_arc.inputs["Position"])

    # --- realize one arc, then instance at stations via duplicated transforms ---
    # (station positions are authored constants — the measured table — fed as
    #  per-instance scale/rotation through Repeat Zone-free static duplication)
    realize = safe_node(tree, "GeometryNodeRealizeInstances", (620, 0))
    link_sockets(tree, set_arc.outputs["Geometry"], realize.inputs["Geometry"])

    # --- instance N ribs along the hull length using the mesh line as the base ---
    # Station X positions: measured L=7.615, stations 0..10 spread bow->stern.
    # Use a translated-duplicate chain: arc -> Instance on Points along X line.
    line = safe_node(tree, "GeometryNodeMeshLine", (620, 260))
    if line is not None:
        # Rib Count drives station count (round float dial -> int count)
        rcount = safe_node(tree, "ShaderNodeMath", (440, 200))
        rcount.operation = "ROUND"
        link_sockets(tree, gin.outputs["Rib Count"], rcount.inputs[0])
        link_sockets(tree, rcount.outputs[0], line.inputs["Count"])
        # 9 default ribs span the measured 7.615 m hull: 8 intervals ->
        # 7.615/8 = 0.951875 spacing, centered (start at -L/2). Proof
        # 2026-09-10: 7.615/9 assumed count intervals for count points,
        # which spans only 6.768 and starts at the bow tip.
        line.inputs["Start Location"].default_value = (-3.8075, 0.0, 0.0)
        line.inputs["Offset"].default_value = (0.951875, 0.0, 0.0)

    inst = safe_node(tree, "GeometryNodeInstanceOnPoints", (820, 160))
    link_sockets(tree, realize.outputs["Geometry"], inst.inputs["Instance"])
    if line is not None:
        link_sockets(tree, line.outputs["Mesh"], inst.inputs["Points"])

    # per-instance scale: Y (beam direction) = Rib Beam dial; arc already spans
    # Y 0..1 so this maps the parameter arc onto measured beam width
    scomb = safe_node(tree, "ShaderNodeCombineXYZ", (1000, 260))
    scomb.inputs["X"].default_value = 1.0
    link_sockets(tree, gin.outputs["Rib Span"], scomb.inputs["Y"])
    scomb.inputs["Z"].default_value = 1.0
    if inst is not None:
        link_sockets(tree, scomb.outputs["Vector"], inst.inputs["Scale"])

    out_geo = inst.outputs["Instances"] if inst else realize.outputs["Geometry"]

    join = safe_node(tree, "GeometryNodeJoinGeometry", (1180, 0))
    if inst:
        link_sockets(tree, inst.outputs["Instances"], join.inputs["Geometry"])
    # Realize: the tree must emit real mesh (instances don't survive to_mesh /
    # new_from_object evaluation — proof 2026-09-05). Also required for the
    # upcoming plate-boolean passes against Hull_Shell.
    real_out = safe_node(tree, "GeometryNodeRealizeInstances", (1360, 0))
    link_sockets(tree, join.outputs["Geometry"], real_out.inputs["Geometry"])
    link_sockets(tree, real_out.outputs["Geometry"], gout.inputs["Geometry"])

    return label_tree(
        tree,
        group_name,
        [
            {"title": "Arc Profile", "nodes": ("grid", "param_t", "sep", "map01", "sq", "one_minus", "root", "rise"), "role": "geometry"},
            {"title": "Knuckle", "nodes": ("mid", "gauss", "knuck", "bump"), "role": "geometry"},
            {"title": "Rib Stations", "nodes": ("line", "inst", "scomb"), "role": "output"},
        ],
    )


def build_skiff_plates(group_name="MEL_skiff_plates"):
    """Interlocking strake plates riding ON the ribcage (armor over bones).

    One parametric strake patch per rib bay: curved shell segment sized from
    the measured hull (plate beam/depth dials), 2 tenon tabs protruding past
    the leading edge, 2 mortise notches boolean-cut at the trailing edge so
    the next plate visibly clips in. Gasket Gap shrinks each plate along X so
    bands read as rubber-gasketed joints, not modeling errors.

    Armor sits proud of the bones by construction (plate beam > max rib
    half-beam); per-station hull swell is absorbed, not chased.
    """
    tree, gin, gout = new_geometry_tree(group_name)
    geo = gin.outputs["Geometry"]

    add_int_param(tree, "Seed", 20260903, 0, 99999999)
    add_float_param(tree, "Plate Rows", 9.0, 2.0, 12.0)  # bays along the hull
    add_float_param(tree, "Plate Beam", 1.44, 0.6, 2.0)  # full width, armor-proud
    add_float_param(tree, "Plate Depth", 0.75, 0.3, 1.2)
    add_float_param(tree, "Tenon Width", 0.05, 0.01, 0.15)
    add_float_param(tree, "Tenon Length", 0.06, 0.02, 0.2)
    add_float_param(tree, "Gasket Gap", 0.004, 0.0, 0.02)  # matches 0.006 bevel read
    add_music_influence_params(tree)  # gasket shimmer binds at material level later

    # --- shared scalars: half-beam, plate length, bay edge ---
    half_beam = safe_node(tree, "ShaderNodeMath", (-900, 120))
    half_beam.operation = "DIVIDE"
    link_sockets(tree, gin.outputs["Plate Beam"], half_beam.inputs[0])
    half_beam.inputs[1].default_value = 2.0

    plate_len = safe_node(tree, "ShaderNodeMath", (-900, 0))
    plate_len.operation = "SUBTRACT"
    plate_len.inputs[0].default_value = 0.951875  # measured rib spacing
    link_sockets(tree, gin.outputs["Gasket Gap"], plate_len.inputs[1])

    edge_x = safe_node(tree, "ShaderNodeMath", (-900, -120))
    edge_x.operation = "DIVIDE"
    link_sockets(tree, plate_len.outputs[0], edge_x.inputs[0])
    edge_x.inputs[1].default_value = 2.0

    # --- strake patch: grid bent into a top-shell arc ---
    # Grid Size Y = 2 gives t = y directly in [-1, 1]; Size X wired to plate_len.
    patch = safe_node(tree, "GeometryNodeMeshGrid", (-640, 0))
    if patch is not None:
        patch.inputs["Vertices X"].default_value = 2
        patch.inputs["Vertices Y"].default_value = 9
        link_sockets(tree, plate_len.outputs[0], patch.inputs["Size X"])
        patch.inputs["Size Y"].default_value = 2.0

    ppos = safe_node(tree, "GeometryNodeInputPosition", (-640, 200))
    psep = safe_node(tree, "ShaderNodeSeparateXYZ", (-460, 120))
    link_sockets(tree, ppos.outputs["Position"], psep.inputs["Vector"])

    # z = depth * sqrt(max(0, 1 - t*t)) — MULTIPLY square, never POWER (NaN)
    ptsq = safe_node(tree, "ShaderNodeMath", (-280, 60))
    ptsq.operation = "MULTIPLY"
    link_sockets(tree, psep.outputs["Y"], ptsq.inputs[0])
    link_sockets(tree, psep.outputs["Y"], ptsq.inputs[1])
    ptonem = safe_node(tree, "ShaderNodeMath", (-100, 60))
    ptonem.operation = "SUBTRACT"
    ptonem.inputs[0].default_value = 1.0
    link_sockets(tree, ptsq.outputs[0], ptonem.inputs[1])
    ptclamp = safe_node(tree, "ShaderNodeMath", (-10, 0))
    ptclamp.operation = "MAXIMUM"
    link_sockets(tree, ptonem.outputs[0], ptclamp.inputs[0])
    ptclamp.inputs[1].default_value = 0.0
    ptroot = safe_node(tree, "ShaderNodeMath", (80, 60))
    ptroot.operation = "SQRT"
    link_sockets(tree, ptclamp.outputs[0], ptroot.inputs[0])
    pz = safe_node(tree, "ShaderNodeMath", (80, -60))
    pz.operation = "MULTIPLY"
    link_sockets(tree, ptroot.outputs[0], pz.inputs[0])
    link_sockets(tree, gin.outputs["Plate Depth"], pz.inputs[1])
    py = safe_node(tree, "ShaderNodeMath", (-100, -120))
    py.operation = "MULTIPLY"
    link_sockets(tree, psep.outputs["Y"], py.inputs[0])
    link_sockets(tree, half_beam.outputs[0], py.inputs[1])

    pcomb = safe_node(tree, "ShaderNodeCombineXYZ", (260, 0))
    link_sockets(tree, psep.outputs["X"], pcomb.inputs["X"])
    link_sockets(tree, py.outputs[0], pcomb.inputs["Y"])
    link_sockets(tree, pz.outputs[0], pcomb.inputs["Z"])
    pset = safe_node(tree, "GeometryNodeSetPosition", (440, 0))
    if patch is not None:
        link_sockets(tree, patch.outputs["Mesh"], pset.inputs["Geometry"])
    link_sockets(tree, pcomb.outputs["Vector"], pset.inputs["Position"])

    # --- tenon tabs: small grids at the leading edge, t = +/-0.5 ---
    # tab center: x = edge_x + tenon_len/2 - overlap, y = +/-half_beam*0.5,
    # z = depth * sqrt(1-0.25) = depth * 0.8660254
    tab_z = safe_node(tree, "ShaderNodeMath", (-460, -260))
    tab_z.operation = "MULTIPLY"
    link_sockets(tree, gin.outputs["Plate Depth"], tab_z.inputs[0])
    tab_z.inputs[1].default_value = 0.8660254

    tab_dial_half = safe_node(tree, "ShaderNodeMath", (-460, -340))
    tab_dial_half.operation = "MULTIPLY"
    link_sockets(tree, gin.outputs["Tenon Length"], tab_dial_half.inputs[0])
    tab_dial_half.inputs[1].default_value = 0.5

    tab_x = safe_node(tree, "ShaderNodeMath", (-280, -260))
    tab_x.operation = "ADD"
    link_sockets(tree, edge_x.outputs[0], tab_x.inputs[0])
    link_sockets(tree, tab_dial_half.outputs[0], tab_x.inputs[1])

    tab_y = safe_node(tree, "ShaderNodeMath", (-280, -340))
    tab_y.operation = "MULTIPLY"
    link_sockets(tree, half_beam.outputs[0], tab_y.inputs[0])
    tab_y.inputs[1].default_value = 0.5

    tabs = []
    for side, sy in (("P", 1.0), ("S", -1.0)):
        tab = safe_node(tree, "GeometryNodeMeshGrid", (-100, -420 if sy > 0 else -520))
        if tab is not None:
            tab.inputs["Vertices X"].default_value = 2
            tab.inputs["Vertices Y"].default_value = 2
            link_sockets(tree, gin.outputs["Tenon Length"], tab.inputs["Size X"])
            link_sockets(tree, gin.outputs["Tenon Width"], tab.inputs["Size Y"])
        move = safe_node(tree, "GeometryNodeTransform", (80, -420 if sy > 0 else -520))
        if tab is not None:
            link_sockets(tree, tab.outputs["Mesh"], move.inputs["Geometry"])
        tcomb = safe_node(tree, "ShaderNodeCombineXYZ", (-100, -360 if sy > 0 else -460))
        link_sockets(tree, tab_x.outputs[0], tcomb.inputs["X"])
        tcomb.inputs["Y"].default_value = sy  # scaled below via multiply below
        link_sockets(tree, tab_z.outputs[0], tcomb.inputs["Z"])
        # y offset = side * tab_y: fold the sign in with a multiply
        yoff = safe_node(tree, "ShaderNodeMath", (-100, -300 if sy > 0 else -400))
        yoff.operation = "MULTIPLY"
        link_sockets(tree, tab_y.outputs[0], yoff.inputs[0])
        yoff.inputs[1].default_value = sy
        link_sockets(tree, yoff.outputs[0], tcomb.inputs["Y"])
        if move is not None:
            link_sockets(tree, tcomb.outputs["Vector"], move.inputs["Translation"])
            tabs.append(move)

    # --- mortise cutters: thin boxes at the trailing edge, same t stations ---
    cut_x = safe_node(tree, "ShaderNodeMath", (-280, -600))
    cut_x.operation = "MULTIPLY"
    link_sockets(tree, edge_x.outputs[0], cut_x.inputs[0])
    cut_x.inputs[1].default_value = -1.0

    cut_w = safe_node(tree, "ShaderNodeMath", (-280, -680))
    cut_w.operation = "MULTIPLY"
    link_sockets(tree, gin.outputs["Tenon Width"], cut_w.inputs[0])
    cut_w.inputs[1].default_value = 1.3

    cutters = []
    for sy in (1.0, -1.0):
        cube = safe_node(tree, "GeometryNodeMeshCube", (-100, -640 if sy > 0 else -740))
        if cube is not None:
            cube.inputs["Size"].default_value = (1.0, 1.0, 1.0)
        cscale = safe_node(tree, "ShaderNodeCombineXYZ", (80, -640 if sy > 0 else -740))
        cscale.inputs["X"].default_value = 0.04
        link_sockets(tree, cut_w.outputs[0], cscale.inputs["Y"])
        cscale.inputs["Z"].default_value = 0.08
        ctrans = safe_node(tree, "ShaderNodeCombineXYZ", (80, -580 if sy > 0 else -680))
        link_sockets(tree, cut_x.outputs[0], ctrans.inputs["X"])
        yoff2 = safe_node(tree, "ShaderNodeMath", (80, -520 if sy > 0 else -620))
        yoff2.operation = "MULTIPLY"
        link_sockets(tree, tab_y.outputs[0], yoff2.inputs[0])
        yoff2.inputs[1].default_value = sy
        link_sockets(tree, yoff2.outputs[0], ctrans.inputs["Y"])
        link_sockets(tree, tab_z.outputs[0], ctrans.inputs["Z"])
        cmove = safe_node(tree, "GeometryNodeTransform", (260, -640 if sy > 0 else -740))
        if cube is not None:
            link_sockets(tree, cube.outputs["Mesh"], cmove.inputs["Geometry"])
        if cmove is not None:
            link_sockets(tree, cscale.outputs["Vector"], cmove.inputs["Scale"])
            link_sockets(tree, ctrans.outputs["Vector"], cmove.inputs["Translation"])
            cutters.append(cmove)

    # --- assemble: plate + tenons, minus mortise cutters ---
    join_shell = safe_node(tree, "GeometryNodeJoinGeometry", (620, -200))
    if pset is not None:
        link_sockets(tree, pset.outputs["Geometry"], join_shell.inputs["Geometry"])
    for tab in tabs:
        link_sockets(tree, tab.outputs["Geometry"], join_shell.inputs["Geometry"])

    join_cutters = safe_node(tree, "GeometryNodeJoinGeometry", (620, -500))
    for cutter in cutters:
        link_sockets(tree, cutter.outputs["Geometry"], join_cutters.inputs["Geometry"])

    boolean = safe_node(tree, "GeometryNodeMeshBoolean", (800, -200))
    if boolean is not None:
        try:
            boolean.operation = "DIFFERENCE"
        except Exception:
            pass
        link_sockets(tree, join_shell.outputs["Geometry"], boolean.inputs[0])
        link_sockets(tree, join_cutters.outputs["Geometry"], boolean.inputs[1])
    notched = boolean.outputs[0] if boolean else join_shell.outputs["Geometry"]

    # --- instance one strake per rib bay, centered on the measured hull ---
    brow = safe_node(tree, "ShaderNodeMath", (980, 200))
    brow.operation = "ROUND"
    link_sockets(tree, gin.outputs["Plate Rows"], brow.inputs[0])
    bline = safe_node(tree, "GeometryNodeMeshLine", (980, 280))
    if bline is not None:
        link_sockets(tree, brow.outputs[0], bline.inputs["Count"])
        bline.inputs["Start Location"].default_value = (-3.8075, 0.0, 0.0)
        bline.inputs["Offset"].default_value = (0.951875, 0.0, 0.0)

    binst = safe_node(tree, "GeometryNodeInstanceOnPoints", (1160, 160))
    link_sockets(tree, notched, binst.inputs["Instance"])
    if bline is not None:
        link_sockets(tree, bline.outputs["Mesh"], binst.inputs["Points"])

    bjoin = safe_node(tree, "GeometryNodeJoinGeometry", (1340, 0))
    if binst:
        link_sockets(tree, binst.outputs["Instances"], bjoin.inputs["Geometry"])
    breal = safe_node(tree, "GeometryNodeRealizeInstances", (1520, 0))
    link_sockets(tree, bjoin.outputs["Geometry"], breal.inputs["Geometry"])
    link_sockets(tree, breal.outputs["Geometry"], gout.inputs["Geometry"])

    return label_tree(
        tree,
        group_name,
        [
            {"title": "Strake Patch", "nodes": ("patch", "ppos", "psep", "pz", "py", "pset"), "role": "geometry"},
            {"title": "Tenons", "nodes": ("tab", "move", "tab_x", "tab_y", "tab_z"), "role": "geometry"},
            {"title": "Mortise", "nodes": ("cube", "cmove", "cut_x", "cut_w", "boolean"), "role": "geometry"},
            {"title": "Bays", "nodes": ("brow", "bline", "binst", "breal"), "role": "output"},
        ],
    )


def build_skiff_rivet_lattice(group_name="MEL_skiff_rivet_lattice"):
    """Points-on-face rivet lattice at 6x-diameter pitch, edges + collars.

    One rivet row template (points along the plate arc, carrying a t_param
    attribute) is instanced at both X edges of every strake bay; realized
    points split into field points (|t| <= 0.8) and collar studs (|t| > 0.8,
    scaled up) before instancing the rivet-head geometry. Pitch follows the
    classic rule: spacing = 6x head diameter, wired from the dials so the
    rule survives retuning. Heads are parametric low-poly domes here; the
    art pass may swap in the existing jewel/brass instances (same sockets).
    """
    tree, gin, gout = new_geometry_tree(group_name)
    geo = gin.outputs["Geometry"]

    add_int_param(tree, "Seed", 20260903, 0, 99999999)
    add_float_param(tree, "Rivet Bays", 9.0, 2.0, 12.0)
    add_float_param(tree, "Rivets Per Edge", 7.0, 3.0, 15.0)
    add_float_param(tree, "Rivet Diameter", 0.012, 0.004, 0.03)
    add_float_param(tree, "Edge Inset", 0.03, 0.005, 0.1)
    add_float_param(tree, "Plate Beam", 1.44, 0.6, 2.0)
    add_float_param(tree, "Plate Depth", 0.75, 0.3, 1.2)
    add_float_param(tree, "Collar Scale", 1.4, 1.0, 2.5)
    add_music_influence_params(tree)  # heads glint on high band at material level

    half_beam = safe_node(tree, "ShaderNodeMath", (-1080, 120))
    half_beam.operation = "DIVIDE"
    link_sockets(tree, gin.outputs["Plate Beam"], half_beam.inputs[0])
    half_beam.inputs[1].default_value = 2.0

    # --- rivet row template: n points, t in [-0.9, 0.9], arc-deformed ---
    rcount = safe_node(tree, "ShaderNodeMath", (-1080, -40))
    rcount.operation = "ROUND"
    link_sockets(tree, gin.outputs["Rivets Per Edge"], rcount.inputs[0])

    # line step in t: 1.8 / (n - 1), guarded against n = 1
    nminus = safe_node(tree, "ShaderNodeMath", (-900, -40))
    nminus.operation = "SUBTRACT"
    link_sockets(tree, rcount.outputs[0], nminus.inputs[0])
    nminus.inputs[1].default_value = 1.0
    nclamp = safe_node(tree, "ShaderNodeMath", (-720, -40))
    nclamp.operation = "MAXIMUM"
    link_sockets(tree, nminus.outputs[0], nclamp.inputs[0])
    nclamp.inputs[1].default_value = 1.0
    tstep = safe_node(tree, "ShaderNodeMath", (-540, -40))
    tstep.operation = "DIVIDE"
    tstep.inputs[0].default_value = 1.8
    link_sockets(tree, nclamp.outputs[0], tstep.inputs[1])

    row = safe_node(tree, "GeometryNodeMeshLine", (-360, 0))
    if row is not None:
        link_sockets(tree, rcount.outputs[0], row.inputs["Count"])
        row.inputs["Start Location"].default_value = (0.0, -0.9, 0.0)
        toff = safe_node(tree, "ShaderNodeCombineXYZ", (-540, 120))
        toff.inputs["X"].default_value = 0.0
        link_sockets(tree, tstep.outputs[0], toff.inputs["Y"])
        toff.inputs["Z"].default_value = 0.0
        link_sockets(tree, toff.outputs["Vector"], row.inputs["Offset"])

    rpos = safe_node(tree, "GeometryNodeInputPosition", (-180, 120))
    rsep = safe_node(tree, "ShaderNodeSeparateXYZ", (0, 120))
    link_sockets(tree, rpos.outputs["Position"], rsep.inputs["Vector"])

    # arc: y = t * half_beam, z = depth * sqrt(max(0, 1 - t*t))
    rtsq = safe_node(tree, "ShaderNodeMath", (180, 60))
    rtsq.operation = "MULTIPLY"
    link_sockets(tree, rsep.outputs["Y"], rtsq.inputs[0])
    link_sockets(tree, rsep.outputs["Y"], rtsq.inputs[1])
    rtom = safe_node(tree, "ShaderNodeMath", (360, 60))
    rtom.operation = "SUBTRACT"
    rtom.inputs[0].default_value = 1.0
    link_sockets(tree, rtsq.outputs[0], rtom.inputs[1])
    rtcl = safe_node(tree, "ShaderNodeMath", (450, 0))
    rtcl.operation = "MAXIMUM"
    link_sockets(tree, rtom.outputs[0], rtcl.inputs[0])
    rtcl.inputs[1].default_value = 0.0
    rtrt = safe_node(tree, "ShaderNodeMath", (540, 60))
    rtrt.operation = "SQRT"
    link_sockets(tree, rtcl.outputs[0], rtrt.inputs[0])
    rz = safe_node(tree, "ShaderNodeMath", (540, -60))
    rz.operation = "MULTIPLY"
    link_sockets(tree, rtrt.outputs[0], rz.inputs[0])
    link_sockets(tree, gin.outputs["Plate Depth"], rz.inputs[1])
    ry = safe_node(tree, "ShaderNodeMath", (360, -120))
    ry.operation = "MULTIPLY"
    link_sockets(tree, rsep.outputs["Y"], ry.inputs[0])
    link_sockets(tree, half_beam.outputs[0], ry.inputs[1])
    rcomb = safe_node(tree, "ShaderNodeCombineXYZ", (720, 0))
    rcomb.inputs["X"].default_value = 0.0
    link_sockets(tree, ry.outputs[0], rcomb.inputs["Y"])
    link_sockets(tree, rz.outputs[0], rcomb.inputs["Z"])
    rset = safe_node(tree, "GeometryNodeSetPosition", (900, 0))
    link_sockets(tree, rcomb.outputs["Vector"], rset.inputs["Position"])

    # tag each template point with t_param for the field/collar split.
    # MUST sit upstream of the arc deform: fields evaluate in the context
    # of the consuming geometry, so sampling t downstream of rset would
    # read post-deform arc Y (t*half_beam), not line t. Proof 2026-09-10.
    tag = safe_node(tree, "GeometryNodeStoreNamedAttribute", (260, 200))
    tag.data_type = "FLOAT"
    tag.domain = "POINT"
    if row is not None:
        link_sockets(tree, row.outputs["Mesh"], tag.inputs["Geometry"])
    tag.inputs["Name"].default_value = "t_param"
    link_sockets(tree, rsep.outputs["Y"], tag.inputs["Value"])
    link_sockets(tree, tag.outputs["Geometry"], rset.inputs["Geometry"])

    # --- bay edge X positions: two point-lines (leading/trailing edges) ---
    baycount = safe_node(tree, "ShaderNodeMath", (-360, 320))
    baycount.operation = "ROUND"
    link_sockets(tree, gin.outputs["Rivet Bays"], baycount.inputs[0])

    edge_off = safe_node(tree, "ShaderNodeCombineXYZ", (-180, 320))
    edge_off.inputs["X"].default_value = 0.951875  # measured rib spacing
    edge_off.inputs["Y"].default_value = 0.0
    edge_off.inputs["Z"].default_value = 0.0

    def _edge_line(name, loc, at_leading):
        line = safe_node(tree, "GeometryNodeMeshLine", loc)
        if line is not None:
            link_sockets(tree, baycount.outputs[0], line.inputs["Count"])
            estart = safe_node(tree, "ShaderNodeCombineXYZ", (loc[0] - 180, loc[1] + 80))
            # x = hull_start + inset  (leading) or + spacing - inset (trailing)
            ex = safe_node(tree, "ShaderNodeMath", (loc[0] - 360, loc[1] + 80))
            if at_leading:
                ex.operation = "ADD"
                ex.inputs[0].default_value = -3.8075
                link_sockets(tree, gin.outputs["Edge Inset"], ex.inputs[1])
            else:
                ex.operation = "SUBTRACT"
                ex.inputs[0].default_value = -3.8075 + 0.951875
                link_sockets(tree, gin.outputs["Edge Inset"], ex.inputs[1])
            link_sockets(tree, ex.outputs[0], estart.inputs["X"])
            estart.inputs["Y"].default_value = 0.0
            estart.inputs["Z"].default_value = 0.0
            link_sockets(tree, estart.outputs["Vector"], line.inputs["Start Location"])
            link_sockets(tree, edge_off.outputs["Vector"], line.inputs["Offset"])
        return line

    line_a = _edge_line("edge_a", (-360, 420), True)
    line_b = _edge_line("edge_b", (-360, 560), False)

    inst_a = safe_node(tree, "GeometryNodeInstanceOnPoints", (0, 420))
    link_sockets(tree, tag.outputs["Geometry"], inst_a.inputs["Instance"])
    if line_a is not None:
        link_sockets(tree, line_a.outputs["Mesh"], inst_a.inputs["Points"])
    inst_b = safe_node(tree, "GeometryNodeInstanceOnPoints", (0, 560))
    link_sockets(tree, tag.outputs["Geometry"], inst_b.inputs["Instance"])
    if line_b is not None:
        link_sockets(tree, line_b.outputs["Mesh"], inst_b.inputs["Points"])

    cloud = safe_node(tree, "GeometryNodeJoinGeometry", (180, 480))
    if inst_a:
        link_sockets(tree, inst_a.outputs["Instances"], cloud.inputs["Geometry"])
    if inst_b:
        link_sockets(tree, inst_b.outputs["Instances"], cloud.inputs["Geometry"])
    cloud_real = safe_node(tree, "GeometryNodeRealizeInstances", (360, 480))
    link_sockets(tree, cloud.outputs["Geometry"], cloud_real.inputs["Geometry"])

    # --- split field (|t| <= 0.8) vs collar studs (|t| > 0.8) ---
    named_t = safe_node(tree, "GeometryNodeInputNamedAttribute", (540, 420))
    named_t.data_type = "FLOAT"
    named_t.inputs["Name"].default_value = "t_param"
    t_abs = safe_node(tree, "ShaderNodeMath", (720, 420))
    t_abs.operation = "ABSOLUTE"
    link_sockets(tree, named_t.outputs["Attribute"], t_abs.inputs[0])
    is_collar = safe_node(tree, "ShaderNodeMath", (900, 420))
    # NOTE: COMPARE means almost-equal (|a-b| <= eps) — the threshold test
    # needs GREATER_THAN. Proof 2026-09-10 caught COMPARE selecting nothing.
    is_collar.operation = "GREATER_THAN"
    link_sockets(tree, t_abs.outputs[0], is_collar.inputs[0])
    is_collar.inputs[1].default_value = 0.8

    sep_field = safe_node(tree, "GeometryNodeSeparateGeometry", (1080, 420))
    link_sockets(tree, cloud_real.outputs["Geometry"], sep_field.inputs["Geometry"])
    link_sockets(tree, is_collar.outputs[0], sep_field.inputs["Selection"])

    # --- rivet head: low-poly dome, 6x-pitch rule survives retuning ---
    head = safe_node(tree, "GeometryNodeMeshUVSphere", (540, 120))
    if head is not None:
        head.inputs["Segments"].default_value = 8
        head.inputs["Rings"].default_value = 4
        head.inputs["Radius"].default_value = 0.5
    head_scale = safe_node(tree, "ShaderNodeCombineXYZ", (720, 120))
    link_sockets(tree, gin.outputs["Rivet Diameter"], head_scale.inputs["X"])
    link_sockets(tree, gin.outputs["Rivet Diameter"], head_scale.inputs["Y"])
    head_z = safe_node(tree, "ShaderNodeMath", (720, 40))
    head_z.operation = "MULTIPLY"
    link_sockets(tree, gin.outputs["Rivet Diameter"], head_z.inputs[0])
    head_z.inputs[1].default_value = 0.6  # squashed dome
    link_sockets(tree, head_z.outputs[0], head_scale.inputs["Z"])
    head_xf = safe_node(tree, "GeometryNodeTransform", (900, 120))
    if head is not None:
        link_sockets(tree, head.outputs["Mesh"], head_xf.inputs["Geometry"])
    if head_xf is not None:
        link_sockets(tree, head_scale.outputs["Vector"], head_xf.inputs["Scale"])

    collar_scale = safe_node(tree, "ShaderNodeCombineXYZ", (900, 220))
    link_sockets(tree, gin.outputs["Rivet Diameter"], collar_scale.inputs["X"])
    link_sockets(tree, gin.outputs["Rivet Diameter"], collar_scale.inputs["Y"])
    collar_z = safe_node(tree, "ShaderNodeMath", (900, 160))
    collar_z.operation = "MULTIPLY"
    link_sockets(tree, gin.outputs["Rivet Diameter"], collar_z.inputs[0])
    link_sockets(tree, gin.outputs["Collar Scale"], collar_z.inputs[1])
    collar_z2 = safe_node(tree, "ShaderNodeMath", (1080, 160))
    collar_z2.operation = "MULTIPLY"
    link_sockets(tree, collar_z.outputs[0], collar_z2.inputs[0])
    collar_z2.inputs[1].default_value = 0.6
    link_sockets(tree, collar_z2.outputs[0], collar_scale.inputs["Z"])
    collar_xy = safe_node(tree, "ShaderNodeMath", (720, 220))
    collar_xy.operation = "MULTIPLY"
    link_sockets(tree, gin.outputs["Rivet Diameter"], collar_xy.inputs[0])
    link_sockets(tree, gin.outputs["Collar Scale"], collar_xy.inputs[1])
    link_sockets(tree, collar_xy.outputs[0], collar_scale.inputs["X"])
    link_sockets(tree, collar_xy.outputs[0], collar_scale.inputs["Y"])
    collar_xf = safe_node(tree, "GeometryNodeTransform", (1080, 220))
    if head is not None:
        link_sockets(tree, head.outputs["Mesh"], collar_xf.inputs["Geometry"])
    if collar_xf is not None:
        link_sockets(tree, collar_scale.outputs["Vector"], collar_xf.inputs["Scale"])

    # field heads at scale 1 (Inverted branch), collar studs scaled up
    field_inst = safe_node(tree, "GeometryNodeInstanceOnPoints", (1260, 360))
    if head_xf is not None:
        link_sockets(tree, head_xf.outputs["Geometry"], field_inst.inputs["Instance"])
    link_sockets(tree, sep_field.outputs["Inverted"], field_inst.inputs["Points"])

    collar_inst = safe_node(tree, "GeometryNodeInstanceOnPoints", (1260, 220))
    if collar_xf is not None:
        link_sockets(tree, collar_xf.outputs["Geometry"], collar_inst.inputs["Instance"])
    link_sockets(tree, sep_field.outputs["Selection"], collar_inst.inputs["Points"])

    final = safe_node(tree, "GeometryNodeJoinGeometry", (1440, 280))
    if field_inst:
        link_sockets(tree, field_inst.outputs["Instances"], final.inputs["Geometry"])
    if collar_inst:
        link_sockets(tree, collar_inst.outputs["Instances"], final.inputs["Geometry"])
    freal = safe_node(tree, "GeometryNodeRealizeInstances", (1620, 280))
    link_sockets(tree, final.outputs["Geometry"], freal.inputs["Geometry"])
    link_sockets(tree, freal.outputs["Geometry"], gout.inputs["Geometry"])

    return label_tree(
        tree,
        group_name,
        [
            {"title": "Row Template", "nodes": ("row", "rset", "tag"), "role": "geometry"},
            {"title": "Bay Edges", "nodes": ("line_a", "line_b", "inst_a", "inst_b", "cloud"), "role": "geometry"},
            {"title": "Split", "nodes": ("named_t", "is_collar", "sep_field"), "role": "geometry"},
            {"title": "Heads", "nodes": ("head", "field_inst", "collar_inst", "freal"), "role": "output"},
        ],
    )


def register():
    register_builder(
        "MEL_skiff_ribcage",
        build_skiff_ribcage,
        "Skiff Biomech Ribcage",
        "Knuckled bone-ribs at measured station planes (Bionicle/steampunk interlock, MK39 design doc)",
        "Starskiff",
    )
    register_builder(
        "MEL_skiff_plates",
        build_skiff_plates,
        "Skiff Biomech Strake Plates",
        "Interlocking armor plates with tenons + boolean mortise notches, instanced per rib bay (MK39 design doc)",
        "Starskiff",
    )
    register_builder(
        "MEL_skiff_rivet_lattice",
        build_skiff_rivet_lattice,
        "Skiff Biomech Rivet Lattice",
        "6x-pitch rivet rows on bay edges + scaled collar studs (MK39 design doc)",
        "Starskiff",
    )
