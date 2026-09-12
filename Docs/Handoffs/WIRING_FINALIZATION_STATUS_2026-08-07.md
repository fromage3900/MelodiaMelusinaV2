# Wiring Finalization Status — 2026-08-07 (paused for editor restart)

**Scope:** Persona-lite loop finalization (Blueprint wiring + game systems) before editor rebuild.
**Status:** PAUSED mid-execution — editor restarted by owner. All completed work is saved to disk and survives the restart.

---

## 1. Done, verified, SAVED (survives restart)

### B1 — Battle UI creation chain restored ✅
- `BP_BattleController` EventGraph (`/Game/TurnBasedJRPGTemplate/Blueprints/Battle/BP_BattleController`):
  - Added `K2Node_CreateWidget_0` "Create BP Battle UI Widget", `Class = /Game/TurnBasedJRPGTemplate/Blueprints/UI/BP_BattleUI.BP_BattleUI_C`
  - Wired (matches pristine `_ThirdParty` copy exactly):
    - `K2Node_CallFunction_17` (AdjustCamera).then → CreateWidget_0.execute
    - `K2Node_MacroInstance_4` (SwitchToStaticCamera).success → CreateWidget_0.execute
    - CreateWidget_0.then → `K2Node_VariableSet_10` (Set battleUI).execute
    - CreateWidget_0.ReturnValue → VariableSet_10.battleUI
  - Intact downstream chain (pre-existing): Set battleUI → AddToViewport(14) → ShowBattleUI(6) → SetReadyUnits(18)
  - Removed dead islands: `K2Node_CallFunction_237/238/239/240`, `K2Node_VariableSet_27/28` (class-less Create Widget stubs for melodiaBattleUI/MelodiaUI)
  - Compile: 0 errors. Saved.
- **Why it matters:** `BP_BattleUI.OnKeyDown` (D/F/J/K → `RegisterLaneHit(0..3)`) + `ShowBattleUI` (PushContext, CreateWidget WBP_MelodiaRhythmHighway, BindRhythmHUD, SetKeyboardFocus) + `HideBattleUI` teardown are all on this widget — nothing ever instantiated it before this fix.

### B2 — Encounter bridge (021b replacement) ✅
- **Tags VERIFIED present on disk** (state evolved since inventory snapshot):
  - `L_KaleidoNave` `BP_InteractionBattle_C_0` (FirstDream_InteractionBattle) → tags `['melodia_smoke_encounter']`
  - `L_Melodia_Dreamstate` `BP_InteractionBattle_C_0` → tags `['melodia_smoke_encounter']`
- **Bridge contract VERIFIED:** `UMelodiaExternalJRPGBridgeSubsystem::StartTaggedJRPGBattle` requires exactly 1 tagged actor + `FindFunction("StartBattle")` + `offLevelBattleData` struct prop + `OnBattleOver` multicast. All present:
  - `StartBattle(enemyList, offLevelBattleData)` exists on `BP_DynamicEnemyBattleBase` (inherited by BP_InteractionBattle) — first struct param matches the property struct.
  - `offLevelBattleData` + `OnBattleOver` live on `BP_BattleBase`.
- **NEW actor built + placed + persisted:**
  - `BP_KaleidoNaveArrivalTrigger` (`/Game/MelodiaIntegration/Blueprints/Opening/`) — EventGraph: `EventBeginPlay → Delay(0.5) → SpawnActor QuillscriptInterpreter → Cast → Set Interpreter → Start(ScriptAsset=/Game/MelodiaIntegration/Narrative/MelodiaQuillSmoke.MelodiaQuillSmoke)`. Compile 0 errors, saved.
  - Placed in `L_KaleidoNave` as actor `ArrivalEncounterTrigger_Smoke` (label), near first PlayerStart, folder `Melodia|Opening`. Verified persisted across a level reload.
- **Flow this enables:** sanctuary MorningIntro beat fires `melodia:battle` → no tagged actor in L_MelusinaMorning → authored graceful abort branch ("battle could not begin") → Sir's C++ departure (`DepartureDestinationLevel = /Game/EnvSandbox/Environments/L_KaleidoNave`, CDO-verified) → travel to KaleidoNave → `ArrivalEncounterTrigger_Smoke` plays `MelodiaQuillSmoke` (the orphaned battle beat, identical battle content) → `melodia:battle:melodia_smoke_encounter` fires → bridge finds the tagged actor → battle starts in-world.

### B5 — Portals ✅ (verified, no change needed)
- `L_KaleidoNave` + `L_Melodia_Dreamstate` `MelodiaOpeningPortal_0` instances: `DestinationLevelName=/Game/ZenForestTest`, `TravelEvent=CompleteDreamstate`, bOneShot=true — functional C++ class (`MelodiaOpeningPortal.cpp` routes through `UMelodiaAuthorityLocator` → `TravelTo`, OpenLevel fallback). The inventory report's "unconfigured portals" was based on stale data.
- **NOTE (open, not blocking):** Dreamstate portal still points at ZenForestTest, not KaleidoNave. Per decision 029i the portal was meant to be repointed to `L_KaleidoNave`. But Sir's departure goes straight to KaleidoNave (CDO), so the portal is a secondary exit. Decide whether to repoint during the post-rebuild phase.

### B3a — Rhythm function surface verified ✅ (research)
- Compiled function cache (live editor): `FinishSession`, `GetPendingDamageMultiplier`, `ClearPendingDamageMultiplier`, `ConsumePendingRequest`, `HasPendingRequest`, `SubmitRatedInput`, `StartSession`, `BindRhythmHUD`, `RegisterLaneHit` — ALL present on `MelodiaRhythmCombatSubsystem`.
- **`UseSkillWithRhythm` NOT in compiled binary** — source `.h` (08-07 11:36) newer than generated header (08-06 23:49). The BP edit for B3 must happen AFTER the C++ rebuild.

---

## 2. Research findings (offline, from `_bpc_evg.json` export)

### B3 — old rhythm cluster (defect confirmed, fix deferred to post-rebuild)
Live cluster: `CustomEvent_34 (UseSkill) → Set currentTargetUnit → AssignDelegate_3 (Bind OnSkillUsed) → CallFunction_115 (UseMP) → CallFunction_196 (StartSession) → Branch(19) [StartSession>0] → BOTH then/else → CallFunction_124 (UseSkill)`.
- **Bug:** montage fires in parallel with the rhythm session → damage notify (~0.51s) reads `PendingDamageMultiplier` before FinishSession latches (~3.05s) → unscaled damage. Exactly the defect `UseSkillWithRhythm` (h:223-244) was built to replace.
- **B3b (post-rebuild):** add `UseSkillWithRhythm(currentSkill)` node, wire `UseMP.then → UseSkillWithRhythm → HideSkillActionButtons(110)`, delete `StartSession(196)`, `Branch(19)`, `ResolveRhythmSkillId(198)`, int-compare(197), `UseSkill(124)`.

### B4 — victory/defeat closure (gap confirmed, exact fix known)
- Downstream chains ARE wired and correct:
  - `OnBattleOver(15) → FadeOut(154) → HideBattleUI(53) → SwitchEnum_0 → CompleteBattle(Victory=45 / Defeat=49 / Fled=51)` (narrative typed completion ✅)
  - `PlayerWon(13) → Keys(180) → UpdatePlayerUnits(191) → AddGold → … → SwitchToExploreMode(47)`
  - `EnemyWon(14) → Delay(123) → PlayVictoryAnimation(127) → CreateWidget_3 (Victory widget)` and `(130) → CreateWidget_5 (Defeat widget)`
- **GAP:** `PlayerWon(13)` and `EnemyWon(14)` have ZERO callers in the live BP. `OnBattleOverHandler(8)` (bound via AddDelegate_2) ends after `Set isBattleOver + Set battleResult`. `Branch(3)` (isBattleOver, from OnUnitsTurnEnded) → `CallFunction_55 (OnBattleOver).then` is **empty**.
- **Pristine comparison:** pristine `_ThirdParty` copy HAS `K2Node_CallFunction_34 (Player Won)` + `_35 (Enemy Won)` calling those custom events — the live copy lost them (same removal that took the UI creation). Fix = re-add the two caller nodes wired off the result routing, exactly as pristine does (needs 1-2 read calls on the pristine BP after editor restart — use `get_execution_flow` or `compare_blueprints`, NOT per-node get_node_details which crashed the editor).
- Also noted: `BP_BattleBase.OverlapStarted` empty stub, `DetectInteraction` graph missing on runtime PC (pre-existing, separate).

### B6 — new beats (unreachable, planned wiring)
- `MelodiaQuillSolsticeDrum`/`MelodiaQuillDawnVeil`: `referenced_by = []`.
- `melodia_q_echo_02_complete` path exists (StarWeaver, ZenForestTest-reachable, needs play-twice accept→complete).
- `melodia_q_echo_03_complete` CANNOT be set: `MelodiaQuillTwilightDancer` orphaned, quest `melodia_q_echo_03` never accepted → DawnVeil permanently unreachable until TwilightDancer chain restored.

### B7 — grade display
- `BP_MelodiaBattleUI::ShowRhythmGrade` = empty stub (entry node only). `OnPresentationRhythmResult` has no listener. Wire after B3b lands.

---

## 3. C++ prep spec (ready to apply — subagent-verified)

- **C1:** Insert `ConsumePendingRequest` fallback in `FinishSession` between cpp:518–520 (verbatim before/after in the prep report; compile-safe — `TryGrantShards(FName,int32,FName)` + `TrySpendMana(float)` match).
- **C2:** `OrreryMainMenuGameMode::CanonicalSaveSlot = "MelodiaJRPGSlot0"` (currently "MelusinaSlot0" — mismatches everything else).
- **NOT NEEDED (already correct in tree):** the "ordering doc comment" and "accumulator/latch" items are already in the agreed final state (StartSession owns the multiplier reset; ResetSessionAccumulators doesn't touch it; header + cpp agree; no test asserts the multiplier).

---

## 4. Operational learnings (avoid editor crashes)

1. **NEVER `export_graph` a large EventGraph** (703-node BP_BattleController export + KaleidoNave T3D export both crashed the editor / MCP).
2. **Avoid per-node `get_node_details` loops on the 700-node BP** — 3 editor crashes traced to `resolve_node` / `get_functions` / repeated `get_node_details` on BP_BattleController. Use local JSON exports for analysis; single `compare_blueprints` / `get_execution_flow` / `search_nodes` for targeted reads; `batch_execute` for edits; compile once.
3. `build_blueprint_from_spec`: fields at TOP level (not nested under `spec`); `VariableSet` nodes need the variable to exist first (`add_variable` before `add_node`); `SpawnActorFromClass` needs a `MakeTransform` feeding `SpawnTransform`.
4. Editor Python: `EditorLevelLibrary.load_level/save_current_level` (deprecated but works); load BP class via `unreal.load_class(None, "/path.BP_X_C")`; spawn with `location=`/`rotation=` kwargs (Transform kwarg fails).
5. MCP restart dance: kill `monolith_proxy`, relaunch `powershell -Command 'Start-Sleep 86400 | & proxy.exe'` hidden; or just restart the editor (Monolith HTTP listener boots inside it on 9316).

---

## 5. Remaining work (ordered)

| # | Item | Depends on | Notes |
|---|------|-----------|-------|
| B4 | Re-add PlayerWon/EnemyWon callers in BP_BattleController (from pristine pattern) | editor up | 1-2 reads + batch edit |
| B7 | Wire ShowRhythmGrade / OnPresentationRhythmResult listener | B3b (grade source) | BP_MelodiaBattleUI |
| B6 | Wire SolsticeDrum ref + restore TwilightDancer→echo_03 chain | editor up | QSC refs + NPC wiring |
| C1+C2 | C++ edits + `-NoUBA` build | editor CLOSED | verbatim spec in prep report |
| B3b | Post-rebuild: UseSkillWithRhythm node + remove old cluster | C build done | adds the scaled-damage path |
| F1 | Skin 19 stock widgets + 3 skill surfaces (Universal texture set) | any | proven set is `T_Melodia_Universal_*`, NOT the 339 unreferenced Figma textures |
| P1/P2 | Full PIE smoke; errored-blueprints clean; regression suite | all above | loop: sanctuary→departure→KaleidoNave→battle→rhythm→victory→reward→save→load |

**Rollback safety:** filesystem backup at `CompatibilityLabs/ProductionPreIntegrationBackup_2026-07-26`; B1/B2 edits are isolated to one BP + one new BP + one level actor addition.
