import os
import sys
from pathlib import Path

import bpy

ADDONS_ROOT = Path(__file__).resolve().parents[1]
if str(ADDONS_ROOT) not in sys.path:
    sys.path.insert(0, str(ADDONS_ROOT))
from melodia_utils import repo_root

showroom_dir = repo_root() / "Tools" / "MelodiaProceduralStudio" / "GeneratedScenes" / "showroom"
out_obj = showroom_dir / "terrain.obj"
if not out_obj.exists():
    raise FileNotFoundError("Showroom terrain is missing: %s" % out_obj)

# import using operator
before = set(bpy.data.objects)
bpy.ops.import_scene.obj(filepath=os.fspath(out_obj))
new_objects = [o for o in bpy.data.objects if o not in before]
imported = [o for o in new_objects if o.type == 'MESH']
for obj in new_objects:
    obj["melodia_debug_import"] = True
print('IMPORTED_MESHES=' + str(len(imported)))
for obj in imported:
    print('MESH=' + obj.name + '|VERTS=' + str(len(obj.data.vertices)) + '|FACES=' + str(len(obj.data.polygons)))

# frame scene manually
import math, mathutils
meshes = [o for o in bpy.context.scene.objects if o.type == 'MESH' and o.data]
print('SCENE_MESHES=' + str(len(meshes)))
for o in meshes:
    print('SCENE_MESH=' + o.name)
    bbox = [o.matrix_world @ mathutils.Vector(corner) for corner in o.bound_box]
    xs = [v.x for v in bbox]
    ys = [v.y for v in bbox]
    zs = [v.z for v in bbox]
    print('BOUNDS=' + str((min(xs),max(xs),min(ys),max(ys),min(zs),max(zs))))
