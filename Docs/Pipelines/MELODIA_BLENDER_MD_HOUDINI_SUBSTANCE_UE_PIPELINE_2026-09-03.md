# Melodia Wardrobe Pipeline: Blender 5.2 -> MD -> Houdini -> Substance -> UE (2026-09-03)

The interchange path for market/closet garments onto Melusina. Extends (does not
replace) `Docs/Art/UNIVERSAL_GARMENT_INTERCHANGEABLE_WARDROBE_2026-09-02.md` and the
canonical Substance pattern in `Docs/Production/CANONICAL_SHOREWAKE_SUBSTANCE_STAGING_PIPELINE_2026-09-02.md`.

## Stage order (each stage's output is the next stage's input)

1. Source: market FBX/OBJ (Fab 2-citizen, signed-in license, interactive) or MD/CLO
   interactive drape. No headless MD path exists (GUI-only, zero script API) — report
   that, never fake it.
2. Interchange prep (Blender 5.2.1 ONLY, never 4.5):
   `Tools/Houdini/sea_above_reef/garment_intake_prep.py -- --source <path>
   --slot <S> --descriptor <Pascal>` -> OBJ (Substance) + FBX (UE) + intake_manifest
   (seed 20260902 + sha256) under `Saved/Audit/wardrobe_pipeline/intake/
   Cos_<Slot>_Melusina_<D>/`.
3. GN variation (this session): apply `MEL_garment_uv_unwrap` (live cylindrical UV,
   15 nodes) then `MEL_garment_loom_variation` (seed fold+drape, 13 nodes) and/or
   `MEL_garment_audio_drape` (offline bake-lane fold+drape, 27 nodes) as GN modifiers
   via the Melodia Wardrobe N-panel. Per-layer starting points:
   `preset_param_sets("MEL_garment_loom_variation")` (8) and
   `preset_param_sets("MEL_garment_audio_drape")` (BASS_WEAVE / VOCAL_MID /
   TREBLE_SHIMMER / BEAT_PULSE_WIDE). Panel Emit writes OBJ+FBX+manifest back to the
   intake folder.
4. Substance: canonical pattern — startup module, 28 OPEN texture sets, base AO/Chladni
   maps staged as resources, NOTHING wired (artist owns the look). Scale discipline:
   static base-PBR set only (skip `foo.N.png` frames) — 2,900 maps crashed Painter.
5. UE: `DA_MelodiaCosmeticCatalog` + `Cos_` draft rows (editor lane, Monolith 9316),
   cloth tier dispatch (A authored / B Chaos candidate / C WPO), per-garment MI on the
   verified small family only.

## Blender 5.2 truths (proven headless 2026-09-03, `Tools/wardrobe_pipeline/gn52_proof.py`)

- GN builders must use the current core API: `new_geometry_tree(name)` returns
  `(tree, gin, gout)`; `add_*_param` returns the SOCKET (wire via `gin.outputs[name]`).
  The old `make_group_input(tree)` / builder-fn-first `register_builder` forms are dead.
- Set Position has no scalar path: scale Normal (VectorMath SCALE) into Offset.
- ShaderNodeMath has no CLAMP op in 5.x: use ShaderNodeClamp (Min/Max/Value).
- TexNoise `W` fails `inputs["W"]` key lookup in 5.2 (identifier quirk) while iteration
  shows it — always resolve via `core.sock()` (iteration fallback), never direct index.
- Mirror sync: repo `deploy/surreal_arch/melodia_gn/*.py` -> manual `cp` into
  `%APPDATA%/Blender Foundation/Blender/5.2/scripts/addons/surreal_arch/melodia_gn/`.
  Headless runs use `--factory-startup` (user addons hang exit).

## Gates before handoff

`chladni_eigen_verify.py` 9/9, `universal_garment_vocab_check.py` PASS (0 collisions),
preset-socket audit PASS (12/12), `gn52_proof.py` GN52_PROOF PASS. Intake folders for
Cloud / AntiqueDoll / ButterflyWing carry OBJ+FBX+manifest (committed batch 1).

## Honest blockers (owner-gated, unchanged)

Monolith 9316 down disables catalog/MI/wardrobe-subsystem wiring; Fab download needs a
signed-in license; MD/CLO drape is interactive; audio-drape is bake-lane only (UE keeps
runtime rhythm authority, zero new audio writers).
