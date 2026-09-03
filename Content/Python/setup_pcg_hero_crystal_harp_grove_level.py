"""Assemble the additive Crystal Harp Grove proof level."""
from __future__ import annotations

import json

import pcg_hero_proof_level as proof


LEVEL_DIR = "/Game/EnvSandbox/PCG/Musical/Hero"
LEVEL_PATH = f"{LEVEL_DIR}/L_PCG_Hero_CrystalHarpGrove"
GRAPH_PATH = f"{LEVEL_DIR}/PCG_Hero_CrystalHarpGrove"
PROFILE_PATH = f"{LEVEL_DIR}/DA_Hero_CrystalHarpGroveProfile"
UDS_BLUEPRINT_CLASS_PATH = "/Game/UltraDynamicSky/Blueprints/Ultra_Dynamic_Sky.Ultra_Dynamic_Sky_C"


CONTROL_PRESET = {
    "Depth": 760.0,
    "Density": 0.55,
    "WalkWidth": 280.0,
    "ArrayCount": 20,
    "ArraySpacing": 520.0,
    "ResampleSpacing": 100.0,
    "ScaleMin": 0.88,
    "ScaleMax": 1.22,
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
    import build_pcg_hero_crystal_harp_grove as builder

    importlib.reload(proof_module)
    proof = proof_module
    importlib.reload(control)
    importlib.reload(common)
    importlib.reload(builder)

    levels = proof.load_or_create_level(unreal, LEVEL_DIR, LEVEL_PATH)
    actors = unreal.get_editor_subsystem(unreal.EditorActorSubsystem)
    existing = {actor.get_actor_label(): actor for actor in (actors.get_all_level_actors() or [])}
    proof.ensure_control_driver(unreal, actors, existing, CONTROL_PRESET)
    builder.build_crystal_harp_grove_graph()
    graph = unreal.EditorAssetLibrary.load_asset(GRAPH_PATH)
    profile = unreal.EditorAssetLibrary.load_asset(PROFILE_PATH)
    if not graph or not profile:
        raise RuntimeError("Crystal Harp Grove graph/profile did not load after build")

    host_class = proof.resolve_class(unreal, "APCGHeroMusicGraphHost")
    if host_class is None:
        raise RuntimeError("APCGHeroMusicGraphHost is unavailable; compile/reload C++ first")
    host = proof.spawn_or_reuse(unreal, actors, existing, host_class, "PCG Hero Crystal Harp Grove", (0.0, 0.0, 0.0))
    proof.set_tag(host, "PCG_HeroMusicHost")
    proof.set_tag(host, "PCG_CrystalHarpGrove")
    proof.set_if_present(host, "profile", profile)
    proof.set_if_present(host, "music_graph", graph)
    proof.set_if_present(host, "note_count", 20)
    proof.assign_and_generate(unreal, host, graph)
    proof.hide_pcg_architecture_volumes(unreal, existing)

    proof.spawn_or_reuse(unreal, actors, existing, unreal.PlayerStart, "Crystal Harp Grove Player Start", (-5100.0, -280.0, 170.0), (0.0, 18.0, 0.0))
    proof.add_lighting_and_camera(
        unreal,
        actors,
        existing,
        "Crystal Harp Grove",
        (-1850.0, -1700.0, 980.0),
        (-11.0, 34.0, 0.0),
        (18.0, 12.0, 0.10),
        (0.0, 0.0, -50.0),
    )

    uds_class = unreal.load_class(None, UDS_BLUEPRINT_CLASS_PATH)
    if uds_class is not None:
        uds = proof.spawn_or_reuse(unreal, actors, existing, uds_class, "Crystal Harp Grove UDS", (0.0, 0.0, 0.0))
        proof.set_tag(uds, "PCG_CrystalHarpGrove_UDS")
        try:
            uds.set_actor_hidden_in_game(False)
        except Exception:
            pass

    sun = existing.get("Crystal Harp Grove Key Light")
    if sun:
        component = sun.get_component_by_class(unreal.DirectionalLightComponent)
        proof.set_if_present(component, "intensity", 1.05)
        proof.set_if_present(component, "light_color", unreal.Color(188, 216, 255, 255))
    fill = existing.get("Crystal Harp Grove Warm Fill")
    if fill:
        component = fill.get_component_by_class(unreal.PointLightComponent)
        proof.set_if_present(component, "intensity", 520.0)
        proof.set_if_present(component, "attenuation_radius", 6000.0)
    sky = existing.get("Crystal Harp Grove Sky Fill")
    if sky:
        proof.set_if_present(sky.get_component_by_class(unreal.SkyLightComponent), "intensity", 0.48)

    levels.save_current_level()
    result = {
        "level": LEVEL_PATH,
        "graph": GRAPH_PATH,
        "profile": PROFILE_PATH,
        "expected_strings": 20,
        "stations": 5,
        "driver": "BP_MelodiaPCGControl tagged PCG_Control",
        "render_preset": {"CullDistance": 0.0, "WriteCustomDepth": True, "StencilValue": 3},
        "layout": "five four-string crystal harp gates on a rising S-curve with paired frame rails",
        "interaction": "player-pawn proximity trigger -> spring press/release -> note event/audio/rhythm response",
        "completion": "ordered grove cadence and canonical rhythm crescendo",
        "production_maps_touched": False,
        "sky": {"blueprint_class": UDS_BLUEPRINT_CLASS_PATH, "actor_label": "Crystal Harp Grove UDS", "tag": "PCG_CrystalHarpGrove_UDS"},
    }
    unreal.log(f"[PCG Hero Crystal Harp Grove] level ready {json.dumps(result)}")
    return result


if __name__ == "__main__":
    print(build_level())
