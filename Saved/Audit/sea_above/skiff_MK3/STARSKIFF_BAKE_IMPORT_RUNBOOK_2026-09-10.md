# Starskiff updated-bake import runbook — 2026-09-10/12

Fresh 2048 bakes are staged and ready. Import is editor work (one healthy
editor, Python or Monolith channel up). Tonight both channels were down
(Rider Python bridge "not available" on the fresh PID 49136 session, :9316
without listener), so this file is the one-shot contract.

## Sources (seed 20260904, 2048)

`Saved/Audit/melusina_lookdev/houdini_variants/` via:
- `python Tools/Houdini/sea_above_reef/refined_starskiff_wood.py --size 2048 --seed 20260904`
  → Hull_BaseColor/Normal/Roughness/Height, Wake_Emission, PlankSeam_Mask
  (+ `refined_starskiff_wood_manifest.json`)
- `python Tools/Houdini/sea_above_reef/refined_starskiff_regal.py --size 2048 --seed 20260904`
  → RegalFiligree_Mask, BrassFiligree_BaseColor/Roughness/Normal,
  Hull_Regal_Normal/Height, SternCrest_Mask/BaseColor, Jewel_BaseColor/Normal,
  Rope_Normal, PlankNail_Normal, RegalEdgeWear_Mask
  (+ `refined_starskiff_regal_manifest.json`)

## Destinations (PATH CHANGE — read before importing)

PR #188 (`a69079dd`) consolidated Starskiff textures out of
`/Game/Melodia/Characters/Melusina/Textures/Clothes/` into
**`/Game/Melodia/SeaAbove/Textures/`**. The 2026-09-04 spec
(`Saved/Audit/melusina_lookdev/starskiff_import_spec.md`) still names the old
base — substitute the new one. 81 Starskiff files live there now.

## Per-file flags (unchanged from the 09-04 spec)

| Texture | sRGB | Compression | LOD group |
|---|---|---|---|
| *_BaseColor | true | TC_Default | World |
| *_Normal | false | TC_Normalmap (OpenGL Y+, do NOT flip) | World |
| *_Roughness, *_Height | false | TC_Default | World |
| *_Mask, *_Emission | false | TC_Masks | World (Emission: Effects) |

Files already present refresh in place (`replace_existing`); verify by
re-reading texture properties + `list_dirty_packages`, never by the import
success flag alone. No master material edits; MIs rebind on load.

## After import

Re-check `MI_Starskiff_Hull_Regal` / `MI_Starskiff_Brass`, then run one PIE
boarding pass (tonight's contract in
`Saved/Audit/starskiff_boarding_proof_2026-09-10.json`) so the new hull art
is covered by live evidence, not just pixels on disk.
