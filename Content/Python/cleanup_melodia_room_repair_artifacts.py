"""Remove only known redundant maps created by interrupted RoomData repair attempts."""

import json
from pathlib import Path

import unreal


KNOWN_REDUNDANT_ASSETS = [
    "/Game/Melodia/Roguelike/Rooms/L_MelodiaGrove_V2_V2",
]
REPORT = Path(unreal.Paths.project_saved_dir()) / "Audit" / "melodia_room_repair_cleanup.json"


def main() -> None:
    rows = []
    for asset_path in KNOWN_REDUNDANT_ASSETS:
        if not unreal.EditorAssetLibrary.does_asset_exist(asset_path):
            rows.append({"asset": asset_path, "status": "already_absent"})
            continue
        referencers = list(unreal.EditorAssetLibrary.find_package_referencers_for_asset(asset_path, load_assets_to_confirm=True))
        if referencers:
            rows.append({"asset": asset_path, "status": "retained", "referencers": referencers})
            continue
        deleted = unreal.EditorAssetLibrary.delete_asset(asset_path)
        rows.append({"asset": asset_path, "status": "deleted" if deleted else "delete_failed"})

    REPORT.parent.mkdir(parents=True, exist_ok=True)
    REPORT.write_text(json.dumps({"rows": rows}, indent=2), encoding="utf-8")
    if any(row["status"] in {"retained", "delete_failed"} for row in rows):
        raise RuntimeError("Redundant repair artifact cleanup did not complete")


if __name__ == "__main__":
    main()
