"""Finalize wiring for the universal landscape master.

Single entry point that:
1. Adds the pro triplanar overlay lane (upgrade_landscape_triplanar_pro)
2. Applies healthy PBR texture defaults + creates/updates instances (apply_healthy_landscape_defaults)
3. Saves everything and writes an audit manifest

Run inside the UE editor Python interpreter:

    import finalize_universal_landscape_master as f
    f.main()

Or headless:

    UnrealEditor-Cmd.exe BS_GodFile.uproject ^
      -ExecutePythonScript="G:/EnvironmentPortfolio/BS_GodFile/Content/Python/finalize_universal_landscape_master.py" ^
      -unattended -nullrhi
"""

from __future__ import annotations

import json
from datetime import datetime, timezone
from pathlib import Path

import unreal

import upgrade_landscape_triplanar_pro as tripro
import apply_healthy_landscape_defaults as healthy


REPORT = Path(__file__).resolve().parents[2] / "Saved" / "Audit" / "universal_landscape_master_finalized.json"


def main() -> dict:
    unreal.log("=== FINALIZE UNIVERSAL LANDSCAPE MASTER ===")

    tripro_result = tripro.main()
    healthy_result = healthy.main()

    try:
        unreal.EditorLoadingAndSavingUtils.save_dirty_packages(True, True)
    except Exception as exc:
        unreal.log_warning(f"save_dirty_packages: {exc}")

    report = {
        "timestamp": datetime.now(timezone.utc).isoformat(),
        "triplanar_pro": tripro_result,
        "healthy_defaults": healthy_result,
    }
    REPORT.parent.mkdir(parents=True, exist_ok=True)
    REPORT.write_text(json.dumps(report, indent=2), encoding="utf-8")
    unreal.log(f"[FinalizeUniversalLandscapeMaster] report -> {REPORT}")
    return report


if __name__ == "__main__":
    main()
