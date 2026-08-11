# Melodia UI Asset Inventory — 2026-08-03

**Purpose:** Single authoritative table mapping Figma → Web → UE → missing, so the stock-UI replacement list is one source of truth.
**Sources:** `MELODIA_LUXURY_UI_FILIGREE_NIKKI_MOTION_PLAN_2026-07-12.md`, `MELODIA_UE58_INTEGRATION_ARCHITECTURE_2026-07-26.md`, `MELODIA_AUTHORITATIVE_RHYTHM_COMBAT_WIRING_2026-08-03.md`, Kiro 2026-08-01 accounting.

---

## 1. Available — Figma SSOT (authored)

| Asset | Figma Location | Notes |
|-------|---------------|-------|
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

## 3. Available — UE (current, verified 2026-08-03)

| Asset | Path | Status |
|-------|------|--------|
| `WBP_Battle_Rhythm` | `/Game/Melodia/UI/` | Compiled; highway host hierarchy (HitWindow, JudgementText, ComboText, ClockSourceText) |
| `BP_BattleUI` | `/Game/TurnBasedJRPGTemplate/Blueprints/UI/` | Hosts `MelodiaNoteHighway` child; Show/Hide lifecycle visibility wired (161 nodes/153 conns) |
| `BP_MelodiaRhythmPrompt` | `/Game/MelodiaIntegration/UI/` | Existing rhythm prompt host |
| `WBP_SkillCodex` | `/Game/Melodia/UI/` | Skill presentation surface |
| `DT_MelodySlime_Skills` | `/Game/MelodiaIntegration/Blueprints/` | Skill data reference |

## 4. Stock UI to Replace (template primitives)

| Stock Asset | Verdict | Action |
|-------------|---------|--------|
| `BP_InfoDialogue` | Template modal | Keep as primitive; not narrative |
| `BP_YesNoDialogue` | Template modal | Keep as primitive |
| `BP_DialogueButton` | Generic button | Keep as primitive |
| JRPG `Dialogues/` folder | Not a narrative substitute | QuillScript is the narrative layer |
| `Conversation2DSampleUI` / `Conversation2DSampleShopUI` | Obsolete sample | Exclude from migration |

## 5. Missing WBPs (not yet scaffolded)

| WBP | Priority | Source |
|-----|----------|--------|
| Command phase WBP | P1 | Luxury plan §B2 |
| Enemy phase WBP | P1 | Luxury plan §B2 |
| Results phase WBP | P1 | Luxury plan §B2 |
| FieldHUD WBP | P1 | Luxury plan §B2 |
| Title WBP | P1 | Luxury plan §B2 |
| ElementWheel / SP / ULT meter WBPs | P1 | Luxury plan §B2 |
| SheetMusicRoll / NoteGlyph / PlaybackHead atoms | P1 | Luxury plan §B2 |
| DialogueOverlay | P2 | Luxury plan §B2 |

## 6. Pass L3 UE Catch-up (unchecked)

- [ ] Reimport Batch O atlas
- [ ] Bitmap filigree + note-head bind (exit tint-only)
- [ ] Designer BindWidgets for Mobile + Grade pop FX
- [ ] Scaffold/author missing phase WBPs
- [ ] MPC/Quartz hooks (after visual parity)

## 7. Rhythm UI Wiring Status (2026-08-03)

| Item | Status |
|------|--------|
| `WBP_Battle_Rhythm` hierarchy | ✅ Compiled/saved |
| `BP_BattleUI` hosts `MelodiaNoteHighway` | ✅ 161 nodes/153 conns, 0 errors |
| Show/Hide lifecycle visibility | ✅ Wired |
| Rhythm-session lifecycle visibility | ⏳ Remaining |
| Note scheduling (VideoRenderTime/Quartz) | ⏳ Remaining |
| Input grading (ExperiencedTime) | ⏳ Remaining |
| JudgementText/ComboText/ClockSourceText bindings | ⏳ Remaining |
| Text-color serializer readback | ⚠️ Known issue |

---

**End of Inventory**