"""Build the first authored Melodia opening maps.

Run from a released Unreal Editor session or with UnrealEditor-Cmd:
    py Content/Python/setup_melodia_opening_levels.py

The script is idempotent by actor label and only owns L_Melodia_Dreamstate and
L_MelusinaMorning. It does not edit BP_Melusina, its AnimBP, or ZenForestTest.
"""
from __future__ import annotations

import json
from datetime import datetime, timezone
from pathlib import Path

import unreal


LEVEL_DIR = "/Game/Melodia/Levels/Opening"
DREAMSTATE = f"{LEVEL_DIR}/L_Melodia_Dreamstate"
MORNING = f"{LEVEL_DIR}/L_MelusinaMorning"
REPORT = Path(unreal.Paths.project_dir()) / "Saved" / "Melodia" / "opening_level_setup.json"

GAME_MODE = "/Game/Melodia/_PROJECT/BP_MelodiaGameMode.BP_MelodiaGameMode_C"
BRIDGE = "/Game/Melodia/_PROJECT/MelusinasHouse/SM_venetianbridge"
ROOM = "/Game/Melodia/_PROJECT/MelusinasHouse/SM_room1"
ROOM_DETAIL = "/Game/Melodia/_PROJECT/MelusinasHouse/SM_room2"
BED_PROXY = "/Game/Melodia/_PROJECT/MelusinasHouse/SM_Cube_001"
PERCH_PROXY = "/Game/Melodia/_PROJECT/MelusinasHouse/SM_Cube_002"


def _asset_exists(path: str) -> bool:
    return unreal.EditorAssetLibrary.does_asset_exist(f"{path}.{path.rsplit('/', 1)[-1]}")


def _load_asset(path: str):
    if not _asset_exists(path):
        raise RuntimeError(f"Required opening asset missing: {path}")
    return unreal.load_asset(path)


def _ensure_level(level_path: str):
    les = unreal.get_editor_subsystem(unreal.LevelEditorSubsystem)
    if not _asset_exists(level_path):
        if not unreal.EditorAssetLibrary.does_directory_exist(LEVEL_DIR):
            unreal.EditorAssetLibrary.make_directory(LEVEL_DIR)
        if not les.new_level(level_path, is_partitioned_world=False):
            raise RuntimeError(f"Could not create level: {level_path}")
    elif not les.load_level(level_path):
        raise RuntimeError(f"Could not load level: {level_path}")
    return les, unreal.get_editor_subsystem(unreal.EditorActorSubsystem)


def _actors_by_label(eas):
    return {actor.get_actor_label(): actor for actor in eas.get_all_level_actors()}


def _spawn(eas, existing, cls, label: str, location, rotation=(0.0, 0.0, 0.0)):
    actor = existing.get(label)
    if actor:
        actor.set_actor_location(unreal.Vector(*location), False, False)
        actor.set_actor_rotation(unreal.Rotator(*rotation), False)
        return actor
    actor = eas.spawn_actor_from_class(cls, unreal.Vector(*location), unreal.Rotator(*rotation))
    if not actor:
        raise RuntimeError(f"Could not spawn {label}")
    actor.set_actor_label(label)
    existing[label] = actor
    return actor


def _mesh(eas, existing, label: str, asset_path: str, location, scale=(1.0, 1.0, 1.0), rotation=(0.0, 0.0, 0.0)):
    actor = _spawn(eas, existing, unreal.StaticMeshActor, label, location, rotation)
    component = actor.get_component_by_class(unreal.StaticMeshComponent)
    component.set_static_mesh(_load_asset(asset_path))
    actor.set_actor_scale3d(unreal.Vector(*scale))
    return actor


def _set_game_mode():
    world = unreal.EditorLevelLibrary.get_editor_world()
    game_mode_class = unreal.load_class(None, GAME_MODE)
    if not world or not game_mode_class:
        raise RuntimeError("Melodia game mode could not be resolved")
    world.get_world_settings().set_editor_property("default_game_mode", game_mode_class)


def _set_anchor(anchor, scalar: float):
    """Set the editor-safe portion of opening state.

    The C++ state components deliberately default to Absent/Clear.  UE 5.8 does
    not currently generate Python enum wrappers for these plugin-local enums,
    so the authored tier transition remains a Blueprint integration task.  The
    scalar is exposed and gives the opening an immediately inspectable gameplay
    consequence without relying on an unavailable Python wrapper.
    """
    dissonance = anchor.get_editor_property("dissonance")
    dissonance.set_editor_property("songcraft_scalar", scalar)


def build_dreamstate() -> dict:
    les, eas = _ensure_level(DREAMSTATE)
    existing = _actors_by_label(eas)
    _set_game_mode()
    _spawn(eas, existing, unreal.PlayerStart, "Dreamstate_PlayerStart", (-900.0, 0.0, 150.0))
    _mesh(eas, existing, "Dreamstate_BifrostBridge", BRIDGE, (0.0, 0.0, 0.0), (1.25, 1.25, 1.0))
    _spawn(eas, existing, unreal.DirectionalLight, "Dreamstate_MoonKey", (0.0, 0.0, 3000.0), (-30.0, 215.0, 0.0))
    _spawn(eas, existing, unreal.SkyLight, "Dreamstate_Sky", (0.0, 0.0, 2500.0))
    _spawn(eas, existing, unreal.SkyAtmosphere, "Dreamstate_Atmosphere", (0.0, 0.0, 0.0))
    _spawn(eas, existing, unreal.ExponentialHeightFog, "Dreamstate_Mist", (0.0, 0.0, 0.0))
    anchor_cls = unreal.load_class(None, "/Script/MelodiaCore.MelodiaOpeningStateAnchor")
    portal_cls = unreal.load_class(None, "/Script/MelodiaCore.MelodiaOpeningPortal")
    dissonance_beat_cls = unreal.load_class(None, "/Script/MelodiaCore.MelodiaDissonanceBeat")
    if not anchor_cls or not portal_cls or not dissonance_beat_cls:
        raise RuntimeError("Melodia opening runtime classes are unavailable; rebuild MelodiaCore")
    anchor = _spawn(eas, existing, anchor_cls, "Dreamstate_OpeningState", (0.0, 0.0, 100.0))
    _set_anchor(anchor, 0.75)
    _spawn(eas, existing, dissonance_beat_cls, "Dreamstate_FirstDissonanceBeat", (0.0, 0.0, 160.0))
    portal = _spawn(eas, existing, portal_cls, "Dreamstate_WakePortal", (900.0, 0.0, 120.0))
    portal.set_editor_property("destination_level_name", "/Game/ZenForestTest")
    # Unreal exposes C++ bools prefixed with b as their display/property name
    # without that prefix in Python.
    portal.set_editor_property("one_shot", True)
    les.save_current_level()
    return {"level": DREAMSTATE, "actors": sorted(_actors_by_label(eas)), "saved": True}


def build_morning() -> dict:
    les, eas = _ensure_level(MORNING)
    existing = _actors_by_label(eas)
    _set_game_mode()
    _spawn(eas, existing, unreal.PlayerStart, "Morning_PlayerStart", (-300.0, 0.0, 110.0), (0.0, 0.0, 0.0))
    _mesh(eas, existing, "Morning_RoomShell", ROOM, (0.0, 0.0, 0.0))
    _mesh(eas, existing, "Morning_RoomDetail", ROOM_DETAIL, (0.0, 0.0, 0.0))
    _mesh(eas, existing, "Morning_Bed_PROXY_REPLACE", BED_PROXY, (-150.0, -120.0, 40.0), (2.4, 1.25, 0.45))
    perch_location = (160.0, 130.0, 120.0)
    intro_cls = unreal.load_class(None, "/Script/MelodiaCore.MelodiaSirMelodiousIntroActor")
    if intro_cls:
        # The canonical armature-bearing Sir Melodious mesh is resolved by the
        # actor class. Keep this authored intro in place until the dedicated
        # companion-control Blueprint adds player switching and flight.
        proxy = existing.pop("Morning_SirMelodiousPerch_PROXY_REPLACE", None)
        if proxy:
            eas.destroy_actor(proxy)
        # This actor is script-owned. Recreate it so constructor changes (such
        # as the newly delivered rigged mesh) replace stale serialized fallback
        # component arrays from a previous map build.
        prior_sir = existing.pop("Morning_SirMelodious_STATIC_INTRO", None)
        if prior_sir:
            eas.destroy_actor(prior_sir)
        sir = _spawn(eas, existing, intro_cls, "Morning_SirMelodious_STATIC_INTRO", perch_location)
        # The canonical armature-bearing delivery is authored at cockatoo scale.
        sir.set_actor_scale3d(unreal.Vector(1.0, 1.0, 1.0))
        sir.set_editor_property("depart_after_reunion", True)
        sir.set_editor_property("departure_delay_seconds", 1.25)
        sir.set_editor_property("departure_duration_seconds", 1.8)
        sir.set_editor_property("departure_offset", unreal.Vector(650.0, 0.0, 260.0))
        sir.set_editor_property("departure_destination_level", "/Game/Melodia/Levels/Opening/L_Melodia_Dreamstate")
    else:
        _mesh(eas, existing, "Morning_SirMelodiousPerch_PROXY_REPLACE", PERCH_PROXY, perch_location, (0.35, 0.35, 1.4))
    _spawn(eas, existing, unreal.DirectionalLight, "Morning_WindowKey", (0.0, 0.0, 1800.0), (-35.0, 135.0, 0.0))
    _spawn(eas, existing, unreal.SkyLight, "Morning_Sky", (0.0, 0.0, 1800.0))
    anchor_cls = unreal.load_class(None, "/Script/MelodiaCore.MelodiaOpeningStateAnchor")
    if not anchor_cls:
        raise RuntimeError("Melodia opening state anchor is unavailable; rebuild MelodiaCore")
    anchor = _spawn(eas, existing, anchor_cls, "Morning_OpeningState", (0.0, 0.0, 100.0))
    _set_anchor(anchor, 1.0)
    les.save_current_level()
    return {"level": MORNING, "actors": sorted(_actors_by_label(eas)), "saved": True}


def main():
    result = {
        "generated_at": datetime.now(timezone.utc).isoformat(),
        "dreamstate": build_dreamstate(),
        "morning": build_morning(),
    }
    REPORT.parent.mkdir(parents=True, exist_ok=True)
    REPORT.write_text(json.dumps(result, indent=2), encoding="utf-8")
    unreal.log(f"[MelodiaOpening] Built opening maps -> {REPORT}")
    return result


if __name__ == "__main__":
    main()
