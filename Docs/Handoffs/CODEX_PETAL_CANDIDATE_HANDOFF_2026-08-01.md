# Petal candidate handoff — 2026-08-01

## Safe candidate assets

- `/Game/EnvSandbox/VFX/Candidates/Petals/NS_SakuraPetals_v3_Candidate`
  - Derived from `NS_SakuraPetals_v2`; no source system was replaced.
  - The `Petals` emitter now generates `DeathEvent` events.
  - `EM_PondRipple` and `EM_PetalPile` are event-only receivers: their local Shape/Box spawn locations were removed, so landings resolve from the source event payload instead of an additional local spawn region.
  - Niagara validation: valid, no errors or warnings.
- `/Game/EnvSandbox/VFX/Candidates/Petals/NS_SakuraPetalPiles_Candidate`
  - Derived from `NS_SakuraGroundPetals`.
  - User scalars: `PileSpawnRate` (24), `PileRadius` (700), `PileScaleMin` (1.6), `PileScaleMax` (2.6), `PileLifetimeMin` (22), `PileLifetimeMax` (45).
  - The spawn rate, mesh scale range, lifetime range, and shape radius bindings are exposed for stackable authored instances. Keep each placed instance as an independent pile; do not use it to persist gameplay state.
- `/Game/EnvSandbox/VFX/Candidates/Petals/NS_SurrealSakuraGust_Candidate`
  - Derived from `NS_SakuraPetalGust`; candidate-only mesh pass uses `/Game/Melodia/Meshes/VFX/SM_SakuraPetal`.
  - User scalars: `GustParticleCount` (48), `GustNoiseStrength` (32).
  - Compiles cleanly. The automated preview scene renders both this mesh system and the unmodified mesh-pile source near-black, so preview PNGs are not visual proof. Review it in the target level before promotion.
- `/Game/EnvSandbox/VFX/Candidates/Materials/M_NiagaraPetal_Loop_v2_Candidate`
  - The actual gust material candidate. It is a clean duplicate/rebuild of the base petal material with a subtle `ParticleRelativeTime` lifecycle shimmer; it is assigned only to `NS_SurrealSakuraGust_Candidate`.
  - It remains a candidate and does not replace `M_SakuraPetal` or `MI_Niagara_Petal_Instance`.
- `/Game/EnvSandbox/VFX/Candidates/Materials/M_NiagaraPetal_Loop_Candidate`
  - Initial unpromoted duplicate retained as a non-referenced recovery copy.
- `/Game/EnvSandbox/VFX/Candidates/Materials/Functions/MF_MelodiaPetalLifecycle_Candidate`
  - Shared candidate-only loop mask. Inputs: `NormalizedAge`, `LoopSpeed`, `PhaseOffset`, `FlutterStrength`, `PresentationPulse`; output: `Lifecycle`.
  - Presentation-only; it does not invent a rhythm clock or write gameplay state.

## Project-wide musical cohesion

Use existing `/Game/Melodia/_PROJECT/04_Materials/MPC_Melodia_Palette` when the material loop is wired into a promoted material. Its presentation signals are `BeatPulse`, `BeatPhase`, `BeatIntensity`, `RhythmPulse`, `GlobalSparkleIntensity`, `PaletteShift`, `GlobalEmissiveBoost`, and cozy channels including `PetalFallIntensity` and `DreamRipple`.

`UMelodiaMusicClockSubsystem` remains the sole visual beat authority. It is backed by Harmonix/Quartz timing and has no fabricated wall-clock fallback. Petal effects may read these signals only as capped, optional visual modulation; they must not influence encounters, collision, quest state, damage, or turn flow.

## Current placed integration — Fallen Moon

The user redirected the placement to `L_FallenMoon`; no Morning actors were modified. Two actors were duplicated from the existing `FX_DebrisSparkle` actor and then assigned their candidate systems:

- `FX_FallenMoon_PetalPiles_Candidate` at `(900, -500, 6000)`, scale `(0.5, 0.5, 0.5)`, using `NS_SakuraPetalPiles_Candidate`.
  - Instance overrides: spawn rate 12, radius 420, scale 1.2–2.0, lifetime 30–55 seconds.
- `FX_FallenMoon_SurrealPetalGust_Candidate` at `(-900, 500, 6450)`, scale `(0.5, 0.5, 0.5)`, using `NS_SurrealSakuraGust_Candidate`.
  - Instance overrides: particle count 28, noise strength 18.

Both are tagged `MelodiaFXCandidate` and `NoReplace`. Existing `FX_MoonAurora`, `FX_DebrisSparkle`, and `FX_Constellation` retain their original systems and transforms. The level was saved after placement.
