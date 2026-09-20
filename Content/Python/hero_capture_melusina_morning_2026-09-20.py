"""Hero portfolio capture for L_MelusinaMorning — mid-morning + warmer sets from live WC_Lookdev_* cams."""
from __future__ import annotations
import json
from datetime import datetime, timezone
from pathlib import Path
import unreal

HIDE_ALWAYS = (
    "FX_Morning_Mist",  # wrong system → NS_Melodia_CursorTrail
    "FX_BowStage_PondMist",  # empty
)
HIDE_PREFIXES = (
    "SM_PM3D_Sphere3D",
    "SM_Greybox_",
    "HoudiniEngine_",
    "Houdini_Rainbow",
)
SHOW_PREFIXES = (
    "WC_Lookdev_",
    "WC_EscherWalk_",
    "WC_NS_Morning_",
    "FX_Morning_Bed_",
    "FX_Morning_Pollen",
    "FX_Morning_Petal",
    "FX_Morning_Wind",
)
SHOW_EXACT = (
    "WC_morning_rainbow_bloom_Field",
    "WC_MorningFlowerField_WindSource",
    "PPV_NikkiDream",
    "Ultra_Dynamic_Sky2",
)

# Preferred capture order for website heroes
PREFERRED = [
    "walk_deck_meadow",
    "walk_deck_approach",
    "oblique",
    "waterline",
    "south_form",
    "website_top",
    "field_hero",
    "meadow_wide",
]


def _label(a):
    try:
        return a.get_actor_label() or ""
    except Exception:
        return ""


def prepare_beauty(svc):
    notes = {"hidden": [], "shown": [], "skipped_class_c": []}
    for a in svc.get_all_level_actors():
        lab = _label(a)
        folder = ""
        try:
            folder = str(a.get_folder_path() or "")
        except Exception:
            pass
        hide = False
        if lab in HIDE_ALWAYS:
            hide = True
        if any(lab.startswith(p) for p in HIDE_PREFIXES):
            hide = True
        if folder.startswith("BowStage") and not lab.startswith("WC_NS_Morning_"):
            hide = True
        if "class_c" in lab.lower() or "ClassC" in lab or folder.lower().endswith("class_c"):
            hide = True
            notes["skipped_class_c"].append(lab)
        if "Preview" in lab and "ChoralSheep" in lab:
            hide = True
        if hide:
            a.set_is_temporarily_hidden_in_editor(True)
            a.set_actor_hidden_in_game(True)
            notes["hidden"].append(lab)
            continue
        show = lab in SHOW_EXACT or any(lab.startswith(p) for p in SHOW_PREFIXES)
        # Live beauty Niagara (Material Artist confirmed names)
        if lab in (
            "WC_NS_Morning_petal",
            "WC_NS_Morning_pollen",
            "WC_NS_Morning_mist",
            "WC_NS_Morning_windfront",
        ) or lab.startswith("WC_NS_Morning_"):
            show = True
        if show:
            a.set_is_temporarily_hidden_in_editor(False)
            a.set_actor_hidden_in_game(False)
            notes["shown"].append(lab)
    return notes


def set_uds(svc, mode: str):
    uds = next((a for a in svc.get_all_level_actors() if _label(a) == "Ultra_Dynamic_Sky2"), None)
    if not uds:
        return {"ok": False, "error": "no Ultra_Dynamic_Sky2"}
    presets = {
        "mid_morning": {
            "Animate Time of Day": False,
            "Time of Day": 1100.0,
            "Cloud Coverage": 1.8,
            "Overall Intensity": 1.25,
            "Sun Light Intensity": 5.5,
        },
        "warm_golden": {
            "Animate Time of Day": False,
            "Time of Day": 1700.0,
            "Cloud Coverage": 1.4,
            "Overall Intensity": 1.15,
            "Sun Light Intensity": 4.8,
        },
    }
    cfg = presets[mode]
    applied = {}
    for k, v in cfg.items():
        try:
            uds.set_editor_property(k, v)
            applied[k] = v
        except Exception as e:
            applied[k] = "ERR:" + str(e)[:80]
    return {"ok": True, "mode": mode, "applied": applied}


def list_lookdev_cams(svc):
    cams = [a for a in svc.get_all_level_actors() if _label(a).startswith("WC_Lookdev_")]
    def sort_key(a):
        name = _label(a).replace("WC_Lookdev_", "")
        try:
            return PREFERRED.index(name)
        except ValueError:
            return 100 + abs(hash(name)) % 50
    cams.sort(key=sort_key)
    return cams


def capture_cams(svc, cams, tag: str, out_dir: Path):
    world = unreal.get_editor_subsystem(unreal.UnrealEditorSubsystem).get_editor_world()
    out_dir.mkdir(parents=True, exist_ok=True)
    stamp = datetime.now(timezone.utc).date().isoformat()
    rt = unreal.RenderingLibrary.create_render_target2d(
        world, 1920, 1080, unreal.TextureRenderTargetFormat.RTF_RGBA8, unreal.LinearColor(0, 0, 0, 1), False
    )
    cap = svc.spawn_actor_from_class(unreal.SceneCapture2D, unreal.Vector(0, 0, 0))
    shots = []
    try:
        comp = cap.get_editor_property("capture_component2d")
        comp.set_editor_property("texture_target", rt)
        comp.set_editor_property("capture_source", unreal.SceneCaptureSource.SCS_FINAL_COLOR_LDR)
        comp.set_editor_property("capture_every_frame", False)
        for a in cams:
            loc = a.get_actor_location()
            rot = a.get_actor_rotation()
            cap.set_actor_location_and_rotation(loc, rot, False, False)
            cam_comp = None
            try:
                cam_comp = a.camera_component
            except Exception:
                cam_comp = a.get_component_by_class(unreal.CameraComponent)
            fov = 70.0
            if cam_comp:
                try:
                    fov = float(cam_comp.get_editor_property("field_of_view"))
                except Exception:
                    pass
            comp.set_editor_property("fov_angle", fov)
            try:
                pps = comp.get_editor_property("post_process_settings")
                # Leave level PPV_NikkiDream in control; light capture bias only
                pps.set_editor_property("override_auto_exposure_bias", True)
                pps.set_editor_property("auto_exposure_bias", 0.35)
                pps.set_editor_property("override_bloom_intensity", False)
                comp.set_editor_property("post_process_settings", pps)
                comp.set_editor_property("post_process_blend_weight", 1.0)
            except Exception:
                pass
            for _ in range(4):
                comp.capture_scene()
            name = _label(a).replace("WC_Lookdev_", "")
            fn = out_dir / ("hero_%s_%s_%s.png" % (tag, name, stamp))
            opts = unreal.ImageWriteOptions()
            opts.set_editor_property("format", unreal.DesiredImageFormat.PNG)
            opts.set_editor_property("overwrite_file", True)
            opts.set_editor_property("async_", False)
            unreal.ImageWriteBlueprintLibrary.export_to_disk(rt, str(fn).replace("\\", "/"), opts)
            shots.append({
                "name": name,
                "tag": tag,
                "file": str(fn).replace("\\", "/"),
                "bytes": fn.stat().st_size if fn.exists() else 0,
                "fov": fov,
                "loc": [loc.x, loc.y, loc.z],
            })
    finally:
        cap.destroy_actor()
    return shots


def main():
    svc = unreal.get_editor_subsystem(unreal.EditorActorSubsystem)
    beauty = prepare_beauty(svc)
    cams = list_lookdev_cams(svc)
    out_dir = Path(unreal.Paths.project_dir()) / "Saved" / "Portfolio" / "Hero" / "MelusinaMorning"
    all_shots = []

    uds_mid = set_uds(svc, "mid_morning")
    shots_mid = capture_cams(svc, cams, "midmorning", out_dir)
    all_shots.extend(shots_mid)

    uds_warm = set_uds(svc, "warm_golden")
    shots_warm = capture_cams(svc, cams, "warm1700", out_dir)
    all_shots.extend(shots_warm)

    # Restore mid-morning as working look
    set_uds(svc, "mid_morning")

    try:
        unreal.get_editor_subsystem(unreal.LevelEditorSubsystem).save_current_level()
        saved = True
    except Exception as e:
        saved = str(e)

    # Website hero picks (heuristic): prefer walk meadow, oblique, south/waterline from midmorning
    pick_names = ["walk_deck_meadow", "oblique", "south_form", "waterline", "website_top"]
    mid_by_name = {s["name"]: s for s in shots_mid}
    website_heroes = []
    for n in pick_names:
        if n in mid_by_name and mid_by_name[n]["bytes"] > 100000:
            website_heroes.append(mid_by_name[n])
        if len(website_heroes) >= 3:
            break
    docs_top = mid_by_name.get("website_top") or mid_by_name.get("walk_deck_approach")

    report = {
        "generated_at": datetime.now(timezone.utc).isoformat(),
        "world": unreal.get_editor_subsystem(unreal.UnrealEditorSubsystem).get_editor_world().get_path_name(),
        "beauty": {
            "hidden_count": len(beauty["hidden"]),
            "hidden_sample": beauty["hidden"][:40],
            "shown_count": len(beauty["shown"]),
            "class_c": beauty["skipped_class_c"][:20],
        },
        "cams": [_label(c) for c in cams],
        "uds_mid": uds_mid,
        "uds_warm": uds_warm,
        "shots": all_shots,
        "website_heroes_midmorning": website_heroes,
        "docs_top": docs_top,
        "level_saved": saved,
        "ppv": "PPV_NikkiDream left untouched (Material Artist GREEN)",
        "niagara": "WC_NS_Morning_* shown; FX_Morning_Mist + FX_BowStage_PondMist hidden",
    }
    out = Path(unreal.Paths.project_dir()) / "Saved" / "Audit" / "hero_capture_melusina_morning_2026-09-20.json"
    out.write_text(json.dumps(report, indent=2), encoding="utf-8")
    summary = {
        "cams": len(cams),
        "mid_shots": len(shots_mid),
        "warm_shots": len(shots_warm),
        "hidden": len(beauty["hidden"]),
        "website_heroes": [s["name"] for s in website_heroes],
        "docs_top": (docs_top or {}).get("name"),
        "out_dir": str(out_dir),
        "report": str(out),
        "saved": saved,
        "sample_bytes": [(s["tag"], s["name"], s["bytes"]) for s in all_shots[:6]],
    }
    print("HERO_CAP " + json.dumps(summary, default=str))
    unreal.log("HERO_CAP " + json.dumps(summary, default=str))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
