#!/usr/bin/env python3
"""Dash-capability offline probe — UMelodiaDressingSubsystem contract check.

No editor, no .uasset writes. Verifies the dressing subsystem headers exist and
expose the Dash-role API (DressHeroClutter / PhysicallyDrop / FindCompositionOccluders).
Output: Saved/Audit/dressing_probe_YYYY-MM-DD.json
"""
from __future__ import annotations
import json, datetime
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
AUDIT = ROOT / "Saved" / "Audit"
SRC = ROOT / "Source" / "BS_GodFile" / "MelodiaIntegration"
H = SRC / "MelodiaDressingSubsystem.h"
C = SRC / "MelodiaDressingSubsystem.cpp"

def main() -> int:
    ts = datetime.datetime.now().strftime("%Y-%m-%d")
    htext = H.read_text(encoding="utf-8", errors="replace") if H.exists() else ""
    probe = {
        "generated": datetime.datetime.now().isoformat(),
        "header": {"exists": H.exists(), "bytes": H.stat().st_size if H.exists() else 0},
        "cpp": {"exists": C.exists(), "bytes": C.stat().st_size if C.exists() else 0},
        "api": {
            "DressHeroClutter": "DressHeroClutter" in htext,
            "PhysicallyDrop": "PhysicallyDrop" in htext,
            "FindCompositionOccluders": "FindCompositionOccluders" in htext,
            "GetDressingCatalogPath": "GetDressingCatalogPath" in htext,
        },
        "no_content_project_writes": True,
        "no_new_material_master": True,
        "verdict": "SCAFFOLD — Dash-capability dressing subsystem; build + PIE validation next closed-editor window",
    }
    AUDIT.mkdir(parents=True, exist_ok=True)
    jpath = AUDIT / f"dressing_probe_{ts}.json"
    jpath.write_text(json.dumps(probe, indent=2), encoding="utf-8")
    print(f"Probe -> {jpath}")
    print(f"Verdict: {probe['verdict']}")
    return 0

if __name__ == "__main__":
    raise SystemExit(main())