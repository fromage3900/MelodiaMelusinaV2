"""Read-only verification for the Zen first-dungeon unlock fixture."""
from __future__ import annotations

import json
from pathlib import Path

import unreal
from gmm.game.rules_generated import RULES


LEVEL = "/Game/ZenForestTest"
REPORT = Path(unreal.Paths.project_saved_dir()) / "Melodia" / "first_dungeon_unlock_verification.json"
OPENING = RULES["opening_flow"]


def main():
    levels = unreal.get_editor_subsystem(unreal.LevelEditorSubsystem)
    actors = unreal.get_editor_subsystem(unreal.EditorActorSubsystem)
    if not levels.load_level(LEVEL):
        raise RuntimeError(f"Could not load {LEVEL}")

    by_label = {actor.get_actor_label(): actor for actor in actors.get_all_level_actors()}
    required = {
        "MelodiaSmoke_Encounter_01",
        "RoguelikeDungeonGenerator_Melodia",
        "Melodia_FirstDungeonCoordinator",
        "Melodia_FirstDungeonGate",
    }
    missing = sorted(required - set(by_label))
    if missing:
        raise RuntimeError(f"Zen first-dungeon fixture is incomplete: {missing}")

    encounter = by_label["MelodiaSmoke_Encounter_01"]
    coordinator = by_label["Melodia_FirstDungeonCoordinator"]
    gate = by_label["Melodia_FirstDungeonGate"]
    enemy_id = str(encounter.get_editor_property("enemy_id"))
    seed = int(gate.get_editor_property("first_run_seed"))
    if enemy_id != OPENING["tutorial_enemy_id"]:
        raise RuntimeError(f"Tutorial enemy drift: {enemy_id}")
    if seed != OPENING["first_dungeon_seed"]:
        raise RuntimeError(f"First dungeon seed drift: {seed}")
    if coordinator.get_editor_property("start_run_on_begin_play"):
        raise RuntimeError("First dungeon must remain locked until the tutorial victory")
    if not gate.get_editor_property("run_coordinator"):
        raise RuntimeError("First dungeon gate has no run coordinator")

    result = {
        "ok": True,
        "level": LEVEL,
        "enemy_id": enemy_id,
        "seed": seed,
        "heart_tokens_on_unlock": OPENING["heart_tokens_on_unlock"],
        "required_labels": sorted(required),
    }
    REPORT.parent.mkdir(parents=True, exist_ok=True)
    REPORT.write_text(json.dumps(result, indent=2), encoding="utf-8")
    unreal.log(f"[MelodiaOpening] First dungeon unlock verified -> {REPORT}")
    return result


if __name__ == "__main__":
    main()
