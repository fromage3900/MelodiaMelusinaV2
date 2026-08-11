"""Record navigation evidence for the currently loaded WP level.

Run after an explicit full nav build and WP streaming settle. Unlike the
multi-level audit, this never reloads the world while sampling, avoiding the
false-zero caused by Recast tiles being discarded during the next load.
"""
from __future__ import annotations

import json
from datetime import datetime, timezone
from pathlib import Path

import unreal


ROOT = Path(__file__).resolve().parents[2]
REPORT = ROOT / "Saved" / "Audit" / "wp_navigation_verified_routes.json"
ROUTES = {
    "L_WP_SakuraDream": (0.0, 1200.0),
    "L_WP_SpaceCathedral": (0.0, 1600.0),
    "L_WP_BaroqueGrotto": (0.0, 1600.0),
    "L_WP_CosmicOrrery": (0.0, 400.0),
}


def main() -> int:
    world = unreal.get_editor_subsystem(unreal.UnrealEditorSubsystem).get_editor_world()
    level_name = world.get_name()
    if level_name not in ROUTES:
        unreal.log_error(f"[WPNavRecord] unsupported level: {level_name}")
        return 1
    end_x, end_y = ROUTES[level_name]
    start = unreal.Vector(0.0, 0.0, 0.0)
    end = unreal.Vector(end_x, end_y, 0.0)
    extent = unreal.Vector(500.0, 500.0, 1000.0)
    projected_start = unreal.NavigationSystemV1.project_point_to_navigation(
        world, start, None, None, extent
    )
    projected_end = unreal.NavigationSystemV1.project_point_to_navigation(
        world, end, None, None, extent
    )
    path = (
        unreal.NavigationSystemV1.find_path_to_location_synchronously(
            world, projected_start, projected_end
        )
        if projected_start and projected_end
        else None
    )
    actors = unreal.get_editor_subsystem(unreal.EditorActorSubsystem).get_all_level_actors() or []
    result = {
        "level": level_name,
        "recorded_at": datetime.now(timezone.utc).isoformat(),
        "terrain_actor_count": sum("Terrain" in a.get_actor_label() for a in actors),
        "pcg_volume_count": sum(a.get_actor_label().startswith("PCG_") for a in actors),
        "projected_start": [projected_start.x, projected_start.y, projected_start.z] if projected_start else None,
        "projected_end": [projected_end.x, projected_end.y, projected_end.z] if projected_end else None,
        "route_pass": bool(path and path.path_points),
        "path_point_count": len(path.path_points) if path else 0,
        "path_length_cm": path.get_path_length() if path else 0.0,
    }
    existing = json.loads(REPORT.read_text(encoding="utf-8")) if REPORT.exists() else {"levels": {}}
    existing.setdefault("levels", {})[level_name] = result
    existing["all_routes_pass"] = all(v.get("route_pass", False) for v in existing["levels"].values())
    REPORT.parent.mkdir(parents=True, exist_ok=True)
    REPORT.write_text(json.dumps(existing, indent=2), encoding="utf-8")
    unreal.log(f"[WPNavRecord] {level_name}: route_pass={result['route_pass']} -> {REPORT}")
    return 0 if result["route_pass"] else 1


if __name__ == "__main__":
    raise SystemExit(main())
