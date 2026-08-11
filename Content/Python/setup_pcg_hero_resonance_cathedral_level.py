"""Assemble the protected, additive Resonance Cathedral proof level."""
from __future__ import annotations

import json

import pcg_hero_proof_level as proof


LEVEL_DIR = "/Game/EnvSandbox/PCG/Musical/Hero"
LEVEL_PATH = f"{LEVEL_DIR}/L_PCG_Hero_ResonanceCathedral"
GRAPH_PATH = f"{LEVEL_DIR}/PCG_Hero_ResonanceCathedral"
PROFILE_PATH = f"{LEVEL_DIR}/DA_Hero_ResonanceCathedralProfile"


CONTROL_PRESET = {
    "Depth": 1800.0,
    "Density": 0.40,
    "WalkWidth": 220.0,
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
    import unreal
    import importlib
    import pcg_hero_proof_level as proof_module
    import pcg_hero_music_control as control
    import pcg_hero_music_common as common
    import build_pcg_hero_resonance_cathedral as builder
    importlib.reload(proof_module)
    proof = proof_module
    importlib.reload(control)
    importlib.reload(common)
    importlib.reload(builder)

    levels = proof.load_or_create_level(unreal, LEVEL_DIR, LEVEL_PATH)
    actors = unreal.get_editor_subsystem(unreal.EditorActorSubsystem)
    existing = {actor.get_actor_label(): actor for actor in (actors.get_all_level_actors() or [])}
    proof.ensure_control_driver(unreal, actors, existing, CONTROL_PRESET)
    # Build after the tagged driver is in the current proof level. This is the
    # same On-Demand snapshot path used when any of the eleven knobs changes.
    builder.build_resonance_cathedral_graph()
    graph = unreal.EditorAssetLibrary.load_asset(GRAPH_PATH)
    profile = unreal.EditorAssetLibrary.load_asset(PROFILE_PATH)
    if not graph or not profile:
        raise RuntimeError("cathedral graph/profile did not load after build")

    host_class = proof.resolve_class(unreal, "PCGResonanceCathedralHost")
    if host_class is None:
        raise RuntimeError("PCGResonanceCathedralHost is unavailable; compile/reload C++ first")
    host = proof.spawn_or_reuse(unreal, actors, existing, host_class, "PCG Hero Resonance Cathedral", (0.0, 0.0, 0.0))
    proof.set_tag(host, "PCG_HeroMusicHost")
    proof.set_tag(host, "PCG_ResonanceCathedral")
    proof.set_if_present(host, "profile", profile)
    proof.set_if_present(host, "music_graph", graph)
    proof.set_if_present(host, "station_count", 4)
    proof.assign_and_generate(unreal, host, graph)
    # The classic library pieces are now spawned as explicit graph branches
    # with measured transforms.  Retire the old authored-volume composition so
    # its inconsistent imported scale cannot compete with the playable row.
    proof.hide_pcg_architecture_volumes(unreal, existing)

    proof.spawn_or_reuse(unreal, actors, existing, unreal.PlayerStart, "Resonance Cathedral Player Start", (0.0, -1050.0, 120.0), (0.0, 90.0, 0.0))
    proof.add_lighting_and_camera(
        unreal,
        actors,
        existing,
        "Resonance Cathedral",
        (0.0, -2600.0, 700.0),
        (-5.0, 90.0, 0.0),
        (28.0, 34.0, 0.12),
        (0.0, 0.0, -24.0),
    )
    sun = existing.get("Resonance Cathedral Key Light")
    if sun:
        proof.set_if_present(sun.get_component_by_class(unreal.DirectionalLightComponent), "intensity", 1.10)
    fill = existing.get("Resonance Cathedral Warm Fill")
    if fill:
        fill_component = fill.get_component_by_class(unreal.PointLightComponent)
        proof.set_if_present(fill_component, "intensity", 650.0)
        proof.set_if_present(fill_component, "attenuation_radius", 5000.0)
    sky = existing.get("Resonance Cathedral Sky Fill")
    if sky:
        proof.set_if_present(sky.get_component_by_class(unreal.SkyLightComponent), "intensity", 0.50)
    levels.save_current_level()
    result = {
        "level": LEVEL_PATH,
        "graph": GRAPH_PATH,
        "profile": PROFILE_PATH,
        "expected_pads": 12,
        "stations": 4,
        "driver": "BP_MelodiaPCGControl tagged PCG_Control",
        "render_preset": {"CullDistance": 0.0, "WriteCustomDepth": True, "StencilValue": 3},
        "interaction": "three ordered chord-degree pads within two beats opens each station; completion is local presentation only",
    }
    unreal.log(f"[PCG Hero Resonance Cathedral] level ready {json.dumps(result)}")
    return result


if __name__ == "__main__":
    print(build_level())
