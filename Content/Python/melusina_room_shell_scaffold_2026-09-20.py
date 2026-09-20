# -*- coding: utf-8 -*-
"""Scaffold MelusinaRoomShell — parametric size-editable room (floor grid + edge walls + door sockets).
Reads Saved/Audit/melusina_room_shell_<ShellId>_params.json OR defaults SalonA.
Labels WC_HouseRoomShell_<ShellId>_*. Destroy-only those. Pitch/roll 0.
"""
from __future__ import annotations
import json, math
from datetime import datetime, timezone
from pathlib import Path
import unreal

EAL = unreal.EditorAssetLibrary
SAVED = Path(unreal.Paths.project_saved_dir()) / "Audit"
OUT = SAVED / "melusina_room_shell_scaffold_2026-09-20.json"

FLOOR_PATHS = (
    "/Game/EnvSandbox/Meshes/Atlantis/SM_ATL_Palace_FloorA",
    "/Game/EnvSandbox/Greybox_Kit/SM_Greybox_Floor_4x4",
)
WALL_PATHS = (
    "/Game/Melodia/_PROJECT/MelusinasHouse/SM_wallhi",
    "/Game/_PROJECT/MelusinasHouse/SM_wallhi",
)

DEFAULTS = {
    "ShellId": "SalonA",
    "AnchorLabel": "SM_room_2",
    "Width_cm": 1200.0,
    "Depth_cm": 1000.0,
    "Height_cm": 350.0,
    "WallThickness_cm": 20.0,
    "ModuleSize_cm": 400.0,
    "DoorWidth_cm": 120.0,
    "Doors": {"N": True, "E": True, "S": False, "W": False},
    "Yaw_deg": None,
    "OffsetFromAnchor_cm": [0.0, 0.0, 0.0],
}


def _lab(a):
    try:
        return a.get_actor_label() or ""
    except Exception:
        return ""


def _load_paths(paths):
    for p in paths:
        if EAL.does_asset_exist(p):
            return p, EAL.load_asset(p)
    return None, None


def _find(svc, name):
    for a in svc.get_all_level_actors():
        if _lab(a) == name:
            return a
    return None


def _destroy_shell(svc, shell_id):
    prefix = "WC_HouseRoomShell_%s_" % shell_id
    gone = []
    for a in list(svc.get_all_level_actors()):
        lab = _lab(a)
        if lab.startswith(prefix):
            if svc.destroy_actor(a):
                gone.append(lab)
    return gone


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
    return float(t[4].z), _lab(t[9]) if t[9] else ""


def _spawn(mesh, loc, yaw, scale, label, folder, ignore, tags):
    a = unreal.EditorLevelLibrary.spawn_actor_from_object(mesh, loc, unreal.Rotator(0.0, yaw, 0.0))
    if not a:
        return None
    a.set_actor_label(label)
    try:
        a.set_actor_scale3d(unreal.Vector(*scale))
        a.set_actor_rotation(unreal.Rotator(0.0, yaw, 0.0), False)
        a.set_folder_path(folder)
        a.tags = tags
    except Exception:
        pass
    ignore.append(a)
    return a


def _spawn_socket(svc, loc, yaw, label, folder, ignore):
    # empty actor as socket marker
    try:
        a = svc.spawn_actor_from_class(unreal.Actor, loc, unreal.Rotator(0.0, yaw, 0.0))
    except Exception:
        a = unreal.EditorLevelLibrary.spawn_actor_from_class(unreal.Actor, loc, unreal.Rotator(0.0, yaw, 0.0))
    if not a:
        return None
    a.set_actor_label(label)
    try:
        a.set_folder_path(folder)
        a.tags = ["Portfolio", "MelusinaHouse", "RoomShell", "DoorSocket"]
    except Exception:
        pass
    ignore.append(a)
    return a


def main():
    # load params
    params = dict(DEFAULTS)
    # allow override file
    for cand in (
        SAVED / "melusina_room_shell_SalonA_params.json",
        SAVED / "melusina_room_shell_params.json",
    ):
        if cand.exists():
            params.update(json.loads(cand.read_text(encoding="utf-8")))
            params["_params_file"] = str(cand)
            break

    shell_id = params["ShellId"]
    svc = unreal.get_editor_subsystem(unreal.EditorActorSubsystem)
    world = unreal.get_editor_subsystem(unreal.UnrealEditorSubsystem).get_editor_world()
    ignore = [a for a in svc.get_all_level_actors() if _lab(a).startswith("WC_HouseRoomShell_")]
    gone = _destroy_shell(svc, shell_id)

    fp, floor = _load_paths(FLOOR_PATHS)
    wp, wall = _load_paths(WALL_PATHS)
    report = {
        "schema": "melodia.melusina_room_shell_scaffold.v1",
        "generated_at": datetime.now(timezone.utc).isoformat(),
        "params": {k: v for k, v in params.items() if not k.startswith("_")},
        "destroyed": gone,
        "meshes": {"floor": fp, "wall": wp},
        "spawned": [],
        "sockets": [],
    }
    if not floor or not wall:
        report["error"] = "missing floor or wall mesh"
        OUT.write_text(json.dumps(report, indent=2), encoding="utf-8")
        print("SHELL_ERR missing mesh")
        return 1

    anchor = _find(svc, params.get("AnchorLabel") or "SM_room_2")
    if not anchor:
        report["error"] = "anchor not found"
        OUT.write_text(json.dumps(report, indent=2), encoding="utf-8")
        print("SHELL_ERR no anchor")
        return 1

    aloc = anchor.get_actor_location()
    try:
        ayaw = float(anchor.get_actor_rotation().yaw) if params.get("Yaw_deg") is None else float(params["Yaw_deg"])
    except Exception:
        ayaw = float(params["Yaw_deg"] or 0.0)
    if params.get("Yaw_deg") is not None:
        ayaw = float(params["Yaw_deg"])

    ox, oy, oz = params.get("OffsetFromAnchor_cm") or [0, 0, 0]
    rad = math.radians(ayaw)
    cx = float(aloc.x) + ox * math.cos(rad) - oy * math.sin(rad)
    cy = float(aloc.y) + ox * math.sin(rad) + oy * math.cos(rad)
    gz, glab = _ground(world, cx, cy, float(aloc.z) + 500.0, ignore) or (float(aloc.z), "anchor_z")
    cz = gz + 2.0 + oz

    W = float(params["Width_cm"])
    D = float(params["Depth_cm"])
    H = float(params["Height_cm"])
    M = float(params["ModuleSize_cm"])
    thick = float(params["WallThickness_cm"])
    door_w = float(params["DoorWidth_cm"])
    doors = params.get("Doors") or {}
    folder = "MelusinaHouse/RoomShells/%s" % shell_id
    tags = ["Portfolio", "MelusinaHouse", "RoomShell", "SizeEditable"]

    # Floor grid — tile count from interior size / module
    nx = max(1, int(round(W / M)))
    ny = max(1, int(round(D / M)))
    # scale floor mesh to module (assume native ~400 if Atlantis unknown — use M/400)
    fscale = M / 400.0
    origin_x = cx - (nx - 1) * M * 0.5
    origin_y = cy - (ny - 1) * M * 0.5
    fi = 0
    for iy in range(ny):
        for ix in range(nx):
            x = origin_x + ix * M
            y = origin_y + iy * M
            # rotate into shell yaw
            lx = cx + (x - cx) * math.cos(rad) - (y - cy) * math.sin(rad)
            ly = cy + (x - cx) * math.sin(rad) + (y - cy) * math.cos(rad)
            lab = "WC_HouseRoomShell_%s_Floor_%02d" % (shell_id, fi)
            a = _spawn(floor, unreal.Vector(lx, ly, cz), ayaw, (fscale, fscale, 1.0), lab, folder, ignore, tags)
            if a:
                report["spawned"].append({"label": lab, "kind": "floor"})
            fi += 1

    # Perimeter walls — segments along each edge, skip door bay
    def wall_run(side, length, outward_yaw):
        nseg = max(1, int(round(length / M)))
        segs = []
        for i in range(nseg):
            t = (i + 0.5) / nseg - 0.5  # -0.5..0.5 along edge
            segs.append((t * length, i))
        return segs, nseg

    # Local edges: N=+Y, S=-Y, E=+X, W=-X
    edges = [
        ("N", 0.0, D * 0.5, W, ayaw + 0.0),
        ("S", 0.0, -D * 0.5, W, ayaw + 180.0),
        ("E", W * 0.5, 0.0, D, ayaw + 90.0),
        ("W", -W * 0.5, 0.0, D, ayaw - 90.0),
    ]
    # wall scale: length along edge uses module; thickness; height
    # Melusina wallhi unknown native — approximate scale so height ~ H
    wall_z_scale = H / 300.0
    wall_y_scale = thick / 20.0
    wi = 0
    for side, lx, ly, length, wyaw in edges:
        nseg = max(1, int(round(length / M)))
        for i in range(nseg):
            # skip middle segment if door on this side
            mid = (nseg - 1) / 2.0
            if doors.get(side) and nseg >= 2 and abs(i - mid) < 0.6:
                continue
            along = ((i + 0.5) / nseg - 0.5) * length
            if side in ("N", "S"):
                local_x, local_y = along, ly
            else:
                local_x, local_y = lx, along
            wx = cx + local_x * math.cos(rad) - local_y * math.sin(rad)
            wy = cy + local_x * math.sin(rad) + local_y * math.cos(rad)
            lab = "WC_HouseRoomShell_%s_Wall_%s_%02d" % (shell_id, side, i)
            # length scale along wall: module / 400
            wscale = (M / 400.0, wall_y_scale, wall_z_scale)
            a = _spawn(
                wall,
                unreal.Vector(wx, wy, cz + H * 0.5),
                wyaw,
                wscale,
                lab,
                folder,
                ignore,
                tags + ["Wall", side],
            )
            if a:
                report["spawned"].append({"label": lab, "kind": "wall", "side": side})
            wi += 1

    # Door sockets
    socket_defs = {
        "N": (0.0, D * 0.5, ayaw),
        "S": (0.0, -D * 0.5, ayaw + 180.0),
        "E": (W * 0.5, 0.0, ayaw + 90.0),
        "W": (-W * 0.5, 0.0, ayaw - 90.0),
    }
    for side, (lx, ly, syaw) in socket_defs.items():
        if not doors.get(side):
            continue
        sx = cx + lx * math.cos(rad) - ly * math.sin(rad)
        sy = cy + lx * math.sin(rad) + ly * math.cos(rad)
        lab = "WC_HouseRoomShell_%s_Socket_%s" % (shell_id, side)
        if _spawn_socket(svc, unreal.Vector(sx, sy, cz + 10.0), syaw, lab, folder, ignore):
            report["sockets"].append({"label": lab, "side": side, "loc": [sx, sy, cz + 10.0]})

    try:
        unreal.get_editor_subsystem(unreal.LevelEditorSubsystem).save_current_level()
        report["level_saved"] = True
    except Exception as e:
        report["level_saved"] = str(e)

    report["center"] = [cx, cy, cz]
    report["ground"] = glab
    report["grid"] = {"nx": nx, "ny": ny, "module": M}
    report["counts"] = {
        "floors": sum(1 for s in report["spawned"] if s["kind"] == "floor"),
        "walls": sum(1 for s in report["spawned"] if s["kind"] == "wall"),
        "sockets": len(report["sockets"]),
    }
    OUT.write_text(json.dumps(report, indent=2, default=str), encoding="utf-8")
    print("ROOM_SHELL " + json.dumps({"ShellId": shell_id, **report["counts"], "W": W, "D": D, "H": H}))
    unreal.log("ROOM_SHELL wrote " + str(OUT))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
