"""Read-only AAA audits + sign-off merge (safe while editor is open).

  python Content/Python/run_material_aaa_audits.py
"""
from __future__ import annotations

import json
import subprocess
from datetime import datetime, timezone
from pathlib import Path

PROJECT_ROOT = Path(__file__).resolve().parents[2]
SIGNOFF = PROJECT_ROOT / "Saved" / "Audit" / "portfolio_materials_aaa.json"
UE_CMD = Path(r"C:\Program Files\Epic Games\UE_5.8\Engine\Binaries\Win64\UnrealEditor-Cmd.exe")
UPROJECT = PROJECT_ROOT / "BS_GodFile.uproject"


def run_audits() -> dict:
    import review_portfolio_masters as rpm
    import audit_zen_trimsheet as zt
    import audit_landscape_aaa as la
    import audit_grand_water_aaa as wa

    rpm._run_in_ue()
    zen = zt._audit_in_ue()
    zt.REPORT.write_text(json.dumps(zen, indent=2), encoding="utf-8")
    land = la._audit_in_ue()
    la.REPORT.write_text(json.dumps(land, indent=2), encoding="utf-8")
    water = wa._audit_in_ue()
    wa.REPORT.write_text(json.dumps(water, indent=2), encoding="utf-8")

    master_ok = False
    master_path = PROJECT_ROOT / "Saved" / "Audit" / "master_review.json"
    if master_path.exists():
        mr = json.loads(master_path.read_text(encoding="utf-8"))
        summary = mr.get("summary") or mr
        master_ok = summary.get("clean", False) or (
            summary.get("banned_texture_count", summary.get("banned_texture_slots", 1)) == 0
            and summary.get("unwired_texture_count", summary.get("unwired_texture_slots", 1)) == 0
        )

    merged = {
        "timestamp": datetime.now(timezone.utc).isoformat(),
        "zen_trimsheet_all_ok": zen.get("all_ok"),
        "landscape_aaa_all_ok": land.get("all_ok"),
        "grand_water_aaa_all_ok": water.get("all_ok"),
        "master_review_ok": master_ok,
        "all_ok": bool(
            zen.get("all_ok") and land.get("all_ok") and water.get("all_ok") and master_ok
        ),
        "note": "audit-only; close editor and run run_material_aaa_pipeline.py for full sync",
    }
    SIGNOFF.parent.mkdir(parents=True, exist_ok=True)
    SIGNOFF.write_text(json.dumps(merged, indent=2), encoding="utf-8")
    return merged


def main() -> int:
    try:
        import os
        import unreal  # noqa: F401
        os.environ.setdefault("BS_AAA_READ_ONLY", "1")
        merged = run_audits()
        print(f"AAA_AUDITS all_ok={merged['all_ok']} -> {SIGNOFF}")
        return 0 if merged["all_ok"] else 1
    except ImportError:
        if not UE_CMD.exists():
            return 1
        cmd = [
            str(UE_CMD),
            str(UPROJECT),
            f"-ExecutePythonScript={(PROJECT_ROOT / 'Content/Python/run_material_aaa_audits.py').as_posix()}",
            "-stdout",
            "-unattended",
            "-nullrhi",
            "-DisablePlugins=Monolith",
        ]
        return subprocess.run(cmd, cwd=str(PROJECT_ROOT)).returncode


if __name__ == "__main__":
    raise SystemExit(main())
