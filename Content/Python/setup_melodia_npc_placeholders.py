"""Place a small, deterministic NPC placeholder cast in ZenForestTest.

ZenForestTest is the authority exploration map, and the coordinates below were
authored against its geometry -- they are correct as written.

These actors are explicitly temporary silhouettes for dialogue, direction, and
composition testing until release-cleared VRM assets are imported. Rerunning
the script updates existing labelled actors instead of creating duplicates.
"""
from __future__ import annotations

import json
import os
from pathlib import Path

import unreal


# ZenForestTest is the AUTHORITY EXPLORATION MAP (owner, 2026-08-14). Exploration
# NPCs belong here. Do not "correct" this to MelodiaIntegrationMap -- that is the
# integration proof map (save/load, Quill resume, idempotence), a different role.
# Override only for a deliberate test in another level.
MAP_PATH = os.environ.get("MELODIA_NPC_MAP", "/Game/ZenForestTest")
PLACEHOLDER_CLASS = "/Script/MelodiaCore.MelodiaNPCPlaceholder"
REPORT_PATH = Path(__file__).resolve().parents[2] / "Saved" / "Melodia" / "npc_placeholder_setup.json"

NPCS = (
    {
        "label": "MelodiaNPC_SD_02_PetalPriestess",
        "id": "SD_02_PetalPriestess",
        "name": "Petal Priestess",
        "archetype": "SakuraDreamer",
        "location": (120.0, -155.0, -40.0),
        "yaw": 35.0,
        "lines": ("The rhythm echo has awakened.", "Follow the lanterns and trust the beat."),
        "guidance": "The first encounter waits just ahead.",
    },
    {
        "label": "MelodiaNPC_CW_01_StarWeaver",
        "id": "CW_01_StarWeaver",
        "name": "Star Weaver",
        "archetype": "CosmicWeaver",
        "location": (890.0, 235.0, -40.0),
        "yaw": -135.0,
        "lines": ("Every constellation keeps a rhythm.",),
        "guidance": "Listen for a brighter cadence beyond the grove.",
    },
    {
        "label": "MelodiaNPC_MD_01_TwilightDancer",
        "id": "MD_01_TwilightDancer",
        "name": "Twilight Dancer",
        "archetype": "MirageDancer",
        "location": (1050.0, -255.0, -40.0),
        "yaw": 150.0,
        "lines": ("A clean step makes the whole world sing.",),
        "guidance": "Keep moving; the rhythm is kinder when you meet it halfway.",
    },
)


def _find_by_label(label: str):
    for actor in unreal.EditorLevelLibrary.get_all_level_actors():
        if actor.get_actor_label() == label:
            return actor
    return None


def _text(value: str):
    return unreal.Text(value)


def _configure(actor, definition: dict[str, object]) -> None:
    actor.set_actor_label(str(definition["label"]))
    actor.set_actor_location(unreal.Vector(*definition["location"]), False, False)
    actor.set_actor_rotation(unreal.Rotator(0.0, float(definition["yaw"]), 0.0), False)
    actor.set_editor_property("npc_id", definition["id"])
    actor.set_editor_property("display_name", _text(str(definition["name"])))
    actor.set_editor_property("archetype", definition["archetype"])
    actor.set_editor_property("battle_enemy_id", "")
    actor.tags = list(dict.fromkeys([*actor.tags, unreal.Name(str(definition["id"])), unreal.Name("MelodiaQuestNPC")]))
    interaction = actor.get_editor_property("interaction")
    interaction.set_editor_property("interaction_prompt", _text("Press E to talk"))
    interaction.set_editor_property("dialogue_lines", [_text(line) for line in definition["lines"]])
    interaction.set_editor_property("encounter_guidance", _text(str(definition["guidance"])))
    actor.apply_archetype_presentation()


def main() -> bool:
    unreal.EditorLoadingAndSavingUtils.load_map(MAP_PATH)
    actor_class = unreal.load_class(None, PLACEHOLDER_CLASS)
    if not actor_class:
        raise RuntimeError(f"Unable to load {PLACEHOLDER_CLASS}; rebuild MelodiaCore first.")

    created, updated = [], []
    for definition in NPCS:
        actor = _find_by_label(str(definition["label"]))
        if actor:
            updated.append(definition["id"])
        else:
            actor = unreal.EditorLevelLibrary.spawn_actor_from_class(
                actor_class,
                unreal.Vector(*definition["location"]),
                unreal.Rotator(0.0, float(definition["yaw"]), 0.0),
            )
            created.append(definition["id"])
        _configure(actor, definition)

    unreal.EditorLoadingAndSavingUtils.save_dirty_packages(True, True)
    report = {
        "ok": True,
        "map": MAP_PATH,
        "placeholder_class": PLACEHOLDER_CLASS,
        "created": created,
        "updated": updated,
        "count": len(NPCS),
    }
    REPORT_PATH.parent.mkdir(parents=True, exist_ok=True)
    REPORT_PATH.write_text(json.dumps(report, indent=2) + "\n", encoding="utf-8")
    unreal.log(f"[MelodiaNPCPlaceholder] Wrote {REPORT_PATH}")
    return True


if __name__ == "__main__":
    main()
