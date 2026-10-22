"""Polished corners stills: hero Nikki on hybrid bands + 3 locked beauty cams + soft expose."""
from __future__ import annotations
import json, math
from datetime import datetime, timezone
from pathlib import Path
import unreal

EAL = unreal.EditorAssetLibrary
MEL = unreal.MaterialEditingLibrary
BAND_PREFIX = "/Game/EnvSandbox/Materials/Instances/Flora/Rainbow/MI_RainbowSpeedTree_"
BANDS = [
    ("B0_Red", (1.0, 0.14, 0.18), 1.45),
    ("B1_Orange", (1.0, 0.45, 0.12), 1.25),
    ("B2_Gold", (1.0, 0.82, 0.2), 1.2),
    ("B3_Green", (0.3, 0.9, 0.38), 1.15),
    ("B4_Blue", (0.25, 0.48, 1.0), 0.95),
    ("B5_Indigo", (0.4, 0.3, 1.0), 1.3),
    ("B6_Violet", (0.88, 0.3, 1.0), 1.5),
]
HERO_NIKKI = {
    "PastelLift": 0.42,
    "DreamSaturation": 0.38,
    "DreamContrast": -0.04,
    "DreamShadowLift": 0.18,
    "DreamIntensity": 0.78,
    "DreamWarmth": 0.12,
    "SparkleIntensity": 0.22,
    "SparkleScale": 160.0,
    "SparkleThreshold": 0.48,
    "SparkleTwinkleSpeed": 0.35,
}
LOCKED = [
    # name, prefer existing label, eye/framing notes applied in place_locked_cams
    "website_oblique",
    "website_south",
    "walk_deck_meadow",
]


def _label(a):
    try:
        return a.get_actor_label() or ""
    except Exception:
        return ""


def push_hero_nikki():
    out = []
    for lab, tint, boost in BANDS:
        path = BAND_PREFIX + lab
        mi = EAL.load_asset(path)
        if not mi:
            out.append({"label": lab, "ok": False})
            continue
        names = set(str(n) for n in MEL.get_scalar_parameter_names(mi))
        wrote = {}
        for k, v in HERO_NIKKI.items():
            if k not in names:
                continue
            MEL.set_material_instance_scalar_parameter_value(mi, k, float(v))
            wrote[k] = float(v)
        # wind stay
        if "MelodiaWindResponse" in names:
            MEL.set_material_instance_scalar_parameter_value(mi, "MelodiaWindResponse", 0.45)
        r, g, b = tint
        br, bg, bb = min(1.6, r * boost), min(1.6, g * boost), min(1.6, b * boost)
        try:
            MEL.set_material_instance_vector_parameter_value(
                mi, "MelodiaWindRevealTint", unreal.LinearColor(br, bg, bb, 1.0))
            wrote["MelodiaWindRevealTint"] = [br, bg, bb]
        except Exception:
            pass
        try:
            MEL.set_material_instance_vector_parameter_value(
                mi, "DreamTint", unreal.LinearColor(br, bg, bb, 1.0))
        except Exception:
            pass
        EAL.save_asset(path)
        out.append({"label": lab, "ok": True, "wrote": wrote})
    return out


def look_at(from_v, to_v):
    dx, dy, dz = to_v.x - from_v.x, to_v.y - from_v.y, to_v.z - from_v.z
    yaw = math.degrees(math.atan2(dy, dx))
    horiz = math.sqrt(dx * dx + dy * dy) or 1.0
    pitch = math.degrees(math.atan2(dz, horiz))
    return unreal.Rotator(pitch, yaw, 0.0)


def soft_uds(svc):
    uds = next((a for a in svc.get_all_level_actors() if _label(a) == "Ultra_Dynamic_Sky2"), None)
    if not uds:
        return {"ok": False}
    cfg = {
        "Animate Time of Day": False,
        "Time of Day": 1130.0,
        "Cloud Coverage": 2.1,
        "Overall Intensity": 1.15,
        "Sun Light Intensity": 4.6,
    }
    applied = {}
    for k, v in cfg.items():
        try:
            uds.set_editor_property(k, v)
            applied[k] = v
        except Exception as e:
            applied[k] = str(e)[:60]
    return {"ok": True, "applied": applied}


def beauty_visibility(svc):
    hidden, shown = [], []
    for a in svc.get_all_level_actors():
        lab = _label(a)
        hide = lab.startswith("SM_PM3D_Sphere3D") or lab.startswith("SM_Greybox_") or lab.startswith("Houdini")
        hide = hide or lab in ("FX_Morning_Mist", "FX_BowStage_PondMist")
        if hide:
            a.set_is_temporarily_hidden_in_editor(True)
            a.set_actor_hidden_in_game(True)
            hidden.append(lab)
            continue
        if (lab.startswith("WC_Lookdev_") or lab.startswith("WC_EscherWalk_")
                or lab.startswith("WC_NS_Morning_") or lab.startswith("WC_PortfolioDress_")
                or lab == "WC_morning_rainbow_bloom_Field"
                or lab == "WC_MorningFlowerField_WindSource"):
            a.set_is_temporarily_hidden_in_editor(False)
            a.set_actor_hidden_in_game(False)
            shown.append(lab)
    return {"hidden": len(hidden), "shown": len(shown)}


def place_locked_cams(svc):
    """Refine the 3 locked cams toward meadow + sky; tag PortfolioBeauty."""
    field = next((a for a in svc.get_all_level_actors() if _label(a) == "WC_morning_rainbow_bloom_Field"), None)
    fl = field.get_actor_location() if field else unreal.Vector(-2300, 1440, 66)
    look = unreal.Vector(fl.x, fl.y, fl.z + 100)
    updated = []

    # walk meadow: ensure eye height and look into field
    walk = next((a for a in svc.get_all_level_actors() if _label(a) == "WC_Lookdev_walk_deck_meadow"), None)
    deck = next((a for a in svc.get_all_level_actors() if _label(a) == "WC_EscherWalk_spur_westbank_00"), None)
    if walk and deck:
        dloc = deck.get_actor_location()
        cam_loc = unreal.Vector(dloc.x, dloc.y, dloc.z + 170.0)
        rot = look_at(cam_loc, look)
        walk.set_actor_location_and_rotation(cam_loc, rot, False, False)
        cam = walk.get_component_by_class(unreal.CameraComponent)
        if cam:
            cam.set_editor_property("field_of_view", 58.0)
        try:
            walk.tags = ["WorldCompiler.lookdev", "Portfolio", "PortfolioBeauty", "WalkPOV"]
        except Exception:
            pass
        updated.append({"label": _label(walk), "loc": [cam_loc.x, cam_loc.y, cam_loc.z], "yaw": rot.yaw, "pitch": rot.pitch})

    # oblique / south: keep positions, nudge look toward field center slightly above
    for name in ("WC_Lookdev_website_oblique", "WC_Lookdev_website_south"):
        a = next((x for x in svc.get_all_level_actors() if _label(x) == name), None)
        if not a:
            continue
        loc = a.get_actor_location()
        # oblique: slightly lower pitch into meadow
        target = unreal.Vector(fl.x, fl.y, fl.z + (40 if "oblique" in name else 120))
        rot = look_at(loc, target)
        a.set_actor_rotation(rot, False)
        cam = a.get_component_by_class(unreal.CameraComponent)
        if cam:
            cam.set_editor_property("field_of_view", 62.0 if "oblique" in name else 55.0)
        try:
            a.tags = ["WorldCompiler.lookdev", "Portfolio", "PortfolioBeauty"]
        except Exception:
            pass
        updated.append({"label": name, "yaw": rot.yaw, "pitch": rot.pitch})

    # ensure labels exist
    missing = [n for n in ("WC_Lookdev_website_oblique", "WC_Lookdev_website_south", "WC_Lookdev_walk_deck_meadow")
               if not any(_label(a) == n for a in svc.get_all_level_actors())]
    return {"updated": updated, "missing": missing}


def capture_locked(svc):
    names = ["WC_Lookdev_website_oblique", "WC_Lookdev_website_south", "WC_Lookdev_walk_deck_meadow"]
    world = unreal.get_editor_subsystem(unreal.UnrealEditorSubsystem).get_editor_world()
    out_dir = Path(unreal.Paths.project_dir()) / "Saved" / "Portfolio" / "Hero" / "MelusinaMorning" / "PolishedCorners"
    out_dir.mkdir(parents=True, exist_ok=True)
    stamp = "2026-09-20"
    rt = unreal.RenderingLibrary.create_render_target2d(
        world, 1920, 1080, unreal.TextureRenderTargetFormat.RTF_RGBA8, unreal.LinearColor(0, 0, 0, 1), False)
    cap = svc.spawn_actor_from_class(unreal.SceneCapture2D, unreal.Vector(0, 0, 0))
    shots = []
    try:
        comp = cap.get_editor_property("capture_component2d")
        comp.set_editor_property("texture_target", rt)
        comp.set_editor_property("capture_source", unreal.SceneCaptureSource.SCS_FINAL_COLOR_LDR)
        for name in names:
            a = next((x for x in svc.get_all_level_actors() if _label(x) == name), None)
            if not a:
                shots.append({"name": name, "error": "missing"})
                continue
            cap.set_actor_location_and_rotation(a.get_actor_location(), a.get_actor_rotation(), False, False)
            cam = a.get_component_by_class(unreal.CameraComponent)
            fov = 60.0
            if cam:
                try:
                    fov = float(cam.get_editor_property("field_of_view"))
                except Exception:
                    pass
            comp.set_editor_property("fov_angle", fov)
            try:
                pps = comp.get_editor_property("post_process_settings")
                pps.set_editor_property("override_auto_exposure_bias", True)
                pps.set_editor_property("auto_exposure_bias", 0.85)
                pps.set_editor_property("override_auto_exposure_method", True)
                try:
                    pps.set_editor_property("auto_exposure_method", unreal.AutoExposureMethod.AEM_MANUAL)
                    pps.set_editor_property("override_auto_exposure_bias", True)
                except Exception:
                    pass
                # gentle bloom leave to level PPV
                pps.set_editor_property("override_bloom_intensity", False)
                comp.set_editor_property("post_process_settings", pps)
                comp.set_editor_property("post_process_blend_weight", 1.0)
            except Exception:
                pass
            for _ in range(5):
                comp.capture_scene()
            short = name.replace("WC_Lookdev_", "")
            fn = out_dir / ("corner_%s_hero_%s.png" % (short, stamp))
            opts = unreal.ImageWriteOptions()
            opts.set_editor_property("format", unreal.DesiredImageFormat.PNG)
            opts.set_editor_property("overwrite_file", True)
            opts.set_editor_property("async_", False)
            unreal.ImageWriteBlueprintLibrary.export_to_disk(rt, str(fn).replace("\\", "/"), opts)
            shots.append({"name": short, "file": str(fn), "bytes": fn.stat().st_size if fn.exists() else 0, "fov": fov})
    finally:
        cap.destroy_actor()
    return shots


def main():
    nikki = push_hero_nikki()
    svc = unreal.get_editor_subsystem(unreal.EditorActorSubsystem)
    uds = soft_uds(svc)
    vis = beauty_visibility(svc)
    cams = place_locked_cams(svc)
    shots = capture_locked(svc)
    try:
        unreal.get_editor_subsystem(unreal.LevelEditorSubsystem).save_current_level()
        saved = True
    except Exception as e:
        saved = str(e)
    report = {
        "generated_at": datetime.now(timezone.utc).isoformat(),
        "hero_nikki": nikki,
        "uds": uds,
        "visibility": vis,
        "cams": cams,
        "shots": shots,
        "level_saved": saved,
        "ppv": "untouched",
        "locked_corners": LOCKED,
    }
    out = Path(unreal.Paths.project_dir()) / "Saved" / "Audit" / "polished_corners_hero_nikki_2026-09-20.json"
    out.write_text(json.dumps(report, indent=2, default=str), encoding="utf-8")
    summary = {
        "bands": sum(1 for x in nikki if x.get("ok")),
        "uds_ok": uds.get("ok"),
        "cams": cams,
        "shots": [(s.get("name"), s.get("bytes")) for s in shots],
        "saved": saved,
        "report": str(out),
    }
    print("CORNERS " + json.dumps(summary, default=str))
    unreal.log("CORNERS " + json.dumps(summary, default=str))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
