"""Shared finishing stage for the Melusina regalia.

The four pieces so far were swept tubes and instanced primitives -- fine for
placement, poor as objects. A tube has no thickness, no rim, and no clean
normal flow, so gold renders as wire instead of cast metal.

This module wraps the house's own mesh_tools / geometry_extras builders:

    build_auto_bevel      edge-angle weighted bevel + shade smooth.
                          Its docstring: "Mirrors Infinity Nikki soft bevel
                          look: crisp edges stay sharp, flat areas stay soft."
    build_shell_thicken   Extrude Mesh in FACES mode; Solid on joins the
                          original back into a closed shell.

Both are PURE GEOMETRY NODES, so they survive FBX export -- unlike a modifier
stack or MESHmachine, neither of which is needed for this stage.

Proven, not assumed: a unit cube through build_auto_bevel with Width 0.02 /
Segments 3 / Profile 0.5 / Angle Threshold 30 measured 8 verts / 6 faces ->
96 verts / 98 faces.
"""

from __future__ import annotations

import math

import bpy

HERE = r"C:\EnvironmentPortfolio\BS_GodFile\Saved\Audit\regalia"
HOUSE_ADDONS = r"C:\Users\froma\AppData\Roaming\Blender Foundation\Blender\5.2\scripts\addons"


def _import_house():
    """Import the house package. surreal_arch must be on sys.path: melodia_gn /
    stack.py does `from ..branding import N_PANEL_CATEGORY`, so importing the
    subpackage directly raises "attempted relative import beyond top-level
    package"."""
    import sys
    if HOUSE_ADDONS not in sys.path:
        sys.path.insert(0, HOUSE_ADDONS)
    from surreal_arch.melodia_gn import mesh_tools, geometry_extras
    return {"mesh_tools": mesh_tools, "geometry_extras": geometry_extras}


def _group_node(tree, group_name, builder, loc, params=None):
    """Create a GeometryNodeGroup and return its node.

    USE THE BUILDER'S RETURN VALUE. A house builder may return the tree WITHOUT
    registering it under the requested name -- build_star_finial("X") returned a
    tree, yet bpy.data.node_groups.get("X") stayed None, so node_tree was None,
    outputs was empty, and every outputs["Geometry"] raised KeyError.
    """
    ng = bpy.data.node_groups.get(group_name)
    if ng is None and builder is not None:
        built = builder(group_name)
        if isinstance(built, (tuple, list)):
            built = built[0]
        ng = built
    if ng is None:
        print("REGALIA-FINISH-WARN unresolvable house group %s" % group_name)
        return None
    node = tree.nodes.new("GeometryNodeGroup")
    node.location = loc
    node.node_tree = ng
    for k, v in (params or {}).items():
        if k in node.inputs:
            node.inputs[k].default_value = v
    return node


def build_finish_stage(tree, geometry, base_x=-2600, base_y=-900,
                       thickness=0.0016,
                       bevel_width=0.0006,
                       bevel_segments=3,
                       bevel_profile=0.5,
                       angle_threshold=30.0,
                       do_thicken=True,
                       do_bevel=True,
                       label="regalia"):
    """Return a socket carrying `geometry` thickened and bevelled.

    thickness    metres; 0.0016 = 1.6 mm band wall, right for cast gold
    bevel_width  metres; 0.0006 = 0.6 mm rim highlight. This is the single
                 biggest readability win on metal: a hard-edged tube reads as
                 wire, a chamfered one reads as cast.
    """
    mods = _import_house()

    out = geometry
    x = base_x

    if do_thicken:
        th = _group_node(tree, "MEL_regalia_thicken_%s" % label,
                         mods["geometry_extras"].build_shell_thicken,
                         (x, base_y),
                         params={"Thickness": thickness, "Solid": True})
        if th is None:
            print("REGALIA-FINISH-WARN no thicken node; passing through")
        else:
            tree.links.new(geometry, th.inputs["Geometry"])
            out = th.outputs["Geometry"]
            x -= 260

    if do_bevel:
        bv = _group_node(tree, "MEL_regalia_bevel_%s" % label,
                         mods["mesh_tools"].build_auto_bevel,
                         (x, base_y),
                         params={"Width": bevel_width,
                                 "Segments": bevel_segments,
                                 "Profile": bevel_profile,
                                 "Angle Threshold": angle_threshold,
                                 "Shade Smooth": True})
        if bv is None:
            print("REGALIA-FINISH-WARN no bevel node; passing through")
        else:
            tree.links.new(out, bv.inputs["Geometry"])
            out = bv.outputs["Geometry"]
            x -= 260

    return out


def build_thicken_only(tree, geometry, loc=(-2600, -900), thickness=0.0016,
                       label="regalia"):
    """Solidify without bevel. For pieces whose surface is already curved and
    smooth (a pearl, a sphere) a bevel adds nothing and risks self-intersection
    on thin shells."""
    return build_finish_stage(tree, loc[0], loc[1], thickness=thickness,
                              do_thicken=True, do_bevel=False, label=label)
