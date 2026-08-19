# Handoff — Dreamprint Stack Build (2026-08-16)

**Status:** Material/MPC/grade layers **BUILT + VERIFIED headless**; MetaSound
wrapper **BUILT + VERIFIED** (Monolith-less Python route cracked — see §HOLD
→ §BUILT below). A/B + look approval + director wiring = next GUI session.

> **AMENDMENT 2026-08-18** — the material/MPC layers did **NOT** compile as built:
> UE 5.8 custom nodes only see named function inputs, so by-name MPC/param/UV
> references (the "no collection nodes needed" claim below) failed shader
> compile silently. Fixed + verified — see
> `DREAMPRINT_MATERIAL_FINAL_POLISH_2026-08-18.md` and
> `DREAMPRINT_AUDIO_REACTIVITY_PREP_2026-08-18.md`. The verified seam map in the
> audio-reactivity doc supersedes §"Audio inputs" naming below where they differ.

---

## What landed (all read-back verified)

| Asset | Path | Verified |
|---|---|---|
| MPC_MelodiaInk | `/Game/Melodia/_PROJECT/04_Materials/MPC_MelodiaInk` | 7 scalars + InkAccentTint, `ok:true` |
| M_PP_MelodiaInk (master) | `/Game/Melodia/_PROJECT/04_Materials/PostProcess/M_PP_MelodiaInk` | PP domain, **BL_SCENE_COLOR_AFTER_TONEMAPPING**, 23 params, 1 Custom node (3917 chars) |
| MI_MelodiaInk_GameplayStandard | `.../PostProcess/Candidates/Profiles/` | parent M_PP_MelodiaInk ✓ |
| MI_MelodiaInk_Narrative | same folder | ✓ (print offset on) |
| MI_MelodiaInk_PortfolioHero | same folder | ✓ (offset + smear on) |
| M_PP_MeluColorGrade + SyncVision | `/Game/_PROJECT/04_Materials/PostProcess/M_PP_MeluColorGrade` | DREAMPRINT block inserted pre-return, gated on `InkSyncVision > 0.001` (locked look preserved at 0) |

**The one master (owner decision #2) carries the whole printed family**, float-gated:
1. **Halftone (Ben-Day)** — rotated screen-space dot grid, dot radius driven by
   luma (bigger ink in shadow), beat/combo/bass grow dots, fwidth-soft edges.
2. **Hatch (Thresher)** — shadow-zone lines, EnemyTension darkens the zone.
3. **Print offset (ChromaShifter)** — radial R/B misregistration + BreakPulse
   paper-slip.
4. **Paper grain** — hash noise, Treble lifts it, animated.
5. **Sync Vision** — beat/victory palette pulse, comic flash, halftone-negative
   flicker (MeluPrimary-anchored, capped).
6. **Motion smear** — optional, off in Gameplay/Narrative.

Audio inputs are unique MPC globals only: BeatPulse, ComboNormalized,
EnemyTension, BreakPulse, VictoryPulse, MeluPrimary (MPC_Melodia_Palette) +
InkMasterWeight/InkSyncVision/InkBass/InkMid/InkTreble/InkReact
(MPC_MelodiaInk). No collisions with MPC_Portfolio_Audio.

## BUILT — MSS_MelodiaMusicPulse (MetaSound wrapper) — 17:48, live editor

All steps SUCCEEDED via the raw Python binding (Monolith audio_query in this
binary has NO MetaSound actions — SoundCue namespace only — so the spec-builder
route was unavailable; the binding was cracked instead). Verified read-back:
`/Game/Melodia/_PROJECT/04_Audio/Music/MSS_MelodiaMusicPulse` is a real
persistent MetaSoundSource (not transient).

Graph: WavePlayer (`UE/"Wave Player"/Mono`, Wave Asset =
SW_BGM_Zundamon_Sewaa_Full, Loop=true) → "Out Mono" → EnvelopeFollower
(`UE/"Envelope Follower"`, "In") → "Envelope" → graph output "Envelope";
Out Mono also → source audio output.

Key binding facts (all probe-resolved; see build_dreamprint_metasound.py):
- accessor `unreal.get_engine_subsystem(unreal.MetaSoundBuilderSubsystem)`
- `create_source_builder(name, MetaSoundOutputAudioFormat.MONO, False)` → 5-tuple
- node classes via `unreal.MetasoundFrontendClassName("UE", "<name>", "<variant>")`
- pin names are DISPLAY names: "Out Mono", "In", "Wave Asset", "Loop"
- `connect_nodes(output_handle, input_handle)` — handles from find_node_*
- `connect_node_output_to_graph_output(GRAPH_OUTPUT_NAME, node_output_handle)` — **name FIRST**
- literals ONLY via `unreal.MetasoundFrontendLiteralBlueprintAccess`
  (`create_bool/float/object_meta_sound_literal`) — the literal `Type` property
  is protected; empty literals SUCCEED silently (silence trap — avoided)
- asset must be created first (`unreal.MetaSoundSourceFactory` + AssetTools)
  then `build_and_overwrite_meta_sound(asset)` + save; `build_new_meta_sound`
  yields only a transient object

**Remaining for the director:** sample `Envelope` via
`UMetaSoundOutputSubsystem::WatchOutput` (BlueprintCallable, needs the
UAudioComponent playing this source) → write `InkReact` on MPC_MelodiaInk.

## Next (GUI session, one editor)

1. **A/B + look approval** — `Content/Python/setup_dreamprint_ab.py`:
   `mode("candidate", "PortfolioHero")` vs `mode("source")` at fixed 16:9
   cameras on L_KaleidoNave / L_FallenMoon / ZenForestTest / L_MelusinaMorning.
   Candidate volume = approved outline+grade + ink layer on top, priority 25.
   No live-PPV edits until owner sign-off.
2. **MetaSound wrapper** via Monolith spec builder (above).
3. **Director wiring** — `Docs/Plans/DREAMPRINT_DIRECTOR_WIRING_2026-08-15.md`
   (audio component + WatchOutput → InkReact; ProfileIndex 0/1/2 switches
   ink profile MIs + InkMasterWeight).
4. **Cost table** — force a stat refresh (PP instructions/samplers per effect
   gate), Penrose-lattice jitter check (`L_FallenMoon`, 780 beams), TSR
   stability note (After-Tonemap = LDR, cheap; outline stays Before-Tonemap).

## Traps recorded this session (extend AGENTS.md)

1. **`-foo=$var` in native-call position is NOT interpolated** in PowerShell
   5.1 (parsed as parameter declaration) — pre-build argument strings.
2. **`Start-Process -Wait` hung** on UnrealEditor-Cmd despite process exit;
   use direct `&` with `$LASTEXITCODE` (or WaitForExit polling).
3. **Editor exit code is unreliable** (0 even on Python errors) — gate on the
   audit JSON + grep the log for `LogEditorPythonExecuter: Error`.
4. **`get_assets_by_class` needs `/Script/Module.Class` and `get_editor_subsystem`
   rejects engine subsystems** — use `get_engine_subsystem` for
   MetaSoundBuilderSubsystem.
5. **UE 5.8 renamed** `BL_SCENE_COLOR_AFTER_TONEMAPPING` (with PING) — and
   `material_lib.post_process_blendable_location()` falls back to
   `BL_REPLACING_TONEMAPPER` (wrong for LDR passes); pass the location
   explicitly.
6. **MetaSound binding traps:** `create_source_builder` returns a 5-tuple;
   `add_node_by_class_name` takes `MetasoundFrontendClassName` struct; pin
   names are display names ("Out Mono", "In", "Wave Asset"); literal structs
   accept empty silently (silent silence risk).

## Files

Scripts (Content/Python/): `build_dreamprint_mpc.py`, `build_dreamprint_material.py`,
`upgrade_grade_dreamprint.py`, `build_dreamprint_metasound.py`,
`fix_dreamprint_blendable.py`, `verify_dreamprint.py`, `setup_dreamprint_ab.py`.
Runner: `deploy/run_dreamprint_build.ps1`. Spec:
`specs/dreamprint_music_pulse_metasound.json`. Audit: `Saved/Audit/dreamprint_*.json`.
