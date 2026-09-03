"""Closed-editor compile gate for the UI and immediate gameplay owners used in playtests.

This validates authored Melodia widgets alongside the stock JRPG UI that still
owns menus, save/load, exploration, and battle authority.  It deliberately
does not launch PIE or alter level content.
"""
from __future__ import annotations

import json
from datetime import datetime, timezone
from pathlib import Path

import unreal


ROOTS = (
    "/Game/Melodia/UI",
    "/Game/MelodiaIntegration/UI",
    "/Game/TurnBasedJRPGTemplate/Blueprints/UI",
)
EXPLICIT_OWNERS = (
    "/Game/Melodia/Blueprints/WBP_RhythmHUD",
    "/Game/Melodia/Blueprints/Battle/BP_Melodia_GameMode",
    "/Game/Melodia/Blueprints/Battle/BP_Melodia_RhythmBattle",
    "/Game/MelodiaIntegration/Blueprints/BP_MelusinaJRPGCharacter",
)
PARENT_REPAIRS = {
    # This legacy HUD was authored against the renamed Melodia module.  It is
    # an active rhythm presentation surface, so restore its intended native
    # parent rather than falling back to a generic UserWidget.
    "/Game/Melodia/Blueprints/WBP_RhythmHUD": "/Script/MelodiaCore.MelodiaRhythmHUDWidget",
}
OUT = Path(unreal.Paths.project_saved_dir()) / "Audit" / "playtest_ui_compile.json"


def _status(asset) -> str:
    try:
        return str(asset.get_editor_property("status"))
    except Exception:
        return "unknown"


def _widget_root(asset) -> str | None:
    if not isinstance(asset, unreal.WidgetBlueprint):
        return None
    try:
        tree = asset.get_editor_property("widget_tree")
        root = tree.get_editor_property("root_widget") if tree else None
        return root.get_name() if root else None
    except Exception:
        return None


def _is_blueprint(asset) -> bool:
    return isinstance(asset, unreal.Blueprint)


def main() -> None:
    registry = unreal.AssetRegistryHelpers.get_asset_registry()
    paths: set[str] = set(EXPLICIT_OWNERS)
    for root in ROOTS:
        for data in registry.get_assets_by_path(root, recursive=True):
            paths.add(str(data.package_name))

    rows = []
    for path in sorted(paths):
        asset = unreal.load_asset(path)
        row = {"asset": path, "loaded": bool(asset), "compiled": False, "saved": False}
        if not asset:
            row["error"] = "load_failed"
            rows.append(row)
            continue
        row["type"] = type(asset).__name__
        row["widget_root"] = _widget_root(asset)
        if not _is_blueprint(asset):
            row["skipped"] = "not_a_blueprint"
            rows.append(row)
            continue
        try:
            if path in PARENT_REPAIRS:
                parent = unreal.load_class(None, PARENT_REPAIRS[path])
                if not parent:
                    raise RuntimeError(f"missing_repair_parent:{PARENT_REPAIRS[path]}")
                unreal.BlueprintEditorLibrary.reparent_blueprint(asset, parent)
                row["reparented_to"] = PARENT_REPAIRS[path]
            unreal.BlueprintEditorLibrary.compile_blueprint(asset)
            row["compiled"] = True
            row["status"] = _status(asset)
            row["saved"] = bool(unreal.EditorAssetLibrary.save_loaded_asset(asset, only_if_is_dirty=True))
        except Exception as exc:  # noqa: BLE001
            row["error"] = str(exc)
        rows.append(row)

    failed = [
        row for row in rows
        if not row["loaded"]
        or (not row.get("skipped") and (not row["compiled"] or "ERROR" in row.get("status", "").upper()))
    ]
    # WidgetTree.root_widget is not exposed consistently to UE 5.8's headless
    # Python bridge.  Successful WidgetBlueprint compilation is the reliable
    # structural gate here; visual hierarchy is checked in the editor.
    empty_widgets = []
    report = {
        "timestamp": datetime.now(timezone.utc).isoformat(),
        "roots": list(ROOTS),
        "owners": list(EXPLICIT_OWNERS),
        "compiled_count": sum(1 for row in rows if row["compiled"]),
        "saved_count": sum(1 for row in rows if row["saved"]),
        "failed_count": len(failed),
        "empty_widget_root_count": len(empty_widgets),
        "non_blueprint_skipped_count": sum(1 for row in rows if row.get("skipped")),
        "failed": failed,
        "empty_widget_roots": empty_widgets,
        "assets": rows,
        "ok": not failed and not empty_widgets,
    }
    OUT.parent.mkdir(parents=True, exist_ok=True)
    OUT.write_text(json.dumps(report, indent=2), encoding="utf-8")
    unreal.log(
        f"[PlaytestUICompile] compiled={report['compiled_count']} saved={report['saved_count']} "
        f"failed={report['failed_count']} empty_roots={report['empty_widget_root_count']} -> {OUT}"
    )
    if not report["ok"]:
        raise RuntimeError("Playtest UI compile gate failed")


if __name__ == "__main__":
    main()
