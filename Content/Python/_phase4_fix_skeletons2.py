
import unreal
import json

result = {}
skel = unreal.load_asset("/Game/Melodia/Characters/Melusina/SK_Melusina_Skeleton.SK_Melusina_Skeleton")
anim = unreal.load_asset("/Game/Melodia/Characters/Melusina/Animations/A_ThirdPersonIdle.A_ThirdPersonIdle")

# Method 1: set_editor_property 
try:
    anim.set_editor_property("skeleton", skel)
    result["method1_set_editor"] = "OK"
except Exception as e:
    result["method1_set_editor"] = str(e)[:120]

# Method 2: Try the base AnimationAsset.set_skeleton if it exists
try:
    unreal.AnimationAsset.set_skeleton(anim, skel)
    result["method2_anim_set"] = "OK"
except Exception as e:
    result["method2_anim_set"] = str(e)[:120]

# Method 3: Try reflection-based approach
try:
    anim.set_editor_property("skel", skel)
    result["method3_skel"] = "OK"
except Exception as e:
    result["method3_skel"] = str(e)[:80]

# Method 4: Try setting via the skeleton's connect animation
try:
    skel.set_editor_property("preview_anim_blueprint", None)
    result["method4_skel_connect"] = "tried"
except Exception as e:
    result["method4_skel_connect"] = str(e)[:80]

# Method 5: Get all settable properties on AnimSequence
seq = unreal.load_asset("/Game/Melodia/Characters/Melusina/Animations/Mocap/A_Mocap_RunCycle_Sprint.A_Mocap_RunCycle_Sprint")
# Check which properties differ between one with skeleton and one without
result["anim_class"] = anim.get_class().get_name()

# Method 6: Try MelodiaAssetRepairLibrary
try:
    # Set skeleton directly on the animation via internal C++ helper
    repaired = unreal.MelodiaAssetRepairLibrary.set_animation_skeleton(anim, skel)
    result["method6_repaired"] = repaired
except Exception as e:
    result["method6_repaired"] = str(e)[:120]

# Method 7: Check if we can reimport with skeleton
try:
    # Use reimport manager
    from unreal import FbxAutomationUtils
    result["method7_fbx_auto"] = "would need file"
except Exception as e:
    result["method7_fbx_auto"] = str(e)[:80]

print(json.dumps(result))
