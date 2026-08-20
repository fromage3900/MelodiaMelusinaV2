"""Find missing textures on: (1) the dreamprint PP stack materials + MIs,
(2) every material used by ZenForestTest meshes/landscape.

A material whose texture param resolves to nothing renders the engine default
(checker/brick) texture — the visible 'default brick' in the viewport.
"""
from __future__ import annotations

import json
from datetime import datetime, timezone
from pathlib import Path

import unreal

REPORT = Path(__file__).resolve().parents[2] / "Saved" / "Audit" / "missing_texture_audit.json"

PP_STACK = (
    "/Game/EnvSandbox/Materials/PostProcess/Candidates/M_PP_StorybookOutline_Premium_Candidate",
    "/Game/EnvSandbox/Materials/PostProcess/Candidates/Profiles/MI_StorybookOutline_GameplayStandard",
    "/Game/_PROJECT/04_Materials/PostProcess/M_PP_MeluColorGrade",
    "/Game/Melodia/_PROJECT/04_Materials/PostProcess/Candidates/Profiles/MI_MeluColorGrade_GameplayStandard",
    "/Game/Melodia/_PROJECT/04_Materials/PostProcess/M_PP_MelodiaInk",
    "/Game/Melodia/_PROJECT/04_Materials/PostProcess/Candidates/Profiles/MI_MelodiaInk_GameplayStandard",
)

TEX_PARAM_CLASSES = ("MaterialExpressionTextureSampleParameter2D",
                     "MaterialExpressionTextureObjectParameter")


def texture_refs(obj) -> list[dict]:
    refs: list[dict] = []
    if type(obj).__name__ == "MaterialInstanceConstant":
        try:
            for pv in obj.get_editor_property("texture_parameter_values") or []:
                tex = pv.get_editor_property("parameter_value")
                refs.append({"param": str(pv.get_editor_property("parameter_name")),
                             "tex": str(tex.get_path_name()) if tex else None,
                             "source": "mi_override"})
        except Exception:
            pass
        parent = obj.get_editor_property("parent")
        if parent:
            refs += [dict(r, source="parent_default") for r in texture_refs(parent)]
        return refs
    for e in unreal.MaterialEditingLibrary.get_material_expressions(obj) or []:
        if type(e).__name__ not in TEX_PARAM_CLASSES:
            continue
        try:
            tex = e.get_editor_property("texture")
            refs.append({"param": str(e.get_editor_property("parameter_name")),
                         "tex": str(tex.get_path_name()) if tex else None,
                         "source": "master_default"})
        except Exception:
            continue
    return refs


def check_refs(refs: list[dict], owner: str) -> list[dict]:
    bad = []
    seen = set()
    for r in refs:
        key = (r["param"], r["source"])
        if key in seen:
            continue
        seen.add(key)
        tex = r["tex"]
        if not tex:
            bad.append({**r, "owner": owner, "reason": "no texture assigned"})
            continue
        pkg = tex.split(".")[0]
        if not unreal.EditorAssetLibrary.does_asset_exist(pkg):
            bad.append({**r, "owner": owner, "reason": f"asset missing: {pkg}"})
    return bad


def main() -> dict:
    results: list[dict] = []

    for path in PP_STACK:
        obj = unreal.load_asset(path)
        if not obj:
            results.append({"owner": path, "status": "missing_asset"})
            continue
        bad = check_refs(texture_refs(obj), path)
        results.append({"owner": path, "status": "ok" if not bad else "missing_textures",
                        "bad": bad})

    # ZenForestTest: materials on mesh slots + landscape
    les = unreal.get_editor_subsystem(unreal.LevelEditorSubsystem)
    eas = unreal.get_editor_subsystem(unreal.EditorActorSubsystem)
    les.load_level("/Game/ZenForestTest")
    zen_mats: dict[str, str] = {}
    for actor in eas.get_all_level_actors() or []:
        for comp in actor.get_components_by_class(unreal.PrimitiveComponent) or []:
            cn = type(comp).__name__
            mats = []
            if cn == "LandscapeComponent":
                try:
                    lm = comp.get_editor_property("landscape_material")
                    mats = [lm] if lm else []
                except Exception:
                    continue
            else:
                try:
                    mats = list(comp.get_editor_property("override_materials") or [])
                except Exception:
                    try:
                        mats = list(comp.get_editor_property("materials") or [])
                    except Exception:
                        continue
            for m in mats:
                if m:
                    zen_mats[str(m.get_path_name()).split(".")[0]] = cn

    zen_bad = []
    for mat_path in sorted(zen_mats):
        obj = unreal.load_asset(mat_path)
        if not obj:
            continue
        if type(obj).__name__ not in ("Material", "MaterialInstanceConstant"):
            zen_bad.append({"owner": mat_path, "reason": f"slot holds non-material: {type(obj).__name__}"})
            continue
        zen_bad += check_refs(texture_refs(obj), mat_path)

    report = {
        "timestamp": datetime.now(timezone.utc).isoformat(),
        "pp_stack": results,
        "zenforest_materials_checked": len(zen_mats),
        "zenforest_bad_textures": zen_bad,
        "ok": all(r.get("status") == "ok" for r in results) and not zen_bad,
    }
    REPORT.parent.mkdir(parents=True, exist_ok=True)
    REPORT.write_text(json.dumps(report, indent=2), encoding="utf-8")
    print(json.dumps(report, indent=2))
    return report


if __name__ == "__main__":
    main()