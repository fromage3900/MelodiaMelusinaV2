"""Escher Belvedere Loggia -- HERO GN builder (impossible two-story loggia).

A two-level loggia in the spirit of Escher's Belvedere: the LOWER level is a
perimeter-column loggia, and the UPPER level is a rotated (default 45 deg)
box -- slab, four corner columns, roof -- whose corners never align with the
lower column grid. The impossibility is sold by the four lower corner columns
threading PAST the upper floor (they poke out above it), by the upper level's
real supports standing offset at its own rotated corners, and by a straight
staircase that visibly fails to meet the upper floor edge (the Belvedere
ladder effect), continuing into floating steps once the upper level is rotated.

Every parameter is an editable named input on the node group. Wobble + Seed
drive a subtle deterministic facade noise for organic life.
"""

from __future__ import annotations

import bpy

from .core import (
    safe_node, link_sockets, link_float_to_vector, color_node, label_tree,
    new_geometry_tree, add_float_param, add_int_param, add_bool_param,
)


def _math(tree, operation, loc, a=None, b=None):
    """Local shorthand for ShaderNodeMath (keeps the graph legible)."""
    n = safe_node(tree, "ShaderNodeMath", loc)
    try:
        n.operation = operation
    except Exception:
        pass
    if a is not None:
        if isinstance(a, (int, float)):
            n.inputs[0].default_value = a
        else:
            link_sockets(tree, a, n.inputs[0])
    if b is not None:
        if isinstance(b, (int, float)):
            n.inputs[1].default_value = b
        else:
            link_sockets(tree, b, n.inputs[1])
    return n


def _combine(tree, loc, x, y, z):
    """Local shorthand for CombineXYZ with socket-or-scalar components."""
    n = safe_node(tree, "ShaderNodeCombineXYZ", loc)
    for comp, val in (("X", x), ("Y", y), ("Z", z)):
        if val is None:
            continue
        if isinstance(val, (int, float)):
            try:
                n.inputs[comp].default_value = val
            except Exception:
                pass
        else:
            link_sockets(tree, val, n.inputs[comp])
    return n


def _position_piece(tree, loc, geometry_sock, x=None, y=None, z=None):
	"""Translate a piece without collapsing point-distributed geometry."""
	transform = safe_node(tree, "GeometryNodeTransform", loc)
	link_sockets(tree, geometry_sock, transform.inputs["Geometry"])
	if x is not None or y is not None or z is not None:
		pos = _combine(tree, (loc[0] - 200, loc[1] - 120), x, y, z)
		link_sockets(tree, pos.outputs["Vector"], transform.inputs["Translation"])
	return transform.outputs["Geometry"]


def _instance_box(tree, loc, size, points_sock):
    """Instance a box primitive (size = 3-tuple of sockets/floats) on points."""
    box = safe_node(tree, "GeometryNodeMeshCube", loc)
    size_xyz = _combine(tree, (loc[0] - 200, loc[1] + 140), size[0], size[1], size[2])
    link_sockets(tree, size_xyz.outputs["Vector"], box.inputs["Size"])
    inst = safe_node(tree, "GeometryNodeInstanceOnPoints", (loc[0] + 120, loc[1]))
    link_sockets(tree, points_sock, inst.inputs["Points"])
    link_sockets(tree, box.outputs["Mesh"], inst.inputs["Instance"])
    realize = safe_node(tree, "GeometryNodeRealizeInstances", (loc[0] + 420, loc[1]))
    link_sockets(tree, inst.outputs["Instances"], realize.inputs["Geometry"])
    return realize.outputs["Geometry"]


def _belvedere_wobble(tree, geometry_sock, wobble_sock, seed_sock, loc):
    """Subtle deterministic facade wobble driven by Wobble + Seed."""
    pos = safe_node(tree, "GeometryNodeInputPosition", (loc[0] - 260, loc[1] - 140))
    noise = safe_node(tree, "ShaderNodeTexNoise", loc)
    seed_vec = _combine(tree, (loc[0] - 260, loc[1] + 100), seed_sock, 0.0, 0.0)
    noise_in = safe_node(tree, "ShaderNodeVectorMath", (loc[0] - 60, loc[1] + 100))
    noise_in.operation = "ADD"
    link_sockets(tree, pos.outputs["Position"], noise_in.inputs[0])
    link_sockets(tree, seed_vec.outputs["Vector"], noise_in.inputs[1])
    link_sockets(tree, noise_in.outputs["Vector"], noise.inputs["Vector"])
    noise.inputs["Scale"].default_value = 1.8
    noise.inputs["Detail"].default_value = 2.0
    noise.label = "wobble"

    sub = _math(tree, "SUBTRACT", (loc[0] + 180, loc[1] - 140), noise.outputs["Fac"], 0.5)
    amp = _math(tree, "MULTIPLY", (loc[0] + 180, loc[1] - 260), wobble_sock, 0.12)
    wob = _math(tree, "MULTIPLY", (loc[0] + 340, loc[1] - 140), sub.outputs[0], amp.outputs[0])

    offset = _combine(tree, (loc[0] + 500, loc[1] - 140), wob.outputs[0], wob.outputs[0], 0.0)
    vadd = safe_node(tree, "ShaderNodeVectorMath", (loc[0] + 340, loc[1] - 320))
    vadd.operation = "ADD"
    link_sockets(tree, pos.outputs["Position"], vadd.inputs[0])
    link_sockets(tree, offset.outputs["Vector"], vadd.inputs[1])

    set_pos = safe_node(tree, "GeometryNodeSetPosition", (loc[0] + 680, loc[1] - 140))
    link_sockets(tree, geometry_sock, set_pos.inputs["Geometry"])
    link_sockets(tree, vadd.outputs["Vector"], set_pos.inputs["Position"])
    return set_pos.outputs["Geometry"]


# ---------------------------------------------------------------------------
# Master builder
# ---------------------------------------------------------------------------

def build_escher_belvedere(group_name="MEL_escher_belvedere"):
    """Escher Belvedere Loggia -- impossible rotated two-story loggia.

    Lower loggia columns thread past the upper floor; the upper level is
    rotated (0-90 deg) with its own corner supports; a misaligned staircase
    continues into floating steps once rotated. All parameters are editable
    named inputs; Wobble + Seed drive a subtle facade wobble.
    """
    tree, gin, gout = new_geometry_tree(group_name)
    bx, by = 0, 0

    add_float_param(tree, "Lower Width", 5.0, 3.0, 10.0)
    add_float_param(tree, "Lower Depth", 4.0, 3.0, 8.0)
    add_float_param(tree, "Upper Width", 3.0, 1.5, 6.0)
    add_float_param(tree, "Upper Depth", 2.4, 1.5, 5.0)
    add_float_param(tree, "Upper Height", 2.6, 1.5, 4.0)
    add_float_param(tree, "Upper Rotation", 45.0, 0.0, 90.0)
    add_int_param(tree, "Column Count X", 2, 2, 4)
    add_int_param(tree, "Column Count Y", 2, 2, 4)
    add_float_param(tree, "Column Radius", 0.08, 0.04, 0.2)
    add_float_param(tree, "Floor Thickness", 0.2, 0.1, 0.4)
    add_bool_param(tree, "Staircase", True)
    add_bool_param(tree, "Vines", True)
    add_bool_param(tree, "Tall Threading Columns", True)
    add_float_param(tree, "Wobble", 0.05, 0.0, 0.3)
    add_int_param(tree, "Seed", 11, 0, 9999)

    pieces = []

    # -- lower floor slab -----------------------------------------------------
    lower_slab = safe_node(tree, "GeometryNodeMeshCube", (bx - 900, by + 1000))
    lower_slab.label = "lower slab"
    ls_size = _combine(tree, (bx - 1100, by + 920),
                       gin.outputs["Lower Width"], gin.outputs["Lower Depth"],
                       gin.outputs["Floor Thickness"])
    link_sockets(tree, ls_size.outputs["Vector"], lower_slab.inputs["Size"])
    ls_half = _math(tree, "MULTIPLY", (bx - 1100, by + 860),
                    gin.outputs["Floor Thickness"], 0.5)
    ls_out = _position_piece(tree, (bx - 700, by + 1000), lower_slab.outputs["Mesh"],
                             x=0.0, y=0.0, z=ls_half.outputs[0])
    pieces.append(ls_out)

    # -- lower loggia columns (threading height switch) ------------------------
    # tall = Upper Height * 1.3 (poke past the upper floor); short = Upper Height
    tall_h = _math(tree, "MULTIPLY", (bx - 1600, by + 600), gin.outputs["Upper Height"], 1.3)
    short_h = _math(tree, "MULTIPLY", (bx - 1600, by + 540), gin.outputs["Upper Height"], 1.0)
    h_sw = safe_node(tree, "GeometryNodeSwitch", (bx - 1400, by + 600))
    h_sw.input_type = "FLOAT"
    link_sockets(tree, gin.outputs["Tall Threading Columns"], h_sw.inputs["Switch"])
    link_sockets(tree, short_h.outputs[0], h_sw.inputs[1])
    link_sockets(tree, tall_h.outputs[0], h_sw.inputs[2])
    col_h = h_sw.outputs["Output"]

    grid = safe_node(tree, "GeometryNodeMeshGrid", (bx - 1600, by + 300))
    grid.label = "grid"
    link_sockets(tree, gin.outputs["Column Count X"], grid.inputs["Vertices X"])
    link_sockets(tree, gin.outputs["Column Count Y"], grid.inputs["Vertices Y"])
    link_sockets(tree, gin.outputs["Lower Width"], grid.inputs["Size X"])
    link_sockets(tree, gin.outputs["Lower Depth"], grid.inputs["Size Y"])

    column = safe_node(tree, "GeometryNodeMeshCylinder", (bx - 1400, by + 300))
    column.label = "column"
    link_sockets(tree, gin.outputs["Column Radius"], column.inputs["Radius"])
    column.inputs["Depth"].default_value = 1.0
    column.inputs["Vertices"].default_value = 10

    inst = safe_node(tree, "GeometryNodeInstanceOnPoints", (bx - 1200, by + 300))
    inst.label = "instance"
    link_sockets(tree, grid.outputs["Mesh"], inst.inputs["Points"])
    link_sockets(tree, column.outputs["Mesh"], inst.inputs["Instance"])

    scale_inst = safe_node(tree, "GeometryNodeScaleInstances", (bx - 1000, by + 300))
    link_sockets(tree, inst.outputs["Instances"], scale_inst.inputs["Instances"])
    link_float_to_vector(tree, col_h, scale_inst, "Scale",
                         component=2, defaults=(1.0, 1.0, 0.0))

    realize = safe_node(tree, "GeometryNodeRealizeInstances", (bx - 800, by + 300))
    link_sockets(tree, scale_inst.outputs["Instances"], realize.inputs["Geometry"])

    col_z = _math(tree, "MULTIPLY", (bx - 800, by + 240), col_h, 0.5)
    cols = _position_piece(tree, (bx - 600, by + 300), realize.outputs["Geometry"],
                           x=0.0, y=0.0, z=col_z.outputs[0])

    # capital caps on top of the threaded columns (only with threading on)
    cap = safe_node(tree, "GeometryNodeMeshCube", (bx - 1600, by + 60))
    cap.label = "cap"
    cap_r = _math(tree, "MULTIPLY", (bx - 1800, by + 60), gin.outputs["Column Radius"], 4.0)
    cap_size = _combine(tree, (bx - 1700, by), cap_r.outputs[0], cap_r.outputs[0], 0.18)
    link_sockets(tree, cap_size.outputs["Vector"], cap.inputs["Size"])
    inst_cap = safe_node(tree, "GeometryNodeInstanceOnPoints", (bx - 1400, by + 60))
    link_sockets(tree, grid.outputs["Mesh"], inst_cap.inputs["Points"])
    link_sockets(tree, cap.outputs["Mesh"], inst_cap.inputs["Instance"])
    realize_cap = safe_node(tree, "GeometryNodeRealizeInstances", (bx - 1200, by + 60))
    link_sockets(tree, inst_cap.outputs["Instances"], realize_cap.inputs["Geometry"])
    cap_z = _math(tree, "SUBTRACT", (bx - 1200, by), tall_h.outputs[0], 0.09)
    caps_placed = _position_piece(tree, (bx - 1000, by + 60), realize_cap.outputs["Geometry"],
                                  x=0.0, y=0.0, z=cap_z.outputs[0])

    thread_join = safe_node(tree, "GeometryNodeJoinGeometry", (bx - 400, by + 300))
    link_sockets(tree, cols, thread_join.inputs["Geometry"])
    link_sockets(tree, caps_placed, thread_join.inputs["Geometry"])
    thread_sw = safe_node(tree, "GeometryNodeSwitch", (bx - 200, by + 300))
    thread_sw.input_type = "GEOMETRY"
    link_sockets(tree, gin.outputs["Tall Threading Columns"], thread_sw.inputs["Switch"])
    link_sockets(tree, cols, thread_sw.inputs["False"])
    link_sockets(tree, thread_join.outputs["Geometry"], thread_sw.inputs["True"])
    pieces.append(thread_sw.outputs["Output"])

    # -- upper level (slab + corner supports + roof, rotated) ------------------
    upper_slab = safe_node(tree, "GeometryNodeMeshCube", (bx - 1500, by + 800))
    upper_slab.label = "upper slab"
    us_size = _combine(tree, (bx - 1700, by + 720),
                       gin.outputs["Upper Width"], gin.outputs["Upper Depth"],
                       gin.outputs["Floor Thickness"])
    link_sockets(tree, us_size.outputs["Vector"], upper_slab.inputs["Size"])
    us_ft_half = _math(tree, "MULTIPLY", (bx - 1700, by + 660),
                       gin.outputs["Floor Thickness"], 0.5)
    us_z = _math(tree, "ADD", (bx - 1600, by + 620),
                 gin.outputs["Upper Height"], us_ft_half.outputs[0])
    upper_slab_out = _position_piece(tree, (bx - 1300, by + 800), upper_slab.outputs["Mesh"],
                                     x=0.0, y=0.0, z=us_z.outputs[0])

    uc_h = _math(tree, "MULTIPLY", (bx - 1800, by + 400), gin.outputs["Upper Height"], 0.55)
    uc_mid = _math(tree, "MULTIPLY", (bx - 1800, by + 340), uc_h.outputs[0], 0.5)
    uc_center = _math(tree, "ADD", (bx - 1700, by + 300), us_z.outputs[0], uc_mid.outputs[0])
    uc_center = _math(tree, "ADD", (bx - 1600, by + 260), uc_center.outputs[0],
                      us_ft_half.outputs[0])

    upper_parts = [upper_slab_out]
    for i, (sx, sy) in enumerate(((1, 1), (-1, 1), (-1, -1), (1, -1))):
        uc = safe_node(tree, "GeometryNodeMeshCylinder", (bx - 1400, by + 400 - i * 90))
        uc.label = "upper column"
        link_sockets(tree, gin.outputs["Column Radius"], uc.inputs["Radius"])
        link_sockets(tree, uc_h.outputs[0], uc.inputs["Depth"])
        uc.inputs["Vertices"].default_value = 10
        ucx = _math(tree, "MULTIPLY", (bx - 1600, by + 400 - i * 90),
                    gin.outputs["Upper Width"], 0.5 * sx)
        ucy = _math(tree, "MULTIPLY", (bx - 1600, by + 340 - i * 90),
                    gin.outputs["Upper Depth"], 0.5 * sy)
        uc_out = _position_piece(tree, (bx - 1200, by + 400 - i * 90), uc.outputs["Mesh"],
                                 x=ucx.outputs[0], y=ucy.outputs[0], z=uc_center.outputs[0])
        upper_parts.append(uc_out)

    roof = safe_node(tree, "GeometryNodeMeshCube", (bx - 1400, by + 1000))
    roof.label = "roof"
    rw = _math(tree, "MULTIPLY", (bx - 1600, by + 1000), gin.outputs["Upper Width"], 0.92)
    rd = _math(tree, "MULTIPLY", (bx - 1600, by + 960), gin.outputs["Upper Depth"], 0.92)
    roof_size = _combine(tree, (bx - 1600, by + 920), rw.outputs[0], rd.outputs[0],
                         gin.outputs["Floor Thickness"])
    link_sockets(tree, roof_size.outputs["Vector"], roof.inputs["Size"])
    roof_z1 = _math(tree, "ADD", (bx - 1600, by + 880), us_z.outputs[0], uc_h.outputs[0])
    roof_z = _math(tree, "ADD", (bx - 1500, by + 840), roof_z1.outputs[0],
                   gin.outputs["Floor Thickness"])
    roof_out = _position_piece(tree, (bx - 1200, by + 1000), roof.outputs["Mesh"],
                               x=0.0, y=0.0, z=roof_z.outputs[0])
    upper_parts.append(roof_out)

    upper_join = safe_node(tree, "GeometryNodeJoinGeometry", (bx - 400, by + 600))
    upper_join.label = "upper join"
    for up in upper_parts:
        link_sockets(tree, up, upper_join.inputs["Geometry"])

    rotate = safe_node(tree, "GeometryNodeTransform", (bx - 200, by + 600))
    rotate.label = "rotate"
    link_sockets(tree, upper_join.outputs["Geometry"], rotate.inputs["Geometry"])
    rot_rad = _math(tree, "MULTIPLY", (bx - 400, by + 520),
                    gin.outputs["Upper Rotation"], 0.0174533)
    link_float_to_vector(tree, rot_rad.outputs[0], rotate, "Rotation",
                         component=2, defaults=(0.0, 0.0, 0.0))
    pieces.append(rotate.outputs["Geometry"])

    # -- staircase (misaligned with the upper floor; floats when rotated) -------
    stair_sw = safe_node(tree, "GeometryNodeSwitch", (bx - 500, by - 300))
    stair_sw.input_type = "GEOMETRY"
    link_sockets(tree, gin.outputs["Staircase"], stair_sw.inputs["Switch"])

    st_line = safe_node(tree, "GeometryNodeMeshLine", (bx - 1200, by - 300))
    st_line.mode = "OFFSET"
    st_line.inputs["Count"].default_value = 13
    st_dx = _math(tree, "MULTIPLY", (bx - 1400, by - 300), gin.outputs["Lower Width"], 0.065)
    st_dz = _math(tree, "MULTIPLY", (bx - 1400, by - 340), gin.outputs["Upper Height"], 0.0833)
    st_x = _math(tree, "MULTIPLY", (bx - 1400, by - 380), gin.outputs["Lower Width"], 0.45)
    st_y = _math(tree, "MULTIPLY", (bx - 1400, by - 420), gin.outputs["Lower Depth"], -0.62)
    st_start = _combine(tree, (bx - 1400, by - 460), st_x.outputs[0], st_y.outputs[0], 0.0)
    st_off = _combine(tree, (bx - 1400, by - 500), st_dx.outputs[0], 0.0, st_dz.outputs[0])
    link_sockets(tree, st_start.outputs["Vector"], st_line.inputs["Start Location"])
    link_sockets(tree, st_off.outputs["Vector"], st_line.inputs["Offset"])
    st_step_w = _math(tree, "MULTIPLY", (bx - 1400, by - 540), st_dx.outputs[0], 0.92)
    steps = _instance_box(tree, (bx - 900, by - 300),
                          (st_step_w.outputs[0], 1.1, 0.3), st_line.outputs["Mesh"])

    # floating ladder extension: only when the upper level is rotated
    rot_cmp = safe_node(tree, "FunctionNodeCompare", (bx - 1200, by - 680))
    rot_cmp.data_type = "FLOAT"
    rot_cmp.operation = "GREATER_THAN"
    link_sockets(tree, gin.outputs["Upper Rotation"], rot_cmp.inputs["A"])
    rot_cmp.inputs["B"].default_value = 1.0

    ext_line = safe_node(tree, "GeometryNodeMeshLine", (bx - 1400, by - 680))
    ext_line.mode = "OFFSET"
    ext_line.inputs["Count"].default_value = 5
    ext_run = _math(tree, "MULTIPLY", (bx - 1600, by - 680), st_dx.outputs[0], 12.0)
    ext_x = _math(tree, "ADD", (bx - 1500, by - 680), st_x.outputs[0], ext_run.outputs[0])
    ext_z = _math(tree, "ADD", (bx - 1500, by - 720), gin.outputs["Upper Height"], 0.35)
    ext_start = _combine(tree, (bx - 1500, by - 760), ext_x.outputs[0], st_y.outputs[0],
                         ext_z.outputs[0])
    ext_off = _combine(tree, (bx - 1500, by - 800), st_dx.outputs[0], 0.0, 0.24)
    link_sockets(tree, ext_start.outputs["Vector"], ext_line.inputs["Start Location"])
    link_sockets(tree, ext_off.outputs["Vector"], ext_line.inputs["Offset"])
    ext_steps = _instance_box(tree, (bx - 1100, by - 680),
                              (st_step_w.outputs[0], 1.0, 0.3), ext_line.outputs["Mesh"])
    ext_sw = safe_node(tree, "GeometryNodeSwitch", (bx - 900, by - 680))
    ext_sw.input_type = "GEOMETRY"
    link_sockets(tree, rot_cmp.outputs["Result"], ext_sw.inputs["Switch"])
    link_sockets(tree, ext_steps, ext_sw.inputs["True"])

    stair_join = safe_node(tree, "GeometryNodeJoinGeometry", (bx - 700, by - 300))
    link_sockets(tree, steps, stair_join.inputs["Geometry"])
    link_sockets(tree, ext_sw.outputs["Output"], stair_join.inputs["Geometry"])
    link_sockets(tree, stair_join.outputs["Geometry"], stair_sw.inputs["True"])
    pieces.append(stair_sw.outputs["Output"])

    # -- vines (deterministic overgrowth on the lower columns) ------------------
    vine_sw = safe_node(tree, "GeometryNodeSwitch", (bx - 700, by - 1150))
    vine_sw.input_type = "GEOMETRY"
    link_sockets(tree, gin.outputs["Vines"], vine_sw.inputs["Switch"])
    vine_parts = []
    for i, (vh, vx_s, vy_s, tilt) in enumerate((
            (0.8, 0.42, 0.40, 0.18), (1.5, -0.42, 0.40, -0.12),
            (2.2, 0.42, -0.40, 0.0), (2.9, -0.42, -0.40, 0.22),
            (3.2, 0.42, 0.40, 0.0), (1.1, -0.42, 0.40, 0.0))):
        v = safe_node(tree, "GeometryNodeMeshCube", (bx - 1100, by - 1150 - i * 80))
        v.label = "vine"
        v_size = _combine(tree, (bx - 1300, by - 1150 - i * 80), 0.09, 0.09, 0.5)
        link_sockets(tree, v_size.outputs["Vector"], v.inputs["Size"])
        vx = _math(tree, "MULTIPLY", (bx - 1300, by - 1210 - i * 80),
                   gin.outputs["Lower Width"], vx_s)
        vy = _math(tree, "MULTIPLY", (bx - 1300, by - 1250 - i * 80),
                   gin.outputs["Lower Depth"], vy_s)
        v_out = _position_piece(tree, (bx - 900, by - 1150 - i * 80), v.outputs["Mesh"],
                                x=vx.outputs[0], y=vy.outputs[0], z=vh)
        if tilt:
            vt = safe_node(tree, "GeometryNodeTransform", (bx - 700, by - 1150 - i * 80))
            link_sockets(tree, v_out, vt.inputs["Geometry"])
            vt.inputs["Rotation"].default_value[0] = tilt
            v_out = vt.outputs["Geometry"]
        vine_parts.append(v_out)
    vine_join = safe_node(tree, "GeometryNodeJoinGeometry", (bx - 700, by - 1240))
    for vp in vine_parts:
        link_sockets(tree, vp, vine_join.inputs["Geometry"])
    link_sockets(tree, vine_join.outputs["Geometry"], vine_sw.inputs["True"])
    pieces.append(vine_sw.outputs["Output"])

    # -- join, wobble, finish ----------------------------------------------------
    join = safe_node(tree, "GeometryNodeJoinGeometry", (bx + 300, by - 200))
    join.label = "join"
    for p in pieces:
        link_sockets(tree, p, join.inputs["Geometry"])

    wobbled = _belvedere_wobble(tree, join.outputs["Geometry"],
                                gin.outputs["Wobble"], gin.outputs["Seed"],
                                (bx + 700, by - 200))

    shade = safe_node(tree, "GeometryNodeSetShadeSmooth", (bx + 1100, by - 200))
    shade.label = "shade"
    shade.inputs["Shade Smooth"].default_value = True
    link_sockets(tree, wobbled, shade.inputs["Geometry"])
    link_sockets(tree, shade.outputs["Geometry"], gout.inputs["Geometry"])

    color_node(lower_slab, "geometry")
    color_node(grid, "curve")
    color_node(column, "geometry")
    color_node(inst, "instance")
    color_node(scale_inst, "instance")
    color_node(realize, "instance")
    color_node(thread_sw, "instance")
    color_node(upper_join, "geometry")
    color_node(rotate, "instance")
    color_node(stair_sw, "instance")
    color_node(ext_sw, "instance")
    color_node(vine_sw, "instance")
    color_node(join, "geometry")
    color_node(shade, "geometry")

    return label_tree(tree, "MEL_escher_belvedere", [
        {"title": "Inputs", "nodes": ("Group Input",), "role": "input"},
        {"title": "Lower Loggia", "nodes": ("slab", "grid", "column", "thread", "cap"), "role": "geometry"},
        {"title": "Upper Level", "nodes": ("upper", "rotate", "roof"), "role": "instance"},
        {"title": "Staircase", "nodes": ("stair", "step", "ladder"), "role": "geometry"},
        {"title": "Vines", "nodes": ("vine",), "role": "attribute"},
        {"title": "Wobble & Finish", "nodes": ("wobble", "join", "shade"), "role": "attribute"},
        {"title": "Output", "nodes": ("Group Output",), "role": "output"},
    ])


# -- Registry --------------------------------------------------------------
from .core import register_builder

register_builder(
    "MEL_escher_belvedere",
    build_escher_belvedere,
    "Escher Belvedere Loggia",
    "Impossible two-story loggia: lower column grid threaded past a rotated "
    "upper level (45 deg default) with corner supports, a misaligned staircase "
    "with floating ladder steps, deterministic vines, and wobble/seed detail.",
    "castle",
)
