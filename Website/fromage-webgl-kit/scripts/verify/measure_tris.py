import bpy, os, sys, json

MODELS = r"C:\Users\froma\AppData\Local\Temp\ms-sub\wix\models"
FILES = [
    "SK_Melusina_Clothes_Production.fbx",
    "SK_Melusina_FullRig_Production.fbx",
    "SK_Melusina.fbx",
    "SK_SirMelodious_Clothed_Production.fbx",
    "SK_SirMelodious.fbx",
    "SK_Zundamon.fbx",
]

out = []
for name in FILES:
    fp = os.path.join(MODELS, name)
    if not os.path.isfile(fp):
        out.append({"file": name, "error": "not found"})
        continue
    # fresh scene each time
    bpy.ops.wm.read_factory_settings(use_empty=True)
    try:
        bpy.ops.import_scene.fbx(filepath=fp)
    except Exception as e:
        out.append({"file": name, "error": "import failed: %s" % e})
        continue
    tris = 0
    verts = 0
    meshes = 0
    for ob in bpy.data.objects:
        if ob.type != 'MESH':
            continue
        meshes += 1
        me = ob.data
        me.calc_loop_triangles()
        tris += len(me.loop_triangles)
        verts += len(me.vertices)
    out.append({"file": name, "meshes": meshes, "tris": tris, "verts": verts})

print("RESULT_JSON_START")
print(json.dumps(out, indent=2))
print("RESULT_JSON_END")
