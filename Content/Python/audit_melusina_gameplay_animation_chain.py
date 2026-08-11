"""Read-only audit of Melusina exploration and JRPG battle animation chains."""
import json
from pathlib import Path
import unreal

ROOT = Path(unreal.Paths.project_dir())
OUT = ROOT / "Saved" / "Audit" / "melusina_gameplay_animation_chain.json"
ASSETS = {
    "exploration": "/Game/MelodiaIntegration/Blueprints/BP_MelusinaJRPGCharacter",
    "exploration_abp": "/Game/Melodia/Characters/Melusina/ABP_Melusina_Current",
    "battle": "/Game/Experiments/MelodiaJRPG/BP_MelusinaSwordsman_Presentation",
    "battle_abp": "/Game/Experiments/MelodiaJRPG/ABP_Melusina_JRPGPresentation",
    "locomotion_blendspace": "/Game/Melodia/Characters/Melusina/Animations/BS_Melusina_Locomotion",
    "battle_attack_montage": "/Game/Melodia/Characters/Melusina/Animations/AM_Mocap_BasicAttack",
}


def path(value):
    return value.get_path_name().split(".")[0] if value else ""


def prop(obj, *names):
    for name in names:
        try:
            value = obj.get_editor_property(name)
            if value is not None:
                return value
        except Exception:
            pass
    return None


def load(asset_path):
    return unreal.EditorAssetLibrary.load_asset(asset_path)


def bp_cdo(asset_path):
    bp = load(asset_path)
    if not bp:
        return None, None, None
    unreal.BlueprintEditorLibrary.compile_blueprint(bp)
    generated = bp.generated_class()
    return bp, generated, unreal.get_default_object(generated) if generated else None


def component_contract(asset_path):
    bp, generated, cdo = bp_cdo(asset_path)
    meshes = list(cdo.get_components_by_class(unreal.SkeletalMeshComponent)) if cdo else []
    rows = []
    for comp in meshes:
        mesh = prop(comp, "skeletal_mesh_asset", "skeletal_mesh")
        anim_class = prop(comp, "anim_class")
        skeleton = prop(mesh, "skeleton") if mesh else None
        rows.append({
            "component": comp.get_name(),
            "mesh": path(mesh),
            "skeleton": path(skeleton),
            "anim_class": anim_class.get_path_name() if anim_class else "",
            "animation_mode": str(prop(comp, "animation_mode")),
        })
    parent = prop(bp, "parent_class")
    return {
        "loads": bool(bp and generated and cdo),
        "generated_class": generated.get_path_name() if generated else "",
        "parent_class": parent.get_path_name() if parent else "",
        "skeletal_components": rows,
    }


registry = unreal.AssetRegistryHelpers.get_asset_registry()
options = unreal.AssetRegistryDependencyOptions(
    include_soft_package_references=True,
    include_hard_package_references=True,
    include_searchable_names=False,
    include_soft_management_references=False,
    include_hard_management_references=False,
)


def dependencies(asset_path):
    package = unreal.Name(asset_path)
    deps = [str(item) for item in registry.get_dependencies(package, options)]
    rows = []
    for dep in sorted(set(deps)):
        data = registry.get_asset_by_object_path(unreal.Name(f"{dep}.{dep.rsplit('/', 1)[-1]}"))
        class_name = str(data.asset_class_path.asset_name) if data and data.is_valid() else ""
        if class_name in {"AnimSequence", "AnimMontage", "BlendSpace", "AimOffsetBlendSpace", "AnimBlueprint", "SkeletalMesh", "Skeleton"}:
            obj = load(dep)
            skeleton = prop(obj, "skeleton", "target_skeleton") if obj else None
            rows.append({"asset": dep, "class": class_name, "skeleton": path(skeleton)})
    return rows


report = {
    "exploration": component_contract(ASSETS["exploration"]),
    "battle": component_contract(ASSETS["battle"]),
    "exploration_animation_dependencies": dependencies(ASSETS["exploration_abp"]) + dependencies(ASSETS["locomotion_blendspace"]),
    "battle_animation_dependencies": dependencies(ASSETS["battle"]) + dependencies(ASSETS["battle_abp"]) + dependencies(ASSETS["battle_attack_montage"]),
    "assets": ASSETS,
}

# Evaluate compatibility against the body skeleton configured on each character.
for key, dep_key in (("exploration", "exploration_animation_dependencies"), ("battle", "battle_animation_dependencies")):
    body_rows = report[key]["skeletal_components"]
    body = next((row for row in body_rows if row["component"] == "CharacterMesh0"), body_rows[0] if body_rows else None)
    body_skeleton = body["skeleton"] if body else ""
    incompatible = [row for row in report[dep_key] if row["skeleton"] and body_skeleton and row["skeleton"] != body_skeleton]
    report[key]["body_skeleton"] = body_skeleton
    report[key]["incompatible_animation_assets"] = incompatible
    report[key]["skeleton_compatible"] = bool(body_skeleton) and not incompatible

OUT.parent.mkdir(parents=True, exist_ok=True)
OUT.write_text(json.dumps(report, indent=2), encoding="utf-8")
unreal.log("MELUSINA_ANIMATION_AUDIT: " + json.dumps({
    "exploration_anim_class": next((r["anim_class"] for r in report["exploration"]["skeletal_components"] if r["component"] == "CharacterMesh0"), ""),
    "exploration_dependencies": len(report["exploration_animation_dependencies"]),
    "exploration_compatible": report["exploration"]["skeleton_compatible"],
    "battle_anim_class": next((r["anim_class"] for r in report["battle"]["skeletal_components"] if r["component"] == "CharacterMesh0"), ""),
    "battle_dependencies": len(report["battle_animation_dependencies"]),
    "battle_compatible": report["battle"]["skeleton_compatible"],
}))
