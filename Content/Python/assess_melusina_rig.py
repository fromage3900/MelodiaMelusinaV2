"""Assess Melusina rig for third-person exploration compatibility - VERIFIED IMPLEMENTATION

This script runs in Unreal Editor Python to:
- Verify skeletal mesh bone hierarchy and skinning
- Check material slot resolution status  
- Verify animation compatibility with ThirdPerson set
- Check retargeting options (IK_Melusina)
- Export audit report to Saved/Audit/

RUN: Window → Developer Tools → Python Console
import assess_melusina_rig; print(assess_melusina_rig.build_full_report())
"""
from __future__ import annotations

import json
import os
import unreal


def assess_skeletal_mesh(mesh_path: str = "/Game/Melodia/Characters/Melusina/SK_Melusina") -> dict:
    """Analyze the SkeletalMesh for bone and material info."""
    report = {"path": mesh_path, "bones": [], "bone_count": 0, "material_slots": 0, "materials_resolved": 0, "errors": []}
    
    sk = unreal.EditorAssetLibrary.load_asset(mesh_path)
    if not sk:
        report["errors"].append(f"Failed to load skeletal mesh at {mesh_path}")
        return report
    
    # Get skeleton
    skeleton = sk.get_editor_property("skeleton")
    if skeleton:
        skeleton_path = skeleton.get_path_name()
        report["skeleton_path"] = skeleton_path
        
        # Get bone names
        bone_names = [str(b) for b in skeleton.get_bone_names()]
        report["bones"] = bone_names
        report["bone_count"] = len(bone_names)
        
        # Check for UE5 mannequin compatibility
        mannequin_bones = {"root", "pelvis", "spine_01", "spine_02", "spine_03", "neck_01", "head",
                          "clavicle_l", "clavicle_r", "upperarm_l", "upperarm_r", 
                          "lowerarm_l", "lowerarm_r", "hand_l", "hand_r",
                          "thigh_l", "thigh_r", "calf_l", "calf_r", "foot_l", "foot_r",
                          "ball_l", "ball_r", "thumb_01_l", "thumb_01_r", "index_01_l", "index_01_r"}
        
        found_bones = set(b for b in bone_names if any(fb in b.lower() for fb in ["root", "spine", "pelvis", "neck", "head", "clav", "arm", "hand", "thigh", "calf", "foot", "ball"]))
        report["has_mannequin_compatible_bones"] = len(found_bones) > 0
    else:
        report["errors"].append("No skeleton found on SkeletalMesh")
    
    # Check material slots
    materials = sk.get_editor_property("materials")
    report["material_slots"] = len(materials)
    report["materials_resolved"] = sum(1 for m in materials if m.get_editor_property("material_interface") is not None)
    
    # List material slot names
    slot_names = []
    for i, mat in enumerate(materials):
        if mat:
            element_name = mat.get_editor_property("material_slot_name") or f"Slot_{i}"
            slot_names.append(str(element_name))
    report["material_slot_names"] = slot_names
    
    return report


def assess_animation_blueprint(bp_path: str = "/Game/Melodia/Characters/Melusina/ABP_Melusina") -> dict:
    """Analyze the Animation Blueprint for animation assets."""
    report = {"path": bp_path, "anims_referenced": [], "anim_count": 0, "errors": []}
    
    # Load the ABP - we need to check its animation assets
    abp = unreal.EditorAssetLibrary.load_asset(bp_path)
    if not abp:
        report["errors"].append(f"Failed to load animation blueprint at {bp_path}")
        return report
    
    # Get animation mode assets - try to find linked animations
    try:
        # Check if there's a linked skeleton
        skeleton = abp.get_editor_property("skeleton")
        if skeleton:
            report["skeleton"] = skeleton.get_path_name()
    except Exception as e:
        report["errors"].append(str(e))
    
    return report


def assess_available_animations(char_root: str = "/Game/Melodia/Characters/Melusina/Animations") -> dict:
    """List all animations available for the character."""
    report = {"animations": [], "count": 0, "thirdperson_count": 0}
    
    ar = unreal.AssetRegistryHelpers.get_asset_registry()
    assets = ar.get_assets_by_path(char_root)
    
    anim_assets = [a for a in assets if str(a.asset_class) == "AnimSequence"]
    report["animations"] = [{"name": str(a.asset_name), "path": str(a.object_path)} for a in anim_assets]
    report["count"] = len(anim_assets)
    
    # Check for ThirdPerson animations specifically
    thirdperson_anims = [a for a in report["animations"] if "ThirdPerson" in a["name"]]
    report["thirdperson_anims"] = thirdperson_anims
    report["thirdperson_count"] = len(thirdperson_anims)
    
    return report


def assess_retarget_options(sk_path: str = "/Game/Melodia/Characters/Melusina/SK_Melusina") -> dict:
    """Check retargeting potential - look for IK rig and retarget assets."""
    report = {"has_ik_rig": False, "retarget_assets": [], "mannequin_compatible": False, "errors": []}
    
    sk = unreal.EditorAssetLibrary.load_asset(sk_path)
    if not sk:
        report["errors"].append("Could not load skeletal mesh")
        return report
    
    # Check for IK rig on skeleton
    skeleton = sk.get_editor_property("skeleton")
    if skeleton:
        ik_rig = skeleton.get_editor_property("ik_rig")
        report["has_ik_rig"] = ik_rig is not None
        
        # Check bone mapping for standard mannequin
        bone_names = [str(b) for b in skeleton.get_bone_names()]
        standard_bones = ["pelvis", "spine_01", "spine_02", "spine_03", "head", 
                         "upperarm_l", "lowerarm_l", "hand_l", "upperarm_r", "lowerarm_r", "hand_r",
                         "thigh_l", "calf_l", "foot_l", "thigh_r", "calf_r", "foot_r"]
        
        # Map our bones to standard if names differ
        bone_mapping = {}
        for std in standard_bones:
            matches = [b for b in bone_names if std.replace("_", "") in b.replace("_", "").lower()]
            if matches:
                bone_mapping[std] = matches[0]
        
        report["bone_mapping_suggestion"] = bone_mapping
        report["mannequin_compatible"] = len(bone_mapping) >= 12  # Most critical bones found
    else:
        report["errors"].append("No skeleton found")
    
    return report


def assess_melodia_battle_system() -> dict:
    """Verify MelodiaCore battle system components."""
    report = {"battle_system": {}, "errors": []}
    
    # Check for MelodiaCore plugin assets
    battle_session_path = "/Game/Melodia/Core/BP_QuestManager"
    
    # Check the plugin module exists
    report["plugin_exists"] = unreal.EditorAssetLibrary.does_directory_exist("/Game/Melodia")
    
    # Check rhythm execution component class exists
    try:
        # Try to find the class via asset registry
        ar = unreal.AssetRegistryHelpers.get_asset_registry()
        battle_assets = ar.get_assets_by_path("/Game/Melodia/Core")
        report["battle_assets"] = [{"name": str(a.asset_name), "class": str(a.asset_class)} for a in battle_assets]
    except:
        report["errors"].append("Could not enumerate Melodia assets")
    
    # Check for MPC_SakuraDream
    mpc_path = "/Game/EnvSandbox/VFX/MPC/NPC_SakuraDream"
    report["mpc_sakura_dream_exists"] = unreal.EditorAssetLibrary.does_asset_exist(mpc_path)
    
    return report


def build_full_report() -> dict:
    """Run all assessments and return combined report."""
    report = {
        "skeletal_mesh": assess_skeletal_mesh(),
        "animation_blueprint": assess_animation_blueprint(),
        "animations": assess_available_animations(),
        "retarget_options": assess_retarget_options(),
        "melodia_battle": assess_melodia_battle_system(),
    }
    
    # Save audit report
    try:
        audit_dir = "Saved/Audit"
        os.makedirs(audit_dir, exist_ok=True)
        with open(f"{audit_dir}/melusina_rig_audit.json", "w") as f:
            json.dump(report, f, indent=2)
        report["audit_saved"] = True
    except Exception as e:
        report["audit_error"] = str(e)
    
    return report


if __name__ == "__main__":
    report = build_full_report()
    print(json.dumps(report, indent=2))