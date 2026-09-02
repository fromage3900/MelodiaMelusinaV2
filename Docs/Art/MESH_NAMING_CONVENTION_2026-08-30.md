# Mesh Naming Convention — 2026-08-30

**Authority:** `mesh_query validate_naming_conventions` rules + `EnvSandbox/Monoliths/SeaAbove/Prototype/Reef` taxonomy (`SM_{Category}_{Variant}`). Verified 2026-08-30 against live project.

## 0. Engine prefix rules (enforced by `validate_naming_conventions`)

| Class | Prefix | Example |
|---|---|---|
| `StaticMesh` | `SM_` | `SM_ATL_Palace_TreeC` |
| `SkeletalMesh` | `SK_` | `SK_Melusina` |
| `Material` | `M_` | `M_Master_Toon_Unified` |
| `MaterialInstanceConstant` | `MI_` | `MI_SeaAbove_CoralSkin` |
| `Texture2D` | `T_` | `T_SeaAbove_Droplet_Atlas` |
| `Blueprint` | `BP_` | `BP_MelusinaJRPGCharacter` |
| `AnimSequence` | `AS_` | `AS_Melusina_Idle` |
| `AnimMontage` | `AM_` | — |
| `AnimBlueprint` | `ABP_` | `ABP_Melusina_Current` |
| `NiagaraSystem` | `NS_` | `NS_SeaAbove_UpwardDroplets_Prototype` |
| `NiagaraEmitter` | `NE_` | `NE_RibbonLeaderTemplate` |
| `SoundCue` | `SC_` | — |
| `SoundWave` | `SW_` | — |
| `WidgetBlueprint` | `WBP_` | `WBP_MelodiaQuillDialog` |

Custom rules may be passed via `custom_rules` param; defaults above are the gate.

## 1. Project folder taxonomy (Reef is the canonical example)

New content under `Content/EnvSandbox/Monoliths/<Feature>/Prototype/` follows:

```
SM_{Category}_{Variant}    e.g. SM_Coral_Brain, SM_Kelp_Tall, SM_RockChunk_L
MI_{Feature}_{Surface}    e.g. MI_SeaAbove_CoralSkin, MI_SeaAbove_WetRock
T_{Feature}_{Map}_{Channel}  e.g. T_SeaAbove_Droplet_Atlas
NS_{Feature}_{Effect}     e.g. NS_SeaAbove_UpwardDroplets_Prototype
```

Categories observed in the clean Reef ingest (commit `0fe7b877`, 23 meshes): `Clutter_`, `Coral_`, `Flora_`, `Island_`, `Kelp_`, `RockChunk_` plus landmark names `SM_DrownedOrgan`, `SM_Leviathan`.

Legacy buckets (`Content/Greybox_Kit` root, `Content/Library` root, `Content/EnvSandbox/Meshes/{Atlantis,Environment,…}`) are **not** taxonomy-clean — see §3.

## 2. Observed violations 2026-08-30 (scanner evidence)

`validate_naming_conventions` on `/Game/EnvSandbox` — 622 scanned, **150 violations (truncated at limit)**, `passed: 472`.

On `/Game/EnvSandbox/Meshes` alone — 100 scanned, **60 violations (truncated)**.

By bucket (disk counts vs registry counts differ — registry only sees mounted/indexed packages):

| Location | Disk files | Registry meshes | Violation pattern |
|---|---|---|---|
| `Content/EnvSandbox/Meshes/Atlantis` | 333 | ~333 StaticMesh | All `BldgLgPalace_A_KB3D_ATL_BldgLgPalace_A_*` missing `SM_` — e.g. `BldgLgPalace_A_KB3D_ATL_BldgLgPalace_A_TreeC` |
| `Content/EnvSandbox/Meshes/Environment/violin` | 1 | 1 | `violin` → `SM_violin` |
| `Content/EnvSandbox/Materials/Instances/Kenney/RetroFantasyKit` | 10 MIs | 10 | `water`, `tree`, `roof` … missing `MI_` |
| `Content/EnvSandbox/Materials/Instances/Environment/TEST_MI_Orphan_ZenTrimCracked` | 1 | 1 | `TEST_MI_…` already prefixed but orphan test asset — belongs in archive |
| Vendor texture packs (RetroTexturesFantasy ~100, KB3D Atlantis ~30, MelodyToken ~15, Brick/Marble/Voronoi/SDF ~20, Kenney ~8) | ~170 | — | All `Texture2D` without `T_` |

`Content/Greybox_Kit` (670 files on disk, 113 StaticMesh in registry) and `Content/Library` (364 on disk, 60+56 in registry) are duplicate-bucket pairs against `EnvSandbox/{Greybox_Kit,Library}` — consolidation is a **proposal**, not an inline bulk move tonight (see `Saved/Audit/mesh_catalog_2026-08-30.json`).

`Content/_PROJECT/` (~190 meshes) is a **red line — no writes**. Catalog-only.

## 3. Rename procedure (engine-native, reference-safe)

All renames go through `IAssetTools::RenameAssets` (Monolith `mesh_query batch_rename_assets` or `unreal.EditorAssetLibrary.rename_asset`) — automatic reference fixup + redirector creation. Never filesystem-rename referenced assets.

**Atlantis bulk (333 files) — staged, not yet executed (editor contention 2026-08-30 21:59–22:09):**

```
find:    "BldgLgPalace_A_KB3D_ATL_BldgLgPalace_A_"
replace: "SM_ATL_Palace_"
result:  "BldgLgPalace_A_KB3D_ATL_BldgLgPalace_A_TreeC" → "SM_ATL_Palace_TreeC"
```

Zero collisions verified on disk (`total 333, unique 333`). Script staged at `Content/Python/org_atlantis_rename_2026-08-30.py` — iterates `AssetRegistry.get_assets_by_path("/Game/EnvSandbox/Meshes/Atlantis")`, calls `rename_asset` per package, then `save_directory(…, unattended=true)`.

**Small renames (ready):**

| Asset | Fix |
|---|---|
| `/Game/EnvSandbox/Meshes/Environment/violin` | `add_prefix: "SM_"` |
| 10 Kenney MIs (`water`, `tree`, …) | `add_prefix: "MI_"` |
| `TEST_MI_Orphan_ZenTrimCracked` | Move to `EnvSandbox/VFX/_Archive_2026-08-30/` pattern |

**Execution guardrails:**

1. `dry_run: true` preview first (`batch_rename_assets` supports it; the Python loop logs `failed[]`).
2. `unattended: true` on `run_python` suppresses the `Unable to Check Out From Revision Control!` modal storm (gitignored `Content/EnvSandbox/*` + Git SC enabled → save-time checkout fails per asset). Batch save must be unattended; per-asset saves spawn one modal each. Observed 2026-08-30: 4:47 min wave for PBR_Auto MIs.
3. Verify after: `validate_naming_conventions` on the touched path should show violations gone; `get_asset_details` on a renamed asset should resolve at the new path; `find_references` old path should be empty or redirector.
4. Verify per batch — a silent no-op and a wrong-actor move look identical from the return value (`mesh_query manage_sublevel` trap, same family).

## 4. Folder hygiene done / pending

**Done 2026-08-30:** `EnvSandbox/VFX` cruft (9 files across `Deep/Nested/Path/Test`, `_deprecated`, `_Quarantine_2026-08-01`, `_Quarantine_2026-08-15`, `_Recovery_2026-08-01` + `_Showcase` empty dir) proven `referenced_by: []` ×9 via `project_query find_references` → consolidated into `EnvSandbox/VFX/_Archive_2026-08-30/{Deprecated,Quarantine_2026-08-01,Quarantine_2026-08-15,Recovery_2026-08-01,StressTest}` and empty source dirs removed. Registry re-scan confirms new paths.

**Pending (proposal in `Saved/Audit/mesh_catalog_2026-08-30.json`):** root `Content/Greybox_Kit` (670) vs `EnvSandbox/Greybox_Kit` (80), root `Content/Library` (364) vs `EnvSandbox/Library` (60) consolidation; vendor texture pack renames (~170 `T_` violations). These are 1000+ asset moves with redirector churn — proposal + owner sign-off, not an inline bulk move on a live editor with a concurrent PBR lane.

## 5. Red lines

- No writes under `Content/_PROJECT/` — catalog only.
- No Sakura art direction — Sakura-named VFX/materials are parked/archived, never renamed to Sakura; the Zentrim swap spec owns that path.
- No parallel material-master regenerates / live master `.uasset` rewrites.
- `Content/EnvSandbox/*` is gitignored (`.gitignore:183`) — only 33 VFX paths are force-tracked; moves there need no git commit but still need registry verification.
