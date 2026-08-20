# Melodia UI Asset Inventory — 2026-08-13 (UPDATED)

**Last Revised:** 2026-08-13 (this session)  
**Source:** `BP_WidgetComponent_Base_Design.md`, `WidgetStyleSheet.json`, `BP_CommandPhaseWBP`

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
