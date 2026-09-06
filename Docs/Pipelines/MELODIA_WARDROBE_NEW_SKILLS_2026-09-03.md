# Melodia Wardrobe New Skills — 2026-09-03

Seed 20260902 everywhere. Authority: Docs/Art/UNIVERSAL_GARMENT_SYSTEM_MASTER_SPEC_2026-09-02.md (S0-S6),
Docs/Research/EMERGING_TOOLCHAIN_MASTER_INDEX_2026-08-31.md (extend PRESENT, never parallel).
Single audio writer untouched: UMelodiaAudioReactivePresentationSubsystem -> MPC_Melodia_Palette.
Blender 5.2.1 LTS only (audio-GN compat, never 4.5). No Content/**/*.uasset writes by these skills.

## 1. Garment Loom builders (Blender 5.2 GN, live in 5.2 addons after sync)

Source: deploy/surreal_arch/melodia_gn/garment_loom.py
Sync: python deploy/_sync_addon_to_blender_5_2.py (copies deploy/surreal_arch -> 5.2 addons)

- MEL_garment_uv_unwrap — live cylindrical UV projection from mesh position
  (U = atan2(x,z) normalized, V = Y clamped), stored to "uv" attribute.
  Honest limit: GN has no pack-islands node; coherent and non-overlapping for
  garment shells, not a true unwrap. Painter hard-refuses UV-less meshes, so this
  guarantees a coatable fallback. Category: Garment, seedable.
- MEL_garment_loom_variation — seed-driven fold+drape displacement along normal
  (fold = Y-weighted, drape = noise field, deterministic sin-hash on position).
  Category: Garment, seedable.
- Fix 2026-09-03: builders were registered only inside register(), invisible to
  GROUP_BUILDERS until addon register. Now module-level register_builder on import,
  matching audio_terrain.py. Catalog: 248 builders total.

Panel: MELODIA_PT_wardrobe (3D View > N-panel > Melodia > Garment Loom)
  target mesh pointer, 7 slots (Dress/Top/Skirt/Outerwear/Accessory/Footwear/Special),
  Descriptor, Variation Seed, Fold, Drape, Live UV toggle,
  [Add UV + Variation] (melo.loom_modifier), [Emit OBJ+FBX + manifest] (melo.loom_emit).
  Emit names Cos_<Slot>_Melusina<Descriptor>, writes intake_manifest.json
  (schema melodia.garment_loom_emission.v1, sha256, live-vs-source UV flag).

## 2. Audio-drape builder (in flight)

- MEL_garment_audio_drape — deploy/surreal_arch/melodia_gn/garment_audio_drape.py (NEW, landing).
  Sound (NodeSocketSound) + Time (seconds) + Low/High Hz + Band Width + Audio Gain
  + Seed/Fold/Drape -> GeometryNodeSampleSoundFrequencies amplitude -> scales the
  same fold+drape displacement, stores audio_amplitude attr. OFFLINE bake lane only;
  UE runtime rhythm authority untouched. Mirrors audio_terrain.py helpers.

## 3. Blender 5.2 audio GN contract (researched 2026-09-03)

Node: GeometryNodeSampleSoundFrequencies (Blender 5.2 LTS manual, verified present).
Inputs: Sound (datablock, NodeSocketSound interface socket), Time (seconds),
All Channels (mono mix; stereo collapsed when true), Channel (when false),
Low / High (Hz band). FFT: Size 128 (time resolution) .. 32768 (freq resolution);
Window Hann (general) / Hamming / Blackman (leakage suppression) / Rectangular (none).
Output: Amplitude (summed energy in band). Existing proof: MEL_audio_spectrum_terrain /
towers / radial_field in audio_terrain.py (all bake lane, store audio_amplitude +
frequency_hz attrs, apply_universal_music_pass).

## 4. Substance staging skill (worked 2026-09-03)

Pattern: Docs/Production/CANONICAL_SHOREWAKE_SUBSTANCE_STAGING_PIPELINE_2026-09-02.md.
Stage base maps as resources, leave texture sets OPEN, never wire old-outfit maps
onto a newer mesh. Static base-PBR only (skip foo.N.png flipbook frames or Painter
crashes on save). Normal convention: staged OpenGL, flip G on UE export when mixing
with sbs DirectX bakes. Displacement source doubles as Height.

- AntiqueDoll (Dress): meshes/AntiqueDoll.fbx 9,943,024 b sha12 364d4ad2448f;
  5x4K (BaseColor 26 MB / Normal 5.8 MB / Roughness 3.6 MB / Metallic 81 KB /
  Height 6.8 MB). Manifest antiquedoll_staging_manifest.json (melodia.substance_stage.v1).
- ButterflyWing (Accessory): meshes/ButterflyWing.fbx 50,671,984 b sha12 a438809c788a;
  5x4K (BaseColor 12.6 MB / Normal 237 KB / Roughness 121 KB / Metallic 80 KB /
  Height 478 KB). Manifest butterflywing_staging_manifest.json.
Staged under Saved/Audit/melusina_lookdev/substance_staging/<Asset>/ (meshes/ +
resources/ + textures/ mirror + spp/ reserved + README.md).

## 5. Wardrobe intake skill (worked 2026-09-03)

Tool: Tools/Houdini/sea_above_reef/garment_intake_prep.py (Blender 5.2 headless):
  blender.exe -b --factory-startup -noaudio --python <tool> -- --source
  Imports/GarmentIntake/<file> --slot <Slot> --descriptor <Pascal>
Merges to one object, transform-apply, UV/material audit, exports OBJ (Substance) +
FBX (UE) + intake_manifest.json (melodia.garment_intake_prep.v1, seed+sha256).

- Cos_Dress_Melusina_AntiqueDoll: 180,895 v / 316,912 p / 2 UV / 20 slots /
  0 empty / uv_overlap 75. obj sha 9978a006, fbx sha 6e02bd59.
- Cos_Accessory_Melusina_ButterflyWing: 818,770 v / 1,582,132 p / 2 UV / 7 slots /
  0 empty / uv_overlap 11. obj sha 59c414de, fbx sha 8a2b8df1.
  FLAG: 818k verts is hero-or-LOD-only weight; decimate/LOD before UE import,
  candidate cloth tier C (WPO) or D (VAT), never B at this density.
Next per piece: 10-layer cluster -> Substance OPEN stage (section 4 pattern) ->
DA_MelodiaCosmeticCatalog + Cos_ draft -> runtime swap.

## 6. Gates holding PASS

- universal_garment_vocab_check.py: 14 articles, 14 unique modes, 0 collisions — PASS.
- chladni_eigen_verify.py: 9/9 gate (eigenmode physics exactness).
- Intake manifests: 0 empty slots on both pieces; UV present (Painter requirement).

## 7. Still owed (not this doc's claim)

S4/S5 editor materialization (14 MIs, live ground-snap, TraceChannel fix); MD drape
is interactive-only (no script API on this box); FLIP headless not dependable
(particlefluidtank 0 pts); seasonal _Opacity maps for lace cutout; hair pawn rebind.
Full five-stage chain doc landing separately:
Docs/Pipelines/MELODIA_BLENDER_MD_HOUDINI_SUBSTANCE_UE_PIPELINE_2026-09-03.md.
