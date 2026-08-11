
import unreal

anims_to_check = [
    "/Game/Melodia/Characters/Melusina/Animations/A_ThirdPersonIdle.A_ThirdPersonIdle",
    "/Game/Melodia/Characters/Melusina/Animations/A_ThirdPersonWalk.A_ThirdPersonWalk",
    "/Game/Melodia/Characters/Melusina/Animations/A_ThirdPersonRun.A_ThirdPersonRun",
    "/Game/Melodia/Characters/Melusina/Animations/A_ThirdPersonDash.A_ThirdPersonDash",
    "/Game/Melodia/Characters/Melusina/Animations/Mocap/A_Mocap_RunCycle_Sprint.A_Mocap_RunCycle_Sprint",
    "/Game/Melodia/Characters/Melusina/Animations/Mocap/A_Mocap_FairyWand.A_Mocap_FairyWand",
]

for path in anims_to_check:
    anim = unreal.load_asset(path)
    if anim:
        skel = anim.get_editor_property("skeleton")
        skel_name = skel.get_name() if skel else "None"
        anim_class = anim.get_class().get_name()
        num_frames = 0
        try:
            num_frames = anim.get_editor_property("num_frames")
        except:
            pass
        unreal.log(f"{path.split('/')[-1].split('.')[0]:30s} skel={skel_name:30s} frames={num_frames} class={anim_class}")
    else:
        unreal.log(f"{path.split('/')[-1].split('.')[0]:30s} NOT FOUND")
