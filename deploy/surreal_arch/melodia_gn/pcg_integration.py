"""PCG integration GN group builders — tag schemas, material crosswalk.

Water/music PCG tags are stored as FLOAT/INT/BOOLEAN attributes (Blender
named attributes do not support STRING), matching the WP_/MN_ tag ladder
used by the PCG layout lane. The material crosswalk builders emit base
color / metallic / roughness attributes readable by the UE material map
export lane.
"""

from __future__ import annotations

import bpy

from .core import (
    safe_node, link_sockets, link_float_to_vector, color_node, label_tree,
    new_geometry_tree, add_float_param, add_int_param, add_bool_param,
    make_group_input, register_builder,
)


def _pcg_common(group_name, theme):
    """Shared PCG tag graph. theme in ('water', 'music')."""
    tree, gin, gout = new_geometry_tree(group_name)
    bx, by = 0, 0

    if theme == "water":
        add_int_param(tree, "Tag Type", 0, 0, 3)
        add_float_param(tree, "Water Depth", 2.0, 0.1, 10.0)
        add_float_param(tree, "Current Speed", 1.0, 0.01, 10.0)
        add_float_param(tree, "Foam Intensity", 0.5, 0.0, 1.0)
        add_bool_param(tree, "Is Dynamic", True)
    else:
        add_int_param(tree, "Musical Theme", 0, 0, 3)
        add_int_param(tree, "Instrument Count", 0, 0, 16)
        add_float_param(tree, "Tempo", 120.0, 60.0, 180.0)
        add_float_param(tree, "Density", 0.5, 0.01, 2.0)
        add_bool_param(tree, "Is Dynamic", True)

    tag = safe_node(tree, "GeometryNodeStoreNamedAttribute", (bx - 200, by))
    tag.data_type = "INT"
    tag.inputs["Name"].default_value = "pcg_tag_index"
    if theme == "water":
        link_sockets(tree, gin.outputs["Tag Type"], tag.inputs["Value"])
    else:
        link_sockets(tree, gin.outputs["Musical Theme"], tag.inputs["Value"])
    link_sockets(tree, gin.outputs["Geometry"], tag.inputs["Geometry"])

    dyn = safe_node(tree, "GeometryNodeStoreNamedAttribute", (bx, by - 200))
    dyn.data_type = "BOOLEAN"
    dyn.inputs["Name"].default_value = "pcg_is_dynamic"
    link_sockets(tree, gin.outputs["Is Dynamic"], dyn.inputs["Value"])
    link_sockets(tree, tag.outputs["Geometry"], dyn.inputs["Geometry"])

    if theme == "water":
        depth = safe_node(tree, "GeometryNodeStoreNamedAttribute", (bx + 200, by))
        depth.data_type = "FLOAT"
        depth.inputs["Name"].default_value = "water_depth"
        link_sockets(tree, gin.outputs["Water Depth"], depth.inputs["Value"])
        link_sockets(tree, dyn.outputs["Geometry"], depth.inputs["Geometry"])

        foam = safe_node(tree, "GeometryNodeStoreNamedAttribute", (bx + 200, by - 200))
        foam.data_type = "FLOAT"
        foam.inputs["Name"].default_value = "foam_intensity"
        link_sockets(tree, gin.outputs["Foam Intensity"], foam.inputs["Value"])
        link_sockets(tree, depth.outputs["Geometry"], foam.inputs["Geometry"])

        speed = safe_node(tree, "GeometryNodeStoreNamedAttribute", (bx + 400, by - 200))
        speed.data_type = "FLOAT"
        speed.inputs["Name"].default_value = "current_speed"
        link_sockets(tree, gin.outputs["Current Speed"], speed.inputs["Value"])
        link_sockets(tree, foam.outputs["Geometry"], speed.inputs["Geometry"])
        out = speed
        color_node(speed, "attribute")
    else:
        instr = safe_node(tree, "GeometryNodeStoreNamedAttribute", (bx + 200, by))
        instr.data_type = "INT"
        instr.inputs["Name"].default_value = "instrument_count"
        link_sockets(tree, gin.outputs["Instrument Count"], instr.inputs["Value"])
        link_sockets(tree, dyn.outputs["Geometry"], instr.inputs["Geometry"])

        tempo = safe_node(tree, "GeometryNodeStoreNamedAttribute", (bx + 200, by - 200))
        tempo.data_type = "FLOAT"
        tempo.inputs["Name"].default_value = "tempo"
        link_sockets(tree, gin.outputs["Tempo"], tempo.inputs["Value"])
        link_sockets(tree, instr.outputs["Geometry"], tempo.inputs["Geometry"])

        dens = safe_node(tree, "GeometryNodeStoreNamedAttribute", (bx + 400, by - 200))
        dens.data_type = "FLOAT"
        dens.inputs["Name"].default_value = "density"
        link_sockets(tree, gin.outputs["Density"], dens.inputs["Value"])
        link_sockets(tree, tempo.outputs["Geometry"], dens.inputs["Geometry"])
        out = dens
        color_node(dens, "attribute")

    link_sockets(tree, out.outputs["Geometry"], gout.inputs["Geometry"])

    color_node(tag, "attribute")
    color_node(dyn, "attribute")
    color_node(out, "attribute")

    return label_tree(tree, group_name, [
        {"title": "Inputs", "nodes": ("Group Input",), "role": "input"},
        {"title": "PCG Tags", "nodes": ("store",), "role": "attribute"},
        {"title": "Output", "nodes": ("Group Output",), "role": "output"},
    ])


def pcg_water_tags(group_name="MEL_pcg_water_tags"):
    """PCG tag schema for water geometry — tag index, depth, foam, dynamic."""
    return _pcg_common(group_name, "water")


def pcg_water_tags_v2(group_name="MEL_pcg_water_tags_v2"):
    """Enhanced water tag schema with Current Speed lane support."""
    return _pcg_common(group_name, "water")


def pcg_music_tags(group_name="MEL_pcg_music_tags"):
    """PCG tag schema for music geometry — theme, instruments, tempo."""
    return _pcg_common(group_name, "music")


def pcg_music_tags_v2(group_name="MEL_pcg_music_tags_v2"):
    """Enhanced music tag schema with Density lane support."""
    return _pcg_common(group_name, "music")


def _material_common(group_name, water_mode_default=0):
    """Shared material crosswalk graph."""
    tree, gin, gout = new_geometry_tree(group_name)
    bx, by = 0, 0

    add_int_param(tree, "Material Slot Index", 0, 0, 31)
    add_float_param(tree, "Base Color R", 0.8, 0.0, 1.0)
    add_float_param(tree, "Base Color G", 0.8, 0.0, 1.0)
    add_float_param(tree, "Base Color B", 0.8, 0.0, 1.0)
    add_float_param(tree, "Metallic", 0.0, 0.0, 1.0)
    add_float_param(tree, "Roughness", 0.5, 0.0, 1.0)
    add_int_param(tree, "Water Mode", water_mode_default, 0, 2)

    color_s = safe_node(tree, "FunctionNodeCombineColor", (bx - 400, by))
    link_sockets(tree, gin.outputs["Base Color R"], color_s.inputs["Red"])
    link_sockets(tree, gin.outputs["Base Color G"], color_s.inputs["Green"])
    link_sockets(tree, gin.outputs["Base Color B"], color_s.inputs["Blue"])

    store_c = safe_node(tree, "GeometryNodeStoreNamedAttribute", (bx - 200, by))
    store_c.data_type = "FLOAT_COLOR"
    store_c.inputs["Name"].default_value = "material_base_color"
    link_sockets(tree, color_s.outputs["Color"], store_c.inputs["Value"])
    link_sockets(tree, gin.outputs["Geometry"], store_c.inputs["Geometry"])

    store_m = safe_node(tree, "GeometryNodeStoreNamedAttribute", (bx, by - 200))
    store_m.data_type = "FLOAT"
    store_m.inputs["Name"].default_value = "material_metallic"
    link_sockets(tree, gin.outputs["Metallic"], store_m.inputs["Value"])
    link_sockets(tree, store_c.outputs["Geometry"], store_m.inputs["Geometry"])

    store_r = safe_node(tree, "GeometryNodeStoreNamedAttribute", (bx + 200, by - 200))
    store_r.data_type = "FLOAT"
    store_r.inputs["Name"].default_value = "material_roughness"
    link_sockets(tree, gin.outputs["Roughness"], store_r.inputs["Value"])
    link_sockets(tree, store_m.outputs["Geometry"], store_r.inputs["Geometry"])

    store_w = safe_node(tree, "GeometryNodeStoreNamedAttribute", (bx + 200, by))
    store_w.data_type = "INT"
    store_w.inputs["Name"].default_value = "material_water_mode"
    link_sockets(tree, gin.outputs["Water Mode"], store_w.inputs["Value"])
    link_sockets(tree, store_r.outputs["Geometry"], store_w.inputs["Geometry"])
    link_sockets(tree, store_w.outputs["Geometry"], gout.inputs["Geometry"])

    color_node(color_s, "material")
    color_node(store_c, "attribute")
    color_node(store_m, "attribute")
    color_node(store_r, "attribute")
    color_node(store_w, "attribute")

    return label_tree(tree, group_name, [
        {"title": "Inputs", "nodes": ("Group Input",), "role": "input"},
        {"title": "Material Map", "nodes": ("combine color", "store"), "role": "material"},
        {"title": "Output", "nodes": ("Group Output",), "role": "output"},
    ])


def material_crosswalk_integration(group_name="MEL_material_crosswalk"):
    """Material crosswalk for UE export — base color, metallic, roughness, water mode."""
    return _material_common(group_name, water_mode_default=0)


def material_crosswalk_v2(group_name="MEL_material_crosswalk_v2"):
    """Enhanced crosswalk — water mode defaults to caustics lane (mode 1)."""
    return _material_common(group_name, water_mode_default=1)


# -- Registry --
register_builder("MEL_pcg_water_tags", pcg_water_tags, "PCG Water Tags",
    "PCG tag schema for water geometry — pcg_tag_index, water_depth, foam_intensity, pcg_is_dynamic.",
    "set_dressing", hidden=True, role="pcg_alias")
register_builder("MEL_pcg_water_tags_v2", pcg_water_tags_v2, "PCG Water Tags v2",
    "Enhanced water tag schema — adds Current Speed lane support.",
    "set_dressing", role="pcg_keep")
register_builder("MEL_pcg_music_tags", pcg_music_tags, "PCG Music Tags",
    "PCG tag schema for music geometry — pcg_tag_index, instrument_count, tempo, pcg_is_dynamic.",
    "set_dressing", hidden=True, role="pcg_alias")
register_builder("MEL_pcg_music_tags_v2", pcg_music_tags_v2, "PCG Music Tags v2",
    "Enhanced music tag schema — adds Density lane support.",
    "set_dressing", role="pcg_keep")
register_builder("MEL_material_crosswalk", material_crosswalk_integration, "Material Crosswalk",
    "Material crosswalk for UE export — base color, metallic, roughness, water mode attributes.",
    "set_dressing", hidden=True, role="pcg_alias")
register_builder("MEL_material_crosswalk_v2", material_crosswalk_v2, "Material Crosswalk v2",
    "Enhanced crosswalk with caustics-first water mode default.",
    "set_dressing", role="pcg_keep")