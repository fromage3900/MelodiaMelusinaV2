# Canonical rig control map — character_rig (FinalUERig43)

Measured on `character_rig`, 759 bones / 234 deform. Method: set the bone,
force a depsgraph update, evaluate `Melusina` to_mesh, take **max vertex
displacement** against rest. Centroid is the wrong metric here — it reads
0.0000 on bones that visibly move the mesh.

## The rig has three layers

```
c_*        control bones        the handles you pose
*_nostr    IK targets           influence 1.00 — these drive the limbs
FK c_*_fk  FK controls          influence 0.00 — DEAD, do nothing
DEF-*      deform bones         constraint-driven, do not set directly
```

Setting a DEF bone or an FK control directly produces **zero** movement,
because a constraint re-evaluates over it. This is the trap.

## SPINE / NECK / HEAD — pose by ROTATION

Rotate 0.5 rad on X, max vertex displacement:

```
c_root_master.x     0.5136     <- whole body
c_neck_master.x     0.4870
c_spine_01.x        0.4517
c_spine_02.x        0.3915
c_spine_03.x        0.3290
c_subneck_1.x       0.2685
c_neck.x            0.2323
c_head.x            0.1968     <- head turns / nods
c_shoulder.l        0.0836     <- Z axis
c_shoulder.r        0.0855     <- Z axis
c_root.x            0.0775
```

## ARMS / LEGS — pose by TRANSLATION, not rotation

The limbs are IK. Rotating the IK control barely moves anything (0.037–0.11);
**translating** it is the real handle. Translate 0.25 units:

```
c_hand_ik.l   0.2335   (Z)     <- hand / arm position
c_hand_ik.r   0.2389   (X)
c_foot_ik.l   0.2598   (Z)     <- foot / leg position
c_foot_ik.r   0.2599   (Z)
```

IK constraint state (confirmed):

```
leg_ik_nostr.l/r      chain=2  influence=1.00   <- ACTIVE
forearm_ik_nostr.l/r  chain=2  influence=1.00   <- ACTIVE
leg_ik.l/r            chain=2  influence=0.00   <- inactive
forearm_ik.l/r        chain=2  influence=0.00   <- inactive
```

## BODY PLACEMENT — translation

```
c_root.x         0.3204  (Y)
c_root_master.x  0.2867  (X)
c_head.x         0.2517  (Z)
```

## DEAD — do not use (all measured 0.0000)

```
c_arm_fk.l/r   c_forearm_fk.l/r   c_hand_fk.l/r
c_thigh_fk.l/r c_foot_fk.l/r      c_toes_fk.l/r
c_p_root.x     c_p_spine_00..03.x c_p_neck.x  c_p_neck_01.x
c_root_bend.x  c_stretch_arm.l
spine_01/02/03.x   neck.x   root.x   foot.l   toes_01.l   hand.l
arm_stretch.l  thigh_stretch.l
```

Every `c_p_*` bone is a parent/space bone — inert by design.

## Bone naming: this rig vs the EXPORT rig

These are different rigs. Pose tables do not transfer.

```
canonical character_rig        EXPORT MelusinaRig
  c_spine_02.x                   spine_02_x
  c_head.x                       head_x
  c_neck.x                       c_neck_x
  c_hand_ik.l (translate)        c_arm_fk_l (rotate)
  root.x  foot.l  toes_01.l      head_x  c_neck_x  arm_stretch_l
  dot notation                   underscore notation
```

## Texture portability warning

All 67 image paths in this file point at `C:\Users\froma\...` and
`G:\MelodiaMelusina\...`. **Every file is missing on the laptop.** The character
renders anyway because **53 of 67 images are packed**. Never rely on the paths;
never unpin the packing.

14 images cannot be packed at all (their source files are gone upstream):
`bow_Alpha/BaseColor/Emission/Metallic/Roughness`, `SHAWL_*`,
`DPM2.004_BaseColor`, `Material.020_Alpha/Emission`.

## Also: corneas do not render

`L_Cornea` and `R_Cornea` carry `hide_render=True` in the source. Eyes will read
flat. Flip both flags. This is upstream in `FinalUERig43`, so it affects every
use of the rig, not just this animatic.