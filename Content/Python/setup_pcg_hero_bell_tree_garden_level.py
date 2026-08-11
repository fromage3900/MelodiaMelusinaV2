"""Assemble the additive, non-production BellTreeGarden proof level."""
from __future__ import annotations

import json

import pcg_hero_proof_level as proof


LEVEL_DIR = "/Game/EnvSandbox/PCG/Musical/Hero"
LEVEL_PATH = f"{LEVEL_DIR}/L_PCG_Hero_BellTreeGarden"
GRAPH_PATH = f"{LEVEL_DIR}/PCG_Hero_BellTreeGarden"
PROFILE_PATH = f"{LEVEL_DIR}/DA_Hero_BellTreeGardenProfile"
UDS_BLUEPRINT_CLASS_PATH = "/Game/UltraDynamicSky/Blueprints/Ultra_Dynamic_Sky.Ultra_Dynamic_Sky_C"


CONTROL_PRESET = {
    "Depth": 900.0,
    "Density": 0.45,
    "WalkWidth": 300.0,
    "ArrayCount": 18,
    "ArraySpacing": 260.0,
    "ResampleSpacing": 120.0,
    "ScaleMin": 0.85,
    "ScaleMax": 1.20,
    "CullDistance": 0.0,
    "StencilValue": 3,
    "WriteCustomDepth": True,
}


def build_level() -> dict:
    import importlib
    import unreal
    import pcg_hero_proof_level as proof_module
    import pcg_hero_music_control as control
    import pcg_hero_music_common as common
    import build_pcg_hero_bell_tree_garden as builder

    importlib.reload(proof_module)
    proof = proof_module
    importlib.reload(control)
    importlib.reload(common)
    importlib.reload(builder)

    levels = proof.load_or_create_level(unreal, LEVEL_DIR, LEVEL_PATH)
    actors = unreal.get_editor_subsystem(unreal.EditorActorSubsystem)
    existing = {actor.get_actor_label(): actor for actor in (actors.get_all_level_actors() or [])}
    proof.ensure_control_driver(unreal, actors, existing, CONTROL_PRESET)
    builder.build_bell_tree_garden_graph()
    graph = unreal.EditorAssetLibrary.load_asset(GRAPH_PATH)
    profile = unreal.EditorAssetLibrary.load_asset(PROFILE_PATH)
    if not graph or not profile:
        raise RuntimeError("BellTreeGarden graph/profile did not load after build")

    host_class = proof.resolve_class(unreal, "APCGBellTreeGardenHost")
    if host_class is None:
        raise RuntimeError("APCGBellTreeGardenHost is unavailable; compile/reload C++ first")
    host = proof.spawn_or_reuse(unreal, actors, existing, host_class, "PCG Hero Bell Tree Garden", (0.0, 0.0, 0.0))
    proof.set_tag(host, "PCG_HeroMusicHost")
    proof.set_tag(host, "PCG_BellTreeGarden")
    proof.set_if_present(host, "profile", profile)
    proof.set_if_present(host, "music_graph", graph)
    proof.set_if_present(host, "bell_count", 18)
    proof.set_if_present(host, "branch_count", 3)
    proof.assign_and_generate(unreal, host, graph)
    proof.hide_pcg_architecture_volumes(unreal, existing)

    proof.spawn_or_reuse(
        unreal,
        actors,
        existing,
        unreal.PlayerStart,
        "BellTreeGarden Player Start",
        (-1700.0, -520.0, 150.0),
        (0.0, 18.0, 0.0),
    )
    proof.add_lighting_and_camera(
        unreal,
        actors,
        existing,
        "BellTreeGarden",
        (-2500.0, -2200.0, 1500.0),
        (-12.0, 35.0, 0.0),
        (36.0, 18.0, 0.10),
        (0.0, 0.0, -40.0),
    )

    # Place the authored Ultra Dynamic Sky blueprint in this proof level so
    # the rising garden can be judged against the project's actual sky and
    # atmospheric response. It remains level-local and additive.
    uds_class = unreal.load_class(None, UDS_BLUEPRINT_CLASS_PATH)
    if uds_class is None:
        raise RuntimeError(f"UDS blueprint is unavailable: {UDS_BLUEPRINT_CLASS_PATH}")
    uds = proof.spawn_or_reuse(
        unreal,
        actors,
        existing,
        uds_class,
        "BellTreeGarden UDS",
        (0.0, 0.0, 0.0),
    )
    proof.set_tag(uds, "PCG_BellTreeGarden_UDS")
    try:
        uds.set_actor_hidden_in_game(False)
    except Exception:
        pass

    sun = existing.get("BellTreeGarden Key Light")
    if sun:
        proof.set_if_present(sun.get_component_by_class(unreal.DirectionalLightComponent), "intensity", 1.05)
    fill = existing.get("BellTreeGarden Warm Fill")
    if fill:
        fill_component = fill.get_component_by_class(unreal.PointLightComponent)
        proof.set_if_present(fill_component, "intensity", 450.0)
        proof.set_if_present(fill_component, "attenuation_radius", 5000.0)
    sky = existing.get("BellTreeGarden Sky Fill")
    if sky:
        proof.set_if_present(sky.get_component_by_class(unreal.SkyLightComponent), "intensity", 0.45)

    levels.save_current_level()
    result = {
        "level": LEVEL_PATH,
        "graph": GRAPH_PATH,
        "profile": PROFILE_PATH,
        "expected_bells": 18,
        "branches": 3,
        "driver": "BP_MelodiaPCGControl tagged PCG_Control",
        "render_preset": {"CullDistance": 0.0, "WriteCustomDepth": True, "StencilValue": 3},
        "interaction": "ordered tuned-bell stepping; wrong notes reset streak but leave the garden traversable",
        "completion": "local garden completion and canonical rhythm crescendo",
        "production_maps_touched": False,
        "sky": {
            "blueprint_class": UDS_BLUEPRINT_CLASS_PATH,
            "actor_label": "BellTreeGarden UDS",
            "tag": "PCG_BellTreeGarden_UDS",
        },
    }
    unreal.log(f"[PCG Hero BellTreeGarden] level ready {json.dumps(result)}")
    return result


if __name__ == "__main__":
    print(build_level())
