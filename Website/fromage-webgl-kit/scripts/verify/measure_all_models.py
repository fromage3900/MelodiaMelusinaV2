import bpy, os, re, json

KIT = r"C:\Users\froma\AppData\Local\Temp\ms-sub\wix"
HELPER = os.path.join(KIT, "melodia-3d-viewport.js")

src = open(HELPER, encoding="utf-8").read()
refs = sorted(set(re.findall(r"path:\s*'([^']+)'", src)))


def measure(fp):
    bpy.ops.wm.read_factory_settings(use_empty=True)
    ext = os.path.splitext(fp)[1].lower()
    if ext == ".fbx":
        bpy.ops.import_scene.fbx(filepath=fp)
    elif ext == ".glb" or ext == ".gltf":
        bpy.ops.import_scene.gltf(filepath=fp)
    elif ext == ".obj":
        bpy.ops.wm.obj_import(filepath=fp)
    else:
        raise ValueError("unsupported extension " + ext)
    tris = 0
    meshes = 0
    for ob in bpy.data.objects:
        if ob.type != 'MESH':
            continue
        meshes += 1
        me = ob.data
        me.calc_loop_triangles()
        tris += len(me.loop_triangles)
    return meshes, tris


out = []
for ref in refs:
    fp = os.path.join(KIT, ref.replace("/", os.sep))
    if not os.path.isfile(fp):
        out.append({"path": ref, "error": "MISSING"})
        continue
    try:
        meshes, tris = measure(fp)
        out.append({"path": ref, "meshes": meshes, "tris": tris})
    except Exception as e:
        out.append({"path": ref, "error": str(e)})

print("RESULT_JSON_START")
print(json.dumps(out, indent=2))
print("RESULT_JSON_END")
