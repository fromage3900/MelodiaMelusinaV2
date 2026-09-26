"""MEL_doll_socket — BJD/marionette socket joint cut into the real base mesh.

Direction (owner, 2026-09-23): NOT floating ornament balls. A doll joint is a
ball seated in spherical cups CUT into the body: two boolean-difference
cavities offset along the limb axis, ball nested between them, porcelain
material ID for the Copernicus bake lane.

Tree (per modifier on the skin mesh):
  Base - CupA - CupB  (EXACT booleans, cup centers offset +/- along axis)
  + UV sphere ball at center (M_GNJ_Porcelain + mj_porcelain attr)
All coordinates in the SKIN MESH'S LOCAL SPACE — the caller transforms world
bone positions by base.matrix_world.inverted().
"""
from __future__ import annotations

import bpy

from .angel_convergence import _g, _i, _math, add_audio_attributes
from .core import (
    add_float_param, add_vector_param, label_tree, link_sockets,
    mesh_boolean_node, new_geometry_tree, register_builder, safe_node,
)

PORCELAIN_MAT = "M_GNJ_Porcelain"


def ensure_porcelain_material():
    mat = bpy.data.materials.get(PORCELAIN_MAT)
    if mat is None:
        mat = bpy.data.materials.new(PORCELAIN_MAT)
        mat.use_nodes = True
        bsdf = next((n for n in mat.node_tree.nodes if n.type == 'BSDF_PRINCIPLED'), None)
        if bsdf:
            try:
                bsdf.inputs["Base Color"].default_value = (0.93, 0.90, 0.86, 1.0)
                bsdf.inputs["Roughness"].default_value = 0.28
                bsdf.inputs["IOR"].default_value = 1.46
                if "Subsurface Weight" in bsdf.inputs:
                    bsdf.inputs["Subsurface Weight"].default_value = 0.08
            except Exception:
                pass
        mat.diffuse_color = (0.93, 0.90, 0.86, 1.0)
    return mat


def build_mel_doll_socket(group_name="MEL_doll_socket"):
    """Ball + two offset boolean cups, designed to live on the skin mesh."""
    tree, gin, gout = new_geometry_tree(group_name)
    base_geo = _g(gin, "Geometry")

    center = add_vector_param(tree, "Center", (0.0, 0.0, 1.0))
    axis = add_vector_param(tree, "Axis", (0.0, 0.0, 1.0))
    ball_r = add_float_param(tree, "Ball Radius", 0.032, 0.01, 0.08)
    cup_shift = add_float_param(tree, "Cup Shift", 0.45, 0.0, 0.7)
    cavity = add_float_param(tree, "Cavity Scale", 1.05, 1.0, 1.25)

    # normalized axis
    vnorm = safe_node(tree, "ShaderNodeVectorMath", (-1600, 500))
    vnorm.operation = 'NORMALIZE'
    link_sockets(tree, axis, vnorm.inputs[0])

    # offset = axis_n * (ball_r * cup_shift)
    rs = _math(tree, (-1600, 350), "MULTIPLY", a=ball_r, b=cup_shift)
    vscale = safe_node(tree, "ShaderNodeVectorMath", (-1400, 500))
    vscale.operation = 'SCALE'
    link_sockets(tree, _g(vnorm, "Vector"), vscale.inputs[0])
    link_sockets(tree, _g(rs, "Value"), vscale.inputs[3])

    cup_pos = safe_node(tree, "ShaderNodeVectorMath", (-1200, 500))
    cup_pos.operation = 'ADD'
    link_sockets(tree, center, cup_pos.inputs[0])
    link_sockets(tree, _g(vscale, "Vector"), cup_pos.inputs[1])
    cup_neg = safe_node(tree, "ShaderNodeVectorMath", (-1200, 350))
    cup_neg.operation = 'SUBTRACT'
    link_sockets(tree, center, cup_neg.inputs[0])
    link_sockets(tree, _g(vscale, "Vector"), cup_neg.inputs[1])

    cup_rad = _math(tree, (-1400, 200), "MULTIPLY", a=ball_r, b=cavity)

    # ---- ball (porcelain) ----
    ball = safe_node(tree, "GeometryNodeMeshUVSphere", (-1200, 50))
    ball.inputs["Segments"].default_value = 32
    ball.inputs["Rings"].default_value = 16
    link_sockets(tree, ball_r, ball.inputs["Radius"])
    bxf = safe_node(tree, "GeometryNodeTransform", (-1000, 50))
    link_sockets(tree, _g(ball, "Mesh"), _i(bxf, "Geometry"))
    link_sockets(tree, center, _i(bxf, "Translation"))

    # bake-lane mask attribute before material
    sattr = safe_node(tree, "GeometryNodeStoreNamedAttribute", (-800, 50))
    sattr.data_type = 'FLOAT'
    sattr.domain = 'POINT'
    try:
        sattr.inputs["Name"].default_value = "mj_porcelain"
        sattr.inputs["Value"].default_value = 1.0
    except Exception:
        pass
    link_sockets(tree, _g(bxf, "Geometry"), _i(sattr, "Geometry"))

    setmat = safe_node(tree, "GeometryNodeSetMaterial", (-600, 50))
    try:
        setmat.inputs["Material"].default_value = ensure_porcelain_material()
    except Exception:
        pass
    link_sockets(tree, _g(sattr, "Geometry"), _i(setmat, "Geometry"))

    # ---- cups ----
    for nm, csock, y in (("A", _g(cup_pos, "Vector"), -150), ("B", _g(cup_neg, "Vector"), -350)):
        cup = safe_node(tree, "GeometryNodeMeshUVSphere", (-1000, y))
        cup.inputs["Segments"].default_value = 24
        cup.inputs["Rings"].default_value = 12
        link_sockets(tree, _g(cup_rad, "Value"), cup.inputs["Radius"])
        cxf = safe_node(tree, "GeometryNodeTransform", (-800, y))
        link_sockets(tree, _g(cup, "Mesh"), _i(cxf, "Geometry"))
        link_sockets(tree, csock, _i(cxf, "Translation"))
        if nm == "A":
            _, cut1 = mesh_boolean_node(tree, (-500, y), 'DIFFERENCE', base_geo, _g(cxf, "Geometry"))
            prev = cut1
        else:
            _, cut2 = mesh_boolean_node(tree, (-300, y), 'DIFFERENCE', prev, _g(cxf, "Geometry"))
            prev = cut2

    join = safe_node(tree, "GeometryNodeJoinGeometry", (-100, 0))
    link_sockets(tree, prev, _i(join, "Geometry"))
    link_sockets(tree, _g(setmat, "Geometry"), _i(join, "Geometry"))

    out_geo = add_audio_attributes(tree, gin, _g(join, "Geometry"), loc=(100, 200))
    link_sockets(tree, out_geo, _i(gout, "Geometry"))
    label_tree(tree, group_name)
    return tree


register_builder(
    "MEL_doll_socket",
    build_mel_doll_socket,
    "Doll Socket Joint",
    "BJD/marionette socket: boolean cup cavities cut into the skin mesh with "
    "a porcelain ball seated between them. Local-space; feed bone positions "
    "transformed into the mesh's space.",
    category="bionic",
)
