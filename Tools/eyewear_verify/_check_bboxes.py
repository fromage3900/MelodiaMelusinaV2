import bpy
import sys
import json

# Open the saved blend file
bpy.ops.wm.open_mainfile(filepath=r"P:/MelodiaMelusinaV2-Laptop/Saved/Accessories/Silhouette_Grid_v1.blend")

results = []
for obj in bpy.data.objects:
    if obj.name.startswith("Eyewear_"):
        # Update depsgraph to ensure modifiers are evaluated
        depsgraph = bpy.context.evaluated_depsgraph_get()
        eval_obj = obj.evaluated_get(depsgraph)
        
        # Get bounding box in world space
        bbox_corners = [obj.matrix_world @ mathutils.Vector(corner) for corner in obj.bound_box]
        
        xs = [v.x for v in bbox_corners]
        ys = [v.y for v in bbox_corners]
        zs = [v.z for v in bbox_corners]
        
        # Also check evaluated mesh vertex count
        mesh = eval_obj.to_mesh()
        vert_count = len(mesh.vertices) if mesh else 0
        
        import mathutils
        
        results.append({
            "name": obj.name,
            "location": list(obj.location),
            "rotation_euler": list(obj.rotation_euler),
            "scale": list(obj.scale),
            "type": obj.type,
            "vertex_count": vert_count,
            "bbox_min": [min(xs), min(ys), min(zs)],
            "bbox_max": [max(xs), max(ys), max(zs)],
            "bbox_center": [(min(xs)+max(xs))/2, (min(ys)+max(ys))/2, (min(zs)+max(zs))/2],
            "dimensions": [max(xs)-min(xs), max(ys)-min(ys), max(zs)-min(zs)],
        })
        
        print(f"\n{obj.name}:")
        print(f"  Type: {obj.type}")
        print(f"  Rotation: {[f'{r:.4f}' for r in obj.rotation_euler]}")
        print(f"  Scale: {list(obj.scale)}")
        print(f"  Vertex count (evaluated): {vert_count}")
        print(f"  Bounding box min: [{min(xs):.4f}, {min(ys):.4f}, {min(zs):.4f}]")
        print(f"  Bounding box max: [{max(xs):.4f}, {max(ys):.4f}, {max(zs):.4f}]")
        print(f"  Dimensions: [{max(xs)-min(xs):.4f}, {max(ys)-min(ys):.4f}, {max(zs)-min(zs):.4f}]")

print("\n=== SUMMARY ===")
for r in results:
    print(f"{r['name']}: {r['type']}, verts={r['vertex_count']}, dims={[round(d,4) for d in r['dimensions']]}")
