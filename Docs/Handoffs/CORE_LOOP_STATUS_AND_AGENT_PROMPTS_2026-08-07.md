# Core Loop — Status, Next Steps, and Agent Prompts (2026-08-07, late)

**Supersedes:** `INTEGRATION_POLISH_HANDOFFS_2026-08-06.md` (partly stale — Lanes A/C/E are done, Lane D's premise was inverted and is corrected here).
**Companion:** `WIRING_FINALIZATION_STATUS_2026-08-07.md` (owner-authored; B4 and B6 sections in it are now stale, see §1).

---

## 0. The one thing that matters

The game boots, runs and tears down cleanly — PIE smoke passes across three maps. What has **not** executed is the rhythm→damage path specifically: no `MELODIA_RHYTHM session=` line exists in any log yet. The proof that closes it is one battle where a full-Perfect run and a full-Miss run produce **different damage numbers**.

**As of 2026-08-07 there is now an automated wiring suite** — `Melodia.Wiring.*` — that asserts the seams are connected. 13/13 pass across `Melodia.Integration`, `Melodia.Wiring` and `Melodia.RhythmCombat`. Prefer running it over re-reading docs; it is the only status claim in this repo that cannot go stale.

```
UnrealEditor-Cmd.exe <project> -ExecCmds="Automation RunTests Melodia; Quit" -unattended -nullrhi -nosplash
```

---

## 1. Corrections to claims currently circulating

Verify before acting on any of these; several cost real time this session.

| Claim in circulation | Reality |
|---|---|
| `WBP_MelodiaRhythmHighway` "never created" | **False.** Exists at `/Game/Melodia/UI/Rhythm/`, 13 widgets, `LaneRow` + `Lane_D/F/J/K`. |
| `MelodiaMorningIntro` "has no source, black box" | **False.** 42 statements recoverable from the `.uasset`; editable via `CompileQuillSource`. |
| `PlayerWon`/`EnemyWon` have zero callers | **Stale.** `SwitchEnum_0 → Sequence_3/4 → then_0 CompleteBattle, then_1 PlayerWon(204)/EnemyWon(205)`. Already wired, and better than pristine (narrative + stock run in parallel). |
| `MelodiaQuillTwilightDancer` orphaned / `referenced_by=[]` | **False.** It was assigned all along. `find_references` does **not** reliably resolve `TSoftObjectPtr` — do not trust it for soft refs. |
| `UseSkillWithRhythm` not in the compiled binary | **Stale.** Generated header 08-07 15:10, DLL 17:38. It is compiled. B3b is unblocked. |
| Damage notify fires "long after" the rhythm session ends | **Inverted.** Notify ~0.51s, session end ~3.05s. Corrected in source; `UseSkillWithRhythm` is the fix. |
| `melodia:stat:` "wired end-to-end (tested)" | **False.** Tests called `AddSocialStat` directly and bypassed the notification boundary — which is why the arity bug survived. |
| Portals "unconfigured" | **Stale.** Verified configured. |
| `PatternAsset` empty on all 8 skills | **Fixed 08-07.** All 8 now reference `DA_MelodiaSongs`; asserted by `Melodia.Wiring.RhythmSkills.HaveCharts`. |
| `NarrativeIntent` test "fails" | **Fixed 08-07.** Was two bugs — see §2 "Late findings". |

---

## 2. Current state

### Compiled and in the binary (DLL 08-07 17:38)
- `HandleStatVerb` now requires the authored 5-part `melodia:stat:<IntentId>:<StatId>:<Delta>` and routes through `GrantDialogueSocialStat` (which carries `ConsumeOnce`). The 4-part form was deleted. **Harmony can now be granted.**
- `UseSkillWithRhythm(StockSkill)` — replaces the whole `StartSession → Branch → UseSkill` cluster. Unmapped skills dispatch same-frame; rhythm skills defer until `FinishSession` latches the multiplier.
- `SessionEndBeat` set in `StartSession` for charted **and** uncharted sessions; `bSessionCharted` guard removed from the Tick self-close. **Sessions can now finish** — previously `FinishSession` was unreachable.
- `PendingDamageMultiplier` reset moved out of `ResetSessionAccumulators` into `StartSession`, so `InvalidateSession` no longer destroys a live latch.
- `ResolveRhythmSkillId` + `UMelodiaIntegrationConfig::StockSkillRhythmIds` (4 entries seeded).
- `HandleRewardRequested` → `UMelodiaPersonaContent::RewardEquipment` → `RequestEquip`.
- `OnRhythmComplete` listener on `UMelodiaJRPGPresentationRhythmComponent`.
- `SetJudgment` per lane press; aggregate verdict in `FinishSession`.

### Blueprint / asset, saved
- `BP_BattleController`: Battle UI creation chain restored (`K2Node_CreateWidget_0`) — **nothing instantiated `BP_BattleUI` before this**, so all its wiring was dead. `ClearPendingDamageMultiplier` + `ConsumePendingRequest` on both `DealDamage.then`. Victory/Defeat sequences wired.
- `BP_BattleUI`: `OnKeyDown` D/F/J/K → `RegisterLaneHit(0..3)` with a `Select` gating Handled/Unhandled; `bIsFocusable=true` (CDO); `SetKeyboardFocus` in `ShowBattleUI`; highway create→viewport(z90)→`BindRhythmHUD`→show; teardown ordered `InvalidateSession` → `RemoveFromParent`.
- `WBP_MelodiaRhythmHighway`: `LaneRow` bottom-centre 880×140, four tinted lanes, 42pt centred labels.
- `BP_ActionButton`: `ActionOverlay` fills its button (was offset to `left=243.5`, rendering labels outside their own buttons).
- Save slots unified on `MelodiaJRPGSlot0/1/2` across writer + both readers (`BP_SavePointBase`, `BP_SaveUI`, `WBP_SaveLoadPanel`).
- `BP_MelodiaSirMelodiousMorningIntro`: double Quill-resume deleted.
- `DA_MelodiaPersonaContent.RewardEquipment` seeded (3 entries) — **note: `author_melodia_persona_foundation.py` does not write this field; it was hand-seeded and a re-run will not restore it.**
- ZenForestTest: `SD_03_SolsticeSinger` / `DC_04_DawnChorus` given `NPCId` + tags. All five NPCs verified consistent.

### Late findings (2026-08-07 evening) — all fixed and built

**`HandleQuillNotification` was never bound.** It and `HandleQuillScriptPlay` were declared without `UFUNCTION()` but bound with `AddUniqueDynamic` (`MelodiaNarrativeSubsystem.cpp:63-64`). Dynamic delegates only bind reflected functions, so both binds failed at runtime every session with `Unable to bind delegate to 'HandleQuillNotification'`. **No `melodia:` intent from Quill had ever reached the narrative subsystem** — battle, travel, reward, stat, quest, flag. This sat underneath every other narrative defect found this session; the `melodia:stat:` arity bug was real, but the message was never arriving regardless. Both now carry `UFUNCTION()`.

**`bRelaxedAllowlistInEditor` demonstrably masks allowlist failures.** The new test proved it live: an unregistered encounter id passed with `MELODIA_RELAXED_ALLOWLIST: Allowing unregistered ID 'UnknownEncounter'`. `MelodiaIntegrationTests` now sets it `false` so it asserts Shipping semantics. Any id only ever exercised in PIE under relaxed mode is unproven.

**Test harness:** `UGameInstanceSubsystem` declares `ClassWithin = UGameInstance`, so `NewObject(GetTransientPackage())` trips the `ClassWithin` ensure and marks the whole test failed even when its assertions pass. Construct subsystems with a bare `UGameInstance` outer.

**`Melodia.Roguelike.Functional.*` cannot run headless.** `ThreeStagePhysicalRoute` and `TwentyFiveGenerationSoak` poll `FindPIEWorld()` and need a live PIE session plus a placed `AMelodiaDungeonRunCoordinator`. A `-nullrhi` commandlet never provides one, so they can only fail there. Run them from the editor's Session Frontend. Their earlier ensure was collateral from the `HandleQuillNotification` bug and is gone. **No evidence they are actually broken.**

**Grade display wired.** `UMelodiaUIBridgeSubsystem::ShowRhythmGradeOnBattleUI(GradeText, HitCount, MissCount)` drives `BP_MelodiaBattleUI`'s Blueprint event reflectively (Monolith cannot author a delegate bind). It validates `ParmsSize`/`NumParms` and refuses on mismatch, logging the expected signature, rather than invoking a mismatched frame. **Owed in-editor:** give `ShowRhythmGrade` those three parameters and display them; C++ starts driving it the moment the signature matches.

**`GradeToText` is now public + `BlueprintPure`** so the highway HUD, battle overlay and Blueprint read the same labels from one place.

### Known-broken, not yet fixed
1. **Quest 1 cannot complete.** `HandleJRPGBattleEnded` gates on `ActiveBridgeEncounterId == "Encounter_CrystalShard"`. That actor **does exist** (`JRPG_CrystalShard_Battle` in ZenForestTest) but the id is **not** in `DA_MelodiaIntegrationConfig.EncounterIds`. Quests 2 and 3 chain behind it.
2. **A rejected quest permanently burns its retry.** `CompleteQuest` calls `ConsumeOnce` *before* broadcasting; Persona no-ops on a `Locked` quest and the intent is already spent. `ConsumedIntentIds` is `SaveGame`-flagged, so this persists. Fixing (1) will not repair an existing save.
3. **`MelodiaIntegrationTests.cpp:374`** asserts the removed 4-part `melodia:stat:` form. Compiles; fails at run.
4. **`UMelodiaHairComponent` init order.** Constructor sets `SetAnimInstanceClass`, but `SourceMeshComponent` is assigned in `BindToOwnerMesh()` which `BeginPlay` defers one tick. 2–3 `Accessed None` errors per PIE start, stopping at `MELUSINA_HAIR_BOUND`. **Do not add an `IsValid` guard** — it would freeze `HeadTransform` at identity.
5. **`bRelaxedAllowlistInEditor = true`** (`MelodiaIntegrationConfig.h:74`) — unregistered ids pass silently in PIE and hard-fail in Shipping.
6. **`MelodiaQuillSmoke` duplicates `MelodiaMorningIntro`** — same battle id, same `melodia_smoke_reward`, same flag, against one `ConsumedRewardIds`. Second authority on a consume-once id.
7. **`BP_MelodiaBattleUI::ShowRhythmGrade`** is an empty stub; `OnPresentationRhythmResult` has no listener.
8. **Persona subsystem has zero Blueprint callers** project-wide (byte-scanned). No quest log, no equip UI, no Harmony readout bound.

---

## 3. T3D pipeline status

**Working, but the exports are stale and one artifact is actively misleading.**

| Path | State |
|---|---|
| `Saved/T3D/live_catalog/` | 24 files, last written 08-06 00:56 |
| `Saved/T3D/full_catalog/` | 22 files, 08-05 11:57 |
| `Saved/T3D/LIVE_VS_CATALOG_2026-08-06.md` | 08-06 comparison report |
| `Saved/T3D/rhythm_pipeline.json` | **08-04 — STALE AND DANGEROUS.** Predates all current wiring. In it `_196` is `RecordInputNow` (not `StartSession`) and `IfThenElse_19` does not exist. An agent planned from it and produced unusable node ids. **Do not plan from this file.** |
| `onbattlecompleted_spec.json` / `bind_onbattlecompleted.ps1` / `fix_onbattlecompleted.py` | Failed attempts to fake `CreateDelegate` as `KismetSystemLibrary::CreateDelegate` (no such function). Dead ends — the `AddDelegate` node type exists but there is no way to produce its `Delegate` input pin. |

**Verdict:** T3D export/inspect works and is the safe way to analyse the 703-node `BP_BattleController` offline. `build_blueprint_from_spec` works for injection. **T3D cannot author delegate binds** — that remains C++ or hand-authoring. Re-export before any analysis; anything older than the current session is untrustworthy.

---

## 4. Ordered next steps

| # | Task | Needs | Blocks |
|---|---|---|---|
| 1 | **B3b** — `BP_BattleController`: delete `StartSession(196)`, `Branch(19)`, `ResolveRhythmSkillId(198)`, int-compare(197), `UseSkill(124)`; insert one `UseSkillWithRhythm` fed by `currentSkill`, exec `UseMP(115).then → UseSkillWithRhythm → HideSkillActionButtons(110)` | editor | **All rhythm damage scaling.** Until this lands, every rhythm hit is unscaled. |
| 2 | Allowlist `Encounter_CrystalShard` in `DA_MelodiaIntegrationConfig.EncounterIds` (preferred over editing the C++ literal — the actor is real) | editor | quests 1→2→3 |
| 3 | Fix `CompleteQuest` consume-before-broadcast ordering | C++ | quest retry after any rejection |
| 4 | Fix `MelodiaIntegrationTests.cpp:374` to the 5-part form; add a test using the real string from `MelodiaQuillPetalPriestess.qsc:51` | C++ | test suite green |
| 5 | `UMelodiaHairComponent` — move `SetAnimationMode`/`SetAnimInstanceClass` into `BindToOwnerMesh()` before `InitAnim(true)` | C++ | PIE log noise |
| 6 | Wire `ShowRhythmGrade` / an `OnPresentationRhythmResult` listener | editor, after 1 | grade feedback |
| 7 | Resolve `MelodiaQuillSmoke` vs `MelodiaMorningIntro` duplication | decision | reward integrity |
| 8 | **PIE walk** — see §6 | all above | everything |

**Superseded by the 08-07 evening pass** (do not re-do): the `NarrativeIntent` ensure, the `melodia:stat:` test, the hair AnimBP init order, `PatternAsset` on all 8 skills, and the `ShowRhythmGrade` C++ forwarder. Run `Melodia.Wiring` before starting anything — it will tell you the current truth faster than reading this table.

---

## 5. Environment knowledge (carry into every prompt)

- Build recipe is **`-NoUBA`**. Editor must be **CLOSED** to build, **OPEN** for Monolith. A C++ agent and an editor agent can run concurrently **only if the C++ agent does not build**.
- **One editor writer at a time.** Monolith is a single connection.
- **Verify every write with an independent readback**, never the setter's response. `set_widget_property` echoes an empty `value` on struct writes that succeeded. `blueprint_query save_asset` has failed where `editor_query save_packages` worked.
- **Never `export_graph` the 703-node `BP_BattleController`**, and never loop `get_node_details` over it — three editor crashes traced to this. Use `search_nodes`, single `get_execution_flow`/`compare_blueprints`, `batch_execute` for edits, compile once.
- Monolith `add_node` has **no `CreateDelegate`** → BP delegate binds need C++ or hand-authoring. `build_blueprint_from_spec` wires only injected-subgraph internal exec pins; connecting to pre-existing nodes needs a second `connect_pins` pass. Its secondary `Return` node gets no `ReturnValue` pin. Short type names (`Branch`, `VariableSet`), not `K2Node_` prefixes. Param names are inconsistent — read the error, it names the key.
- `find_references` does **not** reliably resolve `TSoftObjectPtr`.
- `InputMappingContext.mappings` is deprecated in UE 5.8; live field is `DefaultKeyMappings.mappings`.
- `GetKey`'s input pin is `Input`, not `Key`. `Select` pin names are `Index`, `Option 0`, `Option 1` — connect the bool to `Index` **first** or it coerces to int.
- Doc filename dates are when written, not when true. Check source mtimes.

---

## 6. PIE playtest checklist

Run in order. Each line: action → expected log/screen → meaning if absent.

1. **Boot** → `Melodia rhythm combat subsystem loaded N skills from asset registry.` → asset-registry discovery works.
2. **Boot** → `MELODIA_AUTHORITY registered InputContextProvider` / `TravelProvider` → authority locator up.
3. **Talk to Petal Priestess (ZenForestTest)** → `MELUSINA_NPC_QUILL_HANDOFF npc=SD_02_PetalPriestess asset=MelodiaQuillPetalPriestess` → NPC→Quill handoff works.
4. **Take the Harmony choice** → no intent-rejection line for `melodia:stat:...` → the 5-part fix landed. *If you see a rejection, `HandleStatVerb` regressed.*
5. **Check `BP_ExploreUI`** → Harmony reads 1 → the read-model surfaces. *(Currently unbound — expect failure until §2 item 8 is done.)*
6. **Enter battle** → `BP_BattleUI` appears → B1's creation chain works.
7. **Battle start** → rhythm highway visible, four tinted lanes labelled D/F/J/K → highway create+bind chain works.
8. **Press D/F/J/K** → `MELODIA_RHYTHM lane=N ... grade=...` → lane input + focus work. *If absent: focus. Confirm `bIsFocusable` and `SetKeyboardFocus`.*
9. **Judgment text** shows PERFECT/GREAT/GOOD/MISS → `SetJudgment` reaches a live widget.
10. **Let the session run out** → session self-closes; `OnRhythmComplete` fires → the Tick self-close fix works.
11. **Compare damage: all-Perfect run vs all-Miss run** → **numbers must differ** → this is the only real proof the multiplier reaches damage. Equal numbers = B3b not landed or notify still ahead of the latch.
12. **Win the battle** → Quill resumes **exactly once** → double-resume stays deleted.
13. **Reward** → equipment granted → `HandleRewardRequested` → `RequestEquip` path works.
14. **Save at a save point** → file written to `MelodiaJRPGSlot0` → slot unification works.
15. **Full process restart** (not PIE restart) → **Load** → Harmony, quest states, consumed rewards intact → narrative record round-trips.

**Known-noisy, ignore:** `ABP_Melusina_WaterHair` "Accessed None … SourceMeshComponent" — 2–3 per PIE start in the first ~240ms, stops at `MELUSINA_HAIR_BOUND`. Diagnosed, fix owed (§4 item 5).

---

## 7. Copy-paste agent prompts

Each is self-contained. **Run the editor agent and the C++ agent concurrently only if the C++ agent does not build.**

---

### PROMPT A — Blueprint: land `UseSkillWithRhythm` (P0, editor)

```
Working dir: C:\EnvironmentPortfolio\BS_GodFile (UE 5.8). Read AGENTS.md and CLAUDE.md FIRST — rule 2 (never add a mechanism whose only job is to cancel out other behaviour), rule 3 (kill it = delete, don't stub).

CONSTRAINTS
- You are the SOLE OWNER OF THE EDITOR (Monolith MCP, port 9316). Do NOT edit .cpp/.h. Do NOT build. Do NOT close/restart the editor. Do NOT touch Tests/.
- NEVER export_graph BP_BattleController (703 nodes) and NEVER loop get_node_details over it — three editor crashes came from that. Use search_nodes / a single get_execution_flow / batch_execute, and compile once.
- Verify every write with an independent readback, not the setter's response. Prefer editor_query save_packages over blueprint_query save_asset.
- Saved/T3D/rhythm_pipeline.json is from 08-04 and STALE — do not plan from it. Re-derive node ids live.

TASK
In /Game/TurnBasedJRPGTemplate/Blueprints/Battle/BP_BattleController EventGraph, replace the old rhythm cluster with the single new C++ entry point.

The C++ function UMelodiaRhythmCombatSubsystem::UseSkillWithRhythm(UObject* StockSkill) IS compiled and in the binary (verified: generated header 08-07 15:10, DLL 17:38). It internally does StartSession(ResolveRhythmSkillId(StockSkill)); returns 0 → dispatches the stock UseSkill immediately on the same frame; non-zero → defers the stock UseSkill until FinishSession latches the damage multiplier.

Current cluster (re-verify ids before editing):
  CallFunction_115 (UseMP) → CallFunction_196 (StartSession) → IfThenElse_19 (Branch, sessionId>0) → BOTH outputs → CallFunction_124 (UseSkill) → CallFunction_110 (HideSkillActionButtons)
  CallFunction_198 = ResolveRhythmSkillId, CallFunction_197 = int compare, CallFunction_188 = Get subsystem.

Required end state:
  CallFunction_115 (UseMP).then → [new] UseSkillWithRhythm.execute → CallFunction_110 (HideSkillActionButtons).execute
  UseSkillWithRhythm.self  ← the existing Get MelodiaRhythmCombatSubsystem node
  UseSkillWithRhythm.StockSkill ← the same "Get currentSkill" that fed UseSkill's self pin

Then DELETE (rule 3 — delete, do not orphan): CallFunction_196, IfThenElse_19, CallFunction_198, CallFunction_197, CallFunction_124.

WHY THIS MATTERS: today both Branch outputs go to UseSkill, so the attack montage runs in parallel with the rhythm session. The damage anim-notify fires ~0.51s in; the session latches its multiplier ~3.05s in. The notify always wins, so every rhythm-scaled hit currently lands at base damage. This is deterministic, not a race.

Compile once, save via editor_query save_packages, and report exact node ids changed/deleted with readback evidence. Say plainly anything in this brief that was wrong against the live graph.
```

---

### PROMPT B — Blueprint/data: unblock the quest chain (P0, editor)

```
Working dir: C:\EnvironmentPortfolio\BS_GodFile (UE 5.8). Read AGENTS.md and CLAUDE.md FIRST.

CONSTRAINTS
- SOLE OWNER OF THE EDITOR. Do NOT edit .cpp/.h, do NOT build, do NOT close the editor, do NOT touch Tests/.
- Verify writes with independent readbacks. Prefer editor_query save_packages.
- find_references does NOT reliably resolve TSoftObjectPtr — do not conclude an asset is orphaned from an empty referenced_by.

TASK
UMelodiaPersonaSubsystem::HandleJRPGBattleEnded completes quest melodia_q_echo_01 only when ActiveBridgeEncounterId == "Encounter_CrystalShard". That actor is REAL — /Game/ZenForestTest contains JRPG_CrystalShard_Battle (BP_InteractionBattle_C) tagged exactly 'Encounter_CrystalShard'. But the id is NOT in DA_MelodiaIntegrationConfig.EncounterIds, so the bridge rejects it. Quests 2 and 3 chain behind quest 1, so all three are unreachable.

1. Add "Encounter_CrystalShard" to DA_MelodiaIntegrationConfig.EncounterIds (/Game/MelodiaIntegration/Config/). Read the asset back with project_query export_asset_text to confirm it persisted — a setter success response is not proof.
2. Verify the bridge path: UMelodiaExternalJRPGBridgeSubsystem::StartTaggedJRPGBattle requires exactly ONE actor with the tag in the loaded level, plus FindFunction("StartBattle"), an offLevelBattleData struct property, and an OnBattleOver multicast. Confirm ZenForestTest has exactly one 'Encounter_CrystalShard' actor and that BattleController_ZenForest does not create a second battle authority.
3. Report whether melodia_q_echo_01's authored CompletionFlagId (melodia_q_echo_01_complete) would be a better completion driver than the hardcoded encounter id — do NOT change C++, just report with evidence.

Report exact changes, readback evidence, and anything in this brief that was wrong.
```

---

### PROMPT C — C++: quest retry, test repair, hair init order (P0/P1, editor closed OR no-build)

```
Working dir: C:\EnvironmentPortfolio\BS_GodFile (UE 5.8). Read AGENTS.md and CLAUDE.md FIRST — rule 2 (never add a mechanism whose only job is to cancel out other behaviour), rule 3 (kill it = delete, don't stub).

CONSTRAINTS
- You own C++ under Source/BS_GodFile/MelodiaIntegration/ INCLUDING Tests/ for task 2.
- Do NOT call any Monolith MCP tool, do NOT edit .uasset/.umap, do NOT open/close the editor.
- If an editor agent is running concurrently: do NOT build; report that a -NoUBA build is owed. Otherwise build with -NoUBA and the editor closed.

TASK 1 (P0) — A rejected quest permanently burns its retry
UMelodiaNarrativeSubsystem::CompleteQuest calls ConsumeOnce BEFORE broadcasting OnQuestRequested. UMelodiaPersonaSubsystem::HandleNarrativeQuest no-ops when the quest is Locked — but the intent id is already spent. ConsumedIntentIds is SaveGame-flagged, so the burn persists across reloads and no amount of re-talking to the NPC recovers it.
Fix the ordering so the intent is consumed only when a listener actually applied the transition. Check AcceptQuest for the same pattern. A dynamic multicast delegate has no return value, so "did a listener apply it?" needs a real answer — options include consuming inside Persona's success path, or having Narrative ask Persona directly instead of broadcasting blind. Do NOT add a bool that merely re-permits the intent; that is the forbidden cancel-out. Genuine idempotence must survive: a quest must never double-complete.

TASK 2 (P1) — Repair a knowingly-broken test
Tests/MelodiaIntegrationTests.cpp:374 asserts HandleQuillNotification("melodia:stat:Harmony:5"). HandleStatVerb now requires the 5-part authored form melodia:stat:<IntentId>:<StatId>:<Delta> and the 4-part form was deleted. The test compiles and fails at run.
Update it. Note the path now goes through GrantDialogueSocialStat → ConsumeOnce, so a second identical call on the same subsystem instance is a no-op by design — account for that. Also add a test that feeds the REAL authored string from Content/MelodiaIntegration/Narrative/MelodiaQuillPetalPriestess.qsc:51. The absence of exactly that test is why the arity bug survived: a handoff doc claimed the intent was "wired end-to-end (tested)" while the tests bypassed the notification boundary entirely.

TASK 3 (P1) — Hair anim init order
UMelodiaHairComponent's constructor calls SetAnimationMode(AnimationBlueprint) + SetAnimInstanceClass(ABP_Melusina_WaterHair), so the ABP ticks from frame one. But SourceMeshComponent is assigned only in BindToOwnerMesh(), which BeginPlay defers one tick (deliberately, to let the battle adapter finish its mesh swap). Those frames tick the ABP with SourceMeshComponent == None → "Accessed None … SourceMeshComponent" at Set HeadTransform, 2-3 times per PIE start.
Fix: move SetAnimationMode/SetAnimInstanceClass out of the constructor into BindToOwnerMesh(), immediately before the existing InitAnim(true). Keep the ConstructorHelpers FClassFinder in the constructor to cache the class. Do NOT add an IsValid guard in the anim graph — it would silently freeze HeadTransform at identity, which is the forbidden cancel-out. Preserve the intentional one-tick deferral.

Report exact files/functions changed, reasoning on Task 1 including rejected alternatives, anything in this brief that was wrong against real code, and whether a build was run or is owed.
```

---

### PROMPT D — UI integration sweep + read-model binding (P1, editor)

```
Working dir: C:\EnvironmentPortfolio\BS_GodFile (UE 5.8). Read AGENTS.md and CLAUDE.md FIRST.

CONSTRAINTS
- SOLE OWNER OF THE EDITOR. No .cpp/.h edits, no build, no editor restart, no Tests/.
- Verify writes with independent readbacks; set_widget_property echoes an empty value on struct writes that succeeded. Prefer editor_query save_packages.
- Never export_graph BP_BattleController; never loop get_node_details over it.

CONTEXT
A byte-scan of all of Content/ found ZERO Blueprint references to UMelodiaPersonaSubsystem or any of its API (GetQuestState, GetAvailableQuests, GetSocialStat, GetEquipmentDefinitions, RequestEquip, IsGatedContentAvailable, GetVisibleMinimapMarkers). The only C++ caller is a diagnostics library. So no quest state, Harmony value, objective, or equipment is shown to the player anywhere.
RefreshMinimapWidgets hardcodes four widget names in C++ against BP_ExploreUI (JournalResonance, JournalObjective, Marker_*) instead of driving from Content->MinimapMarkers.

TASK
1. Re-verify the above (it may have changed). Report the current UI gap list ranked by what blocks a playable 20-minute slice.
2. Bind the read-model that already exists: BP_ExploreUI's JournalResonance and JournalObjective should show the live Harmony value and current objective. Use the existing persona API — do NOT invent a parallel data path; this project has a strict single-authority rule.
3. Verify these recent additions are intact and correct:
   - WBP_MelodiaRhythmHighway: LaneRow (bottom-centre, 880x140) + Lane_D/F/J/K borders with tinted BrushColor and 42pt centred labels
   - BP_BattleUI: OnKeyDown graph with a Select gating Handled/Unhandled; bIsFocusable=true on the CDO; SetKeyboardFocus in ShowBattleUI; highway create→AddToViewport(z90)→BindRhythmHUD→show; teardown ordered InvalidateSession → RemoveFromParent
   - BP_ActionButton: ActionOverlay fills its button (it was anchored at left=243.5 with alignment 1.0, rendering labels outside their own buttons)
4. BP_MelodiaBattleUI::ShowRhythmGrade is an empty stub and OnPresentationRhythmResult has no listener. Report the smallest correct wiring; implement only if PROMPT A has already landed (the grade source depends on it).

Do NOT redesign UI beyond items 2 and 3. Report a ranked gap table with asset paths and evidence quality, and flag every stale claim you find.
```

---

### PROMPT E — Equipment visuals + Sir Melodious as party member (research, read-only)

```
Working dir: C:\EnvironmentPortfolio\BS_GodFile (UE 5.8). Read AGENTS.md and CLAUDE.md FIRST.

CONSTRAINTS
- STRICTLY READ-ONLY. Do NOT edit any file. Do NOT call any Monolith MCP tool (another agent owns the editor). Filesystem tools only.
- Docs here are frequently stale and have caused real bugs to survive. Cross-check every doc claim against real source/assets and mark evidence quality (real source / binary string scan / doc claim).
- .uasset files are binary but yield useful strings; say when a finding came from a binary scan.

QUESTION 1 — Equipment visuals. No mechanical changes are wanted; the owner wants to know whether the equipment system can carry planned Melodia visuals and icons.
FMelodiaEquipmentDefinition (MelodiaPersonaTypes.h:54) has EquipmentId, DisplayName, StockItemAssetId, Slot, and four stat bonuses — apparently NO icon/mesh/material/description field. Confirm, and state exactly what would need adding.
Then: how does the stock JRPG template represent item icons (find the item base under Content/TurnBasedJRPGTemplate/Blueprints/Items/)? Do BP_Rod / BP_LeatherArmor / BP_LeatherBoots have icons, and are they stock art or Melodia art? Does any Melodia-authored equipment icon art exist (search Content/Melodia/UI/, Textures/, Figma exports, Docs/)? Which widget actually displays equipment, and is there a Melodia-skinned version? End with the smallest correct path to Melodia-authored equipment visuals. Do not implement.

QUESTION 2 — Is Sir Melodious a playable party member with a ctrl-switch and unique abilities?
Known: BP_SirMelodiousPlayerUnit.uasset EXISTS, and RecruitSirMelodiousThroughStockParty is called from MelodiaJRPGPartyBootstrapSubsystem.cpp:173-207 (0 Blueprint callers). AMelodiaSirMelodiousIntroActor lives in the QUARANTINED MelodiaCore plugin as a presentation actor.
Determine: is there a real party/roster system beyond one unit? Is there ANY character-switch input binding (check Config/DefaultInput.ini, IMC_*, IA_*, and EMelodiaInputContext — note InputMappingContext.mappings is DEPRECATED in UE 5.8, the live field is DefaultKeyMappings.mappings)? Does Sir have any authored abilities (DA_MelodiaPersonaContent authors 4, all Melusina's kit)? Do the design docs INTEND him playable, or is he scoped as an NPC whose arc is departure→absence→reunion (see Docs/Research/MELODIA_BARD_GRIEF_HOOK_2026-07-31.md and _DECISION_LOG.md Decision 036)?
DISTINGUISH CLEARLY between "absent because unimplemented" and "absent by design." If he is intended playable, give the smallest correct path: unit class, ability set, roster registration, switch input, UI. Do not implement.

Deliver two clearly separated sections with file:line / asset-path evidence. Flag every stale doc claim and everything you could not verify.
```

---

## 7b. UI / widget state (2026-08-07 late — final pass)

### Landed
- **Lane buttons** `Lane_D/F/J/K` on `WBP_MelodiaRhythmHighway` use `T_Melodia_Universal_RhythmLaneInk` as their border brush, per-lane tints preserved (blue/teal/rose/gold @ 0.38a). All 9 lane widgets are `bIsVariable=true` so they are addressable for animation/tinting.
- **`ShowRhythmGrade` wired.** Signature is now exactly `GradeText:String, HitCount:Integer, MissCount:Integer` → `Conv_StringToText` → `SetText(RhythmGradeText)` (new 64pt centred block). Driven from C++ by `UMelodiaUIBridgeSubsystem::ShowRhythmGradeOnBattleUI`, which validates `ParmsSize`/`NumParms` and refuses on mismatch rather than invoking a bad frame.
- **Dead widget path fixed.** `MelodiaUIBridgeSubsystem.cpp` defaulted to `/Game/MelodiaIntegration/Blueprints/BP_MelodiaBattleUI` — the asset is at `/UI/`. That path never existed, so `MelodiaBattleWidget` was always null and the grade forwarder could never fire. Built and verified.
- **`BP_ActionButton.ActionOverlay`** fills its button (was anchored `left=243.5`, spilling labels onto neighbours).

### Two texture sets — know which is which
| Set | Location | Used by |
|---|---|---|
| `T_Melodia_Redesign_*` | `/Game/Melodia/UI/Rhythm/Textures/` | The highway's authored art — `SheetMusicBG`, `AuroraOverlay`, `SparkleField` |
| `T_Melodia_Universal_*` | `/Game/Melodia/UI/Textures/Universal/` | Shared kit — lane ink, hitline, parchment frame, seals, filigree |
| `T_Melodia_SoftMG_*` + others | `/Game/EnvSandbox/Textures/Melodia/GameUI/` | What `UMelodiaRhythmHUDWidget::LoadPresentationTextures` loads for `NativePaint` |

**Read a brush before overwriting it.** `SheetMusicBG` was clobbered this session by assuming it was unset; it held `T_Melodia_Redesign_SheetMusicBackground`. `list_widget_properties` does **not** expand `FSlateBrush` — verify with `project_query export_asset_text` + `object_filter`.

### Open — all need an art/design decision, do not guess
1. **`NoteHeadBeamTexture` loads the hit-line texture.** `MelodiaRhythmHUDWidget.cpp:64` and `:66` assign the identical asset, so note beams render as hit-lines. `SoftMG_SealULT` and `SoftMG_ScrollEdge` are both plausible intended values.
2. **`T_Melodia_LanePress` is authored and unreferenced** — the press-feedback art for the F/J/K lanes. Wiring it means swapping the lane border brush on keypress; the lanes live on `WBP_MelodiaRhythmHighway`, reached from `BP_BattleUI` via its `RhythmHighwayWidget` variable.
3. **`WBP_MainMenu`: `Background` (has `SoftMG_Parchment`) and `CosmicVoid` (no texture, near-black tint) are both Collapsed** beneath a visible `NebulaParchment` (z −20). Likely superseded layers, but `CosmicVoid` reads like an intended deepest backdrop. Un-collapsing changes the composition.
4. **`BP_MelodiaBattleUI` has a dual widget hierarchy** with its parent `BP_BattleUI` — UE explicitly does not support this ("Only one of them should have a widget tree"). `RhythmGradeText` may not render regardless of correct wiring. The highway's own `SetJudgment` already shows grades without this problem, so this second display may be redundant. **Decide whether to keep it before investing further.**

---

### PROMPT F — UI polish sweep (editor)

```
Working dir: C:\EnvironmentPortfolio\BS_GodFile (UE 5.8). Read AGENTS.md and CLAUDE.md FIRST — rule 2 (no mechanism whose only job is to cancel out other behaviour), rule 3 (kill it = delete, don't stub), rule 4 (the owner knows their own rig — act on what they tell you, don't re-verify it).

CONSTRAINTS
- SOLE OWNER OF THE EDITOR (Monolith, port 9316). No .cpp/.h edits, no build, no editor restart, no Tests/.
- ALWAYS read a brush before overwriting it. list_widget_properties does NOT expand FSlateBrush — use project_query export_asset_text with object_filter. A texture was clobbered this session by skipping this.
- set_widget_property echoes an empty `value` on struct writes that SUCCEEDED — always verify via export_asset_text, never the setter response. Font.Size and bIsVariable need raw_mode:true (not on the curated allowlist).
- Prefer editor_query save_packages over blueprint_query save_asset.
- Do NOT guess at art intent. If a texture choice is ambiguous, report options and stop.

THREE TEXTURE SETS — do not cross them without reason:
  T_Melodia_Redesign_*  /Game/Melodia/UI/Rhythm/Textures/        highway authored art
  T_Melodia_Universal_* /Game/Melodia/UI/Textures/Universal/     shared kit
  T_Melodia_SoftMG_* etc /Game/EnvSandbox/Textures/Melodia/GameUI/  loaded by C++ NativePaint

TASKS (in priority order)
1. F/J/K lane press feedback. T_Melodia_LanePress (in the GameUI folder) is authored and referenced by nothing. Wire it as the pressed-state brush for Lane_D/F/J/K on /Game/Melodia/UI/Rhythm/WBP_MelodiaRhythmHighway. Those lanes are already bIsVariable. Input arrives at BP_BattleUI::OnKeyDown (D/F/J/K -> RegisterLaneHit(0..3)); the highway is reached from BP_BattleUI's RhythmHighwayWidget variable. Restore the idle brush after the press — but do NOT add a Tick or a timer whose only job is to undo the swap if a cleaner seam exists.
2. Sweep every widget under /Game/Melodia/UI/ and /Game/MelodiaIntegration/UI/ for: default 100x30 slot sizes (the known-bad default that broke Quill dialogue), auto_size:true combined with explicit offsets, Collapsed widgets that hold real textures, and Images with no ResourceObject. Report a ranked table; fix only the unambiguous ones.
3. /Game/Melodia/UI/WBP_MainMenu: `Background` (holds SoftMG_Parchment) and `CosmicVoid` (no texture) are both Collapsed under a visible NebulaParchment. Determine whether they are superseded or unfinished and report — do not flip visibility without deciding why.

Report each change with export_asset_text evidence, compile status, and save confirmation. State plainly anything in this brief that was wrong against the live project.
```

---

## 8. Rollback

Filesystem backup: `CompatibilityLabs/ProductionPreIntegrationBackup_2026-07-26`.
This session's asset edits are isolated to: `BP_BattleController`, `BP_BattleUI`, `BP_ActionButton`, `WBP_MelodiaRhythmHighway`, `BP_SavePointBase`, `BP_SaveUI`, `BP_MelodiaJRPGGameInstance`, `BP_MelodiaSirMelodiousMorningIntro`, `DA_MelodiaIntegrationConfig`, `DA_MelodiaPersonaContent`, `ZenForestTest.umap`, and the new `BP_KaleidoNaveArrivalTrigger`.
