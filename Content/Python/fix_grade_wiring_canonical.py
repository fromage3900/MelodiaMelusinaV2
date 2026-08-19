"""FINISH WIRING M_PP_MeluColorGrade (canonical master) — 2026-08-18.

Root cause: the grading params were renamed to Dream* but the custom node's
inputs kept the old names (Saturation, Contrast, ...) and the old param
expressions no longer exist — 16 inputs dangle and read 0; the MIs' overrides
for those names were silent no-ops.

Fix (semantics-preserving, zero look risk):
  1. Recreate the missing grading params on the master with defaults = the
     exact values the dead MI overrides encode (the owner's original intent).
  2. Wire every grading input pin from its source expression (set-then-connect
     order, proven in the ink lab).
  3. Remove the meaningless engine-litter override RefractionDepthBias from the
     two MIs that carry it (PP materials have no such param).

Manifest: Saved/Audit/grade_wiring_canonical.json
"""
from __future__ import annotations

import json
from datetime import datetime, timezone
from pathlib import Path

import unreal

import material_lib as lib

REPORT = Path(__file__).resolve().parents[2] / "Saved" / "Audit" / "grade_wiring_canonical.json"

GRADE = "/Game/_PROJECT/04_Materials/PostProcess/M_PP_MeluColorGrade"
GRADE_MIS = (
    "/Game/Melodia/_PROJECT/04_Materials/PostProcess/Candidates/Profiles/MI_MeluColorGrade_GameplayStandard",
    "/Game/Melodia/_PROJECT/04_Materials/PostProcess/Candidates/Profiles/MI_MeluColorGrade_Narrative",
    "/Game/Melodia/_PROJECT/04_Materials/PostProcess/Candidates/Profiles/MI_MeluColorGrade_PortfolioHero",
)

# input pin -> (create param with default | feed from existing param)
NEW_PARAMS = {
    "GradeStrength": 0.69,
    "Saturation": 0.15,
    "Contrast": 0.08,
    "ShadowLift": 0.05,
    "HighlightSoft": 2.0,
    "SplitStrength": 0.2,
    "SpectralStrength": 0.05,
    "SpectralCycles": 3.0,
}
FEED_FROM = {
    "VignetteIntensity": "VignetteBaseIntensity",
    "BeatResponse": "BeatPaletteResponse",
}
REASSERT = ("VignetteFalloff", "VignetteBlurStrength", "VignetteBlurRadiusPx",
            "VignetteFeather", "VignettePigmentBlend", "EmissiveResponse")

DROP_OVERRIDES = {"RefractionDepthBias"}


def main() -> dict:
    mat = unreal.load_asset(GRADE)
    if not mat:
        raise RuntimeError(f"missing {GRADE}")
    by_name: dict[str, unreal.MaterialExpression] = {}
    for e in unreal.MaterialEditingLibrary.get_material_expressions(mat) or []:
        try:
            by_name[str(e.get_editor_property("parameter_name"))] = e
        except Exception:
            continue

    customs = [e for e in unreal.MaterialEditingLibrary.get_material_expressions(mat)
               if type(e).__name__ == "MaterialExpressionCustom"]
    custom = customs[0]
    input_names = {str(x.get_editor_property("input_name"))
                   for x in (custom.get_editor_property("inputs") or [])}

    created = []
    for name, default in NEW_PARAMS.items():
        if name not in input_names:
            continue
        if name not in by_name:
            p = lib.scalar_param(mat, name, "V3 Adaptive", default, -1500, 2600)
            by_name[name] = p
            created.append(name)
        unreal.MaterialEditingLibrary.connect_material_expressions(by_name[name], "", custom, name)

    fed = []
    for pin, src_param in FEED_FROM.items():
        if pin not in input_names or src_param not in by_name:
            continue
        unreal.MaterialEditingLibrary.connect_material_expressions(by_name[src_param], "", custom, pin)
        fed.append(f"{pin}<-{src_param}")

    reasserted = []
    for pin in REASSERT:
        if pin in input_names and pin in by_name:
            unreal.MaterialEditingLibrary.connect_material_expressions(by_name[pin], "", custom, pin)
            reasserted.append(pin)

    # strip engine-litter overrides from the MIs
    mi_changes = []
    for mi_path in GRADE_MIS:
        mi = unreal.load_asset(mi_path)
        if not mi:
            continue
        sv = list(mi.get_editor_property("scalar_parameter_values") or [])
        kept, dropped = [], []
        for pv in sv:
            try:
                info = pv.get_editor_property("parameter_info")
                name = str(info.get_editor_property("name"))
            except Exception:
                kept.append(pv)
                continue
            if name in DROP_OVERRIDES:
                dropped.append(name)
            else:
                kept.append(pv)
        if dropped:
            mi.set_editor_property("scalar_parameter_values", kept)
            unreal.MaterialEditingLibrary.update_material_instance(mi)
            unreal.EditorAssetLibrary.save_loaded_asset(mi, only_if_is_dirty=False)
            mi_changes.append({"mi": mi_path, "dropped": dropped})

    try:
        unreal.MaterialEditingLibrary.recompile_material(mat)
        compile_ok = True
        compile_err = None
    except Exception as exc:
        compile_ok = False
        compile_err = str(exc)
    unreal.EditorAssetLibrary.save_loaded_asset(mat, only_if_is_dirty=False)

    report = {
        "timestamp": datetime.now(timezone.utc).isoformat(),
        "material": GRADE,
        "created_params": created,
        "fed_from": fed,
        "reasserted": reasserted,
        "mi_changes": mi_changes,
        "compile_ok": compile_ok,
        "compile_error": compile_err,
        "ok": compile_ok and created and fed,
    }
    REPORT.parent.mkdir(parents=True, exist_ok=True)
    REPORT.write_text(json.dumps(report, indent=2), encoding="utf-8")
    print(json.dumps(report, indent=2))
    return report


if __name__ == "__main__":
    raise SystemExit(0 if main().get("ok") else 1)