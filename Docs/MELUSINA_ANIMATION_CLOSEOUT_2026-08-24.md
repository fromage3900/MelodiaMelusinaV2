# Melusina Animation — Session Closeout 2026-08-24

**Scope:** animation only (retargets, blendspaces, face). Materials/lookdev were owner-handled
and deliberately untouched, with one exception noted in §3 where an animation query produced
the material answer for free.

**Method:** mixed live-editor notes and on-disk evidence, captured during a single-writer session.
Runtime acceptance is only claimed where a fresh readback is explicitly cited. Where a claim was
made and later disproved in this same session, both are recorded.

---

## 1. Verification method — read this first

**Screenshot A/B comparison is NOT valid in this project.** `editor.capture_scene_preview`
returns stale frames from a previous call. Proven: `walk_t000.png`, `walk_t058.png` and
`run_t050.png` all hashed `405208e34689bb06b9bc9709b33a33bb` — three captures across *two
different animations* returning identical bytes.

This produced a false defect during the session. "The Walk clip is frozen" was drafted off
byte-identical captures and is **wrong**.

`editor.capture_anim_frames` is separately unusable for motion: in AnimBlueprint mode it does
not advance time, so frames come back byte-identical by design. It also leaks a rooted UObject
(`Assertion failed: !IsRooted()`).

**Use `animation_query.get_animated_bone_transform` instead.** It reads evaluated bone data, not
pixels. Example that settled the Walk question:

| bone `foot_l` | t=0 | t=0.58 |
|---|---|---|
| Z (height) | 3.24 — planted | 28.98 — lifted |
| Y (travel) | −15.26 | −34.74 |
| roll | −62.4° | −158.5° |

**P0 impact:** any gate that accepts a screen capture as visual evidence is accepting unreliable
evidence. Gates must assert on bone/curve data.

---

## 2. Retarget lanes — what works, what does not

| Lane | Status | Notes |
|---|---|---|
| Owner mocap → `RTG_Source_to_Melusina` | **WORKS** | Owner ground truth. 20 `A_Src_*` clips. |
| UE4 Mannequin → `RTG_UE4Mannequin_To_Melusina` | **REPAIRED this session** | See below. |
| Quaternius → `RTG_Quaternius_to_Melusina` | **NEVER WORKED** | Owner ground truth. Do not wire, automate, or import. |

### 2.1 The mannequin lane was deleted by accident

`03de1220` is titled *"docs: Material pipeline audit, PPV stack audit, and session handoff"* and
carried **44 asset deletions**, including the entire mannequin retarget path:
`RTG_UE4Mannequin_To_Melusina`, `IK_Melusina_Body`, `A_ThirdPerson{Idle,Walk,Run,Dash,Jump_End}`,
`BS_Melusina_Locomotion`.

`MELUSINA_ANIMATION_PIPELINE_REVIEW_2026-08-20.md` called those deletions *"a reorganisation, not
a loss"* and mapped the mannequin retargeter's replacement to `RTG_Quaternius_to_Melusina` — the
lane that has never worked. **That mapping is wrong and should not be trusted.**

Restored in `84f02466`.

### 2.2 Root cause of the T-pose: one bone name; correction still needs runtime proof

The restored retargeter emitted T-posed clips. Cause found by diffing it against the working
mocap retargeter:

| | `RTG_Mocap_to_Melusina_Current` (works) | `RTG_UE4Mannequin_To_Melusina` (was broken) |
|---|---|---|
| Pelvis → target bone | **`root_x`** | **`pelvis`** |

**Melusina's pelvis bone is `root_x`.** The mannequin retargeter pointed at `pelvis`, which does
not exist on her skeleton, so the FK chains never solved.

The source-side correction was attempted with a single `set_retarget_root_settings` call
(`target_pelvis_bone: root_x`). The 5-op stack and all 19 one-to-one chain mappings — including
full finger chains — were preserved in the saved asset (19,153 → 21,671 bytes).

This is not runtime acceptance: the live readback associated with this closeout still reported
`TargetPelvis=pelvis` against the target skeleton's `root_x`, with no `pelvis` bone. Root-motion
correctness therefore remains `NEED_EVIDENCE` until a fresh readback confirms `root_x` and a clean
PIE motion smoke passes.

### 2.4 CORRECTION — the T-pose owner actually hit was the Idle state, not the retargeter

**Owner ground truth, 2026-08-24 (late):** Melusina was still T-posing in-session. The cause was
that **the `Idle` state's animation was not proper**. Owner fixed it.

This is the correct root cause for the *observed* T-pose and it supersedes the framing above.
`Idle` is the state machine's **entry state** and where she spends most of her time, so a bad Idle
asset reads as "T-posing everywhere" even though the state machine, transitions and every other
state were wired correctly.

`MELUSINA_ANIMATION_PIPELINE_REVIEW_2026-08-20.md` had already recorded the warning —
*"the Idle state's SequencePlayer remains pointed at the pre-v22 asset; promotion to the v22 `cm`
variant is staged (repoint + Loop=true)"* — and this session read that line without connecting it
to the symptom. **Treat a staged/unpromoted entry-state clip as a first-class suspect for any
whole-body pose failure.**

Note the related contradiction still unresolved elsewhere in the docs: `ORCHESTRA_CONVERGENCE`
calls the v22 `cm` variant canonical, while `generated/melusina_animation_library.json` marks
`A_BL_Melusina_Idle_Loop_cm` **`legacy`** ("centimetre export is a direct-target rollback artifact;
it is not source-rig tagged"). Confirm which asset `Idle` now points at before trusting either doc.

**CONFIRMED 2026-08-24 21:33:** `Idle` now plays **`A_Melusina_Idle`** (previously
`A_Melusina_Idle_Mocap_RootX`), read back live via `get_state_info`.

### 2.3 Do not use `set_retargeter_rigs` to repoint a rig

It re-seeds default ops (5 → 9 observed) and the next retarget call crashed the editor inside
Monolith's HTTP handler. Change pelvis/root settings directly instead.

---

## 3. Face shape keys — RETRACTED AND CORRECTED

**The original §3 claimed the live pawn mesh had 0 morph targets and that promoting
`SK_Melusina_OLD` was the highest-value fix in the project. That was WRONG.**

The error: morph counts were read off `SK_Melusina` and assumed to be the pawn mesh, because this
project's docs describe it that way. `BP_MelusinaJRPGCharacter`'s `CharacterMesh0` was never
queried until 2026-08-24 21:40.

**Live truth:**

```
CharacterMesh0.SkeletalMesh = SK_Melusina_V2_Body   (120 morph targets)
CharacterMesh0.AnimClass    = ABP_Melusina_Current_C
```

| Mesh | Morphs | Materials | Used by the game? |
|---|---|---|---|
| **`SK_Melusina_V2_Body`** | **120** | 5 | **YES** |
| `SK_Melusina_OLD` | 69 | 35 | no |
| `SK_Melusina` | 0 | 33 | no |

**The face pipeline is complete and live.** The skeleton declares 120 curves; the pawn mesh carries
120 matching morph targets; UE binds them by name. No AnimBlueprint work, no mesh swap, no reimport.
Promoting `_OLD` would have been a **downgrade, 120 → 69**.

The material slot shift documented elsewhere is on `SK_Melusina` — **a mesh the game does not use**.
The pawn's look comes from `SK_Melusina_V2_Body` plus the four wardrobe garments
(`SK_Melusina_V2_{Shirt,Skirt,Boots,Accessories}`), all four verified mapped on the live Wardrobe
component and applied in `BeginPlay()`.

**Method lesson worth keeping:** every "X is missing" claim in this session that came from a doc
rather than a live query turned out to be false — face, wardrobe and UI all proved already built.
`ORCHESTRA_CONVERGENCE` says as much in its own headline. **Query the live object first.**

## 4. Locomotion + blendspace state

- `ABP_Melusina_Current` / `MelusinaLocomotion`: 7 states, 15 transitions, entry `Idle`.
- `Speed`, `bIsGliding` and `bRuntimeIsJumpWindup` are **all correctly wired**.
- **JumpWindup is not broken.** Both `Idle → JumpWindup` and `Locomotion → JumpWindup` read
  `bRuntimeIsJumpWindup`, not `bIsCrouched`. The Aug-20 review's "needs an owner call on
  bIsCrouched" is **stale** — it was fixed after that review. Crouch can stay disabled.
- `Animations/Locomotion/` holds the full set on the canonical skeleton: `A_Melusina_{Idle,Walk,
  Run,Sprint}` plus `_Mocap_RootX` variants and `JumpStart/JumpLoop/Land`.
- `A_Melusina_Walk_Mocap_RootX` verified healthy: 35 frames, 1.167 s @ 30 fps, `is_looping: true`,
  rate_scale 1.15, real stride amplitude (§1 table).
- `SprintSpeed = 630` in `MelodiaTraversalComponent.h:300`, matching the top blendspace sample.
  **The "714" figure is stale and appears in no live location** — no fix needed.

### 4.1 Retarget output sprawl — the real long-term blocker

The same mocap exists in six-plus parallel folders with none marked canonical:

`Mocap/` (20) · `FemaleBardRetargeted/` (16) · `FemaleBardRetargeted_InPlace/` ·
`FemaleBardRetargeted_LocalAxes/` · `FemaleBardRetargeted_V1Pose/` · `QuaterniusRetargeted/` ·
`QuaterniusRetargeted_Test/` · `QuaterniusRetargeted_V2Fixed/` · `QuaterniusAligned/` ·
`SourceRetargeted/` (3) · `MannequinRetargeted/`

The `_InPlace` / `_LocalAxes` / `_V1Pose` / `_V2Fixed` / `_Test` suffixes are the fingerprints of
repeated retarget attempts that were never resolved. **This — not a missing clip — is what makes
the library unusable long-term.** `Locomotion/` is the de-facto canonical set because the live ABP
binds it.

**Owner decision required:** confirm `Locomotion/` as canonical and archive the rest. Moving
`.uasset` files is Red-tier.

---

## 5. Owner mocap kit — un-imported clips

Source of truth: `C:\Users\froma\OneDrive - Humber Polytechnic\Recordings\Mocap\` (25 FBX).
Imported: 20 `A_Src_*`.

**Not yet imported (7):** `Crumping`, `Curtsee`, `Dodge_002`, `Duck`, `LittleDance_002`,
`Stab_001`, `Twirl`.

Held deliberately: importing into the §4.1 folder sprawl would add to the problem rather than
fix it. Import once a canonical destination is chosen.

Note: `Swim_Fwd_Loop` / `Swim_Idle_Loop` exist in UE but are **not** in the source folder — they
came from elsewhere and their provenance is unverified.

---

## 6. Tooling fix — melodia MCP live path was dead

`deploy/melodia_mcp_server.py::_monolith_call` sent dotted strings as the MCP **tool name**:

```python
"params": {"name": "animation_query.get_abp_info", "arguments": args}
```

Monolith exposes one tool per namespace and selects the operation via an `action` argument, so
that name matched nothing. Every dotted call failed closed to `None`, which callers reported as
`"ABP not found"` / `"Could not read nodes"` — indistinguishable from a genuinely missing asset.

Proven:

```
OLD: RPC-ERROR -32601 "Unknown tool: animation_query.get_abp_info"
NEW: OK {"asset_path":"...ABP_Melusina_Current","skeleton":"..."}
```

Fixed by splitting `<tool>.<action>` and sending `{"action": …, "params": …}`.

**This affected the whole file, not just the animation validators** — `blueprint_query.get_cdo_properties`
included. **P0 impact: `monolith_static` lists `melodia_animation_validate_bindings` and
`melodia_animation_validate_state_machine` as gate implementations.** Those gates were silently
failing rather than validating. Any prior green from them is void.

---

## 7. Build / environment

- `BS_GodFileEditor` **builds clean** (Succeeded, 0 errors, 35.9 s) after disabling Claireon in
  `BS_GodFile.uproject` (`32c4583e`). Claireon was failing with `C1076` heap / `C3859` PCH even
  under `-SingleThread -NoUBA`, blocking every live P0 gate.
- **Claireon is not on the critical path.** The `:9316` Monolith endpoint (1402 tools) is served by
  `Plugins/Monolith`, a separate plugin. Verified live: editor up with 1402 tools and zero Claireon
  modules loaded.
- `Plugins/Claireon` is a 3.3 GB checkout of `believer-oss/Claireon` with its own `.git`. Local AWS
  SigV4 work is preserved on that repo's `local/aws-sigv4` branch. The parent `.gitignore` entry is
  **written but uncommitted** — the pre-commit hook protects `.gitignore` and wants owner sign-off.
- UBT refuses to build while stale `*.patch_*` Live Coding artifacts exist. 43 were moved to the
  session scratchpad; that is what unblocked the editor build.

---

## 8. What remains for P0 + battle integration

### Animation-side — ready
- Locomotion state machine wiring: **done**, all three runtime flags correct.
- Walk/Run/Sprint/Idle clips: **present and healthy** on the canonical skeleton.
- Battle montages present (11): `AM_Melusina_{Death, Hit_Chest, Hit_Head, Spell_Shoot,
  Sword_Attack, Roll, Interact, PickUp, Idle_Dance, Idle_Talk}`, `AM_MUAL_Source_Idle`.

### Animation-side — open
1. **Canonical folder decision** (§4.1) — blocks the 7 mocap imports and any library hygiene.
2. **Face mesh decision** (§3.2) — blocks all facial animation and lipsync.
3. Graph hygiene in `ABP_Melusina_Current`: orphaned `BlendSpacePlayer_0` (bound to
   `RuntimeGroundSpeed`, zero connections), orphaned `Slot_1/2/3`, dead `CharacterProperties`
   chain in `BlueprintThreadSafeUpdateAnimation`.
4. Nine `ABP_Melusina*` assets exist; only three are real (`_Current`, `Hair`, `WaterHair`).

### Not animation, but blocking P0 gates
- Gates `rhythm_owner`, `hud_single_writer`, `rhythm_grade_to_result`, `wardrobe_equip_roundtrip`,
  `wardrobe_gameplay_hook`, `music_world_key` remain OPEN and need PIE.
- Any gate evidence produced by screen capture must be re-derived per §1.
- Any gate green from the two melodia validators must be re-run per §6.

---

## 9. Uncommitted at session close

| Path | State |
|---|---|
| `deploy/melodia_mcp_server.py` | +17/−2, the §6 fix — **on disk, uncommitted** |
| `Content/.../Retarget/RTG_UE4Mannequin_To_Melusina.uasset` | pelvis fix saved by editor, uncommitted |
| `Content/.../MannequinRetargeted/A_Mann_Walk.uasset` | untracked, produced mid-crash, **unverified** |
| `Content/.../MannequinRetargeted/A_MannFix_Walk.uasset` | staged by UE source control |
| `.gitignore` | Claireon ignore rule written, blocked on hook sign-off |

Also restored in `84f02466` but of doubtful value: `A_ThirdPerson*` clips bound to
`SK_MelusinaRigARP_V2Test_Skeleton`, a dead ARP experiment rather than the canonical skeleton.
Candidates for revert.

---

## 10. Corrections issued this session

Recorded so they are not re-derived from stale docs:

1. **G: drive is not corrupt.** `git fetch gdrive main` succeeds. The `bad tree object` error comes
   from broken `refs/air-checkpoints/…` and `refs/cline/checkpoints/…` — throwaway AI-tool refs. A
   bare `git fetch` tries all refs and aborts on one bad one. Fetch named branches instead.
2. **JumpWindup was already fixed** — see §4. The Aug-20 "owner call needed" is stale.
3. **Walk and Idle are not missing** from the project — only from the owner's source FBX kit.
4. **The Walk clip is not frozen** — that was the §1 capture bug.
5. **The mannequin ThirdPerson lane did not "just work"** on restore; it needed the §2.2 pelvis fix.
