"""Deploy persistent, terrain-wide greybox traversal anchors to all WP levels.

The existing pillar volumes are local dressing lanes. This pass adds a sparse
3x3 traversal grid over the 20km mesh terrain: persistent collision platforms
    and connector floors, plus one known-producing volume-driven PCG graph per
    node. Theme-specific surface scatter remains owned by the pillar builder.
PCG generation is kicked asynchronously; reopening the map regenerates the
saved graphs without requiring a daemon or a live GMM connection.
"""
from __future__ import annotations

import json
from pathlib import Path

import unreal
import pcg_graph_builder as gb


ROOT = Path(__file__).resolve().parents[2]
LEVELS = ("SakuraDream", "SpaceCathedral", "BaroqueGrotto", "CosmicOrrery")
LEVEL_ROOT = "/Game/EnvSandbox/Environments/WP/L_WP_{}"
CUBE = "/Game/EnvSandbox/Greybox_Kit/SM_Greybox_Cube_1m.SM_Greybox_Cube_1m"
WALKABLE_GRAPH = "/Game/EnvSandbox/PCG/Styles/Escher/PCG_EscherRelativityRoom"
STYLE_BY_LEVEL = {
    "SakuraDream": "SAKURA",
    "SpaceCathedral": "SPACE_CATHEDRAL",
    "BaroqueGrotto": "BAROQUE_GROTTO",
    "CosmicOrrery": "COSMIC_ORRERY",
}
GRID = (-6500.0, 0.0, 6500.0)
PREFIX = "WPGrid_"


def _persistent(actor) -> None:
    try:
        actor.set_editor_property("is_spatially_loaded", False)
    except Exception:
        pass


def _destroy(eas) -> None:
    for actor in list(eas.get_all_level_actors() or []):
        if actor.get_actor_label().startswith(PREFIX):
            eas.destroy_actor(actor)


def _configure_navigation(eas) -> bool:
    """Persist dynamic Recast generation for editor-authored WP scaffolds."""
    configured = False
    try:
        runtime_generation = unreal.RuntimeGenerationType.DYNAMIC
    except AttributeError:
        return False
    for actor in list(eas.get_all_level_actors() or []):
        if actor.get_class().get_name() != "RecastNavMesh":
            continue
        try:
            actor.set_editor_property("runtime_generation", runtime_generation)
            actor.modify()
            configured = True
        except Exception:
            continue
    return configured


def _mesh_actor(eas, mesh, label, location, scale, tags):
    actor = eas.spawn_actor_from_class(unreal.StaticMeshActor, unreal.Vector(*location))
    _persistent(actor)
    actor.set_actor_label(label)
    actor.set_actor_scale3d(unreal.Vector(*scale))
    comp = actor.static_mesh_component
    comp.set_editor_property("static_mesh", mesh)
    comp.set_collision_enabled(unreal.CollisionEnabled.QUERY_AND_PHYSICS)
    comp.set_collision_profile_name("BlockAll")
    try:
        comp.set_editor_property("can_ever_affect_navigation", True)
    except Exception:
        pass
    actor.tags = [unreal.Name(tag) for tag in tags]
    actor.modify()
    return actor


def deploy(level_key: str) -> dict:
    level = LEVEL_ROOT.format(level_key)
    les = unreal.get_editor_subsystem(unreal.LevelEditorSubsystem)
    if not les.load_level(level):
        return {"level": level_key, "error": "load_failed"}
    try:
        descs = unreal.WorldPartitionBlueprintLibrary.get_actor_descs()
        unreal.WorldPartitionBlueprintLibrary.load_actors([d.guid for d in descs])
    except Exception:
        pass
    eas = unreal.get_editor_subsystem(unreal.EditorActorSubsystem)
    _destroy(eas)
    mesh = unreal.EditorAssetLibrary.load_asset(CUBE)
    graph_path = WALKABLE_GRAPH
    graph = unreal.EditorAssetLibrary.load_asset(graph_path)
    if not mesh or not graph:
        return {"level": level_key, "error": "required_asset_missing", "graph": graph_path}

    navigation_configured = _configure_navigation(eas)
    platforms = []
    volumes = []
    route_nodes = []
    for ix, x in enumerate(GRID):
        for iy, y in enumerate(GRID):
            node = f"{ix}_{iy}"
            _mesh_actor(
                eas, mesh, f"{PREFIX}Platform_{node}", (x, y, 50.0),
                (8.0, 8.0, 0.15),
                ["WP_PrimaryRoute", "WP_NoScatter", "GB_HumanScale", "WP_HeatmapAnchor"],
            )
            vol = eas.spawn_actor_from_class(unreal.PCGVolume, unreal.Vector(x, y, 120.0))
            _persistent(vol)
            vol.set_actor_label(f"{PREFIX}PCG_{node}")
            vol.set_actor_scale3d(unreal.Vector(8.0, 8.0, 3.0))
            comp = vol.get_component_by_class(unreal.PCGComponent)
            gb.assign_pcg_graph(comp, graph)
            gb.configure_pcg_component(comp, seed=9100 + ix * 31 + iy * 17, activated=True)
            comp.generate(True)
            platforms.append(node)
            volumes.append(vol.get_actor_label())
            route_nodes.append({"id": node, "location_cm": [x, y, 50.0], "encounter_clear": True})

    # Straight connector lanes make the grid a real navigation scaffold.
    for ix, x in enumerate(GRID[:-1]):
        for iy, y in enumerate(GRID):
            mid = (x + GRID[ix + 1]) * 0.5
            _mesh_actor(eas, mesh, f"{PREFIX}LinkX_{ix}_{iy}", (mid, y, 50.0), (65.0, 3.0, 0.15), ["WP_PrimaryRoute", "GB_HumanScale", "WP_HeatmapAnchor"])
    for ix, x in enumerate(GRID):
        for iy, y in enumerate(GRID[:-1]):
            mid = (y + GRID[iy + 1]) * 0.5
            _mesh_actor(eas, mesh, f"{PREFIX}LinkY_{ix}_{iy}", (x, mid, 50.0), (3.0, 65.0, 0.15), ["WP_PrimaryRoute", "GB_HumanScale", "WP_HeatmapAnchor"])

    les.save_current_level()
    return {
        "level": level_key,
        "graph": graph_path,
        "style_id": STYLE_BY_LEVEL.get(level_key, "UNKNOWN"),
        "platforms": len(platforms),
        "pcg_volumes": len(volumes),
        "links": 12,
        "route_nodes": route_nodes,
        "navigation_configured": navigation_configured,
    }


def main() -> int:
    results = [deploy(level) for level in LEVELS]
    path = ROOT / "Saved" / "Audit" / "wp_walkable_grid_deploy.json"
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps({"results": results}, indent=2), encoding="utf-8")
    print(json.dumps(results, separators=(",", ":")))
    return 0 if all("error" not in result for result in results) else 1


if __name__ == "__main__":
    raise SystemExit(main())
