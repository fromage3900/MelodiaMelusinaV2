# GN Builder Pipeline — P1 Cymatics Promotion Readiness Memo

**Date:** 2026-09-02  
**Author:** Hermes subagent (GN lane)  
**Scope:** Gather-and-prep only; no editor-bound steps executed.

---

## 1. Current Registry Stats

| Metric | Value |
|--------|-------|
| Registered builders (`register_builder` calls, unique tree names) | **208** |
| Builders with curated presets (`BUILDERS_PRESETS` entries) | **128** |
| Total curated presets | **395** |
| Categories in `CATEGORY_META` | **15** |
| Universal Musical Influence auto-applied | Yes (all builders) |

**Registry API** (`deploy/surreal_arch/melodia_gn/core.py`):
- `register_builder(tree_name, builder_fn, label, description, category, hidden, role)` → populates `GROUP_BUILDERS` + `GROUP_METADATA`
- `GROUP_BUILDERS[tree_name]` → callable builder fn
- `GROUP_METADATA[tree_name]` → `{label, description, category, builder, hidden, role}`
- `CATEGORY_META[cat_id]` → `{label, icon}`
- `BUILDERS_PRESETS[builder_id]` → `{label, presets, preset_labels, preset_descriptions}`

---

## 2. Incomplete Builders (<3 Presets, per Workflow §3)

Only **1 builder** is below the 3-preset minimum:

| Builder | Preset Count |
|---------|-------------|
| `MEL_brass_pipe` | **2** (TRUMPET_STOP, HUNTING_HORN) |

All other 127 preset-bearing builders have ≥3 presets.  
128 builders have zero presets in `BUILDERS_PRESETS` (preset coverage gap — out of scope for this memo).

---

## 3. CATEGORY_META — Cymatics Category Status

**Existing 15 categories:**
`primitives`, `profiles`, `math_attrs`, `structures`, `effects`, `ornament`, `filigree`, `music`, `castle`, `operations`, `mesh_tools`, `set_dressing`, `mother`, `white_current`, `god_molts`

**`cymatics` category: NOT REGISTERED.**  
No `CATEGORY_META` entry exists for cymatics. Per workflow §4, a new category should be registered when the visual direction is genuinely distinct — cymatics qualifies (audio-reactive PBR/geometry driven by frequency analysis). This is a prerequisite for P1 promotion.

---

## 4. P1 Cymatics Promotion — Remaining Steps (from `P0_TASK_LEDGER.json` `P1_closeout`)

Gate: `p1_cymatics_present` — Promote MelodiaCymaticsSubsystem from SCAFFOLDED to PRESENT per Master Index §1.

| # | Step | Status |
|---|------|--------|
| 1 | Verify PostConfigInit module loading and uplugin dependencies | Open |
| 2 | Add cymatic PBR generation as first-class pipeline step (`copernicus_cymatic_parallax.py --cook` flag) | Open |
| 3 | Add cymatic patterns to World Field Bus cross-system contract | Open |
| 4 | Cymatics P1 promotion gate (owner review) | Open |

---

## 5. Reference Notes

- **`references/builder-patterns.md`**: Confirmed registration pattern (`register_builder("MEL_...", fn, "Label", "desc", "category_id")`), preset pattern (3 presets per builder with labels + descriptions), and stage-file generation workflow.
- **`references/monolith-mapping.md`**: 13 Monolith concepts mapped to GN builders. P0 (Faraway Mother, White Current) and P1 (God That Molts) categories already exist in `CATEGORY_META`. Cymatics is not listed as a monolith category — it is a cross-cutting pipeline capability, not a single concept.

---

## 6. Summary

- Registry is healthy: 208 builders, 395 presets, 15 categories.
- Only 1 builder (`MEL_brass_pipe`) needs a 3rd preset to meet workflow §3.
- **Cymatics category is missing from `CATEGORY_META`** — must be added before P1 promotion.
- All 4 P1_closeout steps remain open; none are gather/prep — they require editor or pipeline work.