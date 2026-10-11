# START HERE — Houdini AnimationDoctor Lab — 2026-10-06

**Current mission:** use the college full Houdini Education licence as a bounded KineFX animation-diagnostics lab while Brennan handles hero-render framing and presentation.

## Canonical detailed plan

Read this first:

`Docs/Houdini/FoundryDay_2026-09-24/README.md`

Then jump to:

`## 2026-10-06 update — AnimationDoctor lab day (current priority)`

That section is the authority for today's work. The older Foundry Day world-building gates remain backlog and are not superseded or marked complete.

## Worker mission

Build and validate a reusable, non-destructive:

`HDA_Melodia_AnimationDoctor`

First specimen set:

- `A_Shin_Idle`
- `A_Shin_Idle_pose`
- `A_Shin_Idle_stand`
- `A_Shin_Cast`
- canonical current Melusina target skeleton / runtime retarget assumptions

Diagnose:

1. REST — hierarchy, rest transforms, joint orientation, scale/bone-length mismatch.
2. ROOT — trajectory, offsets, floating, discontinuities/reference-pose jumps.
3. CONTACT — foot contacts and sliding; architecture should later support hands/hooves/grips.
4. JOINT HEALTH — angular velocity, transform discontinuities, extreme transforms; rank bad joints/frames.
5. RETARGET — source vs target vs retarget-result comparison.
6. EXPORT — only deterministic evidence-backed corrections, written as new outputs.

## Authority boundaries

- UE 5.8 remains runtime authority.
- The canonical Melusina skeleton remains target authority.
- Do not replace UE's IK Retargeter.
- Do not create a second canonical animation pipeline.
- Do not overwrite source animations.
- Do not restore stale `BS_GodFile.uproject` or `CURRENT_STATE.md` from old history.
- Source commit `6ca411e1d5` is a bounded recovery/specimen reference, not branch authority.
- Prefer diagnosis and evidence over automatic smoothing/fixing.

## Evidence

Store small reports/captures under:

`Saved/Audit/houdini_foundry/animation_doctor/<clip>/`

Keep large caches/intermediates under `Saved/HoudiniFoundry/` or college scratch. Do not commit caches.

## Second specimen

After at least one Melusina clip produces useful diagnostic proof, test Choral Sheep for hoof contacts and locomotion phase. Only then evaluate deterministic phase offsets, speed variation, and bounded head/ear/tail secondary variation.

## Success gate

Before expanding scope, demonstrate one Shinbi → Melusina clip where the tool can answer:

> What is actually wrong, on which joints and frames, and is the problem source motion, skeleton/rest pose, retarget assumptions, root motion, contact, or UE presentation?

If that cannot be answered from evidence, improve the diagnostic tool rather than modifying runtime architecture.

## Human/agent split

**Muse Spark:** KineFX diagnostic network, measurements, reports, evidence.

**Brennan:** hero-render framing, lighting/composition, visual judgment, explicit review gates.

Do not make Brennan watch long cooks. Use the existing Foundry evidence/caching conventions.

## Git startup

Always synchronize/read current authority before doing work:

```bash
git fetch origin
git show origin/main:START_HERE_HOUDINI_2026-10-06.md
git show origin/main:Docs/Houdini/FoundryDay_2026-09-24/README.md
```

Do not infer current state from a stale local checkout.
