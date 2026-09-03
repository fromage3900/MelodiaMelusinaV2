# Infinity Nikki Pipeline Research and Project Update

Date: 2026-08-14

Scope: public, engineering-relevant observations for Melodia's Melusina V2 and long-term wardrobe platform. This is reference research, not a claim of access to proprietary Infinity Nikki source code or production assets.

## Executive readout

Infinity Nikki's public technical material points to a layered outfit platform rather than a simple skeletal-mesh swap. The durable pattern is:

`shared character contract → per-piece deformation/material assets → outfit gameplay and presentation metadata → cloth/physics and clipping rules → catalog, ownership, evolution, dye, and preview systems`

For Melodia, the immediate priority remains the canonical 465-bone V2 deformation and gameplay promotion. Substrate toon materials remain the production baseline. Cloth simulation, alternate NPR packages, and battle wardrobe should stay behind separate gates until the base contract is green.

## Publicly verified technical patterns

The [Unreal Engine technical interview on Infinity Nikki](https://www.unrealengine.com/developer-interviews/behind-the-scenes-of-infinity-nikki-tracing-a-glamorous-turn-to-an-unreal-open-world?lang=en) describes several relevant patterns:

- The project moved from UE4 to UE5 through a separate transition branch before merging back into the main development line. This supports keeping Melusina V2 staging, promotion, and rollback states explicit rather than mutating the live asset in place.
- Outfit abilities are part of the experience, not merely cosmetics. Materials, crafting, terrain-aware audio, skirt animation, and day/night presentation are all described as connected to the outfit/world layer.
- Cloth work is handled with engine-side weight/property tuning, skeletal physics, and Chaos Cloth. A versatile material setup reduces variant cost, while transparency requires its own performance treatment.
- The interview describes precomputed or rule-based clipping treatment for hair, hats, outerwear, shirts, and waist areas. Melodia should represent these as authored compatibility and clipping data, not attempt to solve every outfit collision procedurally at runtime.
- Photo presentation uses Aim Offset, Control Rig, and Blend Space. This supports keeping a reusable pose/presentation layer separate from the locomotion BlendSpace and gameplay animation state machine.
- The project also discusses platform-aware rendering, virtualized or hierarchical geometry, mobile texture compression, character lighting, jewelry materials, Niagara effects, and interactive world responses. These are later optimization/presentation concerns for Melodia, not prerequisites for V2 promotion.

### Fresh source refresh

The current official 2.8 notice gives a concrete traversal fixture pattern:
`Gilded Dawnchaser` has Follow, Mount, Hover, and Sprint modes; smart-mount and
interaction settings; and explicit restrictions for boss stages, Realm Challenges,
and uncleared dungeons. The [official 2.7 ability preview](https://infinitynikki.infoldgames.com/en/news/525)
adds the complementary pattern of bounded spawned traversal objects (one active wave,
limited Starlets, range/lifetime cleanup) plus stage restrictions. Melodia should make
mode transitions, context policy, helper ownership, cleanup/reset rules, and fallback
presentation first-class fields in capability definitions.

The Epic interview also describes pre-processing and constraint work for high-speed
cloth motion, multi-layer collisions, and precomputed data to reduce runtime clipping
cost. The transferable lesson is to author compatibility/clipping profiles and validate
them in fixtures; do not make every outfit or traversal state solve the full collision
problem at runtime.

## Recent public project update (verified 2026-08-14)

The latest official product update found for this research date is [Infinity Nikki Version 2.8](https://infinitynikki.infoldgames.com/en/news/560), launched July 16, 2026. It adds the permanent [Golden Dust] main quest, a new regional arc in Heaven's Reach, new events and a dungeon, Heart of Infinity progression, new Home resources, Compendium/Expedition/Folklore Guide entries, and a more explicit ability/presentation surface. The notice also describes Machine Control interactions, the Everbloom Mystery fog/cleansing route, and Skyline Rush automaton races with acceleration, obstacles, and ring-shaped air currents; these are useful references for separating capability, event rules, and traversal presentation.

The same notice records the August 6 Part 2 unlock for the remaining Golden Court content and Heart of Infinity progression. It also documents open-world scene preview under four lighting conditions, per-piece effect toggles, styling-scheme import with unavailable-piece handling, mount-specific styling with default fallback, switching from mount mode into gathering abilities, and PC/mobile resource cleanup. These are current product signals for preview state, presentation fallback, ability interruption, and content-resource lifecycle—not requirements to copy the live-service model.

The most useful engineering signal is the Gilded Dawnchaser ability: it exposes Follow,
Mount, Hover, and Sprint modes; supports smart mounting and interaction settings;
blocks use in Realm Challenges and boss stages; and blocks Hover in uncleared dungeons.
Version 2.8 also adds open-world wardrobe scene preview with four lighting conditions,
effect toggles, styling-scheme import with unavailable-piece handling, and custom
styling for Mount mode with automatic fallback when pieces are unavailable while
riding. These are strong reasons for Melodia to make modes, context restrictions,
presentation variants, preview policy, and fallback behavior first-class fields in the
shared content package. The [Golden City Training Guide](https://infinitynikki.infoldgames.com/en/news/541)
is especially relevant to fixture design because it describes an ability interacting
with world machines and two different event traversal/race loops.

The [official Version 2.7 update](https://infinitynikki.infoldgames.com/en/news/533) adds useful catalog signals: dyeable pieces, glow-up variants, and optimized/reissued pieces that inherit prior palette or progression state. The [official Version 2.8 Resonance details](https://infinitynikki.infoldgames.com/en/news/547) add stronger data-model requirements: evolution, glow-up, idle animations, poses, enhanced effects, pity/guarantee milestones, and a selectable featured piece.

No official Version 2.9 announcement was located in this review. Treat 2.8 as the current public reference point, not as a forecast of the next release.

The official [news index](https://infinitynikki.infoldgames.com/en/news) was also checked on 2026-08-14; no newer numbered version notice was visible in the current index results.

For lighting and cross-platform presentation, Silicon Studio's [official Enlighten integration release](https://www.siliconstudio.co.jp/en/news/pressreleases/2025/250206InfinityNikki/pdf/NewsRelease_20250206_EN.pdf) describes Infinity Nikki using Enlighten for dynamic bounced lighting and cross-platform consistency. This is a useful presentation benchmark, but it does not change Melodia's current Substrate decision.

## Implications for Melodia

| Public pattern | Melodia response |
| --- | --- |
| Shared character and outfit contracts | Keep `SK_Melusina_Skeleton` canonical; validate actual mesh bone usage before promotion. |
| Outfit abilities and presentation | Add ability/presentation references to a future `OutfitDefinition`; do not activate battle wardrobe during V2 promotion. |
| Cloth and clipping are authored systems | Add per-outfit cloth/clipping profile fields later; keep dynamic skirt cloth disabled until skeletal deformation is stable. |
| Material variants and dye/evolution | Keep approved Substrate material instances authoritative; model palette, glow-up, and evolution as catalog data rather than material-master edits. |
| Catalog, ownership, pity, reruns, and selection | Extend the existing 39-outfit/TokenWallet contract with grant IDs, rarity, pity state, selectable rewards, progression, and save-version migrations. |
| Photo/pose layer | Keep photo poses, Control Rig, Aim Offset, and presentation animations outside the live locomotion BlendSpace. |
| Ability modes and blocked contexts | Store explicit mode transitions, context locks, preview/effect toggles, and safe fallback presentation in the content package; never scatter them across character graphs. |
| Cross-system capability lookup | Keep Resonant Form queries read-only and module-neutral; `BS_GodFile` must not depend directly on `MelodiaWardrobe` because the Wardrobe module already depends on the game module. |
| Mobile/cross-platform optimization | Benchmark after visual correctness; do not add external renderer dependencies to the V2 gate. |

## Boundaries and decisions

- The existing Substrate toon pipeline is the production baseline.
- MooaToon remains deferred until a measured quality or performance gap justifies an experiment.
- NextCAS-UE remains an isolated cloth/blendshape experiment and is not a V2 dependency.
- ShellFur, proprietary clipping algorithms, and other public interview details are not being replicated as proprietary implementations.
- Battle wardrobe remains disabled by default and requires an explicit owner decision.
- Public Infinity Nikki observations inform Melodia's data boundaries and QA strategy; they do not replace local asset, code, or runtime validation.

## Recommended long-term data shape

The future outfit definition should be able to reference:

- stable outfit ID, display name, lore, style tags, rarity, and acquisition source;
- body, shirt, skirt, boots, accessories, hair, material, palette, and glow/evolution references;
- ownership/grant ID, pity or selection state, save schema version, and refund behavior;
- ability and animation/presentation profiles;
- hidden body zones, clipping/occlusion rules, cloth profile, audio profile, and compatible slots;
- lookbook thumbnail, paper-doll preview, and share-card metadata.

This is intentionally data-driven so the first passing outfit can be reviewed before registering the remaining 38 gacha outfits.

## Delegated research refresh: gameplay and content cadence

The second read-only research pass reviewed the official English news stream and
technical material again on 2026-08-14. Version 2.8 remains the newest numbered
English update visible in the checked [official news index](https://infinitynikki.infoldgames.com/en/news).
The 2.8 notice describes Part 2 opening after August 6 and published event windows
extending through August 27; this is a dated public snapshot, not a forecast. The
[Version 2.8 notice](https://infinitynikki.infoldgames.com/en/news/560) and
[2.8 client/pre-download guide](https://infinitynikki.infoldgames.com/en/news/559)
are the primary references. No official English 2.9 announcement was visible in
that review.

### Capability and traversal rules to carry into Melodia

The official material makes four production concerns explicit:

1. **Context-gated abilities:** abilities can be blocked in uncleared dungeons,
   boss challenges, contests, or other authored contexts; Machine Control is
   progression-gated through the Heart of Infinity. Mount mode can switch into
   gathering abilities, with per-ability rules for whether the mount exits. See
   [Tracing the Golden City](https://infinitynikki.infoldgames.com/en/news/540),
   [Celestial Tide](https://infinitynikki.infoldgames.com/en/news/525), and the
   [2.8 notice](https://infinitynikki.infoldgames.com/en/news/560).
2. **Bounded temporary objects:** spawned waves/anchors require instance limits,
   lifetime and distance cleanup, logout cleanup, and explicit interruption rules.
3. **Four presentation layers:** core gameplay, preview/mock, locked-or-fallback,
   and evolution/upgrade presentation should be separately testable. Preview state
   must never become an unreviewed runtime dependency.
4. **Explicit traversal state:** Melodia should model
   `Available -> Entering -> Active -> Interrupted/Cancelled -> Exiting -> Cooldown`
   with movement mode, collision, input ownership, camera, energy, save/load, and
   multiplayer policy declared per transition.

### Kawaii physics placement implications

The public UE5 interview describes in-engine cloth authoring, skeletal physics,
Chaos Cloth, multi-layer collision, authored/precomputed clipping rules, and Niagara
effects. These are production principles, not code to copy. A production-ready
Melodia Kawaii placement BP therefore needs a root-body validator, named placement
profile, per-bone collision/constraint metadata, deterministic no-physics and
reduced-physics fallbacks, preview/runtime separation, performance tiers, screenshot
or pose validation, compile/save verification, and a disposable test map separate
from the canonical gameplay map. The existing probe remains a validation fixture
until those live proofs exist.

### Long-term content cadence

Version 2.8 also demonstrates a layered content model: permanent story, scheduled
chapters, time-limited events, recurring arenas, reset windows, reruns, pre-download,
and cleanup of retired quest resources. Melodia now reserves this as an offline
contract in `specs/content/melodia_content_release_manifest.v1.json`. The manifest
must carry content/version IDs, availability window, unlock requirements, supported
maps, package references, rewards, reset policy, preload bundle, cleanup policy,
fallback content, migration version, and evidence. It is read-only data; scheduling,
rewards, persistence, and cleanup remain owned by their canonical subsystems.

## Official-source refresh — 2026-08-14

The official pages were re-opened for this handoff. The current public reference is
still Version 2.8: the [launch notice](https://infinitynikki.infoldgames.com/en/news/543)
places launch on July 16, 2026 (UTC-7), while the [full Version 2.8 notice](https://infinitynikki.infoldgames.com/en/news/560)
documents the August 6 Part 2 unlock, Heart of Infinity progression, four-mode
Gilded Dawnchaser traversal, open-world preview/effect toggles, mount-specific
fallback styling, and dated event windows. I found no official English 2.9 notice in
the [official news index](https://infinitynikki.infoldgames.com/en/news) during this
refresh; that is a snapshot, not a forecast.

The refresh adds five concrete implementation lessons for Melodia:

1. **Mode graphs need explicit ownership.** Follow/Mount/Hover/Sprint is a state graph,
   not four booleans. Each transition must declare input ownership, movement/collision,
   camera, interruption, and exit/reset behavior. This belongs in the traversal
   definition and `UMelodiaTraversalComponent`, not in each gate BP.
2. **World helpers need bounded lifetimes.** The [Celestial Tide preview](https://infinitynikki.infoldgames.com/en/news/525)
   limits active waves and Starlets and cleans them on range/logout; the [Golden City
   guide](https://infinitynikki.infoldgames.com/en/news/541) adds machine-control and
   race loops with obstacles, acceleration, and limited power. Melodia fixtures must
   test instance caps, interruption, distance/logout cleanup, and reset without
   writing canonical completion state.
3. **Availability is separate from presentation.** The 2.8 notice allows custom mount
   styling but falls back when pieces are unavailable; it also separates preview
   lighting/effects from runtime ability use. Melodia needs `CapabilityId`,
   `PresentationVariantId`, `FallbackVariantId`, `AllowedContexts`, and
   `UnavailablePiecePolicy` as separate data, with preview incapable of granting a
   runtime capability.
4. **Progression is a content dependency, not a level-local branch.** Heart of Infinity
   unlocks Machine Control and later ability/content nodes. Melodia should keep
   progression snapshots in the shared capability gate and re-evaluate after load,
   travel, context change, and reset.
5. **Art-tech handoff is authored and measured.** Epic's [technical interview](https://www.unrealengine.com/developer-interviews/behind-the-scenes-of-infinity-nikki-tracing-a-glamorous-turn-to-an-unreal-open-world?lang=en)
   confirms engine-side cloth authoring, categorized cloth plus skeletal physics/
   Chaos Cloth, multi-layer collision, preprocessed clipping constraints, Niagara,
   and platform-aware rendering. Melodia should use authored Kawaii/clipping profiles
   and performance tiers; it should not replicate proprietary clipping or renderer
   implementations.

### Melodia work items reinforced by this refresh

- Keep the seven-template order and shared gate contract; add no bespoke mode machine
  to Enemy, Portal, Challenge, or StateAnchor BPs.
- Treat the Kawaii placement BP as a profile-driven presentation fixture with a
  no-physics fallback, reduced-physics tier, root-body validator, and deterministic
  reset evidence before production use.
- Keep `melodia_content_release_manifest.v1.json` as the authority-neutral layer for
  permanent, scheduled, recurring, rerun, retired, preload, fallback, and cleanup
  states; do not move schedule state into BPs.
- Keep battle wardrobe disabled until canonical V2 deformation, capability-gate, and
  First Dream route evidence are live-proven.

## Universal UE retargeting refresh — 2026-08-15

The durable Unreal pattern is contract-first and boundary-based:

1. **Author and validate the target contract** in DCC: stable bone names and
   hierarchy, centimetre scale, normalized weights, morph targets, sockets, and
   a reference-pose probe. Validate the mesh's actual used deform groups; a shared
   Skeleton pointer alone is not proof.
2. **Share one Skeleton when the meshes truly share its hierarchy.** Epic's
   [Skeleton documentation](https://dev.epicgames.com/documentation/en-us/unreal-engine/skeletons-in-unreal-engine)
   says multiple Skeletal Meshes can share one Skeleton when names and hierarchy
   are consistent. This is the correct path for Melusina's V2 body and garments;
   it avoids an unnecessary second retarget after the mesh swap.
3. **Use IK Rig/IK Retargeter only at a real skeleton boundary.** Epic's
   [IK Rig retargeting guidance](https://dev.epicgames.com/documentation/en-us/unreal-engine/ik-rig-animation-retargeting?lang=en-US)
   supports different bone counts, names, orientations, and optional hand/foot IK.
   The proven Melodia chain therefore remains
   `source FBX -> source IK Rig -> RTG -> canonical target sequence`, followed by
   a target-skeleton audit and preview. Do not retarget canonical Quaternius clips
   again merely because the gameplay mesh was replaced.
4. **Use a retarget pose and translation policy deliberately.** Epic's
   [Retarget Manager documentation](https://dev.epicgames.com/documentation/en-us/unreal-engine/retarget-manager-in-unreal-engine?lang=en-US)
   calls out source proportions, base poses, IK bones, and twist/finger mappings.
   Record root, pelvis, limb, twist, and foot policies as data and test them on
   idle/walk/run/sprint plus contact poses before promotion.
5. **Promote through rollback and evidence.** Import staging assets against the
   canonical Skeleton, verify actual bind-pose parity, preserve the original body,
   compile/save, then run a disposable PIE fixture. This is safer than trusting a
   green importer or a runtime Skeleton reference.

### Infinity Nikki lens applied to Melodia

Infinity Nikki's public material is most useful as a product-architecture lens,
not as a claim about proprietary implementation. Outfit, ability, presentation,
fallback, and progression state should be separate data. For Melodia this means:

`OutfitId -> VariantSet -> Capability/ContextPolicy -> Presentation/Fallback -> Fixture/Evidence`

The current Version 2.8 public notice documents multi-mode traversal, blocked
contexts, unavailable-piece fallback styling, preview lighting/effect toggles, and
evolution presentation. Melodia should carry those concerns in versioned definitions
and fixtures while keeping battle wardrobe disabled by default. Catalog ownership,
TokenWallet grants, pity/selection state, dye/glow progression, and save migrations
must remain independent of the skeletal mesh authority.
