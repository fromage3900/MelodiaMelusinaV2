# Melodia Water System Expansion Research

Status: active implementation brief for UE 5.8; research refreshed 2026-08-09.

This document turns the water audit into a game-wide system direction. It is
intentionally written around reusable runtime contracts rather than one-off
effects.

## Current truth

- `M_Water_Master_Grand_v9` already contains the material-side language for
  ripples, proximity foam, and bioluminescence, but it is not yet driven by a
  runtime water authority.
- `UMelodiaTraversalComponent` can enter swimming and diving states, but its
  previous water height was a local actor-Z fallback, not a Water Body query.
- The new `UMelodiaWaterInteractionSubsystem` and
  `MelodiaWaterInteractionTypes.h` establish a typed event/sample seam.
  Events are useful immediately; fallback samples remain explicitly
  non-authoritative when a Water Body query is unavailable.
- `UMelodiaWaterNiagaraBridgeComponent` is now the reusable near-field
  consumer: it subscribes to the bus, filters proximity-only events, uses
  pooled spawning, and writes normalized user parameters.
- `UMelodiaWaterUnderwaterPostProcessComponent` now creates a dynamic v9
  underwater material and submits it through the local player camera manager;
  blend weight and raw immersion depth come from the cached Water Body sample.
- `UMelodiaWaterRippleMaterialBridgeComponent` now implements the v9 three-slot
  ripple ring and decaying bioluminescence impulse writes for water-surface
  actors. The native Water query now auto-attaches it to the selected
  `AWaterBody` at runtime, and the bridge consumes the Water Body component's
  managed material instances in addition to ordinary actor mesh materials.
- `FMelodiaWaterFluidImpulse` and the bounded subsystem replay buffer now give
  Shallow Water/2D FLIP/hero-FLIP adapters a deterministic escalation seam;
  contact-driven impulses are retained without enabling the beta Fluids plugin.
- `NiagaraFluids` is currently disabled in the project. UE 5.8 documents it as
  a Beta plugin and requires an editor restart after enabling it. Do not make
  the whole game depend on it until the tier-2 prototype is measured.
- `UMelodiaWaterFluidZoneComponent` is now an opt-in CPU reference adapter for
  the tier-2 decision. It uses a bounded 32x32 default height field, fixed
  30 Hz stepping, two-substep frame cap, Water Body filtering, radial impulse
  injection, damped wave propagation, and material telemetry parameters. It
  is not enabled globally and does not replace the v9 analytic fallback.

## UE 5.8 capability map

The native Water system is the gameplay authority: query water surface state,
water body identity, depth, and interaction context from one place. Niagara is
the presentation and simulation consumer. The UE 5.8 Niagara Fluids stack
supports 2D game-oriented templates, 3D cinematic/hero templates, grid-based
gas, and hybrid particle/grid liquid simulation. UE documentation also calls
out Shallow Water for pools, wakes, and simple object interactions, 2D FLIP for
splash-oriented interaction, and 3D FLIP for expensive complex interactions.

Primary references:

- [Water System](https://dev.epicgames.com/documentation/en-us/unreal-engine/water-system-in-unreal-engine?lang=en-US)
- [Water Body Actors](https://dev.epicgames.com/documentation/en-us/unreal-engine/water-body-actors-in-unreal-engine)
- [Water Surface Info query](https://dev.epicgames.com/documentation/en-us/unreal-engine/BlueprintAPI/WaterBody/GetWaterSurfaceInfoatLocation?lang=en-US)
- [Water subsystem API](https://dev.epicgames.com/documentation/en-us/unreal-engine/API/Plugins/Water/UWaterSubsystem?lang=en-US)
- [Niagara Fluids overview](https://dev.epicgames.com/documentation/unreal-engine/niagara-fluids-in-unreal-engine?lang=en-US)
- [Fluid simulation overview](https://dev.epicgames.com/documentation/en-us/unreal-engine/fluid-simulation-in-unreal-engine---overview)
- [Niagara Fluids reference](https://dev.epicgames.com/documentation/en-us/unreal-engine/niagara-fluids-reference-guide)
- [UE 5.8 release notes](https://dev.epicgames.com/documentation/en-us/unreal-engine/unreal-engine-5-8-release-notes)

### 2026-08-09 research refresh

- Epic's current UE 5.8 fluid overview explicitly separates the use cases:
  Shallow Water is a height-field displacement model for pools, wakes, and
  simple object interactions; 2D FLIP is intended for splash-oriented effects
  rather than pools; 3D FLIP covers complex liquid interactions at a higher
  cost. This validates the current promotion ladder rather than a single
  universal solver.
- Epic still labels the fluid toolset Beta and warns that fluid scenes can be
  graphically intensive and may cause GPU crashes on Windows. The practical
  consequence is to keep the project fallback-first, measure the local zone,
  and bake hero/cinematic results where runtime simulation is not justified.
- The UE 5.8 Water Body query API documents the same closest-location query
  used by the native adapter. That keeps surface identity, depth, normal,
  velocity, and immersion in one authoritative sample before events fan out.
- The Niagara API reference exposes Niagara Data Channels as a communication
  path between Niagara systems and game code. That is the preferred future
  bridge for a measured solver output; the current source contract remains
  delegate-based so it works without requiring a new editor-authored channel.
- Recent primary bioluminescence work continues to support shear/mechanical
  stress as the useful visual driver, with concentration/profile variation as
  an art control. The current response therefore uses decaying impulse and
  surface-stress proxies, not a binary near-player glow.

Decision record: keep `NiagaraFluids` disabled while the new fluid zone is a
reference/profiling path; promote Shallow Water only for authored active zones;
add 2D FLIP for splash-heavy hero zones; reserve 3D FLIP for authored hero
shots or a measured gameplay payoff.

Research references for the high-end direction:

- [Generalized shallow water simulation](https://research.nvidia.com/labs/prl/shallow-water-simulation/)
- [Water Surface Wavelets](https://visualcomputing.ist.ac.at/publications/2018/WSW/)
- [Real-time large-bodies water with small details](https://diglib.eg.org/bitstreams/091a537c-9e50-4e89-a784-e93b06c30ddc/download)
- [Mechanosensitive dinoflagellate bioluminescence](https://www.nature.com/articles/s41526-017-0016-x)
- [Recent flow/mechanical-stress bioluminescence study](https://www.nature.com/articles/s41598-025-28796-8)

## Runtime architecture

```text
Water Body / query provider
        |
        v
FMelodiaWaterSample -----> material/post-process state
        |
        +--> FMelodiaWaterContactEvent --> Niagara event handler
        |                                  --> shallow-water impulse
        |                                  --> MetaSound parameters
        |                                  --> gameplay/perception hooks
        |
        +--> replay/telemetry/performance capture
```

The contract is deliberately consumer-neutral:

- `bValid` means a provider answered.
- `bSurfaceValid` means surface location/normal are authoritative.
- `DistanceToSurface`, `Immersion`, `WaterDepth`, and `SurfaceVelocity` support
  both underwater post effects and hydrodynamic response.
- `EventType`, `ImpactVelocity`, `ImpulseVector`, `Radius`, `Intensity`,
  `Duration`, and profile IDs are sufficient to drive Niagara, a material MPC,
  a custom primitive-data write, MetaSounds, or a fluid impulse.

This prevents the common failure mode where traversal, VFX, material, and
audio each invent a slightly different definition of “in water.”

## Tiered effect strategy

### Tier 0: universal analytic water response

Always available on every water surface, including low-end and distant water.

- v9 ripple field and normal response.
- Proximity foam from authoritative distance-to-surface and a signed contact
  impulse.
- Low-frequency tiling noise for broad breakup; high-frequency noise only for
  hero instances.
- WPO kept small and frequency-limited; never use it to create collision truth.
- One event can write a bounded ring-buffer of ripple centers/impulses.

### Tier 1: pooled Niagara interaction VFX

The default near-field presentation layer.

- A single pooled Niagara system receives the normalized event stream.
- GPU particles cover droplets, splash crowns, bubbles, and surface motes.
- CPU-side spawning is bounded by distance, event intensity, and concurrency.
- Niagara Collision Query can add scene/depth-aware behavior where helpful;
  gameplay still owns the event and water-body identity.
- Bioluminescence is a delayed, decaying response rather than an always-on
  emissive mask.

### Tier 2: local Shallow Water / 2D FLIP

Use for authored ponds, rivers, grotto chambers, and a small number of active
interaction zones.

- Shallow Water: broad surface displacement, wakes, eddies, shoreline response.
- 2D FLIP: localized splashes and strong contact bursts.
- Feed both from the same event packet; do not let the solver become gameplay
  authority.
- Update only active tiles around characters, boats, creatures, or scripted
  events; freeze or bake distant tiles.
- The current CPU zone is a correctness/profiling reference, not the final
  GPU implementation. Its fixed grid and bounded step budget make a future
  Niagara Grid 2D or Shallow Water replacement comparable in replay tests.

### Tier 3: hero 3D FLIP

Reserve for a hero shot, set piece, or portfolio capture. It is not the global
default. Bake or cache the result when the scene is authored; runtime 3D FLIP
must earn its cost through a visible gameplay or narrative payoff.

## Bioluminescence model

Dinoflagellate research supports a mechanosensitive response: fluid shear and
velocity gradients are more meaningful drivers than raw “player is nearby.”
The practical shader signal should therefore be:

```text
BioImpulse = saturate(
    SurfaceShear * ShearWeight
  + ContactImpulse * ContactWeight
  + WakeCurvature * CurvatureWeight
)
BioResponse = exp(-Age / DecaySeconds) * smoothstep(Threshold, 1, BioImpulse)
```

Art direction can layer a species/profile color, seeded variation, and a short
refractory cooldown so repeated movement creates rhythm instead of a flat
glow. The surface material should receive this through bounded event/ripple
data, while underwater post-process receives only the view-space aggregate and
depth-aware attenuation.

## Underwater and audio expansion

Underwater is a stateful presentation stack, not a single tint:

1. Water query determines immersion and surface distance.
2. Post-process blends color absorption, contrast rolloff, suspended particulate
   density, caustic motion, and bioluminescent scatter.
3. Niagara adds bubbles and micro-particles only while immersion and velocity
   justify them.
4. MetaSounds layer surface movement, muffled transients, bubbles, pressure,
   and environment-specific resonance.
5. Sound concurrency is bounded by water body and event class so a fast swimmer
   cannot turn every ripple into a separate voice.

The sound design target is not literal “water noise.” It is a readable acoustic
state machine: entry, movement, sustained swim, dive, breath pressure, contact,
and re-emergence.

## Text-injection and orchestration pipeline

The professional pipeline should treat text as a schema input, not as a hidden
implementation layer:

1. Author a versioned water profile in text/data form: body ID, effect tier,
   query flags, material defaults, Niagara system references, audio profile,
   bioluminescence curve, and performance caps.
2. Validate names, ranges, references, and tier compatibility before injection.
3. Inject only typed properties and delegate bindings into Blueprint/asset
   graphs; never inject opaque free-form graph edits without a manifest.
4. Generate a deterministic manifest containing source text hash, target asset,
   expected nodes/parameters, and a rollback-safe duplicate path.
5. Compile, run a no-map unit check, then run a water interaction replay on the
   focused map.
6. Capture a Material Render Studio comparison and a short gameplay capture.
7. Promote the profile only when visual, performance, and runtime-reference
   checks pass.

Every text-injected asset should expose an “injection provenance” comment or
metadata field so future changes can distinguish authored work from generated
wiring. This is the key difference between a portfolio prototype and a
maintainable game-wide system.

## Starting performance budgets

These are validation targets, not assumed guarantees:

| Tier | Scope | CPU target | GPU target | Hard cap |
| --- | --- | ---: | ---: | --- |
| 0 | Universal analytic response | < 0.10 ms | < 0.50 ms | no unbounded ripple history |
| 1 | Near-field Niagara VFX | < 0.25 ms | < 1.00 ms | pooled emitters and bounded events |
| 2 | One active 2D fluid tile | < 0.50 ms | < 2.00 ms | fixed update rate and tile budget |
| 3 | Hero 3D FLIP | measured per scene | measured per scene | authored/baked or explicitly justified |

Measure on the target platform with `stat Niagara`, GPU timings, Niagara
debugger captures, and a deterministic traversal replay. Never promote a
higher tier because it looks better in an editor-only still.

## Next execution order

1. Let the first native query auto-attach
   `UMelodiaWaterRippleMaterialBridgeComponent` to the authored Celestial Pond
   and hero Water Bodies, then validate v9 parameters in a replay. Static or
   custom non-Water-Body surfaces still require explicit component attachment.
2. Assign/validate one pooled Niagara contact system and one MetaSound cue in
   the editor; capture the first gameplay interaction replay.
3. Prototype one Shallow Water tile in the Celestial Pond and one 2D FLIP
   splash test in a hero grotto. Use `UMelodiaWaterFluidZoneComponent` first
   to validate the impulse profile, zone bounds, and measurable response.
4. Only then enable `NiagaraFluids`, restart the editor, and measure the tier-2
   templates against the existing Tier 0/1 fallback.
5. Add replay-based tests, map-transition cleanup, and a Render Studio portfolio
   capture for each promoted water profile.

## Verification status

- Source contract: statically reviewed and patched.
- Traversal water events: wired for swim/dive start/stop.
- Dive breath/auto-surface early-return bug: corrected.
- Native Water Body query adapter: implemented against the installed UE 5.8
  `WaterBodyManager`/`TryQueryWaterInfoClosestToWorldLocation` API.
- Niagara bridge component: implemented with pooled contact spawning and
  normalized user-parameter writes.
- Underwater post-process bridge: implemented with camera-manager blendable
  submission and v9 `UnderwaterBlend`/`UnderwaterDepth` writes.
- v9 ripple material bridge: implemented with three-slot shifting, decay, and
  `RippleCenterA/B/C` plus `RippleImpulseA/B/C` writes; native Water Body
  queries auto-attach it and it can write through managed Water Body MIDs.
- Tiered fluid impulse contract: implemented with `ShallowWater2D` default
  requests, bounded 64-event replay storage, and an `OnFluidImpulse` delegate.
- Tier-2 reference zone: implemented with fixed-step bounded height-field
  stepping, radial contact injection, Water Body filtering, telemetry, and
  graceful request downgrading; not yet attached to an authored map zone.
- Unreal compile/UHT: passed on the `BS_GodFile` Win64 Development target;
  `BS_GodFile.exe` linked successfully. Editor automation/replay remains
  pending because the current editor process exposes no Monolith port.
- Niagara Fluids assets and Water Body query adapter: not yet changed.
