# HANDOFF — Rokoko → Melusina root-motion pipeline (for Claude / Claireon, 2026-09-21)

> From: Kimi lane (`reexport_root_motion`, Jev ruling jev-1.13.0).
> This lane never touches UE. Owner ruling 2026-09-21 (Claireon): Kimi owns the
> Rokoko→Melusina root-motion pipeline end-to-end and signals "ROOTED + bug closed";
> Claireon owns UE import + BlendSpace re-axis. **Synthetic outputs NEVER go to UE.**

## Status: PIPELINE GREEN ON SYNTHETIC — **ROOTED + bug closed** ✅

Full 4-stage run on the synthetic take (`A_Rokoko_SynthRun_TEST.fbx`, 3.0 m/s truth)
completed 2026-09-21 22:2x. Final artifact:
`Saved/Audit/rokoko_pipeline_test/out2/A_Melusina_SynthRun_Mocap_RootMotion.fbx`
(465 bones, 34 fr @30 fps = 1.13 s, ROOTED, 5.47 m travel on the `root` track).

Final verify (export report `out2/SynthRun_export_report.json`) — all three agree:
`root_net_m = hip_net_over_clip_m = expected_travel_m = [-4.567, 3.010, 0.0]`

Meaning: `root` carries the capsule trajectory; hip world pose keeps the authored
travel, so relative to `root` the character is in-place — exactly what UE root-motion
extraction expects. Z bob stays on the pelvis chain.

## What exists (all proven)

| Piece | Path | State |
|---|---|---|
| Intake gate (ROOTED/IN_PLACE/NO_HIP + cadence) | `Tools/mocap/rokoko_intake_gate.py` | ✅ pos + neg controls |
| Retargeter (Mixamo/Newton → ARP deform rig) | `Saved/Audit/rokoko_pipeline_test/retarget_to_melusina.py` | ✅ 20/20 pairs, speed 2.969 vs 3.0 truth |
| Loop cut → 30 fps → root-bone injection → export | `Saved/Audit/rokoko_pipeline_test/export_root_motion.py` (v2, supersedes export_locomotion.py) | ✅ verified numbers above |
| One-command runner (gate→retarget→export→final gate) | `Saved/Audit/rokoko_pipeline_test/run_pipeline.ps1` | ✅ ` -Fbx <path> -Clip <Name> [-StepFrames 135] [-SrcFps 120]` |
| Owner sticky note (record steps) | `Imports/Mocap/Rokoko/Inbox/EXPORT_STEPS.txt` | ✅ |

## Contracts and rulings baked into the export

- **Skeleton target: `Imports/Animations/Cascadeur/Target/SK_Melusina_Cascadeur_Target.fbx`
  (464 bones)** — NOT the 759-bone `Tools/Cascadeur/Melusina/SK_Melusina_Skeleton_Cascadeur.fbx`
  (that one has no `root`; retargeting against it caused the earlier "~98 units" anomaly).
  Live `SK_Melusina_Skeleton` (465) has `root` at idx 0, `c_traj`@61 → `root_x`@68 under it.
- **Travel binds to `root`** (Claireon ruling): export injects a `root` edit bone at origin
  (deform), re-parents `c_traj` under it (matrix preserved), keys `root` XY = hip
  trajectory, subtracts the same XY from `c_traj` locals.
- **c_traj local subtraction must go through the parent-chain rotation map** — the
  control rig flips sign/axes (`A = parent.matrix @ parent.bone.matrix_local⁻¹ @
  bone.matrix_local`; subtract `A⁻¹ · Δworld`, NOT raw Δworld). Raw subtraction adds
  travel instead of removing it (observed 3× travel). This was the bake-space bug.
- Export: armature-only, ×100 cm, `-Z/Y`, no leaf bones, 30 fps, window trimmed to the
  loop cut (deepest left-toe plant + StepFrames).
- Blender 5.2 traps already handled: slotted actions (layers→strips→channelbags walk,
  `all_fcurves()`), no `ActionKeyframeStrip.frame_range`, `pose_bones[x].select`,
  Copy Location `use_x/use_y/use_z`.
- Fingers unmapped (rest pose) — fine for locomotion, revisit for hand-authored beats.

## REAL-TAKE RUN — 2026-09-21 23:25 (first ever live pass) ✅

Five text-to-motion takes from Rokoko Studio (Mixamo skeleton, 30 fps, 91 fr, 3.0 s)
ran the full pipeline unattended via the Inbox watcher. **5/5 exported, 0 failed.**

| Clip | Gate | root_net_m (== hip_net ✓) | Output |
|---|---|---|---|
| BowDraw_v1 | IN_PLACE | [0.004, 0.013, 0] | `Saved/Audit/MelusinaReexport_20260921/out_BowDraw_v1/` |
| BowDraw_v2 | IN_PLACE | [0.006, 0.004, 0] | `.../out_BowDraw_v2/` |
| BowKneelAim | ROOTED | [-0.18, -0.017, 0] | `.../out_BowKneelAim/` |
| GlideForward | ROOTED | [0.088, -0.40, 0] | `.../out_GlideForward/` |
| WalkElegant | ROOTED | [0.001, -1.17, 0] | `.../out_WalkElegant/` |

Each `out_<Clip>/` holds `A_Melusina_<Clip>_Mocap_RootMotion.fbx` (465 bones,
30 fps, root-bone contract verified: root carries travel, hip world preserved)
+ `<Clip>_export_report.json` + final-gate re-check (stage 3).
WalkElegant speed ≈ 0.41 m/s over the 2.87 s window — plausible elegant walk.

Runner contract for future takes: gate verdict IN_PLACE is now accepted for
action clips (`-AllowInPlace`); fps/frames auto-detected from the gate JSON,
`-SrcFps`/`-StepFrames` computed (min(135, clip frames − 5)).
Watcher: automation `21371cf8` (condition, 15 min, idempotent — no refire once
a clip has an export report). **ROOTED + bug closed — Kimi lane complete.**

## Waiting on

1. **Claireon**: import the five `A_Melusina_*_Mocap_RootMotion.fbx` + re-axis the
   BlendSpace (WalkElegant ≈ 0.41 m/s is the first real axis value ever measured).

## History that matters

- The 4 locomotion RootX clips have zero root translation (root/c_traj Δ=0) → BlendSpace
  axes are guesses → feet slide. This pipeline is the fix.
- 2025-12-15 OneDrive takes are camera-suite, NOT Rokoko, translation stripped — dead.
- Real Rokoko exports HAVE a `Hips` bone (retargeter auto-detects; synthetic used the
  armature-object fallback).

## Remaining lanes (NOT this one)

Skirt re-weight, hair re-rig, finger controllers (owner decision), cornea (done).
