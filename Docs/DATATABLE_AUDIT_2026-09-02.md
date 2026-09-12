# DataTable Audit — Click & Import with Proper Row Types (2026-09-02)

**Project:** `C:/EnvironmentPortfolio/BS_GodFile` · **Scope:** `Content/Data/` + `Content/MelodiaIntegration/` + P0 Sea Above / Faraway Mother + `Content/Melodia/DataStuctures/`

## TL;DR

- **No broken DataTables in `Content/Data/` or `Content/MelodiaIntegration/`** — neither folder contains DataTables (zero mis-typed `Generic`/`None` row types to fix there).
- **P0 assets are DataAssets, not DataTables** — `DA_MelodiaIntegrationConfig` and `DA_MelodiaCosmeticCatalog` are `UDataAsset` (no `FTableRowBase` row type; correct by design).
- **No biome/cymatic DataTables exist** — Sea Above and Faraway Mother use Copernicus MIs / PCG / EnvSandbox assets, not DataTables. Nothing to import under those names.
- **3 DataTables already imported correctly** (`FMelodia*Row : FTableRowBase`, readback verified).
- **1 mis-typed** (`DT_Burdens` → `UserDefinedStruct` instead of native) and **4 unimported** JSONs — native `FTableRowBase` header + import script provided; editor compile + one python call finishes them.
- **Stale duplicate** at `Content/Content/Melodia/DataStuctures/` should be deleted (drift: 24 vs 31 skill rows).

---

## 1. Content/Data/ and Content/MelodiaIntegration/ — full scan

| Path | What is actually there | DataTables? | Row type issue? |
|------|------------------------|-------------|-----------------|
| `Content/Data/` | `Content/Data/Melodia/melodia_registry_seed.json` (5 enemies + skills, `DataType: MelodiaTokenType`-style seed) | **None** — `.json` seed only, no `.uasset` DataTable | No — nothing to type-check |
| `Content/MelodiaIntegration/` | 11 `DA_*` DataAssets + BPs + maps + narrative | **Zero DataTables** | No — all `UDataAsset`, not `UDataTable` |
| `Imports/Data/` | 139 JSON drafts (Charts/Cosmetics/Dialogue/EnemyVariants/RoomMods) | Not a DataTable import lane | `VALIDATION.md`: 139/139 pass |
| `Content/Melodia/DataStuctures/` | 8 JSON sources, 4 imported `.uasset`s | See §2 | See §2 |
| `Content/Content/Melodia/DataStuctures/` | Duplicate of above (3 JSONs, stale counts) | Spurious | Delete |

No `Generic`/`None` row type found in `Content/Data/` or `Content/MelodiaIntegration/` because **no `UDataTable` lives there**.

---

## 2. DataTable status (the only real DataTable folder is `Content/Melodia/DataStuctures/`)

Folder name is literally `DataStuctures` (typo, kept to avoid breaking references — scripts match it).

| DataTable | Source rows | `.uasset`? | Row struct (binary) | Verdict | Log |
|-----------|-------------|------------|----------------------|---------|-----|
| `DT_MelodySlime_Enemies` | 48 (`EnemyStats`) | ✅ 17 KB | `/Script/MelodiaCore.MelodiaSlimeEnemyRow` | **OK** — `FTableRowBase` derived | `Saved/Audit/melody_slime_datatables.json` · `created_new true, readback_ok true` |
| `DT_MelodySlime_Skills` | 31 (`SkillData`) | ✅ 13 KB | `/Script/MelodiaCore.MelodiaSlimeSkillRow` | **OK** | same log · canonical 31 rows; duplicate at `Content/Content/...` still claims 24 — delete duplicate |
| `DT_MelodySlime_RoomMods` | 21 (`RoguelikeRoomModifier`) | ✅ 14 KB | `/Script/MelodiaCore.MelodiaSlimeRoomModRow` | **OK** | same log · duplicate claims 20 — delete |
| `DT_Burdens` | 21 (`RoguelikeBurden`) | ✅ 2.2 KB | `UserDefinedStruct` | **⚠️ MIS-TYPED** — must be `FMelodiaRoguelikeBurdenRow : FTableRowBase` | `Saved/Audit/roguelike_datatables.json` — mismatch; needs `--force-reimport-burdens` |
| `DT_Blessings` | 26 (`RoguelikeBlessing`) | ❌ | `FMelodiaRoguelikeBlessingRow : FTableRowBase` (new) | **UNIMPORTED** | `roguelike_datatables.json` — `source_validated_headless` |
| `DT_Artifacts` | 4 (`RoguelikeArtifact`) | ❌ | `FMelodiaRoguelikeArtifactRow : FTableRowBase` | **UNIMPORTED** | same |
| `DT_MelodiaTokens` | 8 (`MelodiaTokenType`) | ❌ | `FMelodiaTokenTypeRow : FTableRowBase` (capitalised keys preserved) | **UNIMPORTED** | same |
| `DT_RoguelikeRooms` | 6 (`RoguelikeRoom`) | ❌ | `FMelodiaRoguelikeRoomRow : FTableRowBase` | **UNIMPORTED** | same |
| `DT_QuillPortraits` | n/a (`Content/Melodia/Data/`) | ✅ 3.4 KB | `S_QuillPortraitRow` (UDS) | OK — portrait table, not MelodiaCore lane | Not in this audit's `FTableRowBase` check |

Row-type guard: every `Details > Row Structure` must read `/Script/MelodiaCore.FMelodia*Row`. `Generic` or `None` = broken import. `DT_Burdens` currently reads `UserDefinedStruct` — wrong.

Source for the 3 good tables is defined in `Plugins/MelodiaCore/Source/MelodiaCore/MelodiaSlimeDataRows.h` — all `: public FTableRowBase` (line-matched `typedef FTableRowBase Super` in generated UHT proves it).

---

## 3. P0 Sea Above + Faraway Mother

### DataAssets (not DataTables — no row type)

| Asset | Path | Size | Status |
|-------|------|------|--------|
| `DA_MelodiaIntegrationConfig` | `Content/MelodiaIntegration/Config/DA_MelodiaIntegrationConfig.uasset` | 4.4 KB | ✅ Exists; `TravelLevelIds` contains `LV_SeaAbove_Prototype`; `QuestIds`/`NarrativeFlagIds`/`SocialStatIds`/`DialogueRewardIds`/`StockSkillRhythmIds` all present (binary verified) |
| `DA_MelodiaPersonaContent` | `Content/MelodiaIntegration/Config/DA_MelodiaPersonaContent.uasset` | 8.8 KB | ✅ Exists |
| `DA_MelodiaCosmeticCatalog` | `Plugins/MelodiaWardrobe/Content/Catalog/DA_MelodiaCosmeticCatalog.uasset` | 5.5 KB | ✅ Exists; `TArray<FMelodiaCosmeticRecord>` DataAsset. `Saved/Audit/melodia_cosmetic_catalog_create.json`: `catalog_exists_before true, mesh_preflight` 5/5 resolved, `wrong_type []`, `type_correct true`, `readback ok`. Contains `Cos_Body/Shirt/Skirt/Boots/Accessories_MelusinaV2` — decorative-only, no dangling ResonantForms. |

Both are `UDataAsset` (`UMelodiaIntegrationConfig`, `UMelodiaCosmeticCatalog`) — asking for their `FTableRowBase` row type is category error; they have none by design.

Source manifest: `specs/wardrobe/wardrobe_catalog_manifest.v1.json` (`schema melodia.wardrobe_catalog_contract.v1`, `target_count 5`, `materialization_status source_ready_editor_materialization_pending`).

### Biome / cymatic DataTables

**They do not exist.** Exhaustive `find Content -name *.json | xargs grep -l biome|cymatic|FarawayMother|CelestialSilk` proves it:

- Sea Above = `EnvSandbox/Materials/Instances/Copernicus/MI_Copernicus_SeaAbove_*` + `EnvSandbox/Monoliths/SeaAbove/Prototype/Reef/stage_manifest.json` + `Content/Melodia/SeaAbove/` brass manifests
- Faraway Mother = fabric mountain / VDM system (`faraway_mother_height_aware_placements.json`, `MI_FarawayMother_CelestialSilk_*`)
- Cymatic = PBR texture sets (`T_Cymatic_*`) + `MI_Copernicus_Cymatic*`

If a future biome table is added it must do what §4 does: add a `FTableRowBase` struct, then import.

---

## 4. Fix for the 1 mis-typed + 4 unimported tables

### New header (already in tree)

`Plugins/MelodiaCore/Source/MelodiaCore/MelodiaRoguelikeDataRows.h`

```cpp
FMelodiaRoguelikeBurdenRow   : public FTableRowBase  // DT_Burdens (replaces UDS)
FMelodiaRoguelikeBlessingRow : public FTableRowBase  // DT_Blessings
FMelodiaRoguelikeArtifactRow : public FTableRowBase  // DT_Artifacts
FMelodiaTokenTypeRow         : public FTableRowBase  // DT_MelodiaTokens (caps keys preserved)
FMelodiaRoguelikeRoomRow     : public FTableRowBase  // DT_RoguelikeRooms
```

All fields match JSON keys exactly (no renaming — importer matches on property name). `needs_review` on 4 `DT_Burdens` rows is tolerated as optional annotation, never a column.

### Import scripts

- **Slime triple (done):** `Content/Python/import_melody_slime_datatables.py` — idempotent, already produced `Saved/Audit/melody_slime_datatables.json` with 48/31/21 rows and key-matched readback.
- **Roguelike 5 (new):** `Content/Python/import_roguelike_datatables.py`

Headless verification (no editor) — validates every row's field set, types, and expected counts:

```bat
python3 Content/Python/import_roguelike_datatables.py --verify-only
# → Saved/Audit/roguelike_datatables.json  ok true, source_errors []
```

Editor materialization (single editor, after header is compiled):

```bat
# 1. Compile (close editor, Build.bat / IDE build — MelodiaRoguelikeDataRows.h must be reflected,
#    otherwise /Script/MelodiaCore.FMelodiaRoguelike*Row not found and script fails closed)

# 2a. Verify without writing (editor):
UnrealEditor-Cmd.exe BS_GodFile.uproject -run=py "Content/Python/import_roguelike_datatables.py --verify-only"

# 2b. Replace mis-typed DT_Burdens (UDS → native):
UnrealEditor-Cmd.exe BS_GodFile.uproject -run=py "Content/Python/import_roguelike_datatables.py --force-reimport-burdens"

# 2c. Create the 4 missing tables:
UnrealEditor-Cmd.exe BS_GodFile.uproject -run=py "Content/Python/import_roguelike_datatables.py"
# (or in an open editor's Output Log:  py Content/Python/import_roguelike_datatables.py)
```

Report lands at `Saved/Audit/roguelike_datatables.json` (`dest /Game/Melodia/DataStuctures`, `row_struct`, `row_count`, `keys`, `readback_ok`).

### Click-import alternative (if you prefer not to use python)

1. Ensure header is compiled (step 1 above).
2. Content Browser → `Content/Melodia/DataStuctures` → **Import** → pick the `.json`.
3. Import dialog → **Row Structure** → type `FMelodiaRoguelikeBurdenRow` (etc.) — **never `Generic` or `None`**.
4. Import → save. Re-open DataTable → verify row count equals expected (21/26/4/8/6) and `Details > Row Structure` shows `/Script/MelodiaCore.FMelodia*Row`.

---

## 5. Housekeeping

- Delete `Content/Content/` (full duplicated `Melodia/DataStuctures/` subtree, 3 JSONs, `Content/Content` is never a valid content root — Skills count drift 24 vs 31, RoomMods 20 vs 21).
- `DT_MelodiaTokens` and `DT_RoguelikeRooms` are also served by DataAsset authorities (`UMelodiaTokenCatalog`, `URoomData`). Importing them as DataTables is **optional**. The header+script make either path work; do **not** add a second competing runtime reader.

---

## 6. Files created / modified this audit

| File | Action |
|------|--------|
| `Plugins/MelodiaCore/Source/MelodiaCore/MelodiaRoguelikeDataRows.h` | **Created** — 5 `FTableRowBase` structs |
| `Content/Python/import_roguelike_datatables.py` | **Created** — editor + headless import for the 5 roguelike tables |
| `Content/Python/import_melody_slime_datatables.py` | **Existing** — verified, no change |
| `Saved/Audit/roguelike_datatables.json` | **Created** by `--verify-only` (headless, 5 tables source_validated) |
| `Saved/Audit/melody_slime_datatables.json` | **Existing** — 48/31/21 readback_ok |
| `Saved/Audit/melodia_cosmetic_catalog_create.json` | **Existing** — catalog + mesh preflight ok |
| `Saved/Audit/datatable_audit_2026-09-02.json` | **Created** — machine-readable full ledger |
| `Docs/DATATABLE_AUDIT_2026-09-02.md` | **Created** — this document |

## 7. Build required

`MelodiaRoguelikeDataRows.h` is new — closed-editor `Build.bat` (or IDE build) is required before the editor can resolve `/Script/MelodiaCore.FMelodiaRoguelike*Row`. Live Coding cannot register new reflected types.
