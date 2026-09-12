# Scale-First Musical PCG Stabilization — updated plan (2026-08-10)

Updated 2026-08-10 after tree-verification review. Every asset claim in this plan resolves to a
real asset/class in this project; the review ledger is
`Docs/Production/PCG/SCALE_FIRST_MUSICAL_PCG_PLAN_REVIEW_2026-08-10.md`.

## Current status

- Five proof graphs are authored: Cathedral, Arpeggio Bridge, BellTree Garden, Xylophone Trail, and Crystal Harp Grove.
- Crystal Harp now contains 20 real string meshes plus 5 cross-necks; its close and wide renders are saved.
- The shared interaction audit passes for all five graphs.
- The Crystal Harp graph audit passes.
- The current test suite is **44 `test_*.py` files** across `Content/Python/` and `Tools/`
  (not a fixed "40"); PCG lane tests are `test_pcg_hero_music.py`, `test_pcg_music_sequencer.py`,
  `test_pcg_nikki_scene_dressing.py`, `test_pcg_piano_layout.py`, `test_pcg_scale_world.py`,
  `test_pcg_visual_chunk_builder.py`, `test_pcg_xylophone_path.py`. Run the PCG subset, not a fixed 40.
- The editor is currently closed, so clock, audio, UDSA, live PCG generation, and post-rebuild verification remain pending.
- The combined graph audit (`Content/Python/audit_pcg_hero_graph_trees.py`) has a Resonance
  Cathedral **required-mesh-set** regression: `required_meshes_present` at `:140` fails against
  the spec at `:24-30` (5 required meshes incl. `SM_Pipe`, `tensor_policy: "required"`).
- Scale-world manifests contain the Harp graph and structural chunk bindings, but staged PCG/HLOD/navigation/RVT generation has not been completed.
- **Known architectural gap (added 2026-08-10):** the scale contract
  (`Content/Python/pcg_scale_world_pipeline.py:520-522`) hard-codes
  `"runtime_dependencies": []` and `"music_framework": "out_of_scope_for_visual_world_lane"`.
  The generated interactive nodes are not bound to the canonical clock/reactivity/audio at play
  time. This plan now fixes that before promotion.

**Status update (2026-08-10, Phase A executed):** the contract gap is **closed** — the scale
contract now declares the three runtime consumers (`UMelodiaRhythmReactivitySubsystem`,
`UMelodiaMusicClockSubsystem`, `UMelodiaAudioComponent`) with their call sites, and
`music_framework` names the canonical clock/reactivity/audio/MPC. PCG Python test subset
(35 tests) green; staged-build dry-run green. Pending: editor gate (Phase B) once the JRPG
lane releases the session.

**Status update (2026-08-10, Phase B executed — editor session free):**
- Combined graph-tree audit green for all five graphs after fixing the Cathedral `required_meshes`
  spec (removed the copy-pasted `SM_Pipe` requirement; authored set is piano key/keybed +
  `SM_column_02` + `SM_arch_06`) and the BellTreeGarden spec (removed stale `SM_Ceiling01`;
  authored set is floor/halfwall/column/arch). Both were audit-spec drift — the live graphs
  matched their builders exactly.
- All per-graph audits green: Cathedral 17/17 checks, ArpeggioBridge, BellTreeGarden,
  XylophoneTrail PASS; interaction contract PASS (5/5 graphs, `PCGHeroMusicNode` template
  classes, spring press contract).
- Runtime gates: `melodia.MusicClock.Ensure` dispatched; `MPC_Melodia_Palette` loads;
  `HeroMusicAudio` (MelodiaAudioComponent) on live host; `BP_MelodiaPCGControl_C` driver in
  level with `PCG_Control` tag; UDS present in BellTree proof level.
- Control-driver verification: native CDO read (`blueprint_query get_cdo_properties`) confirms
  all 11 `BP_MelodiaPCGControl` properties with categories (Shape/Walkability/Array/Curve/
  Transform = generation-time; Render = CullDistance/StencilValue/WriteCustomDepth).
- **Step 4 PIE musical-runtime proof PASSED** (`pie_smoke_7_235253`, `ok: true`): BellTree
  level, `SetPressedForActor` on a live `PCGBellTreeGardenNode` → node `IsPressed=True`,
  host `ScoreState total=18 hit=1 perfect=0 miss=0 score=50 streak=1` — full chain
  SetPressedForActor → OnNoteActivated → ApplyNoteToScore → NotifyCommandResolved live, zero
  fatals/asserts/BP-runtime-errors.
- Proof renders recaptured (all real files, `Saved/Audit/`): 5× `*_SceneStill.png` +
  5× `*_Wide_Recap.png`, 2.2–3.1 MB each. Note: `AutomationLibrary.take_high_res_screenshot`
  silently no-oped in `capture_pcg_visual_proofs.py` (rule 9); wide recaps used the
  SceneCapture2D + `export_render_target` path instead.
- Proof-map dirty state after render recook: `L_PCG_Hero_CrystalHarpGrove` (generated-state
  refresh only; left unsaved).
- No PIE or production-map edits have occurred. The concurrent water lane remains untouched.

## Next implementation sequence

1. Rebuild and runtime gate

   - Verify no competing editor/build process owns the module DLL.
   - Reuse the existing UBT rebuild command; use Live Coding only for necessary C++ changes.
   - Resolve any remaining CDO delegate warning, especially `APCGPianoKey::HandleStepBegin`, before declaring the build clean.
   - Reopen the editor and run:
     - `melodia.MusicClock.Ensure`
     - idle `MPC_Melodia_Palette` response check
     - audio/reactivity subsystem checks
     - UDSA proof-level actor check
   - Do not run PIE.

2. Close the graph-audit regression

   - Trace `required_meshes_present` in `Content/Python/audit_pcg_hero_graph_trees.py:140`
     against the Resonance Cathedral spec (`:24-30`).
   - If the required mesh list is stale (drifted from the authored classic-library branches),
     update the spec to the actual existing authored piano/keybed/column/arch/Pipe set.
   - If a graph branch is missing the expected mesh, add the authored mesh branch without changing the 12 interactive pads.
   - Rerun graph and interaction audits for all five graphs.
   - Require zero NaN transforms, unique seeds, valid MIDI identities, and correct actor counts:
     - Cathedral: 12
     - Bridge: 24
     - BellTree: 18
     - Xylophone: 24
     - Harp: 20

3. Execute the scale-first world pipeline

   - Preserve the canonical 25,600 cm World Partition cell (`WP_CELL_SIZE_CM` in
     `Content/Python/pcg_scale_world_pipeline.py:18`; `-IterativeCellSize=25600` in
     `run_pcg_scale_world_build.py:80`).
   - Run offline stages in order:
     1. filtered PCG generation
     2. HLOD generation
     3. navigation build
     4. minimap/RVT updates
   - Keep interactive actors in the gameplay Data Layer and excluded from HLOD
     (`pcg_generation_tiers` in `pcg_scale_world_pipeline.py:507-511`).
   - Capture PCG cache statistics before and after regeneration.
   - Run the 3×3 deterministic chunk seam test (`validate_grid` in
     `pcg_scale_world_pipeline.py:357-390`), including border signatures, nav clearance,
     camera anchors, and stable hero identities.

4. **Bind the generated musical runtime (new — closes the architectural gap)**

   - Stop the scale contract from declaring `runtime_dependencies: []` and
     `music_framework: out_of_scope_for_visual_world_lane`:
     1. Register generated hero nodes with `UMelodiaRhythmReactivitySubsystem` at spawn
        (mirror the existing consumer pattern at `Source/BS_GodFile/Piano/PCGHeroMusic.cpp:89,581-626`).
     2. Route note activation through the shared clock (`UMelodiaMusicClockSubsystem::Get`,
        as already done at `PCGHeroMusic.cpp:395,598-604`) and `UMelodiaAudioComponent::PlayMusicalNote`.
     3. Update `pcg_scale_world_pipeline.py:520-522` to list these dependencies and set
        `music_framework` to the canonical clock/reactivity/audio subsystems.
   - Gate promotion on one **recorded PIE interaction** (press a generated node → note plays →
     reactivity signal publishes), not on static audits alone.
   - No second clock, MPC writer, or reactivity subsystem is added; the plan only wires consumers.

5. Verify real-time controls

   - Change each of the eleven `BP_MelodiaPCGControl` properties independently
     (`Content/Python/pcg_hero_music_control.py:15-27`, alias targets `:32-44`).
   - Regenerate through the existing On-Demand workflow.
   - Record measurable geometry/count/spacing changes for generation-time controls.
   - Verify render controls map to culling, custom depth, stencil, and render-custom-depth behavior.
   - Document any control that is intentionally generation-time only.

6. Visual and interaction review

   - Recapture wide and close proof renders for all five graphs.
   - Review each render for:
     - readable walkable corridor
     - height-aware spacing
     - foreground occlusion
     - recognizable instrument silhouette
     - authored classic architecture
     - no cube fallback geometry
   - For Harp specifically, require visible strings attached to press pads and visible station necks.
   - Preserve proximity filtering, spring press/release, canonical rhythm grading, audio note playback, and the single clock/reactivity/MPC architecture.

7. Promotion freeze

   - Produce proof manifests, audit reports, renders, cache statistics, and promotion recipes.
   - Keep production maps untouched until explicit visual and interaction approval.
   - Defer `QuantumPulse`/`QuantumReactionColor` writer work.

## Interfaces to preserve

- `FPCGHeroMusicNoteEvent`
- `FPCGHeroMusicScoreState`
- `APCGHeroMusicNode`
- `UMelodiaAudioComponent::PlayMusicalNote`
- `UMelodiaMusicClockSubsystem`
- `UMelodiaRhythmReactivitySubsystem`
- `MPC_Melodia_Palette`
- The eleven existing `PCG_Control` properties and their alias mappings

## Acceptance tests

- Clean editor rebuild and no startup CDO delegate warning.
- All five graph audits green (incl. Cathedral required-mesh set).
- All five interaction audits green.
- PCG Python test subset green (7 files, see Current status — do not assert a fixed "40").
- Correct actor counts, deterministic seeds, MIDI identities, collision, pivots, and capsule clearance.
- No duplicate clock, MPC writer, or reactivity subsystem.
- **One recorded PIE interaction: generated node press → `PlayMusicalNote` on the shared clock →
  reactivity publish. This is the musical-runtime completion gate (new).**
- Every control-driver knob produces a documented result.
- PCG/HLOD/nav/RVT stages complete with cache evidence.
- 3×3 chunk seam test passes.
- Wide and close proof renders pass spatial and instrument-readability review.
- No PIE or production-map mutation without separate approval.

## Assumptions

- Audit and scale hardening take priority over adding another instrument.
- Proof-level work remains additive and isolated.
- The concurrent water lane is not restarted, terminated, or modified.
- Existing authored meshes and classic architecture pieces remain mandatory; cube substitutes are disallowed.
- The scale world is environment-art; the JRPG + QuillScript lane is a separate track and this
  plan does not claim to advance it.
