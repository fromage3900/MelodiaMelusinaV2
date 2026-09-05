"""Melusina House foundation builders for Melodia Studio (Blender 5.2).

These are the FIRST builders an agent should use for house work. They establish
rounded floor massing before walls, roof, ornament, furniture, or Unreal export.

Builder ladder:
    MEL_mh_foundation_pod
    MEL_mh_foundation_cluster
    MEL_mh_foundation_porch
    MEL_mh_foundation_master

All four register in the dedicated "melusina_house" GN Stack category.
They intentionally use boring, stable primitives: cylinder -> transform -> bevel.
The visual complexity belongs in the later house layers, not in the foundation.
"""
from __future__ import annotations

from .core import (
    safe_node,
    link_sockets,
    label_tree,
    new_geometry_tree,
    add_float_param,
    register_builder,
)


def _geo_out(node):
    if node is None:
        return None
    for socket in getattr(node, "outputs", []):
        if getattr(socket, "type", "") == "GEOMETRY":
            return socket
    return node.outputs[0] if getattr(node, "outputs", None) else None


def _clear_default_output(tree, gout):
    try:
        target = gout.inputs.get("Geometry")
        if target is not None:
            for link in list(target.links):
                tree.links.remove(link)
    except Exception:
        pass


def _math(tree, loc, operation, a, b):
    node = safe_node(tree, "ShaderNodeMath", loc)
    if node is None:
        return None
    node.operation = operation
    if hasattr(a, "id_data"):
        link_sockets(tree, a, node.inputs[0])
    else:
        node.inputs[0].default_value = float(a)
    if hasattr(b, "id_data"):
        link_sockets(tree, b, node.inputs[1])
    else:
        node.inputs[1].default_value = float(b)
    return node.outputs[0]


def _combine_xyz(tree, loc, x=0.0, y=0.0, z=0.0):
    node = safe_node(tree, "ShaderNodeCombineXYZ", loc)
    if node is None:
        return None
    for value, name in ((x, "X"), (y, "Y"), (z, "Z")):
        if hasattr(value, "id_data"):
            link_sockets(tree, value, node.inputs[name])
        else:
            node.inputs[name].default_value = float(value)
    return node.outputs[0]


def _oval_slab(tree, loc, width, depth, height, bevel, x=0.0, y=0.0):
    """Build a beveled oval slab centered at x/y with its base on Z=0."""
    bx, by = loc
    cyl = safe_node(tree, "GeometryNodeMeshCylinder", (bx, by))
    if cyl is None:
        return None
    try:
        cyl.inputs["Vertices"].default_value = 64
        cyl.inputs["Radius"].default_value = 1.0
        cyl.inputs["Depth"].default_value = 1.0
    except Exception:
        pass

    sx = _math(tree, (bx - 220, by + 180), "MULTIPLY", width, 0.5)
    sy = _math(tree, (bx - 220, by + 80), "MULTIPLY", depth, 0.5)
    scale = _combine_xyz(tree, (bx, by + 180), sx, sy, height)
    half_h = _math(tree, (bx - 220, by - 180), "MULTIPLY", height, 0.5)
    translation = _combine_xyz(tree, (bx, by - 180), x, y, half_h)

    xf = safe_node(tree, "GeometryNodeTransform", (bx + 240, by))
    if xf is None:
        return _geo_out(cyl)
    link_sockets(tree, _geo_out(cyl), xf.inputs["Geometry"])
    if scale is not None:
        link_sockets(tree, scale, xf.inputs["Scale"])
    if translation is not None:
        link_sockets(tree, translation, xf.inputs["Translation"])

    bev = safe_node(tree, "GeometryNodeMeshBevel", (bx + 460, by))
    if bev is None:
        return _geo_out(xf)
    link_sockets(tree, _geo_out(xf), bev.inputs["Mesh"])
    link_sockets(tree, bevel, bev.inputs["Offset"])
    try:
        bev.inputs["Segments"].default_value = 3
        bev.inputs["Profile"].default_value = 0.75
    except Exception:
        pass
    return _geo_out(bev)


def _join(tree, loc, geometries):
    alive = [g for g in geometries if g is not None]
    if not alive:
        return None
    if len(alive) == 1:
        return alive[0]
    join = safe_node(tree, "GeometryNodeJoinGeometry", loc)
    if join is None:
        return alive[0]
    for geo in alive:
        link_sockets(tree, geo, join.inputs["Geometry"])
    return _geo_out(join)


def build_mh_foundation_pod(group_name="MEL_mh_foundation_pod"):
    """One rounded room pod: the atomic floor-massing unit."""
    tree, gin, gout = new_geometry_tree(group_name)
    _clear_default_output(tree, gout)
    add_float_param(tree, "Width", 4.6, 1.0, 20.0)
    add_float_param(tree, "Depth", 3.8, 1.0, 20.0)
    add_float_param(tree, "Foundation Height", 0.36, 0.08, 1.5)
    add_float_param(tree, "Bevel", 0.06, 0.0, 0.3)

    geo = _oval_slab(
        tree, (0, 0),
        gin.outputs["Width"], gin.outputs["Depth"],
        gin.outputs["Foundation Height"], gin.outputs["Bevel"],
    )
    if geo is not None:
        link_sockets(tree, geo, gout.inputs["Geometry"])
    label_tree(tree, group_name, [
        {"title": "House Foundation", "nodes": ("Mesh Cylinder", "Transform", "Bevel"), "role": "geometry"},
        {"title": "Output", "nodes": ("Group Output",), "role": "output"},
    ])
    return (tree, gin, gout)


def build_mh_foundation_cluster(group_name="MEL_mh_foundation_cluster"):
    """Four-pod lower-house mass: salon + two side pods + rear pod."""
    tree, gin, gout = new_geometry_tree(group_name)
    _clear_default_output(tree, gout)
    add_float_param(tree, "Center Width", 5.4, 2.0, 14.0)
    add_float_param(tree, "Center Depth", 4.8, 2.0, 14.0)
    add_float_param(tree, "Side Width", 3.7, 1.5, 10.0)
    add_float_param(tree, "Side Depth", 3.4, 1.5, 10.0)
    add_float_param(tree, "Side Spread", 4.1, 1.0, 10.0)
    add_float_param(tree, "Rear Width", 4.2, 1.5, 12.0)
    add_float_param(tree, "Rear Depth", 3.2, 1.5, 10.0)
    add_float_param(tree, "Rear Offset", 3.8, 1.0, 10.0)
    add_float_param(tree, "Foundation Height", 0.36, 0.08, 1.5)
    add_float_param(tree, "Bevel", 0.06, 0.0, 0.3)

    H = gin.outputs["Foundation Height"]
    B = gin.outputs["Bevel"]
    spread = gin.outputs["Side Spread"]
    neg_spread = _math(tree, (-260, 300), "MULTIPLY", spread, -1.0)
    rear = gin.outputs["Rear Offset"]

    parts = [
        _oval_slab(tree, (0, 520), gin.outputs["Center Width"], gin.outputs["Center Depth"], H, B),
        _oval_slab(tree, (0, 250), gin.outputs["Side Width"], gin.outputs["Side Depth"], H, B, x=neg_spread),
        _oval_slab(tree, (0, -20), gin.outputs["Side Width"], gin.outputs["Side Depth"], H, B, x=spread),
        _oval_slab(tree, (0, -290), gin.outputs["Rear Width"], gin.outputs["Rear Depth"], H, B, y=rear),
    ]
    joined = _join(tree, (760, 140), parts)
    if joined is not None:
        link_sockets(tree, joined, gout.inputs["Geometry"])
    label_tree(tree, group_name)
    return (tree, gin, gout)


def build_mh_foundation_porch(group_name="MEL_mh_foundation_porch"):
    """Front oval/crescent entry slab; stairs and rails are later layers."""
    tree, gin, gout = new_geometry_tree(group_name)
    _clear_default_output(tree, gout)
    add_float_param(tree, "Porch Width", 5.2, 1.5, 12.0)
    add_float_param(tree, "Porch Depth", 2.3, 0.8, 7.0)
    add_float_param(tree, "Front Offset", 4.4, 1.0, 10.0)
    add_float_param(tree, "Foundation Height", 0.28, 0.06, 1.0)
    add_float_param(tree, "Bevel", 0.07, 0.0, 0.3)
    neg_front = _math(tree, (-240, -160), "MULTIPLY", gin.outputs["Front Offset"], -1.0)
    geo = _oval_slab(
        tree, (0, 0),
        gin.outputs["Porch Width"], gin.outputs["Porch Depth"],
        gin.outputs["Foundation Height"], gin.outputs["Bevel"],
        y=neg_front,
    )
    if geo is not None:
        link_sockets(tree, geo, gout.inputs["Geometry"])
    label_tree(tree, group_name)
    return (tree, gin, gout)


def build_mh_foundation_master(group_name="MEL_mh_foundation_master"):
    """Immediate concept-board footprint: core cluster + porch + tower pad."""
    tree, gin, gout = new_geometry_tree(group_name)
    _clear_default_output(tree, gout)
    add_float_param(tree, "Center Width", 5.4, 2.0, 14.0)
    add_float_param(tree, "Center Depth", 4.8, 2.0, 14.0)
    add_float_param(tree, "Side Width", 3.7, 1.5, 10.0)
    add_float_param(tree, "Side Depth", 3.4, 1.5, 10.0)
    add_float_param(tree, "Side Spread", 4.1, 1.0, 10.0)
    add_float_param(tree, "Rear Width", 4.2, 1.5, 12.0)
    add_float_param(tree, "Rear Depth", 3.2, 1.5, 10.0)
    add_float_param(tree, "Rear Offset", 3.8, 1.0, 10.0)
    add_float_param(tree, "Porch Width", 5.2, 1.5, 12.0)
    add_float_param(tree, "Porch Depth", 2.3, 0.8, 7.0)
    add_float_param(tree, "Porch Offset", 4.4, 1.0, 10.0)
    add_float_param(tree, "Tower Radius", 1.15, 0.4, 3.0)
    add_float_param(tree, "Tower X", 5.1, -10.0, 10.0)
    add_float_param(tree, "Tower Y", 1.6, -10.0, 10.0)
    add_float_param(tree, "Foundation Height", 0.36, 0.08, 1.5)
    add_float_param(tree, "Bevel", 0.06, 0.0, 0.3)

    H = gin.outputs["Foundation Height"]
    B = gin.outputs["Bevel"]
    spread = gin.outputs["Side Spread"]
    neg_spread = _math(tree, (-300, 350), "MULTIPLY", spread, -1.0)
    neg_porch = _math(tree, (-300, -420), "MULTIPLY", gin.outputs["Porch Offset"], -1.0)
    tower_diameter = _math(tree, (-300, -560), "MULTIPLY", gin.outputs["Tower Radius"], 2.0)

    parts = [
        _oval_slab(tree, (0, 620), gin.outputs["Center Width"], gin.outputs["Center Depth"], H, B),
        _oval_slab(tree, (0, 350), gin.outputs["Side Width"], gin.outputs["Side Depth"], H, B, x=neg_spread),
        _oval_slab(tree, (0, 80), gin.outputs["Side Width"], gin.outputs["Side Depth"], H, B, x=spread),
        _oval_slab(tree, (0, -190), gin.outputs["Rear Width"], gin.outputs["Rear Depth"], H, B, y=gin.outputs["Rear Offset"]),
        _oval_slab(tree, (0, -460), gin.outputs["Porch Width"], gin.outputs["Porch Depth"], H, B, y=neg_porch),
        _oval_slab(tree, (0, -730), tower_diameter, tower_diameter, H, B, x=gin.outputs["Tower X"], y=gin.outputs["Tower Y"]),
    ]
    joined = _join(tree, (820, 100), parts)
    if joined is not None:
        link_sockets(tree, joined, gout.inputs["Geometry"])
    label_tree(tree, group_name, [
        {"title": "Melusina House Foundation", "nodes": ("Mesh Cylinder", "Transform", "Bevel"), "role": "geometry"},
        {"title": "Output", "nodes": ("Group Output",), "role": "output"},
    ])
    return (tree, gin, gout)


def _register_all():
    register_builder(
        "MEL_mh_foundation_pod", build_mh_foundation_pod,
        "MH Foundation Pod",
        "Atomic rounded/oval room slab for Melusina House massing. Start here before walls.",
        category="melusina_house",
    )
    register_builder(
        "MEL_mh_foundation_cluster", build_mh_foundation_cluster,
        "MH Foundation Cluster",
        "Salon + side pods + rear pod; first useful whole-house floor mass.",
        category="melusina_house",
    )
    register_builder(
        "MEL_mh_foundation_porch", build_mh_foundation_porch,
        "MH Foundation Porch",
        "Front oval entry/terrace slab for the round-Baroque facade.",
        category="melusina_house",
    )
    register_builder(
        "MEL_mh_foundation_master", build_mh_foundation_master,
        "MH Foundation Master",
        "Concept-board blockout: foundation cluster, front porch and Listening Tower pad.",
        category="melusina_house",
    )


_register_all()
