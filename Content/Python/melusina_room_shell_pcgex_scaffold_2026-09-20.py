# -*- coding: utf-8 -*-
"""Scaffold MelusinaRoomShell via PCGex.
Places BP_MelusinaRoomShell on SM_room_2, sets W/D/H + door overrides, generate PCG.
Destroy-only WC_HouseRoomShell_<ShellId>*. GroundPolicy: lock Z to anchor (never SpireRamp).
"""
from __future__ import annotations
import json
from datetime import datetime, timezone
from pathlib import Path
import unreal

EAL = unreal.EditorAssetLibrary
SAVED = Path(unreal.Paths.project_saved_dir()) / "Audit"
OUT = SAVED / "melusina_room_shell_pcgex_scaffold_2026-09-20.json"

BP_CANDIDATES = (
    "/Game/EnvSandbox/Blueprints/House/BP_MelusinaRoomShell",
    "/Game/EnvSandbox/PCG/House/BP_MelusinaRoomShell",
    "/Game/EnvSandbox/Blueprints/BP_MelusinaRoomShell",
)
GRAPH_CANDIDATES = (
    "/Game/EnvSandbox/PCG/House/PCG_MelusinaRoomShell_PCGex",
    "/Game/EnvSandbox/PCG/PCG_MelusinaRoomShell_PCGex",
    "/Game/EnvSandbox/PCG/House/PCG_MelusinaRoomShell",
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
    "GroundPolicy": "lock_to_anchor_z",
}


def _lab(a):
    try:
        return a.get_actor_label() or ""
    except Exception:
        return ""


def _find(svc, name):
    for a in svc.get_all_level_actors():
        if _lab(a) == name:
            return a
    return None


def _destroy_shell(svc, shell_id):
    root = "WC_HouseRoomShell_%s" % shell_id
    prefix = root + "_"
    gone = []
    for a in list(svc.get_all_level_actors()):
        lab = _lab(a)
        if lab == root or lab.startswith(prefix):
            if svc.destroy_actor(a):
                gone.append(lab)
    return gone


def _first_asset(paths):
    for p in paths:
        if EAL.does_asset_exist(p):
            return p, EAL.load_asset(p)
    return None, None


def _set_prop(obj, name, value):
    try:
        obj.set_editor_property(name, value)
        return True
    except Exception:
        return False


def _apply_params(actor, params):
    applied = []
    doors = params.get("Doors") or {}
    mapping = {
        "Width_cm": float(params["Width_cm"]),
        "Depth_cm": float(params["Depth_cm"]),
        "Height_cm": float(params["Height_cm"]),
        "WallThickness_cm": float(params["WallThickness_cm"]),
        "ModuleSize_cm": float(params["ModuleSize_cm"]),
        "DoorWidth_cm": float(params["DoorWidth_cm"]),
        "Width": float(params["Width_cm"]),
        "Depth": float(params["Depth_cm"]),
        "Height": float(params["Height_cm"]),
        "Door_N": bool(doors.get("N")),
        "Door_E": bool(doors.get("E")),
        "Door_S": bool(doors.get("S")),
        "Door_W": bool(doors.get("W")),
        "bDoorN": bool(doors.get("N")),
        "bDoorE": bool(doors.get("E")),
        "bDoorS": bool(doors.get("S")),
        "bDoorW": bool(doors.get("W")),
    }
    for k, v in mapping.items():
        if _set_prop(actor, k, v):
            applied.append(k)
    try:
        comps = actor.get_components_by_class(unreal.PCGComponent)
    except Exception:
        comps = []
    for c in comps or []:
        for k, v in mapping.items():
            if _set_prop(c, k, v):
                applied.append("PCG." + k)
        try:
            c.cleanup()
        except Exception:
            try:
                c.cleanup_local_generation()
            except Exception:
                pass
        try:
            c.generate(True)
            applied.append("PCG.generate")
        except Exception:
            pass
    return applied


def main():
    params = dict(DEFAULTS)
    for cand in (
        SAVED / "melusina_room_shell_SalonA_params.json",
        SAVED / "melusina_room_shell_params.json",
    ):
        if cand.exists():
            params.update(json.loads(cand.read_text(encoding="utf-8-sig")))
            params["_params_file"] = str(cand)
            break

    shell_id = params["ShellId"]
    svc = unreal.get_editor_subsystem(unreal.EditorActorSubsystem)
    gone = _destroy_shell(svc, shell_id)
    bp_path, bp = _first_asset(BP_CANDIDATES)
    graph_path, graph = _first_asset(GRAPH_CANDIDATES)

    report = {
        "schema": "melodia.melusina_room_shell_pcgex_scaffold.v1",
        "generated_at": datetime.now(timezone.utc).isoformat(),
        "params": {k: v for k, v in params.items() if not str(k).startswith("_")},
        "destroyed": gone,
        "pcgex": {"bp": bp_path, "graph": graph_path},
        "applied_props": [],
        "notes": [],
    }

    anchor = _find(svc, params.get("AnchorLabel") or "SM_room_2")
    if not anchor:
        report["error"] = "anchor_not_found"
        OUT.write_text(json.dumps(report, indent=2), encoding="utf-8")
        print("SHELL_PCGEX_ERR no anchor")
        return 1

    aloc = anchor.get_actor_location()
    if params.get("Yaw_deg") is not None:
        ayaw = float(params["Yaw_deg"])
    else:
        try:
            ayaw = float(anchor.get_actor_rotation().yaw)
        except Exception:
            ayaw = 0.0

    ox, oy, oz = params.get("OffsetFromAnchor_cm") or [0.0, 0.0, 0.0]
    cx = float(aloc.x) + float(ox)
    cy = float(aloc.y) + float(oy)
    cz = float(aloc.z) + float(oz)
    report["center"] = [cx, cy, cz]
    report["ground"] = {"policy": "lock_to_anchor_z", "anchor": _lab(anchor), "z": cz}
    report["notes"].append("Z locked to SM_room_2; world line-trace disabled (avoids SpireRamp)")

    if not bp:
        report["status"] = "needs_pcgex_assets"
        report["notes"].append(
            "Missing BP_MelusinaRoomShell / PCG_MelusinaRoomShell_PCGex — "
            "create from PCGex recipe; old SalonA massing destroyed only"
        )
        try:
            unreal.get_editor_subsystem(unreal.LevelEditorSubsystem).save_current_level()
            report["level_saved"] = True
        except Exception as e:
            report["level_saved"] = str(e)
        OUT.write_text(json.dumps(report, indent=2), encoding="utf-8")
        print("SHELL_PCGEX_NEEDS_ASSETS " + json.dumps({
            "destroyed": len(gone), "bp": bp_path, "graph": graph_path, "z": cz
        }))
        return 2

    loc = unreal.Vector(cx, cy, cz)
    rot = unreal.Rotator(0.0, ayaw, 0.0)
    actor = None
    try:
        actor = unreal.EditorLevelLibrary.spawn_actor_from_object(bp, loc, rot)
    except Exception:
        actor = None
    if not actor:
        try:
            cls = unreal.EditorAssetLibrary.load_blueprint_class(bp_path)
            if cls:
                actor = svc.spawn_actor_from_class(cls, loc, rot)
        except Exception as e:
            report["error"] = "spawn_failed:%s" % e
            OUT.write_text(json.dumps(report, indent=2), encoding="utf-8")
            print("SHELL_PCGEX_ERR spawn")
            return 1
    if not actor:
        report["error"] = "spawn_failed"
        OUT.write_text(json.dumps(report, indent=2), encoding="utf-8")
        print("SHELL_PCGEX_ERR spawn")
        return 1

    label = "WC_HouseRoomShell_%s" % shell_id
    actor.set_actor_label(label)
    try:
        actor.set_actor_location(loc, False, True)
        actor.set_actor_rotation(rot, False)
        actor.set_folder_path("MelusinaHouse/RoomShells/%s" % shell_id)
        actor.tags = ["Portfolio", "MelusinaHouse", "RoomShell", "PCGex", "SizeEditable"]
    except Exception:
        pass

    if graph:
        try:
            comps = actor.get_components_by_class(unreal.PCGComponent)
            for c in comps or []:
                try:
                    c.set_editor_property("graph", graph)
                    report["notes"].append("assigned graph to PCGComponent")
                except Exception:
                    pass
        except Exception as e:
            report["notes"].append("graph_assign:%s" % e)

    report["applied_props"] = _apply_params(actor, params)
    report["spawned"] = label
    report["status"] = "ok"
    try:
        unreal.get_editor_subsystem(unreal.LevelEditorSubsystem).save_current_level()
        report["level_saved"] = True
    except Exception as e:
        report["level_saved"] = str(e)

    OUT.write_text(json.dumps(report, indent=2, default=str), encoding="utf-8")
    print("SHELL_PCGEX " + json.dumps({
        "ShellId": shell_id,
        "status": report["status"],
        "z": cz,
        "destroyed": len(gone),
        "bp": bp_path,
        "graph": graph_path,
    }))
    unreal.log("SHELL_PCGEX wrote " + str(OUT))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())

