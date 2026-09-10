import bpy
bpy.ops.wm.read_factory_settings(use_empty=True)
t = bpy.data.node_groups.new("Q3", "GeometryNodeTree")
for bid in ["GeometryNodeExtrudeMesh","GeometryNodeMeshGrid","GeometryNodeInputPosition","GeometryNodeMeshToPoints","ShaderNodeMath","ShaderNodeVectorMath","ShaderNodeCombineXYZ","ShaderNodeSeparateXYZ","GeometryNodeStoreNamedAttribute","GeometryNodeSetShadeSmooth"]:
    try:
        n = t.nodes.new(bid)
        print(bid, "OK IN:", [i.name for i in n.inputs][:6])
    except Exception as e:
        print(bid, "MISS:", str(e)[:80])
