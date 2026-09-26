# GOAL — Rhythm highway gets the Persona treatment + p4 submit of today's UI content (2026-09-26, owner: "updated goal; give the rhythm highway the same love")

Parent: `2026-09-26_p0-ui-working-goal.md` (U1a/b calibration + windows done, U3 HUD/minimap done).
Surface: `UMelodiaRhythmHUDWidget::PaintNoteHighway` / `PaintBattleHUD` (MelodiaCore, native paint) under `WBP_MelodiaRhythmHighway` (QWOP labels). One writer: this widget. Proof level: `MelodiaIntegrationMap` battle trigger, PIE `Shot showui` + log.

## What reads flat today (from the code)
- Judgement pop: linear 1.5 s fade + slow grow — no anticipation/overshoot, not beat-locked.
- Hit notes are only recoloured and keep scrolling; no burst at the hit line, no lane flash. Missed notes look like hits.
- Hit line never pulses with the music; no approach cue as a note arrives.

## Beat-locked motion (128 BPM: 1/8 = 117 ms, 1/4 = 234 ms, beat = 469 ms; scale by clock BPM)
- **HL1 Grade pop:** 0 → 117 ms scale 0.85 → 1.18 (overshoot), 117 → 234 ms settle to 1.0, hold to 469, fade 469 → 703. Per-grade colour; Perfect adds a ring flash.
- **HL2 Hit burst:** when a note resolves, it stops scrolling and becomes a ring at the hit line in its lane (expands + fades over 234 ms, grade colour). Lane column flashes for 117 ms.
- **HL3 Miss read:** unresolved notes that pass the line dim and drop away over 234 ms instead of vanishing like hits.
- **HL4 Beat pulse:** hit line thickens/brightens on every beat, decays over 117 ms (reads MPC BeatPhase wrap, same as the chassis).
- **HL5 Approach cue:** last 1/4 beat before the line, the note scales 1.0 → 1.2 and brightens.
- Gate: PIE battle on MelodiaIntegrationMap, captures mid-chart showing burst + pop; `Melodia` headless suite unchanged (101/103).

## p4 submit (owner "yes" to planning it; submit waits for explicit OK)
- New numbered changelist "UI 09-26: overworld HUD, minimap, orrery chassis, calibration content". Move ONLY: 14 `Content/Melodia/UI/HUD/Textures/*`, `WBP_Melodia_OverworldHUD`, 3 `Content/Melodia/UI/Orrery/Meshes/*`, `WBP_ComicOrrery`, `BP_MelodiaExploreUI`, `BP_MelusinaJRPGCharacter`, `DA_MelodiaPersonaContent`, + reconcile-add the 7 `Content/UI/AssetKit_20260926/*.svg`.
- Leave in default CL untouched: `.mcp.json`, the 4 `L_MelusinaMorning` external-actor changes (editor-opened; owner to review).
- Verify `p4 describe` file count = 29 before `p4 submit -c N`.
