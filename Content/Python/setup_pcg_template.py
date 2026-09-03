"""Template level PCG — minimal greybox preset on L_Template.

  py Content/Python/setup_pcg_template.py
"""
from __future__ import annotations

import json
import subprocess
import sys
from datetime import datetime, timezone
from pathlib import Path

import pcg_portfolio_standards as std

PROJECT_ROOT = Path(__file__).resolve().parents[2]
REPORT = PROJECT_ROOT / "Saved" / "Audit" / "template_pcg.json"
UE_CMD = Path(r"C:\Program Files\Epic Games\UE_5.8\Engine\Binaries\Win64\UnrealEditor-Cmd.exe")
UPROJECT = PROJECT_ROOT / "BS_GodFile.uproject"


def build(*, preset: str = "minimal", generate: bool = True) -> dict:
    import setup_pcg_universal as uni
    import setup_pcg_greybox as grey

    uni.build_all(force=False)
    result = grey.apply_greybox_pcg(std.LEVEL_TEMPLATE, preset=preset, generate=generate)
    report = {
        "timestamp": datetime.now(timezone.utc).isoformat(),
        "level": std.LEVEL_TEMPLATE,
        **result,
    }
    REPORT.parent.mkdir(parents=True, exist_ok=True)
    REPORT.write_text(json.dumps(report, indent=2), encoding="utf-8")
    return report


def main() -> int:
    try:
        import unreal  # noqa: F401
        preset = "minimal"
        for i, a in enumerate(sys.argv):
            if a == "--preset" and i + 1 < len(sys.argv):
                preset = sys.argv[i + 1]
        r = build(preset=preset)
        print(f"TEMPLATE_PCG passed={r.get('passed')}")
        return 0 if r.get("passed") else 1
    except ImportError:
        if not UE_CMD.exists():
            return 1
        cmd = [
            str(UE_CMD), str(UPROJECT),
            f"-ExecutePythonScript={(PROJECT_ROOT / 'Content/Python/setup_pcg_template.py').as_posix()}",
            "-stdout", "-unattended", "-nullrhi", "-DisablePlugins=Monolith",
        ]
        return subprocess.run(cmd, cwd=str(PROJECT_ROOT)).returncode


if __name__ == "__main__":
    raise SystemExit(main())
