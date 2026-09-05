"""Audit, then optionally ground, every StaticMeshActor in SeaAbove.

The sweep uses UE's multi-line trace and accepts only the Landscape hit.  It
does not touch PCG instanced components, sky/ocean actors, or static meshes
whose XY bounds are outside the Landscape actor bounds.  Run with APPLY=False
for the evidence pass; the apply pass moves an actor by the terrain delta
measured at its bounds centre while preserving its XY and rotation.
"""

import json
import os
import unreal


LEVEL_PATH = "/Game/EnvSandbox/Monoliths/SeaAbove/Prototype/LV_SeaAbove_Prototype"
REPORT_PATH = "C:/EnvironmentPortfolio/BS_GodFile/Saved/Audit/sea_above_static_mesh_terrain_sweep_2026-09-04.json"
APPLY = True
MAX_APPLY_DELTA_CM = 5000.0


def _vec(v):
    return [round(v.x, 3), round(v.y, 3), round(v.z, 3)]


def _trace(world, start, end, ignore_actors):
    try:
        hits = unreal.SystemLibrary.line_trace_multi(
            world, start, end, unreal.TraceTypeQuery.ECC_VISIBILITY, True, ignore_actors,
            unreal.DrawDebugTrace.NONE, False, unreal.LinearColor(1, 0, 0, 1),
            unreal.LinearColor(0, 1, 0, 1), 0.0,
        )
    except Exception as exc:
        return None, "trace_exception:%s" % exc
    for hit in hits or []:
        data = hit.to_dict()
        actor = data.get("hit_actor")
        if actor and actor.get_class().get_name() == "Landscape":
            return data, None
    return None, "no_landscape_hit"


def run():
    world = unreal.EditorLevelLibrary.get_editor_world()
    if world is None or not world.get_path_name().startswith(LEVEL_PATH):
        unreal.EditorLevelLibrary.load_level(LEVEL_PATH)
        world = unreal.EditorLevelLibrary.get_editor_world()
    actors = unreal.EditorLevelLibrary.get_all_level_actors()
    landscape = next((a for a in actors if a.get_class().get_name() == "Landscape"), None)
    if landscape is None:
        raise RuntimeError("Landscape actor not found")
    landscape_origin, landscape_extent = landscape.get_actor_bounds(False, False)
    x0, x1 = landscape_origin.x - landscape_extent.x, landscape_origin.x + landscape_extent.x
    y0, y1 = landscape_origin.y - landscape_extent.y, landscape_origin.y + landscape_extent.y
    z0, z1 = landscape_origin.z - landscape_extent.z, landscape_origin.z + landscape_extent.z

    rows = []
    candidates = []
    skipped_outside = 0
    static_actors = [a for a in actors if a.get_class().get_name() == "StaticMeshActor"]
    for actor in static_actors:
        origin, extent = actor.get_actor_bounds(False, False)
        if origin.x + extent.x < x0 or origin.x - extent.x > x1 or origin.y + extent.y < y0 or origin.y - extent.y > y1:
            skipped_outside += 1
            continue
        start_z = max(origin.z + extent.z + 500.0, z1 + 500.0)
        end_z = z0 - 500.0
        # Ignore all static meshes so an elevated prop cannot occlude the
        # landscape hit behind it.  PCG ISM components are not in this list;
        # their graph already owns terrain projection and they are never moved
        # by this actor sweep.
        hit, reason = _trace(
            world,
            unreal.Vector(origin.x, origin.y, start_z),
            unreal.Vector(origin.x, origin.y, end_z),
            static_actors,
        )
        row = {
            "label": actor.get_actor_label(),
            "path": actor.get_path_name(),
            "location": _vec(actor.get_actor_location()),
            "bounds_origin": _vec(origin),
            "bounds_extent": _vec(extent),
            "trace_start_z": round(start_z, 3),
            "trace_end_z": round(end_z, 3),
        }
        if hit is None:
            row["status"] = reason
            rows.append(row)
            continue
        terrain_z = hit["impact_point"].z
        bottom_z = origin.z - extent.z
        delta_z = terrain_z - bottom_z
        row.update({
            "status": "candidate",
            "terrain_hit": _vec(hit["impact_point"]),
            "terrain_normal": _vec(hit["impact_normal"]),
            "bottom_z": round(bottom_z, 3),
            "delta_z": round(delta_z, 3),
            "abs_delta_z": round(abs(delta_z), 3),
        })
        candidates.append((actor, delta_z, row))
        rows.append(row)

    applied = []
    if APPLY:
        for actor, delta_z, row in candidates:
            # Large deltas identify authored floating/island set pieces or
            # imported strata that need their own design decision.  They stay
            # in the audit with exact terrain readings and are deliberately
            # left in place by this grounding pass.
            if abs(delta_z) > MAX_APPLY_DELTA_CM:
                row["status"] = "flagged_large_delta"
                continue
            if abs(delta_z) < 0.5:
                row["status"] = "already_grounded"
                continue
            location = actor.get_actor_location()
            actor.set_actor_location(unreal.Vector(location.x, location.y, location.z + delta_z), False, True)
            row["status"] = "applied"
            row["applied_delta_z"] = round(delta_z, 3)
            applied.append(row["label"])
        unreal.EditorLevelLibrary.save_current_level()

    deltas = [abs(row["delta_z"]) for row in rows if row.get("status") == "candidate"]
    summary = {
        "level": LEVEL_PATH,
        "apply": APPLY,
        "max_apply_delta_cm": MAX_APPLY_DELTA_CM,
        "landscape_bounds_origin": _vec(landscape_origin),
        "landscape_bounds_extent": _vec(landscape_extent),
        "static_mesh_actors": len(static_actors),
        "inside_landscape_xy": len(rows),
        "skipped_outside_landscape_xy": skipped_outside,
        "landscape_hits": len(candidates),
        "no_landscape_hit": sum(1 for row in rows if row.get("status") == "no_landscape_hit"),
        "trace_exceptions": sum(1 for row in rows if str(row.get("status", "")).startswith("trace_exception")),
        "candidate_delta_abs_cm": {
            "min": round(min(deltas), 3) if deltas else None,
            "median": round(sorted(deltas)[len(deltas) // 2], 3) if deltas else None,
            "max": round(max(deltas), 3) if deltas else None,
            "over_5000": sum(1 for d in deltas if d > 5000.0),
            "over_10000": sum(1 for d in deltas if d > 10000.0),
        },
        "applied_count": len(applied),
        "flagged_large_delta_count": sum(1 for row in rows if row.get("status") == "flagged_large_delta"),
        "rows": rows,
    }
    os.makedirs(os.path.dirname(REPORT_PATH), exist_ok=True)
    with open(REPORT_PATH, "w", encoding="utf-8") as handle:
        json.dump(summary, handle, indent=2)
    return {k: v for k, v in summary.items() if k != "rows"}


if __name__ == "__main__":
    print(run())
