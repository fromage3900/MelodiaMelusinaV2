import bpy
bpy.ops.wm.read_factory_settings(use_empty=True)
t = bpy.data.node_groups.new("Q2", "GeometryNodeTree")
for bid in ["GeometryNodeSampleUVSurface","GeometryNodeDistributePointsOnFaces","GeometryNodeInstanceOnPoints","GeometryNodeCurveToMesh","GeometryNodeResampleCurve","GeometryNodeSetPosition","GeometryNodePickInstance" if hasattr(bpy.types,'GeometryNodePickInstance') else "GeometryNodeInstanceOnPoints"]:
    try:
        n = t.nodes.new(bid)
        print(bid, "OK IN:", [i.name for i in n.inputs][:8], "OUT:", [o.name for o in n.outputs][:6])
    except Exception as e:
        print(bid, "MISS:", str(e)[:100])
