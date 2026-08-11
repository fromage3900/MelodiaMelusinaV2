# Impressionist Painting System — BS_GodFile (UE 5.8 Substrate Toon)

Living Impressionist Engine concepts ported to **stock UE 5.8 Substrate Toon** — no MooaToon fork, no Default Lit shortcuts. One core-driven material family with instance-driven palettes and brush behavior.

**Reference spec:** `c:\Users\froma\Living_Impressionist_Engine\` (documentation-only blueprint; 260+ material vision, oil painting + temporal + SDF systems).

**Companion:** `MATERIAL_MIGRATION.md` (SDF batch), `TOON_MIGRATION_RUNBOOK.md` (Melodia conversion playbook).

---

## Non-negotiable shading path

Every impressionist **master** must use this output chain:

```
[Brush / Impasto / Palette / Wetness / Temporal graph]
        │
        ├─► BaseColor  ──┐
        ├─► Roughness  ──┼─► MaterialExpressionSubstrateToonBSDF
        ├─► Normal     ──┘         (Toon Profile: TP_Impressionist_*)
        │
        └─► WorldPositionOffset (impasto displacement)

SubstrateToonBSDF ──► Front Material   (NOT BaseColor legacy pin)
```

| Requirement | Implementation |
|-------------|----------------|
| Shading | `MaterialExpressionSubstrateToonBSDF` |
| Output | `MP_FRONT_MATERIAL` |
| Ramps | `UToonProfile` assets (`TP_Impressionist_Dry`, `_Wet`, `_Impasto`) |
| Substrate | `r.Substrate=True`, `r.Substrate.ProjectGBufferFormat=0` in `Config/DefaultEngine.ini` |
| **Rejected** | Default Lit, MooaToon custom nodes, MCP BaseColor-only wiring |

UnrealMCP **cannot** create `SubstrateToonBSDF` nodes (no Substrate expression types in MCP tool list). Phase 1 is built via **Python** `unreal.MaterialEditingLibrary` — same proven path as `setup_sdf_materials.py`.

---

## Folder layout

```
/Game/EnvSandbox/Materials/
  Impressionist/
    Masters/
      M_Master_Impressionist_Toon              ← primary (meshes, props, architecture)
      M_Master_Impressionist_Toon_Landscape    ← landscape layer coords variant
    Instances/
      MI_Impressionist_Meadow_Dry
      MI_Impressionist_Field_Wet
      MI_Impressionist_Stone_Impasto
      MI_Impressionist_Landscape_Grass
    Functions/                                 ← Phase 2: extract MF_* from master inline logic
  ToonProfiles/
    TP_Impressionist_Dry
    TP_Impressionist_Wet
    TP_Impressionist_Impasto
```

---

## Core masters

### `M_Master_Impressionist_Toon`

Primary object/façade master. World-position brush coordinates, directional strokes, impasto WPO, wetness roughness, temporal smear.

| Input group | Parameter | Default | Range | Role | LIE source |
|-------------|-----------|---------|-------|------|------------|
| **Palette** | `ColorRampLow` | dark shadow | RGB | Void / shadow paint | `ColorRampLow` (MASTER_INDEX) |
| | `ColorRampMid` | mid tone | RGB | Body color | `ColorRampMid` |
| | `ColorRampHigh` | highlight | RGB | Stroke catch-light | `ColorRampHigh` |
| **Brush** | `BrushScale` | 0.045 | 0.01–0.12 | Stroke frequency (world units) | `MF_DirectionalBlending` UV scale |
| | `StrokeStrength` | 0.55 | 0–1 | Cross-hatch visibility | `BlendStrength` (oil painting) |
| | `BrushDirection` | (1, 0.3, 0) | unit XY | World-space stroke flow | `BrushDirection` |
| **Impasto** | `ImpastoStrength` | 0.35 | 0–1 | Relief intensity | `ImpastoStrength` |
| | `ImpastoHeight` | 0.025 | 0–0.1 | WPO displacement scale | `HeightFromImpasto` scale |
| | `NormalStrength` | 1.5 | 0–3 | Normal amplification for thick paint | `NormalAmplitude` (1–3×) |
| **Surface** | `Wetness` | 0.0 | 0–1 | 0=dry matte, 1=wet glossy | Wet surface + ink gate |
| | `DryRoughness` | 0.78 | 0–1 | Toon BSDF roughness (dry) | Base roughness |
| | `WetRoughness` | 0.22 | 0–1 | Toon BSDF roughness (wet) | Audio `RoughnessVariation` analogue |
| | `InkIntensity` | 0.0 | 0–1 | Ink pooling in stroke valleys | `InkIntensity` + `PoolingStrength` proxy |
| **Animation** | `TemporalStrength` | 0.12 | 0–1 | Living paint boil amplitude | `NoiseAmplitude` (Tier 1) |
| | `WindSpeed` | 0.15 | 0–0.5 | Stroke smear rate (time) | `MF_PaintSmearing` time driver |
| | `NoiseScale` | 1.5 | 0.5–5 | World FBm frequency | `NoiseScale` (Tier 1 temporal) |
| | `SmearStrength` | 0.3 | 0–1 | Normal paint-flow smear | `SmearStrength` (Tier 2) |

**Graph logic (portable from Living Impressionist Engine):**

| LIE system | BS_GodFile equivalent | Status |
|------------|----------------------|--------|
| `MF_DirectionalBlending` | `dot(WorldXY, BrushDirection) × BrushScale` + sin/cos cross-hatch | **Implemented** |
| `MF_ImpastoEmulation` | `stroke × ImpastoStrength × ImpastoHeight → WPO`; `NormalStrength` on normal | **Implemented** |
| `MF_VolumetricInkAccumulation` | `InkIntensity × Wetness` darkens valleys toward `ColorRampLow` | **Partial** (no ink texture) |
| `MF_TemporalNoise` | `sin(dot(WorldXY, noise) × NoiseScale + Time × WindSpeed) × TemporalStrength` | **Implemented** (single-octave proxy) |
| `MF_PaintSmearing` | `SmearStrength` modulates normal via world noise | **Implemented** |
| `MF_AnimationBoil` | — | Phase 2 (needs texture UV displacement) |
| `MF_LineJitter` | — | Phase 2 (outline / decorative) |
| `MF_Pulsing Veins` / Vortex pipelines | — | Defer — use SDF batch masters |
| `MF_AudioReactiveBlend` | `M_Master_Toon_Universal` Audio group | Environment pulse + BeatPhase (portfolio) |
| SDF Gothic / Ornament / Escher | — | Separate `M_Toon_SDF` family |

---

## LIE parameter glossary (full extract)

Actionable tunables from `Living_Impressionist_Engine/` mapped to BS_GodFile impressionist masters.

### Must-add now (implemented on `M_Master_Impressionist_Toon*`)

| Parameter | LIE doc / MF | Wired to |
|-----------|--------------|----------|
| `ColorRampLow/Mid/High` | MASTER_INDEX, Phase 1 | BaseColor |
| `BrushScale`, `StrokeStrength`, `BrushDirection` | `MF_DirectionalBlending` | BaseColor stroke mask |
| `ImpastoStrength`, `ImpastoHeight`, `NormalStrength` | `MF_ImpastoEmulation` | WPO, Normal |
| `Wetness`, `DryRoughness`, `WetRoughness` | Oil painting finish | Roughness |
| `InkIntensity` | `MF_VolumetricInkAccumulation` | BaseColor valley darken |
| `TemporalStrength`, `WindSpeed`, `NoiseScale` | `MF_TemporalNoise` Tier 1 | BaseColor, Roughness |
| `SmearStrength` | `MF_PaintSmearing` Tier 2 | Normal |

### Phase 2 (impressionist masters)

| Parameter | LIE source | Notes |
|-----------|------------|-------|
| `InkColor` | `MF_VolumetricInkAccumulation` | Vector tint for pooled ink |
| `PoolingStrength` | `MF_VolumetricInkAccumulation` | Height-based accumulation (needs Z bias) |
| `SmearDirection` | `MF_PaintSmearing` | Separate from `BrushDirection` when needed |
| `BoilIntensity` | `MF_AnimationBoil` | Texture UV chaos — needs `BrushTexture` param |
| `JitterAmount` | `MF_LineJitter` | Edge vibration — pairs with post-process outline |
| `BrushTexture` | `MF_DirectionalBlending` | Optional CC0 surface overlay |
| `HeightTexture` | `MF_ImpastoEmulation` | Replace procedural stroke height |
| `ParallaxScale` | Phase 1 keepers | Substrate slab displacement upgrade |
| `Layer1/2/3Strength` | Phase 2 pipelines | Multi-texture blend (not core impressionist) |

### Defer (audio / MooaToon / SDF-only)

| Parameter | LIE source | Reason |
|-----------|------------|--------|
| `GlobalAudioReactivity`, `Bass/Mid/TrebleIntensity` | `MF_AudioReactiveBlend` + `MPC_Portfolio_Audio` | Mesh spine + outline PP |
| `BeatPhase`, `AnimationType` | `MF_AudioDrivenAnimation` | Audio MPC wiring |
| `ArchFrequency`, `OrnamentStyle`, `EscherStyle`, etc. | SDF Phase 4A–4C | `M_Toon_SDF` batch, not impressionist |
| `RotationSpeed`, `SwirlStrength`, `PulseFrequency`, `VeinStrength` | Phase 2 pipelines | Vortex/Veins masters — Melodia patterns |
| `GoldAccent`, `EmissiveIntensity`, `MetallicIntensity` | Gilded keeper | Gilded/SDF accent instances |
| `FresnelExponent`, `EdgeStrength` | Phase 1 keepers | Toon Profile ramps + future `M_PP_ToonOutline` |

### Cohesion naming (portfolio-wide)

Shared across material families per `audit_material_parameters.py`:

| Name | Families | Meaning |
|------|----------|---------|
| `ColorRampLow/Mid/High` | Impressionist, (SDF uses `*Tint`) | 3-stop palette |
| `NoiseScale` | Impressionist, SDF | Procedural variation frequency |
| `BrushScale` / `StrokeStrength` | Impressionist only | Stroke size / visibility |
| `ImpastoStrength` / `ImpastoHeight` | Impressionist only | Relief amount / WPO scale |
| `Wetness` | Impressionist only | Wet surface blend |

LIE `BlendStrength` → canonical `StrokeStrength`. LIE `NoiseAmplitude` → canonical `TemporalStrength`.

---

### `M_Master_Impressionist_Toon_Landscape`

Same Toon BSDF chain; samples `LandscapeLayerCoords` instead of raw world XY for stable terrain tiling. Flags: `bUsedWithLandscape`, `bUsedWithLandscapeGrass`. Exposes the same 17 parameters as the object master.

---

## Toon profiles

| Profile | Path | Use |
|---------|------|-----|
| `TP_Impressionist_Dry` | `/Game/EnvSandbox/Materials/ToonProfiles/TP_Impressionist_Dry` | Matte dry brush — stepped diffuse, minimal spec |
| `TP_Impressionist_Wet` | `.../TP_Impressionist_Wet` | Glossy wet layers — tighter specular band |
| `TP_Impressionist_Impasto` | `.../TP_Impressionist_Impasto` | Heavy relief — strong shadow steps + spec catch |

**Manual editor step (required for portfolio look):** Open each `TP_*` and sculpt diffuse/specular ramps in the Toon Profile editor (flat shadow steps, optional hatching). Python creates empty profiles; ramp art is editor-tuned.

---

## Showcase instances (Phase 1)

| Instance | Parent | Profile | Character |
|----------|--------|---------|-----------|
| `MI_Impressionist_Meadow_Dry` | Object master | Dry | Warm green field, low wetness, gentle wind |
| `MI_Impressionist_Field_Wet` | Object master | Wet | Blue-teal wet meadow, high wetness + temporal |
| `MI_Impressionist_Stone_Impasto` | Object master | Impasto | Cool grey stone, heavy impasto |
| `MI_Impressionist_Landscape_Grass` | Landscape master | Dry | Terrain grass tiling |

---

## Build (editor)

1. Open `BS_GodFile.uproject` in **UE 5.8** (stock Epic, Substrate enabled).
2. Confirm `Config/DefaultEngine.ini`:
   ```ini
   r.Substrate=True
   r.Substrate.ProjectGBufferFormat=0
   ```
3. **Tools → Execute Python Script** → `Content/Python/setup_impressionist_materials.py`  
   Or Output Log:
   ```
   py "G:/EnvironmentPortfolio/BS_GodFile/Content/Python/setup_impressionist_materials.py"
   ```
4. Verify each master: open graph → confirm **Substrate Toon BSDF** node → **Front Material** connected (no orphaned Base Color pin).
5. Assign `MI_Impressionist_Meadow_Dry` to a test mesh in `/Game/EnvSandbox/_Template`; orbit — strokes, impasto WPO, and wetness should read clearly.

Safe to re-run: deletes and rebuilds masters/instances; reuses existing profiles if present.

---

## Living Impressionist Engine — what it contains

`Living_Impressionist_Engine/` is a **specification package** (6 markdown docs, ~50k words), not a UE project:

| Document | Content |
|----------|---------|
| `MASTER_INDEX.md` | 260+ material ecosystem, melancholic blue palette, 10 musical sections |
| `Phase1_Keeper_Materials_Specifications.md` | 4 MooaToon keeper masters (Marble, Gilded, Facade, Halftone) |
| `Phase2_Creative_Pipelines_Specifications.md` | Vortex, Layered Depth, Pulsing Veins pipeline masters |
| `Phase3_Derivative_Materials_Specifications.md` | 13 derivative instances + Gallery master |
| `Advanced_Systems_SDF_Audio_OilPainting.md` | SDF Gothic/Ornament/Escher, audio reactivity, oil painting MFs |
| `Phase5C_Temporal_Stylization_Complete_Integration.md` | Temporal noise, paint smear, boil, jitter; 5-tier integration |

### MooaToon-specific vs portable

| MooaToon-only | Portable to Substrate Toon |
|---------------|---------------------------|
| `M_MooaToon_*` naming / custom output nodes | Parameterized palette + stroke logic |
| MooaToon cel / hull outline | Substrate Toon BSDF + `TP_*` + future `M_PP_ToonOutline` |
| Material layer stacks (`ML_*`) | Single master + instances (user requirement) |
| Audio-reactive MPC wiring | Optional MPC later; not Phase 1 |
| Raymarched SDF custom HLSL | Existing BS_GodFile SDF batch (`M_Toon_SDF`, batch-2 masters) |
| 260 separate masters | **2 impressionist masters** + SDF family + instances |

---

## Melodia cross-reference

Melodia (`G:\Melodia\Content`) holds **517** material-like assets on MooaToon UE 5.7. Impressionist-adjacent content:

| Melodia pattern | Count / location | BS_GodFile status |
|-----------------|------------------|-------------------|
| `M_OilPainting_*` | Referenced in PCG catalog (`M_OilPainting_Gold_Baroque`) | Rebuilt as impressionist instances + `MI_Toon_SDF_Accent` |
| `M_MooaToon_*` / `M_Universal_Enhanced_*` | ~49 stylized masters | Not copied — re-authored on Substrate Toon |
| `M_Adv*` environment masters | 145 environment masters | Palette/stroke patterns inform instance tuning |
| SDF architectural | 44 SDF masters | Batch 1–2 migrated separately |
| Material layers `ML_*` | 26 layers | **Skipped** — core-driven instances instead |

No Melodia assets are required for Phase 1; instances are authored fresh on Substrate Toon.

---

## Phase 2+ batch plan

| Batch | Work | Tooling |
|-------|------|---------|
| **1 (this doc)** | 2 Toon masters + 3 TP + 4 MI + 17 params | `setup_impressionist_materials.py` |
| **2** | Extract `MF_Impressionist_BrushStroke`, `MF_Impressionist_Impasto`, `MF_Impressionist_Temporal` from inline graph | Editor or Python MF factory |
| **3** | Tune `TP_*` ramps (dry/wet/impasto stepped shading) | Manual editor |
| **4** | Full ink pooling (`InkColor`, `PoolingStrength`, ink textures) | Python graph extension |
| **5** | Composite impressionist + SDF relief (façade = SDF trim + impressionist base) | Instance layering or material blend |
| **6** | Landscape layer blend (multi-palette terrain) | Extend landscape master |
| **7** | Post-process outline `M_PP_ToonOutline` | Matches portfolio toon read |

---

## Manual editor follow-up

1. **Toon Profile ramps** — open `TP_Impressionist_*`; set diffuse/specular steps for impasto vs wet read.
2. **Verify BSDF pins** — if Roughness/Normal did not auto-connect (pin name varies by 5.8 build), wire manually to Toon BSDF.
3. **Substrate displacement slab** — optional upgrade: stack `SubstrateSlabBSDF` with height for true meso-displacement (Phase 2); current Phase 1 uses WPO impasto.
4. **Texture brushes** — wire CC0 surfaces from `/Game/.../Surfaces_CC0/` as optional `BrushTexture` param (Phase 2).
5. **Assign to template** — `_Template` hero mesh + landscape test tile.

---

## MCP limitation summary

| Capability | UnrealMCP | Python (`setup_impressionist_materials.py`) |
|------------|-----------|---------------------------------------------|
| Create empty material | Yes | Yes |
| Add SubstrateToonBSDF | **No** | **Yes** (`MaterialExpressionSubstrateToonBSDF`) |
| Wire Front Material | Partial (legacy property names) | Yes (`MP_FRONT_MATERIAL`) |
| Create ToonProfile | No | Yes (`ToonProfileFactory`) |
| Create material instances | Yes | Yes |

**Do not** use MCP `connect_to_material_output(..., "BaseColor")` for impressionist masters — that bypasses Substrate Toon.

---

*Last updated: 2026-06-19 — added NoiseScale, SmearStrength, InkIntensity, NormalStrength from LIE review*
