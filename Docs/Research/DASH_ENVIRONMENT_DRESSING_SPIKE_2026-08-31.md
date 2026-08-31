# Dash Environment Dressing Spike — 2026-08-31

**Project:** Melodia Melusina / UE5.8  
**Status:** standalone TEST page extracted from buried emerging-toolchain research  
**Parent plan:** `Docs/Research/TOOLCHAIN_CONSOLIDATION_EXECUTION_PLAN_2026-08-31.md`  
**Decision default:** TEST, not CORE  

---

## 1. Position in the Melodia pipeline

Dash is being evaluated as a **last-mile Unreal environment-art acceleration layer**, not as a replacement for Houdini, SpeedTree, PCG, or the world compiler.

```text
SpeedTree = authored botanical assets and wind-ready plant identity
Houdini   = procedural ecology, masks, fields, anatomy, offline simulation
UE PCG    = scalable distribution and runtime/world-aware assembly
Dash      = final human composition pass, local dressing, quick physical placement
```

The test question is narrow:

> Can Dash make a Houdini/PCG/SpeedTree scene feel more authored in less time than ordinary UE editor placement, without leaving fragile plugin-only runtime dependencies?

---

## 2. External evidence anchor

Polygonflow's Dash documentation describes Dash as a UE5 world-building ecosystem with tools for content browsing, scatter, physics painting/dropping, image boards, channel packing, vines, blend materials, pivot tools, color grading and asset export: https://docs.polygonflow.io/

That feature shape supports a Melodia test around **environment dressing and composition cleanup**, not systemic world generation.

---

## 3. Benchmark: P3 Filter-Flow Biome dressing

### Map

`LV_RND_P3_FilterFlow_Dash`

### Baseline inputs

- One small PCG/SpeedTree strip generated from existing biome rules.
- One Houdini semantic-field mask or placeholder vector field:
  - `melodia_filter_flow`
  - `melodia_wind_exposure`
  - `melodia_monolith_proximity`
- One fixed screenshot camera pair:
  - wide readability camera
  - ground-level player camera

### Strict procedure

1. Create or duplicate the baseline scene.
2. Capture baseline screenshots from the fixed cameras.
3. Run a **20-minute Dash pass** only on the duplicate.
4. Allowed operations:
   - prop/debris placement
   - log/rock/field-gear dressing
   - cable/vine/road-like local assemblies
   - physics drop/paint tools
   - small composition cleanups around focal points
5. Capture after screenshots from the same cameras.
6. Compare against a 20-minute manual UE placement pass if time allows.

---

## 4. Pass / park / reject

### ADOPT further if

- The Dash pass visibly improves authored composition/readability within 20 minutes.
- Final scene content can remain ordinary UE actors/meshes/materials where possible.
- It does not require keeping Dash as a runtime dependency.
- It respects existing PCG/SpeedTree/Houdini ownership rather than overwriting it.
- It improves the exact bottleneck: final scene dressing per artist-hour.

### PARK if

- It is nice but not decisively faster than native UE placement.
- Useful tools exist, but output conversion/provenance is unclear.
- It works for props but not vegetation/ecology or P3 field readability.

### REJECT if

- It creates fragile plugin-owned state for ordinary static dressing.
- It encourages one-off edits that cannot be diffed, reproduced, or rolled back.
- It duplicates PCG/Houdini setup without the systemic control.
- It makes source control or migration risky.

---

## 5. Evidence checklist

```markdown
## Result — Dash — <YYYY-MM-DD>

- Dash version/build:
- UE version/build:
- License/trial state:
- Map:
- Baseline creation time:
- Dash hands-on minutes:
- Manual UE comparator minutes:
- Operations used:
- Output type after Dash pass:
- Runtime dependency left behind? yes/no
- Source-control friendliness:
- Screenshots:
  - baseline wide:
  - baseline player:
  - Dash wide:
  - Dash player:
- Visual improvement:
- Problems:
- Decision: ADOPT / PARK / REJECT
- Next action:
```

---

## 6. What to commit

Commit:

- this result block;
- screenshots/contact sheet if lightweight;
- UE notes or small test-map changes if owned and isolated;
- any Dash export/settings notes that make the result reproducible.

Do not commit:

- Dash binaries;
- vendor/sample content;
- Megascans/Polyhaven assets unless project license and repo policy explicitly permit;
- large cache/output folders;
- production-map changes from the first spike.

---

## 7. Promotion criteria

Dash graduates from TEST to OPTIONAL/ADOPT only after **two** Melodia-shaped wins:

1. P3 Filter-Flow Biome dressing improves authored readability in 20 minutes.
2. A second non-P3 scene, preferably Sea Above or Faraway Mother, confirms the speed gain is not scene-specific.

Until then, Dash remains a promising last-mile editor accelerator, not a pipeline pillar.
