"""Upgrade HeroCorner PCG graphs to proper flora/dress/PCGEx sources and reframe cams."""
from __future__ import annotations
import json, math
from datetime import datetime, timezone
from pathlib import Path
import unreal

EAL = unreal.EditorAssetLibrary
GRAPH_DIR = "/Game/Melodia/WorldCompiler/HeroCorners"

# Primary graph per corner (what the volume runs)
INTEGRATION = {
    "WestRim": {
        "primary": "/Game/EnvSandbox/PCG/Styles/Sakura/PCG_Nikki_MandalaBloom",  # PCGEx shapes — sparse radial accent
        "why": "PCGEx CreateShapes/Circle; silhouette-friendly; not PointField DT-dependent",
        "companion": "/Game/EnvSandbox/PCG/Universal/PCG_RockScatter",
    },
    "EastBank": {
        "primary": "/Game/EnvSandbox/PCG/Universal/PCG_MeadowBloom",  # already good
        "why": "Surface sampler + density + prune — Gold/Green meadow without DT",
        "companion": "/Game/EnvSandbox/PCG/Universal/PCG_PathScatter",
    },
    "NorthDress": {
        "primary": "/Game/EnvSandbox/PCG/Universal/PCG_OrnamentalDetail",
        "why": "Rich dress scatter; replaces thin 3-node MemoryDressing clone",
        "companion": "/Game/EnvSandbox/PCG/Universal/PCG_Universal_RockScatter",
    },
    "MeadowChorus": {
        "primary": "/Game/Melodia/WorldCompiler/PCG_WorldCompiler_PointField",
        "why": "KEEP — rainbow DT authority; do not replace with PCGex",
        "companion": None,
    },
}

SKIP_PCGEX_FOR_MORNING = [
    "/Game/EnvSandbox/PCG/Musical/Hero/PCG_Hero_ArpeggioBridge",
    "/Game/EnvSandbox/PCG/Musical/Hero/PCG_Hero_XylophoneTrail",
    "/Game/EnvSandbox/PCG/Musical/Hero/PCG_Hero_ResonanceCathedral",
    "/Game/EnvSandbox/PCG/Musical/Hero/PCG_Hero_CrystalHarpGrove",
]


def _label(a):
    try: return a.get_actor_label() or ""
    except: return ""


def look_at(from_v, to_v):
    dx, dy, dz = to_v.x-from_v.x, to_v.y-from_v.y, to_v.z-from_v.z
    yaw = math.degrees(math.atan2(dy, dx))
    horiz = math.sqrt(dx*dx+dy*dy) or 1.0
    pitch = math.degrees(math.atan2(dz, horiz))
    return unreal.Rotator(pitch=pitch, yaw=yaw, roll=0.0)


def replace_graph_asset(dest_name: str, source_path: str) -> dict:
    dest = f"{GRAPH_DIR}/{dest_name}"
    if not EAL.does_directory_exist(GRAPH_DIR):
        EAL.make_directory(GRAPH_DIR)
    if not EAL.does_asset_exist(source_path):
        return {"ok": False, "error": f"missing source {source_path}"}
    if EAL.does_asset_exist(dest):
        # delete then duplicate for clean replace
        try:
            EAL.delete_asset(dest)
        except Exception as e:
            return {"ok": False, "error": f"delete failed: {e}", "dest": dest}
    ok = EAL.duplicate_asset(source_path, dest)
    return {"ok": bool(ok) and EAL.does_asset_exist(dest), "dest": dest, "source": source_path}


def assign_and_generate(vol, graph_path, seed: int):
    graph = EAL.load_asset(graph_path)
    comp = vol.get_component_by_class(unreal.PCGComponent)
    if not comp or not graph:
        return {"assigned": False, "generate": False}
    assigned = False
    try:
        comp.set_graph(graph)
        assigned = True
    except Exception:
        try:
            gi = comp.get_editor_property("graph_instance")
            if gi:
                for prop in ("graph", "parent", "pcg_graph"):
                    try:
                        gi.set_editor_property(prop, graph)
                        assigned = True
                        break
                    except Exception:
                        pass
        except Exception as e:
            return {"assigned": False, "error": str(e)[:100]}
    try:
        comp.set_editor_property("seed", seed & 0x7FFFFFFF)
    except Exception:
        pass
    world = unreal.get_editor_subsystem(unreal.UnrealEditorSubsystem).get_editor_world()
    try:
        unreal.SystemLibrary.execute_console_command(world, "pcg.FlushCache")
    except Exception:
        pass
    gen = False
    try:
        comp.generate(True)
        gen = True
    except Exception as e:
        gen = f"err:{e}"
    return {"assigned": assigned, "generate": gen, "graph": graph_path}


def spawn_companion(svc, corner_id, loc, scale, graph_path, seed):
    label = f"WC_HeroCorner_{corner_id}_PCG_Companion"
    for a in list(svc.get_all_level_actors()):
        if _label(a) == label:
            svc.destroy_actor(a)
    if not graph_path or not EAL.does_asset_exist(graph_path):
        return {"ok": False, "skipped": True}
    vol = unreal.EditorLevelLibrary.spawn_actor_from_class(
        unreal.PCGVolume, unreal.Vector(*loc), unreal.Rotator(0, 0, 0))
    if not vol:
        return {"ok": False}
    vol.set_actor_label(label)
    vol.set_actor_scale3d(unreal.Vector(scale[0]*0.7, scale[1]*0.7, scale[2]*0.7))
    try:
        vol.set_folder_path(f"HeroCorners/{corner_id}")
        vol.tags = ["Portfolio", "HeroCorner", "HeroCornerCompanion", f"HeroCorner.{corner_id}"]
    except Exception:
        pass
    info = assign_and_generate(vol, graph_path, seed + 17)
    info.update({"ok": True, "label": label, "graph": graph_path})
    return info


def reframe_cam(svc, corner_id, focus, offset, fov):
    label = f"WC_HeroCorner_{corner_id}_Cam"
    a = next((x for x in svc.get_all_level_actors() if _label(x) == label), None)
    if not a:
        return {"ok": False, "missing": label}
    cam_loc = unreal.Vector(focus[0]+offset[0], focus[1]+offset[1], focus[2]+offset[2])
    look = unreal.Vector(focus[0], focus[1], focus[2]+120)
    # MeadowChorus: pull back more so chorus reads
    if corner_id == "MeadowChorus":
        cam_loc = unreal.Vector(focus[0]-1400, focus[1]-1100, focus[2]+720)
        look = unreal.Vector(focus[0], focus[1], focus[2]+80)
        fov = 52.0
    a.set_actor_location(cam_loc, False, False)
    a.set_actor_rotation(look_at(cam_loc, look), False)
    cam = a.get_component_by_class(unreal.CameraComponent)
    if cam:
        cam.set_editor_property("field_of_view", float(fov))
    r = a.get_actor_rotation()
    return {"ok": True, "label": label, "loc": [cam_loc.x, cam_loc.y, cam_loc.z], "yaw": r.yaw, "pitch": r.pitch, "fov": fov}


def beauty_hide_greybox(svc):
    n = 0
    for a in svc.get_all_level_actors():
        lab = _label(a)
        if lab.startswith(("SM_Greybox_", "SM_PM3D_Sphere3D", "Houdini_", "GB_Morning_")) or "Greybox" in lab:
            a.set_is_temporarily_hidden_in_editor(True)
            a.set_actor_hidden_in_game(True)
            n += 1
    return n


def capture(svc):
    world = unreal.get_editor_subsystem(unreal.UnrealEditorSubsystem).get_editor_world()
    uds = next((a for a in svc.get_all_level_actors() if _label(a) == "Ultra_Dynamic_Sky2"), None)
    if uds:
        for k, v in (("Animate Time of Day", False), ("Time of Day", 1130.0), ("Cloud Coverage", 2.1),
                     ("Sun Light Intensity", 4.6), ("Overall Intensity", 1.15)):
            try: uds.set_editor_property(k, v)
            except: pass
    out_dir = Path(unreal.Paths.project_dir())/"Saved"/"Portfolio"/"Hero"/"MelusinaMorning"/"HeroCorners"
    out_dir.mkdir(parents=True, exist_ok=True)
    rt = unreal.RenderingLibrary.create_render_target2d(world,1920,1080,unreal.TextureRenderTargetFormat.RTF_RGBA8,unreal.LinearColor(0,0,0,1),False)
    cap = svc.spawn_actor_from_class(unreal.SceneCapture2D, unreal.Vector(0,0,0))
    shots=[]
    try:
        comp=cap.get_editor_property("capture_component2d")
        comp.set_editor_property("texture_target", rt)
        comp.set_editor_property("capture_source", unreal.SceneCaptureSource.SCS_FINAL_COLOR_LDR)
        for cid in ("MeadowChorus","WestRim","EastBank","NorthDress"):
            a=next((x for x in svc.get_all_level_actors() if _label(x)==f"WC_HeroCorner_{cid}_Cam"), None)
            if not a: continue
            cap.set_actor_location_and_rotation(a.get_actor_location(), a.get_actor_rotation(), False, False)
            cam=a.get_component_by_class(unreal.CameraComponent)
            fov=55.0
            if cam:
                try: fov=float(cam.get_editor_property("field_of_view"))
                except: pass
            comp.set_editor_property("fov_angle", fov)
            try:
                pps=comp.get_editor_property("post_process_settings")
                pps.set_editor_property("override_auto_exposure_bias", True)
                pps.set_editor_property("auto_exposure_bias", 1.0)
                comp.set_editor_property("post_process_settings", pps)
                comp.set_editor_property("post_process_blend_weight", 1.0)
            except: pass
            for _ in range(4):
                comp.capture_scene()
            fn=out_dir/f"hero_corner_{cid}_pcgint_2026-09-20.png"
            opts=unreal.ImageWriteOptions()
            opts.set_editor_property("format", unreal.DesiredImageFormat.PNG)
            opts.set_editor_property("overwrite_file", True)
            opts.set_editor_property("async_", False)
            unreal.ImageWriteBlueprintLibrary.export_to_disk(rt, str(fn).replace("\\","/"), opts)
            shots.append({"id":cid,"bytes":fn.stat().st_size if fn.exists() else 0,"file":str(fn)})
    finally:
        cap.destroy_actor()
    return shots


def main():
    svc = unreal.get_editor_subsystem(unreal.EditorActorSubsystem)
    results = {"integrate": {}, "companions": {}, "cams": {}, "recommendations": {}}

    # --- rewrite graph assets ---
    for cid, spec in INTEGRATION.items():
        if cid == "MeadowChorus":
            results["integrate"][cid] = {"kept": spec["primary"], "why": spec["why"]}
            continue
        dest_name = f"PCG_HeroCorner_{cid}"
        rep = replace_graph_asset(dest_name, spec["primary"])
        results["integrate"][cid] = {**rep, "why": spec["why"]}

    # --- assign to volumes + generate ---
    volume_map = {
        "MeadowChorus": "WC_morning_rainbow_bloom_Field",
        "WestRim": "WC_HeroCorner_WestRim_PCG",
        "EastBank": "WC_HeroCorner_EastBank_PCG",
        "NorthDress": "WC_HeroCorner_NorthDress_PCG",
    }
    scales = {"WestRim": [3.5, 3.5, 2.8], "EastBank": [3.2, 3.2, 2.5], "NorthDress": [4.5, 4.5, 3.0]}
    for cid, vlabel in volume_map.items():
        vol = next((a for a in svc.get_all_level_actors() if _label(a) == vlabel), None)
        if not vol:
            results["integrate"].setdefault(cid, {})["volume"] = "missing"
            continue
        loc = vol.get_actor_location()
        if cid != "MeadowChorus":
            gpath = f"{GRAPH_DIR}/PCG_HeroCorner_{cid}"
            info = assign_and_generate(vol, gpath, hash(cid) & 0x7FFFFFFF)
            results["integrate"][cid]["volume"] = vlabel
            results["integrate"][cid]["runtime"] = info
            # companion
            comp_graph = INTEGRATION[cid].get("companion")
            results["companions"][cid] = spawn_companion(
                svc, cid, [loc.x, loc.y, loc.z], scales.get(cid, [3, 3, 2.5]), comp_graph, hash(cid + "c"))
        else:
            results["integrate"][cid]["volume"] = vlabel
            results["integrate"][cid]["runtime"] = {"kept_pointfield": True}

    # reframe cams
    focuses = {}
    for cid, vlabel in volume_map.items():
        vol = next((a for a in svc.get_all_level_actors() if _label(a) == vlabel), None)
        if vol:
            fl = vol.get_actor_location()
            focuses[cid] = [fl.x, fl.y, fl.z]
    offsets = {
        "MeadowChorus": [-1400, -1100, 720],
        "WestRim": [700, -450, 400],
        "EastBank": [-550, 600, 340],
        "NorthDress": [-900, -650, 480],
    }
    fovs = {"MeadowChorus": 52, "WestRim": 55, "EastBank": 58, "NorthDress": 52}
    for cid, focus in focuses.items():
        results["cams"][cid] = reframe_cam(svc, cid, focus, offsets[cid], fovs[cid])

    hidden = beauty_hide_greybox(svc)
    shots = capture(svc)

    try:
        unreal.get_editor_subsystem(unreal.LevelEditorSubsystem).save_current_level()
        saved = True
    except Exception as e:
        saved = str(e)

    plan = {
        "schema": "melodia.hero_corners_pcg_integration.v1",
        "generated_at": datetime.now(timezone.utc).isoformat(),
        "integrate": results["integrate"],
        "companions": results["companions"],
        "cams": results["cams"],
        "shots": shots,
        "beauty_hidden": hidden,
        "level_saved": saved,
        "use": {
            "MeadowChorus": "KEEP PointField (rainbow DT). No PCGex replace.",
            "WestRim": "PCG_Nikki_MandalaBloom (PCGEx shapes) + RockScatter companion",
            "EastBank": "PCG_MeadowBloom + PathScatter companion",
            "NorthDress": "PCG_OrnamentalDetail + Universal_RockScatter companion",
        },
        "skip_for_morning_meadow": SKIP_PCGEX_FOR_MORNING,
        "also_good_later": [
            "/Game/EnvSandbox/PCG/Styles/Sakura/PCG_Nikki_PhyllotaxisGarden_Walkable",
            "/Game/EnvSandbox/PCG/Universal/PCG_MeadowFalloff",
            "/Game/EnvSandbox/PCG/Universal/PCG_WaterEdgeScatter",
            "/Game/EnvSandbox/PCG/Musical/Hero/PCG_Hero_BellTreeGarden",
        ],
    }
    out = Path(unreal.Paths.project_dir())/"Saved"/"Audit"/"hero_corners_pcg_integration_2026-09-20.json"
    out.write_text(json.dumps(plan, indent=2, default=str), encoding="utf-8")
    print("PCGINT " + json.dumps({
        "west": results["integrate"].get("WestRim"),
        "east": results["integrate"].get("EastBank"),
        "north": results["integrate"].get("NorthDress"),
        "meadow": results["integrate"].get("MeadowChorus"),
        "companions": {k: (v or {}).get("label") for k,v in results["companions"].items()},
        "shots": shots,
        "hidden": hidden,
        "saved": saved,
        "report": str(out),
    }, default=str)[:8000])
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
