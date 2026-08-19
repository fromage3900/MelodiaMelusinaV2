# Universal UE Retargeting Pipeline — Melodia Long-Term Standard

Date: 2026-08-15

## Decision

Use a canonical-skeleton pipeline for meshes that genuinely share the contract,
and an IK Rig/IK Retargeter pipeline only when crossing a source/target skeleton
boundary. Every promotion is gated by actual mesh bone usage, bind-pose parity,
materials, morphs, rollback evidence, and a disposable PIE fixture.

## Pipeline

`DCC source -> contract preflight -> weights/morphs -> export sidecar -> UE staging import -> skeleton/bind audit -> preview -> PIE -> promotion`

For foreign animation:

`source mesh/FBX -> source IK Rig -> explicit retarget chains/root policy -> IK Retargeter -> target sequence -> curve/notify/root-motion audit -> preview/PIE`

For same-contract garments, the retarget stage is intentionally absent:

`bound garment -> canonical 465-bone Skeleton -> leader pose -> material/physics profile -> fixture`

## Non-negotiable checks

- Contract bone count and hierarchy match; actual used deform groups are a subset
  of the canonical contract.
- Units are explicit. A centimetre bake is applied exactly once; exporter and
  importer scale factors are recorded in sidecars.
- Root/pelvis translation, twist bones, feet, hands, sockets, and reference pose
  are compared against the canonical mesh before promotion.
- Morph targets and face/blink names are enumerated separately from skeletal
  animation curves; absence of animation curves does not prove morph absence.
- Retargeters have explicit source/target IK Rigs, chain mappings, retarget pose,
  root-motion policy, and contact validation.
- Gameplay promotion is reversible: original body, AnimBP, BlendSpace, hair
  runtime, and sockets remain recoverable.

## Melusina application

The V1 mocap pattern remains the reference:

`Rokoko -> SK_MocapSource -> IK_MocapSource -> RTG_Mocap_to_Melusina -> IK_Melusina_Body -> A_Mocap_*`

The Quaternius pattern is equivalent:

`Quaternius FBX -> SK_Quaternius/IK_Quaternius -> RTG_Quaternius_to_Melusina -> A_Q_Melusina_*`

After the target sequences are canonical, V2 is a mesh-contract problem, not a
second animation-retarget problem. The failed V2 attempt proved why the bind-pose
probe matters: a double-scaled canonical armature produced 100x translations even
though the UE Skeleton pointer and bone count looked valid. The corrected export
preserves rig scale (`rig_bake_factor=1.0`) and records a ~105.49 cm spine probe.

## Infinity Nikki lens

Adopt the separation of outfit appearance, ability/context policy, presentation
variant, unavailable-piece fallback, progression, and fixture evidence. Do not copy
proprietary shaders, clipping, monetization, or live-service rules. Melodia's
Substrate toon materials remain authoritative; Kawaii/cloth and the Flip Fluid cache
remain profile-driven presentation layers behind deformation and PIE gates.

## Primary references

- [Epic — Skeletons in Unreal Engine 5.8](https://dev.epicgames.com/documentation/en-us/unreal-engine/skeletons-in-unreal-engine)
- [Epic — Animation Retargeting](https://dev.epicgames.com/documentation/en-us/unreal-engine/animation-retargeting-in-unreal-engine?lang=en-US)
- [Epic — IK Rig Retargeting](https://dev.epicgames.com/documentation/en-us/unreal-engine/ik-rig-animation-retargeting?lang=en-US)
- [Epic — Retarget Manager](https://dev.epicgames.com/documentation/en-us/unreal-engine/retarget-manager-in-unreal-engine?lang=en-US)
- [Epic — Behind the Scenes of Infinity Nikki](https://www.unrealengine.com/developer-interviews/behind-the-scenes-of-infinity-nikki-tracing-a-glamorous-turn-to-an-unreal-open-world)
- [Infinity Nikki — Version 2.8](https://infinitynikki.infoldgames.com/en/news/560)
- [Infinity Nikki — Version 2.7 ability preview](https://infinitynikki.infoldgames.com/en/news/525)
