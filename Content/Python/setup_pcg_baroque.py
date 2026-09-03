"""Baroque PCG style wrapper — Phase 3 salvage from Melodia PCGCol_Baroque_*.

  py Content/Python/setup_pcg_baroque.py
"""
from __future__ import annotations

import json
import subprocess
import sys
from datetime import datetime, timezone
from pathlib import Path

import pcg_portfolio_standards as std
import pcg_graph_builder as gb

PROJECT_ROOT = Path(__file__).resolve().parents[2]
REPORT = PROJECT_ROOT / "Saved" / "Audit" / "baroque_pcg.json"
UE_CMD = Path(r"C:\Program Files\Epic Games\UE_5.8\Engine\Binaries\Win64\UnrealEditor-Cmd.exe")
UPROJECT = PROJECT_ROOT / "BS_GodFile.uproject"

MELODIA_BAROQUE_COLS = (
    "/Game/_PROJECT/PCG/Collections/PCGCol_Baroque_Walls",
    "/Game/_PROJECT/PCG/Collections/PCGCol_Baroque_Columns",
    "/Game/_PROJECT/PCG/Collections/PCGCol_Baroque_Cornice",
)


def build_kit() -> dict:
    import unreal

    gb.ensure_directories()
    style_dir = f"{std.DIR_STYLES}/Baroque"
    if not unreal.EditorAssetLibrary.does_directory_exist(style_dir):
        unreal.EditorAssetLibrary.make_directory(style_dir)

    salvaged = []
    for col_path in MELODIA_BAROQUE_COLS:
        if unreal.EditorAssetLibrary.does_asset_exist(col_path):
            salvaged.append(col_path)

    report = {
        "timestamp": datetime.now(timezone.utc).isoformat(),
        "kit_path": std.SMC_BAROQUE,
        "salvaged_collections": salvaged,
        "wall_graph": std.GRAPH_WALL,
        "note": "Clone mesh entries from salvaged collections in editor; wall graph is Phase 3 stub",
    }
    REPORT.parent.mkdir(parents=True, exist_ok=True)
    REPORT.write_text(json.dumps(report, indent=2), encoding="utf-8")
    unreal.log(f"[BaroquePCG] salvaged={len(salvaged)} -> {REPORT}")
    return report


def main() -> int:
    try:
        import unreal  # noqa: F401
        import setup_pcg_universal as uni
        uni.build_all(force=False)
        r = build_kit()
        print(f"BAROQUE_PCG cols={len(r['salvaged_collections'])}")
        return 0
    except ImportError:
        if not UE_CMD.exists():
            return 1
        cmd = [
            str(UE_CMD), str(UPROJECT),
            f"-ExecutePythonScript={(PROJECT_ROOT / 'Content/Python/setup_pcg_baroque.py').as_posix()}",
            "-stdout", "-unattended", "-nullrhi", "-DisablePlugins=Monolith",
        ]
        return subprocess.run(cmd, cwd=str(PROJECT_ROOT)).returncode


if __name__ == "__main__":
    raise SystemExit(main())
