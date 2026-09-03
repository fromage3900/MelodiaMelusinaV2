# Scale-First Musical PCG Stabilization — plan review, folded (2026-08-10)

Reviewed the "Scale-First Musical PCG Stabilization" plan against the live tree. Every asset
claim was checked against `Content/` and `Source/BS_GodFile/Piano/`. Status: **grounded, no
fabricated assets**, with two doc corrections and one architectural failure to record.

**The corrected, actionable plan is `Docs/Production/PCG/SCALE_FIRST_MUSICAL_PCG_PLAN_2026-08-10.md`.**
This file is the evidence ledger behind that plan's changes.

## 1. Verified real (plan claims confirmed against tree)

| Plan claim | Verified in tree |
|---|---|
| 5 proof graphs + profiles + proof levels | `Content/EnvSandbox/PCG/Musical/Hero/PCG_Hero_{ResonanceCathedral,ArpeggioBridge,BellTreeGarden,XylophoneTrail,CrystalHarpGrove}` + `DA_Hero_*Profile` + `L_PCG_Hero_*` |
| `FPCGHeroMusicNoteEvent`, `FPCGHeroMusicScoreState`, `APCGHeroMusicNode` | `Source/BS_GodFile/Piano/PCGHeroMusic.h:51,75,166` |
| `APCGPianoKey::HandleStepBegin` | `Source/BS_GodFile/Piano/PCGPianoKeyboard.cpp:212` (delegate bound at `:80`) |
| `UMelodiaAudioComponent::PlayMusicalNote` | `Source/BS_GodFile/Piano/PCGHeroMusic.cpp` (subobject `HeroMusicAudio` at `:440`) |
| `UMelodiaMusicClockSubsystem` / `UMelodiaRhythmReactivitySubsystem` | Present; used by `PCGHeroMusic.cpp:89,395,581-626` |
| `MPC_Melodia_Palette` | `/Game/Melodia/_PROJECT/04_Materials/MPC_Melodia_Palette` |
| **11** `BP_MelodiaPCGControl` properties + alias mappings | `Content/Python/pcg_hero_music_control.py:15-27` (exactly 11) + `CONTROL_ALIAS_TARGETS:32-44`; BP at `Content/EnvSandbox/PCG/Universal/BP_MelodiaPCGControl.uasset` |
| Actor counts 12/24/18/24/20 | `Content/Python/audit_pcg_hero_interaction_contract.py:10-14` |
| Canonical 25,600 cm WP cell | `Content/Python/pcg_scale_world_pipeline.py:18`; `run_pcg_scale_world_build.py:80` `-IterativeCellSize=25600` |
| Crystal Harp: 20 strings + 5 cross-necks | `Content/Python/build_pcg_hero_crystal_harp_grove.py:70,107` |
| PCG → HLOD → nav → minimap/RVT offline stages | `Content/Python/run_pcg_scale_world_build.py:135-141` |
| Interaction + graph audits for all 5 graphs | `Content/Python/audit_pcg_hero_interaction_contract.py`, `audit_pcg_hero_graph_trees.py`, per-graph `audit_pcg_hero_*.py` |
| 3×3 chunk seam test + border signatures + stable hero identities | `Content/Python/pcg_scale_world_pipeline.py:118-390` (`validate_grid`) |
| Interactive actors in gameplay Data Layer, excluded from HLOD | `pcg_scale_world_pipeline.py:507-511` (`pcg_generation_tiers`) |

## 2. Corrections (plan vs reality)

1. **"40 Python tests" is not reproducible.** The tree has **44** `test_*.py` files across
   `Content/Python/` and `Tools/` — not 40 — and no runner pins a stable aggregate count. Treat
   "40 tests green" as a *specific* suite (e.g. `test_pcg_scale_world.py`,
   `test_pcg_hero_music.py`, `test_pcg_visual_chunk_builder.py`, `test_pcg_*`), not a fixed 40.
2. **The "combined graph audit" is `audit_pcg_hero_graph_trees.py`** (not a separately named
   "combined" asset). The Resonance Cathedral spec there pins `tensor_policy: "required"` and 5
   required meshes incl. `SM_Pipe` (`:24-30`). The plan's "missing required mesh" is this
   required-mesh set drift, not a missing graph — consistent with
   `Docs/Handoffs/HANDOFF_PCG_HERO_AUDIO_2026-08-09.md` (classic architecture branches preserved).
   Fix path per plan step 2 is valid: trace `required_meshes_present` at `audit_pcg_hero_graph_trees.py:140`.

## 3. Where the plan fails to create the architecture it needs

**The plan's own scale contract severs it from the music/gameplay loop.**

`Content/Python/pcg_scale_world_pipeline.py:520-522` hard-codes:

```
"runtime_dependencies": [],
"music_framework": "out_of_scope_for_visual_world_lane",
```

A plan titled "Musical PCG" whose chunk contract declares **zero runtime dependencies** and
places the music framework explicitly out of scope builds the World Partition/HLOD/nav/RVT
machinery correctly but **binds nothing to the shared clock, reactivity, or audio** at play time.
The interactive pads/nodes are generated and statically audited; nothing in the scale path
registers them with `UMelodiaRhythmReactivitySubsystem`, plays `PlayMusicalNote`, or joins the
narrative bridge. Steps 4-5 (control-driver verification, visual review) are the only runtime
touches, and both are explicitly non-PIE.

- The acceptance gate "no duplicate clock/MPC/reactivity" is vacuously satisfied: the lane adds
  **no consumer** of those singletons, so there is nothing to duplicate — and nothing that plays.
- This lane is environment-art only. It does **not** advance the AGENTS.md current phase
  (Production JRPG + QuillScript: dialogue → JRPG battle → result → resume).

**Action if the architecture is the goal:** add the missing consumer wiring so generated hero
nodes register with the canonical reactivity subsystem and call `PlayMusicalNote` on the shared
clock (mirror `PCGHeroMusic.cpp:89`), then record one PIE interaction as the completion gate.
Until then the plan succeeds at *scale-first environment generation* and stops short of a
*musical* runtime.

## 4. Assets referenced for the PCG workflow

- Driver BP: `Content/EnvSandbox/PCG/Universal/BP_MelodiaPCGControl.uasset`
- Alias graph: `Content/EnvSandbox/PCG/Universal/PCG_ControlReaderAliases.uasset`
- Builder settings: `/Game/EnvSandbox/PCG/Musical/Hero/DA_PCGHeroBuilderSettings`
- Proof maps: `L_PCG_Hero_*` + `L_PCG_Hero_ScaleWorldProof`
- Control module (11 props/aliases): `Content/Python/pcg_hero_music_control.py`
- Scale contract (25,600 cm, chunk seam, tiers): `Content/Python/pcg_scale_world_pipeline.py`
- Offline stage runner: `Content/Python/run_pcg_scale_world_build.py`

## 5. Supersedes / related

- Extends `Docs/Production/PCG/MUSICAL_PCG_NOTES_2026-08-08.md` (piano/sequencer lane).
- Related handoff: `Docs/Handoffs/HANDOFF_PCG_HERO_AUDIO_2026-08-09.md`.
- Does not modify production maps, the JRPG lane, or the concurrent water lane.
