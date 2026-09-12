# SDF Niagara candidate finalization — 2026-08-01

## Scope

This pass is strictly Niagara. It does not alter the broader SDF material library, landscape materials, or placed environment actors.

## Candidate library

Each source system remains untouched. The following candidate systems live in `/Game/EnvSandbox/VFX/Candidates/SDF/` and validate with no Niagara errors or warnings:

- `NS_SDF_PulsingGeometry_Candidate`
- `NS_SDF_ParallaxFish_Candidate`
- `NS_SDF_ParallaxPulse_Candidate`
- `NS_SDF_Foliage_Vine_Candidate`
- `NS_SDF_Foliage_Grass_Candidate`
- `NS_SDF_Foliage_Bush_Candidate`

All six expose the same independent per-instance authoring controls:

- `User.SDFParticleCount` (`int`, default `8`)
- `User.SDFParticleLifetime` (`float`, default `10.0`)
- `User.SDFLoopDuration` (`float`, default `10.0`)

Those parameters are bound directly to the burst count, particle lifetime, and emitter loop duration—not stored as unused metadata. This makes each effect repeatable, tunable, and safe to duplicate for a level without changing its source asset.

## Existing materials retained

Candidate renderers preserve the sources' existing material assignments. This is intentional: the systems retain their authored SDF visual identities while gaining reliable Niagara authoring controls. The systems remain presentation-only and do not create gameplay, quest, collision, or rhythm authority.

## Sakura loose ends resolved

- `NS_SakuraPetals_v3_Candidate`: valid, no warnings/suggestions; its ripple/pile receivers are event-only with stable persistent IDs.
- `NS_SakuraPetalPiles_Candidate`: GPU mesh pile with bound count, radius, scale, and lifetime controls; the placed Fallen Moon instance has independent overrides.
- `NS_SurrealSakuraGust_Candidate`: independent Nanite-petal gust candidate with its own count/noise controls.

## Live visual sign-off

Use placed candidates only after checking mesh scale/orientation at the intended camera. Automated Niagara previews are not reliable evidence for this project's mesh-petal material rendering; system compilation and authored instance controls are verified, but lookdev sign-off remains an editor viewport decision.
