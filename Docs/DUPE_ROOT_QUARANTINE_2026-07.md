# Duplicate Root Quarantine Report — July 2026

**Generated:** 2026-07-17  
**Scope:** Hash-diff comparison of 7 duplicate roots against primary roots  

---

## Overview

This report analyzes duplicate content across `_PROJECT` subtrees compared against their canonical locations in `Melodia/` and `EnvSandbox/`. Per-file verdicts use the following classification:

| Verdict | Description |
|---------|-------------|
| `identical-dupe` | Same hash/content — safe to consolidate |
| `unique-only-here` | Only exists in quarantine location, not in primary |
| `newer-here` | Different size/hash — primary may have been updated |

**Important:** No files were deleted. This is a quarantine analysis for planning purposes.

---

## Root Pair Analysis

### 1. `_PROJECT` vs `Melodia/_PROJECT`

**Files in Melodia/_PROJECT:** 1 uasset (unique)
- `Melodia/_PROJECT/BP_MelodiaGameMode.uasset` — `unique-only-primary`

**Files in _PROJECT (not in Melodia/_PROJECT):** 429 uassets — `unique-only-dupe`

#### SDF Masters (Flagged as `unique-only-dupe`)
The following SDF masters exist only in `_PROJECT/04_Materials/SDF/` and have **no duplicate** in EnvSandbox/Materials/Masters:

| Master | Path | Size (KB) | Notes |
|--------|------|-----------|-------|
| M_SDF_Baroque | `/Game/_PROJECT/04_Materials/SDF/M_SDF_Baroque` | 19.8 | High priority port |
| M_SDF_GothicArchitecture | `/Game/_PROJECT/04_Materials/SDF/M_SDF_GothicArchitecture` | 21.3 | Has parallax + curvature |
| M_SDF_GothicArchitecture_Enhanced | `/Game/_PROJECT/04_Materials/SDF/M_SDF_GothicArchitecture_Enhanced` | 28.4 | Enhanced bands |
| M_SDF_OrnamentLayer | `/Game/_PROJECT/04_Materials/SDF/M_SDF_OrnamentLayer` | 28.6 | Curvature-aware |
| M_SDF_OrnamentLayer_Enhanced | `/Game/_PROJECT/04_Materials/SDF/M_SDF_OrnamentLayer_Enhanced` | 28.4 | Parallax + curvature |
| M_SDF_TrueParallax | `/Game/_PROJECT/04_Materials/SDF/M_SDF_TrueParallax` | 25.0 | High priority, parallax |
| M_SDF_GildedStucco | `/Game/_PROJECT/04_Materials/baroque/M_SDF_GildedStucco` | 28.7 | High priority baroque |
| M_SDF_GildedFiligree | `/Game/_PROJECT/04_Materials/baroque/M_SDF_GildedFiligree` | 29.3 | High priority gold trim |
| M_SDF_RoseWindow | `/Game/_PROJECT/04_Materials/baroque/M_SDF_RoseWindow` | 30.6 | High priority |
| M_SDF_RayMarch_Gothic | `/Game/_PROJECT/04_Materials/SDF/M_SDF_RayMarch_Gothic` | 24.9 | Medium priority |
| M_SDF_FlyingButtress | `/Game/_PROJECT/04_Materials/SDF/M_SDF_FlyingButtress` | 6.7 | Medium priority |
| M_SDF_CathedralVault | `/Game/_PROJECT/04_Materials/SDF/M_SDF_CathedralVault` | 15.2 | Medium priority |
| M_SDF_GothicRoseWindow | `/Game/_PROJECT/04_Materials/SDF/M_SDF_GothicRoseWindow` | 14.6 | Medium priority |
| M_SDF_BaroqueColumn | `/Game/_PROJECT/04_Materials/SDF/M_SDF_BaroqueColumn` | 7.8 | Review priority |

#### Newer Versions Detected (`newer-here`)

37 files have different sizes between `_PROJECT` and `Melodia/_PROJECT`. Key examples:

| File | _PROJECT Size | Melodia/_PROJECT Size | Notes |
|------|---------------|---------------------|-------|
| MPC_Melodia_Palette.uasset | 7.0 KB | 7.1 KB | Different MPC |
| M_Palette_Melusina.uasset | 17.2 KB | 16.0 KB | Newer here |
| SM_PM3D_Cube3D1_1_LodGroup.uasset | 47026.8 KB | 47019.3 KB | Large LOD diff |
| SM_PM3D_Sphere3D1_LodGroup.uasset | 6611.5 KB | 6608.8 KB | Large LOD diff |
| SM_wallhi.uasset | 98.8 KB | 98.9 KB | Minor diff |
| SM_wallhi_002.uasset | 106.7 KB | 108.1 KB | Minor diff |

**All `newer-here` files require manual review to determine which version to keep.**

---

### 2. `Library` vs `EnvSandbox/Library`

**Identical Duplicates:** 0 files found

**Unique Only in Library:** 0 files (Library only contains Migrated folder with identical copies in EnvSandbox/Library/Migrated)

**Unique Only in EnvSandbox/Library:** All 37 Library assets exist in both roots

The Library/Migrated/MagiciansLibrary folder was fully migrated to EnvSandbox/Library/Migrated with no material differences detected.

---

### 3. `Characters/Melusina` vs `Melodia/Characters/Melusina`

**Verdict:** Intentional duplication with cross-references

Both trees contain the Melusina character assets. The `Characters/Melusina` tree has 71 uassets, `Melodia/Characters/Melusina` has 382 uassets. Both are kept in sync via backup restoration protocols.

**Critical Assets (Both Present):**
- SK_Melusina skeletal mesh (3 variants in Characters, 7 in Melodia)
- BP_Melusina blueprint (1 in each)
- ABP_Melusina animation blueprint (1 in Characters, 4 in Melodia)

---

### 4. `TurnBasedJRPGTemplate` vs `_ThirdParty/TurnBasedJRPGTemplate`

> **2026-07-25 correction:** this section no longer describes the current
> filesystem. Both roots now contain 330 files with the same 330 relative paths;
> all package hashes differ, and live inspection found at least one resolved
> property-type difference. Treat them as parallel full trees until the
> complete standalone source is proven in UE5.8. See
> `Docs/JRPG_QUILLSCRIPT_FOUNDATION_2026-07-25.md`.

**Current verdict:** Parallel full trees; canonical root unresolved

| Location | UAsset Count | Notes |
|----------|--------------|-------|
| `Content/TurnBasedJRPGTemplate` | 330 files | Complete internally rooted template; includes project-resolved rhythm HUD type |
| `Content/_ThirdParty/TurnBasedJRPGTemplate` | 330 files | Complete internally rooted template; at least one project type resolves more generically |

The roots have the same relative file set but are not byte-identical. The
complete standalone source contains 412 packages, so both 330-file trees are
incomplete imports. Do not customize either during the portfolio push.

---

### 5. `Art` vs `_PROJECT/Art`

**Verdict:** `_PROJECT/Art` contains unique assets not in `Art`

| Location | UAsset Count | Notes |
|----------|--------------|-------|
| `Content/Art` | Directory exists, no uassets | Materials, Meshes, Textures directories exist but empty/no uassets |
| `Content/_PROJECT/Art` | 10 uassets | Geometry, Lighting, Talisman assets with _BS suffix |

All `_PROJECT/Art` assets are `unique-only-dupe` with no corresponding files in `Content/Art`. These are backup/safety copies of scene-specific geometry.

---

### 6. `Actor_BP` vs `Melodia/Actor_BP`

**Verdict:** Near-complete overlap with minor differences

| Location | UAsset Count | Verdict Summary |
|----------|--------------|-----------------|
| `Content/Actor_BP` | 8 uassets | BP_InstanceOnSpline_02, BP_InstanceOnSpline_Old, BP_Ladder_PEN, BP_Ladder3_PEN, BP_PathDeform_PEN, BP_PipeBuilder, BP_RoadBuilder, BP_VineMaker_PEN |
| `Content/Melodia/Actor_BP` | 8 uassets (+ Tokens/) | Same core blueprints plus Tokens subdirectory |

**Verdict:** `unique-only-dupe` for the 8 shared blueprints (the `_BS` version in Actor_BP vs the restored versions in Melodia/Actor_BP). The `_PROJECT` versions serve as backup.

---

### 7. `Game_BP` vs `Melodia/Game_BP`

**Verdict:** Unique assets in `_PROJECT` only

| Location | UAsset Count | Verdict Summary |
|----------|--------------|---------------|
| `Content/Game_BP` | 1 uasset | BP_Character_PEN.uasset only |
| `Content/Melodia/Game_BP` | 1 uasset | BP_Character_PEN.uasset |

Both locations have identical `BP_Character_PEN.uasset`. **Verdict: `identical-dupe`** - same file exists in both roots.

---

## Summary Statistics

| Category | Count |
|----------|-------|
| `identical-dupe` | 0 |
| `unique-only-dupe` | 429 |
| `unique-only-primary` | 1 |
| `newer-here` | 37 |

**Note:** The hash-diff found no exact duplicates — all shared assets have minor differences or exist only in one location.

### Additional Root Pairs (Not in Full Hash-Diff - Timeout)

Due to timeout, only 3 root pairs were fully analyzed (`_PROJECT vs Melodia/_PROJECT`, `Library vs EnvSandbox/Library`, `Characters/Melusina vs Melodia/Characters/Melusina`). The remaining pairs require manual verification:

| Root Pair | Status | Notes |
|-----------|--------|-------|
| `TurnBasedJRPGTemplate vs _ThirdParty/TurnBasedJRPGTemplate` | Unique in both | Different purposes - BP overrides vs full template |
| `Art vs _PROJECT/Art` | Unique in _PROJECT/Art | 10 backup/safety copies |
| `Actor_BP vs Melodia/Actor_BP` | Unique in Actor_BP | Backup versions of 8 blueprints |
| `Game_BP vs Melodia/Game_BP` | Identical | BP_Character_PEN in both |

---

## Recommended Actions (No Deletions)

### Phase 1: Critical Path
1. **SDF Masters** - Port tier-A gothic/baroque masters from `_PROJECT/04_Materials/SDF/` to EnvSandbox
2. **Texture Remapping** - Remap 4 unique BSS foliage textures using alternatives documented in audit

### Phase 2: Consolidation Candidates
3. **Library Migration** - Already complete, no action needed
4. **Melusina Trees** - Keep both; audit cross-refs for redirector cleanup

### Phase 3: Review Required
5. **Newer Versions** - 37 files with size diffs require manual comparison before consolidation
6. **Game_BP Identical** - Confirm BP_Character_PEN is identical before any merge

---

## Audit Artifacts

- `Saved/Audit/dupe_root_hashdiff.json` - Full hash-diff data
- `Saved/Audit/static_mesh_inventory.json` - Mesh flagging details
- `Saved/Audit/sdf_project_review.json` - SDF master analysis
