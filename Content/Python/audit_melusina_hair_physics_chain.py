"""Read-only audit of Melusina hair attachment, copy-pose, and Kawaii Physics."""
import json
from pathlib import Path
import unreal

OUT = Path(unreal.Paths.project_dir()) / "Saved" / "Audit" / "melusina_hair_physics_chain.json"
CHARACTERS = {
    "production": "/Game/Melodia/Characters/Melusina/BP_Melusina",
    "jrpg_exploration": "/Game/MelodiaIntegration/Blueprints/BP_MelusinaJRPGCharacter",
    "jrpg_battle": "/Game/Experiments/MelodiaJRPG/BP_MelusinaSwordsman_Presentation",
}
HAIR_MESH = "/Game/Melodia/Characters/Melusina/Hair/SK_MelusinaHair"
HAIR_ABP = "/Game/Melodia/Characters/Melusina/Hair/ABP_Melusina_WaterHair"


def prop(obj, name, default=None):
    try:
        return obj.get_editor_property(name)
    except Exception:
        return default


def path(obj):
    return obj.get_path_name().split(".")[0] if obj else ""


def character_contract(asset_path):
    bp = unreal.load_asset(asset_path)
    if not bp:
        return {"loads": False}
    unreal.BlueprintEditorLibrary.compile_blueprint(bp)
    generated = bp.generated_class()
    cdo = unreal.get_default_object(generated) if generated else None
    rows = []
    components = list(cdo.get_components_by_class(unreal.SkeletalMeshComponent)) if cdo else []
    # Native component templates added to a Blueprint SCS are not consistently
    # returned by GetComponentsByClass on the generated CDO in commandlets.
    # Gather those templates through SubobjectDataSubsystem as well.
    try:
        subsystem = unreal.get_engine_subsystem(unreal.SubobjectDataSubsystem)
        library = unreal.SubobjectDataBlueprintFunctionLibrary
        for handle in subsystem.k2_gather_subobject_data_for_blueprint(bp):
            obj = library.get_object(library.get_data(handle))
            if obj and isinstance(obj, unreal.SkeletalMeshComponent) and obj not in components:
                components.append(obj)
    except Exception:
        pass
    for comp in components:
        mesh = prop(comp, "skeletal_mesh_asset") or prop(comp, "skeletal_mesh")
        anim_class = prop(comp, "anim_class")
        parent = comp.get_attach_parent()
        rows.append({
            "component": comp.get_name(),
            "class": comp.get_class().get_name(),
            "mesh": path(mesh),
            "anim_class": anim_class.get_path_name() if anim_class else "",
            "attach_parent": parent.get_name() if parent else "",
            "attach_socket": str(comp.get_attach_socket_name()),
            "relative_location": str(prop(comp, "relative_location")),
            "relative_rotation": str(prop(comp, "relative_rotation")),
            "relative_scale": str(prop(comp, "relative_scale3d")),
        })
    hair = next((row for row in rows if row["mesh"] == HAIR_MESH and row["anim_class"].startswith(HAIR_ABP)), None)
    # UMelodiaHairComponent performs the inherited CharacterMesh0 attachment in
    # BeginPlay, so its CDO may remain rooted in the Blueprint's SCS hierarchy.
    runtime_attached_component = bool(hair and hair["component"].startswith("WaterHairMesh"))
    statically_attached_component = bool(hair and hair["attach_parent"] == "CharacterMesh0")
    return {
        "loads": bool(cdo),
        "generated_class": generated.get_path_name() if generated else "",
        "components": rows,
        "hair_contract_ok": bool(hair and (runtime_attached_component or statically_attached_component)),
    }


abp = unreal.load_asset(HAIR_ABP)
copy_nodes = []
kawaii_nodes = []
if abp:
    try:
        for node in abp.get_nodes_of_class(unreal.AnimGraphNode_CopyPoseFromMesh):
            runtime = prop(node, "node")
            copy_nodes.append({
                "name": node.get_name(),
                "use_attached_parent": bool(prop(runtime, "use_attached_parent", False)),
                "copy_curves": bool(prop(runtime, "copy_curves", False)),
                "source_mesh_component_pin": any(str(pin.pin_name) == "SourceMeshComponent" for pin in list(prop(node, "pins", []) or [])),
            })
    except Exception as exc:
        copy_nodes.append({"error": str(exc)})

    kawaii_class = getattr(unreal, "AnimGraphNode_KawaiiPhysics", None)
    if kawaii_class:
        try:
            for node in abp.get_nodes_of_class(kawaii_class):
                runtime = prop(node, "node")
                row = {"name": node.get_name()}
                root_bone = prop(runtime, "root_bone")
                row["root_bone"] = str(prop(root_bone, "bone_name", ""))
                for field in ("exclude_bones", "dummy_bone_length", "bone_forward_axis", "physics_settings", "limits_data_asset", "bone_constraints_data_asset"):
                    value = prop(runtime, field)
                    row[field] = path(value) if hasattr(value, "get_path_name") else str(value)
                kawaii_nodes.append(row)
        except Exception as exc:
            kawaii_nodes.append({"error": str(exc)})

report = {
    "characters": {name: character_contract(asset) for name, asset in CHARACTERS.items()},
    "hair_anim_blueprint": {
        "asset": HAIR_ABP,
        "loads": bool(abp),
        "copy_pose_nodes": copy_nodes,
        "kawaii_physics_class_exposed": bool(getattr(unreal, "AnimGraphNode_KawaiiPhysics", None)),
        "kawaii_physics_nodes": kawaii_nodes,
    },
}
report["ok"] = (
    report["characters"]["production"].get("hair_contract_ok", False)
    and report["characters"]["jrpg_exploration"].get("hair_contract_ok", False)
    and len(copy_nodes) == 1
    and len(kawaii_nodes) == 1
    and "hair_root" in kawaii_nodes[0].get("root_bone", "")
)
OUT.parent.mkdir(parents=True, exist_ok=True)
OUT.write_text(json.dumps(report, indent=2), encoding="utf-8")
unreal.log("MELUSINA_HAIR_PHYSICS_AUDIT: " + json.dumps({
    "ok": report["ok"],
    "production_hair": report["characters"]["production"].get("hair_contract_ok", False),
    "jrpg_hair": report["characters"]["jrpg_exploration"].get("hair_contract_ok", False),
    "copy_pose_nodes": len(copy_nodes),
    "kawaii_nodes": len(kawaii_nodes),
}))
