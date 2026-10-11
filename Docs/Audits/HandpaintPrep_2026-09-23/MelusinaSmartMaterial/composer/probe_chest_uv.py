"""Chest-part UV occupancy grid (which cells of the chest's uv box hold UVs)."""
import bpy, sys
argv = sys.argv
argv = argv[argv.index("--") + 1:] if "--" in argv else []
fbx = argv[0]
bpy.ops.wm.read_factory_settings(use_empty=True)
bpy.ops.import_scene.fbx(filepath=fbx)
ob = None
for o in bpy.context.scene.objects:
    if o.type == "MESH" and o.name.endswith(".004"):
        ob = o
if ob is None:
    print("NO .004"); raise SystemExit(1)
uvl = ob.data.uv_layers.active
N = 16
grid = [[0] * N for _ in range(N)]
for l in uvl.data:
    u, v = l.uv[0], l.uv[1]
    gx = min(N - 1, int((u - 0.635) / (0.911 - 0.635) * N))
    gy = min(N - 1, int((v - 0.001) / (0.224 - 0.001) * N))
    if 0 <= gx < N and 0 <= gy < N:
        grid[gy][gx] += 1
# print grid top-down (v high -> low = image top -> bottom)
for row in reversed(grid):
    print(" ".join("%3d" % c for c in row))
print("BOX u 0.635-0.911 v 0.001-0.224 -> px x 1300-1866 y 1589-2046")
