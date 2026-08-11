"""Repair the bounded Melusina JRPG presentation contract: hair plus one skill impact."""
from __future__ import annotations

import json
from pathlib import Path
import unreal

BATTLE_BP = "/Game/Experiments/MelodiaJRPG/BP_MelusinaSwordsman_Presentation"
ATTACK_MONTAGE = "/Game/Melodia/Characters/Melusina/Animations/AM_Mocap_BasicAttack"
USE_SKILL_NOTIFY = "/Game/TurnBasedJRPGTemplate/Blueprints/AnimNotifies/BP_UseSkillN"
REPORT = Path(unreal.Paths.project_dir()) / "Saved" / "Audit" / "melusina_battle_repair.json"


def load(path: str):
    asset = unreal.load_asset(path)
    if not asset:
        raise RuntimeError(f"Missing required asset: {path}")
    return asset


def notify_class_from_blueprint(path: str):
    blueprint = load(path)
    generated = blueprint.generated_class()
    if not generated:
        raise RuntimeError(f"Notify Blueprint has no generated class: {path}")
    return generated


def notify_rows(animation) -> list[dict]:
    rows = []
    for event in unreal.AnimationBlueprintLibrary.get_animation_notify_event_data(animation):
        notify = event.get_editor_property("notify")
        rows.append({
            "time": float(event.get_editor_property("trigger_time")),
            "class": notify.get_class().get_path_name() if notify else "",
        })
    return rows


def ensure_hair_component(bp) -> str:
    subsystem = unreal.get_engine_subsystem(unreal.SubobjectDataSubsystem)
    library = unreal.SubobjectDataBlueprintFunctionLibrary
    handles = list(subsystem.k2_gather_subobject_data_for_blueprint(bp))
    for handle in handles:
        obj = library.get_object(library.get_data(handle))
        if obj and isinstance(obj, unreal.MelodiaHairComponent):
            return "already_present"
    if not handles:
        raise RuntimeError("Battle Blueprint has no root subobject")
    params = unreal.AddNewSubobjectParams(
        parent_handle=handles[0],
        new_class=unreal.MelodiaHairComponent,
        blueprint_context=bp,
    )
    new_handle, failure = subsystem.add_new_subobject(params)
    if not failure.is_empty():
        raise RuntimeError(f"Could not add battle hair component: {failure}")
    subsystem.rename_subobject(new_handle, unreal.Text("WaterHairMesh"))
    return "added"


def ensure_single_skill_notify(montage, notify_class) -> tuple[str, float]:
    matching = [row for row in notify_rows(montage) if row["class"] == notify_class.get_path_name()]
    if len(matching) > 1:
        raise RuntimeError(f"Attack montage has {len(matching)} skill impact notifies; expected at most one")
    if matching:
        return "already_present", matching[0]["time"]

    # Existing trajectory audit identified the strongest forward extension near 4.0 s.
    impact_time = min(4.0, max(0.0, float(montage.get_editor_property("sequence_length")) - 0.05))
    created = unreal.AnimationBlueprintLibrary.add_animation_notify_event(montage, impact_time, notify_class)
    if not created:
        raise RuntimeError("Failed to add BP_UseSkillN to Melusina's attack montage")
    return "added", impact_time


def main() -> None:
    bp = load(BATTLE_BP)
    montage = load(ATTACK_MONTAGE)
    notify_class = notify_class_from_blueprint(USE_SKILL_NOTIFY)

    hair_action = ensure_hair_component(bp)
    notify_action, impact_time = ensure_single_skill_notify(montage, notify_class)

    unreal.BlueprintEditorLibrary.compile_blueprint(bp)
    if not unreal.EditorAssetLibrary.save_loaded_asset(bp, only_if_is_dirty=False):
        raise RuntimeError(f"Could not save {BATTLE_BP}")
    if not unreal.EditorAssetLibrary.save_loaded_asset(montage, only_if_is_dirty=False):
        raise RuntimeError(f"Could not save {ATTACK_MONTAGE}")

    cdo = unreal.get_default_object(bp.generated_class())
    hair_components = list(cdo.get_components_by_class(unreal.MelodiaHairComponent))
    matching_notifies = [row for row in notify_rows(montage) if row["class"] == notify_class.get_path_name()]
    report = {
        "battle_blueprint": BATTLE_BP,
        "hair_action": hair_action,
        "hair_component_count": len(hair_components),
        "attack_montage": ATTACK_MONTAGE,
        "notify_action": notify_action,
        "impact_time": impact_time,
        "skill_notify_count": len(matching_notifies),
        "skill_notifies": matching_notifies,
        "ok": len(hair_components) == 1 and len(matching_notifies) == 1,
    }
    REPORT.parent.mkdir(parents=True, exist_ok=True)
    REPORT.write_text(json.dumps(report, indent=2), encoding="utf-8")
    unreal.log("MELUSINA_BATTLE_REPAIR: " + json.dumps(report, sort_keys=True))
    if not report["ok"]:
        raise RuntimeError(f"Melusina battle repair did not satisfy its contract: {report}")


main()
