# UI Figma Skin Task — Handoff for the Skinning Agent
**Date:** 2026-08-06 · **Author:** research lane (read-only) · **Status:** READY TO PASTE
**Source of truth:** `Docs/Reviews/SESSION_REVIEW_2026-08-06.md` (§3: "full UI sweep Melodia-styled" = FALSE),
`Saved/t3d-catalog.html` (live migration grid), live MCP inspection of `/Game/Melodia/UI/WBP_MainMenu`.

---

## 1. Paste this prompt into any agent

```text
TASK: Skin the remaining stock JRPG UI widgets with the Melodia Figma asset pack, using
WBP_MainMenu as the reference for what working Melodia-styled systems/buttons look like.
Project: C:\EnvironmentPortfolio\BS_GodFile (UE 5.8). Monolith MCP is live at
http://127.0.0.1:9316/mcp (tools/call with {"name": <tool>, "arguments": {action, params}};
call via `python deploy\call_mcp.py tools/call "<json>"` from repo root).

WORKING RULES (read AGENTS.md first)
- Overlay only: do NOT restructure stock widget roots, do NOT remove/reparent existing
  layout containers (Docs/LOWER_TIER_FOUNDATION_LOCK_2026-07-29.md "Battle UI / keyboard
  guidance" rule: "Overlay only; do not restructure the stock root"). Replace textures,
  fonts, tints, and states on the widgets that already exist.
- Do not touch Content\Melodia assets, the 4 already-migrated widgets
  (BP_ExploreUI, BP_HPBar, BP_MPBar, BP_ActionTimeBar), or BP_VictoryDialogue /
  BP_DefeatDialogue / WBP_ComicOrrery (already skinned).
- One small verifiable change per widget; compile and fingerprint before moving on.
- Do not add new MCP actions, properties, or flags to compensate for problems. If a
  widget's root is stock, skin it in place.

TARGET ASSETS TO SKIN (19 stock widgets, live /Game paths from t3d-catalog.html)
Primary (from session review — highest priority):
- /Game/TurnBasedJRPGTemplate/Blueprints/UI/Dialogues/BP_LevelUpDialogue      (LevelUp)
- /Game/TurnBasedJRPGTemplate/Blueprints/UI/Dialogues/BP_ItemObtainDialogue  (ItemObtain)
- /Game/TurnBasedJRPGTemplate/Blueprints/UI/MainMenu/BP_PartyUI              (Party)
- /Game/TurnBasedJRPGTemplate/Blueprints/UI/MainMenu/BP_UnitDetails          (Unit Details)
- /Game/TurnBasedJRPGTemplate/Blueprints/UI/MainMenu/BP_ItemDetails          (Item)
- /Game/TurnBasedJRPGTemplate/Blueprints/UI/MainMenu/BP_EquipmentDetails     (Equipment)
- /Game/TurnBasedJRPGTemplate/Blueprints/UI/BP_QuestNotification             (Quest)
- /Game/TurnBasedJRPGTemplate/Blueprints/UI/BP_QuestNotificationListUI       (Quest list)
- Skill surfaces (no dedicated stock BP; skin these support widgets):
  /Game/TurnBasedJRPGTemplate/Blueprints/UI/BP_SkillButton
  /Game/TurnBasedJRPGTemplate/Blueprints/UI/BP_SkillDetails
  /Game/TurnBasedJRPGTemplate/Blueprints/UI/BP_SkillUseDialogue
Remaining stock (skin after the primary set):
- /Game/TurnBasedJRPGTemplate/Blueprints/UI/Dialogues/BP_InfoDialogue
- /Game/TurnBasedJRPGTemplate/Blueprints/UI/Dialogues/BP_YesNoDialogue
- /Game/TurnBasedJRPGTemplate/Blueprints/UI/BP_DamageTextUI
- /Game/TurnBasedJRPGTemplate/Blueprints/UI/BP_EnemyUnitUI
- /Game/TurnBasedJRPGTemplate/Blueprints/UI/BP_PlayerUnitUI
- /Game/TurnBasedJRPGTemplate/Blueprints/UI/BP_TargetIcon
- /Game/TurnBasedJRPGTemplate/Blueprints/UI/BP_UnitClass
- /Game/TurnBasedJRPGTemplate/Blueprints/UI/BP_InteractionUI
- /Game/TurnBasedJRPGTemplate/Blueprints/UI/BP_MobileUI
- /Game/TurnBasedJRPGTemplate/Blueprints/UI/BP_CraftBar
- /Game/TurnBasedJRPGTemplate/Blueprints/UI/BP_FadeTransitionUI
Live T3D exports to diff against are in Saved\T3D\live_catalog\ (23 exports, re-exported
2026-08-06 — use these, NOT Saved\T3D\full_catalog which is stale).

FIGMA TEXTURE INVENTORY (all at /Game/Melodia/UI/Textures/Figma/, imported 2026-08-04)
Full group listing with /Game paths — see section 2 of
Docs\Handoffs\UI_FIGMA_SKIN_TASK_2026-08-06.md. Quick reference of the most reusable:
- Buttons: T_Melodia_Figma_Button_Premium, T_Melodia_Figma_Button_Premium-Primary,
  T_Melodia_Figma_Button_-_F_key(+___Interact), T_Melodia_Figma_Button_-_J_key(+___Confirm),
  T_Melodia_Figma_Button_-_K_key(+___Cancel), T_Melodia_Figma_KeybindButton,
  T_Melodia_Figma_State_Hover / State_Pressed / State_Disabled
- Panels/containers: T_Melodia_Figma_Container(+_margin,_transform), T_Melodia_Figma_Card
  (+_margin,_Blessing,_Burden,_Image,_Premium,_Portal_gold,_Portal_iris,_Portal_sakura),
  T_Melodia_Figma_SoftMG_ParchmentPanel, T_Melodia_Figma_SoftMG_ScrollEdge,
  T_Melodia_Figma_SheetParchment, T_Melodia_Figma_SheetSurface, T_Melodia_Figma_SheetEchoSoft,
  T_Melodia_Figma_SheetHead, T_Melodia_Figma_SheetMusicBackground, T_Melodia_Figma_Frame,
  T_Melodia_Figma_Section, T_Melodia_Figma_Cover_Frame, T_Melodia_Figma_Toast(+_transform),
  T_Melodia_Figma_TurnOrderBanner, T_Melodia_Figma_BreakdownGrid, T_Melodia_Figma_ChoiceCards,
  T_Melodia_Figma_StatusBadge, T_Melodia_Figma_CombatBar(+_margin), T_Melodia_Figma_BarRow
- Dividers/pipes/ornament: T_Melodia_Figma_DividerScroll, T_Melodia_Figma_Divider_Glyph,
  T_Melodia_Figma_MagicalDivider(+_margin), T_Melodia_Figma_FiligreeDividerWave,
  T_Melodia_Figma_FiligreeOrnament, T_Melodia_Figma_gold-rule, T_Melodia_Figma_ornate_staff_lines,
  T_Melodia_Figma_style_divider/_DividerScroll/_DividerWave/_CornerBaroque/_CornerOrnate/
  _crest/_CrestBaroque/_CrestFinale/_MedallionRosette/_GradeHalo/_LaneRail,
  T_Melodia_Figma_BraceVolute/_CornerBaroque/_CrestBaroque/_MedallionRosette,
  T_Melodia_Figma_ScrollArm(+_transform), T_Melodia_Figma_Game_ScrollBorderRail,
  T_Melodia_Figma_Variant_pipes(+_dot,_spark), T_Melodia_Figma_Variant_astral/_diamond,
  T_Melodia_Figma_Game_FiligreeBatchO_Baroque(+_BraceVolute,_CornerBaroque,_CrestBaroque,_DividerScroll)
- Type specimens: T_Melodia_Figma_Type_type_body-default/_body-large/_caption/_display-large/
  _display-xl/_header-section/_header-sub/_label-technical/_metadata/_title-project,
  T_Melodia_Figma_Type_Live_SSOT_Specimens__canonical_, T_Melodia_Figma_TypeSpace_Root/_Spacing,
  T_Melodia_Figma_Heading_1/_Paragraph/_Text/_Text_margin/_TitleCol/_SectionTitle/_Header
- Battle rhythm rows: T_Melodia_Figma_RhythmLane, T_Melodia_Figma_lane_A/_B/_C/_D,
  T_Melodia_Figma_NoteHighway(+_dim), T_Melodia_Figma_Hitline, T_Melodia_Figma_NoteObject,
  T_Melodia_Figma_turn_rail, T_Melodia_Figma_Game_PlaybackHead/_MeasureMarker/_SPMeter/_ULTMeter
- Equipment/item/element icons: T_Melodia_Figma_BootsIcon/_HelmIcon/_RingIcon/_SwordIcon/
  _GuardIcon/_PotionIcon/_HealIcon/_IceIcon/_NatureIcon/_TideIcon/_EmberIcon/_SpellbookIcon/
  _StrikeIcon/_GemDiamond/_PearlBadge/_Icon/_IconCell
- Foundations/tokens (DA_MelodiaDesignTokens at /Game/Melodia/Data/DA_MelodiaDesignTokens):
  T_Melodia_Figma_Foundations_Gold/_Iri/_Ivory/_Plum/_Root/_Semantic (+ all *_color_* swatches)
- Cosmic backgrounds: T_Melodia_Figma_asset_mi_MI_Cosmic_BlueNebulaC/_EclipseHalo/
  _PurpleNebulaA/B/C/_StarfieldA/B/C/_VoidDeep, T_Melodia_Figma_AuroraLayer,
  T_Melodia_Figma_shader_overlay, T_Melodia_Figma_Game_IriShaderOverlay
- Universal already-proven set (used by WBP_MainMenu + BP_ExploreUI):
  /Game/Melodia/UI/Textures/Universal/T_Melodia_Universal_ParchmentFrame,
  T_Melodia_Universal_DividerScroll, T_Melodia_Universal_CrestBaroque,
  T_Melodia_Universal_CornerBaroque, T_Melodia_Universal_BraceVolute,
  T_Melodia_Universal_MedallionRosette, T_Melodia_Universal_Hitline,
  T_Melodia_Universal_RhythmLaneInk, T_Melodia_Universal_SealSP, T_Melodia_Universal_SealULT

REFERENCE — what a working Melodia button/panel looks like (WBP_MainMenu,
/Game/Melodia/UI/WBP_MainMenu, owner-confirmed good; verified live via ui_query
get_widget_tree + export_asset_text on 2026-08-06):
- Font for all labels: /Game/Melodia/UI/Fonts/F_Melodia_UI — Size 19, LetterSpacing 70,
  Justification Center, ColorAndOpacity mint (R=0,G=214,B=158,A=1). Use this font for
  every TextBlock you skin.
- Button recipe (stock UMG Button, no style class): WidgetStyle = FButtonStyle,
  Normal/Hovered/Pressed/Disabled all DrawAs=Box with Margin 0.28/0.28/0.28/0.28 and
  ResourceObject = /Game/Melodia/UI/Textures/Universal/T_Melodia_Universal_ParchmentFrame,
  differing only in TintColor:
    Normal   = (0.015, 0.008, 0.025, 0.87)   near-black plum
    Hovered  = (0.122, 0.061, 0.159, 0.97)   plum-purple lift
    Pressed  = (0.0065, 0.004, 0.0116, 1.0)  darkest
    Disabled = (0.0086, 0.006, 0.0123, 0.47) faded
  Foreground: NormalForeground = gold (0.949, 0.839, 0.620), HoveredForeground = iris cyan
  (0.471, 0.922, 1.0), PressedForeground = gold. NormalPadding = (30,15,30,15),
  PressedPadding = (30,17,30,13) (label drops 2px when pressed). BackgroundColor = (0,46,61,0.95).
- Panel recipe (layered Images on CanvasPanel, same slot geometry):
  wash Image at ZOrder 0 + reading panel Image at ZOrder 1; corner ornaments (MenuCornerTop/
  Bottom style) at ZOrder 2; divider Image at ZOrder 4; crest at ZOrder 4; text stack
  ZOrder 3-8. Background layers fill screen at ZOrder -30..-1 (Background, CosmicVoid,
  NebulaParchment, right-side rosette). Everything is a plain Image widget with a brush —
  no material instances, no effects layers.
- Keyboard nav: explicit Up/Down WidgetNavigation chains between sibling buttons (Rule=Explicit).

METHOD
1. Per widget: record baseline via blueprint_query get_graph_fingerprint
   (action params: asset_path) and save it. Work from the live T3D text in
   Saved\T3D\live_catalog\ (run `python Tools\t3d_blueprint_injector.py --help` first;
   it submits whole specs as one JSON-RPC tools/call; declarative one-shot builder is
   blueprint_query action build_blueprint_from_spec).
2. Replace stock textures (T_MenuBackground, T_CircleButton, T_TurnbasedJRPG*,
   T_BasicButton etc.) with the Figma assets above; swap fonts to F_Melodia_UI; apply the
   MainMenu button/panel recipe. Do NOT add or remove slots, containers, or the root.
3. compile_blueprint (action params: asset_path) until 0 errors, 0 warnings that reference
   your change. Then re-run get_graph_fingerprint and confirm the delta is only
   brush/font/tint/value changes (no topology change) — optionally assert with
   assert_graph_matches against the baseline fingerprint.
4. save_asset (action params: asset_path) per widget. At the end run
   blueprint_query save_dirty_assets to close the data-loss window, and check
   list_errored_blueprints == 0 (AGENTS.md: check before AND after your session).
5. Do not save unrelated dirty packages; do not touch Content\Melodia or the 4 migrated
   widgets or Victory/Defeat/Orrery.
6. Optional verification: `python Tools\bp_regression_checker.py --all` for fingerprint
   baselines, and re-export a widget's T3D (project_query export_asset_text) to confirm
   the Melodia refs landed in live text.

ACCEPTANCE CRITERIA (per widget)
- [ ] Stock textures replaced with Figma/Universal Melodia textures (grep the re-exported
      live T3D: no T_TurnbasedJRPG*, T_MenuBackground, T_CircleButton refs remain)
- [ ] All TextBlocks on F_Melodia_UI font (or MainMenu-consistent mint/gold/iris colors
      where font must stay default)
- [ ] compile_blueprint: 0 errors
- [ ] get_graph_fingerprint before/after: topology unchanged (brush/font/tint-only diff)
- [ ] save_asset + save_dirty_assets done; list_errored_blueprints == 0
- [ ] Stock root structure untouched (overlay-only rule)
Report per-widget: path, textures swapped, compile result, fingerprint delta, saved.
```

---

## 2. Evidence appendix

### 2.1 Figma texture inventory (339 assets, `Content\Melodia\UI\Textures\Figma\`)
All paths below are `/Game/Melodia/UI/Textures/Figma/<name>`. Sizes shown are .uasset
bytes on disk (textures are bulk; large entries are full-resolution exports).

| Group | Assets (count) | Notes |
|---|---|---|
| **Buttons & keybinds** (10) | `Button_Premium`, `Button_Premium-Primary`, `Button_-_F_key`, `Button_-_F_key___Interact`, `Button_-_J_key`, `Button_-_J_key___Confirm`, `Button_-_K_key`, `Button_-_K_key___Cancel`, `KeybindButton`, plus `State_Hover/Pressed/Disabled` | Direct button-state kit; premium pair = likely primary/CallToAction |
| **Panels, containers, cards** (24) | `Container(+_margin,_transform)`, `Card(+_margin,_Blessing,_Burden,_Image,_Premium,_Portal_gold/iris/sakura)`, `Cover_Frame`, `Frame`, `Section`, `Header`, `SoftMG_ParchmentPanel`, `SoftMG_ScrollEdge`, `SheetParchment`, `SheetSurface`, `SheetEchoSoft`, `SheetHead`, `SheetMusicBackground`, `Toast(+_transform)`, `TurnOrderBanner`, `BreakdownGrid`, `ChoiceCards`, `SpecCardTable`, `StatusBadge` | `_margin` variants (Container 375 KB, Card 612 KB) are 9-slice-capable box frames; `SoftMG_ParchmentPanel` 691 KB is the premium panel |
| **Dividers / pipes / ornament** (35) | `DividerScroll`, `Divider_Glyph`, `MagicalDivider(+_margin)`, `FiligreeDividerWave`, `FiligreeOrnament`, `gold-rule`, `ornate_staff_lines`, `ScrollArm(+_transform)`, `BraceVolute`, `CornerBaroque`, `CrestBaroque`, `MedallionRosette`, `style_divider/_DividerScroll/_DividerWave/_CornerBaroque/_CornerOrnate/_crest/_CrestBaroque/_CrestFinale/_MedallionRosette/_GradeHalo/_LaneRail`, `Variant_pipes(+_dot,_spark)`, `Variant_astral`, `Variant_diamond`, `Game_FiligreeBatchO_Baroque(+4 sub-parts)`, `Game_ScrollBorderRail`, `Motion_BaroqueMedallion`, `Motion_BraceVoluteSheen` | The "variant pipes" from the brief are `Variant_pipes*`; style_* set is the reusable ornament grammar |
| **Type specimens** (20) | `Type_type_body-default/_body-large/_caption/_display-large/_display-xl/_header-section/_header-sub/_label-technical/_metadata/_title-project`, `Type_Live_SSOT_Specimens__canonical_`, `TypeSpace_Root`, `TypeSpace_Spacing`, `Heading_1`, `Paragraph`, `Text(+_margin)`, `TitleCol`, `SectionTitle` | Reference only — text in game uses `F_Melodia_UI` font, not textures |
| **Battle rhythm / HUD** (38) | `CombatBar(+_margin)`, `BarRow`, `RhythmLane`, `lane_A/B/C/D`, `NoteHighway(+_dim)`, `Hitline`, `SoftMG_Hitline__was_NoteBeam_`, `NoteObject`, `turn_rail`, `axis_track`, `Game_PlaybackHead`, `Game_MeasureMarker`, `Game_BattleRhythm(+Advanced,_Refined)`, `Game_RhythmReactivityBoard`, `Game_SheetMusicRoll`, `Game_SheetMusicHUD___Desktop/_Mobile`, `Game_SPMeter`, `Game_ULTMeter`, `Game_IntensityWarning`, `rhythm_hud_locked`, `Game_BattleCommand`, `Game_BattleEnemy`, `Game_BattleMobile`, `Game_BattleResults`, `Game_ElementWheel`, `Game_PartyScore`, `Game_ResonanceBond`, `Game_FieldHUD`, `Game_DialogueOverlay`, `Game_DissonanceBanner`, `Game_SectionHeader`, `Game_Title`, `Game_MovementLabel`, `Game_SoftMG_Kit` (1.1 MB), `_BattleEnemyTurn`, `_BattleToughnessBreak`, `GradePop`, `grade_Good/Great/Miss/Perfect`, `FiligreeGradeHalo_Good/Great/Miss/Perfect` | Grade set already in use by skinned Victory/Orrery widgets |
| **Equipment / item / element icons** (21) | `BootsIcon`, `HelmIcon`, `RingIcon`, `SwordIcon`, `GuardIcon`, `PotionIcon`, `HealIcon`, `IceIcon`, `NatureIcon`, `TideIcon`, `EmberIcon`, `SpellbookIcon`, `StrikeIcon`, `GemDiamond`, `PearlBadge`, `Icon`, `IconCell` (95 KB), `MaterialSwatchCard`, `Game_SkillCodex`, `Game_SongCodexFull`, `Game_SongCodexGrid` | Directly reusable for Equipment/Item/Skill rows |
| **Foundations / tokens** (32) | `Foundations_Gold/_Iri/_Ivory/_Plum/_Root/_Semantic` + `*_color_*` swatches (gold 100/300/500/700, iri cyan/gold/magenta/pearl/purple, ivory 50/100/200/300, plum 500-900, semantic accent_astral/iris/primary, surface_base/raised/sunken) + `Foundations_*_Row` | Matches `DA_MelodiaDesignTokens`; swatches are reference swatches |
| **Cosmic / background** (13) | `asset_mi_MI_Cosmic_BlueNebulaC`, `_EclipseHalo`, `_PurpleNebulaA/B/C`, `_StarfieldA/B/C`, `_VoidDeep`, `Asset_MI_Sphere`, `AuroraLayer` (3.1 MB), `shader_overlay` (1.8 MB), `Game_IriShaderOverlay` (1.9 MB) | Full-screen backdrop candidates |
| **Motion FX** (12) | `Motion_BreakReveal`, `Motion_GradePopLuxury`, `Motion_IdleBreathe`, `Motion_OrrerySparkleOrbit`, `Motion_PerfectStreak`, `Motion_PortraitIri`, `Motion_SoftMG_Baroque`, `Motion_SparkleBurst`, `Motion_SparkleDrift`, `Motion_ULTReady` | For animated widgets only (not in this pass) |
| **Orrery / showcase** (12) | `MagicalOrrery` (941 KB), `Motion_OrrerySparkleOrbit`, `Placeholder_for_MagicalOrrery`, `HeroShowcase`, `Embed_Hero/_Passport/_SectionHeader`, `Passport_Banner`, `LandscapeSplatCard`, `LoopPreviewSlot`, `NiagaraPreviewSlot`, `Template_EnvironmentShowcase` | Already used by `WBP_ComicOrrery` (14 refs) |
| **Spec pages / docs rows** (50+) | `Page_*`, `row_*`, `Embed_*`, `Template_*`, `slot_*`, `thumb_zone`, `preview`, `QA_Index`, `Tech_Index`, `Readiness_matrix`, `T_Melodia_Figma_Redesign_UI_with_Magical_Girl_Theme` (10.9 MB), `EssentialUI_readiness_update___2026-07-16`, `Web_Shop___MG_Sync_Notes`, `TypeSpace_*`… | Figma documentation frames, NOT game assets — do not use |
| **Universal proven set** (10) | `/Game/Melodia/UI/Textures/Universal/T_Melodia_Universal_{ParchmentFrame, DividerScroll, CrestBaroque, CornerBaroque, BraceVolute, MedallionRosette, Hitline, RhythmLaneInk, SealSP, SealULT}` | The already-proven set — ParchmentFrame is THE button/panel brush in WBP_MainMenu and BP_ExploreUI |

### 2.2 WBP_MainMenu reference findings (live MCP, 2026-08-06)
`ui_query get_widget_tree` + `project_query export_asset_text` on `/Game/Melodia/UI/WBP_MainMenu`
(parent `UserWidget`; 28 widgets; BlueprintGuid `080280874E8AEE9FACA2B495078C316C`).

**Structure** — `RootCanvas` (CanvasPanel) hosts 18 direct children:
- Background stack (full-screen, fill anchors): `Background` Image (Collapsed, z=-30),
  `CosmicVoid` Image (Collapsed, z=-29), `NebulaParchment` Image (HitTestInvisible, z=-20),
  `MenuWorldRosette` Image (right-anchored, z=-1).
- Panel stack: `MenuPanelWash` Image (z=0) + `MenuReadingPanel` Image (z=1), same slot
  (left 46 / top 44 / right 674 / bottom 44, anchored left-full-height); `MenuCornerTop` +
  `MenuCornerBottom` (z=2), `MenuDivider` (z=4), `MenuCrest` (z=4).
- Text stack (z=3..8): `MenuKicker`, `MenuSubtitle`, `MenuSectionLabel`, `MenuCornerNote`,
  `MenuWorldKicker`, `MenuWorldTitle`, `TitleText`, `SaveStateText`.
- `ButtonContainer` (VerticalBox, z=7) → `Btn_Continue`, `Btn_NewGame`, `Btn_LoadGame`,
  `Btn_Settings` (UMG `Button`), each with one label TextBlock child.

**Button recipe (verbatim from T3D)** — see §1 paste block: 4-state `FButtonStyle` all on
`T_Melodia_Universal_ParchmentFrame` (DrawAs=Box, Margin 0.28), differing only in tint;
gold/iris foregrounds; NormalPadding (30,15,30,15) / PressedPadding (30,17,30,13);
`BackgroundColor (0,46,61,0.95)`; label font `F_Melodia_UI` Size 19 LetterSpacing 70
(exception: `BtnLabel_Settings` uses default font object but same size/color);
label color mint (0,214,158); explicit Up/Down navigation chains; tooltips.

**Key takeaways for the skin agent**
1. No style classes, no CommonUI, no material instances — plain UMG `Button` +
   `FButtonStyle` with a single 9-slice texture + tint per state.
2. Panels = layered plain `Image` widgets with a brush; `_margin`/`_transform` Figma
   textures are the 9-slice candidates; wash (z0) + panel (z1) + corners (z2) + divider (z4).
3. Font = `F_Melodia_UI` (also the "true migration" marker in HPBar/MPBar/ActionTimeBar).
4. Foreground state colors: gold 0.949/0.839/0.620, iris 0.471/0.922/1.0.

### 2.3 Stock-widget evidence (from `Saved\t3d-catalog.html` + `Saved\T3D\live_catalog\`)
- 23/23 widgets re-exported live 2026-08-06 (15.59 MB, 5,649 nodes); 22/23 drifted vs 08-05.
- **4/23 truly migrated**: `BP_ExploreUI` (ParchmentFrame), `BP_HPBar`/`BP_MPBar`/
  `BP_ActionTimeBar` (F_Melodia_UI font only — still stock brushes).
- **19/23 STOCK** — the skin targets listed in §1. Representative stock texture markers:
  `T_MenuBackground`, `T_CircleButton`, `T_TurnbasedJRPG*` (confirmed in
  `BP_PartyUI`, `BP_EquipmentDetails` live exports).
- Skinned so far (session review): Victory 5 refs, Defeat 1, `WBP_ComicOrrery` 14 refs —
  i.e. exactly 3 of 23 widget classes carry Figma/Universal Melodia refs.

### 2.4 Pipeline gates (verified live in MCP tools/list)
- `blueprint_query`: `get_graph_fingerprint`, `assert_graph_matches`, `compile_blueprint`,
  `validate_blueprint`, `save_asset`, `save_dirty_assets`, `build_blueprint_from_spec`,
  `export_graph`, `get_dependencies`.
- `ui_query`: `get_widget_tree`, `set_brush`, `set_font`, `set_widget_property`,
  `set_slot_property`, `batch_style`, `build_ui_from_spec`, `compile_widget`.
- `project_query`: `export_asset_text` (used to verify Melodia refs land in live T3D).
- Offline: `Tools\t3d_blueprint_injector.py` (batch T3D spec injection),
  `Tools\bp_regression_checker.py` (fingerprint baseline comparison).
- Contract preflight: `Content\Python\verify_melodia_ui_contract.py` covers the battle
  HUD (WBP_Battle_Rhythm / WBP_GradePop) — untouched by this pass; run it anyway as a
  final sanity check that nothing in the battle path regressed.

## 3. Blockers
- None. Monolith MCP live at 127.0.0.1:9316 (standard tools/list + tools/call; the old
  `monolith_discover <namespace>` syntax on the raw endpoint returns
  "Unknown method: monolith_discover — use tools/list to enumerate available tools,
  then tools/call").
- Note: `list_errored_blueprints` was NOT visible in the `blueprint_query` action list
  (132 actions) — if the gate needs it, it lives in the editor/material namespace
  (`tools/list` again), or use `validate_blueprint` per asset.
- `BP_Skill*` (Skill UI) has no standalone stock widget in the T3D catalog — the skill
  surfaces are `BP_SkillButton` / `BP_SkillDetails` / `BP_SkillUseDialogue` under
  `/Game/TurnBasedJRPGTemplate/Blueprints/UI/`; the skin agent should treat them as the
  "Skill" target.
