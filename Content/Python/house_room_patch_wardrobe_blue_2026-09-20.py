# -*- coding: utf-8 -*-
"""Patch: re-seat BlueRoom + place WardrobeRotunda near bed/wardrobe anchors.
Destroys only WC_HouseRoom_BlueRoom_* and WC_HouseRoom_WardrobeRotunda_*.
Prefer ground labels: BrushifyIsland_*, SM_classic_arch_*, Melusina, SM_room — reject Phylo/Grey/Spire.
"""
from __future__ import annotations
import json, math
from datetime import datetime, timezone
from pathlib import Path
import unreal

EAL = unreal.EditorAssetLibrary
OUT = Path(unreal.Paths.project_saved_dir()) / "Audit" / "house_room_patch_wardrobe_blue_2026-09-20.json"
FLOOR = "/Game/EnvSandbox/Meshes/Atlantis/SM_ATL_Palace_FloorA"
FLOOR_FB = "/Game/EnvSandbox/Greybox_Kit/SM_Greybox_Floor_4x4"
WALL = "/Game/Melodia/_PROJECT/MelusinasHouse/SM_wallhi"
WALL_FB = "/Game/_PROJECT/MelusinasHouse/SM_wallhi"

GOOD = ("BrushifyIsland_", "SM_classic_arch", "Melusina", "SM_room", "Landscape", "House", "arch")
BAD = ("Phylo", "WC_Phylo", "WC_Grey", "WC_Spire", "WC_Walk", "WC_HouseRoom_")


def _lab(a):
    try:
        return a.get_actor_label() or ""
    except Exception:
        return ""


def _load(*paths):
    for p in paths:
        if EAL.does_asset_exist(p):
            return p, EAL.load_asset(p)
    return None, None


def _good(lab):
    if not lab or any(b in lab for b in BAD):
        return False
    return any(g in lab for g in GOOD)


def _ignore(svc):
    return [a for a in svc.get_all_level_actors()
            if _lab(a).startswith(("WC_HouseRoom_", "WC_HouseBase_", "WC_SpireRamp_", "WC_PhyloWalk_", "WC_Grey"))]


def _ground(world, x, y, z_hint, ignore):
    for z0 in (z_hint + 4000, z_hint + 1500, z_hint + 800, 500.0, -100.0):
        hit = unreal.SystemLibrary.line_trace_single(
            world,
            unreal.Vector(x, y, z0),
            unreal.Vector(x, y, z0 - 9000.0),
            unreal.TraceTypeQuery.TRACE_TYPE_QUERY1, True, ignore,
            unreal.DrawDebugTrace.NONE, True,
            unreal.LinearColor.RED, unreal.LinearColor.GREEN, 0.0,
        )
        try:
            t = hit.to_tuple()
        except Exception:
            continue
        if not t or not t[0]:
            continue
        lab = _lab(t[9]) if t[9] else ""
        if _good(lab) and float(t[5].z) >= 0.5:
            return t[4], lab
    return None


def _destroy_prefix(svc, prefixes):
    gone = []
    for a in list(svc.get_all_level_actors()):
        lab = _lab(a)
        if any(lab.startswith(p) for p in prefixes):
            if svc.destroy_actor(a):
                gone.append(lab)
    return gone


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


def _room(world, ignore, floor, wall, rid, x, y, z_hint, yaw, fs):
    entry = {"spawned": [], "skipped": None, "xy": [x, y]}
    g = _ground(world, x, y, z_hint, ignore)
    if not g:
        # spiral search
        for rad in (150, 300, 450, 600, 800):
            for k in range(8):
                ang = k * (math.pi / 4)
                g = _ground(world, x + math.cos(ang) * rad, y + math.sin(ang) * rad, z_hint, ignore)
                if g:
                    x, y = float(g[0].x), float(g[0].y)
                    break
            if g:
                break
    if not g:
        entry["skipped"] = "no_good_ground"
        return entry
    loc, glab = g
    z = float(loc.z) + 4.0
    folder = "MelusinaHouse/Rooms/%s" % rid
    if floor:
        flab = "WC_HouseRoom_%s_Floor" % rid
        if _spawn(floor, unreal.Vector(x, y, z), yaw, fs, flab, folder, ignore):
            entry["spawned"].append({"label": flab, "ground": glab, "loc": [x, y, z]})
    if wall:
        hx, hy = 90.0 * fs[0], 90.0 * fs[1]
        for i, (ox, oy, ay) in enumerate(((0, hy, 0), (0, -hy, 0), (hx, 0, 90), (-hx, 0, 90))):
            wx = x + ox * math.cos(math.radians(yaw)) - oy * math.sin(math.radians(yaw))
            wy = y + ox * math.sin(math.radians(yaw)) + oy * math.cos(math.radians(yaw))
            wlab = "WC_HouseRoom_%s_Wall_%d" % (rid, i)
            if _spawn(wall, unreal.Vector(wx, wy, z + 150.0), yaw + ay, (fs[0] * 0.45, 0.12, 1.3), wlab, folder, ignore):
                entry["spawned"].append({"label": wlab})
    return entry


def main():
    svc = unreal.get_editor_subsystem(unreal.EditorActorSubsystem)
    world = unreal.get_editor_subsystem(unreal.UnrealEditorSubsystem).get_editor_world()
    ignore = _ignore(svc)
    gone = _destroy_prefix(svc, ("WC_HouseRoom_BlueRoom_", "WC_HouseRoom_WardrobeRotunda_"))
    fp, floor = _load(FLOOR, FLOOR_FB)
    wp, wall = _load(WALL, WALL_FB)

    # Wardrobe near QuillTrigger / bed
    wardrobe_xy = (1340.0, 2000.0)  # between wardrobe trigger and bed
    bed_z_hint = -400.0
    # BlueRoom near SM_room_2 but east-south toward solid arch/island
    blue_xy = (700.0, 900.0)

    report = {
        "schema": "melodia.house_room_patch_wardrobe_blue.v1",
        "generated_at": datetime.now(timezone.utc).isoformat(),
        "destroyed": gone,
        "meshes": {"floor": fp, "wall": wp},
        "rooms": {
            "WardrobeRotunda": _room(world, ignore, floor, wall, "WardrobeRotunda",
                                     wardrobe_xy[0], wardrobe_xy[1], bed_z_hint, -15.0, (1.5, 1.5, 1.0)),
            "BlueRoom": _room(world, ignore, floor, wall, "BlueRoom",
                              blue_xy[0], blue_xy[1], -200.0, 15.0, (1.6, 1.4, 1.0)),
        },
    }
    try:
        unreal.get_editor_subsystem(unreal.LevelEditorSubsystem).save_current_level()
        report["level_saved"] = True
    except Exception as e:
        report["level_saved"] = str(e)

    report["counts"] = {
        rid: {"spawned": len(r.get("spawned") or []), "skipped": r.get("skipped")}
        for rid, r in report["rooms"].items()
    }
    OUT.parent.mkdir(parents=True, exist_ok=True)
    OUT.write_text(json.dumps(report, indent=2, default=str), encoding="utf-8")
    print("HOUSE_ROOM_PATCH " + json.dumps(report["counts"]))
    unreal.log("HOUSE_ROOM_PATCH wrote " + str(OUT))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
