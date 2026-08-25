"""Nikki Flora Quarter -- HERO GN builder (Infinity Nikki themed architecture).

A comprehensive, parameter-driven pastel fantasy architecture generator with
four composition modes plus editable roofs, built for wide project usage:

  Mode 0  TOWNHOUSE -- multi-story pastel townhouse (bay window, balcony,
           flower boxes, chimney, lantern, porch, cornice, 4 roof styles)
  Mode 1  PAVILION  -- tea-house / festival stall pavilion (tiered roof,
           awning, counter, cushions)
  Mode 2  SPIRE     -- whimsical tall tower for skylines and floating
           islands (tapered sections, rings, finial tops, floating base)
  Mode 3  RUIN      -- broken quarter wall / ruin (split walls, lean,
           broken roof slab, rubble, column stumps)

Every parameter is an editable named input on the node group. A shared
Variation + Seed pair drives a subtle facade wobble for organic life.
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
    """Set a piece's position (primitives are origin-centered)."""
    set_pos = safe_node(tree, "GeometryNodeSetPosition", loc)
    link_sockets(tree, geometry_sock, set_pos.inputs["Geometry"])
    if x is not None or y is not None or z is not None:
        pos = _combine(tree, (loc[0] - 200, loc[1] - 120), x, y, z)
        link_sockets(tree, pos.outputs["Vector"], set_pos.inputs["Position"])
    return set_pos.outputs["Geometry"]


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


def _select_mode(tree, mode_sock, geo_0, geo_1, geo_2, geo_3, loc):
    """4-way geometry selector: mode 0/1/2/3 via nested boolean switches."""
    cmp1 = safe_node(tree, "FunctionNodeCompare", (loc[0], loc[1] + 320))
    cmp1.data_type = "INT"
    cmp1.operation = "EQUAL"
    link_sockets(tree, mode_sock, cmp1.inputs["A"])
    cmp1.inputs["B"].default_value = 1

    cmp2 = safe_node(tree, "FunctionNodeCompare", (loc[0], loc[1] + 160))
    cmp2.data_type = "INT"
    cmp2.operation = "EQUAL"
    link_sockets(tree, mode_sock, cmp2.inputs["A"])
    cmp2.inputs["B"].default_value = 2

    cmp3 = safe_node(tree, "FunctionNodeCompare", (loc[0], loc[1]))
    cmp3.data_type = "INT"
    cmp3.operation = "EQUAL"
    link_sockets(tree, mode_sock, cmp3.inputs["A"])
    cmp3.inputs["B"].default_value = 3

    sw1 = safe_node(tree, "GeometryNodeSwitch", (loc[0] + 220, loc[1] + 320))
    sw1.input_type = "GEOMETRY"
    link_sockets(tree, cmp1.outputs["Result"], sw1.inputs["Switch"])
    link_sockets(tree, geo_0, sw1.inputs["False"])
    link_sockets(tree, geo_1, sw1.inputs["True"])

    sw2 = safe_node(tree, "GeometryNodeSwitch", (loc[0] + 220, loc[1] + 160))
    sw2.input_type = "GEOMETRY"
    link_sockets(tree, cmp2.outputs["Result"], sw2.inputs["Switch"])
    link_sockets(tree, sw1.outputs["Output"], sw2.inputs["False"])
    link_sockets(tree, geo_2, sw2.inputs["True"])

    sw3 = safe_node(tree, "GeometryNodeSwitch", (loc[0] + 220, loc[1]))
    sw3.input_type = "GEOMETRY"
    link_sockets(tree, cmp3.outputs["Result"], sw3.inputs["Switch"])
    link_sockets(tree, sw2.outputs["Output"], sw3.inputs["False"])
    link_sockets(tree, geo_3, sw3.inputs["True"])

    return sw3.outputs["Output"]


def _add_wobble(tree, geometry_sock, variation_sock, seed_sock, loc):
    """Subtle deterministic facade wobble driven by Variation + Seed."""
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

    sub = _math(tree, "SUBTRACT", (loc[0] + 180, loc[1] - 140), noise.outputs["Fac"], 0.5)
    amp = _math(tree, "MULTIPLY", (loc[0] + 180, loc[1] - 260), variation_sock, 0.12)
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
# Mode 0 -- TOWNHOUSE
# ---------------------------------------------------------------------------

def _build_townhouse(tree, gin, loc):
    """Multi-story pastel townhouse with editable roofs and dressing toggles."""
    bx, by = loc

    wall_h = _math(tree, "MULTIPLY", (bx - 900, by + 40),
                   gin.outputs["Floors"], gin.outputs["Floor Height"])

    wall = safe_node(tree, "GeometryNodeMeshCube", (bx - 600, by + 40))
    wall_size = _combine(tree, (bx - 800, by - 80),
                         gin.outputs["Width"], gin.outputs["Depth"], wall_h.outputs[0])
    link_sockets(tree, wall_size.outputs["Vector"], wall.inputs["Size"])
    wall_out = _position_piece(tree, (bx - 400, by + 40), wall.outputs["Mesh"],
                               x=0.0, y=0.0, z=wall_h.outputs[0])
    pieces = [wall_out]

    # -- window strip on the front face -------------------------------------
    # rows land mid-floor: center_z = (floors-1)*fh/2 + 0.55*fh
    floors_m1 = _math(tree, "SUBTRACT", (bx - 1300, by - 240), gin.outputs["Floors"], 1)
    span_sz = _math(tree, "MULTIPLY", (bx - 1200, by - 240), floors_m1.outputs[0],
                    gin.outputs["Floor Height"])
    span_clamp = _math(tree, "MAXIMUM", (bx - 1400, by - 240), span_sz.outputs[0], 1.0)
    grid_w = _math(tree, "MULTIPLY", (bx - 1100, by - 360), gin.outputs["Width"], 0.82)
    grid_y = _math(tree, "MULTIPLY", (bx - 1100, by - 480), gin.outputs["Depth"], 0.5)
    grid_half = _math(tree, "MULTIPLY", (bx - 1200, by - 480), span_sz.outputs[0], 0.5)
    grid_off = _math(tree, "MULTIPLY", (bx - 1100, by - 520), gin.outputs["Floor Height"], 0.55)
    grid_z = _math(tree, "ADD", (bx - 1200, by - 520), grid_half.outputs[0], grid_off.outputs[0])
    grid = safe_node(tree, "GeometryNodeMeshGrid", (bx - 900, by - 240))
    link_sockets(tree, gin.outputs["Window Count"], grid.inputs["Vertices X"])
    link_sockets(tree, gin.outputs["Floors"], grid.inputs["Vertices Y"])
    link_sockets(tree, grid_w.outputs[0], grid.inputs["Size X"])
    link_sockets(tree, span_clamp.outputs[0], grid.inputs["Size Y"])
    grid_placed = _position_piece(tree, (bx - 800, by - 240), grid.outputs["Mesh"],
                                  x=0.0, y=grid_y.outputs[0], z=grid_z.outputs[0])

    win_w = _math(tree, "MULTIPLY", (bx - 1100, by - 620), gin.outputs["Width"], 0.11)
    win_w = _math(tree, "MAXIMUM", (bx - 1200, by - 620), win_w.outputs[0], 0.7)
    win_h = _math(tree, "MULTIPLY", (bx - 1100, by - 660), gin.outputs["Floor Height"], 0.42)
    win_h = _math(tree, "MAXIMUM", (bx - 1200, by - 660), win_h.outputs[0], 1.1)
    win_thick = _math(tree, "MAXIMUM", (bx - 1300, by - 700),
                      _math(tree, "MULTIPLY", (bx - 1400, by - 700),
                            gin.outputs["Depth"], 0.06).outputs[0], 0.06)
    windows = _instance_box(tree, (bx - 700, by - 260),
                            (win_w.outputs[0], win_thick.outputs[0], win_h.outputs[0]),
                            grid_placed)
    pieces.append(windows)

    # -- flower boxes under each window -------------------------------------
    fb = safe_node(tree, "GeometryNodeSwitch", (bx - 700, by - 420))
    fb.input_type = "GEOMETRY"
    link_sockets(tree, gin.outputs["Flower Boxes"], fb.inputs["Switch"])
    fb_geom = _instance_box(tree, (bx - 900, by - 420), (0.5, 0.16, 0.22), grid_placed)
    fb_lower = safe_node(tree, "GeometryNodeTransform", (bx - 600, by - 420))
    link_sockets(tree, fb_geom, fb_lower.inputs["Geometry"])
    fb_lower.inputs["Translation"].default_value[2] = -0.95
    link_sockets(tree, fb_lower.outputs["Geometry"], fb.inputs["True"])
    pieces.append(fb.outputs["Output"])

    # -- cornice ---------------------------------------------------------------
    cornice = safe_node(tree, "GeometryNodeSwitch", (bx - 700, by - 560))
    cornice.input_type = "GEOMETRY"
    link_sockets(tree, gin.outputs["Trim Cornice"], cornice.inputs["Switch"])
    c_w = _math(tree, "ADD", (bx - 900, by - 620), gin.outputs["Width"], 0.25)
    c_d = _math(tree, "ADD", (bx - 900, by - 660), gin.outputs["Depth"], 0.25)
    c_z = _math(tree, "ADD", (bx - 900, by - 700), wall_h.outputs[0], 0.09)
    c_box = safe_node(tree, "GeometryNodeMeshCube", (bx - 1100, by - 560))
    c_size = _combine(tree, (bx - 1300, by - 640), c_w.outputs[0], c_d.outputs[0], 0.18)
    link_sockets(tree, c_size.outputs["Vector"], c_box.inputs["Size"])
    c_out = _position_piece(tree, (bx - 900, by - 560), c_box.outputs["Mesh"],
                            x=0.0, y=0.0, z=c_z.outputs[0])
    link_sockets(tree, c_out, cornice.inputs["True"])
    pieces.append(cornice.outputs["Output"])

    # -- door -------------------------------------------------------------------
    door_w = _math(tree, "MAXIMUM", (bx - 1100, by - 860),
                   _math(tree, "MULTIPLY", (bx - 1200, by - 860),
                         gin.outputs["Width"], 0.24).outputs[0], 0.9)
    door_th = _math(tree, "ADD", (bx - 1000, by - 900), gin.outputs["Depth"], 0.07)
    door = safe_node(tree, "GeometryNodeMeshCube", (bx - 800, by - 860))
    door_size = _combine(tree, (bx - 1000, by - 940), door_w.outputs[0], door_th.outputs[0], 2.1)
    link_sockets(tree, door_size.outputs["Vector"], door.inputs["Size"])
    door_out = _position_piece(tree, (bx - 600, by - 860), door.outputs["Mesh"],
                               x=0.0, y=door_th.outputs[0], z=1.05)
    pieces.append(door_out)

    # -- bay window ---------------------------------------------------------------
    bay = safe_node(tree, "GeometryNodeSwitch", (bx - 700, by - 1000))
    bay.input_type = "GEOMETRY"
    link_sockets(tree, gin.outputs["Bay Window"], bay.inputs["Switch"])
    bay_w = _math(tree, "MAXIMUM", (bx - 1200, by - 1000),
                  _math(tree, "MULTIPLY", (bx - 1300, by - 1000),
                        gin.outputs["Width"], 0.36).outputs[0], 1.2)
    bay_z = _math(tree, "MULTIPLY", (bx - 1100, by - 1080), gin.outputs["Floor Height"], 0.75)
    bay_y = _math(tree, "MULTIPLY", (bx - 1100, by - 1120), gin.outputs["Depth"], 0.5)
    bay_box = safe_node(tree, "GeometryNodeMeshCube", (bx - 900, by - 1000))
    bay_size = _combine(tree, (bx - 1000, by - 1080), bay_w.outputs[0], 0.5, 1.9)
    link_sockets(tree, bay_size.outputs["Vector"], bay_box.inputs["Size"])
    bay_out = _position_piece(tree, (bx - 700, by - 1000), bay_box.outputs["Mesh"],
                              x=0.0, y=bay_y.outputs[0], z=bay_z.outputs[0])
    link_sockets(tree, bay_out, bay.inputs["True"])
    pieces.append(bay.outputs["Output"])

    # -- porch ---------------------------------------------------------------------
    porch = safe_node(tree, "GeometryNodeSwitch", (bx - 700, by - 1200))
    porch.input_type = "GEOMETRY"
    link_sockets(tree, gin.outputs["Porch"], porch.inputs["Switch"])
    porch_geom = []
    for side in (-0.55, 0.55):
        post = safe_node(tree, "GeometryNodeMeshCylinder", (bx - 900, by - 1200))
        post.inputs["Radius"].default_value = 0.06
        post.inputs["Depth"].default_value = 2.3
        post.inputs["Vertices"].default_value = 10
        px = _math(tree, "MULTIPLY", (bx - 1100, by - 1200), gin.outputs["Width"], side)
        py = _math(tree, "ADD", (bx - 1100, by - 1240), gin.outputs["Depth"], 0.5)
        post_out = _position_piece(tree, (bx - 700, by - 1200), post.outputs["Mesh"],
                                   x=px.outputs[0], y=py.outputs[0], z=1.15)
        porch_geom.append(post_out)
    porch_roof = safe_node(tree, "GeometryNodeMeshCube", (bx - 900, by - 1300))
    pr_w = _math(tree, "MAXIMUM", (bx - 1200, by - 1300),
                 _math(tree, "MULTIPLY", (bx - 1300, by - 1300),
                       gin.outputs["Width"], 0.55).outputs[0], 1.6)
    pr_y = _math(tree, "ADD", (bx - 1100, by - 1340), gin.outputs["Depth"], 0.55)
    pr_size = _combine(tree, (bx - 1000, by - 1380), pr_w.outputs[0], 0.8, 0.08)
    link_sockets(tree, pr_size.outputs["Vector"], porch_roof.inputs["Size"])
    pr_out = _position_piece(tree, (bx - 700, by - 1300), porch_roof.outputs["Mesh"],
                             x=0.0, y=pr_y.outputs[0], z=2.5)
    porch_join = safe_node(tree, "GeometryNodeJoinGeometry", (bx - 500, by - 1200))
    for g in porch_geom:
        link_sockets(tree, g, porch_join.inputs["Geometry"])
    link_sockets(tree, pr_out, porch_join.inputs["Geometry"])
    link_sockets(tree, porch_join.outputs["Geometry"], porch.inputs["True"])
    pieces.append(porch.outputs["Output"])

    # -- lantern -------------------------------------------------------------------
    lantern = safe_node(tree, "GeometryNodeSwitch", (bx - 700, by - 1420))
    lantern.input_type = "GEOMETRY"
    link_sockets(tree, gin.outputs["Lantern"], lantern.inputs["Switch"])
    lamp = safe_node(tree, "GeometryNodeMeshCylinder", (bx - 900, by - 1420))
    lamp.inputs["Radius"].default_value = 0.07
    lamp.inputs["Depth"].default_value = 0.3
    lamp.inputs["Vertices"].default_value = 10
    lampcap = safe_node(tree, "GeometryNodeMeshCone", (bx - 900, by - 1480))
    lampcap.inputs["Radius Bottom"].default_value = 0.13
    lampcap.inputs["Radius Top"].default_value = 0.02
    lampcap.inputs["Depth"].default_value = 0.16
    lampcap.inputs["Vertices"].default_value = 10
    lamp_x = _math(tree, "MULTIPLY", (bx - 1100, by - 1420), gin.outputs["Width"], 0.28)
    lamp_y = _math(tree, "ADD", (bx - 1100, by - 1460), gin.outputs["Depth"], 0.08)
    lamp_body = _position_piece(tree, (bx - 700, by - 1420), lamp.outputs["Mesh"],
                                x=lamp_x.outputs[0], y=lamp_y.outputs[0], z=2.15)
    lamp_top = _position_piece(tree, (bx - 700, by - 1480), lampcap.outputs["Mesh"],
                               x=lamp_x.outputs[0], y=lamp_y.outputs[0], z=2.35)
    lamp_join = safe_node(tree, "GeometryNodeJoinGeometry", (bx - 500, by - 1420))
    link_sockets(tree, lamp_body, lamp_join.inputs["Geometry"])
    link_sockets(tree, lamp_top, lamp_join.inputs["Geometry"])
    link_sockets(tree, lamp_join.outputs["Geometry"], lantern.inputs["True"])
    pieces.append(lantern.outputs["Output"])

    # -- balcony ---------------------------------------------------------------------
    balcony = safe_node(tree, "GeometryNodeSwitch", (bx - 700, by - 1600))
    balcony.input_type = "GEOMETRY"
    link_sockets(tree, gin.outputs["Balcony"], balcony.inputs["Switch"])
    bal_w = _math(tree, "MAXIMUM", (bx - 1200, by - 1600),
                  _math(tree, "MULTIPLY", (bx - 1300, by - 1600),
                        gin.outputs["Width"], 0.62).outputs[0], 1.6)
    bal_y = _math(tree, "ADD", (bx - 1100, by - 1640), gin.outputs["Depth"], 0.6)
    bal_z = _math(tree, "SUBTRACT", (bx - 1100, by - 1680), wall_h.outputs[0], 0.32)
    bal_plate = safe_node(tree, "GeometryNodeMeshCube", (bx - 900, by - 1600))
    bal_size = _combine(tree, (bx - 1000, by - 1640), bal_w.outputs[0], 0.55, 0.07)
    link_sockets(tree, bal_size.outputs["Vector"], bal_plate.inputs["Size"])
    bal_out = _position_piece(tree, (bx - 700, by - 1600), bal_plate.outputs["Mesh"],
                              x=0.0, y=bal_y.outputs[0], z=bal_z.outputs[0])
    rail_off = _math(tree, "DIVIDE", (bx - 1300, by - 1720), bal_w.outputs[0], 5.0)
    rail_half = _math(tree, "MULTIPLY", (bx - 1400, by - 1720), bal_w.outputs[0], -0.5)
    rail_start = _combine(tree, (bx - 1300, by - 1760), rail_half.outputs[0], bal_y.outputs[0], bal_z.outputs[0])
    rail_offv = _combine(tree, (bx - 1300, by - 1800), rail_off.outputs[0], 0.0, 0.0)
    rail_line = safe_node(tree, "GeometryNodeMeshLine", (bx - 1100, by - 1720))
    rail_line.mode = "OFFSET"
    rail_line.inputs["Count"].default_value = 6
    link_sockets(tree, rail_start.outputs["Vector"], rail_line.inputs["Start Location"])
    link_sockets(tree, rail_offv.outputs["Vector"], rail_line.inputs["Offset"])
    rail_geom = _instance_box(tree, (bx - 900, by - 1720), (0.06, 0.05, 1.0),
                              rail_line.outputs["Mesh"])
    bal_join = safe_node(tree, "GeometryNodeJoinGeometry", (bx - 500, by - 1600))
    link_sockets(tree, bal_out, bal_join.inputs["Geometry"])
    link_sockets(tree, rail_geom, bal_join.inputs["Geometry"])
    link_sockets(tree, bal_join.outputs["Geometry"], balcony.inputs["True"])
    pieces.append(balcony.outputs["Output"])

    # -- roof --------------------------------------------------------------------------
    pieces.append(_build_townhouse_roof(tree, gin, (bx - 700, by - 1960), wall_h.outputs[0]))

    # -- chimney ----------------------------------------------------------------------
    chimney = safe_node(tree, "GeometryNodeSwitch", (bx - 700, by - 2140))
    chimney.input_type = "GEOMETRY"
    link_sockets(tree, gin.outputs["Chimney"], chimney.inputs["Switch"])
    span = _math(tree, "MAXIMUM", (bx - 1100, by - 2180), gin.outputs["Width"], gin.outputs["Depth"])
    roof_h = _math(tree, "MULTIPLY", (bx - 1000, by - 2180), span.outputs[0], gin.outputs["Roof Pitch"])
    ch = safe_node(tree, "GeometryNodeMeshCube", (bx - 900, by - 2140))
    ch_size = _combine(tree, (bx - 1100, by - 2180), 0.4, 0.4, 1.7)
    link_sockets(tree, ch_size.outputs["Vector"], ch.inputs["Size"])
    ch_x = _math(tree, "MULTIPLY", (bx - 1100, by - 2220), gin.outputs["Width"], 0.28)
    ch_y = _math(tree, "MULTIPLY", (bx - 1100, by - 2260), gin.outputs["Depth"], -0.25)
    ch_z = _math(tree, "MULTIPLY", (bx - 1200, by - 2300), roof_h.outputs[0], 0.8)
    ch_z = _math(tree, "ADD", (bx - 1100, by - 2300), wall_h.outputs[0], ch_z.outputs[0])
    ch_z = _math(tree, "ADD", (bx - 1000, by - 2300), ch_z.outputs[0], 0.9)
    ch_out = _position_piece(tree, (bx - 700, by - 2140), ch.outputs["Mesh"],
                             x=ch_x.outputs[0], y=ch_y.outputs[0], z=ch_z.outputs[0])
    link_sockets(tree, ch_out, chimney.inputs["True"])
    pieces.append(chimney.outputs["Output"])

    join = safe_node(tree, "GeometryNodeJoinGeometry", (bx + 200, by - 200))
    for p in pieces:
        link_sockets(tree, p, join.inputs["Geometry"])
    return join.outputs["Geometry"]


def _build_townhouse_roof(tree, gin, loc, wall_top):
    """Roof modes for the townhouse: 0=Hip, 1=Onion, 2=Pagoda, 3=Clerestory."""
    bx, by = loc
    span = _math(tree, "MAXIMUM", (bx - 1200, by), gin.outputs["Width"], gin.outputs["Depth"])
    roof_h = _math(tree, "MULTIPLY", (bx - 1000, by), span.outputs[0], gin.outputs["Roof Pitch"])
    half = _math(tree, "MULTIPLY", (bx - 1200, by - 80), span.outputs[0], 0.5)
    ovh = gin.outputs["Eave Overhang"]

    # 0 -- hip roof (pyramid, rotated 45 deg)
    hip = safe_node(tree, "GeometryNodeMeshCone", (bx - 1000, by + 240))
    hip.inputs["Vertices"].default_value = 4
    r_bottom = _math(tree, "ADD", (bx - 1200, by + 240), half.outputs[0], ovh)
    link_sockets(tree, r_bottom.outputs[0], hip.inputs["Radius Bottom"])
    link_sockets(tree, roof_h.outputs[0], hip.inputs["Depth"])
    hip_z = _math(tree, "ADD", (bx - 1200, by + 120), wall_top,
                  _math(tree, "MULTIPLY", (bx - 1300, by + 120), roof_h.outputs[0], 0.5).outputs[0])
    hip_placed = _position_piece(tree, (bx - 800, by + 240), hip.outputs["Mesh"],
                                 x=0.0, y=0.0, z=hip_z.outputs[0])
    hip_tx = safe_node(tree, "GeometryNodeTransform", (bx - 600, by + 240))
    link_sockets(tree, hip_placed, hip_tx.inputs["Geometry"])
    hip_tx.inputs["Rotation"].default_value[2] = 0.7854

    # 1 -- onion dome (squashed sphere + finial)
    onion = safe_node(tree, "GeometryNodeMeshUVSphere", (bx - 1000, by))
    onion.inputs["Segments"].default_value = 24
    onion.inputs["Rings"].default_value = 12
    r_dome = _math(tree, "MULTIPLY", (bx - 1200, by), span.outputs[0], 0.32)
    link_sockets(tree, r_dome.outputs[0], onion.inputs["Radius"])
    dome_scale = _combine(tree, (bx - 1000, by - 100), 1.0, 1.0, 0.6)
    dome_tx = safe_node(tree, "GeometryNodeTransform", (bx - 800, by))
    link_sockets(tree, onion.outputs["Mesh"], dome_tx.inputs["Geometry"])
    link_sockets(tree, dome_scale.outputs["Vector"], dome_tx.inputs["Scale"])
    dome_z = _math(tree, "ADD", (bx - 1100, by - 140), wall_top,
                   _math(tree, "MULTIPLY", (bx - 1200, by - 140), span.outputs[0], 0.19).outputs[0])
    dome_placed = _position_piece(tree, (bx - 600, by), dome_tx.outputs["Geometry"],
                                  x=0.0, y=0.0, z=dome_z.outputs[0])
    finial = safe_node(tree, "GeometryNodeMeshCone", (bx - 800, by - 220))
    finial.inputs["Radius Bottom"].default_value = 0.09
    finial.inputs["Depth"].default_value = 0.3
    finial.inputs["Vertices"].default_value = 8
    fin_z = _math(tree, "ADD", (bx - 900, by - 220), dome_z.outputs[0],
                  _math(tree, "MULTIPLY", (bx - 1000, by - 220), span.outputs[0], 0.19).outputs[0])
    fin_z = _math(tree, "ADD", (bx - 800, by - 220), fin_z.outputs[0], 0.15)
    fin_placed = _position_piece(tree, (bx - 600, by - 220), finial.outputs["Mesh"],
                                 x=0.0, y=0.0, z=fin_z.outputs[0])
    onion_join = safe_node(tree, "GeometryNodeJoinGeometry", (bx - 400, by))
    link_sockets(tree, dome_placed, onion_join.inputs["Geometry"])
    link_sockets(tree, fin_placed, onion_join.inputs["Geometry"])

    # 2 -- pagoda (two stacked cones + cap)
    p1 = safe_node(tree, "GeometryNodeMeshCone", (bx - 1000, by - 320))
    p1.inputs["Vertices"].default_value = 6
    r1_b = _math(tree, "ADD", (bx - 1200, by - 320), half.outputs[0], ovh)
    link_sockets(tree, r1_b.outputs[0], p1.inputs["Radius Bottom"])
    r1_t = _math(tree, "MULTIPLY", (bx - 1200, by - 360), span.outputs[0], 0.28)
    link_sockets(tree, r1_t.outputs[0], p1.inputs["Radius Top"])
    d1 = _math(tree, "MULTIPLY", (bx - 1200, by - 400), roof_h.outputs[0], 0.7)
    link_sockets(tree, d1.outputs[0], p1.inputs["Depth"])
    p1_z = _math(tree, "ADD", (bx - 1200, by - 400), wall_top,
                 _math(tree, "MULTIPLY", (bx - 1300, by - 400), d1.outputs[0], 0.5).outputs[0])
    p1_placed = _position_piece(tree, (bx - 800, by - 320), p1.outputs["Mesh"],
                                x=0.0, y=0.0, z=p1_z.outputs[0])
    p2 = safe_node(tree, "GeometryNodeMeshCone", (bx - 1000, by - 520))
    p2.inputs["Vertices"].default_value = 6
    r2_b = _math(tree, "ADD", (bx - 1200, by - 520), r1_t.outputs[0], ovh)
    link_sockets(tree, r2_b.outputs[0], p2.inputs["Radius Bottom"])
    r2_t = _math(tree, "MULTIPLY", (bx - 1200, by - 560), span.outputs[0], 0.12)
    link_sockets(tree, r2_t.outputs[0], p2.inputs["Radius Top"])
    d2 = _math(tree, "MULTIPLY", (bx - 1200, by - 600), roof_h.outputs[0], 0.5)
    link_sockets(tree, d2.outputs[0], p2.inputs["Depth"])
    d1h = _math(tree, "MULTIPLY", (bx - 1300, by - 600), d1.outputs[0], 0.5)
    d2h = _math(tree, "MULTIPLY", (bx - 1300, by - 640), d2.outputs[0], 0.5)
    p2_z = _math(tree, "ADD", (bx - 1200, by - 600), p1_z.outputs[0], d1h.outputs[0])
    p2_z = _math(tree, "ADD", (bx - 1100, by - 600), p2_z.outputs[0], d2h.outputs[0])
    p2_placed = _position_piece(tree, (bx - 800, by - 520), p2.outputs["Mesh"],
                                x=0.0, y=0.0, z=p2_z.outputs[0])
    pag_join = safe_node(tree, "GeometryNodeJoinGeometry", (bx - 400, by - 320))
    link_sockets(tree, p1_placed, pag_join.inputs["Geometry"])
    link_sockets(tree, p2_placed, pag_join.inputs["Geometry"])

    # 3 -- clerestory (crown box + mini roof)
    cl = safe_node(tree, "GeometryNodeMeshCube", (bx - 1000, by - 760))
    cl_w = _math(tree, "MULTIPLY", (bx - 1200, by - 760), span.outputs[0], 0.45)
    cl_d = _math(tree, "MULTIPLY", (bx - 1200, by - 800), span.outputs[0], 0.35)
    cl_h = _math(tree, "MULTIPLY", (bx - 1200, by - 840), roof_h.outputs[0], 0.6)
    cl_size = _combine(tree, (bx - 1000, by - 840), cl_w.outputs[0], cl_d.outputs[0], cl_h.outputs[0])
    link_sockets(tree, cl_size.outputs["Vector"], cl.inputs["Size"])
    cl_z = _math(tree, "ADD", (bx - 1100, by - 880), wall_top,
                 _math(tree, "MULTIPLY", (bx - 1200, by - 880), cl_h.outputs[0], 0.5).outputs[0])
    cl_placed = _position_piece(tree, (bx - 800, by - 760), cl.outputs["Mesh"],
                                x=0.0, y=0.0, z=cl_z.outputs[0])
    cl_roof = safe_node(tree, "GeometryNodeMeshCone", (bx - 1000, by - 960))
    cl_roof.inputs["Vertices"].default_value = 4
    cr_r = _math(tree, "MULTIPLY", (bx - 1200, by - 960), span.outputs[0], 0.2)
    link_sockets(tree, cr_r.outputs[0], cl_roof.inputs["Radius Bottom"])
    cr_h = _math(tree, "MULTIPLY", (bx - 1200, by - 1000), roof_h.outputs[0], 0.3)
    link_sockets(tree, cr_h.outputs[0], cl_roof.inputs["Depth"])
    cr_z = _math(tree, "ADD", (bx - 1100, by - 1000), cl_z.outputs[0],
                 _math(tree, "MULTIPLY", (bx - 1200, by - 1000), cl_h.outputs[0], 0.5).outputs[0])
    cr_placed = _position_piece(tree, (bx - 800, by - 960), cl_roof.outputs["Mesh"],
                                x=0.0, y=0.0, z=cr_z.outputs[0])
    cl_join = safe_node(tree, "GeometryNodeJoinGeometry", (bx - 400, by - 760))
    link_sockets(tree, cl_placed, cl_join.inputs["Geometry"])
    link_sockets(tree, cr_placed, cl_join.inputs["Geometry"])

    return _select_mode(tree, gin.outputs["Roof Mode"],
                        hip_tx.outputs["Geometry"],
                        onion_join.outputs["Geometry"],
                        pag_join.outputs["Geometry"],
                        cl_join.outputs["Geometry"],
                        (bx + 200, by))


# ---------------------------------------------------------------------------
# Mode 1 -- PAVILION
# ---------------------------------------------------------------------------

def _build_pavilion(tree, gin, loc):
    """Tea-house / festival stall pavilion with tiered roof and awning."""
    bx, by = loc

    plat = safe_node(tree, "GeometryNodeMeshCube", (bx - 600, by))
    plat_w = _math(tree, "ADD", (bx - 800, by), gin.outputs["Pavilion Width"], 0.9)
    plat_d = _math(tree, "ADD", (bx - 800, by - 60), gin.outputs["Pavilion Depth"], 0.9)
    plat_size = _combine(tree, (bx - 800, by - 120), plat_w.outputs[0], plat_d.outputs[0], 0.15)
    link_sockets(tree, plat_size.outputs["Vector"], plat.inputs["Size"])
    plat_out = _position_piece(tree, (bx - 400, by), plat.outputs["Mesh"],
                               x=0.0, y=0.0, z=0.04)
    pieces = [plat_out]

    # Engawa step (zen teahouse language) - thinner inner floor above the deck
    engawa = safe_node(tree, "GeometryNodeMeshCube", (bx - 600, by + 160))
    eng_size = _combine(tree, (bx - 800, by + 160),
                        gin.outputs["Pavilion Width"], gin.outputs["Pavilion Depth"], 0.06)
    link_sockets(tree, eng_size.outputs["Vector"], engawa.inputs["Size"])
    eng_out = _position_piece(tree, (bx - 400, by + 160), engawa.outputs["Mesh"],
                              x=0.0, y=0.0, z=0.11)
    pieces.append(eng_out)

    # corner posts
    grid = safe_node(tree, "GeometryNodeMeshGrid", (bx - 800, by - 200))
    grid.inputs["Vertices X"].default_value = 2
    grid.inputs["Vertices Y"].default_value = 2
    link_sockets(tree, gin.outputs["Pavilion Width"], grid.inputs["Size X"])
    link_sockets(tree, gin.outputs["Pavilion Depth"], grid.inputs["Size Y"])
    post = safe_node(tree, "GeometryNodeMeshCylinder", (bx - 600, by - 200))
    link_sockets(tree, gin.outputs["Column Radius"], post.inputs["Radius"])
    post.inputs["Depth"].default_value = 1.0
    post.inputs["Vertices"].default_value = 10
    inst = safe_node(tree, "GeometryNodeInstanceOnPoints", (bx - 400, by - 200))
    link_sockets(tree, grid.outputs["Mesh"], inst.inputs["Points"])
    link_sockets(tree, post.outputs["Mesh"], inst.inputs["Instance"])
    scale = safe_node(tree, "GeometryNodeScaleInstances", (bx - 200, by - 200))
    link_sockets(tree, inst.outputs["Instances"], scale.inputs["Instances"])
    link_float_to_vector(tree, gin.outputs["Column Height"], scale, "Scale",
                         component=2, defaults=(1.0, 1.0, 0.0))
    realize = safe_node(tree, "GeometryNodeRealizeInstances", (bx, by - 200))
    link_sockets(tree, scale.outputs["Instances"], realize.inputs["Geometry"])
    post_z = _math(tree, "MULTIPLY", (bx - 200, by - 260), gin.outputs["Column Height"], 0.5)
    posts_placed = _position_piece(tree, (bx + 200, by - 200), realize.outputs["Geometry"],
                                   x=0.0, y=0.0, z=post_z.outputs[0])
    pieces.append(posts_placed)

    # tiered roof (up to 3 tiers, gated by Tier Count)
    roof_parts = []
    roof_top = _math(tree, "ADD", (bx - 1000, by - 420), gin.outputs["Column Height"], 0.15)
    for tier in range(3):
        t = safe_node(tree, "GeometryNodeMeshCone", (bx - 800, by - 420 + tier * -180))
        t.inputs["Vertices"].default_value = 8
        shrink = 0.62 ** tier
        r_b = _math(tree, "MULTIPLY", (bx - 1000, by - 420 + tier * -180),
                    gin.outputs["Pavilion Width"], 0.5 * shrink)
        r_b = _math(tree, "ADD", (bx - 900, by - 420 + tier * -180), r_b.outputs[0], gin.outputs["Overhang"])
        r_t = _math(tree, "MULTIPLY", (bx - 1000, by - 460 + tier * -180), r_b.outputs[0], 0.55)
        d = _math(tree, "MULTIPLY", (bx - 1000, by - 500 + tier * -180),
                  gin.outputs["Column Height"], 0.35 * shrink)
        link_sockets(tree, r_b.outputs[0], t.inputs["Radius Bottom"])
        link_sockets(tree, r_t.outputs[0], t.inputs["Radius Top"])
        link_sockets(tree, d.outputs[0], t.inputs["Depth"])
        d_half = _math(tree, "MULTIPLY", (bx - 900, by - 540 + tier * -180), d.outputs[0], 0.5)
        z = _math(tree, "ADD", (bx - 800, by - 540 + tier * -180), roof_top.outputs[0], d_half.outputs[0])
        placed = _position_piece(tree, (bx - 600, by - 420 + tier * -180), t.outputs["Mesh"],
                                 x=0.0, y=0.0, z=z.outputs[0])
        show = safe_node(tree, "GeometryNodeSwitch", (bx - 400, by - 420 + tier * -180))
        show.input_type = "GEOMETRY"
        link_sockets(tree, placed, show.inputs["True"])
        if tier > 0:
            gate = safe_node(tree, "FunctionNodeCompare", (bx - 600, by - 480 + tier * -180))
            gate.data_type = "INT"
            gate.operation = "GREATER_THAN"
            link_sockets(tree, gin.outputs["Tier Count"], gate.inputs["A"])
            gate.inputs["B"].default_value = tier
            link_sockets(tree, gate.outputs["Result"], show.inputs["Switch"])
        else:
            show.inputs["Switch"].default_value = True
        roof_parts.append(show.outputs["Output"])
        roof_top = _math(tree, "ADD", (bx - 900, by - 560 + tier * -180), roof_top.outputs[0], d.outputs[0])
    fin = safe_node(tree, "GeometryNodeMeshCone", (bx - 600, by - 1100))
    fin.inputs["Radius Bottom"].default_value = 0.1
    fin.inputs["Depth"].default_value = 0.35
    fin.inputs["Vertices"].default_value = 8
    fin_z = _math(tree, "ADD", (bx - 800, by - 1100), roof_top.outputs[0], 0.25)
    fin_placed = _position_piece(tree, (bx - 400, by - 1100), fin.outputs["Mesh"],
                                 x=0.0, y=0.0, z=fin_z.outputs[0])
    roof_parts.append(fin_placed)
    roof_join = safe_node(tree, "GeometryNodeJoinGeometry", (bx - 200, by - 420))
    for rp in roof_parts:
        link_sockets(tree, rp, roof_join.inputs["Geometry"])
    pieces.append(roof_join.outputs["Geometry"])

    # awning
    awning = safe_node(tree, "GeometryNodeSwitch", (bx - 600, by - 1240))
    awning.input_type = "GEOMETRY"
    link_sockets(tree, gin.outputs["Awning"], awning.inputs["Switch"])
    aw = safe_node(tree, "GeometryNodeMeshCube", (bx - 800, by - 1240))
    aw_w = _math(tree, "MULTIPLY", (bx - 1000, by - 1240), gin.outputs["Pavilion Width"], 0.85)
    aw_size = _combine(tree, (bx - 1000, by - 1300), aw_w.outputs[0], 0.6, 0.06)
    link_sockets(tree, aw_size.outputs["Vector"], aw.inputs["Size"])
    aw_y = _math(tree, "ADD", (bx - 1000, by - 1340), gin.outputs["Pavilion Depth"], 0.5)
    aw_z = _math(tree, "MULTIPLY", (bx - 1000, by - 1380), gin.outputs["Column Height"], 0.75)
    aw_placed = _position_piece(tree, (bx - 600, by - 1240), aw.outputs["Mesh"],
                                x=0.0, y=aw_y.outputs[0], z=aw_z.outputs[0])
    aw_tilt = safe_node(tree, "GeometryNodeTransform", (bx - 400, by - 1240))
    link_sockets(tree, aw_placed, aw_tilt.inputs["Geometry"])
    aw_tilt.inputs["Rotation"].default_value[0] = -0.35
    link_sockets(tree, aw_tilt.outputs["Geometry"], awning.inputs["True"])
    pieces.append(awning.outputs["Output"])

    # counter
    counter = safe_node(tree, "GeometryNodeSwitch", (bx - 600, by - 1420))
    counter.input_type = "GEOMETRY"
    link_sockets(tree, gin.outputs["Counter"], counter.inputs["Switch"])
    ct = safe_node(tree, "GeometryNodeMeshCube", (bx - 800, by - 1420))
    ct_w = _math(tree, "MULTIPLY", (bx - 1000, by - 1420), gin.outputs["Pavilion Width"], 0.75)
    ct_size = _combine(tree, (bx - 1000, by - 1480), ct_w.outputs[0], 0.5, 0.9)
    link_sockets(tree, ct_size.outputs["Vector"], ct.inputs["Size"])
    ct_y = _math(tree, "MULTIPLY", (bx - 1000, by - 1520), gin.outputs["Pavilion Depth"], 0.35)
    ct_out = _position_piece(tree, (bx - 600, by - 1420), ct.outputs["Mesh"],
                             x=0.0, y=ct_y.outputs[0], z=0.45)
    link_sockets(tree, ct_out, counter.inputs["True"])
    pieces.append(counter.outputs["Output"])

    # cushions
    cush = safe_node(tree, "GeometryNodeSwitch", (bx - 600, by - 1600))
    cush.input_type = "GEOMETRY"
    link_sockets(tree, gin.outputs["Cushions"], cush.inputs["Switch"])
    c_line = safe_node(tree, "GeometryNodeMeshLine", (bx - 800, by - 1600))
    c_line.mode = "OFFSET"
    c_line.inputs["Count"].default_value = 2
    c_off = _math(tree, "MULTIPLY", (bx - 1000, by - 1600), gin.outputs["Pavilion Width"], 0.25)
    c_start = _combine(tree, (bx - 1000, by - 1640), 0.0, 0.0, 0.21)
    c_offv = _combine(tree, (bx - 1000, by - 1680), c_off.outputs[0], 0.0, 0.0)
    link_sockets(tree, c_start.outputs["Vector"], c_line.inputs["Start Location"])
    link_sockets(tree, c_offv.outputs["Vector"], c_line.inputs["Offset"])
    cush_geom = _instance_box(tree, (bx - 600, by - 1600), (0.45, 0.45, 0.12),
                              c_line.outputs["Mesh"])
    link_sockets(tree, cush_geom, cush.inputs["True"])
    pieces.append(cush.outputs["Output"])

    join = safe_node(tree, "GeometryNodeJoinGeometry", (bx + 400, by - 200))
    for p in pieces:
        link_sockets(tree, p, join.inputs["Geometry"])
    return join.outputs["Geometry"]


# ---------------------------------------------------------------------------
# Mode 2 -- SPIRE
# ---------------------------------------------------------------------------

def _build_spire(tree, gin, loc):
    """Whimsical tapered tower for skylines and floating islands."""
    bx, by = loc
    pieces = []

    # floating base (inverted cone under the body)
    fb = safe_node(tree, "GeometryNodeSwitch", (bx - 600, by - 200))
    fb.input_type = "GEOMETRY"
    link_sockets(tree, gin.outputs["Floating Base"], fb.inputs["Switch"])
    base = safe_node(tree, "GeometryNodeMeshCone", (bx - 800, by - 200))
    base.inputs["Vertices"].default_value = 8
    br = _math(tree, "MULTIPLY", (bx - 1000, by - 200), gin.outputs["Base Radius"], 1.15)
    link_sockets(tree, br.outputs[0], base.inputs["Radius Bottom"])
    base.inputs["Depth"].default_value = 1.2
    base_tx = safe_node(tree, "GeometryNodeTransform", (bx - 600, by - 200))
    link_sockets(tree, base.outputs["Mesh"], base_tx.inputs["Geometry"])
    base_tx.inputs["Rotation"].default_value[0] = 3.14159
    base_z = _math(tree, "MULTIPLY", (bx - 1000, by - 260), gin.outputs["Base Radius"], -0.6)
    base_placed = _position_piece(tree, (bx - 400, by - 200), base_tx.outputs["Geometry"],
                                  x=0.0, y=0.0, z=base_z.outputs[0])
    link_sockets(tree, base_placed, fb.inputs["True"])
    pieces.append(fb.outputs["Output"])

    # stacked tapered sections (up to 4, gated by Section Count)
    sec_count = _math(tree, "MAXIMUM", (bx - 1200, by), gin.outputs["Section Count"], 1)
    sec_h = _math(tree, "DIVIDE", (bx - 1000, by), gin.outputs["Spire Height"], sec_count.outputs[0])
    sections = []
    for i in range(4):
        t = i * -180
        cyl = safe_node(tree, "GeometryNodeMeshCylinder", (bx - 800, by - 120 + t))
        cyl.inputs["Vertices"].default_value = 12
        i_f = _math(tree, "MULTIPLY", (bx - 1200, by - 160 + t), i * 1.0, 1.0)
        taper_i = _math(tree, "MULTIPLY", (bx - 1100, by - 160 + t), gin.outputs["Spire Taper"], i_f.outputs[0])
        frac = _math(tree, "DIVIDE", (bx - 1000, by - 160 + t), taper_i.outputs[0], sec_count.outputs[0])
        one_minus = _math(tree, "SUBTRACT", (bx - 1100, by - 200 + t), 1.0, frac.outputs[0])
        r = _math(tree, "MULTIPLY", (bx - 1000, by - 200 + t), gin.outputs["Base Radius"], one_minus.outputs[0])
        link_sockets(tree, r.outputs[0], cyl.inputs["Radius"])
        link_sockets(tree, sec_h.outputs[0], cyl.inputs["Depth"])
        z = _math(tree, "MULTIPLY", (bx - 1000, by - 280 + t), sec_h.outputs[0], i + 0.5)
        placed = _position_piece(tree, (bx - 600, by - 120 + t), cyl.outputs["Mesh"],
                                 x=0.0, y=0.0, z=z.outputs[0])
        show = safe_node(tree, "GeometryNodeSwitch", (bx - 400, by - 120 + t))
        show.input_type = "GEOMETRY"
        link_sockets(tree, placed, show.inputs["True"])
        if i > 0:
            gate = safe_node(tree, "FunctionNodeCompare", (bx - 600, by - 180 + t))
            gate.data_type = "INT"
            gate.operation = "GREATER_THAN"
            link_sockets(tree, gin.outputs["Section Count"], gate.inputs["A"])
            gate.inputs["B"].default_value = i
            link_sockets(tree, gate.outputs["Result"], show.inputs["Switch"])
        else:
            show.inputs["Switch"].default_value = True
        sections.append(show.outputs["Output"])
        # ring lip between sections
        if i < 3:
            lip = safe_node(tree, "GeometryNodeSwitch", (bx - 600, by - 60 + t))
            lip.input_type = "GEOMETRY"
            link_sockets(tree, gin.outputs["Rings"], lip.inputs["Switch"])
            lcyl = safe_node(tree, "GeometryNodeMeshCylinder", (bx - 800, by - 60 + t))
            lcyl.inputs["Vertices"].default_value = 12
            lr = _math(tree, "ADD", (bx - 1000, by - 60 + t), r.outputs[0], 0.08)
            link_sockets(tree, lr.outputs[0], lcyl.inputs["Radius"])
            lcyl.inputs["Depth"].default_value = 0.12
            lz = _math(tree, "MULTIPLY", (bx - 1000, by - 100 + t), sec_h.outputs[0], i + 1)
            lip_placed = _position_piece(tree, (bx - 400, by - 60 + t), lcyl.outputs["Mesh"],
                                         x=0.0, y=0.0, z=lz.outputs[0])
            link_sockets(tree, lip_placed, lip.inputs["True"])
            sections.append(lip.outputs["Output"])
    section_join = safe_node(tree, "GeometryNodeJoinGeometry", (bx + 100, by - 120))
    for s in sections:
        link_sockets(tree, s, section_join.inputs["Geometry"])
    pieces.append(section_join.outputs["Geometry"])

    # window band along one face
    wb = safe_node(tree, "GeometryNodeSwitch", (bx - 600, by - 980))
    wb.input_type = "GEOMETRY"
    link_sockets(tree, gin.outputs["Window Band"], wb.inputs["Switch"])
    w_line = safe_node(tree, "GeometryNodeMeshLine", (bx - 800, by - 980))
    w_line.mode = "OFFSET"
    w_line.inputs["Count"].default_value = 5
    w_off = _math(tree, "MULTIPLY", (bx - 1000, by - 980), gin.outputs["Spire Height"], 0.2)
    w_offv = _combine(tree, (bx - 1000, by - 1020), 0.0, 0.0, w_off.outputs[0])
    link_sockets(tree, w_offv.outputs["Vector"], w_line.inputs["Offset"])
    w_r = _math(tree, "MULTIPLY", (bx - 1000, by - 1060), gin.outputs["Base Radius"], 0.85)
    w_start = _combine(tree, (bx - 1000, by - 1100), 0.0, w_r.outputs[0], 0.9)
    link_sockets(tree, w_start.outputs["Vector"], w_line.inputs["Start Location"])
    w_geom = _instance_box(tree, (bx - 600, by - 980), (0.35, 0.12, 0.9), w_line.outputs["Mesh"])
    link_sockets(tree, w_geom, wb.inputs["True"])
    pieces.append(wb.outputs["Output"])

    # top modes: 0=cone, 1=onion, 2=star
    top_cone = safe_node(tree, "GeometryNodeMeshCone", (bx - 800, by - 1260))
    top_cone.inputs["Vertices"].default_value = 8
    tr = _math(tree, "MULTIPLY", (bx - 1000, by - 1260), gin.outputs["Base Radius"], 0.35)
    link_sockets(tree, tr.outputs[0], top_cone.inputs["Radius Bottom"])
    th = _math(tree, "MULTIPLY", (bx - 1000, by - 1300), gin.outputs["Spire Height"], 0.2)
    link_sockets(tree, th.outputs[0], top_cone.inputs["Depth"])
    tz = _math(tree, "ADD", (bx - 1000, by - 1340), gin.outputs["Spire Height"],
               _math(tree, "MULTIPLY", (bx - 1100, by - 1340), th.outputs[0], 0.5).outputs[0])
    top_placed = _position_piece(tree, (bx - 600, by - 1260), top_cone.outputs["Mesh"],
                                 x=0.0, y=0.0, z=tz.outputs[0])

    top_onion = safe_node(tree, "GeometryNodeMeshUVSphere", (bx - 800, by - 1440))
    top_onion.inputs["Segments"].default_value = 20
    top_onion.inputs["Rings"].default_value = 10
    or_ = _math(tree, "MULTIPLY", (bx - 1000, by - 1440), gin.outputs["Base Radius"], 0.3)
    link_sockets(tree, or_.outputs[0], top_onion.inputs["Radius"])
    o_scale = _combine(tree, (bx - 800, by - 1520), 1.0, 1.0, 0.7)
    o_tx = safe_node(tree, "GeometryNodeTransform", (bx - 600, by - 1440))
    link_sockets(tree, top_onion.outputs["Mesh"], o_tx.inputs["Geometry"])
    link_sockets(tree, o_scale.outputs["Vector"], o_tx.inputs["Scale"])
    oz = _math(tree, "ADD", (bx - 1000, by - 1480), gin.outputs["Spire Height"], 0.3)
    onion_placed = _position_piece(tree, (bx - 400, by - 1440), o_tx.outputs["Geometry"],
                                   x=0.0, y=0.0, z=oz.outputs[0])

    star = safe_node(tree, "GeometryNodeMeshCone", (bx - 800, by - 1600))
    star.inputs["Vertices"].default_value = 5
    star.inputs["Radius Bottom"].default_value = 0.16
    star.inputs["Radius Top"].default_value = 0.0
    star.inputs["Depth"].default_value = 0.45
    star_z = _math(tree, "ADD", (bx - 1000, by - 1600), gin.outputs["Spire Height"], 1.1)
    star_placed = _position_piece(tree, (bx - 600, by - 1600), star.outputs["Mesh"],
                                  x=0.0, y=0.0, z=star_z.outputs[0])

    top_sel = _select_mode(tree, gin.outputs["Top Mode"],
                           top_placed, onion_placed, star_placed, top_placed,
                           (bx + 100, by - 1300))
    pieces.append(top_sel)

    join = safe_node(tree, "GeometryNodeJoinGeometry", (bx + 500, by - 200))
    for p in pieces:
        link_sockets(tree, p, join.inputs["Geometry"])
    return join.outputs["Geometry"]


# ---------------------------------------------------------------------------
# Mode 3 -- RUIN
# ---------------------------------------------------------------------------

def _build_ruin(tree, gin, loc):
    """Broken quarter wall / ruin with lean, rubble, and column stumps."""
    bx, by = loc
    pieces = []

    thk = _math(tree, "MAXIMUM", (bx - 1000, by),
                _math(tree, "MULTIPLY", (bx - 1100, by), gin.outputs["Ruin Depth"], 0.18).outputs[0],
                0.3)
    break_frac = _math(tree, "DIVIDE", (bx - 1000, by - 40),
                       _math(tree, "ADD", (bx - 1100, by - 40), gin.outputs["Wall Break"], 1.0).outputs[0],
                       3.0)
    break_frac = _math(tree, "MAXIMUM", (bx - 1100, by - 40), break_frac.outputs[0], 0.2)

    # front wall left slab
    wall_a_w = _math(tree, "SUBTRACT", (bx - 1000, by - 80), gin.outputs["Ruin Width"],
                     _math(tree, "MULTIPLY", (bx - 1100, by - 80),
                           gin.outputs["Ruin Width"], break_frac.outputs[0]).outputs[0])
    wall_a = safe_node(tree, "GeometryNodeMeshCube", (bx - 800, by - 80))
    wall_a_size = _combine(tree, (bx - 1000, by - 120), wall_a_w.outputs[0], thk.outputs[0],
                           gin.outputs["Ruin Height"])
    link_sockets(tree, wall_a_size.outputs["Vector"], wall_a.inputs["Size"])
    wall_a_x = _math(tree, "MULTIPLY", (bx - 1100, by - 160), wall_a_w.outputs[0], -0.5)
    wall_a_z = _math(tree, "MULTIPLY", (bx - 1100, by - 200), gin.outputs["Ruin Height"], 0.5)
    wall_a_placed = _position_piece(tree, (bx - 600, by - 80), wall_a.outputs["Mesh"],
                                    x=wall_a_x.outputs[0], y=0.0, z=wall_a_z.outputs[0])

    # front wall right slab (broken)
    wall_b_w = _math(tree, "MULTIPLY", (bx - 1000, by - 240), gin.outputs["Ruin Width"], break_frac.outputs[0])
    wall_b_h = _math(tree, "MULTIPLY", (bx - 1000, by - 240), gin.outputs["Ruin Height"],
                     _math(tree, "SUBTRACT", (bx - 1100, by - 240), 1.0, break_frac.outputs[0]).outputs[0])
    wall_b = safe_node(tree, "GeometryNodeMeshCube", (bx - 800, by - 240))
    wall_b_size = _combine(tree, (bx - 1000, by - 280), wall_b_w.outputs[0], thk.outputs[0], wall_b_h.outputs[0])
    link_sockets(tree, wall_b_size.outputs["Vector"], wall_b.inputs["Size"])
    wall_b_x = _math(tree, "MULTIPLY", (bx - 1100, by - 320), gin.outputs["Ruin Width"], 0.5)
    wall_b_x = _math(tree, "SUBTRACT", (bx - 1000, by - 320), wall_b_x.outputs[0],
                     _math(tree, "MULTIPLY", (bx - 1100, by - 320), wall_b_w.outputs[0], 0.5).outputs[0])
    wall_b_z = _math(tree, "MULTIPLY", (bx - 1100, by - 360), wall_b_h.outputs[0], 0.5)
    wall_b_placed = _position_piece(tree, (bx - 600, by - 240), wall_b.outputs["Mesh"],
                                    x=wall_b_x.outputs[0], y=0.0, z=wall_b_z.outputs[0])

    # lean the whole front wall assembly
    front_join = safe_node(tree, "GeometryNodeJoinGeometry", (bx - 400, by - 240))
    link_sockets(tree, wall_a_placed, front_join.inputs["Geometry"])
    link_sockets(tree, wall_b_placed, front_join.inputs["Geometry"])
    lean = safe_node(tree, "GeometryNodeTransform", (bx - 200, by - 240))
    link_sockets(tree, front_join.outputs["Geometry"], lean.inputs["Geometry"])
    lean_rot = _math(tree, "MULTIPLY", (bx - 400, by - 320), gin.outputs["Lean"], 1.0)
    link_float_to_vector(tree, lean_rot.outputs[0], lean, "Rotation",
                         component=2, defaults=(0.0, 0.0, 0.0))
    pieces.append(lean.outputs["Geometry"])

    # side wall (back-left, lower)
    side = safe_node(tree, "GeometryNodeMeshCube", (bx - 800, by - 520))
    side_h = _math(tree, "MULTIPLY", (bx - 1000, by - 520), gin.outputs["Ruin Height"], 0.7)
    side_size = _combine(tree, (bx - 1000, by - 560), thk.outputs[0], gin.outputs["Ruin Depth"], side_h.outputs[0])
    link_sockets(tree, side_size.outputs["Vector"], side.inputs["Size"])
    side_x = _math(tree, "MULTIPLY", (bx - 1100, by - 600), gin.outputs["Ruin Width"], -0.5)
    side_z = _math(tree, "MULTIPLY", (bx - 1100, by - 640), side_h.outputs[0], 0.5)
    side_placed = _position_piece(tree, (bx - 600, by - 520), side.outputs["Mesh"],
                                  x=side_x.outputs[0], y=0.0, z=side_z.outputs[0])
    pieces.append(side_placed)

    # broken roof slab
    broof = safe_node(tree, "GeometryNodeSwitch", (bx - 600, by - 720))
    broof.input_type = "GEOMETRY"
    link_sockets(tree, gin.outputs["Broken Roof"], broof.inputs["Switch"])
    slab = safe_node(tree, "GeometryNodeMeshCube", (bx - 800, by - 720))
    slab_size = _combine(tree, (bx - 1000, by - 760),
                         gin.outputs["Ruin Width"], gin.outputs["Ruin Depth"], 0.08)
    link_sockets(tree, slab_size.outputs["Vector"], slab.inputs["Size"])
    slab_z = _math(tree, "MULTIPLY", (bx - 1000, by - 800), gin.outputs["Ruin Height"], 0.5)
    slab_y = _math(tree, "MULTIPLY", (bx - 1000, by - 840), gin.outputs["Ruin Depth"], 0.25)
    slab_placed = _position_piece(tree, (bx - 600, by - 720), slab.outputs["Mesh"],
                                  x=0.0, y=slab_y.outputs[0], z=slab_z.outputs[0])
    slab_tilt = safe_node(tree, "GeometryNodeTransform", (bx - 400, by - 720))
    link_sockets(tree, slab_placed, slab_tilt.inputs["Geometry"])
    slab_tilt.inputs["Rotation"].default_value[1] = 0.4
    slab_tilt.inputs["Rotation"].default_value[2] = -0.3
    link_sockets(tree, slab_tilt.outputs["Geometry"], broof.inputs["True"])
    pieces.append(broof.outputs["Output"])

    # rubble
    rub = safe_node(tree, "GeometryNodeSwitch", (bx - 600, by - 900))
    rub.input_type = "GEOMETRY"
    link_sockets(tree, gin.outputs["Rubble"], rub.inputs["Switch"])
    rub_parts = []
    for i, (rx, ry, rz, s) in enumerate(((0.35, 0.25, 0.22, 1.0),
                                         (-0.4, 0.1, 0.14, 0.6),
                                         (0.15, 0.35, 0.18, 0.8),
                                         (-0.15, -0.2, 0.12, 0.5))):
        rb = safe_node(tree, "GeometryNodeMeshCube", (bx - 800, by - 940 + i * -60))
        rb_size = _combine(tree, (bx - 1000, by - 960 + i * -60), s, s, s)
        link_sockets(tree, rb_size.outputs["Vector"], rb.inputs["Size"])
        r_z = _math(tree, "MULTIPLY", (bx - 1000, by - 980 + i * -60), rz, 0.5)
        rb_placed = _position_piece(tree, (bx - 600, by - 940 + i * -60), rb.outputs["Mesh"],
                                    x=rx, y=ry, z=r_z.outputs[0])
        rub_parts.append(rb_placed)
    rub_join = safe_node(tree, "GeometryNodeJoinGeometry", (bx - 400, by - 940))
    for rp in rub_parts:
        link_sockets(tree, rp, rub_join.inputs["Geometry"])
    link_sockets(tree, rub_join.outputs["Geometry"], rub.inputs["True"])
    pieces.append(rub.outputs["Output"])

    # column stumps
    stumps = safe_node(tree, "GeometryNodeSwitch", (bx - 600, by - 1120))
    stumps.input_type = "GEOMETRY"
    link_sockets(tree, gin.outputs["Column Stumps"], stumps.inputs["Switch"])
    stump_parts = []
    for i, sx in enumerate((-0.45, 0.45)):
        st = safe_node(tree, "GeometryNodeMeshCylinder", (bx - 800, by - 1160 + i * -80))
        st.inputs["Radius"].default_value = 0.12
        st.inputs["Depth"].default_value = 0.9
        st.inputs["Vertices"].default_value = 10
        sxv = _math(tree, "MULTIPLY", (bx - 1000, by - 1160 + i * -80), gin.outputs["Ruin Width"], sx)
        st_z = _math(tree, "ADD", (bx - 900, by - 1200 + i * -80),
                     _math(tree, "MULTIPLY", (bx - 1000, by - 1200 + i * -80), sx, 0.3).outputs[0],
                     0.45)
        st_placed = _position_piece(tree, (bx - 600, by - 1160 + i * -80), st.outputs["Mesh"],
                                    x=sxv.outputs[0], y=0.0, z=st_z.outputs[0])
        stump_parts.append(st_placed)
    stump_join = safe_node(tree, "GeometryNodeJoinGeometry", (bx - 400, by - 1160))
    for sp in stump_parts:
        link_sockets(tree, sp, stump_join.inputs["Geometry"])
    link_sockets(tree, stump_join.outputs["Geometry"], stumps.inputs["True"])
    pieces.append(stumps.outputs["Output"])

    join = safe_node(tree, "GeometryNodeJoinGeometry", (bx + 300, by - 300))
    for p in pieces:
        link_sockets(tree, p, join.inputs["Geometry"])
    return join.outputs["Geometry"]


# ---------------------------------------------------------------------------
# Master builder
# ---------------------------------------------------------------------------

def build_nikki_quarter(group_name="MEL_nikki_quarter"):
    """Nikki Flora Quarter -- comprehensive Infinity Nikki themed architecture.

    Modes: 0=Townhouse, 1=Pavilion, 2=Spire, 3=Ruin. All parameters are
    editable named inputs; shared Variation + Seed drive a subtle wobble.
    """
    tree, gin, gout = new_geometry_tree(group_name)
    bx, by = 0, 0

    add_int_param(tree, "Mode", 0, 0, 3)
    add_float_param(tree, "Variation", 0.3, 0.0, 1.0)
    add_int_param(tree, "Seed", 7, 0, 9999)

    # -- townhouse params -----------------------------------------------------
    add_float_param(tree, "Width", 4.0, 2.0, 8.0)
    add_float_param(tree, "Depth", 3.5, 1.5, 6.0)
    add_int_param(tree, "Floors", 3, 1, 4)
    add_float_param(tree, "Floor Height", 2.7, 1.8, 3.5)
    add_int_param(tree, "Window Count", 3, 1, 5)
    add_int_param(tree, "Roof Mode", 0, 0, 3)
    add_float_param(tree, "Roof Pitch", 0.7, 0.2, 1.5)
    add_float_param(tree, "Eave Overhang", 0.45, 0.1, 1.2)
    add_bool_param(tree, "Bay Window", True)
    add_bool_param(tree, "Balcony", True)
    add_bool_param(tree, "Flower Boxes", True)
    add_bool_param(tree, "Chimney", True)
    add_bool_param(tree, "Lantern", True)
    add_bool_param(tree, "Porch", True)
    add_bool_param(tree, "Trim Cornice", True)

    # -- pavilion params -------------------------------------------------------
    add_float_param(tree, "Pavilion Width", 5.0, 2.0, 10.0)
    add_float_param(tree, "Pavilion Depth", 4.0, 2.0, 8.0)
    add_float_param(tree, "Column Height", 3.0, 2.0, 5.0)
    add_float_param(tree, "Column Radius", 0.07, 0.03, 0.2)
    add_float_param(tree, "Overhang", 0.6, 0.2, 1.5)
    add_int_param(tree, "Tier Count", 2, 1, 3)
    add_bool_param(tree, "Awning", True)
    add_bool_param(tree, "Counter", True)
    add_bool_param(tree, "Cushions", True)

    # -- spire params ----------------------------------------------------------
    add_float_param(tree, "Base Radius", 1.2, 0.5, 3.0)
    add_float_param(tree, "Spire Height", 9.0, 4.0, 20.0)
    add_float_param(tree, "Spire Taper", 0.6, 0.2, 1.0)
    add_int_param(tree, "Section Count", 3, 2, 6)
    add_int_param(tree, "Top Mode", 0, 0, 2)
    add_bool_param(tree, "Rings", True)
    add_bool_param(tree, "Window Band", True)
    add_bool_param(tree, "Floating Base", True)

    # -- ruin params -----------------------------------------------------------
    add_float_param(tree, "Ruin Width", 4.5, 2.0, 8.0)
    add_float_param(tree, "Ruin Depth", 2.5, 1.5, 5.0)
    add_float_param(tree, "Ruin Height", 4.0, 2.0, 8.0)
    add_int_param(tree, "Wall Break", 1, 0, 2)
    add_float_param(tree, "Lean", 0.15, 0.0, 0.6)
    add_bool_param(tree, "Broken Roof", True)
    add_bool_param(tree, "Rubble", True)
    add_bool_param(tree, "Column Stumps", True)

    geo_town = _build_townhouse(tree, gin, (bx - 1600, by + 900))
    geo_pav = _build_pavilion(tree, gin, (bx - 1600, by - 600))
    geo_spire = _build_spire(tree, gin, (bx - 1600, by - 2300))
    geo_ruin = _build_ruin(tree, gin, (bx - 1600, by - 3700))

    selected = _select_mode(tree, gin.outputs["Mode"],
                            geo_town, geo_pav, geo_spire, geo_ruin,
                            (bx + 1200, by))

    wobbled = _add_wobble(tree, selected, gin.outputs["Variation"],
                          gin.outputs["Seed"], (bx + 1900, by))

    shade = safe_node(tree, "GeometryNodeSetShadeSmooth", (bx + 2600, by))
    shade.inputs["Shade Smooth"].default_value = True
    link_sockets(tree, wobbled, shade.inputs["Geometry"])
    link_sockets(tree, shade.outputs["Geometry"], gout.inputs["Geometry"])

    color_node(shade, "geometry")
    color_node(selected, "instance")

    return label_tree(tree, "MEL_nikki_quarter", [
        {"title": "Inputs", "nodes": ("Group Input",), "role": "input"},
        {"title": "Townhouse", "nodes": ("floor", "window", "roof", "door"), "role": "geometry"},
        {"title": "Pavilion", "nodes": ("platform", "post", "awning"), "role": "instance"},
        {"title": "Spire", "nodes": ("section", "ring", "finial", "base"), "role": "geometry"},
        {"title": "Ruin", "nodes": ("wall", "lean", "rubble", "stump"), "role": "attribute"},
        {"title": "Selection", "nodes": ("switch", "compare"), "role": "instance"},
        {"title": "Output", "nodes": ("shade", "Group Output"), "role": "output"},
    ])


# -- Registry --------------------------------------------------------------
from .core import register_builder

register_builder(
    "MEL_nikki_quarter",
    build_nikki_quarter,
    "Nikki Flora Quarter",
    "Infinity Nikki themed architecture: townhouse, pavilion, spire, ruin "
    "with fully editable parameters (roofs, dressing toggles, variation).",
    "structures",
)
