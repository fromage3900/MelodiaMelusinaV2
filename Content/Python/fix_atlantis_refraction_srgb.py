"""One-off: fix sRGB flag on the Atlantis WaterClean refraction.inverted texture.

The first import run reported it failed because the dotted stem was used as the
asset path, but the importer auto-sanitized it to
KB3D_ATL_WaterClean_refraction_inverted. Its sRGB flag was never set (defaults
to on; refraction must be sRGB off). This script sets it and saves.
"""
from __future__ import annotations

import json
from datetime import datetime, timezone
from pathlib import Path

import unreal

PATH = "/Game/EnvSandbox/Textures/Atlantis/KB3D_ATL_WaterClean_refraction_inverted"
REPORT = Path(__file__).resolve().parents[2] / "Saved" / "Audit" / "atlantis_refraction_srgb_fix.json"

tex = unreal.EditorAssetLibrary.load_asset(PATH)
if not tex:
    result = {"ok": False, "error": f"load failed: {PATH}",
              "candidates": unreal.EditorAssetLibrary.list_assets(
                  "/Game/EnvSandbox/Textures/Atlantis", recursive=False,
                  include_folder=True)}
else:
    tex.set_editor_property("srgb", False)
    saved = unreal.EditorAssetLibrary.save_loaded_asset(tex, only_if_is_dirty=True)
    result = {"ok": saved, "path": PATH, "srgb": False,
              "texture_class": type(tex).__name__}
result["timestamp"] = datetime.now(timezone.utc).isoformat()
REPORT.parent.mkdir(parents=True, exist_ok=True)
REPORT.write_text(json.dumps(result, indent=2), encoding="utf-8")
print(json.dumps(result, indent=2))
raise SystemExit(0 if result.get("ok") else 1)