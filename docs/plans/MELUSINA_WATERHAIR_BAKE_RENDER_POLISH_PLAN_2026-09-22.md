# Melusina Water-Hair Bake + Render Polish Plan — 2026-09-22 evening

> For Hermes: authored from the contact-sheet review (vision-passed) of tonight's lane
> outputs: 24 Copernicus maps + first 22 frames of the FLIP hero render. Lane folder:
> `Saved/Audit/melusina_bake_staging_20260922/` (README_STAGING.md carries the full
> evidence index). Supersedes nothing; feeds the grandmaster plan v7 W7 fabric/bake lane.

## 1. Review findings (the sheets)

Copernicus maps (copernicus_maps_sheet.png):
- Normal + Curvature channels: REAL structure on all six meshes — strand/clump detail on
  hair, radial fiber pattern on both irises, lash shafts clean. Irises pass as proper
  eye bakes (crypts/furrows + collarette read).
- **Roughness/Thickness: flat white on ALL six** — root cause: open single-layer sheets
  give the one-sided inward ray nothing to hit (fallback wrote 1.0).
- **HairB AO near-black** — dense 26k-vert tangle self-occludes 64 rays almost everywhere.
- Minor UV-bleed/stretch artifacts in hair normals (island padding) — lookdev-pass item.

Hero render (render_sequence_sheet.png):
- Framing good (turntable, character centered), water READS as water (translucent volume,
  droplets near shoulders).
- **Character underexposed — silhouette against the sky.** Single biggest fix: rim + key.
- Hair reads "uniform purple jelly" — needs strand-depth variation (tonight's own AO maps
  supply exactly this when wired into the emission path).

## 2. Waves

### R1 — Re-bake v2 (executed tonight)
- Two-sided thickness: rays both ways, min distance, normalized by bbox diagonal, honest
  0.5 fallback; shipped as custom attrib `thickn` through a SECOND baker node (the baker
  exposes exactly one custom output, index 11 — two custom attribs cannot stack on one).
- HairB AO gamma lift 0.45; others unchanged (gamma is per-mesh, seeded, recorded).
- Evidence: `copernicus_bake_manifest.json` (v2) + re-generated map sheet.

### R2 — Render prep gen2 (executed tonight)
- Per-mesh water materials `Water_Advance_AO_{A,B,C}` with that mesh's baked AO multiplied
  into the emission color path (factor 0.85) — strand-depth darkening; FLIP meshes keep the
  authored material (single water writer; the copies are render-lane variants, documented).
- Three-point area rig (key warm / fill neutral / rim cool) aimed at (0, -0.05, 1.15);
  verify still gated on exposure (mean 0.15-0.45) with one bounded energy auto-adjust.
- EEVEE headless is BANNED for animation on this box (nvoglv64.dll access violation after
  ~4 frames); sequences run Cycles (OPTIX->CUDA->CPU), 48-64 samples + OIDN.

### R3 — Lit hero sequence (running overnight)
- 240 frames, Cam_Turntable, 1920x1080 -> `Saved/PIE/melusina_hair_flip_20260922/`.
- Evidence on completion: `render_sequence_evidence.json` (count, motion diffs, stats) +
  regenerated contact sheet for the owner's morning eye-gate.

### R4 — UE import staging (staged tonight, executed next editor session)
- `Exports/MelusinaBakeStaging_20260922/UE_import/`: RUNBOOK + manifest + textures.
- Textures only (meshes already live in UE — no re-import, no mesh authority fork);
  FLIP sequence via staged Alembic export, imported as geometry cache (Nanite OFF,
  collision NONE). sRGB OFF on all four channels; TC_Normalmap / TC_Masks.

### R5 — Queued (owner-gated / next windows)
- Normal-map island padding pass on the hair UVs (bleed artifacts, lookdev).
- FLIP Alembic export (script staged) + U2 import.
- LEFT EYE: no L-side iris/cornea mesh exists in the harp WIP — owner decides
  (body-material region vs new mesh) before any left-eye bake/wiring.
- G: texture relink (`Material.021_Normal.png` missing — pre-existing, non-hero).
- Flipbook (MelusinaAnimated) wiring onto the regalia maps — grandmaster W6 note.

## 3. Owner gates
| Gate | Question | Default if silent |
|---|---|---|
| G-A | Left eye: body-material region or new mesh? | wait |
| G-B | Keep the unlit silhouette frames (first ~33) as a "dusk" variant? | delete at closeout |
| G-C | Water material render-variants (AO copies) acceptable as render-lane only, never the authored master? | yes, documented |
