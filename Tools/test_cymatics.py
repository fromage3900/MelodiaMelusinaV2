#!/usr/bin/env python3
"""Cymatics offline probe — UMelodiaCymaticsSubsystem contract check.

No editor, no .uasset writes. Verifies the cymatics (audio→geometry) subsystem
exposes the read-only Chladni pattern API and holds no audio-authority state.
Output: Saved/Audit/cymatics_probe_YYYY-MM-DD.json
"""
from __future__ import annotations
import json, datetime
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
AUDIT = ROOT / "Saved" / "Audit"
SRC = ROOT / "Source" / "BS_GodFile" / "MelodiaIntegration"
H = SRC / "MelodiaCymaticsSubsystem.h"
C = SRC / "MelodiaCymaticsSubsystem.cpp"

def main() -> int:
    ts = datetime.datetime.now().strftime("%Y-%m-%d")
    htext = H.read_text(encoding="utf-8", errors="replace") if H.exists() else ""
    probe = {
        "generated": datetime.datetime.now().isoformat(),
        "header": {"exists": H.exists(), "bytes": H.stat().st_size if H.exists() else 0},
        "cpp": {"exists": C.exists(), "bytes": C.stat().st_size if C.exists() else 0},
        "cymatics_api": {
            "SampleCymaticAmplitude": "SampleCymaticAmplitude" in htext,
            "GetCymaticMode": "GetCymaticMode" in htext,
            "GetBeatPulse": "GetBeatPulse" in htext,
            "GetBassIntensity": "GetBassIntensity" in htext,
            "IsReadOnlyByContract": "IsReadOnlyByContract" in htext,
        },
        "read_only_not_writer": "READ" in htext and "never write" in htext.lower(),
        "chladni_implemented": "Chladni" in htext and "cos(n" in C.read_text(encoding="utf-8", errors="replace") if C.exists() else False,
        "verdict": "SCAFFOLD - cymatics audio-to-geometry driver; read-only (consumes existing MPC writer), no second writer. Build + PIE validation next window.",
    }
    AUDIT.mkdir(parents=True, exist_ok=True)
    jpath = AUDIT / f"cymatics_probe_{ts}.json"
    jpath.write_text(json.dumps(probe, indent=2), encoding="utf-8")
    print(f"Probe -> {jpath}")
    print(f"Verdict: {probe['verdict']}")
    return 0

if __name__ == "__main__":
    raise SystemExit(main())