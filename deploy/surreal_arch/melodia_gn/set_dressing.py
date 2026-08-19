"""Set-dressing GN group builders — themed structure adaptations (24 variants).

Twelve water-themed pieces (gazebo through waterfall) and twelve
music-themed pieces (bandstand through fountain). Every variant shares the
same decoration contract: it stores themed attributes (water_level,
current_speed, ripple_carve / instrument_count, tempo, notation_density)
on its output geometry so PCG and material lanes can read them.
"""

from __future__ import annotations

import math

import bpy

from .core import (
    safe_node, link_sockets, link_float_to_vector, color_node, label_tree,
    new_geometry_tree, add_float_param, add_int_param, add_bool_param,
    add_mesh_torus, make_group_input, register_builder,
)

_WATER_TYPES = (
    "structure", "gazebo", "arch", "portico", "wall", "curtain",
    "fountain", "dock", "deck", "bridge", "canal", "waterfall",
)
_MUSIC_TYPES = (
    "structure", "gazebo", "arch", "portico", "wall", "curtain",
    "bandstand", "stage", "shell", "recital", "bridge", "fountain",
)


def _piece_geometry(kind, tree, gin, x, y):
    """Build the base geometry for a set-dressing piece kind.

    Returns the output socket of the piece (before themed attributes).
    """
    if kind in ("structure", "gazebo", "bandstand"):
        drum = safe_node(tree, "GeometryNodeMeshCylinder", (x - 300, y))
        drum.inputs["Radius"].default_value = 2.0
        drum.inputs["Depth"].default_value = 4.0
        drum.inputs["Vertices"].default_value = 24
        drum.fill_type = "NGON"
        roof = safe_node(tree, "GeometryNodeMeshCone", (x - 300, y - 200))
        roof.inputs["Radius Bottom"].default_value = 2.5
        roof.inputs["Depth"].default_value = 1.5
        roof.inputs["Vertices"].default_value = 24
        roof.fill_type = "NGON"
        if kind == "bandstand":
            stage = safe_node(tree, "GeometryNodeMeshCube", (x - 300, y - 400))
            stage.inputs["Size"].default_value = (4.0, 3.0, 0.4)
            join = safe_node(tree, "GeometryNodeJoinGeometry", (x - 100, y))
            link_sockets(tree, drum.outputs["Mesh"], join.inputs["Geometry"])
            link_sockets(tree, roof.outputs["Mesh"], join.inputs["Geometry"])
            link_sockets(tree, stage.outputs["Mesh"], join.inputs["Geometry"])
            return join.outputs["Geometry"]
        join = safe_node(tree, "GeometryNodeJoinGeometry", (x - 100, y))
        link_sockets(tree, drum.outputs["Mesh"], join.inputs["Geometry"])
        link_sockets(tree, roof.outputs["Mesh"], join.inputs["Geometry"])
        return join.outputs["Geometry"]

    if kind == "arch":
        arch = add_mesh_torus(tree, (x - 300, y), 1.5, 0.3, 48, 12)
        return arch.outputs["Mesh"]

    if kind == "portico":
        grid = safe_node(tree, "GeometryNodeMeshGrid", (x - 500, y))
        grid.inputs["Size X"].default_value = 6.0
        grid.inputs["Size Y"].default_value = 2.0
        grid.inputs["Vertices X"].default_value = 4
        grid.inputs["Vertices Y"].default_value = 2
        col = safe_node(tree, "GeometryNodeMeshCylinder", (x - 500, y - 200))
        col.inputs["Radius"].default_value = 0.08
        col.inputs["Depth"].default_value = 3.0
        col.inputs["Vertices"].default_value = 12
        col.fill_type = "NGON"
        inst = safe_node(tree, "GeometryNodeInstanceOnPoints", (x - 300, y))
        link_sockets(tree, grid.outputs["Mesh"], inst.inputs["Points"])
        link_sockets(tree, col.outputs["Mesh"], inst.inputs["Instance"])
        real = safe_node(tree, "GeometryNodeRealizeInstances", (x - 200, y))
        link_sockets(tree, inst.outputs["Instances"], real.inputs["Geometry"])
        ped = safe_node(tree, "GeometryNodeMeshCube", (x - 500, y - 400))
        ped.inputs["Size"].default_value = (6.0, 0.4, 0.6)
        join = safe_node(tree, "GeometryNodeJoinGeometry", (x - 100, y))
        link_sockets(tree, real.outputs["Geometry"], join.inputs["Geometry"])
        link_sockets(tree, ped.outputs["Mesh"], join.inputs["Geometry"])
        return join.outputs["Geometry"]

    if kind in ("wall", "curtain"):
        wall = safe_node(tree, "GeometryNodeMeshCube", (x - 300, y))
        wall.inputs["Size"].default_value = (8.0, 0.5, 6.0)
        return wall.outputs["Mesh"]

    if kind == "fountain":
        basin = safe_node(tree, "GeometryNodeMeshCylinder", (x - 400, y))
        basin.inputs["Radius"].default_value = 2.5
        basin.inputs["Depth"].default_value = 0.8
        basin.inputs["Vertices"].default_value = 32
        basin.fill_type = "NGON"
        jet = safe_node(tree, "GeometryNodeMeshUVSphere", (x - 400, y - 220))
        jet.inputs["Radius"].default_value = 0.4
        jet.inputs["Segments"].default_value = 16
        jet.inputs["Rings"].default_value = 10
        jet_pos = safe_node(tree, "GeometryNodeSetPosition", (x - 200, y - 220))
        link_sockets(tree, jet.outputs["Mesh"], jet_pos.inputs["Geometry"])
        jet_off = safe_node(tree, "ShaderNodeCombineXYZ", (x - 300, y - 320))
        jet_off.inputs["X"].default_value = 0.0
        jet_off.inputs["Y"].default_value = 0.0
        jet_off.inputs["Z"].default_value = 1.2
        link_sockets(tree, jet_off.outputs["Vector"], jet_pos.inputs["Offset"])
        join = safe_node(tree, "GeometryNodeJoinGeometry", (x - 100, y))
        link_sockets(tree, basin.outputs["Mesh"], join.inputs["Geometry"])
        link_sockets(tree, jet_pos.outputs["Geometry"], join.inputs["Geometry"])
        return join.outputs["Geometry"]

    if kind == "dock":
        planks = []
        for i in range(3):
            plank = safe_node(tree, "GeometryNodeMeshCube", (x - 500 + i * 60, y))
            plank.inputs["Size"].default_value = (1.5, 0.15, 0.6)
            planks.append(plank.outputs["Mesh"])
        posts = []
        for i in range(2):
            post = safe_node(tree, "GeometryNodeMeshCylinder", (x - 500 + i * 200, y - 260))
            post.inputs["Radius"].default_value = 0.12
            post.inputs["Depth"].default_value = 0.9
            post.inputs["Vertices"].default_value = 12
            post.fill_type = "NGON"
            posts.append(post.outputs["Mesh"])
        join = safe_node(tree, "GeometryNodeJoinGeometry", (x - 100, y))
        for m in planks + posts:
            link_sockets(tree, m, join.inputs["Geometry"])
        return join.outputs["Geometry"]

    if kind == "deck":
        grid = safe_node(tree, "GeometryNodeMeshGrid", (x - 400, y))
        grid.inputs["Size X"].default_value = 3.0
        grid.inputs["Size Y"].default_value = 3.0
        grid.inputs["Vertices X"].default_value = 8
        grid.inputs["Vertices Y"].default_value = 8
        floats = []
        for i in range(4):
            fl = safe_node(tree, "GeometryNodeMeshCylinder", (x - 400 + (i % 2) * 200, y - 240 - (i // 2) * 140))
            fl.inputs["Radius"].default_value = 0.2
            fl.inputs["Depth"].default_value = 0.5
            fl.inputs["Vertices"].default_value = 12
            fl.fill_type = "NGON"
            floats.append(fl.outputs["Mesh"])
        join = safe_node(tree, "GeometryNodeJoinGeometry", (x - 100, y))
        link_sockets(tree, grid.outputs["Mesh"], join.inputs["Geometry"])
        for m in floats:
            link_sockets(tree, m, join.inputs["Geometry"])
        return join.outputs["Geometry"]

    if kind == "bridge":
        arch = add_mesh_torus(tree, (x - 400, y), 1.8, 0.25, 48, 12)
        rails = []
        for i in range(2):
            rail = safe_node(tree, "GeometryNodeMeshCylinder", (x - 400 + i * 300, y - 240))
            rail.inputs["Radius"].default_value = 0.06
            rail.inputs["Depth"].default_value = 4.5
            rail.inputs["Vertices"].default_value = 8
            rail.fill_type = "NGON"
            rails.append(rail.outputs["Mesh"])
        join = safe_node(tree, "GeometryNodeJoinGeometry", (x - 100, y))
        link_sockets(tree, arch.outputs["Mesh"], join.inputs["Geometry"])
        for m in rails:
            link_sockets(tree, m, join.inputs["Geometry"])
        return join.outputs["Geometry"]

    if kind == "canal":
        water = safe_node(tree, "GeometryNodeMeshGrid", (x - 400, y))
        water.inputs["Size X"].default_value = 4.0
        water.inputs["Size Y"].default_value = 1.5
        water.inputs["Vertices X"].default_value = 16
        water.inputs["Vertices Y"].default_value = 8
        walls = []
        for i in range(2):
            wall = safe_node(tree, "GeometryNodeMeshCube", (x - 400, y - 240 - i * 160))
            wall.inputs["Size"].default_value = (4.0, 0.4, 1.2)
            walls.append(wall.outputs["Mesh"])
        join = safe_node(tree, "GeometryNodeJoinGeometry", (x - 100, y))
        link_sockets(tree, water.outputs["Mesh"], join.inputs["Geometry"])
        for m in walls:
            link_sockets(tree, m, join.inputs["Geometry"])
        return join.outputs["Geometry"]

    if kind == "waterfall":
        sheet = safe_node(tree, "GeometryNodeMeshGrid", (x - 400, y))
        sheet.inputs["Size X"].default_value = 4.0
        sheet.inputs["Size Y"].default_value = 2.0
        sheet.inputs["Vertices X"].default_value = 16
        sheet.inputs["Vertices Y"].default_value = 8
        cascades = []
        for i in range(3):
            c = safe_node(tree, "GeometryNodeMeshCylinder", (x - 400 + i * 150, y - 260))
            c.inputs["Radius"].default_value = 0.15
            c.inputs["Depth"].default_value = 1.2
            c.inputs["Vertices"].default_value = 12
            c.fill_type = "NGON"
            cascades.append(c.outputs["Mesh"])
        join = safe_node(tree, "GeometryNodeJoinGeometry", (x - 100, y))
        link_sockets(tree, sheet.outputs["Mesh"], join.inputs["Geometry"])
        for m in cascades:
            link_sockets(tree, m, join.inputs["Geometry"])
        return join.outputs["Geometry"]

    if kind == "stage":
        apron = safe_node(tree, "GeometryNodeMeshCube", (x - 300, y))
        apron.inputs["Size"].default_value = (6.0, 3.0, 0.5)
        curtains = []
        for i in range(2):
            c = safe_node(tree, "GeometryNodeMeshCylinder", (x - 300 + i * 300, y - 240))
            c.inputs["Radius"].default_value = 1.2
            c.inputs["Depth"].default_value = 3.0
            c.inputs["Vertices"].default_value = 24
            c.fill_type = "NGON"
            curtains.append(c.outputs["Mesh"])
        join = safe_node(tree, "GeometryNodeJoinGeometry", (x - 100, y))
        link_sockets(tree, apron.outputs["Mesh"], join.inputs["Geometry"])
        for m in curtains:
            link_sockets(tree, m, join.inputs["Geometry"])
        return join.outputs["Geometry"]

    if kind == "shell":
        dome = safe_node(tree, "GeometryNodeMeshUVSphere", (x - 300, y))
        dome.inputs["Radius"].default_value = 2.0
        dome.inputs["Segments"].default_value = 32
        dome.inputs["Rings"].default_value = 12
        floor = safe_node(tree, "GeometryNodeMeshCube", (x - 300, y - 240))
        floor.inputs["Size"].default_value = (4.0, 3.0, 0.3)
        join = safe_node(tree, "GeometryNodeJoinGeometry", (x - 100, y))
        link_sockets(tree, dome.outputs["Mesh"], join.inputs["Geometry"])
        link_sockets(tree, floor.outputs["Mesh"], join.inputs["Geometry"])
        return join.outputs["Geometry"]

    if kind == "recital":
        walls = []
        for i in range(2):
            w = safe_node(tree, "GeometryNodeMeshCube", (x - 300 + i * 200, y))
            w.inputs["Size"].default_value = (0.4, 4.0, 3.0)
            walls.append(w.outputs["Mesh"])
        panels = []
        for i in range(3):
            p = safe_node(tree, "GeometryNodeMeshCube", (x - 300 + i * 120, y - 260))
            p.inputs["Size"].default_value = (0.08, 1.2, 0.6)
            panels.append(p.outputs["Mesh"])
        join = safe_node(tree, "GeometryNodeJoinGeometry", (x - 100, y))
        for m in walls + panels:
            link_sockets(tree, m, join.inputs["Geometry"])
        return join.outputs["Geometry"]

    # music fountain: stacked tiers + jet
    tiers = []
    for i, (r, d) in enumerate(((2.0, 0.6), (1.2, 0.6))):
        t = safe_node(tree, "GeometryNodeMeshCylinder", (x - 400 + i * 250, y))
        t.inputs["Radius"].default_value = r
        t.inputs["Depth"].default_value = d
        t.inputs["Vertices"].default_value = 32
        t.fill_type = "NGON"
        tiers.append(t.outputs["Mesh"])
    jet = safe_node(tree, "GeometryNodeMeshCone", (x - 400, y - 260))
    jet.inputs["Radius Bottom"].default_value = 0.2
    jet.inputs["Depth"].default_value = 0.9
    jet.inputs["Vertices"].default_value = 16
    jet.fill_type = "NGON"
    join = safe_node(tree, "GeometryNodeJoinGeometry", (x - 100, y))
    for m in tiers + [jet.outputs["Mesh"]]:
        link_sockets(tree, m, join.inputs["Geometry"])
    return join.outputs["Geometry"]


def _water_attributes(tree, gin, gout, geom):
    """Store the water-theme attribute contract on `geom` and output it."""
    bx = geom.node.location.x + 220
    by = geom.node.location.y

    store_wl = safe_node(tree, "GeometryNodeStoreNamedAttribute", (bx, by))
    store_wl.data_type = "FLOAT"
    store_wl.inputs["Name"].default_value = "water_level"
    link_sockets(tree, gin.outputs["Water Level"], store_wl.inputs["Value"])
    link_sockets(tree, geom, store_wl.inputs["Geometry"])

    store_cs = safe_node(tree, "GeometryNodeStoreNamedAttribute", (bx, by - 180))
    store_cs.data_type = "FLOAT"
    store_cs.inputs["Name"].default_value = "current_speed"
    link_sockets(tree, gin.outputs["Current Speed"], store_cs.inputs["Value"])
    link_sockets(tree, store_wl.outputs["Geometry"], store_cs.inputs["Geometry"])

    store_rc = safe_node(tree, "GeometryNodeStoreNamedAttribute", (bx, by - 360))
    store_rc.data_type = "FLOAT"
    store_rc.inputs["Name"].default_value = "ripple_carve"
    link_sockets(tree, gin.outputs["Ripple Carve"], store_rc.inputs["Value"])
    link_sockets(tree, store_cs.outputs["Geometry"], store_rc.inputs["Geometry"])
    link_sockets(tree, store_rc.outputs["Geometry"], gout.inputs["Geometry"])
    color_node(store_wl, "attribute")
    color_node(store_cs, "attribute")
    color_node(store_rc, "attribute")


def _music_attributes(tree, gin, gout, geom):
    """Store the music-theme attribute contract on `geom` and output it."""
    bx = geom.node.location.x + 220
    by = geom.node.location.y

    store_ic = safe_node(tree, "GeometryNodeStoreNamedAttribute", (bx, by))
    store_ic.data_type = "INT"
    store_ic.inputs["Name"].default_value = "instrument_count"
    link_sockets(tree, gin.outputs["Instrument Count"], store_ic.inputs["Value"])
    link_sockets(tree, geom, store_ic.inputs["Geometry"])

    store_t = safe_node(tree, "GeometryNodeStoreNamedAttribute", (bx, by - 180))
    store_t.data_type = "FLOAT"
    store_t.inputs["Name"].default_value = "tempo"
    link_sockets(tree, gin.outputs["Tempo"], store_t.inputs["Value"])
    link_sockets(tree, store_ic.outputs["Geometry"], store_t.inputs["Geometry"])

    store_nd = safe_node(tree, "GeometryNodeStoreNamedAttribute", (bx, by - 360))
    store_nd.data_type = "FLOAT"
    store_nd.inputs["Name"].default_value = "notation_density"
    link_sockets(tree, gin.outputs["Notation Density"], store_nd.inputs["Value"])
    link_sockets(tree, store_t.outputs["Geometry"], store_nd.inputs["Geometry"])
    link_sockets(tree, store_nd.outputs["Geometry"], gout.inputs["Geometry"])
    color_node(store_ic, "attribute")
    color_node(store_t, "attribute")
    color_node(store_nd, "attribute")


def _make_water_builder(kind):
    def _builder(group_name="MEL_water_them_" + kind):
        tree, gin, gout = new_geometry_tree(group_name)
        add_float_param(tree, "Water Level", 1.0, 0.0, 5.0)
        add_float_param(tree, "Current Speed", 1.0, 0.01, 10.0)
        add_float_param(tree, "Ripple Carve", 0.5, 0.0, 2.0)
        add_int_param(tree, "Debris Count", 10, 0, 50)
        add_bool_param(tree, "Floating", False)
        geom = _piece_geometry(kind, tree, gin, 0, 200)
        _water_attributes(tree, gin, gout, geom)
        return label_tree(tree, group_name, [
            {"title": "Inputs", "nodes": ("Group Input",), "role": "input"},
            {"title": "Piece", "nodes": ("cylinder", "cube", "grid", "torus", "sphere", "join"), "role": "geometry"},
            {"title": "Water Attributes", "nodes": ("store",), "role": "attribute"},
            {"title": "Output", "nodes": ("Group Output",), "role": "output"},
        ])
    _builder.__name__ = "build_water_them_" + kind
    return _builder


def _make_music_builder(kind):
    def _builder(group_name="MEL_music_them_" + kind):
        tree, gin, gout = new_geometry_tree(group_name)
        add_int_param(tree, "Instrument Count", 4, 0, 16)
        add_float_param(tree, "Notation Density", 0.5, 0.0, 2.0)
        add_int_param(tree, "Harmonic Panel Count", 4, 1, 16)
        add_float_param(tree, "Tempo", 120.0, 60.0, 180.0)
        add_bool_param(tree, "Has Score Lines", True)
        geom = _piece_geometry(kind, tree, gin, 0, 200)
        _music_attributes(tree, gin, gout, geom)
        return label_tree(tree, group_name, [
            {"title": "Inputs", "nodes": ("Group Input",), "role": "input"},
            {"title": "Piece", "nodes": ("cylinder", "cube", "grid", "torus", "sphere", "join"), "role": "geometry"},
            {"title": "Music Attributes", "nodes": ("store",), "role": "attribute"},
            {"title": "Output", "nodes": ("Group Output",), "role": "output"},
        ])
    _builder.__name__ = "build_music_them_" + kind
    return _builder


WATER_BUILDERS = {k: _make_water_builder(k) for k in _WATER_TYPES}
MUSIC_BUILDERS = {k: _make_music_builder(k) for k in _MUSIC_TYPES}
globals().update({("build_water_them_" + k): fn for k, fn in WATER_BUILDERS.items()})
globals().update({("build_music_them_" + k): fn for k, fn in MUSIC_BUILDERS.items()})

# -- Registry (24 variants) --
_WATER_DESC = {
    "structure": "Moat pavilion composite with water line, current speed, and ripple carving.",
    "gazebo": "Gazebo on a moat ring with ripple-carved base and floating markers.",
    "arch": "Water bridge arch with current markers and debris scatter.",
    "portico": "Canal-side portico with water line and current flow attributes.",
    "wall": "Canal wall with current flow markers and water stain gradient.",
    "curtain": "Water-stained curtain wall with depth gradient and debris.",
    "fountain": "Tiered fountain with basin jet and water attributes.",
    "dock": "Plank dock on posts with buoyancy floats.",
    "deck": "Floating deck platform with buoy markers.",
    "bridge": "Arched water bridge with twin rail lines.",
    "canal": "Canal channel — twin walls and water surface plane.",
    "waterfall": "Waterfall sheet with cascade tubes and splash markers.",
}
_MUSIC_DESC = {
    "structure": "Concert pavilion composite with instrument and tempo attributes.",
    "gazebo": "Concert pavilion with instrument miniatures and score line carves.",
    "arch": "Concert arch with notation carvings and harmonic panel markers.",
    "portico": "Opera house portico with harmonic panels and notation density.",
    "wall": "Rehearsal room wall with score line notches.",
    "curtain": "Stage backdrop curtain with score line gradient.",
    "bandstand": "Bandstand — drum, roof, stage with instrument count.",
    "stage": "Opera stage apron with curtain cylinders.",
    "shell": "Acoustic concert shell — dome and floor.",
    "recital": "Recital room — walls with acoustic panels.",
    "bridge": "Music bridge with staff-line rails.",
    "fountain": "Musical fountain — stacked tiers with jet.",
}
for _kind in _WATER_TYPES:
    register_builder(
        "MEL_water_them_" + _kind, WATER_BUILDERS[_kind],
        "Water-Themed " + _kind.replace("_", " ").title(),
        _WATER_DESC[_kind], "set_dressing", hidden=True, role="factory")
for _kind in _MUSIC_TYPES:
    register_builder(
        "MEL_music_them_" + _kind, MUSIC_BUILDERS[_kind],
        "Music-Themed " + _kind.replace("_", " ").title(),
        _MUSIC_DESC[_kind], "set_dressing", hidden=True, role="factory")
