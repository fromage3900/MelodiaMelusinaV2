# Melusina Animation Pipeline — Review 2026-08-20

**Method:** live editor, one writer, Monolith on :9316. Every claim below is a live query or a
source line — nothing is inferred from documentation.
**Authority:** [`../../PROJECT.md`](../../PROJECT.md) ·
[`ORCHESTRA_CONTRACT_2026-08-20.md`](ORCHESTRA_CONTRACT_2026-08-20.md)

---

## Verdict

The rig, the skeleton, the blendspace and the physics chain are in good shape. **The state
machine is not.** Three of its seven states are unreachable because the variables their
transitions depend on are never assigned anywhere in the Animation Blueprint, and the one
blendspace player that *is* correctly bound to real speed is orphaned outside the pose chain.

This is the same disease as the rest of the project: **the parts are built, the wire between
them is missing.**

---

## 1. What is actually live

| | |
|---|---|
| Pawn | `/Game/Melodia/Characters/Melusina/BP_Melusina` |
| Mesh | `SK_Melusina` — **465 bones**, matches the contract |
| Anim class | `ABP_Melusina_Current_C` |
| Skeleton | `SK_Melusina_Skeleton` |
| ABP parent | `UMelodiaLocomotionAnimInstance` (C++, MelodiaCore) |
| Graphs | `AnimGraph`, `BlueprintThreadSafeUpdateAnimation`, `EventGraph` |
| State machine | `MelusinaLocomotion` — 7 states, 13 transitions, entry `Idle` |

### Pose chain (AnimGraph, output-connected)

```
StateMachine "MelusinaLocomotion"
  -> Slot 'DefaultSlot'
  -> Local To Component
  -> Kawaii Physics        (root: c_kilt_master_x  -- skirt, not hair)
  -> Copy Bone             (head_x -> eyes)
  -> Component To Local
  -> Output Pose
```

That chain is clean and correct. Hair is handled separately (`ABP_Melusina_Hair`,
`ABP_Melusina_WaterHair`, plus `UMelodiaHairComponent` attaching to `head_x`), which matches the
documented architecture — body and hair share zero bone names, so Copy Pose cannot work.

---

## 2. Defect A — three states are unreachable

`get_abp_variables` returns 12 Blueprint variables. Every `Set` node in the entire ABP is
enumerated below (16 total, from `search_nodes`):

| Graph | Variables actually assigned |
|---|---|
| `BlueprintThreadSafeUpdateAnimation` | `Velocity`, `Acceleration`, `bIsMoving` |
| `EventGraph` | `VFX_SparkleRate`, `VFX_SwingEnergy`, `VFX_MotionEnergy`, `VFX_LandPulse`, `WasInAir`, `bIsCrouched` |

**Never assigned anywhere: `Speed`, `bIsGliding`, `bJumpWindup`.**

Now the transitions that depend on them:

| Transition | Rule | Status |
|---|---|---|
| `Idle → Locomotion` | `Speed > 10.0` | **DEAD** — `Speed` is never set, so it is always 0 |
| `Airborne → Glide` | `bIsGliding` | **DEAD** — never set |
| `Idle → JumpWindup` | `bIsCrouched` | Live, but see Defect C |
| `Locomotion → JumpWindup` | `bIsCrouched` | Live, but see Defect C |
| `Idle/JumpStart/Airborne → …` | `bRuntimeIsInAir`, `bRuntimeIsGrounded` (C++) | Live and correct |
| `Land → …` | `WasInAir` | Live |

### Consequence

**Melusina cannot enter the `Locomotion` state.** `Idle → Locomotion` is the only entry, and its
condition can never be true. Walking, running and sprinting are unreachable from the state
machine regardless of movement input.

**Melusina cannot enter the `Glide` state**, which matters directly: `Glide` is one of the three
wardrobe traversal capabilities and the one wired to the new money-pouch Resonant Form
(2026-08-20). The animation half of that feature cannot play.

This is consistent with the project record — the V2 rebuild plan's step 10 ("Run PIE at speeds
0 / 150 / 180 / 300 / 420 / 540 / 630; inspect idle, walk, run, sprint…") is still **OPEN**.
Locomotion has never been PIE-verified.

---

## 3. Defect B — the correctly-bound blendspace is orphaned

`AnimGraphNode_BlendSpacePlayer_0` plays `BS_Melusina_Locomotion_Hybrid` and its `X` pin is
**property-bound to `RuntimeGroundSpeed`** — the C++ value that carries real speed. That binding
is exactly right.

It has **zero connections** (`connected_pins: []`). It is not in the pose chain and never
evaluates.

The blendspace that *is* in the chain, `AnimGraphNode_BlendSpacePlayer_2` inside the `Locomotion`
state, appears in no pin-binding record — its `X` is unbound and defaults to 0. So even if
Defect A were fixed and `Locomotion` became reachable, it would play the slowest sample.

Also orphaned in `AnimGraph`: `AnimGraphNode_Slot_1`, `_2`, `_3` — three unconnected duplicate
slot nodes.

---

## 4. Defect C — `bIsCrouched` drives jump windup

Both `Idle → JumpWindup` and `Locomotion → JumpWindup` are gated on `bIsCrouched`, while the
purpose-named `bJumpWindup` variable exists and is never used.

Either the wrong variable was wired, or crouch is deliberately doubling as a jump-windup tell.
The naming says the former. **This one needs an owner call, not a guess** — it is a design
question, not a defect I can settle from the graph.

---

## 5. Defect D — duplicate dead logic in ThreadSafeUpdate

`BlueprintThreadSafeUpdateAnimation` contains two copies of the same computation:

| Chain | Source | Connected to entry? |
|---|---|---|
| `VariableSet_4 → _6 → _7` | `PawnVelocity`, `PawnAcceleration` (C++) | **Yes — live** |
| `VariableSet_0, _2, _3` | `CharacterProperties.Velocity`, `.InputAcceleration` | **No — dead** |

The dead chain reads from a different source than the live one. It is an older implementation
left behind, plus its 6 supporting math/property-access nodes. Harmless at runtime, but it makes
the graph misleading to read and is exactly the kind of thing that produces a wrong fix later.

---

## 6. Asset topology — 43 deletions

> **Resolved same day.** These were committed by the owner in `03de1220`. The section below
> described them while still uncommitted; the "decide and commit deliberately" call has been made
> and the canonical-replacement mapping is the part that still matters.

`git status` shows **43 deleted Melusina animation assets** in the working tree, unstaged:
`ABP_Melusina`, `IK_Melusina_Body`, `RTG_UE4Mannequin_To_Melusina`, `BS_Melusina_Locomotion`,
both `V2Test` ABPs, 22 `AM_` montages and 17 `A_` sequences.

**These are a reorganisation, not a loss.** Canonical replacements exist and are live:

| Deleted | Canonical replacement |
|---|---|
| `Melusina/ABP_Melusina` | `Melusina/ABP_Melusina_Current` |
| `Melusina/IK_Melusina_Body` | `Mocap/Retarget/IK_Melusina_Body_Current` |
| `Melusina/Retarget/RTG_UE4Mannequin_To_Melusina` | `Mocap/Retarget/RTG_Mocap_to_Melusina_Current`, `RTG_Quaternius_to_Melusina` |
| `V2Test/BS_Melusina_Locomotion` | `Animations/BS_Melusina_Locomotion_Hybrid` |

**But the deletions are uncommitted**, which makes the state fragile in both directions: a
`git checkout .` resurrects 43 stale assets, and a careless `git add -A` makes the removal
permanent without review. Decide and commit deliberately.

### ABP proliferation

Nine `ABP_Melusina*` assets exist:

- `Melodia/Characters/Melusina/ABP_Melusina_Current` ← **live**
- `…/ABP_Melusina_Current_BACKUP_20260729`
- `…/ABP_Melusina_Current_Rollback`
- `…/Hair/ABP_Melusina_Hair`, `…/Hair/ABP_Melusina_WaterHair` ← legitimate, separate rig
- `…/_Archive/ABP_Melusina`, `…/_Archive/FromCharactersMelusina/ABP_Melusina`
- `Content/Characters/Melusina/ABP_Melusina` ← duplicate root tree
- `Content/Experiments/MelodiaJRPG/ABP_Melusina_JRPGPresentation`

Two are real (`_Current` + the hair pair). The rest are backups, archives and a duplicate tree.
This is the animation-pillar version of the convergence problem.

---

## 7. Pawn composition

> ## ⚠ CORRECTION 2026-08-20 (later) — THIS SECTION EXAMINED THE WRONG PAWN
>
> Section 7 below inspects `/Game/Melodia/Characters/Melusina/BP_Melusina`. **That is not the
> live pawn.** `BP_MelodiaJRPGGameMode` sets **`BP_MelusinaJRPGCharacter_C`**
> (`/Game/MelodiaIntegration/Blueprints/BP_MelusinaJRPGCharacter`) as its default pawn, and
> `BP_Melusina` has zero references and is placed in no level.
>
> Everything §7 concluded about missing components is therefore **wrong**. On the real pawn:
>
> | Claim in §7 | Actual state on `BP_MelusinaJRPGCharacter` |
> |---|---|
> | No `MelodiaWardrobeComponent` | **PRESENT** — component `Wardrobe` |
> | No `MelodiaTraversalComponent` | **PRESENT** — component `MelodiaTraversal` |
> | `bRequireCapabilityProviderForGlide` defaults false | **Set to `True`**, context `active_traversal_context` |
> | Sprint 714 vs blendspace max 650 disagree | **Agree** — live `SprintSpeed = 630`, exactly the top blendspace sample. The 714 figure came from a stale ledger note. |
>
> **Consequence for the money pouch:** of the four blockers §8 listed, three never existed and the
> fourth (`bIsGliding` never assigned) was fixed in the addendum. The wardrobe→Glide chain is
> complete pending PIE.
>
> §7 is left unedited below as the record of the error. Read it as a description of an orphaned
> Blueprint, not of the game.

### 7a. The orphaned `BP_Melusina`

| Component | Class | Note |
|---|---|---|
| `CharacterMesh0` | `SkeletalMeshComponent` | `SK_Melusina`, **not** `SK_Melusina_V2_Body` |
| `WaterHairMesh` | `SkeletalMeshComponent` | child of CharacterMesh0 |
| `WaterHairFlipCache` | `GeometryCacheComponent` | |
| `WaterHairDripFX` | `NiagaraComponent` | |
| `Outfit` | **`MelodiaOutfitComponent`** | the compat-only component marked DEAD in the convergence audit |
| — | `MelodiaWardrobeComponent` | **ABSENT** |
| — | `MelodiaTraversalComponent` | **ABSENT** |

Three consequences:

1. **The V2 mesh promotion is still open**, exactly as `MELUSINA_V2_REBUILD_AND_INFINITY_NIKKI_WARDROBE_PLAN_2026-08-14.md` recorded. The pawn still uses the original `SK_Melusina`.
2. **The pawn carries the deprecated outfit component and not the owner one.** This is the concrete form of the convergence audit's finding that nothing outside `Plugins/MelodiaWardrobe/` calls `UMelodiaWardrobeSubsystem`.
3. **There is no traversal component**, so `bIsGliding` has no writer on this pawn even in C++ — a second, independent reason Glide cannot play.

---

## 8. What this means for the 2026-08-20 wardrobe work

The money-pouch Resonant Form (`form.first_resonance_echo` → `Glide`, gated on
`challenge.first_resonance_echo.completed`) is **correct data on an unreachable path.** Four
things stand between it and an observable effect, all independent:

| # | Blocker | Where |
|---|---|---|
| 1 | No `MelodiaWardrobeComponent` on the pawn | `BP_Melusina` |
| 2 | No `MelodiaTraversalComponent` on the pawn | `BP_Melusina` |
| 3 | `bRequireCapabilityProviderForGlide` defaults **`false`** | `MelodiaTraversalComponent.h:208` |
| 4 | `bIsGliding` never assigned in the ABP | `ABP_Melusina_Current` |

Blocker 3 is worth calling out: with that flag false, the capability is never consulted, so the
outfit would grant nothing even with components attached. The header comment says as much —
"set this true so input and Blueprint requests share the same capability gate."

None of this invalidates the data authored today; it defines the remaining path.

---

## 9. Recommended order

Smallest, highest-certainty fixes first. Each is independently verifiable.

| # | Fix | Effort | Unblocks |
|---|---|---|---|
| 1 | Bind `Speed` — either set it from `RuntimeGroundSpeed` in ThreadSafeUpdate, or repoint the `Idle → Locomotion` rule at `RuntimeGroundSpeed` directly | small | **walking at all** |
| 2 | Bind `BlendSpacePlayer_2.X` (inside `Locomotion`) to `RuntimeGroundSpeed` | small | walk/run/sprint blending |
| 3 | Delete the orphaned `BlendSpacePlayer_0` and `Slot_1/2/3` | small | graph legibility |
| 4 | Delete the dead `CharacterProperties` chain in ThreadSafeUpdate | small | graph legibility |
| 5 | Owner call on `bIsCrouched` vs `bJumpWindup` for the JumpWindup transitions | decision | correct jump tell |
| 6 | Add `MelodiaTraversalComponent` + `MelodiaWardrobeComponent` to `BP_Melusina`; set `bRequireCapabilityProviderForGlide = true` | medium | the whole wardrobe→traversal pillar |
| 7 | Set `bIsGliding` from `Traversal->IsGliding()` (the C++ already computes `bRuntimeIsGliding`) | small | Glide animation |
| 8 | Decide and commit the 43 deletions | decision | repo hygiene |
| 9 | V2 mesh promotion to `SK_Melusina_V2_Body` | medium | per the V2 plan, separately gated |

Items 1, 2 and 7 together make `wardrobe_gameplay_hook` observable. Item 6 is the prerequisite
for all of them mattering.

**None of this was changed in this pass.** This is a read-only review; the ABP was not modified.

---

## 10. Tooling note

`melodia_animation_get_runtime_abp` and `melodia_animation_validate_bindings` returned
`"BP not found"` / `"Could not read nodes"` for an ABP that Monolith reads correctly at the same
path (`animation_query.get_abp_info` succeeds). The wrapper in `deploy/melodia_mcp_server.py` is
not resolving what Monolith resolves. Worth a look before those validators are trusted in a gate
— `monolith_static` lists both as gate impls.


---

# Addendum — fixes applied and verified, 2026-08-20 (later same day)

The review above was read-only. This addendum records the fixes that were then **applied**, what
was verified by screenshot, and two corrections to the review itself.

## Fixes applied to `ABP_Melusina_Current`

All three landed, compiled **0 errors / 0 warnings**, and saved (660,681 → 672,062 bytes).

| # | Fix | How |
|---|---|---|
| 1 | `Speed` is now assigned | New `K2Node_PropertyAccess_4` (`RuntimeGroundSpeed`) → `Set Speed`, spliced into the live exec chain after `Set bIsMoving` |
| 2 | `bIsGliding` is now assigned | New `K2Node_PropertyAccess_5` (`bRuntimeIsGliding`) → `Set bIsGliding`, chained after `Set Speed` |
| 3 | `Locomotion` blendspace reads real speed | `AnimGraphNode_BlendSpacePlayer_2.X` pin-bound to `RuntimeGroundSpeed` |

Both new reads use genuine **Property Access** nodes, so the thread-safe update graph stays
thread-safe — not foreign-member VariableGets, which is the documented cause of
"Accessing an object reference is not thread-safe".

Verified live exec chain after the edit:

```
FunctionEntry -> Set Velocity -> Set Acceleration -> Set bIsMoving
             -> Set Speed        (<- RuntimeGroundSpeed)
             -> Set bIsGliding   (<- bRuntimeIsGliding)
```

**Consequence:** `Idle -> Locomotion` (`Speed > 10.0`) and `Airborne -> Glide` (`bIsGliding`) can
now both fire. Those were the two unreachable states in §2. This does **not** yet prove they fire
correctly at runtime — that needs PIE, which was not run.

## Screenshot verification

`Saved/Screenshots/Monolith/MelusinaLocoCheck/` and `.../AnimFrames/20260820_164938_*`.

| Capture | Blend param | Result |
|---|---|---|
| `walk300_001_t0.33.png` | 300 (Run) | Posed, coherent deformation |
| `A_idle_spd0_000_t0.50.png` | 0 (Idle) | Full body, standing, one leg forward |
| `D_sample630_000_t0.40.png` | 630 (Sprint sample) | Clear sprint pose in silhouette |

**What this proves:** the Melusina skeleton, the retargeted mocap clips, and the
`BS_Melusina_Locomotion_Hybrid` blendspace all evaluate correctly. Skirt, boots, hat and hair
deform together with no exploded geometry. The retarget is functioning.

**What it does not prove:** in-game locomotion. These are isolated preview-scene captures, not PIE.

## Correction 1 — the blendspace is NOT broken at 600

An intermediate capture at blend param 600 returned a T-pose, and I initially read that as an
interpolation defect between the 540 and 630 samples. **That conclusion was wrong.** The exact
630 sample rendered a correct sprint pose on a freshly launched editor, and the T-pose captures
were the 5th and 6th capture calls in a degraded session — see Correction 2. Treat the blendspace
as sound: 1D `GroundSpeed` 0→650 with 7 samples (Idle 0, Walk 150/180, Run 300/420, Sprint
540/630).

One genuine note remains: the ledger records sprint at **714 uu/s**, above the blendspace max of
**650**. That clamps rather than breaks, but the top sample and the movement component disagree.
Worth an owner decision, not a defect.

## Correction 2 — `capture_anim_frames` crashes the editor

`editor.capture_anim_frames` leaks a rooted UObject and brings the editor down with
`Assertion failed: !IsRooted()` (`UObjectBaseUtility.h:209`) on a later call.

Observed twice:
- Session A: 4 captures succeeded, then a `run_python` call asserted inside `HandleRunPython`.
- Session B: 1 capture succeeded, then the next `capture_anim_frames` asserted inside
  `FMonolithToolRegistry::ExecuteAction` — no Python involved.

The shared `!IsRooted()` assert across both paths points at the capture path rooting a preview
object and never unrooting it; the next allocation or GC then trips the assert.

**Practical rule until fixed: one `capture_anim_frames` call per editor session, then relaunch.**
Budget for it — do not chain captures.

This is a Monolith plugin bug (`Plugins/Monolith/Source/MonolithEditor/`), not an engine or
content problem, and it is worth fixing since capture is the project's main visual-evidence path.

## Still open from §9

Items 3–9 were **not** done: the orphaned `BlendSpacePlayer_0` and `Slot_1/2/3` remain, the dead
`CharacterProperties` chain remains, `bIsCrouched` vs `bJumpWindup` still needs an owner call, the
two components are still absent from `BP_Melusina`, `bRequireCapabilityProviderForGlide` is still
`false`, and the V2 mesh promotion is still open.

Fixing items 1, 2 and 7 (done here) removes the *animation-side* blockers to
`wardrobe_gameplay_hook`. The *pawn-side* blockers — no wardrobe component, no traversal
component, capability gate off — are untouched and still stand between the money pouch and an
observable Glide.

---
## 2026-08-20 (later) — Idle canonical +水 hair renderer + pawn source-of-truth

**Decisions:** `BP_MelusinaJRPGCharacter` (`Content/MelodiaIntegration/Blueprints/BP_MelusinaJRPGCharacter.uasset`) is the single OWNER pawn (Pillar 5, `ORCHESTRA_CONVERGENCE_2026-08-20.md`). `A_BL_Melusina_Idle_Loop` v22 ARP factory rebuild (`generated/melusina_animation_library.json:25`, `A_BL_Melusina_Idle_Loop_cm` / `A_BL_Source_Idle_Loop`) is canonical idle — prior origin/scaling issues were import-pipeline, not clip choice.

**Idle:** the `MelusinaLocomotion` `Idle` state's SequencePlayer remains pointed at the pre-v22 asset; promotion to the v22 `cm` variant is staged (repoint + Loop=true, single `capture_anim_frames` per session per known `!IsRooted()` Monolith bug).

**Water-hair renderer (long-term): Groom (Hair Strands) + Niagara `WaterHairDripFX`, not GeometryCache.** `WaterHairFlipCache` (`GeometryCacheComponent`) bakes and cannot react to wind/MPC/`bIsGliding`; the live groom path already exists — `Hair/ABP_Melusina_Hair`, `ABP_Melusina_WaterHair` + `UMelodiaHairComponent` on `head_x` (`ORCHESTRA_CONVERGENCE.md:Pillar 5` table: WaterHairMesh present, PIE `MELUSINA_HAIR_BOUND`). Keep `GeometryCache` disabled as fallback, don't delete until Groom parity in PIE. Material reads `MPC_Melodia_Palette` `AudioReactAmount`, not PPV slot 1 (per `MATERIAL_PIPELINE_AUDIT` / `PPV_STACK_AUDIT`).

**Pawn SoT verification:** `BP_MelodiaJRPGGameMode` DefaultPawnClass → `BP_MelusinaJRPGCharacter_C` (lives, 0 references on `Content/Melodia/Characters/Melusina/BP_Melusina` smoke pawn). `Wardrobe` + `MelodiaTraversal` + `bRequireCapabilityProviderForGlide=True` already on owner — convergence doc Pillar 5 correction.

**Remaining:** repoint idle SequencePlayer, disable `WaterHairFlipCache`, PIE + ledger `record_gate` for `wardrobe_gameplay_hook`/`music_world_key` (still OPEN).
