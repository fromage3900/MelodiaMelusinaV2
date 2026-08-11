"""Higgsas Geometry Nodes library bridge."""
from __future__ import annotations

import os

import bpy

from .capabilities import higgsas_library_path

HIGGSAS_ARCH_NODES = [
    "NTBricks Grid",
    "NTHexagon Grid",
    "NTTriangle Grid",
    "NTCairo Tile Grid",
    "NTDistance to Edge Voronoi",
    "NTScales Texture",
    "NTRounded Cube",
    "NTPyramid",
    "NTSpin",
    "NTTaper",
    "NTBend",
    "NTMesh Offset",
    "NTSolidify",
    "NTInset Face",
    "NTCircular Array",
    "NTArray",
    "NTDynamic Catenary Splines",
    "NTLoft Splines",
    "NTEven Curve to Mesh",
    "NTTriplanar UV Mapping",
    "NTMesh Points Fracture",
    "NTVoxel Remesh",
    "NTRipples Solver",
]

_HIGGSAS_BUILDERS: dict = {}


def is_available() -> bool:
    for ng in bpy.data.node_groups:
        if ng.name.startswith("NT") and len(ng.name) > 4:
            return True
    return os.path.exists(higgsas_library_path())


def library_path() -> str:
    return higgsas_library_path()


def load_node(name: str):
    ng = bpy.data.node_groups.get(name)
    if ng is not None:
        return ng
    path = library_path()
    if not os.path.exists(path):
        return None
    try:
        with bpy.data.libraries.load(path, link=False) as (src, dst):
            if name in src.node_groups:
                dst.node_groups = [name]
            else:
                return None
    except Exception:
        return None
    return bpy.data.node_groups.get(name)


def load_arch_nodes() -> tuple[list, list]:
    loaded, skipped = [], []
    for name in HIGGSAS_ARCH_NODES:
        if load_node(name) is not None:
            loaded.append(name)
        else:
            skipped.append(name)
    return loaded, skipped


def register_higgsas_builder(arch_type: str, builder_fn) -> None:
    _HIGGSAS_BUILDERS[arch_type] = builder_fn


def apply_surface_pass(obj, props, monolith) -> bool:
    """Post-generate overlay when higgsas_detail requests a surface style."""
    detail = getattr(props, "higgsas_detail", "NONE")
    if detail == "NONE" or not is_available():
        return False
  # Full GN overlay is arch-type specific; v2.70 ensures library is warm.
    style = getattr(props, "higgsas_surface_style", "BRICK")
    node_map = {
        "BRICK": "NTBricks Grid",
        "HEX": "NTHexagon Grid",
        "VORONOI": "NTDistance to Edge Voronoi",
        "CAIRO": "NTCairo Tile Grid",
    }
    ng_name = node_map.get(style) or node_map.get(detail)
    if ng_name:
        load_node(ng_name)
    return ng_name is not None


def higg_node(tree, name, loc, monolith, fallback_type=None):
    """Add Higgsas group node with native fallback (needs monolith _safe_node)."""
    ng = load_node(name)
    safe = getattr(monolith, "_safe_node", None)
    color = getattr(monolith, "color_node", None)
    if ng is None:
        if safe and fallback_type:
            return safe(tree, fallback_type, loc)
        return None
    try:
        node = tree.nodes.new("GeometryNodeGroup")
        node.node_tree = ng
        node.location = loc
        if color:
            color(node, "ornament")
        return node
    except Exception:
        if safe and fallback_type:
            return safe(tree, fallback_type, loc)
        return None
