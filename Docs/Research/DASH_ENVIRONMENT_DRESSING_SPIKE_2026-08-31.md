# Dash Environment Dressing Spike — 2026-08-31

**Project:** Melodia Melusina / UE5.8  
**Status:** standalone TEST page extracted from buried emerging-toolchain research; revised after UE5.8 native-authoring trench sweep  
**Parent plan:** `Docs/Research/TOOLCHAIN_CONSOLIDATION_EXECUTION_PLAN_2026-08-31.md`  
**Companion:** `Docs/Research/EMERGING_3D_TOOLCHAIN_TRENCH_SWEEP_05_2026-08-31.md`  
**Decision default:** TEST, not CORE  

---

## 1. Position in the Melodia pipeline

Dash is being evaluated as a **last-mile Unreal environment-art acceleration layer**, not as a replacement for Houdini, SpeedTree, PCG, or the world compiler.

```text
SpeedTree = authored botanical assets and wind-ready plant identity
Houdini   = procedural ecology, masks, fields, anatomy, offline simulation
UE PCG    = scalable distribution + native manual/art-directable overrides
Dash      = optional final human composition / local physical placement accelerator
```

### Revised test question

The original benchmark asked whether Dash could beat ordinary Unreal placement. That baseline is now obsolete for UE5.8.

UE5.8 PCG adds non-destructive Manual Editing, Data Overrides, editor-mode painting/spline/surface/volume tools and richer editor queries. Dash therefore has to answer a harder question:

> Can Dash make a Houdini/PCG/SpeedTree scene more authored in less time than **UE5.8 PCG Manual Editing + PCG Editor Mode + normal editor transforms**, without leaving fragile plugin-only runtime dependencies?

If the native UE5.8 artist-override path reaches equivalent quality and preserves more procedural provenance, Dash should remain optional even if it is pleasant to use.

---

## 2. External evidence anchors

Polygonflow's Dash documentation/product material describes a UE5 world-building ecosystem with content browsing, scatter, physics placement, vines/cables, blend materials, channel packing and scene-dressing utilities:

- https://docs.polygonflow.io/
- https://polygonflow.io/dash

Epic's UE5.8 PCG documentation/release notes describe the native comparator:

- PCG Manual Editing / Data Overrides / editor improvements: https://dev.epicgames.com/documentation/unreal-engine/unreal-engine-5-8-release-notes
- PCG Editor Mode: https://dev.epicgames.com/documentation/unreal-engine/pcg-editor-mode-in-unreal-engine

The comparison is therefore **Dash vs current native UE5.8 procedural art direction**, not Dash vs primitive hand placement.

---

## 3. Benchmark: P3 Filter-Flow Biome dressing

### Map

`LV_RND_P3_FilterFlow_Dash`

### Baseline inputs

- One small PCG/SpeedTree strip generated from existing biome rules.
- One Houdini semantic-field source or deterministic placeholder using canonical contract names:
  - `melodia_filter_flow_strength`
  - `melodia_filter_flow_dir_ws`
  - `melodia_wind_exposure`
  - `melodia_monolith_proximity`
  - `melodia_ecological_density`
- One fixed screenshot camera pair:
  - wide readability camera;
  - ground-level player camera.
- Identical prop/foliage source set for both comparison lanes.

---

## 4. Required three-lane comparison

### Lane A — untouched procedural baseline

Capture the generated PCG/SpeedTree scene before human overrides.

Purpose: establish what the systemic world compiler produces on its own.

### Lane B — native UE5.8 artist pass

**Strict 20-minute pass** using only:

- PCG Manual Editing;
- Data Overrides;
- PCG Editor Mode paint/spline/volume tools if already available;
- ordinary transform/selection tools where necessary.

Allowed goals:

- exclude badly composed generated instances;
- reposition/modify a small number of hero instances;
- paint or spline a local density/composition override;
- preserve the underlying procedural source wherever possible;
- create one deliberate focal corridor supporting `melodia_filter_flow_dir_ws`.

### Lane C — Dash artist pass

Duplicate the same untouched baseline and run a **strict 20-minute Dash pass**.

Allowed operations:

- prop/debris placement;
- log/rock/field-gear dressing;
- cable/vine/road-like local assemblies;
- physics drop/paint tools;
- fast composition cleanup around focal points;
- local scatter/placement only when it does not become a second systemic biome generator.

Do not spend Dash time recreating procedural rules that Houdini/PCG already own.

---

## 5. Metrics

Record separately for Lane B and Lane C:

```text
setup_minutes
hands_on_minutes
meaningful_artist_actions
assets_touched
plugin_owned_state_created
ordinary_UE_assets_created
procedural_provenance_preserved = yes/no/partial
undo_restore_quality
source_control_diff_shape
runtime_dependency = yes/no
reopen/reload_result
package_result if applicable
```

### Visual scoring

Use the exact same cameras and score 1–5 for:

- focal readability;
- apparent intentionality;
- filter-flow readability before explicit VFX;
- silhouette rhythm;
- negative-space control;
- density hierarchy;
- “hand-authored” feel;
- consistency with untouched systemic ecology.

If possible, ask a second viewer to rank blind A/B/C screenshots without knowing which tool produced each pass.

---

## 6. Pass / park / reject

### ADOPT further if

Dash should advance only if **all** are true:

- it produces a visibly stronger composition than the UE5.8 native artist pass in the same time, **or** reaches equivalent quality materially faster;
- the improvement comes from a repeated Melodia bottleneck, not a novelty feature;
- final scene content can remain ordinary UE actors/meshes/materials where possible;
- it does not require a runtime Dash dependency;
- it respects existing PCG/SpeedTree/Houdini ownership rather than replacing it;
- reload/source-control behavior is understandable;
- a second scene reproduces the gain.

### PARK if

- Dash is faster for a few operations but native PCG Manual Editing covers most of the need;
- useful tools exist, but output conversion/provenance is unclear;
- the gain is primarily UX preference rather than measurable production acceleration;
- it wins on props but adds little to ecology/field readability.

### REJECT if

- it creates fragile plugin-owned state for ordinary static dressing;
- it encourages one-off edits that cannot be reproduced, restored, or rolled back;
- it duplicates PCG/Houdini systems with less systemic control;
- source-control or migration risk exceeds the art-time saving;
- UE5.8 Manual Editing/Editor Mode matches it closely enough that another dependency is unjustified.

---

## 7. Evidence checklist

```markdown
## Result — Dash vs UE5.8 Native Artist Pass — <YYYY-MM-DD>

- Dash version/build:
- UE version/patch:
- Dash license/trial state:
- Map:
- Baseline generation time:
- Native PCG Manual Edit minutes:
- Dash hands-on minutes:
- Native operations used:
- Dash operations used:
- Native output/provenance:
- Dash output/provenance:
- Runtime dependency left by Native? yes/no
- Runtime dependency left by Dash? yes/no
- Source-control friendliness — Native:
- Source-control friendliness — Dash:
- Reload/reopen validation — Native:
- Reload/reopen validation — Dash:
- Screenshots:
  - untouched wide:
  - native wide:
  - Dash wide:
  - untouched player:
  - native player:
  - Dash player:
- Blind visual ranking if performed:
- What Dash was uniquely better at:
- What UE5.8 native was uniquely better at:
- Problems:
- Decision: ADOPT / PARK / REJECT
- Next action:
```

---

## 8. What to commit

Commit:

- the result block;
- fixed-camera screenshots/contact sheet if lightweight;
- native PCG tool/preset definitions if project-owned and source-control friendly;
- UE notes or small isolated test-map changes if repo policy permits;
- Dash export/settings notes required to reproduce the result.

Do not commit:

- Dash binaries;
- vendor/sample content;
- third-party assets without license/repo clearance;
- large generated cache/output folders;
- production-map changes from the first spike.

---

## 9. Promotion criteria

Dash graduates from TEST to OPTIONAL/ADOPT only after **two comparative Melodia wins**:

1. P3 Filter-Flow Biome: Dash beats the UE5.8 Manual Editing/Editor Mode baseline on measurable artist-hour value.
2. A second non-P3 scene — preferably Sea Above or Faraway Mother — confirms the gain is not scene-specific.

If it wins only one specialized operation, document that operation and keep Dash as a narrow utility rather than promoting the whole ecosystem.

---

## 10. Native-first principle

Before buying or institutionalizing a third-party worldbuilding layer, first ask:

> Can this bottleneck be solved by a small Melodia-specific PCG Editor Mode tool that writes the canonical semantic fields and leaves the project fully native?

Dash should survive because it is **better**, not because the project failed to test the engine it already owns.