# -*- coding: utf-8 -*-
"""Greybox roads via BP_InstanceOnSpline — ONLY after measure receipt.
Spawns/destroys WC_GreySpline_* and WC_GreyRoad_* only.
Mesh: SM_Greybox_Cube_1m. Ground-projects control points.
"""
from __future__ import annotations
import json, math
from datetime import datetime, timezone
from pathlib import Path
import unreal

EAL = unreal.EditorAssetLibrary
OUT = Path(unreal.Paths.project_saved_dir()) / "Audit" / "hero_corners_greybox_roads_2026-09-20.json"
BP_PATHS = [
    "/Game/Actor_BP/BP_InstanceOnSpline",
    "/Game/EnvSandbox/PCG/Universal/BP_InstanceOnSpline",
]
GREY = "/Game/EnvSandbox/Greybox_Kit/SM_Greybox_Cube_1m"
SPACING = 200.0

RUNS = [
    {
        "id": "WestMeadow",
        "pts": [(-3200.0, 1880.0), (-3200.0, 1400.0), (-3198.0, 742.0)],
        "z_hints": [1285.0, 900.0, 586.0],
    },
    {
        "id": "MeadowEast",
        "pts": [(-3198.0, 742.0), (-2300.0, 1100.0), (-1450.0, 1520.0)],
        "z_hints": [586.0, 1500.0, 2585.0],
    },
    {
        "id": "ApproachNorth",
        "pts": [(-1450.0, 1520.0), (-200.0, 1900.0), (900.0, 2300.0)],
        "z_hints": [2585.0, 1500.0, 960.0],
    },
]

DRESS_PREFIXES = ("WC_MA_Dress_", "WC_HeroDress_", "WC_PortfolioDress_", "WC_GreyRoad_", "WC_GreySpline_")


def _label(a):
    try:
        return a.get_actor_label() or ""
    except Exception:
        return ""


def _destroy_ours(svc):
    gone = []
    for a in list(svc.get_all_level_actors()):
        lab = _label(a)
        if lab.startswith("WC_GreyRoad_") or lab.startswith("WC_GreySpline_"):
            if svc.destroy_actor(a):
                gone.append(lab)
    return gone


def _is_bad_ground(lab):
    return any(lab.startswith(p) for p in DRESS_PREFIXES)


def _ground(world, x, y, z_hint, ignore):
    start = unreal.Vector(x, y, z_hint + 5000.0)
    end = unreal.Vector(x, y, z_hint - 8000.0)
    hit = unreal.SystemLibrary.line_trace_single(
        world, start, end,
        unreal.TraceTypeQuery.TRACE_TYPE_QUERY1, True, ignore,
        unreal.DrawDebugTrace.NONE, True,
        unreal.LinearColor.RED, unreal.LinearColor.GREEN, 0.0,
    )
    try:
        t = hit.to_tuple()
    except Exception:
        return None
    if not t or not t[0]:
        return None
    actor = t[9]
    lab = _label(actor) if actor else ""
    if _is_bad_ground(lab):
        return None
    if float(t[5].z) < 0.55:
        return None
    return t[4], lab


def _load_bp():
    for p in BP_PATHS:
        if EAL.does_asset_exist(p):
            cls = EAL.load_blueprint_class(p)
            if cls:
                return p, cls
    return None, None


def _set_spline_points(spline_comp, points):
    # Clear and add world-ish local points (actor at first point)
    n = spline_comp.get_number_of_spline_points()
    while n > 0:
        spline_comp.remove_spline_point(n - 1, True)
        n = spline_comp.get_number_of_spline_points()
    for i, p in enumerate(points):
        spline_comp.add_spline_point(p, unreal.SplineCoordinateSpace.LOCAL, False)
    spline_comp.update_spline()


def main():
    svc = unreal.get_editor_subsystem(unreal.EditorActorSubsystem)
    world = unreal.get_editor_subsystem(unreal.UnrealEditorSubsystem).get_editor_world()
    gone = _destroy_ours(svc)
    bp_path, bp_cls = _load_bp()
    grey = EAL.load_asset(GREY) if EAL.does_asset_exist(GREY) else None
    report = {
        "schema": "melodia.hero_corners_greybox_roads.v1",
        "generated_at": datetime.now(timezone.utc).isoformat(),
        "destroyed_prior": gone,
        "bp": bp_path,
        "grey_mesh": GREY if grey else None,
        "runs": {},
    }
    if not bp_cls or not grey:
        report["error"] = "missing BP_InstanceOnSpline or greybox mesh"
        OUT.write_text(json.dumps(report, indent=2), encoding="utf-8")
        print("GREY_ROAD_ERR " + json.dumps(report.get("error")))
        return 1

    ignore = []
    for run in RUNS:
        entry = {"points": [], "spawned": None, "skipped": None}
        world_pts = []
        for (x, y), zh in zip(run["pts"], run["z_hints"]):
            g = _ground(world, x, y, zh, ignore)
            if not g:
                entry["skipped"] = "no ground at %.0f,%.0f" % (x, y)
                break
            loc, lab = g
            world_pts.append(loc)
            entry["points"].append({"loc": [loc.x, loc.y, loc.z], "ground": lab})
        if entry.get("skipped") or len(world_pts) < 2:
            report["runs"][run["id"]] = entry
            continue

        origin = world_pts[0]
        actor = svc.spawn_actor_from_class(bp_cls, origin, unreal.Rotator(0, 0, 0))
        if not actor:
            entry["skipped"] = "spawn_failed"
            report["runs"][run["id"]] = entry
            continue
        name = "WC_GreyRoad_%s" % run["id"]
        actor.set_actor_label(name)
        try:
            actor.set_folder_path("HeroCorners/GreyRoads")
            actor.tags = ["Portfolio", "HeroCorner", "GreyRoad", "Greybox"]
        except Exception:
            pass

        # Prefer a SplineComponent on the BP; fall back to child
        splines = actor.get_components_by_class(unreal.SplineComponent) or []
        if not splines:
            entry["skipped"] = "no SplineComponent on BP"
            # leave actor for inspection
            entry["spawned"] = name
            report["runs"][run["id"]] = entry
            continue
        sc = splines[0]
        local_pts = [unreal.Vector(p.x - origin.x, p.y - origin.y, p.z - origin.z) for p in world_pts]
        _set_spline_points(sc, local_pts)

        # Best-effort: set common property names if present
        for prop, val in (
            ("Mesh", grey),
            ("StaticMesh", grey),
            ("InstanceMesh", grey),
            ("Spacing", SPACING),
            ("SpacingCm", SPACING),
            ("Gap", SPACING),
        ):
            try:
                actor.set_editor_property(prop, val)
            except Exception:
                pass
        try:
            actor.call_editor_construction_script()
        except Exception:
            pass

        # Measure resulting bounds
        try:
            origin_b, extent = actor.get_actor_bounds(False, True)
            entry["bounds_extent"] = [float(extent.x), float(extent.y), float(extent.z)]
            entry["length_approx"] = float(
                sum(
                    math.sqrt(
                        (world_pts[i].x - world_pts[i - 1].x) ** 2
                        + (world_pts[i].y - world_pts[i - 1].y) ** 2
                        + (world_pts[i].z - world_pts[i - 1].z) ** 2
                    )
                    for i in range(1, len(world_pts))
                )
            )
        except Exception:
            pass
        entry["spawned"] = name
        ignore.append(actor)
        report["runs"][run["id"]] = entry

    try:
        unreal.get_editor_subsystem(unreal.LevelEditorSubsystem).save_current_level()
        report["level_saved"] = True
    except Exception as e:
        report["level_saved"] = str(e)

    OUT.parent.mkdir(parents=True, exist_ok=True)
    OUT.write_text(json.dumps(report, indent=2, default=str), encoding="utf-8")
    print("GREY_ROAD " + json.dumps({k: v.get("spawned") or v.get("skipped") for k, v in report["runs"].items()}))
    unreal.log("GREY_ROAD wrote " + str(OUT))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
