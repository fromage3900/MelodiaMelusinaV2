# -*- coding: utf-8 -*-
"""Belvedere REAL walk path — hide floater junk, spawn one continuous grounded path.
Labels: hide WC_GreySpire_Helix_*; path WC_WalkPath_Belvedere_*; destroy prior WC_WalkPath_Belvedere_*.
"""
from __future__ import annotations
import json, math
from datetime import datetime, timezone
from pathlib import Path
import unreal

EAL = unreal.EditorAssetLibrary
OUT = Path(unreal.Paths.project_saved_dir()) / "Audit" / "walk_path_belvedere_2026-09-20.json"
GREY = "/Game/EnvSandbox/Greybox_Kit/SM_Greybox_Cube_1m"
SPACING = 140.0
PATH_WIDTH_SCALE = 2.0  # metres-ish on 1m cube -> 2m wide pads via scale XY

# Prefer walk toward live spire base
END = (160.0, 1600.0, 914.0)
# Candidate starts (first that grounds wins)
STARTS = [
    (-1335.0, 1505.0, 1230.0),  # escher walk westbank
    (-1450.0, 1520.0, 2585.0),  # eastbank pcg
    (-1950.0, 2070.0, 2905.0),  # eastbank cam-ish
    (420.0, 2960.0, 1120.0),    # landing
]

IGNORE_PREFIXES = (
    "WC_GreySpire_", "WC_GreyGrotto_", "WC_GreyRoad_", "WC_PhyloWalk_",
    "WC_WalkPath_", "WC_MA_Dress_", "WC_HeroDress_",
)


def _label(a):
    try:
        return a.get_actor_label() or ""
    except Exception:
        return ""


def _ignore(svc):
    return [a for a in svc.get_all_level_actors() if any(_label(a).startswith(p) for p in IGNORE_PREFIXES)]


def _good(lab):
    if not lab or any(lab.startswith(p) for p in IGNORE_PREFIXES):
        return False
    return any(t in lab for t in ("BrushifyIsland_", "Landscape", "SM_classic_arch", "Island", "Terrain"))


def _ground(world, x, y, z_hint, ignore):
    hit = unreal.SystemLibrary.line_trace_single(
        world,
        unreal.Vector(x, y, z_hint + 8000.0),
        unreal.Vector(x, y, z_hint - 12000.0),
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
    lab = _label(t[9]) if t[9] else ""
    if not _good(lab) or float(t[5].z) < 0.55:
        return None
    return t[4], lab


def _hide(a):
    try:
        a.set_actor_hidden_in_game(True)
        a.set_is_temporarily_hidden_in_editor(True)
        return True
    except Exception:
        return False


def _destroy_prior_path(svc):
    gone = []
    for a in list(svc.get_all_level_actors()):
        lab = _label(a)
        if lab.startswith("WC_WalkPath_Belvedere_"):
            if svc.destroy_actor(a):
                gone.append(lab)
    return gone


def _polyline(p0, p1, spacing):
    x0, y0, z0 = p0
    x1, y1, z1 = p1
    dist = math.hypot(x1 - x0, y1 - y0)
    n = max(2, int(dist / spacing) + 1)
    pts = []
    for i in range(n):
        t = i / (n - 1)
        pts.append((x0 + (x1 - x0) * t, y0 + (y1 - y0) * t, z0 + (z1 - z0) * t))
    return pts


def main():
    svc = unreal.get_editor_subsystem(unreal.EditorActorSubsystem)
    world = unreal.get_editor_subsystem(unreal.UnrealEditorSubsystem).get_editor_world()
    ignore = _ignore(svc)
    report = {
        "schema": "melodia.walk_path_belvedere.v1",
        "generated_at": datetime.now(timezone.utc).isoformat(),
        "hidden": [],
        "path": [],
        "skipped": [],
        "destroyed_prior_path": _destroy_prior_path(svc),
    }

    # 1) Hide ALL helix + floating roads/phylo/grotto walls that fail ground
    for a in list(svc.get_all_level_actors()):
        lab = _label(a)
        force = lab.startswith("WC_GreySpire_Helix")
        check = (
            lab.startswith("WC_GreyRoad_")
            or lab.startswith("WC_PhyloWalk_")
            or (lab.startswith("WC_GreyGrotto_") and "CryptFloor" not in lab and "Portal" not in lab)
        )
        if not force and not check:
            continue
        loc = a.get_actor_location()
        if force:
            if _hide(a):
                report["hidden"].append({"label": lab, "reason": "helix_air_climb"})
            continue
        g = _ground(world, loc.x, loc.y, loc.z, ignore)
        if not g or abs(float(loc.z) - float(g[0].z)) > 100.0:
            if _hide(a):
                report["hidden"].append({"label": lab, "reason": "floater_or_no_ground"})

    # 2) Pick start that grounds
    start = None
    for s in STARTS:
        g = _ground(world, s[0], s[1], s[2], ignore)
        if g:
            start = (g[0].x, g[0].y, g[0].z)
            report["start_ground"] = g[1]
            report["start_xyz"] = list(start)
            break
    end_g = _ground(world, END[0], END[1], END[2], ignore)
    if not end_g:
        report["error"] = "spire base has no ground"
        OUT.write_text(json.dumps(report, indent=2), encoding="utf-8")
        print("WALK_PATH_ERR no end ground")
        return 1
    end = (end_g[0].x, end_g[0].y, end_g[0].z)
    report["end_ground"] = end_g[1]
    report["end_xyz"] = list(end)

    if not start:
        report["error"] = "no grounded start among candidates"
        OUT.write_text(json.dumps(report, indent=2), encoding="utf-8")
        print("WALK_PATH_ERR no start")
        return 1

    mesh = EAL.load_asset(GREY) if EAL.does_asset_exist(GREY) else None
    if not mesh:
        report["error"] = "missing greybox mesh"
        OUT.write_text(json.dumps(report, indent=2), encoding="utf-8")
        return 1

    # Mid waypoint to avoid long chord through void: bend via (-600, 1600)
    mid_xy = ((start[0] + end[0]) * 0.5, (start[1] + end[1]) * 0.5)
    mid_g = _ground(world, mid_xy[0], mid_xy[1], (start[2] + end[2]) * 0.5, ignore)
    if mid_g:
        mid = (mid_g[0].x, mid_g[0].y, mid_g[0].z)
    else:
        # pull mid toward known island corridor
        mid_g = _ground(world, -600.0, 1600.0, 1500.0, ignore)
        mid = (mid_g[0].x, mid_g[0].y, mid_g[0].z) if mid_g else None

    segs = []
    if mid:
        segs += _polyline(start, mid, SPACING)
        segs += _polyline(mid, end, SPACING)[1:]
    else:
        segs = _polyline(start, end, SPACING)

    for i, (x, y, zhint) in enumerate(segs):
        g = _ground(world, x, y, zhint, ignore)
        if not g:
            report["skipped"].append({"i": i, "xy": [x, y], "reason": "no_ground"})
            continue
        loc, glab = g
        # pad slightly above
        spawn = unreal.Vector(loc.x, loc.y, loc.z + 12.0)
        actor = unreal.EditorLevelLibrary.spawn_actor_from_object(
            mesh, spawn, unreal.Rotator(0.0, 0.0, 0.0)
        )
        if not actor:
            report["skipped"].append({"i": i, "reason": "spawn_failed"})
            continue
        name = "WC_WalkPath_Belvedere_%02d" % i
        actor.set_actor_label(name)
        try:
            actor.set_actor_scale3d(unreal.Vector(PATH_WIDTH_SCALE, PATH_WIDTH_SCALE, 0.25))
            actor.set_folder_path("HeroCorners/WalkPath_Belvedere")
            actor.tags = ["Portfolio", "HeroCorner", "WalkPath", "Belvedere"]
        except Exception:
            pass
        ignore.append(actor)
        report["path"].append({"label": name, "loc": [spawn.x, spawn.y, spawn.z], "ground": glab})

    try:
        unreal.get_editor_subsystem(unreal.LevelEditorSubsystem).save_current_level()
        report["level_saved"] = True
    except Exception as e:
        report["level_saved"] = str(e)

    report["counts"] = {
        "hidden": len(report["hidden"]),
        "path_pads": len(report["path"]),
        "skipped": len(report["skipped"]),
    }
    # length approx
    report["path_length_xy_cm"] = 0.0
    for i in range(1, len(report["path"])):
        a, b = report["path"][i - 1]["loc"], report["path"][i]["loc"]
        report["path_length_xy_cm"] += math.hypot(b[0] - a[0], b[1] - a[1])

    OUT.parent.mkdir(parents=True, exist_ok=True)
    OUT.write_text(json.dumps(report, indent=2, default=str), encoding="utf-8")
    print("WALK_PATH " + json.dumps(report["counts"] | {"len_m": round(report["path_length_xy_cm"] / 100.0, 2)}))
    unreal.log("WALK_PATH wrote " + str(OUT))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
