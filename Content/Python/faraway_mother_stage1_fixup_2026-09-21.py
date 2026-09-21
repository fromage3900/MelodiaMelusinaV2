# -*- coding: utf-8 -*-
"""Stage 1 fixup: raycast with line_trace_single, scale ground, place 7, save_packages(only_dirty=False), reload verify."""
from __future__ import annotations
import hashlib, json
from datetime import datetime, timezone
from pathlib import Path
import unreal

LVL = "/Game/EnvSandbox/Monoliths/FarawayMother/Prototype/LV_FarawayMother_Prototype"
MANIFEST = Path(r"C:\EnvironmentPortfolio\BS_GodFile\Saved\Audit\faraway_mother_height_aware_pcg.json")
OUT = Path(r"C:\EnvironmentPortfolio\BS_GodFile\Saved\Audit") / f"faraway_mother_stage1_{datetime.now().strftime('%Y-%m-%d')}.json"
GROUND_LABEL = "FM_Ground_FabricRidge"
GROUND_MESH = "/Game/EnvSandbox/Meshes/Terrain/SM_FarawayMother_FabricRidge"
PLAYER_LABEL = "FM_PlayerStart"
SEED = 20260829

EAL = unreal.EditorAssetLibrary
LES = unreal.get_editor_subsystem(unreal.LevelEditorSubsystem)
UES = unreal.get_editor_subsystem(unreal.UnrealEditorSubsystem)
EAS = unreal.get_editor_subsystem(unreal.EditorActorSubsystem)


def log(m):
    unreal.log(f"[FM-S1] {m}")


def world_path():
    w = UES.get_editor_world()
    return w.get_path_name() if w else None


def raycast_z(x, y):
    world = UES.get_editor_world()
    start = unreal.Vector(float(x), float(y), 50000.0)
    end = unreal.Vector(float(x), float(y), -50000.0)
    actors_to_ignore = []
    try:
        hit = unreal.SystemLibrary.line_trace_single(
            world, start, end, unreal.DrawDebugTrace.NONE, True, actors_to_ignore,
            unreal.TraceTypeQuery.TRACE_TYPE_QUERY1, False
        )
    except Exception as e1:
        try:
            hit = unreal.SystemLibrary.line_trace_single_for_objects(
                world, start, end, [unreal.ObjectTypeQuery.OBJECT_TYPE_QUERY1], True, actors_to_ignore,
                unreal.DrawDebugTrace.NONE, False
            )
        except Exception as e2:
            try:
                hit = unreal.SystemLibrary.line_trace_single_new(world, start, end, 0, True, [], 0)
            except Exception as e3:
                return None, False, f"trace_failed:{e1}|{e2}|{e3}"
    # Normalize hit
    try:
        if isinstance(hit, (tuple, list)):
            ok = bool(hit[0])
            hr = hit[1] if len(hit) > 1 else None
            if ok and hr is not None:
                ip = getattr(hr, "impact_point", None) or hr.get_editor_property("impact_point")
                return float(ip.z), True, "hit"
            return None, False, "miss"
        # HitResult object
        blocking = bool(getattr(hit, "blocking_hit", False))
        if not blocking:
            try:
                blocking = bool(hit.get_editor_property("blocking_hit"))
            except Exception:
                pass
        if blocking:
            ip = getattr(hit, "impact_point", None)
            if ip is None:
                ip = hit.get_editor_property("impact_point")
            return float(ip.z), True, "hit"
        return None, False, "miss"
    except Exception as e:
        return None, False, f"parse:{e}"


def save_all():
    pkgs = []
    w = UES.get_editor_world()
    if w:
        pkgs.append(w.get_outermost())
    for a in EAS.get_all_level_actors():
        try:
            pkgs.append(a.get_outermost())
        except Exception:
            pass
    seen = set(); uniq = []
    for p in pkgs:
        try:
            n = p.get_name()
            if n not in seen:
                seen.add(n); uniq.append(p)
        except Exception:
            pass
    n = 0
    for i in range(0, max(len(uniq), 1), 60):
        chunk = uniq[i:i+60]
        if not chunk:
            break
        try:
            unreal.EditorLoadingAndSavingUtils.save_packages(chunk, False)
            n += len(chunk)
        except TypeError:
            try:
                unreal.EditorLoadingAndSavingUtils.save_packages(chunk, only_dirty=False)
                n += len(chunk)
            except Exception as e:
                log(f"save_packages: {e}")
                unreal.EditorLoadingAndSavingUtils.save_dirty_packages(True, True)
        except Exception as e:
            log(f"save_packages: {e}")
            try:
                unreal.EditorLoadingAndSavingUtils.save_dirty_packages(True, True)
            except Exception as e2:
                log(f"save_dirty: {e2}")
    LES.save_current_level()
    try:
        LES.save_all_dirty_levels()
    except Exception:
        pass
    return {"packages": len(uniq), "saved": n}


def main():
    if "MelusinaMorning" in (world_path() or ""):
        raise RuntimeError("refused Morning")
    if LVL.split("/")[-1] not in (world_path() or ""):
        LES.load_level(LVL)
    if "MelusinaMorning" in (world_path() or ""):
        raise RuntimeError("refused Morning after load")

    manifest_raw = MANIFEST.read_bytes()
    manifest = json.loads(manifest_raw.decode("utf-8"))
    mhash = hashlib.sha256(manifest_raw).hexdigest()

    # Scale ground to cover placement bounds (~9km)
    ground = None
    for a in EAS.get_all_level_actors():
        if (a.get_actor_label() or "") == GROUND_LABEL:
            ground = a
            break
    if not ground:
        mesh = EAL.load_asset(GROUND_MESH)
        ground = EAS.spawn_actor_from_class(unreal.StaticMeshActor, unreal.Vector(0, 0, 0), unreal.Rotator())
        ground.set_actor_label(GROUND_LABEL)
        ground.static_mesh_component.set_static_mesh(mesh)
    # large planar coverage
    ground.set_actor_scale3d(unreal.Vector(40, 40, 8))
    try:
        ground.static_mesh_component.set_collision_enabled(unreal.CollisionEnabled.QUERY_AND_PHYSICS)
        ground.static_mesh_component.set_collision_response_to_all_channels(unreal.CollisionResponse.ECR_BLOCK)
    except Exception as e:
        log(f"collision: {e}")
    ground.tags = ["FarawayMother", "Stage1", "Ground", f"seed_{SEED}"]

    # ensure player
    ps = None
    for a in EAS.get_all_level_actors():
        if (a.get_actor_label() or "") == PLAYER_LABEL or isinstance(a, unreal.PlayerStart):
            ps = a
            break
    if not ps:
        ps = EAS.spawn_actor_from_class(unreal.PlayerStart, unreal.Vector(0, 0, 300), unreal.Rotator())
        ps.set_actor_label(PLAYER_LABEL)
    gz, ghit, _ = raycast_z(0, 0)
    if ghit and gz is not None:
        ps.set_actor_location(unreal.Vector(0, 0, gz + 150), False, True)

    # clear prior placements
    ids = {p["id"] for p in manifest["placements"]}
    for a in list(EAS.get_all_level_actors()):
        if (a.get_actor_label() or "") in ids:
            EAS.destroy_actor(a)

    placed = []
    z_log = []
    for p in manifest["placements"]:
        pid = p["id"]
        xy = p["xy"]
        mesh_path = p["mesh"].split(".")[0]
        if "Greybox" in mesh_path or "greybox" in mesh_path:
            placed.append({"id": pid, "status": "skipped_greybox"})
            continue
        mesh = EAL.load_asset(mesh_path)
        if not mesh:
            placed.append({"id": pid, "status": "mesh_missing", "mesh": mesh_path})
            continue
        hit_z, did_hit, detail = raycast_z(xy[0], xy[1])
        z_offset = float(p.get("z_offset") or 0)
        if not did_hit or hit_z is None:
            # second try WorldStatic profile
            placed.append({"id": pid, "status": "raycast_miss_skipped", "xy": xy, "detail": detail, "mesh": mesh_path})
            z_log.append({"id": pid, "xy": xy, "hit": False, "detail": detail})
            continue
        final_z = hit_z + z_offset
        actor = EAS.spawn_actor_from_class(
            unreal.StaticMeshActor,
            unreal.Vector(float(xy[0]), float(xy[1]), float(final_z)),
            unreal.Rotator(0, float(p.get("yaw") or 0), 0),
        )
        actor.set_actor_label(pid)
        actor.static_mesh_component.set_static_mesh(mesh)
        sc = p.get("scale") or [1, 1, 1]
        actor.set_actor_scale3d(unreal.Vector(float(sc[0]), float(sc[1]), float(sc[2])))
        mat_path = (p.get("material_resolved") or "").split(".")[0]
        if mat_path:
            mat = EAL.load_asset(mat_path)
            if mat:
                try:
                    actor.static_mesh_component.set_material(0, mat)
                except Exception:
                    pass
        actor.tags = [t for t in [
            "FarawayMother", "Stage1", f"seed_{SEED}",
            p.get("data_layer") or "", p.get("hlod_layer") or "", p.get("builder") or "",
        ] if t]
        try:
            actor.set_folder_path(f"FarawayMother/Stage1/{p.get('data_layer') or 'Fabric'}")
        except Exception:
            pass
        entry = {
            "id": pid, "status": "placed", "xy": xy, "raycast_z": hit_z,
            "z_offset": z_offset, "final_z": final_z, "hit": True, "detail": detail,
            "mesh": mesh_path, "material": mat_path,
            "data_layer": p.get("data_layer"), "hlod_layer": p.get("hlod_layer"),
            "builder": p.get("builder"), "yaw": p.get("yaw"), "scale": sc,
        }
        placed.append(entry)
        z_log.append(entry)

    save_info = save_all()
    ok_reload = LES.load_level(LVL)
    labels = {}
    for a in EAS.get_all_level_actors():
        lab = a.get_actor_label() or ""
        if not lab:
            continue
        loc = a.get_actor_location()
        labels[lab] = {"z": round(loc.z, 2), "xy": [round(loc.x, 2), round(loc.y, 2)], "class": a.get_class().get_name()}

    present = [p["id"] for p in placed if p.get("status") == "placed" and p["id"] in labels]
    missing = [p["id"] for p in placed if p.get("status") == "placed" and p["id"] not in labels]
    report = {
        "schema": "melodia.faraway_mother.stage1_height_aware.v1",
        "generated_at": datetime.now(timezone.utc).isoformat(),
        "level": LVL,
        "seed": SEED,
        "manifest": str(MANIFEST),
        "manifest_sha256": mhash,
        "no_new_landscape": True,
        "morning_untouched": "MelusinaMorning" not in (world_path() or ""),
        "save": save_info,
        "reload_ok": bool(ok_reload),
        "world": world_path(),
        "placements": placed,
        "z_log": z_log,
        "verify": {
            "lvl_exists": EAL.does_asset_exist(LVL),
            "ground_present": GROUND_LABEL in labels,
            "player_present": PLAYER_LABEL in labels,
            "placed_ids_present": present,
            "placed_ids_missing": missing,
            "z_reread": {i: labels[i]["z"] for i in present},
            "actor_count": len(list(EAS.get_all_level_actors())),
            "ground_raycast_00": raycast_z(0, 0),
        },
        "pcg_world_actor": "absent — note for assembly pass",
        "ok": bool(present) and not missing and EAL.does_asset_exist(LVL) and GROUND_LABEL in labels,
    }
    OUT.write_text(json.dumps(report, indent=2, default=str), encoding="utf-8")
    print("STAGE1 " + json.dumps({
        "ok": report["ok"], "out": str(OUT), "placed": len(present),
        "missing": missing, "skips": sum(1 for p in placed if p.get("status") != "placed"),
        "world": report["world"], "actors": report["verify"]["actor_count"],
        "ground_hit": report["verify"]["ground_raycast_00"],
    }, default=str))
    return 0 if report["ok"] else 1


if __name__ == "__main__":
    raise SystemExit(main())
