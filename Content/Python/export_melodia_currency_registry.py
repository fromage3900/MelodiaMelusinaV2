"""Export the canonical economy DataAssets to their text mirrors.

DA_MelodiaCurrencyRegistry -> specs/economy/melodia_currency_registry.v1.json
DA_MelodiaTokenCatalog     -> specs/economy/melodia_token_catalog.v1.json

WHY THIS EXISTS

The DataAssets are canonical (Decision 055): a designer edits currencies and token variants
in the editor, not in Python. But a .uasset is binary, and four consumers need to read the
economy WITHOUT launching Unreal:

  * Content/Python/gmm/game/tokens.py  (the mirrored model, and its pytest suite)
  * Tools/wardrobe_draft_lint.py       (resolves cosmetic token_cost variants to elements)
  * deploy/melodia_mcp_server.py       (melodia_economy_get_currency_registry)
  * CI                                 (schema validation, freshness gate)

So the .uasset is the authority and this export is the publication step. Run it after every
registry or catalog edit. The melodia_economy_registry_export_fresh CI gate fails when these
JSON files are older than the assets they mirror, which is what stops the inversion rotting.

USAGE (inside the Unreal editor's Python console, or via -ExecutePythonScript):

    py Content/Python/export_melodia_currency_registry.py
"""
from __future__ import annotations

import json
import os

import unreal

REGISTRY_ASSET = "/Game/Melodia/Data/DA_MelodiaCurrencyRegistry"
CATALOG_ASSET = "/Game/Melodia/Data/DA_MelodiaTokenCatalog"

# Content/Python/<this file> -> project root is two levels up.
PROJECT_ROOT = os.path.abspath(os.path.join(os.path.dirname(__file__), "..", ".."))
ECONOMY_DIR = os.path.join(PROJECT_ROOT, "specs", "economy")
REGISTRY_JSON = os.path.join(ECONOMY_DIR, "melodia_currency_registry.v1.json")
CATALOG_JSON = os.path.join(ECONOMY_DIR, "melodia_token_catalog.v1.json")

KIND_NAMES = {
    unreal.MelodiaCurrencyKind.SHARD: "Shard",
    unreal.MelodiaCurrencyKind.PREMIUM: "Premium",
    unreal.MelodiaCurrencyKind.RESOURCE: "Resource",
}

ELEMENT_NAMES = {
    unreal.MelodiaSpellElement.FORTE: "Forte",
    unreal.MelodiaSpellElement.TIDE: "Tide",
    unreal.MelodiaSpellElement.GALE: "Gale",
    unreal.MelodiaSpellElement.STONE: "Stone",
    unreal.MelodiaSpellElement.RADIANT: "Radiant",
    unreal.MelodiaSpellElement.UMBRAL: "Umbral",
    unreal.MelodiaSpellElement.ARCANE: "Arcane",
}

KIND_DOCS = {
    "Shard": "Integer, uncapped, GrantId-idempotent. The seven elemental shards.",
    "Premium": "Integer, uncapped, GrantId-idempotent, refundable after a failed purchase.",
    "Resource": (
        "Float, clamped to max_value. Regenerating; not idempotent when granted "
        "without a GrantId."
    ),
}

AUTHORITY_NOTE = (
    "The UE DataAsset is canonical (Decision 055). This file is its text mirror, read by "
    "gmm/game/tokens.py, Tools/wardrobe_draft_lint.py, pytest, CI and the melodia MCP server "
    "so none of them needs a running editor. Re-export after every registry edit; the "
    "melodia_economy_registry_export_fresh CI gate fails if this file is older than the .uasset."
)


def _soft_path(value) -> str:
    """Package path for a TSoftObjectPtr property, or "" when unset."""
    if not value:
        return ""
    try:
        return str(value.get_path_name()).split(".")[0]
    except AttributeError:
        return str(value)


def _currency_row(row) -> dict:
    kind = KIND_NAMES.get(row.get_editor_property("kind"), "Shard")
    color = row.get_editor_property("accent_color")
    out = {
        "currency_id": str(row.get_editor_property("currency_id")),
        "display_name": str(row.get_editor_property("display_name")),
        "description": str(row.get_editor_property("description")),
        "kind": kind,
        "default_value": float(row.get_editor_property("default_value")),
        "max_value": float(row.get_editor_property("max_value")),
        "refundable": bool(row.get_editor_property("refundable")),
        "counts_toward_total_collected": bool(
            row.get_editor_property("counts_toward_total_collected")
        ),
        "sort_order": int(row.get_editor_property("sort_order")),
        "accent_color": [float(color.r), float(color.g), float(color.b), float(color.a)],
        "has_legacy_element": bool(row.get_editor_property("has_legacy_element")),
        "legacy_element": ELEMENT_NAMES.get(
            row.get_editor_property("legacy_element"), "Forte"
        ),
    }
    icon = _soft_path(row.get_editor_property("icon"))
    material = _soft_path(row.get_editor_property("material"))
    if icon:
        out["icon"] = icon
    if material:
        out["material"] = material
    return out


def _token_row(row) -> dict:
    try:
        currency_id = str(row.get_editor_property("currency_id"))
    except Exception:
        # Older cooked catalogs only carried the seven-element compatibility field.
        currency_id = ""
    return {
        "variant_id": str(row.get_editor_property("variant_id")),
        "display_name": str(row.get_editor_property("display_name")),
        "currency_id": currency_id,
        "element": ELEMENT_NAMES.get(row.get_editor_property("element"), "Forte"),
        "value": int(row.get_editor_property("value")),
        "rarity": str(row.get_editor_property("rarity")),
        "texture_path": _soft_path(row.get_editor_property("icon")),
        "material_path": _soft_path(row.get_editor_property("material")),
    }


def _write(path: str, payload: dict) -> None:
    os.makedirs(os.path.dirname(path), exist_ok=True)
    with open(path, "w", encoding="utf-8", newline="\n") as handle:
        json.dump(payload, handle, indent=2, ensure_ascii=False)
        handle.write("\n")
    print(f"WROTE {path}")


def export_registry() -> bool:
    asset = unreal.EditorAssetLibrary.load_asset(REGISTRY_ASSET)
    if not asset:
        print(f"ERROR registry asset not found: {REGISTRY_ASSET}")
        return False

    rows = [_currency_row(row) for row in asset.get_editor_property("currencies")]

    # Fail loudly rather than publishing a mirror the wallet would reject. A duplicate id
    # makes Find ambiguous, and an empty id can never be granted or spent.
    ids = [row["currency_id"] for row in rows]
    duplicates = sorted({i for i in ids if ids.count(i) > 1})
    if duplicates:
        print(f"ERROR duplicate currency_id(s) in the registry: {duplicates}")
        return False
    if any(not i for i in ids):
        print("ERROR a registry row has an empty currency_id")
        return False

    _write(
        REGISTRY_JSON,
        {
            "schema": "melodia_currency_registry.v1",
            "generated_from": REGISTRY_ASSET,
            "generator": "Content/Python/export_melodia_currency_registry.py",
            "authority_note": AUTHORITY_NOTE,
            "registry_schema_version": int(
                asset.get_editor_property("registry_schema_version")
            ),
            "kinds": KIND_DOCS,
            "currencies": sorted(rows, key=lambda r: (r["sort_order"], r["currency_id"])),
        },
    )
    return True


def export_catalog() -> bool:
    asset = unreal.EditorAssetLibrary.load_asset(CATALOG_ASSET)
    if not asset:
        print(f"ERROR token catalog asset not found: {CATALOG_ASSET}")
        return False

    tokens = [_token_row(row) for row in asset.get_editor_property("tokens")]

    # Preserve the non-asset-backed extra elemental variants already published in the mirror.
    # They have no catalog rows yet, and dropping them here would silently shrink the
    # vocabulary Tools/wardrobe_draft_lint.py validates cosmetic token_cost against.
    extras = []
    if os.path.exists(CATALOG_JSON):
        try:
            with open(CATALOG_JSON, encoding="utf-8") as handle:
                extras = json.load(handle).get("extra_elemental_types", [])
        except (OSError, ValueError) as exc:
            print(f"WARN could not read existing catalog mirror ({exc}); extras will be empty")

    # Once the restore script has authored a formerly-extra variant into the DataAsset,
    # the exported row is authoritative. Do not publish the same variant twice in the
    # mirror; the offline loaders intentionally merge both sections.
    authored_variant_ids = {row["variant_id"] for row in tokens}
    extras = [row for row in extras if row.get("variant_id") not in authored_variant_ids]

    _write(
        CATALOG_JSON,
        {
            "schema": "melodia_token_catalog.v1",
            "generated_from": CATALOG_ASSET,
            "generator": "Content/Python/export_melodia_currency_registry.py",
            "authority_note": AUTHORITY_NOTE,
            "tokens": tokens,
            "extra_elemental_types": extras,
        },
    )
    return True


def main() -> None:
    ok_registry = export_registry()
    ok_catalog = export_catalog()
    if ok_registry and ok_catalog:
        print("MELODIA_ECONOMY export complete.")
    else:
        print("MELODIA_ECONOMY export INCOMPLETE — see errors above. Mirrors were not fully updated.")


if __name__ == "__main__":
    main()
