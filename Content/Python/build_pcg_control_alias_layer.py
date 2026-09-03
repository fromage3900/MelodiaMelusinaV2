"""Build the shared native PCG_Control reader/alias graph.

Each reader uses the canonical ``BP_MelodiaPCGControl`` tag and emits the
actual attribute name consumed by PCG settings.  The hero builders still take
their discrete values from a snapshot because authored point arrays must be
rebuilt on demand; this graph is the auditable runtime bridge for universal
PCG settings and future graph branches.
"""
from __future__ import annotations

from typing import Any

import pcg_hero_music_control as control


DEST_FOLDER = "/Game/EnvSandbox/PCG/Universal"
GRAPH_PATH = f"{DEST_FOLDER}/PCG_ControlReaderAliases"

CONTROL_ALIAS_TARGETS = control.CONTROL_ALIAS_TARGETS


def _set(obj: Any, prop: str, value: Any) -> bool:
    try:
        obj.set_editor_property(prop, value)
        return True
    except Exception:
        return False


def _set_output_attribute(unreal: Any, settings: Any, name: str) -> None:
    selector = settings.get_editor_property("output_attribute_name")
    # UE 5.8's Python binding returns True from set_attribute_name() but does
    # not mutate this selector. Importing the serialized selector text does.
    try:
        if not selector.import_text(f"PCGBegin({name})PCGEnd"):
            raise RuntimeError("import_text returned false")
    except Exception:
        if not hasattr(selector, "set_attribute_name") or not selector.set_attribute_name(name):
            raise RuntimeError(f"could not set output attribute selector to {name}")
    if not _set(settings, "output_attribute_name", selector):
        raise RuntimeError(f"could not assign output attribute selector for {name}")


def _configure_reader(unreal: Any, settings: Any, source_name: str, target_name: str) -> None:
    selector = settings.get_editor_property("actor_selector")
    for prop, value in (
        ("actor_filter", unreal.PCGActorFilter.ALL_WORLD_ACTORS),
        ("actor_selection", unreal.PCGActorSelection.BY_TAG),
        ("actor_selection_tag", "PCG_Control"),
        ("select_multiple", False),
    ):
        if not _set(selector, prop, value):
            raise RuntimeError(f"control reader selector property failed: {prop}")
    if not _set(settings, "actor_selector", selector):
        raise RuntimeError("control reader actor selector could not be assigned")
    if not _set(settings, "property_name", source_name):
        raise RuntimeError(f"control reader source property failed: {source_name}")
    _set(settings, "always_requery_actors", True)
    _set(settings, "b_always_requery_actors", True)
    _set_output_attribute(unreal, settings, target_name)


def build_control_alias_graph() -> dict[str, Any]:
    import unreal
    import pcg_graph_builder as graph_builder

    if not unreal.EditorAssetLibrary.does_directory_exist(DEST_FOLDER):
        unreal.EditorAssetLibrary.make_directory(DEST_FOLDER)
    graph, created = graph_builder.load_or_create_graph(GRAPH_PATH, DEST_FOLDER, force=True)
    graph_builder.clear_graph_nodes(graph)
    graph.get_input_node().set_node_position(-900, 0)
    graph.get_output_node().set_node_position(900, 0)

    nodes = []
    for index, (source_name, target_name) in enumerate(CONTROL_ALIAS_TARGETS.items()):
        node, settings = graph_builder.add_node(graph, "PCGGetActorPropertySettings", -650, (index - 5) * 90)
        _configure_reader(unreal, settings, source_name, target_name)
        graph.add_edge(node, "Out", graph.get_output_node(), "Out")
        nodes.append({"source": source_name, "target": target_name, "node": node.get_name()})

    _set(graph, "is_standalone_graph", True)
    unreal.EditorAssetLibrary.save_asset(GRAPH_PATH, only_if_is_dirty=False)
    result = {
        "graph": GRAPH_PATH,
        "created": created,
        "reader_count": len(nodes),
        "tag": "PCG_Control",
        "readers": nodes,
        "edge_contract": "each GetActorProperty.Out -> graph output; aliases are exact target attributes",
    }
    unreal.log(f"[PCG Control Alias Layer] built {result}")
    return result


if __name__ == "__main__":
    print(build_control_alias_graph())
