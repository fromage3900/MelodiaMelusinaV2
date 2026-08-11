# Niagara library deep audit — 2026-08-01

Scope: read-only audit of project-authored Niagara systems under `/Game/EnvSandbox/VFX/Systems`. No Niagara graph, map, material, Blueprint, PCG, lighting, or hair asset was modified by this audit.

## Overall state

- 31 Niagara-system package files exist under the project Systems folder.
- 30 load as Niagara systems; `NS_SakuraPetals` is an intentional ObjectRedirector left by the v1 quarantine move.
- Every loadable system has at least one emitter, module, and renderer.
- All 30 loadable systems report zero Niagara compile errors and zero Niagara diagnostics warnings.
- The 18 systems upgraded in the Codex pass remain healthy, saved, and visually proven in isolated previews. The user also approved the placed P0 effects in level.
- The remaining risk is concentrated in the legacy SDF/constellation/Sakura utility tier rather than the upgraded systems.

## Confirmed unfinished or broken-looking systems

### P0 — visible-output failures

These systems compiled successfully but produced fully black isolated preview captures:

- `NS_ConstellationTwinkle`
- `NS_SDF_PulsingGeometry`
- `NS_SDF_ParallaxPulse`
- `NS_SDF_ParallaxFish`
- `NS_SDF_Foliage_Vine`
- `NS_SDF_Foliage_Grass`
- `NS_SDF_Foliage_Bush`
- `NS_SakuraPondShimmer`
- `NS_SakuraLanternMotes`
- `NS_ConstellationDraw`

The six SDF systems share the same minimal five-module CPU architecture, dynamic bounds, and 1.933-second warmup. Their Initialize Particle stacks do not author sprite size, and `NS_SDF_PulsingGeometry` does not author a burst count. These are structurally incomplete prototypes, not production-ready systems.

`NS_SDF_ParallaxFish` also uses the generic Sakura sprite material rather than a fish-specific renderer treatment.

`NS_ConstellationTwinkle` selects direct sprite sizing but has no authored sprite-size value. `NS_ConstellationDraw` does author size, but its isolated render remains black and therefore needs material/context validation before use.

`NS_SakuraPondShimmer` has a mesh renderer and ripple material, but did not render in isolation. Its mesh/scale initialization and actual placed use should be checked before assuming it works.

`NS_SakuraLanternMotes` has authored lifetime/color/size values but did not render in isolation; its inputs contain legacy string formatting and it remains CPU/dynamic-bounds.

### P0 — event-chain integrity

`NS_SakuraPetals_v2` is visually layered and compiles, but its current semantic topology is not fully proven:

- `EM_PondRipple` and `EM_PetalPile` consume `DeathEvent` from `Petals`.
- The `Petals` emitter reports zero event generators and no generated events.
- Both receivers also retain local Shape/Box location modules, so their placement is mixed event + local shape rather than purely event-driven.

This may explain inconsistent landing ripple/pile behavior. Before changing it, capture the existing placed behavior, then add/repair the source DeathEvent generator and ensure the receiver Position payload is applied. Do not blindly remove the local location modules until the intended composition is confirmed.

## Legacy polish and performance debt

- `NS_SakuraDreamSparkle` visibly renders, but has a 19.933-second warmup, CPU simulation, and dynamic bounds. The warmup is copy-paste-scale residue and should be reduced after a same-camera visual comparison.
- `NS_ConstellationTwinkle`, `NS_SakuraPondShimmer`, `NS_SakuraLanternMotes`, `NS_ConstellationDraw`, and all six SDF systems remain CPU with dynamic bounds.
- The six SDF systems use sprite renderers. A dimensional mesh conversion is only justified after their intended use is established; first make their current authored idea visible and correct.
- Asset-registry referencer queries return no referencers for these legacy systems, but raw package scanning found `NS_ConstellationDraw` and `NS_SakuraDreamSparkle` in `L_InfiniteScore` and the pre-restore Zen Forest backup. Treat “unused” as unproven because World Partition/external actors and serialized soft references may not appear in the registry result.

## Validator notes that are not automatically faults

Event-driven ribbon receivers in Dust Shafts, Wind Ribbon Gust, Sakura Cosmic Aurora, Magic Trail, and Magical Henshin Burst trigger “no spawn module” validator warnings. Their Particle Event scripts compile, their event sources resolve, diagnostics are clean, and isolated previews visibly render; these warnings are validator false positives for event-spawned receivers.

Independent sparkle/petal burst emitters inside Wind Ribbon Gust and Magical Henshin Burst are deliberate layered bursts, not necessarily missing event links.

## Recommended repair order

1. Repair and visually prove the `NS_SakuraPetals_v2` DeathEvent chain because it is active and foundational.
2. Repair `NS_ConstellationDraw` and `NS_SakuraDreamSparkle` because serialized map references were found.
3. Repair `NS_SakuraPondShimmer` and `NS_SakuraLanternMotes`, then confirm whether either is actually placed.
4. Treat the six SDF systems as a separate prototype-to-production lane: establish intended use, author complete size/count/motion/bounds, preview each, then decide sprite versus mesh.
5. Repair `NS_ConstellationTwinkle` or quarantine it if a better constellation system already supersedes it and zero authoritative references are proven.

## Evidence

- Structural inventory: Monolith Niagara summaries and exports for all 30 loadable systems.
- Compile health: `get_system_diagnostics` for all systems, zero errors/warnings.
- Semantic validation: `validate_system` plus full event topology for `NS_SakuraPetals_v2`.
- Isolated captures: `Saved/Screenshots/Monolith/20260801_101528_*.png` through `20260801_101530_*.png`.
- Serialized map-name scan: `L_InfiniteScore.umap`, `ZenForestTest.umap`, and `ZenForestTest_PreRestore_Backup.umap`.
