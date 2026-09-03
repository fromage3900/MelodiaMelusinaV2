"""Restore the canonical ZenForest story/dungeon gameplay contract idempotently."""

from pathlib import Path
import json
import unreal

LEVEL = "/Game/ZenForestTest"
GENERATOR_BP = "/Game/Melodia/Roguelike/Blueprints/BP_RoguelikeDungeonGenerator"
DREAMSTATE = "/Game/Melodia/Levels/Opening/L_Melodia_Dreamstate"
REPORT = Path(unreal.Paths.project_saved_dir()) / "Audit" / "zenforest_roguelike_contract_repair.json"


def find_by_label(actors, label):
    return next((actor for actor in actors.get_all_level_actors() if actor.get_actor_label() == label), None)


def ensure_actor(actors, cls, label, location):
    actor = find_by_label(actors, label)
    if actor:
        return actor
    actor = actors.spawn_actor_from_class(cls, unreal.Vector(*location), unreal.Rotator())
    if not actor:
        raise RuntimeError(f"Could not spawn {label}")
    actor.set_actor_label(label)
    return actor


def main():
    levels = unreal.get_editor_subsystem(unreal.LevelEditorSubsystem)
    actors = unreal.get_editor_subsystem(unreal.EditorActorSubsystem)
    if not levels.load_level(LEVEL):
        raise RuntimeError(f"Could not load {LEVEL}")

    generator_asset = unreal.EditorAssetLibrary.load_asset(GENERATOR_BP)
    if not generator_asset:
        raise RuntimeError(f"Missing {GENERATOR_BP}")

    generator = ensure_actor(
        actors, generator_asset.generated_class(), "RoguelikeDungeonGenerator_Melodia", (1400.0, 0.0, -40.0)
    )
    coordinator = ensure_actor(
        actors, unreal.MelodiaDungeonRunCoordinator, "Melodia_FirstDungeonCoordinator", (1400.0, 0.0, -40.0)
    )
    room_exit = ensure_actor(
        actors, unreal.MelodiaRoomExit, "BP_MelodiaRoomExit", (1800.0, 0.0, 100.0)
    )
    gate = ensure_actor(
        actors, unreal.MelodiaFirstDungeonGate, "Melodia_FirstDungeonGate", (1050.0, 0.0, -40.0)
    )
    encounter = ensure_actor(
        actors, unreal.MelodiaEncounterTrigger, "MelodiaSmoke_Encounter_01", (500.0, 0.0, 100.0)
    )
    portal = ensure_actor(
        actors, unreal.MelodiaOpeningPortal, "StoryTravel_ToDreamstate", (-800.0, 0.0, 100.0)
    )

    encounter.set_editor_property("enemy_id", "SakuraPhantom")
    encounter.set_editor_property("encounter_display_name", unreal.Text("Sakura Phantom"))
    encounter.set_editor_property("one_shot", True)

    coordinator.set_editor_property("dungeon_generator", generator)
    coordinator.set_editor_property("active_room_exit", room_exit)
    coordinator.set_editor_property("start_run_on_begin_play", False)
    coordinator.set_editor_property("initial_run_seed", 1337)

    room_exit.set_editor_property("coordinator", coordinator)
    room_exit.set_editor_property("allow_coordinator_auto_resolve", False)

    gate.set_editor_property("run_coordinator", coordinator)
    gate.set_editor_property("first_run_seed", 1337)

    portal.set_editor_property("destination_level_name", DREAMSTATE)
    portal.set_editor_property("one_shot", True)

    if not levels.save_current_level():
        raise RuntimeError(f"Could not save {LEVEL}")

    result = {
        "level": LEVEL,
        "generator": generator.get_actor_label(),
        "coordinator": coordinator.get_actor_label(),
        "room_exit": room_exit.get_actor_label(),
        "gate": gate.get_actor_label(),
        "encounter": encounter.get_actor_label(),
        "story_portal": portal.get_actor_label(),
    }
    REPORT.parent.mkdir(parents=True, exist_ok=True)
    REPORT.write_text(json.dumps(result, indent=2), encoding="utf-8")
    unreal.log(f"[ZenForestRoguelikeRepair] {REPORT}")
    return result


if __name__ == "__main__":
    main()
