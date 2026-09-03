"""Audit the hard boundary between authored story travel and roguelike traversal."""

import json
from pathlib import Path

import unreal


PROJECT = Path(unreal.Paths.project_dir())
REPORT = Path(unreal.Paths.project_saved_dir()) / "Audit" / "melodia_transition_contract.json"
SOURCE_ROOT = PROJECT / "Plugins" / "MelodiaCore" / "Source" / "MelodiaCore"
ZEN_MAP = "/Game/ZenForestTest"
ACTIVE_ROOM_MAPS = (
    "/Game/Melodia/Roguelike/Rooms/L_MelodiaGrove",
    "/Game/Melodia/Roguelike/Rooms/L_MelodiaGrove_V2",
)


def read_source(name: str) -> str:
    return (SOURCE_ROOT / name).read_text(encoding="utf-8")


def source_contract() -> dict:
    portal = read_source("MelodiaOpeningPortal.cpp") + read_source("MelodiaOpeningPortal.h")
    room_exit = read_source("MelodiaRoomExit.cpp") + read_source("MelodiaRoomExit.h")
    coordinator = read_source("MelodiaDungeonRunCoordinator.cpp") + read_source("MelodiaDungeonRunCoordinator.h")
    return {
        "story_portal_calls_open_level": "OpenLevel" in portal,
        "story_portal_has_no_run_subsystem": (
            '#include "MelodiaRoguelikeRunSubsystem' not in portal and "RunSubsystem->" not in portal
        ),
        "story_portal_has_no_dungeon_generator": (
            '#include "DungeonGenerator' not in portal and "DungeonGenerator->" not in portal
        ),
        "room_exit_requests_next_stage": "RequestNextStage" in room_exit,
        "room_exit_never_calls_open_level": "OpenLevel" not in room_exit,
        "coordinator_never_calls_open_level": "OpenLevel" not in coordinator,
        "coordinator_uses_run_subsystem": "UMelodiaRoguelikeRunSubsystem" in coordinator,
        "coordinator_uses_dungeon_generator": "DungeonGenerator" in coordinator,
    }


def load_actors(path: str):
    levels = unreal.get_editor_subsystem(unreal.LevelEditorSubsystem)
    if not levels.load_level(path):
        raise RuntimeError(f"Could not load {path}")
    return unreal.get_editor_subsystem(unreal.EditorActorSubsystem).get_all_level_actors()


def zen_contract() -> dict:
    actors = load_actors(ZEN_MAP)
    portals = [a for a in actors if isinstance(a, unreal.MelodiaOpeningPortal)]
    exits = [a for a in actors if isinstance(a, unreal.MelodiaRoomExit)]
    coordinators = [a for a in actors if isinstance(a, unreal.MelodiaDungeonRunCoordinator)]
    legacy = [a for a in actors if "MelodiaTeleporterVolume" in a.get_class().get_name()]
    result = {
        "story_portal_count": len(portals),
        "room_exit_count": len(exits),
        "coordinator_count": len(coordinators),
        "legacy_teleporter_count": len(legacy),
        "story_portal_labels": [a.get_actor_label() for a in portals],
        "room_exit_labels": [a.get_actor_label() for a in exits],
        "room_exits_have_explicit_coordinator": all(
            a.get_editor_property("coordinator") is not None for a in exits
        ),
        "room_exits_disable_auto_resolve": all(
            not a.get_editor_property("allow_coordinator_auto_resolve") for a in exits
        ),
    }
    actors = portals = exits = coordinators = legacy = None
    unreal.SystemLibrary.collect_garbage()
    return result


def entrance_contract() -> list[dict]:
    rows = []
    for path in ACTIVE_ROOM_MAPS:
        actors = load_actors(path)
        entrances = [a for a in actors if isinstance(a, unreal.MelodiaRoomEntrance)]
        starts = [a for a in actors if isinstance(a, unreal.PlayerStart)]
        rows.append({
            "map": path,
            "entrance_count": len(entrances),
            "primary_count": sum(bool(a.get_editor_property("primary_run_entrance")) for a in entrances),
            "player_start_count": len(starts),
            "entrance_labels": [a.get_actor_label() for a in entrances],
        })
        actors = entrances = starts = None
        unreal.SystemLibrary.collect_garbage()
    return rows


def main() -> None:
    source = source_contract()
    zen = zen_contract()
    rooms = entrance_contract()
    checks = {
        **source,
        "zen_has_story_portal": zen["story_portal_count"] >= 1,
        "zen_has_one_explicit_room_exit": (
            zen["room_exit_count"] == 1
            and zen["room_exits_have_explicit_coordinator"]
            and zen["room_exits_disable_auto_resolve"]
        ),
        "zen_has_no_legacy_teleporter": zen["legacy_teleporter_count"] == 0,
        "active_rooms_have_one_entrance_each": all(row["entrance_count"] == 1 for row in rooms),
        "active_layout_has_one_primary_entrance": sum(row["primary_count"] for row in rooms) == 1,
    }
    report = {
        "passed": all(checks.values()),
        "checks": checks,
        "zen_forest": zen,
        "active_room_entrances": rooms,
    }
    REPORT.parent.mkdir(parents=True, exist_ok=True)
    REPORT.write_text(json.dumps(report, indent=2), encoding="utf-8")
    unreal.log(f"[MelodiaTransitionContractAudit] {REPORT} passed={report['passed']}")
    if not report["passed"]:
        failed = [name for name, value in checks.items() if not value]
        raise RuntimeError(f"Transition contract audit failed: {failed}")


if __name__ == "__main__":
    main()
