"""Wire the Zen tutorial victory to the first deterministic dungeon gate.

Run only with editor ownership after MelodiaCore has been rebuilt. The script
owns three labels in ZenForestTest and does not alter environment composition.
"""
from __future__ import annotations

import json
from pathlib import Path

import unreal
from gmm.game.rules_generated import RULES


LEVEL = "/Game/ZenForestTest"
ENCOUNTER_LABEL = "MelodiaSmoke_Encounter_01"
GENERATOR_LABEL = "RoguelikeDungeonGenerator_Melodia"
COORDINATOR_LABEL = "Melodia_FirstDungeonCoordinator"
GATE_LABEL = "Melodia_FirstDungeonGate"
GENERATOR_BP = "/Game/Melodia/Roguelike/Blueprints/BP_RoguelikeDungeonGenerator"
REPORT = Path(unreal.Paths.project_saved_dir()) / "Melodia" / "first_dungeon_unlock_setup.json"
OPENING = RULES["opening_flow"]


def _find(eas, label: str):
    return next((actor for actor in eas.get_all_level_actors() if actor.get_actor_label() == label), None)


def _spawn(eas, cls, label: str, location):
    actor = _find(eas, label)
    if actor:
        return actor
    actor = eas.spawn_actor_from_class(cls, unreal.Vector(*location), unreal.Rotator())
    if not actor:
        raise RuntimeError(f"Could not spawn {label}")
    actor.set_actor_label(label)
    return actor


def main():
    levels = unreal.get_editor_subsystem(unreal.LevelEditorSubsystem)
    actors = unreal.get_editor_subsystem(unreal.EditorActorSubsystem)
    if not levels.load_level(LEVEL):
        raise RuntimeError(f"Could not load {LEVEL}")

    encounter = _find(actors, ENCOUNTER_LABEL)
    if not encounter:
        raise RuntimeError(f"Missing required tutorial encounter: {ENCOUNTER_LABEL}")
    encounter.set_editor_property("enemy_id", OPENING["tutorial_enemy_id"])
    encounter.set_editor_property("encounter_display_name", unreal.Text("Sakura Phantom"))
    encounter.set_editor_property("one_shot", True)

    generator = _find(actors, GENERATOR_LABEL)
    if not generator:
        bp = unreal.EditorAssetLibrary.load_asset(GENERATOR_BP)
        if not bp:
            raise RuntimeError(f"Missing dungeon generator Blueprint: {GENERATOR_BP}")
        generator = _spawn(actors, bp.generated_class(), GENERATOR_LABEL, (1400.0, 0.0, -40.0))

    coordinator_cls = unreal.load_class(None, "/Script/MelodiaCore.MelodiaDungeonRunCoordinator")
    gate_cls = unreal.load_class(None, "/Script/MelodiaCore.MelodiaFirstDungeonGate")
    if not coordinator_cls or not gate_cls:
        raise RuntimeError("Rebuild MelodiaCore before placing the first dungeon gate")

    coordinator = _spawn(actors, coordinator_cls, COORDINATOR_LABEL, (1400.0, 0.0, -40.0))
    coordinator.set_editor_property("dungeon_generator", generator)
    coordinator.set_editor_property("start_run_on_begin_play", False)
    coordinator.set_editor_property("initial_run_seed", OPENING["first_dungeon_seed"])

    gate = _spawn(actors, gate_cls, GATE_LABEL, (1050.0, 0.0, -40.0))
    gate.set_editor_property("run_coordinator", coordinator)
    gate.set_editor_property("first_run_seed", OPENING["first_dungeon_seed"])

    levels.save_current_level()
    result = {
        "level": LEVEL,
        "encounter": ENCOUNTER_LABEL,
        "enemy_id": OPENING["tutorial_enemy_id"],
        "coordinator": COORDINATOR_LABEL,
        "gate": GATE_LABEL,
        "seed": OPENING["first_dungeon_seed"],
    }
    REPORT.parent.mkdir(parents=True, exist_ok=True)
    REPORT.write_text(json.dumps(result, indent=2), encoding="utf-8")
    unreal.log(f"[MelodiaOpening] First dungeon unlock wired -> {REPORT}")
    return result


if __name__ == "__main__":
    main()
