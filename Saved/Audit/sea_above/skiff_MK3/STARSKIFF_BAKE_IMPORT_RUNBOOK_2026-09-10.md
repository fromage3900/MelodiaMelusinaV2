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

---

## OUTCOME — 2026-09-12 23:33 EDT (ran; two premises were wrong)

Harness: `Content/Python/import_starskiff_bakes_20260912.py` (dry-run / `main(dry_run=False)`),
driven through Monolith `editor_query run_python`. Receipt:
`Saved/Audit/melusina_lookdev/starskiff_bake_import_2026-09-12.json`.

**Result: 19/19 imported, 0 deleted, all saved (dirty packages 0).** Read-back per file is
2048x2048 with the runbook's flags — BaseColor sRGB on, Normal `TC_Normalmap`, Mask/Emission
`TC_Masks`, Emission on `TEXTUREGROUP_EFFECTS`, everything else `TEXTUREGROUP_WORLD`.
`flip_green_channel=False` left as authored (the bake chain pre-flips to DirectX). Destination
is `/Game/Melodia/SeaAbove/Textures` per PR #188.

Two corrections to the contract above:

1. **`AssetImportTask` has no `srgb` / `compression_settings` / `lod_group` fields in UE 5.8.**
   `import_starskiff_v2.py` set them and raised `AttributeError` on every file — it never
   imported anything. The 19 files were imported with `TextureFactory`, then the texture
   properties were set on the asset and saved.
2. **"MIs rebind on load" is false — nothing consumes these bakes.** After the import,
   `get_referencers` on `T_Starskiff_Hull_BaseColor` returns **0**. `MI_Starskiff_Hull`,
   `MI_Starskiff_Brass`, `MI_Starskiff_Wake` and `MI_Starskiff_Hull_Regal` are all identical
   unwired placeholder instances of `M_Master_Toon_Universal`:
   `Albedo = T_Cymatic_FarawayAlabasterDrape_BaseColor`, `NormalMap = T_Neutral_Normal`,
   `ORM = T_Neutral_ORM`, `EmissiveMap = T_Neutral_Metallic`, `LayerB_Albedo = Cracks_3`.
   The meshes that actually render (`SM_Starskiff_Proxy_*`) point their `Starskiff_Hull`,
   `Starskiff_Planks` and `Starskiff_Brass` slots at exactly those instances — so the hull
   currently draws a cymatic alabaster drape albedo, not starskiff wood.
   The only MIs that do use a starskiff family are `MI_Starskiff_Night_Hull`
   (`T_Starskiff_Night_BaseColor/Normal/Roughness`) and `MI_Starskiff_Night_Wake`
   (`T_Starskiff_Night_Wake_Emission`) — a separate **Night** set, which is the wiring pattern
   to copy if this refreshed set is the daylight counterpart.

**Not done:** the PIE boarding pass. Nothing to see yet — the new art is unreferenced, so a
boarding pass would capture the placeholder materials and prove nothing about the bakes.
Wiring the refreshed textures into the hull/brass/wake instances is the open owner decision
(day vs night set on a hero ship), not an import defect.

Incident on the way: all 19 target `.uasset` were **read-only on disk** (`-r--r--r--`), so the
first apply pass imported and set properties in memory but silently failed to save
(`save_loaded_asset` → False, mtimes unchanged). Cleared with `chmod +w` on those 19 files only
(the documented `attrib -R` remedy; `attrib` itself rejects MSYS path arguments — use
`chmod +w` from bash), then re-ran. 4004 of 26653 `.uasset` in the tree are still read-only.
