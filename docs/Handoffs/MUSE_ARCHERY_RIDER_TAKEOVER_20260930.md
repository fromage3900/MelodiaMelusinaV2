# Muse worker prompt: WaveHarp animation repair and Rider takeover

Use `C:/EnvironmentPortfolio/BS_GodFile` on existing local `main`. Read `AGENTS.md`, `_AGENT_WORKING_AGREEMENT.md`, and the latest archery entries in `CURRENT_STATE.md`. Current State remains the status authority; this file is an executable worker prompt, not a separate status ledger.

## Animation worker: execute this bounded repair

Repair draw, held aim and release on the actual Morning pawn. Preserve the hero mesh/skeleton, hair, skirt, stock locomotion, combat/damage/rhythm/outcome owners and existing authored materials. Do not rerun a blanket retarget/import or switch branches. Own only the necessary animation candidates and `ABP_Melusina_Current`; coordinate any native binding change with the Rider owner.

Actual runtime bindings inspected this session:

- Pawn: `/Game/MelodiaIntegration/Blueprints/BP_MelusinaJRPGCharacter`.
- Mesh: `/Game/Melodia/Characters/Melusina/Outfits/V2/SK_Melusina_V2_Body`.
- Skeleton: `/Game/Melodia/Characters/Melusina/SK_Melusina_Skeleton`.
- ABP: `/Game/Melodia/Characters/Melusina/ABP_Melusina_Current`.
- Draw: `Animations/AM_RangeAttack` -> `A_RangeAttack`.
- Release: `Animations/Polish_20260919/AM_Melusina_BowAttack_Gameplay` -> `A_Melusina_BowAttackV2_A_RangeAttack`.
- Both bound sequences report `C:/Program Files/AnimationStarterPack/Fire_Shotgun_Hip.fbx` as import provenance. Metadata may be inherited; it is not a full edit history.
- Native component freezes draw at 0.45 s and plays release at 1.6x. Connected `DefaultSlot` is full body: locomotion -> slot -> component space -> Kawaii -> CopyBone -> existing downstream processing -> output.

Existing full-action candidate:

`/Game/Melodia/Characters/Melusina/Animations/Mocap/A_Melusina_BowDraw_v2_Mocap_RootMotionMelusina_Mocap_Rig_Action`

This exists, is 2.833 s / 30 fps / 86 keys, has root motion enabled, and was imported by `Content/Python/import_rokoko_mocap_batch.py` directly onto the target skeleton from `Saved/Audit/MelusinaReexport_20260921/out_BowDraw_v2/A_Melusina_BowDraw_v2_Mocap_RootMotion.fbx`. It is a 465-bone target-rig export. **Do not feed it through `RTG_Mocap_to_Melusina_Current` again**; that retargeter belongs to the separate raw Rokoko source pipeline.

Critical new UE evidence: `get_bone_track_keys` reports root scale `[100,100,100]` at frames 0–2; canonical skeleton root scale is `[1,1,1]`. At t=1.4, FK-composed `hand_l` scale is approximately 100 and location is `[3350.846,-2942.019,11899.332]` cm. Existing bound release clip at t=.45 reports hand scale1 and location `[.822,35.556,111.930]` cm. The source export report's ~4cm net root travel does not establish a correctly scaled imported animation. Inspect the actual candidate's root and pelvis tracks; test a duplicated, corrected, in-place candidate before binding it. Do not compensate by scaling the hero actor or bow to .01.

The candidate's deformation tracks (`arm_stretch_l`, `hand_l`, `forearm_stretch_r`) vary across all86 keys; several `c_*` control tracks are constant. Follow the mesh's actual deformation hierarchy. Do not choose the many finger/end-bone action fragments as the full bow animation.

1. Correct the demonstrated candidate import/unit defect in a copy; preview on V2 with WaveHarp attached. Sample grip, string hand, shoulder/wrist continuity, root/pelvis and feet. Validate real evaluation, not just skeleton names.
2. Select usable draw, fully drawn hold and release beats. Bake/remove actual root travel for moving aim. Disabling root-motion extraction alone does not remove baked translation. Author only a missing beat if the existing full actions cannot supply it.
3. Layer bow upper-body motion over existing leg locomotion in the current ABP, before downstream physics. Scope the branch filter to the verified deformation spine hierarchy. Replace the arbitrary .45-s attack freeze with the validated hold beat. Keep other montage users working.
4. Compile and prove in `/Game/Melodia/Levels/Opening/L_MelusinaMorning`: real player stationary/moving aim, draw/hold/release, 4–6 consecutive shots, cancel and FLOW/SEQUENCE recovery. Capture before/after motion and active montage/bone data. Require plausible hand/bow contact, no backward bow, no pose snap, and zero relevant runtime errors. Do not call this fixed until live PIE passes.

For graph edits, follow the required export -> fingerprint -> mutate -> compile -> assert -> fingerprint -> save loop, one asset at a time. The untouched AnimGraph fingerprint was stable across two reads and a no-op resave: `892e53f93276f2694820a7ad7cc78793220355dc` (`topology+defaults`,15nodes,10connections). Root made no graph edit. The ABP is now dirty on disk: preserve worker/owner edits; do not reset or commit it under the assumption that the dirty blob is only a no-op resave.

`capture_anim_frames` returned T-pose-looking frames for both the bow candidate and the existing release sequence. Those diagnostic renders alone cannot determine whether runtime deformation is broken; pair them with PIE bone/montage readback. Root did not create or promote a corrected clip.

## Rider owner: smallest reliable takeover

- Keep one UE5.8 editor and one Monolith listener on127.0.0.1:9316. Root last observed PID35140, Morning, no PIE; recheck before controlling the editor. Coordinate editor ownership with Muse. Use the existing RiderLink; do not install another editor bridge.
- Open `BS_GodFile.uproject` in Rider. Relevant breakpoints: WaveHarp `StartDraw`, `ReleaseDraw`, `ResolveProjectileHit`; arrow `Consume`; JRPG bridge `ResolveWorldFlowAttack` and its authoritative resolver; hybrid `ApplyResolvedSequenceDamage`.
- Current physical inputs in source: LMB press/release draws/fires; RMB hold aims; MMB toggles aim; Tab enters SEQUENCE; X cancels; Q/W/O/P are phrase lanes in SEQUENCE. Recheck live mappings if another worker changes them.
- One damage path: arrow `Consume` sets `bConsumed` before callbacks -> WaveHarp `ResolveProjectileHit` -> existing JRPG bridge `ResolveWorldFlowAttack` -> stock resolved result -> hybrid sink -> same world slime HP. Preserve this path. Python tension damage is provisional and must not be introduced.
- For native work, coordinate a closed-editor Development Editor build after Muse saves; current last successful full build is `Saved/Audit/HybridPlayable_20260930/BuildChordSFX.log`. The later HUD65% scale edit has not been built or visually accepted.
- Then test five clicks ~.5s apart, moving aim, a real slime hit, same-HP FLOW -> SEQUENCE -> FLOW and exactly-once completion. Native shot logs from the latest owner test show9 shots, but scenery hits; they do not prove this fresh chord/damage scenario.
- `python Tools/fps60_harness.py --map /Game/Melodia/Levels/Opening/L_MelusinaMorning --name morning_takeover --duration 12 --performance-only` now excludes PNG readbacks and uses the session's own CSV. It starts/owns a PIE smoke session, so run only when the editor is available. It does not drive WASD or shots or force60fps. This patch has offline validation only; live harness/performance proof is owed. Keep UE foreground; background3fps is invalid. Use a separate showcase capture after measuring performance.

## Loose ends explicitly owed

- Foreground60fps certification and acceptable Niagara travel rendering remain unproven. Last measured foreground frame was26.11ms (~38fps), not a p95 pass. Kawaii collision accumulation was fixed and tested; do not retune hero physics to hide remaining cost.
- HUD65% compact scaling remains an unbuilt/unseen source iteration. Check anchors, readability and duplicate reticles against `MorningHUDBeforeCleanup.png` and the owner's latest Figma board; do not call it approved.
- Choral sheep uses canonical mesh at identity relative transform. Measure bounds-bottom against a ground trace; correct a proven actor/follow-height defect, not the mesh offset. No placement fix was completed.
- The second visual Melusina belongs to stock party spawn. Inspect `/Game/MelodiaIntegration/Party/BP_SirMelodiousJRPGCharacter` for parent/interface compatibility and correct the second roster class. `BP_SirMelodious_Flight` is a different exploration pawn; do not substitute it blindly. No replacement was completed.
- Saved practice slime external actor `Content/__ExternalActors__/Melodia/Levels/Opening/L_MelusinaMorning/D/9C/ZV45WIWVHAGXUPNDJRT0N5.uasset` is a local uncommitted fixture. Its exact placement/reachability needs a fresh ground check; don't blanket-save or commit Morning externals. Its folder package is `Content/__ExternalObjects__/Melodia/Levels/Opening/L_MelusinaMorning/C/34/D3ZEVT0U29V1L8RSR9ORPP.uasset`.
- GOOD/PERFECT once-only rhythm scaling, fresh audio listening acceptance, restart/durable-outcome and packaged proof remain owed for this latest showcase iteration.

## Evidence to consume

All paths below are under `C:/EnvironmentPortfolio/BS_GodFile/`:

- `Saved/Audit/HybridPlayable_20260930/JevArcheryRetargetPlan.json`: real Jev1.13 review, selects existing bow source -> authored hold -> ABP blend, author only missing beats.
- `Saved/Audit/HybridPlayable_20260930/AnimationPoseDiagnostics.json`: measured root/unit and graph baseline envelope from this closeout.
- `Saved/Audit/HybridPlayable_20260930/AnimGraphBefore.json`: rollback/assertion baseline before any root graph edits.
- `Saved/Audit/HybridPlayable_20260930/BuildChordSFX.log`: UE5.8 Development Editor build succeeded34.73s.
- `Saved/Audit/MelodiaTests-20260930-200041/index.json`:43Success +7SuccessWithWarnings,0Failed,0NotRun; includes Hybrid/Rhythm/Wiring/CoreRules/Integration and Kawaii regression.
- `Saved/Audit/HybridPlayable_20260930/MorningStatsAnimAfterCollisionFix.json`: live Kawaii collision ~.449ms average, full node ~2.117ms in that measured session.
- `Saved/Audit/HybridPlayable_20260930/MorningHUDBeforeCleanup.png`: diagnostic full-HUD capture, not approved portfolio output.
- `Saved/Audit/HybridPlayable_20260930/BowPoseV2/` and `BowPoseCurrent/`: isolated preview diagnostics, not live archery proof.

Safe commits are local checkpoints, not canonical runtime approval. Root will record their exact IDs in CURRENT_STATE and the closeout receipt. Preserve pre-existing staged document renames and all other dirty work. Do not blanket-stage, reset, clean, stash, switch/rebase or push without owner instruction.
