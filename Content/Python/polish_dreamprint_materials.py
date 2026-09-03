"""Dreamprint — apply final wiring polish to M_PP_MelodiaInk + M_PP_MeluColorGrade.

1. M_PP_MelodiaInk:
   - replace Custom code with the wired build_dreamprint_material.CODE (dead
     params InkPaperLight/InkHatchShadowBand/InkPaperColor now consumed;
     InkMid/InkHueShift/InkAccentTint consumers added; all identity-at-default)
   - reassert scalar defaults InkPaperLight=1.0, InkHatchShadowBand=1.0
   - add MaterialExpressionCollectionParameter nodes for MPC_MelodiaInk and
     MPC_Melodia_Palette (Custom HLSL names cannot resolve without the
     collection reference — probe 2026-08-18 showed zero collection nodes)
2. M_PP_MeluColorGrade:
   - add MPC_MelodiaInk collection node (dreamprint block's InkSyncVision was
     unbound; MPC_Melodia_Palette already referenced)

Idempotent. Manifest: Saved/Audit/dreamprint_material_polish.json
"""
from __future__ import annotations

import importlib
import json
from datetime import datetime, timezone
from pathlib import Path

import unreal

import material_lib as lib
import build_dreamprint_material as bdm

importlib.reload(bdm)

REPORT = Path(__file__).resolve().parents[2] / "Saved" / "Audit" / "dreamprint_material_polish.json"

INK = "/Game/Melodia/_PROJECT/04_Materials/PostProcess/M_PP_MelodiaInk"
GRADE = "/Game/_PROJECT/04_Materials/PostProcess/M_PP_MeluColorGrade"
MPC_INK = "/Game/Melodia/_PROJECT/04_Materials/MPC_MelodiaInk"
MPC_PALETTE = "/Game/Melodia/_PROJECT/04_Materials/MPC_Melodia_Palette"

MARKERS = ("// ===== 7. PAPER TONE", "accentMix", "InkHatchShadowBand", "midInk")


def has_collection_ref(mat: unreal.Material, collection_path: str) -> bool:
    for e in unreal.MaterialEditingLibrary.get_material_expressions(mat) or []:
        if type(e).__name__ != "MaterialExpressionCollectionParameter":
            continue
        coll = e.get_editor_property("collection")
        if coll and str(coll.get_path_name()).split(".")[0] == collection_path:
            return True
    return False


def ensure_collection_ref(mat: unreal.Material, collection_path: str, param_name: str) -> dict:
    if has_collection_ref(mat, collection_path):
        return {"ok": True, "created": False}
    lib.collection_param(mat, collection_path, param_name, -600, 900)
    return {"ok": True, "created": True}


def set_scalar_default(mat: unreal.Material, name: str, value: float) -> bool:
    for e in unreal.MaterialEditingLibrary.get_material_expressions(mat) or []:
        try:
            if type(e).__name__ == "MaterialExpressionScalarParameter" \
                    and str(e.get_editor_property("parameter_name")) == name:
                e.set_editor_property("default_value", value)
                return True
        except Exception:
            continue
    return False


def apply_ink() -> dict:
    mat = unreal.load_asset(INK)
    out: dict = {"path": INK}
    customs = [e for e in unreal.MaterialEditingLibrary.get_material_expressions(mat)
               if type(e).__name__ == "MaterialExpressionCustom"]
    if not customs:
        out["error"] = "no Custom node"
        return out
    custom = customs[0]
    before_len = len(custom.get_editor_property("code"))
    custom.set_editor_property("code", bdm.CODE)
    out["code_before_len"] = before_len
    out["code_after_len"] = len(bdm.CODE)
    out["markers"] = {m: m in bdm.CODE for m in MARKERS}
    out["defaults"] = {
        "InkPaperLight": set_scalar_default(mat, "InkPaperLight", 1.0),
        "InkHatchShadowBand": set_scalar_default(mat, "InkHatchShadowBand", 1.0),
    }
    out["added_collections"] = {
        "MPC_MelodiaInk": ensure_collection_ref(mat, MPC_INK, "InkMasterWeight"),
        "MPC_Melodia_Palette": ensure_collection_ref(mat, MPC_PALETTE, "BeatPulse"),
    }
    try:
        unreal.MaterialEditingLibrary.recompile_material(mat)
        out["compile"] = "ok"
    except Exception as exc:
        out["compile"] = f"error: {exc}"
    unreal.EditorAssetLibrary.save_loaded_asset(mat, only_if_is_dirty=False)
    reread = {str(e.get_editor_property("parameter_name"))
              for e in unreal.MaterialEditingLibrary.get_material_expressions(mat)
              if type(e).__name__ == "MaterialExpressionCollectionParameter"}
    out["collection_nodes_after"] = sorted(reread)
    out["ok"] = all(out["markers"].values()) \
        and out["added_collections"]["MPC_MelodiaInk"]["ok"] \
        and out["added_collections"]["MPC_Melodia_Palette"]["ok"]
    return out


def apply_grade() -> dict:
    mat = unreal.load_asset(GRADE)
    out: dict = {"path": GRADE}
    out["added_collections"] = {
        "MPC_MelodiaInk": ensure_collection_ref(mat, MPC_INK, "InkSyncVision"),
    }
    try:
        unreal.MaterialEditingLibrary.recompile_material(mat)
        out["compile"] = "ok"
    except Exception as exc:
        out["compile"] = f"error: {exc}"
    unreal.EditorAssetLibrary.save_loaded_asset(mat, only_if_is_dirty=False)
    out["ok"] = out["added_collections"]["MPC_MelodiaInk"]["ok"]
    return out


def main() -> dict:
    ink = apply_ink()
    grade = apply_grade()
    report = {
        "timestamp": datetime.now(timezone.utc).isoformat(),
        "ink": ink,
        "grade": grade,
        "ok": ink.get("ok") and grade.get("ok"),
    }
    REPORT.parent.mkdir(parents=True, exist_ok=True)
    REPORT.write_text(json.dumps(report, indent=2), encoding="utf-8")
    print(json.dumps(report, indent=2))
    return report


if __name__ == "__main__":
    raise SystemExit(0 if main().get("ok") else 1)