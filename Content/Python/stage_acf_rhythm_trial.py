"""Stage the existing ACF trial's missing evade grant after its tags are registered.

Editor-side, project-relative, and trial-only. No pawn, map, animation, config,
or production authority is changed. This is asset staging, not gameplay proof.
"""

import json
from pathlib import Path

import unreal


TRIAL_ROOT = "/Game/Melodia/CombatTrial/RhythmAction"
ROLL = "/Game/Melodia/Characters/Melusina/Animations/Montages/AM_Melusina_Roll"


def registered_tag(name):
    tag = unreal.GameplayTag()
    tag.import_text('(TagName="' + name + '")')
    if str(tag.get_editor_property("tag_name")) != name:
        raise RuntimeError("ACF tag is not registered: " + name)
    return tag


def create_asset(name, asset_class):
    path = TRIAL_ROOT + "/" + name
    if unreal.EditorAssetLibrary.does_asset_exist(path):
        raise RuntimeError("Preserve existing trial asset; refusing overwrite: " + path)
    factory = unreal.DataAssetFactory()
    factory.set_editor_property("data_asset_class", asset_class)
    asset = unreal.AssetToolsHelpers.get_asset_tools().create_asset(
        name, TRIAL_ROOT, asset_class, factory
    )
    if asset is None:
        raise RuntimeError("Asset creation failed: " + path)
    return asset


def stage():
    # Validate everything before creating the first package. Missing plugin tag
    # registration must never leave an apparently usable ability with an empty tag.
    dodge_tag = registered_tag("Actions.Dodge")
    hero_tag = registered_tag("Teams.Heroes")
    montage = unreal.load_asset(ROLL)
    if not isinstance(montage, unreal.AnimMontage):
        raise RuntimeError("Existing Melusina roll montage failed to load")
    for name in ("DA_MelusinaRhythmTrialAbilities", "DA_MelusinaRhythmTrialInit"):
        if unreal.EditorAssetLibrary.does_asset_exist(TRIAL_ROOT + "/" + name):
            raise RuntimeError("Trial assets already exist; inspect rather than overwrite")

    abilities = create_asset("DA_MelusinaRhythmTrialAbilities", unreal.ACFAbilitySet)
    dodge = unreal.new_object(
        unreal.ACFDirectionalDodgeAction, outer=abilities, name="MelusinaTrialEvade"
    )
    dodge.set_anim_montage(montage)
    # The current roll has one Default section. Do not point ACF at nonexistent
    # Front/Back/Left/Right sections or modify the owner's animation montage.
    directions = dodge.get_editor_property("dodge_direction_to_montage_section_map")
    dodge.set_editor_property(
        "dodge_direction_to_montage_section_map",
        {direction: unreal.Name("Default") for direction in directions},
    )
    entry = unreal.ActionAbilityConfig()
    entry.set_editor_property("triggering_tag", dodge_tag)
    entry.set_editor_property("action", dodge)
    entry.set_editor_property("ability_level", 1)
    abilities.set_editor_property("action_abilities", [entry])
    if not unreal.EditorAssetLibrary.save_loaded_asset(abilities, only_if_is_dirty=False):
        raise RuntimeError("Ability-set save failed; no pawn binding was made")

    definition = create_asset("DA_MelusinaRhythmTrialInit", unreal.ACFCharacterDataAsset)
    definition.set_editor_property("default_ability_set", abilities)
    definition.set_editor_property("team", hero_tag)
    # Trial initialization must not enter the plugin's independent save system.
    definition.set_editor_property("should_automatically_be_saved", False)
    if not unreal.EditorAssetLibrary.save_loaded_asset(definition, only_if_is_dirty=False):
        raise RuntimeError("Character-definition save failed; no pawn binding was made")

    saved = unreal.load_asset(abilities.get_path_name())
    entries = saved.get_editor_property("action_abilities")
    assert len(entries) == 1
    assert entries[0].triggering_tag.get_editor_property("tag_name") == unreal.Name("Actions.Dodge")
    assert entries[0].action.get_anim_montage() == montage
    assert all(str(section) == "Default" for section in
               entries[0].action.get_editor_property("dodge_direction_to_montage_section_map").values())
    report = {
        "scope": "saved trial data only; not bound to a pawn",
        "abilities": abilities.get_path_name(),
        "definition": definition.get_path_name(),
        "evade_class": dodge.get_class().get_path_name(),
        "montage": montage.get_path_name(),
        "action_count": len(entries),
        "runtime_proven": False,
        "remaining": ["possession and action input", "directional displacement",
                      "invulnerability window", "musical timing and counter",
                      "ACF hit, health and death", "ECHO/FLOW ACF damage connection"],
    }
    out = Path(unreal.Paths.project_saved_dir()) / "Audit/acf_trial/20261011/staged_evade.json"
    out.parent.mkdir(parents=True, exist_ok=True)
    out.write_text(json.dumps(report, indent=2), encoding="utf-8")
    print(json.dumps(report))


if __name__ == "__main__":
    stage()
