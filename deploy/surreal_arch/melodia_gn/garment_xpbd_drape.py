"""Garment XPBD drape — research-lane wrapper over Blender 5.2's built-in Cloth Dynamics asset.

EXPERIMENTAL. Instantiates the built-in ``Cloth Dynamics (Experimental)`` node
group (ships with Blender 5.2 LTS in ``geometry_nodes_dynamics_assets.blend``;
the group already contains the XPBD Simulation zone, so this wrapper is a
single group node: shell geometry in, simulated geometry out) on an incoming
garment shell, exposing Pin Group plus silk-like defaults.

HARD LIMITS (verified Blender 5.2.1, 2026-09-03):
- Experimental asset: interface may shift between Blender releases.
- NO self-collision: layered shells (e.g. Underskirt + Skirt_Full) interpenetrate.
- Single shells only: drape one hero shell per modifier.
- Reference bake only: a headless bake informs (never replaces) in-editor UE
  Chaos cloth authoring. Tier B input, not a Tier B asset.

Pin Group is a per-vertex float mask (field): 0.0 = free, 1.0 = pinned to rest.
Default 0.0 (fully free drape); waistband pinning needs a painted mask or
vertex-group-to-attribute feed, not yet wired here.
"""

from __future__ import annotations

import os

import bpy  # noqa: F401  (builder runs inside Blender; needed for py parity)

from .core import (
    add_bool_param,
    add_float_param,
    add_int_param,
    label_tree,
    link_sockets,
    make_group_output,
    new_geometry_tree,
    register_builder,
    safe_node,
    sock,
)
from .logging import log

# Built-in dynamics asset library shipped with Blender 5.2 LTS.
DYNAMICS_LIB = os.path.join(
    os.path.dirname(bpy.app.binary_path),
    "5.2", "datafiles", "assets", "nodes",
    "geometry_nodes_dynamics_assets.blend",
)
CLOTH_GROUP_NAME = "Cloth Dynamics (Experimental)"

# First-guess silk defaults (structural softness low = near-inextensible,
# bending softness high = fluid folds). NOT artist-validated; tune per shell.
SILK_STRETCHINESS = 0.05
SILK_BENDINESS = 0.85


def ensure_cloth_group():
    """Append the built-in Cloth Dynamics group (deps auto-follow) or raise."""
    ng = bpy.data.node_groups.get(CLOTH_GROUP_NAME)
    if ng is not None:
        return ng
    if not os.path.isfile(DYNAMICS_LIB):
        raise RuntimeError(
            "XPBD dynamics asset library not found: %s "
            "(Blender 5.2 LTS required)" % DYNAMICS_LIB
        )
    try:
        with bpy.data.libraries.load(DYNAMICS_LIB, link=False) as (df, dt):
            dt.node_groups = [CLOTH_GROUP_NAME]
    except Exception as exc:
        raise RuntimeError(
            "Failed to append '%s' from %s: %s"
            % (CLOTH_GROUP_NAME, DYNAMICS_LIB, exc)
        )
    ng = bpy.data.node_groups.get(CLOTH_GROUP_NAME)
    if ng is None:
        raise RuntimeError(
            "Built-in asset '%s' missing from %s" % (CLOTH_GROUP_NAME, DYNAMICS_LIB)
        )
    log.info("garment_xpbd_drape: appended built-in '%s'", CLOTH_GROUP_NAME)
    return ng


def build_garment_xpbd_drape(group_name="MEL_garment_xpbd_drape"):
    """Drape an incoming garment shell through the built-in Cloth Dynamics group."""
    cloth_tree = ensure_cloth_group()
    tree, gin, gout = new_geometry_tree(group_name)

    add_float_param(tree, "Pin Group", 0.0, 0.0, 1.0)
    add_float_param(tree, "Stretchiness", SILK_STRETCHINESS, 0.0, 1.0)
    add_float_param(tree, "Bendiness", SILK_BENDINESS, 0.0, 1.0)
    add_int_param(tree, "Substeps", 5, 1, 64)
    add_int_param(tree, "Constraint Steps", 15, 1, 100)
    add_float_param(tree, "Mass", 1.0, 0.001, 100.0)
    add_float_param(tree, "Friction", 0.5, 0.0, 2.0)
    add_float_param(tree, "Collision Radius", 0.01, 0.0, 0.5)
    add_float_param(tree, "Linear Damping", 1.0, 0.0, 10.0)
    add_bool_param(tree, "Gravity", True)
    make_group_output(tree, "NodeSocketFloat", "Residual Error")

    cloth = safe_node(tree, "GeometryNodeGroup", (100, 0))
    if cloth is None:
        raise RuntimeError("GeometryNodeGroup node unavailable in %s" % group_name)
    cloth.node_tree = cloth_tree
    try:
        cloth.label = "Cloth Dynamics (built-in)"
    except Exception:
        pass

    link_sockets(tree, gin.outputs["Geometry"], sock(cloth, "Geometry"))
    for param in ("Pin Group", "Stretchiness", "Bendiness", "Substeps",
                  "Constraint Steps", "Mass", "Friction", "Collision Radius",
                  "Linear Damping", "Gravity"):
        target = sock(cloth, param)
        if target is None:
            raise RuntimeError(
                "Built-in Cloth group has no input '%s' — asset interface "
                "shifted under this Blender build; wrapper needs updating." % param
            )
        link_sockets(tree, gin.outputs[param], target)
    link_sockets(tree, sock(cloth, "Geometry", outputs=True), gout.inputs["Geometry"])
    link_sockets(
        tree, sock(cloth, "Residual Error", outputs=True),
        gout.inputs["Residual Error"],
    )
    return label_tree(tree, group_name, [
        {"title": "XPBD Drape", "nodes": ("cloth dynamics",), "role": "geometry"},
        {"title": "Sim Health", "nodes": ("residual",), "role": "output"},
    ])


register_builder("MEL_garment_xpbd_drape", build_garment_xpbd_drape,
                 "Garment XPBD Drape",
                 "Research-lane Cloth Dynamics drape over a garment shell (experimental, single-shell, no self-collision)",
                 "Garment")
