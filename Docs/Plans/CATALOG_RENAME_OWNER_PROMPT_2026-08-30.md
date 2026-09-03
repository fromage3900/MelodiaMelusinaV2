# Catalog Rename Owner Confirmation Prompt

**Generated:** 2026-08-30 (overnight daemon)
**Source:** `catalog_naming_harmonization_2026-08-31.json` + `catalog_*_batch_2026-08-31.json`
**Mode:** Spec only — awaiting owner confirmation before any rename script execution.

---

## Convention

**Pattern:** `Cos_<Slot>_Melusina<Descriptor>`
- PascalCase, no underscores within descriptor
- No bare `Melusina` (all items need a variant descriptor)
- Examples: `Cos_Dress_MelusinaResonantWeave`, `Cos_Gloves_MelusinaTide`

## Current Violations (5 of 26 IDs)

| Current ID | Issue | Canonical Rename (proposed) |
|---|---|---|
| `Cos_Dress_Melusina_ResonantWeave` | underscore in descriptor | `Cos_Dress_MelusinaResonantWeave` |
| `Cos_Dress_Melusina_SwiftCurrent` | underscore in descriptor | `Cos_Dress_MelusinaSwiftCurrent` |
| `Cos_Dress_Melusina_TideWalker` | underscore in descriptor | `Cos_Dress_MelusinaTideWalker` |
| `Cos_Dress_Melusina` | bare Melusina, no descriptor | `Cos_Dress_MelusinaClassic` (or owner choice) |
| `Cos_Gloves_Melusina` | bare Melusina, no descriptor | `Cos_Gloves_MelusinaClassic` (or owner choice) |

## Examples from Same Catalog (already correct)

| Current ID | Status |
|---|---|
| `Cos_Dress_MelusinaWhisper` | ✓ Correct |
| `Cos_Dress_MelusinaTide` | ✓ Correct |
| `Cos_Dress_MelusinaRadiance` | ✓ Correct |
| `Cos_Gloves_MelusinaRadiant` | ✓ Correct |
| `Cos_Gloves_MelusinaForte` | ✓ Correct |
| `Cos_Gloves_MelusinaShadows` | ✓ Correct |
| `Cos_Hat_MelusinaForte` | ✓ Correct |
| `Cos_Hat_MelusinaMaiden` | ✓ Correct |

## Owner Decision Needed

For the 2 bare-Melusina items, pick a descriptor:

**`Cos_Dress_Melusina`** — options:
- `MelusinaClassic` (default/fallback feel)
- `MelusinaTide` (matches Tide element mood)
- `MelusinaPristine` (clean/simple)

**`Cos_Gloves_Melusina`** — options:
- `MelusinaClassic`
- `MelusinaGale` (matches Gale element mood)
- `MelusinaRefined`

For the 3 underscore variants, confirm auto-rename by removing the underscore:
- `Cos_Dress_Melusina_ResonantWeave` → `Cos_Dress_MelusinaResonantWeave`
- `Cos_Dress_Melusina_SwiftCurrent` → `Cos_Dress_MelusinaSwiftCurrent`
- `Cos_Dress_Melusina_TideWalker` → `Cos_Dress_MelusinaTideWalker`

## Impact Assessment

- **Resonant form bindings:** 3 items reference `Cos_Dress_Melusina_ResonantWeave` via `ResonantFormId` in the dress batch. The underscore→PascalCase rename requires updating:
  - `DA_MelodiaCosmeticCatalog` data asset (CosmeticId field)
  - `Cos_Dress_Melusina_ResonantWeave` resonant binding entry
  - Any quest/flag references (text scan shows none)
- **String references:** `cosmetic_rename_stringref_scan_2026-08-30.json` confirmed 28 hits, 0 runtime references, all in audit/plan/doc files.
- **Safe to rename:** Text scan shows no Blueprint or C++ hard refs. All references are data asset fields.

## Proposed Next Step

Once owner confirms descriptors, generate `catalog_rename_script_2026-08-30.py` that:
1. Opens `DA_MelodiaCosmeticCatalog` via `unreal.DataTable` API
2. Renames the 5 CosmeticId entries in-place
3. Updates the 3 `ResonantFormId` binding entries
4. Outputs before/after diff for verification
5. Runs with `--dry-run` flag by default