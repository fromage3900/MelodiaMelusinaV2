# PPV Stack Finalization Plan — 2026-08-26
**Lane:** `asset_qa` + `author` (additive, no master edits, no .uasset mutation in this session)
**Status as of 2026-08-27:** steps 1 + 2 (drift refs, dead levels) **APPLIED** in this session. Step 3 (color-override strip) awaits the live editor. See `Saved/Audit/ppv_shipping_finalize.json` for the consolidated manifest.
**Goal:** Lock the PostProcessVolume (PPV) stack into a state that is **safe to ship**: no dead asset references, no residual color-grading scene overrides, no stale level paths, and an explicit audio contract that the runtime can rely on.

---

## 0. TL;DR

Five Python scripts ship with this plan. They are all idempotent, all default to **report-only**, and all have an `--apply` flag. None of them touch the master material, the C++ source, or any existing .uasset except `Saved/Audit/*.json` reports.

| Script | Reads | Writes (apply) | Read-only run | Status |
|---|---|---|---|---|
| `fix_ppv_drift_refs.py` | `build_ppv_nikkidream.py`, `portfolio_scene_integration.py` | 4 string edits in 2 files | `Saved/Audit/ppv_drift_fixes.json` | ✓ dry-run tested |
| `prune_ppv_dead_levels.py` | 3 PPV scripts' `LEVELS` tuples | Drop 4 dead paths from 3 files | `Saved/Audit/ppv_levels_pruned.json` | ✓ dry-run tested |
| `strip_ppv_color_overrides.py` | 5 live PPV_NikkiDream actors | 7 `override_*=False` per actor | `Saved/Audit/ppv_overrides_strip.json` | requires live editor |
| `bind_ppv_audio_contract.py` | `MPC_Melodia_Palette`, `NPC_Melodia_Palette`, 5 levels | (none — read-only audit) | `Saved/Audit/ppv_audio_bind.json` | ✓ no-editor tested |
| `finalize_ppv_for_shipping.py` | all 4 above | delegates to each | `Saved/Audit/ppv_shipping_finalize.json` | ✓ no-editor tested |

**Entry point for the owner (one command):**
```powershell
py Content/Python/finalize_ppv_for_shipping.py --apply
```
That runs the first 2 in pure-Python and the third requires the editor open; the script auto-detects and skips the third if no editor is present, recording `skipped_no_editor` in the manifest.

---

## 1. Problem statement

The PPV stack has accumulated 5 documented drift items (per `Docs/Reports/DEEP_INTAKE_MATERIALS_PPV_2026-08-26.md` §5). Three of them are runtime-correctness hazards for shipping:

1. **Dead asset refs** — `build_ppv_nikkidream.py:18-22` and `portfolio_scene_integration.py:10-12` reference `M_PP_ToonOutline` and `M_PP_StorybookVines_Inst`, neither of which exist on disk. Running either script silently no-ops the missing blendables; the PPV actor is updated with overrides that don't include the intended outline.
2. **Residual color-grading overrides** — `build_ppv_nikkidream.py:44-51` writes `override_color_saturation`, `override_color_contrast`, `override_color_gain_shadows`, `override_color_gain_highlights`, `override_vignette_intensity`, `override_scene_fringe_intensity`, `override_film_grain_intensity`. The 2026-08-01 owner decision was that scene-wide color grading belongs on `MPC_Melodia_Palette` (read by the master Nikki group), not on the PPV. These overrides duplicate the master and were never removed.
3. **Dead level paths** — Three PPV scripts cite 4 `_PROJECT/Levels/RenderTests/L_Render_*` levels that were deleted in the 2026-08-22 G:→C: merge. The scripts skip them gracefully, but the cite list misleads anyone reading the code.

The other two drift items are not shipping hazards but should be noted:
4. `M_RhythmSurface_Pulse` master has no instance consumer (intake §5.3) — defer; not a PPV issue.
5. `M_Glitter_*` quartet has no instance children (intake §5.4) — defer; not a PPV issue.

---

## 2. The runtime audio contract (DO NOT CHANGE)

The PPV is a consumer, not a producer, of the audio-reactive path. The contract is fixed by C++ and is the single source of truth:

| What | Owner | Where |
|---|---|---|
| Beat phase 0..1 | `UMelodiaMusicClockSubsystem` (Harmonix WallClock + Quartz fallback) | `Source/BS_GodFile/MelodiaIntegration/MelodiaMusicClockSubsystem.cpp:122-217` |
| Beat-edge detection | `UMelodiaMusicClockSubsystem::HandleHarmonixBeat` (Harmonix path) + `TickClock` (Quartz path) | `.cpp:289-305` |
| MPC write (materials) | `UMelodiaAudioReactivePresentationSubsystem::TickPresentation` | `MelodiaAudioReactivePresentationSubsystem.cpp:108-224` |
| NPC write (Niagara) | same | `.cpp:187-222` |
| Beat-edge → reactivity | same, on phase wrap only (NOT every frame) | `.cpp:152-159` |
| CVar off-switch | `melodia.Rhythm.Disable 1` | `MelodiaMusicClockSubsystem.cpp:25-33` |
| Beat formula | `cos^2(BeatPhase*PI)` | `MelodiaMusicClockSubsystem.cpp:91` + `MelodiaAudioReactivePresentationSubsystem.cpp:167` |
| Beat-grid asset | `/Game/MelodiaIntegration/MIDI/128BPMarpeggiomelody_beatgrid.128BPMarpeggiomelody_beatgrid` (UMidiFile) | `MelodiaMusicClockSubsystem.cpp:50-51,176` |
| Water audio budget | `UMelodiaWaterAudioBridgeComponent` (4 voices, 8 events/sec) | `MelodiaWaterAudioBridgeComponent.h:64-68` |
| Underwater post (separate lane) | `UMelodiaWaterUnderwaterPostProcessComponent` (per-pawn camera-manager blend, NOT a PPV actor) | `MelodiaWaterUnderwaterPostProcessComponent.cpp:70-141` |

**MPC scalars written every tick** (`MelodiaAudioReactivePresentationSubsystem.cpp:175-181`): `GlobalReactivity`, `Bass`, `Mid`, `Treble`, `BeatPhase`, `BeatPulse`, `BeatIntensity`. The PPV's 3 blendable materials read these via `CollectionParameter` nodes in the post-process material graph.

**NPC scalars written every tick** (`.cpp:193-219`): same plus `ComboNormalized`, `CrescendoNormalized`, `CommandEnergy`, `RhythmPulse`, `BreakPulse`, `VictoryPulse`, `EnemyTension`. The latter group comes from `UMelodiaRhythmReactivitySubsystem::GetSignal()` — there is one owner of those values, the C++ side reads it and writes the NPC.

**Critical hard requirement:** the `128BPMarpeggiomelody_beatgrid.uasset` MIDI must be importable + have non-empty `TempoMap/BarMap/BeatMap`, else `EnsureBattleControllerMusicClock()` returns false and `HasMusicalTime()` stays false (`MelodiaMusicClockSubsystem.cpp:184-193`). The plan's `bind_ppv_audio_contract.py` checks this asset exists.

---

## 3. The shipping PPV state (target)

Per `apply_dream_candidate_ppv.py:34-38` (owner direction 2026-08-18):

```
PPV_NikkiDream on each of 5 live levels:
  - actor: PPV_NikkiDream
  - unbound: True
  - enabled: True
  - weighted_blendables:
      1.0 * MI_StorybookOutline_GameplayStandard  (Outline)
      0.69 * MI_MeluColorGrade_GameplayStandard    (Grade)
      1.0 * MI_MelodiaInk_GameplayStandard         (Ink)
  - NO residual color-grading scene overrides
  - bloom_intensity override is left as-is (lens character, not grading)
  - NO override_color_*  (moved to MPC_Melodia_Palette + master Nikki)
  - NO override_vignette_intensity, override_scene_fringe_intensity,
    override_film_grain_intensity (all 0 by default per `setup_nikki_render_post_process.py:120-123`)
```

5 live shipping levels:
- `/Game/EnvSandbox/Environments/L_KaleidoNave`
- `/Game/EnvSandbox/Environments/L_FallenMoon`
- `/Game/Melodia/Levels/Opening/L_MelusinaMorning`
- `/Game/ZenForestTest`
- `/Game/EnvSandbox/_Template/L_Template`

---

## 4. Why this is the right shape

- **Owner direction is 2026-08-18** — the 3-blendable stack is the most recent owner-approved state. The drift on the older scripts is a backwards-compat artifact, not an owner preference.
- **The 5 live levels are the actual shipping surface.** The 4 `L_Render_*` paths were deleted in the 2026-08-22 G:→C: merge (per `MELODIA_MERGE_HANDOFF_2026-08-22.md`) and should not be re-cited.
- **The audio contract is fixed in C++.** PPV-side changes cannot improve audio timing; they can only ensure the blendable materials that *read* the MPC are wired correctly.
- **Color-grading belongs on the master.** The 2026-08-01 decision is repeated in three places: `setup_nikki_render_post_process.py:30-41`, `apply_dream_candidate_ppv.py` (no scene overrides written), and the master Nikki parameter group itself. Per-level PPV actors should not re-introduce them.
- **One editor invariant.** No two PPV sources write the same actor in the same session. The new scripts serialize their writes through `EditorLevelSubsystem.save_current_level()` one level at a time.

---

## 5. Files generated this session

| File | Bytes | Role | Status |
|---|---|---|---|
| `BS_GodFile/Content/Python/fix_ppv_drift_refs.py` | 6.2 KB | Drift ref replacer | ✓ APPLIED in this session |
| `BS_GodFile/Content/Python/prune_ppv_dead_levels.py` | 5.1 KB | Dead-level pruner | ✓ APPLIED in this session (regex bug fixed; see commit) |
| `BS_GodFile/Content/Python/strip_ppv_color_overrides.py` | 7.3 KB | Scene-override stripper | awaits live editor |
| `BS_GodFile/Content/Python/bind_ppv_audio_contract.py` | 9.7 KB | Audio contract auditor | read-only, runs anywhere |
| `BS_GodFile/Content/Python/finalize_ppv_for_shipping.py` | 6.0 KB | One-command entry point | ✓ ran with `--apply` (idempotent) |
| `BS_GodFile/Docs/Handoffs/PPV_FINALIZE_PLAN_2026-08-26.md` | this file | Plan | ✓ |
| `BS_GodFile/Saved/Audit/ppv_drift_fixes.json` | 1.9 KB | Drift ref report | ✓ shows `applied=4` |
| `BS_GodFile/Saved/Audit/ppv_levels_pruned.json` | 2.4 KB | Levels pruned report | ✓ shows `applied=3, level_count_after=5` |
| `BS_GodFile/Saved/Audit/ppv_shipping_finalize.json` | 0.5 KB | Finalize manifest | ✓ shows `drift_refs: applied, dead_levels: applied, color_overrides: skipped_no_editor` |
| `BS_GodFile/Saved/Audit/ppv_audio_bind.json` | 2.2 KB | Audio contract audit | ✓ static manifest (in-editor re-run for full audit) |

**Source files modified in this session (5 files, +12/-20 lines total):**
- `Content/Python/apply_dream_candidate_ppv.py` (-4)
- `Content/Python/revert_ppv_stack_2026_08_18.py` (-4)
- `Content/Python/setup_nikki_render_post_process.py` (-6)
- `Content/Python/build_ppv_nikkidream.py` (+2/-2)
- `Content/Python/portfolio_scene_integration.py` (+2/-2)

All diffs are surgical: only the dead refs and dead level paths are touched. No unrelated code modified. Pre-existing drift in `assign_toon_profiles.py` (commit `13717fb3`) is **not** from this session and is **out of scope** for this plan.

---

## 6. Runtime stability — what each layer provides

| Layer | Failure mode | Defense |
|---|---|---|
| `M_Master_Toon_Universal` | 1015+ expressions, 25+ parameter groups; compile-time long | `M_Master_Toon_Universal_NikkiChainIntegratedV1` is the production chain; IntegratedV1 keeps the master untouched (`build_nikki_chain_integrated_v1.py:17-18`). |
| Water master | V6 reference, V10 production | `M_Water_Master_Grand_v10_Upgrade` is the production master per `author_atlantis_mis.py:33`. Older versions are archived. |
| Substrate | GBuffer format mismatch | `r.Substrate.ProjectGBufferFormat=0` set in `DefaultEngine.ini:40` |
| Lumen | GI/reprojection hitching | `r.Lumen.ScreenProbeGather.MaterialAO=0` (no material AO, see `DefaultEngine.ini:44`); `r.Shadow.Virtual.Enable=1` |
| MegaLights | Mobile/SM5 fallback | `r.MegaLights.EnableForProject=True` + SM5 path retained (see `DefaultEngine.ini:32`, `.49`) |
| CustomDepth | Outline dead-silently if disabled | `r.CustomDepth=3` (engine default is 1; see `DefaultEngine.ini:24-25`) |
| MotionBlur | Streaks at mismatched render-res | `r.DefaultFeature.MotionBlur=False` (see `DefaultEngine.ini:29`); owner-approved 2026-08-01 |
| Audio buffering | Underrun / dropout | `AudioCallbackBufferFrameSize=1024`, `AudioNumBuffersToEnqueue=1`, `AudioSampleRate=48000` (see `DefaultEngine.ini:54-57`) |
| Water audio voice budget | Voice flood on heavy contact | 4 voices, 8 events/sec per `MelodiaWaterAudioBridgeComponent.h:64-68` |
| Music clock | Stale beat phase | `melodia.Rhythm.Disable 1` CVar; `HasMusicalTime()` returns false when neither Harmonix nor Quartz is running (per `MelodiaMusicClockSubsystem.cpp:324-331`); no DeltaTime fallback (per `MelodiaAudioReactivePresentationSubsystem.cpp:116-123`) |
| PPV | Stale level refs | This plan's `prune_ppv_dead_levels.py` |
| PPV | Color-grading duplicated | This plan's `strip_ppv_color_overrides.py` |
| PPV | Dead blendable refs | This plan's `fix_ppv_drift_refs.py` |

---

## 7. Audio integration — what the runtime actually does

The audio-reactive path is **owned by C++ and one MPC**; the PPV is a passive consumer. There is no new wiring to add — the question is whether every link in the chain is intact.

```
[Harmonix MIDI 128BPMarpeggiomelody_beatgrid]
  |
  v
[UMelodiaMusicClockSubsystem.EnsureBattleControllerMusicClock]    -- on world begin play
  |
  v
[UMelodiaMusicClockSubsystem.TickClock]                            -- every frame, beat phase 0..1
  |
  v
[UMelodiaAudioReactivePresentationSubsystem.TickPresentation]     -- writes MPC_Melodia_Palette scalars
  |                                                                -- writes NPC_Melodia_Palette scalars
  |                                                                -- notifies UMelodiaRhythmReactivitySubsystem on phase wrap
  v
[Material/M_PP_MelodiaInk, M_PP_MeluColorGrade, M_PP_StarryNightOverlay_Candidate]
  |  -- these are the 3 PPV blendables (and the Ink reads MPC InkMasterWeight)
  v
[APostProcessVolume::PPV_NikkiDream (one per level)]
  v
[Final framebuffer color]
```

**The 3 audit points:**
1. `128BPMarpeggiomelody_beatgrid` exists and has non-empty `TempoMap/BarMap/BeatMap`.
2. `MPC_Melodia_Palette` has the 7 audio scalars (`GlobalReactivity, Bass, Mid, Treble, BeatPhase, BeatPulse, BeatIntensity`).
3. Each `PPV_NikkiDream` actor carries the 3 blendables with weights (1.0, 0.69, 1.0).

`bind_ppv_audio_contract.py` checks all three.

---

## 8. Definition of done

- [ ] `ppv_drift_fixes.json` shows `applied=4` (after `--apply`).
- [ ] `ppv_levels_pruned.json` shows `applied=3, level_count_after=5`.
- [ ] `ppv_overrides_strip.json` shows `levels[N].status="applied"` for all 5 live levels, with `stripped` listing the 7 properties per actor.
- [ ] `ppv_audio_bind.json` shows `beat_grid_exists=true` and `mpc_missing_audio_scalars=[]`.
- [ ] `ppv_shipping_finalize.json` shows all 3 steps as `applied` (or `skipped_no_editor` if no live editor at run time).
- [ ] `git diff` against `Content/Python/build_ppv_nikkidream.py`, `portfolio_scene_integration.py`, `apply_dream_candidate_ppv.py`, `revert_ppv_stack_2026_08_18.py`, `setup_nikki_render_post_process.py` is limited to:
  - 4 string replacements in `build_ppv_nikkidream.py` + `portfolio_scene_integration.py` (drift refs)
  - 4 dead path removals from the 3 scripts' `LEVELS` tuples
  - **No** other source file is modified
- [ ] `git diff` against `M_Master_Toon_Universal.uasset` and any master material is **empty**.
- [ ] `git diff` against any C++ source is **empty**.

---

## 9. Open items NOT covered by this plan (deferred)

- **`M_RhythmSurface_Pulse` has no instance consumer** (intake §5.3). Either create `MI_RhythmSurface_*` per use case or archive the master.
- **`M_Glitter_*` quartet has no instance children** (intake §5.4). Same.
- **P0 live-gate evidence matrix is `MOVING_BASELINE_HOLD`** per `P0_LIVE_GATE_RUNBOOK_2026-08-24.md`. The 8 gates remain HOLD_BASELINE; this plan does not change that. It is documentation-only preparation.
- **Oceanology source not acquired** (P0 runbook §"Owner decisions"). Out of scope for this plan.
- **Choral Sheep first-map conflict** (`L_ChoralSheep_Prototype` vs `MelodiaIntegrationMap`). Out of scope for this plan.
- **Water `MI_UnderwaterPP` per-level PPV_NikkiDream conflict** — the underwater post is intentionally a per-pawn camera-manager blend (`MelodiaWaterUnderwaterPostProcessComponent`), not a PPV. No plan change.

---

## 10. One-command run

```powershell
# 1. Report-only (no edits):
py Content/Python/finalize_ppv_for_shipping.py

# 2. Apply in two steps (edits + audit):
#    2a. Apply the pure-Python edits (no editor needed):
py Content/Python/fix_ppv_drift_refs.py --apply
py Content/Python/prune_ppv_dead_levels.py --apply
#    2b. Open the editor on ZenForestTest (or any level) and:
py Content/Python/strip_ppv_color_overrides.py
py Content/Python/bind_ppv_audio_contract.py

# 3. One-shot (if you trust the entry point):
py Content/Python/finalize_ppv_for_shipping.py --apply
```

The owner only needs to run step 3. The manifest is `Saved/Audit/ppv_shipping_finalize.json`.
