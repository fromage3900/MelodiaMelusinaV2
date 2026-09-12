"""Report what's actually in the silhouette grid blend."""
import sys

import bpy

bpy.ops.wm.open_mainfile(filepath=r"P:/MelodiaMelusinaV2-Laptop/Saved/Accessories/Silhouette_Grid_v1.blend")

print("=== Silhouette Grid v1 Contents ===")
print(f"  Blend: {bpy.data.filepath}")
print(f"  Scene: {bpy.context.scene.name}")
print(f"  Engine: {bpy.context.scene.render.engine}")
print(f"  Resolution: {bpy.context.scene.render.resolution_x} x {bpy.context.scene.render.resolution_y}")
print()

print("Objects:")
for o in sorted(bpy.data.objects, key=lambda x: x.name):
    if o.type == 'EMPTY' and 'Eyewear' in o.name:
        mod_names = [m.name for m in o.modifiers]
        print(f"  {o.name:20s} loc=({o.location.x:.2f}, {o.location.y:.2f}, {o.location.z:.2f}) scale=({o.scale.x:.3f}) rot_x={o.rotation_euler.x:.2f} mods={mod_names}")
    elif o.type == 'CAMERA':
        print(f"  {o.name:20s} loc=({o.location.x:.2f}, {o.location.y:.2f}, {o.location.z:.2f}) lens={o.data.lens:.0f}mm clip_start={o.data.clip_start:.4f}")
    elif o.type == 'LIGHT':
        print(f"  {o.name:20s} type={o.data.type} energy={o.data.energy:.0f} loc=({o.location.x:.1f}, {o.location.y:.1f}, {o.location.z:.1f})")

print()
print("Modifier params per eyewear:")
for o in sorted(bpy.data.objects, key=lambda x: x.name):
    if o.type == 'EMPTY' and 'Eyewear' in o.name:
        for m in o.modifiers:
            if m.type == 'NODES' and m.node_group:
                print(f"\n  {o.name}:")
                for it in m.node_group.interface.items_tree:
                    if getattr(it, "in_out", None) == "INPUT":
                        n = getattr(it, "name", "")
                        if "Material" not in n and "UV" not in n:
                            try:
                                v = it.default_value
                                print(f"    {n:25s} = {v}")
                            except Exception:
                                print(f"    {n:25s} = (?)")

# Evaluate bounding boxes — convert empties to mesh to read GN output
print()
print("Evaluated bounding boxes:")
bpy.context.view_layer.update()
deps = bpy.context.evaluated_depsgraph_get()
for o in sorted(bpy.data.objects, key=lambda x: x.name):
    if o.type == 'EMPTY' and 'Eyewear' in o.name:
        ev = o.evaluated_get(deps)
        # Create a temporary mesh from the evaluated object
        me = bpy.data.meshes.new("__probe__")
        ev.to_mesh(me)
        if me.vertices:
            xs = [v.co.x for v in me.vertices]
            ys = [v.co.y for v in me.vertices]
            zs = [v.co.z for v in me.vertices]
            w = max(ys) - min(ys)
            h = max(zs) - min(zs)
            d = max(xs) - min(xs)
            print(f"  {o.name:15s} W={w*100:.1f}cm H={h*100:.1f}cm D={d*100:.1f}cm verts={len(me.vertices)}")
        else:
            print(f"  {o.name:15s} EMPTY OUTPUT")
        bpy.data.meshes.remove(me)

print()
print("DONE")
