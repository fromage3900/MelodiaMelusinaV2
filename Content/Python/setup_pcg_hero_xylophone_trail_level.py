"""Assemble the additive, non-production Xylophone Trail proof level.

This is deliberately a small instrument path: real beveled bars own the
walkable surface, classic authored floor/rail pieces own the support grammar,
and the graph's measured PCGEx guide rail explains the route at a glance.
"""
from __future__ import annotations

import json

import pcg_hero_proof_level as proof


LEVEL_DIR = "/Game/EnvSandbox/PCG/Musical/Hero"
LEVEL_PATH = f"{LEVEL_DIR}/L_PCG_Hero_XylophoneTrail"
GRAPH_PATH = f"{LEVEL_DIR}/PCG_Hero_XylophoneTrail"
PROFILE_PATH = f"{LEVEL_DIR}/DA_Hero_XylophoneTrailProfile"
UDS_BLUEPRINT_CLASS_PATH = "/Game/UltraDynamicSky/Blueprints/Ultra_Dynamic_Sky.Ultra_Dynamic_Sky_C"


CONTROL_PRESET = {
    "Depth": 1800.0,
    "Density": 0.40,
    "WalkWidth": 220.0,
    # The graph expands one control section into six pentatonic bars.
    "ArrayCount": 4,
    "ArraySpacing": 480.0,
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
    import build_pcg_hero_xylophone_trail as builder

    importlib.reload(proof_module)
    proof = proof_module
    importlib.reload(control)
    importlib.reload(common)
    importlib.reload(builder)

    levels = proof.load_or_create_level(unreal, LEVEL_DIR, LEVEL_PATH)
    actors = unreal.get_editor_subsystem(unreal.EditorActorSubsystem)
    existing = {actor.get_actor_label(): actor for actor in (actors.get_all_level_actors() or [])}
    proof.ensure_control_driver(unreal, actors, existing, CONTROL_PRESET)
    builder.build_xylophone_trail_graph()
    graph = unreal.EditorAssetLibrary.load_asset(GRAPH_PATH)
    profile = unreal.EditorAssetLibrary.load_asset(PROFILE_PATH)
    if not graph or not profile:
        raise RuntimeError("Xylophone Trail graph/profile did not load after build")

    host_class = proof.resolve_class(unreal, "APCGHeroMusicGraphHost")
    if host_class is None:
        raise RuntimeError("APCGHeroMusicGraphHost is unavailable; compile/reload C++ first")
    host = proof.spawn_or_reuse(unreal, actors, existing, host_class, "PCG Hero Xylophone Trail", (0.0, 0.0, 0.0))
    proof.set_tag(host, "PCG_HeroMusicHost")
    proof.set_tag(host, "PCG_XylophoneTrail")
    proof.set_if_present(host, "profile", profile)
    proof.set_if_present(host, "music_graph", graph)
    proof.set_if_present(host, "note_count", 24)
    proof.assign_and_generate(unreal, host, graph)
    proof.hide_pcg_architecture_volumes(unreal, existing)

    # The camera is aligned to the S-curve so the route reads as a sequence
    # of landings rather than a row of disconnected props.
    proof.spawn_or_reuse(
        unreal,
        actors,
        existing,
        unreal.PlayerStart,
        "Xylophone Trail Player Start",
        (-6100.0, -240.0, 170.0),
        (0.0, 0.0, 0.0),
    )
    proof.add_lighting_and_camera(
        unreal,
        actors,
        existing,
        "Xylophone Trail",
        (-6100.0, -2100.0, 1450.0),
        (-10.0, 30.0, 0.0),
        (56.0, 24.0, 0.10),
        (0.0, 0.0, -50.0),
    )

    sun = existing.get("Xylophone Trail Key Light")
    if sun:
        component = sun.get_component_by_class(unreal.DirectionalLightComponent)
        proof.set_if_present(component, "intensity", 1.10)
        proof.set_if_present(component, "light_color", unreal.Color(205, 224, 255, 255))
    fill = existing.get("Xylophone Trail Warm Fill")
    if fill:
        component = fill.get_component_by_class(unreal.PointLightComponent)
        proof.set_if_present(component, "intensity", 620.0)
        proof.set_if_present(component, "attenuation_radius", 6500.0)
    sky = existing.get("Xylophone Trail Sky Fill")
    if sky:
        proof.set_if_present(sky.get_component_by_class(unreal.SkyLightComponent), "intensity", 0.48)

    # Give the trail the same authored atmospheric context as the other
    # proof scenes. This is level-local and additive; it does not alter any
    # production sky or material asset.
    uds_class = unreal.load_class(None, UDS_BLUEPRINT_CLASS_PATH)
    if uds_class is not None:
        uds = proof.spawn_or_reuse(
            unreal,
            actors,
            existing,
            uds_class,
            "Xylophone Trail UDS",
            (0.0, 0.0, 0.0),
        )
        proof.set_tag(uds, "PCG_XylophoneTrail_UDS")
        try:
            uds.set_actor_hidden_in_game(False)
        except Exception:
            pass

    levels.save_current_level()
    result = {
        "level": LEVEL_PATH,
        "graph": GRAPH_PATH,
        "profile": PROFILE_PATH,
        "expected_bars": 24,
        "driver": "BP_MelodiaPCGControl tagged PCG_Control",
        "render_preset": {"CullDistance": 0.0, "WriteCustomDepth": True, "StencilValue": 3},
        "layout": "24 crosswise beveled bars on an ascending S-curve with readable floor landings and low rails",
        "interaction": "existing APCGHeroMusicNode player overlap -> spring press/release",
        "music_framework_changes": [],
        "production_maps_touched": False,
        "sky": {
            "blueprint_class": UDS_BLUEPRINT_CLASS_PATH,
            "actor_label": "Xylophone Trail UDS",
            "tag": "PCG_XylophoneTrail_UDS",
        },
    }
    unreal.log(f"[PCG Hero Xylophone Trail] level ready {json.dumps(result)}")
    return result


if __name__ == "__main__":
    print(build_level())
