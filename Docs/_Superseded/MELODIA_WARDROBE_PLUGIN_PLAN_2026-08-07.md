# Melodia Wardrobe Plugin — Universal Outfit Collection + Fashion Gameplay

**Date:** 2026-08-07
**Status:** Step 1 in flight.
**Lane:** New `Plugins/MelodiaWardrobe/` plugin. Additive to live route. Zero touch of quarantined `MelodiaCore` runtime.
**Decisions:** 043, 044, 045 in `_DECISION_LOG.md`.

---

## 1. What this PR ships

A new `MelodiaWardrobe` plugin providing:

1. **Universal outfit slot engine** — 6 slots (Body, Hat, Gloves, Shawl, Trail, HairCharm), one `USkeletalMeshComponent` per slot, leader-posed onto the body mesh. Same-skeleton garments use `SetLeaderPoseComponent`; different-skeleton garments (out of scope this PR) would use the hair-style `SourceMeshComponent` redirect.
2. **Cosmetic registry** — `UMelodiaCosmeticDefinition` DataAsset wraps one `Cos_<X>_<Y>.json` draft. `DA_MelodiaCosmeticCatalog` is the global registry. First pass: 1 entry (`Cos_Dress_Melusina`).
3. **Wardrobe state authority** — `UMelodiaWardrobeSubsystem` (GameInstanceSubsystem) owns the owned-set, the equipped-map, save/load via `FMelodiaNarrativeRecord` v3 (additive, no schema break), and the purchase path.
4. **Gacha loop** — `UMelodiaWardrobeGachaSubsystem` (GameInstanceSubsystem). Weighted random, 1 Golden per pull, idempotent on `GrantId` via the wallet's existing dedupe. Quantum ranking is a later swap-in behind the same signature (per AGENTS.md §Quantum usage).
5. **UI** — `WBP_Wardrobe` (Owned Grid + Equip screen + Pull screen), pushed onto `UMelodiaInputContextSubsystem` like the Orrery menu.

## 2. What it does NOT ship (and why)

- **No ACFU integration.** Decision 020/029g. (Owner signalled openness to ACFU in 2026-08-07 — see §8 "Possible ACFU follow-up".)
- **No second save file.** All wardrobe state lives on `FMelodiaNarrativeRecord` v3.
- **No touch of `ABP_Melusina_Current`, `RTG_UE4Mannequin_To_Melusina`, `SK_Melusina_Skeleton`, `BP_EquipmentBase`, `UMelodiaTokenWalletSubsystem`, or the public API of `UMelodiaNarrativeSubsystem`.**
- **No "soft-gate" outfit-ability gameplay** (per foundation closeout §2.2, deferred).
- **No paid marketplace plugin** in this PR.
- **No bulk-register of the other 38 cosmetics** in this PR. Gate 10 says stop after one dress.

## 3. What is re-hosted from quarantined MelodiaCore

The slot-swap algorithm at `Plugins/MelodiaCore/Source/MelodiaCore/MelodiaOutfitComponent.cpp:16-58` (`FindOrCreateSlotComponent` + `EquipGarment`) is re-hosted into `MelodiaWardrobe/Source/Private/MelodiaWardrobeComponent.cpp` with three additions the original lacked:

- Material override application (`SetMaterial` per slot index)
- Mirror of equipped state to `UMelodiaWardrobeSubsystem` via the new subsystem
- (Type rename + namespace) `UMelodiaOutfitComponent` → `UMelodiaWardrobeComponent`

The quarantined source remains on disk untouched. The re-host is one-way; Decision 3.1 (move MelodiaCore's 65 dead headers to `_Reference/`) is still the right follow-up but out of scope here.

## 4. File layout

```
BS_GodFile/Plugins/MelodiaWardrobe/
├── MelodiaWardrobe.uplugin                (new)
├── Source/MelodiaWardrobe/
│   ├── MelodiaWardrobe.Build.cs           (depends on Core, CoreUObject, Engine,
│   │                                      UMG, Slate, SlateCore, Json,
│   │                                      JsonUtilities, MelodiaIntegration.
│   │                                      NOT MelodiaCore.)
│   ├── Public/
│   │   ├── MelodiaCosmeticTypes.h              (new; redeclares slot enum)
│   │   ├── MelodiaCosmeticDefinition.h         (new)
│   │   ├── MelodiaWardrobeComponent.h          (new; port of UMelodiaOutfitComponent)
│   │   ├── MelodiaWardrobeSubsystem.h          (new)
│   │   └── MelodiaWardrobeGachaSubsystem.h     (new)
│   └── Private/
│       ├── MelodiaCosmeticDefinition.cpp       (new)
│       ├── MelodiaWardrobeComponent.cpp        (new; algorithm port)
│       ├── MelodiaWardrobeSubsystem.cpp        (new)
│       └── MelodiaWardrobeGachaSubsystem.cpp   (new)
├── Content/
│   ├── Catalog/DA_MelodiaCosmeticCatalog.uasset  (new; 1 entry first pass)
│   ├── Cosmetics/DA_Cos_Dress_Melusina.uasset    (new; 1 of 39)
│   ├── BP/BP_MelodiaWardrobeComponent.uasset     (new; empty BP child)
│   └── UI/WBP_Wardrobe.uasset                    (new)
└── Saved/Audit/MelodiaWardrobe_smoke.json        (PIE gate evidence)
```

`.uproject` change: one line.

## 5. Save schema bump — `FMelodiaNarrativeRecord` v2 → v3

`MelodiaNarrativeTypes.h`:
- `CurrentVersion` from `2` to `3`.
- Three new SaveGame-tagged fields, all default-empty so v2 saves load cleanly:
  - `TSet<FName> OwnedCosmeticIds`
  - `TMap<EMelodiaWardrobeSlot, FName> EquippedCosmeticIds` (named `EMelodiaWardrobeSlot` not `EMelodiaOutfitSlot` to avoid UHT collision with the quarantined MelodiaCore enum of the same name)
  - `int32 LastPullUnixSeconds = 0`
- Migration: `MigrateRecord` gets one new `case 2:` branch (no-op).
- Tests: `MelodiaIntegrationTests.cpp` `FMelodiaNarrativeRecordDefaultsTest` line 115 + new test case for v2 → v3.

## 6. Live route touch (intentionally minimal)

**Exactly one change** to the live route:
- Open `BP_MelusinaJRPGCharacter` in the editor. Add a `MelodiaWardrobeComponent` instance named `Wardrobe` to the component list. No variable changes, no graph changes, no Mesh change.

Everything else in the live route is **zero change**:
- `BP_MelodiaJRPGGameMode`, `RTG_UE4Mannequin_To_Melusina`, `ABP_Melusina_Current`, `SK_Melusina_Skeleton`, `BP_EquipmentBase`, `UMelodiaTokenWalletSubsystem`: zero.
- `UMelodiaNarrativeSubsystem` API surface: zero change. Only additive v3 fields.
- `MelodiaCore` plugin: zero (still quarantined, still out of build).

Retarget risk: zero (slot components use `SetLeaderPoseComponent(bodyMesh)` because your already-imported meshes share `SK_Melusina_Skeleton`).

## 7. Execution order (binary gates, per AGENTS.md)

| # | Task | Acceptance gate |
|---|------|-----------------|
| 1 | `FMelodiaNarrativeRecord` v2 → v3 additive fields + migration + tests. | Migration + Defaults tests pass; existing PIE save still loads. |
| 2 | Create `Plugins/MelodiaWardrobe/` uplugin + Build.cs + 5 C++ files. | New module compiles 0e/0w. `run_pie_smoke` baseline unchanged. |
| 3 | One `.uproject` line enabling the new plugin. | Module loads on next PIE. |
| 4 | Add `Wardrobe` component to `BP_MelusinaJRPGCharacter`. No other edit. | `run_pie_smoke` 46/3 baseline unchanged. |
| 5 | Python one-shot: instantiate `DA_Cos_Dress_Melusina` + `DA_MelodiaCosmeticCatalog` (1 entry). | Soft pointer resolves; registry shows the entry. |
| 6 | PIE: pull (Golden → dress) + equip + save + full process restart + load + re-equip. | `OwnedIds` and `EquippedIds` survive restart; dress mesh visible on live pawn; `GoldenTokens` decremented exactly once. |
| 7 | `WBP_Wardrobe` — Owned Grid + Equip screen (no Pull screen yet). | UI shows the one dress; click equips it. |
| 8 | Add Pull screen to `WBP_Wardrobe`. | One Golden → one dress, atomic, idempotent on `GrantId`. |
| 9 | Write `Saved/Audit/MelodiaWardrobe_smoke.json`. | File exists with timestamps. |
| 10 | **Decision gate.** Stop. Owner reviews. Do not bulk-register the other 38 cosmetics in this PR. | Owner review. |

## 8. Possible ACFU follow-up (out of scope this PR)

The owner signalled openness to cherry-picking from ACFU on 2026-08-07. The compat matrix at `Docs/_Reference/MELODIA_ACFU_QUILLSCRIPT_COMPATIBILITY_MATRIX_2026-07-25.md` is the authoritative source for which ACFU pieces are safe to integrate. Per the matrix:

- **ACFU combat system** — rejected (JRPG template is the live authority).
- **ACFU inventory / quest / save / dialogue** — rejected (each duplicates a live authority).
- **ACFU's interaction system + camera utilities** — not yet evaluated. These are plausible cherry-picks if any are 5.8-verifiable, but they are not the wardrobe's blocker.
- **ACFU's ability/effect system** — interesting for "outfit passive abilities" (the soft-gate layer foundation closeout §2.2 explicitly deferred), but the soft-gate gameplay is also deferred this PR.

A follow-up decision (likely 046) would re-open the ACFU compat lab if the owner wants to experiment with ACFU pieces that don't conflict with the JRPG template. This PR does not enable ACFU and does not create a compat lab.

## 9. Decision log entries (this PR)

- **Decision 043** — Re-open wardrobe lane in additive, non-gameplay-gating form. Foundation closeout §2.2 deferral stays in place for the soft-gate gameplay axis; the collection/UI/commerce axis is opened.
- **Decision 044** — Re-host `UMelodiaOutfitComponent` algorithm into new `MelodiaWardrobe` plugin. One-way copy; quarantined source remains on disk untouched. Decision 3.1 (move MelodiaCore's 65 dead headers to `_Reference/`) is the right cleanup, separate decision.
- **Decision 045** — Marketplace plugin import closed for this PR. Reopened only by a future decision after this PR's data layer is proven.
