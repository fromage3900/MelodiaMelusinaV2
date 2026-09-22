# Melusina Re-export Runbook — Blender / Cascadeur

**What this teaches:** which Melusina defects are authored upstream, what each one actually is at
bone level, and what order to fix them in so UE work isn't blocked. Measured live 2026-09-21 unless
a source is named.

Companion: `Docs/Handoffs/CLAIREON_MELUSINA_PHYSICS_BOW_HANDOFF_2026-09-20.md` and the
Melusina Rig Postmortem artifact (2026-08-15).

---

## 0. Do these two in one Blender pass

They touch the same file and both gate downstream work.

---

## 1. Root motion on locomotion clips — BLOCKER

**Measured:** `root` and `c_traj` have **exactly zero** translation across the full clip.
`root_x` carries 3.81 uu of drift over 1.167 s (≈3.3 uu/s) — that is noise, not travel.

| Clip | Length | root Δ | c_traj Δ | root_x Δ |
|---|---|---|---|---|
| `A_Melusina_Idle_Mocap_RootX` | 0.500 s | 0 | 0 | — |
| `A_Melusina_Walk_Mocap_RootX` | 1.167 s | 0 | 0 | (−3.14, −2.17) |
| `A_Melusina_Run_Mocap_RootX` | 1.167 s | 0 | 0 | (−3.14, −2.17) |
| `A_Melusina_Sprint_Mocap_RootX` | 0.917 s | 0 | 0 | (6.71, −8.09) |

All four: `enable_root_motion = False`, `root_motion_root_lock = REF_POSE`.

**Why it blocks everything:** a BlendSpace axis is a contract — *this clip is what she looks like at
N uu/s*. With no root motion the authored speed is unknowable from the asset, so every axis position
is a guess and the feet slide. No amount of blend tuning fixes an error that lives in the axis.

**Do:** re-export with root motion baked and preserved, root **unlocked**. Once that exists the real
speeds are measurable and the BlendSpace can be placed correctly for the first time.

**Open question for you:** Sprint is confirmed a distinct clip (different length, different root_x
delta). Walk and Run share both length and root_x delta — that is *suggestive* of one clip retimed,
but identical near-zero drift does not settle it. Worth a look while you're in there.

---

## 2. Cornea re-weight — BLOCKER

From the 2026-08-15 postmortem, still unfixed and observed again today in animated frames.

The 100-vertex cornea section of the body mesh is skinned to a bone called `eyes`. Walk its
ancestry and it never reaches the head:

```
eyes -> MCH-eyes_parent -> root          (severed; constraint lost on export)
head_x -> neck_x -> spine_03_x -> spine_01_x -> root_x -> c_traj -> root   (correct)
```

`MCH-eyes_parent` is a Rigify eye-aim target driven by a **Blender constraint**, and constraints do
not survive FBX export. In Unreal it becomes a plain child of `root`, so when a clip animates
`head_x` the head moves and the eyes stay put.

**Why it keeps passing review:** at the reference pose everything is coincident, so every *static*
capture looks correct. It only separates once a clip animates the head — which is exactly where it
showed up in today's bow-montage frames and never in the idle ones.

**Do:** move the 100 cornea verts onto `DEF_eye.L` / `DEF_eye.R`, which already exist and already sit
correctly inside the head:

```
DEF_eye.L -> MCH-eye.L -> master_eye.L -> ORG-face -> head.x
```

Weights only — no skeleton change, no retargeter change, no animation change — so the V1 clips keep
working. The postmortem's script dry-runs by default, writes a weight backup, verifies the
`faceit_left_eyes_other` (50) ∪ `faceit_right_eyes_other` (50) split is exact with zero overlap, and
aborts rather than inventing a midline.

---

## 3. Finger controllers — needs your decision first

Same defect class. Phalanges 2 and 3 are skinned to ARP controllers (`c_index2_l`, `c_thumb3_r`)
which the export also flattens onto `root`.

| Mesh | Violations | Composition |
|---|---|---|
| `EXPORT_Body` | 21 | 20 finger controllers + `eyes` |
| `EXPORT_Accessories` | 20 | finger controllers |
| `EXPORT_Boots` | 0 | clean |
| `EXPORT_Shirt` | 0 | clean |
| `EXPORT_Skirt` | 0 | clean — all kilt bones under `root_x` |

In Blender these **are** correctly parented under `hand.l`; it is the FBX export that orphans them.
So this is either a re-weight onto the `*_ref` chain that becomes Unreal's deform skeleton, **or** an
export-config change. Those give different results — don't guess.

---

## 4. Hair re-rig — this is why it reads as a helmet

**Measured:** 148 bones = 2 roots + **73 two-bone strand chains**, on its own skeleton
`SK_Melusina_Hair_Skeleton` (separate from `SK_Melusina_Skeleton`, which is why it can't leader-pose
and needs `CopyPoseFromMesh` in its AnimGraph).

A two-bone strand can only rotate **rigidly about its root**. It cannot curve along its length. That
is the moulded silhouette, and no damping/stiffness value reaches it.

**Do:** a genuine multi-segment hair rig — 3–5 joints per strand — with weights redistributed along
each strand. This is the Cascadeur/Blender job, not a tuning job.

**Already landed on the UE side (don't redo):** `bBoneSubdivisionCollisionOnly` was `True`, so the
**220 inter-bone dummy bones** KawaiiPhysics already generates at `BoneSubdivisionCount = 1` were
used for collision only and never simulated. Set to `False` on 2026-09-21 — those 220 bones now
simulate at zero extra bone cost. Verified stable in PIE (hair bone z 129–182, no explosion). It
helps; it does not replace the re-rig.

The accepted damping tune is unchanged and verified not drifted: Damping .18, WorldDamping .50/.50,
Stiffness .08, LimitAngle 60, Wind .20, WarmUp on.

---

## 5. Hat, eyelashes, shirt rig

On the rig, staged for re-export.

**Note for anyone auditing from the UE side:** slot naming on this body is arbitrary —
`MI_Melusina_IRISFRONT_001` sits on a slot literally named `Gradient__Radial__002`. Searching UE by
asset name proves nothing about what exists upstream. Don't conclude absence from a name search.

On reimport the battle wardrobe picks garments up automatically, **provided they land on
`SK_Melusina_Skeleton`** — see §6.

---

## 6. Skirt skeleton consolidation — deferred, known

The R2 skirt carries its own companion skeleton,
`SK_Melusina_V2_Skirt_R2_SmoothChains_Skeleton`. The wardrobe **correctly refuses** it: leader-pose
sharing copies the body's bone transforms by index, so a garment on a different skeleton would
render, just wrongly. That refusal is a feature, not the bug.

Body, Shirt, Boots and Accessories are all already on `SK_Melusina_Skeleton` and equip fine.

Current workaround: the capture level carries a standalone `Portfolio_R2_Skirt` actor.
Real fix: reimport the corrected weights against the canonical skeleton, or explicitly bless the
duplicate skeleton.

---

## 7. Capture clip — use the corrected shoulders, not the production montage

For stills, **do not** play `AM_Melusina_BowAttack_Bound`. It carries the hiked shoulders:
`c_shoulder_l/r` remain at reference pose for all 40 keys while the deform tracks `shoulder_l/r`
carry the large rotations. That is baked animation/retarget pose, not KawaiiPhysics or V2 mesh
placement.

Use `/Game/Melodia/Characters/Melusina/Portfolio/A_Melusina_BowAttackV2_PortfolioShoulders`
(shoulders slerped 55% toward reference) played as a **dynamic montage on `DefaultSlot`**.

If you promote the shoulder fix to production, rebuild a proper persistent montage from the
corrected sequence in-editor and **confirm non-zero duration** before replacing any binding — the
previously generated container reported duration 0 and was deleted.

---

## 8. The gate that should catch all of this

One rule, checkable offline from data already in the repo:

> **Every skinned bone must descend from `root_x`.**

A bone outside the pelvis subtree can only move if an animation explicitly keys it — which is exactly
how the cornea defect hid behind the V1 mocap library for months. The V1 clips were baked in Blender
*with constraints evaluated*, so they carry explicit keys on `eyes` and on every controller bone; a
freshly retargeted clip keys only the chained deform bones.

Suite: `test_melusina_skin_topology_contract`. The 41 existing violations are recorded as accepted
debt so only *new* orphan bindings fail. After the cornea and finger fixes, that baseline should
drop — lower it deliberately rather than leaving the old number in place.

---

## Order

1. Root motion re-export **+** cornea re-weight — one Blender pass, both gate downstream.
2. Reimport body and accessories; hat / eyelashes / shirt ride along if ready.
3. BlendSpace re-placement from measured speeds (UE side, first time the numbers are real).
4. Finger controllers, once the export-vs-reweight decision is made.
5. Hair multi-segment re-rig.
6. Skirt skeleton consolidation.

---

## Sources

Live Claireon reads: `AnimationLibrary.get_bone_pose_for_time`, `blend_space_inspect`,
`uobject_inspect`, `level_list_actors`, KawaiiPhysics node properties.
Docs: Melusina Rig Postmortem (2026-08-15),
`Docs/Handoffs/CLAIREON_MELUSINA_PHYSICS_BOW_HANDOFF_2026-09-20.md`.
No claim here rests on a static capture alone. Walk-vs-Run clip identity is explicitly left open.
