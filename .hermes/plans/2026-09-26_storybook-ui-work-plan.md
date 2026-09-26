# WORK PLAN — Storybook UI system, live in game (2026-09-26, owner: "updated work plan from the work I did while you were gone + all Figma updates")

Supersedes the open parts of `2026-09-26_p0-ui-working-goal.md` and `2026-09-26_rhythm-highway-love-goal.md`.

## What changed while Claude was away (verified on disk / p4 / Figma API)
- **p4 CL 225** "UI 09-26: overworld HUD, minimap, orrery chassis, calibration content" — the UI content is in the depot.
- **Rhythm highway HL1–HL5 implemented** in `UMelodiaRhythmHUDWidget` (+383/−? lines): grade pop owns `LastGradePopTime` (fixes the beat-pulse flicker bug), `FMelodiaHighwayBurst` rings, lane flashes, resolved/miss tracking incl. the "resolved notes disappear from the push" path, BPM tracked from pushed beat positions, all amplitudes scaled by the motion tier. Built (MelodiaCore DLL 00:00 > source 23:34). **Live gate PARTIAL** (`Saved/Audit/rhythm_highway_20260926/highway_cue_gate.json`): the battle never started — the gate script called Python names that don't exist (`handle_quill_notification`, `handle_narrative_battle_requested`, `on_skill_selected_handler`).
- Minimap palette scoped into a namespace (unity-build redefinition fix with the calibration widget). Built.
- Jev anim-readiness audit (`Prototypes/JevAnimReadinessAudit/`): sheep readiness 2 (blocker thresholds+resave 0.71), Sir readiness 1 (wire existing clip first 0.9; riskiest: no Sir source blend 0.40). `ABP_ChoralSheep` modified.
- **Uncommitted:** `CURRENT_STATE.md` 09-26 block (my miss — it didn't land in `340fff560`), HL source, minimap fix, `ABP_ChoralSheep`, Morning external actors (editor-opened in p4 default CL, not ours).

## Figma "Melusina Menu UI / 2" — updates 02:58 and 03:28 (API-read)
- New page **"02 — Melodia UI System / Storybook Kit"**: Foundations, Component Families, Page Archetypes, **Motion Grammar**, Components Library, Templates Gallery.
- **Real components now:** 6 sets / 23 variants — `MDL / Medallion` (Compass·Music·Heart × Night·Light), `Plaque` (Night·Light × M·L), `Divider` (Ribbon·Crest × themes), `Sparkle` (Crystal·Cluster·Glint), `Page Frame`, `Portrait Frame` (Oval·Circle).
- **Compendium storybook:** "The interface becomes an object" (Codex v5: closed relic → mechanical bloom → living instrument), Archive Index (Characters / Worlds / Instruments + Relics·Songs·Creatures), entry prototypes Melusina · Faraway Mother · Sonic Scepter; 15 Smart-Animate links at 450 ms.
- **Motion grammar:** GLINT 0–160 · UNSEAL 120–340 · BLOOM 340–560 (restrained overshoot) · ORBIT 560–860 · BREATHE 860+. At 128 BPM this is ≈ beat-locked already: 1/8 (117) · ¾ beat (352) · 1¼ (586) · 1⅞ (879).
- Foundations: pearl · deep water · champagne gold · cyan · blush · lavender; "vellum, pearl, opal, shell, pale enamel; avoid chrome, harsh black, constant glitter".
- **Still open in Figma:** fonts now **11 families** (Space Grotesk 893, Crimson Text 190 lead); components have Theme/Size variants but **no interaction states** (Default/Focused/Pressed/Locked/New); one "F · J · K" string remains (highway frame).

## Owner decisions (block the listed step)
- **D1 Motion grammar → beats:** adopt GLINT/UNSEAL/BLOOM/ORBIT/BREATHE as the one motion vocabulary, beat-scaled (above). Replaces the orrery's 0/117/234/469/703. (W2)
- **D2 Type ramp:** Crimson Text (display) + Space Grotesk (UI/body)? Everything else retired. (W2, W6)
- **D3 Party lead on the HUD:** Sir Melodious (template party today) or give Melusina a party unit. (W5)

**Decided 2026-09-26 (owner):** D1 = Motion Grammar, beat-snapped (GLINT 0–117 · UNSEAL →352 · BLOOM →586 · ORBIT →879 ms @128 BPM · BREATHE) · D2 = **Kaisei Decol + Klee One** · D3 = **Melusina gets a party unit and leads** · W0 commit approved.

## Order (each step ends in a live PIE check; content-first)
- **W0 Close the open loops.** Commit CURRENT_STATE + HL source + minimap fix (plan + OK). Fix the highway gate to start the battle the way the game does (narrative `melodia:battle:<id>` path via the real subsystem API / `BP_InteractionBattle` overlap) and drive lanes through `TryHitNoteInLane`; record HL1–HL5 live. Place `Btn_Calibrate` in `WBP_MelodiaSettings`; owner does one tap-run.
- **W1 Compendium — first Storybook surface.** Author the 3 prototype entries into `DA_MelodiaPersonaContent.Compendium` (Melusina/Character, Faraway Mother/Place, Sonic Scepter/Instrument; field notes from Figma). Native `UMelodiaCompendiumWidget` (BindWidget) on `GetCompendiumEntriesByCategory`: Archive Index (3 threads + more) → entry spread (portrait frame, plaque title, divider, field note). Opened from the orrery. Gate: PIE shows the 3 real entries, locked entries as silhouettes.
- **W2 Storybook Kit → UE.** Export the 23 component variants at 2× via the Figma images API → `/Game/Melodia/UI/Storybook/` (UI texture group). One C++ `FMelodiaMotionGrammar` (GLINT…BREATHE, beat-scaled from the clock) used by the orrery unfold, grade pop, compendium open and medallion focus. Type ramp per D2.
- **W3 Orrery hub = storybook cover.** Cut the competing elements; Medallion (Compass/Music/Heart) for Worlds/Songs/Bonds; Plaque title; Page Frame; circular mask; the owner-approved starfield UI master (Night theme ground, sparkles restrained per Foundations).
- **W4 One menu owner.** Orrery hub owns Compendium / Journal / Settings / Calibration; opening one closes the others; HUD hides while open; Esc backs out one level.
- **W5 HUD leftovers.** Bar fill colours, live interaction prompt, skill row cooldowns, orrery sigil replaces 1/2/J/Esc, D3.
- **W6 Quill = storybook caption** (Plaque + Page Frame Light theme).
- **Anim lane (parallel, owner priority):** Jev says wire Sir's existing clip first (0.9) and tune/resave sheep thresholds (0.71).

## Asks for the owner in Figma
Interaction states on Medallion + Plaque (Default/Focused/Pressed/Locked/New); fix the last "F · J · K" to Q · W · O · P; pick the 2 fonts (D2).
