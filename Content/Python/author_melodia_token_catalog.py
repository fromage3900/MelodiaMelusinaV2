"""Author DA_MelodiaTokenCatalog from the canonical gmm TOKEN_TYPES model.

Single source of truth: Content/Python/gmm/game/tokens.py TOKEN_TYPES.
Do NOT hand-edit rows. Regenerate them (per MelodiaTokenCatalog.h).
"""
from __future__ import annotations

import unreal

ASSET_PATH = "/Game/Melodia/Data/DA_MelodiaTokenCatalog"
ASSET_DIR = "/Game/Melodia/Data"

ROWS = [
    {
        "variant_id": "heart",
        "display_name": "Forte Shard",
        "element": unreal.MelodiaSpellElement.FORTE,
        "value": 10,
        "rarity": "common",
        "icon": "/Game/EnvSandbox/Textures/melodsytoken/Textures/T_MelodyToken_Heart_BaseColor",
        "material": "/Game/EnvSandbox/Materials/Instances/MelodyTokens/MI_MelodyToken_Heart",
    },
    {
        "variant_id": "star",
        "display_name": "Radiant Shard",
        "element": unreal.MelodiaSpellElement.RADIANT,
        "value": 12,
        "rarity": "uncommon",
        "icon": "/Game/EnvSandbox/Textures/melodsytoken_textures/MelodyToken_Star_BaseColor",
        "material": "/Game/EnvSandbox/Materials/Instances/MelodyTokens/MI_MelodyToken_Star",
    },
    {
        "variant_id": "swirl",
        "display_name": "Arcane Shard",
        "element": unreal.MelodiaSpellElement.ARCANE,
        "value": 15,
        "rarity": "rare",
        "icon": "/Game/EnvSandbox/Textures/melodsytoken_textures/MelodyToken_Swirl_BaseColor",
        "material": "/Game/EnvSandbox/Materials/Instances/MelodyTokens/MI_MelodyToken_Swirl",
    },
    {
        "variant_id": "water",
        "display_name": "Tide Shard",
        "element": unreal.MelodiaSpellElement.TIDE,
        "value": 12,
        "rarity": "common",
        "icon": "/Game/EnvSandbox/Textures/melodsytoken_textures/MelodyToken_Water_BaseColor",
        "material": "/Game/EnvSandbox/Materials/Instances/MelodyTokens/MI_MelodyToken_Water",
    },
]


def row_to_def(row: dict) -> unreal.MelodiaTokenDefinition:
    d = unreal.MelodiaTokenDefinition()
    d.set_editor_property("variant_id", row["variant_id"])
    d.set_editor_property("display_name", unreal.Text(row["display_name"]))
    d.set_editor_property("element", row["element"])
    d.set_editor_property("value", row["value"])
    d.set_editor_property("rarity", row["rarity"])
    icon = unreal.EditorAssetLibrary.load_asset(row["icon"])
    if icon:
        d.set_editor_property("icon", icon)
    else:
        print(f"WARN icon missing: {row['icon']}")
    material = unreal.EditorAssetLibrary.load_asset(row["material"])
    if material:
        d.set_editor_property("material", material)
    else:
        print(f"WARN material missing: {row['material']}")
    return d


def main():
    asset = unreal.EditorAssetLibrary.load_asset(ASSET_PATH)
    if not asset:
        factory = unreal.DataAssetFactory()
        factory.set_editor_property("data_asset_class", unreal.MelodiaTokenCatalog)
        asset = unreal.AssetToolsHelpers.get_asset_tools().create_asset(
            "DA_MelodiaTokenCatalog", ASSET_DIR, unreal.MelodiaTokenCatalog, factory
        )
        if not asset:
            raise RuntimeError("Could not create MelodiaTokenCatalog asset")

    definitions = [row_to_def(r) for r in ROWS]
    asset.set_editor_property("tokens", definitions)
    asset.set_editor_property("generated_from", "Content/Python/gmm/game/tokens.py")

    unreal.EditorAssetLibrary.save_asset(ASSET_PATH)
    for r in ROWS:
        print(f"ROW {r['variant_id']}: {r['display_name']} element={r['element']} value={r['value']} rarity={r['rarity']}")
    print("SAVED", ASSET_PATH)


if __name__ == "__main__":
    main()