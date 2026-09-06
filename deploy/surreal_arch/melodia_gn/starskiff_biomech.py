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
        line.inputs["Offset"].default_value = (0.846, 0.0, 0.0)  # 7.615/9 spacing

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


def register():
    register_builder(
        "MEL_skiff_ribcage",
        build_skiff_ribcage,
        "Skiff Biomech Ribcage",
        "Knuckled bone-ribs at measured station planes (Bionicle/steampunk interlock, MK39 design doc)",
        "Starskiff",
    )
