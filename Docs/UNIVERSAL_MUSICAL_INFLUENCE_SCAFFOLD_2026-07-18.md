# UniversalMusicalInfluence — Scaffolding Notes (2026-07-18)

Working name for the project-wide mechanic: **the world reacts to the music**, subtly,
everywhere, not just on Melusina. This doc names the layers that already exist, what's
newly wired, and the extension points left for incremental follow-up. Nothing here
invents new material families — everything routes through `M_Master_Toon_Universal`'s
existing exposed params or the existing `MPC_Melodia_Palette` collection.

## Layer 1 — Signal source (done, pre-existing)
`UMelodiaRhythmReactivitySubsystem` (world subsystem) already collapses gameplay/audio
events (Quartz beat, command grade, combo, crescendo, break, victory, enemy tension)
into one `FMelodiaRhythmReactivitySignal` and calls `Publish()` on every change/tick.
This is the single source of truth — nothing downstream should read Quartz directly.

## Layer 2 — Global broadcast via MPC (done, already project-wide)
`Publish()` writes 9 named scalars to `MPC_Melodia_Palette`
(BeatPulse, BeatPhase, BeatIntensity, RhythmPulse, GlobalSparkleIntensity, PaletteShift,
GlobalEmissiveBoost, ProximityGlow, TemporalJitter). Because it's a Material Parameter
Collection, **any material in the level can already sample these today** by adding a
`CollectionParameter` node pointed at `MPC_Melodia_Palette` — no C++/opt-in needed. This
is the cheapest, safest "environment reacts to music" hook: whoever authors an
environment material chooses to read a low-weight collection param (e.g. blend
`GlobalEmissiveBoost` at 2-5% into an emissive channel). Kept deliberately subtle by
convention — small weights, not new VFX.

## Layer 3 — Per-actor dynamic-material opt-in (done, generic, not Melusina-specific)
`RegisterReactiveMeshComponent(UPrimitiveComponent*)` creates MIDs on every material
slot of whatever mesh component you pass it and adds them to
`ReactiveDynamicMaterials`. `PublishToReactiveMaterials()` then pushes
DreamPulseAmp/Iridescence/TemporalStrength/ParallaxStrength onto every registered MID
each publish — again, safe no-ops on materials that don't expose those params. **This
function was written generically on purpose** — it is not Melusina-only. Any actor
(a prop, a foliage instance, a set piece) can call
`UMelodiaRhythmReactivitySubsystem::Get(this)->RegisterReactiveMeshComponent(MyMesh)`
in BeginPlay to opt in. That's the whole "UniversalMusicalInfluence" mechanic at the
gameplay layer — it already scales to the world, it's just not called anywhere but
Melusina yet.

Confirmed today: cold build for the `Get()` static helper succeeded (see build log,
`Result: Succeeded`). Melusina's own `RegisterReactiveMeshComponent(GetMesh())`
BeginPlay wiring is the next concrete step once the editor/Monolith bridge is back up.

## Layer 4 — TouchDesigner bridge (exists for battle events, not yet for continuous music signal)
`_TouchDesigner/grandmaster_melodia/scripts/wire_battle_osc.py` already sets up an OSC
In CHOP on port 9000 receiving discrete battle events from a UE-side `battle_osc.py`
sender (14 mapped routes). That's the established UE→TD channel — reuse it rather than
building a second one. Not yet built: a *continuous* stream of the same
`FMelodiaRhythmReactivitySignal` fields (BeatPulse/BeatPhase in particular) sent over
that channel so TD-side geometry/shader work can react to the beat clock the same way
UE materials do. This is the natural Phase 2 for the TD side of
UniversalMusicalInfluence — flagged, not started.

## What's explicitly NOT being done here
No new material families, no editing `M_Master_Toon_Universal`'s shared graph directly,
no exhaustive per-level wiring pass. Per direction, this stays scaffolding: the generic
mechanism exists and is documented; adoption (which props/levels opt in, how strong)
is a deliberate, incremental follow-up so the effect stays subtle rather than overdone.

## Next concrete steps (in order)
1. Wire `RegisterReactiveMeshComponent(GetMesh())` into `BP_Melusina` BeginPlay (blocked
   on editor relaunch after today's cold build).
2. Pick 1-2 environment set pieces (not everything) to opt in via the same call, at low
   published weights, as the first real "world reacts to music" proof point.
3. Extend `battle_osc.py`/`wire_battle_osc.py` to stream BeatPulse/BeatPhase
   continuously for the TouchDesigner side, reusing port 9000.
