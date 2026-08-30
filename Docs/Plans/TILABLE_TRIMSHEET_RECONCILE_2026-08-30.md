# Tilable/Trimsheet Reconciliation — 2026-08-30

**Sources:** `Saved/Audit/tilable_trimsheet_split_2026-08-30.json` + `Saved/Audit/material_catalog_consolidated_2026-08-31.json` + `Docs/Plans/PBR_ORPHAN_INSTANCE_SPEC_2026-08-30.md`
**Mode:** Offline reconciliation. No `.uasset` writes.

---

## Summary

The tilable/trimsheet split (91 tilable, 25 trimsheet, 311 unique) and the PBR orphan spec (12 complete sets) are **largely orthogonal**:

- **Tilable stems** = texture classification (can be tiled seamlessly). Most already have MIs.
- **Complete PBR sets** = texture completeness (has all PBR maps). Some lack MIs.

**Overlap count:** 8 KB3D_ATL_* textures appear in both lists.

---

## Overlap Table

| Texture | In Tilable Split | In PBR Orphan Spec | Existing MI | Action |
|---|---|---|---|---|
| KB3D_ATL_BrickStoneCleanA | ✅ Tilable | ❌ Not orphan (not in 12) | ✅ MI_BrickStoneCleanA | None |
| KB3D_ATL_BrickStoneCleanB | ✅ Tilable | ❌ Not orphan | ✅ MI_BrickStoneCleanB | None |
| KB3D_ATL_BrickStoneCleanBeigeA | ✅ Tilable | ❌ Not orphan | ✅ MI_BrickStoneCleanBeigeA | None |
| KB3D_ATL_BrickStoneCleanBlueA | ✅ Tilable | ❌ Not orphan | ✅ MI_BrickStoneCleanBlueA | None |
| KB3D_ATL_BrickStoneCleanBlueB | ✅ Tilable | ❌ Not orphan | ✅ MI_BrickStoneCleanBlueB | None |
| KB3D_ATL_BrickStoneCleanBlueC | ✅ Tilable | ❌ Not orphan | ✅ MI_BrickStoneCleanBlueC | None |
| KB3D_ATL_BrickStoneCleanRedB | ✅ Tilable | ❌ Not orphan | ✅ MI_BrickStoneCleanRedB | None |
| KB3D_ATL_BrickStoneCleanWhiteA | ✅ Tilable | ❌ Not orphan | ✅ MI_BrickStoneCleanWhiteA | None |

**Conclusion:** All 8 overlapping KB3D_ATL_* textures already have MIs. No action needed.

---

## Non-Overlapping PBR Orphan Sets (4 items)

These are in the PBR orphan spec but NOT in the tilable split:

| Set | Type | MI Proposed |
|---|---|---|
| ZenTrim_CrackedToHell | Trimsheet | MI_ZenTrim_CrackedToHell |
| basetrim | Trimsheet | MI_basetrim |
| concretetrim | Trimsheet | MI_concretetrim |
| landscape_grass | Tilable (landscape) | MI_Landscape_Grass |

**Action:** These 4 are covered by the PBR orphan spec. No additional tilable-specific work needed.

---

## Non-Overlapping Tilable Stems (83 items)

91 total tilable stems minus 8 overlaps = 83 stems that are tilable but NOT complete PBR sets.

**Sub-classification:**

| Category | Count | Action |
|---|---|---|
| KB3D_ATL_* with existing MI | ~40 | None (already covered) |
| KB3D_ATL_* without MI | ~43 | Propose MI creation (deferred — large batch) |
| PackTextures tilable | ~5 | Review individually |

**Recommendation:** The 43 KB3D_ATL_* tilable stems without MIs are candidates for batch MI creation. However, they are lower priority than the 4 PBR orphan sets (which have complete PBR maps). Defer to a future batch job after orphan MIs are created.

---

## Unified Priority List

| Priority | Task | Source | Effort |
|---|---|---|---|
| 1 | Create MI for 4 PBR orphan sets | PBR orphan spec | Low (4 items) |
| 2 | Rename 3 cosmetic IDs (Block 1) | Cosmetic rename spec | Low (string-ref scan CLEAR) |
| 3 | Fix 114 MI naming violations | MI naming spec | Medium (114 items) |
| 4 | Create MI for 43 tilable stems | Tilable split | High (batch job) |
| 5 | Quarantine 2 zentrim scratch files | Zentrim cleanup | Trivial |
| 6 | Texture swap on 2 SakuraDream MIs | Zentrim cleanup | Low |

---

## Safety Notes

- All MI creation requires editor Monolith MCP or T3D command
- Batch operations should use `--what-if` dry-run first
- Commit checkpoints before each batch
- Run `melodia_material_audit` after each batch to verify clean compile