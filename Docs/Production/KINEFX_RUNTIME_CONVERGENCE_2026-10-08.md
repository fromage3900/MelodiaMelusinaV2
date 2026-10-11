# KineFX Runtime Convergence — Audit + Universal System Plan — 2026-10-08

Read-only audit run against the live editor (GUI PID 21012, Monolith :9316). Evidence in
`Saved/Audit/MelusinaKineFXAudit_20261008/`. No asset was mutated, no clip edited, no skeleton touched.

## 1. Headline: two canon claims are now STALE

Measured live, not read from docs:

| claim in MELUSINA_RUNTIME_CANON | live measurement | verdict |
|---|---|---|
| "the six SparrowArchery clips carry the reference-pose arm defect — OPEN" | all six **PASS** 15.774 / 28.561 / 28.615 (±0) | **RESOLVED** — the clips were fixed at some point; the canon was never updated |
| "raw retarget output into SK_Melusina_Skeleton is known-defective" | all 13 live Melusina clips pass arm canon | true as a *rule*, not as a *current defect* |

Receipts: `fleet_arm_audit.json` (13 clips), `sparrow_frozen_audit.json` (6 frozen clips).

**Do not re-run the arm-correction recipe on those clips.** It would overwrite good animated arm
motion with a constant pose. That is a regression, not a fix.

## 2. The real remaining runtime defects

Arm convention is *not* the problem. These are:

### A. Loop seams on cycling clips (the actual visible pop)

| clip | foot_l seam | foot_r seam | note |
|---|---:|---:|---|
| A_Shin_Cast | 18.012 cm | 25.693 cm | worst in the project |
| A_Melusina_Sprint | 13.988 | 12.095 | |
| A_Melusina_JumpLoop | 10.524 | 14.304 | airborne, less visible |
| A_Melusina_Land | 8.447 | 3.315 | |
| A_Melusina_Walk / Run | 5.318 | 13.127 | walk and run are the same numbers — suspicious |
| RMB_Drawback | 8.248 | 8.294 | |
| RMB_Fire | 5.858 | 5.279 | |
| Idle / Primary_Fire_* / RMB_Loop | <0.2 | <0.2 | clean |

### B. Root motion is not enabled on anything

`get_sequence_info` returns null for root-motion on all audited clips. Root drift measures 0.000 cm,
so the clips are in-place — correct for a blendspace-driven locomotion rig, but it means **glide,
jump and any root-moved move currently rely on code, not motion**. The 8,042 cm glide deviation
recorded in CURRENT_STATE is a symptom of this, not of the clip's pose data.

### C. Foot/floor contact is unresolved and is NOT a clip problem

`foot_l_min_z`: idle +2.577, walk +2.458, run +2.458, sprint +2.263 — feet sit **above** the floor in
pose space and are expected to be corrected by FootPlacement. JumpStart dips to −1.831 and A_Shin_Cast
to −18.482. The boot penetration (~30 cm) is therefore a **solver/ground-reference** problem, which
matches the two rejected canaries in CURRENT_STATE (root_x offset broke cuff fit; mesh lift broke the
anatomical foot). Geometry edits and clip edits cannot fix it.

## 3. What KineFX is and is not here

Houdini 22.0.368 is installed (`/c/Program Files/Side Effects Software/Houdini 22.0.368`).
Houdini **KineFX** is a *rigging and motion-editing* framework (rig-from-skeleton, rig pose,
motion-clip, biped, full-body IK, mocap retarget). It is not a UE retargeter.

Monolith's retarget stack is UE's native **IK Rig / IK Retargeter**, which is the correct runtime
owner for UE consumption. KineFX belongs *upstream*:

| stage | owner | why |
|---|---|---|
| source motion authoring / mocap cleanup / seam repair / full-body IK | **Houdini KineFX** | procedural, batch, deterministic, headless, reversible |
| UE retarget into SK_Melusina_Skeleton | **UE IK Retargeter** (Monolith) | must run where the canonical skeleton lives |
| runtime playback, FootPlacement, layered blend | **ABP_Melusina_Current** | existing owner, do not fork |

So: KineFX does not *replace* the UE retarget lane. It replaces the **hand-fixing of clips one at a
time** that is currently the bottleneck.

## 4. The universal system — one contract, three owners

`specs/universal_rig/rig_contract.v1.json` already carries the bone map, arm canon and the 11-filter
layer mask. It is the right seam and it is already correct. Converge everything onto it:

```
   Houdini KineFX (source)          UE (runtime)
   ----------------------           ------------------------------
   clip in  ->  seam repair   ->    UE IK Retargeter -> SK_Melusina_Skeleton
             ->  FBX out             ->  arm-canon verify  ->  ABP_Melusina_Current
             ->  manifest             ->  FootPlacement     ->  runtime
                     |                             |
                     +------ specs/universal_rig/rig_contract.v1.json ------+
                                (single source of truth for names, canon, mask)
```

**Gate every clip with one script, in one place.** A clip is shippable only if it reports:
arm canon PASS, loop seam <1 cm, root-motion flag as intended, foot min-z in range for its class.
That script is the convergence mechanism — not a new framework.

## 5. Ordered work (bounded, reversible, duplicate-first)

1. **Update the canon** (`MELUSINA_RUNTIME_CANON_2026-10-05.md` §4): mark the Sparrow arm defect
   RESOLVED with these receipts; add the "do not re-apply the recipe" warning. Owner-facing doc edit.
2. **Author the KineFX seam-repair tool** at `Tools/Houdini/kinefx/melusina_seam_repair.py`:
   read clip FBX → match first/last pose → blend boundary keys → write to a NEW folder. Never in place.
   Target the worst three first: A_Shin_Cast (18/25.7 cm), Sprint (14/12 cm), Walk (5.3/13.1 cm).
3. **Author the one gate** at `Tools/animation/verify_clip_gate.py` (the four checks above) so every
   future clip — KineFX, Shinbi, ACFU, mocap — passes the same door.
4. **Fix foot contact as a solver problem**, not a clip problem: the c_foot_ik_l/r canary already
   described in CURRENT_STATE (copy anatomical foot pose to separate IK targets before FootPlacement,
   then native LegIK before Kawaii). KineFX cannot help here; this is ABP work.
5. **Unblock `skeleton_fbx_export`** (C6 in the staged plan) so the universal-rig lane stops waiting
   on it. That is the one gate on the whole "universal system" story.

## 6. Explicitly not doing

- Not editing the frozen skeleton, the frozen Sparrow clips, or the WaveHarp shape keys.
- Not re-running `copy_bone_pose_between_sequences` on clips that already pass (regression risk).
- Not building a second retargeter, a second compiler, or a parallel animation framework.
- Not touching boot geometry — geometry is ruled out by two rejected canaries.
- No git/p4 operations; receipts stay under `Saved/Audit/`.
