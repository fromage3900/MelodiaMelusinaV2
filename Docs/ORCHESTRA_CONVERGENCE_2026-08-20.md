# Orchestra Convergence — which implementation owns which pillar

**Date:** 2026-08-20
**Authority:** [`../../PROJECT.md`](../../PROJECT.md)
**Companion:** [`ORCHESTRA_CONTRACT_2026-08-20.md`](ORCHESTRA_CONTRACT_2026-08-20.md) (the seams)

This document exists because the four pillars were built in parallel and never joined. Its job is
to name **exactly one OWNER per pillar** and mark everything else.

Verdicts:

- **OWNER** — the single implementation that owns this behaviour. Build here.
- **LIVE** — real, load-bearing, has callers. Not the owner of the pillar, but not dead either.
  Do not delete.
- **DEAD** — no live callers on the shipping path. Marked for deletion pending owner sign-off
  (deletion is Red-tier per `CLAUDE.md`).
- **MERGE** — holds unique behaviour that must move to the OWNER before it can die.

Every verdict below cites a source line. **No verdict here is from inference.**

---

## Headline finding: the project is much further along than its docs say

Three of the four pillars are substantially built. The `_VERTICAL_SLICE_SCOPE.md` deferral list and
the "world puzzle does not exist" assumption were both wrong:

| Assumption going in | What the source actually says |
|---|---|
| "MelodiaCore's three rhythm classes are dead duplicates" | **Wrong on 2 of 3.** `MelodiaRhythmHUDWidget` and `MelodiaRhythmReactivitySubsystem` are both live and load-bearing on the shipping path. |
| "World puzzle does not exist" | **Wrong.** `Source/BS_GodFile/Piano/` is a complete music-as-key system — PCG-spawned piano keys, steppable note nodes, pattern scoring, and an `OnPatternCompleted` event. |
| "Wardrobe has no gameplay hook" | **Wrong.** `MelodiaTraversalCapabilityProvider.h` already defines Glide/Dash/Swim capabilities with `MelodiaWardrobe` as the canonical provider — the Infinity Nikki pattern, already wired. |

The work really is convergence, not construction.

---

## Pillar 1 — RHYTHM

| Implementation | Location | Evidence | Verdict |
|---|---|---|---|
| `UMelodiaRhythmCombatSubsystem` + `RhythmBeatTracker` + `MelodiaRhythmSkillDefinition` | `Source/BS_GodFile/MelodiaIntegration/` | Owner-locked WORKED in PIE, `Docs/Handoffs/RHYTHM_GAME_LOCKED_2026-08-12.md`. Binds the HUD at `MelodiaRhythmCombatSubsystem.cpp:168`. | **OWNER** |
| `UMelodiaMusicClockSubsystem` | `Source/BS_GodFile/MelodiaIntegration/` | Harmonix/Quartz beat authority; drives `MPC_Melodia_Palette` via `MelodiaAudioReactivePresentationSubsystem::TickPresentation`. | **OWNER** (beat authority) |
| `UMelodiaJRPGPresentationRhythmComponent` | `Source/BS_GodFile/MelodiaIntegration/` | Live: emits grade OSC via `HandleRhythmSessionCompleted`, calls Reactivity at `:195`. | **LIVE** |
| `UMelodiaRhythmHUDWidget` | `Plugins/MelodiaCore/` | **LIVE, not dead.** The OWNER subsystem binds it (`MelodiaRhythmCombatSubsystem.cpp:168, 276, 449, 506`) and `MelodiaUIBridgeSubsystem.cpp:365` instantiates it. | **LIVE** |
| `UMelodiaRhythmReactivitySubsystem` | `Plugins/MelodiaCore/` | **LIVE, not dead.** Six external call sites: `MelodiaAudioReactivePresentationSubsystem.cpp:141`, `MelodiaJRPGPresentationRhythmComponent.cpp:195`, `MelodiaTraversalComponent.cpp:1012`, `Piano/PCGHeroMusic.cpp:89, 581, 626`. Owns the shared material bus and OSC emission. | **LIVE** |
| `UMelodiaRhythmExecutionComponent` | `Plugins/MelodiaCore/` | Zero live callers. Only held as a property on `AMelodiaBattleArena`, and `MelodiaAudioReactivePresentationSubsystem.cpp:132` states in a comment: *"that actor is never spawned."* | **DEAD** |
| `UMelodiaBattleInputComponent` key remap (Q/W/O/P) | `Plugins/MelodiaCore/` | Created only by `AMelodiaGameMode` (`MelodiaGameMode.cpp:51`) and a unit test (`MelodiaCoreRulesTests.cpp:338`). The live game mode is `BP_MelodiaJRPGGameMode`, so the remap never executes. | **DEAD** (inert) |
| `BP_BattleUI::OnKeyDown` four `Equal(Key)` nodes | Blueprint | **The actual live input seam.** Documented in `CURRENT_STATE.md` (2026-08-08) as the effective fix after the C++ change proved inert. | **OWNER** (input seam) |
| `WBP_MelodiaRhythmHighway` lane legend | Blueprint | Still displays the retired D/F/J/K binding; live keys are Q/W/O/P. Known defect, unfixed. | **LIVE — defect** |

### Actions

1. Mark `MelodiaRhythmExecutionComponent` and the `MelodiaBattleInputComponent` remap DEAD in-header. Deletion needs owner sign-off.
2. **Do not touch** `MelodiaRhythmHUDWidget` or `MelodiaRhythmReactivitySubsystem`. They live in MelodiaCore but are on the shipping path. MelodiaCore being "quarantined" does not make everything inside it dead — verify before assuming.
3. Fix the `WBP_MelodiaRhythmHighway` lane legend to Q/W/O/P.
4. Document `BP_BattleUI::OnKeyDown` as the input seam in the contract, so it stops being folklore.

> **Correction to the `rhythm_owner` gate.** The gate cannot be *"MelodiaCore's rhythm classes have
> zero live callers"* — two of them have many, correctly. The real contract is
> **exactly one rhythm path reaches the JRPG damage calculation**, which is about the execution
> path, not the module a class lives in.

---

## Pillar 2 — WARDROBE

| Implementation | Location | Evidence | Verdict |
|---|---|---|---|
| `UMelodiaWardrobeSubsystem` + `UMelodiaWardrobeComponent` + `UMelodiaWardrobeGachaSubsystem` + `UMelodiaCosmeticDefinition` | `Plugins/MelodiaWardrobe/` | Coherent, self-consistent C++ API. Component mirrors equipped state to the subsystem (`MelodiaWardrobeComponent.h:6`). | **OWNER** |
| `specs/wardrobe/wardrobe_catalog_contract.v1.json` | `specs/wardrobe/` | The data contract the OWNER reads. | **OWNER** (data contract) |
| Traversal capability provider (Glide / Dash / Swim) | `Source/BS_GodFile/MelodiaIntegration/MelodiaTraversalCapabilityProvider.h:30-38` | **The wardrobe→gameplay hook, already built.** `MelodiaWardrobe` is named the canonical provider; `MelodiaTraversalComponent` is the caller. Registry rejects multiple providers to avoid split truth. | **OWNER** (gameplay hook) |
| `Content/Python/wire_melusina_wardrobe_component.py`, `wire_melusina_wardrobe_instances.py`, `import_melusina_wardrobe_contract.py` | `Content/Python/` | Importer/authoring tooling, not runtime. Belongs behind the C++ API. | **MERGE** |
| `deploy/ollama_wardrobe_catalog_daemon.py` | `deploy/` | Already produces catalog rows with a local model. Becomes the `wardrobe_catalog` production lane's reference implementation. | **MERGE** (→ producer) |
| `UMelodiaOutfitComponent` | `Plugins/MelodiaCore/` | Created as a default subobject on every `AMelodiaCharacterBase` (`MelodiaCharacterBase.cpp:19`). `Docs/Plans/MELUSINA_V2_REBUILD_AND_INFINITY_NIKKI_WARDROBE_PLAN_2026-08-14.md` already calls it compatibility-only. Second outfit authority. | **DEAD** (compat-only) |
| `UMelodiaNPRClothingComponent` | `Plugins/MelodiaNPR/` | Self-contained blendshape sync with its own `GetCurrentOutfit`/`SetCurrentOutfit`. A **third** outfit-state holder; no external callers found. | **DEAD** or **MERGE** — needs one decision |

### Critical finding

**Nothing outside `Plugins/MelodiaWardrobe/` calls `UMelodiaWardrobeSubsystem`.** The pillar is
built and internally coherent but is **not connected to the running game from C++**. The only
declared connection point is the traversal capability provider. Whether a Blueprint wires it is an
open question that needs one editor session to answer.

This is the single biggest convergence gap in the project: a complete, well-designed wardrobe
system that nothing calls.

### Actions

1. Establish in-editor whether a `MelodiaWardrobeComponent` exists on the live pawn and whether its default garment map is populated. `MELUSINA_V2_REBUILD...` records both as OPEN at last check.
2. Decide `MelodiaNPRClothingComponent`: fold its blendshape sync into the OWNER, or mark DEAD. Three outfit-state holders is two too many.
3. Mark `MelodiaOutfitComponent` DEAD in-header.
4. Prove the Glide/Dash/Swim path end-to-end — the header itself warns: *"a capability needs a provider that maps it and a caller that asks for it, or it is a name with no behaviour behind it."*

---

## Pillar 3 — UI

This is the hardest call in the project, and the honest answer is that **the two-writer design is
deliberate and documented**, not accidental.

`MelodiaUIBridgeSubsystem.h` states it plainly:

> *"Melodia widgets are created into generic UUserWidget variables so there are NO type
> compatibility issues with stock BP_BattleUI_C typed variables. The stock UI still renders
> underneath (invisible if hidden); Melodia UI is the visible overlay."*

| Implementation | Location | Evidence | Verdict |
|---|---|---|---|
| Stock `BP_BattleUI` | Blueprint (JRPG template) | Owns command input via `OnKeyDown`. Part of the absolute authority layer. | **OWNER** (command input) |
| `UMelodiaUIBridgeSubsystem` | `Source/BS_GodFile/MelodiaIntegration/` | Creates `MelodiaBattleWidget` at `:124` **and again** at `:348`, plus `MelodiaRhythmHUDWidget` at `:365`. GameInstance subsystem. | **OWNER** (battle overlay) — pending §Decision |
| `UMelodiaJRPGBattleOverlaySubsystem` | `Source/BS_GodFile/MelodiaIntegration/` | **A second GameInstance subsystem creating battle-time widgets**: `MelodiaBattleKeyboardLegendWidget` at `:64`, `RhythmPrompt` at `:83`. | **MERGE** → UIBridge |
| `UMelodiaUIWiringComponent`, `UMelodiaUIFeedbackSubsystem`, `UMelodiaUIBridgeLibrary` | `Source/BS_GodFile/MelodiaIntegration/` | Support surfaces around the bridge. | **LIVE** |
| `UMelodiaQuillPresentationWidgets` | `Source/BS_GodFile/MelodiaIntegration/` | Narrative presentation; creates choice entries at `:222`. Distinct surface from battle. | **LIVE** |
| `UMelodiaBattleResultsWidget`, `UMelodiaExplorationHUDWidget` | `Plugins/MelodiaCore/` | MelodiaCore widgets. Live-caller status **not yet established** — do not assume dead, given the `MelodiaRhythmHUDWidget` lesson above. | **UNKNOWN — verify** |

### The one question that settles this pillar

**Does the stock battle UI still need to render, or can it be fully hidden so Melodia's overlay is
the only writer?**

Everything else follows from the answer. This cannot be settled from source — it needs one editor
session with `melodia_ui_get_battle_hud` and `melodia_ui_validate_widget`, one writer, no second
MCP surface.

### Actions

1. Answer the question above in-editor. Record the answer in the contract.
2. Merge `MelodiaJRPGBattleOverlaySubsystem` into `MelodiaUIBridgeSubsystem`. Two GameInstance subsystems independently spawning battle widgets is the concrete two-writer defect, independent of the stock-UI question.
3. Establish caller status for the two MelodiaCore widgets before judging them.

---

## Pillar 4 — WORLD PUZZLE (music as key)

**This pillar exists.** It was missed on the first pass because it is filed under `Piano/`, not
`Puzzle/` or `Challenge/`.

| Implementation | Location | Evidence | Verdict |
|---|---|---|---|
| `APCGHeroMusicNode`, `APCGHeroMusicGraphHost` | `Source/BS_GodFile/Piano/PCGHeroMusic.{h,cpp}` | Steppable world note-nodes with `HandleStepBegin`/`HandleStepEnd` overlap triggers, spring-physics press, lane assignment, `ScoreState` (Score/Streak/HitCount/MissCount), grade judging, and `OnPatternCompleted` broadcast at `:620`. | **OWNER** |
| `APCGPianoKey`, `UPCGPianoKeyboardProfile` | `Source/BS_GodFile/Piano/PCGPianoKeyboard.h` | PCG-spawned piano keys with real MIDI notes, black/white, `InitializeFromPCGPoint`. | **OWNER** |
| `PCGMusicSequencer` | `Source/BS_GodFile/Piano/` | Sequencing layer. | **LIVE** |
| Piano content | `Content/EnvSandbox/PCG/Musical/` | Real assets: `SM_PianoKey_White_Bevel`, `SM_PianoKey_Black_Bevel`, `SM_Piano_Keybed`, `MI_Piano_Ivory`, `MI_Piano_Ebony`, `M_Piano_Surface`. | **LIVE** |
| Piano build tooling | `Content/Python/build_pcg_piano.py`, `pcg_piano_layout.py`, `setup_pcg_piano_level.py`, `audit_pcg_piano.py`, `test_pcg_piano_layout.py` | Complete authoring pipeline with its own test. | **LIVE** |
| `UMelodiaPCGWaterGameplayBridgeComponent` | `Source/BS_GodFile/MelodiaIntegration/` | **The only consumer of `OnPatternCompleted`** (`:48`). Routes pattern completion into water gameplay. | **LIVE** |

### The actual gap

The music-as-key loop is **built and closed** — but it closes onto **water only**. A completed
pattern produces a water reaction and a `Reactivity->NotifyVictory()` presentation pulse
(`PCGHeroMusic.cpp:626`). It never reaches narrative, quest, or traversal state.

`PCGHeroMusic.cpp:624` states the boundary deliberately:

> *"Presentation-only: the existing reactivity subsystem owns the shared material bus and never
> enters the combat or damage pipeline."*

That boundary is **correct and must be preserved** — music must not become a second combat
authority. But "never enters combat" is not the same as "never has a consequence." A Zelda ocarina
does not deal damage; it opens a door.

### Actions

1. **Do not build a puzzle system.** Wire the existing `OnPatternCompleted` to **one** narrative consequence through the existing 7-verb contract — a `melodia:flag:` or `melodia:quest:` notification into `UMelodiaNarrativeSubsystem`, which already owns idempotency via `ConsumedIntentIds`.
2. That single edge satisfies `music_world_key` and turns three built-but-disconnected systems into a loop.
3. Preserve the presentation-only boundary. Music opens doors; the JRPG template still deals damage.

---

## Summary — what convergence actually requires

> **Progress 2026-08-20 (same day).** Actions 1 and 5 are implemented and awaiting a build/PIE.
> See "Work landed" below the table.

| # | Action | Pillar | Blocked on |
|---|---|---|---|
| 1 | Wire `OnPatternCompleted` → narrative | World puzzle | **CODE WRITTEN** — needs a closed-editor build |
| 2 | Answer the stock-UI render question in-editor | UI | One editor session |
| 3 | Merge `MelodiaJRPGBattleOverlaySubsystem` into `MelodiaUIBridgeSubsystem` | UI | #2 |
| 4 | Establish whether the live pawn has a populated `MelodiaWardrobeComponent` | Wardrobe | One editor session |
| 5 | Prove the Glide/Dash/Swim capability path end-to-end | Wardrobe | **DATA AUTHORED** — needs #1 built, then PIE |
| 6 | Fix `WBP_MelodiaRhythmHighway` lane legend → Q/W/O/P | Rhythm | Nothing |
| 7 | Mark DEAD: `MelodiaRhythmExecutionComponent`, `MelodiaBattleInputComponent` remap, `MelodiaOutfitComponent` | Rhythm, Wardrobe | Nothing (marking only; deletion needs owner) |
| 8 | Decide `MelodiaNPRClothingComponent`: merge or dead | Wardrobe | Owner call |
| 9 | Establish caller status for `MelodiaBattleResultsWidget`, `MelodiaExplorationHUDWidget` | UI | Nothing |

**Not on this list, deliberately:** building a puzzle system, building a wardrobe UI, adding rhythm
songs, or deleting anything. All of that is either already built or gated behind owner sign-off.

---

## Standing rule this document establishes

> **MelodiaCore being quarantined does not make everything inside it dead.**
>
> `MelodiaRhythmHUDWidget` and `MelodiaRhythmReactivitySubsystem` both live in MelodiaCore and both
> carry the shipping path. Two of three assumed-dead classes turned out load-bearing. **Grep for
> callers before assigning any DEAD verdict** — and exclude `Intermediate/` from the search, or
> generated UHT files will drown the real answer.


---

## Work landed 2026-08-20

### The music-as-key adapter now exists

`Source/BS_GodFile/MelodiaIntegration/MelodiaPCGNarrativeChallengeBridgeComponent.{h,cpp}`

This is the "pending world challenge adapter" that
`specs/blueprints/fixtures/first_resonance_world_challenge.v1.json` names as its
`runtime_authority` and which had **no implementation** — the fixture sat at
`status: contract_spec_only`. It mirrors `UMelodiaPCGWaterGameplayBridgeComponent`
exactly: attach to an `APCGHeroMusicGraphHost`, bind `OnPatternCompleted`, and commit.

It commits through **`UMelodiaNarrativeSubsystem::CommitWorldChallenge`** — one atomic
transaction carrying the completion flag, the allowlisted reward and the consumed intent.
Never `SetNarrativeFlag` + `GrantDialogueReward` separately; the subsystem's own comment
forbids that split.

Boundaries held:
- **No combat contact.** It sets a flag and grants an allowlisted reward. It never touches
  damage, turns, targeting or party state — preserving the `PCGHeroMusic.cpp:624`
  presentation-only boundary. Music opens doors; the JRPG template deals damage.
- **No direct save write**, per the fixture's `adapter_must_not_write_save_object_directly`.
- **No local idempotency bool.** `ConsumedIntentIds` in the narrative record is the single
  source of truth, and it is SaveGame-flagged, so replay after a reload is still a no-op.
  A local flag would be a second truth that a reload would silently contradict.

Ids all verified against the live allowlist (`melodia_config_get_allowlist`):
`challenge.first_resonance_echo` / `challenge.first_resonance_echo.completed` /
`reward.first_resonance_echo`.

**Not yet built.** It is a new `UCLASS` with `GENERATED_BODY`, so Live Coding cannot
register it — only a full closed-editor build can. The editor was open, so no build was
attempted. `source.lint_header` reports clean; every referenced symbol was verified present.

### The wardrobe gameplay hook now has data

`Plugins/MelodiaWardrobe/Content/Catalog/DA_MelodiaCosmeticCatalog` (4522 → 5232 bytes)

The wardrobe→traversal chain was **fully coded and completely empty**: 5 cosmetics,
**0 resonant forms**, every `resonant_form_id` null — the first outfit is
`resonant_form_policy: decorative_only` by design, so no equipped cosmetic could grant
anything.

Authored the missing link:

| Field | Value |
|---|---|
| `form_id` | `form.first_resonance_echo` |
| `required_flag_ids` | `[challenge.first_resonance_echo.completed]` |
| `granted_capabilities` | `[Glide]` |
| `restricted_context_ids` | `[battle_session]` |
| linked cosmetic | `Cos_Accessories_MelusinaV2` |

### Why these two are one change

They close the project's whole thesis in a single chain, and neither half is useful alone:

```
play the piano pattern
  -> OnPatternCompleted
  -> CommitWorldChallenge          (the new adapter)
  -> flag challenge.first_resonance_echo.completed
  -> FormUnlockedAgainst() passes  (the new catalog data)
  -> equipping Cos_Accessories_MelusinaV2 grants Glide
  -> MelodiaTraversalComponent opens a route that was closed
```

Music opens a door. The wardrobe carries the gameplay meaning. Combat is never touched.
`restricted_context_ids: [battle_session]` enforces that last part in data as well as code.

### Two gotchas worth keeping

1. **`save_asset(only_if_is_dirty=False)` still silently no-ops on a read-only file.** The
   catalog is LFS-`lockable`, so it sits `-r--r--r--` on disk. The call returned success and
   the mtime did not move. Always check the mtime, not the return value — the existing
   warning in `CURRENT_STATE.md` covers dirty-flag failures but not the read-only case.
   `GitSourceControl` is not enabled and `github.com` is unreachable, so no LFS lock can be
   taken; the flag was cleared locally.
2. **MelodiaCore quarantine does not imply dead.** Restated because it cost the first pass of
   this audit two wrong verdicts.

### Neither gate is recorded

`music_world_key` and `wardrobe_gameplay_hook` remain **OPEN**. Code and data exist; nothing
is proven. The next steps, in order:

1. Close the editor and build `BS_GodFileEditor`.
2. Add `UMelodiaPCGNarrativeChallengeBridgeComponent` to an `APCGHeroMusicGraphHost` in a level.
3. PIE: play the pattern, confirm the flag commits once and the reward grants once.
4. Equip `Cos_Accessories_MelusinaV2`, confirm Glide becomes active and is suppressed in battle.
5. Replay the pattern and reload the save — confirm no double-grant.
6. Only then: `python Tools/echo_run.py record music_world_key pass`.


---

# Pillar 5 — THE PAWN (added 2026-08-20, later)

Four Melusina character Blueprints existed. This section names the owner and retires the rest.

## Verdicts

| Blueprint | Parent | Evidence | Verdict |
|---|---|---|---|
| `/Game/MelodiaIntegration/Blueprints/BP_MelusinaJRPGCharacter` | `BP_JRPGCharacterBase_C` (JRPG template) | **Referenced by `BP_MelodiaJRPGGameMode` as its default pawn.** 25 components + 4 native. Uses `ABP_Melusina_Current`. Confirmed instantiated in PIE as `BP_MelusinaJRPGCharacter_C_1`. | **OWNER** |
| `/Game/Experiments/MelodiaJRPG/BP_MelusinaSwordsman_Presentation` | `BP_PlayerUnitBase_C` | Mutual hard reference with the owner. A battle **unit**, not a character — a different role in the JRPG template, not a duplicate. | **LIVE** |
| `/Game/Melodia/Characters/Melusina/BP_Melusina` | `MelodiaSmokeCharacter` (C++, MelodiaCore) | Zero references. In no `.umap`. Parent is a **smoke-test class**. Decision 044's rationale states this pawn "was retired for being a second authority." | **DEAD** (already retired by decision) |
| `/Game/Characters/Melusina/BP_Melusina` | `Character` (engine) | Zero references either direction. Duplicate root tree. | **DEAD** |

## What was consolidated

The owner carried **both** outfit authorities: `Wardrobe` (`MelodiaWardrobeComponent`, the owner per
Decision 044) *and* a vestigial `Outfit` (`MelodiaOutfitComponent`, the superseded one).

`Outfit` had **zero references** in the pawn's graphs. Decision 044 records that
`UMelodiaWardrobeComponent` is a one-way re-host of the `UMelodiaOutfitComponent` algorithm, with
the material-override and subsystem-mirror additions the original lacked.

**Removed `Outfit` from `BP_MelusinaJRPGCharacter`.** Compile went from
`UpToDateWithWarnings` to **`UpToDate`, 0 errors / 0 warnings** — the vestigial component was the
warning source. Saved 406,053 → 405,062 bytes.

Decision 044's constraint is honored: the quarantined `MelodiaCore` source was **not** moved,
deleted or modified. Only the redundant component instance on the live pawn was removed.

## Correction — the live pawn was never missing anything

An earlier pass in this session inspected `BP_Melusina` and concluded the pawn lacked a wardrobe
component, lacked a traversal component, and had the capability gate off. **All three were wrong**
— that was the orphaned smoke-test pawn. The real pawn has:

| | State |
|---|---|
| `Wardrobe` (`MelodiaWardrobeComponent`) | Present |
| `MelodiaTraversal` (`MelodiaTraversalComponent`) | Present |
| `bRequireCapabilityProviderForGlide` | **`True`** |
| `TraversalCapabilityContextId` | `active_traversal_context` |
| `SprintSpeed` | 630 — exactly the top blendspace sample, no disagreement |
| `WaterHairMesh` (`MelodiaHairComponent`) | Present, binds to `head_x` at runtime (verified in PIE log) |

**So the money-pouch chain has one remaining unknown, not four.** Wardrobe → capability →
traversal → `bIsGliding` → Glide state is complete in data and wiring; only PIE proof is missing.

Note the form's `restricted_context_ids: [battle_session]` does not collide with the live query
context `active_traversal_context`, so the restriction behaves as intended.

## New finding — crouch is disabled, so JumpWindup is unreachable

PIE logged: `BP_MelusinaJRPGCharacter_C_1 is trying to crouch, but crouching is disabled on this
character! (check CharacterMovement NavAgentSettings)`.

Both `Idle → JumpWindup` and `Locomotion → JumpWindup` are gated on `bIsCrouched`. If crouch is
disabled on the movement component, `bIsCrouched` can never be true and **JumpWindup is a third
unreachable state** — alongside the `Locomotion` and `Glide` states fixed earlier today.

This settles the open question in the animation review's Defect C: `bIsCrouched` driving jump
windup is a **wiring error**, not a deliberate crouch-as-windup design. The purpose-named
`bJumpWindup` variable exists and is unused, and `JumpWindupVisualDuration = 0.4` is configured on
the traversal component — the intent is clear.

**Not fixed here** — it needs either `bJumpWindup` wired to the transitions, or crouch enabled.
That is an owner call.

## Remaining pawn work

1. Retire the two DEAD Blueprints (deletion is Red-tier — needs owner sign-off).
2. Harvest before retiring: `Content/Melodia/.../BP_Melusina` holds `ToggleOrreryMenu` and a
   `WaterHairFlipCache` (`GeometryCacheComponent`) that the owner does not have. Decide whether
   either is wanted on the owner.
3. Resolve the JumpWindup wiring above.
4. Two pre-existing compile warnings on the owner: `RecreatePinForVariable: 'CharacterMesh0' pin
   not found` (×2). Unrelated to this change; present before it.

## Doc defect noticed

`_DECISION_LOG.md` has **two different decisions numbered 044** — the wardrobe re-host
(2026-08-07) and "KawaiiPhysics replaces Chaos Cloth". Decision numbers are being cited across the
codebase (`MelodiaWardrobeComponent.h:3` cites 044), so a collision is a real hazard.
