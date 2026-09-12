"""Probe GeometryNodeUVUnwrap actual socket names on 5.2."""
import sys

import bpy

sys.path.insert(0, r"P:/MelodiaMelusinaV2-Laptop/deploy")

g = bpy.data.node_groups.new("probe", "GeometryNodeTree")
n = g.nodes.new("GeometryNodeUVUnwrap")
print("  UVUnwrap inputs : %s" % [s.name for s in n.inputs])
print("  UVUnwrap outputs: %s" % [s.name for s in n.outputs])
bpy.data.node_groups.remove(g)

g = bpy.data.node_groups.new("probe", "GeometryNodeTree")
n = g.nodes.new("GeometryNodeStoreNamedAttribute")
print("  StoreNamedAttr inputs : %s" % [s.name for s in n.inputs])
print("  StoreNamedAttr outputs: %s" % [s.name for s in n.outputs])
bpy.data.node_groups.remove(g)

g = bpy.data.node_groups.new("probe", "GeometryNodeTree")
n = g.nodes.new("GeometryNodeRealizeInstances")
print("  RealizeInstances inputs : %s" % [s.name for s in n.inputs])
print("  RealizeInstances outputs: %s" % [s.name for s in n.outputs])
bpy.data.node_groups.remove(g)
print("DONE")
