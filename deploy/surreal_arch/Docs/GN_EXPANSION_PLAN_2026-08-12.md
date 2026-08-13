# Melodia GN expansion plan — 2026-08-12

**Supersedes:** [OVERNIGHT_EXPANSION_2026-08-12.md](OVERNIGHT_EXPANSION_2026-08-12.md) (counts in that file are stale).  
**Audit:** [`Saved/Audit/gn_library_audit_2026-08-12.md`](../../../Saved/Audit/gn_library_audit_2026-08-12.md)  
**Cockpit:** [`Docs/BLENDER_MELODIA_COCKPIT.md`](../../../Docs/BLENDER_MELODIA_COCKPIT.md)

**Tonight cine/UE board:** [`Docs/Handoffs/TONIGHT_PORTFOLIO_STUDIO_PREP_2026-08-12.md`](../../../Docs/Handoffs/TONIGHT_PORTFOLIO_STUDIO_PREP_2026-08-12.md) (hero props, 4 P0 levels, water-hair cache). Not GN volume.

**Thesis: stop adding volume. Quality and thin-kit depth next.**  
Live registry is **165/165 construct**, **12/12 GN Stack sections**. That already exceeds the overnight 134-source / 119-live target. `geometry_extras` and the extras modules are imported. `mel_gn.apply_preset` is wired.

---

## What the overnight note got wrong

| Claim (overnight) | Reality (this evening) |
|-------------------|------------------------|
| Live registry 119 | **165** |
| `geometry_extras` not imported | Imported in `__init__.py` (15 builders live) |
| Preset apply unwired | `MEL_GN_OT_apply_preset` / `mel_gn.apply_preset` exists |
| Preset coverage 14.3% of 119 | **10.3% of 165** (17 builders, 52 looks) — extras landed without presets |
| Next step: wire extras | **Done.** Do not re-do it |

---

## Stabilize (next Blender open)

1. Open v22 in **5.2**. Do not click Sync & Reload on leftover crashed-session code.  
2. **N → BlenderMCP → Connect** (9876) if an agent needs the GUI.  
3. Studio Health: `sections=12/12 section_trees=165`.  
4. Confirm Circular Array still adds a NODES modifier (stack property patch is in AppData).

No stage save without `MELODIA_ALLOW_STAGE_SAVE=1`.

---

## P0 — Quality (1–2 sessions, mostly no editor)

Data work in `presets.py`, `aaa_quality.py`, `core.py` STUDIO_LABELS. Blender only to smoke-apply.

1. **Presets for remaining high then medium** (from `BUILDER_PRIORITY`):
   - High missing: `MEL_effect_magic`, `MEL_music_harmonic`
   - Medium missing: `MEL_music_treble_clef`, `MEL_filigree_spiral`, `MEL_escher_belvedere`, `MEL_escher_penrose_stairs`, `MEL_castle_assembler`
   - 2–3 looks each; socket names must match group inputs (spaces, e.g. `"Wall Thick"`).
2. **Fix `naming_convention_audit`:** require `MEL_` + snake_case only. Do **not** rename `MEL_arch` / `MEL_column` / friends.
3. **STUDIO_LABELS** for cockpit smoke: Castle Kit, Musical Notation, Ornament, Magic Effects (at least one labeled tree each that is not already covered).
4. Export `audit_presets()` JSON to `Saved/Audit/gn_presets_audit_<stamp>.json`.

Target after P0: high-priority 6/6 have presets; medium gaps closed; naming audit reports 0 false positives.

---

## P1 — Product shape

Deepen **thin kits** before any new Set Dressing clone (already 39 / 24%).

| Kit | Live now | Intent |
|-----|---------:|--------|
| Filigree and Crests | 4 | 2–4 more *if* a sellable crest/volute SKU is chosen; otherwise labels + presets on the four that exist. `FILIGREE_*` monolith rewrites stay deferred. |
| Operations | 3 | 1–2 compose helpers (iterate/bounded already exist); do not grow a parallel math category. |
| Ornament | 9 | Presets on vine / radial / frame before new generators. |
| Primitives / Mesh Tools / Math | 14 / 12 / 9 | Presets optional; these are tools, not SKUs. |

Wire remaining high-value presets into the **existing** apply UI. Do not add a second preset system.

---

## P2 — Automation

1. Fingerprint bake via `melodia_gn/bake.py`. Start with the **12 trees that have 51+ nodes** (Penrose, Nikki, Observatory, Escher set, siege tower, water gerstner/ripples, …), not all 165.  
2. Commit a hash baseline under `Saved/Audit/`.  
3. Change `aaq_quality_checklist` to read measured fields (construct, preset yes/no, STUDIO_LABELS yes/no, node count) instead of all-OPEN.

---

## P3 — Pack

AAA builder pack v1 / store screenshots only after P0 presets on heroes and a fingerprint on the heavy trees. `store_live` stays **false** until sell ZIP + screenshots ([MONETIZATION_GEOMETRY_FIX_EXPORT](../../../Docs/MONETIZATION_GEOMETRY_FIX_EXPORT_2026-07-12.md)).

---

## Explicit non-goals

- New `water_them_*` / `music_them_*` factories  
- Unreal / rhythm / Quill lanes  
- Stage saves from agents  
- Sync & Reload as a daily ritual (fresh 5.2 start loads AppData)  
- Mass-rename of `MEL_*` ids  
- Treating construct-pass as mesh-quality-pass  

---

## P0 landed (closed-editor) — 2026-08-12

Data-only. No Blender, no stage save. Smoke-apply in 5.2 still required (Stabilize).

- **`presets.py`:** 7 builders, 3 looks each (21). High: `MEL_effect_magic` (LIQUID / CRYSTAL / GRAVITY_WELL), `MEL_music_harmonic` (SOLO_FUNDAMENTAL / CHOIR_STACK / PHRASE_SWELL). Medium: `MEL_music_treble_clef`, `MEL_filigree_spiral`, `MEL_escher_belvedere`, `MEL_escher_penrose_stairs`, `MEL_castle_assembler` (scalars only; no Walls/Towers/Keep/Gatehouse). Library now 24 builders / 73 looks.
- **`naming_convention_audit`:** `MEL_` + snake_case rest. No category-segment / two-underscore requirement. Short ids (`MEL_arch`, `MEL_column`, …) are valid. No builder renames.
- **`STUDIO_LABELS`:** added `EFFECT_MAGIC`, `EFFECT_WAVE`, `FILIGREE_SPIRAL` (Magic Effects smoke gap; filigree unlabeled). Castle / Music / Ornament were already labeled.
- **Audit JSON:** [`Saved/Audit/gn_presets_audit_2026-08-12.json`](../../../Saved/Audit/gn_presets_audit_2026-08-12.json)

---

## Suggested session order

```text
1. Restart 5.2 (UX patches + P0 presets/labels from AppData)
2. Smoke-apply the 7 P0 builders (mel_gn.apply_preset)
3. Tonight board: hero props + water-hair Layer C bake (see TONIGHT_PORTFOLIO_STUDIO_PREP)
4. Filigree/Operations depth only if a SKU is named
5. Fingerprint the 12 heavy trees
```

---

## Water-hair cache for UE (not a GN builder)

Hair **look** is already water: Blender `Water (Advance).001` / UE `SK_MelusinaHair` + `MI_Melusina_WaterHair`. Flip Fluids is **not** the gameplay hair mesh.

| Layer | Ship in | Method |
|-------|---------|--------|
| A Look | Always | Skeletal hair + water/toon MI |
| B Drip | Gameplay | Niagara `Melusina_WaterFX` (existing specs) |
| C Cine cache | Sequencer / plates | Flip Fluids bake → Alembic `fluid_surface` → Geometry Cache |

Cache path `KitbashExport/flip_cache_melusina_waterhair/` is **empty of `.bobj`** (2026-08-12). Rebake on **v22** after `tune_melusina_hair_drip.py`. Do not conflate with Water V10 Niagara Fluids. Full procedure: tonight board.
