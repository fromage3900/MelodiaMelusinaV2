"""Finish wiring the EnvSandbox/Materials/Masters fork of M_PP_MeluColorGrade.

Same condition as the canonical master (Dream* renames left the grading inputs
dangling) PLUS it never received the dreamprint sync-vision block. Mirror of
the canonical fix:
  1. recreate the 8 grading params (defaults = the values the dead overrides
     encode on the canonical MIs),
  2. wire all grading inputs,
  3. insert the DREAMPRINT block (anchor exists), add the 4 MPC collection
     nodes + 4 named inputs (BeatPulse/VictoryPulse/MeluPrimary/InkSyncVision),
     set-then-connect order.
The Melodia/_PROJECT copy is a DIFFERENT legacy lineage (pre-V3, 8 inputs,
self-contained) used by the preview studio — left untouched.

Manifest: Saved/Audit/grade_wiring_envsandbox_fork.json
"""
from __future__ import annotations

import json
from datetime import datetime, timezone
from pathlib import Path

import unreal

import material_lib as lib

REPORT = Path(__file__).resolve().parents[2] / "Saved" / "Audit" / "grade_wiring_envsandbox_fork.json"

GRADE = "/Game/EnvSandbox/Materials/Masters/M_PP_MeluColorGrade"
MPC_INK = "/Game/Melodia/_PROJECT/04_Materials/MPC_MelodiaInk"
MPC_PALETTE = "/Game/Melodia/_PROJECT/04_Materials/MPC_Melodia_Palette"

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

BLOCK_MARKER = "// ---- DREAMPRINT SYNC-VISION (gated; locked look preserved at 0)"
BLOCK = """
// ---- DREAMPRINT SYNC-VISION (gated; locked look preserved at 0) ----
{
    float svBeat   = saturate(BeatPulse) * saturate(InkSyncVision);
    float svVict   = saturate(VictoryPulse) * saturate(InkSyncVision);
    float sv       = saturate(svBeat + svVict);
    if (InkSyncVision > 0.001) {
        float3 pv = max(MeluPrimary, 1e-4);
        pv /= max(dot(pv, float3(0.2126, 0.7152, 0.0722)), 1e-4);
        split = lerp(split, split * pv * (1.0 + sv * 0.35), sv * 0.5);
        split += sv * 0.04;
        float inv = smoothstep(0.6, 1.0, BeatPulse) * InkSyncVision;
        split = lerp(split, float3(1.0, 1.0, 1.0) - split, inv * 0.30);
    }
}
"""
NEW_BLOCK_INPUTS = (("BeatPulse", MPC_PALETTE), ("VictoryPulse", MPC_PALETTE),
                    ("MeluPrimary", MPC_PALETTE), ("InkSyncVision", MPC_INK))


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

    created, fed, reasserted = [], [], []
    for name, default in NEW_PARAMS.items():
        if name not in input_names:
            continue
        if name not in by_name:
            by_name[name] = lib.scalar_param(mat, name, "V3 Adaptive", default, -1500, 2600)
            created.append(name)
        unreal.MaterialEditingLibrary.connect_material_expressions(by_name[name], "", custom, name)
    for pin, src_param in FEED_FROM.items():
        if pin in input_names and src_param in by_name:
            unreal.MaterialEditingLibrary.connect_material_expressions(by_name[src_param], "", custom, pin)
            fed.append(f"{pin}<-{src_param}")
    for pin in REASSERT:
        if pin in input_names and pin in by_name:
            unreal.MaterialEditingLibrary.connect_material_expressions(by_name[pin], "", custom, pin)
            reasserted.append(pin)

    # dreamprint block + MPC inputs
    code = custom.get_editor_property("code")
    block_state = "already"
    if BLOCK_MARKER not in code:
        anchor = "return lerp(src,max(split,0.0),g);"
        if anchor not in code:
            raise RuntimeError("v3 anchor missing")
        code = code.replace(anchor, BLOCK + "\n" + anchor)
        custom.set_editor_property("code", code)
        block_state = "inserted"

    entries = list(custom.get_editor_property("inputs") or [])
    template = entries[0]
    added, connected = [], []
    for ident, coll_path in NEW_BLOCK_INPUTS:
        if ident in input_names:
            continue
        node = by_name.get(ident)
        if not node or type(node).__name__ != "MaterialExpressionCollectionParameter":
            node = lib.collection_param(mat, coll_path, ident, -1500, 2900)
            by_name[ident] = node
        entry = template.copy()
        entry.set_editor_property("input_name", ident)
        entries.append(entry)
        input_names.add(ident)
        added.append(ident)
    custom.set_editor_property("inputs", entries)
    for ident, _coll in NEW_BLOCK_INPUTS:
        if ident in input_names:
            unreal.MaterialEditingLibrary.connect_material_expressions(by_name[ident], "", custom, ident)
            connected.append(ident)

    try:
        unreal.MaterialEditingLibrary.recompile_material(mat)
        compile_ok = True
        compile_err = None
    except Exception as exc:
        compile_ok = False
        compile_err = str(exc)
    unreal.EditorAssetLibrary.save_loaded_asset(mat, only_if_is_dirty=False)

    after = custom.get_editor_property("inputs") or []
    report = {
        "timestamp": datetime.now(timezone.utc).isoformat(),
        "material": GRADE,
        "created_params": created,
        "fed_from": fed,
        "reasserted": reasserted,
        "dreamprint_block": block_state,
        "block_inputs_added": added,
        "block_inputs_connected": connected,
        "input_count_after": len(after),
        "compile_ok": compile_ok,
        "compile_error": compile_err,
        "ok": bool(compile_ok and created and fed and connected),
    }
    REPORT.parent.mkdir(parents=True, exist_ok=True)
    REPORT.write_text(json.dumps(report, indent=2), encoding="utf-8")
    print(json.dumps(report, indent=2))
    return report


if __name__ == "__main__":
    raise SystemExit(0 if main().get("ok") else 1)