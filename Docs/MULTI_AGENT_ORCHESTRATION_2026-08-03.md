# Multi-Agent Orchestration — 2026-08-03 Evening

## Collision Locks
| Asset | Owner | Permission |
|-------|-------|------------|
| BP_BattleController EventGraph | Qwen | Edit |
| BP_MelodiaJRPGGameInstance | Qwen | Edit |
| BP_InteractionBattle | Qwen | Edit CDO properties |
| WBP_MelodiaRhythmHighway | UI_Agent | Edit |
| BP_BattleUI widget tree | UI_Agent | Edit |
| BP_ActionButton + BP_ActionsUI | UI_Agent | Edit |
| BP_UnitBattleDetails | UI_Agent | Edit |
| C++ Source (Bridge/Narrative) | Locked | Read-only |
| DA_MelodiaIntegrationConfig | Locked | Read-only |
| L_KaleidoNave / L_MelusinaMorning | Human (PIE) | Read-only |

## Agent Lanes

### Lane A — Qwen: Blueprint Wiring (via UEBlueprintMCP)
**Goal:** Wire battle controller to narrative subsystem, register rhythm skills
**Tools:** UEBlueprintMCP (blueprint tools), Monolith (readback)
**Tasks:**
1. Wire BP_BattleController result matrix → `CompleteBattle()` call on narrative subsystem
2. Wire rhythm skills registration: `RegisterSkill(DA_CadenceStrike)` etc. in GameInstance
3. Tag placed BP_InteractionBattle instance with `melodia_smoke_encounter` tag  

### Lane B — UI Agent: Rhythm Highway + UI Polish
**Goal:** Assign textures to rhythm highway, polish battle UI
**Tools:** Monolith ui_query
**Tasks:**
1. Assign redesign SheetMusicBG/Aurora/Sparkle textures to WBP_MelodiaRhythmHighway
2. Set MelodiaNoteHighway Image brush texture in BP_BattleUI
3. Apply Melodia palette to stock BP_ActionsUI background/panel

### Lane C — Human (you): PIE Verification
**Goal:** Walk the 20-min slice, prove connections
**Tasks:**
1. New Game → Melusina Morning → Sir dialogue → Quill choice
2. Battle triggers → UI shows → result → Quill resumes
3. Save → exit → reload → state preserved

## Execution Order
Phase 1: Lane A + Lane B in parallel (both use different assets)
Phase 2: Lane C after both A and B report done
