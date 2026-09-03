"""Capture material thumbnail previews to Saved/Portfolio/MaterialPreviews/.

Scans MASTER_DIR and ENV_INST_DIR for materials, renders a small preview
using UE automation thumbnail capture when available, otherwise records
metadata only.

Run (editor):
  py "G:/EnvironmentPortfolio/BS_GodFile/Content/Python/capture_material_previews.py"
"""
from __future__ import annotations

import json
from datetime import datetime, timezone
from pathlib import Path
import material_lib as lib

PROJECT_ROOT = Path(__file__).resolve().parents[2]
OUT_DIR = PROJECT_ROOT / "Saved" / "Portfolio" / "MaterialPreviews"
REPORT = OUT_DIR / "previews_manifest.json"


def _material_label(asset) -> str:
    try:
        return asset.get_editor_property("asset_name") or asset.get_name()
    except Exception:
        return asset.get_name()


def _capture_thumbnail(asset) -> str | None:
    import unreal

    try:
        options = unreal.AssetThumbnailCaptureOptions()
        options.size = unreal.IntPoint(256, 256)
        options.render_background = True
        options.background_color = unreal.LinearColor(0.15, 0.15, 0.15, 1.0)
        path = str(OUT_DIR / f"thumb_{asset.get_name()}.png")
        if hasattr(unreal, "AutomationLibrary"):
            unreal.AutomationLibrary.take_thumbnail(
                asset, path, options
            )
            return path
    except Exception:
        pass
    return None


def capture_material_previews() -> dict:
    import unreal

    OUT_DIR.mkdir(parents=True, exist_ok=True)
    dirs = [lib.MASTER_DIR, lib.ENV_INST_DIR]
    results = {}
    for folder in dirs:
        try:
            asset_list = unreal.EditorAssetLibrary.list_assets(folder, recursive=True)
        except Exception:
            asset_list = []
        for asset_path in asset_list:
            asset = unreal.load_asset(asset_path)
            if not asset:
                continue
            try:
                if not asset.is_a(unreal.MaterialInterface.static_class()):
                    continue
            except Exception:
                continue
            name = asset.get_name()
            entry = {"path": asset_path, "label": _material_label(asset)}
            thumb = _capture_thumbnail(asset)
            if thumb:
                entry["thumbnail"] = thumb
            results[name] = entry
    return {"ok": True, "count": len(results), "materials": results}


def write_previews_manifest() -> Path:
    """Capture previews and write previews_manifest.json; returns the path."""
    result = capture_material_previews()
    payload = {
        "generated_at": datetime.now(timezone.utc).isoformat(),
        "generated_by": "capture_material_previews.py",
        "ok": result.get("ok", False),
        **result,
    }
    OUT_DIR.mkdir(parents=True, exist_ok=True)
    REPORT.write_text(json.dumps(payload, indent=2), encoding="utf-8")
    return REPORT


def main() -> int:
    path = write_previews_manifest()
    payload = json.loads(path.read_text(encoding="utf-8"))
    print(f"MATERIAL_PREVIEWS captured={payload.get('count', 0)} -> {path}")
    return 0 if payload.get("ok") else 1


if __name__ == "__main__":
    raise SystemExit(main())