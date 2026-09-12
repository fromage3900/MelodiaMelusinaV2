# Premium outline stack — build report, 2026-08-01

## SESSION CLOSED — final PPV state

`PPV_NikkiDream` (ZenForestTest, **level deliberately unsaved** — owner art work is dirty there):

| Slot | Asset | Notes |
|---|---|---|
| 1 | `MI_StorybookOutline_Premium_Hero` | **LOCKED — owner approved. Do not touch.** |
| 2 | `MI_MeluColorGrade_PortfolioHero` | live grade |
| 3 | `M_PP_StarryNightOverlay_Candidate_Inst` | Van Gogh sky, V7 discrete dabs |

Sky instance is tuned **deliberately loud** for structure reading, not final art:
`StrokeDensity 11`, `StrokeGap 0.55`, `StrokeThickness 0.46`, `StrokeHueVar 0.72`,
`BristleAmount 0.7`, `BrushTiling 5`, `ImpastoRelief 3.6`, `ImpastoStrength 1.0`,
`PaintSpecular 0.78`, `SkyPaintAmount 0.78`, `ValueStructure 0.95`, `SwirlWarp 0.26`,
`HaloStrength 1.1`, `NebulaIntensity 0.6`, `StarIntensity 2.0`.

⚠️ **`UseUDSTimeOfDay` is 0 and `ManualNightAmount` is 1** — the sky is pinned permanently on so it
could be seen and tuned. **Before shipping any capture, set `UseUDSTimeOfDay=1` and put UDS at
~23:00**, which restores the intended behaviour where the painting fades in and out on UDS's real
clock and recedes behind cloud/fog.

### Why it was invisible at first (worth remembering)

Three causes stacked, and the first alone was fatal: UDS `Time of Day` was `960` (16:00), so the
night gate evaluated to exactly 0 and the shader's first branch returned the untouched frame. The
integration was working *correctly* — the effect self-suppresses in daylight — but six versions could
have been invisible for that reason alone at any point. The instance also carried a corrupt
`ManualNightAmount = -6.021` and a `SkyDepthThreshold` of `164173`.

**Lesson: when a gated effect "doesn't show", check the gate inputs before touching the shader.**


## Sky V7 — DISCRETE DABS (347 PS instr, 0 issues, readback confirmed)

Owner looked at V6 and said it still didn't read as the painting. Correct call, and it isolated the
cause: **V3–V6 all refined a *continuous* height field.** Vortices, travel, halos, value structure
and UDS integration were all layered onto a field with no stroke boundaries — and a continuous field
elongated along a direction reads as flowing texture no matter how it is tuned. Van Gogh's marks are
separate objects.

V7 replaces the generator (everything else is untouched and still correct):

- Flow-aligned space quantised into **rows** across the current and **cells** along it; one dab per
  cell, each row hash-offset so dabs never form a visible grid.
- Each dab hashes to its own **length, thickness and hue**.
- Dabs are **shorter than their cell** — the remainder is canvas, and that gap is the entire point.
- **Tapered ends**: blunt where the brush lands, thin where it lifts.
- `T_Flow_Brushed` demoted to **bristle grain inside a dab** rather than being the stroke field.
- **Per-dab hue scatter** across the palette so neighbours differ instead of a region washing as one.

Params (`VanGogh Painting`): `StrokeDensity` 26, `StrokeGap` 0.35, `StrokeThickness` 0.38,
`BristleAmount` 0.55, `StrokeHueVar` 0.45. Applied via `Content/Python/apply_starrynight_v7.py`
(idempotent; holds the 63-pin list and rewire map).

Verified beyond the compile: `strokeMask` and `StrokeGap` present, and the old `h1 * 0.55` continuous
blend is **absent** — the generator was genuinely replaced, not layered over.

## Starry Night refinement plan — what still separates V6 from the painting

**Do step 0 before any of this.** Six versions have been authored without a single one being seen
rendered. Open `ZenForestTest` at night (`UDSTimeOfDay` is now the driver — set UDS to ~23:00, or
set `UseUDSTimeOfDay=0` and `ManualNightAmount=1`), and tune what already exists before adding
anything. The dials that will move it most: `ValueStructure` (0.6), `StrokeElongation` (3.2),
`StrokeTravel` (0.35), `ImpastoRelief` (1.0), `BrushTiling` (8.0), and `VortexA`/`VortexB` `.xy` to
place the currents where the camera actually frames them. If it already reads, stop — the list below
is optional.

### The three gaps that actually matter, in order

**1. Strokes are continuous, not discrete.** This is the single biggest remaining difference. Van
Gogh's marks are *separate dabs* with visible canvas between them and definite ends. V6 elongates a
continuous noise field along the flow, which reads as flowing texture rather than individual strokes.
Fix: quantise the stroke space into cells along the tangent, hash a stroke ID per cell, and give each
its own length, phase and slight curvature — with genuine gaps between them. `T_Flow_Brushed` becomes
the *shape within* a stroke rather than the stroke field itself.

**2. Every stroke in a region is the same hue.** In the painting, adjacent strokes are different
colours — cobalt beside cerulean beside white beside chrome yellow. V6 derives colour from a global
luminance remap, so a whole area shifts together. Fix: per-stroke hue jitter driven by the stroke ID
hash, bounded to the palette (`R1999_Navy` → `Melusina_Lavender` → `Melusina_SoftWhite` →
`R1999_Gold`), so variation stays on-brand rather than rainbowing.

**3. One global flow field.** Real brushwork follows *form*: strokes curve around the currents, lie
flat along the horizon, and radiate concentrically around the bright stars. V6 has a single tangent.
Fix: blend three tangent sources by weight — vortex-tangential, horizon-parallel, and star-radial
near halo centres. `T_Flow_Radial` (already in the project, unused) is the natural driver for the
third.

### Smaller, after those land

- **Moon:** UDS already renders one. Paint a halo *around* it using `UDSMoonVector` projected to
  screen — do not draw a second moon, that is the "eating" mistake again.
- **Inter-stroke occlusion:** thick paint has a bright ridge on the lit side and a dark valley
  opposite. Sharpen the existing relight at stroke boundaries and add slight AO in the gaps.
- **Regional value:** the painting is dark at the frame edges and bright at the centres of the
  currents. Currently the value remap is purely luminance-driven, so it has no composition.
- **Canvas weave:** a faint substrate texture under everything ties the strokes together.

### Project assets still unused for this

`T_Starryfabric_normal` / `_displace` (authored thick-paint normal + displacement — could replace the
derived normal with real brushwork), the ZBrush Orb brush pack at project root (genuine impasto
alphas), `T_Flow_Radial`, and the master's `14 Celestial (Nebula)` group (nebula **and galaxy**
layers plus `bCelestialUsesDreamPalette`).

## ⚠️ Substrate reroutes things — check before declaring a feature missing

This cost two wrong conclusions in one day. `r.Substrate=True` and
`r.Substrate.ProjectGBufferFormat=0` are live, which changes where material features actually live:

1. **`ShadingModelID`** — `PPI_ShadingModelID` never returns `TWOSIDED_FOLIAGE` (6) under Substrate,
   because the Substrate shader tree only ever assigns `0`, `DEFAULT_LIT`, `SUBSTRATE_TOON` or
   `HAIR`. The "foliage-safe" classification in the live outline is therefore dead code.
2. **Emissive on `M_Master_Toon_Universal`** — `MP_EMISSIVE_COLOR` reads "nothing connected", which
   looks alarming and means nothing. Under Substrate **all** legacy pins (`BaseColor`, `Emissive`,
   `Roughness`, `Metallic`, `Normal`) are empty by design; everything routes through
   `MaterialExpressionSubstrateToonBSDF_4` → `FrontMaterial`. Pin 5 `EmissiveColor` **is** connected,
   fed by `MaterialExpressionAdd_11` from the whole Nikki glow chain. Emissive works.

**Rule: before reporting a material feature as missing or broken, inspect the Substrate BSDF node,
not the legacy output pins.** Both errors above came from reading the legacy pin and stopping there.

The one true limitation on the universal master is that it has **no emissive texture sampler** —
glow is authored via parameters, not textured. Adding one is a master-architecture change requiring
owner approval and a closed editor; it affects every material parented to that master.

## ⛔ LOOP STOPPED — landscape parallax needs an architecture decision

**The landscape master cannot do parallax, and adding it is a master-architecture change.**

Studied `M_Master_Toon_Landscape_HeightBlend` (confirmed live via `MI_Landscape_SakuraGarden` on the
`Landscape2` actor):

- It **has** per-layer height maps: `Grass_Height`, `Mud_Height`, `Rock_Height`, `Path_Height`.
- It has **no parallax parameters at all** — no `ParallaxScale`/`Strength`/`Height`.
- Its material-function calls are `MF_ColorRamp3`, `MF_Itto`, `MF_LandscapeHeightCompete`,
  `MF_Madoka`, `MF_NikkiDreamGrade`, `MF_NormalAdjust`. **No parallax function.**

So the height maps drive `MF_LandscapeHeightCompete` — **height *blending* between layers**, which is
a different feature from parallax occlusion. Height-blend decides which layer wins per pixel; it does
not offset UVs for depth. "Fine-tune the landscape to use parallax" is therefore not a tuning task —
it requires adding a parallax path to the master, which affects every landscape instance and is
explicitly ask-first under `CLAUDE.md`. **Not attempted.**

### Universal master parallax IS live — token work validated

Contrast, verified rather than assumed (given the Substrate lessons above):

- `ParallaxStrength` (`ScalarParameter_740`) → **3 consumers** (`Multiply_792/797/802`, one per
  texture layer).
- `LayerA_ParallaxScale` (`ScalarParameter_697`) → `Multiply_791`.

So the four Melody Token instances, which pair a `HeightMap` with `ParallaxStrength = 1.0`, will
genuinely parallax. Star/Swirl/Water have Displacement maps wired; Heart has none and sits at 0.

**Minor drift noted:** `setup_master_universal.py` defines `MF_PARALLAX_CORE` and references
`MF_ParallaxCore`, but the master actually calls **`MF_SpaceParallax`** — parallax proper is inline
UV offset (the script's own comment says so: *"Inline height parallax UV offset; avoids stale
MF_ParallaxCore pin typing"*). The constant is vestigial.

### DECIDED 2026-08-01 (owner): no parallax on terrain

`M_Master_Toon_Landscape_HeightBlend` keeps its current depth model — **height-blend plus normals,
no parallax path**. Do not add one, and do not treat its missing parallax parameters as a gap; this
is the intended design for a stylised toon landscape.

Parallax remains in scope only for the **universal master** (props, tokens, hero assets), where it is
already live and verified.

## Polish loop — iteration log

Recurring 15-min loop (session job `a5c360bc`). Study first, one narrow area per pass, every write
read back before it counts as done.

### Iter 4 — unification (sky V6, 324 PS instr, 0 issues, readback confirmed). LOOP STOPPED.

**Studied first: the grade already speaks the project's language, the other two had drifted off it.**

`M_PP_MeluColorGrade` (the active `/Game/_PROJECT/...` one) uses the master's Nikki vocabulary —
`DreamContrast`, `DreamSaturation`, `DreamShadowLift`, `DreamHighlightSoft`, `DreamTint`,
`DreamShadowTint`, `DreamHighlightTint`, `DreamSpectralCycles`, `NikkiHeroGradeStrength` — and reads
`MPC_Melodia_Palette`. The outline and sky read **neither**, and had hand-drifted their colours:

| Authored in `MPC_Melodia_Palette` | What the materials invented instead |
|---|---|
| `Melusina_InkNavy` (0.04, 0.04, 0.08) | outline `OutlineColor` (0.075, 0.035, 0.095) |
| `R1999_Navy` (0.05, 0.08, 0.18) | sky `DeepColor` (0.32, 0.42, 1.15) |
| `R1999_Gold` (0.85, 0.70, 0.30) | sky `LightColor` (1.35, 1.15, 0.55) |
| `Melusina_SoftWhite`, `Melusina_Lavender` | sky `StarTint`, `NebulaTint` |

**`PaletteFollow`** (default **0**, locked look unchanged) blends the sky's local colours onto
`R1999_Navy` / `R1999_Gold` / `Melusina_SoftWhite` / `Melusina_Lavender`. At 1 the sky is driven
entirely from the shared palette.

**⚠️ Engine limit found: a material may reference at most 2 MaterialParameterCollections.**
Adding the palette made three and the material failed to compile outright. Resolved by **deleting
`MPC_MelodiaSkyLookdev_Candidate`** from the sky: every channel was 0, no adapter ever wrote it, and
UDS now supplies the real drivers — it was a parallel controller of exactly the kind the project's
rules forbid. `NightAmount` survives as a plain scalar override. Collections now referenced:
`UltraDynamicWeather_Parameters` + `MPC_Melodia_Palette`.

**This budget is the binding constraint on unification.** The outline cannot read both UDS and the
palette *and* anything else. Plan the two slots deliberately per material.

**Also found: `MPC_Portfolio_Palette` is a near-duplicate of `MPC_Melodia_Palette`** — identical
vector set (`Melusina_*`, `R1999_*`, `Melu*`). Two palette authorities is a real duplicate-authority
problem; the master reads one, the grade reads the other. Needs an owner decision, not an agent's.

**Still not applied to the outline** — it has the same drift (`OutlineColor` vs `Melusina_InkNavy`)
and the same 2-collection budget to plan. Next session's first job.

### Iter 3 — the actual painting (sky V5, 304 PS instr, 0 issues, readback confirmed)

Reference-driven rather than "stars + swirls". Starry Night's structure is specific:

- **Two spiral currents.** The painting is built on two great vortices, not uniform turbulence. Each
  (`VortexA`, `VortexB` — xy = position in equirect sky space, z = strength/direction) rotates the
  sample field by an angle falling off as `1/r²`, so curl is strongest at the eye and relaxes
  outward. `VortexB` is authored with negative strength so the two currents counter-rotate.
- **Strokes that TRAVEL.** The previous version had a static height field — the single biggest reason
  it didn't read as brushwork. Sample space is now elongated along the local flow tangent
  (`StrokeElongation`) and scrolled along it (`StrokeTravel`), turning the field into short dashes
  that move with the current. The three octaves each ride the tangent at different rates.
- **Haloed stars.** Every star in the painting sits in a concentric bloom. A high-mip read of the
  NASA plate (`HaloMip`) gives the glow footprint; ringing it by luminance (`HaloRings`) turns a soft
  bloom into painted halos.
- **Value structure.** The painting separates into deep ultramarine shadow and chrome-yellow light
  with little between. Sky luminance is remapped across `DeepColor` (cobalt) and `LightColor`
  (chrome yellow) through `ValueLow`/`ValueHigh`, blended by `ValueStructure`. Without this the
  effect reads as texture on a photograph — this is the colour spine.

New group `VanGogh Painting`. All UDS integration from iter 2 is preserved.

⚠️ **Process note — order of operations.** Setting the Custom node's *code* before adding its *pins*
produces alarming (but harmless) `use of undeclared identifier` compile failures in the log between
the two steps. **Always update `inputs` first, then the code, then rewire.** And remember the pin
rewrite wipes all connections, so the full set must be re-wired every time.

### Iter 2 — UDS integration, not replacement (sky V4, 250 PS instr, 0 issues, readback confirmed)

**The problem:** the overlay consumed nothing from UDS. It painted stars, nebula and impasto over
every sky-depth pixel unconditionally — and clouds are sky-depth too, so UDS's cloud shapes were
being flattened. It was decorating a frame UDS had already authored, with no knowledge of it.

**The fix: read UDS's own live collection.** `UltraDynamicWeather_Parameters` already publishes
everything needed, so no adapter and no parallel controller were built — the project's standing rule
is that UDS keeps authority over time, weather, sun/moon, cloud, fog and skylight, and this now
consumes those values one-way.

| UDS parameter | How the painting responds |
|---|---|
| `Time of Day` (0–1440 min) | Drives night directly. `ManualNightAmount` survives as an override, blended by `UseUDSTimeOfDay`. The painting now appears and fades on UDS's own cycle. |
| `Cloud Coverage` | Recedes the whole effect (`CloudRecede`) so overcast skies stay UDS's. |
| `Fog` | Recedes (`FogRecede`) — the painting washes out with atmosphere. |
| `Global Occlusion` | Dims (`OcclusionRecede`). |
| **`Sun Vector` / `Moon Vector`** | **Lights the impasto.** Projected into screen space via `View.ViewRight`/`ViewUp` and blended sun→moon by night, so paint ridges catch light from the *actual* celestial body and relight across the day instead of from a baked constant. |
| `Wind Intensity` / `Wind Angle` | Drives stroke travel speed and direction — brushwork flows with the real wind. |

**Cloud preservation.** Sky luminance now rejects stars and nebula (`StarSkyRejection`): bright sky
pixels — i.e. lit clouds — reject the overlay, so UDS's cloud structure survives instead of being
painted flat. This is the specific fix for "eating" the sky.

Three `UseUDS*` switches default to **1** (integrated). Set any to 0 to fall back to the hand-authored
constant for that channel.

⚠️ **Known trap, hit twice now:** `update_custom_hlsl_node` with an `inputs` array **wipes every
existing connection**, not just the changed ones. Always re-wire the full pin set afterwards and
confirm `is_compiled: true` — a partial rewire compiles as `missing input 1 (SceneColor)`.

### Iter 1 — jitter / AA (V3a, 335 PS instr, 0 issues, readback confirmed)

**Fixed: unbounded AA half-band.** `aaS`/`aaC` came straight from `fwidth(response) * AAWidth` with
no upper clamp. On a steep silhouette `fwidth` exceeds 1.0, which drives the smoothstep lower bound
`1.0 - aa` **negative** — the ramp then starts from a negative response and collapses back into a
hard, quad-shaped step. That is a direct contributor to the blocky resolve, and it gets *worse* as
`AAWidth` is raised, which is the opposite of what the dial promises. Now clamped to `[1e-5, 0.9]`.

**Jitter sign — reviewed, believed correct, still unverified in motion.**
`View.TemporalAAJitter.xy * float2(0.5,-0.5) * ViewSizeAndInvSize.xy * invBuffer`, subtracted from
`uvC`. Dimensionally right (clip → viewport UV → pixels → buffer UV), the `-0.5` on Y handles the
clip/UV flip, and subtracting is correct because UE bakes `+jitter` into the projection matrix. The
neighbour taps derive from the corrected `uvC`, so the ring stays consistent. **This cannot be
confirmed without a moving camera** — `JitterCompensation` is signed, so if contours still swim,
try `-1` before assuming the maths is wrong.

**Project-state finding: `r.TSR.ShadingRejection.Flickering = 1`.** TSR's flicker rejection actively
fights high-frequency post-process content, which is exactly what a 1-pixel ink contour is. If
outlines shimmer in motion after the jitter sign is confirmed, this cvar is the next suspect — not
the material. Also live: `r.AntiAliasingMethod=4` (TSR), `r.TSR.History.ScreenPercentage=200`,
`r.TemporalAASamples=8`.


## Van Gogh sky V3 — real impasto (199 PS instr, 0 issues)

### ⚠️ `MF_Impressionist_Impasto` is a stub — do not build on it

Inspected because the sky "looked nothing like Van Gogh". The function has **9 outputs and every
one is `StrokeMask * ScalarParam * ScalarParam`** — the same two-multiply block appended nine times,
with two duplicate `StrokeMask` inputs. It produces **no height, no normal, no lighting**. Anything
wired to it gets a scaled mask and nothing more. `M_Melodia_StarryNight_Impressionist` consumes its
`ImpastoHeight` output, which is why that material's "impasto" also reads flat.

Real impasto is now written directly in the overlay. If the function is ever repaired, it needs a
height field and a derived normal, not more multiply blocks.

### What makes it read as thick paint

Paint looks thick because **ridges catch light**. The overlay now:

1. Builds a **height field** from `T_Flow_Brushed` at three octaves (big sweeps 0.55, mid strokes
   0.31, fine bristle chatter 0.14), each scrolling at a different rate.
2. **Domain-warps** the sample coordinates through `T_Flow_Swirl` before sampling — this is what
   bends straight strokes into Van Gogh's curling currents. Without the warp you get stripes.
3. Takes the **screen-space gradient of that height as a paint normal** (`ddx`/`ddy`, scaled ×400
   since the field varies slowly per pixel).
4. **Relights it** — half-lambert against `PaintLightDir` plus a Blinn-ish specular
   (`PaintGloss`/`PaintSpecular`), so crevices between strokes darken and ridges glint.

### Proper constellations

`T_NASA_StarMap_4K` **was already in the project** — no download needed. Sampled through an
**equirectangular** UV built from the world view direction
(`atan2(dir.y, dir.x)`, `acos(dir.z)`), so constellations sit in real sky positions and stay put as
the camera turns. `Purple_Nebula_3` layers underneath with independent tiling and slow drift.

### Tiling / control set (group `VanGogh`)

`StarMapTiling`, `StarMapOffset`, `StarTint`, `StarIntensity`, `NebulaTiling`, `NebulaTint`,
`NebulaIntensity`, `BrushTiling` (8.0), `SwirlWarp` (0.12), `SwirlSpeed` (0.12), `ImpastoRelief`,
`ImpastoStrength` (0.75), `PaintGloss` (24), `PaintSpecular` (0.35), `PaintLightDir`,
`SkyPaintAmount`, `SkyPaintTint`. Textures are `TextureObjectParameter`s, so any of the four maps can
be swapped per instance without touching the master.

Still sky-pixels-only and UDS-hybrid. Dead V1/V2 params were deleted, not orphaned; the superseded
`MF_ConstellationField` call and its helper were removed. **Not yet seen rendered.**

### Also available, not yet used

`T_Starryfabric_normal` / `_displace` (thickly-painted normal + displacement), `T_Flow_Radial`,
`T_Standalone_StarryAlpha1/2`, the ZBrush Orb brush pack at project root, and the master's
`14 Celestial (Nebula)` group (`StarMap`, constellation ramp, nebula **and galaxy** layers,
`bCelestialUsesDreamPalette`).


## V3 LOOKDEV PASS — Nikki magic suite, halftone/blur, Van Gogh sky

### Correction: the magic suite exists, I was wrong

An earlier note in this file said `MF_NikkiRimGlow` / `_Sparkle` / `_IridescenceSheen` "were never
built". That was wrong — it checked for `MF_*` **assets**. The effects live as **inline parameter
groups inside `M_Master_Toon_Universal`**, and there are far more than three:

`08 Nikki Rim & Glow` · `09 Nikki Sparkle` · `10 Nikki Iridescence & Sheen` · `10a Color Ramp` ·
`10b Dream Rim (magic)` · `10c Dream Bloom` · `10d Dream Flow (living magic)` · `10e Dream Pulse
(breathing)` · `10f Kaleidoscope Sigil` · `10g Dawn Wash` · `10h Dream Mist` · `10i Twinkle Glints` ·
`10j Dream Halo` · `11b Impasto Paint` · `14 Celestial (Nebula)` · `20 Cinematic` (atmospheric
depth) · `22 Temporal / Ink`.

**`14 Celestial (Nebula)` is a fully authored starry system** (`StarMap`, `ConstellationScale/Strength`,
`CelestialNebulaScale/Strength`, `CelestialGalaxyScale/Strength`, `CelestialStarIntensity`,
`CelestialToonSteps`, `bCelestialUsesDreamPalette`) — worth mining before building any new sky maths.

### Outline V3 — 334 PS instr, 0 issues

New dials use the **same parameter names as the master's groups**, so the outline speaks the same
language as the surface material. **Every one defaults to neutral**, and `MI_StorybookOutline_Premium_Hero`
overrides none of them — verified — so the locked look renders unchanged.

- **Ink blur (fixes the square breakup).** `fwidth()` resolves per 2×2 pixel quad, which is exactly
  what made the AA break up in squares. The edge field is now blended from the directional **max**
  (sharp) toward the directional **mean** (soft) via `InkBlurStrength`, with `InkBlurRadius` widening
  the tap ring. Softening the response *before* the resolve fixes it at source rather than hiding it.
- **Proper halftone.** A true rotated dot screen: dot **radius tracks local ink coverage**
  (`sqrt(edge)`), screen rotated by `HalftoneAngle`, cell size `HalftoneScale`, blended by
  `HalftoneAmount`. Coverage-driven radius is what reads as printed ink; a fixed-cell threshold is
  what reads as a grid.
- **`10b Dream Rim (magic)`** — `DreamRimStrength/Power/Cycles/Color`. Spectral cycling rim from the
  reconstructed normal against the view vector, additive into the ink.
- **`10 Nikki Iridescence & Sheen`** — `Iridescence`, `IridescencePower`, `IridescenceCycles`,
  `IridescenceTint`. View-dependent spectral shift on the ink itself.
- **`20 Cinematic` atmospheric depth** — `DistanceFadeStrength/Start/End`, `AtmosphericFadeColor`.
  Distant contours drift into haze instead of staying full-strength ink.

### Starry sky V2 — Van Gogh impasto, 222 PS instr

- **The star lattice is gone.** V1 placed one star per cubic cell via `floor(dir * StarDensity)` —
  a regular 3D grid. Stars now come from **`MF_ConstellationField`** (real star textures +
  constellation ramp), fed a world-space view direction so they stay pinned to the sky. The six dead
  V1 params (`StarDensity`, `StarSize`, `StarSparsity`, `TwinkleSpeed`, `TwinkleAmount`, `StarColor`)
  were deleted rather than left as orphans.
- **Impasto swirl:** two counter-rotating flow fields produce a curl, strokes align to it, and
  `abs(sin())` banding gives the raised-paint ridges — `SwirlScale`, `SwirlSpeed`, `BrushSharpness`,
  `BrushContrast`, `ImpastoStrength`, `SkyPaintAmount`, `SkyPaintTint`.
- **Sky pixels only**, gated by the existing depth test, so the toon world and UI contrast are
  untouched. UDS hybrid preserved.

### A/B

`MI_StorybookOutline_Premium_Hero_Dream` has all the new dials turned up; the locked Hero leaves them
neutral, so comparing the two isolates exactly this lookdev layer.

```
import setup_ppv_candidate_ab as ab
ab.mode("dream")     # magic suite on
ab.mode("premium")   # locked look
```

**Not yet seen rendered.** Note the live PPV carries `M_PP_StarryNightOverlay_Candidate_Inst`, an
instance of the sky material — its V1 overrides for the deleted star params drop harmlessly, but its
new `VanGogh` group values are at master defaults and want tuning.


## SESSION CLOSEOUT — final state (owner approved the look: "it looks great", locking)

`PPV_NikkiDream` in `ZenForestTest` now carries three blendables:

| Order | Asset | Weight |
|---|---|---|
| 1 | `MI_StorybookOutline_Premium_Hero` | 1.0 |
| 2 | `MI_MeluColorGrade_PortfolioHero` | 1.0 |
| 3 | `M_PP_StarryNightOverlay_Candidate` | 1.0 |

**⚠️ The level is NOT saved.** `ZenForestTest` holds owner art work that was already dirty, so
nothing was committed. Save manually when happy, or the starry overlay attachment is lost on close.

### Outline V2 — extended AA + working vine growth (233 PS instr, 0 issues)

- **Extended AA:** `AAWidth` (default 1.5) widens the derivative band, and the resolved edge is run
  through a smootherstep so the ramp has no second-derivative kink at either end. No extra samples.
- **Vine growth actually works now.** The previous version sampled a scrolling **screen-space** UV,
  so the pattern swam across surfaces whenever the camera moved — which is why it was disabled
  outright in FoliageSafe. It now reconstructs translated world position from scene depth
  (`View.ScreenToTranslatedWorld`) and samples the branch mask in world space, so vines stay pinned
  to geometry. Growth spreads *outward* from contours by lowering the response threshold rather than
  fading opacity, so `VineGrowthLength` reads as tendril length. Gated on `VineBranchStrength > 0`,
  so it costs nothing while off.

### Starry night overlay — `M_PP_StarryNightOverlay_Candidate` (148 PS instr, 0 issues)

Post-process domain, additive, **sky pixels only** (`SceneDepth > SkyDepthThreshold`). The authored
`M_Melodia_StarryNight_UDS_Candidate` could not be used directly — it is `MD_Surface`, not a
post-process material, so it cannot be a PPV blendable. This is the overlay equivalent.

UDS hybrid, as intended: UDS keeps full authority over sky, fog, sun/moon, clouds and weather; this
only adds stars on top. Star direction is world-space (`View.ScreenToTranslatedWorld`), so stars stay
pinned to the sky under camera rotation instead of sliding in screen space.

`NightAmount` reads `MPC_MelodiaSkyLookdev_Candidate`. **That MPC currently defaults every channel to
0 and no UDS adapter writes it yet**, so a straight binding would have rendered the overlay invisible
out of the box. The night driver is therefore `max(NightAmount, ManualNightAmount)` with
`ManualNightAmount` defaulting to 1 — authorable now, and the moment the adapter starts writing the
MPC it takes over automatically with no material edit.

Parameters (group `Starry`): `StarIntensity`, `StarDensity` 260, `StarSize` 0.06, `StarSparsity` 0.06,
`TwinkleSpeed` 1.4, `TwinkleAmount` 0.5, `StarColor`, `SkyDepthThreshold` 100000, `ManualNightAmount`.

**Not yet seen rendered** — the stars are the one thing in this pass with no visual confirmation.
If they read too dense or too sparse, `StarSparsity` is the dial (higher = fewer stars).


## ⚠️ HEADLINE: foliage classification is DEAD CODE under Substrate

`M_PP_StorybookOutline_FoliageSafe_Candidate` — the current **live project-wide outline** — classifies
foliage with:

```hlsl
float shadingModelId = SceneTextureLookup(uvC, PPI_ShadingModelID, false).r;
float isFoliage = 1.0 - step(0.5, abs(shadingModelId - 6.0));   // 6 = TWOSIDED_FOLIAGE
```

**This can never evaluate true in this project.** Traced through the UE 5.8 engine shaders:

- `Config/DefaultEngine.ini` sets `r.Substrate=True` and `r.Substrate.ProjectGBufferFormat=0`;
  confirmed live as `r.Substrate = 1`, `GBufferFormat = 0`.
- That routes `SceneTextureLookup(..., PPI_ShadingModelID, ...)` down the Substrate branch in
  `MaterialTemplate.ush:3382`, which returns `SubstrateGBuffer.ShadingModelID`.
- Across the whole `Shaders/Private/Substrate/` tree, `ShadingModelID` is only ever assigned
  `0`, `SHADINGMODELID_DEFAULT_LIT`, `SHADINGMODELID_SUBSTRATE_TOON`, or `SHADINGMODELID_HAIR`.
  **`SHADINGMODELID_TWOSIDED_FOLIAGE` (6, per `ShadingCommon.ush:26`) is never produced.**

Consequences, all of which match observed behaviour:

- `isFoliage` is permanently `0`, so grass takes the full architecture ink path.
- `FoliageDepthInkStrength`, `FoliageNormalInkStrength`, `FoliageDistanceFadeStart/End` are inert on
  every instance. Tuning them has no effect and never did.
- The material is not, in fact, foliage-safe. This is why grass still inks solid.

**Not silently patched.** Choosing a replacement classifier is a design decision that affects the live
material, not just the new candidate, so it belongs to the owner. Viable options:

1. **Subsurface colour test** — `PPI_SubsurfaceColor` *is* populated under Substrate. Foliage
   carries non-zero subsurface; rock and architecture do not. Cheapest swap, one line, no per-actor
   setup. Needs a visual check that no non-foliage asset in the scene uses subsurface.
2. **CustomStencil** — fully reliable and already wired (`r.CustomDepth=3` is persisted, and
   `SetReactiveStencil` is live). Costs a per-component stencil assignment on the foliage actors.
3. **Disable Substrate** — do not do this for an outline; it is a project-wide rendering decision.

Note the `abs(id - 6.0)` form would also be fragile even under the legacy path, since it is a float
equality test against a packed value. Prefer a range test whichever classifier wins.

## What was built

`/Game/EnvSandbox/Materials/PostProcess/Candidates/M_PP_StorybookOutline_Premium_Candidate`
— forked from FoliageSafe, **181 PS instructions**, 0 validation issues, marker
`MELODIA_PREMIUM_OUTLINE_V1` verified present in the saved asset after write.

Preserved verbatim from FoliageSafe: `GetDefaultSceneTextureUV`, the view-rect clamp built from
`View.ViewRectMin` / `View.ViewSizeAndInvSize` (the mismatched-resolution streak-band fix), the
one-sided depth silhouette, and stencil styles 1–3 / 4-as-NoInk.

**1. Analytic antialiasing.** Depth and normal responses now stay continuous all the way to the
resolve, then each is antialiased at its own derivative width:

```hlsl
float aaS = max(fwidth(silResponse), 1e-5);
float silEdge = smoothstep(1.0 - aaS, 1.0 + aaS, silResponse);
```

The old code pre-saturated both terms, which is precisely what forced the hard stair-stepped edge.

**2. Silhouette / crease separation.** The single `max()` is split into a depth-driven silhouette
(`OutlineColor`, `DepthWeight`, `DepthRelativeThreshold`) and a normal-driven crease (`CreaseColor`,
`NormalWeight`, `CreaseThreshold`), each AA-resolved independently and composited silhouette-over-crease
so outer contours stay decisive. This is also the correct home for the foliage fix once a working
classifier exists — keep the silhouette, drop the crease.

**3. Perspective-tapered width.** Width is now world-referenced rather than fixed screen texels:
`widthPx = clamp(OutlineWidth * (RefDistance / dC), MinWidthPx, MaxWidthPx)`, plus `TaperStrength`
fading opacity with the same ratio. `MinWidthPx` is floored at 0.35 so distant lines cannot alias
back into shimmer.

**4. TSR jitter control.** TSR (`r.AntiAliasingMethod=4`) jitters the GBuffer sub-pixel every frame
while SceneColor arrives resolved; that mismatch is what makes contours crawl. Now compensated:

```hlsl
float2 jitterPx = View.TemporalAAJitter.xy * float2(0.5, -0.5) * View.ViewSizeAndInvSize.xy;
uvC = clamp(uvC - jitterPx * invBuffer * JitterCompensation, viewUVMin, viewUVMax);
```

`View.TemporalAAJitter` was verified to compile in this post-process context. `JitterCompensation`
defaults to 1; it is a signed scalar, so a negative value flips the correction if the sign proves
inverted in motion.

New parameters (group `Premium`): `CreaseColor`, `CreaseThreshold`, `RefDistance`, `MinWidthPx`,
`MaxWidthPx`, `TaperStrength`, `JitterCompensation`.

Instance: `Candidates/Profiles/MI_StorybookOutline_Premium_Hero` (21 scalar + 2 vector overrides,
authored fresh — no values copied from existing profiles).

## Static-switch quality tiers — deliberately NOT built, premise did not hold

The approved plan called for a `PremiumQuality` static switch on the assumption the full stack would
land at 300–450 instructions. It landed at **181, only +11 over FoliageSafe's 170.** Adding a second
Custom HLSL node plus a static switch to save ~11 instructions would mean two copies of the same
shader body — exactly the duplicated-material-logic trap that produced a byte-identical "rewrite"
earlier today. Flagged rather than built; say the word if you still want the tiers.

## A/B

`Content/Python/setup_ppv_candidate_ab.py` gained a `premium` profile pairing
`MI_StorybookOutline_Premium_Hero` with `MI_MeluColorGrade_GameplayStandard`, so the grade is held
constant and the comparison isolates the outline. All five profiles resolve.

```
import setup_ppv_candidate_ab as ab
ab.mode("premium")     # premium stack
ab.mode("source")      # back to live
```

## State left behind

`ZenForestTest` was left exactly as found — the A/B `ensure()` spawns a candidate volume, so it was
destroyed again afterwards; the level still holds only `PPV_NikkiDream` and was **not saved**
(owner art work is deliberately dirty there). No live material, PPV, or existing instance parameter
was modified.

## Not yet verified — needs eyes

1. **Visual A/B** at a fixed ZenForest camera. Nothing here has been seen rendered.
2. **Motion check** for jitter/crawl, and the sign of `JitterCompensation`.
3. **Mismatched-resolution capture** — `take_high_res_screenshot(1920, 1080, 'x.png')` with **no**
   sleep after the call; a clean bottom edge proves the view-rect clamp survived the rewrite.
4. The foliage classifier decision above, which gates whether grass improves at all.
