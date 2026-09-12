# Session closeout — 2026-08-09

Branch: `sonnet-core-mechanics-20260808`. Everything below was verified against the live
graph, the running editor, or a green build. No claim here rests on a document.

---

## The headline

**One boolean gated the entire audio-reactive layer, and it had never once been true.**

`UMelodiaMusicClockSubsystem::HasMusicalTime()` returns
`IsHarmonixClockRunning() || IsQuartzClockRunning()`. Neither could ever be true:
`PresentationRhythm.HarmonixClock` was never assigned, no MetaSound music actor was ever
placed, and the Quartz fallback needed a `UMelodiaAudioComponent` that no actor carried.

Every consumer is ternary-gated on that bool. So `BeatPhase` and `BeatPulse` sat at 0.0,
**89 assets** bound to `MPC_Melodia_Palette` rendered flat, and the OSC beat feed to
TouchDesigner never sent a packet — because the send lives inside the same branch.

That is why "TouchDesigner isn't affecting the materials": TD was starved of the same beat
the materials were. It also corrects a claim made mid-session — TD *can* drive materials,
via `Content/Python/osc_server.py` on port **8000** (editor-Python, MPC writes). The
outbound leg is UE → **9000** → TD, in C++.

---

## Everything fixed

| Fix | Evidence |
|---|---|
| Wall-clock Harmonix music clock on `BP_BattleController`, 128 BPM via `SetDefaultTempo` | build green; `MELODIA_MUSICCLOCK ... musical time is live` observed in PIE |
| **`BeatPulse` was inverted** — `sin²(phase·π)` peaked at phase 0.5, i.e. the off-beat. Now `cos²` | build green; both copies corrected |
| Melusina's four skills unlocked at level 1 (DoubleHit/FocusAttack were required-level 2) | CDO read back: all four = 1 |
| Melusina's identity: `title` "Arthur" → "Melusina" | binary check: 0 occurrences of "Arthur" |
| Quantum MPC writer — publishes all five `Quantum*` params with 3.5/sec decay | build green |
| Sir fielded into `partyMembers`; recruitment log gated on a read-back probe | build green |
| **Lane A4** — `melodia_smoke_complete` → `NotifySirRescued()` | build green |
| `AbortPendingBattle` made `BlueprintCallable` | build green |
| `battleController` written on the stock battle UI from C++ | `MELODIA_BATTLEUI_LINK linked ...` in PIE; error cascade stops at that timestamp |
| Stock-contract validator + automation test | `MELODIA_CONTRACT all 12 stock seams resolve` |
| T3D parent-call probe | `valid: true`, `engine_accepts: true` |

### Build blockers fixed that belonged to other lanes
- `MelodiaWaterAudioBridgeComponent.cpp:238,241` — **C2445**, ternaries mixing
  `LoadSynchronous()`'s raw pointer with a `TObjectPtr` default. Added `.Get()`.
- `MelodiaWaterNiagaraBridgeComponent.cpp:252` — **LNK2019**,
  `UNiagaraDataChannelReader::Cleanup()` is declared but **not `NIAGARA_API`-exported**, so it
  cannot be called cross-module. Removed; it is an internal lifecycle method on a GC'd UObject.

Both were blocking the entire project's build, and would have failed the moment any lane
tried to compile — the "DLL is locked" reports were masking a real compile failure.

---

## Corrections — claims made this session that were WRONG

Recorded because a wrong claim left standing is this project's most expensive failure mode.
**Four of the five below were mine.**

1. **"`BP_BattleUI::battleController` has 4 reads and 0 writes."** Wrong. `K2Node_CreateWidget_7`
   has an **expose-on-spawn input pin** named `battleController` wired to `Self`. A
   `find_variable_references` census counts `K2Node_VariableSet` nodes and **silently misses
   expose-on-spawn pins**. The runtime error is still real, which points at a second widget
   instance created outside that path — unresolved.
2. **"The allowlist fails closed with no error."** Wrong on both halves.
   `bRelaxedAllowlistInEditor = true` lets unregistered ids **pass with a warning** in every
   non-shipping build; it fails closed only in `UE_BUILD_SHIPPING`. And `Reject()` does log.
   Consequence: an authored typo works in PIE and breaks in a packaged demo.
3. **"`Content/_ThirdParty/TurnBasedJRPGTemplate/` is a pristine copy."** Wrong — 156 Blueprints
   vs 205/206, missing whole subsystems, and its `BP_BattleController` was edited after copying.
   The trustworthy reference is `CompatibilityLabs/TurnBasedJRPGUE58`.
4. **"The Piano handlers lack `UFUNCTION`."** Wrong — all three have it; a `sed` window cut off
   the line above and I misread it.
5. Relayed from another lane: **"PIDs 45144 and 54908 both hold the DLL lock."** Stale — 54908
   was gone and the DLL was writable. Verified before building rather than trusting the report.

---

## Research: six parallel read-only investigations

### Why the note highway has never appeared
**`StockSkillRhythmIds` on `DA_MelodiaIntegrationConfig` is empty.** `ResolveRhythmSkillId()`
returns `NAME_None` → `StartSession` returns 0 → no session can start. **A DataAsset value,
not a graph — T3D cannot fix it.**

Second cause: `SetNoteHighwayActive_Implementation` only *stores* `bNoteHighwayActive` /
`HighwayNotes` / `HighwayBeatPosition` / `HighwayScrollBeatsAhead`. Nothing renders, and
`WBP_MelodiaRhythmHighway` contains none of those names.

Already correct: lane input (`RegisterLaneHit` on Q/W/O/P in both `OnKeyDown` and `OnKeyUp`),
`ShowRhythmGrade`, and the highway creator in `BP_BattleUI::ShowBattleUI`.

### Why the narrative loop cannot complete
The only `melodia_smoke_encounter`-tagged actor is in **`L_KaleidoNave`**; `MelodiaMorningIntro`
runs in **`L_MelusinaMorning`**, and `StartTaggedJRPGBattle` iterates only the current world.
Result: abort → `"unavailable"` → `melodia_smoke_complete` never set.

### Death / survivability
- No post-battle HP restore — **soft-lock vector**.
- No retry on defeat; only exit is `OpenLevel(L_MelodiaMainMenu)`. The stock template
  **never had a game-over system** — an absence in the source, not a regression.
- `NotifyDeathRecovery` / `NotifyRetryRecovery` have **zero call sites**.
- Battle-result exactly-once is **confirmed clean** — no defect.
- `BP_UnitBase` and `BP_BattleBase` are **md5-identical** to the intact template.

### Save/load — mostly already wired
`WBP_MainMenu` binds all three buttons to the canonical slot library; `BP_JRPGGameInstance`
already carries the narrative sync/restore nodes. Those gates are **runtime proofs, not wiring**.
Real gaps: the stock `SaveGameToSlot` path bypasses `IsSavingAllowed()`, and
`LoadCanonicalJRPGSlot` returns `bNarrativeRestored` so callers cannot distinguish "refused"
from "loaded, narrative degraded".

### Party
`PartyPawnClasses` **self-seeds in C++** (index 1 = `BP_SirMelodious_Flight_C`); LeftControl is
bound in C++ on both pawns. The only blocker was `bSirMelodiousExplorationUnlocked` — now
addressed by A4. Note **LeftControl only**; RightControl and gamepad are unmapped.

### A stranded presentation layer
`BP_MelodiaGameMode` has **zero referencers** and is not `GlobalDefaultGameMode`, yet it is the
sole referencer of **both** `WBP_Battle_Rhythm` and `WBP_Battle_Results`. Authored UI that
nothing can reach. Do not wire into either.

---

## T3D injection — proven, with limits

`validate_nodes_t3d` returned `valid: true`, `engine_accepts: true` for a
`K2Node_CallParentFunction`. **The "must be authored by hand" line in
`COOP_SKILL_RESONANCE_SPEC_2026-08-08.md` was an untested assumption and is dead.**
Method and payloads: `Docs/T3D_Patterns/payloads/`.

Open: `MemberParent` still warns `unresolved_member_parent`. Resolve by copying a real
parent-call node and reading its exact `FunctionReference=` spelling. Do not inject while that
warning stands — a bad member ref passes the engine's own gate and imports as a red node.

**No usable baseline exists.** `Content/Exports/` is Aug 1, `BP_BattleController` is Aug 8 23:55,
`Saved/T3D/` contains **neither battle asset**, and only `EventGraph` was ever captured.
Re-export before any injection.

---

## Process lessons

- **Live Coding cannot introduce new imports.** `.cpp`-only edits hot-patch fine; the moment a
  change calls a symbol the binary never imported (`SetDefaultTempo`, `GetState`), it fails.
  Header changes always need a full build.
- **Verify the editor lock directly**, not from a report: attempt a write-open on
  `Binaries/Win64/UnrealEditor-BS_GodFile.dll`. Twice today a "locked" claim was false.
- **A crash report is evidence, not blame.** Two crashes: one was mine (hand-built `UMidiFile`
  with no bar map → null deref in HarmonixMidi), one was not.
- **Don't hand-build engine data structures.** `MakeDefaultSongMap()` shows the required shape:
  `Init(ticksPerQuarter)` + tempo point + **bar map**. A tempo change alone is not a song map.
- **Six read-only explorers in parallel worked well** because none touched the editor. The
  editor is a single exclusive lock; parallelism belongs in source and research lanes only.

---

## Where to start next

`Docs/Handoffs/CORE_SYSTEMS_HANDOFF_2026-08-09.md` — verified state, the corrections above, and
the ordered execution list. First move is `StockSkillRhythmIds`; it is a data edit and it
unblocks the note highway, which has never been seen to work.
