"""Author the isolated Crystal Harp / water gameplay proof map in the editor.

This script is intentionally opt-in and refuses production map paths. It uses
the existing Crystal Harp graph, native Water classes when reflected, and the
new project-owned platform/anchor/controller classes. Final Water Body/Zone
property wiring remains an editor verification gate because those properties
are engine-version/plugin configuration rather than stable Python schema.
"""
from __future__ import annotations

from typing import Any


PROOF_MAP_PATH = "/Game/EnvSandbox/PCG/Musical/Hero/L_PCG_Hero_WaterGameplayProof"
CRYSTAL_HARP_GRAPH_PATH = "/Game/EnvSandbox/PCG/Musical/Hero/PCG_Hero_CrystalHarpGrove"
CRYSTAL_HARP_PROFILE_PATH = "/Game/EnvSandbox/PCG/Musical/Hero/DA_Hero_CrystalHarpGroveProfile"
PROOF_MARKER = "PCG_WATER_GAMEPLAY_PROOF"


def _load_class(unreal: Any, script_path: str) -> Any:
    cls = unreal.load_class(None, script_path)
    if not cls:
        raise RuntimeError(f"required reflected class is unavailable: {script_path}")
    return cls


def _spawn(unreal: Any, actor_class: Any, location, label: str) -> Any:
    actor = unreal.EditorLevelLibrary.spawn_actor_from_class(
        actor_class,
        unreal.Vector(float(location[0]), float(location[1]), float(location[2])),
    )
    if not actor:
        raise RuntimeError(f"could not spawn proof actor: {label}")
    actor.set_actor_label(label)
    actor.tags = list(set(actor.tags + [PROOF_MARKER]))
    return actor


def _set(actor: Any, prop: str, value: Any) -> bool:
    try:
        actor.set_editor_property(prop, value)
        return True
    except Exception:
        return False


def build_proof_map(unreal: Any, map_path: str = PROOF_MAP_PATH) -> dict[str, Any]:
    if not map_path.startswith("/Game/EnvSandbox/PCG/Musical/Hero/L_PCG_Hero_WaterGameplayProof"):
        raise RuntimeError("proof authoring is restricted to the isolated water proof map")
    if not unreal.EditorAssetLibrary.does_asset_exist(CRYSTAL_HARP_GRAPH_PATH):
        raise RuntimeError(f"existing Crystal Harp graph is missing: {CRYSTAL_HARP_GRAPH_PATH}")

    if not unreal.EditorAssetLibrary.does_asset_exist(map_path):
        if not unreal.EditorLevelLibrary.new_level(map_path):
            raise RuntimeError(f"could not create proof map: {map_path}")
    else:
        unreal.EditorLevelLibrary.load_level(map_path)

    # The proof is a generated, isolated lane. A failed or repeated authoring
    # pass must replace only its own tagged actors instead of accumulating
    # duplicate hosts, Water Bodies, or gameplay devices.
    existing_proof_actors = [
        actor
        for actor in unreal.EditorLevelLibrary.get_all_level_actors()
        if PROOF_MARKER in [str(tag) for tag in actor.tags]
    ]
    for actor in existing_proof_actors:
        unreal.EditorLevelLibrary.destroy_actor(actor)

    platform_class = _load_class(unreal, "/Script/BS_GodFile.MelodiaWaterPlatform")
    anchor_class = _load_class(unreal, "/Script/BS_GodFile.MelodiaWaterGameplayDeviceAnchor")
    host_class = _load_class(unreal, "/Script/BS_GodFile.PCGHeroMusicGraphHost")
    water_body_class = _load_class(unreal, "/Script/Water.WaterBodyLake")
    water_zone_class = _load_class(unreal, "/Script/Water.WaterZone")

    spawned: list[str] = []
    host = _spawn(unreal, host_class, (0.0, 0.0, 100.0), "PCG Water Proof - Crystal Harp Host")
    _set(host, "music_graph", unreal.EditorAssetLibrary.load_asset(CRYSTAL_HARP_GRAPH_PATH))
    _set(host, "profile", unreal.EditorAssetLibrary.load_asset(CRYSTAL_HARP_PROFILE_PATH))
    spawned.append(host.get_path_name())

    water_body = _spawn(unreal, water_body_class, (0.0, 0.0, 0.0), "PCG Water Proof - Native Water Body")
    water_zone = _spawn(unreal, water_zone_class, (0.0, 0.0, 0.0), "PCG Water Proof - Water Zone")
    spawned.extend([water_body.get_path_name(), water_zone.get_path_name()])

    anchor_specs = (
        ("reservoir", (800.0, 0.0, 40.0), "Reservoir"),
        ("valve", (1100.0, 0.0, 40.0), "Valve"),
        ("resonance_bridge", (1400.0, 0.0, 40.0), "Resonance Bridge"),
        ("water_gate", (1900.0, 0.0, 40.0), "Water Gate"),
        ("current_volume", (1600.0, 320.0, 40.0), "Current Volume Anchor"),
    )
    for role, location, label in anchor_specs:
        anchor = _spawn(unreal, anchor_class, location, f"PCG Water Proof - {label}")
        _set(anchor, "gameplay_role", role)
        _set(anchor, "water_network_id", "WaterNetwork_CrystalHarpGrove")
        _set(anchor, "water_node_id", "HarpResonance")
        _set(anchor, "route_id", "Route_HarpCrossing")
        spawned.append(anchor.get_path_name())

    moving = _spawn(unreal, platform_class, (2400.0, 0.0, 160.0), "PCG Water Proof - Kinematic Moving Platform")
    _set(moving, "platform_id", "Proof_KinematicPlatform")
    _set(moving, "water_network_id", "WaterNetwork_CrystalHarpGrove")
    _set(moving, "motion_mode", unreal.MelodiaWaterPlatformMotionMode.KINEMATIC_ROUTE)
    spawned.append(moving.get_path_name())

    buoyant = _spawn(unreal, platform_class, (2400.0, 320.0, 160.0), "PCG Water Proof - Physics Buoyant Platform")
    _set(buoyant, "platform_id", "Proof_BuoyantPlatform")
    _set(buoyant, "water_network_id", "WaterNetwork_CrystalHarpGrove")
    _set(buoyant, "motion_mode", unreal.MelodiaWaterPlatformMotionMode.PHYSICS_BUOYANT)
    spawned.append(buoyant.get_path_name())

    unreal.EditorLevelLibrary.save_current_level()
    return {
        "map": map_path,
        "marker": PROOF_MARKER,
        "crystal_harp_graph": CRYSTAL_HARP_GRAPH_PATH,
        "native_water_body": water_body.get_path_name(),
        "water_zone": water_zone.get_path_name(),
        "spawned_actor_count": len(spawned),
        "spawned_actors": spawned,
        "editor_verification_gates": [
            "assign Water Body to Water Zone and verify native query readback",
            "inject bridge/controller T3D clusters on the live host path",
            "record one PIE interaction through the full proof sequence",
        ],
    }


if __name__ == "__main__":
    print("Run build_proof_map(unreal) from the Unreal Python console.")
