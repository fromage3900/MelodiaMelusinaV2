
import unreal

result = {}

anims = [
    ("A_ThirdPersonIdle", "/Game/Melodia/Characters/Melusina/Animations/A_ThirdPersonIdle.A_ThirdPersonIdle"),
    ("A_ThirdPersonRun", "/Game/Melodia/Characters/Melusina/Animations/A_ThirdPersonRun.A_ThirdPersonRun"),
    ("A_Mocap_RunCycle_Sprint", "/Game/Melodia/Characters/Melusina/Animations/Mocap/A_Mocap_RunCycle_Sprint.A_Mocap_RunCycle_Sprint"),
    ("A_Mocap_Dodge", "/Game/Melodia/Characters/Melusina/Animations/Mocap/A_Mocap_Dodge.A_Mocap_Dodge"),
]

for name, path in anims:
    anim = unreal.load_asset(path)
    if anim:
        info = {}
        try:
            info["skeleton"] = str(anim.get_editor_property("skeleton"))
        except:
            info["skeleton"] = "ERR"
        try:
            info["num_frames"] = anim.get_editor_property("num_frames")
        except:
            info["num_frames"] = -1
        try:
            info["rate_scale"] = anim.get_editor_property("rate_scale")
        except:
            info["rate_scale"] = -1
        try:
            info["bone_names"] = [str(n) for n in (anim.get_editor_property("bone_names") or [])[:5]]
        except:
            info["bone_names"] = "ERR"
        try:
            info["has_root_bone"] = anim.get_editor_property("has_root_bone")
        except:
            info["has_root_bone"] = "ERR"
        result[name] = info
    else:
        result[name] = "NOT FOUND"

print(json.dumps(result))
