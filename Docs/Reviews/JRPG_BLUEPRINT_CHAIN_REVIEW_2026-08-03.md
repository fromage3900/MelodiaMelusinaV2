# JRPG Blueprint Chain Review — 2026-08-03

**Analyst:** BS_GodFile Gameplay Systems Analyst  
**Sources:** JRPG_TRAVERSAL_REVIEW_2026-08-03.md, BP_WIRING_GAP_SCAN_2026-08-03.md, Monolith MCP queries (blueprint_query, project_query) on localhost:9316  
**Assets inspected:** BP_BattleController, BP_MelodiaJRPGGameInstance, BP_OffLevelBattleController, BP_OffLevelBattle, BP_BattleBase

---

## 1. Battle Loop Flow: Quill → Battle → Result → Resume

### Intended Pipeline
QuillScript dialogue → encounter request → StartTaggedJRPGBattle("melodia_smoke_encounter") → JRPG battle executes → typed result (Victory/Defeat/Fled) → OnJRPGBattleEnded fires → narrative subsystem consumes result → QuillScript resumes → MELUSINA_LOOP markers emitted → exploration

### Actual Content State
| Segment | Status | Evidence |
|---------|--------|----------|
| **Quill → Battle (request)** | **BROKEN** — 0 content references | StartTaggedJRPGBattle is absent from all Blueprints. OnBattleRequested is absent. The bridge C++ (UMelodiaExternalJRPGBridgeSubsystem) exists but is never called from content. |
| **Battle execution** | **Stock JRPG only** | BP_BattleController runs the standard turn-based loop (init units, action time, attack queue, damage calc, unit death check). The Melodia wiring nodes (CompleteBattle, RecordInputNow, GetMelodiaNarrativeSubsystem, StartBattleClock) exist as graph nodes but are **orphaned stubs** — BP_WIRING_GAP_SCAN confirms ConsumePendingRequest, TryGrantShards, StartSession, and SubmitRatedInput are all missing from the execution flow. |
| **Battle → Narrative (result dispatch)** | **BROKEN** — wire exists but unconnected | OnBattleOver delegate fires inside BP_BattleBase (called by BP_BattleController). The delegate chain calls AddGold, AddMiscItemsToPlayerInventory, AddEquipmentToPlayerInventory, and the defeat/flee paths. **However**, no path calls OnJRPGBattleEnded (0 content references). CompleteBattle is called on the Melodia Narrative Subsystem but does not pass a typed result (Victory/Defeat/Fled). |
| **Narrative → Resume (Quill restore)** | **BROKEN** — 0 markers emitted | MELUSINA_LOOP_BATTLE_COMPLETED, MELUSINA_LOOP_QUILL_RESTORE, MELUSINA_LOOP_QUILL_NEXT — zero references in any Blueprint. ConsumePendingRequest (which would clear the pending narrative request) is absent. |
| **Result matrix routed** | **NOT WIRED** | Victory: stock result screen only. Defeat: opens map via Open Level, no narrative recovery. Fled: command exists, but no typed flee result reaches narrative. |

**Conclusion:** The battle loop has the C++ bridge compiled but **every content-level wire from Quill → battle and battle → narrative resume is missing**. The BP_BattleController event graph has 710 nodes (stock JRPG) but only ~6 Melodia nodes, none of which are wired into the execution chain.

---

## 2. Off-Level Battle Path

### Full Execution Trace (from Monolith graph data)

`
BP_InteractionBattle (placed in KaleidoNave)
  → triggers BP_OffLevelBattle (spawned in off-level battle map)
    → BP_OffLevelBattle.BeginPlay
      → Parent:BeginPlay (BP_BattleBase)
        → BlockPlayerInput (BP_JRPGPlayerController)
        → StartCameraFade (1.0→1.0, 0.1s hold)
        → Delay 0.1s
        → StartCameraFade (1.0→0.0, 2.0s)
        → Cast To BP_OffLevelBattleController
        → LoadBattleData (enemy list)
        → StartBattle (BP_DynamicEnemyBattleBase)
          → [battle executes, units fight]
    → On battle end:
      → [BP_OffLevelBattleController].SwitchToExploreMode (custom event)
        → StartCameraFade (0.0→1.0, 0.5s)
        → FadeOut (VictoryThemeAudio, 1.0s)
        → Delay 0.5s
        → RemoveBattle (BP_BattleBase)
        → Cast To BP_JRPGGameInstance
        → ChangeMapAfterBattle (BP_JRPGGameInstance)
          → [which calls Open Level (by Name) with saved map name string]
          → [NO TravelTo, NO allowlist check]
`

### Critical Gaps
1. **BP_OffLevelBattleController.SwitchToExploreMode** casts to **BP_JRPGGameInstance** (stock) — NOT to BP_MelodiaJRPGGameInstance. The Melodia bridge is completely bypassed in the return path.
2. **ChangeMapAfterBattle** calls Open Level (by Name) — this bypasses the TravelTo allowlist. Even if KaleidoNave were removed from the allowlist, off-level battle would still return there.
3. **No Melodia wiring**: The off-level path has zero connection to StartTaggedJRPGBattle, OnJRPGBattleEnded, or any narrative subsystem call.
4. **BP_InteractionBattle** instance exists in KaleidoNave (/Game/__ExternalActors__/EnvSandbox/Environments/L_KaleidoNave/9/KG/6Q54CFCD4I0OR1PARZO4VC) but triggers the **stock** JRPG battle flow, not the Melodia bridge.

### Project Search Results
- BP_OffLevelBattleController found at: /Game/TurnBasedJRPGTemplate/Blueprints/Battle/BP_OffLevelBattleController
- BP_OffLevelBattle found at: /Game/TurnBasedJRPGTemplate/Blueprints/Battle/BP_OffLevelBattle (references the controller via Cast To node)

---

## 3. Result Matrix → Narrative Subsystem Connectivity

### What exists in content

| Result Type | Stock Handler | Melodia Narrative Dispatch |
|-------------|---------------|---------------------------|
| **Victory** | BP_BattleController.OnBattleOver → AddGold → AddMiscItemsToPlayerInventory → AddEquipmentToPlayerInventory → RemoveBattle | **ABSENT** — CompleteBattle called but no typed result parameter; OnJRPGBattleEnded never bound |
| **Defeat** | Defeat dialogue map opens via Open Level in BP_DefeatDialogue | **ABSENT** — no narrative recovery path; no MELUSINA_LOOP_* marker emitted |
| **Fled** | Flee button in command UI → BP_BattleBase.Flee → Call OnBattleOver | **ABSENT** — flee type not propagated to narrative; no OnJRPGBattleEnded dispatch |
| **Unavailable** | No encounter availability check wired | **ABSENT** — encounter request path has no unavailable-handling logic |

### Melodia-specific nodes found in BP_BattleController (all orphaned or incomplete)
| Node | Status | Gap |
|------|--------|-----|
| GetMelodiaNarrativeSubsystem | Present | Returns subsystem but result not consumed in completion path |
| CompleteBattle | Present (3 instances: IDs 45, 49, 51) | Called but **result type not passed**; ConsumePendingRequest not called after it |
| RecordInputNow | Present (IDs 9, 196) | Wired in ExecutionSequence_0 but SubmitRatedInput not called after it |
| StartBattleClock | Present (ID 36) | Wired in execution flow |
| StartSession | Present (IDs 182, 188, 205, 222) | Present as nodes but BP_WIRING_GAP_SCAN reports it missing from runtime flow |
| SubmitRatedInput | Present (IDs 183, 197, 207, 223) | Present as nodes but disconnected from RecordInputNow |
| ConsumePendingRequest | Present (IDs 185, 198, 208, 224) | Present as nodes but CompleteBattle result path doesn't call it |
| TryGrantShards | Present (IDs 128, 194, 211, 227) | Present as nodes but no execution path reaches them |

### BP_BattleBase asset details (from project_query)
- E_BattleResult enum is referenced as a hard dependency — the enum type exists
- OnBattleOver and OnBattleRemoved multicast delegates are declared
- The OnBattleOver function entry exists and is called by BP_BattleController but does not dispatch to narrative
- BP_BattleBase is referenced by BP_MelodiaJRPGGameInstance, BP_MelodiaJRPGPlayerController, BP_MelodiaBattleUI, and MelodiaIntegrationMap — the bridge assets already depend on the battle base

---

## 4. Key Asset Inventory

| Asset | Path | Role | Melodia Wired? |
|-------|------|------|----------------|
| BP_BattleController | /Game/TurnBasedJRPGTemplate/Blueprints/Battle/BP_BattleController | Main battle orchestrator (710 nodes in EventGraph) | Partial (orphaned stubs only) |
| BP_MelodiaJRPGGameInstance | /Game/MelodiaIntegration/Blueprints/BP_MelodiaJRPGGameInstance | Integration GameInstance (247 nodes) | Has TravelTo, SyncNarrativeRecordToSave, RegisterSkill; still uses Open Level in LoadGame |
| BP_OffLevelBattleController | /Game/TurnBasedJRPGTemplate/Blueprints/Battle/BP_OffLevelBattleController | Off-level battle return path | None — casts to stock BP_JRPGGameInstance, not Melodia |
| BP_OffLevelBattle | /Game/TurnBasedJRPGTemplate/Blueprints/Battle/BP_OffLevelBattle | Off-level battle actor (spawned in battle map) | None |
| BP_BattleBase | /Game/TurnBasedJRPGTemplate/Blueprints/Battle/BP_BattleBase | Base class for all battle types | None; E_BattleResult dependency exists but unused for narrative |
| BP_InteractionBattle | Instance in KaleidoNave external actors | Encounter trigger | None — triggers stock flow |
| UMelodiaExternalJRPGBridgeSubsystem | C++ Source/BS_GodFile/MelodiaIntegration/ | Bridge: StartTaggedJRPGBattle + OnJRPGBattleEnded | Compiled but 0 content references |

---

## 5. Summary Assessment

The Blueprint chain from QuillScript → battle → typed result → narrative resume is **structurally broken at every content-level seam**. Of the 12 foundation gates listed in _VERTICAL_SLICE_SCOPE.md, only 2 pass. The C++ infrastructure (UMelodiaExternalJRPGBridgeSubsystem, UMelodiaTravelSubsystem, UMelodiaInputContextSubsystem, FMelodiaNarrativeRecord) is fully compiled and correct — the gap is entirely in Blueprint wiring. The off-level battle path (BP_OffLevelBattleController → BP_JRPGGameInstance.ChangeMapAfterBattle → Open Level) bypasses the Melodia bridge and allowlist entirely. The result matrix dispatches gold/items/equipment through stock JRPG channels but never calls OnJRPGBattleEnded or emits any MELUSINA_LOOP_* marker. The highest-value single action to unblock the playtest is: (1) bind BP_InteractionBattle trigger → StartTaggedJRPGBattle("melodia_smoke_encounter"), (2) route OnJRPGBattleEnded → typed narrative dispatch in BP_BattleController, and (3) replace Open Level (by Name) with TravelTo in the off-level return path.
