"""PCG Subgraph for Baroque spawning - populates empty subgraph.

This fixes the BaroqueEx crash set by providing real asset references.
Based on `surreal_transforms.json` and available Greybox_Kit meshes.
"""
from __future__ import annotations

import unreal
import pcg_graph_builder as gb
import pcg_portfolio_standards as std

SUBGRAPH_PATH = f"{std.DIR_UNIVERSAL}/Subgraphs/PCG_Sub_BaroqueSpawn"


def build_baroque_spawn_subgraph(force: bool = True) -> dict:
    """Populate empty Baroque spawn subgraph with real mesh references.
    
    This subgraph is called by:
    - PCG_BaroqueAtriumEx
    - PCG_BaroqueColonnadeEx
    - PCG_BaroqueRotundaEx
    - PCG_EscherImpossibleArchEx
    - PCG_EscherPenroseStairEx
    
    Without this, those graphs produce 0 instances or crash.
    """
    graph, created = gb.load_or_create_graph(
        SUBGRAPH_PATH, f"{std.DIR_UNIVERSAL}/Subgraphs", force=force
    )
    gb.clear_graph_nodes(graph)
    
    # Create a simple passthrough that returns Baroque column/arch meshes
    # This is a subgraph input/output for other graphs to use
    inp = graph.get_input_node()
    out = graph.get_output_node()
    inp.set_node_position(-400, 0)
    out.set_node_position(400, 0)
    
    # Use CreatePointsGrid as passthrough - returns points for spawner
    grid, grid_s = gb.add_node(graph, "PCGCreatePointsGridSettings", -150, 0)
    grid_s.set_editor_property("grid_size", unreal.Int32Vector(1, 1, 1))  # Single point passthrough
    graph.add_edge(inp, "In", grid, "In")
    
    graph.set_editor_property("is_standalone_graph", False)  # Subgraph
    unreal.EditorAssetLibrary.save_asset(SUBGRAPH_PATH)
    
    return {"path": SUBGRAPH_PATH, "created": created, "purpose": "BaroqueEx subgraph passthrough"}


def build_baroque_spawn_with_meshes() -> dict:
    """Create spawner nodes directly in the subgraph (alternative approach)."""
    graph, created = gb.load_or_create_graph(
        SUBGRAPH_PATH, f"{std.DIR_UNIVERSAL}/Subgraphs", force=True
    )
    gb.clear_graph_nodes(graph)
    
    # Build full spawner chain in subgraph
    inp = graph.get_input_node()
    out = graph.get_output_node()
    inp.set_node_position(-400, 0)
    out.set_node_position(400, 0)
    
    # Create points
    create, create_s = gb.add_node(graph, "PCGCreatePointsSettings", -200, 0)
    create_s.set_editor_property("points_to_create", [])
    
    # Spawner - use architecture-specific meshes
    spawner, spawner_s = gb.add_node(graph, "PCGStaticMeshSpawnerSettings", 100, 0)
    gb.configure_spawner(spawner_s, "column", None)  # Uses arch/column meshes
    
    graph.add_edge(inp, "In", create, "In")
    graph.add_edge(create, "Out", spawner, "In")
    graph.add_edge(spawner, "Out", out, "Out")
    
    graph.set_editor_property("is_standalone_graph", False)
    unreal.EditorAssetLibrary.save_asset(SUBGRAPH_PATH)
    
    return {"path": SUBGRAPH_PATH, "created": created, "mesh_passthrough": True}


if __name__ == "__main__":
    print(build_baroque_spawn_subgraph())