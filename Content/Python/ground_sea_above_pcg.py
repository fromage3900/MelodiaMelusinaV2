"""Create/rebuild Sea Above PCG derivatives with landscape grounding.

This intentionally leaves the shared hero graphs untouched.  The source graphs
are authored as small musical motifs; derivative graphs switch Create Points to
local-component coordinates and insert a world raycast on each direct point
branch before its existing consumer.  Landscape-only hits keep the motif
grounded while preserving original points when a ray misses.
"""

import unreal


def _raycast_node(graph, source, target, source_label, target_label):
    graph.remove_edge(source, source_label, target, target_label)
    node, settings = graph.add_node_of_type(unreal.PCGWorldRaycastElementSettings)
    settings.set_editor_property("ray_direction", unreal.Vector(0.0, 0.0, -1.0))
    settings.set_editor_property("ray_length", 100000.0)
    settings.set_editor_property("raycast_mode", unreal.PCGWorldRaycastMode.INFINITE)
    settings.set_editor_property("keep_original_point_on_miss", True)
    settings.set_editor_property("unbounded", True)
    query = settings.get_editor_property("world_query_params")
    query.set_editor_property(
        "select_landscape_hits", unreal.PCGWorldQuerySelectLandscapeHits.REQUIRE
    )
    query.set_editor_property("ignore_pcg_hits", True)
    query.set_editor_property("ignore_self_hits", True)
    settings.set_editor_property("world_query_params", query)
    x, y = source.get_node_position()
    node.set_node_position(x + 200, y)
    source.add_edge_to(source_label, node, "Origins")
    node.add_edge_to("Out", target, target_label)
    return node


def ground_graph(graph_path):
    graph = unreal.EditorAssetLibrary.load_asset(graph_path)
    if not graph:
        raise RuntimeError("Missing PCG graph: %s" % graph_path)

    # Idempotence: remove only this pass's raycast nodes, restoring their
    # source-to-target edge from the surviving graph topology.
    for old in list(graph.nodes):
        if old.get_settings() and old.get_settings().get_class().get_name() == "PCGWorldRaycastElementSettings":
            incoming = [e for e in graph.get_all_edges() if e.get_output_node() == old]
            outgoing = [e for e in graph.get_all_edges() if e.get_input_node() == old]
            source = None
            target = None
            source_label = "Out"
            target_label = "In"
            if incoming:
                edge = incoming[0]
                source = edge.get_input_node()
                source_label = edge.get_input_pin_label()
            if outgoing:
                edge = outgoing[0]
                target = edge.get_output_node()
                target_label = edge.get_output_pin_label()
            graph.remove_node(old)
            if source and target:
                graph.add_edge(source, source_label, target, target_label)

    for node in graph.nodes:
        settings = node.get_settings()
        if settings and settings.get_class().get_name() == "PCGCreatePointsSettings":
            settings.set_editor_property("coordinate_space", unreal.PCGCoordinateSpace.LOCAL_COMPONENT)

    inserted = []
    for source in list(graph.nodes):
        settings = source.get_settings()
        if not settings or settings.get_class().get_name() != "PCGCreatePointsSettings":
            continue
        for edge in list(graph.get_all_edges()):
            if edge.get_input_node() != source:
                continue
            target = edge.get_output_node()
            source_label = edge.get_input_pin_label()
            target_label = edge.get_output_pin_label()
            if target and target_label:
                node = _raycast_node(graph, source, target, source_label, target_label)
                inserted.append(node.get_name())

    unreal.EditorAssetLibrary.save_loaded_asset(graph, False)
    return {"graph": graph_path, "raycast_nodes": inserted, "node_count": len(graph.nodes)}


if __name__ == "__main__":
    print(ground_graph("/Game/EnvSandbox/PCG/Styles/SeaAbove/PCG_SeaAbove_BellTreeGarden"))
