# Melodia Traversal System & Save/Load Review - 2026-08-03

**Reviewer:** UE 5.8 Gameplay Systems Analyst
**Build target:** 0 errors, native closed-editor build passes
**Scope:** TravelTo <-> InputContext interaction, travel path coverage (allowlist, spawn placement, context clear), save/load state preservation (narrative record, wallet, party)
**Monolith service:** Not available for live queries (port 9316 had no active process); analysis is 100% static C++ source review

---

## 1. TravelTo <-> Input Context System Interaction

### The chain

```
Quill "melodia:travel:<LevelId>"
  => MelodiaNarrativeSubsystem::HandleQuillNotification         (NarrativeSubsystem.cpp:629-631)
    => RequestTravel(LevelId)                                   (allowlist validation)
      => OnTravelRequested.Broadcast(LevelId)                   (NarrativeSubsystem.cpp:196)
UMelodiaTravelSubsystem::HandleTravelRequested(LevelId)         (registered at init, line 23)
  => OnTravelStarted.Broadcast(LevelId, SpawnTag)
  => UGameplayStatics::OpenLevel(World, LevelId)                (TravelSubsystem.cpp:119)
    => [level transition]
      => FCoreUObjectDelegates::PostLoadMapWithWorld
UMelodiaTravelSubsystem::HandlePostLoadMap(LoadedWorld)         (registered at init, line 26)
  => Input->ClearAllContexts("travel arrival: <LevelId>")       (TravelSubsystem.cpp:141)
  => PlacePawnAtSpawn(LoadedWorld, SpawnTag)
  => OnTravelArrived.Broadcast(LevelId, bPlaced)
```

### Key design decisions

| Element | Location | What it does |
|---------|----------|--------------|
| **Spawn tag pre-storage** | TravelTo() line 84-87 | SetSpawnContext is called **before** RequestTravel because the broadcast fires synchronously -- the tag must be in the narrative record before HandleTravelRequested reads it back via GetPendingSpawnTag. |
| **Input context clear on arrival** | HandlePostLoadMap line 137-142 | Travel arrival **force-cleans** the entire input stack, logging every orphaned context with its owner name. This is the safety net that prevents cursor/input-mode stranding. |
| **Spawn tag persistence** | FMelodiaNarrativeRecord::SpawnContext (NarrativeTypes.h:109) | Tags survive save/load because they live on the narrative record, not on the transient TravelSubsystem member. |

### Interaction strength

The coupling is **appropriately loose**: TravelSubsystem holds a pointer to InputContextSubsystem obtained at call-time (not stored during Initialize). ClearAllContexts is called with the arriving level ID as the reason string, so the leak-detection log tells exactly which transition stranded what. No tight circular dependency exists.

**Verdict: Pattern is correct. The input system provides exactly one thing travel needs (a blow-away-the-stack operation), and travel consumes it at exactly the right moment.**

---

## 2. Travel Path Coverage

### 2a. Allowlist validation

| Entry point | Allowlist check? | File | Line |
|-------------|-----------------|------|------|
| TravelTo() direct C++ call | YES, via Narrative->RequestTravel(LevelId) -> IsAllowed(Config->TravelLevelIds, LevelId) | TravelSubsystem.cpp:91, NarrativeSubsystem.cpp:191-193 | 91, 191-193 |
| melodia:travel: Quill intent | YES, same path via HandleQuillNotification -> RequestTravel | NarrativeSubsystem.cpp:629-631 | 629-631 |
| Save-load fallback | **NO** -- falls back to OpenLevel if TravelTo returns false | SaveSlotLibrary.cpp:168 | 168 |
| MelodiaCore OpenLevel calls (7) | **Bypassed entirely** -- plugin cannot reach TravelSubsystem (module dependency) | Documented in SaveSlotLibrary.cpp:139-140 | 139-140 |
| AMelodiaTravelInteractionPortal::TryInteract | YES, via Travel->TravelTo() | TravelInteractionPortal.cpp:43 | 43 |

**Finding:** The primary paths are protected. Two known bypasses exist: (1) the save-load fallback in LoadCanonicalJRPGSlot when TravelTo rejects the opening route ID, and (2) the 7 OpenLevel calls in MelodiaCore that cannot reach this subsystem due to module dependency direction.

### 2b. Spawn tag placement

| Aspect | Status | Details |
|--------|--------|---------|
| Tag stored before travel | YES | Narrative->SetSpawnContext(LevelId, SpawnTag) in TravelTo() |
| Tag retrieved on arrival | YES | GetPendingSpawnTag(ArrivedLevelId) in HandlePostLoadMap |
| PlacePawnAtSpawn logic | YES | Checks PlayerStartTag first, then Tags array; teleports pawn + sets control rotation |
| No-tag fallback | YES | SpawnTag.IsNone() returns false, engine picks default -- documented as "no worse than before" |
| No-matching-start fallback | YES | Logs warning with tag name and count of PlayerStarts present |
| No-pawn case | YES | Logs warning, returns false |

**Finding:** Spawn placement logic is correct and handles all edge cases. The dual-match (PlayerStartTag or Tags array) is a pragmatic concession to level-designer workflow. **No gaps.**

### 2c. Input context clear on arrival

| Path | Context clear? | Notes |
|------|---------------|-------|
| TravelTo -> OpenLevel | YES | HandlePostLoadMap calls ClearAllContexts |
| Save load (SavedMap found) | YES | TravelTo is used (eventually via stock LoadThisGame event) |
| Save load (no SavedMap, TravelTo succeeds) | YES | Normal path |
| Save load (no SavedMap, TravelTo fails) | **Bypassed** | Falls through to direct OpenLevel at SaveSlotLibrary.cpp:168 -- no context clear |
| MelodiaCore OpenLevel | **Bypassed** | Plugin cannot reach the subsystem |

**Finding:** The context-clear safety net is reliable for all paths going through TravelTo. The two bypass paths leave a stale-context risk, though in practice the widget layer has zero PushContext/PopContext bindings (see below), so there is nothing to leak yet.

### 2d. Gap: Input context system has zero content bindings

No Blueprint widget or graph in the content index calls PushContext or PopContext. The ClearAllContexts safety net on travel arrival fires into an empty stack today. Every widget that should push Dialogue, Battle, or Menu is still using ad-hoc Set Input Mode / Show Mouse Cursor nodes. This is tracked in the wiring checklist step 3 and remains the root cause of cursor-stuck bugs.

---

## 3. Save/Load State Preservation

### 3a. Narrative record (FMelodiaNarrativeRecord)

| Field | Saved? | Loaded? | Migrated? | Notes |
|-------|--------|---------|-----------|-------|
| Version | YES | YES | N/A (schema version) | CurrentVersion = 2 |
| Flags (TMap<FName, bool>) | YES | YES | v1->v2: no migration needed | Defaults empty |
| QuillVariables (TMap<FName, FText>) | YES | YES | YES | Captured in CapturePersistentQuillVariables; compatibility lane for pre-full-payload saves |
| QuillPersistentData (TArray<uint8>) | YES | YES | YES | Full Quill serializer payload |
| ScriptCheckpoint (FName) | YES | YES | Auto: zeroed = none | |
| ConsumedIntentIds (TArray<FName>) | YES | YES | YES | Prevents double-apply after reload |
| ActiveQuestIds (TArray<FName>) | YES | YES | v1->v2: defaults empty | Manually managed via SetQuestActive |
| ConsumedRewardIds (TArray<FName>) | YES | YES | v1->v2: defaults empty | |
| SocialStats (TMap<FName, int32>) | YES | YES | v1->v2: defaults empty | Version 2 addition |
| BondRanks (TMap<FName, int32>) | YES | YES | v1->v2: defaults empty | Version 2 addition, reserved |
| PhaseIndex (int32) | YES | YES | v1->v2: defaults 0 | Version 2 addition |
| SpawnContext (TMap<FName, FName>) | YES | YES | v1->v2: defaults empty | Version 2 addition |

**Save chain:** CreateCanonicalJRPGSlot/SyncNarrativeRecordToSave -> CapturePersistentQuillVariables() -> copies NarrativeRecord to JRPGSaveObject->melodiaNarrativeRecord via FStructProperty reflection.

**Load chain:** LoadCanonicalJRPGSlot/RestoreNarrativeRecordFromSave -> reads melodiaNarrativeRecord -> MigrateRecord() (version stepping) -> RestorePersistentQuillVariables() -> writes to NarrativeRecord.

**Version migration:** v1->v2 adds SocialStats (empty map), BondRanks (empty map), PhaseIndex (0), SpawnContext (empty map). All four default correctly for a pre-v2 save. No data is lost.

**Finding: Narrative record save/load is complete and correct.** Every tracked field is saved, loaded, and migrated where applicable. The CapturePersistentQuillVariables/RestorePersistentQuillVariables pair handles both the raw Quill serializer payload and the namespaced text variables, with a compatibility lane for pre-payload saves.

### 3b. Wallet state

The wallet (UMelodiaTokenWalletSubsystem in MelodiaCore plugin) has its own **independent save/restore** path via CaptureToSave(Save)/RestoreFromSave(Save) that reads/writes its fields directly on the same BP_JRPGSaveGame object. Per the RHYTHM_WALLET_REVIEW_2026-08-03.md:

- All 7 shard-element balances + mana + golden tokens are saved and restored
- ConsumedGrantIds set survives restart -- grant-idempotency is proven
- One-way migration: Heart->Forte, Swirl->Arcane (pre-v4 saves)
- OnWalletChanged fires after restore (UI must handle load-time broadcasts gracefully)

**Finding: Wallet save/restore is complete and correct.** It operates beside the narrative record, not through it. No double-save or version conflict exists because both target distinct fields on the same save object.

### 3c. Party state

Party composition, levels, XP, equipment, and skills are **not owned by any Melodia subsystem**. They remain solely in the JRPG template's own save serialization (BP_JRPGSaveGame fields). The UMelodiaJRPGPartyBootstrapSubsystem only provides a one-shot RecruitSirMelodiousThroughStockParty() bootstrap that calls into the stock party system.

**Finding: Party state is preserved through the canonical JRPG save, not through Melodia systems.** This is by design. The narrative record does not duplicate party data. No gap -- the absence is architectural, not accidental.

### 3d. Save boundary safety

UMelodiaSaveRecoverySubsystem invalidates rhythm transient state at every save/load boundary:

- BeginSaveBoundary / EndSaveBoundary -> invalidates beat trackers + rhythm session
- BeginLoadBoundary / EndLoadBoundary -> same
- NotifyDeathRecovery / NotifyRetryRecovery -> same

The rhythm session invalidation is gated on a registered session ID (avoids guessing on unrelated combat transactions). Beat trackers are stopped via world-wide TActorIterator.

**Finding: Transient rhythm state is correctly cleaned up at save/load boundaries.** The safety guard (refusing to invalidate an unregistered session) prevents accidental corruption of stock JRPG combat state.

---

## 4. Identified Gaps

| # | Gap | Location | Severity | Mitigation |
|---|-----|----------|----------|------------|
| G1 | **Save load fallback bypasses travel authority** | SaveSlotLibrary.cpp:168 | Medium | Fallback call to OpenLevel skips allowlist check, spawn placement, and input context clear. Mitigated only because this fires once (new-save -> opening map). TravelTo failure logs a clear warning telling the developer to add the ID to the allowlist. |
| G2 | **MelodiaCore cannot reach TravelSubsystem** | SaveSlotLibrary.cpp:139 (doc) | Medium | 7 OpenLevel calls in the plugin bypass all protections. Blocked by module dependency direction. Requires moving IMelodiaTravelProvider interface or the subsystem into a shared module. |
| G3 | **Input context has zero content bindings** | Every widget | High | PushContext/PopContext are never called from Blueprints. ClearAllContexts fires on an empty stack. Cursor/input-mode management is still ad-hoc. Root cause of stuck-cursor bugs. |
| G4 | **TravelTo/OpenLevel coexistence** | BP_MelodiaJRPGGameInstance + 10+ other assets | Medium | Migration is incomplete. Documented in JRPG_TRAVERSAL_REVIEW. |
| G5 | **No narrative/JRPG state cross-check** | Save/Load chain | Low | If narrative record loads but JRPG party data is corrupt, no reconciliation mechanism exists. The systems trust each other's serialization implicitly. |

---

## 5. Summary

| Area | Verdict |
|------|---------|
| TravelTo <-> InputContext | Pattern is correct. Travel arrival force-cleans the input stack. No circular dependency. |
| Allowlist validation | Primary paths protected. Two bypasses exist (save-load fallback, MelodiaCore plugin). |
| Spawn tag placement | Complete. Handles all edge cases (no tag, no matching PlayerStart, no pawn). |
| Input context clear | Present on all TravelTo paths. Bypassed on the two OpenLevel fallback paths. |
| Narrative record save/load | Complete. All 12 fields saved, loaded, migrated. Versioned schema with migration path. |
| Wallet save/load | Complete. Independent save/restore on same save object. Grant-idempotency survives restart. |
| Party save/load | Not Melodia's responsibility. JRPG template owns this entirely. Architectural, not a gap. |
| Save boundary safety | Complete. Rhythm transient state invalidated at every boundary. |

**The C++ foundation for traversal and save/load is structurally sound.** All subsystems build cleanly, the interaction chain between travel and input is correct, and the narrative record captures every field it should. The wallet operates independently but correctly. The remaining gaps are content-layer wiring (input context bindings, TravelTo migration completion) and two documented bypass paths (save-load fallback, MelodiaCore OpenLevel calls) that are known and scoped.

**One-line per material finding:**
1. TravelTo correctly coordinates spawn-tag persistence, allowlist validation, and input-context-clear on arrival.
2. The save-load fallback at MelodiaSaveSlotLibrary.cpp:168 is the last direct OpenLevel in the game module and bypasses all three travel protections when TravelTo rejects the opening route.
3. Every field in FMelodiaNarrativeRecord (v2) is saved, loaded, and migrated -- narrative state, social stats, bond ranks, spawn context, and Quill data all survive a restart.
4. Wallet state is preserved through MelodiaCore's own CaptureToSave/RestoreFromSave pair, operating beside (not through) the narrative record on the same save object.
5. The input context system has zero content bindings across all Blueprints -- the C++ safety net is live but fires into an empty stack.
