"""Turn a World Compiler harmony bundle heightmap into a terrain static-mesh FBX (headless Blender 5.2).

    blender -b --factory-startup --python Tools/harmony_heightmap_to_mesh.py -- <bundle_dir> <out_dir> [step]

Reads harmony.json + harmony_height.r16. The mesh pivot is the recipe anchor: vertex XY are offsets
from the chunk centre, vertex Z is height above anchor z (metres in Blender, cm after UE import).
`step` decimates the grid (1 = full 505², 2 = 253²). Place the imported mesh at the anchor.
"""
import json
import struct
import sys
from pathlib import Path

import bpy
import numpy as np

argv = sys.argv[sys.argv.index("--") + 1:]
bundle, out_dir = Path(argv[0]), Path(argv[1])
step = int(argv[2]) if len(argv) > 2 else 1
meta = json.loads((bundle / "harmony.json").read_text(encoding="utf-8"))
res = meta["resolution"]
raw = (bundle / meta["heightmap"]["file"]).read_bytes()
grid = np.array(struct.unpack(f"<{res * res}H", raw), dtype=np.float64).reshape(res, res)  # [row=y][col=x]
z0 = meta["z_min_cm"] - meta["anchor_cm"][2]
span = meta["z_max_cm"] - meta["z_min_cm"]
heights_cm = z0 + grid / 65535.0 * span
heights_cm = heights_cm[::step, ::step]
n = heights_cm.shape[0]
half_m = meta["size_cm"] / 200.0
coords = np.linspace(-half_m, half_m, n)
xs, ys = np.meshgrid(coords, coords)                # ys varies by row (= +y), xs by column (= +x)
# Blender->UE FBX import flips Y (right- to left-handed): author -Y so UE +Y matches the bundle.
verts = np.stack([xs, -ys, heights_cm / 100.0], axis=-1).reshape(-1, 3)

idx = np.arange(n * n).reshape(n, n)
quads = np.stack([idx[:-1, :-1], idx[1:, :-1], idx[1:, 1:], idx[:-1, 1:]], axis=-1).reshape(-1, 4)  # CCW after the Y flip

bpy.ops.wm.read_factory_settings(use_empty=True)
bpy.context.scene.unit_settings.system = "METRIC"
bpy.context.scene.unit_settings.scale_length = 1.0
name = f"SM_Harmony_{bundle.name}"
mesh = bpy.data.meshes.new(name)
mesh.vertices.add(len(verts))
mesh.vertices.foreach_set("co", verts.ravel())
mesh.loops.add(quads.size)
mesh.loops.foreach_set("vertex_index", quads.ravel())
mesh.polygons.add(len(quads))
mesh.polygons.foreach_set("loop_start", np.arange(0, quads.size, 4))
mesh.polygons.foreach_set("loop_total", np.full(len(quads), 4))
uv = mesh.uv_layers.new(name="UVTerrain")
uvs = (np.stack([xs, ys], axis=-1).reshape(-1, 2) + half_m) / (2.0 * half_m)
uv.data.foreach_set("uv", uvs[quads.ravel()].ravel())
mesh.update(calc_edges=True)
mesh.validate()
mesh.shade_smooth()
obj = bpy.data.objects.new(name, mesh)
bpy.context.scene.collection.objects.link(obj)
obj.select_set(True)
bpy.context.view_layer.objects.active = obj

out_dir.mkdir(parents=True, exist_ok=True)
fbx = out_dir / f"{name}.fbx"
bpy.ops.export_scene.fbx(filepath=str(fbx), use_selection=True, object_types={"MESH"}, apply_unit_scale=True,
                         apply_scale_options="FBX_SCALE_NONE", axis_forward="-Y", axis_up="Z",
                         mesh_smooth_type="FACE", add_leaf_bones=False, bake_anim=False)
report = {"mesh": name, "grid": n, "verts": len(mesh.vertices), "faces": len(mesh.polygons),
          "z_range_cm": [float(heights_cm.min()), float(heights_cm.max())], "size_m": 2 * half_m,
          "fbx": str(fbx).replace("\\", "/"), "fbx_bytes": fbx.stat().st_size,
          "place_at_cm": meta["anchor_cm"]}
(out_dir / f"{name}.json").write_text(json.dumps(report, indent=2) + "\n", encoding="utf-8")
print("HARMONY_MESH", json.dumps(report))
