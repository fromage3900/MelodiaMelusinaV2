import bpy, os, json

MODELS = r"C:\Users\froma\AppData\Local\Temp\ms-sub\wix\models"
files = sorted(f for f in os.listdir(MODELS) if f.lower().endswith((".fbx", ".obj", ".glb", ".gltf")))


def measure(fp):
    bpy.ops.wm.read_factory_settings(use_empty=True)
    ext = os.path.splitext(fp)[1].lower()
    if ext == ".fbx":
        bpy.ops.import_scene.fbx(filepath=fp)
    elif ext in (".glb", ".gltf"):
        bpy.ops.import_scene.gltf(filepath=fp)
    elif ext == ".obj":
        bpy.ops.wm.obj_import(filepath=fp)
    else:
        raise ValueError(ext)
    tris = 0
    meshes = 0
    for ob in bpy.data.objects:
        if ob.type != 'MESH':
            continue
        meshes += 1
        ob.data.calc_loop_triangles()
        tris += len(ob.data.loop_triangles)
    return meshes, tris


out = []
for f in files:
    fp = os.path.join(MODELS, f)
    try:
        meshes, tris = measure(fp)
        out.append({"file": f, "meshes": meshes, "tris": tris, "bytes": os.path.getsize(fp)})
    except Exception as e:
        out.append({"file": f, "error": str(e)})

out.sort(key=lambda d: d.get("tris", -1))
print("RESULT_JSON_START")
print(json.dumps(out, indent=1))
print("RESULT_JSON_END")
