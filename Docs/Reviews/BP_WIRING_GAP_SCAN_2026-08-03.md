# BP_WIRING_GAP_SCAN_2026-08-03.md

## Melodia Gameplay Chain — Blueprint Wiring Audit

**Date:** 2026-08-03  
**Scope:** All Blueprints in the Melodia gameplay chain  
**Method:** Monolith MCP blueprint_query export_graph + project_query search  
**Auditor:** BP Wiring Auditor (automated scan)

---

## 1. Connection Matrix

| Connection | Source BP | Target / Subsystem | Status | Evidence |
|---|---|---|---|---|
| **Quill → Battle** | _QuillscriptAsset (Narrative)_ | BP_BattleController | ❌ MISSING | No Quillscript→Battle bridge found; no OnBattleRequested call in any BP |
| **Battle → Narrative** | BP_BattleController | Melodia Narrative Subsystem | ✅ CONNECTED | CompleteBattle (Melodia Narrative Subsystem) found in BP_BattleController EventGraph |
| **Narrative → Save** | BP_MelodiaJRPGGameInstance | Melodia Narrative Subsystem | ✅ CONNECTED | Sync Narrative Record to Save and Restore Narrative Record from Save both present |
| **Skill → Session** | BP_MelodiaJRPGGameInstance | Melodia Rhythm Combat Subsystem | ⚠️ PARTIAL | RegisterSkill present, but StartSession is MISSING |
| **Session → Grade** | BP_BattleController | Melodia JRPGPresentation Rhythm | ⚠️ PARTIAL | RecordInputNow present, but SubmitRatedInput is MISSING |
| **Grade → Resolve** | BP_BattleController | (Melodia Narrative Subsystem) | ❌ MISSING | ConsumePendingRequest and TryGrantShards both absent |
| **Resolve → Wallet** | BP_BattleController | (Melodia Economy / Shard Grant) | ❌ MISSING | TryGrantShards not called anywhere |
| **Battle → UI Context** | BP_BattleUI | Melodia Input Context Subsystem | ⚠️ PARTIAL | PushContext/PopContext present in BP_BattleUI, but NOT in BP_MelodiaBattleUI |
| **BattleUI → Note Highway** | BP_BattleUI | WBP_MelodiaRhythmHighway | ⚠️ PARTIAL | MelodiaNoteHighway variable exists but SetNoteHighwayActive never called |
| **GameInstance → Battle Start** | BP_MelodiaJRPGGameInstance | (JRPGBattle start) | ❌ MISSING | StartTaggedJRPGBattle not found anywhere; OnBattleRequested not found anywhere |

---

## 2. Missing Nodes (Function Calls That SHOULD Exist But DON'T)

### Critical Missing Calls (entirely absent from all Blueprints):

| Expected Function | Target Subsystem | Should Appear In | Impact |
|---|---|---|---|
| **StartTaggedJRPGBattle** | Melodia Rhythm Combat Subsystem | BP_MelodiaJRPGGameInstance or BP_MelodiaJRPGPlayerController | No tagged battle can be initiated — entry point broken |
| **OnBattleRequested** | (event/delegate) | Any MelodiaIntegration BP | Narrative→battle handshake completely absent |
| **OnJRPGBattleEnded** | (event/delegate) | BP_BattleController or BP_MelodiaBattleUI | No callback when a JRPGBattle finishes |
| **StartSession** | Melodia Rhythm Combat Subsystem | BP_MelodiaJRPGGameInstance or BP_BattleController | Skills registered but session never started — combat skills won't execute |
| **SubmitRatedInput** | Melodia JRPGPresentation Rhythm Component | BP_BattleController (after RecordInputNow) | Input is recorded but never rated — no timing evaluation |
| **ConsumePendingRequest** | Melodia Narrative Subsystem | BP_BattleController (in CompleteBattle flow) | Pending narrative requests pile up, never consumed |
| **TryGrantShards** | Melodia Narrative Subsystem | BP_BattleController (after CompleteBattle) | Players never receive shard rewards from battles |
| **SetNoteHighwayActive** | WBP_MelodiaRhythmHighway | BP_BattleUI or BP_MelodiaBattleUI | Note highway widget never activated/deactivated |
| **BindEvent** (for Melodia events) | (delegate system) | BP_BattleController or BP_MelodiaBattleUI | No event bindings for Melodia-specific gameplay signals |
| **MELUSINA_LOOP** | (music/audio) | BP_MelodiaJRPGGameInstance or Level BP | Melusina's loop audio never triggered |

### Missing in BP_MelodiaBattleUI (the Melodia-specific battle UI):

BP_MelodiaBattleUI has **none** of the following Melodia connections:
- PushContext / PopContext (Melodia Input Context Subsystem) — present in BP_BattleUI but NOT here
- MelodiaNoteHighway variable — absent
- RecordInputNow — absent
- CompleteBattle — absent

This means BP_MelodiaBattleUI is effectively a non-functional copy of BP_BattleUI without any Melodia wiring.

---

## 3. Live Coding Impact — Did 28 Live Coding Errors Revert Wiring?

### Investigation Results

The base BP_BattleController at /Game/TurnBasedJRPGTemplate/Blueprints/Battle/BP_BattleController **still contains** Melodia connections:
- CompleteBattle (Target is Melodia Narrative Subsystem) ✅ STILL PRESENT
- RecordInputNow (Target is Melodia JRPGPresentation Rhythm Component) ✅ STILL PRESENT
- Get Melodia Narrative Subsystem ✅ STILL PRESENT
- Start Battle Clock (Target is Melodia Audio Component) ✅ STILL PRESENT

The base BP_BattleUI at /Game/TurnBasedJRPGTemplate/Blueprints/UI/BP_BattleUI **still contains**:
- PushContext (Target is Melodia Input Context Subsystem) ✅ STILL PRESENT
- PopContext (Target is Melodia Input Context Subsystem) ✅ STILL PRESENT
- MelodiaNoteHighway variable ✅ STILL PRESENT
- MelodiaBattleInputContextHandle variable ✅ STILL PRESENT

However, the **ThirdParty copy** at /Game/_ThirdParty/TurnBasedJRPGTemplate/Blueprints/Battle/BP_BattleController has **zero** Melodia connections — it is the clean unmodified template.

**Conclusion:** The Live Coding errors did NOT revert the Qwen-added wiring in the main copies. However, the wiring that exists is incomplete (see Section 2). The 28 Live Coding errors likely correlate to the **missing connections** rather than reverted ones — the compiler is complaining about dangling references to Melodia subsystems that aren't fully wired into the execution flow.

---

## 4. Priority Fix List (Top 5 Missing Connections by Gameplay Impact)

| Rank | Missing Connection | Why It Breaks The Game |
|---|---|---|
| **#1** | StartTaggedJRPGBattle (from BP_MelodiaJRPGGameInstance to Melodia Rhythm Combat Subsystem) | Without this, no JRPG battle can ever be started via the Melodia system. The entire gameplay loop from "battle requested" to "battle begins" is severed. This is the root cause of the "battle never starts" bug. |
| **#2** | StartSession (from BP_MelodiaJRPGGameInstance / BP_BattleController to Melodia Rhythm Combat Subsystem) | Skills are registered (RegisterSkill is wired) but no session is started. This means rhythm combat skill executions never activate — the combat system is wired to the skill definitions but has no execution context. |
| **#3** | SubmitRatedInput (from BP_BattleController to Melodia JRPGPresentation Rhythm Component) | RecordInputNow is called but the recorded input is never rated for timing accuracy (Perfect/Good/Miss). Without this, all player input yields no grade — the rhythm game aspect of combat is completely non-functional. |
| **#4** | ConsumePendingRequest + TryGrantShards (from BP_BattleController to Melodia Narrative Subsystem) | CompleteBattle is called but the battle completion pipeline is never finalized. Pending narrative requests never get consumed, and shard rewards are never granted. Players finish battles but receive no progression rewards. |
| **#5** | OnBattleRequested / OnJRPGBattleEnded (any Blueprint) | These event/delegate signals are completely absent from the entire project. The narrative-to-battle and battle-to-narrative handshake has no wiring whatsoever. Quillscript cannot trigger battles, and when battles end, narrative state is never updated. |

---

## Attached Scan Data

### Blueprint Export Summary

| Blueprint | Path | Functions Found | Connections Found |
|---|---|---|---|
| BP_BattleController | /Game/TurnBasedJRPGTemplate/Blueprints/Battle/BP_BattleController | 99+ unique function calls | 200+ connections |
| BP_MelodiaJRPGGameInstance | /Game/MelodiaIntegration/Blueprints/BP_MelodiaJRPGGameInstance | 37 unique function calls | ~40 connections |
| BP_BattleUI | /Game/TurnBasedJRPGTemplate/Blueprints/UI/BP_BattleUI | 29 unique function calls | ~60 connections |
| BP_MelodiaBattleUI | /Game/MelodiaIntegration/UI/BP_MelodiaBattleUI | 27 unique function calls | ~50 connections |
| BP_MelodiaJRPGGameMode | /Game/MelodiaIntegration/Blueprints/BP_MelodiaJRPGGameMode | 0 (empty graph) | 0 |
| BP_MelodiaJRPGPlayerController | /Game/MelodiaIntegration/Blueprints/BP_MelodiaJRPGPlayerController | 80+ unique function calls | ~100 connections |
| BP_JRPGGameInstance (base) | /Game/TurnBasedJRPGTemplate/Blueprints/Controllers/BP_JRPGGameInstance | 34 unique function calls | ~35 connections |

### Project-wide Term Coverage

| Term | Found In |
|---|---|
| BindEvent | BP_PauseMenu, BP_MainMenu, BP_WearEquipmentUI (all as BindEvents Custom Event, not Melodia-specific) |
| OnBattleRequested | **NOT FOUND** |
| OnJRPGBattleEnded | **NOT FOUND** |
| StartTaggedJRPGBattle | **NOT FOUND** |
| CompleteBattle | BP_BattleController only |
| RegisterSkill | BP_MelodiaJRPGGameInstance only |
| StartSession | **NOT FOUND** |
| RecordInputNow | BP_BattleController only |
| SubmitRatedInput | **NOT FOUND** |
| ConsumePendingRequest | **NOT FOUND** |
| TryGrantShards | **NOT FOUND** |
| MELUSINA_LOOP | **NOT FOUND** |

---

## Quillscript Narrative Assets (Integration Context)

The following narrative Quillscript assets exist in the project but **no Blueprint calls OnBattleRequested** to connect them to the JRPG battle system:

1. /Game/MelodiaIntegration/Narrative/MelodiaQuillPetalPriestess
2. /Game/MelodiaIntegration/Narrative/MelodiaQuillSmoke
3. /Game/MelodiaIntegration/Narrative/MelodiaQuillStarWeaver
4. /Game/MelodiaIntegration/Narrative/MelodiaQuillTwilightDancer
5. /Game/MelodiaIntegration/Narrative/MelodiaMorningIntro

These are story assets with no Blueprint-based trigger wiring — the Quill→Battle connection is completely disconnected.

---

## Widget Tree Data

### BP_MelodiaActionsUI
- Parent: UserWidget
- Children: CanvasPanel → ItemButton (BP_ActionButton_C), SkillButton (BP_ActionButton_C), FleeButton (BP_ActionButton_C), AttackButton (BP_ActionButton_C)
- Animations: ShowAnimation (0.25s)
- **No Melodia input context wiring visible at widget level**

### WBP_MelodiaRhythmHighway
- Parent: UserWidget
- Children: CanvasPanel → SheetMusicBG (Image), AuroraOverlay (Image), SparkleField (Image)
- **3 visual layers, no blueprint wiring to activate/deactivate — SetNoteHighwayActive is never called**

---

*End of Audit Report*
