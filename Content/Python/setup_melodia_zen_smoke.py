"""Configure ZenForestTest as the Melodia native gameplay smoke-test map.

Run from UE:
    py Content/Python/setup_melodia_zen_smoke.py
"""
from __future__ import annotations

import unreal


MAP_PATH = "/Game/ZenForestTest"
PLAYER_START_LABEL = "MelodiaSmoke_PlayerStart"
ENCOUNTER_LABEL = "MelodiaSmoke_Encounter_01"
GAME_MODE_CLASS_PATH = "/Game/Melodia/_PROJECT/BP_MelodiaGameMode.BP_MelodiaGameMode_C"
MELUSINA_PAWN_CLASS_PATH = "/Game/Melodia/Characters/Melusina/BP_Melusina.BP_Melusina_C"


def _load_class(path: str):
    cls = unreal.load_class(None, path)
    if not cls:
        raise RuntimeError(f"Unable to load class: {path}")
    return cls


def _find_actor_by_label(label: str):
    for actor in unreal.EditorLevelLibrary.get_all_level_actors():
        if actor.get_actor_label() == label:
            return actor
    return None


def _ensure_player_start():
    actor = _find_actor_by_label(PLAYER_START_LABEL)
    if actor:
        return actor

    actor = unreal.EditorLevelLibrary.spawn_actor_from_class(
        unreal.PlayerStart,
        unreal.Vector(0.0, 0.0, 140.0),
        unreal.Rotator(0.0, 0.0, 0.0),
    )
    actor.set_actor_label(PLAYER_START_LABEL)
    unreal.log(f"[MelodiaSmoke] Created {PLAYER_START_LABEL}")
    return actor


def _ensure_encounter_trigger():
    actor = _find_actor_by_label(ENCOUNTER_LABEL)
    if not actor:
        trigger_class = _load_class("/Script/MelodiaCore.MelodiaEncounterTrigger")
        actor = unreal.EditorLevelLibrary.spawn_actor_from_class(
            trigger_class,
            unreal.Vector(550.0, 0.0, -40.0),
            unreal.Rotator(0.0, 0.0, 0.0),
        )
        actor.set_actor_label(ENCOUNTER_LABEL)
        unreal.log(f"[MelodiaSmoke] Created {ENCOUNTER_LABEL}")

    # Keep the smoke actor deterministic even when rerunning after code changes.
    actor.set_actor_location(unreal.Vector(550.0, 0.0, -40.0), False, False)
    actor.set_actor_rotation(unreal.Rotator(0.0, 0.0, 0.0), False)
    # Properties may be missing while the editor runs a DLL older than source
    # (live-coding pending); skip those instead of aborting the whole setup.
    for prop, value in (
        ("encounter_level", 1),
        ("enemy_id", "CrystalShard"),
        ("encounter_display_name", unreal.Text("Zen Forest Smoke Encounter")),
        ("cooldown_seconds", 1.0),
        ("one_shot", False),
    ):
        try:
            actor.set_editor_property(prop, value)
        except Exception as exc:
            unreal.log_warning(f"[MelodiaSmoke] Skipped {prop} (stale module?): {exc}")

    def _get_component(prop):
        try:
            return actor.get_editor_property(prop)
        except Exception as exc:
            unreal.log_warning(f"[MelodiaSmoke] Component {prop} unavailable (stale module?): {exc}")
            return None

    trigger_volume = _get_component("trigger_volume")
    if trigger_volume:
        trigger_volume.set_box_extent(unreal.Vector(260.0, 260.0, 180.0), True)

    encounter_label = _get_component("encounter_label")
    if encounter_label:
        encounter_label.set_editor_property("text", unreal.Text("Zen Forest Smoke Encounter"))
        encounter_label.set_editor_property("world_size", 34.0)

    encounter_light = _get_component("encounter_light")
    if encounter_light:
        encounter_light.set_editor_property("intensity", 900.0)
        encounter_light.set_editor_property("attenuation_radius", 420.0)

    return actor


def _set_world_game_mode():
    game_mode_class = _load_class(GAME_MODE_CLASS_PATH)
    melusina_class = _load_class(MELUSINA_PAWN_CLASS_PATH)
    world = unreal.EditorLevelLibrary.get_editor_world()
    if not world:
        raise RuntimeError("No editor world after loading ZenForestTest")

    game_mode_cdo = unreal.get_default_object(game_mode_class)
    if not game_mode_cdo:
        raise RuntimeError(f"Unable to access GameMode CDO: {GAME_MODE_CLASS_PATH}")

    game_mode_cdo.set_editor_property("default_pawn_class", melusina_class)
    unreal.EditorAssetLibrary.save_asset("/Game/Melodia/_PROJECT/BP_MelodiaGameMode", only_if_is_dirty=False)
    unreal.log("[MelodiaSmoke] BP_MelodiaGameMode default_pawn_class set to BP_Melusina")

    world_settings = world.get_world_settings()
    world_settings.set_editor_property("default_game_mode", game_mode_class)
    unreal.log("[MelodiaSmoke] WorldSettings default_game_mode set to MelodiaGameMode")


def setup():
    unreal.EditorLoadingAndSavingUtils.load_map(MAP_PATH)
    _set_world_game_mode()
    _ensure_player_start()
    _ensure_encounter_trigger()
    unreal.EditorLoadingAndSavingUtils.save_dirty_packages(True, True)
    unreal.log("[MelodiaSmoke] ZenForestTest smoke setup complete")


if __name__ == "__main__":
    setup()
