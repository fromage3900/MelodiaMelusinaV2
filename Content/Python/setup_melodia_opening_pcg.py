"""Build and bind the first safe PCG dressing graph for Melodia Dreamstate."""
from __future__ import annotations

import json
from pathlib import Path

import unreal

import pcg_graph_builder as gb
import pcg_validate_helpers as vh


LEVEL = "/Game/Melodia/Levels/Opening/L_Melodia_Dreamstate"
GRAPH_PATH = "/Game/Melodia/PCG/PCG_Dreamstate_DistantRuin"
GRAPH_DIR = "/Game/Melodia/PCG"
VOLUME_LABEL = "PCG_MelodiaOpening_Dream_Atmosphere"
REPORT = Path(unreal.Paths.project_dir()) / "Saved" / "Melodia" / "dreamstate_pcg_setup.json"
EXCLUDE = {"Dreamstate_BifrostBridge", "GB_Dream_StartTerrace", "GB_Dream_MidTerrace", "GB_Dream_WakeTerrace"}


def _tag(actor, tag):
    tags = list(actor.tags)
    name = unreal.Name(tag)
    if name not in tags:
        tags.append(name)
        actor.tags = tags


def main():
    levels = unreal.get_editor_subsystem(unreal.LevelEditorSubsystem)
    actors = unreal.get_editor_subsystem(unreal.EditorActorSubsystem)
    if not levels.load_level(LEVEL):
        raise RuntimeError(f"Could not load {LEVEL}")
    by_label = {actor.get_actor_label(): actor for actor in actors.get_all_level_actors()}
    volume = by_label.get(VOLUME_LABEL)
    if not volume:
        raise RuntimeError(f"Missing reserved PCG volume: {VOLUME_LABEL}")
    for label in EXCLUDE:
        actor = by_label.get(label)
        if actor:
            _tag(actor, "PCG_Exclude")

    graph, _ = gb.load_or_create_graph(GRAPH_PATH, GRAPH_DIR, force=True)
    gb.clear_graph_nodes(graph)
    # The atmosphere envelope deliberately lives beside the walkable bridge.
    # This avoids fragile graph-difference pins and keeps procedural geometry
    # strictly decorative/off-route.
    volume.set_actor_location(unreal.Vector(0.0, 720.0, 220.0), False, False)
    volume.set_actor_scale3d(unreal.Vector(10.0, 2.2, 2.0))
    sampler, sampler_settings = gb.add_node(graph, "PCGVolumeSamplerSettings", -600, 0)
    sampler_settings.set_editor_property("voxel_size", unreal.Vector(550.0, 550.0, 550.0))
    sampler_settings.set_editor_property("unbounded", False)
    transform, transform_settings = gb.add_node(graph, "PCGTransformPointsSettings", -200, 0)
    gb.apply_transform(transform_settings, scale_min=0.16, scale_max=0.45, jitter=90.0)
    spawner, spawner_settings = gb.add_node(graph, "PCGStaticMeshSpawnerSettings", 150, 0)
    if not gb.configure_spawner(spawner_settings, "rock", None):
        raise RuntimeError("Could not configure Dreamstate rock spawner")
    graph.add_edge(graph.get_input_node(), "In", sampler, "Volume")
    graph.add_edge(sampler, "Out", transform, "In")
    graph.add_edge(transform, "Out", spawner, "In")
    graph.add_edge(spawner, "Out", graph.get_output_node(), "Out")
    graph.set_editor_property("is_standalone_graph", True)
    meta = {"role": "rock", "sampling_radius_cm": 550.0, "off_route_volume": True}
    unreal.EditorAssetLibrary.save_asset(GRAPH_PATH, only_if_is_dirty=False)
    component = volume.get_component_by_class(unreal.PCGComponent)
    if not component:
        raise RuntimeError("Dreamstate PCG volume has no PCG component")
    gb.assign_pcg_graph(component, graph)
    gb.configure_pcg_component(component, seed=31337, activated=True)
    generated = False
    try:
        vh.generate_and_wait(component, force=True)
        generated = True
    except Exception as exc:
        unreal.log_warning(f"[MelodiaPCG] Generation deferred: {exc}")
    levels.save_current_level()
    result = {"level": LEVEL, "graph": GRAPH_PATH, "volume": VOLUME_LABEL, "generated": generated, "meta": meta}
    REPORT.parent.mkdir(parents=True, exist_ok=True)
    REPORT.write_text(json.dumps(result, indent=2), encoding="utf-8")
    unreal.log(f"[MelodiaPCG] Dreamstate dressing graph -> {REPORT}")


if __name__ == "__main__":
    main()
