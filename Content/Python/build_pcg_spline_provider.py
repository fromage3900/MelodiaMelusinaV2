"""Spline provider helper for PCG graphs that require spline input.

Provides BP_PathSplineProvider pattern proven on CorniceEx fix.
Supports: Bezier graphs, Path graphs, Wall garden graphs.

Infinity Nikki-style usage:
- Linear spline points for straight edges
- Closed loops for enclosed boundaries
- Offset-and-difference edge detection for walls/trims
"""
from __future__ import annotations

DEST_FOLDER = "/Game/EnvSandbox/PCG/Universal/Subgraphs"


def spawn_spline_provider(eas, label: str = "BP_PathSplineProvider", points: list[tuple] | None = None):
    """Spawn or retrieve a BP_PathSplineProvider with optional points.
    
    Args:
        eas: EditorActorSubsystem
        label: Actor label to find or create
        points: List of (x, y, z) tuples for spline points. If None, creates default 3-point path.
    
    Returns:
        SplineComponent or None
    """
    import unreal
    
    # Find existing spline provider
    for actor in eas.get_all_level_actors() or []:
        if actor.get_actor_label() == label:
            spline_comp = actor.get_component_by_class(unreal.SplineComponent)
            if spline_comp and points:
                _set_spline_points(spline_comp, points)
            return spline_comp
    
    # Spawn new spline provider
    spline_cls = unreal.BP_PathSplineProvider.static_class() if hasattr(unreal, "BP_PathSplineProvider") else unreal.SplineActor.static_class()
    
    if points is None:
        points = [(0, 0, 0), (1000, 0, 0), (2000, 0, 0)]  # Default path
    
    actor = eas.spawn_actor_from_class(spline_cls, unreal.Vector(*points[0]), unreal.Rotator(0, 0, 0))
    if actor:
        actor.set_actor_label(label)
        spline_comp = actor.get_component_by_class(unreal.SplineComponent)
        if spline_comp:
            _set_spline_points(spline_comp, points)
            spline_comp.set_editor_property("closed_loop", False)
            # Linear points for architectural straight edges
            for i in range(len(points)):
                spline_comp.set_editor_property("point_type", unreal.SplinePointType.Linear)
        return spline_comp
    return None


def _set_spline_points(spline_comp, points: list[tuple]) -> None:
    """Set spline points using Vector list (not SplinePoint structs)."""
    import unreal
    
    for i, pt in enumerate(points):
        pos = unreal.Vector(pt[0], pt[1], pt[2])
        if i < spline_comp.get_spline_point_number():
            spline_comp.set_spline_point(i, pos)
        else:
            spline_comp.add_spline_point(pos)


def build_spline_based_graph(graph_path: str, spline_label: str = "BP_PathSplineProvider") -> dict:
    """Wire a graph to use a spline provider's points.
    
    Pattern proven on CorniceEx fix:
    SplineSampler → Transform → Spawner (no intermediate subdivision needed)
    """
    import unreal
    import pcg_graph_builder as gb
    
    folder = graph_path.rsplit("/", 1)[0]
    graph, created = gb.load_or_create_graph(graph_path, folder, force=True)
    
    inp = graph.get_input_node()
    out = graph.get_output_node()
    inp.set_node_position(-1000, 0)
    out.set_node_position(1000, 0)
    
    # Spline sampler for path-based scattering
    sampler, sampler_settings = gb.add_node(graph, "PCGSplineSamplerSettings", -700, 0)
    sampler_settings.set_editor_property("distance_between_points", 100.0)
    graph.add_edge(inp, "In", sampler, "Spline")
    
    # Transform with gentle randomization
    xform, xform_settings = gb.add_node(graph, "PCGTransformPointsSettings", -200, 0)
    gb.apply_transform(xform_settings, scale_min=0.5, scale_max=1.5, jitter=20.0)
    graph.add_edge(sampler, "Out", xform, "In")
    
    # Spawner - uses generic cube for now, override per style
    spawner, spawner_settings = gb.add_node(graph, "PCGStaticMeshSpawnerSettings", 250, 0)
    spawner_settings.set_editor_property("use_seed", True)
    
    graph.add_edge(xform, "Out", spawner, "In")
    graph.add_edge(spawner, "Out", out, "Out")
    
    unreal.EditorAssetLibrary.save_asset(graph_path)
    return {"path": graph_path, "created": created, "spline_provider": spline_label}


def apply_spline_to_wall_graph(graph, points: list[tuple] | None = None) -> dict:
    """Apply spline input to a wall-detail graph for testing without wall-tagged actors.
    
    Infinity Nikki pattern: spline-defined boundary with offset edges.
    """
    import unreal
    import pcg_graph_builder as gb
    
    # Clear existing and rebuild with spline chain
    gb.clear_graph_nodes(graph)
    
    inp = graph.get_input_node()
    out = graph.get_output_node()
    inp.set_node_position(-1000, 0)
    out.set_node_position(1000, 0)
    
    # Spline sampler
    sampler, sampler_settings = gb.add_node(graph, "PCGSplineSamplerSettings", -700, 0)
    sampler_settings.set_editor_property("distance_between_points", 150.0)
    graph.add_edge(inp, "In", sampler, "Spline")
    
    # Transform
    xform, xform_settings = gb.add_node(graph, "PCGTransformPointsSettings", -200, 0)
    gb.apply_transform(xform_settings, scale_min=0.5, scale_max=1.2, jitter=10.0)
    graph.add_edge(sampler, "Out", xform, "In")
    
    # Spawner
    spawner, spawner_settings = gb.add_node(graph, "PCGStaticMeshSpawnerSettings", 250, 0)
    graph.add_edge(xform, "Out", spawner, "In")
    graph.add_edge(spawner, "Out", out, "Out")
    
    return {"spline_sampler": True}