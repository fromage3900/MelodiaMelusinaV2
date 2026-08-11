# Niagara renderer audit — 2026-08-01

## Scope and safety boundary

Audited the 30 production systems under `/Game/EnvSandbox/VFX/Systems` only. Third-party Ultra Dynamic Sky, ArtOfShader, recovery packages, and candidate packages are excluded from production replacement.

The pass does **not** treat “it compiles” as visual sign-off. Each conversion is previewed before it is saved; recovery copies are retained under `Saved/Recovery/Niagara_20260801`.

## Confirmed renderer-state result

No visible production renderer now resolves to an Engine/Niagara default material. The only render entry with no material is the light renderer on `NS_Uni_Fireflies`, which is correct.

Confirmed, compile-valid upgrades:

- `NS_ConstellationDraw` — mesh-card renderer using `MI_Niagara_Melodia_ConstellationRosette`; visually verified crescent/rosette treatment.
- `NS_SakuraLanternMotes` — mesh-card renderer using `MI_Niagara_Melodia_LanternFiligree`; spawn and lifetime tuned down for sparse lantern motes.
- `NS_Uni_PollenSparkle` — authored `MI_Niagara_Sparkle` material; visually verified as a restrained pollen field.
- `NS_SakuraPetalGust` — visible renderer converted from sprite to the project Nanite Sakura petal mesh using `M_SakuraPetal`; validation clean.

## Material lanes

- **Petal mesh:** Sakura petal systems use the project petal mesh/material instead of a generic sprite.
- **Symbolic card:** constellation and lantern effects use the custom ornament-card material and full-resolution Japanese alpha sources; never the 32px `_vfxMed` copies.
- **Sparkle:** pollen/firefly/fairy family uses the existing authored sparkle material where a small luminous mote is the intended visual language.
- **SDF:** Bush, Grass, Vine, Fish, Pulse, and Geometry retain their dedicated SDF material routes. They are not to be mass-converted through the card shader.

## Not portfolio-approved yet

These systems have non-default material assignments, but need purpose-built visual approval before placement or promotion:

- `NS_Uni_GroundWisps`, `NS_Uni_WaterMist`, `NS_Uni_MistSheet`: the initial `MistGrain` card substitution made visible rectangular cards. Do not use it as the final mist solution. A copied `M_Niagara_MelodiaSoftMist_Candidate` exists only as an unapproved research branch; its low-opacity smoke output needs a real in-world A/B before assignment.
- `NS_MagicTrail`: the note-card experiment produced broken linework in offline preview. Leave its current renderer state unpromoted until a dedicated ribbon/beam material is built.
- `NS_Uni_DustShafts`, `NS_EmberMotes`, `NS_FairyDust`: material changes compile, but need same-camera map validation rather than relying solely on isolated black-background previews.
- `NS_SakuraDreamSparkle` and `NS_ConstellationTwinkle`: they use authored sprite materials, not Engine defaults, but are still visually generic and should be promoted to a stronger motif in the next polish lane.

## Next implementation order

1. Build one **soft-field mist** candidate that uses smoke/alpha structure, Particle Color, depth fade, and non-rectangular coverage. Test it only on WaterMist in an isolated map actor before reuse.
2. Build one **music-ribbon** candidate for MagicTrail/Henshin/DustShafts; keep trail leader and ribbon material contracts distinct.
3. Promote DreamSparkle and ConstellationTwinkle to symbolic mesh-card or SDF-driven motifs after an A/B, without changing existing placed-map actors en masse.
4. Validate SDF effects in scene against PPV alpha/emissive preservation before any actor swap.

## Acceptance rule

An emitter is considered complete only when it has: a non-default render material or intentional mesh/ribbon lane, clean Niagara diagnostics, a visually non-blank preview, and one in-world capture approval. “No default material” alone is an audit milestone, not final art approval.

## Final safe-placeholder closure

To prevent the remaining utility systems from carrying blank/default/card-rectangle output while their final ambient material is authored, `M_Niagara_SDFStarburst_Candidate` is now the explicit pale magical-dew placeholder for `NS_Uni_GroundWisps`, `NS_Uni_WaterMist`, and `NS_Uni_MistSheet`. The same curated translucent SDF fallback now supports `NS_ConstellationTwinkle` and `NS_SakuraDreamSparkle`.

All five systems validate cleanly and their renderer bindings resolve to that material. This is intentionally a simple, visible temporary language—not a claim that the three mist utilities are final physical mist.
