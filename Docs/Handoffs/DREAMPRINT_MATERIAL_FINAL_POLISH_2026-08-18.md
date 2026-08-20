# Handoff — Dreamprint Material Final Polish (2026-08-18)

**Status**: The 3 dreamprint post-process MATERIALS are surgically reviewed, fixed,
compiling clean, and machine-verified. Final wiring polish is DONE.

Materials (the live dreamprint stack):
| Material | Path | Role |
|---|---|---|
| M_PP_MelodiaInk | `/Game/Melodia/_PROJECT/04_Materials/PostProcess/` | printed ink (After Tonemapping) |
| M_PP_MeluColorGrade | `/Game/_PROJECT/04_Materials/PostProcess/` | grade + DREAMPRINT sync-vision block |
| M_PP_StorybookOutline | `/Game/EnvSandbox/Materials/PostProcess/` (live profile parents the Premium_Candidate) | outline |

---

## 1. Root cause found (this session) — nothing was compiling

Both the ink master and the grade's dreamprint block failed shader compile since creation.
`recompile_material()` does not throw; the build audits only checked param lists, so the
failures were invisible. Evidence: `Saved/Logs/BS_GodFile.log` "Failed to compile Material
... Default Material will be used in game" + `Saved/ShaderDebugInfo/`.

**Why**: UE 5.8 emits Custom-node code as a helper function
`CustomExpression0(FMaterialPixelParameters Parameters)` — by-name globals (UV, SceneColor,
MPC channels, even the material's own scalar params) are NOT declared in that scope, and
`SceneTextureLookup` is not included. Proven by reading the generated shader dump
(`Saved/ShaderDebugInfo/.../PostProcessMaterialShaders.usf`).

**The working project pattern** (grade's original 25 inputs): every identifier the code
reads must be a **named function input**, wired from graph expressions. Proven via scratch
lab: generated call-site `CustomExpression0(Parameters, 0.5f, 0.5f, 0.25f)` showed values
propagating through renamed pins (`Saved/Audit/custom_input_lab*.json`).

## 2. What was fixed

### M_PP_MelodiaInk — rebuilt (build_dreamprint_material.py, force path, now canonical)
- **42 named inputs**: UV (ScreenPosition), SceneColor + cR/cB/smeared (SceneTexture
  PPI_PostProcessInput0 at graph-computed dynamic UVs — replaces the illegal
  `SceneTextureLookup` calls), 13 MPC channels (BeatPulse, ComboNormalized, EnemyTension,
  BreakPulse, VictoryPulse, MeluPrimary from MPC_Melodia_Palette; InkMasterWeight,
  InkSyncVision, InkBass, InkMid, InkTreble, InkReact, InkHueShift, InkAccentTint from
  MPC_MelodiaInk), 20 scalars + 4 vectors.
- **Dead params wired** (all identity-at-default — locked look preserved bit-identical):
  - `InkHatchShadowBand` → hatch zone slope `(1.0 + InkHatchShadowBand)`; default 1.0 = old `2.0`
  - `InkPaperLight` → paper-tone mix `(1.0 − InkPaperLight)·(1.0 − luma)`; default 1.0 = off
  - `InkPaperColor` → paper tint in that mix (gated by the above)
  - plus previously-unconsumed MPC: `InkMid` (mid-tone dot growth; default 0 = off),
    `InkHueShift` (accent blend toward `InkAccentTint`; 0.5 = identity), `InkAccentTint`
- **Blendable location**: explicit AFTER_TONEMAPPING — the rebuild hit handoff trap #5
  (`material_lib.post_process_blendable_location()` falls back to BL_REPLACING_TONEMAPPER);
  build script now resolves the enum explicitly and reasserts it.
- Compiles clean (log-verified), 0 unbound identifiers.

### M_PP_MeluColorGrade — 4 inputs appended (polish_dreamprint_grade_inputs.py)
- `BeatPulse`, `VictoryPulse`, `MeluPrimary` (MPC_Melodia_Palette), `InkSyncVision`
  (MPC_MelodiaInk) — the DREAMPRINT SYNC-VISION block's identifiers now resolve; block
  compiles. 29 inputs total. Compiles clean.

### M_PP_StorybookOutline — verified clean (no changes needed)
- MPC_Melodia_Palette referenced, 0 unbound identifiers, compiles. Note: the live profile
  (`MI_StorybookOutline_GameplayStandard`) parents **M_PP_StorybookOutline_Premium_Candidate**
  (Candidates/), not the base master.

### Other
- `mi_preview_studio.py:113` fixed: stale `/Game/Melodia/_PROJECT/.../M_PP_MeluColorGrade`
  → canonical `/Game/_PROJECT/.../M_PP_MeluColorGrade`.
- Scratch lab asset `_Scratch/M_PP_CustomInputLab` deleted (self-created).
- Stale grade forks (documented, NOT deleted — owner decision): 
  `Melodia/_PROJECT/04_Materials/PostProcess/M_PP_MeluColorGrade` (08-03, no V3 anchor) and
  `EnvSandbox/Materials/Masters/M_PP_MeluColorGrade` (08-12, V3 anchor, no DREAMPRINT block).

## 3. Verification

- `Saved/Audit/dreamprint_verify.json` — **ok=true, all 12 checks** (v2: adds input-bound
  check, blendable-location asserts for all 3 masters, compile state, metasound_exists
  now true — the old stale-false is resolved).
- Compile evidence: `LogShaderCompilers` shows NO failure after the final rebuilds;
  `Saved/ShaderDebugInfo/PCD3D_SM6` dumps are stale (pre-fix).
- Audit chain: `dreamprint_material_polish.json`, `dreamprint_grade_inputs.json`,
  `dreamprint_material_probe.json`, `custom_input_lab*.json`.

## 4. Scripts (Content/Python)

`build_dreamprint_material.py` (canonical: CODE + 42-input wiring + explicit blendable),
`polish_dreamprint_materials.py` (code/defaults/MPC refs — superseded by the rebuild for
the ink; kept for history), `polish_dreamprint_grade_inputs.py`, `verify_dreamprint.py` (v2),
`probe_dreamprint_materials.py`.

## 5. Still open (owner/GUI, unchanged scope)

PPV stale-volume cleanup (L_SakuraPath/L_Template), A/B + look approval
(`setup_dreamprint_ab.py`), MetaSound WatchOutput → InkReact BP wiring, director wiring —
see `DREAMPRINT_AUDIO_REACTIVITY_PREP_2026-08-18.md` (incl. the ComboNormalized/VictoryPulse/
BreakPulse/EnemyTension MPC-writer gap found during prep).