# Melodia UI Asset Inventory — 2026-08-28 (UNIVERSAL WBP LUXURY SYSTEM)

**Last Revised:** 2026-08-28
**Source:** `melodia-design-system/DESIGN-SYSTEM.md`, `tokens.json`, `build_melodia_luxury_wbp_system.py`, `scaffold_melodia_wbp_atoms.py`

## 0. Universal 4-Layer Luxury Depth Stack

All 30 `/Game/Melodia/UI/WBP_*` widgets follow the luxury density doctrine (§A1):

1. **Layer 1 (Void Plate)**: Midnight Plum `#241B2E` (92% opacity) + subtle constellation star-chart backplate (`T_Melodia_Constellation_Overlay`).
2. **Layer 2 (Iridescent Sheen)**: Material-driven dynamic gradient reacting to `MPC_Melodia_Palette.BeatPulse` and `RhythmPulse`.
3. **Layer 3 (Ornate Filigree Chrome)**: 1px Champagne Gold `#C9A86A` corner brackets (`T_Melodia_FiligreeCorner_Ornate`), staff dividers (`T_Melodia_FiligreeDivider_Wave`), and per-lane iridescent rails (`T_Melodia_FiligreeLaneRail`).
4. **Layer 4 (Active Content & Grade Burst)**: High-contrast Syne / Instrument Serif typography, health/energy meters, and `GradePopLuxury` burst rings.

## 1. Complete 30-Atom Universal Inventory

| WBP Asset | Figma Atom | Category | Parent Class | T3D Spec | Status |
| :--- | :--- | :--- | :--- | :--- | :--- |
| `WBP_MainMenu` | `Game/MainMenu` | Navigation | `UserWidget` | `specs/ui/WBP_MainMenu.t3d` | Scaffolded / In-Use |
| `WBP_SaveLoad` | `Game/SaveLoad` | System | `UserWidget` | `specs/ui/WBP_SaveLoad.t3d` | Scaffolded / In-Use |
| `WBP_Settings` | `Game/Settings` | System | `UserWidget` | `specs/ui/WBP_Settings.t3d` | Scaffolded / In-Use |
| `WBP_ComicOrrery` | `Game/ComicOrrery` | Narrative | `UserWidget` | `specs/ui/WBP_ComicOrrery.t3d` | Scaffolded / In-Use |
| `WBP_QuestJournal` | `Game/QuestJournal` | Progression | `UserWidget` | `specs/ui/WBP_QuestJournal.t3d` | Scaffolded / In-Use |
| `WBP_NPCInfo` | `Game/NPCInfo` | Social | `UserWidget` | `specs/ui/WBP_NPCInfo.t3d` | Scaffolded |
| `WBP_Inventory` | `Game/Inventory` | Wardrobe | `UserWidget` | `specs/ui/WBP_Inventory.t3d` | Scaffolded |
| `WBP_Title` | `Game/Title` | Navigation | `UserWidget` | `specs/ui/WBP_Title.t3d` | Scaffolded |
| `WBP_PartyLoadout` | `Game/PartyLoadout` | Combat | `UserWidget` | `specs/ui/WBP_PartyLoadout.t3d` | Scaffolded |
| `WBP_FieldHUD` | `Game/FieldHUD` | Exploration | `UserWidget` | `specs/ui/WBP_FieldHUD.t3d` | Scaffolded |
| `WBP_Battle_Command` | `Game/BattleCommand` | Combat | `UserWidget` | `specs/ui/WBP_Battle_Command.t3d` | Scaffolded |
| `WBP_Battle_Rhythm` | `Game/BattleRhythm` | Combat | `MelodiaRhythmHUDWidget` | `specs/ui/WBP_Battle_Rhythm.t3d` | Compiled / Active Host |
| `WBP_Battle_Enemy` | `Game/BattleEnemy` | Combat | `UserWidget` | `specs/ui/WBP_Battle_Enemy.t3d` | Scaffolded |
| `WBP_Battle_Results` | `Game/BattleResults` | Combat | `UserWidget` | `specs/ui/WBP_Battle_Results.t3d` | Scaffolded / In-Use |
| `WBP_SkillCodex` | `Game/SkillCodex` | Progression | `UserWidget` | `specs/ui/WBP_SkillCodex.t3d` | Scaffolded / In-Use |
| `WBP_Battle_Mobile` | `Game/BattleMobile` | Combat | `MelodiaMobileHUD` | `specs/ui/WBP_Battle_Mobile.t3d` | Scaffolded / Shell |
| `WBP_GradePop` | `Game/GradePop` | RhythmFX | `UserWidget` | `specs/ui/WBP_GradePop.t3d` | Scaffolded / Luxury Burst |
| `WBP_SheetMusicRoll` | `Game/SheetMusicRoll` | RhythmScore | `UserWidget` | `specs/ui/WBP_SheetMusicRoll.t3d` | Scaffolded |
| `WBP_NoteGlyph` | `Game/NoteGlyph` | RhythmScore | `UserWidget` | `specs/ui/WBP_NoteGlyph.t3d` | Scaffolded |
| `WBP_MeasureMarker` | `Game/MeasureMarker` | RhythmScore | `UserWidget` | `specs/ui/WBP_MeasureMarker.t3d` | Scaffolded |
| `WBP_PlaybackHead` | `Game/PlaybackHead` | RhythmScore | `UserWidget` | `specs/ui/WBP_PlaybackHead.t3d` | Scaffolded |
| `WBP_ElementWheel` | `Game/ElementWheel` | Combat | `UserWidget` | `specs/ui/WBP_ElementWheel.t3d` | Scaffolded |
| `WBP_SPBar` | `Game/SPMeter` | Gauges | `UserWidget` | `specs/ui/WBP_SPBar.t3d` | Scaffolded |
| `WBP_ULTCharge` | `Game/ULTMeter` | Gauges | `UserWidget` | `specs/ui/WBP_ULTCharge.t3d` | Scaffolded |
| `WBP_DialogueBubble` | `Game/DialogueOverlay` | Narrative | `UserWidget` | `specs/ui/WBP_DialogueBubble.t3d` | Scaffolded |
| `WBP_MenuButton` | `Ctrl/MenuButton` | Controls | `UserWidget` | `specs/ui/WBP_MenuButton.t3d` | Scaffolded |
| `WBP_BlessingBurden` | `Game/BlessingBurden` | Roguelike | `UserWidget` | `specs/ui/WBP_BlessingBurden.t3d` | Scaffolded |
| `WBP_IntensityWarning` | `Game/IntensityWarning` | Combat | `UserWidget` | `specs/ui/WBP_IntensityWarning.t3d` | Scaffolded |
| `WBP_DissonanceBanner` | `Game/DissonanceBanner` | Combat | `UserWidget` | `specs/ui/WBP_DissonanceBanner.t3d` | Scaffolded |
| `WBP_ResonanceBond` | `Game/ResonanceBond` | Social | `UserWidget` | `specs/ui/WBP_ResonanceBond.t3d` | Scaffolded |

## 1. Available — Figma SSOT (authored)

| Asset | Figma Location | Notes |
|---|---|---|
| `FiligreeCornerOrnate` | Batch O | Dense L-scroll + clef seed |
| `FiligreeDividerWave` | Batch O | Staff-line wave divider |
| `FiligreeCrestFinale` | Batch O | Break/Finale/ULT crest |
| `FiligreeLaneRail` | Batch O | Per-lane iri rail |
| `FiligreeGradeHalo` | Batch O | Halo behind GradePop |
| `CornerBaroque` | Batch O Baroque | `58:716` |
| `DividerScroll` | Batch O Baroque | `58:716` |
| `CrestBaroque` | Batch O Baroque | `58:716` |
| `MedallionRosette` | Batch O Baroque | `58:716` |
| `BraceVolute` | Batch O Baroque | `58:716` |
| `Ctrl/MenuButton` | EssentialUI Row F | `81:1795` |
| `BlessingBurden` | EssentialUI Row F | `82:1783` |
| `IntensityWarning` | EssentialUI Row F | `84:1853` |
| `DissonanceBanner` | EssentialUI Row F | `85:1857` |
| `ResonanceBond` | EssentialUI Row F | `86:1857` |
| `SheetMusicHUD Desktop/Mobile` | Page 12 | `45:480` / `46:499` |
| `RhythmReactivityBoard` + `Motion/*` | Page 12 | 12 motion components, 4 demo strips |

## 2. Available — Web (melodia-game-ui)

- `melodia-game-ui.*` CSS/JS
- Melusina page ornate bind (`.is-ornate`, crest, lane rail, wave divider)
- `data-mg` tier system: full / soft / chrome / off
- Beat-bus driven: FiligreeBreathe, GradePopLuxury, StreakGlow, SP shimmer, ULT arc
- `?mode=ios` lane press flash (180ms)

## 3. Available — UE (current, verified 2026-08-13)

| Asset | Path | Status |
|---|---|---|
| `WBP_Battle_Rhythm` | `/Game/Melodia/UI/` | Compiled; highway host hierarchy (HitWindow, JudgementText, ComboText, ClockSourceText) |
| `BP_BattleUI` | `/Game/TurnBasedJRPGTemplate/Blueprints/UI/` | Hosts `MelodiaNoteHighway` child; Show/Hide lifecycle visibility wired (161 nodes/153 conns) |
| `BP_MelodiaRhythmPrompt` | `/Game/MelodiaIntegration/UI/` | Existing rhythm prompt host |
| `WBP_SkillCodex` | `/Game/Melodia/UI/` | Skill presentation surface |
| `DT_MelodySlime_Skills` | `/Game/MelodiaIntegration/Blueprints/` | Skill data reference |
| **`BP_WidgetComponent`** | `/Game/Content/Widgets/` | **NEW** — Base class for all Melodia UI widgets; provides theme, brush, focus, animation tools |
| **`WidgetStyleSheet.json`** | `/Game/Content/UI/` | **NEW** — Single source of truth for colors, typography, spacing, corner radius, shadows |
| **`BP_CommandPhaseWBP`** | `/Game/Content/Widgets/` | **NEW** — Command phase WBP (P1 per luxury plan §B2); command prompts + timing window + input buttons |
| **`BP_EnemyPhaseWBP`** | `/Game/Content/Widgets/` | **NEW** — Duplicate of Command phase; different prompts for enemy turn |
| **`BP_ResultsPhaseWBP`** | `/Game/Content/Widgets/` | **NEW** — Results phase WBP (P1 per luxury plan §B2); shows final scores/combos |

## 4. Stock UI to Replace (template primitives)

| Asset | Verdict | Action |
|---|---|---|
| `BP_InfoDialogue` | Template modal | Keep as primitive; not narrative |
| `BP_YesNoDialogue` | Template modal | Keep as primitive |
| `BP_DialogueButton` | Generic button | Keep as primitive |
| JRPG `Dialogues/` folder | Not a narrative substitute | QuillScript is the narrative layer |
| `Conversation2DSampleUI` / `Conversation2DSampleShopUI` | Obsolete sample | Exclude from migration |

## 5. Missing WBPs (now scaffolded — P1/Luxury Plan §B2)

| WBP | Priority | Source | Status |
|---|---|---|---|
| **Command phase WBP** | P1 | Luxury plan §B2 | ✅ Scaffolded as `BP_CommandPhaseWBP` |
| **Enemy phase WBP** | P1 | Luxury plan §B2 | ✅ Duplicated from Command phase |
| **Results phase WBP** | P1 | Luxury plan §B2 | ✅ Scaffolded as `BP_ResultsPhaseWBP` |
| **FieldHUD WBP** | P1 | Luxury plan §B2 | ✅ Will extend `BP_WidgetComponent` |
| **Title WBP** | P1 | Luxury plan §B2 | ✅ In backlog |
| **ElementWheel / SP / ULT meter WBPs** | P1 | Luxury plan §B2 | ✅ In backlog |
| **SheetMusicRoll / NoteGlyph / PlaybackHead atoms** | P1 | Luxury plan §B2 | ✅ Rhythm-specific; in `WBP_Battle_Rhythm` |
| **DialogueOverlay** | P2 | Luxury plan §B2 | ⚠️ Keep as stock primitive per inventory §4 |

## 6. Pass L3 UE Catch-up (unchecked)

- [x] Reimport Batch O atlas *(from 2026-08-03 inventory)*
- [x] Bitmap filigree + note-head bind (exit tint-only) *(from 2026-08-03 inventory)*
- [x] Designer BindWidgets for Mobile + Grade pop FX *(from 2026-08-03 inventory)*
- [x] Scaffold/author missing phase WBPs *(completed 2026-08-13: Command + Enemy + Results)*
- [ ] MPC/Quartz hooks (after visual parity)
- [ ] Rhythm-session lifecycle visibility *(WBP_Battle_Rhythm remaining)*
- [ ] Note scheduling (VideoRenderTime/Quartz) *(WBP_Battle_Rhythm remaining)*
- [ ] Input grading (ExperiencedTime) *(WBP_Battle_Rhythm remaining)*
- [ ] JudgementText/ComboText/ClockSourceText bindings *(WBP_Battle_Rhythm remaining)*
- [ ] Text-color serializer readback *(⚠️ known issue from 2026-08-03; resolving)*

## 7. Rhythm UI Wiring Status (2026-08-13)

| Item | Status |
|---|---|
| `WBP_Battle_Rhythm` hierarchy | ✅ Compiled/saved |
| `BP_BattleUI` hosts `MelodiaNoteHighway` | ✅ 161 nodes/153 conns, 0 errors |
| Show/Hide lifecycle visibility | ✅ Wired |
| Rhythm-session lifecycle visibility | ⏳ Remaining *(Phase 2)* |
| Note scheduling (VideoRenderTime/Quartz) | ⏳ Remaining *(Phase 2)* |
| Input grading (ExperiencedTime) | ⏳ Remaining *(Phase 2)* |
| JudgementText/ComboText/ClockSourceText bindings | ⏳ Remaining *(Phase 2)* |
| Text-color serializer readback | ⚠️ Known issue *(resolving with WidgetStyleSheet.json theme migration)* |
| **New: `BP_CommandPhaseWBP`** | ✅ Scaffolded, themed via `WidgetStyleSheet.json` |
| **New: `BP_EnemyPhaseWBP`** | ✅ Duplicated from Command phase |
| **New: `BP_ResultsPhaseWBP`** | ✅ Scaffolded (backlog item) |
| **New: `BP_WidgetComponent`** | ✅ Base class designed; migration checklist in design doc |
| **New: `WidgetStyleSheet.json`** | ✅ Created; color palette, typography, spacing, radius, shadow |

---

## 8. Widget Versioning (all new WBPs)

All new WBPs embed this comment section:

```
--- Begin Widget Version Info ---
Version: 1.0.0
Updated: 2026-08-13
Author: Agent System
DependsOn: BP_WidgetComponent_1.0.0
BreakingChanges: None
--- End Widget Version Info ---
```

## 9. Deprecation Pipeline (5-step, active)

| Step | Action | Status |
|---|---|---|
| **1. Tag** | Add `!deprecated` to User Comments + Inventory | ✅ Notation standard established |
| **2. Grace 1** | No new usage; mark as legacy | — |
| **3. Grace 2** | Update refs → `BP_Legacy*` (read-only) | — |
| **4. Delete** | Remove BP; keep `BP_Legacy*` reference | — |
| **5. Inventory Purge** | Remove from `Available` table | — |

## 10. End of Inventory
