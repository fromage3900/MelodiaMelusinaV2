"""Audit the Arpeggio Bridge proof graph, level, seeds, and control bridge."""
from __future__ import annotations

import pcg_hero_music_control as control
from build_pcg_hero_arpeggio_bridge import C_MAJOR_ARPEGGIO, build_bridge_layout, build_bridge_curve_points


GRAPH_PATH = "/Game/EnvSandbox/PCG/Musical/Hero/PCG_Hero_ArpeggioBridge"
PROFILE_PATH = "/Game/EnvSandbox/PCG/Musical/Hero/DA_Hero_ArpeggioBridgeProfile"
LEVEL_PATH = "/Game/EnvSandbox/PCG/Musical/Hero/L_PCG_Hero_ArpeggioBridge"
UNIVERSAL_SCATTER_PATH = "/Game/EnvSandbox/PCG/Universal/PCG_Melodia_Universal_Scatter"
MPC_PATH = "/Game/Melodia/_PROJECT/04_Materials/MPC_Melodia_Palette"
TENSOR_SOURCE_PATH = "/Game/EnvSandbox/PCG/Styles/Escher/PCG_Escher_SpiralAscent"


def audit() -> dict:
    import unreal

    level_editor = unreal.get_editor_subsystem(unreal.LevelEditorSubsystem)
    current_world = level_editor.get_world()
    current_path = current_world.get_outermost().get_name() if current_world else ""
    if current_path != LEVEL_PATH and not level_editor.load_level(LEVEL_PATH):
        raise RuntimeError(f"could not load proof level {LEVEL_PATH}")

    nodes, _ = build_bridge_layout()
    expected_seeds = [(node_index << 16) | ((lane + 1) << 8) | midi for _, _, _, node_index, lane, midi in nodes]
    snapshot = control.read_control_snapshot(unreal)
    report = {
        "expected": {"nodes": 24, "pattern": list(C_MAJOR_ARPEGGIO)},
        "assets": {path: unreal.EditorAssetLibrary.does_asset_exist(path) for path in (GRAPH_PATH, PROFILE_PATH, LEVEL_PATH, UNIVERSAL_SCATTER_PATH, MPC_PATH, TENSOR_SOURCE_PATH)},
        "graph": {},
        "level": {},
        "control": control.control_alias_manifest(snapshot, "bridge"),
        "checks": {
            "unique_seeds": len(expected_seeds) == len(set(expected_seeds)),
            "unique_midi_identities": len({(node_index, midi) for _, _, _, node_index, _, midi in nodes}) == 24,
            "c_major_pitch_classes": all(midi % 12 in {0, 4, 7} for midi in C_MAJOR_ARPEGGIO),
            "two_octave_range": max(C_MAJOR_ARPEGGIO) - min(C_MAJOR_ARPEGGIO) <= 24,
            "all_eleven_controls_mapped": len(control.map_control_aliases(snapshot, "bridge")) == 11,
            "canonical_mpc_path": MPC_PATH.endswith("MPC_Melodia_Palette"),
            "universal_scatter_asset_present": unreal.EditorAssetLibrary.does_asset_exist(UNIVERSAL_SCATTER_PATH),
            "expanded_tensor_source_present": unreal.EditorAssetLibrary.does_asset_exist(TENSOR_SOURCE_PATH),
            "measured_traversal_curve": len(build_bridge_curve_points()) == 24,
        },
    }
    graph = unreal.EditorAssetLibrary.load_asset(GRAPH_PATH)
    if graph:
        nodes_in_graph = list(graph.get_editor_property("nodes") or [])
        classes = [node.get_settings().get_class().get_name() for node in nodes_in_graph if node.get_settings()]
        report["graph"] = {"nodes": len(nodes_in_graph), "classes": classes, "path": GRAPH_PATH}
        mesh_paths = []
        for node in nodes_in_graph:
            settings = node.get_settings()
            if not settings or settings.get_class().get_name() != "PCGStaticMeshSpawnerSettings":
                continue
            selector = settings.get_editor_property("mesh_selector_parameters")
            for entry in selector.get_editor_property("mesh_entries"):
                descriptor = entry.get_editor_property("descriptor")
                mesh = descriptor.get_editor_property("static_mesh")
                if mesh:
                    mesh_paths.append(mesh.get_path_name().split(".")[0])
        required_classic_meshes = {
            "/Game/EnvSandbox/Greybox_Kit/SM_Greybox_Floor_4x4",
            "/Game/EnvSandbox/Greybox_Kit/SM_Greybox_HalfWall_4",
            "/Game/EnvSandbox/Greybox_Kit/SM_column_02",
        }
        report["graph"]["static_mesh_paths"] = sorted(set(mesh_paths))
        report["checks"]["graph_has_actor_branch"] = "PCGSpawnActorSettings" in classes
        report["checks"]["graph_has_black_and_keybed_branches"] = classes.count("PCGStaticMeshSpawnerSettings") >= 2
        report["checks"]["classic_architecture_branches"] = classes.count("PCGStaticMeshSpawnerSettings") >= 4
        report["checks"]["classic_mesh_descriptors_exact"] = required_classic_meshes.issubset(set(mesh_paths))
        report["checks"]["graph_has_pcgex_curve_branch"] = (
            "PCGExSampleNearestSplineSettings" in classes
            and "PCGSplineSamplerSettings" in classes
            and "PCGExCreateSplineSettings" in classes
        )
        # The copied TensorSpin/Extrude branch is intentionally absent from
        # the playable bridge until its finite guide-data contract is proven.
        # This is safer than serializing a dormant gable-producing branch.
        report["checks"]["graph_tensor_branch_disabled"] = (
            "PCGExCreateTensorSpinSettings" not in classes
            and "PCGExExtrudeTensorsSettings" not in classes
        )

    try:
        actors = unreal.get_editor_subsystem(unreal.EditorActorSubsystem).get_all_level_actors() or []
        nodes_in_level = [actor for actor in actors if "PCG_HeroMusicNode" in [str(tag) for tag in (actor.tags or [])] and "PCG_ArpeggioBridge" in [str(tag) for tag in (actor.tags or [])]]
        hosts = [actor for actor in actors if actor.get_class().get_name() == "PCGArpeggioBridgeHost"]
        gates = [actor for actor in actors if "PCG_ArpeggioFarGate" in [str(tag) for tag in (actor.tags or [])]]
        architecture = [actor for actor in actors if "PCG_HeroArchitecture" in [str(tag) for tag in (actor.tags or [])]]
        report["level"] = {
            "actor_count": len(actors),
            "node_actor_count": len(nodes_in_level),
            "host_count": len(hosts),
            "gate_count": len(gates),
            "architecture_volume_count": len(architecture),
            "architecture_volume_classes": [actor.get_class().get_name() for actor in architecture],
            "node_indices": sorted({int(actor.get_editor_property("node_index")) for actor in nodes_in_level}),
        }
        report["checks"]["node_actor_count"] = len(nodes_in_level) == 24
        report["checks"]["host_present"] = len(hosts) == 1
        report["checks"]["far_gate_present"] = len(gates) == 1
        report["checks"]["architecture_volume_absent"] = len(architecture) == 0
    except Exception as exc:
        report["level"]["actor_audit_error"] = str(exc)
    report["checks"]["assets_present"] = all(report["assets"].values())
    unreal.log(f"[PCG Hero Arpeggio Bridge] audit {report}")
    return report


if __name__ == "__main__":
    print(audit())
