"""Assemble the protected, additive Arpeggio Bridge proof level."""
from __future__ import annotations

import json

import pcg_hero_proof_level as proof


LEVEL_DIR = "/Game/EnvSandbox/PCG/Musical/Hero"
LEVEL_PATH = f"{LEVEL_DIR}/L_PCG_Hero_ArpeggioBridge"
GRAPH_PATH = f"{LEVEL_DIR}/PCG_Hero_ArpeggioBridge"
PROFILE_PATH = f"{LEVEL_DIR}/DA_Hero_ArpeggioBridgeProfile"
UDS_BLUEPRINT_CLASS_PATH = "/Game/UltraDynamicSky/Blueprints/Ultra_Dynamic_Sky.Ultra_Dynamic_Sky_C"


CONTROL_PRESET = {
    "Depth": 1800.0,
    "Density": 0.40,
    "WalkWidth": 220.0,
    "ArrayCount": 24,
    "ArraySpacing": 180.0,
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
    import build_pcg_hero_arpeggio_bridge as builder
    importlib.reload(proof_module)
    proof = proof_module
    importlib.reload(control)
    importlib.reload(common)
    importlib.reload(builder)

    levels = proof.load_or_create_level(unreal, LEVEL_DIR, LEVEL_PATH)
    actors = unreal.get_editor_subsystem(unreal.EditorActorSubsystem)
    existing = {actor.get_actor_label(): actor for actor in (actors.get_all_level_actors() or [])}
    proof.ensure_control_driver(unreal, actors, existing, CONTROL_PRESET)
    builder.build_arpeggio_bridge_graph()
    graph = unreal.EditorAssetLibrary.load_asset(GRAPH_PATH)
    profile = unreal.EditorAssetLibrary.load_asset(PROFILE_PATH)
    if not graph or not profile:
        raise RuntimeError("bridge graph/profile did not load after build")

    host_class = proof.resolve_class(unreal, "PCGArpeggioBridgeHost")
    if host_class is None:
        raise RuntimeError("PCGArpeggioBridgeHost is unavailable; compile/reload C++ first")
    host = proof.spawn_or_reuse(unreal, actors, existing, host_class, "PCG Hero Arpeggio Bridge", (0.0, 0.0, 0.0))
    proof.set_tag(host, "PCG_HeroMusicHost")
    proof.set_tag(host, "PCG_ArpeggioBridge")
    proof.set_if_present(host, "profile", profile)
    proof.set_if_present(host, "music_graph", graph)
    proof.set_if_present(host, "note_count", 24)
    proof.assign_and_generate(unreal, host, graph)
    # Direct measured classic library branches own the bridge composition;
    # retire any previous authored PCGEx volume from this proof level.
    proof.hide_pcg_architecture_volumes(unreal, existing)

    gate_x = (24 - 1) * 180.0 * 0.5
    gate = proof.spawn_or_reuse(unreal, actors, existing, unreal.StaticMeshActor, "Arpeggio Bridge Far Gate", (gate_x, 77.0, 1840.0), (0.0, 90.0, 0.0))
    gate.static_mesh_component.set_editor_property("static_mesh", unreal.EditorAssetLibrary.load_asset("/Game/EnvSandbox/Greybox_Kit/SM_arch_06"))
    gate.set_actor_scale3d(unreal.Vector(0.28, 0.28, 0.45))
    proof.set_tag(gate, "PCG_ArpeggioFarGate")
    try:
        gate.set_actor_hidden_in_game(True)
    except Exception:
        pass
    proof.set_if_present(host, "completion_gate", gate)

    proof.spawn_or_reuse(unreal, actors, existing, unreal.PlayerStart, "Arpeggio Bridge Player Start", (-2070.0, -80.0, 120.0), (0.0, 0.0, 0.0))
    proof.add_lighting_and_camera(
        unreal,
        actors,
        existing,
        "Arpeggio Bridge",
        (-2850.0, -1050.0, 1500.0),
        (-18.0, 24.0, 0.0),
        (48.0, 14.0, 0.12),
        (0.0, 0.0, -340.0),
    )
    # The bridge is a compact proof scene; keep the same canonical material
    # response but lower the local proof exposure so the stone and ivory read
    # as surfaces instead of clipping to white.
    sun = existing.get("Arpeggio Bridge Key Light")
    if sun:
        proof.set_if_present(sun.get_component_by_class(unreal.DirectionalLightComponent), "intensity", 1.20)
    fill = existing.get("Arpeggio Bridge Warm Fill")
    if fill:
        fill_component = fill.get_component_by_class(unreal.PointLightComponent)
        proof.set_if_present(fill_component, "intensity", 500.0)
        proof.set_if_present(fill_component, "attenuation_radius", 5000.0)
    sky = proof.spawn_or_reuse(unreal, actors, existing, unreal.SkyLight, "Arpeggio Bridge Sky Fill", (0.0, 0.0, 2200.0))
    sky_component = sky.get_component_by_class(unreal.SkyLightComponent)
    proof.set_if_present(sky_component, "intensity", 0.50)
    proof.set_if_present(sky_component, "light_color", unreal.Color(170, 190, 220, 255))

    # Give the floating traversal a readable horizon and atmospheric depth in
    # the proof capture. This is level-local; it does not touch production sky
    # settings or the water material family.
    uds_class = unreal.load_class(None, UDS_BLUEPRINT_CLASS_PATH)
    if uds_class is not None:
        uds = proof.spawn_or_reuse(unreal, actors, existing, uds_class, "ArpeggioBridge UDS", (0.0, 0.0, 0.0))
        proof.set_tag(uds, "PCG_ArpeggioBridge_UDS")
        try:
            uds.set_actor_hidden_in_game(False)
        except Exception:
            pass
    levels.save_current_level()
    result = {
        "level": LEVEL_PATH,
        "graph": GRAPH_PATH,
        "profile": PROFILE_PATH,
        "expected_nodes": 24,
        "driver": "BP_MelodiaPCGControl tagged PCG_Control",
        "render_preset": {"CullDistance": 0.0, "WriteCustomDepth": True, "StencilValue": 3},
        "interaction": "near-beat ordered stepping advances the bridge; misses reset streak but leave traversal intact",
        "completion": "far gate reveal plus canonical material-bus pulse",
        "sky": {
            "blueprint_class": UDS_BLUEPRINT_CLASS_PATH,
            "actor_label": "ArpeggioBridge UDS",
            "tag": "PCG_ArpeggioBridge_UDS",
        },
    }
    unreal.log(f"[PCG Hero Arpeggio Bridge] level ready {json.dumps(result)}")
    return result


if __name__ == "__main__":
    print(build_level())
