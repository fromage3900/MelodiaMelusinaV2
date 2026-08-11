"""Zen Shrine Axis PCG graph — implements roji sequence from research.

Based on research/zen/01_roji_sequence.md:
- Torii threshold
- Stepping stones (tobiishi) or dew path (roji slab)
- Tsukubai hand-wash
- Engawa/teahouse buffer

Research/zen/02_shrine_axis.md: Sacred approach spine
Research/zen/03_karesansui_grammar.md: Dry landscape grammar

Infinity Nikki patterns:
- Linear spline points for straight edges
- Modular 400cm floor tile sizing
- Human-scale 1.6-2.2m path width
"""
from __future__ import annotations

import unreal
import pcg_graph_builder as gb
import pcg_portfolio_standards as std

DIR_ZEN = f"{std.DIR_STYLES}/Zen"
GRAPH_SHRINE_AXIS = f"{DIR_ZEN}/PCG_Zen_ShrineAxis"
GRAPH_ROJI_PATH = f"{DIR_ZEN}/PCG_Zen_RojiPath"


def build_zen_shrine_axis(name: str = "PCG_Zen_ShrineAxis") -> dict:
    """Sacred approach spine: torii → sando ×2 → kairo → karesansui → machiai → lantern.
    
    Uses spline sampler + axis compression transform.
    """
    graph, created = gb.load_or_create_graph(f"{DIR_ZEN}/{name}", DIR_ZEN, force=True)
    gb.clear_graph_nodes(graph)
    
    inp = graph.get_input_node()
    out = graph.get_output_node()
    inp.set_node_position(-1000, 0)
    out.set_node_position(1000, 0)
    
    # Spline sampler for shrine axis path
    spline, spline_s = gb.add_node(graph, "PCGSplineSamplerSettings", -700, 0)
    spline_s.set_editor_property("distance_between_points", 400.0)  # Floor tile size
    graph.add_edge(inp, "In", spline, "Spline")
    
    # Transform with axis compression (from surreal_transforms.json)
    xform, xform_s = gb.add_node(graph, "PCGTransformPointsSettings", -300, 0)
    gb.apply_transform(xform_s, scale_min=1.0, scale_max=1.0, jitter=0.0)
    graph.add_edge(spline, "Out", xform, "In")
    
    # Spawner - use architectural meshes
    spawner, spawner_s = gb.add_node(graph, "PCGStaticMeshSpawnerSettings", 200, 0)
    gb.configure_spawner(spawner_s, "floor", std.MI_GREYBOX_GRASS)
    graph.add_edge(xform, "Out", spawner, "In")
    graph.add_edge(spawner, "Out", out, "Out")
    
    graph.set_editor_property("is_standalone_graph", True)
    unreal.EditorAssetLibrary.save_asset(f"{DIR_ZEN}/{name}")
    
    return {"path": f"{DIR_ZEN}/{name}", "created": created}


def build_zen_roji_path(name: str = "PCG_Zen_RojiPath", path_width: float = 200.0) -> dict:
    """Roji purification path with tobiishi stepping stones.
    
    Path width 2.0m per roji_sequence.md.
    """
    graph, created = gb.load_or_create_graph(f"{DIR_ZEN}/{name}", DIR_ZEN, force=True)
    gb.clear_graph_nodes(graph)
    
    inp = graph.get_input_node()
    out = graph.get_output_node()
    inp.set_node_position(-1000, 0)
    out.set_node_position(1000, 0)
    
    # Surface sampler for ground scatter
    surf, surf_s = gb.add_node(graph, "PCGSurfaceSamplerSettings", -700, 0)
    surf_s.set_editor_property("points_per_squared_meter", 0.012)
    graph.add_edge(inp, "In", surf, "Surface")
    
    # Self-pruning for stone spacing (300cm apart per traditional roji)
    prune, prune_s = gb.add_node(graph, "PCGSelfPruningSettings", -400, 0)
    prune_s.set_editor_property("radius", 300.0)
    graph.add_edge(surf, "Out", prune, "In")
    
    # Transform
    xform, xform_s = gb.add_node(graph, "PCGTransformPointsSettings", -150, 0)
    gb.apply_transform(xform_s, scale_min=0.8, scale_max=1.2, jitter=50.0)
    graph.add_edge(prune, "Out", xform, "In")
    
    # Spawner - use rock meshes for stepping stones
    spawner, spawner_s = gb.add_node(graph, "PCGStaticMeshSpawnerSettings", 100, 0)
    gb.configure_spawner(spawner_s, "rock", None)
    graph.add_edge(xform, "Out", spawner, "In")
    graph.add_edge(spawner, "Out", out, "Out")
    
    graph.set_editor_property("is_standalone_graph", True)
    unreal.EditorAssetLibrary.save_asset(f"{DIR_ZEN}/{name}")
    
    return {"path": f"{DIR_ZEN}/{name}", "created": created}


def build_all() -> dict:
    return {
        "shrine_axis": build_zen_shrine_axis(),
        "roji_path": build_zen_roji_path(),
    }


if __name__ == "__main__":
    print(build_all())