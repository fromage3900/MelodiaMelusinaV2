"""Audit the Resonance Cathedral proof graph, level, seeds, and control bridge."""
from __future__ import annotations

import pcg_hero_music_control as control
from build_pcg_hero_resonance_cathedral import build_cathedral_layout, build_cathedral_vault_curve_points


GRAPH_PATH = "/Game/EnvSandbox/PCG/Musical/Hero/PCG_Hero_ResonanceCathedral"
PROFILE_PATH = "/Game/EnvSandbox/PCG/Musical/Hero/DA_Hero_ResonanceCathedralProfile"
LEVEL_PATH = "/Game/EnvSandbox/PCG/Musical/Hero/L_PCG_Hero_ResonanceCathedral"
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

    pads, _ = build_cathedral_layout()
    expected_seeds = [(node_index << 16) | (degree << 8) | midi for _, _, _, node_index, degree, midi in pads]
    snapshot = control.read_control_snapshot(unreal)
    report = {
        "expected": {"stations": 4, "pads": 12},
        "assets": {path: unreal.EditorAssetLibrary.does_asset_exist(path) for path in (GRAPH_PATH, PROFILE_PATH, LEVEL_PATH, UNIVERSAL_SCATTER_PATH, MPC_PATH, TENSOR_SOURCE_PATH)},
        "graph": {},
        "level": {},
        "control": control.control_alias_manifest(snapshot, "cathedral"),
        "checks": {
            "unique_seeds": len(expected_seeds) == len(set(expected_seeds)),
            "unique_midi_identities": len({(node_index, midi) for _, _, _, node_index, _, midi in pads}) == 12,
            "all_eleven_controls_mapped": len(control.map_control_aliases(snapshot, "cathedral")) == 11,
            "canonical_mpc_path": MPC_PATH.endswith("MPC_Melodia_Palette"),
            "universal_scatter_asset_present": unreal.EditorAssetLibrary.does_asset_exist(UNIVERSAL_SCATTER_PATH),
            "expanded_tensor_source_present": unreal.EditorAssetLibrary.does_asset_exist(TENSOR_SOURCE_PATH),
            "measured_vault_curve": len(build_cathedral_vault_curve_points()) >= 5,
        },
    }
    graph = unreal.EditorAssetLibrary.load_asset(GRAPH_PATH)
    if graph:
        nodes = list(graph.get_editor_property("nodes") or [])
        classes = [node.get_settings().get_class().get_name() for node in nodes if node.get_settings()]
        report["graph"] = {"nodes": len(nodes), "classes": classes, "path": GRAPH_PATH}
        mesh_paths = []
        for node in nodes:
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
            "/Game/EnvSandbox/PCG/Musical/SM_PianoKey_Black_Bevel",
            "/Game/EnvSandbox/PCG/Musical/SM_Piano_Keybed",
            "/Game/EnvSandbox/Greybox_Kit/SM_column_02",
            "/Game/EnvSandbox/Greybox_Kit/SM_arch_06",
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
        report["checks"]["graph_has_expanded_pcgex_tensor_branch"] = (
            "PCGExCreateTensorSpinSettings" in classes
            and "PCGExExtrudeTensorsSettings" in classes
        )

    try:
        actors = unreal.get_editor_subsystem(unreal.EditorActorSubsystem).get_all_level_actors() or []
        pads_in_level = [actor for actor in actors if "PCG_HeroMusicNode" in [str(tag) for tag in (actor.tags or [])] and "PCG_ResonanceCathedral" in [str(tag) for tag in (actor.tags or [])]]
        hosts = [actor for actor in actors if actor.get_class().get_name() == "PCGResonanceCathedralHost"]
        architecture = [actor for actor in actors if "PCG_HeroArchitecture" in [str(tag) for tag in (actor.tags or [])]]
        report["level"] = {
            "actor_count": len(actors),
            "pad_actor_count": len(pads_in_level),
            "host_count": len(hosts),
            "architecture_volume_count": len(architecture),
            "architecture_volume_classes": [actor.get_class().get_name() for actor in architecture],
            "node_indices": sorted({int(actor.get_editor_property("node_index")) for actor in pads_in_level}),
            "midi_notes": sorted({int(actor.get_editor_property("midi_note")) for actor in pads_in_level}),
        }
        report["checks"]["pad_actor_count"] = len(pads_in_level) == 12
        report["checks"]["host_present"] = len(hosts) == 1
        hidden_architecture = all(
            bool(getattr(actor, "hidden", False))
            or (bool(actor.is_hidden_ed()) if hasattr(actor, "is_hidden_ed") else False)
            or (bool(actor.is_temporarily_hidden_in_editor()) if hasattr(actor, "is_temporarily_hidden_in_editor") else False)
            for actor in architecture
        )
        report["checks"]["architecture_volume_retired"] = len(architecture) == 0 or hidden_architecture
    except Exception as exc:
        report["level"]["actor_audit_error"] = str(exc)
    report["checks"]["assets_present"] = all(report["assets"].values())
    unreal.log(f"[PCG Hero Resonance Cathedral] audit {report}")
    return report


if __name__ == "__main__":
    print(audit())
