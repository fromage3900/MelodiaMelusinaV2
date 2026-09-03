# Material Studio Doctrine — Melodia Void / Nikki Lens

**Status:** Active (2026-07-14)  
**Supersedes:** UDSW outdoor-plaza material studio for `L_MaterialPreview_Studio`.

## Two lanes

| Lane | Level | Lighting | Purpose |
|------|-------|----------|---------|
| Material lookdev | `L_MaterialPreview_Studio` | Melodia void + soft 3-point — **no UDS / no SkyAtmosphere** | Fashion-fantasy swatch stills & orbit loops |
| World beauty | Sakura / WP / `L_Render_*` | UDSW day-night | Places, not material identity |

## Visual lock

- Backdrop: `MI_Show_MelodiaVoidGradient` (+ tint children). Brand void ≠ void-padded placeholder loops.
- Camera: 55mm, orbit r=220 / elev=18°, ~60–70% swatch fill, 1080².
- PP: Outline → StorybookVines → MeluGrade; bloom 0.65, vignette 0.22, grain 0.06, CA 0.35.
- Priority plates: `NikkiPriority` in `mi_preview_studio.py` (NikkiHero, SkinSoft, CherryBlossom, …).

See `Docs/INFOLD_SENDOFF_CAPTURE.md`, `Docs/Production/RENDER_POST_PROCESS_NIKKI.md`.
