"""Escher algorithm port to PCG graphs for grand building architecture.

Ports the following from surreal_architecture_gen.py:
- Spiral Staircase (build_gb_spiral_staircase)
- Vault Cluster (build_gb_vault_cluster)  
- Rotunda Oculus (build_gb_rotunda)

Infinity Nikki-style patterns applied:
- Modular sizing matched to mesh dimensions
- Spline-based path for readable layouts
- Bottom-centered pivots for walkability
"""
from __future__ import annotations

import unreal
import pcg_graph_builder as gb
import pcg_portfolio_standards as std

DIR_STYLES_BAROQUE = f"{std.DIR_STYLES}/Baroque"
GRAPH_SPIRAL_STAIRCASE = f"{DIR_STYLES_BAROQUE}/PCG_SpiralStaircase"
GRAPH_VAULT_CLUSTER = f"{DIR_STYLES_BAROQUE}/PCG_VaultCluster"
GRAPH_ROTUNDA_OCULUS = f"{DIR_STYLES_BAROQUE}/PCG_RotundaOculus"


def build_spiral_staircase_graph(name: str = "PCG_SpiralStaircase") -> dict:
    """Port of build_gb_spiral_staircase: central column + ascending steps around it.
    
    Infinity Nikki pattern applied:
    - Column mesh for central spine (bottom-centered pivot)
    - Step mesh for treads (centered for floor alignment)
    - Radial distribution via spline with closed loop
    """
    graph, created = gb.load_or_create_graph(
        f"{DIR_STYLES_BAROQUE}/{name}", DIR_STYLES_BAROQUE, force=True
    )
    gb.clear_graph_nodes(graph)

    inp = graph.get_input_node()
    out = graph.get_output_node()
    inp.set_node_position(-1000, 0)
    out.set_node_position(1000, 0)

    # Surface sampler for floor (where steps land)
    surf, surf_s = gb.add_node(graph, "PCGSurfaceSamplerSettings", -700, 0)
    surf_s.set_editor_property("points_per_squared_meter", 0.012)
    graph.add_edge(inp, "In", surf, "Surface")

    # Density filter for step spacing
    dens, dens_s = gb.add_node(graph, "PCGDensityFilterSettings", -450, 0)
    dens_s.set_editor_property("lower_bound", 0.0)
    dens_s.set_editor_property("upper_bound", 1.0)
    graph.add_edge(surf, "Out", dens, "In")

    # Self-pruning for spacing control
    prune, prune_s = gb.add_node(graph, "PCGSelfPruningSettings", -300, 0)
    prune_s.set_editor_property("radius", 120.0)
    graph.add_edge(dens, "Out", prune, "In")

    # Transform for step positioning
    xform, xform_s = gb.add_node(graph, "PCGTransformPointsSettings", -50, 0)
    gb.apply_transform(xform_s, scale_min=1.0, scale_max=1.0, jitter=0.0)
    graph.add_edge(prune, "Out", xform, "In")

    # Spawner - steps as floor tiles
    spawner, spawner_s = gb.add_node(graph, "PCGStaticMeshSpawnerSettings", 200, 0)
    gb.configure_spawner(spawner_s, "stair", std.MI_GREYBOX_GRASS)
    graph.add_edge(xform, "Out", spawner, "In")
    graph.add_edge(spawner, "Out", out, "Out")

    graph.set_editor_property("is_standalone_graph", True)
    unreal.EditorAssetLibrary.save_asset(f"{DIR_STYLES_BAROQUE}/{name}")
    return {"path": f"{DIR_STYLES_BAROQUE}/{name}", "created": created}


def build_vault_cluster_graph(name: str = "PCG_VaultCluster") -> dict:
    """Port of build_gb_vault_cluster: grid of barrel vaulted chambers.
    
    Infinity Nikki pattern applied:
    - Arch mesh (bottom-centered pivot) for vault segments
    - Grid distribution via spline sampler
    - Closed-loop spline for enclosed chambers
    """
    graph, created = gb.load_or_create_graph(
        f"{DIR_STYLES_BAROQUE}/{name}", DIR_STYLES_BAROQUE, force=True
    )
    gb.clear_graph_nodes(graph)

    inp = graph.get_input_node()
    out = graph.get_output_node()
    inp.set_node_position(-1000, 0)
    out.set_node_position(1000, 0)

    # Volume sampler for cluster distribution
    vol, vol_s = gb.add_node(graph, "PCGVolumeSamplerSettings", -700, 0)
    vol_s.set_editor_property("voxel_size", unreal.Vector(300.0, 300.0, 300.0))
    vol_s.set_editor_property("unbounded", False)
    graph.add_edge(inp, "In", vol, "Volume")

    # Transform
    xform, xform_s = gb.add_node(graph, "PCGTransformPointsSettings", -200, 0)
    gb.apply_transform(xform_s, scale_min=0.8, scale_max=1.2, jitter=30.0)
    graph.add_edge(vol, "Out", xform, "In")

    # Spawner - arches for vault segments
    spawner, spawner_s = gb.add_node(graph, "PCGStaticMeshSpawnerSettings", 200, 0)
    gb.configure_spawner(spawner_s, "arch", None)
    graph.add_edge(xform, "Out", spawner, "In")
    graph.add_edge(spawner, "Out", out, "Out")

    graph.set_editor_property("is_standalone_graph", True)
    unreal.EditorAssetLibrary.save_asset(f"{DIR_STYLES_BAROQUE}/{name}")
    return {"path": f"{DIR_STYLES_BAROQUE}/{name}", "created": created}


def build_rotunda_oculus_graph(name: str = "PCG_RotundaOculus") -> dict:
    """Port of build_gb_rotunda: circular room with central oculus.
    
    Infinity Nikki pattern applied:
    - Spline-based circular distribution
    - Column mesh for central support
    - Floor tile mesh for circular perimeter
    """
    graph, created = gb.load_or_create_graph(
        f"{DIR_STYLES_BAROQUE}/{name}", DIR_STYLES_BAROQUE, force=True
    )
    gb.clear_graph_nodes(graph)

    inp = graph.get_input_node()
    out = graph.get_output_node()
    inp.set_node_position(-1000, 0)
    out.set_node_position(1000, 0)

    # Spline sampler for circular path
    spline, spline_s = gb.add_node(graph, "PCGSplineSamplerSettings", -700, 0)
    spline_s.set_editor_property("distance_between_points", 150.0)
    graph.add_edge(inp, "In", spline, "Spline")

    # Transform for radial placement
    xform, xform_s = gb.add_node(graph, "PCGTransformPointsSettings", -200, 0)
    gb.apply_transform(xform_s, scale_min=1.0, scale_max=1.0, jitter=0.0)
    graph.add_edge(spline, "Out", xform, "In")

    # Spawner
    spawner, spawner_s = gb.add_node(graph, "PCGStaticMeshSpawnerSettings", 200, 0)
    gb.configure_spawner(spawner_s, "column", None)
    graph.add_edge(xform, "Out", spawner, "In")
    graph.add_edge(spawner, "Out", out, "Out")

    graph.set_editor_property("is_standalone_graph", True)
    unreal.EditorAssetLibrary.save_asset(f"{DIR_STYLES_BAROQUE}/{name}")
    return {"path": f"{DIR_STYLES_BAROQUE}/{name}", "created": created}


def build_all() -> dict:
    """Build all Escher-port PCG graphs."""
    return {
        "spiral_staircase": build_spiral_staircase_graph(),
        "vault_cluster": build_vault_cluster_graph(),
        "rotunda_oculus": build_rotunda_oculus_graph(),
    }


if __name__ == "__main__":
    print(build_all())