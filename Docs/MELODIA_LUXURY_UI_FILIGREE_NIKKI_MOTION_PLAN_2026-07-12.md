# Melodia Luxury HUD + Ornate Filigree + Nikki Rhythm Motion Plan

**Date:** 2026-07-12  
**Status:** Plan (ready to execute)  
**Grandmaster:** https://www.figma.com/design/Yx8ud7n39NdWZvnNvo4Xlf/Untitled · key `Yx8ud7n39NdWZvnNvo4Xlf`  
**Depends on:** [MELODIA_FIGMA_AAA_SYSTEMS_PLAN_2026-07-12.md](MELODIA_FIGMA_AAA_SYSTEMS_PLAN_2026-07-12.md) · [MELODIA_MELUSINA_GAME_UX.md](MELODIA_MELUSINA_GAME_UX.md) · [DEEPSEEK §16 Nikki Doctrine](DEEPSEEK_RHYTHM_GAMEPLAY_HANDOFF.md#16-infinity-nikki-aesthetic-doctrine) · [MELODIA_CORE_LOOP_GAP_INVENTORY](MELODIA_CORE_LOOP_GAP_INVENTORY_2026-07-11.md)

---

## North star

Elevate Melodia combat UI from “pretty prototype” to **luxury celestial sheet-music HUD** — Nikki-adjacent romance without sacrificing Theatrhythm / HSR readability — by:

1. Raising luxury density (materials, depth, type hierarchy, safe-frame polish).
2. Expanding ornate filigree chrome and closing **core-system atom gaps**.
3. Shipping an **advanced Figma motion system** for beat-reactive Nikki styling, then bridging web → UE.

**Do not:** flip `store_live`, monetize the rhythm game, or dual-lineage HUD under JRPG Minimal chrome.

---

## Current baseline (honest)

| Layer | Maturity | Gap for “luxury + Nikki reactivity” |
|-------|----------|-------------------------------------|
| Figma 12–13 + Batch N atlas | High | MotionDemo is basic loops; no full rhythm-reactivity timeline board |
| Web Melusina (`melodia-game-ui.*`) | High | Filigree mostly static/CSS; MPC→UI table still manual |
| UE NativePaint + Rhythm/GradePop/Mobile shell | Medium | Tint filigree only; most phase WBPs missing; BindWidgets designer |
| Core loop resolve / songcraft | Separate P0 | Luxury UI can ship ahead of C++ resolve parity |

---

## Pillar A — Luxury feeling (visual & hierarchy)

### A1. Luxury density bar (definition of done)

A frame feels “luxury” when:

- **Depth stack ≥ 4 layers:** void plate → iri sheen → filigree → content → grade/sparkle FX.
- **One hero zone** per MelodiaCore phase; secondary chrome drops ≥40% opacity.
- **Type:** Syne / Instrument Serif / Bricolage / Azeret only (page 01–02 tokens).
- **Iri ramp discipline:** Perfect=`iri/gold`, Great=`iri/cyan`, Good=`iri/pearl`, Miss=`iri/magenta` — never flat white.
- **Material doctrine (Nikki §16):** layered glow with summed emissive feel ≤ ~0.5; pastel + sparkle without washing BaseColor.
- **Safe frame:** 1440×810 desktop; portrait thumb zone bottom 35% mobile.

### A2. Surfaces to elevate (ordered)

| Priority | Surface | Action |
|----------|---------|--------|
| P0 | `Game/BattleRhythmRefined` + Melusina web rhythm | Add depth stack, richer crest/corner, staff vignette |
| P0 | `Game/GradePop` variants | Luxury grade pop: filigree burst ring + iri fill + numeral hierarchy |
| P1 | Command / Enemy / Results frames | Match Rhythm luxury language (same tokens, phase-dim rules) |
| P1 | Mobile `Game/BattleMobile` | Luxury within thumb zone — no chrome under fingers |
| P2 | Title / FieldHUD / SkillCodex | Passport / lookbook continuity with Melusina marketing bands |
| P2 | Portfolio Melusina page chrome | Soft MG tier + lookbook connectors (already Pass A — refine density) |

### A3. Luxury craft rules

- Prefer **ornament + light** over cards/shadow stacks.
- Filigree must read as *jewelry framing the score*, not clutter on the highway.
- Numerals (combo, grade, meters) stay high-contrast; romance lives in frames/FX.
- Web proof first (`melodia-melusina.html`); Figma is SSOT; UE follows bitmap bind.

---

## Pillar B — Ornate filigrees + core-system gaps

### B1. Filigree expansion (Batch O — “Atelier Ornate”)

Extend beyond Batch N corner / divider / crest:

| New atom | Role | Atlas / export |
|----------|------|----------------|
| `Game/FiligreeCornerOrnate` | Dense L-scroll + clef seed (P0/P1 density variants) | `T_Melodia_FiligreeCorner_Ornate` |
| `Game/FiligreeDividerWave` | Staff-line wave divider between HUD bands | `T_Melodia_FiligreeDivider_Wave` |
| `Game/FiligreeCrestFinale` | Break / Finale / ULT crest | `T_Melodia_FiligreeCrest_Finale` |
| `Game/FiligreeLaneRail` | Per-lane iri rail under note highway | `T_Melodia_FiligreeLaneRail` |
| `Game/FiligreeGradeHalo` | Halo ring behind GradePop | `T_Melodia_FiligreeGradeHalo` |
| `Game/IriShaderOverlay` v2 | Beat-gated sheen intensity props | Keep overlay; add Reactivity variants |

**Export path:** `pipeline/figma/export_melodia_game_ui_assets.py --ornate-only` · lock via `ART_SOURCE.json`.  
**World kitbash note:** `SM_Orn_FiligreeRing` stays **3D SKU** (HandRemake/WIP) — do not confuse with HUD filigree.

### B2. Core-system atom gaps (from UX atom→WBP map)

Fill missing gaps so Figma/web/UE share one inventory:

| Gap | Figma | Web | UE | Priority |
|-----|-------|-----|----|----------|
| Bitmap filigree bind | Batch N + O | CSS + PNG | NativePaint tint → brush bind | P0 |
| `WBP_Battle_Mobile` BindWidgets | `Game/BattleMobile` | `?mode=ios` | Shell exists — designer tree | P0 |
| Command / Enemy / Results WBPs | Present | Phase switch | Scaffold → author | P1 |
| FieldHUD / Title / SkillCodex | Present | Thin / specs | Scaffold | P1 |
| ElementWheel / SP / ULT meters | Present | Partial CSS | Missing WBP | P1 |
| SheetMusicRoll / NoteGlyph / PlaybackHead | Present | Partial | Missing atoms | P1 |
| DialogueOverlay | Present | Specs | Missing | P2 |
| Quartz one-clock → UI | Spec only | Rules JSON clock | Time-based only | P2 (after luxury) |
| MPC_Portfolio_Audio → meters | AudioReactivitySpec page 06 | Manual table | Unwired | P1 motion bridge |
| Songcraft resolve / Break payoff | N/A (gameplay) | N/A | Core loop P0 | Parallel Claude lane |

### B3. Gap-close sequence

```text
Batch O Figma filigree set
  → export atlas + ART_SOURCE lock
  → web Melusina bind ornate PNGs
  → UE reimport EnvSandbox GameUI textures
  → NativePaint / WBP brush bind (filigree + note heads)
  → scaffold remaining WBP atoms (editor idle)
  → designer BindWidgets for Mobile + phase boards
```

---

## Pillar C — Advanced Figma motion plan (Nikki rhythm reactivity)

### C1. Motion authority

| Source | Role |
|--------|------|
| Figma page **13** MG Chrome | Tier budgets (`data-mg` full/soft/chrome/off) |
| Figma page **12** `Game/MotionDemo` | Extend → full Rhythm Reactivity board |
| Page **06** `AudioReactivitySpec` | Bass / mid / high → UI channel map |
| DEEPSEEK §16 | Nikki glow / sparkle / iri doctrine |
| Implement path | `get_motion_context` → CSS / web → UE anim blueprints |

### C2. New Figma board: `Game/RhythmReactivityBoard` (page 12)

Create a **timeline-driven** board (not just 2.5s decorative loops) with named motion components:

| Component | Beat role | Nikki cue | Duration / ease |
|-----------|-----------|-----------|-----------------|
| `Motion/FiligreeBreathe` | OnBeat (1/1) | Soft scale 1.0→1.02 + iri opacity | 400ms easeOut, loop |
| `Motion/StaffShimmer` | Bass band | Horizontal sheen sweep on staff plate | 600ms, gated by bass > threshold |
| `Motion/NoteTrailIri` | Perfect hit | Cyan→gold trail along lane | 280ms |
| `Motion/GradePopLuxury` | Judgment | Halo expand + numeral punch + sparkle burst | Perfect 420 / Great 360 / Good 300 / Miss 240 |
| `Motion/HitlinePulse` | Hit window | Gold hitline bloom | ±window ms synced |
| `Motion/StreakGlowEdge` | Combo ≥3/5/8 | Edge glow ramp green→cyan→gold | Crossfade 200ms per tier |
| `Motion/BreakCrestReveal` | Toughness break | CrestFinale scale + gold flash | 500ms |
| `Motion/ULTArcPulse` | High band / ULT ready | Arc ring pulse | 800ms loop until fire |
| `Motion/SPMeterShimmer` | Bass-driven SP | Meter fill shimmer | Continuous while SP rising |
| `Motion/PhaseDim` | Phase change | Non-active zones → 40% | 250ms |
| `Motion/PortraitIri` | Melusina idle | Soft iri rim on portrait column | 2.4s boomerang |
| `Motion/MobileLanePress` | Lane tap | Thumb ripple + filigree corner flash | 180ms |

**Variants:** `Desktop` / `Mobile` / `SoftMG` (portfolio) / `CombatFull` (PIE).

### C3. Reactivity channel matrix (design contract)

| Channel | Source (target) | Drives |
|---------|-----------------|--------|
| `Beat` | MelodiaRhythmExecution / web clock | FiligreeBreathe, HitlinePulse |
| `Bass` | MPC_Portfolio_Audio (future) / proxy | StaffShimmer, SPMeterShimmer |
| `Mid` | MPC | Note trail intensity |
| `High` / `Onset` | MPC | ULTArcPulse, sparkle density |
| `Grade` | BattleSession judgment | GradePopLuxury, NoteTrailIri |
| `Streak` | Combo count | StreakGlowEdge |
| `Break` | Toughness break | BreakCrestReveal |
| `Phase` | MelodiaCore phase | PhaseDim |

Until Quartz/MPC automation: Figma + web use **proxy drivers** (beat clock + simulated bands); document as manual table (existing UX pattern).

### C4. Figma authoring workflow (advanced)

1. **Variables:** bind opacity/scale/color to page 01–02 iri tokens (push from `figma_variables_update.json` when ready).
2. **Component sets:** each `Motion/*` as component with props `Intensity` (0–1), `Grade`, `Tier`.
3. **Timeline cohorts:** group FiligreeBreathe + HitlinePulse + StaffShimmer under one beat root so `get_motion_context(recursive=true)` returns synchronized cohorts.
4. **MotionDemo v2:** replace single 2.5s loop with **4 demo strips** — Idle breathe · Hit Perfect streak · Break reveal · ULT ready.
5. **Page 13 lock:** map each motion to `data-mg` tier (full = combat; soft = Melusina marketing; chrome = filigree-only; off = a11y).
6. **Export:** still frames for atlas where needed; motion stays Figma→code via MCP `get_motion_context`, not video-as-SSOT (optional `export_video` for review only).

### C5. Implementation bridge (after Figma board)

| Step | Target | Notes |
|------|--------|-------|
| 1 | Web `melodia-game-ui.css/js` | Port keyframes from `get_motion_context` snippets; gate with `data-mg` + beat bus |
| 2 | Code Connect | Map `Motion/*` → Melusina selectors |
| 3 | UE | Anim / Material Parameter Collections on HUD; Prefer bitmap filigree bound first |
| 4 | Proof | Melusina page demo strip + PIE judgment FX checklist |

---

## Phased delivery

### Pass L1 — Luxury + Filigree design (Figma, ~1–2 sessions)

- [x] Author Batch O filigree atoms on page 12 — `Game/FiligreeBatchO` (`40:334`)
- [x] Elevate `BattleRhythmRefined` + `GradePop` luxury density (Batch O corners/rail/crest + GradeHalo)
- [x] Build `Game/RhythmReactivityBoard` + Motion/* set — board `41:242`
- [x] Extend `Game/MotionDemo` → v2 strips (legacy renamed; 4 strips on ReactivityBoard)
- [x] Update page 13 motion budget rows for new Motions
- [x] Screenshot pack → `Saved/Audit/luxury_ui_figma_pass/`

### Pass L2 — Web proof

- [x] Ornate PNG/CSS bind in Melusina (`.is-ornate`, crest, lane rail, wave divider)
- [x] Beat-bus driven FiligreeBreathe / GradePopLuxury / StreakGlow / SP shimmer / ULT arc
- [x] Soft MG marketing band uses soft tier; combat strip uses reactivity attrs
- [x] `?mode=ios` lane press flash (180ms)
- [x] Reactivity board + Batch O sections on Melusina; design-specs deep links

### Pass L2.6 — Batch N deprecate + portfolio chrome (2026-07-16)

- [x] Figma page 12: rename `Game/MusicalFiligree` → `DEPRECATED/Game/MusicalFiligree`, `Game/NoteGlyph` → `DEPRECATED/Game/NoteGlyph`; callout frame `66:531`
- [x] ART_SOURCE: `deprecated_batch_n` + `portfolio_chrome_pass` (SkillRing / ComboBurst / GothicFrame*)
- [x] Generator `Tools/_gen_melodia_musical_filigree_chrome.py` — pearl/gold/iri-cyan on void
- [x] Web: skill-strip ring + combo-cartouche burst via `data-mg` soft|chrome|full only (phase machine untouched)
- [x] Gothic frame corners on Melusina SheetMusicHUD rhythm panel
- [ ] Continue gothic / recruiter portfolio graphics on application-hub + design-specs
- [ ] UE: do not reimport retired Batch N NoteHead / non-Baroque Filigree slots

### Pass L2.5 — Motion + Baroque expand (2026-07-16)

- [x] Keyframe all four RhythmReactivityBoard strips + SoftMG_Baroque (timeline 2.4s) — board `41:242`
- [x] New `Game/FiligreeBatchO_Baroque` (`58:716`): CornerBaroque · DividerScroll · CrestBaroque · MedallionRosette · BraceVolute
- [x] Melusina `#final-polish` section checklist (SheetHUD → Motion → Baroque → iOS → web bind → UE L3)
- [x] Export baroque atlas → `melodia-game-ui/` + ART_SOURCE lock
- [x] Web CSS instances for baroque variants on SoftMG / SheetMusicHUD corners
- [x] SoftMG quieter breathe (2.4s) vs CombatFull (520ms); title crest + brace bind
- [x] Deploy Melusina + baroque PNGs to gh-pages (2026-07-16)
- [x] Filigree SSOT: default CSS + MG nav ticks + design-specs + Melusina phases → CornerBaroque / DividerScroll
- [x] Editorial iri: SoftMG 2.4s kicker/title ramp; ivory no longer kills clip; game-eyebrow iridescent
- [x] design-specs → shared site-nav + data-mg soft; Melusina Editorial.init for dream/MG boot

### Pass L2.7 — Essential UI Figma SSOT (2026-07-16)

- [x] Page 12 `Melodia/EssentialUI` (`69:767`): MainMenu, SaveLoad, Settings, ComicOrrery, Quest, NPC, Inventory, Party, battle/field elevations, sparkle motion atoms, and readiness matrix.
- [x] Page 13 `MG/SparkleTierBudget` (`72:2284`) strip only; use full/soft/chrome/off density budgets for sparkle handoff.
- [x] Scaffold map extended for Essential UI WBP atoms; node audit: `Saved/Audit/melodia_essential_ui_figma_20260716.md`.

### Pass L2.8 — First-Slice Essentials Figma (desktop, 2026-07-17)

- [x] Page 12 `Melodia/EssentialUI` new `Row F · First-Slice Essentials (Desktop)` (`79:1783`): `Ctrl/MenuButton` set (`81:1795`), `Game/BlessingBurden` (`82:1783`), `Game/IntensityWarning` (`84:1853`), `Game/DissonanceBanner` (`85:1857`), `Game/ResonanceBond` (`86:1857`).
- [x] Scoped to the documented [first 20-minute vertical slice](MELODIA_FIRST_20_MINUTES_VERTICAL_SLICE.md); JRPG suite (Shop/Bestiary/Status/Map/Craft/Achievements/Party/Inventory) deferred per the slice doc.
- [x] Readiness matrix 3rd line + node audit [melodia_essential_ui_rowF_20260717.md](../Saved/Audit/melodia_essential_ui_rowF_20260717.md); WBP scaffold map + [wiring plan §7](MELODIA_FIGMA_UI_WIRING_PLAN_2026-07-16.md) extended (gaps F1–F4).
- [x] SoftMG + Baroque only; Nikki §16 glow discipline; HSR/Genshin readability; Persona-5 menu inversion on the Pressed button state.

### Pass L3 — UE catch-up

- [ ] Reimport Batch O atlas
- [ ] Bitmap filigree + note-head bind (exit tint-only)
- [ ] Designer BindWidgets Mobile + Grade pop FX
- [ ] Scaffold / author missing phase WBPs (Command → Results → Field → Title)
- [ ] Optional: MPC / Quartz hooks after visual parity

### Pass L4 — Docs + honesty

- [ ] Refresh AAA plan Pass B/C checkboxes
- [ ] Update UX audio-reactivity table with channel matrix
- [ ] Code Connect selectors for Motion/*
- [ ] Keep package→Figma automation unwired until Pass D

---

## Priority matrix

| P | Item | Owner |
|---|------|--------|
| P0 | RhythmReactivityBoard + luxury GradePop/Filigree | Figma |
| P0 | Bitmap filigree bind path (web then UE) | Codex → Claude |
| P0 | Mobile BindWidgets | Designer / Claude |
| P1 | Batch O atlas export + Melusina ornate bind | Codex |
| P1 | Remaining battle phase frames luxury pass | Figma + web |
| P1 | SP/ULT meter shimmer wired to proxy channels | Web → UE |
| P2 | Quartz one-clock + real MPC | Claude (after L3 visuals) |
| P2 | Songcraft resolve gaps | Claude (parallel, core loop) |
| P3 | Package→Figma automation | Pipeline |

---

## Success criteria

- Melusina rhythm frame passes **luxury density bar** (4-layer depth, iri grades, ornate filigree).
- Batch O atoms exist in Figma + atlas lock + web.
- `RhythmReactivityBoard` demos Idle / Perfect streak / Break / ULT with Nikki doctrine readable in ≤0.5s.
- Core atom inventory: no orphan Figma `Game/*` without web selector **or** documented UE deferral.
- Combat clarity preserved (highway + grades) under full MG motion tier.

---

## Do / don't

**Do**

- Figma SSOT → web proof → UE bind  
- Nikki romance in frames/FX; clarity in numerals/notes  
- Reuse lookbook / MG tier system  

**Don't**

- Auto-regen TrebleClef / MusicalCorner / Tokens for HUD (separate HandRemake lane)  
- Claim Quartz/MPC automation before wired  
- Overdraw emissive (Nikki §16 washout lesson)  
- Parent Melusina atoms under JRPG Minimal HUD lineage  

---

## Addendum — SheetMusicHUD composition reweight (2026-07-14)

**Atoms are library units; HUD presentation is a continuous score.**

- Figma page **12** beauty SSOT: `SheetMusicHUD / Desktop` (`45:480`) + `SheetMusicHUD / Mobile` (`46:499`) — parchment/staff sheet + integral filigree scrollwork, not an atom rail of chips/pills.
- Batch O chrome (`FiligreeCornerOrnate`, `FiligreeDividerWave`, `FiligreeCrestFinale`, `FiligreeLaneRail`, `FiligreeGradeHalo`) reads as **one framing jewelry system**.
- Web: `#phase-rhythm.game-ui-sheet-master`; legacy chip/meter/dialogue piles use `.is-legacy-atom` (off by default).
- Grades = notation flourishes (halo + filigree), not floating toast chips.
- UE WBP brush bind remains a follow-up after web+Figma sign-off.