# Closeout Source Verdicts — 2026-08-11 (lane: opencode)

Source-only analysis for `CORE_GAMEPLAY_CLOSEOUT_PLAN_2026-08-11.md` Steps 3 + 5.
No editor access used (two UnrealEditor instances were running; one-editor rule).

## Step 3 — Damage-scalar sequencing verdict: PASS (by design, current path)

**Question:** can the rhythm scalar latch before the montage's damage notify reads it?

**Call order, quoted from `MelodiaRhythmCombatSubsystem.cpp` FinishSession (~L495-535):**

1. `bSessionActive = false; PushHighwayToHUD(false);` — highway cleared before broadcast.
2. HUD judgment/status writes (`SetJudgment`, `ShowBattleStatus`, `TriggerSparkleBurst`).
3. `OnRhythmComplete.Broadcast(Aggregate, Hits, Misses);` — listeners pop the rhythm
   input context / hide the highway.
4. `if (UObject* SkillToUse = DeferredSkill) { DeferredSkill = nullptr; InvokeStockUseSkill(SkillToUse); }`
   — comment: *"PendingDamageMultiplier was latched above, so the montage's damage
   notify now reads a real scalar instead of identity."*
5. `ConsumePendingRequest(...)` — clears only the request, **never** `PendingDamageMultiplier`
   (comment: "so the montage's damage notify still reads the latched scalar").

**Timing:** montage damage notify fires at 0.500–0.516s of a 1.29998s montage (measured
from the assets); the montage only *starts* at step 4, which runs after the latch
(steps 1-3). The historical ~2.5s gap (notify before latch) applied to the old
parallel-start pattern (`StartSession -> Branch -> UseSkill` fired on both branches in
`BP_BattleController`), which `UseSkillWithRhythm` replaced (`MelodiaRhythmCombatSubsystem.h:236-255`).

**Also confirmed:** `PendingDamageMultiplier` is deliberately NOT reset in FinishSession /
InvalidateSession (`MelodiaRhythmCombatSubsystem.cpp:150-175` comment); `StartSession`
owns the reset. Do not "fix" it (closeout Do-Not-Fix list agrees).

**Verdict:** rhythm CAN affect damage on the current path, provided the BP side calls
`UseSkillWithRhythm` (deferred invocation) and no `OnRhythmComplete` listener
double-invokes the skill (`cpp:534` documents the exactly-once guard; `cpp:716` drops
the deferral cleanly on invalidation). Campaign 1's A/B (`melodia.Rhythm.Disable 0|1`)
is therefore meaningful on this path. No HOLD from sequencing.

## Step 5 — RestorePartyAfterBattle: WIRED 2026-08-11 (cloud foundation)

- `MelodiaJRPGPostBattleLibrary` map field lookup corrected: `curentMP` → `currentMP`
  (matches unit-instance property + JRPG catalog).
- Call site: `UMelodiaExternalJRPGBridgeSubsystem::HandleBattleOver` restores via the
  live `BP_BattleController` **before** `CompleteBattle` / Quill resume.
- Still needs a closed-editor build + one PIE defeat/victory to observe
  `MELODIA_RECOVERY restored N player unit(s)` in the log.

## Notes

- Two UnrealEditor instances were running (PIDs 35236, 38220, both started 2026-08-11
  15:02-15:03, same project, both `-log`) with Monolith on 9316 held by 35236. Per the
  one-editor rule, no editor work (PIE, graph reads, T3D) was attempted; this document
  is source-only. Confirm one instance before Campaign 1.
