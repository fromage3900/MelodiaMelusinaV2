# Enemy Battle Repeat-Test Plan — 2026-08-28

**Status:** planning/draft, offline, no editor
**Author:** Melusina (Hermes agent, no-editor lane)
**Live with:** Junie (Rider, editor lock) — this lane stays offline; the actual repeat tests are
editor-bound and go to Junie's queue

---

## Purpose

A plan for repeating enemy battles — not a one-off smoke, but a repeatable harness that runs the
same encounter many times, collects the result distribution, and flags when the result stops matching
the authored contract. This is the long-term-scale version of the P0 battle proof: the P0 proof is
four terminal outcomes once; the repeat-test harness is "run the same battle 50 times and confirm the
result distribution matches the authored spawn/chance/timing contract."

This plan is read-only — no `.uasset` writes, no editor. The actual harness + tests go to Junie's
editor queue when she's ready.

---

## 1. Why repeat tests

The P0 `battle_integration_map` gate is proven once (2026-08-27 live PIE, all four terminal outcomes,
Quill resumes exactly once each). That is a **point-in-time** proof. It does not prove:
- The result is stable across N repetitions (no state leak between battles)
- The spawn chance actually fires at the authored rate (1.0 = always, but what about 0.7?)
- The rhythm grade actually changes the result at the authored scalar (not just once, but across a
  distribution of grades)
- The save/load round-trip preserves the battle state (not just once, but across a restart)

A repeat-test harness answers these by running the same encounter N times and collecting the result
distribution. It is the long-term-scale version of the P0 proof.

---

## 2. What the P0 proof already established (truth)

From `Docs/P0_TASK_LEDGER.json` → `agent_work_log_2026-08-27.p0_closeout_session`:

- `BP_InteractionBattle` (tag `melodia_smoke_encounter`) had `enemyList=[]`, so
  `MelodiaExternalJRPGBridgeSubsystem.cpp:130` rejected every battle with "tagged battle actor has no
  authored enemy roster". Fixed: one row, key `BP_WeakEnemy_C`, `spawnChance=1.0`, `minLevel=1`,
  `maxLevel=1`; map saved 13:07.
- All four terminal outcomes driven through the authored `MelodiaQuillSmoke` golden run:
  - **unavailable** (abort path)
  - **victory** `result=victory typed=0` (`SetHP(0)` on `BP_WeakEnemy_C`)
  - **defeat** `result=defeat typed=1` (`SetHP(0)` on `BP_SirMelodiousPlayerUnit_C`)
  - **fled** `result=fled typed=2` (`fleeChance=100` + `BP_BattleController.Flee`)
- Quill resumed **EXACTLY ONCE** on every outcome (`MELUSINA_LOOP_QUILL_RESTORE` then `_NEXT`, never
  twice).
- Atomic commit proven on victory branch in order:
  1. `melodia:quest:melodia_q_echo_01`
  2. `melodia:reward:melodia_smoke_reward`
  3. `melodia:flag:melodia_smoke_complete:true`
  4. `Script 'MelodiaQuillSmoke' ended`
- Fled branch committed **ONLY the flag** (no quest/reward) — proving the commit is branch-conditional.

**Known defect (carried forward):** player-unit death crashes the editor — `Assertion failed: false
[AnimMontage.h] [Line: 781]` ~10s after `SetHP(0)` on `BP_SirMelodiousPlayerUnit_C`. Defeat result
lands correctly first. **Not a P0 gate blocker**, but it makes repeated defeat testing impractical.
Prefer the flee path for repeat tests.

---

## 3. The repeat-test harness (conceptual design)

### Goal

Run the same encounter N times, collect the result distribution, and assert that the distribution
matches the authored contract (spawn chance, flee chance, rhythm scalar, Quill resume once per battle).

### Inputs (authored, read from config + Blueprint CDO)

| Input | Source | How to read |
|-------|--------|-------------|
| Enemy roster | `BP_InteractionBattle.enemyList` | `blueprint_query get_cdo_properties` (C++, not Python) |
| Spawn chance per enemy | enemy roster row `spawnChance` | `blueprint_query get_cdo_properties` |
| Flee chance | `BP_BattleController.Flee` / `fleeChance` | `blueprint_query get_cdo_properties` |
| Rhythm scalar | `UMelodiaRhythmCombatSubsystem` / `ApplyRhythmAttackScalar()` | C++ source read, not Python probe |
| Quill resume contract | `UMelodiaNarrativeSubsystem` dispatch table (7 verbs) | C++ source read |

### Outputs (collected per battle)

| Output | Assertion |
|--------|-----------|
| Terminal result | Must be one of {victory, defeat, fled, unavailable} |
| Quill resume count | Must be exactly 1 per battle (MELUSINA_LOOP_QUILL_RESTORE + _NEXT, never 2) |
| Atomic commit order (victory branch) | Must match the 08-27 order (quest → reward → flag → script end) |
| Flag state (fled branch) | Must commit only the flag, no quest/reward |
| HP state | Must match the typed result (victory = enemy HP 0, defeat = player HP 0, fled = both alive) |

### Repetition modes

1. **Deterministic repeat** — same input every time (no rhythm variation, no RNG). Confirms the result
   is stable across N repetitions with no state leak. N = 10 minimum.
2. **Stochastic repeat** — authored spawn/flee chance enabled, rhythm grade varied across the authored
   scalar range. Confirms the result distribution matches the authored contract. N = 50 minimum.
3. **Save/load repeat** — after each battle, save canonically, restart the process, load, confirm the
   battle state is preserved. N = 5 minimum (each one is expensive — full process restart).

### What the harness must NOT do

- **Not a probe-only run.** Calling `subsystem.register_lane_hit()` / `controller.use_skill()` from
  Python proves the native seam responds when invoked — it does NOT prove a player pressing Q/W/O/P
  sees a highway. The harness must drive real input through `BP_BattleUI::OnKeyDown` (or a documented
  `InputKey` injection path into the focused widget). A probe-only green run is a HOLD.
- **Not a frame capture without a report.** PNG captures with no accompanying JSON assertion report and
  no committed verifier cannot be re-checked. Save the assertion report next to the frames.
- **Not a harness that crashes on entry.** Fix the probe first, then rerun. Never paper over it.

---

## 4. The offline readiness checklist (before the editor lane runs the harness)

This lane can verify the readiness checklist offline. The actual harness run is editor-bound.

### Readiness checklist

- [ ] `BP_InteractionBattle.enemyList` is non-empty (currently `BP_WeakEnemy_C`, `spawnChance=1.0`,
  `minLevel=1`, `maxLevel=1`) — verify via `blueprint_query get_cdo_properties`
- [ ] `BP_BattleController.Flee` / `fleeChance` is authored for the flee path — verify via
  `blueprint_query get_cdo_properties`
- [ ] `UMelodiaNarrativeSubsystem` dispatch table recognizes all 7 verbs — verify via C++ source read
- [ ] `UMelodiaRhythmCombatSubsystem::ApplyRhythmAttackScalar()` is the single path into stock damage —
  verify via C++ source read
- [ ] `bRelaxedAllowlistInEditor` is OFF for the test run (so unregistered IDs fail closed, not with a
  warning) — verify via `blueprint_query get_cdo_properties`
- [ ] The Quill interpreter is running (battle is script-driven; an IDLE PIE smoke can NEVER start a
  battle) — verify via `MELODIA_INTENT_REJECTED` / `MissingRuntime=5` log check
- [ ] The `test_qsc_allowlist_contract` is 4/4 PASS (so no script emits an unallowlisted ID) — verify
  via offline `python -m unittest`
- [ ] The `test_p0_quests_and_content_contract` is 8/8 PASS — verify via offline `python -m unittest`

### What this lane can verify offline (no editor)

- The two Python contract tests (always runnable)
- The C++ source reads (the dispatch table, `ApplyRhythmAttackScalar()`, the enemy roster config struct)
- The readiness checklist items that are source-based (not CDO-based)

### What this lane cannot verify offline (editor-bound)

- `BP_InteractionBattle.enemyList` CDO state (needs `blueprint_query get_cdo_properties`)
- `BP_BattleController.Flee` / `fleeChance` CDO state
- `bRelaxedAllowlistInEditor` CDO state
- The Quill interpreter running (needs a PIE smoke)
- The actual harness run (needs a PIE smoke with real input)

---

## 5. The test plan for Junie's editor queue

When Junie is ready to run the repeat tests, the plan is:

### Phase A — Deterministic repeat (N=10)

1. Load `MelodiaIntegrationMap`, start `BP_InteractionBattle` with `enemyList` populated.
2. Drive the battle to victory via real input (or documented `InputKey` injection).
3. Assert: result = victory, Quill resumed once, atomic commit order matches 08-27.
4. Repeat 10 times. Assert: no state leak, every repetition produces the same result.

### Phase B — Stochastic repeat (N=50)

1. Same setup, but enable authored spawn/flee chance and vary the rhythm grade across the authored
   scalar range.
2. Run 50 times. Collect the result distribution.
3. Assert: the distribution matches the authored contract (spawn chance × flee chance × rhythm scalar).

### Phase C — Save/load repeat (N=5)

1. After each battle, save canonically via the stock JRPG save (`BP_JRPGSaveGame.melodiaNarrativeRecord`).
2. **Full process restart** (not just a reload — the gate requires a process restart).
3. Load, confirm the battle state is preserved (flags, quest state, consumed intents, checkpoint).
4. Repeat 5 times.

### Phase D — Defect verification

1. Confirm the player-unit death crash (`AnimMontage.h:781`) still occurs on defeat — document it as a
   known defect, not a gate blocker.
2. Confirm the flee path does NOT trigger the death crash (flee = both alive).
3. Prefer the flee path for repeat tests if the death crash makes defeat testing impractical.

---

## 6. The offline contract test (this lane writes, Junie runs)

This lane writes an offline contract test that asserts the readiness checklist is satisfied before the
editor lane runs the harness. The test is `Content/Python/Tests/test_enemy_battle_repeat_readiness.py`.

### What it asserts (offline, no editor)

- The two Python contract tests are green (`test_qsc_allowlist_contract` 4/4, `test_p0_quests_and_content_contract` 8/8).
- The C++ source files that implement the dispatch table and `ApplyRhythmAttackScalar()` exist and
  contain the expected symbols (read the source, not the compiled binary).
- The config struct for the enemy roster is defined in the source (read the header, not the CDO).

### What it does NOT assert (editor-bound, left for Junie)

- The actual CDO state of `BP_InteractionBattle.enemyList`
- The Quill interpreter running
- The actual harness run

### File map

| File | Purpose |
|------|---------|
| `Content/Python/Tests/test_enemy_battle_repeat_readiness.py` | Offline readiness contract test (this lane writes) |
| `Docs/Handoffs/ENEMY_BATTLE_REPEAT_TEST_PLAN_2026-08-28.md` | **this file** |
| `Docs/P0_TASK_LEDGER.json` → `agent_work_log_2026-08-27` | The P0 battle proof (source of truth for the 08-27 atomic commit order) |
| `Source/BS_GodFile/MelodiaIntegration/MelodiaExternalJRPGBridgeSubsystem.cpp` | Enemy roster rejection path (line 130) |
| `Source/BS_GodFile/MelodiaIntegration/MelodiaRhythmCombatSubsystem.cpp` | `ApplyRhythmAttackScalar()` single path |
| `Source/BS_GodFile/MelodiaIntegration/MelodiaNarrativeSubsystem.cpp` | 7-verb dispatch table |
