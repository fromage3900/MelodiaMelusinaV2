# Core gameplay systems — closeout plan (2026-08-11)

**Goal: record all four completion gates (`runtime`, `save_load`, `repeat_consume`,
`package_launch`) in the ledger with real evidence, per the evidence standard
(AGENTS.md, 2026-08-11). The loop is not done until the ledger has the rows.**
This plan supersedes the execution order in `CORE_SYSTEMS_HANDOFF_2026-08-10.md` for
everything marked DONE below; the rest inherits it.

---

## 0. Verified state at plan time (2026-08-11, all re-verified today)

| Thing | State |
|---|---|
| Build | **GREEN** — full closed-editor rebuild 2:24 PM; `UnrealEditor-BS_GodFile.dll` 2.6 MB, gameplay symbols present |
| Module load | **FIXED** — `MelodiaCore` enabled in `BS_GodFile.uproject`; headless editor launch: `InternalLoadLibrary: 'BS_GodFile'` + MelodiaCore mount, no "could not be loaded" |
| Build blockers fixed today | `MelodiaBattleMapConfig.h/.cpp` were UTF-16 blobs (even in git) → UHT "GENERATED_BODY in skipped block"; re-encoded to UTF-8 BOM |
| Beat map | **DONE** — `MelodiaMusicClockSubsystem.cpp:50-51,167-179` loads `128BPMarpeggiomelody_beatgrid` MIDI with full tempo/bar/beat maps; never hand-built |
| Highway-ownership fix | **OWNER LOCK 2026-08-12 — RHYTHM GAME WORKED in PIE.** `bExecutionDrivingHighway` live; see `Docs/Handoffs/RHYTHM_GAME_LOCKED_2026-08-12.md` |
| `melodia.Rhythm.Disable 1` cvar | **EXISTS** — `MelodiaMusicClockSubsystem.cpp:25-33`, the A/B control |
| Probe | `Content/Python/rhythm_battle_runtime_probe.py` — `skill_class` NameError fixed, committed (lines 18,188-193) |
| Ledger | `runtime` = FAIL (honest row, 2026-08-11); `save_load`, `repeat_consume`, `package_launch` = OPEN. `Saved/Echo/state.txt` matches |
| Editor | closed; port 9316 free; no UnrealEditor/UBT processes |
| Known asset damage | `Content/BigBush*`, `GenericFlower1.uasset` — "Invalid value for PACKAGE_FILE_TAG" (pre-existing, unrelated to module error; quarantine, do not delete) |

**Ledger truth is the contract: a gate is certified only when `record_gate.py <id> pass`
has a row. Prose in a session log is not a row.**

---

## 1. Execution order

### Step 1 — Preconditions (one editor, gates reachable)
- Exactly one editor on 9316; `python Tools/echo_run.py status` → reachable.
- `python Tools/echo_run.py run static_gates` — each gate `[ok]`; any HOLD/FAIL blocks
  the campaign work.
- `python Tools/bp_sweep.py` scoped re-run (project-wide version died in the three-editor
  incident on 08-08; scoped runs are clean).

### Step 2 — Observe the highway-ownership fix in PIE — **DONE / OWNER LOCK 2026-08-12**
**RHYTHM GAME WORKED.** Owner confirmed live PIE. Canonical lock:
`Docs/Handoffs/RHYTHM_GAME_LOCKED_2026-08-12.md`. Do not reopen this step as a P0 blocker.
(Formal Campaign 1 harness packaging remains Step 4.)

### Step 3 — Verify the damage-scalar sequencing (before any A/B)
- Read the live `UseSkill` → montage damage notify (~2.5 s) → `FinishSession` latch
  sequencing (`MelodiaRhythmCombatSubsystem.h:188-199`, `.cpp:160-165`).
- `PendingDamageMultiplier` must not be reset on invalidate — `StartSession` owns the
  reset; do not "fix" it.
- Deliverable: a written verdict that rhythm can or cannot affect damage on the current
  path, with the exact call order quoted. If the scalar can't latch before the damage
  notify, this is a HOLD on Campaign 1, not a reason to fudge numbers.

### Step 4 — Campaign 1: rhythm→damage delta with REAL input (gate: `runtime`)
Per `Docs/ECHO/campaign_01_rhythm_damage_delta.md`:
- Route: `L_MelusinaMorning → L_KaleidoNave` (Dreamstate is merged — the route is now
  Morning → KaleidoNave; the tagged `melodia_smoke_encounter` actor lives in
  KaleidoNave's persistent level).
- **Real keys** through `BP_BattleUI::OnKeyDown` (Q/W/O/P → `RegisterLaneHit`), or a
  documented `InputKey` injection into the focused widget. Probe-only = HOLD.
- Confirm lanes light on press and unlight on release (OnKeyUp), `ShowRhythmGrade`
  renders, `MELODIA_RHYTHM session=` appears in the log (never has).
- Damage A (rhythm on) vs damage B (`melodia.Rhythm.Disable 1`), identical input.
  A ≠ B is the deliverable. Equal numbers = not PLAYing = do not record.
- Evidence artifacts, all three: `MELODIA_RHYTHM session=` log excerpt; assertion
  report JSON next to the frames; the committed harness that produced both.

### Step 5 — Wire `RestorePartyAfterBattle` + settle `curentMP`
- Read `FS_UnitState` in the stock struct first: line 82 `currentHP` vs line 83
  `curentMP` — either a faithful match to a stock typo or a bug that silently disables
  the MP half. Settle it, then wire the one call site:
- `UMelodiaJRPGPostBattleLibrary::RestorePartyAfterBattle(BattleController)` hangs off
  the proven battle-end path (`CompleteBattle` → `ResumeQuillOnce()`, exactly-once
  confirmed). Owner decision stands: heal only, no retry-on-defeat; `NotifyDeathRecovery`
  / `NotifyRetryRecovery` stay uncalled.

### Step 6 — Campaign 4: result matrix (completes `runtime` row)
Per `campaign_04_result_matrix.md`: Victory, Defeat, Fled, unavailable; each
resumes/aborts Quill **exactly once**; no double resume, no stub-silent defeat, no lost
pending result, no mid-battle save. Precondition: B4 closure wiring verified
(`verify_battle_closure.py` 10/10). A pass here **replaces** the Campaign 1 row (latest
wins in ledger views).

### Step 7 — Campaign 2: save round trip + repeat consume (gates: `save_load`, `repeat_consume`)
- Slot names unified on `MelodiaJRPGSlot0/1/2` (ledger says done 2026-08-07).
- Part A: PIE to first autosave boundary → save file on disk → **fully exit the editor**
  → relaunch → load via the canonical flow → confirm state restored, no duplicate reward/
  dialogue. This gate has never closed; an in-memory guard that double-pays after
  relaunch is exactly what it catches.
- Part B: replay the same authored beat twice (Quill resume + save reload); second
  occurrence is a no-op; `melodia:stat:` idempotent per `<IntentId>`; two beats may still
  award the same stat.
- Record both rows.

### Step 8 — Campaign 3: Development package launch (gate: `package_launch`)
- Preconditions: re-cook (`Saved/StagedBuilds_20260730/` is 2026-07-30; the tree changed
  since — re-cook, verify `+MapsToCook` covers Morning + KaleidoNave); enumerate
  `Saved/StagedBuilds*/Windows*/BS_GodFile.exe` before assuming a path; no editor lock.
- Launch outside the editor, walk Morning → KaleidoNave, confirm maps load, Quill
  dialogue, battle chain starts.
- Standing failure class: cook exit 25 / modal-hang / shader compile stalls — grep for
  `MODAL_OPEN` before blaming the build. The gate is the **launch**, not the cook; a
  failing launch is recorded `fail` with command + log tail + exit code verbatim.

### Step 9 — Close-out hygiene (after the four gates have rows)
- `python Tools/bp_sweep.py` project-wide; confirm zero duplicate short names.
- Duplicate trees (`Docs/ECHO/reconciliation_duplicate_trees.md`): **owner sign-off
  required** before any move. Recommended: quarantine the 33-asset mirror to
  `_QuarantineAssets_20260809/` (relocate, never delete; mirror is untracked and
  unrecoverable); leave `_ThirdParty` island unaddressed pending decision.
- Record `duplicate_trees` gate only after execution + sweep clean.
- Note the `BigBush*`/`GenericFlower1` PACKAGE_FILE_TAG damage for owner review —
  quarantine candidates, not inputs to any game system.

---

## 2. Hard rules that still apply (violations have cost days)

- One editor instance; verify the DLL lock by write-open attempt, never by report.
- Never `git clean -fd` / `git checkout -- .` — bulk `Content/` is untracked.
- Never Python against `Content/TurnBasedJRPGTemplate/Blueprints/Skills/` (`D_DamageType`
  = fatal editor death); use Monolith `blueprint_query` (native C++).
- `MODAL_OPEN` is a dialog, not a hang.
- Unclean compile or `matched:false` is a HARD STOP. Header changes need a full
  closed-editor build (Live Coding cannot introduce new imports).
- `bRelaxedAllowlistInEditor = true` — the allowlist does not fail closed in editor
  builds; run a verification pass with it off before shipping.
- Full closed-editor build before trusting a green claim (adaptive unity hides
  collisions; three of four 08-10 blockers were unity-merges).
- The harness that produced the evidence must be the harness on disk (commit before run).

## 3. Do not "fix"

- Lane input (Q/W/O/P in both `OnKeyDown` and `OnKeyUp`), `ShowRhythmGrade`, the highway
  creator in `BP_BattleUI::ShowBattleUI`.
- Petal Cadence Resonance via `buffs` on `BP_BattleSkillBase`.
- `PendingDamageMultiplier` not resetting in `InvalidateSession`.
- `BP_MelodiaGameMode` — zero referencers; sole owner of `WBP_Battle_Rhythm` /
  `WBP_Battle_Results`; wire into neither.
- `melodia:item:` is a logging stub — no authoring depends on it granting anything.

## 4. Acceptance (owner's words, unchanged)

Blueprints for gameplay fully wired; turn-based rhythm skills cause the note highway to
appear, trigger damage, and advance the turn; Sir Melodious is the only available active
pawn to ctrl-switch to on the integration map.
