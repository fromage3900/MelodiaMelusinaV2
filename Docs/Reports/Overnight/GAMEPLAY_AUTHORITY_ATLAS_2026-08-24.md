# Gameplay Authority Atlas — 2026-08-24

**Scope:** static AST/text parse only. No Unreal/Monolith/Blender/network/AWS execution. No .uasset parsing. Paths normalized, timestamps omitted, deterministic JSON.

**Read-only inputs:** `Source/BS_GodFile/MelodiaIntegration/**`, `Source/BS_GodFile/Piano/**`, `Plugins/MelodiaCore/**`, `Plugins/MelodiaWardrobe/**`, `Plugins/QuillScript/**`, `Content/Python/gmm/**`, `Tools/**`, `specs/**`.

**Counts:** nodes=1270 edges=1391 sccs=1249 cycles=6

Static reachability is not runtime proof - see tiers below.

## 1. Source Presence vs Static Reachability vs Runtime Proof

| Evidence Tier | Meaning | Example |
|---|---|---|
| **Source presence** | File exists on disk, parses | `Source/.../MelodiaNarrativeSubsystem.h:1` |
| **Static reachability** | Import/include edge from known entry point (AST) | `HandleQuillNotification` dispatch table, `CreateWidget` call site, `OnPatternCompleted` binding |
| **Runtime proof** | Observed in PIE/package with ledger row. **Atlas never claims this without live evidence.** All runtime claims are `LIVE_EVIDENCE_REQUIRED` | `mem:// ledger` |

This atlas separates the three. Static edges are not runtime. See per-node `runtime_reachability` for tier.

## 2. Authority Distinctions (explicit)

| Surface | Canonical Owner | Adapter/Presentation | Prototype/Authoring Overlap | Verdict |
|---|---|---|---|---|
| **QuillScript narrative** | `Plugins/QuillScript` (`UQuillscriptSubsystem`) | `UMelodiaNarrativeSubsystem` (sole 7-verb bridge) | `Content/Python/gmm/ui/commands.py` quill-like verbs are Python prototype, not shipping authority | CANONICAL vs ADAPTER vs PROTOTYPE |
| **Stock JRPG battle/party/inventory/save** | TurnBased template: `BP_BattleController`, `BP_JRPGSaveGame`, `MelodiaSaveSlotLibrary` (adapter) | `UMelodiaExternalJRPGBridgeSubsystem` (narrow reflection), `MelodiaJRPGPartyBootstrapSubsystem` (bootstrap) | `gmm/game/battle_manager.py`, `player_state.py`, `save_manager.py` are standalone Python prototype authority competing with stock | CANONICAL vs ADAPTER vs PROTOTYPE/MERGE |
| **MelodiaIntegration rhythm & bridge seams** | `UMelodiaRhythmCombatSubsystem` + `UMelodiaMusicClockSubsystem` (Harmonix/Quartz) | `MelodiaJRPGPresentationRhythmComponent` (presentation), `MelodiaNarrativeSubsystem` bridge, `MelodiaExternalJRPGBridgeSubsystem` | `rhythm_clock.py`, `MelodiaRhythmExecutionComponent`, `MelodiaBattleInputComponent` are dead/prototype paths | CANONICAL vs PRESENTATION vs DEAD_CANDIDATE |
| **MelodiaWardrobe ownership** | `UMelodiaWardrobeSubsystem` (`Plugins/MelodiaWardrobe`) + catalog contract | `UMelodiaWardrobeComponent` (pawn mirror), `MelodiaWardrobeGachaSubsystem` (acquisition adapter) | `UMelodiaOutfitComponent` (dead), GMM wardrobe drafts are prototype | CANONICAL vs ADAPTER vs DEAD_CANDIDATE |
| **Presentation-only MelodiaCore surfaces** | None — presentation only by phase | `MelodiaAudioReactivePresentationSubsystem`, `MelodiaRhythmReactivitySubsystem`, `MelodiaUIBridgeSubsystem` (canonical for widget lifecycle but presentation bus for MPC), `Material` masters | `Tools/BlenderAddons/melodia_*` authoring | PRESENTATION vs AUTHORING |
| **GMM prototype/authoring overlap** | No shipping authority | `Tools/**`, `specs/**`, `Content/Python/envui`, `init_unreal.py` are authoring | `Content/Python/gmm/**` is prototype that overlaps all production authorities | PROTOTYPE/AUTHORING isolated |

## 3. Domain Grouping

### narrative — QuillScript; UMelodiaNarrativeSubsystem is the sole integration seam

Nodes: 107 — adapter:11, canonical:96

| path | symbol | role | verdict | confidence | runtime_reachability | citation |
|---|---|---|---|---|---|---|
| Plugins/MelodiaWardrobe/Source/MelodiaWardrobe/Public/MelodiaWardrobeSubsystem.h | UMelodiaNarrativeSubsystem | adapter | ADAPTER | 1.0 | source-present only | Plugins/MelodiaWardrobe/Source/MelodiaWardrobe/Public/MelodiaWardrobeSubsystem.h:16 |
| Plugins/QuillScript/Quillscript.uplugin | Quillscript | canonical | OWNER | 0.99 | source-present only | Plugins/QuillScript/Quillscript.uplugin:5 |
| Plugins/QuillScript/Source/Quillscript/Private/Core/QuillscriptAsset.cpp | QuillscriptAsset | canonical | OWNER | 0.99 | source-present only | Plugins/QuillScript/Source/Quillscript/Private/Core/QuillscriptAsset.cpp:3 |
| Plugins/QuillScript/Source/Quillscript/Private/Core/QuillscriptInterpreter.cpp | given | canonical | OWNER | 0.99 | static-reachable via CreateWidget | Plugins/QuillScript/Source/Quillscript/Private/Core/QuillscriptInterpreter.cpp:103 |
| Plugins/QuillScript/Source/Quillscript/Private/Core/QuillscriptNetwork.cpp | QuillscriptNetwork | canonical | OWNER | 0.99 | source-present only | Plugins/QuillScript/Source/Quillscript/Private/Core/QuillscriptNetwork.cpp:3 |
| Plugins/QuillScript/Source/Quillscript/Private/Core/QuillscriptSettings.cpp | QuillscriptSettings | canonical | OWNER | 0.99 | source-present only | Plugins/QuillScript/Source/Quillscript/Private/Core/QuillscriptSettings.cpp:3 |
| Plugins/QuillScript/Source/Quillscript/Private/Core/QuillscriptSubsystem.cpp | QuillscriptSubsystem | canonical | OWNER | 0.99 | source-present only | Plugins/QuillScript/Source/Quillscript/Private/Core/QuillscriptSubsystem.cpp:3 |
| Plugins/QuillScript/Source/Quillscript/Private/Quillscript.cpp | Quillscript | canonical | OWNER | 0.99 | static-reachable via CreateWidget | Plugins/QuillScript/Source/Quillscript/Private/Quillscript.cpp:3 |
| Plugins/QuillScript/Source/Quillscript/Private/Text/SmartTextBlock.cpp | SmartTextBlock | canonical | OWNER | 0.99 | source-present only | Plugins/QuillScript/Source/Quillscript/Private/Text/SmartTextBlock.cpp:3 |
| Plugins/QuillScript/Source/Quillscript/Private/Text/SmartTextBlockDecorator.cpp | SmartTextBlockDecorator | canonical | OWNER | 0.99 | source-present only | Plugins/QuillScript/Source/Quillscript/Private/Text/SmartTextBlockDecorator.cpp:3 |
| Plugins/QuillScript/Source/Quillscript/Private/Text/SmartTextDecorator.cpp | SmartTextDecorator | canonical | OWNER | 0.99 | static-reachable via CreateWidget | Plugins/QuillScript/Source/Quillscript/Private/Text/SmartTextDecorator.cpp:3 |
| Plugins/QuillScript/Source/Quillscript/Private/Text/SmartTypewriter.cpp | SmartTypewriter | canonical | OWNER | 0.99 | source-present only | Plugins/QuillScript/Source/Quillscript/Private/Text/SmartTypewriter.cpp:3 |
| Plugins/QuillScript/Source/Quillscript/Private/Utils/Evaluator.cpp | Evaluator | canonical | OWNER | 0.99 | source-present only | Plugins/QuillScript/Source/Quillscript/Private/Utils/Evaluator.cpp:3 |
| Plugins/QuillScript/Source/Quillscript/Private/Utils/Lexer.cpp | Lexer | canonical | OWNER | 0.99 | source-present only | Plugins/QuillScript/Source/Quillscript/Private/Utils/Lexer.cpp:3 |
| Plugins/QuillScript/Source/Quillscript/Private/Utils/Quill.cpp | Quill | canonical | OWNER | 0.99 | source-present only | Plugins/QuillScript/Source/Quillscript/Private/Utils/Quill.cpp:3 |
| Plugins/QuillScript/Source/Quillscript/Private/Utils/Tools.cpp | method | canonical | OWNER | 0.99 | source-present only | Plugins/QuillScript/Source/Quillscript/Private/Utils/Tools.cpp:644 |
| Plugins/QuillScript/Source/Quillscript/Private/Widgets/BackgroundBox.cpp | BackgroundBox | canonical | OWNER | 0.99 | source-present only | Plugins/QuillScript/Source/Quillscript/Private/Widgets/BackgroundBox.cpp:3 |
| Plugins/QuillScript/Source/Quillscript/Private/Widgets/DialogBox.cpp | DialogBox | canonical | OWNER | 0.99 | source-present only | Plugins/QuillScript/Source/Quillscript/Private/Widgets/DialogBox.cpp:3 |
| Plugins/QuillScript/Source/Quillscript/Private/Widgets/SelectionBox.cpp | SelectionBox | canonical | OWNER | 0.99 | source-present only | Plugins/QuillScript/Source/Quillscript/Private/Widgets/SelectionBox.cpp:3 |
| Plugins/QuillScript/Source/Quillscript/Private/Widgets/SpriteBox.cpp | SpriteBox | canonical | OWNER | 0.99 | source-present only | Plugins/QuillScript/Source/Quillscript/Private/Widgets/SpriteBox.cpp:3 |
| Plugins/QuillScript/Source/Quillscript/Public/Base/Directory.h | EDirectory | canonical | OWNER | 0.99 | source-present only | Plugins/QuillScript/Source/Quillscript/Public/Base/Directory.h:12 |
| Plugins/QuillScript/Source/Quillscript/Public/Base/EvaluatedOption.h | EvaluatedOption | canonical | OWNER | 0.99 | source-present only | Plugins/QuillScript/Source/Quillscript/Public/Base/EvaluatedOption.h:6 |
| Plugins/QuillScript/Source/Quillscript/Public/Base/Expression.h | Expression | canonical | OWNER | 0.99 | source-present only | Plugins/QuillScript/Source/Quillscript/Public/Base/Expression.h:6 |
| Plugins/QuillScript/Source/Quillscript/Public/Base/History.h | UQuillscriptAsset | canonical | OWNER | 0.99 | source-present only | Plugins/QuillScript/Source/Quillscript/Public/Base/History.h:10 |
| Plugins/QuillScript/Source/Quillscript/Public/Base/InputMode.h | EInputMode | canonical | OWNER | 0.99 | source-present only | Plugins/QuillScript/Source/Quillscript/Public/Base/InputMode.h:12 |
| Plugins/QuillScript/Source/Quillscript/Public/Base/InstructionType.h | InstructionType | canonical | OWNER | 0.99 | source-present only | Plugins/QuillScript/Source/Quillscript/Public/Base/InstructionType.h:8 |
| Plugins/QuillScript/Source/Quillscript/Public/Base/InterpreterState.h | InterpreterState | canonical | OWNER | 0.99 | source-present only | Plugins/QuillScript/Source/Quillscript/Public/Base/InterpreterState.h:6 |
| Plugins/QuillScript/Source/Quillscript/Public/Base/MultiplayerMode.h | EMultiplayerMode | canonical | OWNER | 0.99 | source-present only | Plugins/QuillScript/Source/Quillscript/Public/Base/MultiplayerMode.h:12 |
| Plugins/QuillScript/Source/Quillscript/Public/Base/MultiplayerSelectionMode.h | EMultiplayerSelectionMode | canonical | OWNER | 0.99 | source-present only | Plugins/QuillScript/Source/Quillscript/Public/Base/MultiplayerSelectionMode.h:12 |
| Plugins/QuillScript/Source/Quillscript/Public/Base/Operator.h | EOperator | canonical | OWNER | 0.99 | source-present only | Plugins/QuillScript/Source/Quillscript/Public/Base/Operator.h:12 |
| Plugins/QuillScript/Source/Quillscript/Public/Base/Permission.h | EPermission | canonical | OWNER | 0.99 | source-present only | Plugins/QuillScript/Source/Quillscript/Public/Base/Permission.h:14 |
| Plugins/QuillScript/Source/Quillscript/Public/Base/Picker.h | EPicker | canonical | OWNER | 0.99 | source-present only | Plugins/QuillScript/Source/Quillscript/Public/Base/Picker.h:12 |
| Plugins/QuillScript/Source/Quillscript/Public/Base/PrintType.h | EPrintType | canonical | OWNER | 0.99 | source-present only | Plugins/QuillScript/Source/Quillscript/Public/Base/PrintType.h:12 |
| Plugins/QuillScript/Source/Quillscript/Public/Base/SaveState.h | SaveState | canonical | OWNER | 0.99 | source-present only | Plugins/QuillScript/Source/Quillscript/Public/Base/SaveState.h:10 |
| Plugins/QuillScript/Source/Quillscript/Public/Base/ScriptIdMethod.h | EScriptIdMethod | canonical | OWNER | 0.99 | source-present only | Plugins/QuillScript/Source/Quillscript/Public/Base/ScriptIdMethod.h:12 |
| Plugins/QuillScript/Source/Quillscript/Public/Base/ScriptSettings.h | AQuillscriptInterpreter | canonical | OWNER | 1.0 | source-present only | Plugins/QuillScript/Source/Quillscript/Public/Base/ScriptSettings.h:26 |
| Plugins/QuillScript/Source/Quillscript/Public/Base/SettingsFile.h | ESettingsFile | canonical | OWNER | 0.99 | source-present only | Plugins/QuillScript/Source/Quillscript/Public/Base/SettingsFile.h:12 |
| Plugins/QuillScript/Source/Quillscript/Public/Base/SoundState.h | SoundState | canonical | OWNER | 0.99 | source-present only | Plugins/QuillScript/Source/Quillscript/Public/Base/SoundState.h:6 |
| Plugins/QuillScript/Source/Quillscript/Public/Base/Statement.h | Statement | canonical | OWNER | 0.99 | source-present only | Plugins/QuillScript/Source/Quillscript/Public/Base/Statement.h:6 |
| Plugins/QuillScript/Source/Quillscript/Public/Base/StatementType.h | EStatementType | canonical | OWNER | 0.99 | source-present only | Plugins/QuillScript/Source/Quillscript/Public/Base/StatementType.h:12 |
| Plugins/QuillScript/Source/Quillscript/Public/Base/TooltipTextStyle.h | TooltipTextStyle | canonical | OWNER | 0.99 | source-present only | Plugins/QuillScript/Source/Quillscript/Public/Base/TooltipTextStyle.h:8 |
| Plugins/QuillScript/Source/Quillscript/Public/Base/VerbosityMode.h | EVerbosityMode | canonical | OWNER | 0.99 | source-present only | Plugins/QuillScript/Source/Quillscript/Public/Base/VerbosityMode.h:12 |
| Plugins/QuillScript/Source/Quillscript/Public/Core/QuillscriptAsset.h | final | canonical | OWNER | 0.99 | source-present only | Plugins/QuillScript/Source/Quillscript/Public/Core/QuillscriptAsset.h:20 |
| Plugins/QuillScript/Source/Quillscript/Public/Core/QuillscriptInterpreter.h | AQuillscriptInterpreter | canonical | OWNER | 1.0 | source-present only | Plugins/QuillScript/Source/Quillscript/Public/Core/QuillscriptInterpreter.h:23 |
| Plugins/QuillScript/Source/Quillscript/Public/Core/QuillscriptNetwork.h | AQuillscriptNetwork | canonical | OWNER | 0.99 | source-present only | Plugins/QuillScript/Source/Quillscript/Public/Core/QuillscriptNetwork.h:13 |
| Plugins/QuillScript/Source/Quillscript/Public/Core/QuillscriptSettings.h | final | canonical | OWNER | 0.99 | source-present only | Plugins/QuillScript/Source/Quillscript/Public/Core/QuillscriptSettings.h:18 |
| Plugins/QuillScript/Source/Quillscript/Public/Core/QuillscriptSubsystem.h | AQuillscriptInterpreter | canonical | OWNER | 1.0 | source-present only | Plugins/QuillScript/Source/Quillscript/Public/Core/QuillscriptSubsystem.h:12 |
| Plugins/QuillScript/Source/Quillscript/Public/Quillscript.h | final | canonical | OWNER | 0.99 | source-present only | Plugins/QuillScript/Source/Quillscript/Public/Quillscript.h:11 |
| Plugins/QuillScript/Source/Quillscript/Public/Text/SmartTextBlock.h | USmartTextBlock | canonical | OWNER | 0.99 | source-present only | Plugins/QuillScript/Source/Quillscript/Public/Text/SmartTextBlock.h:13 |
| Plugins/QuillScript/Source/Quillscript/Public/Text/SmartTextBlockDecorator.h | USmartTextBlockDecorator | canonical | OWNER | 0.99 | source-present only | Plugins/QuillScript/Source/Quillscript/Public/Text/SmartTextBlockDecorator.h:11 |
| ... 57 more ... | | | | | | |

### battle — TurnBased JRPG template (turns, targeting, damage, results)

Nodes: 14 — adapter:1, canonical:9, merge:4

| path | symbol | role | verdict | confidence | runtime_reachability | citation |
|---|---|---|---|---|---|---|
| Content/TurnBasedJRPGTemplate/Blueprints/Battle/BP_BattleController.uasset | BP_BattleController | canonical | OWNER | 1.0 | source-present only | Content/TurnBasedJRPGTemplate/Blueprints/Battle/BP_BattleController.uasset:1 |
| Plugins/MelodiaCore/Source/MelodiaCore/MelodiaBattleSession.cpp | MelodiaBattleSession | merge | MERGE | 0.99 | source-present only | Plugins/MelodiaCore/Source/MelodiaCore/MelodiaBattleSession.cpp:4 |
| Plugins/MelodiaCore/Source/MelodiaCore/MelodiaBattleSession.h | UMelodiaBattleSession | merge | MERGE | 1.0 | source-present only | Plugins/MelodiaCore/Source/MelodiaCore/MelodiaBattleSession.h:59 |
| Plugins/MelodiaCore/Source/MelodiaCore/MelodiaDungeonRunCoordinator.h | UMelodiaBattleSession | merge | MERGE | 1.0 | source-present only | Plugins/MelodiaCore/Source/MelodiaCore/MelodiaDungeonRunCoordinator.h:12 |
| Plugins/MelodiaCore/Source/MelodiaCore/MelodiaMinimalHUD.h | UMelodiaBattleSession | merge | MERGE | 1.0 | source-present only | Plugins/MelodiaCore/Source/MelodiaCore/MelodiaMinimalHUD.h:11 |
| Source/BS_GodFile/MelodiaIntegration/MelodiaBattleInteractionTrigger.cpp | MelodiaBattleInteractionTrigger | canonical | OWNER | 0.99 | source-present only | Source/BS_GodFile/MelodiaIntegration/MelodiaBattleInteractionTrigger.cpp:1 |
| Source/BS_GodFile/MelodiaIntegration/MelodiaBattleInteractionTrigger.h | UBoxComponent | canonical | OWNER | 0.99 | source-present only | Source/BS_GodFile/MelodiaIntegration/MelodiaBattleInteractionTrigger.h:7 |
| Source/BS_GodFile/MelodiaIntegration/MelodiaBattleKeyboardLegendWidget.cpp | MelodiaBattleKeyboardLegendWidget | canonical | OWNER | 0.99 | source-present only | Source/BS_GodFile/MelodiaIntegration/MelodiaBattleKeyboardLegendWidget.cpp:1 |
| Source/BS_GodFile/MelodiaIntegration/MelodiaBattleKeyboardLegendWidget.h | UFont | canonical | OWNER | 0.99 | source-present only | Source/BS_GodFile/MelodiaIntegration/MelodiaBattleKeyboardLegendWidget.h:7 |
| Source/BS_GodFile/MelodiaIntegration/MelodiaBattleMapConfig.cpp | MelodiaBattleMapConfig | canonical | OWNER | 0.99 | source-present only | Source/BS_GodFile/MelodiaIntegration/MelodiaBattleMapConfig.cpp:1 |
| Source/BS_GodFile/MelodiaIntegration/MelodiaBattleMapConfig.h | UBattleMapConfig | canonical | OWNER | 0.99 | source-present only | Source/BS_GodFile/MelodiaIntegration/MelodiaBattleMapConfig.h:28 |
| Source/BS_GodFile/MelodiaIntegration/MelodiaExternalJRPGBridgeSubsystem.cpp | MelodiaExternalJRPGBridgeSubsystem | adapter | ADAPTER | 0.99 | source-present only | Source/BS_GodFile/MelodiaIntegration/MelodiaExternalJRPGBridgeSubsystem.cpp:1 |
| Source/BS_GodFile/MelodiaIntegration/MelodiaJRPGPostBattleLibrary.cpp | loaded | canonical | OWNER | 0.99 | source-present only | Source/BS_GodFile/MelodiaIntegration/MelodiaJRPGPostBattleLibrary.cpp:40 |
| Source/BS_GodFile/MelodiaIntegration/MelodiaJRPGPostBattleLibrary.h | UMelodiaJRPGPostBattleLibrary | canonical | OWNER | 0.99 | source-present only | Source/BS_GodFile/MelodiaIntegration/MelodiaJRPGPostBattleLibrary.h:23 |

### rhythm — UMelodiaRhythmCombatSubsystem; UMelodiaMusicClockSubsystem owns beat time

Nodes: 17 — canonical:11, dead_candidate:5, presentation:1

| path | symbol | role | verdict | confidence | runtime_reachability | citation |
|---|---|---|---|---|---|---|
| Plugins/MelodiaCore/Source/MelodiaCore/MelodiaBattleInputComponent.cpp | MelodiaBattleInputComponent | dead_candidate | DEAD_CANDIDATE | 0.99 | source-present only | Plugins/MelodiaCore/Source/MelodiaCore/MelodiaBattleInputComponent.cpp:1 |
| Plugins/MelodiaCore/Source/MelodiaCore/MelodiaBattleInputComponent.h | UMelodiaRhythmExecutionComponent | dead_candidate | DEAD_CANDIDATE | 0.96 | source-present only | Plugins/MelodiaCore/Source/MelodiaCore/MelodiaBattleInputComponent.h:9 |
| Plugins/MelodiaCore/Source/MelodiaCore/MelodiaMobileHUD.h | UMelodiaBattleInputComponent | dead_candidate | DEAD_CANDIDATE | 0.96 | source-present only | Plugins/MelodiaCore/Source/MelodiaCore/MelodiaMobileHUD.h:16 |
| Plugins/MelodiaCore/Source/MelodiaCore/MelodiaRhythmExecutionComponent.cpp | MelodiaRhythmExecutionComponent | dead_candidate | DEAD_CANDIDATE | 0.99 | source-present only | Plugins/MelodiaCore/Source/MelodiaCore/MelodiaRhythmExecutionComponent.cpp:4 |
| Plugins/MelodiaCore/Source/MelodiaCore/MelodiaRhythmExecutionComponent.h | UMelodiaRhythmExecutionComponent | dead_candidate | DEAD_CANDIDATE | 0.96 | source-present only | Plugins/MelodiaCore/Source/MelodiaCore/MelodiaRhythmExecutionComponent.h:88 |
| Plugins/MelodiaCore/Source/MelodiaCore/MelodiaRhythmReactivitySubsystem.cpp | path | canonical | OWNER | 0.99 | source-present only | Plugins/MelodiaCore/Source/MelodiaCore/MelodiaRhythmReactivitySubsystem.cpp:26 |
| Plugins/MelodiaWardrobe/Source/MelodiaWardrobe/Public/MelodiaResonantPassageComponent.h | UMelodiaMusicClockSubsystem | canonical | OWNER | 1.0 | source-present only | Plugins/MelodiaWardrobe/Source/MelodiaWardrobe/Public/MelodiaResonantPassageComponent.h:8 |
| Source/BS_GodFile/MelodiaIntegration/MelodiaJRPGPresentationRhythmComponent.cpp | MelodiaJRPGPresentationRhythmComponent | canonical | OWNER | 0.99 | source-present only | Source/BS_GodFile/MelodiaIntegration/MelodiaJRPGPresentationRhythmComponent.cpp:1 |
| Source/BS_GodFile/MelodiaIntegration/MelodiaJRPGPresentationRhythmComponent.h | UMelodiaJRPGPresentationRhythmComponent | presentation | PRESENTATION_ONLY | 0.98 | source-present only | Source/BS_GodFile/MelodiaIntegration/MelodiaJRPGPresentationRhythmComponent.h:43 |
| Source/BS_GodFile/MelodiaIntegration/MelodiaMusicClockSubsystem.cpp | MelodiaMusicClockSubsystem | canonical | OWNER | 0.99 | source-present only | Source/BS_GodFile/MelodiaIntegration/MelodiaMusicClockSubsystem.cpp:1 |
| Source/BS_GodFile/MelodiaIntegration/MelodiaMusicClockSubsystem.h | UMelodiaMusicClockSubsystem | canonical | OWNER | 1.0 | source-present only | Source/BS_GodFile/MelodiaIntegration/MelodiaMusicClockSubsystem.h:98 |
| Source/BS_GodFile/MelodiaIntegration/MelodiaRhythmCombatSubsystem.cpp | runtime | canonical | OWNER | 0.99 | source-present only | Source/BS_GodFile/MelodiaIntegration/MelodiaRhythmCombatSubsystem.cpp:188 |
| Source/BS_GodFile/MelodiaIntegration/MelodiaRhythmCombatTypes.h | EMelodiaRhythmEffectType | canonical | OWNER | 0.99 | source-present only | Source/BS_GodFile/MelodiaIntegration/MelodiaRhythmCombatTypes.h:9 |
| Source/BS_GodFile/MelodiaIntegration/MelodiaRhythmSkillDefinition.h | EMelodiaRhythmNiche | canonical | OWNER | 0.99 | source-present only | Source/BS_GodFile/MelodiaIntegration/MelodiaRhythmSkillDefinition.h:15 |
| Source/BS_GodFile/MelodiaIntegration/RhythmBeatTracker.cpp | RhythmBeatTracker | canonical | OWNER | 0.99 | source-present only | Source/BS_GodFile/MelodiaIntegration/RhythmBeatTracker.cpp:3 |
| Source/BS_GodFile/MelodiaIntegration/RhythmBeatTracker.h | UMelodiaMusicClockSubsystem | canonical | OWNER | 1.0 | source-present only | Source/BS_GodFile/MelodiaIntegration/RhythmBeatTracker.h:9 |
| Source/BS_GodFile/MelodiaIntegration/Tests/MelodiaRhythmCombatTests.cpp | MelodiaRhythmCombatTests | canonical | OWNER | 0.99 | source-present only | Source/BS_GodFile/MelodiaIntegration/Tests/MelodiaRhythmCombatTests.cpp:1 |

### save — TurnBased JRPG BP_JRPGSaveGame; NarrativeRecord is an adapted fragment

Nodes: 11 — adapter:2, canonical:3, merge:6

| path | symbol | role | verdict | confidence | runtime_reachability | citation |
|---|---|---|---|---|---|---|
| Content/TurnBasedJRPGTemplate/Blueprints/Battle/BP_JRPGSaveGame.uasset | BP_JRPGSaveGame | canonical | OWNER | 1.0 | source-present only | Content/TurnBasedJRPGTemplate/Blueprints/Battle/BP_JRPGSaveGame.uasset:1 |
| Plugins/MelodiaCore/Source/MelodiaCore/MelodiaBedActor.h | UMelodiaSaveGameSubsystem | merge | MERGE | 1.0 | source-present only | Plugins/MelodiaCore/Source/MelodiaCore/MelodiaBedActor.h:9 |
| Plugins/MelodiaCore/Source/MelodiaCore/MelodiaSaveGame.cpp | MelodiaSaveGame | merge | MERGE | 0.99 | source-present only | Plugins/MelodiaCore/Source/MelodiaCore/MelodiaSaveGame.cpp:1 |
| Plugins/MelodiaCore/Source/MelodiaCore/MelodiaSaveGame.h | UMelodiaSaveGame | merge | MERGE | 1.0 | source-present only | Plugins/MelodiaCore/Source/MelodiaCore/MelodiaSaveGame.h:19 |
| Plugins/MelodiaCore/Source/MelodiaCore/MelodiaSaveGameSubsystem.cpp | MelodiaSaveGameSubsystem | merge | MERGE | 0.99 | source-present only | Plugins/MelodiaCore/Source/MelodiaCore/MelodiaSaveGameSubsystem.cpp:1 |
| Plugins/MelodiaCore/Source/MelodiaCore/MelodiaSaveGameSubsystem.h | UMelodiaSaveGameSubsystem | merge | MERGE | 1.0 | source-present only | Plugins/MelodiaCore/Source/MelodiaCore/MelodiaSaveGameSubsystem.h:52 |
| Plugins/MelodiaCore/Source/MelodiaCore/MelodiaTokenWalletSubsystem.h | UMelodiaSaveGame | merge | MERGE | 1.0 | source-present only | Plugins/MelodiaCore/Source/MelodiaCore/MelodiaTokenWalletSubsystem.h:18 |
| Source/BS_GodFile/MelodiaIntegration/MelodiaSaveRecoverySubsystem.cpp | MelodiaSaveRecoverySubsystem | canonical | OWNER | 0.99 | source-present only | Source/BS_GodFile/MelodiaIntegration/MelodiaSaveRecoverySubsystem.cpp:1 |
| Source/BS_GodFile/MelodiaIntegration/MelodiaSaveRecoverySubsystem.h | UMelodiaSaveRecoverySubsystem | adapter | ADAPTER | 0.98 | source-present only | Source/BS_GodFile/MelodiaIntegration/MelodiaSaveRecoverySubsystem.h:16 |
| Source/BS_GodFile/MelodiaIntegration/MelodiaSaveSlotLibrary.cpp | MelodiaSaveSlotLibrary | canonical | OWNER | 0.99 | source-present only | Source/BS_GodFile/MelodiaIntegration/MelodiaSaveSlotLibrary.cpp:1 |
| Source/BS_GodFile/MelodiaIntegration/MelodiaSaveSlotLibrary.h | UMelodiaSaveSlotLibrary | adapter | ADAPTER | 1.0 | source-present only | Source/BS_GodFile/MelodiaIntegration/MelodiaSaveSlotLibrary.h:24 |

### progression — QuillScript-authored narrative progression plus stock JRPG mechanics, committed through UMelodiaNarrativeSubsystem

Nodes: 6 — canonical:2, merge:4

| path | symbol | role | verdict | confidence | runtime_reachability | citation |
|---|---|---|---|---|---|---|
| Plugins/MelodiaCore/Source/MelodiaCore/MelodiaOpeningFlowSubsystem.cpp | MelodiaOpeningFlowSubsystem | merge | MERGE | 0.99 | source-present only | Plugins/MelodiaCore/Source/MelodiaCore/MelodiaOpeningFlowSubsystem.cpp:1 |
| Plugins/MelodiaCore/Source/MelodiaCore/MelodiaOpeningFlowSubsystem.h | AMelodiaQuestManagerBase | merge | MERGE | 0.99 | source-present only | Plugins/MelodiaCore/Source/MelodiaCore/MelodiaOpeningFlowSubsystem.h:7 |
| Plugins/MelodiaCore/Source/MelodiaCore/MelodiaProgressionComponent.h | UMelodiaProgressionComponent | merge | MERGE | 0.98 | source-present only | Plugins/MelodiaCore/Source/MelodiaCore/MelodiaProgressionComponent.h:23 |
| Plugins/MelodiaCore/Source/MelodiaCore/MelodiaQuestManagerBase.h | AMelodiaQuestManagerBase | merge | MERGE | 0.99 | source-present only | Plugins/MelodiaCore/Source/MelodiaCore/MelodiaQuestManagerBase.h:38 |
| Source/BS_GodFile/MelodiaIntegration/MelodiaPersonaSubsystem.cpp | mapping | canonical | OWNER | 0.99 | source-present only | Source/BS_GodFile/MelodiaIntegration/MelodiaPersonaSubsystem.cpp:82 |
| Source/BS_GodFile/MelodiaIntegration/MelodiaPersonaTypes.h | EMelodiaQuestState | canonical | OWNER | 0.99 | source-present only | Source/BS_GodFile/MelodiaIntegration/MelodiaPersonaTypes.h:8 |

### wardrobe — UMelodiaWardrobeSubsystem and wardrobe catalog contract

Nodes: 55 — canonical:53, dead_candidate:2

| path | symbol | role | verdict | confidence | runtime_reachability | citation |
|---|---|---|---|---|---|---|
| Plugins/MelodiaCore/Source/MelodiaCore/MelodiaCharacterBase.h | UMelodiaOutfitComponent | dead_candidate | DEAD_CANDIDATE | 0.98 | source-present only | Plugins/MelodiaCore/Source/MelodiaCore/MelodiaCharacterBase.h:16 |
| Plugins/MelodiaCore/Source/MelodiaCore/MelodiaCompanionWardrobeBridge.cpp | MelodiaCompanionWardrobeBridge | canonical | OWNER | 0.99 | source-present only | Plugins/MelodiaCore/Source/MelodiaCore/MelodiaCompanionWardrobeBridge.cpp:1 |
| Plugins/MelodiaCore/Source/MelodiaCore/MelodiaCompanionWardrobeBridge.h | UActorComponent | canonical | OWNER | 0.99 | source-present only | Plugins/MelodiaCore/Source/MelodiaCore/MelodiaCompanionWardrobeBridge.h:7 |
| Plugins/MelodiaCore/Source/MelodiaCore/MelodiaOutfitComponent.h | UMelodiaOutfitComponent | dead_candidate | DEAD_CANDIDATE | 0.98 | source-present only | Plugins/MelodiaCore/Source/MelodiaCore/MelodiaOutfitComponent.h:34 |
| Plugins/MelodiaWardrobe/Content/MelodiaWardrobe/Drafts/Cos_Accessory_Melusina_Hat.json | Cos_Accessory_Melusina_Hat | canonical | OWNER | 0.99 | source-present only | Plugins/MelodiaWardrobe/Content/MelodiaWardrobe/Drafts/Cos_Accessory_Melusina_Hat.json:2 |
| Plugins/MelodiaWardrobe/Content/MelodiaWardrobe/Drafts/Cos_Accessory_Melusina_Headband.json | Cos_Accessory_Melusina_Headband | canonical | OWNER | 0.99 | source-present only | Plugins/MelodiaWardrobe/Content/MelodiaWardrobe/Drafts/Cos_Accessory_Melusina_Headband.json:2 |
| Plugins/MelodiaWardrobe/Content/MelodiaWardrobe/Drafts/Cos_Accessory_Melusina_Ribbon.json | Cos_Accessory_Melusina_Ribbon | canonical | OWNER | 0.99 | source-present only | Plugins/MelodiaWardrobe/Content/MelodiaWardrobe/Drafts/Cos_Accessory_Melusina_Ribbon.json:2 |
| Plugins/MelodiaWardrobe/Content/MelodiaWardrobe/Drafts/Cos_Accessory_Melusina_Wings.json | Cos_Accessory_Melusina_Wings | canonical | OWNER | 0.99 | source-present only | Plugins/MelodiaWardrobe/Content/MelodiaWardrobe/Drafts/Cos_Accessory_Melusina_Wings.json:2 |
| Plugins/MelodiaWardrobe/Content/MelodiaWardrobe/Drafts/Cos_Dress_Melusina_Elemental.json | Cos_Dress_Melusina_Elemental | canonical | OWNER | 0.99 | source-present only | Plugins/MelodiaWardrobe/Content/MelodiaWardrobe/Drafts/Cos_Dress_Melusina_Elemental.json:2 |
| Plugins/MelodiaWardrobe/Content/MelodiaWardrobe/Drafts/Cos_Dress_Melusina_Ethereal.json | Cos_Dress_Melusina_Ethereal | canonical | OWNER | 0.99 | source-present only | Plugins/MelodiaWardrobe/Content/MelodiaWardrobe/Drafts/Cos_Dress_Melusina_Ethereal.json:2 |
| Plugins/MelodiaWardrobe/Content/MelodiaWardrobe/Drafts/Cos_Dress_Melusina_Noble.json | Cos_Dress_Melusina_Noble | canonical | OWNER | 0.99 | source-present only | Plugins/MelodiaWardrobe/Content/MelodiaWardrobe/Drafts/Cos_Dress_Melusina_Noble.json:2 |
| Plugins/MelodiaWardrobe/Content/MelodiaWardrobe/Drafts/Cos_Dress_Melusina_Royal.json | Cos_Dress_Melusina_Royal | canonical | OWNER | 0.99 | source-present only | Plugins/MelodiaWardrobe/Content/MelodiaWardrobe/Drafts/Cos_Dress_Melusina_Royal.json:2 |
| Plugins/MelodiaWardrobe/Content/MelodiaWardrobe/Drafts/Cos_Footwear_Melusina_Boot.json | Cos_Footwear_Melusina_Boot | canonical | OWNER | 0.99 | source-present only | Plugins/MelodiaWardrobe/Content/MelodiaWardrobe/Drafts/Cos_Footwear_Melusina_Boot.json:2 |
| Plugins/MelodiaWardrobe/Content/MelodiaWardrobe/Drafts/Cos_Footwear_Melusina_Sandals.json | Cos_Footwear_Melusina_Sandals | canonical | OWNER | 0.99 | source-present only | Plugins/MelodiaWardrobe/Content/MelodiaWardrobe/Drafts/Cos_Footwear_Melusina_Sandals.json:2 |
| Plugins/MelodiaWardrobe/Content/MelodiaWardrobe/Drafts/Cos_Footwear_Melusina_Shoes.json | Cos_Footwear_Melusina_Shoes | canonical | OWNER | 0.99 | source-present only | Plugins/MelodiaWardrobe/Content/MelodiaWardrobe/Drafts/Cos_Footwear_Melusina_Shoes.json:2 |
| Plugins/MelodiaWardrobe/Content/MelodiaWardrobe/Drafts/Cos_Footwear_Melusina_Slippers.json | Cos_Footwear_Melusina_Slippers | canonical | OWNER | 0.99 | source-present only | Plugins/MelodiaWardrobe/Content/MelodiaWardrobe/Drafts/Cos_Footwear_Melusina_Slippers.json:2 |
| Plugins/MelodiaWardrobe/Content/MelodiaWardrobe/Drafts/Cos_Outerwear_Melusina_Cloak.json | Cos_Outerwear_Melusina_Cloak | canonical | OWNER | 0.99 | source-present only | Plugins/MelodiaWardrobe/Content/MelodiaWardrobe/Drafts/Cos_Outerwear_Melusina_Cloak.json:2 |
| Plugins/MelodiaWardrobe/Content/MelodiaWardrobe/Drafts/Cos_Outerwear_Melusina_Coat.json | Cos_Outerwear_Melusina_Coat | canonical | OWNER | 0.99 | source-present only | Plugins/MelodiaWardrobe/Content/MelodiaWardrobe/Drafts/Cos_Outerwear_Melusina_Coat.json:2 |
| Plugins/MelodiaWardrobe/Content/MelodiaWardrobe/Drafts/Cos_Outerwear_Melusina_Jackets.json | Cos_Outerwear_Melusina_Jackets | canonical | OWNER | 0.99 | source-present only | Plugins/MelodiaWardrobe/Content/MelodiaWardrobe/Drafts/Cos_Outerwear_Melusina_Jackets.json:2 |
| Plugins/MelodiaWardrobe/Content/MelodiaWardrobe/Drafts/Cos_Outerwear_Melusina_Vestment.json | Cos_Outerwear_Melusina_Vestment | canonical | OWNER | 0.99 | source-present only | Plugins/MelodiaWardrobe/Content/MelodiaWardrobe/Drafts/Cos_Outerwear_Melusina_Vestment.json:2 |
| Plugins/MelodiaWardrobe/Content/MelodiaWardrobe/Drafts/Cos_Skirt_Melusina_Classical.json | Cos_Skirt_Melusina_Classical | canonical | OWNER | 0.99 | source-present only | Plugins/MelodiaWardrobe/Content/MelodiaWardrobe/Drafts/Cos_Skirt_Melusina_Classical.json:2 |
| Plugins/MelodiaWardrobe/Content/MelodiaWardrobe/Drafts/Cos_Skirt_Melusina_Fantasy.json | Cos_Skirt_Melusina_Fantasy | canonical | OWNER | 0.99 | source-present only | Plugins/MelodiaWardrobe/Content/MelodiaWardrobe/Drafts/Cos_Skirt_Melusina_Fantasy.json:2 |
| Plugins/MelodiaWardrobe/Content/MelodiaWardrobe/Drafts/Cos_Skirt_Melusina_Gothic.json | Cos_Skirt_Melusina_Gothic | canonical | OWNER | 0.99 | source-present only | Plugins/MelodiaWardrobe/Content/MelodiaWardrobe/Drafts/Cos_Skirt_Melusina_Gothic.json:2 |
| Plugins/MelodiaWardrobe/Content/MelodiaWardrobe/Drafts/Cos_Skirt_Melusina_Sailor.json | Cos_Skirt_Melusina_Sailor | canonical | OWNER | 0.99 | source-present only | Plugins/MelodiaWardrobe/Content/MelodiaWardrobe/Drafts/Cos_Skirt_Melusina_Sailor.json:2 |
| Plugins/MelodiaWardrobe/Content/MelodiaWardrobe/Drafts/Cos_Special_Melusina_Event1.json | Cos_Special_Melusina_Event1 | canonical | OWNER | 0.99 | source-present only | Plugins/MelodiaWardrobe/Content/MelodiaWardrobe/Drafts/Cos_Special_Melusina_Event1.json:2 |
| Plugins/MelodiaWardrobe/Content/MelodiaWardrobe/Drafts/Cos_Special_Melusina_Event10.json | Cos_Special_Melusina_Event10 | canonical | OWNER | 0.99 | source-present only | Plugins/MelodiaWardrobe/Content/MelodiaWardrobe/Drafts/Cos_Special_Melusina_Event10.json:2 |
| Plugins/MelodiaWardrobe/Content/MelodiaWardrobe/Drafts/Cos_Special_Melusina_Event11.json | Cos_Special_Melusina_Event11 | canonical | OWNER | 0.99 | source-present only | Plugins/MelodiaWardrobe/Content/MelodiaWardrobe/Drafts/Cos_Special_Melusina_Event11.json:2 |
| Plugins/MelodiaWardrobe/Content/MelodiaWardrobe/Drafts/Cos_Special_Melusina_Event12.json | Cos_Special_Melusina_Event12 | canonical | OWNER | 0.99 | source-present only | Plugins/MelodiaWardrobe/Content/MelodiaWardrobe/Drafts/Cos_Special_Melusina_Event12.json:2 |
| Plugins/MelodiaWardrobe/Content/MelodiaWardrobe/Drafts/Cos_Special_Melusina_Event13.json | Cos_Special_Melusina_Event13 | canonical | OWNER | 0.99 | source-present only | Plugins/MelodiaWardrobe/Content/MelodiaWardrobe/Drafts/Cos_Special_Melusina_Event13.json:2 |
| Plugins/MelodiaWardrobe/Content/MelodiaWardrobe/Drafts/Cos_Special_Melusina_Event14.json | Cos_Special_Melusina_Event14 | canonical | OWNER | 0.99 | source-present only | Plugins/MelodiaWardrobe/Content/MelodiaWardrobe/Drafts/Cos_Special_Melusina_Event14.json:2 |
| Plugins/MelodiaWardrobe/Content/MelodiaWardrobe/Drafts/Cos_Special_Melusina_Event2.json | Cos_Special_Melusina_Event2 | canonical | OWNER | 0.99 | source-present only | Plugins/MelodiaWardrobe/Content/MelodiaWardrobe/Drafts/Cos_Special_Melusina_Event2.json:2 |
| Plugins/MelodiaWardrobe/Content/MelodiaWardrobe/Drafts/Cos_Special_Melusina_Event3.json | Cos_Special_Melusina_Event3 | canonical | OWNER | 0.99 | source-present only | Plugins/MelodiaWardrobe/Content/MelodiaWardrobe/Drafts/Cos_Special_Melusina_Event3.json:2 |
| Plugins/MelodiaWardrobe/Content/MelodiaWardrobe/Drafts/Cos_Special_Melusina_Event4.json | Cos_Special_Melusina_Event4 | canonical | OWNER | 0.99 | source-present only | Plugins/MelodiaWardrobe/Content/MelodiaWardrobe/Drafts/Cos_Special_Melusina_Event4.json:2 |
| Plugins/MelodiaWardrobe/Content/MelodiaWardrobe/Drafts/Cos_Special_Melusina_Event5.json | Cos_Special_Melusina_Event5 | canonical | OWNER | 0.99 | source-present only | Plugins/MelodiaWardrobe/Content/MelodiaWardrobe/Drafts/Cos_Special_Melusina_Event5.json:2 |
| Plugins/MelodiaWardrobe/Content/MelodiaWardrobe/Drafts/Cos_Special_Melusina_Event6.json | Cos_Special_Melusina_Event6 | canonical | OWNER | 0.99 | source-present only | Plugins/MelodiaWardrobe/Content/MelodiaWardrobe/Drafts/Cos_Special_Melusina_Event6.json:2 |
| Plugins/MelodiaWardrobe/Content/MelodiaWardrobe/Drafts/Cos_Special_Melusina_Event7.json | Cos_Special_Melusina_Event7 | canonical | OWNER | 0.99 | source-present only | Plugins/MelodiaWardrobe/Content/MelodiaWardrobe/Drafts/Cos_Special_Melusina_Event7.json:2 |
| Plugins/MelodiaWardrobe/Content/MelodiaWardrobe/Drafts/Cos_Special_Melusina_Event8.json | Cos_Special_Melusina_Event8 | canonical | OWNER | 0.99 | source-present only | Plugins/MelodiaWardrobe/Content/MelodiaWardrobe/Drafts/Cos_Special_Melusina_Event8.json:2 |
| Plugins/MelodiaWardrobe/Content/MelodiaWardrobe/Drafts/Cos_Special_Melusina_Event9.json | Cos_Special_Melusina_Event9 | canonical | OWNER | 0.99 | source-present only | Plugins/MelodiaWardrobe/Content/MelodiaWardrobe/Drafts/Cos_Special_Melusina_Event9.json:2 |
| Plugins/MelodiaWardrobe/Content/MelodiaWardrobe/Drafts/Cos_Top_Melusina_Blouse.json | Cos_Top_Melusina_Blouse | canonical | OWNER | 0.99 | source-present only | Plugins/MelodiaWardrobe/Content/MelodiaWardrobe/Drafts/Cos_Top_Melusina_Blouse.json:2 |
| Plugins/MelodiaWardrobe/Content/MelodiaWardrobe/Drafts/Cos_Top_Melusina_Corset.json | Cos_Top_Melusina_Corset | canonical | OWNER | 0.99 | source-present only | Plugins/MelodiaWardrobe/Content/MelodiaWardrobe/Drafts/Cos_Top_Melusina_Corset.json:2 |
| Plugins/MelodiaWardrobe/Content/MelodiaWardrobe/Drafts/Cos_Top_Melusina_Sweater.json | Cos_Top_Melusina_Sweater | canonical | OWNER | 0.99 | source-present only | Plugins/MelodiaWardrobe/Content/MelodiaWardrobe/Drafts/Cos_Top_Melusina_Sweater.json:2 |
| Plugins/MelodiaWardrobe/Content/MelodiaWardrobe/Drafts/Cos_Top_Melusina_Vest.json | Cos_Top_Melusina_Vest | canonical | OWNER | 0.99 | source-present only | Plugins/MelodiaWardrobe/Content/MelodiaWardrobe/Drafts/Cos_Top_Melusina_Vest.json:2 |
| Plugins/MelodiaWardrobe/MelodiaWardrobe.uplugin | MelodiaWardrobe | canonical | OWNER | 0.99 | source-present only | Plugins/MelodiaWardrobe/MelodiaWardrobe.uplugin:13 |
| Plugins/MelodiaWardrobe/Source/MelodiaWardrobe/MelodiaWardrobe.Build.cs | MelodiaWardrobe | canonical | OWNER | 0.99 | source-present only | Plugins/MelodiaWardrobe/Source/MelodiaWardrobe/MelodiaWardrobe.Build.cs:1 |
| Plugins/MelodiaWardrobe/Source/MelodiaWardrobe/Private/MelodiaCosmeticDefinition.cpp | MelodiaCosmeticDefinition | canonical | OWNER | 0.99 | source-present only | Plugins/MelodiaWardrobe/Source/MelodiaWardrobe/Private/MelodiaCosmeticDefinition.cpp:3 |
| Plugins/MelodiaWardrobe/Source/MelodiaWardrobe/Private/MelodiaResonantPassageComponent.cpp | MelodiaResonantPassageComponent | canonical | OWNER | 0.99 | source-present only | Plugins/MelodiaWardrobe/Source/MelodiaWardrobe/Private/MelodiaResonantPassageComponent.cpp:1 |
| Plugins/MelodiaWardrobe/Source/MelodiaWardrobe/Private/MelodiaWardrobeCompanionBridgeTests.cpp | MelodiaWardrobeCompanionBridgeTests | canonical | OWNER | 0.99 | source-present only | Plugins/MelodiaWardrobe/Source/MelodiaWardrobe/Private/MelodiaWardrobeCompanionBridgeTests.cpp:1 |
| Plugins/MelodiaWardrobe/Source/MelodiaWardrobe/Private/MelodiaWardrobeComponent.cpp | MelodiaWardrobeComponent | canonical | OWNER | 0.99 | source-present only | Plugins/MelodiaWardrobe/Source/MelodiaWardrobe/Private/MelodiaWardrobeComponent.cpp:3 |
| Plugins/MelodiaWardrobe/Source/MelodiaWardrobe/Private/MelodiaWardrobeGachaSubsystem.cpp | MelodiaWardrobeGachaSubsystem | canonical | OWNER | 0.99 | source-present only | Plugins/MelodiaWardrobe/Source/MelodiaWardrobe/Private/MelodiaWardrobeGachaSubsystem.cpp:7 |
| Plugins/MelodiaWardrobe/Source/MelodiaWardrobe/Private/MelodiaWardrobeModule.cpp | MelodiaWardrobeModule | canonical | OWNER | 0.99 | source-present only | Plugins/MelodiaWardrobe/Source/MelodiaWardrobe/Private/MelodiaWardrobeModule.cpp:1 |
| ... 5 more ... | | | | | | |

### traversal — UMelodiaTraversalComponent with one IMelodiaTraversalCapabilityProvider

Nodes: 12 — adapter:2, canonical:10

| path | symbol | role | verdict | confidence | runtime_reachability | citation |
|---|---|---|---|---|---|---|
| Source/BS_GodFile/MelodiaIntegration/MelodiaTraversalCapabilityProvider.cpp | MelodiaTraversalCapabilityProvider | adapter | ADAPTER | 0.99 | source-present only | Source/BS_GodFile/MelodiaIntegration/MelodiaTraversalCapabilityProvider.cpp:1 |
| Source/BS_GodFile/MelodiaIntegration/MelodiaTraversalCapabilityProvider.h | IMelodiaTraversalCapabilityProvider | adapter | ADAPTER | 1.0 | source-present only | Source/BS_GodFile/MelodiaIntegration/MelodiaTraversalCapabilityProvider.h:42 |
| Source/BS_GodFile/MelodiaIntegration/MelodiaTraversalComponent.cpp | MelodiaTraversalComponent | canonical | OWNER | 0.99 | source-present only | Source/BS_GodFile/MelodiaIntegration/MelodiaTraversalComponent.cpp:1 |
| Source/BS_GodFile/MelodiaIntegration/MelodiaTraversalComponent.h | UMelodiaTraversalComponent | canonical | OWNER | 1.0 | source-present only | Source/BS_GodFile/MelodiaIntegration/MelodiaTraversalComponent.h:70 |
| Source/BS_GodFile/MelodiaIntegration/MelodiaWaterGameplayControllerComponent.cpp | MelodiaWaterGameplayControllerComponent | canonical | OWNER | 0.99 | source-present only | Source/BS_GodFile/MelodiaIntegration/MelodiaWaterGameplayControllerComponent.cpp:1 |
| Source/BS_GodFile/MelodiaIntegration/MelodiaWaterGameplayControllerComponent.h | UMelodiaWaterGameplaySubsystem | canonical | OWNER | 0.99 | source-present only | Source/BS_GodFile/MelodiaIntegration/MelodiaWaterGameplayControllerComponent.h:8 |
| Source/BS_GodFile/MelodiaIntegration/MelodiaWaterGameplayDeviceAnchor.cpp | MelodiaWaterGameplayDeviceAnchor | canonical | OWNER | 0.99 | source-present only | Source/BS_GodFile/MelodiaIntegration/MelodiaWaterGameplayDeviceAnchor.cpp:1 |
| Source/BS_GodFile/MelodiaIntegration/MelodiaWaterGameplayDeviceAnchor.h | UBoxComponent | canonical | OWNER | 0.99 | source-present only | Source/BS_GodFile/MelodiaIntegration/MelodiaWaterGameplayDeviceAnchor.h:8 |
| Source/BS_GodFile/MelodiaIntegration/MelodiaWaterGameplaySubsystem.cpp | MelodiaWaterGameplaySubsystem | canonical | OWNER | 0.99 | source-present only | Source/BS_GodFile/MelodiaIntegration/MelodiaWaterGameplaySubsystem.cpp:1 |
| Source/BS_GodFile/MelodiaIntegration/MelodiaWaterGameplaySubsystem.h | FSubsystemCollectionBase | canonical | OWNER | 0.99 | source-present only | Source/BS_GodFile/MelodiaIntegration/MelodiaWaterGameplaySubsystem.h:8 |
| Source/BS_GodFile/MelodiaIntegration/MelodiaWaterGameplayTypes.h | AActor | canonical | OWNER | 0.99 | source-present only | Source/BS_GodFile/MelodiaIntegration/MelodiaWaterGameplayTypes.h:7 |
| Source/BS_GodFile/MelodiaIntegration/Tests/MelodiaWaterGameplayTests.cpp | MelodiaWaterGameplayTests | canonical | OWNER | 0.99 | source-present only | Source/BS_GodFile/MelodiaIntegration/Tests/MelodiaWaterGameplayTests.cpp:1 |

### ui — One writer per surface: stock BP_BattleUI for commands and UMelodiaUIBridgeSubsystem for Melodia battle presentation

Nodes: 173 — canonical:20, dead_candidate:1, presentation:152

| path | symbol | role | verdict | confidence | runtime_reachability | citation |
|---|---|---|---|---|---|---|
| Content/TurnBasedJRPGTemplate/Blueprints/Battle/BP_BattleUI.uasset | BP_BattleUI | canonical | OWNER | 1.0 | source-present only | Content/TurnBasedJRPGTemplate/Blueprints/Battle/BP_BattleUI.uasset:1 |
| Plugins/MelodiaCore/MelodiaCore.uplugin | MelodiaCore | presentation | PRESENTATION_ONLY | 0.99 | source-present only | Plugins/MelodiaCore/MelodiaCore.uplugin:13 |
| Plugins/MelodiaCore/Rules/melodia_rules.json | melodia_rules | presentation | PRESENTATION_ONLY | 0.99 | source-present only | Plugins/MelodiaCore/Rules/melodia_rules.json:5 |
| Plugins/MelodiaCore/Rules/README.md | README | presentation | PRESENTATION_ONLY | 0.99 | source-present only | Plugins/MelodiaCore/Rules/README.md:1 |
| Plugins/MelodiaCore/Source/MelodiaCore/MelodiaAfflictionTypes.cpp | MelodiaAfflictionTypes | presentation | PRESENTATION_ONLY | 0.99 | source-present only | Plugins/MelodiaCore/Source/MelodiaCore/MelodiaAfflictionTypes.cpp:1 |
| Plugins/MelodiaCore/Source/MelodiaCore/MelodiaAfflictionTypes.h | EMelodiaAffliction | presentation | PRESENTATION_ONLY | 0.99 | source-present only | Plugins/MelodiaCore/Source/MelodiaCore/MelodiaAfflictionTypes.h:8 |
| Plugins/MelodiaCore/Source/MelodiaCore/MelodiaAssetRepairLibrary.cpp | MelodiaAssetRepairLibrary | presentation | PRESENTATION_ONLY | 0.99 | source-present only | Plugins/MelodiaCore/Source/MelodiaCore/MelodiaAssetRepairLibrary.cpp:1 |
| Plugins/MelodiaCore/Source/MelodiaCore/MelodiaAssetRepairLibrary.h | USkeletalMesh | presentation | PRESENTATION_ONLY | 0.99 | source-present only | Plugins/MelodiaCore/Source/MelodiaCore/MelodiaAssetRepairLibrary.h:9 |
| Plugins/MelodiaCore/Source/MelodiaCore/MelodiaAudioComponent.cpp | MelodiaAudioComponent | presentation | PRESENTATION_ONLY | 0.99 | source-present only | Plugins/MelodiaCore/Source/MelodiaCore/MelodiaAudioComponent.cpp:1 |
| Plugins/MelodiaCore/Source/MelodiaCore/MelodiaAudioComponent.h | USoundWave | presentation | PRESENTATION_ONLY | 0.99 | source-present only | Plugins/MelodiaCore/Source/MelodiaCore/MelodiaAudioComponent.h:8 |
| Plugins/MelodiaCore/Source/MelodiaCore/MelodiaAuthorityLocator.cpp | MelodiaAuthorityLocator | presentation | PRESENTATION_ONLY | 0.99 | source-present only | Plugins/MelodiaCore/Source/MelodiaCore/MelodiaAuthorityLocator.cpp:1 |
| Plugins/MelodiaCore/Source/MelodiaCore/MelodiaAuthorityLocator.h | provider | presentation | PRESENTATION_ONLY | 0.99 | source-present only | Plugins/MelodiaCore/Source/MelodiaCore/MelodiaAuthorityLocator.h:13 |
| Plugins/MelodiaCore/Source/MelodiaCore/MelodiaBattleArena.cpp | MelodiaBattleArena | presentation | PRESENTATION_ONLY | 0.99 | source-present only | Plugins/MelodiaCore/Source/MelodiaCore/MelodiaBattleArena.cpp:3 |
| Plugins/MelodiaCore/Source/MelodiaCore/MelodiaBattleArena.h | UStaticMeshComponent | presentation | PRESENTATION_ONLY | 0.99 | source-present only | Plugins/MelodiaCore/Source/MelodiaCore/MelodiaBattleArena.h:14 |
| Plugins/MelodiaCore/Source/MelodiaCore/MelodiaBattleResultsWidget.cpp | MelodiaBattleResultsWidget | presentation | PRESENTATION_ONLY | 0.99 | source-present only | Plugins/MelodiaCore/Source/MelodiaCore/MelodiaBattleResultsWidget.cpp:1 |
| Plugins/MelodiaCore/Source/MelodiaCore/MelodiaBattleResultsWidget.h | UTextBlock | presentation | PRESENTATION_ONLY | 0.99 | source-present only | Plugins/MelodiaCore/Source/MelodiaCore/MelodiaBattleResultsWidget.h:7 |
| Plugins/MelodiaCore/Source/MelodiaCore/MelodiaBattleTypes.h | EMelodiaBattlePhase | presentation | PRESENTATION_ONLY | 0.99 | source-present only | Plugins/MelodiaCore/Source/MelodiaCore/MelodiaBattleTypes.h:10 |
| Plugins/MelodiaCore/Source/MelodiaCore/MelodiaBedActor.cpp | MelodiaBedActor | presentation | PRESENTATION_ONLY | 0.99 | source-present only | Plugins/MelodiaCore/Source/MelodiaCore/MelodiaBedActor.cpp:1 |
| Plugins/MelodiaCore/Source/MelodiaCore/MelodiaCharacterBase.cpp | MelodiaCharacterBase | presentation | PRESENTATION_ONLY | 0.99 | source-present only | Plugins/MelodiaCore/Source/MelodiaCore/MelodiaCharacterBase.cpp:1 |
| Plugins/MelodiaCore/Source/MelodiaCore/MelodiaChoralSheepActor.cpp | MelodiaChoralSheepActor | presentation | PRESENTATION_ONLY | 0.99 | source-present only | Plugins/MelodiaCore/Source/MelodiaCore/MelodiaChoralSheepActor.cpp:1 |
| Plugins/MelodiaCore/Source/MelodiaCore/MelodiaChoralSheepActor.h | AActor | presentation | PRESENTATION_ONLY | 0.99 | source-present only | Plugins/MelodiaCore/Source/MelodiaCore/MelodiaChoralSheepActor.h:8 |
| Plugins/MelodiaCore/Source/MelodiaCore/MelodiaCombatPresentationInterface.h | UMelodiaCombatPresentationInterface | presentation | PRESENTATION_ONLY | 0.99 | source-present only | Plugins/MelodiaCore/Source/MelodiaCore/MelodiaCombatPresentationInterface.h:11 |
| Plugins/MelodiaCore/Source/MelodiaCore/MelodiaCombatStateComponent.cpp | MelodiaCombatStateComponent | presentation | PRESENTATION_ONLY | 0.99 | source-present only | Plugins/MelodiaCore/Source/MelodiaCore/MelodiaCombatStateComponent.cpp:4 |
| Plugins/MelodiaCore/Source/MelodiaCore/MelodiaCombatStateComponent.h | the | presentation | PRESENTATION_ONLY | 0.99 | source-present only | Plugins/MelodiaCore/Source/MelodiaCore/MelodiaCombatStateComponent.h:12 |
| Plugins/MelodiaCore/Source/MelodiaCore/MelodiaCompanionComponent.cpp | MelodiaCompanionComponent | presentation | PRESENTATION_ONLY | 0.99 | source-present only | Plugins/MelodiaCore/Source/MelodiaCore/MelodiaCompanionComponent.cpp:1 |
| Plugins/MelodiaCore/Source/MelodiaCore/MelodiaCompanionComponent.h | AActor | presentation | PRESENTATION_ONLY | 0.99 | source-present only | Plugins/MelodiaCore/Source/MelodiaCore/MelodiaCompanionComponent.h:9 |
| Plugins/MelodiaCore/Source/MelodiaCore/MelodiaCompanionData.cpp | MelodiaCompanionData | presentation | PRESENTATION_ONLY | 0.99 | source-present only | Plugins/MelodiaCore/Source/MelodiaCore/MelodiaCompanionData.cpp:1 |
| Plugins/MelodiaCore/Source/MelodiaCore/MelodiaCompanionData.h | UAnimInstance | presentation | PRESENTATION_ONLY | 0.99 | source-present only | Plugins/MelodiaCore/Source/MelodiaCore/MelodiaCompanionData.h:10 |
| Plugins/MelodiaCore/Source/MelodiaCore/MelodiaCompanionRulesTests.cpp | MelodiaCompanionRulesTests | presentation | PRESENTATION_ONLY | 0.99 | source-present only | Plugins/MelodiaCore/Source/MelodiaCore/MelodiaCompanionRulesTests.cpp:1 |
| Plugins/MelodiaCore/Source/MelodiaCore/MelodiaCore.Build.cs | MelodiaCore | presentation | PRESENTATION_ONLY | 0.99 | source-present only | Plugins/MelodiaCore/Source/MelodiaCore/MelodiaCore.Build.cs:1 |
| Plugins/MelodiaCore/Source/MelodiaCore/MelodiaCore.cpp | MelodiaCore | presentation | PRESENTATION_ONLY | 0.99 | source-present only | Plugins/MelodiaCore/Source/MelodiaCore/MelodiaCore.cpp:1 |
| Plugins/MelodiaCore/Source/MelodiaCore/MelodiaCore.h | FMelodiaCoreModule | presentation | PRESENTATION_ONLY | 0.99 | source-present only | Plugins/MelodiaCore/Source/MelodiaCore/MelodiaCore.h:7 |
| Plugins/MelodiaCore/Source/MelodiaCore/MelodiaCoreRulesLibrary.cpp | MelodiaCoreRulesLibrary | presentation | PRESENTATION_ONLY | 0.99 | source-present only | Plugins/MelodiaCore/Source/MelodiaCore/MelodiaCoreRulesLibrary.cpp:4 |
| Plugins/MelodiaCore/Source/MelodiaCore/MelodiaCoreRulesLibrary.h | URoomData | presentation | PRESENTATION_ONLY | 0.99 | source-present only | Plugins/MelodiaCore/Source/MelodiaCore/MelodiaCoreRulesLibrary.h:11 |
| Plugins/MelodiaCore/Source/MelodiaCore/MelodiaCoreRulesTests.cpp | MelodiaCoreRulesTests | presentation | PRESENTATION_ONLY | 0.99 | source-present only | Plugins/MelodiaCore/Source/MelodiaCore/MelodiaCoreRulesTests.cpp:1 |
| Plugins/MelodiaCore/Source/MelodiaCore/MelodiaCurrencyRegistry.cpp | MelodiaCurrencyRegistry | presentation | PRESENTATION_ONLY | 0.99 | source-present only | Plugins/MelodiaCore/Source/MelodiaCore/MelodiaCurrencyRegistry.cpp:3 |
| Plugins/MelodiaCore/Source/MelodiaCore/MelodiaCurrencyRegistry.h | UMaterialInterface | presentation | PRESENTATION_ONLY | 0.99 | source-present only | Plugins/MelodiaCore/Source/MelodiaCore/MelodiaCurrencyRegistry.h:34 |
| Plugins/MelodiaCore/Source/MelodiaCore/MelodiaCurrencyRegistryTests.cpp | MelodiaCurrencyRegistryTests | presentation | PRESENTATION_ONLY | 0.99 | source-present only | Plugins/MelodiaCore/Source/MelodiaCore/MelodiaCurrencyRegistryTests.cpp:1 |
| Plugins/MelodiaCore/Source/MelodiaCore/MelodiaDevEntitlementProvider.cpp | MelodiaDevEntitlementProvider | presentation | PRESENTATION_ONLY | 0.99 | source-present only | Plugins/MelodiaCore/Source/MelodiaCore/MelodiaDevEntitlementProvider.cpp:1 |
| Plugins/MelodiaCore/Source/MelodiaCore/MelodiaDevEntitlementProvider.h | UMelodiaDevEntitlementProvider | presentation | PRESENTATION_ONLY | 0.99 | source-present only | Plugins/MelodiaCore/Source/MelodiaCore/MelodiaDevEntitlementProvider.h:9 |
| Plugins/MelodiaCore/Source/MelodiaCore/MelodiaDissonanceBeat.cpp | MelodiaDissonanceBeat | presentation | PRESENTATION_ONLY | 0.99 | source-present only | Plugins/MelodiaCore/Source/MelodiaCore/MelodiaDissonanceBeat.cpp:1 |
| Plugins/MelodiaCore/Source/MelodiaCore/MelodiaDissonanceBeat.h | UBoxComponent | presentation | PRESENTATION_ONLY | 0.99 | source-present only | Plugins/MelodiaCore/Source/MelodiaCore/MelodiaDissonanceBeat.h:8 |
| Plugins/MelodiaCore/Source/MelodiaCore/MelodiaDungeonFunctionalTests.cpp | final | presentation | PRESENTATION_ONLY | 0.99 | source-present only | Plugins/MelodiaCore/Source/MelodiaCore/MelodiaDungeonFunctionalTests.cpp:17 |
| Plugins/MelodiaCore/Source/MelodiaCore/MelodiaDungeonRecipeConsumer.h | UMelodiaDungeonRecipeConsumer | presentation | PRESENTATION_ONLY | 0.99 | source-present only | Plugins/MelodiaCore/Source/MelodiaCore/MelodiaDungeonRecipeConsumer.h:9 |
| Plugins/MelodiaCore/Source/MelodiaCore/MelodiaDungeonRunCoordinator.cpp | MelodiaDungeonRunCoordinator | presentation | PRESENTATION_ONLY | 0.99 | static-reachable via CreateWidget | Plugins/MelodiaCore/Source/MelodiaCore/MelodiaDungeonRunCoordinator.cpp:1 |
| Plugins/MelodiaCore/Source/MelodiaCore/MelodiaEconomyTestListener.h | UMelodiaEconomyTestListener | presentation | PRESENTATION_ONLY | 0.99 | source-present only | Plugins/MelodiaCore/Source/MelodiaCore/MelodiaEconomyTestListener.h:24 |
| Plugins/MelodiaCore/Source/MelodiaCore/MelodiaEncounterTrigger.cpp | MelodiaEncounterTrigger | presentation | PRESENTATION_ONLY | 0.99 | source-present only | Plugins/MelodiaCore/Source/MelodiaCore/MelodiaEncounterTrigger.cpp:3 |
| Plugins/MelodiaCore/Source/MelodiaCore/MelodiaEncounterTrigger.h | UStaticMeshComponent | presentation | PRESENTATION_ONLY | 0.99 | source-present only | Plugins/MelodiaCore/Source/MelodiaCore/MelodiaEncounterTrigger.h:15 |
| Plugins/MelodiaCore/Source/MelodiaCore/MelodiaEnemyBase.cpp | MelodiaEnemyBase | presentation | PRESENTATION_ONLY | 0.99 | source-present only | Plugins/MelodiaCore/Source/MelodiaCore/MelodiaEnemyBase.cpp:1 |
| Plugins/MelodiaCore/Source/MelodiaCore/MelodiaEnemyBase.h | UAnimMontage | presentation | PRESENTATION_ONLY | 0.99 | source-present only | Plugins/MelodiaCore/Source/MelodiaCore/MelodiaEnemyBase.h:8 |
| ... 123 more ... | | | | | | |

### music_world — APCGHeroMusicGraphHost emits; UMelodiaNarrativeSubsystem commits consequences; reactivity remains presentation

Nodes: 13 — adapter:1, canonical:10, presentation:2

| path | symbol | role | verdict | confidence | runtime_reachability | citation |
|---|---|---|---|---|---|---|
| Plugins/MelodiaCore/Source/MelodiaCore/MelodiaRhythmReactivitySubsystem.h | UMelodiaRhythmReactivitySubsystem | presentation | PRESENTATION_ONLY | 0.98 | source-present only | Plugins/MelodiaCore/Source/MelodiaCore/MelodiaRhythmReactivitySubsystem.h:59 |
| Source/BS_GodFile/MelodiaIntegration/MelodiaPCGNarrativeChallengeBridgeComponent.cpp | MelodiaPCGNarrativeChallengeBridgeComponent | canonical | OWNER | 0.99 | source-present only | Source/BS_GodFile/MelodiaIntegration/MelodiaPCGNarrativeChallengeBridgeComponent.cpp:1 |
| Source/BS_GodFile/MelodiaIntegration/MelodiaPCGWaterGameplayBridgeComponent.cpp | MelodiaPCGWaterGameplayBridgeComponent | canonical | OWNER | 0.99 | source-present only | Source/BS_GodFile/MelodiaIntegration/MelodiaPCGWaterGameplayBridgeComponent.cpp:1 |
| Source/BS_GodFile/MelodiaIntegration/MelodiaPCGWaterGameplayBridgeComponent.h | UMelodiaPCGWaterGameplayBridgeComponent | adapter | ADAPTER | 0.98 | source-present only | Source/BS_GodFile/MelodiaIntegration/MelodiaPCGWaterGameplayBridgeComponent.h:13 |
| Source/BS_GodFile/MelodiaIntegration/MelodiaWaterAudioBridgeComponent.cpp | MelodiaWaterAudioBridgeComponent | canonical | OWNER | 0.99 | source-present only | Source/BS_GodFile/MelodiaIntegration/MelodiaWaterAudioBridgeComponent.cpp:1 |
| Source/BS_GodFile/MelodiaIntegration/MelodiaWaterAudioBridgeComponent.h | UAudioComponent | canonical | OWNER | 0.99 | source-present only | Source/BS_GodFile/MelodiaIntegration/MelodiaWaterAudioBridgeComponent.h:8 |
| Source/BS_GodFile/MelodiaIntegration/MelusinaSorrowSeamComponent.h | UMelusinaSorrowSeamComponent | presentation | PRESENTATION_ONLY | 1.0 | source-present only | Source/BS_GodFile/MelodiaIntegration/MelusinaSorrowSeamComponent.h:16 |
| Source/BS_GodFile/Piano/PCGHeroMusic.cpp | reflected | canonical | OWNER | 0.99 | source-present only | Source/BS_GodFile/Piano/PCGHeroMusic.cpp:18 |
| Source/BS_GodFile/Piano/PCGHeroMusic.h | APCGHeroMusicGraphHost | canonical | OWNER | 1.0 | source-present only | Source/BS_GodFile/Piano/PCGHeroMusic.h:163 |
| Source/BS_GodFile/Piano/PCGMusicSequencer.cpp | PCGMusicSequencer | canonical | OWNER | 0.99 | source-present only | Source/BS_GodFile/Piano/PCGMusicSequencer.cpp:1 |
| Source/BS_GodFile/Piano/PCGMusicSequencer.h | UPCGComponent | canonical | OWNER | 0.99 | source-present only | Source/BS_GodFile/Piano/PCGMusicSequencer.h:9 |
| Source/BS_GodFile/Piano/PCGPianoKeyboard.cpp | load | canonical | OWNER | 0.99 | source-present only | Source/BS_GodFile/Piano/PCGPianoKeyboard.cpp:3 |
| Source/BS_GodFile/Piano/PCGPianoKeyboard.h | UPCGComponent | canonical | OWNER | 0.99 | source-present only | Source/BS_GodFile/Piano/PCGPianoKeyboard.h:9 |

### economy — TurnBased JRPG inventory/save authority; wardrobe acquisition may adapt through UMelodiaWardrobeGachaSubsystem

Nodes: 3 — canonical:2, merge:1

| path | symbol | role | verdict | confidence | runtime_reachability | citation |
|---|---|---|---|---|---|---|
| Source/BS_GodFile/MelodiaIntegration/MelodiaDesignTokens.cpp | MelodiaDesignTokens | canonical | OWNER | 0.99 | source-present only | Source/BS_GodFile/MelodiaIntegration/MelodiaDesignTokens.cpp:1 |
| Source/BS_GodFile/MelodiaIntegration/MelodiaDesignTokens.h | UMelodiaDesignTokens | canonical | OWNER | 0.99 | source-present only | Source/BS_GodFile/MelodiaIntegration/MelodiaDesignTokens.h:210 |
| Source/BS_GodFile/MelodiaIntegration/MelodiaRhythmCombatSubsystem.h | UMelodiaTokenWalletSubsystem | merge | MERGE | 0.98 | source-present only | Source/BS_GodFile/MelodiaIntegration/MelodiaRhythmCombatSubsystem.h:11 |

### tooling — Repository tooling and manifests; never runtime gameplay authority

Nodes: 856 — authoring:677, prototype:125, unknown:54

| path | symbol | role | verdict | confidence | runtime_reachability | citation |
|---|---|---|---|---|---|---|
| Content/Python/envui/commands.py | _log | authoring | AUTHORING | 0.99 | source-present only | Content/Python/envui/commands.py:9 |
| Content/Python/envui/menu.py | _py_path_prefix | authoring | AUTHORING | 0.99 | source-present only | Content/Python/envui/menu.py:4 |
| Content/Python/envui/paths.py | _project_root | authoring | AUTHORING | 0.99 | source-present only | Content/Python/envui/paths.py:7 |
| Content/Python/gmm/core/audit.py | _project_root | prototype | PROTOTYPE | 0.99 | source-present only | Content/Python/gmm/core/audit.py:19 |
| Content/Python/gmm/core/mcp_client.py | McpError | prototype | PROTOTYPE | 0.99 | source-present only | Content/Python/gmm/core/mcp_client.py:17 |
| Content/Python/gmm/core/settings.py | GmmSettings | prototype | PROTOTYPE | 0.99 | source-present only | Content/Python/gmm/core/settings.py:27 |
| Content/Python/gmm/daemon/generators.py | gen_enemy_forte | prototype | PROTOTYPE | 0.99 | source-present only | Content/Python/gmm/daemon/generators.py:11 |
| Content/Python/gmm/daemon/shared.py | state_path | prototype | PROTOTYPE | 0.99 | source-present only | Content/Python/gmm/daemon/shared.py:20 |
| Content/Python/gmm/daemon/tasks.py | TaskPriority | prototype | PROTOTYPE | 0.99 | source-present only | Content/Python/gmm/daemon/tasks.py:13 |
| Content/Python/gmm/family/cli.py | validate_file | prototype | PROTOTYPE | 0.99 | source-present only | Content/Python/gmm/family/cli.py:11 |
| Content/Python/gmm/family/contracts.py | is_known_role | prototype | PROTOTYPE | 0.99 | source-present only | Content/Python/gmm/family/contracts.py:21 |
| Content/Python/gmm/family/fixture.py | musical_ornament_manifest | prototype | PROTOTYPE | 0.99 | source-present only | Content/Python/gmm/family/fixture.py:5 |
| Content/Python/gmm/family/manifest.py | _required | prototype | PROTOTYPE | 0.99 | source-present only | Content/Python/gmm/family/manifest.py:20 |
| Content/Python/gmm/feel_lab.py | FeelRun | prototype | PROTOTYPE | 0.99 | source-present only | Content/Python/gmm/feel_lab.py:35 |
| Content/Python/gmm/fixtures/instance_on_spline_request.json | instance_on_spline_request | prototype | PROTOTYPE | 0.99 | source-present only | Content/Python/gmm/fixtures/instance_on_spline_request.json:1 |
| Content/Python/gmm/fixtures/melodia_project_manifest.fixture.json | melodia_project_manifest.fixture | prototype | PROTOTYPE | 0.99 | source-present only | Content/Python/gmm/fixtures/melodia_project_manifest.fixture.json:1 |
| Content/Python/gmm/fixtures/niagara_nikki_library.json | niagara_nikki_library | prototype | PROTOTYPE | 0.99 | source-present only | Content/Python/gmm/fixtures/niagara_nikki_library.json:1 |
| Content/Python/gmm/fixtures/water_family_profiles.json | water_family_profiles | prototype | PROTOTYPE | 0.99 | source-present only | Content/Python/gmm/fixtures/water_family_profiles.json:1 |
| Content/Python/gmm/fixtures/water_surface_request.json | water_surface_request | prototype | PROTOTYPE | 0.99 | source-present only | Content/Python/gmm/fixtures/water_surface_request.json:2 |
| Content/Python/gmm/game/afflictions.py | AfflictionInstance | prototype | PROTOTYPE | 0.99 | source-present only | Content/Python/gmm/game/afflictions.py:102 |
| Content/Python/gmm/game/audio_engine.py | AudioEngine | prototype | PROTOTYPE | 0.99 | source-present only | Content/Python/gmm/game/audio_engine.py:7 |
| Content/Python/gmm/game/battle_manager.py | apply_affliction | prototype | PROTOTYPE | 0.99 | source-present only | Content/Python/gmm/game/battle_manager.py:36 |
| Content/Python/gmm/game/battle_osc.py | _pad | prototype | PROTOTYPE | 0.99 | source-present only | Content/Python/gmm/game/battle_osc.py:23 |
| Content/Python/gmm/game/combo_rewards.py | ComboReward | prototype | PROTOTYPE | 0.99 | source-present only | Content/Python/gmm/game/combo_rewards.py:19 |
| Content/Python/gmm/game/config.py | TimingWindows | prototype | PROTOTYPE | 0.99 | source-present only | Content/Python/gmm/game/config.py:34 |
| Content/Python/gmm/game/data_registry.py | EnemyStats | prototype | PROTOTYPE | 0.99 | source-present only | Content/Python/gmm/game/data_registry.py:32 |
| Content/Python/gmm/game/elements.py | element_multiplier | prototype | PROTOTYPE | 0.99 | source-present only | Content/Python/gmm/game/elements.py:14 |
| Content/Python/gmm/game/equipment_catalog.py | get_equipment | prototype | PROTOTYPE | 0.99 | source-present only | Content/Python/gmm/game/equipment_catalog.py:7 |
| Content/Python/gmm/game/interaction.py | InteractableType | prototype | PROTOTYPE | 0.99 | source-present only | Content/Python/gmm/game/interaction.py:11 |
| Content/Python/gmm/game/jrpg_bridge.py | template_action_to_melodia | prototype | PROTOTYPE | 0.99 | source-present only | Content/Python/gmm/game/jrpg_bridge.py:65 |
| Content/Python/gmm/game/modifiers.py | ActiveModifier | prototype | PROTOTYPE | 0.99 | source-present only | Content/Python/gmm/game/modifiers.py:15 |
| Content/Python/gmm/game/ollama_import.py | load_enemy_variants | prototype | PROTOTYPE | 0.99 | source-present only | Content/Python/gmm/game/ollama_import.py:31 |
| Content/Python/gmm/game/party.py | PartyMember | prototype | PROTOTYPE | 0.99 | source-present only | Content/Python/gmm/game/party.py:10 |
| Content/Python/gmm/game/player_state.py | Equipment | prototype | PROTOTYPE | 0.99 | source-present only | Content/Python/gmm/game/player_state.py:8 |
| Content/Python/gmm/game/rhythm_clock.py | MelodiaRhythmClock | prototype | PROTOTYPE | 0.99 | source-present only | Content/Python/gmm/game/rhythm_clock.py:13 |
| Content/Python/gmm/game/roguelike.py | RoomTemplate | prototype | PROTOTYPE | 0.99 | source-present only | Content/Python/gmm/game/roguelike.py:28 |
| Content/Python/gmm/game/roguelike_contract.py | _u32 | prototype | PROTOTYPE | 0.99 | source-present only | Content/Python/gmm/game/roguelike_contract.py:30 |
| Content/Python/gmm/game/roguelike_dungeon.py | DungeonRoomType | prototype | PROTOTYPE | 0.99 | source-present only | Content/Python/gmm/game/roguelike_dungeon.py:33 |
| Content/Python/gmm/game/room_modifiers_melodyslime.py | load_room_modifiers | prototype | PROTOTYPE | 0.99 | source-present only | Content/Python/gmm/game/room_modifiers_melodyslime.py:19 |
| Content/Python/gmm/game/rules_generated.py | module:Content/Python/gmm/game/rules_generated.py | prototype | PROTOTYPE | 0.99 | source-present only | Content/Python/gmm/game/rules_generated.py:1 |
| Content/Python/gmm/game/save_manager.py | default_save_dir | prototype | PROTOTYPE | 0.99 | source-present only | Content/Python/gmm/game/save_manager.py:25 |
| Content/Python/gmm/game/songcraft_effects.py | SongcraftSkillEffect | prototype | PROTOTYPE | 0.99 | source-present only | Content/Python/gmm/game/songcraft_effects.py:15 |
| Content/Python/gmm/game/tokens.py | _load_token_catalog | prototype | PROTOTYPE | 0.99 | source-present only | Content/Python/gmm/game/tokens.py:81 |
| Content/Python/gmm/game/toughness.py | ToughnessResult | prototype | PROTOTYPE | 0.99 | source-present only | Content/Python/gmm/game/toughness.py:13 |
| Content/Python/gmm/gameplay_smoke.py | SmokeResult | prototype | PROTOTYPE | 0.99 | source-present only | Content/Python/gmm/gameplay_smoke.py:18 |
| Content/Python/gmm/geometry/array_tools.py | ArrayTransform | prototype | PROTOTYPE | 0.99 | source-present only | Content/Python/gmm/geometry/array_tools.py:15 |
| Content/Python/gmm/geometry/modifiers.py | GeometryModifier | prototype | PROTOTYPE | 0.99 | source-present only | Content/Python/gmm/geometry/modifiers.py:30 |
| Content/Python/gmm/geometry/procedural_window.py | WindowSpec | prototype | PROTOTYPE | 0.99 | source-present only | Content/Python/gmm/geometry/procedural_window.py:18 |
| Content/Python/gmm/geometry/schemas.py | validate_bevel_parameters | prototype | PROTOTYPE | 0.99 | source-present only | Content/Python/gmm/geometry/schemas.py:17 |
| Content/Python/gmm/geometry/sessions.py | PreviewSession | prototype | PROTOTYPE | 0.99 | source-present only | Content/Python/gmm/geometry/sessions.py:17 |
| ... 806 more ... | | | | | | |

### party — TurnBased JRPG template (party and units)

Nodes: 3 — adapter:1, canonical:1, merge:1

| path | symbol | role | verdict | confidence | runtime_reachability | citation |
|---|---|---|---|---|---|---|
| Plugins/MelodiaCore/Source/MelodiaCore/MelodiaPartySubsystem.h | UMelodiaPartySubsystem | merge | MERGE | 1.0 | source-present only | Plugins/MelodiaCore/Source/MelodiaCore/MelodiaPartySubsystem.h:17 |
| Source/BS_GodFile/MelodiaIntegration/MelodiaJRPGPartyBootstrapSubsystem.cpp | EStockPartyMembership | canonical | OWNER | 0.99 | source-present only | Source/BS_GodFile/MelodiaIntegration/MelodiaJRPGPartyBootstrapSubsystem.cpp:59 |
| Source/BS_GodFile/MelodiaIntegration/MelodiaJRPGPartyBootstrapSubsystem.h | UMelodiaJRPGPartyBootstrapSubsystem | adapter | ADAPTER | 0.98 | source-present only | Source/BS_GodFile/MelodiaIntegration/MelodiaJRPGPartyBootstrapSubsystem.h:13 |

## 4. Focused GMM Blast-Radius

Focused GMM blast radius

**Scope:** `battle_manager`, `player_state`, `save_manager`, `rhythm_clock`, `equipment`, `UI commands`, `editor startup registration`, and **every import from outside `gmm`**. Isolated prototype: no shipping authority.

| Area | Representative Files (static) | Outside `gmm` Importers (every consumer) | Note |
|---|---|---|---|
| battle_manager | Content/Python/gmm/game/battle_manager.py<br>Content/Python/gmm/main.py<br>Content/Python/gmm/melodia/battle.py | Content/Python/envui/commands.py<br>Content/Python/init_unreal.py<br>Tools/generate_and_inject_content.py<br>Tools/wardrobe_draft_lint.py | static only; runtime LIVE_EVIDENCE_REQUIRED - no engine execution |
| player_state | Content/Python/gmm/game/party.py<br>Content/Python/gmm/game/player_state.py<br>Content/Python/gmm/tests/test_player_state.py | Content/Python/envui/commands.py<br>Content/Python/init_unreal.py<br>Tools/generate_and_inject_content.py<br>Tools/wardrobe_draft_lint.py | static only; runtime LIVE_EVIDENCE_REQUIRED - no engine execution |
| save_manager | Content/Python/gmm/game/save_manager.py<br>Content/Python/gmm/tests/test_save_manager.py | Content/Python/envui/commands.py<br>Content/Python/init_unreal.py<br>Tools/generate_and_inject_content.py<br>Tools/wardrobe_draft_lint.py | static only; runtime LIVE_EVIDENCE_REQUIRED - no engine execution |
| rhythm_clock | Content/Python/gmm/game/rhythm_clock.py<br>Content/Python/gmm/tests/test_rhythm_clock.py | Content/Python/envui/commands.py<br>Content/Python/init_unreal.py<br>Tools/generate_and_inject_content.py<br>Tools/wardrobe_draft_lint.py | static only; runtime LIVE_EVIDENCE_REQUIRED - no engine execution |
| equipment | Content/Python/gmm/game/equipment_catalog.py<br>Content/Python/gmm/tests/test_equipment_catalog.py | Content/Python/envui/commands.py<br>Content/Python/init_unreal.py<br>Tools/generate_and_inject_content.py<br>Tools/wardrobe_draft_lint.py | static only; runtime LIVE_EVIDENCE_REQUIRED - no engine execution |
| UI commands | Content/Python/gmm/game/equipment_catalog.py<br>Content/Python/gmm/tests/test_equipment_catalog.py<br>Content/Python/gmm/ui/battle_gui.py | Content/Python/envui/commands.py<br>Content/Python/init_unreal.py<br>Tools/generate_and_inject_content.py<br>Tools/wardrobe_draft_lint.py | static only; runtime LIVE_EVIDENCE_REQUIRED - no engine execution |
| editor startup registration | Content/Python/envui/commands.py<br>Content/Python/gmm/ui/register.py<br>Content/Python/init_unreal.py | Content/Python/envui/commands.py<br>Content/Python/init_unreal.py<br>Tools/generate_and_inject_content.py<br>Tools/wardrobe_draft_lint.py | static only; runtime LIVE_EVIDENCE_REQUIRED - no engine execution |

**Every external `gmm` importer (complete, static):**

- `Content/Python/envui/commands.py`
- `Content/Python/init_unreal.py`
- `Tools/generate_and_inject_content.py`
- `Tools/wardrobe_draft_lint.py`

## 5. Strongly Connected Components & Dependency Cycles

SCCs: 1249 | Cycles (SCC size>1 or self-loop): 6

**Cycles:**
- Content/Python/gmm/ui/battle_menu.py -> Content/Python/gmm/ui/builder.py
- Plugins/MelodiaCore/Source/MelodiaCore/MelodiaDungeonRunCoordinator.cpp -> Plugins/MelodiaCore/Source/MelodiaCore/MelodiaRoguelikeRewardWidget.cpp -> Plugins/MelodiaCore/Source/MelodiaCore/MelodiaRoomExit.cpp
- Plugins/MelodiaCore/Source/MelodiaCore/MelodiaRhythmExecutionComponent.cpp -> Plugins/MelodiaCore/Source/MelodiaCore/MelodiaRhythmHUDWidget.cpp
- Plugins/MelodiaCore/Source/MelodiaCore/MelodiaSongDataAsset.h -> Plugins/MelodiaCore/Source/MelodiaCore/MelodiaSongSkillLibrary.cpp
- Plugins/QuillScript/Source/Quillscript/Private/Core/QuillscriptAsset.cpp -> Plugins/QuillScript/Source/Quillscript/Private/Core/QuillscriptInterpreter.cpp -> Plugins/QuillScript/Source/Quillscript/Private/Core/QuillscriptNetwork.cpp -> Plugins/QuillScript/Source/Quillscript/Private/Core/QuillscriptSettings.cpp -> Plugins/QuillScript/Source/Quillscript/Private/Core/QuillscriptSubsystem.cpp -> Plugins/QuillScript/Source/Quillscript/Private/Text/SmartTextBlockDecorator.cpp -> Plugins/QuillScript/Source/Quillscript/Private/Text/SmartTextDecorator.cpp -> Plugins/QuillScript/Source/Quillscript/Private/Text/SmartTypewriter.cpp -> Plugins/QuillScript/Source/Quillscript/Private/Utils/Evaluator.cpp -> Plugins/QuillScript/Source/Quillscript/Private/Utils/Lexer.cpp -> Plugins/QuillScript/Source/Quillscript/Private/Utils/Quill.cpp -> Plugins/QuillScript/Source/Quillscript/Private/Utils/Tools.cpp -> Plugins/QuillScript/Source/Quillscript/Private/Widgets/BackgroundBox.cpp -> Plugins/QuillScript/Source/Quillscript/Private/Widgets/DialogBox.cpp -> Plugins/QuillScript/Source/Quillscript/Private/Widgets/SelectionBox.cpp -> Plugins/QuillScript/Source/Quillscript/Private/Widgets/SpriteBox.cpp
- Tools/MaterialMaker/graph_manipulator.py -> Tools/MaterialMaker/melodia_material_maker_addon.py

<details><summary>All SCCs</summary>
- [1] Content/Python/envui/commands.py
- [1] Content/Python/envui/menu.py
- [1] Content/Python/envui/paths.py
- [1] Content/Python/gmm/core/audit.py
- [1] Content/Python/gmm/core/mcp_client.py
- [1] Content/Python/gmm/core/settings.py
- [1] Content/Python/gmm/daemon/generators.py
- [1] Content/Python/gmm/daemon/shared.py
- [1] Content/Python/gmm/daemon/tasks.py
- [1] Content/Python/gmm/family/cli.py
- [1] Content/Python/gmm/family/contracts.py
- [1] Content/Python/gmm/family/fixture.py
- [1] Content/Python/gmm/family/manifest.py
- [1] Content/Python/gmm/feel_lab.py
- [1] Content/Python/gmm/fixtures/instance_on_spline_request.json
- [1] Content/Python/gmm/fixtures/melodia_project_manifest.fixture.json
- [1] Content/Python/gmm/fixtures/niagara_nikki_library.json
- [1] Content/Python/gmm/fixtures/water_family_profiles.json
- [1] Content/Python/gmm/fixtures/water_surface_request.json
- [1] Content/Python/gmm/game/afflictions.py
- ... 1229 more singletons ...
</details>

## 6. Proposed Retirement / Merge Sequence (no deletion, no source edit)

> This sequence proposes moves only. No file deletion or source edit is performed by this atlas.

1. **Freeze the authority contract and generate this atlas in CI/offline review.** — Prevents new callers from landing while competing systems are migrated.
2. **Prove and then disable shipping creation/reachability for UMelodiaBattleSession.** — Stock JRPG must remain the only turn/damage/result executor; harvest presentation/data only.
3. **Move required MelodiaSaveGameSubsystem fragments into the stock BP_JRPGSaveGame adapter and retire its public Save/Load API.** — One canonical slot must restore all shipping state without dual-save drift.
4. **Reduce OpeningFlow to a Quill/Narrative projection and remove direct quest-manager mutation.** — Narrative progression needs one transaction owner rather than synchronization between state machines.
5. **Replace wardrobe calls to RestoreNarrativeRecord with narrow grant/equip/unequip transactions.** — An outfit mutation must not replay Quill and water load-time restore effects.
6. **Refactor UMelodiaTraversalComponent internally into movement state, resources, sensors, input, and presentation.** — Improve state validity while retaining one traversal executor and one capability provider.
7. **Delete compatibility observers/components only after static callers and live Blueprint reachability are both proven absent.** — Source absence is not Blueprint or asset absence; deletion remains an owner/runtime gate.

## 7. UNKNOWNs & LIVE_EVIDENCE_REQUIRED

UNKNOWN or low-confidence nodes: 54 | LIVE_EVIDENCE_REQUIRED flagged: 1266

Rather than guessing, these are marked `UNKNOWN` or `LIVE_EVIDENCE_REQUIRED`. If Blueprint/.uasset live state is required, mark `LIVE_EVIDENCE_REQUIRED` and continue elsewhere.

| path | symbol | domain | verdict | reason | citation |
|---|---|---|---|---|---|
| Content/Python/envui/commands.py | _log | tooling | AUTHORING | runtime proof needed | Content/Python/envui/commands.py:9 |
| Content/Python/envui/menu.py | _py_path_prefix | tooling | AUTHORING | runtime proof needed | Content/Python/envui/menu.py:4 |
| Content/Python/envui/paths.py | _project_root | tooling | AUTHORING | runtime proof needed | Content/Python/envui/paths.py:7 |
| Content/Python/gmm/core/audit.py | _project_root | tooling | PROTOTYPE | runtime proof needed | Content/Python/gmm/core/audit.py:19 |
| Content/Python/gmm/core/mcp_client.py | McpError | tooling | PROTOTYPE | runtime proof needed | Content/Python/gmm/core/mcp_client.py:17 |
| Content/Python/gmm/core/settings.py | GmmSettings | tooling | PROTOTYPE | runtime proof needed | Content/Python/gmm/core/settings.py:27 |
| Content/Python/gmm/daemon/generators.py | gen_enemy_forte | tooling | PROTOTYPE | runtime proof needed | Content/Python/gmm/daemon/generators.py:11 |
| Content/Python/gmm/daemon/shared.py | state_path | tooling | PROTOTYPE | runtime proof needed | Content/Python/gmm/daemon/shared.py:20 |
| Content/Python/gmm/daemon/tasks.py | TaskPriority | tooling | PROTOTYPE | runtime proof needed | Content/Python/gmm/daemon/tasks.py:13 |
| Content/Python/gmm/family/cli.py | validate_file | tooling | PROTOTYPE | runtime proof needed | Content/Python/gmm/family/cli.py:11 |
| Content/Python/gmm/family/contracts.py | is_known_role | tooling | PROTOTYPE | runtime proof needed | Content/Python/gmm/family/contracts.py:21 |
| Content/Python/gmm/family/fixture.py | musical_ornament_manifest | tooling | PROTOTYPE | runtime proof needed | Content/Python/gmm/family/fixture.py:5 |
| Content/Python/gmm/family/manifest.py | _required | tooling | PROTOTYPE | runtime proof needed | Content/Python/gmm/family/manifest.py:20 |
| Content/Python/gmm/feel_lab.py | FeelRun | tooling | PROTOTYPE | runtime proof needed | Content/Python/gmm/feel_lab.py:35 |
| Content/Python/gmm/fixtures/instance_on_spline_request.json | instance_on_spline_request | tooling | PROTOTYPE | runtime proof needed | Content/Python/gmm/fixtures/instance_on_spline_request.json:1 |
| Content/Python/gmm/fixtures/melodia_project_manifest.fixture.json | melodia_project_manifest.fixture | tooling | PROTOTYPE | runtime proof needed | Content/Python/gmm/fixtures/melodia_project_manifest.fixture.json:1 |
| Content/Python/gmm/fixtures/niagara_nikki_library.json | niagara_nikki_library | tooling | PROTOTYPE | runtime proof needed | Content/Python/gmm/fixtures/niagara_nikki_library.json:1 |
| Content/Python/gmm/fixtures/water_family_profiles.json | water_family_profiles | tooling | PROTOTYPE | runtime proof needed | Content/Python/gmm/fixtures/water_family_profiles.json:1 |
| Content/Python/gmm/fixtures/water_surface_request.json | water_surface_request | tooling | PROTOTYPE | runtime proof needed | Content/Python/gmm/fixtures/water_surface_request.json:2 |
| Content/Python/gmm/game/afflictions.py | AfflictionInstance | tooling | PROTOTYPE | runtime proof needed | Content/Python/gmm/game/afflictions.py:102 |
| Content/Python/gmm/game/audio_engine.py | AudioEngine | tooling | PROTOTYPE | runtime proof needed | Content/Python/gmm/game/audio_engine.py:7 |
| Content/Python/gmm/game/battle_manager.py | apply_affliction | tooling | PROTOTYPE | runtime proof needed | Content/Python/gmm/game/battle_manager.py:36 |
| Content/Python/gmm/game/battle_osc.py | _pad | tooling | PROTOTYPE | runtime proof needed | Content/Python/gmm/game/battle_osc.py:23 |
| Content/Python/gmm/game/combo_rewards.py | ComboReward | tooling | PROTOTYPE | runtime proof needed | Content/Python/gmm/game/combo_rewards.py:19 |
| Content/Python/gmm/game/config.py | TimingWindows | tooling | PROTOTYPE | runtime proof needed | Content/Python/gmm/game/config.py:34 |
| Content/Python/gmm/game/data_registry.py | EnemyStats | tooling | PROTOTYPE | runtime proof needed | Content/Python/gmm/game/data_registry.py:32 |
| Content/Python/gmm/game/elements.py | element_multiplier | tooling | PROTOTYPE | runtime proof needed | Content/Python/gmm/game/elements.py:14 |
| Content/Python/gmm/game/equipment_catalog.py | get_equipment | tooling | PROTOTYPE | runtime proof needed | Content/Python/gmm/game/equipment_catalog.py:7 |
| Content/Python/gmm/game/interaction.py | InteractableType | tooling | PROTOTYPE | runtime proof needed | Content/Python/gmm/game/interaction.py:11 |
| Content/Python/gmm/game/jrpg_bridge.py | template_action_to_melodia | tooling | PROTOTYPE | runtime proof needed | Content/Python/gmm/game/jrpg_bridge.py:65 |
| ... 1236 more ... | | | | | |

## 8. Top Duplicate-Authority Clusters

- **combat_executors**: UMelodiaBattleSession, module:Content/Python/gmm/game/battle_manager.py, module:Content/Python/gmm/main.py
- **save_owners**: UMelodiaSaveGameSubsystem, UMelodiaSaveSlotLibrary, module:Content/Python/gmm/game/save_manager.py, module:Content/Python/gmm/game/player_state.py
- **narrative_progression**: UMelodiaNarrativeSubsystem, UMelodiaOpeningFlowSubsystem, UMelodiaPersonaSubsystem
- **wardrobe_state**: UMelodiaWardrobeSubsystem, UMelodiaWardrobeComponent, UMelodiaOutfitComponent
- **rhythm_execution**: UMelodiaRhythmCombatSubsystem, UMelodiaRhythmExecutionComponent, UMelodiaBattleInputComponent, module:Content/Python/gmm/game/rhythm_clock.py
- **battle_ui**: UMelodiaUIBridgeSubsystem, UMelodiaJRPGBattleOverlaySubsystem, UMelodiaRhythmHUDWidget, module:Content/Python/gmm/ui/battle_gui.py
- **economy_state**: UMelodiaTokenWalletSubsystem, UMelodiaWardrobeGachaSubsystem, module:Content/Python/gmm/game/tokens.py

## 9. Document Drift (code vs 2026-08-20 contracts)

- **battle_overlay** — STALE_DOC: doc `The 2026-08-20 contract says UMelodiaJRPGBattleOverlaySubsystem creates a second set of battle widgets.` vs code `Current header calls it a retired compatibility observer and current cpp creates no widgets.`
- **music_world_key** — IMPLEMENTED_NOT_LIVE_PROVEN: doc `The 2026-08-20 contract labels the Piano-to-Narrative edge unwired.` vs code `UMelodiaPCGNarrativeChallengeBridgeComponent now binds OnPatternCompleted and calls CommitWorldChallenge; live attachment is still unproven statically.`
- **wardrobe_restore_coupling** — CURRENT_CODE_RISK: doc `Wardrobe is presented as a bounded capability/presentation owner.` vs code `Grant/equip/unequip call RestoreNarrativeRecord, which also restores water state and persistent Quill variables.`

## 10. Per-Node Field Legend

Every node has: `path` (normalized posix), `symbol`/`module`, `role`/`classification`, `domain`, `canonical_owner`, `runtime_reachability` (tiered), `external_consumers` (import list), `verdict` (OWNER/ADAPTER/PRESENTATION_ONLY/AUTHORING/PROTOTYPE/MERGE/DEAD_CANDIDATE/UNKNOWN), `confidence` (0-1), `citation` (`path:line`). See JSON for machine-readable graph.

---
*Generated deterministically via `Tools/authority_atlas` — AST/text parsing only, no engine execution, no timestamps.*
