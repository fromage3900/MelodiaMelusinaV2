# SHOREWAKE — SHOT PLAN v03 (updated 2026-10-07)

Supersedes the shot table in `SHOREWAKE_STORYBOARD_PLAN_v02.md` for the current
state. Three parts: (A) the animatic shot table, (B) the beauty stills set,
(C) the loop render + gates. Durations locked from `SHOREWAKE_BEAT_BOARD.md`.

## A. ANMN301 animatic — 18 shots, 1560 f @ 24 fps (65.0 s), silent

| # | Dur | Cam / stage | Action beat | Current status |
|---|-----|-------------|-------------|----------------|
| 00 | 72f | slug | SHOREWAKE CALLING + credits | DONE in v05 (text verified from frame) |
| 01 | 120f | Wide | Wide mooring, asleep — sea still, no light | panel 01 (Sep 18) |
| 02 | 96f | Intimate | Melusina at the rail, looks at dark water | panel 02 (refreshed Oct 6) |
| 03 | 48f | SkiffClose | Slack rope drips, nothing answers | panel 03 (Sep 18) |
| 04 | 48f | Intimate | Lantern offered over the water | panel 04 (Sep 18) |
| 05 | 72f | SkiffClose | Light dies; shore stays dark | panel 05 (Sep 18) |
| 06 | 120f | Intimate | Decision; lantern down, lyre up (*fade 1) | panel 06 (refreshed Oct 6) |
| 07 | 48f | Intimate | First phrase; one ripple | panel 07 (refreshed Oct 6) |
| 08 | 48f | Wide | Water answers wider | panel 08 (Sep 18) |
| 09 | 48f | Wide | Reef bells wake, bank 1 | panel 09 (Sep 18) |
| 10 | 48f | Wide | Far bells join, bank 2 | panel 10 (Sep 18) |
| 11 | 96f | Intimate | Doubt beat; almost stops, plays on | panel 11 (refreshed Oct 6) |
| 12 | 120f | Intimate | Second phrase completes, light spreads | panel 12 (Sep 18) — pacing: 9 s, trim optional |
| 13 | 72f | SkiffClose | Skiff wakes; hull lifts (*fade 2) | panel 13 (Sep 18) |
| 14 | 96f | Wide | Boarding; push off | panel 14 (refreshed Oct 6) |
| 15 | 120f | Wide | Crossing through lit reef | panel 15 (Sep 18) — pacing: 10 s, trim optional |
| 16 | 120f | Wide | Route opens; far shore glows | panel 16 (Sep 18) |
| 17 | 96f | Intimate | Arrival look-back (*fade 3) | panel 17 (refreshed Oct 6) |
| 18 | 72f | slug | END card | DONE in v05 (text verified from frame) |

Notes:
- v05 (`ShepherdBrennan_AnimaticCreation_2026-10-09_v05.mp4`) passes: 65.00 s, 1920x1080,
  24 fps, silent, title + end text, panel numbers burned in. This is the submission
  candidate.
- The three (*) fades are the only allowed cuts; keep at 06/13/17 boundaries.
- Optional upgrades: pacing trim of 12/15; refresh of the 11 Sep-18 panels once the
  master scene exists (panels would be re-rendered from the same shot table above).

## B. BEAUTY STILLS — 6 frames (1920x1080), from the MASTER scene

Render after the master merge (lookdev + komikaze + geometry). Frames chosen at
seam-safe states (f1 and f120 are identical; f60 is mid-breath).

| # | Name | Camera | Frame | Subject / why it's the shot |
|---|------|--------|-------|------------------------------|
| S1 | "Awakened" | CAM_Wide | 60 | Hero establishing. Full night stack: fog-glow, stars, lit windows, pearls. The reel frame. |
| S2 | "Pearls Along the Rail" | CAM_SkiffClose | 30 | The restored pearl strand + bow jewelry; the detail that was dead for weeks and now sings. |
| S3 | "The Lookout" | Cam_NestCheck | 90 | Nest, star pendants, Sir Melodious' perch bar — the warm-life corner of the ship. |
| S4 | "Lantern Vigil" | CAM_Intimate | 40 | Lantern at its flicker peak (5.12); warm pool over the deck against the cool night. |
| S5 | "The MoonWell" | new `Cam_MoonWell` | 45 | The scrying basin (aim at x 2.6, z 0.77; eye ~1.4 m, ~1.2 m out; verify framing in session). |
| S6 | "Stern & Pennant" | new `Cam_Stern_Beauty` | 75 | Stern roofline, pennant mid-sway (f60 motion 68 mm), star finial; 42 mm, from aft-left, verify in session. |

Output: `Saved/Audit/beauty_<n>_<name>.png`. S5/S6 camera placements are proposals —
confirm in the live session before the batch (the plan is the recipe, the viewport is
the judge).

## C. THE LOOP — 120 f (5.0 s) @ 24 fps

- Render: EEVEE 64 spp, 1920x1080, frames 1-120, headless, from the master.
- Gates before publishing:
  1. transform closure f1 vs f120 = 0.000 on every keyed holder (current audit: PASS);
  2. flicker cycle 4.0 -> 5.12 -> 3.28 -> 4.0 (PASS);
  3. ocean time 0.2 -> 3.0 -> 0.2 (PASS);
  4. keys within 1-120 across all actions (PASS after wake-trim);
  5. pixel seam gate: f1 vs f120 render diff, mean < 0.0005 (run at render time).
- Assemble MP4 with ffmpeg (hermes tools path) from the PNG sequence; verify the
  decoded file (duration/fps/frames) the same way the animatic was verified.

## D. File map (which blend for what)

- `SHOREWAKE_LOOP_v5_animfix.blend` — canonical geometry + animation state (pearls,
  mesh fixes, clean key windows, FLIP parked). **Base for the master.**
- `SHOREWAKE_LOOP_v5_lookdevstack.blend` — lookdev reference (water 64 m, RT, stars,
  fog-glow compositor).
- `SHOREWAKE_LOOP_v5_komikaze_tunedplus.blend` — hybrid material set (50 hybrids).
- `SHOREWAKE_LOOP_v5_master.blend` — to be assembled (goal doc, "the one structural
  step"); render everything from this once it exists.
- `SHOREWAKE_VSE_animatic_v03.blend` + `panels_v3/` — the animatic's VSE/panel assets
  (v05 MP4 origin; if panels are refreshed, this is the assembly point).
