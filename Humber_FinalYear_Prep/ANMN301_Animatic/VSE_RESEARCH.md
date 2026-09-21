# VSE + Water Research (2026-09-17, for ANMN301 animatic)

## Assigned watching: Blender VSE for Complete Beginners Part 1 (yh7YPabqeDk)
Transcript pulled. Substance:
- Open Video Editing workspace from splash screen (New File > Video Editing) or File menu. No 3D knowledge needed.
- Part 1 covers: workspace layout, adding strips, timeline playback.
- Preview lag fixes (matters for 1560-frame timeline): N-panel proxy render size down to 25% (preview only, never affects final), Playback sync set to Frame Dropping or Sync to Audio, strip proxies covered in later parts.
- Parts 3-4 cover transitions and export (per video description timestamps).

## Storypencil verdict: SKIP
- Blender's storyboard add-on (Scene strips + Edit/New/Render buttons, template scene, Grease Pencil draw mode setup). Documented for 4.0-4.2.
- NOT present in installed 5.2.1 (190 bundled modules queried, no story/board/pencil match). The brief explicitly requires Blender VSE image strips, so plain VSE is the compliant path anyway. Revisit only if hand-drawing panels in 3D viewport appeals.

## Water verdict: Ocean modifier, not Flip Fluids
- Ocean modifier verified live in 5.2 headless (default resolution 7). Built-in, free, seconds to render.
- Flip Fluids addon IS installed in user addons, but it bakes gigabytes for realistic sim that fights the toon look. Reserve for one hero splash close-up if ever needed.
- Proxy plan: keep flat shaded plane for panels now; upgrade to Ocean modifier (low res, small waves, toon material) for the capstone look pass.

## Cascadeur verdict: capstone weeks 6-8, not animatic
- Installed (cascadeur.exe) and repo names it the canonical Melusina animation authority (Docs/CASCADEUR_MELUSINA_PIPELINE_2026-08-07.md, 30 FPS export contract, Lane A author on real skeleton).
- Animatic needs 17 posed stills, already working in Blender (19 bones, zero misses). Cascadeur adds nothing until real motion cleanup.

## VSE assembly spec (from brief + standards PDFs)
- 1920x1080, 24 fps, SILENT single MP4. Name: ShepherdBrennan_AnimaticCreation_2026-10-09.mp4 (Friday 5 PM rule).
- Image strips per SHOREWAKE_BEAT_BOARD.md durations x24fps = 1560 frames total. Title + end cards as Color/Text strips 72f each. Max 3 Gamma Cross transitions at panels 06/13/17.
- TEST link allows multiple resumable attempts: submit scratch cuts early and often.
