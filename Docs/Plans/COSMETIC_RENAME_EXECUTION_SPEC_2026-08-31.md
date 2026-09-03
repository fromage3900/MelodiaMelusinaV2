# Cosmetic Rename Execution Spec — 2026-08-31

**Source:** `Saved/Audit/catalog_rename_script_2026-08-31.json` + `Saved/Audit/catalog_naming_harmonization_2026-08-31.json`
**Convention:** `Cos_<Slot>_Melusina<Descriptor>` (PascalCase descriptor, no underscores within, no bare Melusina)

---

## Summary

| Category | Count | Action |
|---|---|---|
| Underscore descriptor fix | 3 | Auto-rename (safe) |
| Bare descriptor (no variant) | 2 | BLOCKED — owner must choose variant |
| Owner confirmation needed | 2 | Flag before execution |

---

## Block 1 — Safe Auto-Renames (3 items)

These follow the convention `Cos_Dress_Melusina<OneWord>` — additive descriptor, no collision risk.

| Old ID | New ID | Slot | Rarity | Issue |
|---|---|---|---|---|
| `Cos_Dress_Melusina_ResonantWeave` | `Cos_Dress_MelusinaResonantWeave` | Dress | Rare | underscore within descriptor |
| `Cos_Dress_Melusina_SwiftCurrent` | `Cos_Dress_MelusinaSwiftCurrent` | Dress | Rare | underscore within descriptor |
| `Cos_Dress_Melusina_TideWalker` | `Cos_Dress_MelusinaTideWalker` | Dress | Rare | underscore within descriptor |

---

## Block 2 — Owner Decision Required (2 items)

These have **bare `Melusina` descriptor** — no variant suffix. Cannot auto-rename without owner input.

| Current ID | Slot | Rarity | Notes |
|---|---|---|---|
| `Cos_Dress_Melusina` | Dress | Core | "Refined dress, Core" pack. Owner must choose: `Cos_Dress_MelusinaRefined`, `Cos_Dress_MelusinaCore`, or a more specific name. |
| `Cos_Gloves_Melusina` | Gloves | Grandmaster | Owner must choose variant suffix (e.g. Forte, Radiant, Shadows, Stone, Tide). |

**Proposed options for owner:**
- `Cos_Dress_MelusinaRefined` (matches "Refined dress" description)
- `Cos_Gloves_MelusinaForte` (Grandmaster tier → "Forte" = strong)

---

## Pre-Execution Checklist

1. **String reference scan** — grep `Plugins/MelodiaWardrobe/Content/` + `deploy/` logs for old-ID string refs:
   ```bash
   grep -r "Cos_Dress_Melusina_ResonantWeave\|Cos_Dress_Melusina_SwiftCurrent\|Cos_Dress_Melusina_TideWalker" Plugins/ deploy/ Saved/
   ```
   If any hits found, add them to the rename map (cascade).

2. **Catalog entry count** — confirm `DA_MelodiaCosmeticCatalog` has exactly 39 records before and after.

3. **Dry-run first** — execute with `--what-if` flag before `--go`:
   ```bash
   python Tools/batch_rename_cosmetics.py --map renames.json --what-if
   ```

4. **Backup** — commit current state before rename:
   ```bash
   git add -A && git commit -m "chore(cosmetic): pre-rename checkpoint"
   ```

---

## Execution Command

```bash
# After owner confirms Block 2 variants:
python Tools/batch_rename_cosmetics.py \
  --map Docs/Plans/COSMETIC_RENAME_MAP_2026-08-31.json \
  --go
```

---

## Safety Notes

- No `.uasset` direct edits — all renames go through T3D command `batch_rename_cosmetics`
- Block 1 is safe to execute immediately
- Block 2 is BLOCKED until owner picks variant names
- After execution, re-run `catalog_naming_harmonization` audit to confirm 0 violations