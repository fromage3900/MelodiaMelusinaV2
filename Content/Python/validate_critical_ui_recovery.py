"""Targeted, no-PIE UMG recovery gate for the exact packages involved in the crash."""

import json
from datetime import datetime, timezone
from pathlib import Path

import unreal


ASSETS = (
    "/Game/Melodia/UI/WBP_MainMenu",
    "/Game/TurnBasedJRPGTemplate/Blueprints/UI/BP_ActionButton",
    "/Game/TurnBasedJRPGTemplate/Blueprints/UI/BP_BattleUI",
    "/Game/TurnBasedJRPGTemplate/Blueprints/Battle/BP_BattleController",
)
GAME_MODE_CLASS = "/Script/MelodiaCore.OrreryMainMenuGameMode"
OUT = Path(unreal.Paths.project_saved_dir()) / "Audit" / "critical_ui_recovery.json"


def blueprint_status(asset) -> str:
    try:
        return str(asset.get_editor_property("status"))
    except Exception:
        return "unknown"


rows = []
for path in ASSETS:
    asset = unreal.load_asset(path)
    row = {"asset": path, "loaded": bool(asset), "compiled": False, "status": "missing"}
    if asset:
        try:
            unreal.BlueprintEditorLibrary.compile_blueprint(asset)
            row["compiled"] = True
            row["status"] = blueprint_status(asset)
            row["saved"] = bool(unreal.EditorAssetLibrary.save_loaded_asset(asset, only_if_is_dirty=True))
        except Exception as exc:  # noqa: BLE001
            row["error"] = str(exc)
    rows.append(row)

game_mode = unreal.load_class(None, GAME_MODE_CLASS)
game_mode_cdo = unreal.get_default_object(game_mode) if game_mode else None
report = {
    "timestamp": datetime.now(timezone.utc).isoformat(),
    "assets": rows,
    "game_mode_class_loads": bool(game_mode),
    "game_mode_cdo_loads": bool(game_mode_cdo),
}
report["failed"] = [
    row for row in rows
    if not row["loaded"] or not row["compiled"] or "ERROR" in row.get("status", "").upper()
]
report["ok"] = not report["failed"] and report["game_mode_class_loads"] and report["game_mode_cdo_loads"]
OUT.parent.mkdir(parents=True, exist_ok=True)
OUT.write_text(json.dumps(report, indent=2), encoding="utf-8")
unreal.log("CRITICAL_UI_RECOVERY: " + json.dumps(report))
if not report["ok"]:
    raise RuntimeError("Critical UMG recovery compile gate failed")
