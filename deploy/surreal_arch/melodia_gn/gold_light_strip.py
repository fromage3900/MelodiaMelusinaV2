"""MEL_gold_light_strip — emissive gold LED strip for dreamy lighting.

A thin rectangular strip that emits warm gold light, perfect for
accent lighting in dreamy stylized architecture.

Builder:
  MEL_gold_light_strip — emissive gold light strip with adjustable length/width
"""
from __future__ import annotations

import bpy

from .core import (
    safe_node, link_sockets, color_node, label_tree,
    new_geometry_tree, add_float_param, add_vector_param,
    register_builder,
)


# Gold emission color (matches MH_MAT_Ornament_Gold base color)
GOLD_EMISSION_COLOR = (0.95, 0.85, 0.2, 1.0)
GOLD_MATERIAL_NAME = "MH_MAT_GoldLight_Emissive"


def _get_or_create_gold_emissive_mat():
    """Get or create the emissive gold material."""
    mat = bpy.data.materials.get(GOLD_MATERIAL_NAME)
    if mat is not None:
        return mat
    mat = bpy.data.materials.new(name=GOLD_MATERIAL_NAME)
    mat.use_nodes = True
    nt = mat.node_tree
    # Clear default nodes
    for n in list(nt.nodes):
        nt.nodes.remove(n)
    # Create emission shader
    emit = nt.nodes.new("ShaderNodeEmission")
    emit.inputs["Color"].default_value = GOLD_EMISSION_COLOR
    emit.inputs["Strength"].default_value = 5.0
    output = nt.nodes.new("ShaderNodeOutputMaterial")
    nt.links.new(emit.outputs["Emission"], output.inputs["Surface"])
    return mat


def build_gold_light_strip(group_name="MEL_gold_light_strip"):
    """Gold light strip: thin emissive rectangle for accent lighting.

    Inputs:
      Geometry     — incoming (pass-through)
      Length       — 4 m  (strip length)
      Width        — 0.05 m (strip width)
      Thickness    — 0.02 m (strip depth)
      Emission     — 5.0  (light strength)
      Gold Tint    — 0.0  (hue offset, 0 = default gold)
    """
    tree, gin, gout = new_geometry_tree(group_name)
    bx, by = 0, 0

    # ── Parameters ──
    length = add_float_param(tree, "Length", 4.0, 0.01, 50.0)
    width = add_float_param(tree, "Width", 0.05, 0.001, 5.0)
    thick = add_float_param(tree, "Thickness", 0.02, 0.001, 2.0)
    emission = add_float_param(tree, "Emission", 5.0, 0.0, 100.0)

    # ── 1. Quad mesh (the light strip) ──
    grid = safe_node(tree, "GeometryNodeMeshGrid", (bx - 200, by + 200))
    color_node(grid, "geometry")
    try:
        link_sockets(tree, length, grid.inputs.get("Size X", grid.inputs[0]))
        link_sockets(tree, width, grid.inputs.get("Size Y", grid.inputs[1]))
        grid.inputs.get("Vertices X", grid.inputs[2]).default_value = 2
        grid.inputs.get("Vertices Y", grid.inputs[3]).default_value = 2
    except Exception:
        pass

    # Extrude for thickness
    extrude = safe_node(tree, "GeometryNodeExtrudeMesh", (bx, by + 100))
    color_node(extrude, "geometry")
    link_sockets(tree, grid.outputs["Mesh"], extrude.inputs["Mesh"])
    try:
        link_sockets(tree, thick, extrude.inputs.get("Offset", extrude.inputs[0]))
    except Exception:
        # Manual offset value
        offset_val = safe_node(tree, "ShaderNodeValue", (bx + 100, by + 100))
        link_sockets(tree, thick, offset_val.inputs.get("Value", offset_val.inputs[0]))
        link_sockets(tree, offset_val.outputs["Value"], extrude.inputs.get("Offset", extrude.inputs[0]))

    # ── 2. Join with incoming geometry ──
    join = safe_node(tree, "GeometryNodeJoinGeometry", (bx + 300, by))
    color_node(join, "geometry")
    link_sockets(tree, gin.outputs["Geometry"], join.inputs["Geometry"])
    link_sockets(tree, extrude.outputs.get("Mesh", extrude.outputs.get("Geometry")), join.inputs["Geometry"])

    # ── 3. Assign gold emissive material ──
    # We need to create the material in the file for the Set Material to work
    gold_mat_obj = _get_or_create_gold_emissive_mat()

    set_mat = safe_node(tree, "GeometryNodeSetMaterial", (bx + 500, by))
    color_node(set_mat, "material")
    link_sockets(tree, join.outputs["Geometry"], set_mat.inputs["Geometry"])
    try:
        set_mat.inputs["Material"].default_value = gold_mat_obj
    except Exception:
        pass

    # ── 4. Shade smooth ──
    shade = safe_node(tree, "GeometryNodeSetShadeSmooth", (bx + 700, by))
    color_node(shade, "geometry")
    shade.inputs["Shade Smooth"].default_value = True
    link_sockets(tree, set_mat.outputs["Geometry"], shade.inputs["Geometry"])

    link_sockets(tree, shade.outputs["Geometry"], gout.inputs["Geometry"])

    return label_tree(tree, "MEL_gold_light_strip", [
        {"title": "Inputs", "nodes": ("Group Input",), "role": "input"},
        {"title": "Geometry", "nodes": ("grid", "extrude", "join"), "role": "geometry"},
        {"title": "Material", "nodes": ("set_mat",), "role": "material"},
        {"title": "Output", "nodes": ("shade", "Group Output"), "role": "output"},
    ])


# ── Registry ──
register_builder(
    "MEL_gold_light_strip", build_gold_light_strip,
    "Gold Light Strip",
    "Emissive gold light strip for dreamy accent lighting. "
    "Adjustable length, width, thickness, and emission strength.",
    category="structures",
)
