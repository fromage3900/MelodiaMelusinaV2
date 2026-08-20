#!/usr/bin/env python3
"""Offline contract suite for the wardrobe grant/equip/present transaction.

Why this exists
---------------
The wardrobe writes into ``FMelodiaNarrativeRecord`` -- the canonical save record.
Three defects shipped there because nothing checked the *order* of validation and
mutation:

1. ``GrantCosmetic`` added a cosmetic id to the persisted ``OwnedCosmeticIds`` with
   no catalog lookup at all, so a typo'd or retired id became a permanent
   unresolvable entry in the save.
2. It broadcast ``EMelodiaWardrobeSlot::Body`` unconditionally, so every listener
   saw a hat grant as a body change.
3. ``FindOrCreateSlotComponent`` bound the leader pose before the mesh existed,
   never registered the component with its owning actor, and left the default
   query+physics collision enabled on a purely cosmetic garment.

Each is a silent no-op or a silently wrong value -- the class of defect this
project keeps paying for -- so each one is asserted here rather than left to a
future reviewer to notice again.

This suite is pure source analysis. It does not open the editor, load Unreal, hit
Monolith, or touch the network. It asserts the shape of the C++, which is what an
offline gate can honestly prove; runtime behaviour needs the editor lane's PIE
evidence and is deliberately not claimed here.

Usage:
    python Tools/test_melodia_wardrobe_transaction_contract.py
"""

from __future__ import annotations

import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]

WARDROBE = ROOT / "Plugins/MelodiaWardrobe/Source/MelodiaWardrobe"
SUBSYSTEM_CPP = WARDROBE / "Private/MelodiaWardrobeSubsystem.cpp"
SUBSYSTEM_H = WARDROBE / "Public/MelodiaWardrobeSubsystem.h"
COMPONENT_CPP = WARDROBE / "Private/MelodiaWardrobeComponent.cpp"
COMPONENT_H = WARDROBE / "Public/MelodiaWardrobeComponent.h"
GACHA_CPP = WARDROBE / "Private/MelodiaWardrobeGachaSubsystem.cpp"
DEFINITION_CPP = WARDROBE / "Private/MelodiaCosmeticDefinition.cpp"

CATALOG_ASSET_PATH = "/MelodiaWardrobe/Catalog/DA_MelodiaCosmeticCatalog"

_results: list[tuple[bool, str]] = []


def check(condition: bool, label: str) -> None:
    _results.append((bool(condition), label))


def read(path: Path) -> str:
    if not path.is_file():
        return ""
    return path.read_text(encoding="utf-8", errors="replace")


def function_body(text: str, signature: str) -> str:
    """Return the body of a top-level C++ function, or '' when absent.

    Relies on the project's brace style: a definition's closing brace is the first
    '\\n}' at column zero after the signature. Good enough for these files and it
    fails to '' rather than matching something arbitrary.
    """
    start = text.find(signature)
    if start == -1:
        return ""
    end = text.find("\n}", start)
    if end == -1:
        return ""
    return text[start:end]


def ordered(body: str, first: str, second: str) -> bool:
    """True when both markers are present and `first` precedes `second`."""
    a, b = body.find(first), body.find(second)
    return a != -1 and b != -1 and a < b


def main() -> int:
    sub_cpp = read(SUBSYSTEM_CPP)
    sub_h = read(SUBSYSTEM_H)
    comp_cpp = read(COMPONENT_CPP)
    comp_h = read(COMPONENT_H)
    gacha = read(GACHA_CPP)
    definition_cpp = read(DEFINITION_CPP)

    for label, text in (
        ("wardrobe subsystem .cpp readable", sub_cpp),
        ("wardrobe subsystem .h readable", sub_h),
        ("wardrobe component .cpp readable", comp_cpp),
        ("wardrobe component .h readable", comp_h),
        ("wardrobe gacha .cpp readable", gacha),
        ("cosmetic definition .cpp readable", definition_cpp),
    ):
        check(bool(text), label)

    if not all((sub_cpp, sub_h, comp_cpp, comp_h, gacha, definition_cpp)):
        report()
        return 1

    # --- One validation seam, used by both mutating paths --------------------
    check(
        "FindGrantableRecord" in sub_h,
        "subsystem declares the FindGrantableRecord validation seam",
    )
    validator = function_body(sub_cpp, "const FMelodiaCosmeticRecord* UMelodiaWardrobeSubsystem::FindGrantableRecord")
    check(bool(validator), "FindGrantableRecord is defined")
    for token in ("no_catalog", "unknown_id", "unauthored_mesh", "missing_mesh"):
        check(
            token in validator,
            f"validator reports a typed reason for {token}",
        )
    check(
        "Mesh.IsNull()" in validator,
        "validator refuses a catalog record with no authored mesh",
    )
    check(
        "LoadSynchronous" in validator,
        "validator refuses a non-null soft path whose mesh cannot load",
    )
    check(
        "CosmeticId.IsNone()" in validator
        and '"unknown_id"' in validator,
        "validator refuses an empty cosmetic id before catalog lookup",
    )

    # --- Grant: validate BEFORE touching the persisted record -----------------
    grant = function_body(sub_cpp, "bool UMelodiaWardrobeSubsystem::GrantCosmetic")
    check(bool(grant), "GrantCosmetic is defined")
    check(
        "FindGrantableRecord" in grant,
        "GrantCosmetic consults the catalog",
    )
    check(
        ordered(grant, "FindGrantableRecord", "RestoreNarrativeRecord"),
        "GrantCosmetic validates BEFORE writing the narrative record",
    )
    check(
        "OwnedCosmeticIds.Contains" in grant,
        "GrantCosmetic treats ownership as the durable idempotency guard",
    )
    check(
        ordered(grant, "OwnedCosmeticIds.Contains", "RestoreNarrativeRecord"),
        "GrantCosmetic short-circuits an already-owned grant before mutating",
    )

    # The original defect: a literal Body slot in the grant broadcast.
    check(
        "Broadcast(EMelodiaWardrobeSlot::Body" not in grant,
        "GrantCosmetic does NOT broadcast a hardcoded Body slot",
    )
    check(
        "Broadcast(Catalogued->Slot" in grant,
        "GrantCosmetic broadcasts the cosmetic's own catalog slot",
    )

    # --- Equip: same seam, same ordering -------------------------------------
    equip = function_body(sub_cpp, "bool UMelodiaWardrobeSubsystem::EquipCosmetic")
    check(bool(equip), "subsystem EquipCosmetic is defined")
    check(
        ordered(equip, "FindGrantableRecord", "RestoreNarrativeRecord"),
        "EquipCosmetic validates BEFORE writing the narrative record",
    )
    check(
        "Catalogued->Slot" in equip,
        "EquipCosmetic takes the slot from the validated record, not a Body fallback",
    )

    # --- Purchase: downstream refusal cannot consume currency ---------------
    purchase = function_body(sub_cpp, "bool UMelodiaWardrobeSubsystem::PurchaseCosmetic")
    check(bool(purchase), "subsystem PurchaseCosmetic is defined")
    check(
        "GoldenPrice <= 0" in purchase,
        "PurchaseCosmetic rejects non-positive caller prices",
    )
    check(
        ordered(purchase, "GrantCosmetic", "TryRefundGolden"),
        "PurchaseCosmetic refunds Golden when the catalog grant is refused",
    )

    # --- Catalog is resolved once and rooted ---------------------------------
    check(
        "CachedCatalog" in sub_h and "CachedCatalog" in sub_cpp,
        "catalog is cached rather than StaticLoadObject'd per query",
    )
    check(
        "UPROPERTY(Transient)" in sub_h.split("CachedCatalog")[0].rsplit("\n\n", 1)[-1],
        "cached catalog is a UPROPERTY so the DataAsset stays rooted",
    )

    # --- Component: ownership, collision, and mesh/leader-pose ordering ------
    create = function_body(comp_cpp, "USkeletalMeshComponent* UMelodiaWardrobeComponent::FindOrCreateSlotComponent")
    check(bool(create), "FindOrCreateSlotComponent is defined")
    check(
        "AddInstanceComponent" in create,
        "dynamically created garment components are registered with the owning actor",
    )
    check(
        ordered(create, "RegisterComponent", "AddInstanceComponent"),
        "component is registered before being added to the actor's instance list",
    )
    check(
        "ECollisionEnabled::NoCollision" in create,
        "garment components are created with collision disabled",
    )
    check(
        "SetGenerateOverlapEvents(false)" in create,
        "garment components do not generate overlap events",
    )
    check(
        ordered(create, "SetSkeletalMesh", "SetLeaderPoseComponent"),
        "mesh is applied BEFORE the leader-pose binding",
    )

    # --- Component: skeleton compatibility is an explicit refusal ------------
    check(
        "IsGarmentSkeletonCompatible" in comp_h,
        "component declares a skeleton compatibility gate",
    )
    compat = function_body(comp_cpp, "bool UMelodiaWardrobeComponent::IsGarmentSkeletonCompatible")
    check(bool(compat), "IsGarmentSkeletonCompatible is defined")
    check(
        "GetSkeleton()" in compat,
        "skeleton gate compares the garment and body USkeleton",
    )
    equip_garment = function_body(comp_cpp, "void UMelodiaWardrobeComponent::EquipGarment")
    check(
        "IsGarmentSkeletonCompatible" in equip_garment,
        "EquipGarment consults the skeleton gate",
    )
    check(
        ordered(equip_garment, "IsGarmentSkeletonCompatible", "FindOrCreateSlotComponent"),
        "skeleton is checked before a slot component is created",
    )

    # --- Component: save-restore refresh path --------------------------------
    check(
        "ApplyWardrobeState" in comp_h,
        "component exposes a re-appliable wardrobe state path",
    )
    begin_play = function_body(comp_cpp, "void UMelodiaWardrobeComponent::BeginPlay")
    check(
        "ApplyWardrobeState" in begin_play,
        "BeginPlay delegates to ApplyWardrobeState rather than duplicating it",
    )
    apply_state = function_body(comp_cpp, "void UMelodiaWardrobeComponent::ApplyWardrobeState")
    check(bool(apply_state), "ApplyWardrobeState is defined")
    check(
        "SetVisibility(false)" in apply_state,
        "re-applying state hides slots the restored record no longer claims",
    )
    check(
        "restore refused slot" in apply_state
        and "skeleton mismatch" in apply_state,
        "restore hides a stale presentation when a saved mesh has a skeleton mismatch",
    )
    check(
        "default slot" in apply_state
        and "stale presentation hidden" in apply_state,
        "default presentation failures also hide stale garments",
    )

    component_equip = function_body(comp_cpp, "bool UMelodiaWardrobeComponent::EquipCosmetic")
    check(bool(component_equip), "component EquipCosmetic is defined")
    check(
        ordered(component_equip, "GetCosmeticMesh", "Wardrobe->EquipCosmetic"),
        "component preflights the mesh before writing the equipped record",
    )
    check(
        ordered(component_equip, "IsGarmentSkeletonCompatible", "Wardrobe->EquipCosmetic"),
        "component preflights skeleton compatibility before writing the equipped record",
    )
    check(
        "PreviousCosmeticId" in component_equip and "Wardrobe->UnequipSlot" in component_equip,
        "component rolls the canonical slot back when presentation fails",
    )
    check(
        "IsSlotShowingMesh" in comp_h
        and "IsSlotShowingMesh" in component_equip
        and "GetSkeletalMeshAsset() == ExpectedMesh" in comp_cpp,
        "component does not mistake a stale visible mesh for a successful equip",
    )

    # --- No second save authority in the wardrobe lane -----------------------
    for name, text in (
        ("subsystem", sub_cpp),
        ("component", comp_cpp),
        ("gacha", gacha),
    ):
        check(
            "UMelodiaSaveGameSubsystem" not in text and "UMelodiaSaveGame" not in text,
            f"{name} does not reach the quarantined second save authority",
        )

    # --- Gacha reports the real equip result ---------------------------------
    try_equip = function_body(gacha, "bool TryEquipGrantedCosmetic")
    check(bool(try_equip), "TryEquipGrantedCosmetic is defined")
    check(
        "return WardrobeComp->EquipCosmetic(CosmeticId);" in try_equip,
        "gacha returns the actual equip result instead of asserting success",
    )
    check(
        "WardrobeComp->EquipCosmetic(CosmeticId);\n\t\treturn true;" not in try_equip,
        "gacha does not discard the equip result and return an unconditional true",
    )

    # --- Definition/catalog load validation ----------------------------------
    check(
        "TryGetStringField" in definition_cpp,
        "cosmetic draft validation does not throw on missing JSON fields",
    )
    check(
        'TEXT("id")' in definition_cpp
        and 'TEXT("slot")' in definition_cpp
        and 'TEXT("rarity")' in definition_cpp,
        "cosmetic draft validation accepts the rich lower-case source shape",
    )
    check(
        "StaticEnum<EMelodiaWardrobeSlot>" in definition_cpp
        and "StaticEnum<EMelodiaCosmeticRarity>" in definition_cpp,
        "cosmetic drafts map slot and rarity through reflected enums",
    )
    check(
        'TEXT("dress")' in definition_cpp,
        "cosmetic draft validation uses the explicit dress-to-Body slot alias",
    )
    check(
        'TEXT("content_pack_id")' in definition_cpp
        and "Record.ContentPackId" in definition_cpp,
        "cosmetic draft validation preserves optional content-pack identity",
    )
    check(
        "ContentPackId" in read(WARDROBE / "Public/MelodiaCosmeticTypes.h"),
        "cosmetic records expose content-pack provenance without making it save authority",
    )
    check(
        "duplicate CosmeticId" in definition_cpp
        and "mesh path does not resolve" in definition_cpp,
        "catalog PostLoad surfaces duplicate ids and stale mesh paths",
    )
    check(
        "Duplicate ids are ambiguous" in definition_cpp
        and "if (Found)" in definition_cpp
        and "return nullptr" in definition_cpp,
        "catalog lookup fails closed when duplicate ids are authored",
    )

    # --- Catalog path agreement ----------------------------------------------
    check(
        sub_cpp.count(CATALOG_ASSET_PATH) >= 1 and gacha.count(CATALOG_ASSET_PATH) >= 1,
        "subsystem and gacha agree on the catalog asset path",
    )

    report()
    return 0 if all(ok for ok, _ in _results) else 1


def report() -> None:
    passed = sum(1 for ok, _ in _results if ok)
    total = len(_results)
    for ok, label in _results:
        if not ok:
            print(f"FAIL  {label}")
    print("validated Melodia wardrobe transaction contract")
    print(f"=== {passed}/{total} passed ===")

    # Informational only. The catalog DataAsset is editor-lane content and cannot be
    # authored from here; the assertions above prove the C++ fails CLOSED without it,
    # which is the part this lane can own. Absence is reported, never a gate failure.
    catalog_note = (
        "present"
        if list(ROOT.glob("Plugins/MelodiaWardrobe/Content/Catalog/DA_MelodiaCosmeticCatalog.*"))
        else "ABSENT (editor lane: grant/equip fail closed until authored)"
    )
    print(f"catalog asset {CATALOG_ASSET_PATH}: {catalog_note}")


if __name__ == "__main__":
    raise SystemExit(main())
