# P0 Integration Handoff — 2026-08-20

**Read first:** [`../../../PROJECT.md`](../../../PROJECT.md) (authority) ·
[`../ORCHESTRA_CONVERGENCE_2026-08-20.md`](../ORCHESTRA_CONVERGENCE_2026-08-20.md) (who owns what) ·
[`../ORCHESTRA_CONTRACT_2026-08-20.md`](../ORCHESTRA_CONTRACT_2026-08-20.md) (the seams)

**Purpose:** the three work fronts that remain before the P0 vertical slice is playable —
mana-drain skills, the WBP/HUD layer, and animation composition. Everything below is verified
against source or the live editor on 2026-08-20.

---

## Project state: locked in

The pawn is consolidated. There is now exactly **one runtime Melusina unit**.

| | |
|---|---|
| **The pawn** | `/Game/MelodiaIntegration/Blueprints/BP_MelusinaJRPGCharacter` |
| Parent | `BP_JRPGCharacterBase_C` — the TurnBasedJRPG combat authority |
| Set by | `BP_MelodiaJRPGGameMode` as default pawn |
| Anim class | `ABP_Melusina_Current` (fixed today — see §3) |
| Compile | **0 errors / 0 warnings** |

### What landed on it today

| Change | Detail |
|---|---|
| Removed `Outfit` (`MelodiaOutfitComponent`) | Second outfit authority, 0 references. Decision 044 supersedes it with `MelodiaWardrobeComponent`. Compile went `UpToDateWithWarnings` → `UpToDate`. |
| Added `WaterHairFlipCache` (`GeometryCacheComponent`) | `GC_MelusinaHairFlip_v22`, running/looping/interpolate/extrapolate all true, transform matched to source. Harvested from the retired pawn. |
| Added `ToggleOrreryMenu` + `ActiveOrreryWidget` | Full toggle graph copied and re-wired; creates `WBP_ComicOrrery`. Execution flow verified identical to source. |

Final size 433,407 bytes, saved and on disk.

### Deprecated units

Both tagged in asset metadata (`MelodiaStatus=DEPRECATED`, `MelodiaSupersededBy`,
`MelodiaDeprecationNote`) — visible in the content browser, non-destructive, reversible.

- `/Game/Melodia/Characters/Melusina/BP_Melusina` — parent `MelodiaSmokeCharacter` (a **smoke-test
  class**), 0 references, in no level. Decision 044 already records this pawn as retired.
- `/Game/Characters/Melusina/BP_Melusina` — parent engine `Character`, 0 references either
  direction, duplicate root tree.

**Deletion is Red-tier and was not performed.** Both are now feature-empty — everything unique was
harvested. They can be deleted whenever you sign off.

`BP_MelusinaSwordsman_Presentation` is **not** deprecated — it is the in-battle *unit*
(`BP_PlayerUnitBase_C`), a different role in the JRPG template, and is live.

---

## Front 1 — Mana drain skills (the economy)

### Status: fully specified, fully prototyped, **zero engine implementation**

| Layer | State |
|---|---|
| Design spec | **Complete** — [`../P0_VERTICAL_SLICE_SPEC.md`](../P0_VERTICAL_SLICE_SPEC.md) §1–§5 |
| Task ledger | **Complete** — [`../P0_TASK_LEDGER.json`](../P0_TASK_LEDGER.json) |
| Reference implementation | **Complete** — `deploy/melodia_economy.py`, 199 lines, deterministic |
| MCP simulation | **Live** — `melodia_economy_{get_state,rhythm_hit,cast_skill,activate_grief_hook}` |
| **C++ / Blueprint** | **DOES NOT EXIST** — no `*Econom*` or `*Grief*` source file anywhere |

This is the same pattern as the rest of the project: the thinking is done, the wire is missing.

### The reference implementation is the spec

`deploy/melodia_economy.py` is not a sketch. It is deterministic and directly portable:

| Function | Behavior |
|---|---|
| `MelodiaGlobalEconomy` | The four economies + grief as one dataclass |
| `_clamp` / `_clamp_economy` | The `[0..Max]` clamp rule §4 requires |
| `on_rhythm_hit(economy, accuracy)` | Rhythm accuracy → economy yield, grief-modulated |
| `cast_healing_song(economy, tier)` | Consumes Healing, grants small Mana (routes around the grief penalty) |
| `cast_mana_song(economy, tier)` | Consumes Mana, restores Resonance, **reduces Grief** |
| `cast_utility_debuff(economy, tier)` | **The mana drain.** Consumes `8*tier` Utility, drains `15*tier` enemy mana, emits `debuff: "mana_drain"` |
| `activate_grief_hook(economy, dungeon_id)` | Route-entry grief activation |
| `record_cast` / `get_cast_history` | The quest gate — P0 requires all three families cast at least once |

**Port it, don't re-derive it.** And keep the Python: it is the unit-test oracle. Any C++ port
should produce identical numbers for identical inputs, which makes the test trivial to write and
non-negotiable to pass.

### Chain rules that must survive the port

These are the loop, and they are easy to lose in translation:

```
HealingSong      -> small Mana bonus      (bypasses grief penalty on Healing->Mana)
ManaSong         -> reduces Grief
UtilityDebuff    -> mana drain            -> enemy weaker via reduced ManaEconomy
UtilityBuff      -> buffs party
UtilityCleanse   -> clears debuffs
```

### Order of work

1. Port `MelodiaGlobalEconomy` + the clamp to a C++ struct/subsystem. **Not** onto the JRPG
   template — economy is a Melodia layer, the template keeps damage/turns.
2. Port the three cast functions. Start with `cast_utility_debuff` — the mana drain is the P0 gate.
3. Wire `on_rhythm_hit` to the existing rhythm grade path
   (`MelodiaJRPGPresentationRhythmComponent::HandleRhythmSessionCompleted`).
4. Write the parity test against the Python oracle before wiring any UI.
5. Only then the HUD (Front 2).

**Must not:** the economy never becomes a second damage authority. It modulates; the JRPG template
still resolves. Same boundary as the music-as-key work.

---

## Front 2 — Live WBP fixes

### 2a. The economy HUD does not exist

`Docs/P0_VERTICAL_SLICE_SPEC.md` §2 requires, and **none of it is built**:

- 4 economy indicators (`HealingEconomy`, `ManaEconomy`, `UtilityEconomy`, `GriefEconomy`)
- Grief indicator (bar or icon)
- Cast buttons per family (Healing / Mana / Utility — Debuff at minimum)
- Scalar tier display per family
- Rhythm/combo feedback tied to economy yield

A search for `WBP_*Econom*`, `WBP_*Grief*`, `WBP_*Song*` returns **nothing**.

**Build on the existing foundation, do not start fresh.** `Content/Melodia/UI/Foundation/` already
has the design system: `WBP_MelodiaParchmentPanel`, `WBP_MelodiaUniversalButton`,
`WBP_MelodiaDarkBoard`, `WBP_MelodiaDivider`, `WBP_MelodiaFiligreeGradeHalo`,
`WBP_MelodiaElementWheel`. The economy HUD should be assembled from these, not authored raw.

### 2b. Rhythm highway lane legend — known defect

`Content/Melodia/UI/Rhythm/WBP_MelodiaRhythmHighway` still displays the **retired D/F/J/K**
binding. Live keys are **Q/W/O/P**, via `BP_BattleUI::OnKeyDown`'s four `Equal(Key)` nodes.

The C++ remap in `UMelodiaBattleInputComponent` is **inert** — that component is only created by
`AMelodiaGameMode`, which is not the live game mode. Do not "fix" it there again; it will do
nothing. The Blueprint `OnKeyDown` is the real input seam.

Fix in-editor via `ui.get_widget_tree` on the highway, then `ui.set_text` on the legend blocks.
Small, visible, unambiguous — good first task of a session.

### 2c. The HUD has two writers

`hud_single_writer` is **OPEN and actively violated**. Two GameInstance subsystems independently
create battle-time widgets:

- `MelodiaUIBridgeSubsystem` — `CreateWidget` at `:124`, `:348`, `:365`
- `MelodiaJRPGBattleOverlaySubsystem` — `CreateWidget` at `:64`, `:83`

…on top of stock `BP_BattleUI`, which still renders underneath by design
(`MelodiaUIBridgeSubsystem.h` documents this explicitly).

**Merge `MelodiaJRPGBattleOverlaySubsystem` into `MelodiaUIBridgeSubsystem`.** That is fixable
now and is independent of the harder question — *does stock `BP_BattleUI` still need to render, or
can it be fully hidden?* — which needs one editor session with `melodia_ui_get_battle_hud` and
`melodia_ui_validate_widget`. Record the answer in the contract when you have it.

Do not add the economy HUD as a *third* writer. It goes through the merged owner.

---

## Front 3 — Animation composition

Based on the capture work done today. Full detail:
[`../MELUSINA_ANIMATION_PIPELINE_REVIEW_2026-08-20.md`](../MELUSINA_ANIMATION_PIPELINE_REVIEW_2026-08-20.md).

### What the screenshots proved

Captures live in `Saved/Screenshots/Monolith/MelusinaLocoCheck/` and
`.../AnimFrames/20260820_164938_*`.

| Blend param | Result |
|---|---|
| 0 (Idle) | Full body, standing, one leg forward — correct |
| 300 (Run) | Posed, coherent deformation |
| 630 (Sprint sample) | Clear sprint pose |

**The skeleton, the retargeted mocap clips, and `BS_Melusina_Locomotion_Hybrid` all evaluate
correctly.** Skirt, boots, hat and hair deform together, no exploded geometry. The retarget is
functioning — that question is closed.

The blendspace is 1D `GroundSpeed` 0→650 with 7 samples (Idle 0, Walk 150/180, Run 300/420,
Sprint 540/630). Live `SprintSpeed = 630` on the traversal component matches the top sample
exactly — **no disagreement**, contrary to an earlier note citing 714 from a stale ledger row.

### Three fixes applied today

All compiled 0/0 and saved (660,681 → 672,062 bytes):

| Fix | Effect |
|---|---|
| `Speed` ← `RuntimeGroundSpeed` (Property Access → `Set Speed`) | `Idle → Locomotion` (`Speed > 10.0`) can now fire — **she can leave Idle at all** |
| `bIsGliding` ← `bRuntimeIsGliding` | `Airborne → Glide` can now fire — the wardrobe capability's animation half |
| `BlendSpacePlayer_2.X` pin-bound to `RuntimeGroundSpeed` | The in-state blendspace reads real speed instead of defaulting to 0 |

Both reads use genuine **Property Access** nodes, so the thread-safe update graph stays
thread-safe. Live chain:

```
FunctionEntry -> Set Velocity -> Set Acceleration -> Set bIsMoving
             -> Set Speed        (<- RuntimeGroundSpeed)
             -> Set bIsGliding   (<- bRuntimeIsGliding)
```

### Composition work still open

1. **JumpWindup is unreachable — third dead state.** PIE logged
   `BP_MelusinaJRPGCharacter_C_1 is trying to crouch, but crouching is disabled on this character!`
   Both `Idle → JumpWindup` and `Locomotion → JumpWindup` are gated on `bIsCrouched`, which can
   never be true while crouch is disabled. The purpose-named `bJumpWindup` exists and is unused,
   and `JumpWindupVisualDuration = 0.4` is configured. **Owner call:** wire `bJumpWindup` to the
   transitions, or enable crouch on the movement component.
2. **Orphaned nodes in `AnimGraph`** — `BlendSpacePlayer_0` (correctly bound to
   `RuntimeGroundSpeed` but connected to nothing) and `Slot_1/2/3`. Remove or connect.
3. **Dead duplicate chain in ThreadSafeUpdate** — `VariableSet_0/_2/_3` read
   `CharacterProperties.*` and are not connected to the function entry. An older implementation.
   Harmless at runtime, misleading to read.
4. **Two pre-existing compile warnings** on the pawn:
   `RecreatePinForVariable: 'CharacterMesh0' pin not found` (×2). Present before today's work.
5. **Nine `ABP_Melusina*` assets exist**; two are real (`_Current` + the hair pair). The rest are
   backups, archives and a duplicate tree — the animation-pillar version of the convergence problem.

### ⚠ Capture tooling hazard

`editor.capture_anim_frames` **leaks a rooted UObject and crashes the editor** with
`Assertion failed: !IsRooted()` (`UObjectBaseUtility.h:209`) on a later call. Observed twice today:
4 captures then crash; relaunch, 1 capture then crash.

**Rule until fixed: one `capture_anim_frames` call per editor session, then relaunch.** Budget for
it; do not chain captures. This is a Monolith plugin bug
(`Plugins/Monolith/Source/MonolithEditor/`) and worth fixing, since capture is the project's main
visual-evidence path.

---

## Gate status

Nothing below was recorded as passing. Verify with `python Tools/echo_run.py status`, not prose.

| Gate | State | What it needs |
|---|---|---|
| `runtime` | **PASS** 2026-08-13 | owner-locked, do not reopen |
| `save_load` | **PASS** 2026-08-14 | owner-verified |
| `repeat_consume` | **PASS** 2026-08-14 | |
| `package_launch` | **PASS** 2026-08-14 | |
| `static_gates` | **FAIL** 2026-08-14 | 2 material baseline drifts: `M_Master_Simple_Universal` 25→26 nodes, `M_Master_Toon_Landscape_HeightBlend` 290→304. **Re-baseline, do not revert** — commit `54c4064d` deliberately enables triplanar blend on the landscape master, so the drift is authored work, not corruption. Run `Docs/T3D_Baseline/verify_baseline.py` and accept the new baseline. |
| `music_world_key` | OPEN | C++ bridge **built**; needs component placed on a hero-music host + PIE |
| `wardrobe_gameplay_hook` | OPEN | data + wiring complete; needs PIE |
| `hud_single_writer` | OPEN | violated — merge the two overlay subsystems |
| `rhythm_owner` | OPEN | |
| `rhythm_grade_to_result` | OPEN | |
| `wardrobe_equip_roundtrip` | OPEN | |

---

## Start here next session

In order. Each is small and verifiable.

1. **Fix the rhythm highway lane legend** to Q/W/O/P. Fastest visible win.
2. **PIE the money-pouch chain.** Place `UMelodiaPCGNarrativeChallengeBridgeComponent` on an
   `APCGHeroMusicGraphHost`, play the pattern, confirm the flag commits once and the reward grants
   once; equip `Cos_Accessories_MelusinaV2`, confirm Glide activates and is suppressed in battle;
   replay + reload to confirm no double-grant. Then record `music_world_key` and
   `wardrobe_gameplay_hook`.
3. **Merge `MelodiaJRPGBattleOverlaySubsystem` into `MelodiaUIBridgeSubsystem`.**
4. **Port `melodia_economy.py` to C++**, mana drain first, with the Python parity test.
5. **Build the economy HUD** from `Content/Melodia/UI/Foundation/` primitives, through the single
   UI owner.
6. **Resolve JumpWindup** (owner call) and clear the AnimGraph orphans.

**Standing constraints:** one editor, one writer, no second MCP surface on one graph. Check
`ls Content/MelodiaIntegration/Blueprints/*.uasset -la` for read-only before any save —
LFS-lockable assets sit `-r--r--r--` and `save_asset` returns success while writing nothing.
Always verify by mtime.
