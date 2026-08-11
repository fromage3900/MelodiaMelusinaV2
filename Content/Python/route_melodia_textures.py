"""Route Melodia procedural textures from _PROJECT to EnvSandbox via UE asset duplication.

Uses unreal.EditorAssetLibrary.duplicate_asset() for proper internal name migration.
Must run IN-EDITOR (Python Editor Script Plugin). Headless UE can't duplicate uassets.

Run in editor:
  py "G:/EnvironmentPortfolio/BS_GodFile/Content/Python/route_melodia_textures.py"
  py "G:/EnvironmentPortfolio/BS_GodFile/Content/Python/route_melodia_textures.py" --dry-run
  py "G:/EnvironmentPortfolio/BS_GodFile/Content/Python/route_melodia_textures.py" --family Voronoi,Vein,Marble
"""
from __future__ import annotations

import json
import sys
from datetime import datetime, timezone
from pathlib import Path

import unreal

PROJECT_ROOT = Path(__file__).resolve().parents[2]
SRC_BASE = "/Game/Melodia/_PROJECT/04_Materials/Textures"
DST_BASE = "/Game/EnvSandbox/Materials/SDF/Textures"
REPORT = PROJECT_ROOT / "Saved" / "Audit" / "melodia_texture_route.json"

TEXTURE_FAMILIES = [
    "Voronoi", "Vein", "Swirl", "Milky", "Grainy", "Cracks",
    "Marble", "Gabor", "Manifold", "Melt", "Perlin", "Super_Noise",
    "Super_Perlin", "Streak", "Spokes", "Techno", "Turbulence", "Craters",
]


def _ensure_dir(path: str) -> None:
    if not unreal.EditorAssetLibrary.does_directory_exist(path):
        unreal.EditorAssetLibrary.make_directory(path)


def route_family(family: str, dry_run: bool = False) -> dict:
    src_dir = f"{SRC_BASE}/{family}"
    dst_dir = f"{DST_BASE}/{family}"

    if not unreal.EditorAssetLibrary.does_directory_exist(src_dir):
        return {"family": family, "status": "source_missing", "count": 0}

    _ensure_dir(dst_dir)

    assets = unreal.EditorAssetLibrary.list_assets(src_dir, recursive=False, include_folder=False)
    if not assets:
        return {"family": family, "status": "empty", "count": 0}

    duplicated = []
    existed = []
    failed = []

    for src_path in assets:
        asset_name = src_path.rsplit("/", 1)[-1].rsplit(".", 1)[0]
        dst_path = f"{dst_dir}/{asset_name}"

        if unreal.EditorAssetLibrary.does_asset_exist(dst_path):
            existed.append(asset_name)
            continue

        if dry_run:
            duplicated.append(asset_name)
            continue

        try:
            unreal.EditorAssetLibrary.duplicate_asset(
                source_asset_path=src_path,
                destination_asset_path=dst_path,
            )
            duplicated.append(asset_name)
        except Exception as exc:
            failed.append({"name": asset_name, "error": str(exc)})

    result = {
        "family": family,
        "total": len(assets),
        "duplicated": len(duplicated),
        "existed": len(existed),
        "failed": len(failed),
    }
    if duplicated:
        result["sample"] = duplicated[:5]
    if failed:
        result["failures"] = failed[:5]

    unreal.log(f"[TextureRoute] {family}: {len(duplicated)} dup, {len(existed)} exist, {len(failed)} fail")
    return result


def main() -> int:
    dry_run = "--dry-run" in sys.argv

    # Filter families
    families = TEXTURE_FAMILIES
    for arg in sys.argv:
        if arg.startswith("--family=") or arg.startswith("--family "):
            val = arg.split("=", 1)[-1] if "=" in arg else ""
            if val:
                families = [f.strip() for f in val.split(",")]

    unreal.log("=== Routing Melodia textures to EnvSandbox ===")
    if dry_run:
        unreal.log("DRY RUN — no assets will be duplicated")

    results = []
    total_dup = 0
    total_exist = 0
    total_fail = 0

    for family in families:
        r = route_family(family, dry_run)
        results.append(r)
        total_dup += r["duplicated"]
        total_exist += r["existed"]
        total_fail += r["failed"]

    report = {
        "timestamp": datetime.now(timezone.utc).isoformat(),
        "dry_run": dry_run,
        "families_processed": len(families),
        "total_duplicated": total_dup,
        "total_existed": total_exist,
        "total_failed": total_fail,
        "results": results,
    }

    REPORT.parent.mkdir(parents=True, exist_ok=True)
    REPORT.write_text(json.dumps(report, indent=2, ensure_ascii=False, default=str), encoding="utf-8")

    unreal.log(f"[TextureRoute] Done: {total_dup} dup, {total_exist} exist, {total_fail} fail -> {REPORT}")
    unreal.EditorLoadingAndSavingUtils.save_dirty_packages(True, True)
    return 0 if total_fail == 0 else 1


if __name__ == "__main__":
    raise SystemExit(main())
