"""Editor-side navigation probe for the four World Partition greyboxes.

The probe samples each verified PCG volume center, projects it to the current
navmesh, and checks a simple sequential route through those samples. It is a
route sanity check, not a substitute for a capsule sweep or a PIE traversal.
"""
from __future__ import annotations

import json
import time
from datetime import datetime, timezone
from pathlib import Path

import unreal


ROOT = Path(__file__).resolve().parents[2]
REPORT = ROOT / "Saved" / "Audit" / "wp_navigation_probe.json"
LEVELS = [
    "/Game/EnvSandbox/Environments/WP/L_WP_SakuraDream",
    "/Game/EnvSandbox/Environments/WP/L_WP_SpaceCathedral",
    "/Game/EnvSandbox/Environments/WP/L_WP_BaroqueGrotto",
    "/Game/EnvSandbox/Environments/WP/L_WP_CosmicOrrery",
]


def _project(world, point):
    return unreal.NavigationSystemV1.project_point_to_navigation(
        world, point, None, None, unreal.Vector(500.0, 500.0, 1000.0)
    )


def _vec(point):
    return {"x": point.x, "y": point.y, "z": point.z}


def audit_level(path: str) -> dict:
    level_editor = unreal.get_editor_subsystem(unreal.LevelEditorSubsystem)
    level_editor.load_level(path)
    world = unreal.get_editor_subsystem(unreal.UnrealEditorSubsystem).get_editor_world()
    # Loading a WP map can leave the editor nav data stale until an explicit
    # rebuild. This is a read/verify pass; it does not save the level.
    unreal.SystemLibrary.execute_console_command(world, "RebuildNavigation")
    # WP actor streaming and Recast tile creation complete asynchronously even
    # after the console command returns. Give the editor a short settle window
    # before sampling; otherwise this probe reports a false zero.
    time.sleep(3.0)
    actors = unreal.get_editor_subsystem(unreal.EditorActorSubsystem).get_all_level_actors() or []
    nav_bounds = [a for a in actors if a.get_class().get_name() == "NavMeshBoundsVolume"]
    recast = [a for a in actors if a.get_class().get_name() == "RecastNavMesh"]
    terrain_actors = [
        a for a in actors
        if "Terrain" in a.get_actor_label() or "Terrain" in a.get_class().get_name()
    ]
    volumes = sorted(
        [a for a in actors if a.get_actor_label().startswith("PCG_")],
        key=lambda actor: actor.get_actor_label(),
    )
    samples = []
    for actor in volumes:
        source = actor.get_actor_location()
        projected = _project(world, source)
        samples.append({
            "label": actor.get_actor_label(),
            "source": _vec(source),
            "projected": _vec(projected) if projected else None,
            "projected_to_nav": projected is not None,
        })

    route_links = []
    for start, end in zip(samples, samples[1:]):
        if not start["projected"] or not end["projected"]:
            route_links.append({"from": start["label"], "to": end["label"], "reachable": False})
            continue
        nav_path = unreal.NavigationSystemV1.find_path_to_location_synchronously(
            world,
            unreal.Vector(**start["projected"]),
            unreal.Vector(**end["projected"]),
        )
        # UE 5.8 exposes NavigationPath points as a property.
        points = list(nav_path.path_points or []) if nav_path else []
        route_links.append({
            "from": start["label"],
            "to": end["label"],
            "reachable": bool(points),
            "path_point_count": len(points),
            "path_length_cm": float(nav_path.get_path_length()) if nav_path else 0.0,
        })

    return {
        "level": path,
        # The Python World wrapper does not expose WorldPartition as a
        # property in UE 5.8; the level family is already verified separately.
        "world_partition": "/WP/" in path,
        "nav_bounds_count": len(nav_bounds),
        "recast_navmesh_count": len(recast),
        "terrain_actor_count": len(terrain_actors),
        "terrain_actor_labels": [a.get_actor_label() for a in terrain_actors],
        "volume_count": len(volumes),
        "samples": samples,
        "route_links": route_links,
        "nav_projection_pass": bool(samples) and all(s["projected_to_nav"] for s in samples),
        "sequential_route_pass": bool(route_links) and all(r["reachable"] for r in route_links),
        "capsule_clearance_evaluated": False,
        "manual_gate": "PIE capsule traversal and camera readability still required",
    }


def main() -> int:
    results = [audit_level(path) for path in LEVELS]
    report = {
        "generated_at": datetime.now(timezone.utc).isoformat(),
        "levels": results,
        "all_nav_projection_pass": all(r["nav_projection_pass"] for r in results),
        "all_sequential_route_pass": all(r["sequential_route_pass"] for r in results),
        "capsule_clearance_evaluated": False,
    }
    REPORT.parent.mkdir(parents=True, exist_ok=True)
    REPORT.write_text(json.dumps(report, indent=2), encoding="utf-8")
    unreal.log(f"[WPNavAudit] wrote {REPORT}")
    return 0 if report["all_nav_projection_pass"] else 1


if __name__ == "__main__":
    raise SystemExit(main())
