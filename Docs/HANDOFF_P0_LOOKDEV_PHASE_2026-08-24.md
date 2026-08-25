# 🎼 MELUSINA — P0 + LOOKDEV PHASE HANDOFF
### 2026-08-24 · animation pillar closed · lookdev pillar opening

> **One-line state:** animation, face and wardrobe are all built and live. What remains is
> runtime proof (P0 gates need PIE) and UI data binding — not construction.

---

---

## 🚨 LATE CORRECTION — the T-pose was the Idle state

Owner ground truth: Melusina was still T-posing. **The `Idle` state's animation was not proper.**
Owner fixed it.

`Idle` is the entry state of `MelusinaLocomotion`, so a bad clip there presents as a whole-body
T-pose in nearly every situation — masking the fact that transitions, runtime flags, glide and the
blendspace were all wired correctly.

**Lesson for the prompts below:** when a whole-body pose failure appears, check the **entry state's
clip first**. It is cheaper than diffing retargeters and it was called out in the Aug-20 review
("Idle SequencePlayer remains pointed at the pre-v22 asset") a week before it bit.

**CONFIRMED 2026-08-24 21:33:** `Idle` now plays **`A_Melusina_Idle`** (previously
`A_Melusina_Idle_Mocap_RootX`). Owner's fix, read back live via `get_state_info`.

---

---

## 🩸 THE SILENT KILLER — read-only `.uasset` reverts your work

**Confirmed twice on 2026-08-24.** The pelvis fix on `RTG_UE4Mannequin_To_Melusina` was applied,
appeared to succeed, and **silently reverted**. Root cause:

```
os.access(file, os.W_OK) -> False        # file is read-only
EditorAssetLibrary.save_loaded_asset()   -> False   (no exception, no dialog)
```

The edit lives in memory, the editor reports success, and the change vanishes the moment the asset
reloads. It bit the retargeter **and** `BS_Melusina_Locomotion_Hybrid` in the same session.

Where the flag comes from: assets restored via `git checkout` land read-only, and source-control
operations can re-apply it — it came back *after* being cleared once.

**Mandatory pattern for every `.uasset` write:**

```python
import os, stat, unreal
f = r'<absolute path to .uasset>'
os.chmod(f, stat.S_IWRITE | stat.S_IREAD)          # clear read-only FIRST
a = unreal.load_asset('<game path>')
ok = unreal.EditorAssetLibrary.save_loaded_asset(a)
assert ok, 'save failed'
print(os.path.getmtime(f))                          # CONFIRM disk mtime moved
```

**Never trust an edit you have not seen change the disk mtime.**

---

## 📊 PILLAR DASHBOARD

| Pillar | State | Blocking on |
|---|---|---|
| 🟢 **Retargeting** | **DONE** — mocap lane + mannequin lane both verified | — |
| 🟢 **Locomotion clips** | **DONE** — Idle/Walk/Run/Sprint present, Run now genuinely distinct | — |
| 🟢 **Glide** | **DONE** — layered blend, arms 19 uu wider / 28 uu lower | polish only (sway) |
| 🟢 **Kawaii skirt** | **TUNED** — 4 values retuned for the new run cycle | your eye in PIE |
| 🟢 **Editor build** | **GREEN** — 0 errors, 35.9 s | — |
| 🟡 **Blendspace** | **80%** — Run band real; Walk band still duplicated | a walk take |
| 🟢 **Face / shape keys** | **DONE** — 120 morphs live on `SK_Melusina_V2_Body` | — |
| 🟡 **Materials** | shifted slots are on `SK_Melusina`, **a mesh the game does not use** | confirm correct target first |
| 🔴 **P0 gates** | **6 OPEN** | PIE, not code |

---

## ⛔ RETRACTED — "the live mesh has no morphs" was WRONG

**An earlier version of this handoff claimed `SK_Melusina_OLD` was the highest-value fix because
the live mesh had 0 morph targets and a broken material map. That was wrong and is retracted.**

The error: morph counts were read off `SK_Melusina` and assumed to be the pawn mesh, because the
project docs and `MELUSINA_ANIMATION_PIPELINE_REVIEW_2026-08-20.md` describe it that way.
`CharacterMesh0` was never actually queried until 2026-08-24 21:40.

**Live truth, read from `BP_MelusinaJRPGCharacter`'s CDO:**

```
CharacterMesh0.SkeletalMesh = SK_Melusina_V2_Body
CharacterMesh0.AnimClass    = ABP_Melusina_Current_C
```

| Mesh | Morphs | Materials | On the pawn? |
|---|---|---|---|
| **`SK_Melusina_V2_Body`** | **120** | 5 (modular base) | **YES — live** |
| `SK_Melusina_OLD` | 69 | 35 | no |
| `SK_Melusina` | 0 | 33 (shifted) | no |

**Consequences — all three change the plan:**

1. **The face pipeline is COMPLETE.** 120 morph targets are live on the pawn, matching the 120
   curves the skeleton declares, name for name. Nothing to build. Promoting `SK_Melusina_OLD`
   would be a **downgrade** (120 → 69).
2. **The material patchwork is on `SK_Melusina` — a mesh the game does not use.** Material effort
   aimed at that asset is aimed at the wrong target. The pawn's visible materials come from
   `SK_Melusina_V2_Body` (5 slots) plus the four wardrobe garment meshes.
3. **The wardrobe is fully wired**, verified on the live component:
   `Shirt→SK_Melusina_V2_Shirt`, `Skirt→SK_Melusina_V2_Skirt`, `Boots→SK_Melusina_V2_Boots`,
   `Accessories→SK_Melusina_V2_Accessories`. Applied in `BeginPlay()` (not on Activate, so
   `bAutoActivate: False` does not block it). Saved cosmetics take priority over defaults.

**Standing lesson:** this project's docs consistently understate what is built —
`ORCHESTRA_CONVERGENCE` says so in its own headline ("the project is much further along than its
docs say"). **Query the live object before believing any doc claim that something is missing.**

---

## ✅ VERIFIED THIS SESSION — every claim has a receipt

| Fix | Receipt |
|---|---|
| Mannequin retarget pelvis `pelvis` → **`root_x`** | `foot_l` Z **4.18 → 25.52** across cycle |
| **`A_Melusina_RunLoop_Trim`** created | 33 keys, 1.067 s, `loop=true`, `foot_l` travels **9.2 uu** |
| Blendspace Run band → real loop | samples x=300 & x=420 now `RunLoop_Trim` |
| Glide: dance → layered blend | `hand_l` x **74.52** vs jump's 55.34 |
| Kawaii retuned | stiffness .16→**.22**, damping .50→**.56**, limit 42°→**36°**, grav −120→**−200** |
| melodia MCP live path | `RPC-ERROR -32601` → `OK` |
| Editor unblocked | Claireon off; Monolith **1402 tools** unaffected |

**Root-cause diagnosis that unblocked the blendspace:** `A_Melusina_Walk_Mocap_RootX` and
`A_Melusina_Run_Mocap_RootX` are **byte-identical to 15 decimal places** — `foot_l` at t=0.58 returns
`(13.549325127357811, −34.737963090970197, 28.977805997133007)` for *both*. One clip wearing two
names. No amount of sample tuning could ever have fixed that.

---

---

## 🔌 INTEGRATION LAYER — the beat/FX pipe was never connected

**Found and fixed in code 2026-08-24 (staged, needs a build).**

`NPC_Melodia_Palette` (`/Game/EnvSandbox/VFX/MPC/`) declares **64 Niagara parameters** — `BeatPulse`,
`BeatPhase`, `BeatIntensity`, `RhythmPulse`, `ComboNormalized`, `CrescendoNormalized`,
`CommandEnergy`, `BreakPulse`, `VictoryPulse`, `EnemyTension`, `DreadPresence`, `DissonanceAmount`,
plus the full Melusina colour set.

**At least six Niagara systems already sample it** — `NS_Melodia_ClickSparkle`,
`NS_Melodia_CursorTrail`, `NS_Melusina_Arc`, `NS_Melusina_ChaosDrift`, `NS_Melusina_Dust`,
`NS_Melusina_EntropyDust`.

**Nothing in game code ever wrote it.** The only C++ referencing `UNiagaraParameterCollection` is
Monolith's own tooling plugin. `MelodiaAudioReactivePresentationSubsystem` publishes the beat
namespace to `MPC_Melodia_Palette` (materials) and stops there — Niagara cannot read an MPC, so
**every beat-reactive FX parameter in the game read a constant 0.0.**

Fix: mirror the same seven values into the NPC in the same publish function
(`GlobalReactivity`, `Bass`, `Mid`, `Treble`, `BeatPhase`, `BeatPulse`, `BeatIntensity`).
47 lines added, nothing removed. **Not yet built** — needs a closed editor.

Gotcha worth keeping: `UNiagaraParameterCollectionInstance::SetFloatParameter` runs its argument
through `ParameterNameFromFriendlyString`, so pass the **bare** name (`"BeatPulse"`). Passing the
fully-qualified `NPC.MelodiaPalette.BeatPulse` silently writes a parameter nothing reads.

### Still unwired on this seam
- **`NS_Melodia_LaneHit` has ZERO references** — a purpose-built rhythm lane-hit effect that nothing
  spawns.
- **`RhythmBeatTracker::OnBeat.Broadcast()` has no C++ listener at all.** The beat fires into
  nothing.
- `ComboNormalized` / `VictoryPulse` / `EnemyTension` are declared in the NPC and unwritten —
  feeding them from `MelodiaBattleSession` is the cheapest route to battle-intensity variation.

---

## ✔ AGENT RESULTS — independently verified

| Claim | Verified how | Result |
|---|---|---|
| `WBP_Battle_Rhythm` now reads live state | `get_graph_summary` on EventGraph | **TRUE** — Tick → SetText(Judgement←`LastJudgmentText`) → SetText(Combo←`SessionCombo`) → SwitchEnum → 3× SetText(ClockSource), 20 nodes, exec chain intact |
| Sprint is already a clean loop, needs no trim | `get_sequence_info` + `get_animated_bone_transform` | **TRUE** — 110 frames @120fps, `is_looping: true`, `foot_l` Z **50.547** mid-cycle. Task closed as already-done. |

**Three of my own stated facts were wrong and the agents caught them:**
1. `UMelodiaRhythmHUDWidget` *does* have `LastJudgmentText` — my grep missed it on the
   **Judgement/Judgment** spelling.
2. `MelodiaBattleSession` has `SessionCombo` (live) and `SessionMaxCombo` (persistent), **not**
   `MaxCombo`.
3. **There are TWO `UMelodiaTokenWalletSubsystem` classes** — the real one in `Plugins/MelodiaCore`
   and a thinner stub in `Plugins/MelodiaTokenWallet` (500-token endowment, `GetSnapshot` not
   `Pure`). `_Quarantine_DuplicateWallet_*` folders suggest a migration in flight. **Resolve the
   wrong one and wallet UI shows different numbers.** Same disease as the duplicate
   `MPC_Melodia_Palette`.

Also corrected: `A_Melusina_Sprint_Mocap_RootX` lives under `Animations/Locomotion/`, and
`BS_Melusina_Locomotion_Hybrid` directly under `Animations/` — not where earlier drafts implied.

---

## 🤖 COPY-PASTE AGENT PROMPTS

Each block is self-contained. Paste one per session. **Do not run two against the same asset.**

---

### 🎨 PROMPT A — Lookdev: material pass on the meshes the game ACTUALLY uses

```
Improve Melusina's materials. Work ONLY on the assets the live pawn uses.

VERIFIED 2026-08-24 (read from BP_MelusinaJRPGCharacter CDO, do not re-derive):
- CharacterMesh0.SkeletalMesh = /Game/Melodia/Characters/Melusina/Outfits/V2/SK_Melusina_V2_Body
  (120 morph targets, 5 material slots)
- The Wardrobe component (MelodiaWardrobeComponent) equips four more meshes in BeginPlay:
    Shirt       -> Outfits/V2/SK_Melusina_V2_Shirt
    Skirt       -> Outfits/V2/SK_Melusina_V2_Skirt
    Boots       -> Outfits/V2/SK_Melusina_V2_Boots
    Accessories -> Outfits/V2/SK_Melusina_V2_Accessories
  So her on-screen look = V2_Body + those four. THOSE are the material targets.

DO NOT WORK ON /Game/Melodia/Characters/Melusina/SK_Melusina. It has 33 slots with a
known shift from index 13, but the game DOES NOT USE IT. Earlier handoffs told agents to
fix that mesh; that guidance was wrong and is retracted.

TASK:
1. Read all five V2 meshes with animation_query.get_skeletal_mesh_info. Report slot
   count and assigned material per slot for each.
2. Flag any slot whose assigned material name does not match its slot name, any slot
   pointing into a scratch folder (e.g. _SkeletonFixSpike/), and any unassigned slot.
3. Report findings BEFORE changing anything. Get owner sign-off on the intended mapping.

RULES:
- Verify by re-reading get_skeletal_mesh_info. NEVER by screenshot: capture_scene_preview
  returns STALE frames (proven - three captures across two animations, identical bytes).
- .uasset files are READ-ONLY; save_loaded_asset returns False silently. os.chmod writable
  first, then confirm the disk mtime moved. This has already reverted real work twice.
- MPC_Melodia_Palette exists at TWO paths with different content:
  Content/Melodia/_PROJECT/04_Materials/ (12,374 B) and Content/_PROJECT/04_Materials/
  (7,142 B). The pawn's SorrowSeam component points at the Melodia one. Retire the other
  before any palette work.
```

---

### 😊 PROMPT B — Face / lipsync (the rig is DONE, this is content)

```
Melusina's face rig is COMPLETE. Do not rebuild it.

VERIFIED 2026-08-24:
- Live pawn mesh SK_Melusina_V2_Body has 120 morph targets.
- SK_Melusina_Skeleton declares 120 matching curves (21 phoneme visemes
  aa_ah_ax_01..p_b_m_21, full ARKit set jawOpen/eyeBlinkLeft/browInnerUp, ARP controls).
- UE binds curves to morph targets BY NAME, so the pipeline is already closed.
  No AnimBlueprint work, no mesh swap, no reimport is required.

An earlier handoff claimed the live mesh had 0 morphs and recommended promoting
SK_Melusina_OLD. That was WRONG - it read morph counts off SK_Melusina, which is not the
pawn mesh. Promoting _OLD would DOWNGRADE her 120 -> 69. Retracted.

WHAT IS ACTUALLY LEFT (content, not plumbing):
1. Prove a curve drives a morph at runtime: play any AnimSequence carrying a face curve
   and confirm the morph moves. Verify with get_animated_bone_transform / curve queries,
   NOT screenshots.
2. Author facial performance - idle blinks, dialogue visemes, emotion poses. There is
   currently no facial animation content, only the capability.
3. Blink: a simple looping additive on eyeBlinkLeft/eyeBlinkRight is the cheapest large
   win for making her feel alive.
4. If lipsync is wanted, the 21 phoneme visemes are already named for it.
```

---

### 🖥️ PROMPT B2 — UI live data binding

```
Make the Melodia UI read live game state. It currently binds to NOTHING.

VERIFIED 2026-08-24:
- WBP_Battle_Rhythm: 0 bindings. WBP_MelodiaCurrencyRow: 0 bindings. 38 WBP_* exist.
- Widget class paths in MelodiaUIBridgeSubsystem.cpp all resolve to real assets - the
  problem is wiring, not missing or mispathed assets.
- WBP_Battle_Rhythm parent = C++ UMelodiaRhythmHUDWidget, which exposes BlueprintReadOnly
  ActiveHUDMode, bIsSprinting, bIsGliding, LastActionPromptText. It has NO Combo/Judgement
  /ClockSource properties - that data lives on MelodiaBattleSession (MaxCombo + BlueprintPure
  getters).
- Wallet data: UMelodiaTokenWalletSubsystem::GetSnapshot() -> FMelodiaWalletSnapshot
  (Balances, Resources, ResourceMax, Shards, ManaCurrent/Max, GoldenTokens, TotalCollected)
  plus BlueprintPure GetShards/GetBalance/GetResource/CanAfford.
- ALREADY DONE: JudgementText, ComboText, ClockSourceText converted to variables
  (is_variable was false - a non-variable widget cannot be bound at all).
- MelodiaUIBridgeSubsystem is the SOLE widget owner. MelodiaJRPGBattleOverlaySubsystem was
  deliberately retired into it - do not re-add widget creation there.

Same read-only and no-screenshot rules as PROMPT A.
```

---

### 🎬 PROMPT C — Finish the blendspace

```
Complete Melusina's locomotion blendspace.

CURRENT STATE (verified 2026-08-24):
BS_Melusina_Locomotion_Hybrid, 1D GroundSpeed 0-650, 7 samples:
  x=0        A_Melusina_Idle_Mocap_RootX
  x=150,180  A_Melusina_Walk_Mocap_RootX     <-- SAME CLIP TWICE
  x=300,420  A_Melusina_RunLoop_Trim         <-- fixed this session, real gait
  x=540,630  A_Melusina_Sprint_Mocap_RootX   <-- SAME CLIP TWICE
All samples rate_scale=1. Engine reports root_motion_speed_known=false (root-locked).

REMAINING:
1. Walk band is still one clip at both 150 and 180. The owner's mocap kit has NO walk
   take (verified against C:\Users\froma\OneDrive - Humber Polytechnic\Recordings\Mocap).
   Either record one, or bring in UE5 Manny - but note the cost: those FBX carry
   spine_04/spine_05 (UE5 skeleton); UE4_Mannequin_Skeleton has ZERO spine_04. They are
   animation-only so cannot create their own skeleton. Needs SKM_Manny_Simple (~32MB from
   UE_5.8/Templates/TemplateResources/High/Characters/Content/Mannequins/Meshes/), a new
   IK_UE5Manny (template ships Control Rigs only, no IK rigs), and RTG_UE5Manny_To_Melusina.
2. Sprint is a raw take and needs the same trim treatment as Run - see the trim recipe in
   MELUSINA_NEXT_SESSION_PREP_2026-08-24.md section 1.

TRIM RECIPE (reuse verbatim, it works):
- get_bone_track_keys on thigh_stretch_l (rotation) + root_x (position) - ONE call each.
  Do NOT sample per-frame with get_animated_bone_transform; it is 1-2s/call and times out.
- Build per-frame motion energy from the derivative of both, smoothed over ~8 frames.
  Gate windows to energy > 0.40*max. Raw takes START WITH THE ACTOR STANDING STILL and a
  naive seam-minimiser will pick that dead head (it has a perfect seam and no motion).
- Autocorrelate INSIDE the active region only. Pelvis bob peaks at the HALF cycle; the
  thigh peaks at the FULL gait cycle. TAKE THE FULL CYCLE or the loop swaps feet.
- Trim with unreal.MelodiaAssetRepairLibrary.keep_anim_sequence_frame_range(seq,first,last).
  unreal.AnimationLibrary has NO trim/crop in 5.8.
- Keep exactly `period` frames, not period+1, or the seam frame duplicates.
```

---

### 🪶 PROMPT D — Glide polish

```
Polish Melusina's glide. It is already functional - do not rebuild it.

CURRENT (built 2026-08-24, verified):
Glide state in ABP_Melusina_Current / MelusinaLocomotion:
  A_Melusina_JumpLoop_Mocap_RootX -> BasePose     of Layered blend per bone
  A_Melusina_GlidePose            -> BlendPoses_0
  branch filter: shoulder_l + shoulder_r, depth 12; BlendWeights[0] = 1.0
Legs/torso from the jump loop, both arm chains from the glide pose.
Measured: hand_l x=74.52 z=126.22 (glide) vs 55.34/154.30 (jump) = 19uu wider, 28uu lower.

WHY NOT ADDITIVE: SK_Melusina_Skeleton's REFERENCE POSE already has arms straight out
(T-pose). An additive is Pose - RefPose, so a glide pose near ref yields ~zero delta and
the arms stay down. Additive is the wrong tool for a static pose here.

POLISH TASKS:
1. SWAY - currently a held pose. Author a SHORT ADDITIVE on top of this blend (additive IS
   correct here, because the delta is genuine motion). Slow roll/yaw on c_arm_fk_l/r plus
   subtle spine drift. ~1.5-2.5s loop.
2. ARM SWEEP - ref pose is a straight T. Real glides angle arms back and down. Edit
   A_Melusina_GlidePose arm_stretch_l/r rotation keys, then re-measure hand_l component Z
   (lower Z = more swept).
3. BLEND TIME - Airborne->Glide uses the default 0.2s crossfade. Glide deploy usually wants
   0.25-0.35s.

VERIFY WITH get_animated_bone_transform ON hand_l, NEVER screenshots.
```

---

### 🐑 PROMPT E — Choral Sheep (construction DONE; only the mesh is outstanding)

```
The Choral Sheep companion is BUILT. Do not rebuild it.

DONE 2026-08-24 (verified, saved):
- DA_ChoralSheepDefinition created at /Game/Melodia/Companions/ChoralSheep/
  UMelodiaCompanionDefinitionAsset. CompanionId=ChoralSheep, FollowDistance=180,
  FollowAcceptanceRadius=75, SupportedInteractions=[GRAZE, HARMONIZE, GUIDE].
- BP_ChoralSheep created at the same path, parent AMelodiaChoralSheepActor,
  CompanionDefinition -> DA_ChoralSheepDefinition. Compiled, saved 21:46:25.
- Per the runbook the Blueprint holds NO hard rig reference, so the mesh drops into the
  DATA ASSET later without touching the Blueprint.
- C++ was already complete: AMelodiaChoralSheepActor, UMelodiaCompanionComponent,
  UMelodiaCompanionData, UMelodiaCompanionWardrobeBridge + two test suites.

OUTSTANDING - owner is rigging the mesh:
1. When SK_ChoralSheep exists, set it on DA_ChoralSheepDefinition (NOT on the Blueprint).
2. Optional ABP_ChoralSheep -> the definition's AnimationBlueprint field.
3. The sheep needs its OWN IK rig + retargeter. Do NOT reuse IK_Melusina_Body_Current.
4. First test only in /Game/_PROJECT/Levels/RenderTests/L_ChoralSheep_Prototype per the
   runbook - not L_WP_SakuraDream, not MelodiaIntegrationMap.

Runbook: Docs/CHORAL_SHEEP_INTEGRATION_RUNBOOK.md
```

---

### 🎯 PROMPT F — P0 gates (PIE, not code)

```
Close Melusina's remaining P0 gates. All six need PIE, not code.

OPEN: rhythm_owner, hud_single_writer, rhythm_grade_to_result,
      wardrobe_equip_roundtrip, wardrobe_gameplay_hook, music_world_key
PASSED (historical): runtime, save_load, repeat_consume, package_launch

CRITICAL - TWO CLASSES OF EVIDENCE ARE VOID, RE-DERIVE THEM:
1. Any gate green from melodia_animation_validate_bindings or
   melodia_animation_validate_state_machine. Those are listed in monolith_static as gate
   implementations and were SILENTLY FAILING - _monolith_call sent dotted strings as MCP
   tool names ("animation_query.get_abp_info" is not a tool). Fixed 2026-08-24 in
   deploy/melodia_mcp_server.py, but the MCP server must be RESTARTED to pick it up
   (MCP servers load at session start).
2. Any gate accepting a screen capture as visual evidence. capture_scene_preview returns
   STALE frames - proven: walk_t000, walk_t058 and run_t050 all hashed 405208e3... across
   TWO DIFFERENT animations. Gates must assert on bone/curve data.

hud_single_writer note: MelodiaJRPGBattleOverlaySubsystem was merged into
MelodiaUIBridgeSubsystem (commit e1b62b28). The SAME refactor also exists on the G: drive
as ae49c2f8 - they will conflict on merge. Resolve before trusting either.
```

---

## ⚠️ TRAPS — read before touching the editor

| Trap | Symptom | Do this |
|---|---|---|
| **Read-only .uasset** | `save_loaded_asset` returns `False`, edits vanish silently | `os.chmod` writable, verify disk mtime changed |
| **Stale captures** | different animations return identical PNG bytes | use `get_animated_bone_transform` |
| **`capture_anim_frames`** | frames byte-identical; later `!IsRooted()` crash | avoid; use `capture_scene_preview` sparingly |
| **Two editors** | asset corruption, split Monolith | `Get-Process UnrealEditor` before launching |
| **`set_retargeter_rigs`** | re-seeds ops 5→9, next retarget crashes editor | change pelvis/root settings directly |
| **Stale Live Coding** | UBT: "Unable to build while Live Coding is active" with no editor running | clear `*.patch_*` under `Binaries/` |
| **Bare `git fetch gdrive`** | "bad tree object", looks like corruption | fetch named branches; G: is NOT corrupt |

**Duplicate palette:** `MPC_Melodia_Palette` exists at `Content/Melodia/_PROJECT/04_Materials/`
(12,374 B) **and** `Content/_PROJECT/04_Materials/` (7,142 B) — different content, two sources of
truth for the whole palette-driven lookdev. Retire one before palette work.

**Quaternius has never worked.** Owner ground truth. Do not wire, automate, or import it.

---

## 🔧 KNOWN-OPEN, LOW IMPACT

`RTG_UE4Mannequin_To_Melusina` **Root Motion op (index 3)** still has `TargetPelvis = pelvis`;
the working `RTG_Mocap_to_Melusina_Current` uses `root_x`. **No Monolith action exposes the Root
Motion op** (only Pelvis Motion, FK/IK Chains, Speed Planting), and `IKRetargeter.op_stack` is
deprecated in 5.6+ in favour of `RetargetOps`. Low impact: these clips are root-locked
(`has_root_motion: false`), so the op does little. Fix by hand in the IK Retargeter editor, or via
`UIKRetargeterController.GetOpController`.

The **Pelvis Motion op** — the one that actually caused the T-posed retarget output — is fixed and
verified persisted: `target_pelvis_bone: root_x`, saved 21:33.

---

## 🧭 DECISIONS WAITING ON YOU

1. **Material target confirmation.** The pawn uses `SK_Melusina_V2_Body` + 4 wardrobe garments.
   Confirm material work is aimed there and not at the unused `SK_Melusina`.
2. **Canonical retarget folder.** Six-plus parallel folders hold the same mocap
   (`Mocap/`, `FemaleBardRetargeted{,_InPlace,_LocalAxes,_V1Pose}/`,
   `QuaterniusRetargeted{,_Test,_V2Fixed}/`, `SourceRetargeted/`). `Locomotion/` is de-facto
   canonical — the ABP binds it. Confirm and the rest become archive.
3. **Walk take** — record, or pay the UE5 Manny skeleton cost.
4. **7 un-imported mocap clips** — `Crumping`, `Curtsee`, `Dodge_002`, `Duck`,
   `LittleDance_002`, `Stab_001`, `Twirl`. Held until #1 is settled.

---

*Companions: `MELUSINA_ANIMATION_CLOSEOUT_2026-08-24.md` (findings + corrections),
`MELUSINA_NEXT_SESSION_PREP_2026-08-24.md` (detail + recipes).*
