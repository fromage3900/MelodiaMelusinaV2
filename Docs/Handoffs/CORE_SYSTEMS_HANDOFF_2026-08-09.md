# Core gameplay systems — handoff (2026-08-09)

**Scope for the receiving agent: CORE SYSTEM FUNCTION ONLY.** The owner is handling the
cosmetic/UI-polish side. Do not spend effort on visual polish, tokens, or widget styling.

Everything below was verified this session against the live graph, the running editor, or
source — not from documents. Where something is unproven it says so. **Trust nothing in
older handoffs that contradicts this file**; several of them are stale.

---

## 1. Build state (verified)

- Full rebuild succeeded 2026-08-09 13:01, `Result: Succeeded`, 0 errors, 0 warnings.
  `Binaries/Win64/UnrealEditor-BS_GodFile.dll` @ 13:01:45.
- Editor was closed at handoff time. `melodia.Contract.Validate` → `all 12 stock seams resolve`.

### What landed in that binary
| Feature | Verified? |
|---|---|
| Wall-clock Harmonix music clock on `BP_BattleController`, 128 BPM via `SetDefaultTempo` | compiles; **BPM not yet observed in PIE** |
| `cos²` beat-phase fix (was `sin²` — pulsed on the off-beat) | compiles; not observed |
| Quantum MPC writer (`QuantumChoice/Seed/Backend/Pulse/ReactionColor`) + decay | compiles; not observed |
| Sir fielding into `partyMembers` + honest recruitment log | compiles; **not exercised** |
| `EnsureStockBattleUIControllerReference()` + `melodia.BattleUI.LinkController` | **verified in PIE** |
| Stock-contract validator + `Melodia.Wiring.StockContract.Resolves` test | **verified, green** |

---

## 2. THE blocker for the note highway (highest priority)

**`StockSkillRhythmIds` on `DA_MelodiaIntegrationConfig` is empty.**

`ResolveRhythmSkillId()` (`MelodiaRhythmCombatSubsystem.cpp:173-197`) reads that map to turn a
stock skill class into a rhythm id. A full string dump of the asset shows **no such property
and no `MapProperty`**. So it returns `NAME_None` → `StartSession` returns 0 → **no rhythm
session can ever start.** That is the `MELODIA_RHYTHM no rhythm id mapped for stock skill
class` path, and it is why the note highway has never appeared in any session.

- **This is a DataAsset value, not a graph. T3D cannot fix it.** Use `set_cdo_property`
  (dry-run with `strict:true` first — that pattern worked cleanly for the Melusina skill fix).
- The 8 rhythm definitions exist and auto-scan correctly from `/Game/MelodiaIntegration/Config`
  (`DA_CadenceStrike` … carrying `SkillId=cadence_strike` etc.).
- Melusina's live skills are under `/Game/Experiments/MelodiaJRPG/Skills/`:
  `BP_MelusinaDoubleHit`, `BP_MelusinaFocusAttack`, `BP_MelusinaTrueStrike`, `BP_MelusinaPetalCadence`.
  The map keys need the `_C` generated-class form.
- **Architectural improvement worth making** (owner endorsed): move the rhythm id onto the
  skill Blueprint itself so skills are self-describing and editable, keeping the central map
  only as a legacy fallback that warns when used.

### Second rhythm blocker — the highway never draws
`UMelodiaRhythmHUDWidget::SetNoteHighwayActive_Implementation` only **stores**
`bNoteHighwayActive` / `HighwayNotes` / `HighwayBeatPosition` / `HighwayScrollBeatsAhead`.
Nothing native renders, and `WBP_MelodiaRhythmHighway` contains none of those four names —
its only authored function is `SetLanePressed`. **This is the one genuine T3D injection target.**

### Third — verify before trusting any A/B damage numbers
`MelodiaRhythmCombatSubsystem.h:188-199` documents that the montage damage notify fires
~2.5s **before** `FinishSession` latches the scalar. Unless `UseSkill` is sequenced behind the
`OnRhythmComplete` broadcast, `GetPendingDamageMultiplier()` reads **1.0** and rhythm cannot
affect damage at all. Read the live sequencing first.

**Already correct — do not "fix":** lane input (`RegisterLaneHit` on Q/W/O/P in both
`OnKeyDown` and `OnKeyUp`), `ShowRhythmGrade`, the highway creator in `BP_BattleUI::ShowBattleUI`.

---

## 3. Narrative loop is broken by level geography

The only actor tagged `melodia_smoke_encounter` is `FirstDream_InteractionBattle` in
**`L_KaleidoNave`**. `MelodiaMorningIntro` runs in **`L_MelusinaMorning`**, and
`StartTaggedJRPGBattle` iterates only the current world. So `MatchCount != 1` →
`AbortPendingBattle` → `melodia_battle_result = "unavailable"` → the script plays
"The battle could not begin" and **never sets `melodia_smoke_complete`**.

Also: two scripts compete for the slice spine (`BP_MelodiaSirMelodiousMorningIntro` running
`MelodiaMorningIntro`, vs `BP_KaleidoNaveArrivalTrigger` running `MelodiaQuillSmoke`).
`ActiveInterpreter` is a `TWeakObjectPtr` to a **level actor** — it dies on travel, while
`PendingEncounterId` lives on the GameInstance and survives, so a cross-level battle leaves
the subsystem `Busy` forever. **Pick one spine.**

The seven-verb dispatch itself is confirmed working end to end, and battle-result
exactly-once is **confirmed clean** (`CompleteBattle` clears `PendingEncounterId` and sets
`bBattleCompletionConsumed` before `ResumeQuillOnce()`; delegate uses `AddUnique`).

---

## 4. Sir as the only ctrl-switch target

Nearly done. `PartyPawnClasses` **self-seeds in C++** (`MelodiaPartySubsystem.cpp:16-21`) with
index 0 null (game mode spawns Melusina) and index 1 = `BP_SirMelodious_Flight_C`. LeftControl
is bound in C++ on both pawns (`NewObject<UInputAction>`, no input assets). So the roster and
input already satisfy the requirement.

**The only blocker is `bSirMelodiousExplorationUnlocked`** — one setter, in
`MelodiaJRPGPartyBootstrapSubsystem.cpp:308-310`, which runs only after the read-back probe
confirms Sir reached `partyMembers`. That needs recruitment, which is gated on
`OpeningFlow.Phase == SirRescued`, which **nothing in `MelodiaIntegrationMap` ever sets** —
the only caller is dungeon-run completion and no map places `AMelodiaDungeonRunCoordinator`.
That is lane **A4**: hook `NotifySirRescued()` to the MorningIntro flag
`melodia:flag:melodia_smoke_complete`. C++ + rebuild. Note LeftControl only — RightControl
and gamepad are unmapped.

---

## 5. Death / survivability (blocks a 20-min slice being playable)

- **No post-battle HP restore.** `currentHP` persists, nothing heals it, dead units stay at 0 HP.
  With no shop loop this is a **soft-lock vector**.
- **No retry on defeat** — only exit is `OpenLevel(L_MelodiaMainMenu)`. The stock template
  never had a game-over system; this is an absence in the source, not a regression.
- `NotifyDeathRecovery` / `NotifyRetryRecovery` have **zero call sites**.
- `BP_UnitBase` and `BP_BattleBase` are **md5-identical to the intact template** — death
  handling itself is stock and undamaged.

---

## 6. Save/load — mostly already wired

`WBP_MainMenu` binds all three buttons to `CreateCanonicalJRPGSlot` / `HasCanonicalJRPGSlot` /
`LoadCanonicalJRPGSlot`; `BP_JRPGGameInstance` already carries the narrative sync/restore nodes.
Those gates are **runtime proofs, not wiring jobs.**

Two real gaps: the stock `SaveGameToSlot` path bypasses the `IsSavingAllowed()` guard, and
`LoadCanonicalJRPGSlot` returns `bNarrativeRestored` so the caller cannot distinguish
"refused" from "loaded, narrative degraded."

---

## 7. CORRECTIONS — earlier claims that were WRONG

Inherit these, not the originals:

1. **`BP_BattleUI::battleController` IS written** — by an expose-on-spawn pin on
   `K2Node_CreateWidget_7`, wired to `Self`. The "4 reads, 0 writes" claim came from a
   `VariableSet` census that misses expose-on-spawn pins. The runtime error is still real,
   which points at a **second widget instance** created outside that path (likely the UI
   bridge's `CreateMelodiaBattleUI`). One editor read settles it.
2. **The allowlist does NOT fail closed in editor.** `bRelaxedAllowlistInEditor = true` lets
   unregistered ids pass with a warning in every non-shipping build; it fails closed only in
   Shipping, and `Reject()` does log. Turn it off for verification or typos ship.
3. **`Content/_ThirdParty/TurnBasedJRPGTemplate/` is NOT a pristine copy** — 156 Blueprints vs
   205/206, missing whole subsystems, and its `BP_BattleController` was edited after copying.
   Use `CompatibilityLabs/TurnBasedJRPGUE58` as the reference instead.
4. **Petal Cadence needs no graph** — it applies Resonance via the `buffs` array on
   `BP_BattleSkillBase`. Do not "fix" it. (Note a stale duplicate exists under
   `TurnBasedJRPGTemplate/Blueprints/Skills/` — the live one is under `Experiments/MelodiaJRPG/`.)

---

## 8. T3D injection — proven, with limits

`validate_nodes_t3d` returned **`valid: true`, `engine_accepts: true`** for a
`K2Node_CallParentFunction` payload, so the "must be authored by hand" claim in
`COOP_SKILL_RESONANCE_SPEC_2026-08-08.md` is **dead** — it was an untested assumption.
Payload + method: `Docs/T3D_Patterns/payloads/`.

Open detail: `MemberParent` still warns `unresolved_member_parent` under both quoting forms
tried. Resolve by copying a real parent-call node in the editor and reading its exact
`FunctionReference=` spelling. **Do not inject while that warning stands** — a bad member ref
passes the engine's own gate and imports as a red node.

**Before any injection:** re-export baselines. `Content/Exports/` is Aug 1,
`BP_BattleController.uasset` is Aug 8 23:55, and `Saved/T3D/` contains **neither battle asset**.
Only `EventGraph` was ever captured — `CalculateDamage`/`DealDamage` have never been read.
Also run `bp_live_path.py` (step 0) — injecting into an unreachable graph **succeeds**, which
is worse than failing.

---

## 9. HARD RULES (violating these has already cost this project days)

- **ONE editor instance.** Three concurrent = 5 crashes + 39 lost packages on 2026-08-08.
- **Never `git clean -fd` or `git checkout -- .`** — bulk `Content/` is untracked and
  unrecoverable.
- **Never run Python against `Content/TurnBasedJRPGTemplate/Blueprints/Skills/`** —
  `D_DamageType` glue generation kills the editor fatally. Monolith `blueprint_query` is
  native C++ and safe.
- **`MODAL_OPEN` in the log** = a modal dialog, not a hang. Do not kill the editor.
- **Verify by re-reading.** `success: true` only means nothing threw.
- Blueprint mutation loop is mandatory: `export_graph` → fingerprint → mutate →
  `compile_blueprint` → `assert_graph_matches` → fingerprint → `save_asset`.
  **Unclean compile or `matched:false` is a HARD STOP**, not a retry trigger.
- Header changes cannot be Live Coded (new imports/symbols fail). `.cpp`-only changes can.

---

## 10. Recommended execution order

1. `StockSkillRhythmIds` (data) → the note highway can finally start
2. Verify the damage-scalar sequencing → makes the A/B meaningful
3. Highway note rendering (T3D) → the highway becomes visible
4. Battle actor level geography → the narrative loop connects
5. A4 Sir rescue trigger (C++) → Sir becomes the ctrl-switch target
6. HP restore + retry decision → the slice becomes survivable

## 11. Acceptance criteria (owner's words)

Blueprints for gameplay fully wired; turn-based rhythm skills cause the note highway to
appear, trigger damage, and advance the turn; Sir Melodious is the only available active pawn
to ctrl-switch to on the integration map.
