# UE 5.8 Toon Shading Material Intake

## Infinity Nikki production lens · BS_GodFile · 2026-08-08

## Executive verdict

The project already has the beginnings of a strong stylized-rendering platform: UE 5.8 Substrate Toon is enabled, the main toon path is built around `SubstrateToonBSDF`, there are dedicated Toon Profiles, and the library has meaningful specialist lanes for landscapes, water, impressionist surfaces, SDF ornament, foliage, magical effects, and post processing.

It is not yet a safe long-term game-wide material system. The primary risk is not lack of visual capability; it is governance and cost control. The central `M_Master_Toon_Universal` graph is an excellent R&D surface but currently combines too many optional art directions, has a very large parameter contract, and still has broken/dead references in the live library. The project also contains dated siblings, scratch masters, showcase leaves, imported/legacy roots, and an incomplete portfolio manifest that make “which asset is canonical?” hard to answer.

My recommendation is:

1. Keep the single Toon BSDF architecture for opaque stylized surfaces.
2. Make the Universal master a lean core plus explicitly gated extensions.
3. Keep Landscape, Water, Foliage/Masked, Fabric/Character, SDF/Hero, Impressionist, and Post Process as specialist parents.
4. Turn Toon Profiles, quality tiers, parameter naming, previews, and compile/performance budgets into production contracts.
5. Repair asset health and canonical ownership before adding more effects.

This is a production hardening and specialization problem, not a reason to build another all-in-one “god material.”

## Scope and evidence

The deep intake covered the production-facing library at `/Game/EnvSandbox/Materials`, its referenced graph snapshot, the existing audit reports, the project rendering configuration, and the wider Content tree for boundary analysis.

### Current disk census

The current audit found:

| Area | Verified count | Interpretation |
|---|---:|---|
| `Content/EnvSandbox/Materials` uassets | 552 | The current project-owned material library, including textures and support assets |
| Assets matching `M_`, `MI_`, `MF_`, `TP_`, `MPC_` naming | 423 material-like assets | Naming census, not a substitute for Unreal class metadata |
| Material-instance-like assets (`MI_`) | 267 | The leaf population that needs parent, tier, profile, and preview governance |
| Material-function-like assets (`MF_`) | 56 | Current function inventory under the project material root |
| Master-folder `M_` assets | 36 | Includes canonical parents plus dated/scratch/specialist variants |
| Toon Profiles (`TP_`) | 18 | Strong starting point for an art-direction/profile matrix |
| Material textures under the root | 33 | 26 are currently reported as unreferenced |
| Entire `Content` tree matching the naming convention | 1,839 | Includes third-party, legacy, compatibility, imported, and non-production roots; not all are in the production spine |

The material-library audit is the source of truth for the current disk-level health snapshot: [material_library_audit.json](C:\EnvironmentPortfolio\BS_GodFile\Saved\Audit\material_library_audit.json).

### Deep graph baseline

The committed UE 5.8 T3D snapshot covers the art-direction spine rather than every instance leaf: 55 assets, 5,303 graph nodes, 6,636,491 bytes of payload, comprising 10 master materials, 27 identity/material functions, 17 Toon Profiles, and one parameter collection. It intentionally excludes the 483 instance leaves in that snapshot, plus archive/scratch/date variants. See [the T3D baseline README](C:\EnvironmentPortfolio\BS_GodFile\Docs\T3D_Baseline\README.md) and [material_catalog.json](C:\EnvironmentPortfolio\BS_GodFile\Docs\T3D_Baseline\material_catalog.json).

This distinction matters: the intake is exhaustive at the library/file level, while graph-level judgment is deepest on the current 55-asset material spine. Instances were reviewed by folder/family, references, parent population, and existing audits rather than by pretending that every leaf is a new shader graph.

### Current graph facts

The primary baselined masters use one `SubstrateToonBSDF` and no `SubstrateSlabBSDF` in the inspected graphs. The expensive complexity is therefore primarily in the upstream texture, mask, ramp, parallax, macro, weather, sparkle, temporal, and artistic feature logic feeding that BSDF—not in a multi-slab material stack.

`M_Master_Toon_Universal` is the largest inspected graph at 1,201 exported objects. It contains 343 unique parameter names and 30 static-switch parameter nodes in the current snapshot. The older June review reported 685 nodes and 192 parameters; that is historical evidence, not the current graph size. The old report is still useful for intent and migration history, but current decisions must use the 2026-08-07 T3D baseline and current audit outputs.

The current Universal graph references `MF_NikkiDreamGrade`, `MF_DF_ContactBlend`, `MF_ColorRamp3`, `MF_NormalAdjust`, `MF_SpaceParallax`, `MF_Madoka`, `MF_Itto`, `MF_Impressionist_Impasto`, a Day-to-Night function, and a MeshBlend function outside the EnvSandbox root. This also exposes a documentation conflict: an older lane review described some Nikki/parallax logic as inline, while the current export shows a Nikki function call. Re-run the live lane audit before deleting or moving any of these functions.

## UE 5.8 Toon and Substrate findings

UE 5.8 introduces experimental Substrate Toon Shading. Epic describes it as a stylized solution built on the Substrate Blendable GBuffer and says it supports local lights, skylights, and Lumen GI. The new Toon BSDF and Toon Profile provide the controlled diffuse/specular response needed for stylized lighting. See the [UE 5.8 release notes](https://dev.epicgames.com/documentation/unreal-engine/unreal-engine-5-8-release-notes?lang=en-US), [Substrate Toon BSDF API](https://dev.epicgames.com/documentation/unreal-engine/API/Runtime/Engine/UMaterialExpressionSubstrateToon-?lang=en-US), and [Toon Profile API](https://dev.epicgames.com/documentation/unreal-engine/API/Runtime/Engine/UToonProfile?lang=en-US).

The important production constraints are:

- `UToonProfile` is experimental and is specified on the material; Epic explicitly documents it as per-material and says not to change it at runtime. Profiles should therefore be authored as stable art-direction assets, with profile selection happening through material parents/instances or quality lanes, not through a runtime “profile switch.”
- Blendable GBuffer is the performance-oriented path. Epic says it targets 60 Hz, has predictable memory/speed, keeps visual consistency across platforms, and has no cook overhead. Adaptive GBuffer is heavier, adds cook cost, and is intended for current-generation consoles/PC SM6; other platforms fall back to Blendable behavior.
- Blendable materials are simplified to one supported feature per pixel and do not support F90, per-pixel diffusion SSS MFP, haziness, or native glints. This is directly relevant to `MF_NikkiSparkle`, gemstone, fabric, and premium sheen ideas: native Substrate glints cannot be the only implementation of a feature intended to work across the game.
- Epic documents default Substrate storage at `r.Substrate.BytesPerPixel=80` and automatic closure simplification when a graph exceeds closure/byte budgets. The project currently uses a single Toon BSDF in the inspected spine, which is a good baseline; adding vertical layers or multiple BSDFs should be reserved for clearly justified surfaces such as water, coated glass, or jewelry.
- Static parameters compile branches away but create permutations. Epic’s material-instance guidance is to minimize static parameter combinations and use hierarchical material instances. A gate is valuable only when it removes meaningful code/texture reads from the compiled branch and the project can keep the combination count under control.

The practical conclusion: use Toon BSDF as the common lighting response, but keep the graph physically disciplined. PBR-ish base inputs, roughness, metalness/F0 intent, normal, and masks should remain coherent under changing lights, Lumen, weather, and time of day. Stylization belongs in the Toon Profile, controlled ramps, tint/mask layers, and deliberately authored accents—not in arbitrary per-material lighting hacks.

See Epic’s [Substrate overview](https://dev.epicgames.com/documentation/en-us/unreal-engine/overview-of-substrate-materials-in-unreal-engine) and [real-time rendering optimization guidelines](https://dev.epicgames.com/documentation/en-us/unreal-engine/guidelines-for-optimizing-rendering-for-real-time-in-unreal-engine).

## The Infinity Nikki lens

This is not a claim that the project can reproduce Infold’s proprietary graphs. The lens is based on Infold’s official UE interview and translates its public production principles into decisions for this library.

Infold describes Infinity Nikki as a balance of cartoon fantasy and realism while retaining PBR-based lighting, with weekly art benchmark meetings to keep the style unified. It also describes versatile fabric masters that merge textures efficiently and reduce material variants, standardized PBR inputs for changing light/weather, VT/VHM terrain optimization, platform-aware foliage and fur LOD, custom treatment of transparent character parts, restrained post processing to preserve room for photo filters, and special materials for high-value jewelry. See [Behind the Scenes of Infinity Nikki](https://www.unrealengine.com/developer-interviews/behind-the-scenes-of-infinity-nikki-tracing-a-glamorous-turn-to-an-unreal-open-world?lang=en-US).

Translated into a material review rubric, every production material should answer:

1. Does it preserve believable base/roughness/normal behavior when lighting, weather, and time of day change?
2. Does it read cleanly at the actual gameplay camera distance, not only in a close-up preview?
3. Is its art direction encoded as a small, intentional set of profile/grade/mask choices?
4. Can an artist use it without understanding the graph’s internals?
5. Does it avoid creating a new parent for every outfit, biome, trim, or effect?
6. Does it have a fast, standard, hero, and cinematic path where the screen-space value justifies the cost?
7. Does it leave post processing/photo mode room instead of baking all glamour into the base surface?
8. Is a high-cost effect attached to focal assets only, with a cheap graceful fallback?

The current project is strongest on visual ambition and specialist experimentation. It needs to become much stronger on points 3–7.

## Family-by-family review

### 1. Universal surface master — keep, slim, and formalize

`M_Master_Toon_Universal` is the correct candidate for the shared opaque environment/prop surface parent. It has a useful core: base surface, packed channels, texture layers, layer blends, triplanar support, macro/detail, toon grade, time-of-day, contact behavior, and controlled premium accents. The prior execution review also found that its parallax block is a real integrated system rather than a duplicate: global controls multiply with per-layer controls and should not be removed blindly.

The problem is accumulated optional identity. Current parameter groups span base channels, triplanar, contact, texture layers, parallax, gemstone, blend stacks, Nikki dream, rim/glow, sparkle, iridescence/sheen, gilding, shadow systems, celestial, fairy dust, magical transform, macro/detail, elemental, weather, cinematic, temporal/ink, palette, and deprecated MeshBlend. That is a valuable R&D catalogue but too broad to be the default runtime path for every wall, rock, trim, or prop.

Recommended action:

- Keep the core surface path and the working parallax/triplanar logic.
- Gate Sparkle, Celestial, Fairy Dust, Weather, Gilding, and other niche families with explicit static gates only after instance evidence is confirmed.
- Preserve Itto and Madoka as generic `InkWear`/`VeinGlow` extensions where current instances use them; do not remove them merely because they originated as character/effect experiments.
- Keep the existing Character removal decision: the July instance audit found zero Universal users for that family. Reconfirm in the current editor before final cleanup.
- Consolidate all ramps onto `MF_ColorRamp3`; the current graph already contains multiple calls and the codebase contains multiple competing ramp concepts.
- Collapse the two sheen concepts and the two shadow-tint concepts into one named contract each.
- Remove `Param_1`, diagnostic switches, and `_LEGACY` parameters only through an override migration table. Parameter renames can silently break instance art.
- Treat `MacroScale` as world-space. The previous review found UV-dependent macro breakup and applied a world-space fix with migrated/clamped overrides. Recheck the eye result on the four named high-scale Zen assets before making that change the permanent baseline.

### 2. Landscape HeightBlend — strong specialist, move toward VT/RVT

`M_Master_Toon_Landscape_HeightBlend` is the best current specialist path. The landscape audit reports 91/91 checks passed, validates four painted terrain layers, height competition, slope/cliff behavior, snow, storybook controls, Nikki fast/hero grades, distance/debug tiers, and the required physical material/layer-info setup. It has 11 checked instances in the current audit family.

The principal risk is ownership, not visual design: there are nine dated sibling copies in the Masters folder, and the T3D baseline leaves their authority unresolved. `M_Master_Nikki_Landscape` also exists under `_Scratch`, so the project has competing ideas about whether terrain styling belongs in the canonical landscape parent or in a Nikki-specific parent.

Recommended action:

- Declare the undated HeightBlend material canonical and move dated siblings into a non-production archive after checking references.
- Keep the four-layer contract and Storybook/Nikki grade as optional modes, not separate parent graphs.
- Make large-world layering a VT/RVT responsibility where appropriate. Epic documents RVT as a good fit for procedural/composited/layered landscape data; this also matches Infold’s public VT/VHM direction.
- Reserve per-pixel parallax for close hero cliff/stone assets, not broad terrain.
- Add distance-faded macro, slope, wetness, and snow paths with explicit quality switches.
- Fix the live broken texture/material references before calling this production-ready.

### 3. Water — promising v7 experiment, not yet canonical

The project contains `M_Water_Master_Grand_v6`, `M_Water_Master_Grand_v7`, a v7 projector, base water instances, six v7 instances, and three showcase water instances. The v7 audit reports 99 expressions, eight-wave spectrum logic, quality contracts, and no graph connection failures. Its declared tiers are sensible: Medium uses six waves and one POM step; High enables more POM/SDF/bioluminescence; Cinematic allows eight waves, ten POM steps, binary refinements, and optional planar work.

The blocker is important: the audit records an UE 5.8 SM6 hardware-ray-tracing closest-hit permutation issue around Substrate SingleLayerWater legacy output pins. The base graph is repaired and the projector compiles, but the engine permutation remains unresolved. Manual validation is still required across BasePass, FHitProxy, LumenCard, shadows, MRQ, TSR motion vectors, and day/dusk/night/grotto captures.

Recommended action:

- Keep v6 as the stable fallback until the v7 blocker is tested on the actual target matrix.
- Keep v7 under an explicit experimental/hero label.
- Preserve the quality contract, but make each expensive branch auditable: wave count, POM steps, binary refinements, SDF shoreline, bioluminescence, planar reflection, and translucency mode.
- Use cheap opaque/masked or low-cost translucent fallbacks for distant water, mobile/handheld profiles, and dense water surfaces.
- Do not fold water into Universal. Its lighting, depth, refraction, shoreline, and motion requirements are materially different.

Supporting evidence: [grand_water_v7.json](C:\EnvironmentPortfolio\BS_GodFile\Saved\Audit\grand_water_v7.json).

### 4. Nikki masters and Nikki functions — promote only as a controlled style lane

The project has `M_Master_Nikki`, `M_Master_Nikki_Landscape` under `_Scratch`, `MF_NikkiDreamGrade`, `MF_NikkiIridescenceSheen`, `MF_NikkiRimGlow`, and `MF_NikkiSparkle`, plus five `NikkiHero` instances and `TP_NikkiDream`. The current Universal export shows `MF_NikkiDreamGrade` wired into the main path, which is a positive sign: the Nikki look is becoming modular rather than remaining entirely inline.

The risk is semantic overreach. An Infinity Nikki-style surface is not “everything dreamy turned on.” It is a stable PBR-informed surface under changing lighting, with focal glamour effects where the camera and asset hierarchy justify them. Dream grade, rim, sparkle, and iridescence should be a deliberate preset stack with a cheap fallback.

Recommended action:

- Promote Nikki masters out of `_Scratch` only after a current live reference audit and a side-by-side benchmark.
- Define `Nikki Fast`, `Nikki Standard`, `Nikki Hero`, and `Nikki Cinematic` contracts using the same inputs and different enabled extensions.
- Keep sparkle as a custom, blendable-safe implementation unless Adaptive/native glints are explicitly validated on every target; Epic documents native glints as unsupported on Blendable GBuffer.
- Treat iridescence as a sheen/film extension with controlled mask and roughness limits, not a global color effect.
- Put jewelry, crystal, and high-reflection accents in a dedicated hero lane rather than raising the cost of all environment materials.
- Maintain one benchmark map with day, dusk, night, wet, shadowed, Lumen, and photo-mode captures.

### 5. Impressionist materials — preserve as a separate painterly family

The impressionist lane has two baselined masters, four identity functions, three Toon Profiles, and separate showcase material. The graphs are materially smaller than Universal: the inspected masters are 124 and 73 exported objects. Brush stroke, impasto, ink pool, and temporal variation are coherent as a painterly family.

Do not merge this into Universal. The visual model is different, and making it a Universal feature would add parameters, texture reads, and temporal behavior to materials that do not want them. Keep the family focused on foreground props, special environments, storybook spaces, and selected cinematic surfaces.

Optimization priorities are temporal stability, screen-space aliasing, distance fade, and predictable behavior under motion vectors/TSR. It should have a low-cost flat/graded fallback for background surfaces.

### 6. SDF and cosmic materials — premium hero/decorative lane

The SDF lane contains nine named material assets and 44 SDF/cosmic/Toon-SDF instance leaves. It includes baroque ornament, filigree, portals, stained glass, moss/stone, nebula, starfield, void, musical geometry, and bioluminescent forms. `MF_SDF_BandRelief` is one of the largest functions in the baseline at 373 exported objects.

This is a strong differentiator for hero spaces, but it is not a generic material path. SDF math, parallax, relief, temporal motion, and multiple feature masks can become expensive at scale and will be especially sensitive to target resolution.

Recommended action:

- Keep SDF as a named premium lane with Fast/Standard/Hero/Cinematic subtiers.
- Use baked/vertex/texture alternatives for distance and low-end paths.
- Avoid using SDF materials on large repeated surfaces unless a frame-budget test proves the value.
- Separate “ornament relief” from “cosmic emissive field” so a baroque wall does not inherit nebula logic.
- Create explicit screen-size rules for SDF depth and temporal detail.

### 7. Foliage, cards, SpeedTree, and Niagara — optimize for overdraw and instance density

The library has five named foliage instances, `M_ToonFoliage`, `M_SpeedTreeMaster`, Niagara foliage materials, procedural foliage instances, and leaf/grass experiments. This family should be judged on masked overdraw, two-sided shading, WPO frequency, wind, shadow cost, and instance/LOD behavior—not on how beautiful a close-up material ball looks.

Follow the public Infinity Nikki lesson here: instance density and screen-size-aware LOD matter as much as shader beauty. Keep grass/leaf cards out of POM, dense SDF, heavy sparkle, and unnecessary triplanar paths. Use vertex color contracts for wind phase, bend, tint, translucency, and variation. Add a very cheap distant path and test foliage in the actual open-world culling/LOD system.

### 8. Foliage/character/fabric/Melusina — do not force all into Universal

The library contains 13 Melusina instances and nine `MelusinaReal` instances under material-specific parents, plus `MF_AnimeSkinWrap`, `MF_ClothWindDrape`, `MF_Melu*`, `TP_Character`, `TP_Melusina`, and fabric-related functions. That is evidence for a dedicated character/fabric lane, not a reason to reintroduce the removed Character family into Universal.

The Infinity Nikki comparison is direct: Infold describes a versatile fabric master that merges fabric textures efficiently, reduces variants, and works across platforms. The project should converge on a dedicated fabric/character parent with a fixed input contract: base color, normal, packed material, cloth/fuzz or sheen mask, skin/hair/eye mode, wind/cloth mask, and one optional hero extension. Semi-transparent outfit pieces should have separate explicit handling and fallback tiers.

Keep Melusina as a real consumer/test family, but resolve whether the `Melusina` and `MelusinaReal` parents are intentional specialization or historical duplication.

### 9. Magical, celestial, Itto, Madoka, gilding, and shadow effects — keep as extensions, not defaults

These effects are useful and artistically distinctive. The previous Universal review found concrete instance use for Itto/Madoka-like `InkWear`/`VeinGlow`, while Celestial, Fairy Dust, Sparkle, and Weather had much smaller user populations. This is exactly the use case for extensions and static gates.

Recommended contract:

- Base surface always available.
- One style grade always available.
- One optional focal accent by default.
- Multiple accents only on Hero/Cinematic tiers.
- All animated effects driven by a small number of shared MPC/MID values, not dozens of independent time nodes.
- All emissive/glow effects bounded by exposure and distance so they do not become a global lighting substitute.

### 10. Trimsheets, triplanar, parallax, and Zen material families — valuable, but screen-space budgeted

The instance library has trimsheet, triplanar, parallax, Zen, wet, floral, stone, wood, paper, and ornamental families. The Universal review correctly keeps core parallax and triplanar, but these features must be assigned by material class and camera range.

Use parallax/POM for close stone, carved trim, steps, cliffs, and ornamental hero surfaces. Avoid it on grass cards, petals, broad landscape, soft fabric, thin paper, and any material whose screen footprint is too small for stable depth. Fade POM steps with distance and quality tier. Use world-space macro variation for coherent world breakup; do not let UV density decide the apparent scale of the world.

### 11. Post process — keep additive and photo-mode friendly

The project has underwater post-process, multiple candidate/backups, Toon/SDF post effects, and several profiles. Follow the Infinity Nikki lesson: natural lighting/fog and restrained base grading should leave room for photo filters. Keep outlines, tone mapping, vignettes, ink treatment, and photo filters in explicit post-process lanes with clear ordering and capture validation.

Avoid baking scene-wide color effects into every material. That makes lighting changes harder to reason about and makes photo mode less controllable.

### 12. Third-party, legacy, compatibility, and imported roots — quarantine by policy

The wider Content scan includes `Greybox_Kit`, `Brushify - Floating Islands`, `ArtOfShader`, `Library`, `_ThirdParty`, `Melodia`, `_PROJECT`, `RVTDecals`, `Surfaces_CC0`, `Genshin_Shader_v1_1`, and compatibility projects. These are useful source material and tests, but they should not silently become part of the production material spine.

Create a boundary rule: production assets may reference approved library roots; imported/third-party roots require an explicit adapter, attribution/license note, and owner. This will prevent the current broken paths from becoming a permanent dependency pattern.

## Current health register

### P0 — fix before expanding the library

- Four missing texture references are reported. Affected live candidates include `MI_Landscape_SakuraGarden`, `MI_Landscape_WitchGarden`, and `MI_Universal_MossStone`. These are pink-material risk, not cosmetic cleanup.
- Thirty-two dead material references are reported. Some are expected backup/archive noise, but live-path issues include `M_Master_Toon_Universal` referencing `/Game/Materials/MF_MeshBlend_Activator_Index`, `M_Master_Toon_Cosmic` referencing a missing `/Game/EnvSandbox/Materials/Functions/MPC_Portfolio_Audio`, and `MF_MooaToonBaseInput_2` referencing old function paths.
- Nine dated Landscape HeightBlend siblings and multiple Universal backup/instance copies make authority ambiguous.
- `M_Master_Nikki` and `M_Master_Nikki_Landscape` are still under `_Scratch`; promotion is unresolved.
- The material family manifest has 30 metadata-only entries and no preview paths. It is not yet a production coverage manifest.
- Water v7 still has an engine/permutation validation blocker. Do not silently make it the only water path.

### P1 — stabilize the architecture

- Create a canonical parent registry with one owner and one status for Universal, Landscape, Water, Impressionist, SDF, Foliage, Fabric/Character, and Post Process.
- Create a parameter registry with stable names, groups, units, clamps, default values, tier availability, and migration aliases.
- Re-run the Universal lane audit against the 2026-08-07 graph. The current T3D export and older written review do not fully agree.
- Collapse duplicate ramp, sheen, and shadow systems.
- Add gates for optional features based on current instance usage, while keeping the Henshin/transform gate conservative until its fan-out is traced.

### P2 — make it scalable across the game

- Build preview fixtures: sphere, plane, curved trim, cliff, landscape patch, foliage card, water patch, translucent cloth, character skin, jewelry, SDF ornament, and impressionist prop.
- Capture Fast/Standard/Hero/Cinematic at gameplay distance and close-up under day/dusk/night, wet/dry, shadowed, Lumen, and MRQ/photo-mode conditions.
- Add automated checks for missing refs, wrong parents, stale duplicate paths, static-switch combinations, instruction counts, texture reads, Substrate simplification, and profile assignment.
- Tie the material manifest to the preview matrix and owner/status fields. A preview-less material cannot be a benchmark material.

## Recommended long-term architecture

### A. Core surface contract

Keep the Universal family, but redefine its default path as:

`BaseColor + packed ORM/material channels + normal + UV/world coordinates + one style grade -> optional low-cost macro -> Substrate Toon BSDF`

The default path should not compile celestial, fairy dust, magical transform, SDF relief, water optics, character skin, or impressionist temporal logic. Those are extension lanes.

### B. Specialist parents

Use these canonical parents:

| Parent lane | Owns |
|---|---|
| Universal Surface | Opaque props, trims, stone, wood, simple environment surfaces |
| Landscape HeightBlend | Terrain painting, slope, snow, wetness, RVT/RVT masks, terrain distance tiers |
| Water | Depth, shoreline, waves, foam, refraction/translucency, bioluminescence |
| Foliage/Masked | Wind, two-sided, subsurface/wrap intent, cutout, low overdraw, LOD |
| Fabric/Character | Cloth/fuzz/sheen, skin/hair/eye modes, outfit masks, transparency variants |
| Nikki Hero | Dream grade, focal rim, bounded sparkle/iridescence, jewelry/hero accents |
| SDF/Hero | Relief, filigree, cosmic fields, portals, hero ornament |
| Impressionist | Brush, impasto, ink, temporal painterly variation |
| Post Process | Outline, tone mapping, underwater, storybook, photo filters |

Each specialist may call shared functions, but it should not inherit every other specialist’s parameter surface.

### C. Extension functions

Standardize a small extension vocabulary: `StyleGrade`, `ColorRamp3`, `MacroDetail`, `Wetness`, `Gilding`, `Sparkle`, `IridescenceSheen`, `ContactBlend`, `ParallaxCore`, `Triplanar`, `InkWear`, `VeinGlow`, and `NikkiDreamGrade`. Each extension needs:

- one input/output contract;
- explicit cost classification;
- a quality-tier rule;
- a preview fixture;
- a fallback behavior;
- no hidden global parameters;
- no duplicated local implementation without a documented exception.

### D. Two-level instance hierarchy

Use `MI_<Family>_<MaterialClass>` as the first level and `MI_<BiomeOrHero>_<Asset>` as the second. Do not create peer instances with unrelated parameter naming. Constants belong in material instances; runtime animation values such as wetness, pulse, time-of-day, and audio reactivity belong in MIDs/MPCs with carefully bounded ranges.

### E. Toon Profile matrix

The 18 current profiles should be normalized into a matrix by physical/art class and tier, for example:

`Default`, `Stone`, `Wood`, `Metal/Gold`, `Glass`, `Water`, `Foliage`, `Character`, `NikkiDream`, `Hero`, `Ornamental`, and the three Impressionist modes.

Do not create a new profile for every asset. Profiles should express the shared lighting language; material instances should express local color/mask/texture differences.

## Optimization strategy

### Pixel cost

- Count texture reads, dependent reads, POM/SDF iterations, WPO, translucency, overdraw, and Substrate feature complexity—not only graph nodes.
- Pack channels aggressively where it does not damage authoring clarity.
- Move cheap, low-frequency variation to vertex color or RVT where possible.
- Fade costly features by distance and screen size.
- Keep sparkle/glow bounded and focal.

### Permutation cost

- Use static switches for a small number of meaningful, mutually exclusive paths.
- Avoid a Cartesian product of independent booleans. Prefer a tier enum or a small number of family gates.
- Record compiled permutation counts per parent and platform.
- Never add a switch without proving that the disabled branch disappears from the compiled material and that the combination count is manageable.

### Memory and world scale

- Use RVT/VT for large layered terrain and road/decal compositing rather than pushing all world layering through every terrain pixel.
- Use asset/texture streaming and stable macro coordinates.
- Keep water, foliage, and translucent cloth on their own memory/overdraw budgets.
- Treat Adaptive GBuffer as a deliberate premium target, not as a default assumption. Validate the project’s actual GBuffer/profile behavior in the editor and on target devices.

### Artist workflow

- Every parameter gets a stable group, units, clamp, tooltip, default, and tier.
- Provide preset instances for common material classes rather than exposing 300+ raw knobs.
- Use benchmark maps and weekly-style art reviews: the project needs a living visual contract, not just a technically correct graph.
- Require a before/after preview when changing Toon Profiles, ramp behavior, macro scale, sparkle, or post processing.

## Execution plan

### Phase 0 — freeze and repair

1. Snapshot the current T3D baseline and audit JSON.
2. Fix the four missing texture references.
3. Classify the 32 dead refs into live blockers, safe archive noise, and intentional external dependencies.
4. Resolve `MF_MeshBlend_Activator_Index`, `MPC_Portfolio_Audio`, and old Mooa function paths.
5. Declare canonical masters; quarantine dated/scratch duplicates after reference verification.

### Phase 1 — Universal hardening

1. Re-run the live instance override audit.
2. Keep core surface, layers, channels, parallax, triplanar, time-of-day, and contact behavior.
3. Gate optional families.
4. Consolidate ramps, sheen, shadow tint, and palette handling.
5. Remove only traced dead branches and only after instance migration.
6. Re-export the graph and compare instruction/texture-read/permutation cost.

### Phase 2 — specialist promotion

1. Promote Nikki masters if their reference audit is clean.
2. Make Water v7 opt-in until the SM6 closest-hit permutation is closed.
3. Make Landscape HeightBlend canonical and move broad-world blending toward VT/RVT.
4. Establish Fabric/Character as its own family.
5. Keep Impressionist and SDF separate with explicit quality contracts.

### Phase 3 — platform matrix

Validate each family across the actual supported tiers. At minimum: desktop SM6/Lumen, console-equivalent high, handheld/mobile-style lower tier, MRQ/cinematic, and photo mode. Capture base pass, shadow, Lumen card, TSR motion, translucent, and hardware-ray-tracing permutations where applicable.

### Phase 4 — expansion

Only after the above is stable, add new families such as jewelry, shell fur, advanced cloth sheen, more magical effects, or SDF variants. Each new effect should arrive as a specialist extension with a cheap fallback and a benchmark scene, not as another universal graph branch.

## Acceptance criteria for a game-wide material platform

- Zero untriaged missing refs in production roots.
- One canonical parent per production family.
- Every production instance has a valid parent, Toon Profile, family, tier, owner, preview, and status.
- No unreviewed `_BACKUP`, `_QUARANTINE`, `_SCRATCH`, or dated asset is referenced by production content.
- Universal default compiles without optional glamour families enabled.
- Every optional extension has measured pixel cost and a fallback.
- Water v7 has a signed-off target matrix or a stable v6 fallback remains available.
- Landscape uses RVT/VT intentionally for broad-world blending.
- Preview captures prove readability under changing lighting and weather.
- Art direction is reviewed against a shared benchmark scene, not just individual material-editor thumbnails.

## Local evidence index

- [Current material health audit](C:\EnvironmentPortfolio\BS_GodFile\Saved\Audit\material_library_audit.json)
- [Landscape AAA audit](C:\EnvironmentPortfolio\BS_GodFile\Saved\Audit\landscape_aaa_audit.json)
- [Water v7 audit](C:\EnvironmentPortfolio\BS_GodFile\Saved\Audit\grand_water_v7.json)
- [Committed T3D spine baseline](C:\EnvironmentPortfolio\BS_GodFile\Docs\T3D_Baseline\README.md)
- [Universal graph review and prior optimization stages](C:\EnvironmentPortfolio\BS_GodFile\Docs\Production\UNIVERSAL_MASTER_NODE_REVIEW.md)
- [Historical material-system review](C:\EnvironmentPortfolio\BS_GodFile\Docs\Production\MATERIAL_SYSTEM_REVIEW.md)
- [Layering/parallax/Nikki review](C:\EnvironmentPortfolio\BS_GodFile\Docs\Production\MATERIAL_LAYERING_PARALLAX_NIKKI_REVIEW.md)
- [Current project rendering configuration](C:\EnvironmentPortfolio\BS_GodFile\Config\DefaultEngine.ini)
- [Portfolio material manifest](C:\EnvironmentPortfolio\BS_GodFile\Saved\Portfolio\Materials\material_family_manifest.json)

## Bottom line

The project should aim for an Infinity Nikki-like production philosophy rather than an Infinity Nikki-looking shader: stable PBR-informed lighting, strong art benchmarks, shared masters with few variants, exceptional focal materials, open-world-aware VT/LOD behavior, and platform-specific cost contracts. The current library can reach that standard, but only if the next work is primarily consolidation, health repair, profiling, and specialization. The next major visual feature should wait until the material spine is canonical and measurable.
