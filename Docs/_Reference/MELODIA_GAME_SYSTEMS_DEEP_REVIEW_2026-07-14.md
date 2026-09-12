# Melodia Game Systems Deep Review - 2026-07-14

**Scope:** Read-only review of the current MelodiaCore C++ runtime against the generated rules contract and the no-editor GMM simulator expectations.

**Current state:** Songcraft effects and generated modifier tables are now present in C++ and partially consumed by `UMelodiaBattleSession::ResolveRhythmExecutionResult`. The highest leverage work has moved from "port songcraft at all" to "make the authored systems actually govern combat, turn order, and the roguelike loop."

## P0 Issues

### GS-001: Fix multiplicative modifier stacking

**Impact:** Stackable `mul` modifiers can invert their intended effect. `TempoBreak` is authored as a speed slow (`0.85`, stack, max 3), but the C++ evaluator multiplies by `Value * Stacks`, so 2 stacks produce `1.7x` speed instead of `0.7225x`.

**Evidence:**

- `Plugins/MelodiaCore/Source/MelodiaCore/MelodiaCombatStateComponent.cpp`
  - `UMelodiaCombatStateComponent::EvaluateModifier`
- `Plugins/MelodiaCore/Source/MelodiaCore/MelodiaRulesGenerated.h`
  - `TempoBreak`, `HasteDance`, `GuardHymn`, `ResonantFocus`
- `Content/Python/gmm/game/modifiers.py`
  - `ModifierStack.evaluate`

**Acceptance:**

- `mul` modifiers stack by exponentiation or equivalent repeated multiplication.
- `add` modifiers continue to scale linearly by stack count.
- C++ automation covers `TempoBreak` at 1, 2, and 3 stacks.

### GS-002: Respect permanent modifier duration

**Impact:** The rules schema allows `duration_turns = -1` for permanent modifiers, but C++ `TickModifiers` decrements and removes every modifier whose duration is `<= 0`. Any future permanent rule would expire on the first tick.

**Evidence:**

- `Plugins/MelodiaCore/Rules/melodia_rules.json`
  - modifiers schema: `duration_turns`, `-1 = permanent`
- `Plugins/MelodiaCore/Source/MelodiaCore/MelodiaCombatStateComponent.cpp`
  - `UMelodiaCombatStateComponent::TickModifiers`

**Acceptance:**

- Negative-duration modifiers survive turn ticks.
- C++ automation covers a permanent modifier and a finite modifier in the same stack.

### GS-003: Make AV the battle-session turn authority

**Impact:** `HasteDance`, `TempoBreak`, enemy speed, and generated enemy delay fractions do not control who acts next. The session still resolves as player result -> enemy turn -> player command, with delay implemented as enemy turn skip stacks rather than AV arithmetic.

**Evidence:**

- `Plugins/MelodiaCore/Source/MelodiaCore/MelodiaBattleSession.cpp`
  - `UMelodiaBattleSession::NotifyRhythmExecutionFinished`
  - `UMelodiaBattleSession::ExecuteEnemyTurn`
- `Plugins/MelodiaCore/Source/MelodiaCore/MelodiaCoreRulesLibrary.cpp`
  - `CalculateAVCost`
  - `AddAVCost`
- `Plugins/MelodiaCore/Rules/melodia_rules.json`
  - `turn_economy.base_av`
  - `enemy_delay_on_hit_av_fraction`
  - `enemy_delay_on_break_av_fraction`

**Acceptance:**

- Battle session stores player/enemy AV values.
- Acting side advances according to lowest AV / elapsed AV.
- Speed modifiers affect future AV cost.
- Generated delay fractions add AV delay, not only skip a full enemy turn.
- C++ automation proves a faster player can act twice before a slow enemy, and a delayed enemy acts later.

### GS-004: Restore ultimate as an interrupt economy

**Impact:** Ultimate is command-gated to `AwaitingPlayerCommand` and immediately hands tempo back to the enemy when it does not kill. The design contract expects ultimate to be fireable as an AV interrupt payoff.

**Evidence:**

- `Plugins/MelodiaCore/Source/MelodiaCore/MelodiaBattleSession.cpp`
  - `UMelodiaBattleSession::CanSubmitUltimateCommand`
  - `UMelodiaBattleSession::SubmitUltimateCommand`

**Acceptance:**

- Ultimate can be submitted while a battle is active when the gauge is ready and no rhythm execution is resolving.
- Ultimate records an interrupt count/state.
- Ultimate damage uses generated ultimate rules consistently.
- C++ automation proves ultimate does not force an immediate enemy turn unless AV state says so.

## P1 Issues

### GS-005: Wire all declared modifier stats into runtime hooks

**Impact:** Several generated modifier stats exist but are not evaluated by the systems they should affect. `Attack` and `DamageTaken` are used; `UltGain`, `SPGain`, `Speed`, and `RhythmWindow` are either unused or waiting on AV/rhythm hooks.

**Evidence:**

- `Plugins/MelodiaCore/Source/MelodiaCore/MelodiaCombatStateComponent.cpp`
  - `AddUltimateGauge`
  - `AddSkillPoints`
- `Plugins/MelodiaCore/Source/MelodiaCore/MelodiaBattleSession.cpp`
  - generated songcraft effect application
- `Plugins/MelodiaCore/Rules/melodia_rules.json`
  - modifier stat schema

**Acceptance:**

- `UltGain` modifies generated/skill ultimate gain.
- `SPGain` modifies basic and perfect SP rewards.
- `Speed` feeds AV scheduling.
- `RhythmWindow` has either a real hook or is removed/deferred from runtime registry.

### GS-006: Fix roguelike run phase/event ordering

**Impact:** `StartNewRun` broadcasts the stage recipe before setting phase to `Generating`. A synchronous generator completion callback can be ignored because `NotifyGenerationComplete` only accepts the `Generating` phase.

**Evidence:**

- `Plugins/MelodiaCore/Source/MelodiaCore/MelodiaRoguelikeRunSubsystem.cpp`
  - `StartNewRun`
  - `BuildCurrentStage`
  - `NotifyGenerationComplete`

**Acceptance:**

- Phase changes to `Generating` before broadcasting the recipe.
- Completion callbacks cannot be dropped due to local phase ordering.
- Automation or PIE smoke covers start -> generate complete -> exploring.

### GS-007: Clarify and complete reward-to-next-stage advancement

**Impact:** `AMelodiaDungeonRunCoordinator::CommitRewardAndAdvance` selects a reward and unlocks the exit, but does not advance the stage. If exit Blueprint logic owns advancement, the function name is misleading; if not, the run can stall in `Transitioning`.

**Evidence:**

- `Plugins/MelodiaCore/Source/MelodiaCore/MelodiaDungeonRunCoordinator.cpp`
  - `CommitRewardAndAdvance`
- `Plugins/MelodiaCore/Source/MelodiaCore/MelodiaRoguelikeRunSubsystem.cpp`
  - `SelectReward`
  - `AdvanceStage`

**Acceptance:**

- Either rename/split the API to `CommitRewardAndUnlockExit`, or call `AdvanceStage` from the actual exit transition path.
- One PIE path proves: victory -> reward -> exit -> next generated stage -> second encounter.

## Test Backlog

- Add C++ runtime-path tests for `UMelodiaBattleSession::ResolveRhythmExecutionResult`, not just helper functions.
- Add generated songcraft tests for `StarlitPing`, `TidalWave`, `GustStaccato`, `StoneWall`, and `TidalMend`.
- Add AV scheduling tests once player/enemy AV state exists.
- Add roguelike phase tests for run start, generation completion, reward idempotency, and stage advance.

## Next Highest-Leverage Order

1. `GS-001` modifier stacking correctness.
2. `GS-002` permanent modifier duration.
3. `GS-003` AV authority in battle session.
4. `GS-004` ultimate interrupt semantics.
5. `GS-006` roguelike phase/event ordering.
6. `GS-007` reward-to-exit-to-next-stage proof.
7. `GS-005` remaining modifier stat hooks.
