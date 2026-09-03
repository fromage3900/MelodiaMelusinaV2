"""Celestial Dream Observatory -- HERO GN builder.

A breathtaking Nikki-style floating observatory: a floating island
(squashed sphere + inverted cone underside + hanging root clusters),
a gilded drum with window band, a dome with ring band, and a tilted
celestial ORRERY of rings and planets orbiting above the dome, finished
with hanging lanterns, a deck railing, and a star finial. Built for hero
silhouettes in the Dreamstate and KaleidoNave levels.

Every parameter is an editable named input on the node group.
"""

from __future__ import annotations

import bpy

from .core import (
    safe_node, link_sockets, link_float_to_vector, color_node, label_tree,
    new_geometry_tree, add_float_param, add_int_param, add_bool_param,
)


def _math(tree, operation, loc, a=None, b=None):
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
	transform = safe_node(tree, "GeometryNodeTransform", loc)
	link_sockets(tree, geometry_sock, transform.inputs["Geometry"])
	if x is not None or y is not None or z is not None:
		pos = _combine(tree, (loc[0] - 200, loc[1] - 120), x, y, z)
		link_sockets(tree, pos.outputs["Vector"], transform.inputs["Translation"])
	return transform.outputs["Geometry"]


def _add_wobble(tree, geometry_sock, variation_sock, seed_sock, loc):
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
    amp = _math(tree, "MULTIPLY", (loc[0] + 180, loc[1] - 260), variation_sock, 0.1)
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


def _ring(tree, loc, radius_sock, thickness):
    """A thin ring band: circle extruded along edges."""
    bx, by = loc
    circle = safe_node(tree, "GeometryNodeMeshCircle", (bx - 200, by))
    circle.inputs["Vertices"].default_value = 64
    circle.fill_type = "NONE"
    link_sockets(tree, radius_sock, circle.inputs["Radius"])
    extrude = safe_node(tree, "GeometryNodeExtrudeMesh", (bx, by))
    link_sockets(tree, circle.outputs["Mesh"], extrude.inputs["Mesh"])
    extrude.mode = "EDGES"
    extrude.inputs["Offset Scale"].default_value = thickness
    return extrude.outputs["Mesh"]


def _gate(tree, loc, geo_sock, count_sock, index):
    show = safe_node(tree, "GeometryNodeSwitch", loc)
    show.input_type = "GEOMETRY"
    link_sockets(tree, geo_sock, show.inputs["True"])
    gate = safe_node(tree, "FunctionNodeCompare", (loc[0] - 200, loc[1]))
    gate.data_type = "INT"
    gate.operation = "GREATER_THAN"
    link_sockets(tree, count_sock, gate.inputs["A"])
    gate.inputs["B"].default_value = index
    link_sockets(tree, gate.outputs["Result"], show.inputs["Switch"])
    return show.outputs["Output"]


def build_sky_observatory(group_name="MEL_sky_observatory"):
    """Celestial Dream Observatory -- floating island + dome + orrery.

    The signature hero silhouette: squashed island, gilded drum and dome,
    tilted orrery rings with planets, lanterns, deck railing, star finial.
    """
    tree, gin, gout = new_geometry_tree(group_name)
    bx, by = 0, 0

    add_float_param(tree, "Island Radius", 3.0, 1.5, 6.0)
    add_float_param(tree, "Island Height", 1.4, 0.6, 3.0)
    add_float_param(tree, "Drum Radius", 1.6, 0.8, 3.5)
    add_float_param(tree, "Drum Height", 2.6, 1.2, 5.0)
    add_float_param(tree, "Dome Radius", 1.8, 0.8, 4.0)
    add_int_param(tree, "Ring Count", 4, 0, 5)
    add_float_param(tree, "Ring Tilt", 18.0, 0.0, 45.0)
    add_bool_param(tree, "Planets", True)
    add_bool_param(tree, "Deck Railing", True)
    add_bool_param(tree, "Lanterns", True)
    add_bool_param(tree, "Star Finial", True)
    add_float_param(tree, "Wobble", 0.05, 0.0, 0.3)
    add_int_param(tree, "Seed", 7, 0, 9999)

    pieces = []

    # -- floating island -----------------------------------------------------
    island = safe_node(tree, "GeometryNodeMeshUVSphere", (bx - 900, by + 200))
    island.inputs["Segments"].default_value = 48
    island.inputs["Rings"].default_value = 24
    link_sockets(tree, gin.outputs["Island Radius"], island.inputs["Radius"])
    is_scale = _combine(tree, (bx - 1100, by + 120), 1.0, 1.0, 0.32)
    is_tx = safe_node(tree, "GeometryNodeTransform", (bx - 700, by + 200))
    link_sockets(tree, island.outputs["Mesh"], is_tx.inputs["Geometry"])
    link_sockets(tree, is_scale.outputs["Vector"], is_tx.inputs["Scale"])
    is_z = _math(tree, "MULTIPLY", (bx - 900, by + 60), gin.outputs["Island Radius"], 0.18)
    island_out = _position_piece(tree, (bx - 500, by + 200), is_tx.outputs["Geometry"],
                                 x=0.0, y=0.0, z=is_z.outputs[0])
    pieces.append(island_out)

    # underside cone
    under = safe_node(tree, "GeometryNodeMeshCone", (bx - 900, by))
    under.inputs["Vertices"].default_value = 24
    ur = _math(tree, "MULTIPLY", (bx - 1100, by), gin.outputs["Island Radius"], 0.85)
    link_sockets(tree, ur.outputs[0], under.inputs["Radius Bottom"])
    link_sockets(tree, gin.outputs["Island Height"], under.inputs["Depth"])
    under_tx = safe_node(tree, "GeometryNodeTransform", (bx - 700, by))
    link_sockets(tree, under.outputs["Mesh"], under_tx.inputs["Geometry"])
    under_tx.inputs["Rotation"].default_value[0] = 3.14159
    under_z = _math(tree, "MULTIPLY", (bx - 900, by - 80), gin.outputs["Island Height"], -0.5)
    under_out = _position_piece(tree, (bx - 500, by), under_tx.outputs["Geometry"],
                                x=0.0, y=0.0, z=under_z.outputs[0])
    pieces.append(under_out)

    # hanging root clusters around the island lip
    roots = safe_node(tree, "GeometryNodeMeshCircle", (bx - 900, by - 200))
    roots.inputs["Vertices"].default_value = 8
    roots.inputs["Radius"].default_value = 1.0
    roots.fill_type = "NONE"
    root_cone = safe_node(tree, "GeometryNodeMeshCone", (bx - 900, by - 320))
    root_cone.inputs["Vertices"].default_value = 6
    root_cone.inputs["Radius Bottom"].default_value = 0.18
    root_cone.inputs["Radius Top"].default_value = 0.0
    root_cone.inputs["Depth"].default_value = 0.9
    root_r = _math(tree, "MULTIPLY", (bx - 900, by - 260), gin.outputs["Island Radius"], 0.85)
    root_scale_r = _math(tree, "MULTIPLY", (bx - 900, by - 320), root_r.outputs[0], 0.6)
    root_scale = _combine(tree, (bx - 700, by - 320), root_scale_r.outputs[0], root_scale_r.outputs[0], 1.0)
    roots_tx = safe_node(tree, "GeometryNodeTransform", (bx - 700, by - 200))
    link_sockets(tree, roots.outputs["Mesh"], roots_tx.inputs["Geometry"])
    link_sockets(tree, root_scale.outputs["Vector"], roots_tx.inputs["Scale"])
    root_inst = safe_node(tree, "GeometryNodeInstanceOnPoints", (bx - 500, by - 200))
    link_sockets(tree, roots_tx.outputs["Geometry"], root_inst.inputs["Points"])
    link_sockets(tree, root_cone.outputs["Mesh"], root_inst.inputs["Instance"])
    root_real = safe_node(tree, "GeometryNodeRealizeInstances", (bx - 300, by - 200))
    link_sockets(tree, root_inst.outputs["Instances"], root_real.inputs["Geometry"])
    root_z = _math(tree, "MULTIPLY", (bx - 500, by - 260), gin.outputs["Island Radius"], 0.3)
    roots_out = _position_piece(tree, (bx - 100, by - 200), root_real.outputs["Geometry"],
                                x=0.0, y=0.0, z=root_z.outputs[0])
    pieces.append(roots_out)

    # -- observatory drum -----------------------------------------------------
    drum_z = _math(tree, "MULTIPLY", (bx - 900, by - 400), gin.outputs["Island Radius"], 0.2)
    drum = safe_node(tree, "GeometryNodeMeshCylinder", (bx - 900, by - 420))
    drum.inputs["Vertices"].default_value = 32
    link_sockets(tree, gin.outputs["Drum Radius"], drum.inputs["Radius"])
    link_sockets(tree, gin.outputs["Drum Height"], drum.inputs["Depth"])
    drum_center = _math(tree, "ADD", (bx - 900, by - 480), drum_z.outputs[0],
                        _math(tree, "MULTIPLY", (bx - 1000, by - 480),
                              gin.outputs["Drum Height"], 0.5).outputs[0])
    drum_out = _position_piece(tree, (bx - 700, by - 420), drum.outputs["Mesh"],
                               x=0.0, y=0.0, z=drum_center.outputs[0])
    pieces.append(drum_out)

    # gilded ring bands on the drum
    band_1 = _ring(tree, (bx - 900, by - 600), gin.outputs["Drum Radius"], 0.08)
    band_1r = _math(tree, "ADD", (bx - 1100, by - 600), gin.outputs["Drum Radius"], 0.05)
    band_1z = _math(tree, "MULTIPLY", (bx - 900, by - 640), gin.outputs["Drum Height"], 0.25)
    band_1z = _math(tree, "ADD", (bx - 800, by - 640), drum_z.outputs[0], band_1z.outputs[0])
    band_1o = _position_piece(tree, (bx - 700, by - 600), band_1,
                              x=0.0, y=0.0, z=band_1z.outputs[0])
    band_2z = _math(tree, "MULTIPLY", (bx - 900, by - 680), gin.outputs["Drum Height"], 0.75)
    band_2z = _math(tree, "ADD", (bx - 800, by - 680), drum_z.outputs[0], band_2z.outputs[0])
    band_2o = _position_piece(tree, (bx - 700, by - 680), _ring(tree, (bx - 900, by - 700),
                              gin.outputs["Drum Radius"], 0.08),
                              x=0.0, y=0.0, z=band_2z.outputs[0])
    pieces.append(band_1o)
    pieces.append(band_2o)

    # window band around the drum
    win_line = safe_node(tree, "GeometryNodeMeshLine", (bx - 900, by - 820))
    win_line.mode = "OFFSET"
    win_line.inputs["Count"].default_value = 5
    win_off = _math(tree, "DIVIDE", (bx - 1100, by - 820), gin.outputs["Drum Height"], 4.0)
    win_offv = _combine(tree, (bx - 1100, by - 860), 0.0, 0.0, win_off.outputs[0])
    link_sockets(tree, win_offv.outputs["Vector"], win_line.inputs["Offset"])
    win_r = _math(tree, "MULTIPLY", (bx - 1100, by - 900), gin.outputs["Drum Radius"], 0.7)
    win_start = _combine(tree, (bx - 1100, by - 940), 0.0, win_r.outputs[0], 0.3)
    link_sockets(tree, win_start.outputs["Vector"], win_line.inputs["Start Location"])
    win_box = safe_node(tree, "GeometryNodeMeshCube", (bx - 700, by - 820))
    win_size = _combine(tree, (bx - 900, by - 860), 0.45, 0.12, 0.8)
    link_sockets(tree, win_size.outputs["Vector"], win_box.inputs["Size"])
    win_inst = safe_node(tree, "GeometryNodeInstanceOnPoints", (bx - 500, by - 820))
    link_sockets(tree, win_line.outputs["Mesh"], win_inst.inputs["Points"])
    link_sockets(tree, win_box.outputs["Mesh"], win_inst.inputs["Instance"])
    win_real = safe_node(tree, "GeometryNodeRealizeInstances", (bx - 300, by - 820))
    link_sockets(tree, win_inst.outputs["Instances"], win_real.inputs["Geometry"])
    win_geo = _position_piece(tree, (bx - 100, by - 820), win_real.outputs["Geometry"],
                              x=0.0, y=0.0, z=drum_z.outputs[0])
    pieces.append(win_geo)

    # -- dome ------------------------------------------------------------------
    dome_base = _math(tree, "ADD", (bx - 900, by - 1000), drum_z.outputs[0],
                      gin.outputs["Drum Height"])
    dome = safe_node(tree, "GeometryNodeMeshUVSphere", (bx - 900, by - 1020))
    dome.inputs["Segments"].default_value = 48
    dome.inputs["Rings"].default_value = 24
    link_sockets(tree, gin.outputs["Dome Radius"], dome.inputs["Radius"])
    dome_scale = _combine(tree, (bx - 1100, by - 1100), 1.0, 1.0, 0.72)
    dome_tx = safe_node(tree, "GeometryNodeTransform", (bx - 700, by - 1020))
    link_sockets(tree, dome.outputs["Mesh"], dome_tx.inputs["Geometry"])
    link_sockets(tree, dome_scale.outputs["Vector"], dome_tx.inputs["Scale"])
    dome_z = _math(tree, "MULTIPLY", (bx - 900, by - 1060), gin.outputs["Dome Radius"], 0.36)
    dome_z = _math(tree, "ADD", (bx - 800, by - 1060), dome_base.outputs[0], dome_z.outputs[0])
    dome_out = _position_piece(tree, (bx - 500, by - 1020), dome_tx.outputs["Geometry"],
                               x=0.0, y=0.0, z=dome_z.outputs[0])
    pieces.append(dome_out)

    # dome base ring
    dome_ring = _ring(tree, (bx - 900, by - 1200), gin.outputs["Dome Radius"], 0.1)
    dome_ring_r = _math(tree, "ADD", (bx - 1100, by - 1200), gin.outputs["Dome Radius"], 0.06)
    dome_ring_o = _position_piece(tree, (bx - 700, by - 1200), dome_ring,
                                  x=0.0, y=0.0, z=dome_base.outputs[0])
    pieces.append(dome_ring_o)

    # star finial
    finial = safe_node(tree, "GeometryNodeSwitch", (bx - 700, by - 1300))
    finial.input_type = "GEOMETRY"
    link_sockets(tree, gin.outputs["Star Finial"], finial.inputs["Switch"])
    star = safe_node(tree, "GeometryNodeMeshCone", (bx - 900, by - 1300))
    star.inputs["Vertices"].default_value = 5
    star.inputs["Radius Bottom"].default_value = 0.18
    star.inputs["Radius Top"].default_value = 0.0
    star.inputs["Depth"].default_value = 0.5
    star_z = _math(tree, "ADD", (bx - 900, by - 1340), dome_z.outputs[0],
                   _math(tree, "MULTIPLY", (bx - 1000, by - 1340),
                         gin.outputs["Dome Radius"], 0.36).outputs[0])
    star_out = _position_piece(tree, (bx - 500, by - 1300), star.outputs["Mesh"],
                               x=0.0, y=0.0, z=star_z.outputs[0])
    link_sockets(tree, star_out, finial.inputs["True"])
    pieces.append(finial.outputs["Output"])

    # -- orrery rings ----------------------------------------------------------
    tilt_rad = _math(tree, "MULTIPLY", (bx - 1200, by - 1600), gin.outputs["Ring Tilt"], 0.0174533)
    orrery_parts = []
    for i in range(5):
        ring_r = _math(tree, "ADD", (bx - 1200, by - 1600 + i * -120),
                       _math(tree, "MULTIPLY", (bx - 1300, by - 1600 + i * -120),
                             gin.outputs["Dome Radius"], 1.15 + 0.5 * i).outputs[0], 0.0)
        ring_geo = _ring(tree, (bx - 1000, by - 1600 + i * -120), ring_r.outputs[0], 0.06)
        ring_tx = safe_node(tree, "GeometryNodeTransform", (bx - 800, by - 1600 + i * -120))
        link_sockets(tree, ring_geo, ring_tx.inputs["Geometry"])
        ring_tilt_i = _math(tree, "MULTIPLY", (bx - 1000, by - 1640 + i * -120),
                            tilt_rad.outputs[0], i * 1.0)
        link_float_to_vector(tree, ring_tilt_i.outputs[0], ring_tx, "Rotation",
                             component=0, defaults=(0.0, 0.0, 0.0))
        ring_z = _math(tree, "MULTIPLY", (bx - 1000, by - 1680 + i * -120),
                       gin.outputs["Dome Radius"], 0.1 * i)
        ring_z = _math(tree, "ADD", (bx - 900, by - 1680 + i * -120), dome_z.outputs[0],
                       ring_z.outputs[0])
        ring_placed = _position_piece(tree, (bx - 600, by - 1600 + i * -120),
                                      ring_tx.outputs["Geometry"],
                                      x=0.0, y=0.0, z=ring_z.outputs[0])
        orrery_parts.append(_gate(tree, (bx - 400, by - 1600 + i * -120), ring_placed,
                                  gin.outputs["Ring Count"], i))
    orrery_join = safe_node(tree, "GeometryNodeJoinGeometry", (bx, by - 1600))
    for rp in orrery_parts:
        link_sockets(tree, rp, orrery_join.inputs["Geometry"])
    pieces.append(orrery_join.outputs["Geometry"])

    # planets on the outer ring plane
    planets = safe_node(tree, "GeometryNodeSwitch", (bx - 600, by - 1900))
    planets.input_type = "GEOMETRY"
    link_sockets(tree, gin.outputs["Planets"], planets.inputs["Switch"])
    planet_parts = []
    for i, (ang, pr) in enumerate(((0.0, 0.16), (1.2, 0.12), (2.6, 0.2), (4.0, 0.14))):
        planet = safe_node(tree, "GeometryNodeMeshUVSphere", (bx - 800, by - 1900 + i * -80))
        planet.inputs["Segments"].default_value = 24
        planet.inputs["Rings"].default_value = 16
        planet.inputs["Radius"].default_value = pr
        pr_r = _math(tree, "MULTIPLY", (bx - 1000, by - 1900 + i * -80),
                     gin.outputs["Dome Radius"], 2.0)
        px = _math(tree, "MULTIPLY", (bx - 1000, by - 1940 + i * -80), pr_r.outputs[0],
                   _math(tree, "COSINE", (bx - 1100, by - 1940 + i * -80), ang, None).outputs[0])
        py = _math(tree, "MULTIPLY", (bx - 1000, by - 1980 + i * -80), pr_r.outputs[0],
                   _math(tree, "SINE", (bx - 1100, by - 1980 + i * -80), ang, None).outputs[0])
        pz = _math(tree, "ADD", (bx - 1000, by - 2020 + i * -80), dome_z.outputs[0], 0.4)
        planet_out = _position_piece(tree, (bx - 600, by - 1900 + i * -80), planet.outputs["Mesh"],
                                     x=px.outputs[0], y=py.outputs[0], z=pz.outputs[0])
        planet_parts.append(planet_out)
    planet_join = safe_node(tree, "GeometryNodeJoinGeometry", (bx - 400, by - 1900))
    for pp in planet_parts:
        link_sockets(tree, pp, planet_join.inputs["Geometry"])
    link_sockets(tree, planet_join.outputs["Geometry"], planets.inputs["True"])
    pieces.append(planets.outputs["Output"])

    # -- lanterns hanging from the outermost ring ----------------------------
    lanterns = safe_node(tree, "GeometryNodeSwitch", (bx - 600, by - 2150))
    lanterns.input_type = "GEOMETRY"
    link_sockets(tree, gin.outputs["Lanterns"], lanterns.inputs["Switch"])
    l_pts = safe_node(tree, "GeometryNodeMeshCircle", (bx - 800, by - 2150))
    l_pts.inputs["Vertices"].default_value = 8
    l_pts.inputs["Radius"].default_value = 1.0
    l_pts.fill_type = "NONE"
    l_r = _math(tree, "MULTIPLY", (bx - 1000, by - 2150), gin.outputs["Dome Radius"], 2.4)
    l_pts_tx = safe_node(tree, "GeometryNodeTransform", (bx - 600, by - 2150))
    link_sockets(tree, l_pts.outputs["Mesh"], l_pts_tx.inputs["Geometry"])
    l_scale = _combine(tree, (bx - 800, by - 2200), l_r.outputs[0], l_r.outputs[0], 1.0)
    link_sockets(tree, l_scale.outputs["Vector"], l_pts_tx.inputs["Scale"])
    l_z = _math(tree, "ADD", (bx - 800, by - 2240), dome_z.outputs[0],
                _math(tree, "MULTIPLY", (bx - 900, by - 2240),
                      gin.outputs["Dome Radius"], 0.4).outputs[0])
    l_pts_tx.inputs["Translation"].default_value[2] = 0.0
    lantern_body = safe_node(tree, "GeometryNodeMeshCylinder", (bx - 800, by - 2280))
    lantern_body.inputs["Radius"].default_value = 0.09
    lantern_body.inputs["Depth"].default_value = 0.3
    lantern_body.inputs["Vertices"].default_value = 10
    lantern_cap = safe_node(tree, "GeometryNodeMeshCone", (bx - 800, by - 2340))
    lantern_cap.inputs["Radius Bottom"].default_value = 0.12
    lantern_cap.inputs["Radius Top"].default_value = 0.02
    lantern_cap.inputs["Depth"].default_value = 0.14
    lantern_cap.inputs["Vertices"].default_value = 10
    l_inst1 = safe_node(tree, "GeometryNodeInstanceOnPoints", (bx - 600, by - 2280))
    link_sockets(tree, l_pts_tx.outputs["Geometry"], l_inst1.inputs["Points"])
    link_sockets(tree, lantern_body.outputs["Mesh"], l_inst1.inputs["Instance"])
    l_real1 = safe_node(tree, "GeometryNodeRealizeInstances", (bx - 400, by - 2280))
    link_sockets(tree, l_inst1.outputs["Instances"], l_real1.inputs["Geometry"])
    l_inst2 = safe_node(tree, "GeometryNodeInstanceOnPoints", (bx - 600, by - 2340))
    link_sockets(tree, l_pts_tx.outputs["Geometry"], l_inst2.inputs["Points"])
    link_sockets(tree, lantern_cap.outputs["Mesh"], l_inst2.inputs["Instance"])
    l_real2 = safe_node(tree, "GeometryNodeRealizeInstances", (bx - 400, by - 2340))
    link_sockets(tree, l_inst2.outputs["Instances"], l_real2.inputs["Geometry"])
    lanterns_join = safe_node(tree, "GeometryNodeJoinGeometry", (bx - 200, by - 2280))
    link_sockets(tree, l_real1.outputs["Geometry"], lanterns_join.inputs["Geometry"])
    link_sockets(tree, l_real2.outputs["Geometry"], lanterns_join.inputs["Geometry"])
    lanterns_out = _position_piece(tree, (bx, by - 2280), lanterns_join.outputs["Geometry"],
                                   x=0.0, y=0.0, z=l_z.outputs[0])
    link_sockets(tree, lanterns_out, lanterns.inputs["True"])
    pieces.append(lanterns.outputs["Output"])

    # -- deck railing around the island lip ------------------------------------
    deck = safe_node(tree, "GeometryNodeSwitch", (bx - 600, by - 2500))
    deck.input_type = "GEOMETRY"
    link_sockets(tree, gin.outputs["Deck Railing"], deck.inputs["Switch"])
    d_pts = safe_node(tree, "GeometryNodeMeshCircle", (bx - 800, by - 2500))
    d_pts.inputs["Vertices"].default_value = 28
    d_pts.inputs["Radius"].default_value = 1.0
    d_pts.fill_type = "NONE"
    d_r = _math(tree, "MULTIPLY", (bx - 1000, by - 2500), gin.outputs["Island Radius"], 0.9)
    d_tx = safe_node(tree, "GeometryNodeTransform", (bx - 600, by - 2500))
    link_sockets(tree, d_pts.outputs["Mesh"], d_tx.inputs["Geometry"])
    d_scale = _combine(tree, (bx - 800, by - 2540), d_r.outputs[0], d_r.outputs[0], 1.0)
    link_sockets(tree, d_scale.outputs["Vector"], d_tx.inputs["Scale"])
    d_post = safe_node(tree, "GeometryNodeMeshCube", (bx - 800, by - 2580))
    d_post_size = _combine(tree, (bx - 1000, by - 2620), 0.05, 0.05, 0.8)
    link_sockets(tree, d_post_size.outputs["Vector"], d_post.inputs["Size"])
    d_inst = safe_node(tree, "GeometryNodeInstanceOnPoints", (bx - 600, by - 2580))
    link_sockets(tree, d_tx.outputs["Geometry"], d_inst.inputs["Points"])
    link_sockets(tree, d_post.outputs["Mesh"], d_inst.inputs["Instance"])
    d_real = safe_node(tree, "GeometryNodeRealizeInstances", (bx - 400, by - 2580))
    link_sockets(tree, d_inst.outputs["Instances"], d_real.inputs["Geometry"])
    d_z = _math(tree, "MULTIPLY", (bx - 600, by - 2620), gin.outputs["Island Radius"], 0.28)
    d_out = _position_piece(tree, (bx - 200, by - 2580), d_real.outputs["Geometry"],
                            x=0.0, y=0.0, z=d_z.outputs[0])
    link_sockets(tree, d_out, deck.inputs["True"])
    pieces.append(deck.outputs["Output"])

    # -- assemble --------------------------------------------------------------
    join = safe_node(tree, "GeometryNodeJoinGeometry", (bx + 400, by - 1600))
    for p in pieces:
        link_sockets(tree, p, join.inputs["Geometry"])

    wobbled = _add_wobble(tree, join.outputs["Geometry"],
                          gin.outputs["Wobble"], gin.outputs["Seed"], (bx + 800, by - 1600))

    shade = safe_node(tree, "GeometryNodeSetShadeSmooth", (bx + 1500, by - 1600))
    shade.inputs["Shade Smooth"].default_value = True
    link_sockets(tree, wobbled, shade.inputs["Geometry"])
    link_sockets(tree, shade.outputs["Geometry"], gout.inputs["Geometry"])

    color_node(shade, "geometry")

    return label_tree(tree, "MEL_sky_observatory", [
        {"title": "Inputs", "nodes": ("Group Input",), "role": "input"},
        {"title": "Floating Island", "nodes": ("island", "under", "root"), "role": "geometry"},
        {"title": "Observatory", "nodes": ("drum", "band", "window", "dome"), "role": "geometry"},
        {"title": "Orrery", "nodes": ("ring", "planet", "tilt"), "role": "instance"},
        {"title": "Lanterns & Deck", "nodes": ("lantern", "deck", "post"), "role": "instance"},
        {"title": "Output", "nodes": ("shade", "Group Output"), "role": "output"},
    ])


# -- Registry --------------------------------------------------------------
from .core import register_builder

register_builder(
    "MEL_sky_observatory",
    build_sky_observatory,
    "Celestial Dream Observatory",
    "Breathtaking floating observatory hero: island, dome, gilded bands, "
    "tilted orrery rings with planets, hanging lanterns, deck railing, star "
    "finial -- for Dreamstate and KaleidoNave hero silhouettes.",
    "structures",
)
