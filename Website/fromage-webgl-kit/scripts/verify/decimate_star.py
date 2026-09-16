import bpy, os, json

SRC = r"C:\Users\froma\AppData\Local\Temp\ms-sub\wix\models\SM_MelodyToken_Star.fbx"
OUT = r"C:\Users\froma\AppData\Local\Temp\ms-sub\wix\models\SM_MelodyToken_Star_Web.fbx"
TARGET = 6000

bpy.ops.wm.read_factory_settings(use_empty=True)
bpy.ops.import_scene.fbx(filepath=SRC)

before = 0
for ob in bpy.data.objects:
    if ob.type == 'MESH':
        ob.data.calc_loop_triangles()
        before += len(ob.data.loop_triangles)

mods = 0
for ob in list(bpy.data.objects):
    if ob.type != 'MESH':
        continue
    ob.data.calc_loop_triangles()
    t = len(ob.data.loop_triangles)
    if t == 0:
        continue
    ratio = max(0.0001, min(1.0, TARGET / float(before)))
    m = ob.modifiers.new(name="WebDecimate", type='DECIMATE')
    m.decimate_type = 'COLLAPSE'
    m.ratio = ratio
    # apply
    bpy.context.view_layer.objects.active = ob
    ob.select_set(True)
    bpy.ops.object.modifier_apply(modifier=m.name)
    mods += 1

after = 0
for ob in bpy.data.objects:
    if ob.type == 'MESH':
        ob.data.calc_loop_triangles()
        after += len(ob.data.loop_triangles)

bpy.ops.export_scene.fbx(filepath=OUT, use_selection=False, apply_scale_options='FBX_SCALE_ALL')

print("RESULT_JSON_START")
print(json.dumps({
    "before": before,
    "after": after,
    "modifiers_applied": mods,
    "out": OUT,
    "out_bytes": os.path.getsize(OUT) if os.path.isfile(OUT) else None,
}, indent=1))
print("RESULT_JSON_END")
