"""Give the second Fiblat cell an honest graph-owned 60 m footprint.

PCG's CreatePointsGrid is authored in local-component space here, so changing
the volume actor scale alone does not enlarge the generated point set.  This
duplicates the proven graph and changes only its explicit grid extents; the
golden-ratio Fiblat settings, landscape raycast, mesh palette, and seed remain
unchanged.
"""

import unreal


SOURCE_PATH = "/Game/EnvSandbox/PCG/Styles/SeaAbove/PCG_SeaAbove_East_PhyllotaxisBiome"
DEST_PATH = "/Game/EnvSandbox/PCG/Styles/SeaAbove/PCG_SeaAbove_East_PhyllotaxisCourtyard"
LEVEL_PATH = "/Game/EnvSandbox/Monoliths/SeaAbove/Prototype/LV_SeaAbove_Prototype"
LABEL = "PCG_East_PhyllotaxisCourtyard"


def _duplicate_or_load(source, destination):
    if unreal.EditorAssetLibrary.does_asset_exist(destination):
        graph = unreal.EditorAssetLibrary.load_asset(destination)
        if graph is None:
            raise RuntimeError("Could not load existing graph: %s" % destination)
        return graph, False
    folder, name = destination.rsplit("/", 1)
    graph = unreal.AssetToolsHelpers.get_asset_tools().duplicate_asset(name, folder, source)
    if graph is None:
        raise RuntimeError("Could not duplicate graph: %s -> %s" % (SOURCE_PATH, destination))
    return graph, True


def run():
    if not unreal.EditorLevelLibrary.get_editor_world().get_path_name().startswith(LEVEL_PATH):
        unreal.EditorLevelLibrary.load_level(LEVEL_PATH)
    source = unreal.EditorAssetLibrary.load_asset(SOURCE_PATH)
    if source is None:
        raise RuntimeError("Missing source graph: %s" % SOURCE_PATH)
    graph, created = _duplicate_or_load(source, DEST_PATH)
    grid_node = next((node for node in graph.nodes if node.get_name() == "CreatePointsGrid_0"), None)
    if grid_node is None:
        raise RuntimeError("Missing CreatePointsGrid_0 in courtyard graph")
    settings = grid_node.get_settings()
    settings.set_editor_property("grid_extents", unreal.Vector(3000.0, 3000.0, 0.0))
    settings.set_editor_property("cell_size", unreal.Vector(6000.0, 6000.0, 20.0))
    fiblat_node = next((node for node in graph.nodes if node.get_name() == "ShapeBuilderFiblat_0"), None)
    if fiblat_node is None:
        raise RuntimeError("Missing ShapeBuilderFiblat_0 in courtyard graph")
    fiblat_settings = fiblat_node.get_settings()
    fiblat_config = fiblat_settings.get_editor_property("config")
    # Fiblat's Fit bounds, rather than the seed grid, own the final radial
    # footprint.  Expand the disc from the proven 18 m to a 27 m radius band
    # while keeping resolution 140 and phi=GoldenRatio unchanged.
    fiblat_config.default_extents = unreal.Vector(2700.0, 2700.0, 4.0)
    fiblat_settings.set_editor_property("config", fiblat_config)
    unreal.EditorAssetLibrary.save_loaded_asset(graph, False)

    actor = next((a for a in unreal.EditorLevelLibrary.get_all_level_actors() if a.get_actor_label() == LABEL), None)
    if actor is None:
        raise RuntimeError("Missing actor: %s" % LABEL)
    actor.set_actor_scale3d(unreal.Vector(1.0, 1.0, 1.0))
    component = actor.get_component_by_class(unreal.PCGComponent)
    if component is None:
        raise RuntimeError("Missing PCGComponent on %s" % LABEL)
    result = component.set_graph(graph)
    if result is False:
        raise RuntimeError("Could not assign courtyard graph")
    component.generate(True)
    unreal.EditorLevelLibrary.save_current_level()
    return {
        "status": "created" if created else "updated",
        "graph": DEST_PATH,
        "grid_extents_cm": [3000.0, 3000.0, 0.0],
        "cell_size_cm": [6000.0, 6000.0, 20.0],
        "fiblat_default_extents_cm": [2700.0, 2700.0, 4.0],
        "actor": LABEL,
        "actor_scale": [1.0, 1.0, 1.0],
        "generation": "async_started",
    }


if __name__ == "__main__":
    print(run())
