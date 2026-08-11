
import unreal, json
# Check an existing source animation to understand the skeleton
anim = unreal.load_asset('/Game/Melodia/Mocap/Source/Anims/A_Src_Dodge.A_Src_Dodge')
result = {}
if anim:
    result['path'] = '/Game/Melodia/Mocap/Source/Anims/A_Src_Dodge'
    result['class'] = anim.get_class().get_name()
    try:
        skel = anim.get_editor_property('skeleton')
        result['skeleton'] = skel.get_path_name() if skel else None
    except:
        result['skeleton_error'] = 'no skeleton prop'
    try:
        rate = anim.get_editor_property('rate_scale')
        result['rate_scale'] = rate
    except:
        pass
    # Check bone names
    try:
        bones = anim.get_editor_property('bone_names')
        result['bone_count'] = len(bones) if bones else 0
        if bones:
            result['first_bones'] = bones[:5]
    except:
        result['bones_error'] = 'no bone_names'
else:
    result['error'] = 'Cannot load animation'

print(json.dumps(result))
