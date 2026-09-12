# Melodia Presentation / JRPG Skill Slice

**Status:** isolated adapter compiled and saved; impact-frame validation pending; no production asset mutation  
**Mechanical authority:** TurnBased JRPG template  
**Presentation source:** Melusina assets and selected Melodia presentation work

## Decision

The first slice will not reparent a JRPG unit to `AMelodiaSmokeCharacter`.
`AMelodiaSmokeCharacter` owns exploration camera, input, party registration,
glide, movement, and menu behavior, which conflicts with the proven JRPG battle
unit lifecycle.

Instead, use a disposable child of `BP_SwordsmanPlayerUnit` in the UE5.8 JRPG
lab. Preserve JRPG stats, targeting, turn scheduling, damage, and battle
completion. Replace only the visual presentation with Melusina's mesh, a clean
lab-only animation Blueprint, and one montage.

```text
JRPG selects and validates skill
  -> presentation adapter requests montage
  -> montage reaches exactly one impact notify
  -> BP_UseSkillN invokes existing JRPG UseSkill resolution
  -> montage/presentation completes
  -> JRPG advances the turn
```

## Slice A: single-target basic attack

Mechanical owner:

- `BP_SwordsmanPlayerUnit`
- `BP_PlayerUnitBase`
- `BP_BattleController`
- existing ordinary attack/skill flow
- `BP_UseSkillN` animation notify

Presentation:

- `SK_Melusina`
- `SK_Melusina_Skeleton`
- `ABP_Melusina_JRPGPresentation` (lab-only, plain `AnimInstance`)
- `AM_Mocap_BasicAttack`
- source animation `A_Mocap_MercyStab`

## Implemented isolated adapter

Created under `/Game/Experiments/MelodiaJRPG`:

- `ABP_Melusina_JRPGPresentation`
  - targets `SK_Melusina_Skeleton`;
  - plays `A_Melusina_Idle` through `DefaultSlot`;
  - compiles with 0 errors and 0 warnings.
- `BP_MelusinaSwordsman_Presentation`
  - derives from `BP_SwordsmanPlayerUnit`;
  - adds `MelusinaPresentationMesh`;
  - assigns `SK_Melusina` and the clean lab AnimBP;
  - assigns `AM_Mocap_BasicAttack` as `attackAnimationMontage`;
  - hides the inherited JRPG mesh on BeginPlay;
  - compiles with 0 errors and 0 warnings.

The inherited JRPG class remains the mechanical owner. No production package
was edited.

## AnimBP compatibility finding

`ABP_Melusina_Current` is not safe to reuse as the first isolated adapter. A
compile attempt in the disposable lab exposed hard dependencies on:

- `/Script/MelodiaCore.MelodiaLocomotionAnimInstance`;
- `/Script/KawaiiPhysicsEd`;
- an unavailable custom-version GUID.

UE5.8 then asserted in Property Access compilation and closed the lab editor.
The production project was not open or modified. This confirms that importing
the production AnimBP would also import the unstable runtime/plugin surface the
slice is designed to avoid. The clean plain-`AnimInstance` adapter is therefore
the current approved route.

## Attack timing evidence

`AM_Mocap_BasicAttack` is 6.825 seconds long, uses `DefaultSlot`, and currently
contains zero notifies. Its source `A_Mocap_MercyStab` is 819 frames at 120 fps
and has no root motion.

Read-only right-hand trajectory sampling places the authored action between
approximately 2.0 and 5.5 seconds, with strongest forward extension near 4.0
seconds. This narrows the inspection window but does not by itself prove the
contact frame. Exactly one `BP_UseSkillN` notify will be added only after visual
scrubbing confirms contact.

Acceptance:

- command is accepted once;
- montage starts once;
- exactly one impact callback occurs;
- JRPG applies damage once;
- target reaction and UI update occur;
- turn is released once after presentation;
- missing montage/notify times out safely without deadlocking battle.

## Slice B: basic heal

After the attack passes, repeat the contract with:

- `BP_PriestPlayerUnit`;
- `BP_BasicHeal`;
- `AM_Mocap_Skill`, after verifying its authored sequence;
- intended source animation `A_Mocap_FairyWand`;
- existing `CUE_Heal`;
- the same single-impact and single-completion guarantees.

## First-pass exclusions

- no `AMelodiaSmokeCharacter` parent;
- no MelodiaCore combat/state authority;
- no rhythm judgement or beat-window dependency;
- no boss, multi-hit, focus, or true-strike skill;
- no QuillScript dependency;
- no hair physics requirement;
- no production JRPG Blueprint edits;
- no gameplay save-schema changes.

Hair, water material, camera embellishment, and rhythm-aware timing may be
evaluated only after the basic attack resolves correctly under JRPG authority.

## Timing telemetry

Record:

- command accepted time;
- montage start time;
- impact notify time;
- JRPG effect resolution time;
- presentation completion time;
- turn release time;
- duplicate, missing, or late callback count.

The initial experiment measures authored feel; it does not transfer timing
authority to MelodiaCore. A later optional test may compare impact placement
against beat phase while preserving deterministic JRPG resolution.

## Source locations

JRPG lab:

`C:\EnvironmentPortfolio\CompatibilityLabs\TurnBasedJRPGUE58`

Melusina presentation source:

`C:\EnvironmentPortfolio\BS_GodFile\Content\Melodia\Characters\Melusina`

Relevant production C++ reference:

`C:\EnvironmentPortfolio\BS_GodFile\Plugins\MelodiaCore\Source\MelodiaCore\MelodiaSmokeCharacter.*`

## Next editor steps

1. In the JRPG UE5.8 lab, visually scrub `AM_Mocap_BasicAttack` /
   `A_Mocap_MercyStab`, concentrating on 2.0–5.5 seconds.
2. Confirm the intended contact frame and add exactly one `BP_UseSkillN`
   notify.
3. Re-query the montage and verify a notify count of exactly one.
4. Compile and save the experimental AnimBP and unit Blueprint.
5. Wire the experimental unit into a disposable battle test only.
6. Run one battle and capture the timing observations above.
