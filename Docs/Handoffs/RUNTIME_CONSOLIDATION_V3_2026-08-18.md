# Runtime Consolidation v3 — Duplicate Runtime Eliminated

**Date:** 2026-08-18 (evening session)
**Status:** Core consolidation DONE and verified on disk. One content-authoring step remains (enemy roster).

## The duplicate runtime, resolved

`MelodiaIntegrationMap.umap` WorldSettings had `DefaultGameMode = BP_MelodiaGameMode` — the
**quarantined** `AMelodiaGameMode` (`NotBlueprintable, NotPlaceable`, Decision 016). Every other
Melodia map already used `BP_MelodiaJRPGGameMode`. On that one map both paths ran at once:
the quarantined GameMode spawned `WBP_Battle_Rhythm` while `UMelodiaUIBridgeSubsystem` spawned
`BP_MelodiaBattleUI` — two battle UIs, two authorities.

### Changes shipped

1. **Map GameMode flipped**: `MelodiaIntegrationMap` → `BP_MelodiaJRPGGameMode` (verified via
   on-disk binary grep — only `/Game/MelodiaIntegration/Blueprints/BP_MelodiaJRPGGameMode` remains).
2. **Rhythm HUD wired into the JRPG path** — `MelodiaUIBridgeSubsystem.cpp`:
   `CreateBattleUIInternal` now also spawns the native highway HUD
   (`/Game/Melodia/UI/WBP_Battle_Rhythm`, `UMelodiaRhythmHUDWidget`) at Z=90 and calls
   `UMelodiaRhythmCombatSubsystem::BindRhythmHUD`. `RemoveBattleUIInternal` unbinds and removes it.
   `.cpp`-only change (tracked via anonymous-namespace `GBridgeRhythmHUD`), closed-editor build
   succeeded (26 s, EXITCODE=0). **Do not rely on a Live Coding patch — the fix is in the DLL on disk.**
3. **Encounter tag dedup**: 4 interaction actors shared tag `melodia_smoke_encounter`; the external
   bridge requires exactly one. Tag now only on `BP_InteractionBattle_2` (map saved).
4. **Infinite loop did NOT reproduce** under `BP_MelodiaJRPGGameMode` (direct `StartBattle` test):
   battle UI created, input context → Battle, zero `Infinite loop` errors. The 16:19 loop was likely
   aggravated by the duplicate-GameMode HUD fight. `battle_encounter` gate stays FAIL until the
   canonical path passes (see below).

## Melusina comparison (verified via reflection)

| | `bp_melusina` (canonical pawn) | `BP_MelusinaJRPGCharacter` (JRPG battle) |
|---|---|---|
| Parent | `MelodiaSmokeCharacter` | `BP_JRPGCharacterBase` |
| Mesh | `SK_Melusina` (old model, proper MI materials) | **None set** on `CharacterMesh0` (V2 pieces exist under `Outfits/V2/`, assigned via Wardrobe/Outfit at runtime) |
| AnimClass | `ABP_Melusina_Current` | **None** — battle Melusina plays no runtime anims |
| Extras | water hair, camera rig | 24 comps: VFX set, Wardrobe, hair |

This is the "JRPG Melusina has no proper runtime animations" finding: its skeletal mesh component
has neither mesh nor AnimClass at the Blueprint level.

## Remaining blocker for the canonical battle trigger

`StartTaggedJRPGBattle('melodia_smoke_encounter')` now finds exactly one actor but rejects:
**"tagged battle actor has no authored enemy roster."** `enemyList` on all four interaction actors
is empty. Shape (from `describe_cdo_schema`): `enemyList: TArray<S_EnemyUnitSpawnDataList>` where
each entry has a TMap with key `S_EnemyUnitSpawnData{spawnChance, minLevel, maxLevel}` and value =
enemy unit class (e.g. `BP_WeakEnemy`).

**Manual fix (2 min in editor):** select `BP_InteractionBattle_2` → Details → `enemyList` → add one
entry → spawnChance 1.0, min/max level 1/5, class `BP_WeakEnemy`. ⚠️ Do NOT script this:
both Python `set_editor_property` (can't nativize user-defined-struct arrays) and Monolith
`mesh.set_actor_properties` (JSON import assert → editor crash, Array.h:1339) failed hard.
Also note: `narrative.StartBattle` rejects with `MissingRuntime` unless a Quill interpreter is
active — the canonical in-game entry is dialogue, or the encounter trigger overlap
(`BP_MelodiaEncounter_FirstDream`, EncounterId `melodia.fixture.encounter.first_dream_repeatable`).

## Editor stability lessons (this session)

- **Never `load_object` a `.umap` and then `load_level` the same map** — the held reference trips
  "Old level package not cleaned up by garbage collection" fatal at `EditorServer.cpp:2544`.
  Cost two editor instances.
- Live Coding patches are **in-memory only**; a restart silently reverts to the on-disk DLL.
- Crash-recovery "Restore Packages" modal blocks Monolith; dismiss via UI, never kill the editor.

## Melusina IS the runtime unit now (2026-08-18 late evening, verified in PIE)

The template actor was never coming from the GameMode — it came from **two** leftover defaults:

1. `BP_SirMelodiousPlayerUnit::exploreCharacter` was `BP_JRPGCharacter` (template pawn).
   → now `/Game/MelodiaIntegration/Blueprints/BP_MelusinaJRPGCharacter`. All 11 animation
   slots on the unit repointed to her montages (`AM_Melusina_Sword_Attack`, `_Hit_Chest`,
   `_Hit_Head`, `_Death`, `_Idle_Dance`, `_Interact`, `_Spell_Shoot`, `_Roll`;
   idle sequence `A_Q_Melusina_Idle_Loop`). Saved.
2. `BP_MelodiaJRPGPlayerController::playerUnits` (CDO TMap) held the four STOCK template
   units, Mage first — so the possessed pawn was `BP_MageCharacter`. The party-switch key
   only cycled stock units. → now the map contains exactly one entry:
   `BP_SirMelodiousPlayerUnit`. Saved via `save_packages` (note: `save_asset` failed while
   PIE was up — use `save_packages` with the package path).

**PIE-verified (log + runtime reflection):** `Game class is 'BP_MelodiaJRPGGameMode_C'`,
possessed pawn `BP_MelusinaJRPGCharacter_C`, body `SK_Melusina_V2_Body` on
`SK_Melusina_Skeleton`, wardrobe slots (shirt/skirt/boots/accessories, leader pose =
CharacterMesh0) and `WaterHairMesh` all live. Hide/unhide test confirmed the on-screen
Melusina IS the possessed pawn. Music clock alive on `BP_BattleController_2`.

### Known remaining gap: idle T-pose (pre-existing, not a regression)

Her AnimClass is now `ABP_Melusina_Current` (full locomotion state machine,
`BS_Melusina_Locomotion_Hybrid`, KawaiiPhysics; thread-safe update casts only to
`Character`, so the JRPG pawn is compatible). Anim instance runs, skeleton matches,
but the AnimGraph outputs ref pose in explore.
⚠️ `ABP_Melusina_JRPG_V2` and `ABP_Melusina_Current_V2` both T-pose — their sequences
target `SK_MelusinaRigARP_V2Test_Skeleton`, NOT `SK_Melusina_Skeleton`. Do not use them.
The stock template pawn has NO mesh/AnimClass at CDO either — template assigns anim at
runtime somewhere in the PC's `SetExploreCharacter`/spawn chain (200+ nodes, not yet
traced). Next step: trace how the template plays `idleAnimation` on the explore pawn and
hook Melusina's idle the same way, or debug why `MelusinaLocomotion` state machine
outputs ref pose with velocity 0.

## Next work

1. Trace the template's runtime idle-animation path (`SetExploreCharacter` in
   `BP_MelodiaJRPGPlayerController`) and wire Melusina's idle. T-pose is cosmetic-only;
   mechanics, battle triggers, rhythm HUD are unaffected.
2. Author the enemy roster (above), then run `battle_encounter` gate via canonical path and record.
3. Retire `BP_MelodiaGameMode` once the JRPG path is battle-verified (owner sign-off required;
   untracked/unrecoverable).
4. `BP_MelodiaBattleUI` (bridge overlay) vs `WBP_Battle_Rhythm` (HUD) — consider converging to one
   widget (the proposed `WBP_MelodiaBattleHUD_V3`) once battle loop is green.

## UPDATE 2026-08-18 ~21:25 — T-pose FIXED and PIE-verified

**Root cause found:** `ABP_Melusina_Current` AnimGraph was mid-surgery — `OutputPose` was fed
only by the `MelusinaLocomotion` state machine, while the `Slot 'DefaultSlot'` → LocalToComponent →
KawaiiPhysics → CopyBone → ComponentToLocal chain ended unconnected, so montages never rendered
and idle output was ref pose.

**Fix (2 connections, compiled clean, saved to disk 21:13):**
- `StateMachine_1.Pose → Slot_0.Source`
- `ComponentToLocalSpace_0.Pose → Root_0.Result`
(Stray `Slot_1/2/3` + `BlendSpacePlayer` left unconnected — harmless leftovers, do not delete.)

**PIE verification (MelodiaIntegrationMap):** pawn `BP_MelusinaJRPGCharacter_C`, mesh
`SK_Melusina_V2_Body`, AnimClass `ABP_Melusina_Current_C`; `hand_r` world position oscillates
between probes (idle breathing, not ref pose); HighResShot
`Saved/Screenshots/WindowsEditor/HighresScreenshot00002.png` shows Melusina in a natural
third-person idle in the Zen Forest encounter map. Not a T-pose.

**New landmines recorded this session:**
- 228 uassets + 43 umaps in `Content/` are READ-ONLY; `save_packages` on a read-only uasset
  FATALS the editor ("Error saving", GetLastError 183). Run `attrib -r` on any asset before saving.
- Relaunch booted the editor into the Orrery main-menu map, not MelodiaIntegrationMap — always
  `load_level` the integration map before `start_pie`.
- Do NOT `load_object` a `.umap` before `load_level` (fatal).
- Bone probes must be separate `run_python` calls — `time.sleep` blocks the game thread.

Item 1 of Next work is DONE. Remaining: enemy roster on `BP_InteractionBattle_2` → `battle_encounter` gate.

## UPDATE 2026-08-18 ~23:40 — idle T-pose actually fixed (second pass)

The 21:13 fix reconnected the AnimGraph chain but the owner correctly reported she was
STILL T-posed. Real root cause was one level deeper: the `Idle` state's SequencePlayer
was disconnected (same mid-surgery pattern), and the sequence it nominally referenced —
`Locomotion/A_Melusina_Idle_Mocap_RootX` — contains near-ref-pose data (hand_r at
(-64,-19,139) vs ref-pose (-74,13,126)). `QuaterniusRetargeted_V2Fixed/A_Q_Melusina_Idle_Loop`
is ALSO unusable on this skeleton — its tracks are in a broken space (hand z=7608 → mesh
flung 76m away, renders as invisible).

**Fix:** Idle state now plays `Locomotion/A_Melusina_Idle` (2.63s, the sequence inside her
working `AM_Idle` montage; hand at (-36,29,82) = arms down). Rewired via
`animation set_state_animation`, compiled, saved. PIE-verified with unlit+lit HighResShots:
`Saved/Screenshots/WindowsEditor/HighresScreenshot00008.png` — natural standing idle,
hair/dress/wardrobe all following, pawn = `BP_MelusinaJRPGCharacter_C_1`.

**Diagnostic lessons:**
- `animation sample_pie_anim_instance` reports the ACTIVE STATE even when the state's
  inner player is disconnected — "state = Idle" does NOT mean "idle is playing".
- Verify a sequence by `get_animated_bone_transform` on `hand_r` vs the skeleton ref pose
  (`get_bone_ref_pose`): ref pose hands are at (±74.5, 12.8, 126.2) on SK_Melusina_Skeleton.
- The red mannequin in this map is `BP_NPC_2` (template NPC, harmless, spams a
  BP_InteractionDetector Accessed None error — separate cleanup item).

---

## 2026-08-19 (00:15–00:55 EDT) — MelusinaLocomotion per-state sweep & remaining-state fixes

Continuation of the Idle fix above: audited every other state in `MelusinaLocomotion`
(ABP `/Game/Melodia/Characters/Melusina/ABP_Melusina_Current`), validated sequences via
`animation get_animated_bone_transform` on `hand_r` vs ref pose (-74.5, 12.8, 126.2),
fixed the two states with bad/missing data, compiled, saved (no read-only flags present).

### Per-state verdicts

| State | Player found | Sequence | Verdict | Action |
|---|---|---|---|---|
| Idle | SequencePlayer | `A_Melusina_Idle` (set 08-18) | GOOD (already fixed) | none |
| JumpStart | SequencePlayer | `A_Melusina_JumpStart_Mocap_RootX` | VALID — animates (hand moves (-55,-12,112)→(-17,1,63)), plausible windup | none |
| Airborne | SequencePlayer | `A_Melusina_JumpLoop_Mocap_RootX` | VALID — animates, looping, mid-air-ish pose | none |
| Land | SequencePlayer | `A_Melusina_Land_Mocap_RootX` | VALID — animates (hand (-24,10,75)→(-63,-17,107)) | none |
| **Glide** | **none — StateResult only, fully disconnected** | — | BROKEN (no player node) | **REWIRED** → `A_Melusina_JumpLoop_Mocap_RootX` via `animation set_state_animation` (nearest validated airborne loop; not a purpose-authored glide) |
| Locomotion | BlendSpacePlayer `BS_Melusina_Locomotion` (NOT `BS_Melusina_Locomotion_Hybrid`) | see below | sample 0 broken, rest valid | sample 0 swapped |
| JumpWindup | SequencePlayer | `A_Melusina_JumpStart_Mocap_RootX` | VALID (same data as JumpStart) | none |

### Blendspace `Animations/BS_Melusina_Locomotion` (1D, Speed 0–750, 4 samples)

| # | Speed | Sequence | Verdict |
|---|---|---|---|
| 0 | 0 | ~~`A_Melusina_Idle_Mocap_RootX`~~ → **`A_Melusina_Idle`** | was ref-pose data (hand (-64,-19,139)); **REPLACED** via `animation edit_blendspace_sample` (param name is `anim_path`, not `anim_asset_path`) |
| 1 | 180 | `A_Melusina_Walk_Mocap_RootX` | VALID data but **byte-identical to Run** (same hand_r transform at t=0.1 and t=0.583) — walk and run will look the same; cosmetic, not fixed |
| 2 | 420 | `A_Melusina_Run_Mocap_RootX` | VALID (see #1 duplicate note) |
| 3 | 630 | `A_Melusina_Sprint_Mocap_RootX` | VALID, distinct (hand (-7.5,33,97)) |

Sibling finding: non-mocap `A_Melusina_Run` and `A_Melusina_Sprint` are also
byte-identical to each other. So gait variety across the speed axis is thin in both
families. Not a blocker; noted for whoever authors gait variety later.

### Build/save
- `compile_blueprint` on ABP → UpToDate, 0 errors/warnings.
- `save_asset` ABP + BS (both were dirty, both saved). `list_dirty_packages` = 0 after.

### PIE verification
- Pawn confirmed `BP_MelusinaJRPGCharacter_C_1`, AnimClass ABP_Melusina_Current, mesh SK_Melusina_V2_Body.
- `HighresScreenshot00009.png` — natural standing idle (not T-pose), clear framing. GOOD.
- Movement via `add_movement_input` over slate tick worked twice (y 300→883, then more),
  but `HighresScreenshot00010–00014` all land with the camera clipped behind a wall or the
  pawn wedged in the corner at (733,-523) — no clean mid-walk glamour shot obtained.
- `sample_pie_anim_instance` while pawn had velocity reported active_state **Idle** every
  time — i.e. the machine appears to NOT leave Idle into Locomotion under movement input.
  This matches tonight's earlier warning that state names ≠ what's playing; needs a look at
  the Idle→Locomotion transition rule (unproven: could also be sampling-timing artifact).
- New PIE hazard discovered: the pawn's `PawnInputComponent0` (EnhancedInputComponent) can
  end up **inactive** in PIE, silently making `add_movement_input` a no-op
  (`velocity` stays 0 though the world ticks). `ic.activate()` restored movement. Check
  `ic.is_active()` before trusting "injection did nothing" conclusions.

### Still unproven / open
- Whether Idle→Locomotion (and jump-chain) transitions fire in live play — needs owner playtest.
- Glide has no authored glide animation; JumpLoop is a placeholder stand-in.
- Walk==Run and Run(non-mocap)==Sprint duplicate data — gait variety is authored-thin.
