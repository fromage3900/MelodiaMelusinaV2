"""Test UV unwrap — position-based planar projection."""
import sys

import bpy

sys.path.insert(0, r"P:/MelodiaMelusinaV2-Laptop/deploy")

tree = bpy.data.node_groups.new("test", "GeometryNodeTree")
tree.interface.new_socket("Geometry", in_out="INPUT", socket_type="NodeSocketGeometry")
tree.interface.new_socket("Geometry", in_out="OUTPUT", socket_type="NodeSocketGeometry")

gin = tree.nodes.new("NodeGroupInput")
gout = tree.nodes.new("NodeGroupOutput")

grid = tree.nodes.new("GeometryNodeMeshGrid")
grid.inputs["Size X"].default_value = 1.0
grid.inputs["Size Y"].default_value = 1.0
grid.inputs["Vertices X"].default_value = 4
grid.inputs["Vertices Y"].default_value = 4

# Position -> planar UV (divide by 1000 to get meters -> 0..1)
pos = tree.nodes.new("GeometryNodeInputPosition")
sep = tree.nodes.new("ShaderNodeSeparateXYZ")

# x_meters / 1000 + 0.5 → ~0..1 range for a ~1m object
div_x = tree.nodes.new("ShaderNodeMath")
div_x.operation = "DIVIDE"
div_x.inputs[1].default_value = 1000.0

div_y = tree.nodes.new("ShaderNodeMath")
div_y.operation = "DIVIDE"
div_y.inputs[1].default_value = 1000.0

add_x = tree.nodes.new("ShaderNodeMath")
add_x.operation = "ADD"
add_x.inputs[1].default_value = 0.5

add_y = tree.nodes.new("ShaderNodeMath")
add_y.operation = "ADD"
add_y.inputs[1].default_value = 0.5

comb = tree.nodes.new("ShaderNodeCombineXYZ")

store = tree.nodes.new("GeometryNodeStoreNamedAttribute")
store.data_type = "FLOAT2"
store.domain = "CORNER"
store.inputs["Name"].default_value = "UV"

# Link
tree.links.new(gin.outputs[0], grid.inputs[0])
tree.links.new(grid.outputs["Mesh"], store.inputs["Geometry"])
tree.links.new(pos.outputs["Position"], sep.inputs["Vector"])
tree.links.new(sep.outputs["X"], div_x.inputs[0])
tree.links.new(div_x.outputs[0], add_x.inputs[0])
tree.links.new(sep.outputs["Y"], div_y.inputs[0])
tree.links.new(div_y.outputs[0], add_y.inputs[0])
tree.links.new(add_x.outputs[0], comb.inputs["X"])
tree.links.new(add_y.outputs[0], comb.inputs["Y"])
tree.links.new(comb.outputs["Vector"], store.inputs["Value"])
tree.links.new(store.outputs["Geometry"], gout.inputs[0])

# Test
me = bpy.data.meshes.new("m")
ob = bpy.data.objects.new("o", me)
bpy.context.scene.collection.objects.link(ob)
mod = ob.modifiers.new("n", "NODES")
mod.node_group = tree
bpy.context.view_layer.update()
ev = ob.evaluated_get(bpy.context.evaluated_depsgraph_get())
m = ev.to_mesh()
print("verts:", len(m.vertices) if m else 0)
print("uv_layers:", [l.name for l in m.uv_layers] if m else [])
ob.modifiers.clear()
bpy.data.objects.remove(ob, do_unlink=True)
bpy.data.meshes.remove(me)
bpy.data.node_groups.remove(tree)
print("DONE")
