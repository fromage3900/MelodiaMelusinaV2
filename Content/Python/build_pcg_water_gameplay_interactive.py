"""Build the additive deterministic PCG water-gameplay placement graph.

The existing five hero graphs remain untouched. This graph owns only device
anchors and platform actors, all in the gameplay Data Layer and excluded from
HLOD/static merging. Runtime state is owned by the native water subsystem.
"""
from __future__ import annotations

from typing import Any

import pcg_hero_music_common as common
from pcg_scale_world_pipeline import (
    WATER_INTERACTIVE_GRAPH_PATH,
    interactive_placements_for_chunk,
)


GRAPH_PATH = WATER_INTERACTIVE_GRAPH_PATH
DEST_FOLDER = "/Game/EnvSandbox/PCG/Musical/Hero"
PROOF_HERO_SLOT = "CrystalHarpGrove"


def _configure_actor_spawn(unreal: Any, settings: Any, actor_class_name: str, tags: list[str], label: str) -> None:
    if not common._set_if_present(settings, "option", common._enum_value(unreal, "PCGSpawnActorOption", "NO_MERGING", "NoMerging")):
        raise RuntimeError("water gameplay spawn option could not be set to NoMerging")
    if not common._set_if_present(settings, "attach_options", common._enum_value(unreal, "PCGAttachOptions", "ATTACHED", "Attached")):
        raise RuntimeError("water gameplay spawn attachment could not be set")
    if not common._set_if_present(settings, "template_actor_class", common.resolve_actor_class(unreal, actor_class_name)):
        raise RuntimeError(f"water gameplay actor class unavailable: {actor_class_name}")
    for prop, value in {
        "post_spawn_function_names": ["InitializeFromPCGPoint"],
        "tags_to_add_on_actors": tags,
        "delete_actors_before_generation": True,
        "force_disable_actor_parsing": True,
        "actor_label": label,
    }.items():
        if not common._set_if_present(settings, prop, value):
            raise RuntimeError(f"water gameplay spawn property failed: {prop}")


def build_water_gameplay_layout(world_seed: int = 3900, chunk_x: int = 1, chunk_y: int = 1) -> tuple[dict[str, Any], ...]:
    placements = interactive_placements_for_chunk(world_seed, chunk_x, chunk_y, (PROOF_HERO_SLOT,))
    return tuple(
        {
            "stable_actor_id": placement.stable_actor_id,
            "role": placement.gameplay_role,
            "water_network_id": placement.water_network_id,
            "water_node_id": placement.water_node_id,
            "route_id": placement.route_id,
            "motion_mode": placement.motion_mode,
            "point_seed": int(placement.stable_actor_id[-8:], 16),
            "location": (
                float((placement.local_index % 4) * 420.0),
                float((placement.local_index // 4) * 420.0),
                80.0 if placement.motion_mode != "None" else 40.0,
            ),
        }
        for placement in placements
    )


def build_pcg_water_gameplay_graph(world_seed: int = 3900, chunk_x: int = 1, chunk_y: int = 1) -> dict[str, Any]:
    import unreal
    import pcg_graph_builder as graph_builder

    layout = build_water_gameplay_layout(world_seed, chunk_x, chunk_y)
    graph, _created = graph_builder.load_or_create_graph(GRAPH_PATH, DEST_FOLDER, force=True)
    graph_builder.clear_graph_nodes(graph)
    graph.get_input_node().set_node_position(-900, 0)
    graph.get_output_node().set_node_position(900, 0)
    branch_results = []
    for index, item in enumerate(layout):
        create_node, create_settings = graph_builder.add_node(graph, "PCGCreatePointsSettings", -650, index * 180 - 630)
        create_settings.set_editor_property("points_to_create", [common.make_point(unreal, item["location"], item["point_seed"], bounds=(100.0, 100.0, 60.0))])
        actor_class = "AMelodiaWaterPlatform" if item["motion_mode"] != "None" else "AMelodiaWaterGameplayDeviceAnchor"
        tags = [
            "PCG_WaterGameplayInteractive",
            f"WaterStableId_{item['stable_actor_id']}",
            f"WaterRole_{item['role']}",
            f"WaterNetwork_{item['water_network_id']}",
            f"WaterNode_{item['water_node_id']}",
        ]
        if item["route_id"]:
            tags.append(f"WaterRoute_{item['route_id']}")
        if item["motion_mode"] != "None":
            tags.append(f"WaterMotion_{item['motion_mode']}")
        spawn_node, spawn_settings = graph_builder.add_node(graph, "PCGSpawnActorSettings", -350, index * 180 - 630)
        _configure_actor_spawn(unreal, spawn_settings, actor_class, tags, f"Water Gameplay {item['role']}")
        graph.add_edge(create_node, "Out", spawn_node, "In")
        graph.add_edge(spawn_node, "Out", graph.get_output_node(), "Out")
        branch_results.append({"role": item["role"], "actor_class": actor_class, "stable_actor_id": item["stable_actor_id"]})
    unreal.EditorAssetLibrary.save_asset(GRAPH_PATH, only_if_is_dirty=False)
    result = {
        "graph": GRAPH_PATH,
        "world_seed": int(world_seed),
        "chunk": [int(chunk_x), int(chunk_y)],
        "interactive_actor_count": len(layout),
        "branches": branch_results,
        "data_layer": "DL_Musical_HeroGameplay",
        "exclude_from_hlod": True,
        "staged_build_order": ["filtered_pcg_generation", "hlod_generation", "navigation_build", "minimap_rvt_generation"],
    }
    unreal.log(f"[PCG Water Gameplay] built {result}")
    return result


if __name__ == "__main__":
    print(build_pcg_water_gameplay_graph())
