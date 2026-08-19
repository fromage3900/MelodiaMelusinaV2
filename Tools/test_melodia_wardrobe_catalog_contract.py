#!/usr/bin/env python3
"""Focused offline contract for the catalog-first V2 wardrobe source lane.

This test validates the checked-in source/spec/tooling boundary only. It does not
open Unreal, create a DataAsset, modify a Blueprint, inspect a ``.uasset``, or
claim equip/save/restore evidence. Those claims require editor readback and live
PIE, which belong to a later verification workstream.
"""
from __future__ import annotations

import json
import sys
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
MANIFEST = ROOT / "specs" / "wardrobe" / "wardrobe_catalog_manifest.v1.json"
SCHEMA = ROOT / "specs" / "wardrobe" / "wardrobe_catalog_source.v1.json"
CONTRACT = ROOT / "specs" / "wardrobe" / "wardrobe_catalog_contract.v1.json"
CATALOG_SCRIPT = ROOT / "Content" / "Python" / "create_melodia_cosmetic_catalog.py"
PAWN_SCRIPT = ROOT / "Content" / "Python" / "wire_melusina_wardrobe_component.py"
LINTER = ROOT / "Tools" / "wardrobe_draft_lint.py"


def load(path: Path) -> dict:
    value = json.loads(path.read_text(encoding="utf-8"))
    if not isinstance(value, dict):
        raise AssertionError(f"{path} must contain an object")
    return value


def main() -> int:
    schema = load(SCHEMA)
    contract = load(CONTRACT)
    manifest = load(MANIFEST)
    catalog_source = manifest["first_outfit"]
    records = catalog_source["records"]

    assert schema["properties"]["catalog_asset"]["const"] == manifest["catalog_asset"]
    assert schema["properties"]["first_outfit"]["properties"]["record_count"]["const"] == 5
    assert schema["properties"]["materialization"]["properties"]["editor_only"]["const"] is True
    assert contract["properties"]["target_count"]["const"] == 5
    assert contract["properties"]["gacha_count"]["const"] == 0
    assert contract["properties"]["battle_gate"]["const"] is False
    assert manifest["materialization_status"] == (
        "source_ready_editor_materialization_pending"
    )
    assert manifest["catalog_asset"] == (
        "/MelodiaWardrobe/Catalog/DA_MelodiaCosmeticCatalog"
    )
    assert len(records) == manifest["target_count"] == 5
    assert len({row["cosmetic_id"] for row in records}) == 5
    assert {row["slot"] for row in records} == {
        "Body",
        "Shirt",
        "Skirt",
        "Boots",
        "Accessories",
    }
    assert all(row["rarity"] == "Common" for row in records)
    assert all(row["resonant_form_id"] is None for row in records)
    assert all(
        row["mesh"].startswith(
            "/Game/Melodia/Characters/Melusina/Outfits/V2/SK_Melusina_V2_"
        )
        for row in records
    )
    assert catalog_source["default_slots"] == [
        "Shirt",
        "Skirt",
        "Boots",
        "Accessories",
    ]
    assert catalog_source["battle_wardrobe_enabled"] is False

    reconciliation = manifest["draft_reconciliation"]
    assert reconciliation["slot_aliases"] == {"dress": "Body"}
    assert reconciliation["rarity_aliases"] == {}
    assert set(reconciliation["deferred_rarity_values"]) == {"Refined", "Couture"}
    assert reconciliation["rarity_policy"] == {
        "status": "owner_decision_required",
        "unresolved_values": ["Refined", "Couture"],
        "import_action": "reject_until_explicit_mapping",
    }
    assert reconciliation["content_pack_field"] == "content_pack_id"
    assert reconciliation["content_pack_policy"] == (
        "preserve_when_present_optional_until_collection_authority"
    )
    assert reconciliation["larger_catalog_status"] == (
        "blocked_until_rarity_decision_and_mesh_mapping"
    )
    for shape in reconciliation["accepted_source_shapes"]:
        assert Path(ROOT / shape["root"]).is_dir(), shape["root"]

    # Exercise the same enum/mapping readers the draft linter uses. This catches
    # a source/spec drift without copying the enum vocabulary into this test.
    sys.path.insert(0, str(LINTER.parent))
    import wardrobe_draft_lint as draft_lint  # noqa: E402

    slots = draft_lint.read_enum(draft_lint.SLOT_HEADER, "EMelodiaWardrobeSlot")
    rarities = draft_lint.read_enum(
        draft_lint.RARITY_HEADER, "EMelodiaCosmeticRarity"
    )
    assert slots and rarities
    aliases = reconciliation["slot_aliases"]
    all_ids = set()
    deferred = {value.casefold() for value in reconciliation["deferred_rarity_values"]}
    mapped_slots = 0
    for path in draft_lint.draft_paths():
        draft = load(path)
        if "CosmeticId" in draft:
            identity, slot, rarity = (
                draft.get("CosmeticId"),
                draft.get("Slot"),
                draft.get("Rarity"),
            )
            assert draft.get("SourceDraftPath")
        else:
            identity, slot, rarity = (
                draft.get("id", path.stem),
                draft.get("slot"),
                draft.get("rarity"),
            )
        assert identity and identity not in all_ids, identity
        all_ids.add(identity)
        assert draft_lint.resolve_slot(slot, slots, aliases), (path, slot)
        mapped_slots += 1
        assert rarity in rarities or rarity.casefold() in deferred, (path, rarity)
    assert mapped_slots == len(all_ids) == len(draft_lint.draft_paths())
    lint_report, lint_code = draft_lint.lint()
    assert lint_code == 0
    assert lint_report["blocking_count"] == 0
    assert lint_report["owner_decision_count"] == 23
    assert lint_report["unmodelled_count"] == 0
    assert set(lint_report["content_pack_mappings"].values()) == {
        "Core",
        "Pack_MoonlitSonata",
        "Pack_GildedOverture",
    }

    catalog_text = CATALOG_SCRIPT.read_text(encoding="utf-8")
    assert "SOURCE_MANIFEST" in catalog_text
    assert "catalog_diff" in catalog_text
    assert "--replace-existing" in catalog_text
    assert "--dry-run" in catalog_text
    assert "save_loaded_asset" in catalog_text
    assert "resolve_meshes" in catalog_text
    assert "EditorAssetLibrary.load_asset" in catalog_text
    assert "_is_skeletal_mesh" in catalog_text
    assert "resolved_meshes[source[\"mesh\"]]" in catalog_text
    assert "SoftObjectPath(source[\"mesh\"])" not in catalog_text
    assert catalog_text.index("records = build_records") < catalog_text.index(
        "create_asset("
    )
    assert "cleanup_deleted_new_catalog" in catalog_text
    assert "gacha_must_remain_disabled" in catalog_text
    assert "first_outfit_must_remain_decorative" in catalog_text
    assert "content_pack_id" in catalog_text
    assert "reject_until_explicit_mapping" in catalog_text
    assert "PIECES =" not in catalog_text

    pawn_text = PAWN_SCRIPT.read_text(encoding="utf-8")
    assert "BP_MelusinaJRPGCharacter" in pawn_text
    assert "MelodiaWardrobeComponent" in pawn_text
    assert "b_enable_battle_wardrobe" in pawn_text
    assert "legacy_outfit_component_present_refuse_mutation" in pawn_text
    assert "editor_compile_save_and_readback" in pawn_text

    print(
        "validated V2 catalog source, draft mappings, "
        f"and editor materialization guards ({len(records)} first-outfit records)"
    )
    print(
        "materialization remains editor-pending; no asset or live equip proof claimed"
    )
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
