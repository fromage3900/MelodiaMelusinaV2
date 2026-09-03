"""Remediate dead PCG systems on shipping levels (dry-run default).

  python Content/Python/fix_pcg_dead_systems.py
  python Content/Python/fix_pcg_dead_systems.py --apply
"""
from __future__ import annotations

import json
import os
import subprocess
import sys
from datetime import datetime, timezone
from pathlib import Path

import pcg_portfolio_standards as std

PROJECT_ROOT = Path(__file__).resolve().parents[2]
REPORT = PROJECT_ROOT / "Saved" / "Audit" / "pcg_fix_report.json"
UE_CMD = Path(r"C:\Program Files\Epic Games\UE_5.8\Engine\Binaries\Win64\UnrealEditor-Cmd.exe")
UPROJECT = PROJECT_ROOT / "BS_GodFile.uproject"


def fix(*, apply: bool = False) -> dict:
    import os
    import unreal
    import organize_pcg_library as org
    import setup_pcg_universal as uni
    import setup_pcg_greybox as grey

    apply = apply or os.environ.get("BS_PCG_FIX_APPLY", "").lower() in ("1", "true", "yes")

    actions: list[dict] = []

    if apply:
        org.organize(move_orphan=True)
        uni.build_all(force=False)
        grey.build_preset_graphs(force=True)

    for level in (std.LEVEL_TEMPLATE, std.LEVEL_SAKURA):
        level_asset = f"{level}.{level.rsplit('/', 1)[-1]}"
        if not unreal.EditorAssetLibrary.does_asset_exist(level_asset):
            actions.append({"action": "skip", "level": level, "reason": "missing"})
            continue
        preset = "minimal" if level == std.LEVEL_TEMPLATE else "showcase"
        grass_mi = std.MI_SAKURA_GRASS if preset == "showcase" else None
        if apply:
            result = grey.apply_greybox_pcg(
                level, preset=preset, generate=True, grass_mi=grass_mi,
            )
            actions.append({"action": "apply_greybox", "level": level, "preset": preset, **result})
        else:
            actions.append({
                "action": "would_apply_greybox",
                "level": level,
                "preset": preset,
            })

    report = {
        "timestamp": datetime.now(timezone.utc).isoformat(),
        "apply": apply,
        "actions": actions,
    }
    REPORT.parent.mkdir(parents=True, exist_ok=True)
    REPORT.write_text(json.dumps(report, indent=2), encoding="utf-8")
    unreal.log(f"[PCGFix] apply={apply} actions={len(actions)} -> {REPORT}")
    return report


def main() -> int:
    apply = "--apply" in sys.argv or os.environ.get("BS_PCG_FIX_APPLY", "").lower() in ("1", "true", "yes")
    try:
        import unreal  # noqa: F401
        fix(apply=apply)
        print(f"PCG_FIX_OK apply={apply} -> {REPORT}")
        return 0
    except ImportError:
        if not UE_CMD.exists():
            return 1
        cmd = [
            str(UE_CMD), str(UPROJECT),
            f"-ExecutePythonScript={(PROJECT_ROOT / 'Content/Python/fix_pcg_dead_systems.py').as_posix()}",
            "-stdout", "-unattended", "-nullrhi", "-DisablePlugins=Monolith",
        ]
        env = os.environ.copy()
        if apply:
            env["BS_PCG_FIX_APPLY"] = "1"
        return subprocess.run(cmd, cwd=str(PROJECT_ROOT), env=env).returncode


if __name__ == "__main__":
    raise SystemExit(main())
