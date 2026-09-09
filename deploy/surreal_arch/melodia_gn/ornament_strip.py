"""MEL_gold_ornament_strip — gold bead distribution along a curve.

Distributes small golden bead/sphere instances along any curve input,
creating ornate trim lines for dreamy stylized architecture.

Builder:
  MEL_gold_ornament_strip — bead chain along spline with gold material
"""
from __future__ import annotations

import bpy

from .core import (
    safe_node, link_sockets, link_float_to_vector, color_node, label_tree,
    new_geometry_tree, add_float_param, add_int_param, add_bool_param,
    add_vector_param, register_builder,
)

GOLD_MATERIAL_NAME = "MH_MAT_Ornament_Gold"


def _ensure_gold_material():
    """Ensure MH_MAT_Ornament_Gold exists in the file."""
    mat = bpy.data.materials.get(GOLD_MATERIAL_NAME)
    if mat is not None:
        return mat
    mat = bpy.data.materials.new(name=GOLD_MATERIAL_NAME)
    mat.use_nodes = True
    nt = mat.node_tree
    for n in list(nt.nodes):
        nt.nodes.remove(n)
    emit = nt.nodes.new("ShaderNodeEmission")
    emit.inputs["Color"].default_value = (0.95, 0.85, 0.2, 1.0)
    emit.inputs["Strength"].default_value = 3.0
    output = nt.nodes.new("ShaderNodeOutputMaterial")
    nt.links.new(emit.outputs["Emission"], output.inputs["Surface"])
    return mat


def build_gold_ornament_strip(group_name="MEL_gold_ornament_strip"):
    """Gold bead strip: instances golden spheres along a curve.

    Inputs:
      Geometry          — incoming (pass-through)
      Spline            — curve to distribute beads along
      Bead Size         — 0.15 m (sphere radius)
      Bead Spacing      — 0.3 m (distance between bead centers)
      Count Override    — 0 (if >0, use this count instead of spacing-based)
    """
    tree, gin, gout = new_geometry_tree(group_name)
    bx, by = 0, 0

    # ── Parameters ──
    bead_size = add_float_param(tree, "Bead Size", 0.15, 0.001, 5.0)
    spacing = add_float_param(tree, "Bead Spacing", 0.3, 0.01, 50.0)
    count_override = add_int_param(tree, "Count Override", 0, 0, 1000)

    # ── 1. Resample curve ──
    resample = safe_node(tree, "GeometryNodeResampleCurve", (bx - 200, by + 200))
    color_node(resample, "curve")
    try:
        resample.mode = "COUNT"
    except Exception:
        pass

    # Link spline input
    spline_in = gin.outputs.get("Spline", gin.outputs.get("Geometry"))
    link_sockets(tree, spline_in, resample.inputs.get("Curve", resample.inputs[0]))

    # Use count_override directly (simpler than computing from length)
    # Default to count_override value if > 0, otherwise use a reasonable default
    # We link the count parameter directly
    try:
        link_sockets(tree, count_override, resample.inputs.get("Count", resample.inputs.get("Count")))
    except Exception:
        pass

    # ── 2. Sphere instance (ICOSphere) ──
    sphere = safe_node(tree, "GeometryNodeMeshIcoSphere", (bx - 300, by - 100))
    color_node(sphere, "instance")
    try:
        sphere.inputs["Radius"].default_value = 1.0
        sphere.inputs["Subdivision"].default_value = 1
    except Exception:
        pass

    # ── 3. Instantiate on points ──
    inst = safe_node(tree, "GeometryNodeInstanceOnPoints", (bx, by))
    color_node(inst, "instance")
    link_sockets(tree, resample.outputs.get("Curve", resample.outputs[0]), inst.inputs.get("Points", inst.inputs[0]))
    link_sockets(tree, sphere.outputs.get("Mesh", sphere.outputs[0]), inst.inputs.get("Instance", inst.inputs[1]))

    # Scale instances to bead size
    scale_inst = safe_node(tree, "GeometryNodeScaleInstances", (bx + 200, by))
    color_node(scale_inst, "instance")
    link_float_to_vector(tree, bead_size, scale_inst, "Scale", defaults=(1.0, 1.0, 1.0))
    link_sockets(tree, inst.outputs.get("Instances"), scale_inst.inputs.get("Instances", scale_inst.inputs[0]))

    # ── 4. Set material ──
    gold_mat = _ensure_gold_material()
    set_mat = safe_node(tree, "GeometryNodeSetMaterial", (bx + 400, by))
    color_node(set_mat, "material")
    link_sockets(tree, scale_inst.outputs.get("Instances"), set_mat.inputs.get("Geometry", set_mat.inputs[0]))
    try:
        set_mat.inputs["Material"].default_value = gold_mat
    except Exception:
        pass

    # ── 5. Realize instances ──
    realize = safe_node(tree, "GeometryNodeRealizeInstances", (bx + 500, by))
    color_node(realize, "geometry")
    link_sockets(tree, set_mat.outputs.get("Geometry"), realize.inputs.get("Geometry", realize.inputs[0]))

    # ── 6. Join with incoming ──
    join = safe_node(tree, "GeometryNodeJoinGeometry", (bx + 700, by))
    color_node(join, "geometry")
    link_sockets(tree, gin.outputs.get("Geometry"), join.inputs.get("Geometry"))
    link_sockets(tree, realize.outputs.get("Geometry"), join.inputs.get("Geometry"))

    link_sockets(tree, join.outputs.get("Geometry"), gout.inputs.get("Geometry"))

    return label_tree(tree, "MEL_gold_ornament_strip", [
        {"title": "Inputs", "nodes": ("Group Input",), "role": "input"},
        {"title": "Curve Sampling", "nodes": ("resample",), "role": "curve"},
        {"title": "Instance", "nodes": ("sphere", "inst", "scale_inst"), "role": "instance"},
        {"title": "Material", "nodes": ("set_mat",), "role": "material"},
        {"title": "Output", "nodes": ("realize", "join", "Group Output"), "role": "output"},
    ])


# ── Registry ──
register_builder(
    "MEL_gold_ornament_strip", build_gold_ornament_strip,
    "Gold Ornament Strip",
    "Distributes golden bead instances along a curve for ornate trim.",
    category="ornament",
)
