# Melodia Figma "Essential UI" → Unreal (BS_GodFile) Wiring Plan

**Date:** 2026-07-16
**Status:** Plan / mapping only — no UMG authored, read-only pass (live UE session owned by another worker; no git commit)
**Grandmaster Figma:** https://www.figma.com/design/Yx8ud7n39NdWZvnNvo4Xlf/Untitled · key `Yx8ud7n39NdWZvnNvo4Xlf` · page **12 Game UI**
**Essential UI board:** `Melodia/EssentialUI` (`69:767`)
**Depends on:** [MELODIA_LUXURY_UI_FILIGREE_NIKKI_MOTION_PLAN_2026-07-12.md](MELODIA_LUXURY_UI_FILIGREE_NIKKI_MOTION_PLAN_2026-07-12.md) · [ZUNDAMON_NPC_SPEC.md](ZUNDAMON_NPC_SPEC.md) · [scaffold_melodia_wbp_atoms.py](../Content/Python/scaffold_melodia_wbp_atoms.py) · [melodia_essential_ui_figma_20260716.md](../Saved/Audit/melodia_essential_ui_figma_20260716.md)
**Backing code:** `Plugins/MelodiaCore/Source/MelodiaCore/`

> Purpose: give an implementer a per-panel path from **Figma frame (node-id) → target WBP → composed atoms → concrete game data binding → sparkle/motion hookup → Desktop/Mobile handling**, plus the recommended first vertical slice and the decisions/blockers that must be resolved before any UMG is authored.

## Runtime authority correction — 2026-07-28

Live Monolith inspection supersedes parts of the older static inventory below:

- The working production loop uses `/Game/TurnBasedJRPGTemplate`, not the `_ThirdParty` duplicate.
- Stock save/load authority is `/Game/TurnBasedJRPGTemplate/Blueprints/Controllers/BP_JRPGGameInstance` plus `BP_JRPGSaveGame`.
- `/Game/MelodiaIntegration/Blueprints/BP_MelodiaJRPGGameInstance` extends that stock graph and calls `SyncNarrativeRecordToSave` immediately before `SaveGameToSlot`, then `RestoreNarrativeRecordFromSave` immediately after loading.
- `Config/DefaultEngine.ini` now selects `BP_MelodiaJRPGGameInstance` directly. The former configured `BP_MelodiaJRPGGameInstance_Config` was an empty child of the stock GameInstance and bypassed those integration hooks.
- `UMelodiaSaveGameSubsystem` is **not** the production gameplay save authority for this Persona-lite slice and must not be wired beside the JRPG save graph.
- Existing production UI assets include `WBP_MenuButton`, `WBP_Settings`, `WBP_ComicOrrery`, `WBP_QuestJournal`, `WBP_SkillCodex`, dialogue and battle widgets. Treat the older “no WBP assets” statement below as historical.
- Verified existing visual assets for the first soft-magical pass include `F_Syne`, `F_InstrumentSerif`, `F_Melodia_UI`, `T_Spark_Sparkle4`, `T_Spark_Twinkle8`, `T_Magic_Heart`, `T_Magic_Star`, and the `JRO_JP_Ornament*_Mask` family. Use masks/tints as reusable brushes; do not duplicate textures.

**Implementation order is now:** preserve the stock save graph → expose a thin menu-facing adapter on the integrated GameInstance → reuse menu atoms with existing fonts/ornament/sparkle textures → validate the dedicated front-end and active stock battle UI in PIE before widening persistence or combat scope.

**Front-end/active-UI update — 2026-07-28:** D1 is resolved. `/Game/Melodia/Levels/Menu/L_MelodiaMainMenu` uses `/Script/MelodiaCore.OrreryMainMenuGameMode`; the native host creates `WBP_MainMenu`, sets UI-only input/cursor, and focuses New Game without spawning gameplay state. Startup config points to this map. Runtime reference inspection selected the primary `/Game/TurnBasedJRPGTemplate` battle UI family, and the restrained Melodia/Kenney visual pass was applied only to its active child widgets. Headless targeted load/compile assertions passed for the menu and touched battle widgets. Continue/Load remain intentionally locked pending canonical save proof and a non-empty `WBP_SaveLoad`.

**Implemented first pass — 2026-07-28:** `WBP_MainMenu` uses existing Kenney fantasy borders plus Melodia fonts/colors, compiles `UpToDate`, and passes the accessibility audit with zero issues. Its graph now wires New Game to `OnNewGameStarted`, Continue to `LoadGame("L_MelusinaMorning")`, and Load Game to create/add `WBP_SaveLoad`. Continue and Load Game are deliberately disabled until a canonical `BP_JRPGSaveGame` slot and non-empty Save/Load screen pass PIE. `F_NotoMusic` is imported for notation-only text, not general menu copy.

---

## 0. Ground truth captured this pass

- **Figma is live on MCP.** Verified `get_metadata` on the board `69:767` and pulled `get_design_context` on `Game/MainMenu` (`70:767`). All node-ids below are from the live file, not repo guesses.
- **No WBP assets exist on disk yet.** `Content/Melodia/UI/` has zero `.uasset` (glob for `WBP_*.uasset` returns nothing). This is greenfield UMG — the scaffold script has only ever written its plan JSON. So every panel below is "author new WBP", not "edit existing".
- **The scaffold map already names the target WBPs** in [scaffold_melodia_wbp_atoms.py](../Content/Python/scaffold_melodia_wbp_atoms.py) (`WBP_ATOMS`), all under `/Game/Melodia/UI/`. This plan reuses those names as the target paths.
- **Design language (from live MainMenu context):** SoftMG parchment + Baroque filigree + pearl/gold/iri-cyan on void. Each Essential-UI panel embeds **both a Desktop 1440 variant and a Mobile 390 variant inside the same frame** (see MainMenu `70:853` "Desktop 1440 variant" + `70:855` "Mobile 390 variant").

### Design tokens (sampled from `Game/MainMenu` 70:767)

| Token | Value | Use |
|---|---|---|
| Void plate | `#0b0a13` | Frame background |
| Parchment field | `rgba(56,41,59,0.92)` | Inner field behind content |
| Parchment fill | `rgb(242,230,207)` → `rgb(227,211,173)` | `SoftMG/ParchmentPanel` gradient |
| Gold border / accent | `rgba(235,184,87,~0.7–0.9)` | Frame + button borders |
| Gold text | `#f2d69e` | Button labels, titles |
| Iri-cyan | `#78ebff` | Subtitles / accent text |
| Plum button | `rgba(77,46,61,0.95)` | Menu buttons + mobile chips |
| Ink | `#291a21` | Text on parchment cards |
| Card gold | `rgba(232,199,140,0.95)` | Melusina plate / teaser / save cards |
| Type | Syne / Instrument Serif / Bricolage / Azeret (page 01–02 tokens; `Inter` is the Figma placeholder) | see luxury plan A1 |

### Shared SoftMG / Baroque atoms (compose into every panel)

| Atom | Node | Role |
|---|---|---|
| `SoftMG/ParchmentPanel` | `62:531` | Tintable parchment base + clef watermark |
| `SoftMG/ScrollEdge` | `62:534` | Scroll border rail |
| `SoftMG/SealSP` | `63:531` | Ink-seal cartouche w/ fill track (SP) |
| `SoftMG/SealULT` | `63:537` | ULT seal variant |
| `SoftMG/LaneInk` | `64:531` | Highway lane ink |
| `SoftMG/Hitline` | `64:533` | Highway hitline |
| `SoftMG/PillowChip` | `64:536` | Soft skill-fill chip / item tile |
| `Game/FiligreeBatchO_Baroque` | `58:716` | Baroque filigree set (below) |
| — CornerBaroque | `58:606` | Corner scroll |
| — DividerScroll | `58:633` | Band divider |
| — CrestBaroque | `58:664` | Header crest |
| — MedallionRosette | `58:689` | Rosette accent |
| — BraceVolute | `58:704` | Brace/volute accent |

> **Guardrail:** SoftMG + Baroque only. Never instantiate `DEPRECATED/*` (Batch N MusicalFiligree/NoteGlyph/NoteBeam, Batch O Ornate). Do **not** edit `SheetMusicHUD` beauty frames (`45:480` Desktop, `46:499` Mobile) — the rhythm HUD beauty SSOT is frozen.

---

## 1. Figma panel inventory (node-ids for direct pull at build time)

Board `Melodia/EssentialUI` (`69:767`), rows A–E. Each `Game/*` node is a **component/symbol**; pull it with `get_design_context(nodeId, fileKey)` when authoring its WBP.

### Row A — P0 Flow shells (`69:770`)
| Panel | Node | Size | Notes |
|---|---|---|---|
| `Game/MainMenu` | `70:767` | 1440×900 | Desktop variant `70:853`, Mobile variant `70:855`. Buttons: Continue `70:857`, New `70:859`, Load `70:861`, Settings `70:863`, Credits `70:865`. Cards: Melusina plate `70:867`, Orrery teaser `70:869`, Latest save `70:871`, Event banner `70:873`. Mobile chips `70:875/877/879/881`. Sparkle dots `70:883–890`. |
| `Game/SaveLoad` | `70:901` | 1440×900 | Slot cards (empty/occupied/autosave), timestamp + location + measure stub |
| `Game/Settings` | `70:1033` | 1440×900 | Audio / Accessibility (`data-mg` full/soft/chrome/off) / Controls |

### Row B — Meta / narrative (`69:771`)
| Panel | Node | Size |
|---|---|---|
| `Game/ComicOrrery` | `71:1022` | 850×900 |
| `Game/QuestJournal` | `71:1110` | 850×900 |
| `Game/NPCInfo` | `71:1195` | 850×900 |
| `Game/Inventory` | `71:1280` | 850×900 |
| `Game/PartyLoadout` | `71:1375` | 850×900 |

### Row C — Battle / field elevate (`69:772`)
| Panel | Node | Size |
|---|---|---|
| `Game/BattleCommand` | `72:1302` | 620×900 |
| `Game/BattleEnemy` | `72:1393` | 620×900 |
| `Game/BattleResults` | `72:1485` | 620×900 |
| `Game/FieldHUD` | `72:1574` | 620×900 |
| `Game/Title` | `72:1663` | 620×900 |
| `Game/SkillCodex` | `72:1754` | 620×900 |
| `Game/DialogueOverlay` | `72:1843` | 620×900 |

### Row D — Sparkle FX atoms (`69:773`)
| Atom | Node | Beat/role |
|---|---|---|
| `Motion/SparkleBurst` | `72:2007` | Perfect / Break / ULT / Shrine burst |
| `Motion/SparkleDrift` | `72:2101` | Idle ambient drift |
| `Motion/OrrerySparkleOrbit` | `72:2165` | Comic Orrery select flourish |

Page 13: `MG/SparkleTierBudget` (`72:2284`) — density budget reference only (full/soft/chrome/off), no screens.

---

## 2. Game-side inventory (what exists to bind against)

All in `Plugins/MelodiaCore/Source/MelodiaCore/`. Key already-exposed surfaces:

| System | Class (file) | Kind | Exposed for UI |
|---|---|---|---|
| Save/Load | `UMelodiaSaveGameSubsystem` (`MelodiaSaveGameSubsystem.h`) | GameInstanceSubsystem | `Get(WCO)`, `SaveGame()`, `LoadGame()`, `HasSaveGame()`, `OnSaveCompleted`, `OnLoadCompleted`. Single slot `"MelusinaSlot0"` hardcoded. |
| Save data | `UMelodiaSaveGame` (`MelodiaSaveGame.h`) | USaveGame | `SaveSlotName`, `SavedAtUtc`, `SaveSystemVersion`, `OpeningPhase`, persistent party stats, **`ActivePartyIndex`**, **`PartyPawnTransforms`**, **`CurrentMapName`** (all `BlueprintReadOnly`) |
| Party swap | `UMelodiaPartySubsystem` (`MelodiaPartySubsystem.h`) | GameInstanceSubsystem | `PartyPawnClasses[]`, `ActiveIndex`, `RegisterPawn`, `SwitchToNext(PC)`, `GetActivePawn()`, `SetActiveIndex(idx, PC)` |
| Quests | `AMelodiaQuestManagerBase` (`MelodiaQuestManagerBase.h`) | **Actor** | `AcceptQuest`, `CompleteQuest`, `IsQuestActive`, `IsQuestCompleted`, `GetActiveQuests()`, `GetCompletedQuestIds()`, `OnQuestAccepted`, `OnQuestCompleted`. Def struct `FMelodiaQuestDef{QuestId, DisplayName, Description, RequiredLevel, RewardXP, RewardGold}` |
| NPC catalog | `UMelodiaNPCDataAsset` / `FMelodiaNPCDefinition` (`MelodiaNPCDefinition.h`) | DataAsset | `FindNPCById`, `GetNPCByIndex`, `GetNPCsByArchetype/Zone`, `GetDemoNPCs()`. NPC has DisplayName, Archetype, Description, portrait mesh, `InteractionConfig` (Dialogue/Shop/Quest/Battle), `AffinityRewards` |
| NPC runtime | `UMelodiaNPCInteractionComponent` (`MelodiaNPCInteractionComponent.h`) | ActorComponent | `SpeakerName`, `InteractionPrompt`, `DialogueLines[]`, `BeginInteraction`, `AdvanceInteraction`, `CancelInteraction`, `GetPromptText`, `HasDialogue`, `OnDialogueLine(Speaker,Line)`, `OnInteractionStarted/Finished` |
| Inventory / gold / XP | `UMelodiaProgressionComponent` (`MelodiaProgressionComponent.h`) | ActorComponent | `Level`, `CurrentXP`, `XPToNextLevel`, `Currency`, `Inventory[]` (`FMelodiaInventoryItem{ItemId, DisplayName, Quantity}`), `AddItem`, `HasItem`, `GetItemQuantity` |
| Battle session | `UMelodiaBattleSession` (`MelodiaBattleSession.h`) | GameInstanceSubsystem | phase machine, `EnemyHP/MaxHP`, `ActiveEnemyId`, `ActiveEnemyIntentName/Damage`, `ActiveEnemyBPM`, `SessionCombo/MaxCombo/Score`, persistent party block, `GetCombatState()`, `GetLastEncounterResult()`, submit* commands, `OnBattlePhaseChanged`, `OnEncounterEnded` |
| Combat state | `UMelodiaCombatStateComponent` (`MelodiaCombatStateComponent.h`) | ActorComponent | `SkillPoints/Max`, `UltimateGauge/Max/bReady`, `EnemyToughness/Max/bBroken`, `PartyHP/Max`, afflictions, modifiers |
| Battle HUD (desktop) | `UMelodiaRhythmHUDWidget` (`MelodiaRhythmHUDWidget.h`) | UserWidget (NativePaint) | `BlueprintNativeEvent` setters: `SetEnemyVitals`, `SetPartyVitals`, `SetSkillPoints`, `SetUltimateGauge`, `SetEnemyBreakGauge`, `SetNoteHighwayActive`, `ShowActionPrompt`, `SetBattlePhaseBanner`, `PushFloatingCombatText`, `TriggerDamageFlash`, `SetJudgment`, **`DoPulse`**, **`TriggerSparkleBurst`** |
| Battle HUD (mobile) | `UMelodiaMobileHUD` (`MelodiaMobileHUD.h`) | UserWidget | `BindWidgetOptional`: HighwayCanvas, ComboText, HPBar, SPBar, UltBar, EnemyNameText, EnemyHPBar, EnemyToughnessBar, GradePopupCanvas, GradeText; `LaneButtons[]` (EditAnywhere); `ForwardLaneTap`, `SetLaneHighlight`, `ShowGradePopup`, `UpdateCombo`, `UpdateResources` |
| Opening flow | `UMelodiaOpeningFlowSubsystem` (`MelodiaOpeningFlowSubsystem.h`) | GameInstanceSubsystem | phase enum, `IsFirstDungeonUnlocked`, `RestoreFromSave`, `ResetOpening` |
| HUD bootstrap | `AMelodiaGameMode` (`MelodiaGameMode.h`) | GameModeBase | `HUDWidgetClass`, `SpawnBattleHUD`, `RemoveBattleHUD`, loop phases Bootstrapping/Exploration/Battle/VictoryReward |

**Sparkle contract:** the naming to honor is `UMelodiaRhythmHUDWidget::TriggerSparkleBurst()` / `DoPulse()` (BlueprintNativeEvent). Meta/menu panels are plain `UUserWidget`, so their sparkle is UMG animation or a shared sparkle sub-widget, triggered by the same verb names for consistency.

---

## 3. Per-panel wiring plan

Format: **Figma → WBP (path) → composed atoms → data bindings → sparkle/motion → Desktop/Mobile**. `[NEW C++]` marks a binding that requires a getter/callable that does not exist yet (all collected in §4).

### 3.1 `Game/MainMenu` (`70:767`) → `WBP_MainMenu` (`/Game/Melodia/UI/WBP_MainMenu`)
- **Atoms:** ParchmentPanel `62:531`, CornerBaroque `58:606` (×2), CrestBaroque `58:664`, SealSP `63:531`, PillowChip `64:536`, sparkle dots.
- **Bindings:**
  - Continue `70:857` → `HasSaveGame()` gate → `LoadGame()` then `UGameplayStatics::OpenLevel(CurrentMapName)`.
  - New Game `70:859` → `UMelodiaOpeningFlowSubsystem::ResetOpening()` + OpenLevel(opening map).
  - Load Game `70:861` → open `WBP_SaveLoad`.
  - Settings `70:863` → open `WBP_Settings`.
  - Credits `70:865` → static credits view.
  - Latest-save card `70:871` → `[NEW C++]` slot summary (SavedAtUtc + CurrentMapName). Melusina plate `70:867` / Event banner `70:873` = static art for now.
- **Sparkle:** ambient `Motion/SparkleDrift` (`72:2101`) via UMG loop over sparkle dots.
- **Desktop/Mobile:** Desktop = full button column (`70:853` region); Mobile = chip column (`70:855`, chips `70:875–881`). One WBP, size-box/`WidgetSwitcher` on viewport aspect, or a `WBP_MainMenu_Mobile` child — recommend single WBP with a responsive switcher.
- **Precondition:** needs a front-end host (level + menu game mode/flow) — see §4 blocker D1.

### 3.2 `Game/SaveLoad` (`70:901`) → `WBP_SaveLoad`
- **Atoms:** ParchmentPanel, CornerBaroque, SealSP as slot seals, PillowChip as slot cards, DividerScroll `58:633`.
- **Bindings:**
  - Slot list → `[NEW C++]` `GetSaveSlotSummaries()` returning per-slot `{SlotName, SavedAtUtc, CurrentMapName, ActivePartyIndex, OpeningPhase, bAutosave, bOccupied}` (render timestamp + location + measure stub).
  - Save button → `SaveGameSubsystem::SaveGame()`; subscribe `OnSaveCompleted(bSuccess)` → refresh + sparkle.
  - Load button → `LoadGame()`; subscribe `OnLoadCompleted(bSuccess)` → OpenLevel(CurrentMapName).
  - Empty slot → New Game path.
- **Sparkle:** `Motion/SparkleBurst` (`72:2007`) on successful save/load.
- **Desktop/Mobile:** 3–4 slot cards in a grid (desktop) → single-column list (mobile).
- **Gap:** subsystem is single-slot (`MelusinaSlot0`); multi-slot cards need slot-name plumbing — see §4 blocker C1.

### 3.3 `Game/Settings` (`70:1033`) → `WBP_Settings`
- **Atoms:** ParchmentPanel, DividerScroll section rules, PillowChip toggles.
- **Bindings:** Audio (master/BGM/SFX), Accessibility → **`data-mg` tier full/soft/chrome/off** (drives sparkle density / motion tier), Controls remap.
- **Gap:** no settings persistence object exists (`GameUserSettings` wrapper or extend `UMelodiaSaveGame`) — see §4 blocker C4. The `data-mg` tier must feed a runtime value the sparkle widgets read.
- **Desktop/Mobile:** tabbed columns → stacked accordion.

### 3.4 `Game/ComicOrrery` (`71:1022`) → `WBP_ComicOrrery`
- **UI world-navigator** (comic-panel "world spheres": Sakura / Stage / Celestial / Village), NOT the 3D CosmicOrrery.
- **Bindings:** each sphere → `OpenLevel(MapName)`; write `CurrentMapName` via save flow on travel. Locked/unlocked state can gate on `UMelodiaOpeningFlowSubsystem::Phase` / `IsFirstDungeonUnlocked()`.
- **Gap:** no map registry (sphere → map name → unlock rule). Small data asset or hardcoded table — see §4 blocker C6.
- **Sparkle:** `Motion/OrrerySparkleOrbit` (`72:2165`) on select.

### 3.5 `Game/QuestJournal` (`71:1110`) → `WBP_QuestJournal`
- **Bindings:** Active list → `AMelodiaQuestManagerBase::GetActiveQuests()`; Completed → `GetCompletedQuestIds()`; subscribe `OnQuestAccepted/OnQuestCompleted`. Quest labels `Q_ZUN_001..005` from [ZUNDAMON_NPC_SPEC.md](ZUNDAMON_NPC_SPEC.md) / `DT_ZundamonQuests`.
- **Gaps:** (a) quest manager is an **Actor**, so UI needs a locator (`GetAllActorsOfClass` or promote to subsystem) — blocker C3a; (b) `FMelodiaQuestDef` has **no objectives array** and no "daily" category, but the design shows active/completed/daily + objective lists — blocker C3b; (c) no link from the manager to `DT_ZundamonQuests` — blocker C3c.

### 3.6 `Game/NPCInfo` (`71:1195`) → `WBP_NPCInfo`
- **Bindings:** portrait/name/description/archetype ← `FMelodiaNPCDefinition` via `UMelodiaNPCDataAsset::FindNPCById`. CTAs: Open Quest (→ QuestJournal / AcceptQuest), Shop (→ shop UI, `InteractionConfig.ShopInventory`), from `InteractionConfig.bQuestGiver` / `InteractionType`.
- **Gap:** relationship/affinity **current value** is not tracked at runtime (`AffinityRewards` are static defs only) — blocker C5.

### 3.7 `Game/DialogueOverlay` (`72:1843`) → `WBP_DialogueBubble`
- **Bindings (mostly ready):** `UMelodiaNPCInteractionComponent`: nameplate ← `SpeakerName`; bubble text ← `OnDialogueLine(Speaker, Line)` / `DialogueLines[]`; advance → `AdvanceInteraction()`; open/close via `OnInteractionStarted/Finished`; prompt ← `GetPromptText()`.
- **Choice row:** `DialogueLines` is a flat `TArray<FText>` — branching choices are not modeled — blocker C5b (optional for v1: linear dialogue works today).
- **Sparkle:** subtle `SparkleDrift` on nameplate.

### 3.8 `Game/Inventory` (`71:1280`) → `WBP_Inventory`
- **Bindings:** grid ← `UMelodiaProgressionComponent::Inventory[]` (`ItemId`, `DisplayName`, `Quantity`); currency ← `Currency`. Tiles = `SoftMG/PillowChip` `64:536`.
- **Gaps:** (a) `FMelodiaInventoryItem` has **no Category** field, but design shows charms/consumables/key tabs — blocker C7a; (b) `ProgressionComponent` lives on some actor (pawn?) — UI needs a locator — blocker C7b.

### 3.9 `Game/PartyLoadout` (`71:1375`) → `WBP_PartyLoadout`
- **Bindings:** slots ← `UMelodiaPartySubsystem` (`ActiveIndex`, `GetActivePawn()`); switch → `SetActiveIndex(idx, PC)` / `SwitchToNext(PC)`. Song-skill summary per member ← `MelodiaSongSkillLibrary` / equipped key (`EquippedKeyElement`).
- **Gap:** subsystem exposes only pawn **classes** + active index — no per-member **display metadata** (name, portrait, song-skill list) — blocker C2.

### 3.10 Battle / Field (`72:1302` Command · `72:1393` Enemy · `72:1485` Results · `72:1574` FieldHUD) → `WBP_Battle_Command` / `WBP_Battle_Enemy` / `WBP_Battle_Results` / `WBP_FieldHUD`
- **Bindings (already fully wired — lowest new-C++ cost):**
  - Enemy: `SetEnemyVitals(EnemyHP, EnemyMaxHP)`, `ActiveEnemyIntentName/Damage`, `SetEnemyBreakGauge(EnemyToughness…)`.
  - Party/resources: `SetPartyVitals`, `SetSkillPoints`, `SetUltimateGauge`.
  - Command: `SubmitBasicCommand/SubmitSkillCommand/SubmitUltimateCommand/SubmitFleeCommand` + `CanSubmit*` gates.
  - Results: `GetLastEncounterResult()`, `SessionScore/MaxCombo`.
  - Phase: `OnBattlePhaseChanged` → `SetBattlePhaseBanner`.
- These **elevate/reskin** the existing `UMelodiaRhythmHUDWidget` (desktop) and `UMelodiaMobileHUD` (mobile) rather than replacing them. Reuse the existing `HUDWidgetClass` bootstrap in `AMelodiaGameMode::SpawnBattleHUD`.
- **Sparkle:** native `TriggerSparkleBurst()` / `DoPulse()` on Perfect/Break/ULT.
- **Mobile:** `WBP_Battle_Mobile` (parent `UMelodiaMobileHUD`) per existing scaffold `MOBILE_AUTHORING` — 4 `LaneButtons`, BindWidgetOptional set, thumb zone bottom ~42%.

### 3.11 `Game/Title` (`72:1663`) → `WBP_Title`, `Game/SkillCodex` (`72:1754`) → `WBP_SkillCodex`
- Title = display-only splash → routes into MainMenu.
- SkillCodex ← `MelodiaSongSkillLibrary` skill defs (display-mostly; confirm a BlueprintPure catalog getter exists, else small getter).

### 3.12 Sparkle atoms (Row D) → shared `WBP_Sparkle*` sub-widgets
- `Motion/SparkleBurst` `72:2007`, `SparkleDrift` `72:2101`, `OrrerySparkleOrbit` `72:2165` → reusable UMG widgets driven by the `data-mg` tier from Settings; invoked with the `TriggerSparkleBurst`/`DoPulse` verb contract so web/UE naming matches.

---

## 4. Panel → WBP → binding summary + gaps

| Figma panel (node) | Target WBP | Primary binding (system) | New C++ needed? |
|---|---|---|---|
| MainMenu `70:767` | `WBP_MainMenu` | SaveGameSubsystem + OpeningFlow + OpenLevel | D1 front-end host; C1 slot summary |
| SaveLoad `70:901` | `WBP_SaveLoad` | `UMelodiaSaveGameSubsystem` Save/Load + delegates | **C1** slot summary + multi-slot |
| Settings `70:1033` | `WBP_Settings` | settings store + `data-mg` tier | **C4** settings persistence + tier value |
| ComicOrrery `71:1022` | `WBP_ComicOrrery` | OpenLevel + OpeningFlow phase | **C6** map/unlock registry |
| QuestJournal `71:1110` | `WBP_QuestJournal` | `AMelodiaQuestManagerBase` | **C3** locator + objectives + DT link |
| NPCInfo `71:1195` | `WBP_NPCInfo` | `UMelodiaNPCDataAsset` / interaction | **C5** runtime affinity |
| DialogueOverlay `72:1843` | `WBP_DialogueBubble` | `UMelodiaNPCInteractionComponent` | none for linear; C5b for choices |
| Inventory `71:1280` | `WBP_Inventory` | `UMelodiaProgressionComponent` | **C7** item category + locator |
| PartyLoadout `71:1375` | `WBP_PartyLoadout` | `UMelodiaPartySubsystem` | **C2** roster display getter |
| BattleCommand `72:1302` | `WBP_Battle_Command` | `UMelodiaBattleSession` submit* | none (exposed) |
| BattleEnemy `72:1393` | `WBP_Battle_Enemy` | RhythmHUD `SetEnemyVitals`/Break | none (exposed) |
| BattleResults `72:1485` | `WBP_Battle_Results` | `GetLastEncounterResult`/Session* | none (exposed) |
| FieldHUD `72:1574` | `WBP_FieldHUD` | RhythmHUD party/resource setters | none (exposed) |
| Title `72:1663` | `WBP_Title` | menu route | D1 |
| SkillCodex `72:1754` | `WBP_SkillCodex` | `MelodiaSongSkillLibrary` | verify catalog getter |
| Sparkle `72:2007/2101/2165` | `WBP_Sparkle*` | `data-mg` tier + verb contract | none |

### New C++ (BlueprintCallable / exposed getters) to add before/with each panel
- **C1 — Save slot summary + multi-slot.** Add `FMelodiaSaveSlotInfo` struct and `UMelodiaSaveGameSubsystem::GetSaveSlotSummaries()` (peek headers without full load) + parameterize slot name (`SaveGame(SlotName)` / `LoadGame(SlotName)`) so Save/Load can show 3–4 cards. *(Blocks MainMenu "Latest save" + SaveLoad.)*
- **C2 — Party roster display.** Add a getter on `UMelodiaPartySubsystem` (or a `UMelodiaPartyMemberData` asset) returning `{DisplayName, Portrait, SongSkillSummary, bActive}` per index.
- **C3 — Quest journal access.** (a) locator: promote `AMelodiaQuestManagerBase` to a subsystem **or** provide `Get(WCO)`; (b) add `Objectives` to `FMelodiaQuestDef` + a `daily` category; (c) hydrate manager from `DT_ZundamonQuests`.
- **C4 — Settings persistence + tier.** A settings store (`UGameUserSettings` subclass or fields on `UMelodiaSaveGame`) and a runtime-readable `EMelodiaMotionTier` (full/soft/chrome/off) the sparkle widgets consume.
- **C5 — NPC affinity runtime.** Track current affinity per NPC (subsystem or save field); optional C5b: model dialogue **choices** (branching) beyond flat `DialogueLines`.
- **C6 — Orrery map registry.** Data asset mapping world-sphere → map name → unlock rule.
- **C7 — Inventory category + locator.** Add `Category` (charms/consumables/key) to `FMelodiaInventoryItem`; expose a locator/getter to reach the owning `UMelodiaProgressionComponent`.

### Decisions/blockers needing the user before implementation
- **D1 — Front-end shell.** There is no menu level or front-end GameMode/flow controller today (only `AMelodiaGameMode` for battle). Decide: dedicated front-end map + menu game mode, or an overlay menu on the existing world. MainMenu/Title depend on this.
- **D2 — Save model scope.** Multi-slot Save/Load (design shows 3–4 slots + autosave) vs the current deliberate single narrow slot. Confirm we may widen slot handling (C1).
- **D3 — Quest source of truth.** Is `DT_ZundamonQuests` the runtime quest source, and do we add objectives/daily now or defer (C3)?
- **D4 — Responsive strategy.** One WBP per panel with a Desktop/Mobile `WidgetSwitcher`, or separate `_Mobile` WBPs (matching the existing `WBP_Battle_Mobile` split)? Recommend single WBP + switcher for the meta panels, separate for battle (mobile already has its own C++ parent).
- **D5 — Type/asset pipeline.** Figma uses `Inter` as placeholder; real type is Syne / Instrument Serif / Bricolage / Azeret. Confirm fonts are imported to UE and confirm the SoftMG/Baroque PNGs are reimported (Pass L3 "Reimport Batch O atlas" is still unchecked in the luxury plan).

---

## 5. Recommended build sequence

**First vertical slice: `Game/SaveLoad` (`70:901`) → `WBP_SaveLoad`, bound to `UMelodiaSaveGameSubsystem`.**

Why this proves the pipeline end-to-end, high-value + low-risk:
- It exercises a **real read *and* write** against a live subsystem (`SaveGame()` / `LoadGame()` + `OnSaveCompleted`/`OnLoadCompleted` delegates), not just static display — the strongest single proof that Figma-frame → WBP → MelodiaCore data actually round-trips.
- The backing subsystem is **already fully `BlueprintCallable`**; the only new C++ is one small, well-scoped addition (C1 slot summary + slot-name), which doubles as the reference pattern for every other "needs a getter" panel.
- It directly touches the systems the task names (save subsystem, `ActivePartyIndex`, `CurrentMapName`).
- Sparkle hookup is trivial (`SparkleBurst` on save success), validating the motion contract.

Author it behind a **minimal `WBP_MainMenu` shell** so it is reachable (Load Game → SaveLoad), which also stands up the front-end host (D1) once, cheaply.

**Then, in dependency order:**
1. **Save/Load** (slice) + **C1**.
2. **Main Menu** shell (**D1**) — hosts Save/Load, Settings, Continue/New; Continue/Load reuse C1.
3. **Settings** (**C4**) — needed so the `data-mg` motion tier exists before sparkle is wired broadly.
4. **Battle/Field HUD elevation** (Command/Enemy/Results/FieldHUD) — **no new C++**; reskins the already-bound `UMelodiaRhythmHUDWidget` + `UMelodiaMobileHUD`. High visual payoff, lowest risk; can run in parallel with 3.
5. **Party Loadout** (**C2**) — depends on `UMelodiaPartySubsystem` display exposure.
6. **Quest Journal** (**C3**) — locator + objectives.
7. **NPC Info** + **Dialogue Overlay** (**C5**) — dialogue is near-ready; affinity is the add.
8. **Inventory** (**C7**).
9. **Comic Orrery** (**C6**) — map registry + travel.
10. **Title** + **Skill Codex** — display-mostly, last.
- **Sparkle atoms** (Row D) authored as shared sub-widgets alongside step 3–4 and reused everywhere via the `TriggerSparkleBurst`/`DoPulse` verb contract.

---

## 6. Guardrails honored this pass
- Read-only: no live UE editor touched, no WBP created, no git commit.
- Figma read via MCP only (`get_metadata` + one `get_design_context`).
- No Blender saves, no Melusina/stage edits, no material clears (melusina-no-stomp).
- SoftMG + Baroque only; no `DEPRECATED/*`; SheetMusicHUD beauty frames untouched.

---

## 7. Row F — First-Slice Essentials (desktop) wiring (2026-07-17)

Focused desktop pass for the documented [first 20-minute vertical slice](MELODIA_FIRST_20_MINUTES_VERTICAL_SLICE.md). Board `Melodia/EssentialUI` row `Row F` = `79:1783`. Node audit: [melodia_essential_ui_rowF_20260717.md](../Saved/Audit/melodia_essential_ui_rowF_20260717.md). The full JRPG suite (Shop/Bestiary/CharacterStatus/WorldMap/Crafting/Achievements/Party/Inventory) is **deferred** per the slice doc's deferral list.

| Figma panel (node) | Target WBP | Primary binding (system) | New C++ needed? |
|---|---|---|---|
| `Ctrl/MenuButton` `81:1795` | `WBP_MenuButton` | reusable button; States=Default/Hover/Pressed/Disabled | none |
| `Game/BlessingBurden` `82:1783` | `WBP_BlessingBurden` | recursive-expedition contract (`RunSeed`+`DoorwayID`+`DissonanceTier`); Room A choice applies one boon + one cost modifier | **F1** run/reward choice API (apply blessing+burden modifiers, record seed) |
| `Game/IntensityWarning` `84:1853` | `WBP_IntensityWarning` | `DA_DissonanceProfile.Accessibility` (reduced-distortion + intensity/flash), motion tier `data-mg` full/soft/chrome/off | **F2** settings tier value (shared with C4) + gate before first Rupture |
| `Game/DissonanceBanner` `85:1857` | `WBP_DissonanceBanner` | `UMelodiaDissonanceSubsystem` Tier (Clear/Strain/Rupture) | **F3** dissonance tier getter + `OnDissonanceChanged` |
| `Game/ResonanceBond` `86:1857` | `WBP_ResonanceBond` | Sir Melodious `ResonanceBond` state (Absent/Reunited/Resonant/Strained) + potency; Perfect/Break flourish | **F4** ResonanceBond state (subsystem or companion component) |

### New C++ (BlueprintCallable / exposed) for the slice
- **F1 — Expedition choice.** Getter for the offered blessing/burden pair + a `CommitDoorwayChoice(BlessingId, BurdenId)` that applies modifiers and records `RunSeed`/`DoorwayID`/`DissonanceTier` (same-seed replay contract).
- **F2 — Motion/accessibility tier.** Runtime-readable `EMelodiaMotionTier` (full/soft/chrome/off) + reduced-distortion + intensity-warning flags the sparkle/post-process widgets consume; the warning modal must gate the first Rupture transition.
- **F3 — Dissonance tier.** `UMelodiaDissonanceSubsystem` getter returning current `Tier` + `OnDissonanceChanged` delegate for the banner.
- **F4 — Resonance bond.** Current bond state + potency (0–1) for Sir Melodious, and the Perfect/Break flourish trigger hook.

### Recommended first slice-UI implementation order
1. `WBP_MenuButton` (no C++) — unblocks all menu authoring.
2. `WBP_DissonanceBanner` + `WBP_ResonanceBond` (display-mostly; F3/F4 are small getters) — highest readability payoff for the slice.
3. `WBP_IntensityWarning` (F2) — required accessibility gate before Rupture.
4. `WBP_BlessingBurden` (F1) — the one meta screen the slice needs, exercises the expedition contract end-to-end.
