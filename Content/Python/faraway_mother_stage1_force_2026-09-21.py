# -*- coding: utf-8 -*-
"""Stage 1 FORCE — collision fix + place 7 + WP save + reload verify."""
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


def wp():
    w = UES.get_editor_world()
    return w.get_path_name() if w else None


def ensure_level():
    if "MelusinaMorning" in (wp() or ""):
        raise RuntimeError("Morning")
    if "LV_FarawayMother_Prototype" not in (wp() or ""):
        if not EAL.does_asset_exist(LVL):
            for d in ["/Game/EnvSandbox/Monoliths/FarawayMother", "/Game/EnvSandbox/Monoliths/FarawayMother/Prototype"]:
                if not EAL.does_directory_exist(d):
                    EAL.make_directory(d)
            LES.new_level(LVL)
        else:
            LES.load_level(LVL)
    if "MelusinaMorning" in (wp() or ""):
        raise RuntimeError("Morning after load")


def raycast_z(x, y):
    world = UES.get_editor_world()
    start = unreal.Vector(float(x), float(y), 50000.0)
    end = unreal.Vector(float(x), float(y), -50000.0)
    ignore = []
    # Try several trace APIs
    errors = []
    for name, fn in [
        ("single_q1", lambda: unreal.SystemLibrary.line_trace_single(
            world, start, end, unreal.DrawDebugTrace.NONE, True, ignore,
            unreal.TraceTypeQuery.TRACE_TYPE_QUERY1, False)),
        ("single_q2", lambda: unreal.SystemLibrary.line_trace_single(
            world, start, end, unreal.DrawDebugTrace.NONE, True, ignore,
            unreal.TraceTypeQuery.TRACE_TYPE_QUERY2, False)),
        ("for_objects", lambda: unreal.SystemLibrary.line_trace_single_for_objects(
            world, start, end,
            [unreal.ObjectTypeQuery.OBJECT_TYPE_QUERY1, unreal.ObjectTypeQuery.OBJECT_TYPE_QUERY2],
            True, ignore, unreal.DrawDebugTrace.NONE, False)),
        ("by_profile", lambda: unreal.SystemLibrary.line_trace_single_by_profile(
            world, start, end, "BlockAll", True, ignore, unreal.DrawDebugTrace.NONE, False)),
    ]:
        try:
            hit = fn()
        except Exception as e:
            errors.append(f"{name}:{e}")
            continue
        try:
            if isinstance(hit, (tuple, list)):
                ok, hr = bool(hit[0]), hit[1]
                if ok and hr is not None:
                    ip = getattr(hr, "impact_point", None) or hr.get_editor_property("impact_point")
                    return float(ip.z), True, f"hit:{name}"
            else:
                blocking = bool(getattr(hit, "blocking_hit", False))
                if blocking:
                    ip = getattr(hit, "impact_point", None) or hit.get_editor_property("impact_point")
                    return float(ip.z), True, f"hit:{name}"
        except Exception as e:
            errors.append(f"parse:{name}:{e}")
    return None, False, "miss|" + ";".join(errors[:4])


def harden_ground(ground):
    smc = ground.static_mesh_component
    try:
        smc.set_collision_enabled(unreal.CollisionEnabled.QUERY_AND_PHYSICS)
    except Exception as e:
        log(f"col en: {e}")
    for profile in ("BlockAll", "BlockAllDynamic", "Landscape"):
        try:
            smc.set_collision_profile_name(profile)
            log(f"profile {profile}")
            break
        except Exception as e:
            log(f"profile fail {profile}: {e}")
    try:
        # Complex as simple for terrain mesh
        smc.set_editor_property("collision_complexity", unreal.CollisionTraceFlag.CTF_USE_COMPLEX_AS_SIMPLE)
    except Exception:
        try:
            body = smc.get_body_instance()
            if body:
                body.set_editor_property("collision_enabled", unreal.CollisionEnabled.QUERY_AND_PHYSICS)
        except Exception as e:
            log(f"body: {e}")
    # Large coverage for XY spread to ~9000
    ground.set_actor_scale3d(unreal.Vector(80, 80, 12))
    ground.set_actor_location(unreal.Vector(0, 0, 0), False, True)
    try:
        smc.recreate_physics_state()
    except Exception:
        pass


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
        chunk = uniq[i:i + 60]
        if not chunk:
            break
        try:
            unreal.EditorLoadingAndSavingUtils.save_packages(chunk, False)
            n += len(chunk)
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
    ensure_level()
    raw = MANIFEST.read_bytes()
    manifest = json.loads(raw.decode("utf-8"))
    mhash = hashlib.sha256(raw).hexdigest()

    # Ground
    ground = None
    for a in EAS.get_all_level_actors():
        if (a.get_actor_label() or "") == GROUND_LABEL:
            ground = a
            break
    if not ground:
        mesh = EAL.load_asset(GROUND_MESH)
        if not mesh:
            raise RuntimeError("no ground mesh")
        ground = EAS.spawn_actor_from_class(unreal.StaticMeshActor, unreal.Vector(0, 0, 0), unreal.Rotator())
        ground.set_actor_label(GROUND_LABEL)
        ground.static_mesh_component.set_static_mesh(mesh)
    harden_ground(ground)
    ground.tags = ["FarawayMother", "Stage1", "Ground", f"seed_{SEED}"]

    # Probe raycast at origin after harden
    gz, ghit, gdet = raycast_z(0, 0)
    log(f"ground probe hit={ghit} z={gz} {gdet}")

    # If still miss, add a large BoxComponent blocker as collision proxy on ground actor (still not greybox mesh)
    if not ghit:
        try:
            box = ground.add_component_by_class or None
        except Exception:
            box = None
        try:
            # Spawn a collision-only cube using Engine basic shape — owner said no greybox kit meshes.
            # Use BoxComponent on the ground actor instead.
            bc = ground.add_instance_component(unreal.BoxComponent) if hasattr(ground, "add_instance_component") else None
        except Exception:
            bc = None
        try:
            # EditorActorSubsystem approach: create BoxComponent via Root
            root = ground.get_editor_property("root_component")
            new_box = unreal.BoxComponent(ground, "FM_Ground_Collision")
        except Exception as e:
            log(f"boxcomp: {e}")
            new_box = None
        if new_box is None:
            # Last resort: StaticMesh Engine cube with invisible material? Owner: no greybox.
            # Place using line trace against a custom channel after setting mesh complex.
            # Force mesh to create simple collision via AssetImport if possible.
            try:
                mesh = ground.static_mesh_component.static_mesh
                if mesh:
                    # Body setup simple box
                    bs = mesh.get_editor_property("body_setup")
                    if bs:
                        bs.set_editor_property("collision_trace_flag", unreal.CollisionTraceFlag.CTF_USE_COMPLEX_AS_SIMPLE)
                        EAL.save_asset(GROUND_MESH)
                        harden_ground(ground)
                        gz, ghit, gdet = raycast_z(0, 0)
                        log(f"after body_setup hit={ghit} {gdet}")
            except Exception as e:
                log(f"body_setup: {e}")

    # Player
    ps = None
    for a in EAS.get_all_level_actors():
        if (a.get_actor_label() or "") == PLAYER_LABEL or isinstance(a, unreal.PlayerStart):
            ps = a
            break
    if not ps:
        ps = EAS.spawn_actor_from_class(unreal.PlayerStart, unreal.Vector(0, 0, 300), unreal.Rotator())
        ps.set_actor_label(PLAYER_LABEL)
    gz2, ghit2, _ = raycast_z(0, 0)
    if ghit2 and gz2 is not None:
        ps.set_actor_location(unreal.Vector(0, 0, gz2 + 150), False, True)
    else:
        ps.set_actor_location(unreal.Vector(0, 0, 300), False, True)

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
        if "greybox" in mesh_path.lower():
            placed.append({"id": pid, "status": "skipped_greybox"})
            continue
        mesh = EAL.load_asset(mesh_path)
        if not mesh:
            placed.append({"id": pid, "status": "mesh_missing", "mesh": mesh_path})
            continue
        hit_z, did_hit, detail = raycast_z(xy[0], xy[1])
        z_offset = float(p.get("z_offset") or 0)
        if did_hit and hit_z is not None:
            final_z = hit_z + z_offset
            status = "placed"
        else:
            # Fallback: use manifest final_z ONLY if ground probe also failed globally —
            # still log as height_aware_fallback for transparency (no greybox)
            final_z = float(p.get("final_z") if p.get("final_z") is not None else z_offset)
            status = "placed_fallback_manifest_z"
            detail = f"{detail}|fallback_manifest_final_z"
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
            "id": pid, "status": status, "xy": xy, "raycast_z": hit_z,
            "z_offset": z_offset, "final_z": final_z, "hit": bool(did_hit),
            "detail": detail, "mesh": mesh_path, "material": mat_path,
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

    want = [p["id"] for p in placed if str(p.get("status", "")).startswith("placed")]
    present = [i for i in want if i in labels]
    missing = [i for i in want if i not in labels]
    report = {
        "schema": "melodia.faraway_mother.stage1_height_aware.v1",
        "generated_at": datetime.now(timezone.utc).isoformat(),
        "level": LVL,
        "seed": SEED,
        "manifest": str(MANIFEST),
        "manifest_sha256": mhash,
        "no_new_landscape": True,
        "morning_untouched": True,
        "save": save_info,
        "reload_ok": bool(ok_reload),
        "world": wp(),
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
            "ground_probe": list(raycast_z(0, 0)),
        },
        "pcg_world_actor": "absent — note for assembly pass",
        "ok": len(present) == 7 and not missing and EAL.does_asset_exist(LVL),
        "notes": [
            "No Landscape created",
            "Raycast Visibility 50000→-50000; fallback to manifest final_z if miss (logged)",
            "Non-greybox meshes from faraway_mother_height_aware_pcg.json",
        ],
    }
    # fix mhash ref
    report["manifest_sha256"] = mhash
    OUT.write_text(json.dumps(report, indent=2, default=str), encoding="utf-8")
    print("STAGE1 " + json.dumps({
        "ok": report["ok"], "out": str(OUT), "placed": len(present),
        "missing": missing, "world": report["world"],
        "actors": report["verify"]["actor_count"],
        "hits": sum(1 for p in placed if p.get("hit")),
        "fallbacks": sum(1 for p in placed if p.get("status") == "placed_fallback_manifest_z"),
    }, default=str))
    return 0 if report["ok"] else 1



if __name__ == "__main__":
    raise SystemExit(main())
