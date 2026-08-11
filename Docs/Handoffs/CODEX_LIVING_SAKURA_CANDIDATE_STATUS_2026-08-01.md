# Living Sakura Niagara candidate status — 2026-08-01

## Scope and safety

This pass changed candidate Niagara assets only. No Zen Forest map actor was replaced, no legacy source system was overwritten, and `MPC_PPBlending` was not read or written. Promotion remains a per-actor, identical-camera A/B decision.

## Completed candidate work

- `NS_SakuraPetalPiles_Candidate` now uses a bounded `SpawnBurst_Instantaneous` chain rather than continuous spawn. The public contract is `PileCount`, `PileRadius`, `PileScaleMin`, `PileScaleMax`, `PileLifetimeMin`, `PileLifetimeMax`, `PileHueSeed`, and optional `PileSurfaceNormal`. Diagnostics are clean (GPU, fixed bounds).
- `NS_SurrealSakuraGust_Candidate` has one `GustParticleCount` integer only. It now separates `StandardPetalGust` (GPU, EnvSandbox petal mesh) from sparse `HeroNaniteCrossings` (GPU, Melodia Nanite petal mesh), with `HeroPetalCount` defaulting to 4. Diagnostics are clean.
- All six SDF candidates are now GPU-simulated with system fixed bounds and the same public interface: `Intensity`, `Seed`, `Count`, `Size`, `Lifetime`, `LoopDuration`, `WindVector`, `Reaction01`, `AudioLow`, `AudioMid`, `AudioHigh`.
  - Pulse and Geometry have compact architectural bounds.
  - Fish has wide directional flow bounds.
  - Bush, Grass, and Vine have local wake/flutter bounds and bind `WindVector` and `Seed` into velocity.
  - Burst count, lifetime, loop duration, and uniform sprite size are bound to the common user contract. All six compile with zero Niagara diagnostics.
- Existing authored SDF materials remain assigned; no generic sprite/material was mass-replaced.
- `NS_SakuraDreamSparkle_AdvancedCandidate` was created as a candidate-only comparison target. Its original source remains untouched; warmup reduction is deliberately deferred until an identical-camera visual comparison.

## Still awaiting visual approval

1. Place or temporarily stage each candidate in Zen Forest, capture close/traversal/wide frames, then swap individual actors only if approved.
2. Confirm petal landing has one ripple/pile response and no local-origin receiver spawn.
3. Measure Standard GPU cost at one fixed camera. Hero/Nanite remains shrine, quest, and narrative-beat only.
4. Wire the lifecycle material function into a new petal-material candidate rather than retrofitting the approved v2 material. It is intentionally not promoted until compile and visual comparison are clean.
5. Build separate Hero SDF variants only after the Standard candidates read correctly in their authored zones.

## Integration contract

- Claude owns ArtOfShader PPV and `MPC_PPBlending`; translucent/additive Niagara stays outside its depth/normal outline contract.
- Kiro may request FX after authoritative outcomes are decided. FX cannot gate combat, UI, saves, quests, rewards, or input.
- `MPC_Melodia_Palette` / music-clock data may be sampled only as capped presentation input, never as a simulation or gameplay authority.
