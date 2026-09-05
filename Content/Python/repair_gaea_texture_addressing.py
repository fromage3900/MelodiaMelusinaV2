"""Keep full-landscape Gaea maps from repeating at the normalized UV boundary."""

import json
import os
import unreal


TEXTURES = [
    "/Game/Gaea/Glacier/Textures/T_Glacier_ColorErosion",
    "/Game/Gaea/Glacier/Textures/T_Glacier_Combine",
    "/Game/Gaea/Glacier/Textures/T_Glacier_GroundTexture",
    "/Game/Gaea/Glacier/Textures/T_Glacier_SatMap",
    "/Game/Gaea/Glacier/Textures/W_Glacier_Snow",
    "/Game/Gaea/Glacier/Textures/W_Glacier_Water",
    "/Game/Gaea/Glacier/Textures/W_Glacier_Rock",
]
REPORT_PATH = "C:/EnvironmentPortfolio/BS_GodFile/Saved/Audit/gaea_texture_addressing_2026-09-04.json"


def run():
    rows = []
    for path in TEXTURES:
        texture = unreal.EditorAssetLibrary.load_asset(path)
        if texture is None:
            rows.append({"asset_path": path, "status": "missing"})
            continue
        before = {
            "address_x": str(texture.get_editor_property("address_x")),
            "address_y": str(texture.get_editor_property("address_y")),
        }
        texture.set_editor_property("address_x", unreal.TextureAddress.TA_CLAMP)
        texture.set_editor_property("address_y", unreal.TextureAddress.TA_CLAMP)
        unreal.EditorAssetLibrary.save_loaded_asset(texture, False)
        rows.append({
            "asset_path": path,
            "status": "saved",
            "before": before,
            "after": {
                "address_x": str(texture.get_editor_property("address_x")),
                "address_y": str(texture.get_editor_property("address_y")),
            },
        })
    summary = {"count": len(rows), "saved": sum(1 for row in rows if row["status"] == "saved"), "rows": rows}
    os.makedirs(os.path.dirname(REPORT_PATH), exist_ok=True)
    with open(REPORT_PATH, "w", encoding="utf-8") as handle:
        json.dump(summary, handle, indent=2)
    return summary


if __name__ == "__main__":
    print(run())
