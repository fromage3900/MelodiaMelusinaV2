"""One-shot migration that separates authored story travel from roguelike traversal."""

import json
from pathlib import Path

import unreal


LEVEL_PATH = "/Game/ZenForestTest"
LEGACY_STORY_LABEL = "MelodiaTeleporter_ToDreamstate"
CANONICAL_STORY_LABEL = "StoryTravel_ToDreamstate"
DREAMSTATE_LEVEL = "/Game/Melodia/Levels/Opening/L_Melodia_Dreamstate"
REPORT_PATH = Path(unreal.Paths.project_saved_dir()) / "Audit" / "melodia_transition_domain_migration.json"


def main() -> None:
    level_subsystem = unreal.get_editor_subsystem(unreal.LevelEditorSubsystem)
    actor_subsystem = unreal.get_editor_subsystem(unreal.EditorActorSubsystem)
    if not level_subsystem.load_level(LEVEL_PATH):
        raise RuntimeError(f"Could not load {LEVEL_PATH}; ensure PIE is stopped")

    actors = list(actor_subsystem.get_all_level_actors())
    legacy = next((actor for actor in actors if actor.get_actor_label() == LEGACY_STORY_LABEL), None)
    canonical = next((actor for actor in actors if actor.get_actor_label() == CANONICAL_STORY_LABEL), None)

    legacy_replaced = False
    if canonical is None:
        location = legacy.get_actor_location() if legacy else unreal.Vector()
        rotation = legacy.get_actor_rotation() if legacy else unreal.Rotator()
        scale = legacy.get_actor_scale3d() if legacy else unreal.Vector(1.0, 1.0, 1.0)
        canonical = actor_subsystem.spawn_actor_from_class(
            unreal.MelodiaOpeningPortal,
            location,
            rotation,
        )
        if canonical is None:
            raise RuntimeError("Failed to spawn canonical Melodia story-travel portal")
        canonical.set_actor_scale3d(scale)
        canonical.set_actor_label(CANONICAL_STORY_LABEL)

    canonical.set_editor_property("destination_level_name", DREAMSTATE_LEVEL)
    canonical.set_editor_property("one_shot", True)

    if legacy and legacy != canonical:
        actor_subsystem.destroy_actor(legacy)
        legacy_replaced = True

    actors = list(actor_subsystem.get_all_level_actors())
    coordinators = [actor for actor in actors if isinstance(actor, unreal.MelodiaDungeonRunCoordinator)]
    exits = [actor for actor in actors if isinstance(actor, unreal.MelodiaRoomExit)]
    if len(coordinators) != 1:
        raise RuntimeError(f"Expected exactly one roguelike coordinator; found {len(coordinators)}")
    if not exits:
        raise RuntimeError("No Melodia roguelike room exit exists in ZenForestTest")

    for room_exit in exits:
        room_exit.set_editor_property("coordinator", coordinators[0])
        room_exit.set_editor_property("allow_coordinator_auto_resolve", False)
    if len(exits) == 1:
        coordinators[0].set_editor_property("active_room_exit", exits[0])
    else:
        raise RuntimeError(f"Expected exactly one authored active room exit; found {len(exits)}")

    if not level_subsystem.save_current_level():
        raise RuntimeError(f"Failed to save {LEVEL_PATH}")

    report = {
        "level": LEVEL_PATH,
        "story_travel": {
            "actor": canonical.get_actor_label(),
            "class": canonical.get_class().get_path_name(),
            "destination": DREAMSTATE_LEVEL,
            "legacy_replaced": legacy_replaced,
        },
        "roguelike_traversal": {
            "coordinator": coordinators[0].get_actor_label(),
            "explicitly_bound_exit_count": len(exits),
            "coordinator_auto_resolve": False,
        },
    }
    REPORT_PATH.parent.mkdir(parents=True, exist_ok=True)
    REPORT_PATH.write_text(json.dumps(report, indent=2), encoding="utf-8")
    unreal.log(f"[MelodiaTransitionMigration] {REPORT_PATH}")


if __name__ == "__main__":
    main()
