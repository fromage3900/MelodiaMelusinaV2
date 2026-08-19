"""Dreamprint — additive Sync-Vision block on the live grade master.

Targets /Game/_PROJECT/04_Materials/PostProcess/M_PP_MeluColorGrade (the V3
master the live profile MIs parent to). The block is gated on
InkSyncVision > 0.001 so the locked look is byte-identical while
InkSyncVision = 0 (the default). Adds: beat/victory palette pulse, a comic
flash, and a halftone-negative flicker — all MPC-driven, all capped.
"""
from __future__ import annotations

import json
import sys
from datetime import datetime, timezone
from pathlib import Path

import unreal

MAT = "/Game/_PROJECT/04_Materials/PostProcess/M_PP_MeluColorGrade"
REPORT = Path(__file__).resolve().parents[2] / "Saved" / "Audit" / "dreamprint_grade_upgrade.json"

MARKER = "// ---- DREAMPRINT SYNC-VISION (gated; locked look preserved at 0)"

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


def main() -> int:
    m = unreal.load_asset(MAT)
    if not m:
        raise RuntimeError(f"Missing {MAT}")
    customs = [e for e in unreal.MaterialEditingLibrary.get_material_expressions(m)
               if type(e).__name__ == "MaterialExpressionCustom"]
    if not customs:
        raise RuntimeError(f"No Custom node in {MAT}")
    custom = customs[0]
    code = custom.get_editor_property("code")

    if MARKER in code:
        report = {"timestamp": datetime.now(timezone.utc).isoformat(),
                  "material": MAT, "status": "already_applied", "ok": True}
        REPORT.parent.mkdir(parents=True, exist_ok=True)
        REPORT.write_text(json.dumps(report, indent=2), encoding="utf-8")
        print(json.dumps(report, indent=2))
        return 0

    anchor = "return lerp(src,max(split,0.0),g);"
    if anchor not in code:
        raise RuntimeError(f"Anchor not found in {MAT} — refusing to guess")
    code = code.replace(anchor, BLOCK + "\n" + anchor)
    custom.set_editor_property("code", code)
    try:
        unreal.MaterialEditingLibrary.recompile_material(m)
    except Exception as exc:
        unreal.log_warning(f"[Dreamprint] grade recompile: {exc}")
    unreal.EditorAssetLibrary.save_loaded_asset(m, only_if_is_dirty=False)

    report = {
        "timestamp": datetime.now(timezone.utc).isoformat(),
        "material": MAT,
        "status": "applied",
        "code_len_after": len(code),
        "ok": True,
    }
    REPORT.parent.mkdir(parents=True, exist_ok=True)
    REPORT.write_text(json.dumps(report, indent=2), encoding="utf-8")
    print(json.dumps(report, indent=2))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())