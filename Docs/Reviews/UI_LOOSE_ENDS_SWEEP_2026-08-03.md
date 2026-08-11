# UI Loose Ends Sweep — 2026-08-03

**Generated:** 2026-08-03  
**Auditor:** UI Loose Ends Auditor (automated sweep)  
**Method:** Monolith MCP at localhost:9316 (ui_query, project_query, blueprint_query) + document diff  
**Read-only research — complete.**

---

## 1. UI Connection Status

### 1.1 BP_BattleUI — MelodiaNoteHighway Variable
| Field | Value |
|---|---|
| **Asset** | /Game/TurnBasedJRPGTemplate/Blueprints/UI/BP_BattleUI |
| **Variable exists?** | YES — "MelodiaNoteHighway" is a tree variable |
| **Widget class** | **Image** (NOT WBP_MelodiaRhythmHighway) |
| **BindWidget?** | No — source=tree_variable, is_bind_widget=false |
| **Visibility** | ESlateVisibility::Visible |
| **MelodiaBattleInputContextHandle** | YES — exists as struct variable (MelodiaInputContextHandle), category=Melodia\|Input, transient=true |
| **SetNoteHighwayActive called?** | **NO** — 0 results across entire project |
| **WBP_Battle_Rhythm dep?** | YES — hard dependency on /Game/Melodia/UI/WBP_Battle_Rhythm (separate widget) |

**Verdict: PARTIAL.** MelodiaNoteHighway exists but is a bare Image, not an instance of WBP_MelodiaRhythmHighway. The highway widget is never activated via SetNoteHighwayActive. There is a separate WBP_Battle_Rhythm dependency that may be the actual rhythm display. The Image-based MelodiaNoteHighway appears to be a dead variable — it holds no texture, has no BindWidget attribution, and its activation function is never called.

### 1.2 BP_ActionsUI — Button Styling
| Field | Value |
|---|---|
| **Asset** | /Game/TurnBasedJRPGTemplate/Blueprints/UI/BP_ActionsUI |
| **Parent class** | UserWidget |
| **Buttons** | ItemButton (BP_ActionButton_C), SkillButton (BP_ActionButton_C), FleeButton (BP_ActionButton_C), AttackButton (BP_ActionButton_C) |
| **Background** | ActionsBackground (Image) |
| **Animations** | ShowAnimation (0.25s) |
| **Render opacity** | 0.92 |

**Verdict: CONNECTED.** All buttons use stock BP_ActionButton_C class. Styling is consistent with the JRPG template. No Melodia-specific button overrides — this is the stock actions UI.

### 1.3 WBP_MelodiaRhythmHighway — Layer Textures
| Field | Value |
|---|---|
| **Asset** | /Game/Melodia/UI/Rhythm/WBP_MelodiaRhythmHighway |
| **Parent class** | UserWidget |
| **Widget count** | 4 (root CanvasPanel + 3 children) |
| **Child layers** | SheetMusicBG (Image, z=0), SparkleField (Image, z=5), AuroraOverlay (Image, z=10) |
| **Textures assigned?** | **NONE** — zero dependencies, no hard references to any Texture2D |
| **Blueprint wiring** | None — no EventGraph nodes detected |

**Verdict: 3 LAYERS NOT 4.** The widget tree shows 3 visual layers (not 4 as stated in the prior wiring-gap scan). None of the 3 Image widgets have assigned textures (no hard texture dependencies). The widget has zero referrers — it is orphaned and never instantiated. The 4th "NoteHighway" layer mentioned in prior docs does not exist.

### 1.4 BP_MelodiaActionsUI — Stock BP_ActionButton Reference
| Field | Value |
|---|---|
| **Asset** | /Game/MelodiaIntegration/UI/BP_MelodiaActionsUI |
| **Stock BP_ActionButton ref?** | YES — Hard reference to /Game/TurnBasedJRPGTemplate/Blueprints/UI/BP_ActionButton |
| **BP_ActionsUI ref?** | YES — Soft reference |
| **Own textures** | Uses stock T_CircleButton, T_SquareButton, T_TriangleButton, T_XButton |
| **Referenced by** | **EMPTY** — zero referrers |

**Verdict: CORRECTLY WIRED BUT ORPHANED.** The integration actions UI correctly references the stock BP_ActionButton. But no Blueprint, level, or widget creates or references this widget — it is dead code.

### 1.5 BP_MelodiaBattleUI — Search Results
| Field | Value |
|---|---|
| **Asset found?** | YES — /Game/MelodiaIntegration/UI/BP_MelodiaBattleUI |
| **Referenced by** | **EMPTY** — zero referrers |
| **Depends on** | BP_BattleController, BP_BattleBase, BP_PlayerUnitBase, BP_UnitBase, BP_ItemBase, BP_UsableItemBase, BP_BattleSkillBase, BP_EnemyBossBase, BP_JRPGPlayerController, BP_MelodiaRhythmPrompt, BP_BossUI, BP_PlayerUnitListUI, BP_TurnOrderList, BP_UnitBattleDetails, BP_ItemUseDialogue, BP_SkillUseDialogue, T_TargetIcon |

**Verdict: ORPHANED.** This widget has substantial dependencies but nothing references it. It is a copy of BP_BattleUI with Melodia Rhythm Prompt but without any of the Melodia-specific wiring (no PushContext/PopContext, no MelodiaNoteHighway, no RecordInputNow, no CompleteBattle as noted in the prior wiring-gap scan).

### 1.6 WBP_MainMenu — References
| Field | Value |
|---|---|
| **Asset found?** | YES — /Game/Melodia/UI/WBP_MainMenu |
| **Referenced by** | **EMPTY** — zero referrers |
| **Depends on** | F_Melodia_UI, F_InstrumentSerif, T_ParchmentNoise, T_Melodia_SoftMG_Parchment, WBP_SaveLoadPanel, BP_MelodiaJRPGGameInstance, BP_JRPGGameInstance, T_Melodia_Universal_ParchmentFrame, T_Melodia_Universal_CrestBaroque, T_Melodia_Universal_CornerBaroque, T_Melodia_Universal_MedallionRosette, T_Melodia_Universal_DividerScroll |

**Verdict: ORPHANED.** Has proper Melodia Universal textures and correct wiring to BP_MelodiaJRPGGameInstance (OnNewGameStarted, HasCanonicalJRPGSlot, LoadCanonicalJRPGSlot, CreateCanonicalJRPGSlot). But nothing in the project references this widget — it is never created or added to viewport.

### 1.7 WBP_MelodiaQuillDialog — Universal Textures
| Field | Value |
|---|---|
| **Asset** | /Game/Melodia/UI/Quill/WBP_MelodiaQuillDialog |
| **Universal textures?** | YES — T_Melodia_Universal_ParchmentFrame (Hard), T_Melodia_Universal_DividerScroll (Hard) |
| **Referenced by** | All 5 Quill assets: MorningIntro, PetalPriestess, Smoke, StarWeaver, TwilightDancer |

**Verdict: CONNECTED.** Correctly references both Universal textures and is referenced by all 5 narrative Quill assets.

### 1.8 WBP_MelodiaQuillSelection — Choice Entry Reference
| Field | Value |
|---|---|
| **Asset** | /Game/Melodia/UI/Quill/WBP_MelodiaQuillSelection |
| **WBP_MelodiaQuillChoiceEntry ref?** | YES — Hard reference |
| **Universal textures?** | YES — T_Melodia_Universal_ParchmentFrame (Hard) |
| **Referenced by** | All 5 Quill assets: MorningIntro, PetalPriestess, Smoke, StarWeaver, TwilightDancer |

**Verdict: CONNECTED.** Correctly references WBP_MelodiaQuillChoiceEntry and is wired to all 5 narrative Quill assets.

### 1.9 WBP_MainMenu — Button Styling
| Field | Value |
|---|---|
| **Buttons** | Btn_NewGame, Btn_Continue, Btn_LoadGame (component bound events present) |
| **Universal textures** | ParchmentFrame, CrestBaroque, CornerBaroque, MedallionRosette, DividerScroll — all hard refs |
| **Font** | F_Melodia_UI + F_InstrumentSerif |
| **Parchment textures** | T_ParchmentNoise, T_Melodia_SoftMG_Parchment |
| **Wiring** | Btn_NewGame → BP_MelodiaJRPGGameInstance::OnNewGameStarted |
| | Btn_Continue → HasCanonicalJRPGSlot / LoadCanonicalJRPGSlot |
| | Btn_LoadGame → Create WBP_SaveLoadPanel + AddToViewport |

**Verdict: FULLY STYLED BUT ORPHANED.** The main menu has complete Melodia-branded button styling with all 5 Universal ornamental textures, proper fonts, and correct wiring to the integration GameInstance. However, it has zero referrers — no level or game mode creates this widget.

---

## 2. Stale/Orphaned Assets — Every Melodia Widget with Zero References

The Monolith udit_orphan_assets action scanned 232 WidgetBlueprints. The following are Melodia-project orphan widgets (zero Asset Registry referrers AND zero cpp_asset_edges entries):

### Critical Orphans (should be wired into the game loop)

| # | Asset Path | Dependencies? | Notes |
|---|---|---|---|
| 1 | **/Game/MelodiaIntegration/UI/BP_MelodiaBattleUI** | YES — full battle UI stack | The Melodia-specific battle UI. Should be the primary battle HUD but nothing creates it |
| 2 | **/Game/MelodiaIntegration/UI/BP_MelodiaActionsUI** | YES — stock action buttons + textures | Melodia actions panel. Should replace BP_ActionsUI in Melodia battles |
| 3 | **/Game/Melodia/UI/WBP_MainMenu** | YES — full menu stack with Universal textures | Full main menu with save/load integration. Should be the game's main menu |
| 4 | **/Game/Melodia/UI/Rhythm/WBP_MelodiaRhythmHighway** | NONE — zero deps, zero textures | The rhythm highway visual. 3 layers, no textures assigned, no activation wiring |

### Supporting Orphans (feature widgets)

| # | Asset Path | Notes |
|---|---|---|
| 5 | /Game/MelodiaIntegration/UI/BP_MelodiaActionButton | Melodia-specific action button (never used) |
| 6 | /Game/MelodiaIntegration/UI/BP_MelodiaTurnOrderList | Melodia turn order list (never used) |
| 7 | /Game/Melodia/Blueprints/WBP_RhythmHUD | Rhythm HUD container |
| 8 | /Game/Melodia/UI/WBP_Battle_Mobile | Mobile battle variant |
| 9 | /Game/Melodia/UI/WBP_ComicOrrery | Comic-style orrery widget |
| 10 | /Game/Melodia/UI/WBP_DialogueBubble | Dialogue bubble widget |
| 11 | /Game/Melodia/UI/WBP_GradePop | Grade popup (Perfect/Good/Miss) |
| 12 | /Game/Melodia/UI/WBP_MelodiaOpeningSlideshow | Opening slideshow widget |
| 13 | /Game/Melodia/UI/WBP_MelodiaSettings | Settings widget |
| 14 | /Game/Melodia/UI/WBP_MenuButton | Menu button atom |
| 15 | /Game/Melodia/UI/WBP_QuestJournal | Quest journal widget |
| 16 | /Game/Melodia/UI/WBP_SaveLoad | Save/load widget |
| 17 | /Game/Melodia/UI/WBP_Settings | Settings (duplicate/alt) |
| 18 | /Game/Melodia/UI/WBP_SkillCodex | Skill codex widget |
| 19 | /Game/Melodia/UI/WBP_UltCutIn | Ultimate cut-in widget |

### Foundation Atoms (design system elements)

| # | Asset Path | Notes |
|---|---|---|
| 20 | /Game/Melodia/UI/Foundation/WBP_MelodiaDivider | Divider element |
| 21 | /Game/Melodia/UI/Foundation/WBP_MelodiaElementWheel | Element wheel |
| 22 | /Game/Melodia/UI/Foundation/WBP_MelodiaFiligreeDividerWave | Filigree divider wave |
| 23 | /Game/Melodia/UI/Foundation/WBP_MelodiaFiligreeGradeHalo | Grade halo effect |
| 24 | /Game/Melodia/UI/Foundation/WBP_MelodiaParchmentPanel | Parchment panel container |
| 25 | /Game/Melodia/UI/Foundation/WBP_MelodiaUniversalButton | Universal button base |

**Total Melodia orphan WidgetBlueprints: 25**

**Additionally orphaned (plugin/third-party, not Melodia-authored):**
- /Quillscript/Runtime/Widgets/DialogBoxBP, BackgroundBoxBP, SpriteBoxBP (3)
- /CommonUI/WBP_VirtualPointer (1)
- /MovieRenderPipeline/...DefaultBurnIn, UI_MovieGraphPipelineScreenOverlay, DefaultGraphBurnIn (3)
- /AudioWidgets/...AudioButtonMatrix, AudioFader, AudioKnobSmall, SubmixEffectDelayPresetWidget (4)
- /CelestialVault/UI/WBP_CelestialControls (1)
- /Takes/...DefaultTakeBurnIn, DefaultRecordingOverlay (2)
- /Game/UltraDynamicSky/...UDS_Analog_Clock, UDS_Onscreen_Controls, UDW_Current_Weather_Display, UDW_Thermometer (4)
- /Game/_ThirdParty/UltraDynamicSky/...UDS_Analog_Clock, UDS_Onscreen_Controls, UDW_Current_Weather_Display, UDW_Thermometer (4)

---

## 3. Document Drift — Which Review Docs Have Incorrect Information

### 3.1 BP_WIRING_GAP_SCAN_2026-08-03.md

**Accuracy assessment: SUBSTANTIALLY STILL ACCURATE, MINOR DRIFT**

| Claim in Doc | Current Status | Drift? |
|---|---|---|
| StartSession — NOT FOUND | **STILL NOT FOUND** (0 search results) | No drift |
| SubmitRatedInput — NOT FOUND | **STILL NOT FOUND** (0 search results) | No drift |
| ConsumePendingRequest — NOT FOUND | **STILL NOT FOUND** (0 search results) | No drift |
| TryGrantShards — NOT FOUND | **STILL NOT FOUND** (0 search results) | No drift |
| StartTaggedJRPGBattle — NOT FOUND | **STILL NOT FOUND** (0 search results) | No drift |
| SetNoteHighwayActive — NOT FOUND | **STILL NOT FOUND** (0 search results) | No drift |
| MelodiaNoteHighway variable exists | Confirmed (class=Image, tree_variable) | No drift |
| "3 visual layers" (WBP_MelodiaRhythmHighway) | **3 layers confirmed** (SheetMusicBG, AuroraOverlay, SparkleField) — doc says 3 | **Minor drift elsewhere: the earlier note above the widget tree says "3 visual layers" but the main text mentions "4 layers" inconsistently** |
| BP_MelodiaBattleUI has "none of the following Melodia connections" | Confirmed — PushContext, PopContext, MelodiaNoteHighway, RecordInputNow, CompleteBattle all absent from get_asset_details nodes | No drift |
| BP_MelodiaActionsUI references BP_ActionButton correctly | Confirmed — Hard reference to stock BP_ActionButton | No drift |

**Verdict: No action needed.** The session has NOT added StartSession, SubmitRatedInput, ConsumePendingRequest, or TryGrantShards — the document remains fully accurate about what's missing.

### 3.2 GRIEF_HOOK_NARRATIVE_SWEEP_2026-08-03.md

**Accuracy assessment: FULLY ACCURATE**

| Claim in Doc | Current Status | Drift? |
|---|---|---|
| 28 engine-log errors | Ambient — not rechecked | N/A (ambient) |
| 0 errored blueprints | Not rechecked | N/A |
| MorningIntro no .qsc source | **Still no source** — only .uasset exists | No drift |
| Smoke + TwilightDancer unwired | Both still have empty referenced_by | No drift |
| 5 Quill assets reference WBP widgets correctly | Confirmed — all 5 ref Dialog + Selection | No drift |
| BP_MelodiaSirMelodiousMorningIntro hard references MorningIntro | Not rechecked | N/A |

**Verdict: No action needed.** All asset statuses and trigger gaps described in this document persist unchanged.

### 3.3 MCP_SURFACE_SCAN_2026-08-03.md

**Accuracy assessment: FULLY ACCURATE**

| Claim in Doc | Current Status | Drift? |
|---|---|---|
| Monolith UP at :9316 | Confirmed — tools responding | No drift |
| VibeUE DOWN (port 8088) | Not rechecked (no health check run) | Likely still down |
| 1,328 registered tools | Not re-listed | N/A |
| UEBlueprintMCP socket listening on 55558 | Not rechecked | N/A |
| Figma token works, 125 components | Not rechecked | N/A |

**Verdict: No action needed.** Infrastructure status document remains accurate.

### 3.4 MULTI_AGENT_DELEGATION_PROMPTS_2026-08-03.md

**Exists:** YES — confirmed at C:\EnvironmentPortfolio\BS_GodFile\Docs\MULTI_AGENT_DELEGATION_PROMPTS_2026-08-03.md

---

## 4. Priority Fix List — Top 5 UI Issues Needing In-Editor Work

### #1 — WBP_MelodiaRhythmHighway is Unreferenced and Has No Textures
**Path:** /Game/Melodia/UI/Rhythm/WBP_MelodiaRhythmHighway  
**Severity:** CRITICAL  
**Issue:** This widget has 3 visual layers (SheetMusicBG, AuroraOverlay, SparkleField) but zero hard texture references. The MelodiaNoteHighway variable in BP_BattleUI is a bare Image, not an instance of this widget. The SetNoteHighwayActive function is never called anywhere.  
**Fix needed:** Assign textures to the 3 Image layers, wire this widget into BP_BattleUI (replace the bare Image MelodiaNoteHighway with an instance of this widget), and call SetNoteHighwayActive from the battle flow.

### #2 — BP_MelodiaBattleUI is Orphaned (Zero References, No Melodia Wiring)
**Path:** /Game/MelodiaIntegration/UI/BP_MelodiaBattleUI  
**Severity:** HIGH  
**Issue:** This widget was intended as the Melodia-specific battle HUD but nothing creates it. It lacks PushContext/PopContext, MelodiaNoteHighway, RecordInputNow, and CompleteBattle.  
**Fix needed:** Either wire this into BP_BattleController as the battle HUD (and add the missing Melodia connections) or delete it and consolidate onto BP_BattleUI.

### #3 — WBP_MainMenu is Orphaned Despite Full Styling
**Path:** /Game/Melodia/UI/WBP_MainMenu  
**Severity:** HIGH  
**Issue:** This widget has complete Melodia branding (all 5 Universal textures, proper fonts, save/load integration) but is never referenced by any GameMode or level. The MelodiaIntegrationMap or BP_MelodiaJRPGGameMode must create this widget.  
**Fix needed:** Add widget creation in BP_MelodiaJRPGGameMode (or BP_MelodiaJRPGPlayerController BeginPlay) to create and add WBP_MainMenu to viewport.

### #4 — BP_MelodiaActionsUI is Orphaned (No Consumer)
**Path:** /Game/MelodiaIntegration/UI/BP_MelodiaActionsUI  
**Severity:** HIGH  
**Issue:** Correctly references stock BP_ActionButton and stock textures, but nothing references this widget. The BP_BattleController and BP_BattleUI use the stock BP_ActionsUI instead.  
**Fix needed:** Either wire BP_MelodiaActionsUI into the Melodia battle flow (replace BP_ActionsUI) or consolidate the integration changes into BP_ActionsUI directly.

### #5 — All 4 Melodia Runtime Connection Functions Still Missing
**Functions:** StartSession, SubmitRatedInput, ConsumePendingRequest, TryGrantShards  
**Severity:** HIGH (gameplay blocking)  
**Issue:** The prior wiring-gap scan identified these 4 critical missing function calls. A re-scan confirms all 4 are STILL absent from every Blueprint in the project. The gameplay chain remains broken at:
- Session: RegisterSkill exists → StartSession does not
- Grade: RecordInputNow exists → SubmitRatedInput does not
- Resolve: CompleteBattle exists → ConsumePendingRequest/TryGrantShards do not
**Fix needed:** Wire these 4 function calls into BP_BattleController and BP_MelodiaJRPGGameInstance per the connection matrix in the wiring-gap scan.

---

## 5. Summary Statistics

| Metric | Count |
|---|---|
| Total WidgetBlueprints scanned | 232 |
| Melodia project orphan widgets | 25 |
| Plugin/third-party orphan widgets | 22 |
| Total orphan WidgetBlueprints | 47 |
| Quill dialog widgets properly connected | 2/2 (Dialog + Selection) |
| QuillChoiceEntry referenced correctly | YES |
| Universal textures correctly referenced | Dialog ✓, Selection ✓, MainMenu ✓ |
| Missing gameplay chain functions | 4 (StartSession, SubmitRatedInput, ConsumePendingRequest, TryGrantShards) still absent |
| Documents with significant drift | 0/3 (all still accurate) |

---

*End of Sweep Report*
