"""Probe Mesh Line / Vector socket names on the running Blender.

Context: `MEL_chime_aeolian_wall` logs
    link_float_to_vector: 'End Location' input not found on node 'Mesh Line'
so the wall's span wiring silently no-ops. Same family as the 5.2 renames in
`core.NODE_REMAP_52`, but a SOCKET rename rather than a node rename, which that
table cannot cover. Report the real input names instead of guessing.
"""
import sys

import bpy

ng = bpy.data.node_groups.new("__socket_probe__", "GeometryNodeTree")
try:
    ln = ng.nodes.new("GeometryNodeMeshLine")
    print("GeometryNodeMeshLine inputs:", [s.name for s in ln.inputs])
    print("GeometryNodeMeshLine mode:", getattr(ln, "mode", "?"))
    try:
        ln.mode = "OFFSET"
        print("after OFFSET:", [s.name for s in ln.inputs])
        ln.mode = "END_POINTS"
        print("after END_POINTS:", [s.name for s in ln.inputs])
    except Exception as exc:
        print("mode set failed:", exc)

    off = ng.nodes.new("GeometryNodeSetPosition")
    print("GeometryNodeSetPosition inputs:", [s.name for s in off.inputs])
finally:
    bpy.data.node_groups.remove(ng)