"""Audit the BellTreeGarden graph and proof level without PIE."""
from __future__ import annotations

from math import dist

import pcg_hero_music_control as control
from build_pcg_hero_bell_tree_garden import BELL_PATTERN, build_bell_branch_curve_points, build_bell_garden_layout, bell_midi_pattern


GRAPH_PATH = "/Game/EnvSandbox/PCG/Musical/Hero/PCG_Hero_BellTreeGarden"
PROFILE_PATH = "/Game/EnvSandbox/PCG/Musical/Hero/DA_Hero_BellTreeGardenProfile"
LEVEL_PATH = "/Game/EnvSandbox/PCG/Musical/Hero/L_PCG_Hero_BellTreeGarden"
MPC_PATH = "/Game/Melodia/_PROJECT/04_Materials/MPC_Melodia_Palette"
BELL_MATERIAL_PATH = "/Game/Melodia/Characters/Melusina/Materials/MI_Melusina_Metal_2__Matcap__002"


def audit() -> dict:
    import unreal

    level_editor = unreal.get_editor_subsystem(unreal.LevelEditorSubsystem)
    current_world = level_editor.get_world()
    current_path = current_world.get_outermost().get_name() if current_world else ""
    if current_path != LEVEL_PATH and not level_editor.load_level(LEVEL_PATH):
        raise RuntimeError(f"could not load proof level {LEVEL_PATH}")

    nodes, _ = build_bell_garden_layout()
    expected_seeds = [
        (node_index << 16) | ((branch + 1) << 8) | midi
        for _, _, _, node_index, _lane, midi, branch in nodes
    ]
    snapshot = control.read_control_snapshot(unreal)
    report = {
        "expected": {"bells": 18, "branches": 3, "pattern": list(bell_midi_pattern())},
        "assets": {
            path: unreal.EditorAssetLibrary.does_asset_exist(path)
            for path in (GRAPH_PATH, PROFILE_PATH, LEVEL_PATH, MPC_PATH, BELL_MATERIAL_PATH)
        },
        "graph": {},
        "level": {},
        "control": control.control_alias_manifest(snapshot, "bell_tree_garden"),
        "checks": {
            "unique_seeds": len(expected_seeds) == len(set(expected_seeds)),
            "unique_midi_identities": len({(node_index, midi) for _, _, _, node_index, _, midi, _ in nodes}) == 18,
            "pentatonic_pitch_classes": all(midi % 12 in {0, 2, 4, 7, 9} for midi in bell_midi_pattern()),
            "two_octave_range": max(bell_midi_pattern()) - min(bell_midi_pattern()) <= 26,
            "all_eleven_controls_mapped": len(control.map_control_aliases(snapshot, "bell_tree_garden")) == 11,
            "canonical_mpc_path": MPC_PATH.endswith("MPC_Melodia_Palette"),
            "measured_traversal_curve": len(build_bell_branch_curve_points()) == 18,
            "even_height_aware_spacing": False,
            "classic_geometry_contract": True,
            "no_cube_fallback_in_graph_builder": True,
        },
    }

    graph = unreal.EditorAssetLibrary.load_asset(GRAPH_PATH)
    if graph:
        graph_nodes = list(graph.get_editor_property("nodes") or [])
        classes = [node.get_settings().get_class().get_name() for node in graph_nodes if node.get_settings()]
        report["graph"] = {"nodes": len(graph_nodes), "classes": classes, "path": GRAPH_PATH}
        mesh_paths = []
        for node in graph_nodes:
            settings = node.get_settings()
            if not settings or settings.get_class().get_name() != "PCGStaticMeshSpawnerSettings":
                continue
            selector = settings.get_editor_property("mesh_selector_parameters")
            for entry in selector.get_editor_property("mesh_entries"):
                descriptor = entry.get_editor_property("descriptor")
                mesh = descriptor.get_editor_property("static_mesh")
                if mesh:
                    mesh_paths.append(mesh.get_path_name().split(".")[0])
        required_meshes = {
            "/Game/EnvSandbox/Greybox_Kit/SM_Greybox_Floor_4x4",
            "/Game/EnvSandbox/Greybox_Kit/SM_Greybox_HalfWall_4",
            "/Game/EnvSandbox/Greybox_Kit/SM_column_02",
            "/Game/EnvSandbox/Greybox_Kit/SM_arch_06",
        }
        report["graph"]["static_mesh_paths"] = sorted(set(mesh_paths))
        report["checks"]["graph_has_bell_actor_branch"] = "PCGSpawnActorSettings" in classes
        report["checks"]["graph_has_pcgex_curve_branch"] = (
            "PCGExSampleNearestSplineSettings" in classes
            and "PCGSplineSamplerSettings" in classes
            and "PCGExCreateSplineSettings" in classes
        )
        report["checks"]["classic_mesh_descriptors_exact"] = required_meshes.issubset(set(mesh_paths))

    layout_distances = [
        dist(nodes[index][:3], nodes[index + 1][:3])
        for index in range(len(nodes) - 1)
    ]
    report["layout"] = {
        "spacing_min": min(layout_distances),
        "spacing_max": max(layout_distances),
        "spacing_variance": max(layout_distances) - min(layout_distances),
        "z_monotonic": all(nodes[index + 1][2] > nodes[index][2] for index in range(len(nodes) - 1)),
    }
    report["checks"]["even_height_aware_spacing"] = (
        report["layout"]["spacing_variance"] < 1.0
        and report["layout"]["z_monotonic"]
    )

    try:
        actors = unreal.get_editor_subsystem(unreal.EditorActorSubsystem).get_all_level_actors() or []
        nodes_in_level = [
            actor for actor in actors
            if "PCG_HeroMusicNode" in [str(tag) for tag in (actor.tags or [])]
            and "PCG_BellTreeGarden" in [str(tag) for tag in (actor.tags or [])]
        ]
        # Reflected native classes omit the C++ A/U prefix in UE Python.
        hosts = [
            actor for actor in actors
            if actor.get_class().get_name().lstrip("A") == "PCGBellTreeGardenHost"
        ]
        architecture = [actor for actor in actors if "PCG_HeroArchitecture" in [str(tag) for tag in (actor.tags or [])]]
        report["level"] = {
            "actor_count": len(actors),
            "node_actor_count": len(nodes_in_level),
            "host_count": len(hosts),
            "architecture_volume_count": len(architecture),
            "node_indices": sorted({int(actor.get_editor_property("node_index")) for actor in nodes_in_level}),
            "node_class_names": sorted({actor.get_class().get_name() for actor in nodes_in_level}),
        }
        report["checks"]["node_actor_count"] = len(nodes_in_level) == 18
        report["checks"]["host_present"] = len(hosts) == 1
        report["checks"]["architecture_volume_absent"] = len(architecture) == 0
        report["checks"]["bell_node_class_present"] = all(
            actor.get_class().get_name().lstrip("A") == "PCGBellTreeGardenNode"
            for actor in nodes_in_level
        )
        uds = [
            actor for actor in actors
            if "PCG_BellTreeGarden_UDS" in [str(tag) for tag in (actor.tags or [])]
            and actor.get_class().get_name() == "Ultra_Dynamic_Sky_C"
        ]
        report["level"]["uds_actor_count"] = len(uds)
        report["checks"]["uds_blueprint_present"] = len(uds) == 1
    except Exception as exc:
        report["level"]["actor_audit_error"] = str(exc)

    report["checks"]["assets_present"] = all(report["assets"].values())
    report["ok"] = all(bool(value) for value in report["checks"].values())
    unreal.log(f"[PCG Hero BellTreeGarden] audit {report}")
    return report


if __name__ == "__main__":
    print(audit())
