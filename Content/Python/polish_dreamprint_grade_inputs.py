"""Dreamprint — append the 4 missing named inputs to the grade master's custom
node (BeatPulse, VictoryPulse, MeluPrimary, InkSyncVision).

The DREAMPRINT SYNC-VISION block reads these by name; UE 5.8 custom nodes only
see function inputs, so the block never compiled. MPC_Melodia_Palette was
already referenced; MPC_MelodiaInk node (InkSyncVision) was added by the earlier
polish pass and is reused here.

Idempotent: skips any input that already exists. Manifest:
Saved/Audit/dreamprint_grade_inputs.json
"""
from __future__ import annotations

import json
from datetime import datetime, timezone
from pathlib import Path

import unreal

import material_lib as lib

REPORT = Path(__file__).resolve().parents[2] / "Saved" / "Audit" / "dreamprint_grade_inputs.json"

GRADE = "/Game/_PROJECT/04_Materials/PostProcess/M_PP_MeluColorGrade"
MPC_INK = "/Game/Melodia/_PROJECT/04_Materials/MPC_MelodiaInk"
MPC_PALETTE = "/Game/Melodia/_PROJECT/04_Materials/MPC_Melodia_Palette"

NEW_INPUTS: tuple[tuple[str, str], ...] = (
    ("BeatPulse", MPC_PALETTE),
    ("VictoryPulse", MPC_PALETTE),
    ("MeluPrimary", MPC_PALETTE),
    ("InkSyncVision", MPC_INK),
)


def main() -> dict:
    mat = unreal.load_asset(GRADE)
    if not mat:
        return {"ok": False, "error": f"missing {GRADE}"}
    customs = [e for e in unreal.MaterialEditingLibrary.get_material_expressions(mat)
               if type(e).__name__ == "MaterialExpressionCustom"]
    if not customs:
        return {"ok": False, "error": "no Custom node"}
    custom = customs[0]

    existing = custom.get_editor_property("inputs") or []
    names = {str(x.get_editor_property("input_name")) for x in existing}
    template = existing[0]

    by_name: dict[str, unreal.MaterialExpression] = {}
    for e in unreal.MaterialEditingLibrary.get_material_expressions(mat) or []:
        try:
            by_name[str(e.get_editor_property("parameter_name"))] = e
        except Exception:
            continue

    # Build the full target array FIRST (pins must exist before connecting —
    # connecting to a not-yet-existing pin silently no-ops and the entry's
    # inner ref stays the template copy's, leaking its type).
    entries = list(existing)
    added, skipped = [], []
    for ident, coll_path in NEW_INPUTS:
        if ident in names:
            skipped.append(ident)
            continue
        entry = template.copy()
        entry.set_editor_property("input_name", ident)
        entries.append(entry)
        added.append(ident)
    custom.set_editor_property("inputs", entries)

    # Connect every new pin (always re-run: heals entries whose inner ref
    # leaked a template type).
    connected, failed = [], []
    for ident, coll_path in NEW_INPUTS:
        node = by_name.get(ident)
        if not node or type(node).__name__ != "MaterialExpressionCollectionParameter":
            node = lib.collection_param(mat, coll_path, ident, -1100, 1500)
            by_name[ident] = node
        try:
            unreal.MaterialEditingLibrary.connect_material_expressions(node, "", custom, ident)
            connected.append(ident)
        except Exception as exc:
            failed.append({"name": ident, "error": str(exc)})

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
        "added": added,
        "skipped": skipped,
        "connected": connected,
        "failed_connects": failed,
        "input_count_after": len(after),
        "input_names_after": [str(x.get_editor_property("input_name")) for x in after],
        "compile_ok": compile_ok,
        "compile_error": compile_err,
        "ok": compile_ok and not failed and all(
            n in {str(x.get_editor_property("input_name")) for x in after} for n, _ in NEW_INPUTS),
    }
    REPORT.parent.mkdir(parents=True, exist_ok=True)
    REPORT.write_text(json.dumps(report, indent=2), encoding="utf-8")
    print(json.dumps(report, indent=2))
    return report


if __name__ == "__main__":
    raise SystemExit(0 if main().get("ok") else 1)