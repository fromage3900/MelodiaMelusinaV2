# Melodia water system test matrix

Status: source/UHT, authored native-Water replay, force routing, Niagara
contact, underwater ownership, and focused editor teardown gates passed on
2026-08-09. The current editor exposes Monolith automation on port 9316.
The authored validation map is project-owned and is not a gameplay map.

## 2026-08-09 validation evidence

- Targeted editor UBT/UHT relink passed after the ProcessEvent safety fix; the
  editor reports zero current C++ compile errors. The project build-error
  panel still contains unrelated pre-existing content/PCG entries and was not
  modified by this lane.
- Authored harness: `/Game/MelodiaIntegration/Water/Validation/L_WaterV10_NativeValidation`
  contains `MelodiaWaterV10`, its native `WaterZone_0`, and the project-owned
  `BP_MelodiaWaterSimulationZone` with `ShallowWaterSim` and `WaveFoamSim`
  references.
- Native query replay: `pie_smoke_5_032936` returned body identity
  `MelodiaWaterV10`, body/zone indices `0/0`, native surface normal and
  velocity, and a valid underwater sample with positive immersion/depth.
  Runtime limits observed in PIE were 6 dynamic forces, 3 impulse forces, and
  a 1024 shallow-water render target.
- Post-recovery smoke: `pie_smoke_1_034326` completed cleanly with zero
  `Blueprint Runtime Error`, `Accessed None`, `Fatal error`,
  `Ensure condition failed`, or `Unhandled Exception` matches.
- Native impulse gate: `pie_smoke_6_034835` reported
  `ImpulseForcesThisWindow=3` against the native limit of 3, with
  `ShallowWaterSim` and `WaveFoamSim` bound, and no runtime errors.
- Native dynamic gate: `pie_smoke_8_034940` successfully invoked the typed
  `HandleFluidImpulse` path and reported `DynamicForcesThisWindow=1`; the
  session remained clean.
- Niagara contact gate: `pie_smoke_9_035022` resolved
  `/Game/EnvSandbox/Water/v10/NDC_MelodiaWaterContact` and reported six
  bounded writes within the 60/sec bridge budget.
- Underwater ownership gate: `pie_smoke_10_035040` resolved
  `M_Water_Underwater_Post_v10` on the native Water Body component and body
  index `0`; teardown remained clean.
- Performance artifacts were written for the recovery, force, Niagara, and
  underwater sessions under `Saved/Profiling/`, including
  `pie_pie_smoke_1_034326.csv/.utrace`,
  `pie_pie_smoke_6_034835.csv/.utrace`,
  `pie_pie_smoke_8_034940.csv/.utrace`,
  `pie_pie_smoke_9_035022.csv/.utrace`, and
  `pie_pie_smoke_10_035040.csv/.utrace`.
- Safety history: an earlier explicit Python USTRUCT force replay
  (`pie_smoke_6_033023`) exposed an access violation at the raw Blueprint
  ProcessEvent boundary. The project-owned adapter now uses an aligned,
  owning parameter frame sized from `UFunction::ParmsSize` and initialized/
  destroyed through reflected properties. The rebuilt editor passed all
  subsequent impulse and dynamic gates above.
- Material Render Studio: the three v10 water instances rendered through
  `L_MaterialPreview_Studio` with distinct byte sizes/luminance and no dirty
  map packages left behind. One unrelated water material instance remains
  dirty from concurrent portfolio work and was intentionally not saved. Final
  stills are in
  `Saved/Portfolio/Renders/Materials/Retake/`.
- Remaining promotion work: the authored map validates the CPU/native bridge
  and Data Channel contract. Niagara Fluids shallow-water/2D FLIP/3D FLIP
  systems still require a promoted hero-zone replay and should not be inferred
  from the contact bridge gate.

## Contract tests

| Case | Input | Expected result |
| --- | --- | --- |
| Native surface query | Melusina above a Water Body | `bValid`, `bSurfaceValid`, surface identity, normal, velocity, depth, and sample time are populated. |
| Native underwater query | Melusina below the surface | `bUnderwater` and immersion depth are true/positive; water level comes from the query. |
| Exclusion volume | Query inside a Water Body exclusion | The excluded body is skipped; no false surface authority is published. |
| No provider | Query with no registered Water Body | Traversal may use its explicit fallback, but the sample remains non-authoritative. |
| Entry/exit | Surface crossing with hysteresis | One `SurfaceEntry`/`SurfaceExit`, one Niagara contact, one fluid impulse per transition. |
| Water identity | Two nearby bodies | Ripple bridge accepts only the matching `WaterBodyId` unless explicitly configured otherwise. |
| Lifecycle | Actor destroyed or map transitions | Cached sample is cleared; dynamic bridges unsubscribe; no stale event consumer remains. |

## Presentation tests

| Consumer | Acceptance criteria |
| --- | --- |
| v9 surface bridge | `RippleCenterA/B/C`, `RippleImpulseA/B/C`, and bioluminescence impulse update on contact, then decay monotonically. |
| Niagara bridge | Ripple/splash systems use pooled spawn; state-only events do not spawn; user radius, intensity, immersion, and impact velocity match the packet. |
| Underwater post | Blend follows immersion with hysteresis; surface state returns the blend to zero; no camera-manager blendable leak across transitions. |
| Audio seam | Entry, swim, dive, impact, and re-emergence resolve profile IDs and respect per-body/event concurrency caps when MetaSounds are assigned. |

## Fluid-zone tests

1. Attach `UMelodiaWaterFluidZoneComponent` to a single authored pond or
   grotto Water Body with `WaterBodyId` set explicitly.
2. Replay one low-intensity ripple, one character entry, and one high-velocity
   impact at known coordinates.
3. Confirm the out-of-bounds impulse is ignored, the in-bounds impulse creates
   a bounded peak, and the peak/energy decay without numerical growth.
4. Confirm a higher requested tier downgrades to the configured zone tier when
   allowed, and is ignored when downgrade is disabled.
5. Capture `stat unit`, GPU timing, Niagara debugger, and a fixed replay hash.

The current reference defaults are deliberately bounded: 32x32 cells, 30 Hz,
two substeps per frame, and a finite local tile. Promotion requires measured
targets from the research brief, not just a good-looking editor preview.

## Promotion gates

- Tier 0/1 fallback remains visually acceptable with the fluid zone disabled.
- Tier 2 must produce a visibly different wake/surface response in a focused
  zone and stay within the budget on the target platform.
- Niagara Fluids promotion remains gated until the same replay can compare its
  Shallow Water and 2D FLIP output against the native reference zone. No global
  plugin toggle or engine-content mutation was performed during this lane.
- 3D FLIP is approved only for a hero shot or a gameplay interaction whose
  payoff is visible and measurable.
- The Material Render Studio capture must show the same water profile in calm,
  contact, underwater, and bioluminescent states.
