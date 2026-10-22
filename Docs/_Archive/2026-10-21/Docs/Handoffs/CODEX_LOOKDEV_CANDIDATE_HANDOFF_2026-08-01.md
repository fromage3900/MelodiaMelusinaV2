# Melodia lookdev candidate handoff — 2026-08-01

## 2026-08-01 project-wide promotion correction (latest)

The deprecated M_PP_StorybookOutline_AdvancedMath_Candidate is not the
project-wide authority and remains unassigned. Its reviewed math was moved into
the existing project-wide M_PP_StorybookOutline_FoliageSafe_Candidate,
preserving that material's viewport/buffer correction and existing asset
references. The foliage-safe master now compiles at 170 pixel instructions and
validates with zero issues.

All existing outline instances now parent the foliage-safe master and carry
bounded Gameplay, Narrative, or Portfolio settings. Corrupt scalar overrides
and orphan RefractionDepthBias values were removed. The shared live
MI_PP_StorybookOutline uses the quiet Gameplay settings.

The actual PPV grade authority was also corrected. The active stack referenced
/Game/_PROJECT/04_Materials/PostProcess/M_PP_MeluColorGrade, not the duplicate
under /Game/Melodia. The active root material now contains the 24-expression
luminance-preserving graph and validates cleanly at 191 pixel instructions.
Existing grade profile instances were reparented to that root master.

The current PPV_NikkiDream stack is now:

- weight 1.0: /Game/EnvSandbox/Materials/PostProcess/Candidates/Profiles/MI_StorybookOutline_GameplayStandard
- weight 0.69: /Game/Melodia/_PROJECT/04_Materials/PostProcess/Candidates/Profiles/MI_MeluColorGrade_GameplayStandard

ZenForestTest was deliberately left unsaved because it already contained
owner-authored dirty map work. The PPV change is live in memory; save the level
when that in-flight environment work is ready. The canonical setup script now
selects the Gameplay grade instance first, falls back to the active root grade
master, and preserves the established 1.0/0.69 blend weights.

## 2026-08-01 late graph-only correction (superseded by promotion above)

This pass changed **material graphs only**. No PPV, level, UDS actor, lookdev
director, or live material-instance assignment was changed. The six existing
profile instances were restored to their exact pre-pass override sets after an
initial out-of-scope tuning attempt:

- Starry profiles: `BrushEnabled`, `BrushStrength`, `NebulaIntensity`,
  legacy `Opacity`, and `StarIntensity` only.
- Grade profiles: `VignetteBaseIntensity` and `VignetteFalloff` only.

The graph work that is now real and saved:

- `/Game/EnvSandbox/Materials/PostProcess/Candidates/M_PP_StorybookOutline_AdvancedMath_Candidate`
  is a new, unassigned fork of the approved foliage-safe candidate. It preserves
  the corrected viewport-to-buffer transform and valid-view-rect clamp, adds
  eight-direction depth/normal sampling, one-sided foreground contours,
  derivative-width anti-aliasing, smooth edge-signal combination, and the
  TwoSidedFoliage suppression lane. It compiles at 170 pixel instructions and
  validates with zero issues. The working live foliage-safe outline was not
  edited or reparented.
- `/Game/Melodia/_PROJECT/04_Materials/PostProcess/Candidates/M_PP_MeluColorGrade_LookdevCandidate`
  is no longer the old 11-node duplicate. Its 24-expression graph now performs
  luminance-preserving saturation/contrast, shadow and highlight shaping,
  normalized split-tone tinting, a bounded spectral phase derived from the
  Universal Master's Dream Rim language, derivative-soft tonal/vignette
  transitions, and capped palette/audio modulation. It compiles at 191 pixel
  instructions and validates with zero issues.
- `/Game/EnvSandbox/Materials/Candidates/Lookdev/M_Melodia_StarryNight_UDS_Candidate`
  is no longer a duplicate of the authored 14-node sky. Its 32-expression
  additive overlay graph now consumes the dedicated sky MPC, combines
  derivative-AA texture stars with phase-offset analytic SDF glints, uses
  anti-aliased elliptical SDF brush strokes for painterly structure, preserves
  a quiet horizon for UDS fog, and gates visibility through night, cloud,
  weather, and look-intensity channels. It compiles at 261 pixel instructions
  and validates with zero issues.

The Universal Master comparison is now explicit: `MF_NikkiDreamGrade` supplies
the tonal hierarchy and normalized dream palette; `DreamRimSpectral` supplies
the bounded cosine palette phase; the Starry candidate adopts the same
phase-offset/sparse-reactivity rule instead of a synchronized global pulse.
The older `MF_Impressionist_Impasto` and `MF_Impressionist_Temporal` assets were
not edited; their duplicated inputs/outputs make them unsuitable as the shared
source until they receive a separate function-integrity cleanup.

The Starry graph is **not yet placed or attached to UDS**. UDS remains the sole
time/weather/cloud/fog/light authority. Promotion requires a separate,
authorized actor/UDS integration pass and matched-camera motion/capture A/B.

## What changed

All work is candidate-only and unassigned. `PPV_NikkiDream` still uses the existing source materials. `MPC_PPBlending` and UDS runtime settings were not changed.

- `M_PP_StorybookOutline_LookdevCandidate` is a parameter-tuning duplicate of the corrected live master. It does **not** contain the planned eight-direction algorithm and remains useful only for tuning comparisons.
- `M_PP_MeluColorGrade_LookdevCandidate` replaces direct global emissive multiplication with a luminance-preserving grade: restrained shadow/highlight split, capped rhythm palette lift, midtone saturation preservation, and a small bounded emissive response. It compiled successfully.
- Each PPV candidate has `GameplayStandard`, `Narrative`, and `PortfolioHero` material instances. Gameplay uses restrained settings; Hero is intentionally capture-only.
- `M_Melodia_StarryNight_UDS_Candidate` and three profile instances were created from the authored Starry Night material. No UDS sky material was swapped.
- `MPC_MelodiaSkyLookdev_Candidate` contains neutral visual-only channels: `NightAmount`, `CloudOcclusion`, `MoonIntensity`, `WeatherAttenuation`, `WindPhase`, `SkyLookIntensity`, and `PortfolioHero`.
- `BP_MelodiaLookdevDirector_Candidate` is an unplaced profile registry/director candidate with a clean compile. Its `ProfileIndex` maps 0/1/2 to Gameplay Standard, Narrative, and Portfolio Hero; it stores the outline/grade profile assets and the dedicated sky MPC. It deliberately has no PPV or UDS write path yet.

## Claude handoff

Claude owns PPV attachment and `MPC_PPBlending`. When ready for live A/B, attach a matching outline and color-grade candidate pair to a temporary/candidate PPV only. Do not replace the two current `PPV_NikkiDream` blendables.

The sky MPC is separate from `MPC_PPBlending`. An eventual UDS adapter should write clamped night/weather/moon/wind values to this MPC only; UDS remains the authority for weather, fog, cloud, solar, lunar, and skylight simulation.

## A/B rig — built and verified (Claude, 2026-08-01)

`Content/Python/setup_ppv_candidate_ab.py` spawns `PPV_NikkiDream_Candidate` (unbound, priority 25)
carrying only the candidate blendable pair. `PPV_NikkiDream` is untouched — its blendables were not
replaced, per the handoff above. Currently placed in `ZenForestTest`, left in `source` mode, level saved.

```
import setup_ppv_candidate_ab as ab
ab.mode("candidate")                          # candidates on, live grade off
ab.mode("candidate", profile="PortfolioHero") # profiles: GameplayStandard | Narrative | PortfolioHero
ab.mode("source")                             # back to the live grade
ab.status()
```

Exactly one volume is enabled at a time, and that is deliberate: **weighted blendables accumulate
across overlapping post-process volumes**, so leaving both on stacks two outline passes and two
grades and compares nothing. The candidate volume overrides no native settings (bloom/vignette/
grain/fringe), so those fall through from the live volume and the comparison isolates the pair
actually under review. All three modes and both profile swaps were verified live before the editor
was closed for a rebuild.

### Read before judging the outline candidate

`M_PP_StorybookOutline_LookdevCandidate` is, as of 11:36, a byte-identical duplicate of the fixed
master — same Custom HLSL (including comments), same `MaterialExpressionGuid`, same 29 expressions,
same 4-tap L/R/U/D cross. The eight-direction sampling, brush taper, and local-depth normalization
described in "What changed" are **not present in the asset**; the code write appears not to have
landed. The grade candidate and all profile instances *are* real, distinct work.

So an A/B run right now compares **parameter tuning**, not a new edge algorithm. Worth re-running
once the outline code actually lands.

### Verified mathematical outline candidate v2 — 2026-08-01

`/Game/EnvSandbox/Materials/PostProcess/Candidates/M_PP_StorybookOutline_MathCandidate_v2` is the
separate algorithm candidate. Its saved Custom HLSL was re-exported after writing and contains the
`MELodia_MATH_CANDIDATE_V2` marker, buffer-space texel offsets, valid-view-rect clamping, and all
four diagonal taps in addition to the axial taps. It uses a max (Chebyshev) neighbourhood for both
depth and center-normal discontinuities, so signals never accumulate into a broad ink fill. It
retains the corrected live material's UDS tint, stencil, falloff, and vine contracts.

It compiled with 91 pixel-shader instructions and validated with zero material issues. Its only
instance is the unassigned, quiet
`/Game/EnvSandbox/Materials/PostProcess/Candidates/Profiles/MI_StorybookOutline_MathCandidate_v2_Standard`;
it has `EdgeStrength=0.62`, `OutlineWidth=1`, `FalloffStart=2200`, `FalloffEnd=7000`, and both UDS
tint and vines disabled. No PPV, map, UDS asset, live outline, or `MPC_PPBlending` reference changed.

Lookdev note: `MI_StorybookOutline_PortfolioHero` raises `FalloffEnd` to 9500 (from 8000), which
extends outlining further into the distance and so pushes *more* foliage into the ink — the opposite
direction from the known dense-foliage blowout. Hero will show that issue most strongly of the three.

## Required visual sign-off

Compare source vs candidate at fixed 16:9 Zen Forest cameras during morning, sunset, clear night, and cloudy night. Approve only if outlines remain stable in camera motion, UI contrast stays intact, no far halo appears, and the candidate does not fight UDS fog/cloud transitions. Record Standard and Hero GPU cost before promotion.
# Final session addendum — authoritative graph polish

The final pass updated the real active assets, not deprecated forks or only
their instances:

- `M_PP_MeluColorGrade` now adds a bounded painterly vignette blend. Four
  view-rect-clamped taps soften only the vignette edge; blurred chroma is
  recombined with the graded luminance before a subtle DreamTint pigment phase.
  Defaults are restrained and the material validates clean at 197 PS
  instructions.
- `M_Master_Toon_Landscape_HeightBlend` now uses the physically meaningful
  `MacroWorldSizeCm` control. The old authored frequency was converted exactly,
  including SakuraGarden and Zen Raked Sand overrides, so the migration is not
  an art-direction retune.
- `MF_UniversalMacroDetail` was audited and is currently metadata-only (zero
  expressions, zero inputs, zero outputs, zero references). It must not be cited
  as a completed shared macro implementation. A future reusable hybrid
  procedural/texture function remains candidate work.
- The final dirty-package audit reports only `ZenForestTest`; it was not saved.
