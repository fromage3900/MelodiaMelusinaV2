> ⚠️ **SUPERSEDED by [`Docs/BLUEPRINT_WIRING_CONTRACT_2026-08-07.md`](../BLUEPRINT_WIRING_CONTRACT_2026-08-07.md)**
>
> This handoff (08-03) contains instructions that are partially incorrect. The 08-07 contract doc
> corrects them:
>
> 1. **"Mark UMG widgets as Is Variable = true"** — Section §4 step 2. **Superseded.** The 08-07
>    contract confirms that `BindWidget` auto-resolves widgets by `Name` regardless of the `Is Variable`
>    flag; manually toggling Is Variable is unnecessary and risks generating dangling variable nodes
>    that pollute the graph. The fix is purely C++ side (add `BindWidget` or `BindWidgetOptional` to
>    the member declarations). See `BLUEPRINT_WIRING_CONTRACT.md` §3.1.
> 2. **"Poor grade multiplier = 0.5"** — Section §4 lists `0.5 Poor`. **Incorrect.** The canonical
>    `EMelodiaRhythmGrade` scalar table (Decision 041, in `MelodiaRhythmCombatTypes.h`) is
>    `Poor=0.35, Good=1.0, Great=1.2, Perfect=1.5`. The 0.5 figure was from an uncommitted draft.
>    See `BLUEPRINT_WIRING_CONTRACT.md` §4.2.
>
> This file is retained for historical audit only. **Do not follow its instructions.**

# Kimi UI Wiring & Integration Notes — 2026-08-03

**For:** Kimi (UI lane)
**From:** Cline (runtime/backend lane)
**Status:** These are the concrete editor-side wiring items. The C++ backend is build-green and registered.

---

## 1. Rhythm Text Bindings (the concrete gap — from live widget audit)

`WBP_Battle_Rhythm` (parent class `MelodiaRhythmHUDWidget`) has:
- `HitWindow` (Image) — `is_variable: true` ✅
- `JudgementText` (TextBlock) — **`is_variable: false`** ❌
- `ComboText` (TextBlock) — **`is_variable: false`** ❌
- `ClockSourceText` (TextBlock) — **`is_variable: false`** ❌

**The C++ `MelodiaRhythmHUDWidget` cannot bind the 3 text widgets because they aren't flagged as variables.**

### Fix
1. In `WBP_Battle_Rhythm`, mark `JudgementText`, `ComboText`, `ClockSourceText` as **Is Variable = true**.
2. Confirm the C++ `MelodiaRhythmHUDWidget` declares them with `BindWidget`/`BindWidgetOptional`.
3. Bind them to the music-clock / adapter delegates (the C++ exposes `OnMelodiaBeat`/`OnMelodiaBar` and the rhythm subtype).

**Until this lands, the highway text stays static** ("READY / COMBO 0 / CLOCK: WAITING") — expected, non-blocking.

## 2. UE Figma Import (Pass L3)

- Reimport the **Batch O atlas** (filigree: CornerOrnate, DividerWave, CrestFinale, LaneRail, GradeHalo) — exit tint-only.
- Bind bitmap filigree + note-heads.
- Designer BindWidgets for Mobile + Grade pop FX.
- Scaffold missing phase WBPs: Command / Enemy / Results / Field / Title.
- Source: `Docs/MELODIA_LUXURY_UI_FILIGREE_NIKKI_MOTION_PLAN_2026-07-12.md` §Pass L3.

## 3. Rhythm → Stock Resolver Hookup

The seam is in `BP_BattleUI` (verified live via Monolith):
- `OnSkillSelectedHandler` / `OnUnitHasEnoughMP` are where a skill resolves.
- Wire `UMelodiaRhythmCombatSubsystem::ConsumePendingRequest` there so the rhythm request feeds the stock damage/heal/SP/turn resolver.
- The C++ is ready (the subsystem produces the request); this is the editor-side consumption.

## 4. Author First Skill DataAsset Rows

Create `UMelodiaRhythmSkillDefinition` assets (pure data, no code):
- **Cadence Strike** — Vigorous → Damage + Crit (single-target)
- **Lullaby Mend** — Calm → Heal + RemoveDebuff (ally recovery)
- **Dissonant Silence** — Sad → Debuff (enemy debuff)

Each row: SkillId, niche, effect type, MIDI params (TempoBPM, key, time signature, pattern asset, note density, intro/active/outro beats), base magnitude, target, SP cost, grade multipliers, presentation theme.

Register them in `UMelodiaRhythmCombatSubsystem` (call `RegisterSkill` at startup).

---

## Backend already done (do not redo)
- `UMelodiaRhythmCombatSubsystem` (session lifecycle, skill catalog, `SubmitRatedInput`, wallet integration)
- `UMelodiaRhythmSkillDefinition` (data asset class)
- `FMelodiaAuthoritativeRhythmResult` / `FMelodiaRhythmEffectRequest` / `EMelodiaRhythmEffectType`
- Harmonix clock registration in `MelodiaJRPGPresentationRhythmComponent`
- Build green (0 errors)

---

**End of Kimi Notes**