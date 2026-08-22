"""Bootstrap DA_MelodiaCurrencyRegistry from its JSON mirror.

This is the RESTORE direction, and it is deliberately the exception rather than the rule.
The DataAsset is canonical (Decision 055); export_melodia_currency_registry.py is the script
that normally runs. Use this one only to:

  * seed the asset the first time, from specs/economy/melodia_currency_registry.v1.json
  * restore it on a fresh clone, or after an accidental delete
  * re-materialise it in CI, where no one has ever opened the editor

It OVERWRITES every row in the asset with what the JSON says. If someone has edited the asset
in the editor and not exported, running this discards their edits — so it refuses unless the
JSON is at least as new as the asset, unless you pass force=True.

USAGE (inside the Unreal editor's Python console):

    py Content/Python/author_melodia_currency_registry.py
"""
from __future__ import annotations

import json
import os

import unreal

ASSET_DIR = "/Game/Melodia/Data"
ASSET_NAME = "DA_MelodiaCurrencyRegistry"
ASSET_PATH = f"{ASSET_DIR}/{ASSET_NAME}"

PROJECT_ROOT = os.path.abspath(os.path.join(os.path.dirname(__file__), "..", ".."))
REGISTRY_JSON = os.path.join(
    PROJECT_ROOT, "specs", "economy", "melodia_currency_registry.v1.json"
)

KINDS = {
    "Shard": unreal.MelodiaCurrencyKind.SHARD,
    "Premium": unreal.MelodiaCurrencyKind.PREMIUM,
    "Resource": unreal.MelodiaCurrencyKind.RESOURCE,
}

ELEMENTS = {
    "Forte": unreal.MelodiaSpellElement.FORTE,
    "Tide": unreal.MelodiaSpellElement.TIDE,
    "Gale": unreal.MelodiaSpellElement.GALE,
    "Stone": unreal.MelodiaSpellElement.STONE,
    "Radiant": unreal.MelodiaSpellElement.RADIANT,
    "Umbral": unreal.MelodiaSpellElement.UMBRAL,
    "Arcane": unreal.MelodiaSpellElement.ARCANE,
}


def row_to_definition(row: dict) -> unreal.MelodiaCurrencyDefinition:
    d = unreal.MelodiaCurrencyDefinition()
    d.set_editor_property("currency_id", row["currency_id"])
    d.set_editor_property("display_name", unreal.Text(row.get("display_name", "")))
    d.set_editor_property("description", unreal.Text(row.get("description", "")))
    d.set_editor_property("kind", KINDS[row["kind"]])
    d.set_editor_property("default_value", float(row.get("default_value", 0.0)))
    d.set_editor_property("max_value", float(row.get("max_value", 0.0)))
    d.set_editor_property("refundable", bool(row.get("refundable", False)))
    d.set_editor_property(
        "counts_toward_total_collected",
        bool(row.get("counts_toward_total_collected", True)),
    )
    d.set_editor_property("sort_order", int(row.get("sort_order", 0)))

    color = row.get("accent_color")
    if color and len(color) == 4:
        d.set_editor_property("accent_color", unreal.LinearColor(*[float(c) for c in color]))

    d.set_editor_property("has_legacy_element", bool(row.get("has_legacy_element", False)))
    d.set_editor_property("legacy_element", ELEMENTS[row.get("legacy_element", "Forte")])

    for prop, key in (("icon", "icon"), ("material", "material")):
        path = row.get(key)
        if not path:
            continue
        loaded = unreal.EditorAssetLibrary.load_asset(path)
        if loaded:
            d.set_editor_property(prop, loaded)
        else:
            # Presentation only; a missing icon must not block seeding the economy.
            print(f"WARN {row['currency_id']}: {key} not found: {path}")
    return d


def main(force: bool = False) -> None:
    if not os.path.exists(REGISTRY_JSON):
        print(f"ERROR mirror not found: {REGISTRY_JSON}")
        return

    with open(REGISTRY_JSON, encoding="utf-8") as handle:
        payload = json.load(handle)

    rows = payload.get("currencies", [])
    if not rows:
        print("ERROR mirror declares no currencies; refusing to author an empty registry "
              "(every wallet transaction would be rejected).")
        return

    existing = unreal.EditorAssetLibrary.load_asset(ASSET_PATH)
    if existing and not force:
        # Guard against silently discarding unexported editor work.
        asset_file = unreal.SystemLibrary.get_project_content_directory() + \
            ASSET_PATH.replace("/Game/", "") + ".uasset"
        if os.path.exists(asset_file) and os.path.getmtime(asset_file) > os.path.getmtime(REGISTRY_JSON):
            print(
                f"REFUSED {ASSET_NAME} is newer than its JSON mirror. Someone edited the asset "
                "and did not export. Run export_melodia_currency_registry.py first, or call "
                "main(force=True) to discard those edits."
            )
            return

    asset = existing
    if not asset:
        factory = unreal.DataAssetFactory()
        factory.set_editor_property("data_asset_class", unreal.MelodiaCurrencyRegistry)
        asset = unreal.AssetToolsHelpers.get_asset_tools().create_asset(
            ASSET_NAME, ASSET_DIR, unreal.MelodiaCurrencyRegistry, factory
        )
        if not asset:
            print(f"ERROR could not create {ASSET_PATH}")
            return

    asset.set_editor_property(
        "registry_schema_version", int(payload.get("registry_schema_version", 1))
    )
    asset.set_editor_property("currencies", [row_to_definition(row) for row in rows])

    unreal.EditorAssetLibrary.save_asset(ASSET_PATH)
    print(f"AUTHORED {ASSET_PATH} with {len(rows)} currencies: "
          f"{', '.join(r['currency_id'] for r in rows)}")


if __name__ == "__main__":
    main()
