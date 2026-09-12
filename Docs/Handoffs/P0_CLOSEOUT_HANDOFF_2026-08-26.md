# P0 Closeout Handoff — 2026-08-26

**Supersedes:** the "Found live, via your own PIE test — the actual P0 blocker" section of
`Docs/Handoffs/MELODIA_HUB_SESSION_HANDOFF_2026-08-26.md`, which describes the reparent as blocked
pending approval and says "do not repeat the retire the duplicate fix." That block is stale as of
this document. The reparent landed, was live-verified in PIE, and the root-cause battle-cascade bug
is fixed.

This document is the current-truth record. `ECHO_BATTLE_LOOP_NOTES_2026-08-26.md` (fixture-level
iteration, no live PIE) remains accurate and is not superseded.

---

## 1. State of play

What is now true that was **not** true this morning:

- `BP_MelodiaJRPGPlayerController` is a real subclass of `BP_JRPGPlayerController_C`, not a
  byte-for-byte duplicate. Every stock hard-typed cast to `BP_JRPGPlayerController_C` — the thing
  that produced the project-wide `Accessed None` battle cascade — now resolves against it.
- A full battle has been run live in PIE end to end: explore -> `BP_PermanentBattle` overlap ->
  battle-state transition -> rhythm music clock running -> `BP_BattleController` holding a live,
  correctly-typed `jRPGPlayerController` and a live `currentAttackingUnit` -> HP bars rendering on
  screen for Sir Melodious and two enemies.
- `BP_MelodiaJRPGPlayerController_C` is 74 KB and 14 EventGraph nodes, down from 1.44 MB and 569
  nodes. The 555 removed nodes were a full duplicate of the parent's graph, not Melodia-specific
  logic.
- A general defect class was found and fixed, not just this one symptom: a duplicated child graph
  can compile with 0 errors and 0 warnings while still being functionally broken, because Blueprint
  only errors on orphaned object/array/map pins — orphaned primitive/bool/enum/exec pins silently
  fall back to a literal default instead of erroring. See section 5.
- One gap remains open and is the new top priority: the Melodia rhythm-highway HUD is not bound to
  the live battle controller (section 4).

---

## 2. Fixed this session

### 2.1 `BP_MelodiaJRPGPlayerController` was a duplicate, not a subclass

- **Cause:** the Blueprint's parent was set to a full duplicate of
  `/Game/TurnBasedJRPGTemplate/Blueprints/Controllers/BP_JRPGPlayerController` (same parent class —
  native `PlayerController` — 21 identical functions, 24 of 25 identical variables), not the stock
  class itself. Any stock code that hard-cast to `BP_JRPGPlayerController_C` — confirmed at
  `BP_InteractionDetector`'s `Set jRPGPlayerController` node — silently returned None against it.
  That None propagated through `BP_BattleController` / `BP_BattleBase` / `BP_EnemyUnitBase`, which
  is the source of the wall of `Accessed None trying to read currentTargetUnit /
  currentAttackingUnit / jRPGPlayerController / exploreCharacter` errors from the earlier
  walk-and-interact test.
- **Fix:** reparented `BP_MelodiaJRPGPlayerController` to
  `/Game/TurnBasedJRPGTemplate/Blueprints/Controllers/BP_JRPGPlayerController.BP_JRPGPlayerController_C`.
  The child's duplicated EventGraph was stripped from 569 nodes to 14, leaving only the genuinely
  Melodia-specific logic (section 2.3). Asset size dropped from 1.44 MB to 74 KB.
- **Proof:** live PIE read of `BP_BattleController_2.jRPGPlayerController` returned
  `BP_MelodiaJRPGPlayerController_C_0` — a `BP_JRPGPlayerController_C`-typed variable successfully
  holding the Melodia controller. This is the exact cast that previously failed; it is now proven
  correct at runtime, not just at compile time. See section 3 for the full live-read table.

### 2.2 `HasInput` macro: input unconditionally blocked

- **Cause:** the `Branch` node's `Condition` pin inside the `HasInput` macro was unconnected, so it
  evaluated to its literal default of `true` and always routed into `isBlocked`, blocking all WASD
  input. This happened because deleting the shadowed child variable `isInputBlocked_0` purged the
  `Get isInputBlocked` node that had been feeding the Branch.
- **Fix:** re-added `Get isInputBlocked` and wired it to `Branch.Condition`, matching the parent
  Blueprint's wiring exactly.
- **Proof:** WASD movement confirmed working by the user after the fix.

### 2.3 Bug class: 50 pins connected in the parent but dangling in the child

- **Cause:** the same duplication that caused 2.1 left 50 pins that are wired in the real parent
  graph dangling in the child's copy. 29 of the 50 were fed by `VariableSet` nodes, meaning severed
  **exec chains** — including both `Possess.InPawn` calls, `Set View Target with Blend`, the
  `Switch on E_GameState` node, and the `Switch on E_ExploreCharacterMode` node.
- **Why the compiler didn't catch it:** only object/array/map pins raise a compile error when
  orphaned. Primitive, bool, enum, and exec pins silently fall back to their literal default instead
  of erroring. A 0-error/0-warning compile on this Blueprint was therefore not evidence of
  correctness — it was evidence that the compiler cannot see this class of defect.
- **Fix:** resolved structurally, not pin-by-pin. Deleting the 555 duplicated nodes (section 2.1)
  means the child now inherits the parent's intact graph instead of running its own broken copy of
  it.
- **Proof:** post-fix pin diff against the parent shows 0 dangling pins.

### 2.4 Ordering trap: `compile_blueprint` after `set_cdo_property` wipes the CDO

- **Cause:** running `compile_blueprint` after `set_cdo_property` resets the just-set default back
  to its pre-edit value. This happened twice against `playerUnits`, which was reset to `{}` both
  times.
- **Fix:** established correct ordering — compile, then `set_cdo_property`, then save. Never compile
  between setting a CDO property and saving.
- **Proof:** first save shipped an empty `playerUnits` map; after reordering, the second save
  shipped the correct `BP_SirMelodiousPlayerUnit_C` entry, confirmed by a live CDO re-query.

### What was deliberately kept vs. dropped

- **Kept:** the 14 surviving EventGraph nodes are a genuinely Melodia-specific cursor-VFX-on-Tick
  chain (`Event Tick` -> `Set CursorFxAccumulator`, `Was Input Key Just Pressed`, `Convert Mouse
  Location To World Space` x2, `Spawn System at Location` x2, `Rotation From X Vector`, float math,
  2 Branches, `Get CursorFxAccumulator`). The parent has no `Event Tick` at all, so this chain
  overrides nothing and is safe.
- **Dropped, needs re-adding:** the child's `ShowQuestRewards` override, which used
  `BP_ItemObtainDialogue` via node `K2Node_CreateWidget_0`. Its surrounding chain was shared with the
  parent's duplicated graph and was removed along with the rest of the 555 duplicate nodes. See
  section 4.

---

## 3. Live PIE evidence

Everything in this table is a **live runtime read from a running PIE session** on
`/Game/MelodiaIntegration/Maps/MelodiaIntegrationMap` — object property reads and log lines pulled
from the running game instance, not source/CDO inspection while stopped. A 12-second PIE smoke run
returned `ok: true` with `Blueprint Runtime Error: 0`, `Accessed None: 0`, `LogChooser: 0` across
both active runtime and teardown.

| Live object / signal | Value observed |
|---|---|
| `exploreCharacter` | `BP_MelusinaJRPGCharacter_C_1` (possession working; CDO value is None — populated at runtime by inherited spawn logic, not a defect) |
| `playerUnits` | `BP_SirMelodiousPlayerUnit_C`, live `currentHP=120`, `curentMP=100` |
| `partyMembers` | Sir Melodious |
| `isInputBlocked` | `false` |
| `gameState` transition | `NewEnumerator0` (Explore) -> `NewEnumerator1` (Battle) |
| `isExplore` | `true` -> `false` on battle start |
| Battle trigger | `BP_PermanentBattle_2` overlap |
| Input context log | `MELODIA_INPUT_CONTEXT EMelodiaInputContext::None -> EMelodiaInputContext::Battle` |
| Battle UI push | `BP_BattleUI_C_0` pushed at depth 1 |
| Music clock log | `MELODIA_MUSICCLOCK wall-clock music clock running on 'BP_BattleController_2'; validated beat-grid MIDI at 128.0 BPM 4/4; musical time is live.` |
| `BP_BattleController_2.currentAttackingUnit` | `BP_SirMelodiousPlayerUnit_C_0` |
| `BP_BattleController_2.currentTurn` | `2` |
| `BP_BattleController_2.isBattleOver` | `false` |
| `BP_BattleController_2` turn order | `[BP_WeakEnemy_C_1, BP_SirMelodiousPlayerUnit_C_0, BP_WeakEnemy_C_0]` |
| **`BP_BattleController_2.jRPGPlayerController`** | **`BP_MelodiaJRPGPlayerController_C_0`** — the precise cast that previously failed, now holding correctly at runtime |
| Screenshot | `Saved/Screenshots/WindowsEditor/HighresScreenshot00021.png` — battle arena, Sir Melodious vs. two enemies, HP bars showing 16 and 65 |
| Rhythm UI textures loaded | `T_Melodia_GradePerfect`, `T_Melodia_SkillChipBG`, `T_Melodia_EnemyGlow`, `T_Melodia_SoftMG_SealSP` |

---

## 4. Still open

Ordered by priority.

1. **TOP PRIORITY — Melodia rhythm HUD is not bound to the battle controller.**
   `BP_BattleController_2.melodiaBattleUI` = **None** and `.MelodiaUI` = **None**, live-read during
   the same PIE session as section 3. The stock `battleUI` binds fine and the rhythm textures load
   into memory, but the Melodia rhythm-highway HUD itself is never assigned to the battle
   controller. This blocks the `rhythm_owner`, `hud_single_writer`, and `rhythm_grade_to_result`
   gates. Not yet root-caused — next session should find where `melodiaBattleUI`/`MelodiaUI` is
   supposed to be set (widget-creation path, likely `MelodiaUIBridgeSubsystem` per the hub handoff)
   and confirm it is actually called on the battle-start path.
2. **`ShowQuestRewards` override needs re-adding.** Dropped along with the 555 duplicate nodes
   (section 2, "What was deliberately kept vs. dropped"). It used `BP_ItemObtainDialogue` via
   `K2Node_CreateWidget_0`. Needs to be re-created on the reparented child, referencing the parent's
   surviving logic rather than re-duplicating it.
3. **`BP_MelodySlimeBattle_Hub` is still abstract** and cannot be spawned, so the Melody Slime is not
   battle-triggerable in the hub map. No exposed Monolith action clears the abstract flag. Also:
   legacy (non-Enhanced-Input) input mappings mean `Interact` cannot be injected programmatically —
   battle in the hub must be triggered by overlap or a real keypress, not a synthetic input call.
4. **Two pre-existing static-gate failures, unrelated to this session's work:**
   - `bp_sweep` fails only because `run_bp_sweep` (`Tools/echo_run.py:313`) additionally requires
     `DUPES == 0`. `bp_sweep.py` itself exits 0. There are ~15 duplicate short names, every one a
     `/Game/Melodia/<path>` vs. `/Game/<path>` mirror pair (`BP_MelodySlime`, `BP_MelodySlimeBattle`,
     `BP_Melusina`, `BP_RhythmHUD`, `WBP_RhythmHUD`, and others) — the already-documented
     two-sources-of-truth mirror tree, not new damage from this session.
   - `verify_baseline` fails with 16 drifted assets (39 clean, 0 failed). All 16 drifted assets are
     **materials** (`M_Master_Toon_Universal`, `MF_Madoka`, `MPC_Melodia_Palette`, and others). Zero
     gameplay assets are involved. Neither gate failure touches the controller or the battle loop.

---

## 5. Traps for the next session

- **Compile-wipes-CDO ordering rule.** `compile_blueprint` run *after* `set_cdo_property` resets the
  just-set default. Correct order: compile -> `set_cdo_property` -> save. Never compile between
  setting a CDO property and saving. This bit `playerUnits` twice in this session.
- **Only object/array/map pins error when orphaned; primitive/bool/enum/exec pins silently fall back
  to their literal default.** A clean 0-error/0-warning compile is not proof a duplicated or edited
  graph is functionally intact — it can hide severed exec chains and wrong-default primitives. Diff
  pin connectivity against a known-good reference (e.g., the parent graph) when duplication or
  large-scale node surgery is involved, not just the compiler's error count.
- **`.uasset` files may come back read-only** (observed repeatedly after `git checkout` in earlier
  sessions in this project). Run `attrib -R` (or `os.chmod` equivalent) on the file before attempting
  `save_asset`/`save_loaded_asset`/Ctrl+S if the save silently fails.
- **A fresh disk mtime alone is not proof a change persisted.** This project has already lost work
  to a second-writer editor collision where a stale instance overwrote assets that had already
  reported `saved: true` with a fresh mtime. After any save — and especially after any suspected
  concurrent-editor window — re-query the live actor list / CDO / property value directly rather than
  trusting the mtime by itself.

---

## 6. How to reproduce the battle test

1. Load `/Game/MelodiaIntegration/Maps/MelodiaIntegrationMap`.
2. Start PIE.
3. Call `OverlapStarted` on `BP_PermanentBattle` (the instance used in this session was
   `BP_PermanentBattle_2`) to trigger the battle transition programmatically instead of walking into
   it.
4. Read `BP_BattleController` properties live (the instance used in this session was
   `BP_BattleController_2`): `jRPGPlayerController`, `currentAttackingUnit`, `currentTurn`,
   `isBattleOver`, `melodiaBattleUI`, `MelodiaUI`.
5. Cross-check `gameState` / `isExplore` on the player controller and the
   `MELODIA_INPUT_CONTEXT` / `MELODIA_MUSICCLOCK` log lines to confirm the battle state machine and
   rhythm clock are both live, not just the controller cast.
