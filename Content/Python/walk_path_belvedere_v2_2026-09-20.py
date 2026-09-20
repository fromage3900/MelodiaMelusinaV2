# -*- coding: utf-8 -*-
"""Belvedere walk path v2 — island-hop + intentional bridges over void.
Destroys prior WC_WalkPath_Belvedere_*. Dense pads (100cm). Bridge pads where no ground.
Collision BlockAll on all pads. Keeps shaft/chamber. Does not touch lake/PCG/cams.
"""
from __future__ import annotations
import json, math
from datetime import datetime, timezone
from pathlib import Path
import unreal

EAL = unreal.EditorAssetLibrary
OUT = Path(unreal.Paths.project_saved_dir()) / "Audit" / "walk_path_belvedere_v2_2026-09-20.json"
GREY = "/Game/EnvSandbox/Greybox_Kit/SM_Greybox_Cube_1m"
SPACING = 100.0

# Island-hop then east to spire (from escher_walkable + live base)
WAYPOINTS = [
    (-1440.0, 1500.0, 582.0),   # BrushifyIsland_10
    (-1598.0, 1860.0, 586.0),   # Island_06
    (-1200.0, 1700.0, 580.0),   # corridor east
    (-800.0, 1650.0, 700.0),
    (-400.0, 1620.0, 800.0),
    (-100.0, 1610.0, 880.0),
    (160.0, 1600.0, 914.0),    # spire / classic arch
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


def _destroy_prior(svc):
    gone = []
    for a in list(svc.get_all_level_actors()):
        lab = _label(a)
        if lab.startswith("WC_WalkPath_Belvedere_"):
            if svc.destroy_actor(a):
                gone.append(lab)
    return gone


def _hide_helix(svc):
    n = 0
    for a in svc.get_all_level_actors():
        lab = _label(a)
        if lab.startswith("WC_GreySpire_Helix"):
            try:
                a.set_actor_hidden_in_game(True)
                a.set_is_temporarily_hidden_in_editor(True)
                n += 1
            except Exception:
                pass
    return n


def _seg(a, b, spacing):
    x0, y0, z0 = a
    x1, y1, z1 = b
    dist = math.hypot(x1 - x0, y1 - y0)
    n = max(2, int(dist / spacing) + 1)
    out = []
    for i in range(n):
        t = i / (n - 1)
        out.append((x0 + (x1 - x0) * t, y0 + (y1 - y0) * t, z0 + (z1 - z0) * t))
    return out


def _enable_collision(actor):
    try:
        for comp in actor.get_components_by_class(unreal.StaticMeshComponent) or []:
            comp.set_collision_enabled(unreal.CollisionEnabled.QUERY_AND_PHYSICS)
            comp.set_collision_profile_name("BlockAll")
    except Exception:
        pass


def main():
    svc = unreal.get_editor_subsystem(unreal.EditorActorSubsystem)
    world = unreal.get_editor_subsystem(unreal.UnrealEditorSubsystem).get_editor_world()
    ignore = _ignore(svc)
    mesh = EAL.load_asset(GREY) if EAL.does_asset_exist(GREY) else None
    report = {
        "schema": "melodia.walk_path_belvedere.v2",
        "generated_at": datetime.now(timezone.utc).isoformat(),
        "destroyed_prior": _destroy_prior(svc),
        "helix_hidden": _hide_helix(svc),
        "path": [],
        "bridges": [],
        "waypoints_resolved": [],
    }
    if not mesh:
        report["error"] = "no greybox"
        OUT.write_text(json.dumps(report, indent=2), encoding="utf-8")
        return 1

    # Resolve waypoints to ground where possible
    resolved = []
    for wp in WAYPOINTS:
        g = _ground(world, wp[0], wp[1], wp[2], ignore)
        if g:
            resolved.append((g[0].x, g[0].y, g[0].z, g[1], False))
            report["waypoints_resolved"].append({"xy": [wp[0], wp[1]], "ground": g[1], "bridge": False})
        else:
            resolved.append((wp[0], wp[1], wp[2], "bridge_lerp", True))
            report["waypoints_resolved"].append({"xy": [wp[0], wp[1]], "ground": None, "bridge": True})

    # Build dense polyline through resolved WPs
    pts = []
    for i in range(len(resolved) - 1):
        a = resolved[i][:3]
        b = resolved[i + 1][:3]
        chunk = _seg(a, b, SPACING)
        if i > 0:
            chunk = chunk[1:]
        pts.extend(chunk)

    last_ground_z = resolved[0][2]
    next_bridge_target_z = resolved[0][2]
    for i, (x, y, zhint) in enumerate(pts):
        g = _ground(world, x, y, zhint, ignore)
        is_bridge = False
        if g:
            loc, glab = g
            z = float(loc.z) + 14.0
            last_ground_z = float(loc.z)
            kind = "ground"
        else:
            # intentional bridge — lerp Z toward next grounded waypoint
            # find next non-bridge resolved ahead
            z = float(zhint) + 14.0
            glab = "BRIDGE_VOID"
            is_bridge = True
            kind = "bridge"
        spawn = unreal.Vector(x, y, z)
        actor = unreal.EditorLevelLibrary.spawn_actor_from_object(mesh, spawn, unreal.Rotator(0, 0, 0))
        if not actor:
            continue
        name = "WC_WalkPath_Belvedere_%s_%03d" % ("Br" if is_bridge else "Gd", i)
        actor.set_actor_label(name)
        try:
            # bridges a bit thicker for footing
            scz = 0.35 if is_bridge else 0.25
            actor.set_actor_scale3d(unreal.Vector(2.2, 2.2, scz))
            actor.set_folder_path("HeroCorners/WalkPath_Belvedere")
            actor.tags = ["Portfolio", "WalkPath", "Belvedere"] + (["Bridge"] if is_bridge else ["Grounded"])
        except Exception:
            pass
        _enable_collision(actor)
        ignore.append(actor)
        rec = {"label": name, "loc": [x, y, z], "ground": glab, "kind": kind}
        report["path"].append(rec)
        if is_bridge:
            report["bridges"].append(rec)

    # length
    length = 0.0
    for i in range(1, len(report["path"])):
        a, b = report["path"][i - 1]["loc"], report["path"][i]["loc"]
        length += math.hypot(b[0] - a[0], b[1] - a[1])
    report["path_length_xy_cm"] = length
    report["counts"] = {
        "pads": len(report["path"]),
        "bridges": len(report["bridges"]),
        "grounded": len(report["path"]) - len(report["bridges"]),
        "len_m": round(length / 100.0, 2),
    }

    try:
        unreal.get_editor_subsystem(unreal.LevelEditorSubsystem).save_current_level()
        report["level_saved"] = True
    except Exception as e:
        report["level_saved"] = str(e)

    OUT.parent.mkdir(parents=True, exist_ok=True)
    OUT.write_text(json.dumps(report, indent=2, default=str), encoding="utf-8")
    print("WALK_PATH_V2 " + json.dumps(report["counts"]))
    unreal.log("WALK_PATH_V2 " + json.dumps(report["counts"]))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
