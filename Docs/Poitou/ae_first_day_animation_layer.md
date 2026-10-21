# Poitou Marais: Animation layer for Melusina's first day

Source: read-only filename scan of `C:\EnvironmentPortfolio\BS_GodFile\Content` on fromage (2026-10-20), plus string scans of
`BP_MelusinaJRPGCharacter` and `ABP_Melusina_Current`. Clip lengths, root-motion flags and existing notifies were **not**
read from the assets (that needs the editor). Infer root motion only from the names (`Mocap_RootX`, `RootMotion`, `InPlace`).

## 0. Runtime wiring found

- Character BP: `/Game/MelodiaIntegration/Blueprints/BP_MelusinaJRPGCharacter`
  - AnimBP: `/Game/Melodia/Characters/Melusina/ABP_Melusina_Current` (hair: `/Game/Melodia/Characters/Melusina/Hair/ABP_Melusina_WaterHair`)
- `ABP_Melusina_Current` references:
  - `/Game/Melodia/Characters/Melusina/Animations/BS_Melusina_Locomotion`, `/Game/Melodia/Characters/Melusina/Animations/BS_Melusina_Locomotion_Hybrid`
  - `/Game/Melodia/Characters/Melusina/Animations/Locomotion/A_Shin_Idle_stand_MocapConv` (idle)
  - `/Game/Melodia/Characters/Melusina/Animations/Locomotion/A_Melusina_JumpStart_Mocap_RootX`, `..._JumpLoop_Mocap_RootX`, `..._Land_Mocap_RootX`
  - `/Game/Melodia/Characters/Melusina/Animations/AnimationDoctor_20261007/RuntimeCloseout_20261009/A_Melusina_Glide_InPlace_Candidate`
  - Montage slots: **DefaultSlot**, **UpperBody**
- Battle AnimBP (not used here): `/Game/MelodiaIntegration/Blueprints/Animations/ABP_Melusina_Battle`
- Other: `/Game/Experiments/MelodiaJRPG/ABP_Melusina_JRPGPresentation`, `/Game/Characters/Melusina/ABP_Melusina` (older)

## 1. Inventory (Melusina-relevant; prefix `/Game/Melodia/Characters/Melusina` unless a full path is given)

### Locomotion
- `/Game/Melodia/Characters/Melusina/Animations/BS_Melusina_Locomotion`, `/Game/Melodia/Characters/Melusina/Animations/BS_Melusina_Locomotion_Hybrid`, `/Game/Melodia/Characters/Melusina/V2Test/Animations/BS_Melusina_Locomotion`
- `/Game/Melodia/Characters/Melusina/Animations/Locomotion/A_Melusina_Walk`, `A_Melusina_Walk_Mocap_RootX` *(root motion)*, `A_Melusina_Walk_Mocap_RootX_SeamFix` *(root motion, loop-fixed)*
- `/Game/Melodia/Characters/Melusina/Animations/Locomotion/A_Melusina_Run`, `A_Melusina_RunLoop_Trim`, `A_Melusina_Run_Mocap_RootX`, `A_Melusina_Run_Mocap_RootX_SeamFix`
- `/Game/Melodia/Characters/Melusina/Animations/Locomotion/A_Melusina_Sprint`, `A_Melusina_Sprint_Mocap_RootX`
- `/Game/Melodia/Characters/Melusina/Animations/Mocap/A_Melusina_WalkElegant_Mocap_RootMotionMelusina_Mocap_Rig_Action` *(root motion; the 14 sibling `..._RootMotion<Bone>_clip_Base_Layer` files look like split-import debris)*
- `/Game/Melodia/Characters/Melusina/Animations/Mocap/A_Mocap_RunCycle`, `A_Mocap_RunCycle_Sprint`, `A_Mocap_RunCycle_Sprint_Loop`
- `/Game/Melodia/Characters/Melusina/Animations/A_ThirdPersonWalk`, `A_ThirdPersonRun`, `A_ThirdPersonDash` (template retargets; also under `/Game/Melodia/Characters/Melusina/V2Test/Animations/`)
- Glide: `/Game/Melodia/Characters/Melusina/Animations/Locomotion/A_Melusina_GlidePose`, `/Game/Melodia/Characters/Melusina/Animations/AnimationDoctor_20261007/RuntimeCloseout_20261009/A_Melusina_Glide_InPlace_Candidate`, `/Game/Melodia/Characters/Melusina/Animations/Mocap/A_Melusina_GlideForward_Mocap_RootMotionMelusina_Mocap_Rig_Action`
- Staging copies: `/Game/Staging/AnimationDoctor/LoopCandidates_20261012/A_Melusina_Walk_Mocap_RootX_SeamFix`, `..._Run_Mocap_RootX_SeamFix`

### Idles
- `/Game/Melodia/Characters/Melusina/Animations/Locomotion/A_Shin_Idle_stand_MocapConv` (**live idle**), `A_Melusina_Idle`, `A_Melusina_Idle_Mocap_RootX`
- `/Game/Melodia/Characters/Melusina/Animations/Authored/A_Melusina_Idle_v22`, `/Game/Melodia/Characters/Melusina/Animations/Authored/A_MUAL_Melusina_Idle_Loop`
- `/Game/Melodia/Characters/Melusina/Animations/Cascadeur/A_CAS_Melusina_Idle_Loop`, `/Game/Melodia/Characters/Melusina/Animations/Cascadeur/A_BL_Melusina_Idle_Loop`
- `/Game/Melodia/Characters/Melusina/Animations/QuaterniusRetargeted_V2Fixed/A_Q_Melusina_Idle_Loop`
- `/Game/Melodia/Characters/Melusina/Animations/ShinbiIdles_20261005/A_Shin_Idle`, `A_Shin_Idle_pose`, `A_Shin_Idle_stand` (also under `ShinbiDoctor_20261007/`)
- `/Game/Melodia/Characters/Melusina/Animations/AnimationDoctor_20261007/ACFUMage_20261008/A_Melusina_ACFUMage_Idle`
- `/Game/Cinematics/Shorewake/HERO01/IdleCanonicalDirect_20260909_V10/Retargeted_V10Exact/A_HERO01_A_Melusina_CuteIdle_UECanonicalDirect_V10_RetargetedExactV10`
- Montages: `/Game/Melodia/Characters/Melusina/Animations/Montages/AM_MUAL_Source_Idle`, `/Game/Melodia/Characters/Melusina/Animations/AM_Idle`

### Emotes / gestures
- `/Game/Melodia/Characters/Melusina/Animations/Montages/AM_Melusina_Idle_Talk`, `AM_Melusina_Idle_Dance`
- `/Game/Melodia/Characters/Melusina/Animations/QuaterniusRetargeted/A_Q_Melusina_Dance_Loop`
- `/Game/Melodia/Characters/Melusina/Animations/Mocap/A_Mocap_LittleDance`, `A_Mocap_LittleDance_001`, `A_Mocap_LittleDance_003`, `A_Mocap_Twirl_001`, `A_Mocap_FairyWand`
- `/Game/Melodia/Characters/Melusina/Animations/AM_Mocap_Victory`, `/Game/Melodia/Characters/Melusina/Animations/AM_Intro`
- `/Game/Staging/HoudiniForge/MelusinaGNToys/A_MEL_Halo_Orrery_Unfold` (prop anim)

### Traversal (jump / land / climb)
- `/Game/Melodia/Characters/Melusina/Animations/Locomotion/A_Melusina_JumpStart_Mocap_RootX`, `A_Melusina_JumpLoop_Mocap_RootX`, `A_Melusina_Land_Mocap_RootX` (live in ABP)
- `/Game/Melodia/Characters/Melusina/Animations/Mocap/A_Mocap_Jump`, `_001`, `_002`, `A_Mocap_Jump_Loop`, `A_Mocap_GracefulLanding`, `A_Mocap_LiftOff`
- `/Game/Melodia/Characters/Melusina/Animations/A_Land`, `A_ThirdPersonJump_End`, `/Game/Melodia/Characters/Melusina/Animations/AM_Mocap_JumpEnd`, `/Game/Melodia/Characters/Melusina/Animations/AM_Q_Melusina_Jump`
- `/Game/Melodia/Characters/Melusina/Animations/Montages/AM_Melusina_Roll`, `/Game/Melodia/Characters/Melusina/Animations/QuaterniusRetargeted/A_Q_Melusina_Roll`, `/Game/Melodia/Characters/Melusina/Animations/Mocap/A_Mocap_Dodge`, `A_Mocap_Dodge_001`
- `/Game/Melodia/Characters/Melusina/Animations/AM_Q_Melusina_Swim`
- **Climb: none found.**

### Interactions
- `/Game/Melodia/Characters/Melusina/Animations/Montages/AM_Melusina_Interact`, `AM_Melusina_PickUp`
- `/Game/Melodia/Characters/Melusina/Animations/AM_Q_Melusina_Interact`, `/Game/Melodia/Characters/Melusina/Animations/QuaterniusRetargeted/A_Q_Melusina_Interact`
- `/Game/Melodia/Characters/Melusina/Animations/AM_Q_Melusina_Sitting`
- `/Game/Melodia/Characters/Melusina/Animations/AM_ItemUse`

### Cinematic / mocap
- `/Game/Melodia/Characters/Melusina/Animations/Mocap/*` (`A_Mocap_*`, BowDraw v1/v2, BowKneelAim, GlideForward, WalkElegant `..._Mocap_RootMotion*`)
- `/Game/Melodia/Characters/Melusina/Animations/AM_Mocap_BasicAttack`, `AM_Mocap_Skill`, `AM_Mocap_JumpEnd`, `AM_Mocap_Victory`
- Shorewake HERO01 CuteIdle (above)
- Combat (out of scope): `AM_Attack`, `AM_*Attack`, `AM_Q_Spell*`, `Polish_20260919/AM_Melusina_BowAttack_*`, `SparrowArchery_*`, `CastCandidates_20261001/*`, `ContactCandidates_20261003/*`

---

## 2. Animation layer: Melusina's first day

Tempo grid: **128 BPM, 4/4. 1 beat = 0.469 s, 1 bar = 1.875 s.** Footbridge gait: 4 steps per bar, 0.6 m stride,
so 2.4 m per bar = **1.28 m/s**. Piano keys sit on a 24.5 cm pitch (24 cm key + 0.5 cm gap), so one stride covers about 2.45 keys.
Notes are **not** driven by animation. `APCGPianoKey` StepTrigger overlap fires `OnKeyPressed`, then
`APCGPianoKeyboard::OnKeyboardPressed` plays the pitch-shifted PressSound
(`Source/BS_GodFile/Piano/PCGPianoKeyboard.h:124-284`). Foot notifies are only for footstep VFX and beat-sync checks.

Route: 7 stops, dawn to dusk (time of day via UDS / `TimeOfDay` on the material, Sequencer-keyed per stop).

| # | Stop / beat | Clip(s) | Reuse (exact path) or NEW spec | System hook |
|---|---|---|---|---|
| 1 | **Wake, dawn idle** (cabin jetty) | Wake + stretch, then idle loop | **NEW `A_MEL_Wake_Stretch`**: 2 bars, one-shot, no root motion, notifies `Yawn`, `ArmsUp`, `SettleToIdle`. Start pose: reuse `/Game/Melodia/Characters/Melusina/Animations/AM_Q_Melusina_Sitting`. Idle: reuse `/Game/Melodia/Characters/Melusina/Animations/Locomotion/A_Shin_Idle_stand_MocapConv` (live) or `/Game/Melodia/Characters/Melusina/Animations/Authored/A_Melusina_Idle_v22` | Level Sequencer intro shot. Montage on **DefaultSlot**, then ABP idle |
| 2 | **Walk on piano footbridges** (stops 2, 4, 6) | Beat-locked walk | **NEW `A_MEL_Walk_PianoStep_128`**: exactly 1 bar loop (1.875 s), 4 footfalls on beats 1-4, root motion **no** (in place, capsule at 1.28 m/s) or root-motion variant at 2.4 m/bar; notifies `FootDown_L`, `FootDown_R`, `Beat` (x4), `Bar` (beat 1). Interim: reuse `/Game/Melodia/Characters/Melusina/Animations/Locomotion/A_Melusina_Walk_Mocap_RootX_SeamFix` via `/Game/Melodia/Characters/Melusina/Animations/BS_Melusina_Locomotion` with play rate tuned to 128 BPM; alt style `/Game/Melodia/Characters/Melusina/Animations/Mocap/A_Melusina_WalkElegant_Mocap_RootMotionMelusina_Mocap_Rig_Action` | PCG key event (`OnKeyboardPressed`) for notes. `FootDown_*` notify drives splash/glint VFX. Optional: a Quartz clock phase-corrects play rate on `Bar` |
| 3 | **Board barque** at jetty | Step-down onto a moving deck | **NEW `AM_MEL_Barque_Board`**: 1 bar, one-shot, root motion **yes** (about 0.8 m fwd, -0.3 m down), notifies `PlantFoot`, `AttachToBarque`, `BalanceSettle`. Fallback: reuse `/Game/Melodia/Characters/Melusina/Animations/Locomotion/A_Melusina_JumpStart_Mocap_RootX` + `/Game/Melodia/Characters/Melusina/Animations/Mocap/A_Mocap_GracefulLanding` | Montage (DefaultSlot), triggered by jetty interact volume. `AttachToBarque` notify attaches the character to the barque actor (bob comes from the barque's own movement) |
| 4 | **Disembark** at jetty | Step-up off the deck | **NEW `AM_MEL_Barque_Disembark`**: 1 bar, one-shot, root motion **yes**, notifies `DetachFromBarque`, `PlantFoot`. Fallback: reuse `/Game/Melodia/Characters/Melusina/Animations/Locomotion/A_Melusina_Land_Mocap_RootX` / `/Game/Melodia/Characters/Melusina/Animations/AM_Mocap_JumpEnd` | Montage, jetty volume. `DetachFromBarque` restores walking movement mode |
| 5 | **Punting with the pigouille** (canal legs between stops) | Punt cycle + deck idle | **NEW `A_MEL_Barque_PuntCycle`**: 1 bar loop, no root motion, notifies `PolePlant` (**beat 1**), `PolePush` (beats 2-3), `PoleRecover` (beat 4). **NEW `A_MEL_Barque_DeckIdle`**: 2 bar loop, wide balance stance, no root motion. **Prop:** no pigouille mesh found (NEW prop + hand socket `hand_r_pole`) | Barque BP advances along the canal spline on `PolePush`. `PolePlant` spawns water ripple (reuse `/Game/Melodia/VFX/NS_Melusina_Ripple` / `NS_Melusina_Splash`, referenced by the character BP). Loop phase locked so beat 1 lands on the bar |
| 6 | **Poitou greetings with villagers** (village stops 3, 5) | Wave, curtsy/bow, chat, hand-over | Reuse `/Game/Melodia/Characters/Melusina/Animations/Montages/AM_Melusina_Idle_Talk` (chat), `/Game/Melodia/Characters/Melusina/Animations/Montages/AM_Melusina_Interact` / `/Game/Melodia/Characters/Melusina/Animations/AM_Q_Melusina_Interact` (hand-over), `/Game/Melodia/Characters/Melusina/Animations/Montages/AM_Melusina_PickUp` (receive gift), `/Game/Melodia/Characters/Melusina/Animations/Mocap/A_Mocap_LittleDance` (festive). **NEW `AM_MEL_Greet_Wave`**: 1 bar, one-shot, **UpperBody** slot, no root motion, notify `WavePeak`. **NEW `AM_MEL_Greet_Curtsy`**: 2 bars, one-shot, DefaultSlot, no root motion, notifies `BowDown`, `BowUp` | Dialogue / NPC interact triggers montage. UpperBody slot lets Wave play while walking |
| 7 | **Abbey ruin approach, awe beat** (stop 6, toward 7) | Slow walk, stop, look up | Slow walk: reuse `/Game/Melodia/Characters/Melusina/Animations/BS_Melusina_Locomotion` at low speed. **NEW `AM_MEL_Awe_LookUp`**: 4 bars, one-shot, no root motion, notifies `GazeUp`, `Breath`, `HandToChest`, `Release`. Optional flourish: reuse `/Game/Melodia/Characters/Melusina/Animations/Mocap/A_Mocap_Twirl_001` | **Level Sequencer** shot (camera crane + montage track). Head look-at on the abbey in ABP if available |
| 8 | **Dusk wind-down** (stop 7) | Sit, sway, close | Reuse `/Game/Melodia/Characters/Melusina/Animations/AM_Q_Melusina_Sitting` (sit), `/Game/Melodia/Characters/Melusina/Animations/Montages/AM_Melusina_Idle_Dance` / `/Game/Melodia/Characters/Melusina/Animations/QuaterniusRetargeted/A_Q_Melusina_Dance_Loop` (small celebratory sway), idle `/Game/Melodia/Characters/Melusina/Animations/Authored/A_MUAL_Melusina_Idle_Loop`. Yawn: reuse NEW `A_MEL_Wake_Stretch` played reversed/mirrored | Sequencer outro. Time of day to dusk |

### Counts
- **Reused existing clips cited in the beats: 19.** A_Shin_Idle_stand_MocapConv, A_Melusina_Idle_v22, A_MUAL_Melusina_Idle_Loop,
  AM_Q_Melusina_Sitting, BS_Melusina_Locomotion, A_Melusina_Walk_Mocap_RootX_SeamFix, A_Melusina_WalkElegant_..._Rig_Action,
  A_Melusina_JumpStart_Mocap_RootX, A_Melusina_Land_Mocap_RootX, A_Mocap_GracefulLanding, AM_Mocap_JumpEnd,
  AM_Melusina_Idle_Talk, AM_Melusina_Interact, AM_Q_Melusina_Interact, AM_Melusina_PickUp, A_Mocap_LittleDance,
  A_Mocap_Twirl_001, AM_Melusina_Idle_Dance, A_Q_Melusina_Dance_Loop. NS_Melusina_Ripple/Splash are counted as VFX, not clips.
- **New clips: 9** (plus 1 prop: the pigouille pole).

### Prioritized new-clip list and build order
1. **A_MEL_Walk_PianoStep_128.** The core mechanic: walking plays the keys. 1-bar in-place loop with FootDown/Beat notifies. Prototype first by timing the existing `A_Melusina_Walk_Mocap_RootX_SeamFix`.
2. **A_MEL_Barque_PuntCycle + pigouille prop/socket.** The second traversal mode. PolePlant on beat 1.
3. **A_MEL_Barque_DeckIdle.** Needed whenever the barque drifts or waits.
4. **AM_MEL_Barque_Board** and 5. **AM_MEL_Barque_Disembark.** Gate every canal leg. Jump/Land fallbacks keep the route playable until they exist.
6. **AM_MEL_Greet_Wave** (UpperBody). Cheap, high charm, used at every village stop.
7. **AM_MEL_Awe_LookUp.** The set-piece for the abbey Sequencer shot.
8. **A_MEL_Wake_Stretch.** Bookends the day (dawn, and reversed at dusk).
9. **AM_MEL_Greet_Curtsy.** Polish. AM_Melusina_Idle_Talk covers it in the meantime.

Build order: (a) beat clock + timed interim walk on one footbridge, checking keys at 24.5 cm pitch versus the 0.6 m stride. (b) Barque actor + deck attach, using fallbacks.
(c) Punt cycle + prop. (d) Board/disembark montages. (e) Greetings. (f) Sequencer shots: wake, awe, dusk.

### Unverified
- Clip lengths, existing notifies, root-motion enable flags and loop seams of every reused asset (names only).
- Whether `ABP_Melusina_Current` has a look-at / aim-offset node for the awe beat.
- Whether the many `/Game/Melodia/Characters/Melusina/Animations/Mocap/..._RootMotion<Bone>_clip_Base_Layer` assets are usable or import debris.
- No climb, punt, wave, curtsy, wake or pole assets exist under Content by filename.
