"""Runtime-contract audit for BP_Melusina and production locomotion."""
from __future__ import annotations

import json
import math
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
REPORT = ROOT / "Saved/Melodia/BP_Melusina_integration_audit.json"
BP = "/Game/Melodia/Characters/Melusina/BP_Melusina"
BODY = "/Game/Melodia/Characters/Melusina/SK_Melusina"
HAIR = "/Game/Melodia/Characters/Melusina/Hair/SK_MelusinaHair"
HAIR_ABP = "/Game/Melodia/Characters/Melusina/Hair/ABP_Melusina_WaterHair"
ABP = "/Game/Melodia/Characters/Melusina/ABP_Melusina_Current"
BLENDSPACE = "/Game/Melodia/Characters/Melusina/Animations/BS_Melusina_Locomotion"
LOCOMOTION = {
    "Idle": "/Game/Melodia/Characters/Melusina/Animations/Locomotion/A_Melusina_Idle",
    "Walk": "/Game/Melodia/Characters/Melusina/Animations/Locomotion/A_Melusina_Walk",
    "Run": "/Game/Melodia/Characters/Melusina/Animations/Locomotion/A_Melusina_Run",
    "Sprint": "/Game/Melodia/Characters/Melusina/Animations/Locomotion/A_Melusina_Sprint",
}


def _path(value) -> str:
    return value.get_path_name().split(".")[0] if value else ""


def _prop(obj, name, default=None):
    try:
        return obj.get_editor_property(name)
    except Exception:
        return default


def main() -> dict:
    import unreal

    failures: list[str] = []
    bp = unreal.EditorAssetLibrary.load_asset(BP)
    generated = bp.generated_class() if bp else None
    cdo = unreal.get_default_object(generated) if generated else None
    if bp:
        unreal.BlueprintEditorLibrary.compile_blueprint(bp)

    components = list(cdo.get_components_by_class(unreal.SkeletalMeshComponent)) if cdo else []
    body = next((c for c in components if c.get_name() == "CharacterMesh0"), None)
    hair = next((c for c in components if c.get_name() == "WaterHairMesh"), None)
    stale_hair = next((c for c in components if c.get_name() == "HairMesh"), None)

    relative_rotation = _prop(body, "relative_rotation")
    yaw = relative_rotation.yaw if relative_rotation else None
    body_mesh = _prop(body, "skeletal_mesh_asset") or _prop(body, "skeletal_mesh")
    anim_class = _prop(body, "anim_class")
    camera_relative = bool(_prop(cdo, "camera_relative_movement", _prop(cdo, "b_camera_relative_movement", False))) if cdo else False
    attach_parent = hair.get_attach_parent() if hair else None
    hair_anim_class = _prop(hair, "anim_class")

    if not bp or not generated or not cdo:
        failures.append("BP_Melusina did not resolve to a generated runtime class")
    if not body or not math.isclose(yaw or 0.0, -90.0, abs_tol=0.1):
        failures.append("CharacterMesh0 yaw is not -90 degrees")
    if not camera_relative:
        failures.append("camera-relative movement contract is disabled")
    if _path(body_mesh) != BODY:
        failures.append("runtime body mesh is not SK_Melusina")
    if not anim_class or not anim_class.get_path_name().startswith(ABP):
        failures.append("runtime AnimClass is not ABP_Melusina_Current")
    if not hair or stale_hair:
        failures.append("native WaterHairMesh is missing or stale Blueprint HairMesh remains")
    if hair and attach_parent is not body:
        failures.append("WaterHairMesh is not attached beneath CharacterMesh0")
    if hair and (not hair_anim_class or not hair_anim_class.get_path_name().startswith(HAIR_ABP)):
        failures.append("WaterHairMesh does not use the partial copy-pose AnimBP")

    blend = unreal.EditorAssetLibrary.load_asset(BLENDSPACE)
    samples = []
    if blend:
        for sample in _prop(blend, "sample_data", []) or []:
            animation = _prop(sample, "animation")
            value = _prop(sample, "sample_value")
            samples.append({"animation": _path(animation), "speed": float(value.x) if value else None})
    expected_samples = [
        (LOCOMOTION["Idle"], 0.0), (LOCOMOTION["Walk"], 180.0),
        (LOCOMOTION["Run"], 420.0), (LOCOMOTION["Sprint"], 630.0),
    ]
    sample_metadata_accessible = bool(samples)
    if sample_metadata_accessible:
        for path, speed in expected_samples:
            if not any(row["animation"] == path and row["speed"] is not None and math.isclose(row["speed"], speed, abs_tol=0.1) for row in samples):
                failures.append(f"missing production blendspace sample {path}@{speed}")
    elif not blend:
        failures.append("production blendspace does not load")

    sequences = {}
    for role, path in LOCOMOTION.items():
        sequence = unreal.EditorAssetLibrary.load_asset(path)
        loop = bool(_prop(sequence, "loop", False)) if sequence else False
        model = _prop(sequence, "data_model_interface") if sequence else None
        track_count = int(model.get_num_bone_tracks()) if model and hasattr(model, "get_num_bone_tracks") else 0
        sequences[role] = {"asset": path, "loads": bool(sequence), "loop": loop, "deform_track_count": track_count}
        if not sequence or not loop or track_count <= 0:
            failures.append(f"{role} is missing, non-looping, or has no animated bone tracks")

    result = {
        "asset": BP,
        "generated_class": generated.get_path_name() if generated else "",
        "runtime": {
            "camera_relative_movement": camera_relative,
            "body_mesh": _path(body_mesh),
            "body_yaw": yaw,
            "anim_class": anim_class.get_path_name() if anim_class else "",
            "hair_component": hair.get_name() if hair else "",
            "hair_attach_parent": attach_parent.get_name() if attach_parent else "",
            "hair_anim_class": hair_anim_class.get_path_name() if hair_anim_class else "",
            "hair_pose_policy": "attached-parent Copy Pose From Mesh",
            "stale_blueprint_hair_component": bool(stale_hair),
        },
        "blendspace": {
            "asset": BLENDSPACE,
            "samples": samples,
            "expected_samples": [{"animation": path, "speed": speed} for path, speed in expected_samples],
            "sample_metadata_accessible_in_editor_python": sample_metadata_accessible,
            "external_verification": "Monolith animation.get_blend_space_info",
        },
        "sequences": sequences,
        "manual_pie_required": [
            "camera-yaw-zero W/S/A/D displacement vectors",
            "mesh-facing dot movement direction > 0.9",
            "hair alignment throughout locomotion",
        ],
        "failures": failures,
        "ok": not failures,
    }
    REPORT.parent.mkdir(parents=True, exist_ok=True)
    REPORT.write_text(json.dumps(result, indent=2), encoding="utf-8")
    unreal.log("Melusina integration audit: " + json.dumps({"ok": result["ok"], "failures": failures}))
    return result


if __name__ == "__main__":
    main()
