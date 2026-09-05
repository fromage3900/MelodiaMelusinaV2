"""Reusable Landscape contact tools for SeaAbove and future level passes.

Agents should call :func:`ground_static_mesh_manifest` through the Monolith
editor Python bridge.  The manifest format is one actor per line, for example::

    MyProp(StaticMeshActor_UAID_...): C:/.../actor.uasset

Only exact label + UAID matches are touched.  A downward visibility trace
ignoring all StaticMeshActors accepts only a Landscape hit.  Grounding moves
the actor vertically so its world bounds bottom contacts that hit, preserving
XY, rotation and scale.  Optional edge clamping is explicit and reported.
"""

import json
import os
import re
import unreal


_MANIFEST_RE = re.compile(r"^([^\(]+)\((StaticMeshActor_UAID_[^\)]+)\):")


def _vec(value):
    return [round(value.x, 3), round(value.y, 3), round(value.z, 3)]


def load_manifest_targets(manifest_path):
    """Return exact ``[{label, uaid}]`` entries from a placement manifest."""
    targets = []
    with open(manifest_path, "r", encoding="utf-8") as handle:
        for raw in handle:
            match = _MANIFEST_RE.match(raw.strip())
            if match:
                targets.append({"label": match.group(1), "uaid": match.group(2)})
    return targets


def _landscape_hit(world, start, end, static_actors):
    try:
        hits = unreal.SystemLibrary.line_trace_multi(
            world,
            start,
            end,
            unreal.TraceTypeQuery.ECC_VISIBILITY,
            True,
            static_actors,
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
        hit_actor = data.get("hit_actor")
        if hit_actor and hit_actor.get_class().get_name() == "Landscape":
            return data, None
    return None, "no_landscape_hit"


def _set_world_location(actor, location):
    """Set an actor transform through the editor subsystem so WP packages dirty."""
    actor.modify()
    transform = unreal.Transform(location, actor.get_actor_quat(), actor.get_actor_scale3d())
    subsystem = unreal.get_editor_subsystem(unreal.EditorActorSubsystem)
    if not subsystem.set_actor_transform(actor, transform):
        raise RuntimeError("EditorActorSubsystem.set_actor_transform failed for %s" % actor.get_path_name())
    # Keep this explicit for callers that use the helper outside the editor UI.
    actor.get_outermost().set_dirty_flag(True)


def ground_static_mesh_manifest(manifest_path, apply=False, clamp_outside_xy=False, report_path=None):
    """Audit or ground the static meshes named by *manifest_path*.

    ``apply=False`` is a read-only audit.  When applying, the current level is
    saved once as a convenience, but World Partition actor transforms are
    persisted only when the returned ``package_paths`` set is passed to the
    Monolith ``editor.save_packages`` action.  The return value is the summary
    dictionary; a JSON report is written when *report_path* is given.
    """
    world = unreal.EditorLevelLibrary.get_editor_world()
    actors = unreal.EditorLevelLibrary.get_all_level_actors()
    landscape = next((actor for actor in actors if actor.get_class().get_name() == "Landscape"), None)
    if landscape is None:
        raise RuntimeError("Landscape actor not found")

    static_actors = [actor for actor in actors if actor.get_class().get_name() == "StaticMeshActor"]
    targets = load_manifest_targets(manifest_path)
    landscape_origin, landscape_extent = landscape.get_actor_bounds(False, False)
    x0, x1 = landscape_origin.x - landscape_extent.x, landscape_origin.x + landscape_extent.x
    y0, y1 = landscape_origin.y - landscape_extent.y, landscape_origin.y + landscape_extent.y
    z0, z1 = landscape_origin.z - landscape_extent.z, landscape_origin.z + landscape_extent.z

    rows = []
    package_paths = set()
    missing = []
    applied_count = 0
    for target in targets:
        actor = next((candidate for candidate in static_actors
                      if candidate.get_actor_label() == target["label"]
                      and candidate.get_path_name().split(".")[-1] == target["uaid"]), None)
        if actor is None:
            missing.append(target)
            continue

        origin, extent = actor.get_actor_bounds(False, False)
        row = {
            "label": target["label"],
            "uaid": target["uaid"],
            "path": actor.get_path_name(),
            "location_before": _vec(actor.get_actor_location()),
            "bounds_origin_before": _vec(origin),
            "bounds_extent": _vec(extent),
            "package": actor.get_outermost().get_name(),
        }
        package_paths.add(actor.get_outermost().get_name())
        outside_xy = origin.x + extent.x < x0 or origin.x - extent.x > x1 or origin.y + extent.y < y0 or origin.y - extent.y > y1
        if outside_xy and clamp_outside_xy:
            clamped_x = min(max(origin.x, x0 + extent.x), x1 - extent.x)
            clamped_y = min(max(origin.y, y0 + extent.y), y1 - extent.y)
            dx, dy = clamped_x - origin.x, clamped_y - origin.y
            if apply:
                location = actor.get_actor_location()
                _set_world_location(actor, unreal.Vector(location.x + dx, location.y + dy, location.z))
                origin, extent = actor.get_actor_bounds(False, False)
                row["location_after_xy_clamp"] = _vec(actor.get_actor_location())
            else:
                origin = unreal.Vector(origin.x + dx, origin.y + dy, origin.z)
            row["xy_clamped"] = True
            outside_xy = False
        if outside_xy:
            row["status"] = "outside_landscape_xy"
            rows.append(row)
            continue

        start_z = max(origin.z + extent.z + 500.0, z1 + 500.0)
        end_z = z0 - 500.0
        hit, reason = _landscape_hit(
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
        if apply and abs(delta_z) >= 0.5:
            location = actor.get_actor_location()
            _set_world_location(actor, unreal.Vector(location.x, location.y, location.z + delta_z))
            row["status"] = "applied"
            row["applied_delta_z"] = round(delta_z, 3)
            applied_count += 1
        elif abs(delta_z) < 0.5:
            row["status"] = "already_grounded"
        rows.append(row)

    if apply:
        unreal.EditorLevelLibrary.save_current_level()

    deltas = [row["abs_delta_z"] for row in rows if "abs_delta_z" in row]
    summary = {
        "level": world.get_path_name() if world else None,
        "manifest": manifest_path,
        "apply": apply,
        "clamp_outside_xy": clamp_outside_xy,
        "manifest_entries": len(targets),
        "matched": len(targets) - len(missing),
        "missing": missing,
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
        "applied_count": applied_count,
        # World Partition stores level actors in external packages.  The
        # caller must pass this exact set to editor.save_packages; saving only
        # the map package does not persist these transforms.
        "package_paths": sorted(package_paths),
        "rows": rows,
    }
    if report_path:
        os.makedirs(os.path.dirname(report_path), exist_ok=True)
        with open(report_path, "w", encoding="utf-8") as handle:
            json.dump(summary, handle, indent=2)
    return summary
