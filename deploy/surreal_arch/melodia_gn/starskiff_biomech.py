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
