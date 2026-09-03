"""Runtime-component audit for Melusina's dedicated water hair."""
from __future__ import annotations

import json
from pathlib import Path

PROJECT = Path(__file__).resolve().parents[2]
REPORT = PROJECT / "Saved/Audit/melusina_water_hair_audit.json"
BP = "/Game/Melodia/Characters/Melusina/BP_Melusina"
INSTANCE = "/Game/EnvSandbox/Materials/Instances/Melusina/MI_Melusina_WaterHair"
PARENT = "/Game/EnvSandbox/Materials/Masters/M_Water_Master_Grand_v6"
MESH = "/Game/Melodia/Characters/Melusina/Hair/SK_MelusinaHair"
HAIR_ABP = "/Game/Melodia/Characters/Melusina/Hair/ABP_Melusina_WaterHair"
EXPECTED = {"GerstnerScale": 0.0, "WaveSpeed": 0.0, "RefractionStrength": 0.0,
            "ShorelineWidth": 0.0, "ShorelineFoam": 0.0, "DepthFadeDistance": 0.0}


def main() -> dict:
    import unreal

    bp = unreal.EditorAssetLibrary.load_asset(BP)
    generated = bp.generated_class() if bp else None
    cdo = unreal.get_default_object(generated) if generated else None
    components = list(cdo.get_components_by_class(unreal.SkeletalMeshComponent)) if cdo else []
    body = next((c for c in components if c.get_name() == "CharacterMesh0"), None)
    hair = next((c for c in components if c.get_name() == "WaterHairMesh"), None)
    mi = unreal.EditorAssetLibrary.load_asset(INSTANCE)
    safe = {}
    if mi:
        for name, expected in EXPECTED.items():
            value = unreal.MaterialEditingLibrary.get_material_instance_scalar_parameter_value(mi, name)
            safe[name] = {"value": float(value), "expected": expected, "ok": abs(value - expected) < 0.0001}
    runtime_materials = list(hair.get_materials()) if hair else []
    hair_anim_class = hair.get_editor_property("anim_class") if hair else None
    checks = {
        "native_component_exists": bool(hair),
        "mesh_matches": bool(hair and (hair.get_editor_property("skeletal_mesh_asset") or hair.get_editor_property("skeletal_mesh")).get_path_name().startswith(MESH)),
        "attached_to_body": bool(hair and hair.get_attach_parent() is body),
        "copy_pose_anim_class": bool(hair_anim_class and hair_anim_class.get_path_name().startswith(HAIR_ABP)),
        "runtime_slot_count": len(runtime_materials),
        "runtime_slots_use_instance": len(runtime_materials) == 4 and all(m and m.get_path_name().startswith(INSTANCE) for m in runtime_materials),
        "parent_matches": bool(mi and mi.get_editor_property("parent").get_path_name().startswith(PARENT)),
        "safe_overrides": safe,
    }
    failures = [name for name, value in checks.items() if name != "safe_overrides" and not value]
    failures.extend(name for name, value in safe.items() if not value["ok"])
    result = {"blueprint": BP, "instance": INSTANCE, "runtime_component": "WaterHairMesh",
              "checks": checks, "failures": failures, "ok": not failures}
    REPORT.parent.mkdir(parents=True, exist_ok=True)
    REPORT.write_text(json.dumps(result, indent=2), encoding="utf-8")
    unreal.log("Melusina water hair audit: " + json.dumps({"ok": result["ok"], "failures": failures}))
    return result


if __name__ == "__main__":
    main()
