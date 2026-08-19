"""Read-only audit for the Melodia procedural dungeon generator Blueprint.

This is intentionally separate from the existing generation helpers.  It never
calls Generate/StartNewDungeon/CreateDungeon, never saves, and never loads PIE.
Use it only after the live editor/Monolith owner gate is clean.
"""

from __future__ import annotations

import json
import unreal


GENERATOR = "/Game/Melodia/Roguelike/Blueprints/BP_RoguelikeDungeonGenerator"
REQUIRED_INTERFACE = "MelodiaDungeonRecipeConsumer"


def prop(obj, name, default=None):
    try:
        return obj.get_editor_property(name)
    except Exception:
        return default


def path_name(obj):
    if obj is None:
        return None
    try:
        return str(obj.get_path_name())
    except Exception:
        return str(obj)


def interface_name(value):
    interface = prop(value, "interface")
    return path_name(interface or value)


def main():
    bp = unreal.load_object(None, GENERATOR)
    report = {
        "kind": "melodia_roguelike_generator_readonly_audit",
        "asset": GENERATOR,
        "mutation_issued": False,
        "save_issued": False,
        "pie_started": False,
        "generation_called": False,
        "asset_loaded": bp is not None,
        "parent_class": None,
        "implemented_interfaces": [],
        "function_graphs": [],
        "placed_actor_count": None,
        "placed_actor_labels": [],
        "required_interface": REQUIRED_INTERFACE,
        "inspection_boundary": [
            "No Generate/StartNewDungeon/CreateDungeon call",
            "No save or asset mutation",
            "No PIE or map load",
        ],
    }
    if bp is None:
        unreal.log("MELODIA_ROGUELIKE_GENERATOR_READONLY: " + json.dumps(report, sort_keys=True))
        print(json.dumps(report, sort_keys=True))
        return report

    parent = prop(bp, "parent_class")
    report["parent_class"] = path_name(parent)
    interfaces = prop(bp, "implemented_interfaces")
    if interfaces is not None:
        try:
            report["implemented_interfaces"] = [interface_name(item) for item in interfaces]
        except Exception as exc:
            report["implemented_interfaces"] = [f"inspection_error:{exc}"]

    try:
        report["function_graphs"] = [str(graph.get_name()) for graph in bp.get_function_graphs()]
    except Exception as exc:
        report["function_graphs"] = [f"inspection_error:{exc}"]

    try:
        generated_class = bp.generated_class()
        world = unreal.EditorLevelLibrary.get_editor_world()
        if world is None:
            world = unreal.EditorLevelLibrary.get_game_world()
        if world is not None and generated_class is not None:
            actors = unreal.GameplayStatics.get_all_actors_of_class(world, generated_class)
            report["placed_actor_count"] = len(actors)
            report["placed_actor_labels"] = [str(actor.get_actor_label()) for actor in actors]
    except Exception as exc:
        report["placed_actor_count"] = f"inspection_error:{exc}"

    text = json.dumps(report, sort_keys=True)
    unreal.log("MELODIA_ROGUELIKE_GENERATOR_READONLY: " + text)
    print(text)
    return report


main()
