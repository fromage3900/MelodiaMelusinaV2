"""Convert Rainbow SpeedTree MIs onto MelodiaPlant_Wind_NikkiToon hybrid + fix placements.

Hybrid = duplicate of M_MelodiaPlant_Wind (SpeedTree wind intact) + MF_NikkiDreamGrade
wired into BaseColor. Band MIs reparented with wind snapshot restored + Nikki defaults.
Also snaps flower ISMs to island crowns and stabilizes PortfolioDress.
"""
from __future__ import annotations
import json
import math
import random
from datetime import datetime, timezone
from pathlib import Path
import unreal

EAL = unreal.EditorAssetLibrary
MEL = unreal.MaterialEditingLibrary
SRC_MASTER = "/Game/Melodia/_PROJECT/04_Materials/Plants/M_MelodiaPlant_Wind"
HYBRID_DIR = "/Game/EnvSandbox/Materials/Masters"
HYBRID_NAME = "M_MelodiaPlant_Wind_NikkiToon"
HYBRID = f"{HYBRID_DIR}/{HYBRID_NAME}"
MF_DREAM = "/Game/EnvSandbox/Materials/Functions/MF_NikkiDreamGrade"
BAND_PREFIX = "/Game/EnvSandbox/Materials/Instances/Flora/Rainbow/MI_RainbowSpeedTree_"
BANDS = [
    ("B0_Red", (1.0, 0.12, 0.16)),
    ("B1_Orange", (1.0, 0.42, 0.12)),
    ("B2_Gold", (1.0, 0.78, 0.18)),
    ("B3_Green", (0.28, 0.85, 0.35)),
    ("B4_Blue", (0.22, 0.42, 0.95)),
    ("B5_Indigo", (0.35, 0.28, 0.95)),
    ("B6_Violet", (0.82, 0.28, 1.0)),
]
WIND_SCALARS = [
    "SharedBend", "SharedOscillation", "SharedSpeed", "SharedTurbulence",
    "SharedFlexibility", "SharedIndependence", "SharedStartHeight",
    "Branch1Bend", "Branch1Oscillation", "Branch1Speed", "Branch1Turbulence",
    "Branch1Flexibility", "Branch1Independence", "Branch1StretchLimit",
    "RipplePlanar", "RippleDirectional", "RippleSpeed", "RippleFlexibility",
    "RippleIndependence", "RippleShimmer",
    "MelodiaWindResponse", "MelodiaWindSpatialScale", "MelodiaWindTravelSpeed", "MelodiaWindHueSeed",
]
WIND_SWITCHES = [
    "SharedEnable", "Branch1Enable", "RippleEnable", "RippleShimmerEnable", "Branch2Enable",
]
NIKKI_DEFAULTS = {
    "PastelLift": 0.28,
    "DreamSaturation": 0.22,
    "DreamContrast": -0.06,
    "DreamShadowLift": 0.10,
    "DreamIntensity": 0.55,
    "DreamWarmth": 0.08,
}
STABLE_WIND = {
    "SharedBend": 0.35, "SharedOscillation": 0.15, "SharedSpeed": 0.08,
    "SharedTurbulence": 0.05, "SharedFlexibility": 0.35, "SharedIndependence": 0.05,
    "SharedStartHeight": 0.05,
    "Branch1Bend": 0.25, "Branch1Oscillation": 0.12, "Branch1Speed": 0.10,
    "Branch1Turbulence": 0.04, "Branch1Flexibility": 0.40, "Branch1Independence": 0.05,
    "Branch1StretchLimit": 0.15,
    "RipplePlanar": 0.08, "RippleDirectional": 0.05, "RippleSpeed": 0.12,
    "RippleFlexibility": 0.25, "RippleIndependence": 0.05, "RippleShimmer": 0.02,
    "MelodiaWindResponse": 0.5, "MelodiaWindSpatialScale": 0.04, "MelodiaWindTravelSpeed": 1.0,
}
GHOST_ALBEDO = "/Game/EnvSandbox/Textures/Surreal/T_Surreal_GhostLotus_Albedo"
GHOST_NORMAL = "/Game/EnvSandbox/Textures/Surreal/T_Surreal_GhostLotus_Normal"
GHOST_EMISSIVE = "/Game/EnvSandbox/Textures/Surreal/T_Surreal_GhostLotus_Emissive"


def _label(a):
    try:
        return a.get_actor_label() or ""
    except Exception:
        return ""


def ensure_hybrid():
    """Duplicate MelodiaPlant_Wind and wire MF_NikkiDreamGrade into BaseColor."""
    rec = {"src": SRC_MASTER, "hybrid": HYBRID}
    if not EAL.does_asset_exist(SRC_MASTER):
        return {"ok": False, "error": "missing src master"}
    if EAL.does_asset_exist(HYBRID):
        m = EAL.load_asset(HYBRID)
        rec["existed"] = True
    else:
        if not EAL.does_directory_exist(HYBRID_DIR):
            EAL.make_directory(HYBRID_DIR)
        ok = EAL.duplicate_asset(SRC_MASTER, HYBRID)
        rec["duplicated"] = bool(ok)
        m = EAL.load_asset(HYBRID)
        if not m:
            return {"ok": False, "error": "duplicate failed", **rec}

    # Ensure Nikki scalar params exist on hybrid
    created_params = []
    for name, default in NIKKI_DEFAULTS.items():
        # Creating via expression if missing from scalar list
        names = [str(n) for n in MEL.get_scalar_parameter_names(m)]
        if name in names:
            continue
        try:
            p = MEL.create_material_expression(m, unreal.MaterialExpressionScalarParameter, -2400, 800 + 80 * len(created_params))
            p.set_editor_property("parameter_name", name)
            p.set_editor_property("default_value", float(default))
            try:
                p.set_editor_property("group", "Nikki")
            except Exception:
                pass
            created_params.append(name)
        except Exception as e:
            created_params.append(f"ERR:{name}:{e}")

    # DreamTint vector
    vec_names = []
    try:
        vec_names = [str(n) for n in MEL.get_vector_parameter_names(m)]
    except Exception:
        pass
    if "DreamTint" not in vec_names:
        try:
            vp = MEL.create_material_expression(m, unreal.MaterialExpressionVectorParameter, -2400, 1400)
            vp.set_editor_property("parameter_name", "DreamTint")
            vp.set_editor_property("default_value", unreal.LinearColor(1.0, 0.92, 0.98, 1.0))
            try:
                vp.set_editor_property("group", "Nikki")
            except Exception:
                pass
            created_params.append("DreamTint")
        except Exception as e:
            created_params.append(f"ERR:DreamTint:{e}")

    # Wire MF_NikkiDreamGrade if not already present
    mf_path = MF_DREAM
    already = False
    try:
        for e in MEL.get_material_expressions(m) or []:
            if "FunctionCall" in e.get_class().get_name():
                fn = e.get_editor_property("material_function")
                if fn and "MF_NikkiDreamGrade" in fn.get_path_name():
                    already = True
                    dream_call = e
                    break
    except Exception:
        already = False
        dream_call = None

    wire_notes = []
    if not already and EAL.does_asset_exist(mf_path):
        try:
            dream_call = MEL.create_material_expression(m, unreal.MaterialExpressionMaterialFunctionCall, -800, 200)
            dream_call.set_material_function(EAL.load_asset(mf_path))
            wire_notes.append("created_MF_NikkiDreamGrade_call")
        except Exception as e:
            # older API
            try:
                dream_call = MEL.create_material_expression(m, unreal.MaterialExpressionMaterialFunctionCall, -800, 200)
                dream_call.set_editor_property("material_function", EAL.load_asset(mf_path))
                wire_notes.append("created_MF_call_via_property")
            except Exception as e2:
                wire_notes.append(f"mf_call_failed:{e2}")
                dream_call = None

        # Find current BaseColor input expression
        try:
            base_node = MEL.get_material_property_input_node(m, unreal.MaterialProperty.MP_BASE_COLOR)
            base_out = None
            try:
                base_out = MEL.get_material_property_input_node_output_name(m, unreal.MaterialProperty.MP_BASE_COLOR)
            except Exception:
                base_out = ""
            wire_notes.append({"base_node": base_node.get_class().get_name() if base_node else None, "out": base_out})
            if dream_call and base_node:
                # Connect previous base → Dream BaseColorIn
                try:
                    MEL.connect_material_expressions(base_node, base_out or "", dream_call, "BaseColorIn")
                    wire_notes.append("connected_base_to_dream")
                except Exception as e:
                    # try unnamed pin
                    try:
                        MEL.connect_material_expressions(base_node, "", dream_call, "BaseColorIn")
                        wire_notes.append("connected_base_unnamed")
                    except Exception as e2:
                        wire_notes.append(f"connect_in_fail:{e2}")
                # Wire Nikki params into MF if pins exist
                names = {str(n): None for n in MEL.get_scalar_parameter_names(m)}
                # find param expressions by iterating
                param_exprs = {}
                for e in MEL.get_material_expressions(m) or []:
                    cn = e.get_class().get_name()
                    if "ScalarParameter" in cn:
                        try:
                            param_exprs[str(e.get_editor_property("parameter_name"))] = e
                        except Exception:
                            pass
                    if "VectorParameter" in cn:
                        try:
                            param_exprs[str(e.get_editor_property("parameter_name"))] = e
                        except Exception:
                            pass
                for pname, pin in (
                    ("PastelLift", "PastelLift"),
                    ("DreamSaturation", "DreamSaturation"),
                    ("DreamContrast", "DreamContrast"),
                    ("DreamShadowLift", "DreamShadowLift"),
                    ("DreamTint", "DreamTint"),
                ):
                    if pname in param_exprs:
                        try:
                            MEL.connect_material_expressions(param_exprs[pname], "", dream_call, pin)
                        except Exception:
                            pass
                # Connect dream result to BaseColor
                try:
                    MEL.connect_material_property(dream_call, "", unreal.MaterialProperty.MP_BASE_COLOR)
                    wire_notes.append("dream_to_basecolor")
                except Exception as e:
                    try:
                        MEL.connect_material_property(dream_call, "Result", unreal.MaterialProperty.MP_BASE_COLOR)
                        wire_notes.append("dream_Result_to_basecolor")
                    except Exception as e2:
                        wire_notes.append(f"dream_out_fail:{e2}")
        except Exception as e:
            wire_notes.append(f"base_probe_fail:{e}")

    try:
        MEL.recompile_material(m)
        rec["recompiled"] = True
    except Exception as e:
        rec["recompile_err"] = str(e)
    EAL.save_asset(HYBRID)
    # Verify Nikki params now visible
    sc = [str(n) for n in MEL.get_scalar_parameter_names(m)]
    rec.update({
        "ok": True,
        "created_params": created_params,
        "wire_notes": wire_notes,
        "has_PastelLift": "PastelLift" in sc,
        "has_DreamSaturation": "DreamSaturation" in sc,
        "has_SharedBend": "SharedBend" in sc,
        "has_MelodiaWindResponse": "MelodiaWindResponse" in sc,
    })
    return rec


def snapshot_mi(mi):
    snap = {"scalars": {}, "vectors": {}, "textures": {}, "switches": {}}
    try:
        for n in MEL.get_scalar_parameter_names(mi):
            sn = str(n)
            if sn in WIND_SCALARS or sn in NIKKI_DEFAULTS or "Melodia" in sn:
                try:
                    snap["scalars"][sn] = float(MEL.get_material_instance_scalar_parameter_value(mi, sn))
                except Exception:
                    pass
    except Exception:
        pass
    try:
        for n in MEL.get_vector_parameter_names(mi):
            sn = str(n)
            if "Tint" in sn or "Melodia" in sn or "Dream" in sn:
                try:
                    c = MEL.get_material_instance_vector_parameter_value(mi, sn)
                    snap["vectors"][sn] = [c.r, c.g, c.b, c.a]
                except Exception:
                    pass
    except Exception:
        pass
    try:
        for n in MEL.get_texture_parameter_names(mi):
            sn = str(n)
            try:
                t = MEL.get_material_instance_texture_parameter_value(mi, sn)
                snap["textures"][sn] = t.get_path_name() if t else None
            except Exception:
                pass
    except Exception:
        pass
    return snap


def convert_band(label, tint, hybrid_mat):
    path = BAND_PREFIX + label
    mi = EAL.load_asset(path)
    if not mi:
        return {"label": label, "ok": False, "error": "missing"}
    before = snapshot_mi(mi)
    parent_before = None
    try:
        p = mi.get_editor_property("parent")
        parent_before = p.get_path_name() if p else None
    except Exception:
        pass

    MEL.set_material_instance_parent(mi, hybrid_mat)

    # Restore wind scalars (prefer snapshot, else stable)
    for k, v in STABLE_WIND.items():
        val = before["scalars"].get(k, v)
        if k == "MelodiaWindHueSeed":
            idx = int(label[1])
            val = (idx + 1) / 14.0
        try:
            MEL.set_material_instance_scalar_parameter_value(mi, k, float(val))
        except Exception:
            pass
    # Switches
    for sw, state in (
        ("SharedEnable", True), ("Branch1Enable", True), ("RippleEnable", True),
        ("RippleShimmerEnable", False), ("Branch2Enable", False),
    ):
        try:
            MEL.set_material_instance_static_switch_parameter_value(mi, sw, state)
        except Exception:
            pass
    # Nikki defaults
    for k, v in NIKKI_DEFAULTS.items():
        try:
            MEL.set_material_instance_scalar_parameter_value(mi, k, float(v))
        except Exception:
            pass
    # Band tint on MelodiaWindRevealTint + DreamTint
    r, g, b = tint
    boost = 1.35 if "Red" in label or "Violet" in label else (0.75 if "Blue" in label else 1.1)
    br, bg, bb = min(1.5, r * boost), min(1.5, g * boost), min(1.5, b * boost)
    try:
        MEL.set_material_instance_vector_parameter_value(
            mi, "MelodiaWindRevealTint", unreal.LinearColor(br, bg, bb, 1.0))
    except Exception:
        pass
    try:
        MEL.set_material_instance_vector_parameter_value(
            mi, "DreamTint", unreal.LinearColor(br, bg, bb, 1.0))
    except Exception:
        pass
    # Textures
    for tex_name, tex_path in (
        ("ColorOpacity", GHOST_ALBEDO),
        ("NormalRoughness", GHOST_NORMAL),
        ("Subsurface", GHOST_EMISSIVE),
    ):
        if EAL.does_asset_exist(tex_path):
            try:
                MEL.set_material_instance_texture_parameter_value(mi, tex_name, EAL.load_asset(tex_path))
            except Exception:
                pass
    EAL.save_asset(path)
    after_sc = [str(n) for n in MEL.get_scalar_parameter_names(mi)]
    parent_after = None
    try:
        p = mi.get_editor_property("parent")
        parent_after = p.get_path_name() if p else None
    except Exception:
        pass
    return {
        "label": label,
        "ok": True,
        "parent_before": parent_before,
        "parent_after": parent_after,
        "has_nikki": "PastelLift" in after_sc or "DreamSaturation" in after_sc,
        "has_wind": "SharedBend" in after_sc,
        "snap_scalars": before["scalars"],
    }


def fix_flower_placements(svc, world, field):
    """Snap flower ISM Z to BrushifyIsland crowns; drop non-island / steep leftovers."""
    removed = 0
    snapped = 0
    for comp in list(field.get_components_by_class(unreal.InstancedStaticMeshComponent) or []):
        mesh = comp.get_editor_property("static_mesh")
        if not mesh or "GenericFlower" not in mesh.get_name():
            continue
        n = int(comp.get_instance_count())
        kill = []
        for i in range(n):
            try:
                xf = comp.get_instance_transform(i, True)
            except Exception:
                continue
            t = xf.translation
            hit = unreal.SystemLibrary.line_trace_single(
                world, unreal.Vector(t.x, t.y, t.z + 500), unreal.Vector(t.x, t.y, t.z - 3000),
                unreal.TraceTypeQuery.ECC_VISIBILITY, False, [],
                unreal.DrawDebugTrace.NONE, True,
                unreal.LinearColor.RED, unreal.LinearColor.GREEN, 0.0,
            )
            tup = hit.to_tuple() if hit else None
            if not tup or not tup[0]:
                kill.append(i)
                continue
            lab = tup[9].get_actor_label() if tup[9] else ""
            if not lab.startswith("BrushifyIsland_"):
                kill.append(i)
                continue
            if float(tup[5].z) < 0.65:
                kill.append(i)
                continue
            # snap to ground
            new_t = unreal.Transform(
                unreal.Vector(t.x, t.y, float(tup[4].z)),
                xf.rotation,
                xf.scale3d,
            )
            try:
                comp.update_instance_transform(i, new_t, True, True, True)
                snapped += 1
            except Exception:
                pass
        for i in sorted(kill, reverse=True):
            try:
                comp.remove_instance(i)
                removed += 1
            except Exception:
                pass
        try:
            comp.mark_render_state_dirty()
        except Exception:
            pass
    return {"removed": removed, "snapped": snapped}


def fix_dress_placements(svc, world):
    """Re-ground WC_PortfolioDress_* and cull floaters / bad hits."""
    fixed = []
    destroyed = []
    for a in list(svc.get_all_level_actors()):
        lab = _label(a)
        if not lab.startswith("WC_PortfolioDress_"):
            continue
        loc = a.get_actor_location()
        hit = unreal.SystemLibrary.line_trace_single(
            world, unreal.Vector(loc.x, loc.y, loc.z + 2000), unreal.Vector(loc.x, loc.y, loc.z - 4000),
            unreal.TraceTypeQuery.ECC_VISIBILITY, False, [],
            unreal.DrawDebugTrace.NONE, True,
            unreal.LinearColor.RED, unreal.LinearColor.GREEN, 0.0,
        )
        tup = hit.to_tuple() if hit else None
        if not tup or not tup[0]:
            svc.destroy_actor(a)
            destroyed.append(lab)
            continue
        glab = tup[9].get_actor_label() if tup[9] else ""
        if not (glab.startswith("Brushify") or glab.startswith("WC_EscherWalk_")):
            svc.destroy_actor(a)
            destroyed.append(lab)
            continue
        new_loc = unreal.Vector(tup[4].x, tup[4].y, tup[4].z)
        a.set_actor_location(new_loc, False, False)
        # normalize crazy scales
        try:
            s = a.get_actor_scale3d()
            sc = max(0.55, min(1.45, (s.x + s.y + s.z) / 3.0))
            a.set_actor_scale3d(unreal.Vector(sc, sc, sc))
        except Exception:
            pass
        fixed.append({"label": lab, "ground": glab, "z": new_loc.z})
    return {"fixed": fixed, "destroyed": destroyed, "remaining": len(fixed)}


def capture_plates(svc):
    names = [
        "WC_Lookdev_walk_deck_meadow",
        "WC_Lookdev_walk_deck_approach",
        "WC_Lookdev_website_oblique",
        "WC_Lookdev_website_south",
    ]
    uds = next((a for a in svc.get_all_level_actors() if _label(a) == "Ultra_Dynamic_Sky2"), None)
    if uds:
        try:
            uds.set_editor_property("Animate Time of Day", False)
            uds.set_editor_property("Time of Day", 1100.0)
            uds.set_editor_property("Cloud Coverage", 1.8)
            uds.set_editor_property("Sun Light Intensity", 5.5)
            uds.set_editor_property("Overall Intensity", 1.25)
        except Exception:
            pass
    world = unreal.get_editor_subsystem(unreal.UnrealEditorSubsystem).get_editor_world()
    out_dir = Path(unreal.Paths.project_dir()) / "Saved" / "Portfolio" / "Hero" / "MelusinaMorning"
    out_dir.mkdir(parents=True, exist_ok=True)
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
            for _ in range(4):
                comp.capture_scene()
            short = name.replace("WC_Lookdev_", "")
            fn = out_dir / ("hero_midmorning_%s_nikki_2026-09-20.png" % short)
            opts = unreal.ImageWriteOptions()
            opts.set_editor_property("format", unreal.DesiredImageFormat.PNG)
            opts.set_editor_property("overwrite_file", True)
            opts.set_editor_property("async_", False)
            unreal.ImageWriteBlueprintLibrary.export_to_disk(rt, str(fn).replace("\\", "/"), opts)
            shots.append({"name": short, "bytes": fn.stat().st_size if fn.exists() else 0, "file": str(fn)})
    finally:
        cap.destroy_actor()
    return shots


def main():
    hybrid = ensure_hybrid()
    hybrid_mat = EAL.load_asset(HYBRID) if hybrid.get("ok") else None
    bands = []
    if hybrid_mat:
        bands = [convert_band(lab, tint, hybrid_mat) for lab, tint in BANDS]

    svc = unreal.get_editor_subsystem(unreal.EditorActorSubsystem)
    world = unreal.get_editor_subsystem(unreal.UnrealEditorSubsystem).get_editor_world()
    field = next((a for a in svc.get_all_level_actors() if _label(a) == "WC_morning_rainbow_bloom_Field"), None)
    place = fix_flower_placements(svc, world, field) if field else {"error": "no field"}
    dress = fix_dress_placements(svc, world)
    shots = capture_plates(svc)

    try:
        unreal.get_editor_subsystem(unreal.LevelEditorSubsystem).save_current_level()
        saved = True
    except Exception as e:
        saved = str(e)

    report = {
        "generated_at": datetime.now(timezone.utc).isoformat(),
        "hybrid": hybrid,
        "bands": bands,
        "placements": place,
        "dress": dress,
        "shots": shots,
        "level_saved": saved,
        "note": "Hybrid keeps SpeedTree wind (Shared*/Branch*/Ripple*/MelodiaWind*) on MelodiaPlant_Wind duplicate; Nikki Dream grade MF + scalars added. Full Substrate Toon BSDF of M_Master_Toon_Universal is not the parent — that would drop SpeedTreeWind MF.",
    }
    out = Path(unreal.Paths.project_dir()) / "Saved" / "Audit" / "nikki_speedtree_hybrid_convert_2026-09-20.json"
    out.write_text(json.dumps(report, indent=2, default=str), encoding="utf-8")
    summary = {
        "hybrid_ok": hybrid.get("ok"),
        "has_nikki_and_wind": hybrid.get("has_PastelLift") and hybrid.get("has_SharedBend"),
        "bands_ok": sum(1 for b in bands if b.get("ok")),
        "bands_nikki": sum(1 for b in bands if b.get("has_nikki")),
        "bands_wind": sum(1 for b in bands if b.get("has_wind")),
        "place": place,
        "dress_remaining": dress.get("remaining"),
        "dress_destroyed": len(dress.get("destroyed") or []),
        "shots": [(s["name"], s["bytes"]) for s in shots],
        "saved": saved,
        "report": str(out),
        "wire": hybrid.get("wire_notes"),
    }
    print("NIKKI_HYBRID " + json.dumps(summary, default=str))
    unreal.log("NIKKI_HYBRID " + json.dumps(summary, default=str))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
