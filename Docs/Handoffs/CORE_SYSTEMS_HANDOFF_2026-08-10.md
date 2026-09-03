# Core gameplay systems — handoff (2026-08-10)

**Scope: CORE SYSTEM FUNCTION ONLY.** The owner handles cosmetic/UI polish. Do not spend
effort on visual polish, tokens, or widget styling.

**Trust this file over `CORE_SYSTEMS_HANDOFF_2026-08-09.md`** — four of its claims were
falsified on 2026-08-10. See §7.

---

## 1. Verified state

| Thing | State |
|---|---|
| Build | **Green.** `Result: Succeeded`, 0 errors. DLL @ 2026-08-10 20:45 |
| `Melodia.Wiring` automation suite | **5/5 passing**, including `RhythmSkills.MappingResolves` |
| `StockSkillRhythmIds` | **4 entries, saved** — all four Melusina skills mapped |
| `BP_BattleController` | **placed in `L_KaleidoNave`**, saved |
| Harmonix music clock | **observed running for the first time** (once the controller existed) |
| Dreamstate→KaleidoNave merge | **DONE** — 18 actors moved, level deleted, allowlist stripped |
| PIE probe on `L_KaleidoNave` | **`tagged=1 controllers=1`** (was `tagged=0`) |
| Dirty packages | none |

### The rhythm mapping
`BP_MelusinaPetalCadence_C → cadence_strike`, `BP_MelusinaFocusAttack_C → downbeat_break`,
`BP_MelusinaDoubleHit_C → resonant_arc`, `BP_MelusinaTrueStrike_C → crescendo_wave`.

Pattern choice is a **feel** decision and trivially retuned via `set_cdo_property`. The
definition's `TargetMode` is irrelevant on the stock-skill path — only the pattern and the
grade multiplier are consumed.

---

## 2. Execution order

### 1. ~~Merge Dreamstate into KaleidoNave~~ — **DONE 2026-08-10**
All 18 actors moved into `L_KaleidoNave`'s persistent level, sublevel entry removed,
`L_Melodia_Dreamstate` deleted, and the level stripped from `TravelLevelIds`.

Verified: `L_KaleidoNave` = 50 actors, one level, no sublevels. Labels and tags preserved
(`FirstDream_InteractionBattle` still carries `melodia_smoke_encounter`). PIE probe now reads
**`tagged=1 controllers=1`** — it was `tagged=0` before. The *"BattleController blueprint needs
to be in the level"* error is gone. No dirty packages, no runtime errors.

Backup retained at `Saved/Recovery/DreamstateRemoval_2026-08-10/L_Melodia_Dreamstate.umap`.
**Do not delete it** until the slice has been played through.

Method, for the next time this is needed:
`mesh_query manage_sublevel {sub_action: "move_actors", actor_names: [...], dest_level:
"PersistentLevel"}`. Two traps: the destination for the persistent level is the literal string
**`"PersistentLevel"`** (an asset path or level name returns *"Destination level not found"*),
and the action matches actor **names, not labels**. `PlayerStart_0`, `StaticMeshActor_1..4`,
`PointLight_0/1` and `PCGVolume_0` existed in *both* levels, so the first attempt silently
matched KaleidoNave's copies and returned `moved_count: 0`. Rename colliding actors to unique
names first (`a.rename('Dream_' + a.get_name())`), then move. Deleting the level asset needs
`EditorAssetLibrary.delete_asset` — `editor_query delete_assets` returned
`failed_to_delete` even after the sublevel was removed.

### 2. The song map has no beat map — START HERE
`LogMIDI: SongMaps does not contain a Beat Map` fires **every frame** now that the clock
runs. A valid song map needs `Init(ticksPerQuarter)` + tempo point + **bar map** + **beat
map**. Copy the engine's own path — `UMusicClockComponent::MakeDefaultSongMap()` — or use a
properly imported asset. **Do not guard around the malformed structure** (working agreement
rule 2; AGENTS.md rule 16, which exists because hand-building one of these already crashed
the editor).

This is now the thing between the project and a visible/audible beat.

### 3. Trigger a battle and watch the rhythm path
After step 1, PIE on `L_KaleidoNave`. The interaction actor starts the battle on its own once
a `BP_BattleController` is present — no console command exists for this, and
`StartTaggedJRPGBattle` lives on a **GameInstance subsystem**, which `pie_call_function`
cannot target (it resolves actors only).

Watch for: `MELODIA_RHYTHM` without `no rhythm id mapped`; the highway appearing; Q/W/O/P
registering; `ShowRhythmGrade`; beat pulse landing **on** the beat (the `sin²`→`cos²` fix has
compiled since 08-09 but has still never been observed); 128 BPM.

### 4. Verify the damage-scalar sequencing — never reached this session
`MelodiaRhythmCombatSubsystem.h:188-199` documents that the montage damage notify fires ~2.5s
**before** `FinishSession` latches the scalar. If `UseSkill` is not sequenced behind the
`OnRhythmComplete` broadcast, `GetPendingDamageMultiplier()` reads **1.0** and rhythm cannot
affect damage at all. **Read the live sequencing before changing anything.** Note the
deliberate comment at `MelodiaRhythmCombatSubsystem.cpp:160-165` — `PendingDamageMultiplier`
is intentionally not reset on invalidate; `StartSession` owns the reset. Do not "fix" that.

A/B with `melodia.Rhythm.Disable 1`, **not** Perfect-vs-Miss (Decision 016 sets no miss
penalty, so that comparison shows no delta by design).

### 5. Highway note rendering — never reached
`SetNoteHighwayActive_Implementation` only *stores* `bNoteHighwayActive` / `HighwayNotes` /
`HighwayBeatPosition` / `HighwayScrollBeatsAhead`. Nothing renders, and
`WBP_MelodiaRhythmHighway` contains none of those names — its only authored function is
`SetLanePressed`. This is the one genuine T3D injection target.

Before injecting: re-export baselines (`Content/Exports/` is Aug 1; `Saved/T3D/` has neither
battle asset), resolve the `unresolved_member_parent` warning by reading a real parent-call
node's exact `FunctionReference=` spelling, and run `bp_live_path.py` — injecting into an
unreachable graph *succeeds*, which is worse than failing.

### 6. Wire `RestorePartyAfterBattle`
`UMelodiaJRPGPostBattleLibrary::RestorePartyAfterBattle(UObject* BattleController)` now
compiles and is in the binary. It still has **zero call sites**. It restores full HP/MP on the
stock `playerUnits` array before `UpdatePlayerUnits` syncs state back — the correct seam.
Hang it off the proven battle-end path (`CompleteBattle` → `ResumeQuillOnce()`), which is
confirmed exactly-once.

Owner decision: **heal only, no retry-on-defeat.** Defeat still exits to `L_MelodiaMainMenu`.
`NotifyDeathRecovery` / `NotifyRetryRecovery` stay uncalled.

**Check before trusting it:** line 83 looks up a struct member named **`curentMP`** (missing
the second `r`) while line 82 uses `currentHP`. Either a faithful match to a typo in the stock
`FS_UnitState` or a real bug that silently disables the MP half of the map write. Read the
struct and settle it.

---

## 3. Do not "fix" these

- Lane input (`RegisterLaneHit` on Q/W/O/P in **both** `OnKeyDown` and `OnKeyUp`),
  `ShowRhythmGrade`, and the highway creator in `BP_BattleUI::ShowBattleUI`.
- Petal Cadence — it applies Resonance via the `buffs` array on `BP_BattleSkillBase`.
- `PendingDamageMultiplier` not resetting in `InvalidateSession` — deliberate.
- `BP_MelodiaGameMode` — zero referencers, not `GlobalDefaultGameMode`, yet the sole
  referencer of both `WBP_Battle_Rhythm` and `WBP_Battle_Results`. **Do not wire into either.**

---

## 4. Tooling limits learned the hard way

- **Actor moves between levels are `mesh_query manage_sublevel {sub_action: "move_actors"}`.**
  What does *not* work, so nobody re-derives it: `EditorLevelUtils.move_actors_to_level` /
  `move_selected_actors_to_level` both demand a `LevelStreaming` destination — the persistent
  level is not one, and `None` trips an ensure. `ACTOR COPY`/`ACTOR PASTE` no-op both via
  `SystemLibrary.execute_console_command` (no world context) and via Monolith's
  `run_console_command` (reports success, pastes nothing). Use the Monolith action.
- **`pie_call_function` resolves actors only** — it cannot reach GameInstance subsystems.
- `run_pie_smoke` rejects `map_path`/`duration_seconds`; the params are `map` and `duration`.
  Unknown params are **warned about, not fatal** — it will silently run on the wrong map.
- `poll_pie_smoke` returns the full per-frame sample array. Prefer `tail_log` / `search_logs`.

---

## 5. Hard rules still in force

One editor instance. Never `git clean -fd` or `git checkout -- .` — bulk `Content/` is
untracked and unrecoverable. No Python against
`Content/TurnBasedJRPGTemplate/Blueprints/Skills/` (`D_DamageType` glue = fatal editor death;
Monolith `blueprint_query` is native C++ and safe). `MODAL_OPEN` is a dialog, not a hang.
Unclean compile or `matched:false` is a HARD STOP. Header changes cannot be Live Coded.
`bRelaxedAllowlistInEditor = true` means the allowlist does **not** fail closed in editor
builds — run a verification pass with it off.

---

## 6. Acceptance criteria (owner's words, unchanged)

Blueprints for gameplay fully wired; turn-based rhythm skills cause the note highway to
appear, trigger damage, and advance the turn; Sir Melodious is the only available active pawn
to ctrl-switch to on the integration map.

---

## 7. CORRECTIONS — inherit these, not the 08-09 originals

1. **`StockSkillRhythmIds` was never empty** — it held one entry. The "no such property, no
   MapProperty" claim came from a string dump. A dump- or census-based method **cannot
   establish absence**; read the CDO through reflection. (Same failure mode as the
   expose-on-spawn miss — see AGENTS.md rules 13 and 20.)
2. **The encounter actor is in `L_Melodia_Dreamstate`**, a streaming sublevel of
   `L_KaleidoNave` — not in KaleidoNave itself, and it does not stream in at PIE start.
3. **The tree was not green** on 2026-08-10 — four blockers, three of them latent
   unity-build collisions that incremental builds had been hiding.
4. **`MelodiaJRPGPostBattleLibrary` had never compiled.** It was a draft, not finished work.
5. **The missing `BP_BattleController` was necessary but not sufficient.** It started the
   music clock; the encounter actor is still absent from that world, and the missing beat map
   surfaced immediately behind it.
