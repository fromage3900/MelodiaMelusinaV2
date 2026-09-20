"""Sheep collar bell — parametric chime bell with clapper and hanger loop.

Built for the Choral Sheep ornament lane: a signature voice-charm that
hangs from the wreath collar. Uses only node/socket patterns already
proven in this package (filigree.py, cute_decor.py). Category "decor".
"""
from __future__ import annotations

from .core import (
    safe_node, link_sockets, color_node, label_tree,
    new_geometry_tree, add_float_param,
    register_builder,
)


def _taper_top(tree, geo_sock, h_sock, base=0.55, loc=(0, 0)):
    """Narrow the top of a height-H geometry: scale XY by 0.55->1.0."""
    pos = safe_node(tree, "GeometryNodeInputPosition",
                    (loc[0] - 600, loc[1]))
    sep = safe_node(tree, "ShaderNodeSeparateXYZ", (loc[0] - 400, loc[1]))
    link_sockets(tree, pos.outputs["Position"], sep.inputs["Vector"])
    half = safe_node(tree, "ShaderNodeMath", (loc[0] - 200, loc[1] - 100))
    half.operation = "MULTIPLY"
    link_sockets(tree, h_sock, half.inputs[0])
    half.inputs[1].default_value = 0.5
    sh = safe_node(tree, "ShaderNodeMath", (loc[0], loc[1] - 100))
    sh.operation = "ADD"
    link_sockets(tree, sep.outputs["Z"], sh.inputs[0])
    link_sockets(tree, half.outputs[0], sh.inputs[1])
    t = safe_node(tree, "ShaderNodeMath", (loc[0] + 200, loc[1] - 100))
    t.operation = "DIVIDE"
    link_sockets(tree, sh.outputs[0], t.inputs[0])
    link_sockets(tree, h_sock, t.inputs[1])
    k = safe_node(tree, "ShaderNodeMath", (loc[0] + 400, loc[1] - 100))
    k.operation = "MULTIPLY_ADD"
    k.inputs[1].default_value = 1.0 - base
    k.inputs[2].default_value = base
    link_sockets(tree, t.outputs[0], k.inputs[0])
    nx = safe_node(tree, "ShaderNodeMath", (loc[0] + 600, loc[1] + 100))
    nx.operation = "MULTIPLY"
    link_sockets(tree, sep.outputs["X"], nx.inputs[0])
    link_sockets(tree, k.outputs[0], nx.inputs[1])
    ny = safe_node(tree, "ShaderNodeMath", (loc[0] + 600, loc[1] - 100))
    ny.operation = "MULTIPLY"
    link_sockets(tree, sep.outputs["Y"], ny.inputs[0])
    link_sockets(tree, k.outputs[0], ny.inputs[1])
    cv = safe_node(tree, "ShaderNodeCombineXYZ", (loc[0] + 800, loc[1]))
    link_sockets(tree, nx.outputs[0], cv.inputs["X"])
    link_sockets(tree, ny.outputs[0], cv.inputs["Y"])
    link_sockets(tree, sep.outputs["Z"], cv.inputs["Z"])
    sp = safe_node(tree, "GeometryNodeSetPosition", (loc[0] + 1000, loc[1]))
    link_sockets(tree, geo_sock, sp.inputs["Geometry"])
    link_sockets(tree, cv.outputs["Vector"], sp.inputs["Position"])
    return sp.outputs["Geometry"]


def _ring(tree, gin, radius_sock, tube_r, segs, loc):
    """Flat torus ring via profile-circle sweep (filigree.py pattern)."""
    prof = safe_node(tree, "GeometryNodeCurvePrimitiveCircle", loc)
    prof.inputs["Radius"].default_value = tube_r
    prof.inputs["Resolution"].default_value = segs
    path = safe_node(tree, "GeometryNodeCurvePrimitiveCircle",
                     (loc[0], loc[1] - 200))
    link_sockets(tree, radius_sock, path.inputs["Radius"])
    path.inputs["Resolution"].default_value = 48
    mesh = safe_node(tree, "GeometryNodeCurveToMesh",
                     (loc[0] + 200, loc[1] - 100))
    link_sockets(tree, path.outputs["Curve"], mesh.inputs["Curve"])
    link_sockets(tree, prof.outputs["Curve"], mesh.inputs["Profile Curve"])
    return mesh.outputs["Mesh"]


def build_sheep_collar_bell(group_name="MEL_sheep_collar_bell"):
    """Parametric chime bell for the Choral Sheep collar.

    Params:
        Bell Height: body height lip to crown
        Lip Radius: flare radius at the mouth
        Dome Scale: 0 = flat cap, 1 = full dome crown
        Clapper Size: ball radius (0 hides the clapper)
        Loop Size: hanger loop radius (0 hides the loop)
    """
    tree, gin, gout = new_geometry_tree(group_name)
    bx, by = 0, 0
    add_float_param(tree, "Bell Height", 0.05, 0.01, 0.2)
    add_float_param(tree, "Lip Radius", 0.02, 0.005, 0.08)
    add_float_param(tree, "Dome Scale", 0.6, 0.0, 1.0)
    add_float_param(tree, "Clapper Size", 0.008, 0.0, 0.03)
    add_float_param(tree, "Loop Size", 0.006, 0.0, 0.02)

    body = safe_node(tree, "GeometryNodeMeshCylinder", (bx - 600, by + 300))
    body.inputs["Vertices"].default_value = 24
    link_sockets(tree, gin.outputs["Lip Radius"], body.inputs["Radius"])
    link_sockets(tree, gin.outputs["Bell Height"], body.inputs["Depth"])
    tapered = _taper_top(tree, body.outputs["Mesh"],
                         gin.outputs["Bell Height"], loc=(bx - 400, by + 300))

    dome = safe_node(tree, "GeometryNodeMeshUVSphere", (bx - 600, by - 100))
    dome.inputs["Segments"].default_value = 16
    dome.inputs["Rings"].default_value = 8
    link_sockets(tree, gin.outputs["Lip Radius"], dome.inputs["Radius"])
    ds = safe_node(tree, "ShaderNodeMath", (bx - 400, by - 100))
    ds.operation = "MULTIPLY"
    link_sockets(tree, gin.outputs["Dome Scale"], ds.inputs[0])
    ds.inputs[1].default_value = 0.5
    dform = safe_node(tree, "GeometryNodeTransform", (bx - 200, by - 100))
    link_sockets(tree, dome.outputs["Mesh"], dform.inputs["Geometry"])
    dsc = safe_node(tree, "ShaderNodeCombineXYZ", (bx - 300, by - 100))
    link_sockets(tree, gin.outputs["Lip Radius"], dsc.inputs["X"])
    link_sockets(tree, gin.outputs["Lip Radius"], dsc.inputs["Y"])
    link_sockets(tree, ds.outputs[0], dsc.inputs["Z"])
    link_sockets(tree, dsc.outputs["Vector"], dform.inputs["Scale"])

    lip = _ring(tree, gin, gin.outputs["Lip Radius"], 0.003, 8,
                (bx - 600, by - 400))

    clap = safe_node(tree, "GeometryNodeMeshUVSphere", (bx - 200, by - 400))
    clap.inputs["Segments"].default_value = 10
    clap.inputs["Rings"].default_value = 6
    link_sockets(tree, gin.outputs["Clapper Size"], clap.inputs["Radius"])

    loop = _ring(tree, gin, gin.outputs["Loop Size"], 0.002, 6,
                 (bx - 200, by - 600))

    join = safe_node(tree, "GeometryNodeJoinGeometry", (bx + 200, by))
    for src in (tapered, dform.outputs["Geometry"], lip,
                clap.outputs["Mesh"], loop):
        link_sockets(tree, src, join.inputs["Geometry"])
    shade = safe_node(tree, "GeometryNodeSetShadeSmooth", (bx + 400, by))
    link_sockets(tree, join.outputs["Geometry"], shade.inputs["Geometry"])
    link_sockets(tree, shade.outputs["Geometry"], gout.inputs["Geometry"])

    color_node(body, "geometry")
    color_node(join, "geometry")
    return label_tree(tree, group_name, [
        {"title": "Inputs", "nodes": ("Group Input",), "role": "input"},
        {"title": "Bell", "nodes": ("Cylinder", "Sphere", "Circle"),
         "role": "geometry"},
        {"title": "Attribute And Output",
         "nodes": ("Group Output",), "role": "output"},
    ])


register_builder("MEL_sheep_collar_bell", build_sheep_collar_bell,
                 "Sheep Collar Bell",
                 "Parametric chime bell with dome, flared lip, clapper, loop",
                 category="decor")

BUILDERS_PRESETS = {
    "MEL_sheep_collar_bell": {
        "label": "Collar Bell",
        "presets": {
            "collar_gold": {"params": {"Bell Height": 0.05,
                                       "Lip Radius": 0.02,
                                       "Dome Scale": 0.6,
                                       "Clapper Size": 0.008,
                                       "Loop Size": 0.006}},
            "tiny_chime": {"params": {"Bell Height": 0.03,
                                      "Lip Radius": 0.012,
                                      "Dome Scale": 0.8,
                                      "Clapper Size": 0.005,
                                      "Loop Size": 0.004}},
            "grand_bell": {"params": {"Bell Height": 0.09,
                                      "Lip Radius": 0.035,
                                      "Dome Scale": 0.5,
                                      "Clapper Size": 0.014,
                                      "Loop Size": 0.01}},
        },
    },
}
