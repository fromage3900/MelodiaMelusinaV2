"""Build a restrained PCG memory-dressing layer for Melusina's bedroom."""
from __future__ import annotations

import json
from pathlib import Path

import unreal

import pcg_graph_builder as gb
import pcg_validate_helpers as vh


LEVEL = "/Game/Melodia/Levels/Opening/L_MelusinaMorning"
GRAPH_PATH = "/Game/Melodia/PCG/PCG_Morning_MemoryDressing"
GRAPH_DIR = "/Game/Melodia/PCG"
VOLUME_LABEL = "PCG_MelodiaOpening_Morning_Dressing"
REPORT = Path(unreal.Paths.project_dir()) / "Saved" / "Melodia" / "morning_pcg_setup.json"


def main():
    levels = unreal.get_editor_subsystem(unreal.LevelEditorSubsystem)
    actors = unreal.get_editor_subsystem(unreal.EditorActorSubsystem)
    if not levels.load_level(LEVEL):
        raise RuntimeError(f"Could not load {LEVEL}")
    by_label = {actor.get_actor_label(): actor for actor in actors.get_all_level_actors()}
    volume = by_label.get(VOLUME_LABEL)
    if not volume:
        raise RuntimeError(f"Missing reserved PCG volume: {VOLUME_LABEL}")

    graph, _ = gb.load_or_create_graph(GRAPH_PATH, GRAPH_DIR, force=True)
    gb.clear_graph_nodes(graph)
    # Keep this against a room corner: the procedural set dressing reads as
    # accumulated memories, never as an obstacle in Melusina's wake path.
    volume.set_actor_location(unreal.Vector(430.0, -360.0, 120.0), False, False)
    volume.set_actor_scale3d(unreal.Vector(1.35, 1.35, 0.75))
    sampler, sampler_settings = gb.add_node(graph, "PCGVolumeSamplerSettings", -600, 0)
    sampler_settings.set_editor_property("voxel_size", unreal.Vector(180.0, 180.0, 180.0))
    sampler_settings.set_editor_property("unbounded", False)
    transform, transform_settings = gb.add_node(graph, "PCGTransformPointsSettings", -200, 0)
    gb.apply_transform(transform_settings, scale_min=0.06, scale_max=0.16, jitter=30.0)
    spawner, spawner_settings = gb.add_node(graph, "PCGStaticMeshSpawnerSettings", 150, 0)
    if not gb.configure_spawner(spawner_settings, "decor", None):
        raise RuntimeError("Could not configure Morning memory-dressing spawner")
    graph.add_edge(graph.get_input_node(), "In", sampler, "Volume")
    graph.add_edge(sampler, "Out", transform, "In")
    graph.add_edge(transform, "Out", spawner, "In")
    graph.add_edge(spawner, "Out", graph.get_output_node(), "Out")
    graph.set_editor_property("is_standalone_graph", True)
    unreal.EditorAssetLibrary.save_asset(GRAPH_PATH, only_if_is_dirty=False)

    component = volume.get_component_by_class(unreal.PCGComponent)
    if not component:
        raise RuntimeError("Bedroom PCG volume has no PCG component")
    gb.assign_pcg_graph(component, graph)
    gb.configure_pcg_component(component, seed=58120, activated=True)
    generated = False
    try:
        vh.generate_and_wait(component, force=True)
        generated = True
    except Exception as exc:
        unreal.log_warning(f"[MelodiaPCG] Bedroom generation deferred: {exc}")
    levels.save_current_level()
    result = {
        "level": LEVEL,
        "graph": GRAPH_PATH,
        "volume": VOLUME_LABEL,
        "generated": generated,
        "meta": {"role": "decor", "theme": "memory_dressing", "off_wake_path": True},
    }
    REPORT.parent.mkdir(parents=True, exist_ok=True)
    REPORT.write_text(json.dumps(result, indent=2), encoding="utf-8")
    unreal.log(f"[MelodiaPCG] Bedroom dressing graph -> {REPORT}")


if __name__ == "__main__":
    main()
