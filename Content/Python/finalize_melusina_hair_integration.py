"""Finalize JRPG Melusina hair presentation and Kawaii Physics configuration."""
from __future__ import annotations

import json
from pathlib import Path
import unreal

PROJECT = Path(unreal.Paths.project_dir())
REPORT = PROJECT / "Saved" / "Audit" / "melusina_hair_integration_fix.json"
JRPG_BP = "/Game/MelodiaIntegration/Blueprints/BP_MelusinaJRPGCharacter"
HAIR_ABP = "/Game/Melodia/Characters/Melusina/Hair/ABP_Melusina_WaterHair"


def prop(obj, name, default=None):
    try:
        return obj.get_editor_property(name)
    except Exception:
        return default


def main() -> dict:
    result = {"jrpg_blueprint": JRPG_BP, "hair_anim_blueprint": HAIR_ABP}
    bp = unreal.load_asset(JRPG_BP)
    if not bp:
        raise RuntimeError(f"Missing Blueprint: {JRPG_BP}")

    subsystem = unreal.get_engine_subsystem(unreal.SubobjectDataSubsystem)
    library = unreal.SubobjectDataBlueprintFunctionLibrary
    handles = list(subsystem.k2_gather_subobject_data_for_blueprint(bp))
    existing_hair = []
    root_handle = handles[0] if handles else None
    for handle in handles:
        data = library.get_data(handle)
        obj = library.get_object(data)
        if obj and isinstance(obj, unreal.MelodiaHairComponent):
            existing_hair.append(obj.get_name())

    if existing_hair:
        result["component_action"] = "already_present"
        result["components"] = existing_hair
    else:
        if root_handle is None:
            raise RuntimeError("Blueprint has no root subobject handle")
        params = unreal.AddNewSubobjectParams(
            parent_handle=root_handle,
            new_class=unreal.MelodiaHairComponent,
            blueprint_context=bp,
        )
        new_handle, failure = subsystem.add_new_subobject(params)
        if not failure.is_empty():
            raise RuntimeError(f"Could not add MelodiaHairComponent: {failure}")
        subsystem.rename_subobject(new_handle, unreal.Text("WaterHairMesh"))
        result["component_action"] = "added"
        result["components"] = ["WaterHairMesh"]

    unreal.BlueprintEditorLibrary.compile_blueprint(bp)
    if not unreal.EditorAssetLibrary.save_loaded_asset(bp, only_if_is_dirty=False):
        raise RuntimeError(f"Could not save Blueprint: {JRPG_BP}")

    abp = unreal.load_asset(HAIR_ABP)
    if not abp:
        raise RuntimeError(f"Missing AnimBlueprint: {HAIR_ABP}")
    kawaii_class = getattr(unreal, "AnimGraphNode_KawaiiPhysics", None)
    if not kawaii_class:
        raise RuntimeError("AnimGraphNode_KawaiiPhysics is not exposed to Python")
    kawaii_nodes = list(abp.get_nodes_of_class(kawaii_class))
    if len(kawaii_nodes) != 1:
        raise RuntimeError(f"Expected exactly one Kawaii Physics node, found {len(kawaii_nodes)}")
    node = kawaii_nodes[0]
    runtime = prop(node, "node")
    root = prop(runtime, "root_bone")
    root.set_editor_property("bone_name", unreal.Name("hair_root"))
    runtime.set_editor_property("root_bone", root)
    node.set_editor_property("node", runtime)
    unreal.BlueprintEditorLibrary.compile_blueprint(abp)
    if not unreal.EditorAssetLibrary.save_loaded_asset(abp, only_if_is_dirty=False):
        raise RuntimeError(f"Could not save AnimBlueprint: {HAIR_ABP}")

    result["kawaii_nodes"] = len(kawaii_nodes)
    result["kawaii_root_bone"] = str(prop(prop(prop(node, "node"), "root_bone"), "bone_name"))
    result["ok"] = result["kawaii_root_bone"] == "hair_root"
    REPORT.parent.mkdir(parents=True, exist_ok=True)
    REPORT.write_text(json.dumps(result, indent=2), encoding="utf-8")
    unreal.log("MELUSINA_HAIR_INTEGRATION_FIXED: " + json.dumps(result, sort_keys=True))
    if not result["ok"]:
        raise RuntimeError(f"Kawaii root did not persist: {result['kawaii_root_bone']}")
    return result


main()
