"""Add one bounded Fibonacci-garden cell to the documented east district.

The cell deliberately reuses the proven Fiblat/GoldenRatio graph.  It is a
vista pocket on the empty eastern third, scaled to a 60 m class footprint and
kept on the same high ridge as the first cell.  The graph's landscape-only
raycast remains the authority for final point height.
"""

import unreal


LEVEL_PATH = "/Game/EnvSandbox/Monoliths/SeaAbove/Prototype/LV_SeaAbove_Prototype"
GRAPH_PATH = "/Game/EnvSandbox/PCG/Styles/SeaAbove/PCG_SeaAbove_East_PhyllotaxisBiome"
LABEL = "PCG_East_PhyllotaxisCourtyard"
LOCATION = unreal.Vector(220000.0, 130000.0, 67000.0)
SCALE = unreal.Vector(12.0, 12.0, 2.0)


def run():
    world = unreal.EditorLevelLibrary.get_editor_world()
    if world is None or not world.get_path_name().startswith(LEVEL_PATH):
        unreal.EditorLevelLibrary.load_level(LEVEL_PATH)
    actors = unreal.EditorLevelLibrary.get_all_level_actors()
    existing = next((a for a in actors if a.get_actor_label() == LABEL), None)
    if existing is not None:
        graph = unreal.EditorAssetLibrary.load_asset(GRAPH_PATH)
        component = existing.get_component_by_class(unreal.PCGComponent)
        if graph is None or component is None:
            raise RuntimeError("Existing courtyard is missing its graph/component")
        existing.set_actor_scale3d(SCALE)
        result = component.set_graph(graph)
        if result is False:
            raise RuntimeError("Could not assign graph to existing %s" % LABEL)
        component.generate(True)
        unreal.EditorLevelLibrary.save_current_level()
        return {"status": "repaired_existing", "label": LABEL, "location": str(existing.get_actor_location())}

    graph = unreal.EditorAssetLibrary.load_asset(GRAPH_PATH)
    if graph is None:
        raise RuntimeError("Missing graph: %s" % GRAPH_PATH)
    volume = unreal.EditorLevelLibrary.spawn_actor_from_class(
        unreal.PCGVolume, LOCATION, unreal.Rotator(0.0, 0.0, 0.0)
    )
    if volume is None:
        raise RuntimeError("Could not spawn PCGVolume")
    volume.set_actor_label(LABEL)
    volume.set_actor_scale3d(SCALE)
    try:
        volume.set_folder_path("SeaAbove/PCG/East")
    except Exception:
        pass
    try:
        volume.tags = [unreal.Name("AutoBlend_HasPrimitiveData")]
    except Exception:
        pass
    component = volume.get_component_by_class(unreal.PCGComponent)
    if component is None:
        raise RuntimeError("Could not assign graph to %s" % LABEL)
    result = component.set_graph(graph)
    if result is False:
        raise RuntimeError("Could not assign graph to %s" % LABEL)
    component.generate(True)
    unreal.EditorLevelLibrary.save_current_level()
    return {
        "status": "created",
        "label": LABEL,
        "graph": GRAPH_PATH,
        "location": [LOCATION.x, LOCATION.y, LOCATION.z],
        "scale": [SCALE.x, SCALE.y, SCALE.z],
        "distribution": "PCGEx_Fiblat_GoldenRatio",
        "generation": "async_started",
    }


if __name__ == "__main__":
    print(run())
