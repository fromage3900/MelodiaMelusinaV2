## UE 5.8 material notes (napo loop)

Append-only scratchpad for engine quirks observed during headless rebuild/audit loops.

### 2026-06-20

- **Benign warnings seen repeatedly**
  - **`LogUnrealNames: Error: String is too long`** appears during headless runs; did not prevent material compile or audits.
  - **`GameFeatureData` AssetManager rule missing** warning appears in headless runs; audits still succeed and `master_review.json` stays `clean: true`.

- **Headless safety**
  - Always pass `-DisablePlugins=Monolith` for UE 5.8 headless: Monolith crashes at `UMonolithSettings::Get()` when enabled.

### Napo tick #2 (2026-06-20)

- **Micro-task**: added `MI_Show_NikkiHero` starter (mirrors `MI_Universal_NikkiHero` params; no new textures beyond existing `SparkleMask` profile).
- **Docs**: repaired broken starter table in `MATERIAL_INTEGRATION.md` (Nikki section had split the markdown table).
- **Starter apply**: `apply_starter_instances.py` headless uses `-nullrhi` + `-DisablePlugins=Monolith` (`.uproject` enablement is not enough — Monolith still crashes Cmd startup).

### Headless Cmd rule (2026-06-20)

- **Every** `UnrealEditor-Cmd` launch from portfolio Python must include `-DisablePlugins=Monolith` alongside `-unattended` / `-nullrhi`, even if Monolith is disabled in `BS_GodFile.uproject`. Without it, headless runs crash at `UMonolithSettings::Get()` during plugin init.

### Napo tick #3 (2026-06-20)

- **Micro-task**: added `MI_Trimsheet_ParallaxPOM` (stepped POM + `ParallaxHeight` + `NormalPower` demo); `setup_trimsheet_instances.py` now supports headless launch like starters.
- **Trimsheet count**: 3 → 4 presets under `Instances/Stylized`.

### Napo tick #4 (2026-06-20)

- **Micro-task**: polished `MI_Universal_TrimsheetBlend` with `ParallaxMode`, `ParallaxSteps`, `NormalStrength` so light blend preset still demos MF_ParallaxCore controls.
- **Note**: deferred `material_lib` import required for headless trimsheet script — top-level `import unreal` breaks outside editor.

### Napo tick #5 (2026-06-20)

- **Micro-task**: starter polish — `MI_Show_StoneCliff` now sets `ParallaxHeight` (0.88) alongside stepped POM so the cliff demo exposes the full parallax height stack.

### Napo tick #6 (2026-06-20)

- **Micro-task**: `MI_Show_CherryBlossom` now enables `bSparkleAdvanced` with `SparkleThreshold/Contrast/TwinkleSpeed` — flower-shadow garden + Nikki sparkle stack demo.

### Napo tick #7 (2026-06-20)

- **Micro-task**: `MI_Trimsheet_HeavyWear` now exposes stepped POM (`ParallaxMode` 2) + `ParallaxHeight` + moss concavity for worn trim sheets.

### Napo tick #8 (2026-06-20)

- **Micro-task**: docs alignment — added **SDF environment masters (top 5)** table to `MATERIAL_INTEGRATION.md` with canonical param naming (`*Tint`, `*Scale`, `*Strength`).
- **Audit**: `master_review.json` unchanged, still `clean: true` (docs-only tick).

### Napo tick #9 (2026-06-20)

- **Micro-task**: `MI_Show_FairyHearts` — layered Nikki rim/glow (`RimWidth`, `PastelLift`, `BloomBoost`) on top of Magical/FairyDust stack for environment cohesion.

### Napo tick #10 (2026-06-20)

- **Micro-task**: `MI_Show_ForestFoliage` — subtle Nikki dream grading (`DreamSaturation`, `DreamShadowLift`, `PastelLift`) on moss/curvature stack.

### Napo tick #11 (2026-06-20)

- **Micro-task**: `MI_Show_ElementHydro` — wired Nikki iridescence/sheen shaping (`IridescencePower`, `IridescenceRoughnessAtten`, `FabricSheen`) on hydro elemental glass.

### Napo tick #12 (2026-06-20)

- **Micro-task**: `MI_Show_InkWash` — Nikki dream grading (`DreamContrast`, `DreamHighlightSoft`, `DreamHueShift`) layered on temporal ink wash.

### Napo tick #13 (2026-06-20)

- **Micro-task**: `MI_Show_ContactRimHero` — Nikki rim shaping (`RimWidth`, `RimBias`, `RimClamp`) stacked with cinematic contact rim + atmospheric fade.

### Napo tick #14 (2026-06-20)

- **Micro-task**: `MI_Show_CelestialNebula` — Nikki inner glow + advanced sparkle (`SparkleThreshold`, `bSparkleAdvanced`) on celestial/nebula stack.

### Napo tick #15 (2026-06-20)

- **Micro-task**: `MI_Show_SkinSoft` — enabled `bNikkiFast` + `DreamHueShift`/`RimClamp` to contrast soft vs `MI_Show_NikkiHero` hero path.

### Napo tick #16 (2026-06-20)

- **Micro-task**: `MI_Trimsheet_VariationCracks` — added `ParallaxHeight` + `NormalPower` to align with other trimsheet POM presets.

### Napo tick #17 (2026-06-20)

- **Micro-task**: `setup_template_showcase.py` — 11-sphere row now includes `MI_Show_NikkiHero` (re-spaced 200u apart); loop progress table added to `MATERIAL_INTEGRATION.md`.

### Napo tick #18 (2026-06-20)

- **Micro-task**: `MI_Show_Default` exposes identity `NormalStrength`/`NormalPower` as parallax-panel baseline; full validation pass (starters + trimsheets + audit).
- Monolith must stay disabled in `.uproject` OR all `UnrealEditor-Cmd` lines need `-DisablePlugins=Monolith`.

### Napo tick #19 (2026-06-20)

- **Status**: loop paused for water/landscape specialist pivot; no code changes this tick.

