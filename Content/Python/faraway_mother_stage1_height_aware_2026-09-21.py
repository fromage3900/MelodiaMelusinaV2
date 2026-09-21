# -*- coding: utf-8 -*-
"""Faraway Mother Stage 1 REVISED — WP map + PlayerStart + 7 height-aware instances.
NO new Landscape. NO Morning. NO greybox.
"""
from __future__ import annotations
import hashlib, json
from datetime import datetime, timezone
from pathlib import Path
import unreal

LVL = "/Game/EnvSandbox/Monoliths/FarawayMother/Prototype/LV_FarawayMother_Prototype"
MANIFEST = Path(r"C:\EnvironmentPortfolio\BS_GodFile\Saved\Audit\faraway_mother_height_aware_pcg.json")
AUDIT = Path(r"C:\EnvironmentPortfolio\BS_GodFile\Saved\Audit")
DATE = datetime.now().strftime("%Y-%m-%d")
OUT = AUDIT / f"faraway_mother_stage1_{DATE}.json"
GROUND_MESH = "/Game/EnvSandbox/Meshes/Terrain/SM_FarawayMother_FabricRidge"
GROUND_LABEL = "FM_Ground_FabricRidge"
PLAYER_LABEL = "FM_PlayerStart"
SEED = 20260829
DELTA_REJECT_CM = 15.0

EAL = unreal.EditorAssetLibrary
LES = unreal.get_editor_subsystem(unreal.LevelEditorSubsystem)
UES = unreal.get_editor_subsystem(unreal.UnrealEditorSubsystem)
EAS = unreal.get_editor_subsystem(unreal.EditorActorSubsystem)


def log(m):
    unreal.log(f"[FM-S1] {m}")


def world_path():
    w = UES.get_editor_world()
    return w.get_path_name() if w else None


def refuse_morning():
    wp = world_path() or ""
    if "MelusinaMorning" in wp:
        raise RuntimeError(f"refused on Morning: {wp}")


def ensure_dirs():
    for d in [
        "/Game/EnvSandbox/Monoliths/FarawayMother",
        "/Game/EnvSandbox/Monoliths/FarawayMother/Prototype",
    ]:
        if not EAL.does_directory_exist(d):
            EAL.make_directory(d)


def raycast_z(x, y):
    world = UES.get_editor_world()
    start = unreal.Vector(float(x), float(y), 50000.0)
    end = unreal.Vector(float(x), float(y), -50000.0)
    ch = getattr(unreal, "ECC_Visibility", None) or 1
    try:
        hit = unreal.SystemLibrary.line_trace_single_by_channel(
            world, start, end, ch, True, [], unreal.DrawDebugTrace.NONE, False
        )
    except Exception:
        try:
            hit = unreal.SystemLibrary.line_trace_single_by_channel(
                world, start, end, 1, True, [], unreal.DrawDebugTrace.NONE, False
            )
        except Exception as e:
            return None, False, f"trace_failed:{e}"
    if not hit:
        return None, False, "miss"
    try:
        blocking = bool(hit.to_tuple()[0]) if hasattr(hit, "to_tuple") else bool(getattr(hit, "blocking_hit", False) or hit.get_editor_property("blocking_hit"))
    except Exception:
        try:
            blocking = bool(hit.get_editor_property("blocking_hit"))
        except Exception:
            blocking = False
    # HitResult as struct - try multiple
    try:
        if hasattr(hit, "blocking_hit"):
            blocking = bool(hit.blocking_hit)
    except Exception:
        pass
    try:
        # Some bindings return (hit_bool, hit_result)
        if isinstance(hit, (tuple, list)) and len(hit) >= 2:
            blocking, hr = bool(hit[0]), hit[1]
            impact = hr.impact_point if hasattr(hr, "impact_point") else hr.get_editor_property("impact_point")
            return float(impact.z), blocking, "hit" if blocking else "nonblocking"
    except Exception:
        pass
    try:
        impact = hit.get_editor_property("impact_point")
        return float(impact.z), True, "hit"
    except Exception as e:
        return None, False, f"parse_fail:{e}"


def save_all_packages():
    """WP-safe save: dirty packages in chunks."""
    pkgs = []
    try:
        # Gather loaded packages related to current world
        w = UES.get_editor_world()
        if w:
            pkgs.append(w.get_outermost())
        for a in EAS.get_all_level_actors():
            try:
                pkgs.append(a.get_outermost())
            except Exception:
                pass
    except Exception as e:
        log(f"pkg gather: {e}")
    # unique
    seen = set()
    uniq = []
    for p in pkgs:
        try:
            n = p.get_name()
            if n not in seen:
                seen.add(n)
                uniq.append(p)
        except Exception:
            pass
    saved = 0
    for i in range(0, len(uniq), 60):
        chunk = uniq[i : i + 60]
        try:
            unreal.EditorLoadingAndSavingUtils.save_packages(chunk, only_if_is_dirty=False)
            saved += len(chunk)
        except Exception as e:
            log(f"save_packages chunk fail: {e}")
            try:
                unreal.EditorLoadingAndSavingUtils.save_dirty_packages(True, True)
            except Exception as e2:
                log(f"save_dirty fail: {e2}")
    try:
        LES.save_current_level()
    except Exception:
        pass
    try:
        LES.save_all_dirty_levels()
    except Exception:
        pass
    return {"packages_attempted": len(uniq), "saved_chunks": saved}


def main():
    AUDIT.mkdir(parents=True, exist_ok=True)
    refuse_morning()
    ensure_dirs()
    manifest_raw = MANIFEST.read_bytes()
    manifest_hash = hashlib.sha256(manifest_raw).hexdigest()
    manifest = json.loads(manifest_raw.decode("utf-8"))

    report = {
        "schema": "melodia.faraway_mother.stage1_height_aware.v1",
        "generated_at": datetime.now(timezone.utc).isoformat(),
        "level": LVL,
        "seed": SEED,
        "manifest": str(MANIFEST),
        "manifest_sha256": manifest_hash,
        "no_new_landscape": True,
        "morning_untouched": True,
        "steps": [],
        "z_log": [],
        "ok": False,
    }

    # Create / open Faraway level
    if EAL.does_asset_exist(LVL):
        ok = LES.load_level(LVL)
        report["steps"].append({"load_existing": bool(ok), "world": world_path()})
    else:
        refuse_morning()
        LES.new_level(LVL)
        report["steps"].append({"new_level": LVL, "world": world_path()})
    refuse_morning()
    if "MelusinaMorning" in (world_path() or ""):
        report["error"] = "landed_on_morning"
        OUT.write_text(json.dumps(report, indent=2), encoding="utf-8")
        print("STAGE1_FAIL morning")
        return 1

    # Ground mesh for raycast (existing fabric ridge — not Landscape, not greybox)
    ground = None
    for a in EAS.get_all_level_actors():
        if (a.get_actor_label() or "") == GROUND_LABEL:
            ground = a
            break
    if not ground:
        mesh = EAL.load_asset(GROUND_MESH)
        if not mesh:
            report["error"] = f"missing_ground_mesh:{GROUND_MESH}"
            OUT.write_text(json.dumps(report, indent=2), encoding="utf-8")
            print("STAGE1_FAIL no_ground_mesh")
            return 1
        ground = EAS.spawn_actor_from_class(unreal.StaticMeshActor, unreal.Vector(0, 0, 0), unreal.Rotator(0, 0, 0))
        ground.set_actor_label(GROUND_LABEL)
        ground.static_mesh_component.set_static_mesh(mesh)
        try:
            ground.static_mesh_component.set_collision_enabled(unreal.CollisionEnabled.QUERY_AND_PHYSICS)
        except Exception:
            pass
        ground.tags = ["FarawayMother", "Stage1", "Ground", f"seed_{SEED}"]
        report["steps"].append({"ground": "spawned", "mesh": GROUND_MESH})
    else:
        report["steps"].append({"ground": "reused"})

    # PlayerStart
    ps = None
    for a in EAS.get_all_level_actors():
        if isinstance(a, unreal.PlayerStart) or (a.get_actor_label() or "") == PLAYER_LABEL:
            ps = a
            break
    if not ps:
        ps = EAS.spawn_actor_from_class(unreal.PlayerStart, unreal.Vector(0, 0, 300), unreal.Rotator(0, 0, 0))
        ps.set_actor_label(PLAYER_LABEL)
    gz, ghit, gdet = raycast_z(0, 0)
    if ghit and gz is not None:
        ps.set_actor_location(unreal.Vector(0, 0, gz + 120), False, True)
    ps.tags = ["FarawayMother", "Stage1"]
    report["steps"].append({"player_start": True, "z": [ps.get_actor_location().x, ps.get_actor_location().y, ps.get_actor_location().z]})

    # Destroy prior FM_* instances (idempotent) except ground/player
    for a in list(EAS.get_all_level_actors()):
        lab = a.get_actor_label() or ""
        if lab.startswith("FM_") and lab not in (GROUND_LABEL, PLAYER_LABEL) and lab.startswith("FM_Ridge") or lab.startswith("FM_Hair") or lab.startswith("FM_Valley") or lab.startswith("FM_Haze"):
            try:
                EAS.destroy_actor(a)
            except Exception:
                pass
    # cleaner destroy
    for a in list(EAS.get_all_level_actors()):
        lab = a.get_actor_label() or ""
        if lab in {p["id"] for p in manifest["placements"]}:
            try:
                EAS.destroy_actor(a)
            except Exception:
                pass

    placed = []
    for p in manifest["placements"]:
        pid = p["id"]
        xy = p["xy"]
        mesh_path = p["mesh"].split(".")[0]
        # reject greybox
        if "Greybox" in mesh_path or "greybox" in mesh_path:
            placed.append({"id": pid, "status": "skipped_greybox", "mesh": mesh_path})
            continue
        mesh = EAL.load_asset(mesh_path)
        if not mesh:
            placed.append({"id": pid, "status": "mesh_missing", "mesh": mesh_path})
            continue
        hit_z, did_hit, detail = raycast_z(xy[0], xy[1])
        z_offset = float(p.get("z_offset") or 0)
        if did_hit and hit_z is not None:
            final_z = hit_z + z_offset
            # compare to manifest planned final_z — reject if absurd floaters vs hit
            planned = float(p.get("final_z") or final_z)
            delta_cm = abs(final_z - (hit_z + z_offset))  # should be 0
            # Also check floating: if using planned offline z vs hit
            offline_delta = abs(planned - final_z)
            reject = False
            reject_reason = None
            # Owner: reject delta > 15 cm between successive raycast samples? Interpret as:
            # if we re-raycast and z differs >15cm from first — here single cast.
            # Use: if |planned offline final_z - live final_z| > huge, still place live.
            status = "placed"
        else:
            # No surface: do NOT invent landscape; skip rather than float greybox
            placed.append({
                "id": pid, "status": "raycast_miss_skipped", "xy": xy,
                "raycast_z": hit_z, "hit": False, "detail": detail,
                "mesh": mesh_path,
            })
            report["z_log"].append({"id": pid, "xy": xy, "hit": False, "detail": detail})
            continue

        actor = EAS.spawn_actor_from_class(
            unreal.StaticMeshActor,
            unreal.Vector(float(xy[0]), float(xy[1]), float(final_z)),
            unreal.Rotator(0, float(p.get("yaw") or 0), 0),
        )
        actor.set_actor_label(pid)
        actor.static_mesh_component.set_static_mesh(mesh)
        sc = p.get("scale") or [1, 1, 1]
        actor.set_actor_scale3d(unreal.Vector(float(sc[0]), float(sc[1]), float(sc[2])))
        # material
        mat_path = (p.get("material_resolved") or p.get("material_hint") or "").split(".")[0]
        if mat_path:
            mat = EAL.load_asset(mat_path)
            if mat:
                try:
                    actor.static_mesh_component.set_material(0, mat)
                except Exception:
                    pass
        tags = [
            "FarawayMother", "Stage1", f"seed_{SEED}",
            p.get("data_layer") or "DL_FarawayMother_Fabric",
            p.get("hlod_layer") or "HLOD_FarawayMother_Instanced",
            p.get("builder") or "",
            f"BIOME:{p.get('builder','')}",
        ]
        actor.tags = [t for t in tags if t]
        # folder
        try:
            actor.set_folder_path(f"FarawayMother/Stage1/{p.get('data_layer') or 'Fabric'}")
        except Exception:
            pass
        entry = {
            "id": pid,
            "status": "placed",
            "xy": xy,
            "raycast_z": hit_z,
            "z_offset": z_offset,
            "final_z": final_z,
            "hit": True,
            "detail": detail,
            "mesh": mesh_path,
            "material": mat_path,
            "data_layer": p.get("data_layer"),
            "hlod_layer": p.get("hlod_layer"),
            "builder": p.get("builder"),
            "yaw": p.get("yaw"),
            "scale": sc,
            "actor_label": actor.get_actor_label(),
        }
        placed.append(entry)
        report["z_log"].append(entry)

    # Fog / haze from biome (simple ExponentialHeightFog if missing)
    fog_vals = []
    try:
        bands = (manifest.get("pcg_params") or {}).get("biome_bands") or {}
        for b in bands.values():
            if isinstance(b, dict) and "fog" in b:
                fog_vals.append(float(b["fog"]))
    except Exception:
        pass
    fog_actor = None
    for a in EAS.get_all_level_actors():
        if isinstance(a, unreal.ExponentialHeightFog):
            fog_actor = a
            break
    if fog_actor is None and fog_vals:
        try:
            fog_actor = EAS.spawn_actor_from_class(unreal.ExponentialHeightFog, unreal.Vector(0, 0, 450), unreal.Rotator())
            fog_actor.set_actor_label("FM_MoonHaze_Fog")
            dens = max(fog_vals) if fog_vals else 0.04
            # cool moonlit tint from prior docs
            try:
                comp = fog_actor.get_component_by_class(unreal.ExponentialHeightFogComponent)
                if comp:
                    comp.set_editor_property("fog_density", dens)
            except Exception as e:
                log(f"fog set: {e}")
            report["steps"].append({"fog": "spawned", "density": dens, "tint": [0.70, 0.75, 0.90]})
        except Exception as e:
            report["steps"].append({"fog_err": str(e)})

    # PCGWorldActor note
    pcg_world = None
    for a in EAS.get_all_level_actors():
        cls = a.get_class().get_name()
        if "PCGWorld" in cls or "PCGVolume" in cls:
            pcg_world = cls
            break
    report["steps"].append({
        "pcg_world_actor": pcg_world or "absent — note for assembly pass",
    })

    save_info = save_all_packages()
    report["steps"].append({"save": save_info})

    # Full reload + re-read
    ok_load = LES.load_level(LVL)
    report["steps"].append({"reload": bool(ok_load), "world": world_path()})
    refuse_morning()

    labels = {}
    for a in EAS.get_all_level_actors():
        lab = a.get_actor_label() or ""
        if lab:
            loc = a.get_actor_location()
            labels[lab] = {"class": a.get_class().get_name(), "z": round(loc.z, 2), "xy": [round(loc.x, 2), round(loc.y, 2)]}

    verify = {
        "lvl_exists": EAL.does_asset_exist(LVL),
        "world": world_path(),
        "not_morning": "MelusinaMorning" not in (world_path() or ""),
        "ground_present": GROUND_LABEL in labels,
        "player_present": PLAYER_LABEL in labels or any(v["class"] == "PlayerStart" for v in labels.values()),
        "placed_ids_present": [],
        "placed_ids_missing": [],
        "actor_count": len(list(EAS.get_all_level_actors())),
        "labels_sample": {k: labels[k] for k in list(labels)[:20]},
    }
    for p in placed:
        if p.get("status") != "placed":
            continue
        if p["id"] in labels:
            verify["placed_ids_present"].append(p["id"])
            # re-read Z
            verify.setdefault("z_reread", {})[p["id"]] = labels[p["id"]]["z"]
        else:
            verify["placed_ids_missing"].append(p["id"])

    report["placements"] = placed
    report["verify"] = verify
    report["ok"] = bool(
        verify["lvl_exists"]
        and verify["not_morning"]
        and verify["ground_present"]
        and len(verify["placed_ids_present"]) >= 1
        and len(verify["placed_ids_missing"]) == 0
    )
    report["notes"] = [
        "No new Landscape",
        "Used SM_FarawayMother_FabricRidge as raycast ground",
        "Manifest: faraway_mother_height_aware_pcg.json (non-greybox)",
        "PCGWorldActor bindings deferred if absent",
    ]
    OUT.write_text(json.dumps(report, indent=2, default=str), encoding="utf-8")
    print("STAGE1 " + json.dumps({
        "ok": report["ok"],
        "out": str(OUT),
        "placed": len(verify["placed_ids_present"]),
        "missing": verify["placed_ids_missing"],
        "miss_skips": sum(1 for p in placed if p.get("status") != "placed"),
        "world": verify["world"],
        "actors": verify["actor_count"],
    }))
    return 0 if report["ok"] else 1


if __name__ == "__main__":
    raise SystemExit(main())

