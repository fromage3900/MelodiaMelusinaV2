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

## Step 5 — RestorePartyAfterBattle: WIRED 2026-08-11

- `MelodiaJRPGPostBattleLibrary.h` — `UFUNCTION(BlueprintCallable) RestorePartyAfterBattle(UObject* BattleController)`.
- Implementation walks `playerUnits` + controller persistent map; map-side MP field is
  **`curentMP`** (typo confirmed 2026-08-11 via Monolith `export_asset_text` on
  `/Game/TurnBasedJRPGTemplate/Blueprints/Structs/S_PlayerUnitData` — do not “fix” it).
- **Call site WIRED** on foundation: `UMelodiaExternalJRPGBridgeSubsystem::HandleBattleOver`
  restores via live `BP_BattleController` **before** `CompleteBattle` / Quill resume.
- Still needs closed-editor build + one PIE defeat/victory to observe
  `MELODIA_RECOVERY restored N player unit(s)` in the log.

**Verdict:** spelling RESOLVED (live reflection = `curentMP`); call-site WIRED (cloud foundation).
Observe in PIE before claiming gate evidence.

## Notes

- Two UnrealEditor instances were running (PIDs 35236, 38220, both started 2026-08-11
  15:02-15:03, same project, both `-log`) with Monolith on 9316 held by 35236. Per the
  one-editor rule, no editor work (PIE, graph reads, T3D) was attempted; this document
  is source-only. Confirm one instance before Campaign 1.

---

## UI Transparency Audit — 2026-08-11 (editor live, Monolith 9316)

**FIXED:** WBP_Battle_Rhythm JudgementText / ComboText / ClockSourceText were authored
ColorAndOpacity A=0 (invisible). Nothing sets the color at runtime (SetJudgment/
ShowBattleStatus write text only; widget graph has zero color nodes; C++ stores values
only). The closeout Step-4 evidence "ShowRhythmGrade renders" could not pass.

- Fix: ui_query set_widget_property ColorAndOpacity = flat rgba JSON {R,G,B,A}
  (import-text shape does NOT persist — this is the line-228 readback quirk; flat rgba
  shape compiles + reads back correctly). Compiled 0 errors, saved, readback verified:
  (SpecifiedColor=(R=1,G=1,B=1,A=1)) on all three.
- Clean: WBP_MelodiaRhythmHighway lane labels white opaque, label text Q/W/O/P
  (names Lane_D/F/J/K legacy only). HitWindow/MenuOpenButtonLabel/overlays correct.
- Flags: RhythmPrompt (BP_MelodiaRhythmPrompt_C) Collapsed by default — verify shown on
  rhythm start in Campaign 1. WBP_MelodiaRhythmHighway = likely duplicate-tree candidate
  for closeout Step 9 sweep (live HUD is WBP_Battle_Rhythm / UMelodiaRhythmHUDWidget).
