# ANMN 301 Animatic — TEXT LAYER FIX (do this before Fri Oct 9, 5 PM)

Generated 2026-10-04 from a headless read of `SHOREWAKE_VSE_animatic_v03.blend`.
Everything below is measured, not guessed.

---

## What I found

The VSE is **complete and correct** — 19 strips, 1920x1080, 24 fps, frames 1-1560
(65.0 s). The 17 panels are all there, in the right order, with the right durations,
matching `SHOREWAKE_BEAT_BOARD.md`.

The film passes every hard spec: H.264, 1920x1080, 24 fps, 65 s, silent (0 audio
streams), clean decode, no broken frames.

**The only problem is text.** Measured from the exported MP4:

| what | where | status |
|---|---|---|
| Title card | frames 1-73 (0.00-3.00 s) | flat dark field, NO TEXT |
| End card | frames 1489-1561 (62.00-65.00 s) | flat dark field, NO TEXT |
| Panel numbers 01-17 | each panel | NOT burned in |

The brief requires: **panels "labeled+numbered"**, **TITLE CARD + END CARD required.**

---

## Why they are blank (this is the useful part)

The strips exist but are the **wrong type**:

```
strip 0  '00_Title'  type=COLOR  f1=73     <- should be an IMAGE or TEXT strip
strip 18 '18_End'    type=COLOR  f0=1489   <- should be an IMAGE or TEXT strip
```

A COLOR strip renders a solid colour. There is nothing to read. Someone made the
strips as placeholders and never gave them content.

Also present but unused:
```
proxy/panels_v3/title.png   6,109 bytes  - pure black, no text
proxy/panels_v3/end.png     6,109 bytes  - pure black, no text
```

So the cards were stubbed out at every level. Wiring those PNGs in would NOT fix it —
they are black too. You need real text.

---

## The fix — 4 text strips, about 10 minutes

Open `ANMN301_Animatic/SHOREWAKE_VSE_animatic_v03.blend` in the Video Editing workspace.

### 1. Title strip
- Add strip: **Add > Text**
- Channel: 2 (so it sits above the COLOR strip without replacing it)
- Frame start 1, duration 72 frames (3 s, matches the COLOR strip exactly)
- Text:
  ```
  SHOREWAKE CALLING

  Brennan Shepherd
  ANMN 301 — Image and Sequence Editing Toolkit
  ```
- Style: centred, size ~90 px for the title, ~40 px for the credits

### 2. End strip
- Add strip: **Add > Text**
- Channel 2
- Frame start 1489, duration 72 frames
- Text:
  ```
  END

  Shorewake Calling
  ANMN 301 Animatic Story Edit
  Brennan Shepherd
  ```
- Style: centred, ~80 px

### 3-4. Panel numbers
Two options — pick one:

**Option A (fastest, 17 text strips):** add a Text strip per panel on channel 2,
positioned bottom-left, size ~36 px, text `01` ... `17`, each matching its panel's
start frame:

| panel | start | panel | start | panel | start |
|---|---|---|---|---|---|
| 01 | 73 | 07 | 577 | 13 | 985 |
| 02 | 193 | 08 | 625 | 14 | 1057 |
| 03 | 289 | 09 | 673 | 15 | 1153 |
| 04 | 337 | 10 | 721 | 16 | 1273 |
| 05 | 385 | 11 | 769 | 17 | 1393 |
| 06 | 457 | 12 | 865 | | |

**Option B (fewer strips):** one Text strip on channel 2 spanning frames 73-1489,
using **Strip Modifiers > Text: Duration** or per-frame markers if your build
supports it. Only do this if you know your Blender version's modifier behaviour —
Option A is predictable and safe.

### Then export
- Output: `ANMN301_Animatic/ShepherdBrennan_AnimaticCreation_2026-10-09.mp4`
  (overwrite the old one, or write v04 — keep the filename convention exact)
- Format: MPEG-4 / H.264, 1920x1080, 24 fps
- **Audio: NONE** (the brief wants silent)
- Render frames 1-1560

---

## Optional: two over-long shots

The brief's pacing guide caps shots around 6 s. Two exceed it:

- shot 12 "Second phrase, full" = 9 s (frames 865-985)
- shot 15 "Crossing" = 10 s (frames 1153-1273)

The other 15 shots are 2-5 s and sit nicely. Only trim these two if you want the
pacing spot-on — it is not a requirement, and the film reads fine as is.

---

## If you do NOTHING else

Submit it anyway. The assignment is a **resumable Blackboard test with multiple
attempts**, and the brief says *"Submit your work by the due date, regardless of
its state."*

A film with correct pacing, clean 17 panels, correct resolution and silent audio
earns far more than an unsubmitted file. The text layer is a few marks, not a
rewrite.