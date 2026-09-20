# -*- coding: utf-8 -*-
"""Stage Melusina house rooms from locked SM_room_2 long-floor base.
Also ensures MelusinasHouse SM_corridor / SM_room1 foundation plates nearby.
Labels WC_HouseRoom_*. Destroy only those (+ optional WC_HouseBase_* we spawn).
Stay off WC_SpireRamp_*/lake/PCG/cams.
"""
from __future__ import annotations
import json, math
from datetime import datetime, timezone
from pathlib import Path
import unreal

EAL = unreal.EditorAssetLibrary
OUT = Path(unreal.Paths.project_saved_dir()) / "Audit" / "house_room_builder_stage_2026-09-20.json"

FLOOR_ATL = "/Game/EnvSandbox/Meshes/Atlantis/SM_ATL_Palace_FloorA"
ROOM1 = "/Game/_PROJECT/MelusinasHouse/SM_room1"
ROOM2 = "/Game/_PROJECT/MelusinasHouse/SM_room2"
ROOM2_ALT = "/Game/Melodia/_PROJECT/MelusinasHouse/SM_room2"
CORRIDOR = "/Game/_PROJECT/MelusinasHouse/SM_corridor"
CORRIDOR_ALT = "/Game/Melodia/_PROJECT/MelusinasHouse/SM_corridor"
WALL = "/Game/Melodia/_PROJECT/MelusinasHouse/SM_wallhi"
WALL_ALT = "/Game/_PROJECT/MelusinasHouse/SM_wallhi"
FLOOR_GB = "/Game/EnvSandbox/Greybox_Kit/SM_Greybox_Floor_4x4"

# Local offsets from SM_room_2 center (cm) — bud rooms around the long floor
ROOMS = [
    {"id": "OvalSalon", "dxy": (0.0, 0.0), "yaw": 0.0, "use_existing_room2": True},
    {"id": "BlueRoom", "dxy": (900.0, 400.0), "yaw": 20.0, "floor_scale": (1.6, 1.4, 1.0)},
    {"id": "WardrobeRotunda", "dxy": (-700.0, 500.0), "yaw": -25.0, "floor_scale": (1.4, 1.4, 1.0)},
    {"id": "ListeningStairLanding", "dxy": (200.0, -800.0), "yaw": 90.0, "floor_scale": (1.2, 2.0, 1.0)},
]

IGNORE = ("WC_HouseRoom_", "WC_HouseBase_", "WC_SpireRamp_", "WC_GreySpire_", "WC_WalkPath_")


def _lab(a):
    try:
        return a.get_actor_label() or ""
    except Exception:
        return ""


def _load(*paths):
    for p in paths:
        if p and EAL.does_asset_exist(p):
            return p, EAL.load_asset(p)
    return None, None


def _find_label(svc, name):
    for a in svc.get_all_level_actors():
        if _lab(a) == name:
            return a
    return None


def _destroy_ours(svc):
    gone = []
    for a in list(svc.get_all_level_actors()):
        lab = _lab(a)
        if lab.startswith("WC_HouseRoom_") or lab.startswith("WC_HouseBase_"):
            if svc.destroy_actor(a):
                gone.append(lab)
    return gone


def _ignore(svc):
    return [a for a in svc.get_all_level_actors() if any(_lab(a).startswith(p) for p in IGNORE)]


def _ground(world, x, y, z_hint, ignore):
    hit = unreal.SystemLibrary.line_trace_single(
        world,
        unreal.Vector(x, y, z_hint + 5000.0),
        unreal.Vector(x, y, z_hint - 8000.0),
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
    return t[4], _lab(t[9]) if t[9] else ""


def _spawn(mesh, loc, yaw, scale, label, folder, ignore):
    a = unreal.EditorLevelLibrary.spawn_actor_from_object(mesh, loc, unreal.Rotator(0.0, yaw, 0.0))
    if not a:
        return None
    a.set_actor_label(label)
    try:
        a.set_actor_scale3d(unreal.Vector(*scale))
        a.set_actor_rotation(unreal.Rotator(0.0, yaw, 0.0), False)
        a.set_folder_path(folder)
        a.tags = ["Portfolio", "MelusinaHouse", "HouseRoom", "RoomBuilder"]
    except Exception:
        pass
    ignore.append(a)
    return a


def main():
    svc = unreal.get_editor_subsystem(unreal.EditorActorSubsystem)
    world = unreal.get_editor_subsystem(unreal.UnrealEditorSubsystem).get_editor_world()
    ignore = _ignore(svc)
    destroyed = _destroy_ours(svc)

    base = _find_label(svc, "SM_room_2")
    report = {
        "schema": "melodia.house_room_builder_stage.v2_room2_lock",
        "generated_at": datetime.now(timezone.utc).isoformat(),
        "destroyed": destroyed,
        "locked_base": "SM_room_2",
        "rooms": {},
        "bases_spawned": [],
    }
    if not base:
        report["error"] = "SM_room_2 not found in level — abort"
        OUT.write_text(json.dumps(report, indent=2), encoding="utf-8")
        print("HOUSE_ROOM_ERR no SM_room_2")
        return 1

    bloc = base.get_actor_location()
    bx, by, bz = float(bloc.x), float(bloc.y), float(bloc.z)
    report["base_loc"] = [bx, by, bz]
    try:
        byaw = float(base.get_actor_rotation().yaw)
    except Exception:
        byaw = 0.0
    report["base_yaw"] = byaw

    # Optional additional foundation plates: corridor + room1 beside room2
    cpath, cmesh = _load(CORRIDOR, CORRIDOR_ALT)
    r1path, r1mesh = _load(ROOM1, ROOM2_ALT)
    fpath, fmesh = _load(FLOOR_ATL, FLOOR_GB)
    wpath, wmesh = _load(WALL, WALL_ALT)

    report["meshes"] = {"corridor": cpath, "room1": r1path, "floor": fpath, "wall": wpath}

    if cmesh:
        # corridor as guide spine off room2 +Y
        g = _ground(world, bx, by + 900.0, bz + 200.0, ignore) or _ground(world, bx, by + 900.0, bz, ignore)
        if g:
            loc, glab = g
            a = _spawn(cmesh, unreal.Vector(loc.x, loc.y, loc.z + 2.0), byaw, (1, 1, 1),
                       "WC_HouseBase_Corridor", "MelusinaHouse/Bases", ignore)
            if a:
                report["bases_spawned"].append({"label": "WC_HouseBase_Corridor", "ground": glab})

    if r1mesh:
        g = _ground(world, bx + 1100.0, by, bz + 200.0, ignore) or _ground(world, bx + 1100.0, by, bz, ignore)
        if g:
            loc, glab = g
            a = _spawn(r1mesh, unreal.Vector(loc.x, loc.y, loc.z + 2.0), byaw + 10.0, (1, 1, 1),
                       "WC_HouseBase_Room1", "MelusinaHouse/Bases", ignore)
            if a:
                report["bases_spawned"].append({"label": "WC_HouseBase_Room1", "ground": glab})

    # Tag existing room2 as locked base (don't destroy)
    try:
        tags = list(base.tags or [])
        for t in ("Portfolio", "MelusinaHouse", "HouseBase", "LockedLongFloor"):
            if t not in tags:
                tags.append(t)
        base.tags = tags
        report["base_tagged"] = True
    except Exception:
        report["base_tagged"] = False

    rad0 = math.radians(byaw)
    for room in ROOMS:
        rid = room["id"]
        entry = {"spawned": [], "skipped": None}
        dx, dy = room["dxy"]
        # rotate offset by base yaw
        x = bx + dx * math.cos(rad0) - dy * math.sin(rad0)
        y = by + dx * math.sin(rad0) + dy * math.cos(rad0)
        yaw = byaw + room["yaw"]

        if room.get("use_existing_room2"):
            entry["spawned"].append({"label": "SM_room_2", "role": "locked_long_floor", "loc": [bx, by, bz]})
            entry["note"] = "OvalSalon uses existing SM_room_2 as floor mass — no duplicate floor"
            # light wall accents only if wall mesh exists
            if wmesh:
                for i, (ox, oy) in enumerate(((0, 400), (0, -400), (500, 0), (-500, 0))):
                    wx = bx + ox * math.cos(rad0) - oy * math.sin(rad0)
                    wy = by + ox * math.sin(rad0) + oy * math.cos(rad0)
                    g = _ground(world, wx, wy, bz + 300.0, ignore)
                    if not g:
                        continue
                    loc, glab = g
                    lab = "WC_HouseRoom_%s_Wall_%d" % (rid, i)
                    a = _spawn(wmesh, unreal.Vector(loc.x, loc.y, loc.z + 160.0), yaw + (90 if i >= 2 else 0),
                               (1.0, 0.12, 1.4), lab, "MelusinaHouse/Rooms/%s" % rid, ignore)
                    if a:
                        entry["spawned"].append({"label": lab, "ground": glab})
            report["rooms"][rid] = entry
            continue

        g = _ground(world, x, y, bz + 400.0, ignore) or _ground(world, x, y, bz, ignore)
        if not g:
            entry["skipped"] = "no_ground"
            report["rooms"][rid] = entry
            continue
        loc, glab = g
        z = float(loc.z) + 4.0
        fs = room.get("floor_scale", (1.5, 1.5, 1.0))
        folder = "MelusinaHouse/Rooms/%s" % rid
        if fmesh:
            flab = "WC_HouseRoom_%s_Floor" % rid
            fa = _spawn(fmesh, unreal.Vector(x, y, z), yaw, fs, flab, folder, ignore)
            if fa:
                entry["spawned"].append({"label": flab, "ground": glab, "loc": [x, y, z]})
        if wmesh:
            hx, hy = 90.0 * fs[0], 90.0 * fs[1]
            for i, (ox, oy, addyaw) in enumerate(((0, hy, 0), (0, -hy, 0), (hx, 0, 90), (-hx, 0, 90))):
                wx = x + ox * math.cos(math.radians(yaw)) - oy * math.sin(math.radians(yaw))
                wy = y + ox * math.sin(math.radians(yaw)) + oy * math.cos(math.radians(yaw))
                wlab = "WC_HouseRoom_%s_Wall_%d" % (rid, i)
                wa = _spawn(wmesh, unreal.Vector(wx, wy, z + 150.0), yaw + addyaw,
                            (fs[0] * 0.45, 0.12, 1.3), wlab, folder, ignore)
                if wa:
                    entry["spawned"].append({"label": wlab})
        report["rooms"][rid] = entry

    try:
        unreal.get_editor_subsystem(unreal.LevelEditorSubsystem).save_current_level()
        report["level_saved"] = True
    except Exception as e:
        report["level_saved"] = str(e)

    total = sum(len(r.get("spawned") or []) for r in report["rooms"].values()) + len(report["bases_spawned"])
    report["counts"] = {"actors": total, "rooms": len(ROOMS), "extra_bases": len(report["bases_spawned"])}
    OUT.parent.mkdir(parents=True, exist_ok=True)
    OUT.write_text(json.dumps(report, indent=2, default=str), encoding="utf-8")
    print("HOUSE_ROOMS_V2 " + json.dumps(report["counts"]))
    unreal.log("HOUSE_ROOMS_V2 wrote " + str(OUT))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
