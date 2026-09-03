# Dawn Chorus — Cos_Dress_Melusina_DawnChorus

First-light rose-gold gown, built overnight 2026-09-03 from proven pieces only.
Status: OPEN for hand-paint. Nothing here is auto-wired to any mesh.

## Package
- meshes/DawnChorus.fbx (7.9 MB, sha12 58860c25f9a0)
- textures/ + resources/ (identical working copy): BaseColor, Normal,
  Roughness, Metallic, Height — 5 maps, hashes in dawn_chorus_manifest.json
- generator: _gen_maps.py (kept for provenance)

## Sources
- MEL_garment_loom_variation presets (seed 20260902)
- MEL_garment_audio_drape hem (offline bake lane)
- AntiqueDollRose Copernicus family, cooked 2026-09-03 01:40 at 2048

## Hand-paint notes
1. Paint from resources/, keep textures/ pristine as the fallback.
2. Gilt trim lines live in the BaseColor rose-gilt band — lift them, don't redraw.
3. Height is parallax data (OpenGL convention; flip G only if mixing DirectX sources).
4. When she sings in it, the hem answers — that's the audio-drape bake, leave room.
