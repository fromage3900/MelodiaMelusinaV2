"""Probe WidgetBlueprint Python API for tree access (UE 5.8)."""
from __future__ import annotations

import json
from pathlib import Path

import unreal

REPORT = Path(__file__).resolve().parents[2] / "Saved" / "Melodia" / "wbp_api_probe.json"
PATH = "/Game/Melodia/UI/WBP_Battle_Mobile"


def main() -> int:
    bp = unreal.EditorAssetLibrary.load_asset(PATH)
    info = {
        "loaded": bool(bp),
        "type": type(bp).__name__ if bp else None,
        "dir_treeish": [],
        "properties_tried": {},
        "parent": None,
    }
    if not bp:
        REPORT.write_text(json.dumps(info, indent=2), encoding="utf-8")
        return 1

    info["dir_treeish"] = sorted(
        n for n in dir(bp) if any(k in n.lower() for k in ("tree", "widget", "root", "parent", "generated"))
    )
    try:
        info["parent"] = str(bp.get_editor_property("parent_class"))
    except Exception as exc:  # noqa: BLE001
        info["parent"] = f"err:{exc}"

    for key in (
        "widget_tree",
        "WidgetTree",
        "tree",
        "root_widget",
        "generated_class",
        "skeleton_generated_class",
        "simple_construction_script",
    ):
        try:
            val = bp.get_editor_property(key)
            info["properties_tried"][key] = {"ok": True, "type": type(val).__name__, "repr": str(val)[:200]}
        except Exception as exc:  # noqa: BLE001
            info["properties_tried"][key] = {"ok": False, "error": str(exc)}

    # Alternative APIs
    alts = {}
    for name in (
        "WidgetBlueprintLibrary",
        "UMGEditorProjectSettings",
        "AssetEditorSubsystem",
        "EditorAssetLibrary",
        "BlueprintEditorLibrary",
    ):
        alts[name] = hasattr(unreal, name)
    info["unreal_modules"] = alts

    # Try generated class CDO BindWidgetOptional presence
    try:
        gen = bp.generated_class
        cdo = unreal.get_default_object(gen) if gen else None
        info["generated_class"] = str(gen)
        info["cdo_type"] = type(cdo).__name__ if cdo else None
        if cdo:
            info["cdo_lane_props"] = [
                n for n in dir(cdo) if "lane" in n.lower() or "combo" in n.lower() or "highway" in n.lower()
            ][:40]
    except Exception as exc:  # noqa: BLE001
        info["generated_error"] = str(exc)

    REPORT.parent.mkdir(parents=True, exist_ok=True)
    REPORT.write_text(json.dumps(info, indent=2), encoding="utf-8")
    unreal.log(f"[WBPProbe] Wrote {REPORT}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
