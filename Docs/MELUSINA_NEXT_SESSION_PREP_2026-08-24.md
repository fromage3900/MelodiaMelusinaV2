# Melusina — Next Session Prep 2026-08-24

Companion to `MELUSINA_ANIMATION_CLOSEOUT_2026-08-24.md`. That doc records what was found and
fixed; this one is the runway for next session.

---

## 0. ⚠ READ FIRST — the T-pose was the Idle state

Owner ground truth (2026-08-24, late): she was still T-posing. **The `Idle` state's animation was
not proper.** Owner fixed it. `Idle` is the entry state, so a bad clip there reads as a whole-body
T-pose everywhere, regardless of how correct the rest of the graph is.

Not the retargeter, not the blendspace, not the glide blend. **Confirmed:** `Idle` now plays **`A_Melusina_Idle`** (was `A_Melusina_Idle_Mocap_RootX`).

---

## 1. Landed this session (verified, on disk)

| Change | Verification |
|---|---|
| `RTG_UE4Mannequin_To_Melusina` pelvis `pelvis` → `root_x` | `foot_l` Z 4.18 → 25.52 across cycle |
| `Glide` state: `A_Mocap_LittleDance_001` → `A_Melusina_JumpLoop_Mocap_RootX`, looping | re-queried state info |
| **`A_Melusina_RunLoop_Trim`** — new trimmed run loop | 33 keys, 1.067 s, `loop=true`, `foot_l` travels 9.2 uu Y |
| `deploy/melodia_mcp_server.py` dotted-call routing | old RPC-ERROR -32601 → new OK |
| Claireon disabled → editor builds | Succeeded, 0 errors, 35.9 s |

### The run-loop trim method (reuse this)

The raw take `A_Mocap_RunCycle` is 268 frames / 8.93 s and **starts with the actor standing still**.
Naive seam-minimisation picks that dead head — it has a perfect seam and no motion. The working
method:

1. Pull full tracks in one call: `get_bone_track_keys` on `thigh_stretch_l` (rotation = leg swing)
   and `root_x` (position = pelvis bob). Local-space keys are fine; do not sample per-frame with
   `get_animated_bone_transform` — it is ~1–2 s per call and will time out.
2. Build a per-frame motion-energy signal from the derivative of both, smoothed over ~8 frames.
   Gate candidate windows to `energy > 0.40 * max`.
3. Autocorrelate **inside the active region only**. The pelvis bob peaks at the *half* cycle
   (16 f); the thigh peaks at the *full* gait cycle (33 f). **Take the full cycle** — both legs must
   return to phase or the loop swaps feet.
4. Choose the start frame minimising `seam_delta − 0.5 × normalised_energy`.
5. Trim with `unreal.MelodiaAssetRepairLibrary.keep_anim_sequence_frame_range(seq, first, last)` —
   your own BlueprintCallable, already handles head+tail correctly. `unreal.AnimationLibrary` has
   **no** trim/crop in 5.8.
6. Keep exactly `period` frames (start .. start+period−1), not period+1 — otherwise the seam frame
   is duplicated.

Measured profile for `A_Mocap_RunCycle`: dead 0–45, active 55–265, chosen 214–246.

---

## 2. Glide — IMPLEMENTED (layered blend, not additive)

**Built and saved this session.** The additive approach was abandoned after inspecting the
skeleton: `SK_Melusina_Skeleton`'s **reference pose already has arms straight out**
(`hand_l` component x=74.52, z=126.22, level with the shoulder at z=127.8 — a T-pose). An additive
is `Pose − RefPose`, so a glide pose authored near the ref pose yields a ~zero delta and the arms
would have stayed down. Additive was the wrong tool.

**What was built instead — layered blend per bone, inside the `Glide` state:**

```
A_Melusina_JumpLoop_Mocap_RootX ──> BasePose    ┐
                                                ├─ Layered blend per bone ──> Output Animation Pose
A_Melusina_GlidePose ───────────> BlendPoses_0  ┘   branch filter: shoulder_l + shoulder_r, depth 12
                                                    BlendWeights[0] = 1.0 (verified)
```

Legs, torso and pelvis come from the jump loop; both arm chains (shoulder → fingers, depth 12)
come from the glide pose. Node count in `Glide` went 2 → 4; compiled clean and saved.

`A_Melusina_GlidePose` was made by duplicating the jump loop and calling
`unreal.AnimationLibrary.remove_all_bone_animation`, which collapses it to the reference pose.
Verified: its `hand_l` reads exactly `(74.517, 12.780, 126.221)` = ref pose, versus the jump loop's
`(55.343, 10.345, 154.296)`. **Arms 19 uu wider and 28 uu lower** — a level, wide glide silhouette.

### Remaining polish on it (not blocking)

- **Sway.** Currently a held pose. A slow roll/yaw oscillation on `c_arm_fk_l/r` or a subtle spine
  drift would sell the Genshin/Nikki feel. Author as a short additive *on top of this blend*, where
  additive IS the right tool because the delta is genuine motion, not a static pose.
- **Arm angle.** Ref pose is a straight T. A real glide angles arms slightly back and down. Adjust by
  editing `A_Melusina_GlidePose`'s `arm_stretch_l/r` rotation keys, then re-measure `hand_l`
  component Z — lower Z = more swept.
- **Blend-in time.** The `Airborne → Glide` transition uses the default 0.2 s crossfade. A glide
  deploy usually wants ~0.25–0.35 s.
- Verify arm elevation with `get_animated_bone_transform` on `hand_l` / `upperarm`, **never**
  screenshots (see §9).

## 3. Kawaii physics — TUNED (needs your eye in PIE)

**One** Kawaii node in `ABP_Melusina_Current`, root `c_kilt_master_x` (skirt). Hair is separate
(`ABP_Melusina_Hair`, `ABP_Melusina_WaterHair`, `UMelodiaHairComponent` on `head_x`) and was **not**
touched.

The previous values were tuned when Walk and Run were the same slow clip. Against the new genuine
1.067 s run cycle with real pelvis bob, stiffness 0.16 at a 42° limit over-swings, and gravity −120
(real is −980) does not settle the hem between footfalls.

| Param | Before | After | Why |
|---|---|---|---|
| `stiffness` | 0.160 | **0.220** | faster return, less lag/overshoot at run speed |
| `damping` | 0.500 | **0.560** | kills oscillation after footfalls |
| `limit_angle` | 42.0° | **36.0°** | prevents over-swing / leg clipping at speed |
| `gravity.z` | −120 | **−200** | settles the hem; still floaty vs real −980 |

Unchanged deliberately: `world_damping_location` 0.70 / `world_damping_rotation` 0.65 (these govern
how much character motion transfers — lowering them would *increase* swing), `radius` 4.0,
`wind_scale` 1.5, `teleport_distance_threshold` 300 / `rotation` 10, `target_framerate` 60.

**This is a reasoned starting point, not a verified look.** Kawaii is a runtime simulation — it
cannot be validated by bone queries (they read authored keys, not sim output) and screenshots are
unreliable here (§9). It needs PIE with your eye. All four values are single fields on
`AnimGraphNode_KawaiiPhysics_0.node.physics_settings`; revert individually if a value reads wrong.

Still open: **`dummy_bone_length` is 0.0**, so the hem's final bone has no simulated tip. A small
value (~3–5) usually makes the hem end move. Left alone because it changes silhouette, which is an
art call.

Also still open: bind the limits DataAsset (`KAWAII:47`) — currently unbound, so the above is tuned
against unbounded behaviour and will want a second pass once it lands.

---

## 4. Graph hygiene — safe, queued

Four confirmed-dead nodes in `AnimGraph` (`connected_pins: []`):

- `AnimGraphNode_BlendSpacePlayer_0` — plays `BS_Melusina_Locomotion_Hybrid`, X pin bound to
  `RuntimeGroundSpeed`. Correct binding, zero connections, never evaluates.
- `AnimGraphNode_Slot_1`, `_2`, `_3` — duplicate `DefaultSlot` nodes.

Plus a dead `CharacterProperties` chain in `BlueprintThreadSafeUpdateAnimation` (the live chain reads
`PawnVelocity`/`PawnAcceleration` from C++; the dead one reads `CharacterProperties.*`).

All removal-only, no behaviour change. Not done this session because node deletion in the AnimGraph
was out of the agreed scope.

---

## 5. Blendspace — the remaining decision

`BS_Melusina_Locomotion_Hybrid` is 1D `GroundSpeed` 0–650, 7 samples, but only **4 unique clips**,
and **Walk and Run are byte-identical to 15 decimal places** (verified: `foot_l` at t=0.58 returns
`(13.549325127357811, −34.737963090970197, 28.977805997133007)` for both). Every sample is
`rate_scale: 1`, and the engine reports `root_motion_speed_known: false` (root-locked), so playrate
was never matched to ground speed.

`A_Melusina_RunLoop_Trim` is now a genuine distinct gait and can take the Run band.

**Still open:** Walk. Your mocap kit has **no walk take at all** — it is genuinely absent from the
25 source FBX, not just un-imported. Options:

- Record a walk (keeps the feminine-motion priority consistent).
- Use UE5 Manny `M_Neutral_Walk_Loop_F.FBX` for walk only. **Cost is higher than it looks:** those
  FBX are UE5 Manny skeleton (they carry `spine_04`/`spine_05`; `UE4_Mannequin_Skeleton` has zero
  `spine_04`, verified). They are animation-only so they cannot create their own skeleton. Requires
  importing `SKM_Manny_Simple` from `UE_5.8/Templates/TemplateResources/High/Characters/Content/Mannequins/Meshes/`
  (~32 MB), authoring an `IK_UE5Manny` (the template ships Control Rigs only, no IK rigs), and a new
  `RTG_UE5Manny_To_Melusina`.

Sprint is already distinct (110 frames, 0.917 s) and needs the same §1 trim treatment if it is also
a raw take.

---

## 6. Choral Sheep companion — ready to go

Blocked only on your approval of `SK_ChoralSheep`. Everything else is in:

- C++ complete: `AMelodiaChoralSheepActor`, `UMelodiaCompanionComponent`, `UMelodiaCompanionData`,
  `UMelodiaCompanionWardrobeBridge`, plus `MelodiaCompanionRulesTests` and
  `MelodiaWardrobeCompanionBridgeTests`.
- Data authored: `ChoralSheepDefinition.json` — follow 180 cm / acceptance 75 cm, interactions
  Graze / Harmonize / Guide, fur LOD bands NativeGroom → ShellCard → Impostor.
- `asset_status` gates: `ue_definition_asset: pending_clean_editor_reservation` — **that gate is now
  satisfied**, the editor builds and runs clean.

Runbook is `Docs/CHORAL_SHEEP_INTEGRATION_RUNBOOK.md`, 4 steps: import FBX → create
`DA_ChoralSheepDefinition` → configure → create `BP_ChoralSheep` from the actor class, assigning
**only** the definition asset (no hard rig reference).

**Animation note:** the sheep needs its own IK rig + retargeter against the same contract Melusina
uses. Do not reuse `IK_Melusina_Body_Current`. The §1 trim method applies to its cycles too.

---

## 7. First quest after Sir Melodious retrieval

Assets that exist: `Content/Melodia/Characters/SirMelodious/Retarget/` has `IK_SirMelodious`,
`IK_SirFlightSource`, `RTG_FlightSource_To_Sir`, `RTG_UE4Mannequin_To_SirMelodious` — so Sir
Melodious has a **working mannequin retarget lane**, unlike Melusina's until this session. His flight
source rig is also the nearest existing reference if you build Melusina's glide as §2 option 3.

Quest wiring runs through the existing narrative seam — the `music_world_key` gate
(`APCGHeroMusicGraphHost::OnPatternCompleted` → `MelodiaPCGNarrativeChallengeBridgeComponent` →
`CommitWorldChallenge(first_resonance_echo)`), code staged in `62202fb1`, needs PIE.

Open before quest work: `wardrobe_gameplay_hook` and `music_world_key` are both still OPEN and both
need PIE, not code.

---

## 8. BP updates queued

1. `BP_MelusinaJRPGCharacter` — attach `UMelusinaSorrowSeamComponent` (crash fixed in `b6646229`;
   it was calling `ConstructorHelpers::FObjectFinder` in `BeginPlay`, which fatals). Set
   `PaletteMPC = /Game/Melodia/_PROJECT/04_Materials/MPC_Melodia_Palette` — **note the duplicate
   palette**, see §9.
2. `BP_ChoralSheep` — create from `AMelodiaChoralSheepActor` per §6.
3. Disable `WaterHairFlipCache` (GeometryCache) in favour of the live Groom path; it bakes and cannot
   react to wind/MPC/`bIsGliding`. Keep as fallback until Groom parity is proven in PIE.
4. Two pre-existing compile warnings on the owner pawn: `RecreatePinForVariable: 'CharacterMesh0' pin
   not found` ×2. Present before this session.

---

## 9. Traps to avoid next session

- **Screenshots lie.** `capture_scene_preview` returns stale frames — three captures across two
  different animations returned identical bytes. Use bone data.
- **`capture_anim_frames`** does not advance time in AnimBlueprint mode and leaks a rooted UObject.
- **Two editors at once** corrupts assets and splits Monolith. Check
  `Get-Process UnrealEditor` before launching.
- **`set_retargeter_rigs` re-seeds ops** (5 → 9 observed) and the next retarget crashed the editor.
  Change pelvis/root settings directly.
- **`MPC_Melodia_Palette` exists twice** with different content: `Content/Melodia/_PROJECT/04_Materials/`
  (12,374 B, Aug 15) and `Content/_PROJECT/04_Materials/` (7,142 B, Aug 11). Two sources of truth for
  the whole palette-driven lookdev. Retire one before palette work.
- **CORRECTED:** the pawn uses **`SK_Melusina_V2_Body` (120 morph targets)**, not `SK_Melusina`.
  Verified from `BP_MelusinaJRPGCharacter`'s CDO on 2026-08-24. **Her face pipeline is complete.**
  An earlier version of this doc said the live mesh had 0 morphs and recommended promoting
  `SK_Melusina_OLD` — that would have been a **downgrade (120 → 69)** and is retracted. The
  slot shift is on `SK_Melusina`, a mesh **the game does not use**.
- **Quaternius has never worked.** Owner ground truth. Do not wire, automate, or import it.

- **Query the live object before believing any doc.** Every "X is missing" claim this session that came from a doc rather than a live query proved false — face, wardrobe and UI were all already built.
