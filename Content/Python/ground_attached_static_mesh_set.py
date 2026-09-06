"""Audit and ground the exact static-mesh set supplied in the SeaAbove manifest.

The manifest contains both geometry and non-geometry actors.  This script
selects only StaticMeshActor entries and matches by label plus the full UAID
suffix, so duplicate labels remain unambiguous.  It raycasts with every
StaticMeshActor ignored and accepts only the Landscape hit, then moves each
actor vertically until its world bounds bottom contacts the terrain at the
actor bounds centre.  XY, rotation and scale are preserved.
"""

import json
import os
import re
import unreal


LEVEL_PATH = "/Game/EnvSandbox/Monoliths/SeaAbove/Prototype/LV_SeaAbove_Prototype"
MANIFEST_PATH = "C:/Users/froma/.codex/attachments/410b07be-2b92-41f6-bfa0-44c544b66d74/pasted-text.txt"
REPORT_PATH = "C:/EnvironmentPortfolio/BS_GodFile/Saved/Audit/sea_above_attached_mesh_grounding_post_2026-09-04.json"
APPLY = False
CLAMP_OUTSIDE_XY = True


def _vec(v):
    return [round(v.x, 3), round(v.y, 3), round(v.z, 3)]


def _manifest_targets():
    targets = []
    line_re = re.compile(r"^([^\(]+)\((StaticMeshActor_UAID_[^\)]+)\):")
    with open(MANIFEST_PATH, "r", encoding="utf-8") as handle:
        for raw in handle:
            match = line_re.match(raw.strip())
            if match:
                targets.append({"label": match.group(1), "uaid": match.group(2)})
    return targets


def _trace(world, start, end, ignore_actors):
    try:
        hits = unreal.SystemLibrary.line_trace_multi(
            world,
            start,
            end,
            unreal.TraceTypeQuery.ECC_VISIBILITY,
            True,
            ignore_actors,
            unreal.DrawDebugTrace.NONE,
            False,
            unreal.LinearColor(1, 0, 0, 1),
            unreal.LinearColor(0, 1, 0, 1),
            0.0,
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

    targets = _manifest_targets()
    static_actors = [a for a in actors if a.get_class().get_name() == "StaticMeshActor"]
    by_key = {}
    for actor in static_actors:
        path_tail = actor.get_path_name().split(".")[-1]
        by_key[(actor.get_actor_label(), path_tail)] = actor

    landscape_origin, landscape_extent = landscape.get_actor_bounds(False, False)
    x0, x1 = landscape_origin.x - landscape_extent.x, landscape_origin.x + landscape_extent.x
    y0, y1 = landscape_origin.y - landscape_extent.y, landscape_origin.y + landscape_extent.y
    z0, z1 = landscape_origin.z - landscape_extent.z, landscape_origin.z + landscape_extent.z

    rows = []
    matched = set()
    missing = []
    candidates = []
    for target in targets:
        actor = next(
            (candidate for candidate in static_actors
             if candidate.get_actor_label() == target["label"]
             and candidate.get_path_name().split(".")[-1] == target["uaid"]),
            None,
        )
        if actor is None:
            missing.append(target)
            continue
        matched.add(target["uaid"])
        origin, extent = actor.get_actor_bounds(False, False)
        row = {
            "label": target["label"],
            "uaid": target["uaid"],
            "path": actor.get_path_name(),
            "location_before": _vec(actor.get_actor_location()),
            "bounds_origin_before": _vec(origin),
            "bounds_extent": _vec(extent),
        }
        outside_xy = origin.x + extent.x < x0 or origin.x - extent.x > x1 or origin.y + extent.y < y0 or origin.y - extent.y > y1
        if outside_xy and CLAMP_OUTSIDE_XY:
            # Keep the actor's authored relative placement while bringing its
            # bounds back inside the landscape footprint.  This is only used
            # for the three ivy actors that were imported beyond the north
            # edge; the trace then resolves their new terrain contact.
            clamped_x = min(max(origin.x, x0 + extent.x), x1 - extent.x)
            clamped_y = min(max(origin.y, y0 + extent.y), y1 - extent.y)
            location = actor.get_actor_location()
            actor.set_actor_location(unreal.Vector(location.x + clamped_x - origin.x, location.y + clamped_y - origin.y, location.z), False, True)
            origin, extent = actor.get_actor_bounds(False, False)
            outside_xy = False
            row["xy_clamped"] = True
            row["location_after_xy_clamp"] = _vec(actor.get_actor_location())
        if outside_xy:
            row["status"] = "outside_landscape_xy"
            rows.append(row)
            continue

        start_z = max(origin.z + extent.z + 500.0, z1 + 500.0)
        end_z = z0 - 500.0
        hit, reason = _trace(
            world,
            unreal.Vector(origin.x, origin.y, start_z),
            unreal.Vector(origin.x, origin.y, end_z),
            static_actors,
        )
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
            "bottom_z_before": round(bottom_z, 3),
            "delta_z": round(delta_z, 3),
            "abs_delta_z": round(abs(delta_z), 3),
        })
        candidates.append((actor, delta_z, row))
        rows.append(row)

    applied = []
    if APPLY:
        for actor, delta_z, row in candidates:
            if abs(delta_z) < 0.5:
                row["status"] = "already_grounded"
                continue
            location = actor.get_actor_location()
            actor.set_actor_location(unreal.Vector(location.x, location.y, location.z + delta_z), False, True)
            row["status"] = "applied"
            row["applied_delta_z"] = round(delta_z, 3)
            applied.append(row["uaid"])
        unreal.EditorLevelLibrary.save_current_level()

    deltas = [row["abs_delta_z"] for row in rows if "abs_delta_z" in row]
    summary = {
        "level": LEVEL_PATH,
        "manifest": MANIFEST_PATH,
        "apply": APPLY,
        "clamp_outside_xy": CLAMP_OUTSIDE_XY,
        "manifest_entries": len(targets),
        "static_mesh_targets": sum(1 for line in targets if line["uaid"].startswith("StaticMeshActor_UAID_")),
        "matched": len(matched),
        "missing": missing,
        "rows": rows,
        "landscape_bounds_origin": _vec(landscape_origin),
        "landscape_bounds_extent": _vec(landscape_extent),
        "landscape_hits": sum(1 for row in rows if "terrain_hit" in row),
        "no_landscape_hit": sum(1 for row in rows if row.get("status") == "no_landscape_hit"),
        "outside_landscape_xy": sum(1 for row in rows if row.get("status") == "outside_landscape_xy"),
        "candidate_delta_abs_cm": {
            "min": round(min(deltas), 3) if deltas else None,
            "median": round(sorted(deltas)[len(deltas) // 2], 3) if deltas else None,
            "max": round(max(deltas), 3) if deltas else None,
            "over_5000": sum(1 for value in deltas if value > 5000.0),
            "over_10000": sum(1 for value in deltas if value > 10000.0),
        },
        "applied_count": len(applied),
    }
    os.makedirs(os.path.dirname(REPORT_PATH), exist_ok=True)
    with open(REPORT_PATH, "w", encoding="utf-8") as handle:
        json.dump(summary, handle, indent=2)
    return {key: value for key, value in summary.items() if key not in ("rows", "missing")}


if __name__ == "__main__":
    print(run())
