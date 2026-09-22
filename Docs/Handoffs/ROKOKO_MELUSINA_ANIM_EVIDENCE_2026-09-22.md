# Rokoko → Melusina Pipeline — Evidence & Blendspace Audit (2026-09-22)

Status authority for the Rokoko mocap lane. Evidence-backed; every claim has a command that re-derives it.

## 1. Pipeline state — GREEN

5 Rokoko Studio Vision takes processed 2026-09-21/22 through Blender → root-motion FBX → UE:

| Clip | UE asset (Mocap/) | Length | Measured speed |
|---|---|---|---|
| WalkElegant | `A_Melusina_WalkElegant_Mocap_RootMotionMelusina_Mocap_Rig_Action` | 2.83 s (86fr@30) | **54 cm/s** (1.53 m over clip) |
| GlideForward | `A_Melusina_GlideForward_Mocap_RootMotionMelusina_Mocap_Rig_Action` | 2.97 s (90fr@30) | **217 cm/s** (6.43 m) |
| BowKneelAim | `..._BowKneelAim_..._Action` | 2.83 s | 55 cm/s (kneel-travel) |
| BowDraw_v1 | `..._BowDraw_v1_..._Action` | 2.97 s | in-place (~2 cm/s) |
| BowDraw_v2 | `..._BowDraw_v2_..._Action` | 2.83 s | in-place (~1 cm/s) |

- Import report: `Saved/Audit/rokoko_mocap_import_report.json` — all 5 `ok`, `unit: cm`, `spine_y: -12.839` (mocap reference), skeleton `SK_Melusina_Skeleton` on all.
- Root motion travels on `root` (idx 0) per staged decision; per-clip proof: `Saved/Audit/MelusinaReexport_20260921/out_*/<Clip>_export_report.json` (`verify.root_net_m`).
- Retarget green evidence: per-clip `A_Rokoko_*_retarget_measure.json` (POSE_QA feet z 0.025–0.107, hip 0.801–0.808).
- Cosmetic debt: UE concatenates dest + FBX take name → `..._RootMotionMelusina_Mocap_Rig_Action` naming, plus 65 junk per-bone `*_clip_Base_Layer.uasset` strays in the same folder (13 per clip). Cleanup pending owner OK (deletion).

## 2. The three retargeting defects the owner caught (all fixed, re-exported, re-imported)

1. **Frozen-pose bug** (`Saved/Audit/rokoko_pipeline_test/retarget_to_melusina.py`): `_RTG` helper bones got COPY_TRANSFORMS constraints with invalid subtargers → Blender fell back to copying the target *object* transform (origin) → all helpers slammed to z=0. Fix: skip `_RID`-suffixed bones in the drive loop; they ride their animated parents. Hip helper: parent first, then head/tail.
2. **UE `root1` import abort** (`export_root_motion.py`): armature object named `root` = same as injected bone → duplicate FBX node → UE renamed track `root1` → import RuntimeError. Fix: `tgt.name = "Melusina_Mocap_Rig"` before FBX export.
3. **Window-cut truncation**: toe-plant/StepFrames logic mangled short takes (GlideForward exported 9 frames). Fix: `if f1 - f0 <= step_frames * 2: w0, w1 = f0, f1`.

## 3. ABP / blendspace audit (2026-09-22, editor queries)

Runtime pawn: `BP_MelusinaJRPGCharacter` → mesh `SK_Melusina_V2_Body`, anim class `ABP_Melusina_Current` ✓.

`ABP_Melusina_Current` AnimGraph live chain (healthy):
`StateMachine(MelusinaLocomotion) → Slot → LocalToComponent → KawaiiPhysics → CopyBone(head_x→eyes) → ComponentToLocal → Output`.
- `melodia_animation_validate_state_machine`: all_ok, entry state `Idle`, 1 state machine, no orphans.
- `melodia_animation_validate_bindings`: ONE finding — `AnimGraphNode_BlendSpacePlayer_0` (BS_Melusina_Locomotion_Hybrid) has no pose output connection. Plus 3 dangling `Slot` nodes. All dead/inert — the live chain bypasses them. These are the "halfway wiring" leftovers.

**T-pose the owner saw**: the only Melusina-class actor spawned in PIE on MelodiaIntegrationMap is `BP_MelusinaSwordsman_Presentation` (a presentation/beauty-shot actor, NOT the JRPG pawn — no `BP_MelusinaJRPGCharacter` pawn exists in PIE). Its anim class was not yet confirmed (editor exited before the read). Check first next session: `mcp__melodia__melodia_animation_get_runtime_abp` with bp_path `/Game/Experiments/MelodiaJRPG/BP_MelusinaSwordsman_Presentation`. Null anim class = the T-pose.

### BS_Melusina_Locomotion (clean, canonical)
- 1D, axis `Speed` 0–750, samples: Idle@0, Walk@180, Run@420, Sprint@630.
- All four are the OLD root-locked in-place clips (`A_*_Mocap_RootX`) — `root_motion_speed_note`: "root motion disabled (root-locked) — authored speed is unknowable". Axis values are nominal guesses, matched to controller speeds, never measured.

### BS_Melusina_Locomotion_Hybrid (degenerate)
- 1D, axis `GroundSpeed` 0–650, **7 samples with duplicates**: Idle@0, Sprint@630, Walk@180, Walk@150 (dup), Run@420, Sprint@540 (dup), Run@300 (dup).
- Referenced ONLY by the dangling BlendSpacePlayer in the ABP — nothing live consumes it.

## 4. Next-session edit plan (one editor session, in order)

1. **Confirm the T-pose actor**: `melodia_animation_get_runtime_abp` on `BP_MelusinaSwordsman_Presentation`. If null/mismatch → set `ABP_Melusina_Current` on its mesh (skeleton check first).
2. **Clean the Hybrid BS** (`animation_query`): delete duplicate samples (Walk@150, Run@300, Sprint@540) or delete the whole BS after removing the dead ABP node. Do NOT touch BS_Melusina_Locomotion axes yet — its clips are in-place so no real speed exists to re-axis to.
3. **Replace the Glide placeholder**: skill state table shows `Glide` = `A_Mocap_LittleDance_001` (placeholder). Bind `A_Melusina_GlideForward_Mocap_RootMotion...Action` via `.agents/skills/melusina-blender-handkeyed-import/scripts/bind_and_verify.py --state Glide --clip <path>`. NOTE: rate-scale will be needed — 217 cm/s clip vs controller glide speed; set `rate_scale = controller_speed/217` so feet don't slide.
4. **Optional first real measured sample**: add WalkElegant (54 cm/s measured) as a "stroll" sample below the nominal Walk@180 in BS_Melusina_Locomotion only if a slow-walk controller speed exists; otherwise keep the 5 mocap clips as action/terminal clips (bow set) rather than locomotion.
5. **Junk cleanup** (owner approval needed — deletion): 65 `*_clip_Base_Layer.uasset` in `Animations/Mocap/`; optionally rename the 5 sequences to drop the `Melusina_Mocap_Rig_Action` suffix.
6. Remove the 4 dead AnimGraph nodes (BS player + 3 slots) after 2–3 land; follow Monolith Recipe 15 (fingerprint → mutate → compile → assert → save).

## 5. Editor session log (2026-09-22)

- ~23:45–00:27: 5 clips imported (guarded importer `Content/Python/import_rokoko_mocap_batch.py`).
- 00:37: PIE screenshot attempts — camera spawn view is buried (black frames + glow); screenshots not usable as pose evidence. Numeric Blender QA is the pose evidence; owner visually confirmed the staged clips ("looks great").
- 00:38: editor fatal — `World Memory Leaks: 1` from EditorServer.cpp during `run_python` (Python-held world refs is the suspected mechanism; do NOT hold PIE UWorld refs across run_python calls — use Monolith `pie_*` C++ actions or `pie_call_function` instead).
- 00:40: editor relaunched via `Tools/launch_ue_canonical.ps1`.
- 01:10: editor exited cleanly (owner-side close). All audits above completed before exit.

Monolith RPC helper (no mcp tools in this session): `python Saved/Audit/rokoko_pipeline_test/monolith_rpc.py <namespace>_query <action> '<json>'`.
