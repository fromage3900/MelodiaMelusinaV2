"""Build the reusable human-scale corridor PCG graph.

The graph produces two procedural wall rails from one-metre grid points. The
wall centers are +/-165 cm apart; with 30 cm wall thickness this leaves a
300 cm clear lane. The point transform raises the wall centers to 120 cm,
giving a 240 cm clear height with the 1 m cube greybox mesh.
"""
from __future__ import annotations

import unreal
import pcg_graph_builder as gb
import pcg_portfolio_standards as std


GRAPH = f"{std.DIR_STYLES}/WP/PCG_WP_HumanScaleCorridor"


def _rail(graph, y_points: int, x: float):
    grid, grid_s = gb.add_node(graph, "PCGCreatePointsGridSettings", -700, int(x))
    grid_s.set_editor_property("grid_extents", unreal.Vector(50.0, (y_points - 1) * 50.0, 50.0))
    grid_s.set_editor_property("cell_size", unreal.Vector(100.0, 100.0, 100.0))
    graph.add_edge(graph.get_input_node(), "In", grid, "In")

    transform, transform_s = gb.add_node(graph, "PCGTransformPointsSettings", -350, int(x))
    transform_s.set_editor_property("scale_min", unreal.Vector(0.15, 0.5, 1.2))
    transform_s.set_editor_property("scale_max", unreal.Vector(0.15, 0.5, 1.2))
    transform_s.set_editor_property("uniform_scale", False)
    # Rail translation is authored by the two owning PCGVolume actors. UE 5.8
    # no longer exposes translation fields on PCGTransformPointsSettings.
    graph.add_edge(grid, "Out", transform, "In")

    spawner, spawner_s = gb.add_node(graph, "PCGStaticMeshSpawnerSettings", 50, int(x))
    gb.configure_spawner(spawner_s, "grass", std.MI_GREYBOX_GRASS)
    graph.add_edge(transform, "Out", spawner, "In")
    return spawner


def build(force: bool = True) -> dict:
    graph, created = gb.load_or_create_graph(GRAPH, f"{std.DIR_STYLES}/WP", force=force)
    gb.clear_graph_nodes(graph)
    graph.get_input_node().set_node_position(-1000, 0)
    graph.get_output_node().set_node_position(500, 0)
    _rail(graph, 17, -165.0)
    _rail(graph, 17, 165.0)
    graph.set_editor_property("is_standalone_graph", True)
    unreal.EditorAssetLibrary.save_asset(GRAPH)
    return {"path": GRAPH, "created": created, "clear_width_cm": 300, "clear_height_cm": 240, "grid_points_per_rail": 17}


if __name__ == "__main__":
    print(build())
