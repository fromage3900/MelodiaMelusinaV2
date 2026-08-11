import unreal, json
ui = unreal.FbxImportUI()
result = {"skeleton_settable": False, "anim_seq_props": []}
try:
    skel = unreal.load_asset('/Game/Melodia/Mocap/Source/SK_MocapSource_Skeleton.SK_MocapSource_Skeleton')
    ui.set_editor_property('skeleton', skel)
    result["skeleton_settable"] = True
except Exception as e:
    result["skeleton_error"] = str(e)[:100]
anim = unreal.FbxAnimSequenceImportData()
props = [p for p in dir(anim) if not p.startswith('_') and not p.startswith('set_') and not p.startswith('get_')]
result["anim_seq_props"] = props
print(json.dumps(result))
