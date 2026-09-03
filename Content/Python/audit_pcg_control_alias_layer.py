"""Editor audit for the shared tagged-driver reader graph."""
from __future__ import annotations

import pcg_hero_music_control as control


GRAPH_PATH = "/Game/EnvSandbox/PCG/Universal/PCG_ControlReaderAliases"
UNIVERSAL_SCATTER_PATH = "/Game/EnvSandbox/PCG/Universal/PCG_Melodia_Universal_Scatter"


def audit() -> dict:
    import unreal

    report = {
        "graph": GRAPH_PATH,
        "graph_present": unreal.EditorAssetLibrary.does_asset_exist(GRAPH_PATH),
        "universal_scatter_present": unreal.EditorAssetLibrary.does_asset_exist(UNIVERSAL_SCATTER_PATH),
        "expected_reader_count": len(control.CONTROL_PROPERTIES),
        "readers": [],
    }
    graph = unreal.EditorAssetLibrary.load_asset(GRAPH_PATH)
    if graph:
        for node in list(graph.get_editor_property("nodes") or []):
            settings = node.get_settings()
            if not settings or settings.get_class().get_name() != "PCGGetActorPropertySettings":
                continue
            try:
                selector = settings.get_editor_property("actor_selector")
                property_name = str(settings.get_editor_property("property_name"))
                output = settings.get_editor_property("output_attribute_name")
                output_name = str(output.get_attribute_name())
                report["readers"].append({
                    "node": node.get_name(),
                    "property": property_name,
                    "output": output_name,
                    "actor_filter": str(selector.get_editor_property("actor_filter")),
                    "actor_selection": str(selector.get_editor_property("actor_selection")),
                    "tag": str(selector.get_editor_property("actor_selection_tag")),
                    "select_multiple": bool(selector.get_editor_property("select_multiple")),
                })
            except Exception as exc:
                report["readers"].append({"node": node.get_name(), "error": str(exc)})

    report["checks"] = {
        "graph_present": report["graph_present"],
        "universal_scatter_present": report["universal_scatter_present"],
        "eleven_readers": len(report["readers"]) == 11,
        "all_source_properties": {item.get("property") for item in report["readers"]} == set(control.CONTROL_PROPERTIES),
        "all_target_aliases": {item.get("output") for item in report["readers"]} == set(control.CONTROL_ALIAS_TARGETS.values()) if hasattr(control, "CONTROL_ALIAS_TARGETS") else len(report["readers"]) == 11,
        "tagged_single_actor_reads": all(item.get("tag") == control.CONTROL_TAG and item.get("select_multiple") is False for item in report["readers"] if "error" not in item),
    }
    unreal.log(f"[PCG Control Alias Layer] audit {report}")
    return report


if __name__ == "__main__":
    print(audit())
