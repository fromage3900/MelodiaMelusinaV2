# Melusina — Animation Next Level + Outfit Component Gameplay Core

**Date:** 2026-08-16 (plan of record) · **Status block added:** 2026-08-18
**Preceded by:** locomotion state machine repaired and saved this session
(`ABP_Melusina_Current.uasset` 608704 bytes @ 13:42)

---

## 08-18 status (read before acting)

The locomotion/idle stack was repaired in memory on 08-16, but the Unreal editor
never persisted a single `.uasset`. `ABP_Melusina_Current.uasset` is dated
**2026-08-14 20:04, 458641 bytes** — the 08-16 repairs never touched disk.
All 34 steps in `build_melusina_locomotion_stack.py` are dry-run clean and
waiting on a **responding** editor. Idle clip itself is the remaining content
gap — state binding, skeleton, and graph wiring are correct.

Until the editor lands: no clip-swapping, no re-deriving of blend rules, no
Quaternius rework (42 clips exist on disk but the registry sees zero —
unrelated to the idle fix).

## Where we actually are

Fixed and on disk today:

| Thing | State |
|---|---|
| `MelusinaLocomotion` | 7 states, `Locomotion` wired to `BS_Melusina_Locomotion`, no duplicate transitions, compile clean 0/0 |
| Transition rules | Driven by **`RuntimeGroundSpeed`** (native, `UMelodiaLocomotionAnimInstance`) |
| Blendspace X | Bound to `RuntimeGroundSpeed` — was unbound, reading 0 |
| Spatial puzzle kit | 5 BP children + prompt widget, 2 fixtures placed, map saved |
| Action montages | 10 wired (7 rebound, 3 created) |
| IK rig chains | `LeftLeg` / `RightLeg` on ARP deform bones, duplicates removed |

**The bug that mattered:** nothing writes the BP variable `Speed`.
`BlueprintThreadSafeUpdateAnimation` sets `Velocity`, `Acceleration`, `bIsMoving` only.
Rules keyed to `Speed` could never fire. The natively-driven float is
`RuntimeGroundSpeed`. Anything new must key off native or thread-safe-written values —
**check the setter exists before keying a rule to a variable.**

**Still open:** the idle *clip* is poor (owner call). State binding, skeleton
(`SK_Melusina_Skeleton` on both V1 and V2 body), and graph wiring are all correct, so
this is content, not plumbing.

---

## Phase A0 — There is no usable idle clip in the project (owner-confirmed)

Do not spend more time rebinding existing clips. Enumerated 2026-08-16:

| Source set | Idle available |
|---|---|
| `A_FB_Melusina_*` (FemaleBard, 16) | none — RunCycle, Jump, Dodge, LittleDance, Twirl, Stab, FairyWand, LiftOff |
| `A_Mocap_*` (Rokoko, 23) | none — same action set |
| `A_Q_Melusina_*` (Quaternius, 46) | `_Idle_Loop` exists but reads wrong on this rig |
| `A_CAS_Melusina_Idle_Loop` (Cascadeur) | Lane A import — fails the contract on 4 axes per `melusina_idle_retarget_rca_2026-08-13.md` |
| `A_Melusina_Idle_Mocap_RootX` | renders as T-pose |

**Retargeter alignment was genuinely broken and is now fixed** —
`RTG_Quaternius_to_Melusina` had `bone_delta_count: 0` (Quaternius is T-pose, Melusina is
ARP A-pose). `align_retarget_pose` produced 32 deltas, and `QuaterniusAligned/` holds
re-baked clips. That was a real defect worth fixing, but it did **not** make the idle good
— the source clip itself is the limit.

**Conclusion: the idle must be authored or sourced, not selected.** Owner has researched
new animation / female-rig sources; that acquisition is the unblock. Until then locomotion
is acceptable and idle is not, and no further clip-swapping should be attempted.

## Phase A — Idle and pose quality (content, not wiring)

1. **Audition the registered idles** against the V2 body and pick one:
   `A_Q_Melusina_Idle_Loop` (now bound), `_Idle_Talking_Loop`, `_Idle_Torch_Loop`,
   `A_CAS_Melusina_Idle_Loop`. 46 Quaternius clips are registered and loadable —
   last night's "they don't load" was a wedged-editor registry artifact, not the assets.
2. **Additive breathing layer.** Author a small additive on top of whichever base idle
   wins, rather than hunting for one clip that does everything. Keeps the base swappable.
3. **Idle break / fidget.** After N seconds idle, play `AM_Melusina_Idle_Dance` or
   `_Idle_Talk` through `DefaultSlot`, then return. The slot node already exists.
4. **Blink.** `eyesCloseL` / `eyesCloseR` (FACS — the ARKit `eyeBlink*` names are empty
   shells and compile to nothing). The approved mocap idle is 0.5s, far too short to bake
   a natural cadence into, so drive blinks from the AnimBP on a randomised ~2-per-7s
   timer. `build_melusina_idle_life.py` already refuses the bake and says so.

## Phase A2 — Materials: the V2 instances have NO texture parameters (owner-reported)

Verified 2026-08-16 via `material_query get_instance_parameters`:
`MI_Melusina_SBW_MELUSINA_006` and `_007` are parented to
`/Game/EnvSandbox/Materials/Masters/M_Master_Toon_Universal` and expose **zero** texture
parameters. They are not pointing at *old* textures — they are pointing at **nothing**, so
the body renders master defaults. This is the likely cause of the reported "textures and
instances don't use the most recent v22 assets" and of the gloves reading wrong.

`SK_Melusina_V2_Body` has 5 slots:

| Slot | Instance |
|---|---|
| 0 SBW_MELUSINA_006 | `MI_Melusina_SBW_MELUSINA_006` |
| 1 SBW_MELUSINA_007 | `MI_Melusina_SBW_MELUSINA_007` |
| 2 Gradient__Radial__002 | `MI_Melusina_SBW_MELUSINA_007` |
| 3 Gradient__Radial__002 | `MI_Melusina_Outline_005` |
| 4 Gradient__Radial__002 | `MI_Melusina_IRISFRONT_001` |

A full PBR set already exists under
`Content/Melodia/Characters/Melusina/Textures/Clothes/` —
`T_MelusinaC_<piece>_{BaseColor,Normal,Roughness,Metallic,Emission,Alpha}` for belt,
bloomers, Bow, frontpanel and others.

Work:
1. Establish the **v22 texture set of record** — confirm with the owner which folder is
   canonical before wiring, since `Textures/Clothes/` may not be the newest export.
2. Map slot → texture set per piece, then `material_query set_instance_parameters` to bind
   Albedo / NormalMap / RoughnessMap / MetallicMap on each instance.
   `specs/anim_presets/melusina_v2_material_map.json` is the approved
   source-material → instance mapping and should stay the authority.
3. Do **not** edit or reparent `M_Master_Toon_Universal` — it is a shared master and the
   V2 importer contract says masters are never edited. Bind at the instance layer only.
4. Re-check after binding: gloves/hands are a good tell because they span body and
   accessory slots.

## Phase A3 — Hands and fingers (content, not wiring)

Verified correct and NOT the problem: `index1_l`/`2`/`3`, `middle*`, `pinky*`, `ring*`,
`thumb*` all exist on `SK_Melusina_Skeleton`; the retargeter maps
`index1_l -> index3_l` (target) from `index_01_l -> index_03_l` (source); all 10 finger
chains present on both rigs.

The weirdness is that the **Quaternius source hand is simpler than Melusina's three-joint
fingers**, so retargeted finger curves are poor. Options, cheapest first:
1. Disable/zero the finger chains in the retarget so hands hold their reference pose
   instead of receiving bad data.
2. Author a static hand pose additive and layer it over locomotion.
3. Re-retarget the hands only, from a source with a matching hand rig.

**Correction to record:** the live retarget target rig is
`/Game/Melodia/Mocap/Retarget/IK_Melusina_Body_Current` — **not**
`/Game/Melodia/Characters/Melusina/IK_Melusina_Body`. Earlier foot-IK chains/solver were
authored into the wrong asset and must be redone against `_Current`.

## Phase B — Locomotion feel

1. **Measure real root speed** per clip (`get_root_motion_speed`) and reposition the
   blendspace samples onto measured values instead of the guessed 0/180/420/630.
   Axis max is already 750 so the 714 uu/s sprint gate no longer clamps.
2. **Sync groups + markers.** `derive_foot_sync_markers` on walk/run/sprint so the blend
   does not slide feet between samples.
3. **Foot IK.** Chains exist; goals do not (`goals: []`). `add_ik_solver` takes
   `goals: [{name, bone}]` — create `Goal_Foot_L/R` on `foot_l` / `foot_r`, then
   `build_foot_ik_pass(abp_path, left_foot_bone, right_foot_bone, pelvis_bone)`.
   Deform chain is ARP: `thigh_stretch_* -> leg_stretch_* -> foot_*`, hip is `root_x`.
   **`thigh_l` / `calf_l` / `pelvis` do not exist** — those are Blender-contract names.
4. **Jump wind-up finish.** `bJumpWindup` exists on the ABP and the `JumpWindup` state is
   entered by it. Remaining: pawn-side `MelodiaTraversalJump` Pressed → set the flag
   without calling `Jump()`, and a `JumpLaunch` notify in the wind-up clip that calls it.
5. **Graph tidy.** 3 duplicate `DefaultSlot` nodes and the orphan
   `BS_Melusina_Locomotion_Hybrid` player are unconnected but confusing — remove.

## Phase C — Outfit component gameplay core

The authority already exists; do not rebuild it.

- `UMelodiaOutfitComponent` (`Plugins/MelodiaCore`) and `UMelodiaWardrobeComponent`
  (`Plugins/MelodiaWardrobe`) both leader-pose slots to the body mesh.
- V2 pieces are imported at `/Game/Melodia/Characters/Melusina/Outfits/V2/`:
  `Body`, `Shirt`, `Skirt`, `Boots`, `Accessories` — all on `SK_Melusina_Skeleton`.

**Physics rule, already settled and worth not re-deriving:** leader-posed children do not
evaluate their own AnimInstance, so a garment can never simulate its own physics. The
`c_kilt_*` bones live in the 465-bone **body** skeleton, so KawaiiPhysics belongs in the
**body ABP** — where it already is, rooted at `c_kilt_master_x` — and propagates to every
garment through leader pose. This scales to new outfits with no code change.

Work:

1. **Register one outfit end-to-end** before any catalog work: a `V2_Default` definition
   binding the five pieces, equipped through the existing component on
   `BP_MelusinaJRPGCharacter`.
2. **Slot contract test** — equip/unequip leaves no orphan components and no skeleton
   mismatch. There is an existing `test_melodia_wardrobe_transaction_contract.py` to extend.
3. **Skirt physics tuning** against real locomotion speeds. It was authored against a
   static pose; now that she actually moves it will read wrong.
   `DA_Melusina_SkirtCollisionLimits` exists; `audit_kawaii_runtime_readonly.py` verifies.
4. **WBP hook.** `WBP_MelodiaInteractionPrompt` exists but is empty. Wardrobe UI should
   reuse the same prompt/PromptText route rather than inventing a second one.

## Phase D — Puzzle + water gameplay wiring

1. **Event wiring** for the new BP children — `OnInteractionRequested` → prompt widget,
   `OnPuzzleActivated` → state anchor. Node IDs exist now that the BPs are created.
2. **Water gameplay is NOT blocked on Oceanology.** A complete native authority already
   exists (`UMelodiaWaterGameplaySubsystem`, `AMelodiaWaterPlatform`,
   `UMelodiaPCGWaterGameplayBridgeComponent`, buoyancy) and is compiled into
   `UnrealEditor-BS_GodFile.dll` (rebuilt 08-16 01:04).
   `Tools/melodia_water_gameplay_t3d.py` has 11 wiring targets, two of which are the
   water↔puzzle bridge: `pattern_completed_puzzle` → `OnPuzzleSolved`, and
   `platform_route_activation`.
3. **Oceanology** gates ocean *look*, not water *gameplay*. Port is ~80% done: include
   tails, RHI SRV, texture unification and the whole buffer layer are ported and verified
   against 5.8 headers. Remaining is one 168-line ray-tracing migration
   (`GetDynamicRayTracingInstances` → `FRayTracingInstanceCollector`). Do **not** compile
   the RT path out — `DefaultEngine.ini:37` has `r.RayTracing=True`.

---

## Working rules earned this session

1. **Verify the artifact, not the response.** `save_asset` returned
   `{"saved": true, "was_dirty": true}` repeatedly while the `.uasset` stayed byte-identical.
   Check mtime. `--apply` now does.
2. **Check a variable has a setter before keying a rule to it.** `Speed` existed, looked
   right, and was never written.
3. **Monolith actions are not idempotent.** `add_transition` / `create_blueprint` duplicate
   or error on re-run. Read existing state first; every driver now does.
4. **A JSON body can report failure while the transport succeeds.** `call()` now raises on
   `success`/`ok` false.
5. **Read schemas with `describe_query action_schema` (`target_action`, not `target`).**
   Param names differ per action: `asset_path`, but `save_path` for `create_blueprint`,
   `blueprint` for `spawn_blueprint_actor`, `machine_name`, `anim_asset_path`,
   `position_x/y`, `axis: "X"`, and `path` as an **array** for pin bindings.
6. **A wedged editor lies about everything** — registry misses, phantom save success.
   Confirm the editor is healthy before believing any negative result about assets.
