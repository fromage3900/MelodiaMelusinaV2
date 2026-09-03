# Kawaii Physics Placement Audit — 2026-08-14

## Verdict

Melodia has a Kawaii Physics runtime setup and a disposable placement probe, but it
does **not** currently have a reusable, production-ready Kawaii Physics placement
Blueprint.

### What exists

- KawaiiPhysics plugin `1.21.0`, configured for UE 5.8, is present at
  `Plugins/KawaiiPhysics`.
- `/Game/Melodia/Characters/Melusina/Hair/ABP_Melusina_WaterHair` contains one
  `AnimGraphNode_KawaiiPhysics` rooted at `hair_root`.
- Existing physics assets/data assets include
  `SK_Melusina_PhysicsAsset`, `SK_Melusina_FIXED_Hair_PhysicsAsset`,
  `DA_Melusina_HairCollisionLimits`, and `DA_Melusina_SkirtCollisionLimits`.
- `/Game/MelodiaIntegration/Tests/BP_KawaiiPhysicsPlacementProbe` exists on disk;
  its compile/export and a live spawn were observed, but map persistence, root-body
  compatibility, limits binding, and deterministic PIE reset remain unverified.
- The repository contains a generic
  `/Game/EnvSandbox/Blueprints/BP_PhysicsPlacementSpawner` plus
  `Tools/build_physics_placement_spawner.py`.

### What the generic placement spawner actually is

`BP_PhysicsPlacementSpawner` is an Actor test utility with a movable
`StaticMeshComponent` named `PlacementMesh`. Its graph is intended to run
`BeginPlay → SetSimulatePhysics(PlacementMesh, true)` for pillow/bed drop tests.
It does not own an AnimBP, Kawaii node, skeletal mesh, bone root, limits asset,
wind profile, or placement-readback contract.

The asset and builder are ignored by the current repository rules, so they are not
tracked production infrastructure. Do not treat their presence on disk as a
reviewed, reproducible project asset.

### Current hair evidence

`Saved/Audit/melusina_hair_physics_chain.json` is a read-only audit from 2026-07-27,
not fresh live proof. It reports:

- production hair contract: true;
- exploration hair contract: true;
- battle presentation contract: false;
- one Kawaii node on `ABP_Melusina_WaterHair`;
- root bone `hair_root`;
- no `LimitsDataAsset` or bone-constraints asset bound on that node.

The battle result is especially important:
`/Game/Experiments/MelodiaJRPG/BP_MelusinaSwordsman_Presentation` uses
`ABP_Melusina_JRPGPresentation` and is not covered by the production/exploration
hair contract. Kawaii Physics is therefore not yet a universal Melodia character
presentation contract.

## Required reusable fixture

Finish the existing dedicated, tracked fixture after the T3D postcondition repair:

`/Game/MelodiaIntegration/Tests/BP_KawaiiPhysicsPlacementProbe`

It should contain:

1. A skeletal mesh component using the canonical Melusina skeleton or a deliberately
   minimal Kawaii test skeleton.
2. A named physics-driven child mesh or hair/skirt mesh.
3. The intended AnimBP and exactly one Kawaii node with explicit `RootBone`.
4. Explicit hair/skirt limits and bone-constraint DataAssets.
5. A small placement/readback graph that records initial transform, simulated pose,
   reset pose, and teardown state without mutating campaign save data.
6. A disposable fixture map and evidence envelope with compile, node, asset-reference,
   and runtime checks.

## Acceptance contract

The fixture is ready when it proves:

- plugin/module loads in editor and packaged Development build;
- target skeletal mesh, skeleton, AnimBP, physics asset, limits asset, and root bone
  all resolve;
- Kawaii simulation starts from the intended reference pose;
- hair/skirt follows the character while preserving the expected attachment contract;
- limits prevent explosive or unbounded motion;
- reset/teleport/travel/PIE teardown returns to a stable pose;
- battle presentation, exploration presentation, and preview fixture agree on the
  same ownership rule;
- no placement test calls the campaign save, travel, narrative, or battle authority.

## Next execution order

1. Re-run the read-only hair physics audit with the editor once available.
2. Inspect `ABP_Melusina_Current`, `ABP_Melusina_JRPGPresentation`, and
   `ABP_Melusina_WaterHair` for Kawaii node/root/limits consistency.
3. Decide whether the battle presentation should use the canonical hair component,
   a dedicated battle presentation mesh, or an explicitly documented no-hair mode.
4. Bind and verify the appropriate limits DataAssets; do not tune by visual guesswork.
5. Build the dedicated probe through the corrected T3D transaction contract.
6. Only then promote the pattern into a reusable `BP_MelodiaPhysicsPresentation_Base`
   or equivalent template.

## Important boundary

Kawaii Physics is an animation/presentation capability. It must not become a second
character, traversal, battle, or persistence authority. The placement probe is a
fixture and debugging surface, not gameplay logic.
