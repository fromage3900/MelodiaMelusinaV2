"""Apply soft pastel BaseTint on NikkiHero pillar MIs for readability.

Run in-editor:
  py Content/Python/fix_nikki_hero_base_tints.py
"""
from __future__ import annotations

import json
from datetime import datetime, timezone
from pathlib import Path

import material_lib as lib
import mi_preview_studio as studio

REPORT = studio.PROJECT_ROOT / "Saved" / "Audit" / "nikki_hero_base_tint_fix.json"


def apply_tints() -> dict:
    import unreal

    results = []
    for name, rgba in studio.NIKKI_HERO_BASE_TINTS.items():
        path = f"{studio.NIKKI_HERO_DIR}/{name}.{name}"
        if not unreal.EditorAssetLibrary.does_asset_exist(path):
            results.append({"id": name, "ok": False, "error": "missing"})
            continue
        mi = unreal.load_asset(path)
        lib.set_instance_vector(mi, "BaseTint", rgba)
        # Keep magical/sparkle restrained for stills
        try:
            lib.set_instance_scalar(mi, "MagicalIntensity", 0.35)
            lib.set_instance_scalar(mi, "IridescencePower", 0.45)
        except Exception:
            pass
        unreal.EditorAssetLibrary.save_asset(path)
        results.append({"id": name, "ok": True, "base_tint": list(rgba), "path": path})
    report = {
        "generated_at": datetime.now(timezone.utc).isoformat(),
        "ok": all(r.get("ok") for r in results),
        "results": results,
    }
    REPORT.parent.mkdir(parents=True, exist_ok=True)
    REPORT.write_text(json.dumps(report, indent=2), encoding="utf-8")
    print(json.dumps(report, indent=2))
    return report


def main() -> int:
    report = apply_tints()
    return 0 if report.get("ok") else 1


if __name__ == "__main__":
    raise SystemExit(main())
