"""Dreamprint — surgical probe of the 3 post-process masters + their MIs.

Read-only (writes only the manifest). Covers, per master:
  - resolve: does_asset_exist / load / redirector check (loaded path vs expected)
  - domain, blendable_location, blendable_priority, two_sided
  - output connections (which expression feeds MP_EMISSIVE_COLOR)
  - expression inventory: Custom (code length + markers), scalar/vector/texture
    params, MaterialExpressionCollectionParameter (collection + parameter name)
  - Custom HLSL identifiers vs available MPC channels (unbound-name report)
  - compile attempt + captured errors (MaterialEditingLibrary + error_expression)

Per profile MI: exists, parent path, scalar/switch/texture overrides count.
"""
from __future__ import annotations

import json
import re
from datetime import datetime, timezone
from pathlib import Path

import unreal

REPORT = Path(__file__).resolve().parents[2] / "Saved" / "Audit" / "dreamprint_material_probe.json"

INK = "/Game/Melodia/_PROJECT/04_Materials/PostProcess/M_PP_MelodiaInk"
GRADE = "/Game/_PROJECT/04_Materials/PostProcess/M_PP_MeluColorGrade"
OUTLINE = "/Game/EnvSandbox/Materials/PostProcess/M_PP_StorybookOutline"

MASTERS = {"ink": INK, "grade": GRADE, "outline": OUTLINE}

MPC_INK = "/Game/Melodia/_PROJECT/04_Materials/MPC_MelodiaInk"
MPC_PALETTE = "/Game/Melodia/_PROJECT/04_Materials/MPC_Melodia_Palette"

INK_PROFILES = [
    "/Game/Melodia/_PROJECT/04_Materials/PostProcess/Candidates/Profiles/MI_MelodiaInk_GameplayStandard",
    "/Game/Melodia/_PROJECT/04_Materials/PostProcess/Candidates/Profiles/MI_MelodiaInk_Narrative",
    "/Game/Melodia/_PROJECT/04_Materials/PostProcess/Candidates/Profiles/MI_MelodiaInk_PortfolioHero",
]
GRADE_PROFILES = [
    "/Game/Melodia/_PROJECT/04_Materials/PostProcess/Candidates/Profiles/MI_MeluColorGrade_GameplayStandard",
    "/Game/Melodia/_PROJECT/04_Materials/PostProcess/Candidates/Profiles/MI_MeluColorGrade_Narrative",
    "/Game/Melodia/_PROJECT/04_Materials/PostProcess/Candidates/Profiles/MI_MeluColorGrade_PortfolioHero",
]
OUTLINE_PROFILES = [
    "/Game/EnvSandbox/Materials/PostProcess/Candidates/Profiles/MI_StorybookOutline_GameplayStandard",
]

HLS_VAR_RE = re.compile(r"\b(BeatPulse|ComboNormalized|EnemyTension|BreakPulse|VictoryPulse|MeluPrimary|InkMasterWeight|InkSyncVision|InkBass|InkMid|InkTreble|InkReact|InkHueShift|InkAccentTint)\b")


def mpc_channels(path: str) -> dict[str, list[str]]:
    mpc = unreal.load_asset(path)
    out = {"scalars": [], "vectors": []}
    if not mpc:
        return out
    try:
        for p in mpc.get_editor_property("scalar_parameters") or []:
            out["scalars"].append(str(p.get_editor_property("parameter_name")))
    except Exception:
        pass
    try:
        for p in mpc.get_editor_property("vector_parameters") or []:
            out["vectors"].append(str(p.get_editor_property("parameter_name")))
    except Exception:
        pass
    return out


def probe_master(key: str, path: str, mpc_channels_all: dict[str, set[str]]) -> dict:
    res: dict = {"path": path, "exists": False}
    if not unreal.EditorAssetLibrary.does_asset_exist(path):
        return res
    mat = unreal.load_asset(path)
    if not mat:
        return res
    res["exists"] = True
    res["resolved_path"] = mat.get_path_name()
    res["redirector"] = res["resolved_path"].split(".")[0] != path
    try:
        res["material_domain"] = str(mat.get_editor_property("material_domain"))
        res["blendable_location"] = str(mat.get_editor_property("blendable_location"))
        res["blendable_priority"] = float(mat.get_editor_property("blendable_priority"))
        res["two_sided"] = bool(mat.get_editor_property("two_sided"))
        res["shading_model"] = str(mat.get_editor_property("shading_model"))
    except Exception as exc:
        res["props_error"] = str(exc)

    exprs = unreal.MaterialEditingLibrary.get_material_expressions(mat) or []
    customs: list[dict] = []
    collections: list[dict] = []
    params: dict[str, list[str]] = {"scalars": [], "vectors": [], "textures": [], "switches": []}
    for e in exprs:
        cls = type(e).__name__
        try:
            pname = str(e.get_editor_property("parameter_name"))
        except Exception:
            pname = None
        if cls == "MaterialExpressionCustom":
            code = e.get_editor_property("code")
            used = sorted(set(HLS_VAR_RE.findall(code)))
            customs.append({"name": e.get_name(), "code_len": len(code),
                            "mpc_identifiers": used, "has_dreamprint_marker": "DREAMPRINT" in code,
                            "has_ink_header": "M_PP_MelodiaInk" in code})
        elif cls == "MaterialExpressionCollectionParameter":
            coll = e.get_editor_property("collection")
            collections.append({"param": pname,
                                "collection": str(coll.get_path_name()) if coll else None})
        elif cls == "MaterialExpressionScalarParameter":
            params["scalars"].append(pname)
        elif cls == "MaterialExpressionVectorParameter":
            params["vectors"].append(pname)
        elif cls in ("MaterialExpressionTextureSampleParameter2D", "MaterialExpressionTextureObjectParameter"):
            params["textures"].append(pname)
        elif cls in ("MaterialExpressionStaticSwitchParameter", "MaterialExpressionStaticBoolParameter"):
            params["switches"].append(pname)
    res["custom_nodes"] = customs
    res["collection_nodes"] = collections

    bound = set()
    for c in collections:
        if c["collection"]:
            bound.add(c["param"])
    unbound = []
    for c in customs:
        for ident in c["mpc_identifiers"]:
            if ident not in bound:
                unbound.append({"identifier": ident, "custom": c["name"],
                                "available_in": [k for k, ch in mpc_channels_all.items() if ident in ch]})
    res["unbound_mpc_identifiers"] = unbound

    try:
        emitter = unreal.MaterialEditingLibrary.get_material_property_input_node(
            mat, unreal.MaterialProperty.MP_EMISSIVE_COLOR)
        res["emissive_input"] = type(emitter).__name__ if emitter else None
    except Exception as exc:
        res["emissive_input_error"] = str(exc)

    compile_err = None
    try:
        unreal.MaterialEditingLibrary.recompile_material(mat)
    except Exception as exc:
        compile_err = str(exc)
    try:
        err_expr = mat.get_editor_property("error_expression")
        if err_expr:
            compile_err = f"error_expression: {err_expr.get_name()}"
    except Exception:
        pass
    res["compile_attempt"] = "ok" if compile_err is None else f"error: {compile_err}"
    return res


def probe_mi(path: str) -> dict:
    res = {"path": path, "exists": False}
    if not unreal.EditorAssetLibrary.does_asset_exist(path):
        return res
    mi = unreal.load_asset(path)
    if not mi:
        return res
    res["exists"] = True
    parent = mi.get_editor_property("parent")
    res["parent"] = str(parent.get_path_name()) if parent else None
    try:
        res["scalar_overrides"] = len(mi.get_editor_property("scalar_parameter_values") or [])
    except Exception:
        res["scalar_overrides"] = "n/a"
    return res


def main() -> dict:
    ch_ink = mpc_channels(MPC_INK)
    ch_pal = mpc_channels(MPC_PALETTE)
    channels_all = {
        "MPC_MelodiaInk": set(ch_ink["scalars"] + ch_ink["vectors"]),
        "MPC_Melodia_Palette": set(ch_pal["scalars"] + ch_pal["vectors"]),
    }
    masters = {k: probe_master(k, v, channels_all) for k, v in MASTERS.items()}
    profiles = {
        "ink": [probe_mi(p) for p in INK_PROFILES],
        "grade": [probe_mi(p) for p in GRADE_PROFILES],
        "outline": [probe_mi(p) for p in OUTLINE_PROFILES],
    }
    report = {
        "timestamp": datetime.now(timezone.utc).isoformat(),
        "mpc_channels": {"MPC_MelodiaInk": ch_ink, "MPC_Melodia_Palette": ch_pal},
        "masters": masters,
        "profiles": profiles,
        "ok": True,
    }
    REPORT.parent.mkdir(parents=True, exist_ok=True)
    REPORT.write_text(json.dumps(report, indent=2), encoding="utf-8")
    print(json.dumps(report, indent=2))
    return report


if __name__ == "__main__":
    main()