"""Stage 4 hero corners on L_MelusinaMorning — each with own PCG graph + camera.

Corners (meadow-cluster distinct, not empty AABB void):
  1. MeadowChorus  — existing WC_morning_rainbow_bloom_Field (PointField) + new hero cam
  2. WestRim       — BrushifyIsland_07 — new PCG graph + volume
  3. EastBank      — BrushifyIsland_10 — new PCG graph + volume
  4. NorthDress    — near PCG_MelodiaOpening_Morning_Dressing / north decks — new graph + volume
"""
from __future__ import annotations
import json, math
from datetime import datetime, timezone
from pathlib import Path
import unreal

EAL = unreal.EditorAssetLibrary
SRC_GRAPH = "/Game/Melodia/WorldCompiler/PCG_WorldCompiler_PointField"
GRAPH_DIR = "/Game/Melodia/WorldCompiler/HeroCorners"
ALT_GRAPHS = {
    "NorthDress": "/Game/Melodia/PCG/PCG_Morning_MemoryDressing",
    "EastBank": "/Game/EnvSandbox/PCG/Universal/PCG_MeadowBloom",
}

CORNERS = [
    {
        "id": "MeadowChorus",
        "title": "Meadow Chorus",
        "island": None,
        "reuse_volume": "WC_morning_rainbow_bloom_Field",
        "loc": [-2298.0, 1442.0, 66.0],
        "cam_offset": [-900.0, -700.0, 520.0],
        "fov": 58.0,
        "band_hint": "full ROYGBIV rainbow field",
        "dress_notes": "Keep as hero chorus; dress path into frame; kill magenta rock blotches in FOV",
    },
    {
        "id": "WestRim",
        "title": "West Rim",
        "island": "BrushifyIsland_07",
        "loc": [-3200.0, 1880.0, 40.0],
        "scale": [4.0, 4.0, 3.0],
        "cam_offset": [650.0, -400.0, 380.0],
        "fov": 55.0,
        "band_hint": "Red/Violet heavy (rim silhouette)",
        "dress_notes": "Silhouette against sky; add 2–3 rocks + mist; sparse flowers",
    },
    {
        "id": "EastBank",
        "title": "East Bank",
        "island": "BrushifyIsland_10",
        "loc": [-1450.0, 1520.0, -200.0],
        "scale": [3.5, 3.5, 2.8],
        "cam_offset": [-500.0, 550.0, 320.0],
        "fov": 60.0,
        "band_hint": "Gold/Green walk-adjacent",
        "dress_notes": "Connect to EscherWalk spur_westbank; PortfolioDress already nearby",
    },
    {
        "id": "NorthDress",
        "title": "North Dressing",
        "island": None,
        "loc": [900.0, 2300.0, -200.0],
        "scale": [5.0, 5.0, 3.5],
        "cam_offset": [-800.0, -600.0, 450.0],
        "fov": 52.0,
        "band_hint": "Memory dressing / cooler indigo",
        "dress_notes": "Reuse Morning_Dressing PCG mood; stage props along approach from landing",
    },
]


def _label(a):
    try:
        return a.get_actor_label() or ""
    except Exception:
        return ""


def look_at(from_v, to_v):
    dx, dy, dz = to_v.x - from_v.x, to_v.y - from_v.y, to_v.z - from_v.z
    yaw = math.degrees(math.atan2(dy, dx))
    horiz = math.sqrt(dx * dx + dy * dy) or 1.0
    pitch = math.degrees(math.atan2(dz, horiz))
    return unreal.Rotator(pitch=pitch, yaw=yaw, roll=0.0)


def ensure_graph(corner_id: str) -> dict:
    dest = f"{GRAPH_DIR}/PCG_HeroCorner_{corner_id}"
    if not EAL.does_directory_exist(GRAPH_DIR):
        EAL.make_directory(GRAPH_DIR)
    src = ALT_GRAPHS.get(corner_id, SRC_GRAPH)
    if not EAL.does_asset_exist(src):
        src = SRC_GRAPH
    if EAL.does_asset_exist(dest):
        return {"path": dest, "created": False, "source": src}
    ok = EAL.duplicate_asset(src, dest)
    return {"path": dest, "created": bool(ok), "source": src, "exists": EAL.does_asset_exist(dest)}


def destroy_prior(svc, prefix):
    gone = []
    for a in list(svc.get_all_level_actors()):
        lab = _label(a)
        if lab.startswith(prefix):
            if svc.destroy_actor(a):
                gone.append(lab)
    return gone


def spawn_volume(svc, corner, graph_path):
    label = f"WC_HeroCorner_{corner['id']}_PCG"
    # destroy prior same label
    for a in list(svc.get_all_level_actors()):
        if _label(a) == label:
            svc.destroy_actor(a)
    loc = unreal.Vector(*corner["loc"])
    # lift to ground
    world = unreal.get_editor_subsystem(unreal.UnrealEditorSubsystem).get_editor_world()
    hit = unreal.SystemLibrary.line_trace_single(
        world, unreal.Vector(loc.x, loc.y, loc.z + 4000), unreal.Vector(loc.x, loc.y, loc.z - 5000),
        unreal.TraceTypeQuery.ECC_VISIBILITY, False, [],
        unreal.DrawDebugTrace.NONE, True,
        unreal.LinearColor.RED, unreal.LinearColor.GREEN, 0.0,
    )
    tup = hit.to_tuple() if hit else None
    ground = None
    if tup and tup[0]:
        loc = unreal.Vector(tup[4].x, tup[4].y, tup[4].z + 80)
        ground = tup[9].get_actor_label() if tup[9] else None
    vol = unreal.EditorLevelLibrary.spawn_actor_from_class(unreal.PCGVolume, loc, unreal.Rotator(0, 0, 0))
    if not vol:
        return {"ok": False, "error": "spawn failed"}
    vol.set_actor_label(label)
    sc = corner.get("scale") or [4.0, 4.0, 3.0]
    vol.set_actor_scale3d(unreal.Vector(*sc))
    try:
        vol.set_folder_path("HeroCorners/" + corner["id"])
        vol.tags = ["Portfolio", "HeroCorner", f"HeroCorner.{corner['id']}"]
    except Exception:
        pass
    graph = EAL.load_asset(graph_path)
    comp = vol.get_component_by_class(unreal.PCGComponent)
    assigned = False
    if comp and graph:
        try:
            comp.set_graph(graph)
            assigned = True
        except Exception as e:
            try:
                # graph instance parent
                gi = comp.get_editor_property("graph_instance")
                if gi:
                    for prop in ("graph", "pcg_graph", "parent"):
                        try:
                            gi.set_editor_property(prop, graph)
                            assigned = True
                            break
                        except Exception:
                            pass
            except Exception as e2:
                assigned = f"fail:{e}/{e2}"
        try:
            comp.set_editor_property("generation_trigger", unreal.PCGComponentGenerationTrigger.GENERATE_ON_DEMAND)
        except Exception:
            pass
        try:
            comp.set_editor_property("seed", (hash(corner["id"]) & 0x7FFFFFFF) or 7)
        except Exception:
            pass
        gen = False
        try:
            unreal.SystemLibrary.execute_console_command(world, "pcg.FlushCache")
        except Exception:
            pass
        try:
            comp.generate(True)
            gen = True
        except Exception as e:
            gen = f"gen_err:{e}"
    return {
        "ok": True,
        "label": label,
        "loc": [loc.x, loc.y, loc.z],
        "scale": sc,
        "ground": ground,
        "graph": graph_path,
        "assigned": assigned,
        "generate": gen,
    }


def spawn_cam(svc, corner, focus_loc):
    label = f"WC_HeroCorner_{corner['id']}_Cam"
    for a in list(svc.get_all_level_actors()):
        if _label(a) == label:
            svc.destroy_actor(a)
    off = corner["cam_offset"]
    cam_loc = unreal.Vector(focus_loc[0] + off[0], focus_loc[1] + off[1], focus_loc[2] + off[2])
    # ground-clamp camera height softly
    world = unreal.get_editor_subsystem(unreal.UnrealEditorSubsystem).get_editor_world()
    hit = unreal.SystemLibrary.line_trace_single(
        world, unreal.Vector(cam_loc.x, cam_loc.y, cam_loc.z + 2000),
        unreal.Vector(cam_loc.x, cam_loc.y, cam_loc.z - 4000),
        unreal.TraceTypeQuery.ECC_VISIBILITY, False, [],
        unreal.DrawDebugTrace.NONE, True,
        unreal.LinearColor.RED, unreal.LinearColor.GREEN, 0.0,
    )
    tup = hit.to_tuple() if hit else None
    if tup and tup[0]:
        # keep intended height if already above ground
        gz = float(tup[4].z)
        if cam_loc.z < gz + 160:
            cam_loc = unreal.Vector(cam_loc.x, cam_loc.y, gz + 180)
    look = unreal.Vector(focus_loc[0], focus_loc[1], focus_loc[2] + 100)
    rot = look_at(cam_loc, look)
    actor = svc.spawn_actor_from_class(unreal.CameraActor, cam_loc, rot)
    if not actor:
        return {"ok": False}
    actor.set_actor_label(label)
    try:
        actor.set_folder_path("HeroCorners/" + corner["id"])
        actor.tags = ["Portfolio", "PortfolioBeauty", "HeroCorner", f"HeroCorner.{corner['id']}"]
    except Exception:
        pass
    cam = actor.get_component_by_class(unreal.CameraComponent)
    if cam:
        cam.set_editor_property("field_of_view", float(corner.get("fov", 58)))
    r2 = actor.get_actor_rotation()
    return {
        "ok": True,
        "label": label,
        "loc": [cam_loc.x, cam_loc.y, cam_loc.z],
        "yaw": r2.yaw,
        "pitch": r2.pitch,
        "fov": corner.get("fov", 58),
    }


def capture_corners(svc, cams):
    world = unreal.get_editor_subsystem(unreal.UnrealEditorSubsystem).get_editor_world()
    uds = next((a for a in svc.get_all_level_actors() if _label(a) == "Ultra_Dynamic_Sky2"), None)
    if uds:
        try:
            uds.set_editor_property("Animate Time of Day", False)
            uds.set_editor_property("Time of Day", 1130.0)
            uds.set_editor_property("Cloud Coverage", 2.1)
            uds.set_editor_property("Sun Light Intensity", 4.6)
            uds.set_editor_property("Overall Intensity", 1.15)
        except Exception:
            pass
    out_dir = Path(unreal.Paths.project_dir()) / "Saved" / "Portfolio" / "Hero" / "MelusinaMorning" / "HeroCorners"
    out_dir.mkdir(parents=True, exist_ok=True)
    rt = unreal.RenderingLibrary.create_render_target2d(
        world, 1920, 1080, unreal.TextureRenderTargetFormat.RTF_RGBA8, unreal.LinearColor(0, 0, 0, 1), False)
    cap = svc.spawn_actor_from_class(unreal.SceneCapture2D, unreal.Vector(0, 0, 0))
    shots = []
    try:
        comp = cap.get_editor_property("capture_component2d")
        comp.set_editor_property("texture_target", rt)
        comp.set_editor_property("capture_source", unreal.SceneCaptureSource.SCS_FINAL_COLOR_LDR)
        for c in cams:
            a = next((x for x in svc.get_all_level_actors() if _label(x) == c["label"]), None)
            if not a:
                continue
            cap.set_actor_location_and_rotation(a.get_actor_location(), a.get_actor_rotation(), False, False)
            cam = a.get_component_by_class(unreal.CameraComponent)
            fov = float(c.get("fov") or 58)
            if cam:
                try:
                    fov = float(cam.get_editor_property("field_of_view"))
                except Exception:
                    pass
            comp.set_editor_property("fov_angle", fov)
            try:
                pps = comp.get_editor_property("post_process_settings")
                pps.set_editor_property("override_auto_exposure_bias", True)
                pps.set_editor_property("auto_exposure_bias", 1.0)
                comp.set_editor_property("post_process_settings", pps)
                comp.set_editor_property("post_process_blend_weight", 1.0)
            except Exception:
                pass
            for _ in range(4):
                comp.capture_scene()
            cid = c["label"].replace("WC_HeroCorner_", "").replace("_Cam", "")
            fn = out_dir / f"hero_corner_{cid}_2026-09-20.png"
            opts = unreal.ImageWriteOptions()
            opts.set_editor_property("format", unreal.DesiredImageFormat.PNG)
            opts.set_editor_property("overwrite_file", True)
            opts.set_editor_property("async_", False)
            unreal.ImageWriteBlueprintLibrary.export_to_disk(rt, str(fn).replace("\\", "/"), opts)
            shots.append({"id": cid, "file": str(fn), "bytes": fn.stat().st_size if fn.exists() else 0})
    finally:
        cap.destroy_actor()
    return shots


def main():
    svc = unreal.get_editor_subsystem(unreal.EditorActorSubsystem)
    destroy_prior(svc, "WC_HeroCorner_")

    results = []
    cams = []
    for corner in CORNERS:
        entry = {"id": corner["id"], "title": corner["title"], "band_hint": corner["band_hint"], "dress_notes": corner["dress_notes"]}
        if corner.get("reuse_volume"):
            vol = next((a for a in svc.get_all_level_actors() if _label(a) == corner["reuse_volume"]), None)
            entry["pcg"] = {
                "ok": vol is not None,
                "label": corner["reuse_volume"],
                "reused": True,
                "graph": SRC_GRAPH,
            }
            focus = corner["loc"]
            if vol:
                fl = vol.get_actor_location()
                focus = [fl.x, fl.y, fl.z]
            ginfo = {"path": SRC_GRAPH, "created": False, "reused_existing_field": True}
        else:
            ginfo = ensure_graph(corner["id"])
            entry["graph"] = ginfo
            entry["pcg"] = spawn_volume(svc, corner, ginfo["path"])
            focus = entry["pcg"].get("loc") or corner["loc"]
        cam = spawn_cam(svc, corner, focus)
        entry["cam"] = cam
        if cam.get("ok"):
            cams.append(cam)
        results.append(entry)

    shots = capture_corners(svc, cams)
    try:
        unreal.get_editor_subsystem(unreal.LevelEditorSubsystem).save_current_level()
        saved = True
    except Exception as e:
        saved = str(e)

    plan = {
        "schema": "melodia.hero_corners_plan.v1",
        "generated_at": datetime.now(timezone.utc).isoformat(),
        "level": "/Game/Melodia/Levels/Opening/L_MelusinaMorning",
        "shot_audit": {
            "keep_direction": ["earlier mid-morning oblique/south composition", "Nikki rim beginning to read on oblique"],
            "blockers": [
                "Flower mid-distance wash to grey/white — GhostLotus/color read still weak",
                "Magenta blotches read as shader errors not band color",
                "Walk POV still sells ground more than chorus",
                "Hybrid Nikki ≠ full Universal toon beauty yet",
            ],
            "material_status": "M_MelodiaPlant_Wind_NikkiToon + Rim/Sparkle/Pearl GREEN (Material Artist verified)",
        },
        "corners": results,
        "shots": shots,
        "collaboration": {
            "you_dress": "Meshes / props / path dressing per corner dress_notes; tell me when a corner is ready to recapture",
            "i_own": "PCG volumes/graphs, hero cams, UDS soft stills, captures, material dials with Material Artist",
            "do_not": "More random cams; edit PPV_NikkiDream; SquishWPO on SpeedTree",
        },
        "next_steps": [
            "1. You stage/dress WestRim + EastBank first (clearest new focal volumes)",
            "2. I recapture those two when you ping ready",
            "3. Together tighten MeadowChorus color-read (ROYGBIV) with Material Artist if wash persists",
            "4. NorthDress last — furthest from meadow cluster, needs most set dressing",
            "5. Lock final 4 website plates only after each corner has intentional dress",
        ],
        "level_saved": saved,
    }
    out = Path(unreal.Paths.project_dir()) / "Saved" / "Audit" / "hero_corners_plan_2026-09-20.json"
    out.write_text(json.dumps(plan, indent=2, default=str), encoding="utf-8")
    summary = {
        "corners": [{
            "id": r["id"],
            "pcg": (r.get("pcg") or {}).get("label"),
            "graph": (r.get("graph") or r.get("pcg") or {}).get("path") or (r.get("pcg") or {}).get("graph"),
            "cam": (r.get("cam") or {}).get("label"),
            "gen": (r.get("pcg") or {}).get("generate"),
        } for r in results],
        "shots": shots,
        "saved": saved,
        "report": str(out),
    }
    print("HERO4 " + json.dumps(summary, default=str))
    unreal.log("HERO4 " + json.dumps(summary, default=str))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
