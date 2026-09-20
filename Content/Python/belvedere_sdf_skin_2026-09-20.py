# -*- coding: utf-8 -*-
"""Belvedere SDF skin — apply fake-SDF MIs to WC_GreySpire_* / WC_GreyGrotto_* only.
Does NOT touch roads, lake, PCG, cams, PPV, NS_Morning_*, or non-WC_Grey* actors.
"""
from __future__ import annotations
import json
from datetime import datetime, timezone
from pathlib import Path
import unreal

EAL = unreal.EditorAssetLibrary
OUT = Path(unreal.Paths.project_saved_dir()) / "Audit" / "belvedere_sdf_skin_2026-09-20.json"

MATS = {
    "shaft": "/Game/EnvSandbox/Materials/Instances/SDFArchitecture/MI_SDF_CrystallineSpire",
    # fallbacks if Architecture MI missing
    "shaft_fb": "/Game/EnvSandbox/Materials/SDF/Instances/MI_SDF_CrystallineSpire",
    "portal": "/Game/EnvSandbox/Materials/Masters/SDF/M_SDF_CosmicPortal",
    "musical": "/Game/EnvSandbox/Materials/Instances/SDFArchitecture/MI_SDF_Musical",
    "rose": "/Game/EnvSandbox/Materials/Instances/SDFArchitecture/MI_SDF_RoseWindow",
    "penrose": "/Game/EnvSandbox/Materials/Instances/SDFArchitecture/MI_SDF_Penrose_Stairs",
    "caustics": "/Game/EnvSandbox/Materials/SDF/Instances/MI_SDF_Caustics_Underwater_Shallow",
    "caustics_fb": "/Game/EnvSandbox/Materials/Masters/SDF/M_SDF_Caustics_Underwater",
    "anemone": "/Game/EnvSandbox/Materials/Masters/SDF/M_SDF_Anemone",
    "kelp": "/Game/EnvSandbox/Materials/Masters/SDF/M_SDF_KelpCurtain",
    "road_neutral": None,  # leave greybox / soft-tune later
}


def _label(a):
    try:
        return a.get_actor_label() or ""
    except Exception:
        return ""


def _load(path):
    if not path:
        return None
    if EAL.does_asset_exist(path):
        return EAL.load_asset(path)
    return None


def _load_first(*paths):
    for p in paths:
        m = _load(p)
        if m:
            return p, m
    return None, None


def _role_for(lab: str):
    if "PortalCard" in lab or lab.endswith("PortalCard"):
        return "portal"
    if lab == "WC_GreySpire_Shaft" or lab.startswith("WC_GreySpire_Shaft"):
        return "shaft"
    if "Chamber" in lab and lab.startswith("WC_GreySpire_"):
        # Floor / ceiling / walls — distribute portal/musical/rose
        if "Floor" in lab or "Ceil" in lab:
            return "portal"
        if lab.endswith("_N") or lab.endswith("_S"):
            return "musical"
        return "rose"
    if lab.startswith("WC_GreySpire_Helix") or "Helix" in lab or "Penrose" in lab or "Landing" in lab:
        return "penrose"
    if lab.startswith("WC_GreyGrotto_"):
        if "Portal" in lab or "Twin" in lab:
            return "portal"
        if "Anemone" in lab or lab.endswith("_02") or lab.endswith("_05"):
            return "anemone"
        if "Kelp" in lab or lab.endswith("_03") or lab.endswith("_06"):
            return "kelp"
        return "caustics"
    if lab.startswith("WC_GreyRoad_"):
        return "skip_road"
    return "skip"


def _apply_mat(actor, mat):
    if not mat:
        return False
    try:
        comps = list(actor.get_components_by_class(unreal.StaticMeshComponent) or [])
    except Exception:
        comps = []
        c = actor.get_component_by_class(unreal.StaticMeshComponent)
        if c:
            comps = [c]
    ok = False
    for comp in comps:
        try:
            n = int(comp.get_num_materials())
        except Exception:
            n = 1
        for i in range(max(1, n)):
            try:
                comp.set_material(i, mat)
                ok = True
            except Exception:
                pass
    return ok


def main():
    loaded = {}
    for key, path in (
        ("shaft", MATS["shaft"]),
        ("portal", MATS["portal"]),
        ("musical", MATS["musical"]),
        ("rose", MATS["rose"]),
        ("penrose", MATS["penrose"]),
        ("caustics", MATS["caustics"]),
        ("anemone", MATS["anemone"]),
        ("kelp", MATS["kelp"]),
    ):
        p, m = _load_first(path, MATS.get(key + "_fb"), MATS.get("shaft_fb") if key == "shaft" else None)
        loaded[key] = {"path": p, "ok": m is not None}
        if key == "shaft" and not m:
            p, m = _load_first(MATS["shaft_fb"])
            loaded[key] = {"path": p, "ok": m is not None}
        if key == "caustics" and not m:
            p, m = _load_first(MATS["caustics_fb"])
            loaded[key] = {"path": p, "ok": m is not None}
        loaded[key]["_mat"] = m

    svc = unreal.get_editor_subsystem(unreal.EditorActorSubsystem)
    report = {
        "schema": "melodia.belvedere_sdf_skin.v1",
        "generated_at": datetime.now(timezone.utc).isoformat(),
        "loaded": {k: {"path": v["path"], "ok": v["ok"]} for k, v in loaded.items()},
        "applied": [],
        "skipped": [],
        "missing_mat_roles": [],
    }

    for a in svc.get_all_level_actors():
        lab = _label(a)
        if not (lab.startswith("WC_GreySpire_") or lab.startswith("WC_GreyGrotto_")):
            continue
        role = _role_for(lab)
        if role.startswith("skip"):
            report["skipped"].append({"label": lab, "reason": role})
            continue
        entry = loaded.get(role) or {}
        mat = entry.get("_mat")
        if not mat:
            report["missing_mat_roles"].append({"label": lab, "role": role})
            continue
        ok = _apply_mat(a, mat)
        report["applied"].append({
            "label": lab,
            "role": role,
            "mat": entry.get("path"),
            "ok": ok,
        })

    # Soft-set AudioReactivity on MICs if present (safe no-op)
    try:
        mel = unreal.MaterialEditingLibrary
        for key in ("musical", "portal", "penrose", "caustics", "anemone"):
            mat = loaded.get(key, {}).get("_mat")
            if mat and isinstance(mat, unreal.MaterialInstanceConstant):
                for pname, pval in (("AudioReactivity", 0.35), ("GlowAmount", 0.25), ("GlowStrength", 0.3)):
                    try:
                        mel.set_material_instance_scalar_parameter_value(mat, pname, float(pval))
                    except Exception:
                        pass
    except Exception as e:
        report["audio_reactivity_note"] = str(e)

    try:
        unreal.get_editor_subsystem(unreal.LevelEditorSubsystem).save_current_level()
        report["level_saved"] = True
    except Exception as e:
        report["level_saved"] = str(e)

    report["counts"] = {
        "applied": len(report["applied"]),
        "skipped": len(report["skipped"]),
        "missing": len(report["missing_mat_roles"]),
    }
    OUT.parent.mkdir(parents=True, exist_ok=True)
    OUT.write_text(json.dumps(report, indent=2, default=str), encoding="utf-8")
    print("BELVEDERE_SDF_SKIN " + json.dumps(report["counts"]))
    unreal.log("BELVEDERE_SDF_SKIN " + json.dumps(report["counts"]))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())

