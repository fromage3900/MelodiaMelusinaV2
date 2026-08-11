"""Thin Melodia core-loop demo stub for BS_GodFile (JRPG template + quest hook).

  python Content/Python/setup_melodia_core_loop_demo.py
"""
from __future__ import annotations

import json
from datetime import datetime, timezone
from pathlib import Path

PROJECT_ROOT = Path(__file__).resolve().parents[2]
AUDIT = PROJECT_ROOT / "Saved" / "Audit"

FOLDERS = (
    "/Game/Melodia/UI/Notation",
    "/Game/Melodia/UI/Notation/Textures",
    "/Game/Melodia/Levels",
)

PHOENIX = (
    "/Game/TurnBasedJRPGTemplate/Blueprints/Battle/BP_BattleController",
    "/Game/TurnBasedJRPGTemplate/Blueprints/UI/BP_BattleUI",
    "/Game/Melodia/Core/BP_QuestManager",
)


def main() -> int:
    try:
        import unreal
    except ImportError:
        print("Requires Unreal Python")
        return 1

    created = []
    for folder in FOLDERS:
        if not unreal.EditorAssetLibrary.does_directory_exist(folder):
            unreal.EditorAssetLibrary.make_directory(folder)
            created.append(folder)

    checks = [{"asset": p, "ok": unreal.EditorAssetLibrary.does_asset_exist(p)} for p in PHOENIX]
    report = {
        "timestamp": datetime.now(timezone.utc).isoformat(),
        "folders_created": created,
        "checks": checks,
        "all_ok": all(c["ok"] for c in checks),
        "note": "Full loop requires MelodiaMelusina_PROD C++ in G:/Melodia",
    }
    AUDIT.mkdir(parents=True, exist_ok=True)
    out = AUDIT / "melodia_core_loop_demo_bs.json"
    out.write_text(json.dumps(report, indent=2), encoding="utf-8")
    print(f"BS_MELODIA_DEMO_OK -> {out}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
