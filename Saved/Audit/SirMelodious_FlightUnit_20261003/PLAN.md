# Sir Melodious — runtime bird flight unit: expanded plan (2026-10-03)

Owner ask: expand Sir's cockatoo animation systems, converge the pipeline, ship a runtime flight unit with polished flaps + idles; research UE bird units; start headless Houdini + Blender.

## 1. What exists (verified on disk 12:58)
- **Canonical SK:** `/Game/Melodia/Characters/SirMelodious/Rigged/SK_SirMelodious_Rigged` (+ `_Skeleton`, `_Physics1`). Ruled canonical 09-24 (wix `SK_SirMelodious_Clothed_Production.fbx` = site lane only). Source FBX `Content/EnvSandbox/SKM_SirMelodious_rig.fbx`.
- **Rig = Auto-Rig Pro export:** root/spine_01/02/neck/head, arm/forearm/hand, **feather chains** `arm_feather_01–04`, `forearm_feather_01–05`, `hand_feather_01–02` (L/R) + `c_*` controls, legs/feet/toes. **No crest, tail, beak/jaw or eyelid bones. Skeleton has 0 sockets.**
- **Clips (imported 09-28, guarded lane, key counts match Blender):** Perch_Idle 96f, Fly_Loop 72f, Sing 72f, Takeoff 60f, Land 60f, Hover_Idle 48f — all in-place, root motion off.
- **ABP_SirMelodious** (10-02): `FlightLocomotion` 4 states Fly/Perch/Takeoff/Land, driver rewired 09-28 (Speed, bPerched). Hover_Idle + Sing imported but **unbound**. **Never PIE-proven as a moving bird.**
- **Pawn:** `AMelodiousFlightCharacter` / `BP_SirMelodious_Flight` (mesh + ABP verified), Ctrl party switch (guarded by `bSirMelodiousExplorationUnlocked`), perch API with idle auto-land. Party: `BP_SirMelodiousPlayerUnit` → `BP_SirMelodiousJRPGCharacter`.
- **Blender lane:** `Saved/Audit/sir_melodious_anims_20260924/` — `author_sir_clips_fix.py`, `remap_sir_clips_v2.py`, verify scripts, `sir_stage_playback_20260927.blend`, FBX in `exports/ue/` (v2 remapped = what UE uses).
- **Tools on fromage:** Houdini 22.0.368 (hython), Blender 4.2–5.2.

## 2. Divergences to converge first (blocking polish)
1. **Two perch systems.** `BP_SirPerch` / `ASirPerchPoint` (09-27, 3 sandbox perches in MelodiaIntegrationMap) vs today's `setup_sir_melodious_perches.py` spawning `AMelodiaExplorationInteractionVolume` with `perch.sirmelodious.landing`. Pick one → owner. Recommend `ASirPerchPoint` (already wired into the pawn's perch API); the interaction volume becomes only the trigger if needed.
2. **Re-import risk.** `import_sirmelodious_rigged.py` (10-03) re-imports the SK from FBX. A mesh re-import can mint a new skeleton and orphan all 6 clips + ABP. Gate: run only by owner, with skeleton forced to `SK_SirMelodious_Rigged_Skeleton`; diff bone list before/after.
3. **Shoulder perch on Melusina** unmet (GOALS_LEDGER): needs a socket decision (Melusina `shoulder_l` socket vs placed perch).
4. **Scale gate vacuous** (all clips report identical `mag_cm`): replace with a wing-tip travel probe (hand_feather tip world-space range per clip).

## 3. UE bird-unit research → design
- **Movement:** CharacterMovement `MOVE_Flying` (already); drive ABP with `Speed`, `VerticalSpeed`, `BankAngle` (yaw-rate × speed), `bPerched`, `FlightPhase`.
- **Locomotion core:** Blend Space 2D *Speed × VerticalSpeed*: Hover (0) → Flap cruise → Glide (high speed, level/down) → Flap_Climb (up). Glide is what makes birds read as birds; flapping constantly reads as a toy.
- **Phase lock:** sync group `Wingbeat` + sync markers `WingUp`/`WingDown` on every flap clip so Hover↔Fly↔Climb blends never pop mid-stroke.
- **Additive layers:** bank lean (Bank_L/Bank_R additive, from BankAngle), head stabilization/look-at (Control Rig aim on `neck_x`/`head_x`, birds keep the head still while the body moves), breathing on perch.
- **Feather polish:** Control Rig post-process: `WingFold` curve folds the feather chains in glide/perch; spring-lag (Spring Interp / AnimDynamics) on `hand_feather_*` + `forearm_feather_*` for overlap on the downstroke.
- **Takeoff/land:** Motion Warping on Land to align to the `ASirPerchPoint` transform; distance-match Land to perch distance (Animation Locomotion Library).
- **Rhythm hook:** flap play rate = BPM / clip-beats (Fly_Loop 72f @24 = 3 s ≈ 2 beats @ 40 BPM equivalent; tune per track); notify `WingDown` → feather-puff Niagara + soft whoosh; Sing state bound to S4 duet trigger.
- **Idle set:** Perch_Idle base + random-sequence player of short perch variants (preen, head tilt, wing stretch, foot shuffle), each 2–4 s, blend 0.25 s.
- **Cockatoo signature:** crest raise/lower = most recognisable cockatoo read; **no crest bones** → either owner adds a 3-bone crest chain in Blender (SK re-import, owner-manual) or a morph target. Decision owed.

## 4. Phases
| # | Phase | Lane | Output | Gate |
|---|---|---|---|---|
| P0 | Converge: perch system pick, freeze SK identity, PIE-prove 4 states | owner + New Bot | decision + 20 s PIE clip | Sir visibly takes off/flies/lands/perches |
| P1 | **Headless Blender** clip set v3 off `author_sir_clips_fix.py`: Glide, Flap_Climb, Flap_Fast, Hover_Turn, Bank_L/R (additive poses), Perch_Preen, Perch_HeadTilt, Perch_WingStretch, Hop | Study (headless) | FBX in `Saved/Audit/SirMelodious_FlightUnit_20261003/exports/ue/` + contract JSON | loop seam = 0 (first==last pose), key counts, wing-tip travel probe |
| P2 | **Headless Houdini** (hython, KineFX): import Sir FBX skeleton, procedural flap generator (phase-offset sine per feather chain, secondary-motion lag), export FBX | Study (headless) | A/B Fly_Loop vs Blender version | owner picks feel from turntable renders |
| P3 | UE unit: blendspace, sync markers, additive bank, Control Rig fold/spring, notifies, Motion Warping land, random perch idles, bind Hover/Sing | New Bot (live) | ABP v2 | compile 0/0; owner Ctrl+S |
| P4 | Proof: PIE capture flight path + perch, FPS check | 💧 | stills + clip | owner review |

Rules: no hero WIP .blend opened; headless work on copies under Saved/Audit; FBX into UE only via guarded animation-only importer onto existing skeleton; owner Ctrl+S only.

## 5. Owner decisions
1. Perch system: `ASirPerchPoint` (recommended) or interaction volume.
2. Crest: add bones (SK re-import) / morph / skip for P0.
3. Melusina shoulder perch: socket vs placed perch.
4. Houdini procedural flap vs Blender hand-keyed as the base Fly_Loop (decide after P2 A/B).

## 6. Headless start: results (13:05)
**Blender 4.5 headless probe** (`probe_clips_headless.py` → `blender_clip_probe.json`), over the v2 FBX that UE uses:
- Sir rest pose: wingspan 42.2 cm, height 28.5 cm, 126 bones.
- **Fly_Loop wing-tip vertical travel is only 3.4 to 3.8 cm on a 42 cm span, with 1 downstroke in 3 s (0.33 Hz).** Hover_Idle: 2.7 to 2.9 cm, 1 stroke in 2 s. That reads as a shiver, not a flap. **This is the main reason the flight looks unpolished.** Target for a stylized cockatoo: about 25 to 35 cm of tip travel, 3 to 5 Hz in hover, and 2 to 3 Hz in cruise with glide gaps. Real cockatoos flap at about 4 to 6 Hz.
- Loops are clean: Fly, Hover, Perch and Sing seams are 0 mm. Takeoff and Land are one-shots, so their seams of 70 and 87 mm are expected.
- Land is asymmetric: left tip travel is 4.0 cm and right is 0.6 cm. Re-key it.
- Sing barely moves the wings, which is fine. It needs head and chest work instead.
- → P1 first job: re-author Fly_Loop and Hover_Idle with real amplitude, driving the `arm`/`forearm`/`hand` chain plus feather lag. Shorten the cycles (Fly about 10 to 12 frames per stroke, Hover about 6 to 8) so the sync markers land on each stroke.

**Houdini 22 headless (hython): BLOCKED, "No licenses could be found".** The hython/KineFX script is staged at `hython_kinefx_probe.py`. It needs a license that hython can reach headless. Interactive Houdini may use a different license (Apprentice and Indie have restrictions). Owner must check License Administrator (hkey) or run the hip from the Houdini GUI. Until then, P2 runs as a Blender procedural pass (driven sine per feather chain), not in Houdini.

## 7. Crest decision (owner, 13:00): YES, a treble-clef crest
- New staging file `SirMelodious_CrestStage_20261003.blend` was built headless (`stage_crest_blend.py`) from the canonical `Content/EnvSandbox/SKM_SirMelodious_rig.fbx`. No older blend was touched.
- It adds a `CREST_TrebleClef_Guide` poly curve (stem, top hook and lower curl) at the head tip (z of about 26 cm), plus a 4-bone `crest_01-04` chain parented to `head.x`. That makes 130 bones, up from 126.
- The guide is a scale stub at about 2.3 cm tall. Owner sculpts the real clef mesh (target about 5-7 cm on a 28.5 cm bird), weights it to `crest_01-04`, and adds shape key `Crest_Raise` (fan open). Bones give curl and sway (spring), and the morph gives raise and fan. Both ride the same mesh FBX re-import.
- **The re-import is owner-manual** and must keep `SK_SirMelodious_Rigged_Skeleton` (only new bones get appended). Then re-run the 6-clip key check.
- The FBX source also still carries junk meshes (`Retopo_*`, `BézierCurve.002`, `spline_ik_curve.x.001`). Clean them in the stage file before export.

## 8. v3 core flight clips: authored and remapped headless (13:30). The crest stays a placeholder.
- **Root cause of the weak flaps (v2):** `best_axis` kept only positive tip dz, so the wing picked Z (13 mm per 25°) over the true flap axis X (-46 mm). v3 measures each side by |dz| and keeps the sign.
- **Scripts:** `author_sir_clips_v3.py` (Blender 5.2) → `exports/A_Sir_*_v3.fbx` → `remap_v3.py` (same Stage C contract as v2, dots to underscores, no double scale) → `exports/ue/` plus `.contract.json` (`ue_import` true) → `probe_v3.py` → `blender_clip_probe_v3.json`.

| Clip | Frames | Wing-tip travel | Strokes | Loop seam |
|---|---|---|---|---|
| Fly_Loop_v3 | 72 (3 s) | 17.8 cm L = R (v2 was 3.4/3.8) | 6 (2 Hz) | 0 mm |
| Hover_Idle_v3 | 48 (2 s) | 20.9 cm L = R (v2 was 2.7/2.9) | 6 (3 Hz) | 0 mm |
| Glide_v3 (new) | 48 | 1.6 cm sway, wings held | 1 | 0 mm |
| Takeoff_v3 | 40 | 21.0 cm | 4 | one-shot |
| Land_v3 | 40 | 20.7 cm L = R (v2 was 4.0/0.6) | 3 + fold | one-shot |

- All five clips have 126 bones and 0 dotted names. Perch_Idle and Sing stay v2, because their wings barely move.
- **UE intake:** `Content/Python/import_sir_anim_guarded_v3.py` uses the same guards as v2 (animation only, skeleton forced, no unit conversion) and creates NEW `A_Sir_*_v3` assets. It doesn't overwrite v2. Run it in the editor with `py import_sir_anim_guarded_v3.py`, only when the PC is idle (watch the paging file).
- **Then the animation blueprint:** `ABP_SirMelodious` Fly → `Fly_Loop_v3`, Takeoff/Land → v3. Add Hover (Speed < 50 and airborne) and Glide (Speed high and VerticalSpeed ≤ 0) as a Speed blend. Sync markers go at each downstroke (Fly every 12 frames, Hover every 8). Owner saves with Ctrl+S.
- **Known limits:** `c_pos` bob delivers only about 10% (it's an ARP control), so body bob is subtle. Feather chains have no lag key yet; that becomes a spring in the animation blueprint.

## 9. v3.2 body pass (13:35)
- **Owner report:** only the wings move. That came from the clips, not the UE retargeter. The v3 clips are authored directly on Sir's skeleton, and RTG is not in the path.
- **Cause:** the source armature's object scale is 0.1068, so `c_pos` translation landed at about 10% of intent (0.6 mm bob), and there was no body lean.
- **Fix:** body bob and lean now go on `c_traj`, the child of the root `c_pos`, so UE root lock and root-motion handling can't strip them. Lean is whole-body, because `head.x` is free-parented to `c_traj` and a spine-only pitch would stretch the neck. Re-authored, remapped and probed (`body_probe_v3_2.json`):
  - **Fly:** head and chest bob 2.5–2.6 cm per stroke, 3° lean lagging the wings by about 15% of a stroke.
  - **Hover:** 2.8 cm, plus an 8° upright offset.
  - **Glide:** 1.7–1.8 cm soar sway.
  - **Takeoff:** 7.4 cm crouch and spring.
  - **Root and neck:** the root `c_pos` stays still, the neck length doesn't vary, and the loops have 0 mm seams.
- **BOM removed** from `import_sir_anim_guarded_v3.py` and the `.contract.json` files. That was the hidden character New Bot hit.
- **UE check if the body still looks flat after re-import:** Skeleton → `c_traj` / `c_pos` translation retargeting must be "Animation". The sequences need Force Root Lock off.

## 10. v3.3 receipt (2026-10-03 ~1:55 PM ET)
Fixes for 💧's v3.2 proof notes. Takeoff strokes now start at the bottom of a stroke (+0.45 phase), so the frame-17 pop is gone: max wingtip step 19.24 cm -> 10.05 cm per frame (median 3.53). Takeoff and Land now lean (head forward travel 7.98 / 7.36 cm) and bob (8.97 / 6.26 cm); Land starts in the Hover pose and lean instead of sitting still. Hover downstroke 50 -> 40 deg to reduce lower-body clipping (max step 9.65 cm). Fly, Glide unchanged. Contracts re-flipped to ue_import=true. Probe: pop_probe_v3_3.json.
Still open: wrist spike lump (mesh/junk, strip Retopo_*, BezierCurve.002, spline_ik_curve.x.001 at crest re-import); Hover clip needs a visual re-check; blend-space play-mode check (New Bot).