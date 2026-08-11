# Standardization Fixes

**Date:** 2026-06-25  
**Mode:** Finalization — fix inconsistencies, not redesign  
**Principle:** Align existing graphs to the documented 5-layer mental model without extracting new material functions or families.

---

## Target layer model (all thematic families)

Every family should map to this stack inside `M_Master_Toon_Universal` (and landscape equivalent):

| Layer | Role | Universal implementation |
|-------|------|------------------------|
| **1 · Base** | Albedo/normal/ORM sample + tint | Textures, Layer A/B, hybrid ORM split |
| **2 · Detail** | Parallax, macro noise, normal adjust | `MF_ParallaxCore`, `MF_MacroDetail`, `MF_NormalAdjust` |
| **3 · Macro variation** | World-scale color/roughness variation | Macro detail MF, moss/snow/wetness (World group) |
| **4 · Masking / blend** | Style-family LERP into accumulators | Nikki MF chain, Celestial MF, Madoka/Itto inline, Magical MF |
| **5 · Output mapping** | Substrate Toon BSDF pins | BaseColor, Normal, Roughness, Metallic, Emissive → Front Material |

---

## 1. Family-by-family standardization status

### Nikki

| Aspect | Standard | Status |
|--------|----------|--------|
| Structure | MF-based sub-stack (Dream → Rim → Sparkle → Iridescence) | ✅ Reference implementation |
| Param group | `Nikki` | ✅ |
| Fast/Hero gate | `bNikkiFast` / `bNikkiHero` | ✅ |
| Landscape | Same MF chain after terrain compete | ✅ |

**No graph changes required.**

---

### Madoka

| Aspect | Standard | Status | Fix |
|--------|----------|--------|-----|
| Structure | Inline voronoi → veins → rings → emissive | ✅ Universal + Landscape | — |
| MF extraction | Planned `MF_Madoka` | ❌ Not done | **Deferred** — would be redesign |
| Param group | `Madoka` (9 params) | ✅ | — |
| Showcase exposure | Starter drives visible demo | ✅ **Applied** | See §4 |

**Landscape vs Universal ordering:** On landscape, Madoka runs **before** Nikki; on Universal, Madoka runs **after** Celestial/Nikki. Both feed the same accumulator semantics (color + emissive). **No reorder** — risk outweighs benefit; document as intentional specialist ordering.

---

### Itto

| Aspect | Standard | Status | Fix |
|--------|----------|--------|-----|
| Structure | Inline truchet → cracks → wear → roughness add | ✅ Ordering fix 2026-06-24 | — |
| Placement | After gilding (`rough_gold` pointer) | ✅ Universal | — |
| Param group | `Itto` (7 params) | ✅ | — |
| Showcase exposure | Stone + ink demos | ✅ **Applied** | See §4 |

**Landscape:** Itto height delta uses hardcoded `0.08` scale — `IttoWearDepth` reserved for future tie-in to parallax height (Phase 2).

---

### Celestial (NASA-driven variation layer)

| Aspect | Standard | Status |
|--------|----------|--------|
| Role | Variation layer after Nikki, before Madoka | ✅ |
| Implementation | `MF_SpaceParallax` MF call | ✅ |
| NASA image data | External refs for MM / optional `StarMap` only | ✅ UE graph stays procedural |
| Legacy params | Kept for MI compat, documented unwired | ✅ |

**Fix:** None to graph. Optional: point `StarMap` default to `T_NASA_StarMap_4K` in catalog when artists want photo stars — **not applied** (would change default look).

---

## 2. Structural inconsistencies (documented, not changed)

| Inconsistency | Location | Decision |
|---------------|----------|----------|
| Thematic **evaluation order** differs Universal vs Landscape | See `MATERIAL_NODE_TREE_REVIEW.md` §1–2 | **Keep** — both compile; reorder = large diff |
| Nikki uses **MF_** modules; Madoka/Itto **inline** | `setup_master_universal.py` | **Keep** — MF extraction is work-plan item, not finalization |
| **AO** not exported as separate pin | Toon BSDF | **Keep** — contact shadow MF covers portfolio needs |
| **22 SDF masters** still legacy shading on disk | `Masters/` | **Fix via** `run_toon_conversion_pending.py` (existing tool) |
| **Celestial legacy param names** | `Celestial` group | **Keep** — backward compat for archived MIs |

---

## 3. Substrate compatibility fixes (existing tooling)

| Issue | Fix | Script |
|-------|-----|--------|
| SDF masters on Default Lit / MooaToon | Batch convert to `SubstrateToonBSDF` | `convert_masters_to_substrate_toon.py` |
| Pending disk stale graphs | Save-retry pass | `run_toon_conversion_pending.py` |
| Invalid legacy `MSM_Toon` enum | Scrub to DefaultLit on converted masters | `scrub_legacy_shadingmodel.py` |
| Dead MeshBlend function path | Retarget to portfolio `MF_MeshBlend_Activator_Index_0` | `fix_meshblend_activator_refs.py` |

**No new substrate nodes added in this pass.**

---

## 4. Applied fixes (this finalization pass)

### 4.1 Starter instance param exposure

**File:** `Content/Python/starter_instances.py`

| Instance | Added params | Purpose |
|----------|--------------|---------|
| `MI_Show_FairyHearts` | `MadokaGlowAmount`, `MadokaVeinEmissive` | Makes Madoka stack visible in magic showcase |
| `MI_Show_StoneCliff` | `IttoCrackDepth`, `IttoWearAmount`, `IttoBreakupAmount` | Carved stone demo on triplanar cliff |
| `MI_Show_InkWash` | `IttoInkStrength`, `IttoCrackDepth`, `IttoBreakupAmount` | Ink-line + breakup on temporal wash |

**Apply in editor:**

```text
py Content/Python/apply_starter_instances.py
```

### 4.2 No changes made to

- Master graph topology (`setup_master_universal.py` untouched)
- PCG systems
- Material function library
- New thematic families
- NASA / Material Maker pipelines

---

## 5. Parameter naming standardization

### Canonical groups (Universal master)

| Group | Families covered |
|-------|------------------|
| `Textures` / `LayerA` / `LayerB` | Base sampling |
| `Layers` | Blend weights |
| `Parallax` | Detail / POM |
| `Nikki` | Infinity Nikki environment |
| `Celestial` | Space parallax |
| `Madoka` | Witch barrier |
| `Itto` | Mythic carved |
| `Gilding` | Gold leaf |
| `World` / `Cinematic` / `Elemental` | Macro + hero |

### Cross-family rules (already enforced in builders)

- Strength params: `*Strength`, `*Amount`, `*Intensity`
- Scales: `*Scale`, `*Depth`
- Toggles: `b*` static switches
- Toon profiles: `TP_*` instance assignment via `assign_instance_profiles.py`

### Known naming drift (accept for ship)

- `CelestialNebulaStrength` vs legacy `CelestialTwinkle` — document migration in instance presets only
- SDF family uses `BandScale` vs `SDF_BandScale` — scoped to SDF masters per `audit_material_parameters.py` CANONICAL schema

---

## 6. Output map consistency

| Master family | BaseColor | Normal | Roughness | Metallic | Emissive |
|---------------|-----------|--------|-----------|----------|----------|
| Universal | ✅ | ✅ | ✅ | ✅ | ✅ |
| Landscape | ✅ | ✅ | ✅ | ✅ | ✅ (reduced stack) |
| Water | ✅ | ✅ | ✅ | — | ✅ (caustics) |
| Impressionist | ✅ | ✅ | ✅ | — | optional |
| SDF (legacy 22) | ⚠️ | ⚠️ | ⚠️ | ⚠️ | ⚠️ until Toon conversion |

---

## 7. Remaining standardization work (post-ship tail)

Ordered by impact, using **existing** scripts only:

1. Run MeshBlend fix + Toon conversion pending (SDF lane)
2. Reparent Unified → Universal (1 instance)
3. Archive legacy `MI_Universal_*` to `_Archive/`
4. Re-run `sync_all_material_instances.py` after master rebuild
5. Optional editor pass: `organize_master_groups.py` if param UI order drifts

**Out of scope (would be redesign):**
- Extract `MF_Madoka` / `MF_Itto` / `MF_Celestial`
- Reorder landscape thematic evaluation to match Universal
- Wire NASA 4K textures into `MF_SpaceParallax` by default
- Merge `M_Master_SDF_Toon` into `M_Toon_SDF`

---

## 8. Validation after fixes

```text
py Content/Python/setup_master_universal.py --force
py Content/Python/apply_starter_instances.py
py Content/Python/setup_template_showcase.py
py Content/Python/review_portfolio_masters.py
python Content/Python/audit_material_library.py
```

Expected:
- Starters compile with Madoka/Itto demos visible at non-zero defaults
- `material_library_audit.json` dead refs trending to zero after MeshBlend + master rebuild
- Template showcase spheres reflect updated instances
