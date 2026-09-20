"""P0 portfolio polish + walkability/composition audit for WC_Lookdev shots."""
from __future__ import annotations
import json
import math
from datetime import datetime, timezone
from pathlib import Path
import unreal

EAL = unreal.EditorAssetLibrary
MEL = unreal.MaterialEditingLibrary

BANDS = [
    ("B0_Red", (1.0, 0.18, 0.22), 1.15),
    ("B1_Orange", (1.0, 0.45, 0.1), 1.05),
    ("B2_Gold", (1.0, 0.8, 0.2), 1.0),
    ("B3_Green", (0.35, 0.95, 0.45), 0.85),
    ("B4_Blue", (0.3, 0.55, 1.0), 0.75),
    ("B5_Indigo", (0.45, 0.3, 0.95), 1.1),
    ("B6_Violet", (0.75, 0.35, 1.0), 1.2),
]
PREFIX = "/Game/EnvSandbox/Materials/Instances/Flora/Rainbow/MI_RainbowSpeedTree_"
HIDE_PREFIXES = ("SM_PM3D_Sphere3D", "SM_Greybox_", "PetalTemplate_")
HIDE_EXACT = {
    "SM_Greybox_Wall_Window", "SM_Greybox_Wall_Mid_001", "SM_Greybox_Wall_Window3",
    "SM_Greybox_Wall_Window2", "SM_Greybox_Wall_Mid_2", "SM_PM3D_Sphere3D1_1",
}
LOOKDEV = [
    "WC_Lookdev_waterline_dolly",
    "WC_Lookdev_website_oblique",
    "WC_Lookdev_website_top",
    "WC_Lookdev_website_south",
    "WC_Lookdev_south_form",
]


def _label(a):
    try:
        return a.get_actor_label() or ""
    except Exception:
        return ""


def _cls(a):
    try:
        return a.get_class().get_name()
    except Exception:
        return ""


def _loc(a):
    t = a.get_actor_location()
    return unreal.Vector(t.x, t.y, t.z)


def _fwd(a):
    try:
        return a.get_actor_rotation().get_forward_vector()
    except Exception:
        return unreal.Vector(1, 0, 0)


def ensure_wind(svc):
    existing = [a for a in svc.get_all_level_actors() if "WindDirectionalSource" in _cls(a)]
    if existing:
        for a in existing:
            if not _label(a):
                a.set_actor_label("WC_MorningFlowerField_WindSource")
            for c in a.get_components_by_class(unreal.WindDirectionalSourceComponent) or []:
                try:
                    c.set_editor_property("strength", 0.4)
                    c.set_editor_property("speed", 0.28)
                    c.set_editor_property("minimum_gust_amount", 0.06)
                except Exception:
                    pass
        return {"created": False, "count": len(existing), "labels": [_label(a) for a in existing]}
    field = next((a for a in svc.get_all_level_actors() if _label(a) == "WC_morning_rainbow_bloom_Field"), None)
    loc = unreal.Vector(-2300, 1440, 400)
    if field:
        fl = field.get_actor_location()
        loc = unreal.Vector(fl.x, fl.y, fl.z + 350)
    actor = unreal.EditorLevelLibrary.spawn_actor_from_class(
        unreal.WindDirectionalSource, loc, unreal.Rotator(0, 25, 0))
    if not actor:
        return {"created": False, "error": "spawn failed"}
    actor.set_actor_label("WC_MorningFlowerField_WindSource")
    for c in actor.get_components_by_class(unreal.WindDirectionalSourceComponent) or []:
        try:
            c.set_editor_property("strength", 0.4)
            c.set_editor_property("speed", 0.28)
            c.set_editor_property("minimum_gust_amount", 0.06)
        except Exception:
            pass
    return {"created": True, "label": _label(actor), "loc": [loc.x, loc.y, loc.z]}


def push_flower_read():
    changed = []
    for label, tint, tint_boost in BANDS:
        path = PREFIX + label
        mi = EAL.load_asset(path)
        if not mi:
            continue
        r, g, b = tint
        br, bg, bb = min(1.0, r * tint_boost), min(1.0, g * tint_boost), min(1.0, b * tint_boost)
        MEL.set_material_instance_vector_parameter_value(
            mi, "MelodiaWindRevealTint", unreal.LinearColor(br, bg, bb, 1.0))
        MEL.set_material_instance_scalar_parameter_value(mi, "MelodiaWindResponse", 0.5)
        for k, v in {
            "SharedIndependence": 0.04,
            "Branch1Independence": 0.04,
            "SharedOscillation": 0.14,
            "Branch1StretchLimit": 0.12,
        }.items():
            try:
                MEL.set_material_instance_scalar_parameter_value(mi, k, float(v))
            except Exception:
                pass
        MEL.update_material_instance(mi)
        EAL.save_asset(path)
        changed.append({"path": path, "tint": [br, bg, bb], "boost": tint_boost})
    return changed


def soften_uds_ppv(svc):
    uds = next((a for a in svc.get_all_level_actors() if _label(a) == "Ultra_Dynamic_Sky2"), None)
    uds_rec = {}
    if uds:
        uds.set_editor_property("Animate Time of Day", False)
        uds.set_editor_property("Time of Day", 1100.0)
        uds.set_editor_property("Sun Light Intensity", 5.5)
        uds.set_editor_property("Overall Intensity", 1.25)
        uds.set_editor_property("Cloud Coverage", 1.8)
        for p in ("Time of Day", "Sun Light Intensity", "Overall Intensity", "Cloud Coverage"):
            uds_rec[p] = uds.get_editor_property(p)
    ppv = next((a for a in svc.get_all_level_actors() if _label(a) == "PPV_NikkiDream"), None)
    ppv_rec = {"found": bool(ppv)}
    if ppv:
        try:
            settings = ppv.get_editor_property("settings")
            try:
                settings.set_editor_property("override_auto_exposure_bias", True)
                settings.set_editor_property("auto_exposure_bias", 0.35)
            except Exception as e:
                ppv_rec["exposure_err"] = str(e)[:120]
            try:
                settings.set_editor_property("override_bloom_intensity", True)
                settings.set_editor_property("bloom_intensity", 0.2)
            except Exception as e:
                ppv_rec["bloom_err"] = str(e)[:120]
            ppv.set_editor_property("settings", settings)
            ppv_rec["tuned"] = True
        except Exception as e:
            ppv_rec["error"] = str(e)[:200]
    return {"uds": uds_rec, "ppv": ppv_rec}


def beauty_hide(svc):
    hidden = []
    for a in svc.get_all_level_actors():
        lab = _label(a)
        folder = ""
        try:
            folder = str(a.get_folder_path() or "")
        except Exception:
            pass
        hide = False
        if lab in HIDE_EXACT:
            hide = True
        if any(lab.startswith(p) for p in HIDE_PREFIXES):
            hide = True
        if folder.startswith("BowStage") and "PondMist" not in lab:
            hide = True
        if lab.startswith("NS_ChoralSheep_") and "Preview" in lab:
            hide = True
        if hide:
            try:
                a.set_is_temporarily_hidden_in_editor(True)
                a.set_actor_hidden_in_game(True)
                hidden.append(lab)
            except Exception:
                pass
    for a in svc.get_all_level_actors():
        lab = _label(a)
        if lab in ("HoudiniEngine_RainbowBloom_3900", "Houdini_RainbowBloom_3900"):
            a.set_is_temporarily_hidden_in_editor(True)
            a.set_actor_hidden_in_game(True)
        if lab == "WC_morning_rainbow_bloom_Field" or lab.startswith("WC_Lookdev_") or lab.startswith("WC_EscherWalk_"):
            a.set_is_temporarily_hidden_in_editor(False)
            a.set_actor_hidden_in_game(False)
        if lab in (
            "FX_Morning_Mist", "FX_Morning_Bed_PollenSparkle", "WC_NS_Morning_pollen_fx_pollen_0_0",
            "WC_NS_Morning_petal_fx_petal_0_0", "WC_NS_Morning_mist_fx_mist_x_0",
            "WC_NS_Morning_windfront_fx_windfront_x_0", "FX_Morning_WaterGlint", "FX_Morning_DustShafts_Threshold",
        ):
            a.set_is_temporarily_hidden_in_editor(False)
            a.set_actor_hidden_in_game(False)
    return hidden


def _trace(world, start, end):
    hit = unreal.SystemLibrary.line_trace_single(
        world, start, end,
        unreal.TraceTypeQuery.TRACE_TYPE_QUERY1, False, [],
        unreal.DrawDebugTrace.NONE, True,
        unreal.LinearColor.RED, unreal.LinearColor.GREEN, 0.0)
    t = hit.to_tuple() if hit else None
    if not t or not t[0]:
        return None
    loc = t[4] if len(t) > 4 else None
    actor = t[9] if len(t) > 9 else None
    try:
        hit_loc = [float(loc.x), float(loc.y), float(loc.z)] if loc else None
    except Exception:
        hit_loc = None
    return {
        "blocking": True,
        "location": hit_loc,
        "actor": _label(actor) if actor else None,
        "class": _cls(actor) if actor else None,
        "distance": float(t[1]) if isinstance(t[1], (int, float)) else None,
    }


def audit_walk_and_compose(svc, world):
    cams = {_label(a): a for a in svc.get_all_level_actors() if _label(a) in LOOKDEV}
    walks = [a for a in svc.get_all_level_actors() if _label(a).startswith("WC_EscherWalk_")]
    field = next((a for a in svc.get_all_level_actors() if _label(a) == "WC_morning_rainbow_bloom_Field"), None)
    field_loc = field.get_actor_location() if field else unreal.Vector(-2300, 1440, 66)
    nav = [a for a in svc.get_all_level_actors() if "NavMesh" in _cls(a) or "NavMesh" in _label(a)]
    results = []
    for name in LOOKDEV:
        a = cams.get(name)
        if not a:
            results.append({"camera": name, "ok": False, "error": "missing"})
            continue
        loc = _loc(a)
        fwd = _fwd(a)
        ground = _trace(world, unreal.Vector(loc.x, loc.y, loc.z + 50), unreal.Vector(loc.x, loc.y, loc.z - 4000))
        walk_samples = []
        for dist in (300, 800, 1500, 2500):
            p = unreal.Vector(loc.x + fwd.x * dist, loc.y + fwd.y * dist, loc.z + 80)
            g = _trace(world, unreal.Vector(p.x, p.y, p.z + 200), unreal.Vector(p.x, p.y, p.z - 2500))
            walk_samples.append({"dist_cm": dist, "ground": g})
        dx, dy, dz = field_loc.x - loc.x, field_loc.y - loc.y, field_loc.z - loc.z
        dist_field = math.sqrt(dx * dx + dy * dy + dz * dz)
        to_len = max(1e-3, dist_field)
        to_n = unreal.Vector(dx / to_len, dy / to_len, dz / to_len)
        flen = max(1e-3, math.sqrt(fwd.x ** 2 + fwd.y ** 2 + fwd.z ** 2))
        fn = unreal.Vector(fwd.x / flen, fwd.y / flen, fwd.z / flen)
        dot = max(-1.0, min(1.0, fn.x * to_n.x + fn.y * to_n.y + fn.z * to_n.z))
        angle_deg = math.degrees(math.acos(dot))
        walks_in_view = []
        for w in walks:
            wl = w.get_actor_location()
            vx, vy, vz = wl.x - loc.x, wl.y - loc.y, wl.z - loc.z
            vl = math.sqrt(vx * vx + vy * vy + vz * vz) or 1
            d2 = (fn.x * vx + fn.y * vy + fn.z * vz) / vl
            if d2 > 0.35 and vl < 6000:
                walks_in_view.append({"label": _label(w), "dist_cm": round(vl, 1)})
        notes = []
        if ground is None:
            notes.append("camera has no ground hit below — floating or over void")
        elif ground.get("distance") and ground["distance"] > 600:
            notes.append("camera high above ground (>6m) — aerial, not walkable POV")
        if angle_deg > 55:
            notes.append("field center off-axis (%.0f deg) — weak meadow hero framing" % angle_deg)
        elif angle_deg < 25:
            notes.append("field center well framed")
        walkable_hits = sum(1 for s in walk_samples if s["ground"] and s["ground"].get("actor"))
        if walkable_hits < 2 and name != "WC_Lookdev_website_top":
            notes.append("few ground hits along look path — void gaps / weak walk-read")
        walk_hits = sum(1 for s in walk_samples if s["ground"] and "EscherWalk" in (s["ground"].get("actor") or ""))
        if walk_hits:
            notes.append("EscherWalk deck in path (%d samples)" % walk_hits)
        results.append({
            "camera": name,
            "ok": True,
            "loc_cm": [round(loc.x, 1), round(loc.y, 1), round(loc.z, 1)],
            "ground_under_cam": ground,
            "walk_samples": walk_samples,
            "dist_to_field_cm": round(dist_field, 1),
            "angle_to_field_deg": round(angle_deg, 1),
            "walks_in_view_count": len(walks_in_view),
            "walks_in_view_sample": walks_in_view[:8],
            "notes": notes,
            "walkable_path_hits": walkable_hits,
            "escher_path_hits": walk_hits,
        })
    return {
        "nav_actors": [{"label": _label(a), "class": _cls(a)} for a in nav],
        "escher_walk_count": len(walks),
        "cameras": results,
    }


def main():
    svc = unreal.get_editor_subsystem(unreal.EditorActorSubsystem)
    world = unreal.get_editor_subsystem(unreal.UnrealEditorSubsystem).get_editor_world()
    wind = ensure_wind(svc)
    flowers = push_flower_read()
    lighting = soften_uds_ppv(svc)
    hidden = beauty_hide(svc)
    walk = audit_walk_and_compose(svc, world)
    try:
        unreal.get_editor_subsystem(unreal.LevelEditorSubsystem).save_current_level()
        saved = True
    except Exception as e:
        saved = str(e)
    wind_after = [_label(a) for a in svc.get_all_level_actors() if "WindDirectional" in _cls(a)]
    report = {
        "generated_at": datetime.now(timezone.utc).isoformat(),
        "world": world.get_path_name() if world else None,
        "p0": {
            "wind": wind,
            "wind_after_labels": wind_after,
            "flower_bands": flowers,
            "lighting": lighting,
            "beauty_hidden_count": len(hidden),
            "beauty_hidden_sample": hidden[:40],
            "level_saved": saved,
        },
        "walk_compose": walk,
    }
    out = Path(unreal.Paths.project_dir()) / "Saved" / "Audit" / "p0_polish_walk_compose_2026-09-20.json"
    out.write_text(json.dumps(report, indent=2), encoding="utf-8")
    cam_notes = []
    for c in walk["cameras"]:
        cam_notes.append({
            "camera": c.get("camera"),
            "angle_to_field_deg": c.get("angle_to_field_deg"),
            "dist_to_field_cm": c.get("dist_to_field_cm"),
            "walkable_path_hits": c.get("walkable_path_hits"),
            "escher_path_hits": c.get("escher_path_hits"),
            "notes": c.get("notes"),
        })
    summary = {
        "wind": wind,
        "wind_after": wind_after,
        "bands_tuned": len(flowers),
        "uds": lighting.get("uds"),
        "hidden": len(hidden),
        "saved": saved,
        "escher_walks": walk.get("escher_walk_count"),
        "cams": cam_notes,
        "report": str(out),
    }
    print("P0_WALK " + json.dumps(summary, default=str))
    unreal.log("P0_WALK " + json.dumps(summary, default=str))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
