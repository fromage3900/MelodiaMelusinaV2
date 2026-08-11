# Material System Review — Environment Art Platform

> Principal-TA review, 2026-06-25. Grounded in the project's own data-verified audits in `Saved/Audit/`
> (`master_review.json`, `material_graph_forensics.json`, `nikki_lane_audit.json`, `graph_hallucination_review.json`,
> `material_library_audit.json`, `material_parameter_audit.json`, `master_param_metadata.json`) plus the on-disk asset tree.
> Scope: make the **existing** architecture coherent, maintainable, production-ready.
> **No redesign. No new shader families.** Every recommendation is non-destructive and preserves current functionality.

---

## Part A — Holistic platform review (how the systems interact)

The platform is five systems sharing **assets** but almost no **contracts**. They are coupled through file/folder conventions and live UE asset references, not through any machine-readable interface.

### 1. Tightly coupled
- **Material ↔ Portfolio.** `capture_material_previews.py` scans `MASTER_DIR` + `ENV_INST_DIR`; `starter_instances.py` `MI_Show_*` drive the render material grid; `compile_render_plates` stamps Figma presentation onto material plates. The portfolio's `materials[]` section is *defined* by the material library.
- **Material ↔ PCG.** PCG scatters meshes that carry `MI_*` instances; `pcg_portfolio_standards.py` / `pcg_sakura_standards.py` assume specific material instances exist. Break a material path and PCG output silently loses its look.
- **All material scripts ↔ `material_lib.py`.** Every builder shares one helper spine (connect/param/texture/ban-list). This is genuinely good coupling — keep it.

### 2. Unintentionally isolated
- **Design System (Figma/Wix).** Lives in a *separate, un-versioned* folder (`Downloads/melodia-design-system/`) and reads hardcoded tokens — it does **not** consume `portfolio_package.json`. The presentation layer is disconnected from the data layer (see [PORTFOLIO_PIPELINE_AUDIT.md](PORTFOLIO_PIPELINE_AUDIT.md)).
- **The parameter-standard contract.** `material_parameter_audit.json` defines canonical schemas for `SDF_Core`, `SDF_MCP`, `Impressionist` — but **not** for the Universal master's 12 families. The studio's biggest shader has no parameter standard.
- **The 60+ `M_SDF_*` masters.** A large experiment library sitting in the production `Masters/` folder, not wired into PCG population or portfolio capture.
- **Impressionist.** Its own `Masters/` + `Instances/` silo, parallel to everything else.

### 3. Missing architectural contracts
- **Material → Portfolio metadata.** The portfolio schema wants `material_type`, `shader_family`, `output_maps` per material; **no producer emits them.** An instance's "family" (Nikki/Zen/Madoka/…) exists only in its folder + name, never as data.
- **Family/parameter standard** for the Universal master (see Part B §4).
- **Production-vs-experiment classification** of masters (the 3 real masters are indistinguishable, by location, from 60+ SDF experiments).
- **PCG → Material assignment contract** — which `MI_*` a scatter uses is convention, not a declared, exportable mapping.

### 4. What prevents one cohesive platform
The systems share **files, not interfaces.** There is no machine-readable manifest describing *what material families, instances, and parameters exist* that PCG and Portfolio can both consume — so Portfolio re-discovers materials by globbing folders, and the family taxonomy lives in human names rather than data. Compounding this, the **god-material design couples all families into one 685-node master**, so a "family" is a runtime toggle, not a separable unit — which directly fights the portfolio goal of *showcasing distinct material families*. Coherence will come from adding one thin contract (a material manifest), not from rebuilding shaders.

---

## Part B — Material System evaluation

### B.0 What actually exists (data-verified)

| Master | Expr count | Substrate Toon | Compiles | Role |
|---|---|---|---|---|
| `M_Master_Toon_Universal` | **~685** (663 no-comments) | ✅ | ✅ | The "god material." 14 texture slots, ~192 parameters, 12 families. |
| `M_Master_Toon_Landscape_HeightBlend` | ~241 | ✅ | ✅ | 4-layer height blend. 76 params. |
| `M_Water_Master_Grand_v6` | ~95–305* | ✅ | ✅ | Translucent water. 15 params. |
| `M_Master_Toon_Unified` (+`_Inst`) | 61 | ✅ | ✅ | **Legacy/superseded** — 3 texture slots only. |
| `M_Master_SDF_Toon`, `M_Toon_SDF` | 44 / — | ✅ | ✅ | Overlapping SDF toon masters. |
| `M_SDF_*` (~60 assets) | varies | mixed | — | Experiment library in the production `Masters/` folder. |

\* Water expr count differs between audits (95 vs 305) — the graph changed substantially between runs; re-snapshot to get a current number.

Library totals (from `material_library_audit.json`): **380 materials, 405 uassets, 18 textures.** Masters compile clean; the system is *functional*. The problems are **maintainability and coherence**, not breakage.

The four named families (**Nikki, Madoka, Itto, Celestial**) plus Gilding, ShadowDream, FlowerShadow, FairyDust, Magical are **parameter groups inside `M_Master_Toon_Universal`**, not separate masters. This is the single most important architectural fact about the system.

---

### B.1 Duplicate logic

| # | Finding | Evidence | Impact |
|---|---|---|---|
| D1 | **Nikki is authored twice** — an *inline* stack in Universal, but a *MaterialFunction chain* (`MF_NikkiDreamGrade → RimGlow → Sparkle → IridescenceSheen`) in Landscape **and** Water. | `nikki_lane_audit.json`: Universal `nikki_mf_calls: []`, `inline_nikki_expected: true`; Landscape/Water `chain_count: 4`. | Every Nikki tweak must be made in 2 places; inline copy duplicates the MF logic. **Highest-value dedup.** |
| D2 | **Parallax is inline in Universal** while the MF exists. | `graph_hallucination_review.json`: `"Universal uses inline parallax stack (no MF_ParallaxCore call)"`. | Same two-places problem as D1. |
| D3 | **`_Archive` instance tree is a full duplicate of `Environment`.** | Zen 16/16, Stylized 10/10 identical names; identical broken refs appear in both. | ~80 instances duplicated → doubled maintenance surface; archive was a *copy*, not a *move*. |
| D4 | **Redundant/legacy masters.** | `M_Master_Toon_Unified`(+`_Inst`), `M_Master_SDF_Toon`, `M_Toon_SDF`; name-dup `M_SDF_HybridStone` vs `M_HybridStone_SDF`; `*_Enhanced` pairs (`GothicArchitecture`, `OrnamentLayer`). | Multiple "unified/toon/SDF" masters with unclear canonical status. |

### B.2 Dead branches / dead nodes

| # | Finding | Evidence |
|---|---|---|
| X1 | **`DetailNormal` sampler flagged unwired ×28** in Universal. | `master_review.json` `texture_violations.unwired` lists `DetailNormal` 28×. Redundant sample nodes feeding nothing. |
| X2 | **Duplicate parameter declarations** — multiple expression nodes share one name: `bTriplanar` ×6, `bSparkleAdvanced` ×2, `bSheenUsesNormal` ×2 (Universal); `bUsePaintedLayers` ×4 (Landscape). | `material_graph_forensics.json` `duplicate_params`. Graph bloat + risk of divergent defaults across copies. |
| X3 | **Missing texture reference** `…/Texture_512x512` from the **Universal master** and ~7 instances (`MI_Universal_CrystalClear`, `IridescentShell`, `MI_Show_AudioPulse/ForestFoliage/NikkiHero`, `MI_Sakura_Bark`) **+ their `_Archive` twins**. | `material_library_audit.json` `missing_texture_refs`. The master wires valid `Texture_512x512_1` but still references the missing base. |
| X4 | **Orphan textures** — 8 `Marble_*` + `T_NASA_MilkyWay_4K` imported but unreferenced. | `material_library_audit.json` `orphan_textures`. |

> Note: `dead_material_nodes.json` reports 0 dead *function calls* — the dead-node scanner only checks MF calls + texture existence, so it does **not** catch X1/X2 (unwired samplers, duplicate param decls). That's a coverage gap, not a clean bill of health.

### B.3 Inconsistent graph patterns

- **Inline-vs-MF split (P1).** Witch/Madoka and Temporal are MF calls in *all three* masters (`witch_call: true`, `temporal_mf_call: true` everywhere) — the correct, consistent pattern. Nikki and Parallax break it by going inline in Universal. **Witch/Temporal is the model; bring Nikki/Parallax up to it.**
- **Folder hygiene (P2).** 60+ experimental `M_SDF_*` masters are co-located with the 3 production masters in `Masters/`. Nothing distinguishes "ship" from "sketch" by location.
- **Instance taxonomy drift (P3).** Instances use divergent prefixes/folders (`MI_Universal_*`, `MI_Zen_*`, `MI_Show_*`, `MI_Sakura_*`, `MI_Trimsheet_*`) with no documented mapping from prefix → family → master.

### B.4 Missing parameter standards

- **The Universal master has no canonical parameter schema.** `material_parameter_audit.json` defines schemas for `SDF_Core`, `SDF_MCP`, `Impressionist` only; it scanned `material_count: 0` for the Universal families. The 192 Universal parameters (`master_param_metadata.json`) carry per-param metadata but no **contract** (required vectors/scalars/groups per family) and no audit coverage.
- **No serialized family descriptor.** Parameter descriptions exist in-graph but aren't exported (corroborated by `UNMAPPED_DATA_POINTS.md`), so neither the portfolio nor a reviewer can see what a family's dials do.

### B.5 Shader-family inconsistencies

- Families are **toggles in one master**, not separable shaders. Consequence: every instance inherits all ~192 params + 685 nodes regardless of the look it uses — higher compile cost, higher cognitive load, and (critically for a *portfolio*) no clean way to present "the Nikki material" or "the Itto material" as a distinct artifact.
- Implementation depth is uneven: Witch/Temporal are fully MF-modular; Nikki/Parallax are inline; Itto/Celestial are parameter clusters with no lane-audit coverage at all (no `itto_lane_audit.json` / `celestial_lane_audit.json` exists — they're unverified).

---

## Part C — Opportunities to simplify (non-destructive, ranked)

Each preserves current functionality; none invents a family or redesigns the BSDF.

1. **Unify Nikki + Parallax onto their existing MaterialFunctions (D1, D2).** Replace Universal's inline Nikki/Parallax stacks with calls to the `MF_Nikki*` / `MF_ParallaxCore` functions already used by Landscape/Water. One source of truth, meaningful node reduction in the 685-node master, **zero visual change** (verify by before/after `render_preview`). Highest leverage.
2. **Collapse duplicate parameter declarations (X2).** Reduce `bTriplanar` 6→1 (and the others) to single referenced nodes. Removes divergent-default risk.
3. **Retire the `_Archive` duplicate tree (D3).** Confirm `Environment/` is canonical, then delete `_Archive/` (or convert to a real move). Halves instance maintenance surface in one step.
4. **Separate experiments from production masters (P2).** Move the 60+ `M_SDF_*` into `Materials/SDF/Masters/` (or `Masters/_Experiments/`), leaving only the 3–4 production masters in `Masters/`. Pure reorg; redirectors handle references.
5. **Fix X3 + prune X1/X4.** Repoint the missing `Texture_512x512` ref on the master + 7 instances; delete the 27 redundant `DetailNormal` samplers; remove the 9 orphan textures.
6. **Retire legacy masters (D4)** once confirmed superseded: `M_Master_Toon_Unified`(+`_Inst`), `M_Master_SDF_Toon`/`M_Toon_SDF` dedup, `*_Enhanced` consolidation.
7. **Extend the parameter-standard contract to the Universal families (B.4).** Add Universal family schemas to `material_parameter_audit.json` and add Itto/Celestial lane audits so all families have the same verification floor as Nikki/Witch. (Standardize/document; do not change the shader.)

### The one cross-cutting contract worth adding
A thin **material manifest exporter** (`material_type`, `shader_family`, parent master, parameter group, `output_maps`, preview path) — sourced from the data the audits already gather — would simultaneously: populate the portfolio `materials[]` section, give PCG a declared material map, and turn the family taxonomy into data. It is the smallest addition that makes Material, PCG, and Portfolio behave like one platform. (Producer-only; consumes existing graph data; invents nothing.)

---

## Verdict

The masters compile and the look works — this is a *coherence and maintainability* problem, not a *correctness* one. The single god-material is the root of most findings: it concentrates 685 nodes, 192 params, and 12 families, hosts the inline/MF inconsistency, and makes families un-presentable. Do **not** rebuild it. Pursue Part C 1–5 (all non-destructive, all verifiable by before/after preview + recompile) to make the existing architecture coherent and production-ready, and add the material manifest to connect the three core systems.
