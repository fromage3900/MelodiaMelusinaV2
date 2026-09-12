# Agent Delegation Packet — Persona-Lite Finalization & Documentation Blitz
**Date:** 2026-08-03  
**Purpose:** Copy-paste prompts for delegating documentation, review, loose-end checks, and system finalization to parallel agents.

---

## How to Use
Each prompt is self-contained. Copy the block, paste to the target agent (Qwen, DeepSeek, Claude, Gemini, Kimi, or any subagent). Each returns a document at the specified path.

---

## PROMPT 1 — System Health & Loose Ends Sweep

**Target:** Qwen/DeepSeek  
**Output:** `Docs/Reviews/SYSTEM_HEALTH_LOOSE_ENDS_2026-08-03.md`

```
You are a UE 5.8 systems auditor. Your task is to sweep the ENTIRE project for loose ends, 
broken references, unconnected systems, and stale documentation claims.

## Read These First
1. `C:\EnvironmentPortfolio\BS_GodFile\Docs\Reviews\QUILLSCRIPT_GRIEF_HOOK_REVIEW_2026-08-03.md`
2. `C:\EnvironmentPortfolio\BS_GodFile\Docs\Reviews\JRPG_TRAVERSAL_REVIEW_2026-08-03.md`
3. `C:\EnvironmentPortfolio\BS_GodFile\Docs\Reviews\RHYTHM_WALLET_REVIEW_2026-08-03.md`
4. `C:\EnvironmentPortfolio\BS_GodFile\_ROADBLOCKS_2026-07-31.md`
5. `C:\EnvironmentPortfolio\BS_GodFile\_DECISION_LOG.md`
6. `C:\EnvironmentPortfolio\BS_GodFile\_TASK_QUEUE.md`

## Then Run These Monolith Queries at localhost:9316
1. `editor_query list_dirty_packages`
2. `editor_query list_errored_blueprints`
3. `project_query search query="ReferenceCount:0"` — find unreferenced assets
4. `project_query search query="error"` — search for error logs
5. `editor_query get_build_summary`

## Deliverable
Write to `C:\EnvironmentPortfolio\BS_GodFile\Docs\Reviews\SYSTEM_HEALTH_LOOSE_ENDS_2026-08-03.md`:

1. **Loose Ends Inventory**: Every asset, system, or config that is:
   - Referenced by nothing (orphaned)
   - Referencing something broken (dangling)
   - Stale (superseded by a newer version)
   - Duplicate (two copies of same thing)
2. **Claim vs. Reality Table**: For every "done" claim in the docs, confirm or deny with Monolith evidence
3. **Contradiction Register**: Update the contradictions from `_ROADBLOCKS_2026-07-31.md` — which are fixed, which persist
4. **Build Health**: Current compile errors, warnings, test failures
5. **Priority Matrix**: Rank loose ends P0-P3 by blast radius on the 20-min slice

Return: The full path and a 5-line summary.
```

---

## PROMPT 2 — Grief Hook Narrative Finalization

**Target:** Claude/Gemini  
**Output:** `Docs/Narrative/GRIEF_HOOK_FINALIZATION_2026-08-03.md`

```
You are a narrative designer for a Persona-lite JRPG. Your task is to finalize the 
grief hook narrative for the First Dream vertical slice.

## Read These
1. `C:\EnvironmentPortfolio\BS_GodFile\Docs\Research\MELODIA_BARD_GRIEF_HOOK_2026-07-31.md`
2. `C:\EnvironmentPortfolio\BS_GodFile\Docs\Research\MELODIA_PSYCH_MUSIC_INDIE_REFERENCE_2026-07-31.md`
3. `C:\EnvironmentPortfolio\BS_GodFile\Docs\MELODIA_IDENTITY_AND_LOOP_2026-07-30.md`
4. `C:\EnvironmentPortfolio\BS_GodFile\Docs\FIRST_DREAM_20_MINUTE_PLAYTEST_2026-08-01.md`
5. `C:\EnvironmentPortfolio\BS_GodFile\Docs\MELODIA_SOLO_GAMEPLAY_CONSTITUTION_2026-07-27.md`

## Also Read (for Quill source reference)
6. Find and read the QuillScript smoke test at `C:\EnvironmentPortfolio\CompatibilityLabs\QuillScriptUE58\TestScripts\MelodiaQuillSmoke.qsc`
7. Read `C:\EnvironmentPortfolio\BS_GodFile\Docs\Handoffs\QUILLSCRIPT_GRIEF_HOOK_REVIEW_2026-08-03.md`

## Then Read the Existing Quill Assets
Use Monolith at localhost:9316:
- `project_query get_asset_details` on `/Game/MelodiaIntegration/Narrative/MelodiaMorningIntro`
- `project_query get_asset_details` on `/Game/MelodiaIntegration/Narrative/MelodiaQuillPetalPriestess`
- `project_query get_asset_details` on `/Game/MelodiaIntegration/Narrative/MelodiaQuillSmoke`
- `project_query get_asset_details` on `/Game/MelodiaIntegration/Narrative/MelodiaQuillStarWeaver`
- `project_query get_asset_details` on `/Game/MelodiaIntegration/Narrative/MelodiaQuillTwilightDancer`

## Deliverable
Write to `C:\EnvironmentPortfolio\BS_GodFile\Docs\Narrative\GRIEF_HOOK_FINALIZATION_2026-08-03.md`:

1. **Beat Map**: The 6 emotional beats of the First Dream:
   B1. Melusina arrives late/post-festival (grief trigger)
   B2. Absent duet partner felt but not explained
   B3. Sir Melodious is alive, snack-seeking (warmth)
   B4. Petal Priestess tonal choice (Harmony +1)
   B5. Battle → typed result → reunion
   B6. Save → return to bed → narrative consequence
   
   For each beat, state: Is it authored in Quill? Is it compiled into the .uasset? Is it triggered by a placed NPC?

2. **QuillScript Authoring Checklist**: For each missing beat, provide the exact QuillScript (.qsc) source needed

3. **Dialogue UI Spec**: Map each beat to the Figma DialogueOverlay (72:1843) child components that render it

4. **Emotional Arc Assessment**: Does the current authored content deliver:
   - Grief without explanation (show, don't tell)
   - Warmth without saccharine (Sir's alive)
   - Choice without punishment (both Priestess options converge)
   - Reunion without retcon (the duet partner stays absent)

Return: The full path and a 5-line summary.
```

---

## PROMPT 3 — Persona-Lite Loop Verification

**Target:** DeepSeek/Kimi  
**Output:** `Docs/Reviews/PERSONA_LITE_LOOP_VERIFICATION_2026-08-03.md`

```
You are a UE 5.8 gameplay integration tester. Your task is to verify EVERY connection 
in the persona-lite loop end-to-end through static analysis.

## Read These
1. `C:\EnvironmentPortfolio\BS_GodFile\Docs\MELODIA_SOLO_GAMEPLAY_CONSTITUTION_2026-07-27.md`
2. `C:\EnvironmentPortfolio\BS_GodFile\Docs\MELODIA_SYSTEMS_COMPOSITION_CONTRACT_2026-07-30.md`
3. `C:\EnvironmentPortfolio\BS_GodFile\Docs\PIE_VERIFICATION_CHECKLIST_2026-08-03.md`
4. `C:\EnvironmentPortfolio\BS_GodFile\Docs\FIRST_DREAM_20_MINUTE_PLAYTEST_2026-08-01.md`
5. `C:\EnvironmentPortfolio\BS_GodFile\Docs\Handoffs\QWEN_BATTLE_NARRATIVE_BINDING_2026-08-03.md`
6. `C:\EnvironmentPortfolio\BS_GodFile\Docs\Reviews\JRPG_TRAVERSAL_REVIEW_2026-08-03.md`

## Run These Monolith Queries
1. `blueprint_query get_graph_summary` on `/Game/MelodiaIntegration/Blueprints/BP_MelodiaJRPGGameInstance`
2. `blueprint_query get_graph_summary` on `/Game/TurnBasedJRPGTemplate/Blueprints/Battle/BP_BattleController`
3. `blueprint_query get_variables` on `/Game/TurnBasedJRPGTemplate/Blueprints/Battle/BP_BattleController`
4. `project_query get_asset_details` on `/Game/MelodiaIntegration/Config/DA_MelodiaIntegrationConfig`
5. `ui_query get_widget_tree` on `/Game/TurnBasedJRPGTemplate/Blueprints/UI/BP_BattleUI`
6. `ui_query get_widget_tree` on `/Game/Melodia/UI/Rhythm/WBP_MelodiaRhythmHighway`

## Deliverable
Write to `C:\EnvironmentPortfolio\BS_GodFile\Docs\Reviews\PERSONA_LITE_LOOP_VERIFICATION_2026-08-03.md`:

1. **Complete Loop Trace**: Follow every step of the loop:
   ```
   New Game → Melusina Morning → Sir interaction → Quill dialogue → 
   Petal Priestess choice → Harmony+1 → quest/marker → Dreamstate traversal → 
   melodia:battle: notification → OnBattleRequested → StartTaggedJRPGBattle → 
   Stock battle → result matrix → CompleteBattle → Quill resume → 
   post-battle dialogue → KaleidoNave travel → save → full exit → load
   ```
   For each step, state:
   - Is the C++ handler compiled? (check via cppreflect_query)
   - Is the Blueprint graph node present? (check via blueprint_query)
   - Is the content reference resolved? (check via project_query)
   - What would break if this step fired in PIE right now?

2. **Authority Compliance Check**: Verify Decision 009 (stock JRPG owns battle), 
   Decision 018 (social stats from Quill only), Decision 028 (save/restore OpenLevel exception)

3. **Failure Mode Analysis**: For each of these, does the system degrade gracefully?
   - Missing Quill runtime
   - Unknown encounter ID
   - No tagged battle actor in level
   - Duplicate battle completion
   - Missing save record

4. **Gate Status**: Which PIE gates (from the checklist) would pass if run NOW vs. which are still blocked

Return: The full path and a 5-line summary.
```

---

## PROMPT 4 — Documentation Corpus Consolidation

**Target:** Gemini  
**Output:** `Docs/DOCUMENTATION_CONSOLIDATION_2026-08-03.md`

```
You are a documentation architect. Your task is to consolidate the 206+ markdown files 
in the project into a coherent, navigable corpus.

## Read These First
1. `C:\EnvironmentPortfolio\BS_GodFile\DOC_INDEX.md`
2. `C:\EnvironmentPortfolio\BS_GodFile\_DECISION_LOG.md`
3. `C:\EnvironmentPortfolio\BS_GodFile\Docs\Handoffs\RHYTHM_SKILL_SYSTEM_EXPANSION_2026-08-03.md`
4. `C:\EnvironmentPortfolio\BS_GodFile\Docs\MELODIA_SOLO_GAMEPLAY_CONSTITUTION_2026-07-27.md`
5. `C:\EnvironmentPortfolio\BS_GodFile\Docs\WEBSITE_OVERHAUL_PLAN_2026-07-31.md`

## Then Scan the File System
List ALL .md files under `C:\EnvironmentPortfolio\BS_GodFile\Docs\` and `C:\EnvironmentPortfolio\BS_GodFile\*.md`.

## Deliverable
Write to `C:\EnvironmentPortfolio\BS_GodFile\Docs\DOCUMENTATION_CONSOLIDATION_2026-08-03.md`:

1. **File Inventory**: Total count, breakdown by directory, oldest/newest
2. **Tier Classification**: Every doc classified as:
   - ACTIVE — current truth, reference in `DOC_INDEX.md`
   - REFERENCE — historical context, useful but not current
   - SUPERSEDED — replaced by a newer doc with same topic
   - FROZEN — frozen by constitution, do not act on
3. **Stale Path Scan**: Find every `G:\` drive path in docs and flag it
4. **Duplicate Detection**: Find docs covering the same topic with different conclusions
5. **Front Door Proposal**: Design a `FRONT_DOOR.md` that gets a new reader to the right
   doc in ≤3 clicks
6. **Prune List**: Which files should be moved to `_Reference/` or `_Superseded/`?

Return: The full path and a 5-line summary.
```

---

## PROMPT 5 — Rhythm Combat Pipeline Deep Review

**Target:** Qwen  
**Output:** `Docs/Reviews/RHYTHM_COMBAT_PIPELINE_DEEP_REVIEW_2026-08-03.md`

```
You are a UE 5.8 audio/rhythm systems engineer. Your task is to trace the ENTIRE 
rhythm combat pipeline from input to gameplay effect, noting every gap.

## Read These
1. `C:\EnvironmentPortfolio\BS_GodFile\Docs\Handoffs\QWEN_HARMONIX_QUARTZ_BATTLE_INTEGRATION_2026-08-03.md`
2. `C:\EnvironmentPortfolio\BS_GodFile\Docs\Handoffs\QWEN_RHYTHM_SKILLS_SCOPE_2026-08-03.md`
3. `C:\EnvironmentPortfolio\BS_GodFile\Docs\Handoffs\RHYTHM_SKILL_SYSTEM_EXPANSION_2026-08-03.md`
4. `C:\EnvironmentPortfolio\BS_GodFile\Docs\Reviews\RHYTHM_WALLET_REVIEW_2026-08-03.md`
5. `C:\EnvironmentPortfolio\BS_GodFile\Plugins\MelodiaCore\Rules\melodia_rules.json`

## Read the Source Code
1. `C:\EnvironmentPortfolio\BS_GodFile\Source\BS_GodFile\MelodiaIntegration\MelodiaRhythmCombatSubsystem.h`
2. `C:\EnvironmentPortfolio\BS_GodFile\Source\BS_GodFile\MelodiaIntegration\MelodiaRhythmCombatSubsystem.cpp`
3. `C:\EnvironmentPortfolio\BS_GodFile\Source\BS_GodFile\MelodiaIntegration\MelodiaJRPGPresentationRhythmComponent.h`
4. `C:\EnvironmentPortfolio\BS_GodFile\Source\BS_GodFile\MelodiaIntegration\MelodiaJRPGPresentationRhythmComponent.cpp`
5. `C:\EnvironmentPortfolio\BS_GodFile\Source\BS_GodFile\MelodiaIntegration\MelodiaMusicClockSubsystem.h`

## Run Monolith Queries
1. `cppreflect_query get_uclass` on `UMelodiaRhythmCombatSubsystem`
2. `cppreflect_query get_uclass` on `UMelodiaJRPGPresentationRhythmComponent`
3. `cppreflect_query get_uclass` on `UMelodiaMusicClockSubsystem`
4. `project_query get_asset_details` on `/Game/MelodiaIntegration/Config/DA_CadenceStrike`
5. `project_query search` query="RecordInputNow"

## Deliverable
Write to `C:\EnvironmentPortfolio\BS_GodFile\Docs\Reviews\RHYTHM_COMBAT_PIPELINE_DEEP_REVIEW_2026-08-03.md`:

1. **Full Pipeline Trace**:
   ```
   Player presses attack → RecordInputNow() → grade evaluation → 
   OnPresentationRhythmResult broadcast → SubmitRatedInput → 
   SubmitResult → ConsumePendingRequest → stock resolver applies effect
   ```
   For each step: which function, which file, what parameters, what returns

2. **Grade Flow**: Trace the EMelodiaSkillGrade from RecordInputNow() through to the stock resolver

3. **Wallet Integration Points**: Where TryGrantShards gets called, with what GrantId

4. **MPC Parameter Contract**: List every MPC_Melodia_Palette scalar that SHOULD be written
   by TickPresentation vs. what IS written

5. **Gap Analysis**: Every missing connection between C++ and Blueprint

Return: The full path and a 5-line summary.
```

---

## PROMPT 6 — Melody Token Economy & Save Integration Audit

**Target:** DeepSeek  
**Output:** `Docs/Reviews/TOKEN_ECONOMY_SAVE_AUDIT_2026-08-03.md`

```
You are an economy designer for a Persona-lite RPG. Your task is to audit the 
Melody Token wallet system end-to-end, from pickup to save to spend.

## Read These
1. `C:\EnvironmentPortfolio\BS_GodFile\Plugins\MelodiaCore\Source\MelodiaCore\MelodiaTokenWalletSubsystem.h`
2. `C:\EnvironmentPortfolio\BS_GodFile\Plugins\MelodiaCore\Source\MelodiaCore\MelodiaTokenWalletSubsystem.cpp`
3. `C:\EnvironmentPortfolio\BS_GodFile\Docs\Handoffs\KIRO_MELODY_TOKEN_INTEGRATION_2026-08-01.md`
4. `C:\EnvironmentPortfolio\BS_GodFile\Docs\Handoffs\CLAUDE_TO_KIRO_STATE_2026-08-01.md`
5. `C:\EnvironmentPortfolio\BS_GodFile\Docs\Reviews\RHYTHM_WALLET_REVIEW_2026-08-03.md`

## Run Monolith Queries
1. `project_query search` query="MI_MelodyToken"
2. `project_query search` query="TokenWallet"
3. `cppreflect_query get_uclass` on `UMelodiaTokenWalletSubsystem`
4. `project_query search` query="TryGrantShards"

## Deliverable
Write to `C:\EnvironmentPortfolio\BS_GodFile\Docs\Reviews\TOKEN_ECONOMY_SAVE_AUDIT_2026-08-03.md`:

1. **Token Table**: All 4 variants (Forte/Star/Swirl/Water) with display name, value, rarity,
   material instance path, texture paths — what exists vs. what's missing

2. **Economy Flow**: 
   ```
   Pickup → TryGrantShards(Element, Amount, GrantId) → OnWalletChanged → HUD update → 
   Battle victory → TryGrantShards again → same GrantId → REJECTED (idempotent)
   ```
   Is the grant-idempotency path proven? Does it survive a full process restart?

3. **Save Integration**: Trace CaptureToSave → RestoreFromSave through the 
   BP_JRPGSaveGame record. Is the wallet state included in the canonical save transaction?

4. **Console Commands**: Verify `melodia.Wallet.Dump`, `Grant`, `Spend`, `AddMana`, `SpendMana`
   work from the in-game console

5. **Gap Analysis**: What would prevent a player from earning tokens in PIE right now?

Return: The full path and a 5-line summary.
```

---

## PROMPT 7 — Input Context & Focus Authority Audit

**Target:** Claude  
**Output:** `Docs/Reviews/INPUT_CONTEXT_AUDIT_2026-08-03.md`

```
You are a UE 5.8 UX/input systems engineer. Your task is to audit every widget and 
system that manages input mode, cursor visibility, and player focus.

## Read These
1. `C:\EnvironmentPortfolio\BS_GodFile\Source\BS_GodFile\MelodiaIntegration\MelodiaInputContextSubsystem.h`
2. `C:\EnvironmentPortfolio\BS_GodFile\Source\BS_GodFile\MelodiaIntegration\MelodiaInputContextSubsystem.cpp`
3. `C:\EnvironmentPortfolio\BS_GodFile\Source\BS_GodFile\MelodiaIntegration\MelodiaAudioReactivePresentationSubsystem.cpp`
4. `C:\EnvironmentPortfolio\BS_GodFile\Source\BS_GodFile\MelodiaIntegration\MelodiaExternalJRPGBridgeSubsystem.cpp`

## Run Monolith Queries
1. `project_query search` query="PushContext" — find EVERY PushContext call in content
2. `project_query search` query="PopContext" — find EVERY PopContext call
3. `project_query search` query="SetInputMode" — find stale SetInputMode calls
4. `ui_query get_widget_tree` on `/Game/Melodia/UI/Quill/WBP_MelodiaQuillDialog`
5. `ui_query get_widget_tree` on `/Game/Melodia/UI/Quill/WBP_MelodiaQuillSelection`
6. `blueprint_query get_graph_summary` on `/Game/TurnBasedJRPGTemplate/Blueprints/UI/BP_BattleUI`

## Deliverable
Write to `C:\EnvironmentPortfolio\BS_GodFile\Docs\Reviews\INPUT_CONTEXT_AUDIT_2026-08-03.md`:

1. **Context Coverage Matrix**: For each surface (dialogue, battle, menu, cinematic),
   does it PushContext on open and PopContext on close?

2. **Stale SetInputMode Calls**: Find every `SetInputMode_GameOnly` / `SetInputMode_UIOnly`
   that should be replaced by PushContext/PopContext

3. **Leak Detection**: Are there any code paths where a context is pushed but never popped?
   (travel force-clears, but what about error paths?)

4. **Focus Restoration**: When dialogue closes, does focus return to the correct widget?
   When menu closes, does the game cursor mode restore correctly?

5. **Recommendations**: Which specific files need changes to close input context gaps

Return: The full path and a 5-line summary.
```

---

## PROMPT 8 — QuillScript Authoring Guide & Morning Source

**Target:** Gemini  
**Output:** `Docs/Narrative/QUILLSCRIPT_AUTHORING_GUIDE_2026-08-03.md`

```
You are a narrative scripter for QuillScript-based dialogue. Your task is to create 
an authoring guide and author the MorningIntro .qsc source.

## Read These
1. `C:\EnvironmentPortfolio\BS_GodFile\Docs\Research\MELODIA_BARD_GRIEF_HOOK_2026-07-31.md`
2. `C:\EnvironmentPortfolio\CompatibilityLabs\QuillScriptUE58\README.md`
3. `C:\EnvironmentPortfolio\CompatibilityLabs\QuillScriptUE58\SMOKE_TEST_SPEC.md`
4. `C:\EnvironmentPortfolio\CompatibilityLabs\QuillScriptUE58\TestScripts\MelodiaQuillSmoke.qsc`
5. Read the QuillScript plugin README for syntax reference

## Then Read the Melodia Adapter Source
6. `C:\EnvironmentPortfolio\BS_GodFile\Source\BS_GodFile\MelodiaIntegration\MelodiaNarrativeSubsystem.h`

## Deliverable
Write to `C:\EnvironmentPortfolio\BS_GodFile\Docs\Narrative\QUILLSCRIPT_AUTHORING_GUIDE_2026-08-03.md`:

1. **QuillScript Syntax Reference**: The subset of QuillScript commands that the Melodia
   adapter supports (melodia:battle:, melodia:quest:, melodia:flag:, melodia:travel:,
   melodia:reward:, melodia:stat:)

2. **MorningIntro.qsc Source**: The full QuillScript source for the Morning Sir interaction:
   ```
   @ Start
   - Sir: "Melusina... you're back."
   - Melusina: "The festival... I missed it, didn't I?"
   - Sir: "The petals have already fallen. But the shrine still remembers."
   * [Follow the quiet chirp] -> Reunion
   * [Ask about the festival] -> Listening
   
   @ Reunion
   - Sir: "There's something I want to show you. Follow me."
   -> Departure
   
   @ Listening
   - Sir: "The festival was beautiful. You would have loved it."
   - Sir: "But more importantly — you're here now."
   $ met_festival = true
   -> Departure
   
   @ Departure
   - Narrator: "Sir hops off the bedpost and chirps toward the door."
   - Narrator: "The dreamstate awaits."
   melodia:travel:melodia_integration_map
   ```

3. **Intent Flow**: Map each melodia: intent verb to the narrative subsystem handler it triggers

4. **Editor Setup**: How to create/edit QuillScript assets in UE 5.8

Return: The full path and a 5-line summary.
```

---

## PROMPT 9 — UI Texture & Asset Inventory

**Target:** Kimi  
**Output:** `Docs/Reviews/UI_TEXTURE_INVENTORY_2026-08-03.md`

```
You are a UI asset manager. Your task is to inventory every texture, widget, and 
style used by the Melodia game UI, identifying gaps and duplicates.

## Read These
1. `C:\EnvironmentPortfolio\generated\assets\melodia-game-ui\ART_SOURCE.json`
2. `C:\EnvironmentPortfolio\BS_GodFile\Docs\TEXTURE_DUPLICATE_AUDIT_2026-08-03.md`
3. `C:\EnvironmentPortfolio\wix\melodia-game-ui.css` (lines 1-100 for texture references)

## Run Monolith Queries
1. `project_query search` query="T_Melodia_Universal" — list all Universal textures
2. `project_query search` query="T_Melodia_SoftMG" — list all SoftMG textures
3. `project_query search` query="T_Melodia_Filigree" — list all Filigree textures
4. `project_query search` query="T_Melodia_Grade" — list all Grade textures
5. `ui_query get_widget_tree` on `/Game/Melodia/UI/Rhythm/WBP_MelodiaRhythmHighway`

## Deliverable
Write to `C:\EnvironmentPortfolio\BS_GodFile\Docs\Reviews\UI_TEXTURE_INVENTORY_2026-08-03.md`:

1. **Texture Manifest**: Every T_Melodia_* texture with:
   - Asset path, format, dimensions (if available)
   - Which Widget Blueprint references it
   - Whether it's part of the Universal (canonical), GameUI, Source, or Alphas set
   - Whether it has a duplicate in another location

2. **Widget Texture Map**: For each key widget (WBP_MainMenu, BP_BattleUI, BP_ActionButton,
   WBP_MelodiaQuillDialog, WBP_MelodiaRhythmHighway), list which texture each Image child uses

3. **Missing Textures**: Textures referenced in CSS (wix/) that have no UE counterpart

4. **Orphaned Textures**: Textures in Content/ that are referenced by zero widgets

5. **Consolidation Plan**: Step-by-step to move everything to the Universal set

Return: The full path and a 5-line summary.
```

---

## PROMPT 10 — Travel & Level Streaming Finalization

**Target:** Claude  
**Output:** `Docs/Reviews/TRAVEL_FINALIZATION_2026-08-03.md`

```
You are a UE 5.8 level streaming engineer. Your task is to verify every travel 
path and level connection in the First Dream route.

## Read These
1. `C:\EnvironmentPortfolio\BS_GodFile\Docs\Reviews\JRPG_TRAVERSAL_REVIEW_2026-08-03.md`
2. `C:\EnvironmentPortfolio\BS_GodFile\Docs\MELODIA_SYSTEMS_COMPOSITION_CONTRACT_2026-07-30.md`
3. `C:\EnvironmentPortfolio\BS_GodFile\Docs\BLUEPRINT_WIRING_CHECKLIST_2026-07-30.md`

## Read the Source
4. `C:\EnvironmentPortfolio\BS_GodFile\Source\BS_GodFile\MelodiaIntegration\MelodiaTravelSubsystem.h`
5. `C:\EnvironmentPortfolio\BS_GodFile\Source\BS_GodFile\MelodiaIntegration\MelodiaTravelSubsystem.cpp`

## Run Monolith Queries
1. `project_query get_asset_details` on `/Game/MelodiaIntegration/Config/DA_MelodiaIntegrationConfig`
2. `project_query search` query="TravelTo" — find ALL TravelTo calls in Blueprints
3. `project_query search` query="OpenLevel" — find all remaining OpenLevel calls
4. `project_query search` query="PlayerStart" — in KaleidoNave
5. `blueprint_query get_graph_summary` on `/Game/MelodiaIntegration/Blueprints/BP_MelodiaJRPGGameInstance`

## Deliverable
Write to `C:\EnvironmentPortfolio\BS_GodFile\Docs\Reviews\TRAVEL_FINALIZATION_2026-08-03.md`:

1. **Route Map**: Main Menu → L_MelusinaMorning → L_KaleidoNave (merged Dreamstate).
   For each transition: which TravelTo call, which LevelId, which PlayerStart tag

2. **Allowlist Audit**: Verify every reachable destination is in DA_MelodiaIntegrationConfig.TravelLevelIds

3. **OpenLevel Audit**: Find every `Open Level (by Name)` call that should be a `TravelTo`.
   Verify Decision 028 exception (save/restore legs)

4. **PlayerStart Tag Status**: Are the KaleidoNave PlayerStarts tagged? Which tag?

5. **Spawn Context**: Does TravelTo set SpawnContext before travel and clear input context
   on arrival? (check C++ source)

6. **Failure Mode**: What happens if TravelTo returns false (destination not allowlisted)?
   Does it degrade to OpenLevel gracefully?

Return: The full path and a 5-line summary.
```

---

## Master Delegation Checklist

| # | Prompt | Agent | Est. Time | Collision |
|---|--------|-------|-----------|-----------|
| 1 | System Health & Loose Ends | Qwen/DeepSeek | 30min | Read-only |
| 2 | Grief Hook Finalization | Claude/Gemini | 45min | Read-only |
| 3 | Persona-Lite Loop Verification | DeepSeek/Kimi | 30min | Read-only |
| 4 | Documentation Consolidation | Gemini | 20min | Read-only |
| 5 | Rhythm Combat Pipeline | Qwen | 30min | Read-only |
| 6 | Token Economy & Save Audit | DeepSeek | 25min | Read-only |
| 7 | Input Context & Focus Audit | Claude | 20min | Read-only |
| 8 | QuillScript Authoring Guide | Gemini | 35min | Read-only |
| 9 | UI Texture & Asset Inventory | Kimi | 20min | Read-only |
| 10 | Travel & Level Streaming | Claude | 25min | Read-only |

All 10 prompts are READ-ONLY — zero collision risk. All can run in parallel.
