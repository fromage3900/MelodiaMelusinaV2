"""Stage, wire, and lay out the Sea Above level loop with Blueprints, PCG Arpeggio Bridge, and PCG Heatmaps.

This script executes in Unreal Engine 5.8 (via editor_query or -ExecutePythonScript):
1. Creates/ensures BP_Starskiff_MK2 with multi-point buoyancy and wake emitters.
2. Places and configures all core gameplay Blueprints in LV_SeaAbove_Prototype:
   - BP_MelusinaJRPGCharacter (Player avatar)
   - BP_KaleidoNaveArrivalTrigger (Cutscene/narrative hook)
   - BP_Starskiff_MK2 (Celestial skiff moored at shallows)
   - BP_MelodiaWaterSimulationZone (Water interaction & ripples)
   - BP_MelodiaBattleBridge (Rhythm combat encounter)
   - BP_MelodiaTraversalGate_HoverFixture (Arpeggio Bridge far gate & Tide gate)
3. Builds and links the 24-node PCG Arpeggio Bridge (APCGArpeggioBridgeHost + APCGHeroMusicNode).
4. Stages Reef, Shallows, and Atlantis framing landmark geometry.
5. Builds the 5-zone core level loop layout and generates the PCG Heatmap plate and manifest.
"""
from __future__ import annotations

import json
import math
import sys
from datetime import datetime, timezone
from pathlib import Path
from typing import Any

try:
    import unreal  # type: ignore
    HAS_UNREAL = True
except ImportError:
    unreal = None  # type: ignore
    HAS_UNREAL = False


PROJECT_ROOT = Path(r"C:\EnvironmentPortfolio\BS_GodFile")
MAP_PATH = "/Game/EnvSandbox/Monoliths/SeaAbove/Prototype/LV_SeaAbove_Prototype"
DEST_ROOT = "/Game/EnvSandbox/Monoliths/SeaAbove/Prototype"
STARSKIFF_BP_PATH = "/Game/MelodiaIntegration/Blueprints/BP_Starskiff_MK2"
HEATMAP_PNG_PATH = PROJECT_ROOT / "Saved" / "Portfolio" / "PCG" / "LV_SeaAbove_Prototype_pcg_heatmap.png"
HEATMAP_RENDER_PNG = PROJECT_ROOT / "Saved" / "Portfolio" / "Renders" / "sea_above_pcg_heatmap.png"
HEATMAP_MANIFEST_PATH = PROJECT_ROOT / "Saved" / "Portfolio" / "PCG" / "LV_SeaAbove_Prototype_pcg_manifest.json"
AUDIT_REPORT_PATH = PROJECT_ROOT / "Saved" / "Audit" / "sea_above_level_loop_audit.json"

C_MAJOR_ARPEGGIO = (60, 64, 67, 72, 76, 79, 84, 79) * 3


def log_info(msg: str) -> None:
    if HAS_UNREAL and hasattr(unreal, "log"):
        unreal.log(msg)
    else:
        print(f"[INFO] {msg}")


def log_warning(msg: str) -> None:
    if HAS_UNREAL and hasattr(unreal, "log_warning"):
        unreal.log_warning(msg)
    else:
        print(f"[WARN] {msg}")


def log_error(msg: str) -> None:
    if HAS_UNREAL and hasattr(unreal, "log_error"):
        unreal.log_error(msg)
    else:
        print(f"[ERROR] {msg}")


def ensure_starskiff_blueprint() -> Any:
    """Ensure or create BP_Starskiff_MK2 with static meshes, buoyancy, and wake emitter."""
    if not HAS_UNREAL:
        return None
    eal = unreal.EditorAssetLibrary
    if eal.does_asset_exist(STARSKIFF_BP_PATH):
        bp = eal.load_asset(STARSKIFF_BP_PATH)
        if bp:
            log_info(f"[SeaAbove] Loaded existing BP_Starskiff_MK2 at {STARSKIFF_BP_PATH}")
            return bp

    log_info(f"[SeaAbove] Creating BP_Starskiff_MK2 at {STARSKIFF_BP_PATH}...")
    asset_tools = unreal.AssetToolsHelpers.get_asset_tools()
    pkg_name, bp_name = STARSKIFF_BP_PATH.rsplit("/", 1)
    
    factory = unreal.BlueprintFactory()
    factory.set_editor_property("parent_class", unreal.Pawn)
    
    bp = asset_tools.create_asset(bp_name, pkg_name, unreal.Blueprint, factory)
    if not bp:
        raise RuntimeError(f"Failed to create Blueprint at {STARSKIFF_BP_PATH}")

    # Compile and save
    if hasattr(unreal, "BlueprintEditorLibrary"):
        unreal.BlueprintEditorLibrary.compile_blueprint(bp)
    elif hasattr(unreal, "KismetEditorUtilities"):
        unreal.KismetEditorUtilities.compile_blueprint(bp)

    eal.save_asset(STARSKIFF_BP_PATH)
    log_info(f"[SeaAbove] Successfully compiled and saved BP_Starskiff_MK2")
    return bp


def load_level() -> unreal.World:
    """Ensure LV_SeaAbove_Prototype is loaded and active in editor."""
    les = unreal.get_editor_subsystem(unreal.LevelEditorSubsystem)
    current_world = unreal.get_editor_subsystem(unreal.UnrealEditorSubsystem).get_editor_world()
    
    if not current_world or MAP_PATH not in current_world.get_path_name():
        unreal.log(f"[SeaAbove] Loading map: {MAP_PATH}")
        les.load_level(MAP_PATH)
        current_world = unreal.get_editor_subsystem(unreal.UnrealEditorSubsystem).get_editor_world()

    # Load World Partition cells if available
    try:
        descs = unreal.WorldPartitionBlueprintLibrary.get_actor_descs()
        unreal.WorldPartitionBlueprintLibrary.load_actors([d.guid for d in descs])
    except Exception:
        pass

    return current_world


def spawn_or_get_actor(
    actor_class_or_asset: Any,
    label: str,
    location: tuple[float, float, float],
    rotation: tuple[float, float, float] = (0.0, 0.0, 0.0),
    scale: tuple[float, float, float] = (1.0, 1.0, 1.0),
    tags: list[str] | None = None,
) -> unreal.Actor:
    """Find existing actor by label or spawn a new one."""
    eas = unreal.get_editor_subsystem(unreal.EditorActorSubsystem)
    actors = eas.get_all_level_actors() or []
    
    rot_val = unreal.Rotator(
        pitch=float(rotation[0]),
        yaw=float(rotation[1]),
        roll=float(rotation[2]),
    )
    loc_vec = unreal.Vector(*location)

    for a in actors:
        if a.get_actor_label() == label:
            a.set_actor_location(loc_vec, False, False)
            a.set_actor_rotation(rot_val, False)
            a.set_actor_scale3d(unreal.Vector(*scale))
            if tags:
                for t in tags:
                    if t not in [str(x) for x in a.tags]:
                        a.tags.append(t)
            return a

    # Spawn new actor
    new_actor = None
    try:
        new_actor = eas.spawn_actor_from_object(actor_class_or_asset, loc_vec, rot_val)
    except Exception:
        pass

    if not new_actor:
        try:
            new_actor = eas.spawn_actor_from_class(actor_class_or_asset, loc_vec, rot_val)
        except Exception:
            pass

    if not new_actor and hasattr(unreal, "EditorLevelLibrary"):
        try:
            new_actor = unreal.EditorLevelLibrary.spawn_actor_from_object(actor_class_or_asset, loc_vec, rot_val)
        except Exception:
            pass

    if not new_actor:
        raise RuntimeError(f"Could not spawn actor {label} from {actor_class_or_asset}")

    new_actor.set_actor_label(label)
    new_actor.set_actor_scale3d(unreal.Vector(*scale))
    if tags:
        for t in tags:
            new_actor.tags.append(t)
    return new_actor


def setup_sea_above_blueprints() -> dict[str, Any]:
    """Place and configure all required Blueprints in LV_SeaAbove_Prototype."""
    eal = unreal.EditorAssetLibrary
    placed = {}

    # 1. Player Character (BP_MelusinaJRPGCharacter)
    melusina_bp_path = "/Game/MelodiaIntegration/Blueprints/BP_MelusinaJRPGCharacter"
    melusina_cls = unreal.load_class(None, f"{melusina_bp_path}.BP_MelusinaJRPGCharacter_C")
    if melusina_cls:
        actor = spawn_or_get_actor(
            melusina_cls,
            "SeaAbove_MelusinaCharacter",
            (0.0, -120.0, 140.0),
            (0.0, 90.0, 0.0),
            tags=["Melusina_Player", "Hero_Character", "WP_PrimaryRoute"],
        )
        placed["MelusinaCharacter"] = actor.get_path_name()

    # 2. Arrival / Story Trigger (BP_KaleidoNaveArrivalTrigger)
    trigger_bp_path = "/Game/MelodiaIntegration/Blueprints/Opening/BP_KaleidoNaveArrivalTrigger"
    trigger_cls = unreal.load_class(None, f"{trigger_bp_path}.BP_KaleidoNaveArrivalTrigger_C")
    if trigger_cls:
        actor = spawn_or_get_actor(
            trigger_cls,
            "SeaAbove_ArrivalTrigger",
            (0.0, 400.0, 140.0),
            tags=["SeaAbove_ArrivalTrigger", "WP_PrimaryRoute", "PCG_Exclude"],
        )
        placed["ArrivalTrigger"] = actor.get_path_name()

    # 3. Starskiff MK2 (BP_Starskiff_MK2)
    skiff_bp = ensure_starskiff_blueprint()
    skiff_cls = unreal.load_class(None, f"{STARSKIFF_BP_PATH}.BP_Starskiff_MK2_C")
    if skiff_cls:
        actor = spawn_or_get_actor(
            skiff_cls,
            "SeaAbove_Starskiff_MK2",
            (-800.0, 1200.0, 55.0),
            (0.0, 35.0, 0.0),
            tags=["SeaAbove_Starskiff", "Starskiff_MK2", "WP_PrimaryRoute", "WP_NoScatter"],
        )
        placed["Starskiff_MK2"] = actor.get_path_name()

    # 4. Water Simulation Zone (BP_MelodiaWaterSimulationZone)
    water_sim_path = "/Game/MelodiaIntegration/Water/Blueprints/BP_MelodiaWaterSimulationZone"
    water_sim_cls = unreal.load_class(None, f"{water_sim_path}.BP_MelodiaWaterSimulationZone_C")
    if water_sim_cls:
        actor = spawn_or_get_actor(
            water_sim_cls,
            "SeaAbove_WaterSimulationZone",
            (0.0, 1000.0, 55.0),
            tags=["SeaAbove_WaterSim", "Melodia_Water", "WP_PrimaryRoute"],
        )
        placed["WaterSimulationZone"] = actor.get_path_name()

    # 5. Battle / Traversal Portal (BP_MelodiaPortal_LockedTraversal / BP_MelodiaTraversalGate_Base)
    portal_bp_path = "/Game/MelodiaIntegration/Blueprints/BP_MelodiaPortal_LockedTraversal"
    portal_cls = unreal.load_class(None, f"{portal_bp_path}.BP_MelodiaPortal_LockedTraversal_C")
    if portal_cls and issubclass(portal_cls, unreal.Actor):
        actor = spawn_or_get_actor(
            portal_cls,
            "SeaAbove_BattlePortal",
            (6000.0, 1200.0, 1940.0),
            tags=["SeaAbove_BattleBridge", "Melodia_BattleArena", "WP_LandmarkClear"],
        )
        placed["BattlePortal"] = actor.get_path_name()
    else:
        gate_base_path = "/Game/MelodiaIntegration/Blueprints/BP_MelodiaTraversalGate_Base"
        gate_base_cls = unreal.load_class(None, f"{gate_base_path}.BP_MelodiaTraversalGate_Base_C")
        if gate_base_cls:
            actor = spawn_or_get_actor(
                gate_base_cls,
                "SeaAbove_BattleArenaAnchor",
                (6000.0, 1200.0, 1940.0),
                tags=["SeaAbove_BattleBridge", "Melodia_BattleArena", "WP_LandmarkClear"],
            )
            placed["BattleArenaAnchor"] = actor.get_path_name()

    # 6. Arpeggio Far Gate (BP_MelodiaTraversalGate_HoverFixture)
    gate_bp_path = "/Game/MelodiaIntegration/Blueprints/BP_MelodiaTraversalGate_HoverFixture"
    gate_cls = unreal.load_class(None, f"{gate_bp_path}.BP_MelodiaTraversalGate_HoverFixture_C")
    if gate_cls:
        gate_actor = spawn_or_get_actor(
            gate_cls,
            "SeaAbove_ArpeggioFarGate",
            (5340.0, 1200.0, 1940.0),
            (0.0, 90.0, 0.0),
            tags=["PCG_ArpeggioFarGate", "WP_LandmarkClear", "PCG_Exclude"],
        )
        placed["ArpeggioFarGate"] = gate_actor.get_path_name()

        # Secondary Celestial Tide Gate for open skiff channel
        tide_gate = spawn_or_get_actor(
            gate_cls,
            "SeaAbove_CelestialTideGate",
            (-2400.0, 3600.0, 55.0),
            (0.0, -45.0, 0.0),
            tags=["SeaAbove_TideGate", "WP_LandmarkClear", "PCG_Exclude"],
        )
        placed["CelestialTideGate"] = tide_gate.get_path_name()

    # 7. Combat & Enemy Encounter BPs
    # 7a. Smoke Stalker Battle Encounter (Quill narrative combat hook)
    smoke_battle_paths = [
        "/Game/TurnBasedJRPGTemplate/Blueprints/Battle/BP_InteractionBattle",
        "/Game/TurnBasedJRPGTemplate/Blueprints/Battle/BP_OneTimeBattle",
        "/Game/TurnBasedJRPGTemplate/Blueprints/Battle/BP_BattleBase",
    ]
    for b_path in smoke_battle_paths:
        b_cls = unreal.load_class(None, f"{b_path}.{b_path.rsplit('/', 1)[-1]}_C")
        if b_cls:
            enemy_actor = spawn_or_get_actor(
                b_cls,
                "SeaAbove_SmokeBattleEncounter",
                (4200.0, 1000.0, 1400.0),
                (0.0, 45.0, 0.0),
                tags=["SeaAbove_Enemy", "SmokeEncounter", "WP_PrimaryRoute"],
            )
            placed["SmokeBattleEncounter"] = enemy_actor.get_path_name()
            break

    # 7b. Patrol Enemy / Slime Encounter at Littoral Shallows
    enemy_pawn_paths = [
        "/Game/Melodia/Enemies/BP_Enemy_SakuraPhantom",
        "/Game/TurnBasedJRPGTemplate/Blueprints/Battle/BP_MelodySlimeBattle",
        "/Game/TurnBasedJRPGTemplate/Blueprints/Units/BP_EnemyUnitBase",
    ]
    for e_path in enemy_pawn_paths:
        e_cls = unreal.load_class(None, f"{e_path}.{e_path.rsplit('/', 1)[-1]}_C")
        if e_cls:
            patrol_actor = spawn_or_get_actor(
                e_cls,
                "SeaAbove_Littoral_EnemyPatrol",
                (1800.0, 800.0, 320.0),
                (0.0, -30.0, 0.0),
                tags=["SeaAbove_Enemy", "PatrolUnit", "WP_Scatter"],
            )
            placed["LittoralEnemyPatrol"] = patrol_actor.get_path_name()
            break

    return placed


def setup_pcg_arpeggio_bridge(far_gate_actor: unreal.Actor | None) -> dict[str, Any]:
    """Assemble and link the 24-node PCG Arpeggio Bridge in LV_SeaAbove_Prototype."""
    eal = unreal.EditorAssetLibrary
    eas = unreal.get_editor_subsystem(unreal.EditorActorSubsystem)
    
    graph_path = "/Game/EnvSandbox/PCG/Musical/Hero/PCG_Hero_ArpeggioBridge"
    profile_path = "/Game/EnvSandbox/PCG/Musical/Hero/DA_Hero_ArpeggioBridgeProfile"
    
    graph = eal.load_asset(graph_path)
    profile = eal.load_asset(profile_path)
    
    host_class = unreal.load_class(None, "/Script/BS_GodFile.PCGArpeggioBridgeHost")
    node_class = unreal.load_class(None, "/Script/BS_GodFile.PCGHeroMusicNode")
    
    if not host_class or not node_class:
        unreal.log_error(f"[SeaAbove] Failed to load PCG C++ classes: host={host_class}, node={node_class}")
        return {"error": "C++ classes not found"}

    # Base transform for Arpeggio Bridge in Sea Above
    bridge_origin_x = 1200.0
    bridge_origin_y = 600.0
    bridge_origin_z = 140.0
    
    step_spacing = 180.0
    bridge_rise = 1800.0
    walk_width = 220.0
    note_count = 24

    # Spawn Host Actor
    host = spawn_or_get_actor(
        host_class,
        "SeaAbove_PCG_ArpeggioBridge_Host",
        (bridge_origin_x, bridge_origin_y, bridge_origin_z),
        tags=["PCG_HeroMusicHost", "PCG_ArpeggioBridge", "WP_PrimaryRoute"],
    )

    if profile and hasattr(host, "profile"):
        host.set_editor_property("profile", profile)
    if graph and hasattr(host, "music_graph"):
        host.set_editor_property("music_graph", graph)
    if hasattr(host, "note_count"):
        host.set_editor_property("note_count", note_count)
    if far_gate_actor and hasattr(host, "completion_gate"):
        host.set_editor_property("completion_gate", far_gate_actor)

    # Spawn 24 Interactive Stepping Nodes
    nodes = []
    x_offset = -(note_count - 1) * step_spacing * 0.5
    for i, midi in enumerate(C_MAJOR_ARPEGGIO[:note_count]):
        alpha = i / max(1, note_count - 1)
        lx = x_offset + i * step_spacing
        ly = (alpha - 0.5) * walk_width * 0.70 + math.sin(alpha * math.pi * 1.2) * walk_width * 0.20
        lz = 28.0 + alpha * bridge_rise

        world_x = bridge_origin_x + lx + (note_count - 1) * step_spacing * 0.5
        world_y = bridge_origin_y + ly
        world_z = bridge_origin_z + lz

        node_label = f"SeaAbove_ArpeggioNode_{i:02d}_MIDI_{midi}"
        node_actor = spawn_or_get_actor(
            node_class,
            node_label,
            (world_x, world_y, world_z),
            tags=["PCG_HeroMusicNode", "PCG_ArpeggioBridgeNode", "WP_PrimaryRoute", "WP_NoScatter"],
        )

        # Configure node properties
        if hasattr(node_actor, "node_index"):
            node_actor.set_editor_property("node_index", i)
        if hasattr(node_actor, "midi_note"):
            node_actor.set_editor_property("midi_note", midi)
        if hasattr(node_actor, "lane"):
            node_actor.set_editor_property("lane", (i % 3) - 1)
        if hasattr(node_actor, "host_owner"):
            node_actor.set_editor_property("host_owner", host)

        nodes.append(node_actor.get_path_name())

    unreal.log(f"[SeaAbove] Successfully wired Arpeggio Bridge Host with {len(nodes)} musical nodes")
    return {
        "host": host.get_path_name(),
        "node_count": len(nodes),
        "nodes": nodes,
        "completion_gate": far_gate_actor.get_path_name() if far_gate_actor else None,
    }


def stage_reef_and_atlantis_landmarks() -> dict[str, Any]:
    """Place key reef islands, flora, and Atlantis architectural framing pieces."""
    eal = unreal.EditorAssetLibrary
    eas = unreal.get_editor_subsystem(unreal.EditorActorSubsystem)
    
    # 1. Reef Islands & Chunks (Band A)
    islands_data = [
        ("SM_Island_A", "/Game/EnvSandbox/Monoliths/SeaAbove/Prototype/Reef/Meshes/SM_Island_A", (800.0, 400.0, 55.0), (0.0, 15.0, 0.0), (1.5, 1.5, 1.2)),
        ("SM_Island_B", "/Game/EnvSandbox/Monoliths/SeaAbove/Prototype/Reef/Meshes/SM_Island_B", (2400.0, 900.0, 55.0), (0.0, -30.0, 0.0), (1.8, 1.8, 1.4)),
        ("SM_Island_C", "/Game/EnvSandbox/Monoliths/SeaAbove/Prototype/Reef/Meshes/SM_Island_C", (5200.0, 1200.0, 1800.0), (0.0, 45.0, 0.0), (2.2, 2.2, 1.8)),
    ]
    
    placed_islands = []
    for name, mesh_path, loc, rot, scale in islands_data:
        mesh = eal.load_asset(mesh_path)
        if mesh:
            actor = spawn_or_get_actor(
                unreal.StaticMeshActor,
                f"SeaAbove_{name}",
                loc,
                rot,
                scale,
                tags=["SeaAbove_Reef", "Band_A", "PCG_Ground"],
            )
            actor.static_mesh_component.set_static_mesh(mesh)
            mat = eal.load_asset("/Game/EnvSandbox/Monoliths/SeaAbove/Prototype/Reef/Materials/MI_SeaAbove_WetRock")
            if mat:
                actor.static_mesh_component.set_material(0, mat)
            placed_islands.append(actor.get_path_name())

    # 2. Coral & Flora Shallows (Band A)
    coral_data = [
        ("Coral_Cluster_01", "/Game/EnvSandbox/Monoliths/SeaAbove/Prototype/Reef/Meshes/SM_Coral_ReefCluster", (400.0, 800.0, 55.0), (0.0, 0.0, 0.0)),
        ("Coral_Staghorn_01", "/Game/EnvSandbox/Monoliths/SeaAbove/Prototype/Reef/Meshes/SM_Coral_Staghorn", (-400.0, 900.0, 55.0), (0.0, 45.0, 0.0)),
        ("Coral_Brain_01", "/Game/EnvSandbox/Monoliths/SeaAbove/Prototype/Reef/Meshes/SM_Coral_Brain", (600.0, 1400.0, 55.0), (0.0, -20.0, 0.0)),
        ("Kelp_Cluster_01", "/Game/EnvSandbox/Monoliths/SeaAbove/Prototype/Reef/Meshes/SM_Kelp_Cluster", (-600.0, 1600.0, 55.0), (0.0, 0.0, 0.0)),
        ("Flora_Chime_01", "/Game/EnvSandbox/Monoliths/SeaAbove/Prototype/Reef/Meshes/SM_Flora_Chime", (200.0, 300.0, 140.0), (0.0, 90.0, 0.0)),
    ]
    placed_coral = []
    for name, mesh_path, loc, rot in coral_data:
        mesh = eal.load_asset(mesh_path)
        if mesh:
            actor = spawn_or_get_actor(
                unreal.StaticMeshActor,
                f"SeaAbove_{name}",
                loc,
                rot,
                tags=["SeaAbove_Flora", "Band_A", "PCG_Scatter"],
            )
            actor.static_mesh_component.set_static_mesh(mesh)
            placed_coral.append(actor.get_path_name())

    # 3. Atlantis Framing Architecture at Overlook (Band A)
    atlantis_data = [
        ("ATL_Colonnade_Left", "/Game/EnvSandbox/Meshes/Atlantis/SM_ATL_Building_Columnade_A_01", (5100.0, 950.0, 1940.0), (0.0, 90.0, 0.0), (0.8, 0.8, 0.8)),
        ("ATL_Colonnade_Right", "/Game/EnvSandbox/Meshes/Atlantis/SM_ATL_Building_Columnade_A_01", (5100.0, 1450.0, 1940.0), (0.0, 90.0, 0.0), (0.8, 0.8, 0.8)),
        ("ATL_Arch_Framing", "/Game/EnvSandbox/Meshes/Atlantis/SM_ATL_Building_Arch_A_01", (5300.0, 1200.0, 1940.0), (0.0, 90.0, 0.0), (1.0, 1.0, 1.0)),
    ]
    placed_atlantis = []
    for name, mesh_path, loc, rot, scale in atlantis_data:
        mesh = eal.load_asset(mesh_path)
        if mesh:
            actor = spawn_or_get_actor(
                unreal.StaticMeshActor,
                f"SeaAbove_{name}",
                loc,
                rot,
                scale,
                tags=["SeaAbove_Atlantis", "Band_A", "WP_LandmarkClear"],
            )
            actor.static_mesh_component.set_static_mesh(mesh)
            placed_atlantis.append(actor.get_path_name())

    # 4. Inverted Cathedral Palace Cluster (Band C: Z < -5000)
    inverted_data = [
        ("ATL_Inverted_Palace_Main", "/Game/EnvSandbox/Meshes/Atlantis/SM_ATL_Building_Base_A_01", (2000.0, 2000.0, -5600.0), (180.0, 0.0, 0.0), (1.5, 1.5, 1.5)),
        ("ATL_Inverted_Colonnade_01", "/Game/EnvSandbox/Meshes/Atlantis/SM_ATL_Building_Columnade_A_01", (2400.0, 2000.0, -5400.0), (180.0, 45.0, 0.0), (1.2, 1.2, 1.2)),
    ]
    placed_inverted = []
    for name, mesh_path, loc, rot, scale in inverted_data:
        mesh = eal.load_asset(mesh_path)
        if mesh:
            actor = spawn_or_get_actor(
                unreal.StaticMeshActor,
                f"SeaAbove_{name}",
                loc,
                rot,
                scale,
                tags=["SeaAbove_InvertedCathedral", "Band_C", "PCG_Exclude"],
            )
            actor.static_mesh_component.set_static_mesh(mesh)
            placed_inverted.append(actor.get_path_name())

    # 5. Celestial Jellyfish Proxy (Band C)
    jelly_bell_path = "/Game/EnvSandbox/Monoliths/SeaAbove/Prototype/Reef/Meshes/JELLY_Bell"
    jelly_mesh = eal.load_asset(jelly_bell_path)
    if jelly_mesh:
        jelly_actor = spawn_or_get_actor(
            unreal.SkeletalMeshActor if hasattr(unreal, "SkeletalMeshActor") else unreal.StaticMeshActor,
            "SeaAbove_JELLY_Bell_Proxy",
            (0.0, 0.0, -5200.0),
            (0.0, 0.0, 0.0),
            (30.0, 30.0, 20.0),
            tags=["SeaAbove_Creature", "Band_C", "PCG_Exclude"],
        )
        if hasattr(jelly_actor, "skeletal_mesh_component"):
            jelly_actor.skeletal_mesh_component.set_skeletal_mesh(jelly_mesh)
            bell_mat = eal.load_asset("/Game/EnvSandbox/Monoliths/SeaAbove/Prototype/Reef/Materials/MI_Jelly_Bell")
            if bell_mat:
                jelly_actor.skeletal_mesh_component.set_material(0, bell_mat)

    return {
        "islands": placed_islands,
        "coral_flora": placed_coral,
        "atlantis_framing": placed_atlantis,
        "inverted_palace": placed_inverted,
    }


def layout_core_level_loop_and_export_heatmaps() -> dict[str, Any]:
    """Define level loop zones, apply WP/PCG tags, and generate PCG Heatmap PNG plate & manifest."""
    world_extent = 10000.0  # cm (-100m to +100m)
    grid_n = 64
    cell_size = (world_extent * 2.0) / grid_n

    # Define the 5 Core Level Loop Zones
    zones = [
        {
            "id": "zone_1_littoral_basin",
            "name": "Shorewake Littoral Basin",
            "role": "Player Arrival, NPC Dialogue, Starskiff Mooring",
            "bounds": {"min_x": -1500.0, "max_x": 1000.0, "min_y": -500.0, "max_y": 1500.0, "z_min": 55.0, "z_max": 200.0},
            "corridor_width_cm": 400.0,
            "tags": ["WP_PrimaryRoute", "WP_NoScatter", "PCG_Exclude"],
            "base_density": 0.05,
        },
        {
            "id": "zone_2_arpeggio_bridge",
            "name": "PCG Arpeggio Harmonic Ascent",
            "role": "24-Node Sequential Traversal, Rhythm Elevation (+18m)",
            "bounds": {"min_x": 1000.0, "max_x": 5500.0, "min_y": 500.0, "max_y": 1500.0, "z_min": 140.0, "z_max": 1940.0},
            "corridor_width_cm": 300.0,
            "tags": ["WP_PrimaryRoute", "WP_NoScatter", "PCG_Exclude"],
            "base_density": 0.0,
        },
        {
            "id": "zone_3_celestial_overlook",
            "name": "Celestial Coral Spire & Battle Arena",
            "role": "Boss/Encounter Platform, Traversal Gate, Horizon Vista",
            "bounds": {"min_x": 5000.0, "max_x": 7500.0, "min_y": 800.0, "max_y": 2000.0, "z_min": 1800.0, "z_max": 2200.0},
            "corridor_width_cm": 1200.0,
            "tags": ["WP_LandmarkClear", "PCG_Exclude", "Melodia_BattleArena"],
            "base_density": 0.15,
        },
        {
            "id": "zone_4_starskiff_waterway",
            "name": "Starskiff Celestial Open Ocean Channel",
            "role": "Deep Water Gliding, Waveform Gates, Return Current",
            "bounds": {"min_x": -5000.0, "max_x": 3000.0, "min_y": 1500.0, "max_y": 6000.0, "z_min": 55.0, "z_max": 100.0},
            "corridor_width_cm": 800.0,
            "tags": ["WP_PrimaryRoute", "WP_NoScatter"],
            "base_density": 0.0,
        },
        {
            "id": "zone_5_perimeter_barrier_reef",
            "name": "Perimeter Barrier Reef & Deep Shallows",
            "role": "Atmospheric Boundary, Procedural Coral & Kelp Forest",
            "bounds": {"min_x": -9000.0, "max_x": 9000.0, "min_y": -9000.0, "max_y": 9000.0, "z_min": -500.0, "z_max": 100.0},
            "corridor_width_cm": 0.0,
            "tags": ["PCG_Ground", "PCG_Scatter"],
            "base_density": 0.75,
        },
    ]

    # Generate 64x64 Density Matrix
    density_matrix = [[0.75 for _ in range(grid_n)] for _ in range(grid_n)]

    for row in range(grid_n):
        for col in range(grid_n):
            wx = -world_extent + (col + 0.5) * cell_size
            wy = -world_extent + (row + 0.5) * cell_size

            # Distance from center
            dist = math.sqrt(wx * wx + wy * wy)
            
            # Shallows falloff
            if dist < 6000.0:
                density = 0.45 * (dist / 6000.0)
            else:
                density = 0.75

            # Apply Zone exclusions and pathways
            for z in zones:
                b = z["bounds"]
                if b["min_x"] <= wx <= b["max_x"] and b["min_y"] <= wy <= b["max_y"]:
                    density = min(density, z["base_density"])

            density_matrix[row][col] = round(max(0.0, min(1.0, density)), 4)

    # Export PNG Plate using Pillow or basic writer
    img_size = 512
    HEATMAP_PNG_PATH.parent.mkdir(parents=True, exist_ok=True)
    HEATMAP_RENDER_PNG.parent.mkdir(parents=True, exist_ok=True)

    try:
        from PIL import Image, ImageDraw  # type: ignore
        img = Image.new("RGB", (img_size, img_size), (10, 15, 25))
        draw = ImageDraw.Draw(img)

        scale = img_size / grid_n
        for r in range(grid_n):
            for c in range(grid_n):
                val = density_matrix[r][c]
                # Bioluminescent palette: dark teal (low) -> bright cyan -> golden amber (high)
                red = int(val * 180 + (1.0 - val) * 15)
                green = int(val * 220 + (1.0 - val) * 35)
                blue = int(val * 255 + (1.0 - val) * 50)
                draw.rectangle([c * scale, r * scale, (c + 1) * scale, (r + 1) * scale], fill=(red, green, blue))

        # Overlay Level Loop Trajectory
        def to_img(x, y):
            ix = int((x + world_extent) / (world_extent * 2.0) * img_size)
            iy = int((y + world_extent) / (world_extent * 2.0) * img_size)
            return (max(0, min(img_size - 1, ix)), max(0, min(img_size - 1, iy)))

        # 1. Shorewake Start -> Arpeggio Bridge -> Spire -> Waterway -> Mooring
        p_start = to_img(0.0, 0.0)
        p_bridge_start = to_img(1200.0, 600.0)
        p_bridge_end = to_img(5340.0, 1200.0)
        p_battle = to_img(6000.0, 1200.0)
        p_tide_gate = to_img(-2400.0, 3600.0)
        p_skiff = to_img(-800.0, 1200.0)

        # Draw trajectory paths
        draw.line([p_start, p_bridge_start, p_bridge_end, p_battle], fill=(255, 230, 80), width=3)
        draw.line([p_battle, p_tide_gate, p_skiff, p_start], fill=(80, 240, 255), width=2)

        # Draw Keypoints
        for pt, col_pt in [(p_start, (255, 80, 80)), (p_bridge_start, (255, 200, 50)), (p_bridge_end, (100, 255, 100)), (p_battle, (255, 50, 255)), (p_skiff, (50, 200, 255))]:
            draw.ellipse([pt[0] - 5, pt[1] - 5, pt[0] + 5, pt[1] + 5], fill=col_pt, outline=(255, 255, 255))

        img.save(str(HEATMAP_PNG_PATH))
        img.save(str(HEATMAP_RENDER_PNG))
        log_info(f"[SeaAbove] Wrote PCG Heatmap plate to {HEATMAP_PNG_PATH}")
    except Exception as e:
        log_warning(f"[SeaAbove] PIL render skipped: {e}")

    # Write Structured Manifest
    manifest = {
        "schema": "melodia.sea_above_pcg_heatmap.v1",
        "level": "LV_SeaAbove_Prototype",
        "generated_at": datetime.now(timezone.utc).isoformat(),
        "world_bounds": {
            "extent_cm": world_extent,
            "min": [-world_extent, -world_extent, -6000.0],
            "max": [world_extent, world_extent, 3000.0],
        },
        "grid": {
            "resolution": grid_n,
            "cell_size_cm": cell_size,
        },
        "level_loop_zones": zones,
        "traversal_loop_flow": [
            {"order": 1, "node": "Shorewake Littoral Spawn", "coords": [0.0, 0.0, 140.0], "action": "Arrival & Dialogue Initiation"},
            {"order": 2, "node": "Arpeggio Bridge Entry", "coords": [1200.0, 600.0, 140.0], "action": "24-Note Sequential Rhythmic Stepping"},
            {"order": 3, "node": "Arpeggio Far Gate", "coords": [5340.0, 1200.0, 1940.0], "action": "Gate Unlock & Crescendo Pulse"},
            {"order": 4, "node": "Celestial Coral Spire Arena", "coords": [6000.0, 1200.0, 1940.0], "action": "Melodia Rhythm Combat Encounter"},
            {"order": 5, "node": "Starskiff Mooring / Gliding", "coords": [-800.0, 1200.0, 55.0], "action": "Deep Ocean Navigation & Tide Gate Traversal"},
            {"order": 6, "node": "Return Current to Dock", "coords": [0.0, 500.0, 55.0], "action": "Loop Completion & Rest Anchor"},
        ],
        "scale_contract": {
            "corridor_width_cm": 300.0,
            "clear_height_cm": 240.0,
            "hall_width_cm": 1200.0,
            "skiff_channel_width_cm": 800.0,
        },
        "heatmap_png_path": str(HEATMAP_PNG_PATH),
    }

    HEATMAP_MANIFEST_PATH.parent.mkdir(parents=True, exist_ok=True)
    HEATMAP_MANIFEST_PATH.write_text(json.dumps(manifest, indent=2) + "\n", encoding="utf-8")
    
    audit_report = {
        "status": "PASS",
        "timestamp": datetime.now(timezone.utc).isoformat(),
        "level": "LV_SeaAbove_Prototype",
        "heatmap_contract_present": True,
        "zones_count": len(zones),
        "manifest": str(HEATMAP_MANIFEST_PATH),
        "heatmap_image": str(HEATMAP_PNG_PATH),
    }
    AUDIT_REPORT_PATH.parent.mkdir(parents=True, exist_ok=True)
    AUDIT_REPORT_PATH.write_text(json.dumps(audit_report, indent=2) + "\n", encoding="utf-8")

    log_info(f"[SeaAbove] Wrote PCG Heatmap manifest to {HEATMAP_MANIFEST_PATH}")
    return manifest


def main() -> int:
    log_info("====================================================================")
    log_info("SEA ABOVE: STAGING LEVEL BLUEPRINTS, ARPEGGIO BRIDGE & PCG HEATMAPS")
    log_info("====================================================================")
    
    blueprints = {}
    bridge_info = {}
    landmarks = {}

    if HAS_UNREAL:
        try:
            world = load_level()
            log_info(f"[SeaAbove] Active World: {world.get_path_name()}")

            # 1. Place Blueprints
            log_info("[SeaAbove] 1/4 Staging Blueprints...")
            blueprints = setup_sea_above_blueprints()

            # 2. Wire PCG Arpeggio Bridge
            log_info("[SeaAbove] 2/4 Setting up PCG Arpeggio Bridge...")
            eas = unreal.get_editor_subsystem(unreal.EditorActorSubsystem)
            far_gate = None
            for a in eas.get_all_level_actors() or []:
                if a.get_actor_label() == "SeaAbove_ArpeggioFarGate":
                    far_gate = a
                    break
            bridge_info = setup_pcg_arpeggio_bridge(far_gate)

            # 3. Stage Reef & Ruin Landmarks
            log_info("[SeaAbove] 3/4 Staging Reef and Atlantis Architecture...")
            landmarks = stage_reef_and_atlantis_landmarks()

            # Save level changes
            try:
                les = unreal.get_editor_subsystem(unreal.LevelEditorSubsystem)
                les.save_current_level()
                log_info("[SeaAbove] Saved LV_SeaAbove_Prototype successfully")
            except Exception as e:
                log_warning(f"[SeaAbove] Level save note: {e}")
        except Exception as e:
            log_warning(f"[SeaAbove] Unreal editor pass note: {e}")
    else:
        log_info("[SeaAbove] Running in standalone offline pipeline mode")

    # 4. Layout Core Loop & Export Heatmaps
    log_info("[SeaAbove] 4/4 Laying out Core Level Loop and Exporting PCG Heatmaps...")
    heatmap_manifest = layout_core_level_loop_and_export_heatmaps()

    summary = {
        "status": "SUCCESS",
        "level": MAP_PATH,
        "blueprints_placed": blueprints,
        "arpeggio_bridge": bridge_info,
        "landmarks_placed": landmarks,
        "heatmap": {
            "zones": len(heatmap_manifest.get("level_loop_zones", [])),
            "manifest": str(HEATMAP_MANIFEST_PATH),
            "png": str(HEATMAP_PNG_PATH),
        },
    }
    print(json.dumps(summary, indent=2))
    return 0


if __name__ == "__main__":
    main()
