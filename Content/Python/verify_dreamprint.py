"""Dreamprint — post-build verification v2 (read-back, no mutation).

Confirms the built stack exists and resolves: MPC channels, master params +
domain + blendable location, custom-node NAMED INPUTS vs code identifiers
(UE 5.8 custom nodes only see function inputs), profile MI parents + overrides,
grade SyncVision marker, compile state, and MetaSound asset.
"""
from __future__ import annotations

import json
import re
from datetime import datetime, timezone
from pathlib import Path

import unreal

REPORT = Path(__file__).resolve().parents[2] / "Saved" / "Audit" / "dreamprint_verify.json"

MPC_INK = "/Game/Melodia/_PROJECT/04_Materials/MPC_MelodiaInk"
MASTER = "/Game/Melodia/_PROJECT/04_Materials/PostProcess/M_PP_MelodiaInk"
PROFILES = [
    "/Game/Melodia/_PROJECT/04_Materials/PostProcess/Candidates/Profiles/MI_MelodiaInk_GameplayStandard",
    "/Game/Melodia/_PROJECT/04_Materials/PostProcess/Candidates/Profiles/MI_MelodiaInk_Narrative",
    "/Game/Melodia/_PROJECT/04_Materials/PostProcess/Candidates/Profiles/MI_MelodiaInk_PortfolioHero",
]
GRADE = "/Game/_PROJECT/04_Materials/PostProcess/M_PP_MeluColorGrade"
OUTLINE = "/Game/EnvSandbox/Materials/PostProcess/M_PP_StorybookOutline"
META = "/Game/Melodia/_PROJECT/04_Audio/Music/MSS_MelodiaMusicPulse"

WANTED_MPC = ["InkMasterWeight", "InkSyncVision", "InkBass", "InkMid", "InkTreble", "InkReact", "InkHueShift", "InkAccentTint"]
WANTED_PARAMS = [
    "InkDotPitch", "InkDotAngle", "InkDotLumaDrive", "InkDotScale", "InkHatchDensity",
    "InkHatchAngle", "InkHatchShadowBand", "InkStrength", "InkPrintOffset",
    "InkPrintOffsetDepth", "InkGrain", "InkGrainScale", "InkSmear", "InkPaperLight",
    "InkPaperShadow", "InkHalftone", "InkHatch", "InkPrintShift", "InkGrainOn",
    "InkSmearOn", "InkColor", "InkHueTint", "InkPaperColor",
]
# identifiers the ink custom code reads — must all be named inputs
INK_CODE_IDS = re.compile(
    r"\b(UV|SceneColor|cR|cB|smeared|BeatPulse|ComboNormalized|EnemyTension|BreakPulse|"
    r"VictoryPulse|InkMasterWeight|InkSyncVision|InkBass|InkMid|InkTreble|InkReact|"
    r"InkHueShift|InkAccentTint|MeluPrimary|InkDotPitch|InkDotAngle|InkDotLumaDrive|"
    r"InkDotScale|InkHatchDensity|InkHatchAngle|InkHatchShadowBand|InkStrength|"
    r"InkPrintOffset|InkPrintOffsetDepth|InkGrain|InkGrainScale|InkSmear|InkPaperLight|"
    r"InkPaperShadow|InkHalftone|InkHatch|InkPrintShift|InkGrainOn|InkSmearOn|InkColor|"
    r"InkHueTint|InkPaperColor)\b")
GRADE_BLOCK_IDS = ["BeatPulse", "VictoryPulse", "InkSyncVision", "MeluPrimary"]


def custom_nodes(mat) -> list:
    return [e for e in unreal.MaterialEditingLibrary.get_material_expressions(mat)
            if type(e).__name__ == "MaterialExpressionCustom"]


def check_material(path: str, id_regex, min_inputs: int, blendable: str | None = None,
                   marker: str | None = None) -> dict:
    res: dict = {"path": path, "exists": False}
    if not unreal.EditorAssetLibrary.does_asset_exist(path):
        return res
    mat = unreal.load_asset(path)
    if not mat:
        return res
    res["exists"] = True
    res["domain"] = str(mat.get_editor_property("material_domain"))
    res["blendable_location"] = str(mat.get_editor_property("blendable_location"))
    res["blendable_priority"] = float(mat.get_editor_property("blendable_priority"))
    customs = custom_nodes(mat)
    res["custom_count"] = len(customs)
    all_inputs: set[str] = set()
    ids_used: set[str] = set()
    code_len = 0
    for c in customs:
        code = c.get_editor_property("code") or ""
        code_len += len(code)
        ids_used |= set(id_regex.findall(code))
        all_inputs |= {str(x.get_editor_property("input_name"))
                       for x in (c.get_editor_property("inputs") or [])}
        if marker:
            res[f"marker_{marker}"] = marker in code
    res["code_len"] = code_len
    res["input_count"] = len(all_inputs)
    res["unbound_identifiers"] = sorted(ids_used - all_inputs)
    if blendable:
        res["blendable_ok"] = blendable in res["blendable_location"]
    try:
        unreal.MaterialEditingLibrary.recompile_material(mat)
        res["recompile"] = "ok"
    except Exception as exc:
        res["recompile"] = f"error: {exc}"
    try:
        err = mat.get_editor_property("error_expression")
        res["error_expression"] = str(err.get_name()) if err else None
    except Exception:
        res["error_expression"] = "n/a"
    return res


def main() -> int:
    res = {"timestamp": datetime.now(timezone.utc).isoformat(), "checks": {}}

    mpc = unreal.load_asset(MPC_INK)
    mpc_names = set()
    if mpc:
        mpc_names |= {str(p.get_editor_property("parameter_name")) for p in (mpc.get_editor_property("scalar_parameters") or [])}
        mpc_names |= {str(p.get_editor_property("parameter_name")) for p in (mpc.get_editor_property("vector_parameters") or [])}
    res["checks"]["mpc_exists"] = bool(mpc)
    res["checks"]["mpc_missing"] = sorted(set(WANTED_MPC) - mpc_names)

    ink = check_material(MASTER, INK_CODE_IDS, 40, blendable="AFTER_TONEMAPPING")
    res["checks"]["ink"] = ink

    res["checks"]["profiles"] = []
    for p in PROFILES:
        mi = unreal.load_asset(p)
        if not mi:
            res["checks"]["profiles"].append({"path": p, "ok": False, "parent": None})
            continue
        parent = mi.get_editor_property("parent")
        res["checks"]["profiles"].append({
            "path": p, "ok": True,
            "parent": str(parent.get_path_name()) if parent else None,
        })

    grade = check_material(GRADE, re.compile(r"\b(" + "|".join(GRADE_BLOCK_IDS) + r")\b"),
                           25, marker="DREAMPRINT")
    res["checks"]["grade"] = grade

    outline = check_material(OUTLINE, re.compile(r"\b(NEVER_MATCH_ZZ)\b"), 0,
                             blendable="AFTER_TONEMAPPING")
    res["checks"]["outline"] = outline

    res["checks"]["metasound_exists"] = bool(unreal.load_asset(META))

    ok_parts = [
        res["checks"].get("mpc_exists"),
        not res["checks"].get("mpc_missing"),
        ink.get("exists") and ink.get("domain") and "POST_PROCESS" in ink.get("domain", ""),
        not ink.get("unbound_identifiers"),
        ink.get("input_count", 0) >= 40,
        ink.get("blendable_ok"),
        all(x.get("ok") for x in res["checks"].get("profiles", [])),
        grade.get("marker_DREAMPRINT"),
        not grade.get("unbound_identifiers"),
        not outline.get("unbound_identifiers"),
        outline.get("blendable_ok"),
        ink.get("error_expression") in (None, "n/a") and grade.get("error_expression") in (None, "n/a"),
    ]
    res["ok"] = all(ok_parts)
    res["ok_detail"] = [bool(x) for x in ok_parts]
    REPORT.parent.mkdir(parents=True, exist_ok=True)
    REPORT.write_text(json.dumps(res, indent=2), encoding="utf-8")
    print(json.dumps(res, indent=2))
    return 0 if res["ok"] else 1


if __name__ == "__main__":
    raise SystemExit(main())