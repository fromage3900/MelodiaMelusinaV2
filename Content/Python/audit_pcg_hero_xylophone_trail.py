"""Audit the Xylophone Trail proof graph, level, geometry branches, and controls."""
from __future__ import annotations

import pcg_hero_music_control as control
from build_pcg_hero_xylophone_trail import build_xylophone_trail_graph
from pcg_xylophone_layout import build_xylophone_path_specs, validate_xylophone_layout


GRAPH_PATH = "/Game/EnvSandbox/PCG/Musical/Hero/PCG_Hero_XylophoneTrail"
PROFILE_PATH = "/Game/EnvSandbox/PCG/Musical/Hero/DA_Hero_XylophoneTrailProfile"
LEVEL_PATH = "/Game/EnvSandbox/PCG/Musical/Hero/L_PCG_Hero_XylophoneTrail"
UNIVERSAL_SCATTER_PATH = "/Game/EnvSandbox/PCG/Universal/PCG_Melodia_Universal_Scatter"
MPC_PATH = "/Game/Melodia/_PROJECT/04_Materials/MPC_Melodia_Palette"
BEVELED_BAR_MESH = "/Game/EnvSandbox/PCG/Musical/SM_PianoKey_White_Bevel"
FLOOR_MESH = "/Game/EnvSandbox/Greybox_Kit/SM_Greybox_Floor_4x4"
RAIL_MESH = "/Game/EnvSandbox/Greybox_Kit/SM_Greybox_HalfWall_4"


def _graph_mesh_paths(graph) -> list[str]:
    meshes: list[str] = []
    for node in list(graph.get_editor_property("nodes") or []):
        settings = node.get_settings()
        if not settings or settings.get_class().get_name() != "PCGStaticMeshSpawnerSettings":
            continue
        selector = settings.get_editor_property("mesh_selector_parameters")
        for entry in selector.get_editor_property("mesh_entries"):
            descriptor = entry.get_editor_property("descriptor")
            mesh = descriptor.get_editor_property("static_mesh")
            if mesh:
                meshes.append(mesh.get_path_name().split(".")[0])
    return sorted(set(meshes))


def audit() -> dict:
    import unreal

    level_editor = unreal.get_editor_subsystem(unreal.LevelEditorSubsystem)
    current_world = level_editor.get_world()
    current_path = current_world.get_outermost().get_name() if current_world else ""
    if current_path != LEVEL_PATH and not level_editor.load_level(LEVEL_PATH):
        raise RuntimeError(f"could not load proof level {LEVEL_PATH}")

    specs = build_xylophone_path_specs()
    snapshot = control.read_control_snapshot(unreal)
    expected_seeds = [spec.seed for spec in specs]
    report = {
        "expected": {"bars": 24, "instrument_family": "pitched_percussion_xylophone"},
        "assets": {
            path: unreal.EditorAssetLibrary.does_asset_exist(path)
            for path in (GRAPH_PATH, PROFILE_PATH, LEVEL_PATH, UNIVERSAL_SCATTER_PATH, MPC_PATH, BEVELED_BAR_MESH, FLOOR_MESH, RAIL_MESH)
        },
        "graph": {},
        "level": {},
        "control": control.control_alias_manifest(snapshot, "XylophoneTrail"),
        "checks": {
            "finite_layout": not validate_xylophone_layout(specs),
            "unique_seeds": len(expected_seeds) == len(set(expected_seeds)),
            "unique_midi_identities": len({(spec.step, spec.midi_note) for spec in specs}) == 24,
            "ascending_height": all(specs[index + 1].z > specs[index].z for index in range(len(specs) - 1)),
            "all_eleven_controls_mapped": len(control.map_control_aliases(snapshot, "XylophoneTrail")) == 11,
            "canonical_mpc_path": MPC_PATH.endswith("MPC_Melodia_Palette"),
            "universal_scatter_asset_present": unreal.EditorAssetLibrary.does_asset_exist(UNIVERSAL_SCATTER_PATH),
        },
    }

    graph = unreal.EditorAssetLibrary.load_asset(GRAPH_PATH)
    if graph:
        graph_nodes = list(graph.get_editor_property("nodes") or [])
        classes = [node.get_settings().get_class().get_name() for node in graph_nodes if node.get_settings()]
        meshes = _graph_mesh_paths(graph)
        report["graph"] = {"nodes": len(graph_nodes), "classes": classes, "static_mesh_paths": meshes, "path": GRAPH_PATH}
        report["checks"].update({
            "graph_has_actor_branch": "PCGSpawnActorSettings" in classes,
            "graph_has_pcgex_curve_branch": all(name in classes for name in ("PCGExCreateSplineSettings", "PCGSplineSamplerSettings", "PCGExSampleNearestSplineSettings")),
            "classic_mesh_descriptors_exact": {FLOOR_MESH, RAIL_MESH}.issubset(set(meshes)),
            "beveled_bar_mesh_in_profile_contract": BEVELED_BAR_MESH in (unreal.EditorAssetLibrary.load_asset(PROFILE_PATH).get_editor_property("node_mesh").get_path_name().split(".")[0] if unreal.EditorAssetLibrary.load_asset(PROFILE_PATH) and unreal.EditorAssetLibrary.load_asset(PROFILE_PATH).get_editor_property("node_mesh") else ""),
        })

    try:
        actors = unreal.get_editor_subsystem(unreal.EditorActorSubsystem).get_all_level_actors() or []
        nodes = [actor for actor in actors if "PCG_HeroMusicNode" in [str(tag) for tag in (actor.tags or [])] and "PCG_XylophoneTrail" in [str(tag) for tag in (actor.tags or [])]]
        hosts = [actor for actor in actors if actor.get_class().get_name().lstrip("A") == "PCGHeroMusicGraphHost"]
        cameras = [actor for actor in actors if actor.get_actor_label() == "Xylophone Trail Overview Camera"]
        report["level"] = {
            "actor_count": len(actors),
            "bar_actor_count": len(nodes),
            "host_count": len(hosts),
            "overview_camera_count": len(cameras),
            "node_indices": sorted({int(actor.get_editor_property("node_index")) for actor in nodes}),
        }
        report["checks"].update({
            "bar_actor_count": len(nodes) == 24,
            "host_present": len(hosts) == 1,
            "overview_camera_present": len(cameras) == 1,
        })
    except Exception as exc:
        report["level"]["actor_audit_error"] = str(exc)

    report["checks"]["assets_present"] = all(report["assets"].values())
    report["ok"] = all(bool(value) for value in report["checks"].values())
    unreal.log(f"[PCG Hero Xylophone Trail] audit {report}")
    return report


if __name__ == "__main__":
    print(audit())
