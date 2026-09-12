# Melodia Enemy Rig Handoff

This handoff defines the minimum battle-presentation contract for the first
three enemies. Do not reuse the Melusina skeleton or AnimBP.

## Shared Contract

Use UE centimeters, a consistent forward axis, and a clean neutral bind pose.
Keep the root at ground contact for grounded enemies and at the visual pivot
for floating enemies. Avoid baked nonuniform scale.

Required semantic bones or sockets:

- `root`
- `body` or `pelvis`
- `spine_01` and `chest` where the silhouette supports them
- `head` or `core`
- `aim_socket`
- `hit_socket`
- `center_socket`
- `vfx_socket`

Optional bones should be added only when they improve the silhouette or a
specific gameplay cue. Export one neutral preview pose as well as the bind
pose. Root motion is disabled for this first battle-only pass.

## Sakura Phantom

- Floating body with a readable vertical idle sway.
- `petal_root`, `petal_l`, and `petal_r` controls for the volley release.
- `aim_socket` at the petal attack origin.
- Preserve a stable float height during hit reactions.
- Break pose should visibly lose lift; defeat may disperse petals.

Combat identity: fast Radiant pressure, `SakuraPhantom`, `Petal Volley`,
128 BPM.

## Stone Golem

- Grounded root with stable feet and low center of mass.
- Separate chest, shoulder, forearm, and fist controls where available.
- `hit_socket` and `vfx_socket` at the impact-facing chest/fist region.
- Keep broad anticipation and recovery poses readable from the battle camera.
- Break pose should visibly sag or stagger; defeat may collapse or fragment.

Combat identity: slow Stone tank, `StoneGolem`, `Stone Slam`, 100 BPM.

## Crystal Shard

- Pivot/core-driven rig; humanoid controls are unnecessary.
- `crystal_core`, `crystal_tip`, and optional `shard_ring` controls.
- Stable rotation axis and center pivot.
- `hit_socket` at the visual center, not the collision origin.
- Break pose should pulse, fracture, or dim; defeat may shatter or fade.

Combat identity: short Forte tutorial encounter, `CrystalShard`,
`Resonance Ping`, 120 BPM.

## Export Gate

Before handing assets to Unreal, verify scale, forward axis, bind pose, socket
names, collision footprint, and that no animation references a Melusina or
`SK_Melusina_Skeleton_OLD` skeleton. The engine integration supplies the
Blueprint callbacks for intent, hit, break, and defeat; the rig should not own
combat authority.
