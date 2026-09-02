# Niagara + Flipbook Material System Plan — 2026-08-28

**Method:** live audit against the running editor (Monolith on 9316), plus offline atlas
decoding. Every count below is measured, not estimated. Where I could not verify something,
it says so.

**Supersedes:** the flipbook sections of `Docs/Handoffs/VFX_NIAGARA_FINALIZATION_2026-08-14.md`
only. That document's promotion pipeline and petal-loop work remain authoritative.

---

## 1. Measured inventory

| Scope | Count |
|---|---|
| `NiagaraSystem` assets under `/Game` | 130 |
| Project-authored (EnvSandbox 67 + Melodia 16 + Effects 3) | 86 |
| Third-party (UltraDynamicSky 21, `_ThirdParty` 21, ArtOfShader 2) | 44 |
| Systems with a **sprite renderer** | **64** (EnvSandbox 49, Melodia 15) |
| Emitters using the flipbook material `MI_Niagara_MelodiaFlipbook_Water` | **1** |

That last row is the headline. The flipbook system exists, compiles, and is wired into exactly
one emitter — `NS_Melusina_Globules` / `GlobuleA`. It is infrastructure that never shipped.

### 1.1 The 49 EnvSandbox sprite systems, by folder

| Folder | Count | Status |
|---|---|---|
| `VFX/Systems/{Universal,Sakura,Magical,Ambient}` | 20 | live |
| `VFX/Candidates/**` | 19 | staging — see §1.2 |
| `Water/v10/**` | 5 | live |
| `VFX/_Recovery_2026-08-01/**` | 3 | rollback snapshots |
| `Monoliths/SeaAbove/Prototype/VFX` | 1 | live (prototype) |
| `VFX/Systems/NS_MagicTrail` | 1 | **duplicate — see §1.3** |

Melodia's 15 are all in one flat `/Game/Melodia/VFX/` folder with no duplicates or staging
copies. That half of the project is clean and is not part of this plan's cleanup.

### 1.2 `Candidates/` is a live pipeline, not dead weight

`VFX_NIAGARA_FINALIZATION_2026-08-14.md` documents candidates being "promoted to their live"
versions. So these are staging, not rot. But promotion leaves the candidate behind, and nothing
sweeps it. Splitting the 19 by whether a live twin already exists:

**Redundant — promoted, twin is live (9):**
`NS_Uni_PollenSparkle_Candidate`, `NS_Uni_LeafDrift_Candidate`, `NS_Uni_Fireflies_Candidate`,
`NS_Uni_DustShafts_Candidate`, `NS_Melodia_LeafPileLoop_Candidate`,
`NS_SakuraDreamSparkle_AdvancedCandidate`, `NS_SakuraLanternMotes_AdvancedCandidate`,
`NS_ConstellationTwinkle_AdvancedCandidate`, `NS_ConstellationDraw_AdvancedCandidate`

**Genuinely pending — no live twin (10):**
the six `NS_SDF_*_Candidate` (the 08-09 doc calls the SDF family "prototypes, not yet"
promoted), `NS_Melodia_LaneHit`, `NS_Melodia_BattleBackdropPulse`,
`NS_SakuraPetals_v3_Candidate`, `NS_SakuraPondShimmer_AdvancedCandidate`

Only the first group is safe to retire, and only after confirming the live twin is the one
actually referenced by levels.

### 1.3 Duplicate short names — this is why `bp_sweep` fails

`NS_MagicTrail` exists twice, both outside staging, with **different content**:

| Path | Emitters | Sim |
|---|---|---|
| `VFX/Systems/NS_MagicTrail` | 2 | CPU |
| `VFX/Systems/Magical/NS_MagicTrail` | 2 | GPU |

`NS_Uni_PollenSparkle` and `NS_Uni_DustShafts` are each duplicated into
`_Recovery_2026-08-01/PreDefaultMaterialCleanup/`. The `_Recovery` folder names
(`PreDefaultMaterialCleanup`, `PreRibbonUpgrade`) state plainly that they are pre-change
snapshots of migrations that already completed.

`bp_sweep` requires `DUPES == 0` (`Tools/echo_run.py:313`). It is a standing known-failure.
Resolving `NS_MagicTrail` and retiring the three `_Recovery` snapshots removes Niagara's
contribution to that failure; the mirror-tree Blueprint duplicates are separate and out of scope.

---

## 2. The core defect: two competing flipbook mechanisms

This is the decision the plan exists to force.

**Mechanism A — engine SubUV.** Niagara's sprite renderer owns `SubImageSize`,
`bSubImageBlend`, and a `SubImageIndexBinding` driven per particle. In use by
`NS_Melodia_LeafPileLoop_Candidate` ("Sprite + SubUV 2×2", `MI_Leaves`).

**Mechanism B — material-side atlas math.** `M_Niagara_MelodiaFlipbook` computes its own cell
UVs in a `MaterialExpressionCustom`:

```hlsl
float cols = max(Cols, 1.0);
float rows = max(Rows, 1.0);
float idx  = floor(fmod(SubIndex, cols * rows));
float cx   = fmod(idx, cols);
float cy   = floor(idx / cols);
float2 cell = float2(1.0 / cols, 1.0 / rows);
return (UV * cell) + float2(cx * cell.x, 1.0 - cell.y - cy * cell.y);
```

with parameters `FlipbookTexture`, `GridCols` (4), `GridRows` (4), `FlipFPS` (15), `Intensity`.

### 2.1 Mechanism B has a fatal authoring bug

`SubIndex` is fed by `Multiply_19`, whose inputs are `MaterialExpressionTime` and the `FlipFPS`
scalar. That is **global game time with no per-particle term**:

```
SubIndex = Time × FlipFPS
```

Every particle drawn with this material displays the **identical frame at the identical
instant**. It looks correct in a 3-particle preview and reads as one synchronised pulsing mass
in a real scene. This is why the system never got adopted past one emitter.

Fix requires a per-particle input — `ParticleRandom` for a random start frame, or
`NormalizedAge` so the atlas plays across each particle's lifetime. **Owner picked
`NormalizedAge`-driven playback** for birth-to-death effects such as droplets.

### 2.1a The opacity chain never sampled the mask — the bigger bug

Found by exporting the graph rather than reading expressions. The material's outputs were:

```
EmissiveColor <- Multiply_21 = (TexRGB x ParticleColorRGB) x Intensity
Opacity       <- Multiply_22 =  TexSample[.A] x ParticleColor[.A]
```

Opacity sampled the texture's **alpha channel**. These atlases have no alpha — the source PNGs
are grayscale/RGB luminance masks, and both were imported as DXT1. DXT1 returns alpha = 1, so
`Opacity = ParticleColor.A` and the flipbook mask never reached opacity at all. Every particle
drew as a full opaque quad with no shape, at every frame.

This, more than §2.1's timing bug, is why the system was never adopted. It is also invisible to
`get_all_expressions` — only the connection export shows which output index feeds Opacity.

**Fixed 2026-08-28:** `Multiply_22.A` now takes the texture's **R** channel
(`OutputIndex=1, MaskR=1`), which is where a luminance mask actually lives.

### 2.2 Recommendation

**Standardise on Mechanism A (engine SubUV) for anything lifetime-driven; keep Mechanism B only
where a material must animate independently of particle age.**

Reasoning: Niagara already owns per-particle sub-image state, exposes it to modules and to
curve-driven age bindings, and costs no custom HLSL to maintain. Mechanism B duplicates that in
a shader and — as §2.1 shows — got the per-particle part wrong precisely because the material
has no natural access to particle age. Keeping both means every future sprite needs an
undocumented choice between them.

This is a consolidation, not a rewrite: only one emitter uses Mechanism B today.

### 2.3 Flipbook texture import settings are wrong

The source PNGs are luminance masks with **no alpha channel** (`T_Alpha_water_globule_flipbook`
and `T_Alpha_sparkle_pulse_flipbook` are 1024×1024 RGB, `T_Alpha_fluid_metaball_flipbook` is
2048×2048 grayscale). The `T_Alpha_` prefix is misleading. Verified content: min 0, max 255,
means 27–73, so the images carry real data.

Both imported textures are:

| Setting | Current | Should be |
|---|---|---|
| `sRGB` | `true` | `false` — sRGB on a mask skews the opacity ramp |
| Compression | `TC_Default` (DXT1) | grayscale/alpha compression |
| LOD group | `TEXTUREGROUP_World` | `TEXTUREGROUP_Effects` |

**Not a bug, checked and cleared:** the grid. `MI_Niagara_MelodiaFlipbook_Water` overrides only
`FlipbookTexture` and inherits `GridCols`/`GridRows` from the sparkle master, which looked
suspicious. Decoding the water-globule atlas offline puts its gutters at 0 / 256 / 512 / 768 /
1024 — it is **4×4**, matching the inherited defaults. Leave it.

**Retracted:** an earlier pass in this session claimed the water atlas was blank, based on
`material_query preview_texture` returning solid white. A known-good Megascans base-colour
texture previews solid white through the same tool. The preview path cannot decode these
formats; that conclusion was an instrument artifact. **Do not use `preview_texture` as evidence
for texture content in this project.**

---

## 3. `NS_SeaAbove_UpwardDroplets_Prototype` — worked example

`get_system_diagnostics` reports `error_count: 0`, `compile_status: UpToDate`. It is healthy and
wrong, which is the pattern this plan is meant to catch.

| Finding | Detail |
|---|---|
| **Wrong material** | Sprite renderer bound to `M_SeaAbove_Membrane_Prototype` — the Bell's membrane shader (`Time → Sine → Add → Multiply`, `MembraneTint`, `Fresnel`, `MembraneOpacity`, **no texture**). Fresnel on a camera-facing billboard is near-constant, so every droplet is a flat uniform quad. |
| `effect_type` | `null` — no scalability or significance handling |
| Bounds | `fixed_bounds: false`, `Dynamic` mode, on a world-space CPU emitter spanning thousands of units |
| `warmup_time` | `0` — the Sea Above cutscene travels in and the droplets visibly start from empty |
| `bCastShadows` | `true` on droplet sprites |
| `SortMode` | `None` on translucent sprites |
| `MaxCameraDistance` | `1000` behind `bEnableCameraDistanceCulling: false` — inert today, deletes the effect past 10 m the day culling is enabled |

Target state: `MI_Niagara_MelodiaFlipbook_Water` (or a `_Droplet` sibling) on Mechanism A with
age-driven sub-image, fixed bounds, an assigned effect type, warmup ≈ one particle lifetime,
shadows off, distance sorting on, and the stale `MaxCameraDistance` cleared.

---

## 4. Plan

> **Status 2026-08-28: Phase 1 complete, Phase 2 complete except the emitter's own
> `calculate_bounds_mode`.** All changes verified by live re-read and saved individually.
> A third defect was found during execution and is recorded in §2.1a.

### Phase 1 — settle the mechanism (no asset churn)
1. Fix `M_Niagara_MelodiaFlipbook`'s `SubIndex` to take a per-particle term (`NormalizedAge`),
   so Mechanism B is correct wherever it is deliberately kept.
2. Re-import the three flipbook textures with mask-correct settings (§2.3).
3. Write the one-paragraph rule into `Docs/NIAGARA_ECOSYSTEM_2026-08-09.md`: engine SubUV is the
   default; material-side atlas math requires a stated reason.

### Phase 2 — fix the Sea Above droplets end-to-end
4. Swap the droplet material off the membrane shader; apply the §3 target state.
5. This becomes the reference implementation every later sprite system is copied from.

### Phase 3 — sprite-renderer hygiene sweep
6. Audit the 20 live `VFX/Systems/**` sprite systems against the §3 checklist —
   material assigned and appropriate, fixed bounds, effect type, sort mode, shadows,
   dead `MaxCameraDistance`.
7. Resolve the `NS_MagicTrail` duplicate: decide which of the CPU and GPU versions is canonical,
   confirm level references, retire the other.
8. Retire the three `_Recovery_2026-08-01` snapshots — their migrations are complete and named
   as such.
9. Retire the 9 promoted candidates in §1.2 **after** confirming each live twin is the
   level-referenced one. Leave the 10 pending candidates alone.
10. Re-run `bp_sweep` and record whether Niagara's duplicate contribution is cleared.

### Deferred
Adopting the flipbook system across the other 63 sprite systems. Not worth doing until Phase 2
proves the reference implementation on screen.

---

## 5. Decisions needed

| # | Question | Default if unanswered |
|---|---|---|
| 1 | `NS_MagicTrail` — is the CPU or GPU version canonical? | Keep GPU (`Systems/Magical/`), it matches the folder convention |
| 2 | Retire the 9 promoted candidates, or keep as historical? | Retire — deleting assets is ask-first, so this stays blocked until answered |
| 3 | Does the SDF candidate family have a promotion date? | Leave untouched |

---

## 5a. Tooling defects found while executing this plan

**`material_query delete_expressions` crashes the editor.** Confirmed 2026-08-28 by killing a
live session:

```
Assertion failed: !IsRooted()  [UObjectBaseUtility.h:209]
  UnrealEditor-MonolithMaterial.dll!FMonolithMaterialActions::DeleteExpressions()
    [Plugins/Monolith/Source/MonolithMaterial/Private/MonolithMaterialActions.cpp:9245]
```

`DeleteExpressions` does not check `IsRooted()` before deleting the expression `UObject`. Called
on `MaterialExpressionTime_5` + `MaterialExpressionScalarParameter_20` while the material was
loaded, it asserts and takes the whole editor down.

**Until that is fixed: do not call `delete_expressions`.** Orphan unwanted expressions by
rewiring around them and leave them in the graph. A disconnected node is inert; a dead editor
costs the session.

**Consequence, and the process rule it proves.** That crash destroyed three verified material
fixes because they had been mutated but not saved. The melodia-p0-loop verification loop ends in
`save_asset` for exactly this reason. For material work the rule is:

```
mutate -> verify the specific property re-reads correctly -> save_material -> only then continue
```

One mutation, one save. Do not batch material edits behind a single save.

**`material_query preview_texture` cannot be used as evidence** — see §2.3. It returns solid
white for known-good textures.

---

## 6. Evidence

- Live audit via `niagara_query` (`query_niagara has_renderer=Sprite`, `search_by_material`,
  `get_system_summary`, `list_renderer_properties`) and `material_query`
  (`get_all_expressions`, `get_expression_details`, `get_expression_connections`,
  `get_material_parameters`, `get_texture_properties`) against the running editor, 2026-08-28.
- Atlas grid derived offline by gutter analysis of the source PNGs.
- `audit_cross_asset_refs` was unavailable (`EngineSource.db not available`); the duplicate
  analysis in §1.3 is from asset paths, not that tool.
