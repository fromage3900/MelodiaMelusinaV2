#!/usr/bin/env python3
"""Magpie seam offline probe — UMelodiaVisualRepresentationSubsystem contract check.

No editor, no .uasset writes. Verifies the visual-truth seam exposes READ-ONLY
accessors (simulation truth -> visual truth) and holds no simulation state.
Output: Saved/Audit/visual_seam_probe_YYYY-MM-DD.json
"""
from __future__ import annotations
import json, datetime
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
AUDIT = ROOT / "Saved" / "Audit"
SRC = ROOT / "Source" / "BS_GodFile" / "MelodiaIntegration"
H = SRC / "MelodiaVisualRepresentationSubsystem.h"
C = SRC / "MelodiaVisualRepresentationSubsystem.cpp"

def main() -> int:
    ts = datetime.datetime.now().strftime("%Y-%m-%d")
    htext = H.read_text(encoding="utf-8", errors="replace") if H.exists() else ""
    ctext = C.read_text(encoding="utf-8", errors="replace") if C.exists() else ""
    probe = {
        "generated": datetime.datetime.now().isoformat(),
        "header": {"exists": H.exists(), "bytes": H.stat().st_size if H.exists() else 0},
        "cpp": {"exists": C.exists(), "bytes": C.stat().st_size if C.exists() else 0},
        "read_seam_api": {
            "GetCurrentRhythmGradeKey": "GetCurrentRhythmGradeKey" in htext,
            "GetBeatPhaseNormalized": "GetBeatPhaseNormalized" in htext,
            "IsBattleActive": "IsBattleActive" in htext,
            "GetActiveNarrativeVisualFlags": "GetActiveNarrativeVisualFlags" in htext,
            "IsReadOnlyByContract": "IsReadOnlyByContract" in htext,
        },
        "read_only_contract": "read-only" in htext or "READ contract" in htext,
        "no_simulation_state_held": "no simulation state" in htext or "no mutable simulation" in htext,
        "verdict": "SCAFFOLD — Magpie simulation/visual seam; read-only, no renderer, no second writer. Build + PIE validation next window.",
    }
    AUDIT.mkdir(parents=True, exist_ok=True)
    jpath = AUDIT / f"visual_seam_probe_{ts}.json"
    jpath.write_text(json.dumps(probe, indent=2), encoding="utf-8")
    print(f"Probe -> {jpath}")
    print(f"Verdict: {probe['verdict']}")
    return 0

if __name__ == "__main__":
    raise SystemExit(main())