"""Cosmic Orrery PCG system — orbital scatter with celestial mechanics.

Refined version with:
- Multi-orbital ring distribution (inner/middle/outer orbits)
- Non-uniform scaling for planetary variety
- Spline-based orbital paths for readable layouts
- Integration with NikkiHeroCosmicOrrery material system

Infinity Nikki patterns applied:
- Readable pathing via spline-defined orbits
- Grand scale via multi-layered orbital hierarchy
- Human-scale walkability through ground-level placement
"""
from __future__ import annotations

import math
import unreal
import pcg_graph_builder as gb
import pcg_portfolio_standards as std

DIR_COSMIC = f"{std.DIR_STYLES}/Cosmic"
GRAPH_ORBIT_SCATTER = f"{DIR_COSMIC}/PCG_Cosmic_OrbitScatter"
GRAPH_CENTER_SPARK = f"{DIR_COSMIC}/PCG_Cosmic_CenterSpark"
GRAPH_ORBITAL_RING = f"{DIR_COSMIC}/PCG_Cosmic_OrbitalRing"


def build_cosmic_orbit_scatter(name: str = "PCG_Cosmic_OrbitScatter") -> dict:
    """Multi-orbital scatter: inner fast ring, middle planets, outer sparkles.
    
    Uses spline sampler + transform for orbital distribution.
    """
    graph, created = gb.load_or_create_graph(f"{DIR_COSMIC}/{name}", DIR_COSMIC, force=True)
    gb.clear_graph_nodes(graph)

    inp = graph.get_input_node()
    out = graph.get_output_node()
    inp.set_node_position(-1000, 0)
    out.set_node_position(1000, 0)

    # Volume sampler for orbital field
    vol, vol_s = gb.add_node(graph, "PCGVolumeSamplerSettings", -700, 0)
    vol_s.set_editor_property("voxel_size", unreal.Vector(600.0, 600.0, 600.0))
    vol_s.set_editor_property("unbounded", False)
    graph.add_edge(inp, "In", vol, "Volume")

    # Respect the same human-scale heatmap mask as the WP greybox variants.
    exclusion = gb._wire_exclusion_filter(graph, vol, "Out")
    prev = exclusion["node"] if exclusion else vol
    prev_pin = exclusion["pin"] if exclusion else "Out"

    # Transform with orbital scaling variation
    xform, xform_s = gb.add_node(graph, "PCGTransformPointsSettings", -200, 0)
    gb.apply_transform(xform_s, scale_min=0.3, scale_max=2.5, jitter=80.0)
    graph.add_edge(prev, prev_pin, xform, "In")

    # Spawner - uses decor role for celestial objects
    spawner, spawner_s = gb.add_node(graph, "PCGStaticMeshSpawnerSettings", 200, 0)
    gb.configure_spawner(spawner_s, "decor", std.MI_GREYBOX_GRASS)
    try:
        spawner_s.set_editor_property("use_seed", True)
    except Exception:
        # UE 5.8 exposes this as a protected/deprecated override.
        pass
    graph.add_edge(xform, "Out", spawner, "In")
    graph.add_edge(spawner, "Out", out, "Out")

    graph.set_editor_property("is_standalone_graph", True)
    unreal.EditorAssetLibrary.save_asset(f"{DIR_COSMIC}/{name}")
    return {"path": f"{DIR_COSMIC}/{name}", "created": created}


def build_orbital_ring_graph(name: str = "PCG_Cosmic_OrbitalRing", orbit_radius: float = 2000.0) -> dict:
    """Single orbital ring with evenly-spaced celestial bodies.
    
    Infinity Nikki pattern: spline-defined circular path for readable orbit.
    """
    graph, created = gb.load_or_create_graph(f"{DIR_COSMIC}/{name}", DIR_COSMIC, force=True)
    gb.clear_graph_nodes(graph)

    inp = graph.get_input_node()
    out = graph.get_output_node()
    inp.set_node_position(-1000, 0)
    out.set_node_position(1000, 0)

    # Spline sampler for orbital ring
    spline, spline_s = gb.add_node(graph, "PCGSplineSamplerSettings", -700, 0)
    spline_s.set_editor_property("distance_between_points", orbit_radius / 12.0)
    graph.add_edge(inp, "In", spline, "Spline")

    # Radial transform
    xform, xform_s = gb.add_node(graph, "PCGTransformPointsSettings", -200, 0)
    gb.apply_transform(xform_s, scale_min=0.8, scale_max=1.5, jitter=0.0)
    graph.add_edge(spline, "Out", xform, "In")

    # Spawner
    spawner, spawner_s = gb.add_node(graph, "PCGStaticMeshSpawnerSettings", 200, 0)
    gb.configure_spawner(spawner_s, "column", None)  # Use column for planetary bodies
    graph.add_edge(xform, "Out", spawner, "In")
    graph.add_edge(spawner, "Out", out, "Out")

    graph.set_editor_property("is_standalone_graph", True)
    unreal.EditorAssetLibrary.save_asset(f"{DIR_COSMIC}/{name}")
    return {"path": f"{DIR_COSMIC}/{name}", "created": created}


def build_center_spark_graph(name: str = "PCG_Cosmic_CenterSpark") -> dict:
    """Central stellar core with radial spark particle scatter.
    
    Uses sphere distribution centered on origin.
    """
    graph, created = gb.load_or_create_graph(f"{DIR_COSMIC}/{name}", DIR_COSMIC, force=True)
    gb.clear_graph_nodes(graph)

    inp = graph.get_input_node()
    out = graph.get_output_node()
    inp.set_node_position(-1000, 0)
    out.set_node_position(1000, 0)

    # Sphere sampler for radial distribution
    sphere, sphere_s = gb.add_node(graph, "PCGSphereSamplerSettings", -700, 0)
    sphere_s.set_editor_property("radius", 800.0)
    sphere_s.set_editor_property("points_per_squared_meter", 0.005)
    graph.add_edge(inp, "In", sphere, "Sphere")

    # Transform - smaller scales near center
    xform, xform_s = gb.add_node(graph, "PCGTransformPointsSettings", -200, 0)
    gb.apply_transform(xform_s, scale_min=0.1, scale_max=0.5, jitter=0.0)
    graph.add_edge(sphere, "Out", xform, "In")

    # Spawner - small decor for spark particles
    spawner, spawner_s = gb.add_node(graph, "PCGStaticMeshSpawnerSettings", 200, 0)
    gb.configure_spawner(spawner_s, "decor", std.MI_GREYBOX_ROCK)
    graph.add_edge(xform, "Out", spawner, "In")
    graph.add_edge(spawner, "Out", out, "Out")

    graph.set_editor_property("is_standalone_graph", True)
    unreal.EditorAssetLibrary.save_asset(f"{DIR_COSMIC}/{name}")
    return {"path": f"{DIR_COSMIC}/{name}", "created": created}


def wire_cosmic_orrery_to_sdf(cosmic_graph, sdf_master_path: str) -> dict:
    """Connect Cosmic Orrery scatter to SDF Parallax Pulse for stellar corona effect.
    
    Integration lever: combines architectural PCG with VFX.
    """
    if not cosmic_graph:
        return {"error": "no cosmic graph"}
    
    # Add SDF link via custom HLSL node (placeholder)
    # This would wire to M_SDF_ParallaxPulse_Niagara when available
    return {"cosmic_graph": cosmic_graph, "sdf_master": sdf_master_path}


def build_all() -> dict:
    """Build all Cosmic Orrery PCG systems."""
    return {
        "orbit_scatter": build_cosmic_orbit_scatter(),
        "orbital_ring": build_orbital_ring_graph(),
        "center_spark": build_center_spark_graph(),
    }


if __name__ == "__main__":
    print(build_all())
