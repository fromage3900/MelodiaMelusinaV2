"""Stage Horizon Eater PCG in L_MelusinaMorning.

Spawns a PCGVolume actor with the HorizonEater_FilterFlow graph and places it
at the horizon distance for the teaser.

Run inside UE Editor via Monolith (editor_query:run_python):
  import stage_horizon_pcg
  import importlib
  importlib.reload(stage_horizon_pcg)
  stage_horizon_pcg.stage()
"""
from __future__ import annotations

import unreal

GRAPH_PATH = "/Game/EnvSandbox/PCG/Styles/SeaAbove/PCG_HorizonEater_FilterFlow"
ACTOR_LABEL = "BP_HorizonEater_PCG"


def _log(msg: str):
    unreal.log(f"[Horizon PCG] {msg}")


def stage() -> dict:
    """Stage the Horizon Eater PCG actor in the current level."""
    subsystem = unreal.get_editor_subsystem(unreal.UnrealEditorSubsystem)
    world = subsystem.get_editor_world()
    if world is None:
        raise RuntimeError("No editor world loaded")

    level_name = world.get_name()
    _log(f"Staging in level: {level_name}")

    # Check if actor already exists
    actors = unreal.GameplayStatics.get_all_actors_of_class(world, unreal.Actor)
    existing = [a for a in actors if ACTOR_LABEL in a.get_name()]
    if existing:
        _log(f"Actor already exists: {existing[0].get_name()}")
        return {"status": "exists", "actor": existing[0].get_name()}

    # Load the PCG graph
    graph = unreal.EditorAssetLibrary.load_asset(GRAPH_PATH)
    if graph is None:
        raise RuntimeError(f"Graph not found: {GRAPH_PATH}")

    _log(f"Loaded graph: {graph.get_name()}")

    # Spawn PCGVolume actor
    pcg_actor = unreal.EditorLevelLibrary.spawn_actor_from_class(unreal.PCGVolume, (0, 0, 0))
    if pcg_actor is None:
        raise RuntimeError("Failed to spawn PCGVolume actor")

    _log(f"Spawned actor: {pcg_actor.get_name()}")

    # Set the label
    pcg_actor.set_actor_label(ACTOR_LABEL)

    # Get the PCG component
    pcg_comp = pcg_actor.get_component_by_class(unreal.PCGComponent)
    if pcg_comp is None:
        _log("PCG component not found on PCGVolume")
    else:
        _log(f"Found PCG component: {pcg_comp.get_name()}")
        # Set the graph via set_graph method
        pcg_comp.set_graph(graph)
        _log(f"Set graph: {GRAPH_PATH}")

    # Place at horizon distance (2000m from center)
    pcg_actor.set_actor_location((200000, 0, 0), False, False)
    _log(f"Placed at horizon distance: (200000, 0, 0)")

    # Save
    unreal.EditorLevelLibrary.save_current_level()
    _log("Level saved")

    result = {
        "status": "staged",
        "actor": pcg_actor.get_name(),
        "label": ACTOR_LABEL,
        "graph": GRAPH_PATH,
        "location": (200000, 0, 0),
    }
    _log(f"Staging complete: {result}")
    return result


if __name__ == "__main__":
    stage()
