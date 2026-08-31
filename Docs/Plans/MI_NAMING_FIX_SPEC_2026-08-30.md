# MI Naming Fix Spec — 2026-08-30

**Source:** `Saved/Audit/mi_naming_fix_2026-08-30.json` (114 violations catalogued)
**Convention:** `MI_<Stem>_<Rxx_TileY>` (e.g. `MI_BrickStone_Atlantis_R055_Tile4`)
**Prerequisites:** Editor Monolith MCP or T3D rename command. No `.uasset` hand-edits.

---

## Summary

| Category | Count | Action |
|---|---|---|
| `no_variant_suffix` | 99 | Rename to add Rxx_TileY suffix |
| `missing_MI_prefix` | 15 | Rename to add MI_ prefix |
| Total violations | 114 | Spec only |

---

## Issue Type 1: No Variant Suffix (99 items)

These follow the pattern `MI_<Stem>` but lack the required `_<Rxx_TileY>` suffix. The audit convention requires `MI_<Stem>_<Rxx_TileY>` for tilable/trimsheet instances, or `MI_<Stem>_<Descriptor>` for hero variants.

### Rename Pattern

| Pattern | Old Example | New Example |
|---|---|---|
| `MI_<Stem>` (single word) | `MI_BrickStoneCleanA` | `MI_BrickStone_CleanA` |
| `MI_<Stem><Variant>` (PascalCase concat) | `MI_AtlasDecalOrnamets` | `MI_AtlasDecal_Ornamets` |

### Valid Examples (from audit)

- `MI_BrickStone_Atlantis_R055_Tile4` — tilable with R/Tile suffix
- `MI_ZenTrim_CrackedToHell_R072_Tile4` — tilable trimsheet
- `MI_Cathedral_Stone` — hero variant with descriptor

### Proposed Renames (first 20)

| Original | Proposed | Issue |
|---|---|---|
| `MI_AtlasDecalOrnamets` | `MI_AtlasDecal_Ornaments` | typo fix + descriptor split |
| `MI_AtlasFlowersA` | `MI_AtlasFlowers_A` | add variant separator |
| `MI_AtlasIvy` | `MI_Atlas_Ivy` | split stem from descriptor |
| `MI_AtlasLeafA` | `MI_AtlasLeaf_A` | add variant separator |
| `MI_AtlasLeafB` | `MI_AtlasLeaf_B` | add variant separator |
| `MI_AtlasOrnaments` | `MI_Atlas_Ornaments` | split stem from descriptor |
| `MI_AtlasPaintPatternsA` | `MI_AtlasPaintPatterns_A` | add variant separator |
| `MI_AtlasTreeA` | `MI_AtlasTree_A` | add variant separator |
| `MI_BrickStoneCleanA` | `MI_BrickStone_CleanA` | split stem from descriptor |
| `MI_BrickStoneCleanB` | `MI_BrickStone_CleanB` | split stem from descriptor |
| `MI_BrickStoneCleanBeigeA` | `MI_BrickStone_CleanBeigeA` | split stem from descriptor |
| `MI_BrickStoneCleanBlueA` | `MI_BrickStone_CleanBlueA` | split stem from descriptor |
| `MI_BrickStoneCleanBlueB` | `MI_BrickStone_CleanBlueB` | split stem from descriptor |
| `MI_BrickStoneCleanBlueC` | `MI_BrickStone_CleanBlueC` | split stem from descriptor |
| `MI_BrickStoneCleanRedB` | `MI_BrickStone_CleanRedB` | split stem from descriptor |
| `MI_BrickStoneCleanTrimA` | `MI_BrickStone_CleanTrimA` | split stem from descriptor |
| `MI_BrickStoneCleanTrimB` | `MI_BrickStone_CleanTrimB` | split stem from descriptor |
| `MI_BrickStoneCleanWhiteA` | `MI_BrickStone_CleanWhiteA` | split stem from descriptor |
| `MI_BrickStoneDamagedA` | `MI_BrickStone_DamagedA` | split stem from descriptor |
| `MI_BrickStoneDamagedB` | `MI_BrickStone_DamagedB` | split stem from descriptor |

---

## Issue Type 2: Missing MI_ Prefix (15 items)

These files lack the required `MI_` prefix.

| Original | Proposed | Path |
|---|---|---|
| `M_Master_Simple_Universal_Inst` | `MI_Master_Simple_Universal_Inst` | `Instances/` |
| `M_Master_Toon_Landscape_HeightBlend_Inst` | `MI_Master_Toon_Landscape_HeightBlend_Inst` | `Instances/` |
| `M_Master_Toon_Universal_Inst` | `MI_Master_Toon_Universal_Inst` | `Instances/` |
| `M_Master_Toon_Universal_Inst1` | `MI_Master_Toon_Universal_Inst1` | `Instances/` |
| `M_Master_Toon_Universal_Inst3` | `MI_Master_Toon_Universal_Inst3` | `Instances/` |
| *(10 more in subdirectories)* | *(to be enumerated)* | |

**Note:** Some `M_Master_*` files in `Instances/` may be intentional master instances (not MIs). Owner must verify before renaming. If a file is a master instance (parent is a master material, not an MI), it should remain as-is or be moved.

---

## Pre-Execution Checklist

1. **String reference scan** — grep all rename targets across `Plugins/`, `deploy/`, `Saved/`, `Tools/`, `Docs/` to find cascade targets.
2. **Dry-run first** — execute with `--what-if` flag:
   ```bash
   python Tools/batch_rename_mis.py --map Docs/Plans/MI_NAMING_RENAME_MAP_2026-08-30.json --what-if
   ```
3. **Backup** — commit current state before rename.
4. **Verify parent refs** — ensure renamed MIs don't break parent material references.

---

## Safety Notes

- **Never hand-edit .uasset** — all renames via Monolith MCP or T3D command
- Spec only — do not execute without owner sign-off
- After execution, run `mi_health` audit to confirm 0 violations
- The 451 "violations" from strict regex includes many legitimate short-name MIs (e.g., `MI_Burlap`, `MI_Grass`). The audit's 114-count uses heuristics to exclude these.