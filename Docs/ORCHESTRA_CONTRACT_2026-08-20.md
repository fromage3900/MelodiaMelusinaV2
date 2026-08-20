# Orchestra Contract — how the pillars meet the authority layers

**Date:** 2026-08-20
**Authority:** [`../../PROJECT.md`](../../PROJECT.md)
**Companion:** [`ORCHESTRA_CONVERGENCE_2026-08-20.md`](ORCHESTRA_CONVERGENCE_2026-08-20.md) (which implementation owns what)
**Modelled on:** [`BLUEPRINT_WIRING_CONTRACT_2026-08-07.md`](BLUEPRINT_WIRING_CONTRACT_2026-08-07.md) — same discipline: every claim traces to a source line or a graph export.

This is the single wiring source of truth for the seams between the four pillars and the two
absolute authority layers.

**Every seam below has one owner and one direction.** A seam with two owners is a defect. A seam
with no proof gate is labelled **UNPROVEN** and may not be described as working.

---

## The absolute authority layers

These two are never rebuilt, wrapped, or competed with.

| Layer | Owns | Location |
|---|---|---|
| **QuillScript** | Narrative, dialogue, choice, the 7-verb notification vocabulary | `Plugins/QuillScript/` |
| **TurnBased JRPG template** | Party, turns, targeting, damage, results, inventory, saves | `BP_MelodiaJRPGGameMode`, `BP_MelodiaJRPGGameInstance`, `BP_BattleController`, `BP_BattleUI`, `BP_JRPGSaveGame` |

Nothing in this document grants a pillar authority over anything in that table.

---

## Seam map

```
  QuillScript ──7-verb notification──► UMelodiaNarrativeSubsystem ──► UMelodiaExternalJRPGBridgeSubsystem ──► JRPG template
                                              ▲    (ConsumeOnce)              StartTaggedJRPGBattle()              │
                                              │                                                                     │
                                              └────────── HandleBattleOver(uint8) ◄─────────────────────────────────┘

  BP_BattleUI::OnKeyDown ──► UMelodiaRhythmCombatSubsystem ──grade──► JRPG damage/result
   (command input, Q/W/O/P)          ▲                                        │
                                     │                                        ▼
              UMelodiaMusicClockSubsystem                        UMelodiaUIBridgeSubsystem
                (Harmonix/Quartz beat)                              (ONE battle-HUD writer)
                                     │
                                     ▼
              UMelodiaRhythmReactivitySubsystem ──► MPC_Melodia_Palette ──► world / material bus
                                                            ▲
  APCGHeroMusicGraphHost ──OnPatternCompleted──►  [ UNWIRED — see Seam 6 ]
   (Piano: music as key)

  UMelodiaWardrobeSubsystem ──► { MI_* Substrate Toon presentation
                                  IMelodiaTraversalCapabilityProvider ──► UMelodiaTraversalComponent }
```

---

## Seam 1 — QuillScript → JRPG battle

| | |
|---|---|
| **Owner** | `UMelodiaNarrativeSubsystem` (the only Quill↔JRPG bridge) |
| **Direction** | QuillScript → Narrative → JRPG. One way. |
| **Carrier** | 7-verb notification string → `UMelodiaExternalJRPGBridgeSubsystem::HandleNarrativeBattleRequested(FName EncounterId)` → `StartTaggedJRPGBattle(FName)` (`MelodiaExternalJRPGBridgeSubsystem.h:34, 46`) |
| **Language** | C++ |
| **Idempotency** | `NarrativeRecord.ConsumedIntentIds` — SaveGame-flagged, so a consumed intent survives reload (`MelodiaNarrativeSubsystem.cpp:177`) |
| **Proof gate** | `repeat_consume` |
| **Status** | **UNPROVEN** — gate open |

The 7 verbs: `battle`, `quest`, `flag`, `travel`, `reward`, `stat`, `item`.
Syntax examples from source: `melodia:stat:<IntentId>:<StatId>:<Delta>` (`:1027`),
`melodia:item:give:<ItemId>:<Count>` (`:1047`, still a logging stub per `echo_pipeline.json`).

**Must not:** any pillar may emit a notification, but **only** `UMelodiaNarrativeSubsystem` may
consume one. No pillar calls the JRPG template directly.

---

## Seam 2 — JRPG battle result → QuillScript resume

| | |
|---|---|
| **Owner** | `UMelodiaExternalJRPGBridgeSubsystem` |
| **Direction** | JRPG → Narrative → Quill. One way. |
| **Carrier** | `HandleBattleOver(uint8 BattleResult)` (`MelodiaExternalJRPGBridgeSubsystem.h:44`) → narrative restore → Quill resumes |
| **Language** | C++ |
| **Contract** | Victory, Defeat, Fled, and unavailable each resume or abort Quill **exactly once** |
| **Proof gate** | Foundation gate "Pass Victory/Defeat/Fled/unavailable"; `rhythm_grade_to_result` for the rhythm-affected case |
| **Status** | **UNPROVEN** — gate open |

**Must not:** retain a duplicate pending result. If Quill resume fails, the result stays
recoverable — see `_VERTICAL_SLICE_SCOPE.md` foundation gate on interpreter invalidation.

---

## Seam 3 — Rhythm input → JRPG damage

**This is the seam that defines the game.** Rhythm rides on JRPG command input; it does not
replace it.

| | |
|---|---|
| **Owner** | `UMelodiaRhythmCombatSubsystem` |
| **Direction** | `BP_BattleUI::OnKeyDown` → rhythm timing window → grade → JRPG damage calculation |
| **Carrier** | Blueprint `OnKeyDown` four `Equal(Key)` nodes (Q/W/O/P) → C++ subsystem |
| **Language** | Blueprint seam, C++ evaluation |
| **Beat authority** | `UMelodiaMusicClockSubsystem` (Harmonix/Quartz) — the only clock |
| **Proof gate** | `rhythm_owner`, `rhythm_grade_to_result` |
| **Status** | Owner-locked WORKED in PIE 2026-08-12; **grade→result edge UNPROVEN** |

**The input seam is Blueprint, not C++.** The C++ remap in `UMelodiaBattleInputComponent` is inert
— that component is only created by `AMelodiaGameMode` (`MelodiaGameMode.cpp:51`), which is not the
live game mode. Documented here so it stops being folklore.

**Must not:**
- Rhythm never becomes the sole input path. The JRPG command decision is the authority; timing
  modifies its outcome.
- Rhythm never owns turn order, targeting, or result type.
- `WBP_MelodiaRhythmHighway`'s lane legend must show Q/W/O/P. It currently shows the retired
  D/F/J/K — **known defect, unfixed.**

---

## Seam 4 — Battle HUD

| | |
|---|---|
| **Owner** | `UMelodiaUIBridgeSubsystem` — **pending the open question below** |
| **Direction** | Native C++ events → widget creation. Widgets never write back into gameplay state. |
| **Carrier** | `CreateWidget<>` at `MelodiaUIBridgeSubsystem.cpp:124, 348, 365` |
| **Language** | C++ |
| **Proof gate** | `hud_single_writer` |
| **Status** | **UNPROVEN — and currently violated.** Two GameInstance subsystems create battle-time widgets independently: `MelodiaUIBridgeSubsystem` and `MelodiaJRPGBattleOverlaySubsystem` (`:64`, `:83`). |

### Open question, blocking this seam

`MelodiaUIBridgeSubsystem.h` documents the current design as: *"The stock UI still renders
underneath (invisible if hidden); Melodia UI is the visible overlay."*

**Does the stock battle UI still need to render, or can it be fully hidden so the Melodia overlay
is the only writer?**

This cannot be answered from source. It needs one editor session, one writer, using
`melodia_ui_get_battle_hud` and `melodia_ui_validate_widget`. **Record the answer here when known.**

**Must not:** no widget may be written by two owners in the same frame. Merging
`MelodiaJRPGBattleOverlaySubsystem` into `MelodiaUIBridgeSubsystem` is required regardless of how
the stock-UI question resolves.

---

## Seam 5 — Wardrobe → presentation and gameplay

The wardrobe pillar has **two** outputs, and they are separate seams sharing one owner.

| | Presentation | Gameplay |
|---|---|---|
| **Owner** | `UMelodiaWardrobeSubsystem` | `UMelodiaWardrobeSubsystem` as `IMelodiaTraversalCapabilityProvider` |
| **Direction** | equipped outfit → Substrate Toon `MI_*` instances | equipped outfit → capability → `UMelodiaTraversalComponent` |
| **Carrier** | `UMelodiaWardrobeComponent` mirrors equipped state to the subsystem (`MelodiaWardrobeComponent.h:6`) | `QueryTraversalCapability(FName CapabilityId, FName ContextId, FName& OutBlockReason)` |
| **Vocabulary** | `wardrobe_catalog_contract.v1.json` | `MelodiaTraversalCapability::{Glide, Dash, Swim}` (`MelodiaTraversalCapabilityProvider.h:32-38`) |
| **Proof gate** | `wardrobe_equip_roundtrip` | `wardrobe_gameplay_hook` |
| **Status** | **UNPROVEN** | **UNPROVEN** |

**This is the Infinity Nikki pattern and it is already built** — outfits grant traversal
abilities. The registry rejects multiple providers to avoid split capability truth.

**Must not:**
- Only **one** capability provider per game instance. The registry enforces this; do not add a second.
- Capability ids are declared **once**, in `MelodiaTraversalCapabilityProvider.h`. They were
  previously raw string literals in two modules with nothing keeping them in agreement — rename one
  side and the ability *silently stops working* (the header documents this failure directly).
- A capability id with no provider mapping and no caller is a name with no behaviour. Adding one is
  not the same as implementing it.
- The wardrobe never touches damage, turns, or party state.

---

## Seam 6 — Music as key → world consequence

**This seam is the one genuine gap, and it is one edge wide.**

| | |
|---|---|
| **Owner** | `APCGHeroMusicGraphHost` (emitter) → `UMelodiaNarrativeSubsystem` (consumer) |
| **Direction** | pattern completion → narrative state. One way. |
| **Carrier** | `OnPatternCompleted` broadcast (`PCGHeroMusic.cpp:620`) → **[UNWIRED]** → 7-verb `melodia:flag:` or `melodia:quest:` notification |
| **Language** | C++ |
| **Proof gate** | `music_world_key` |
| **Status** | **NOT WIRED** |

### What exists

The full music-as-key loop is built: PCG-spawned piano keys (`APCGPianoKey`, real MIDI notes),
steppable world note-nodes with overlap triggers and spring physics (`APCGHeroMusicNode`), pattern
scoring with streak and grade (`APCGHeroMusicGraphHost::ScoreState`), real content in
`Content/EnvSandbox/PCG/Musical/`, and a complete Python authoring pipeline with its own test.

### What is missing

`OnPatternCompleted` has exactly **one** consumer: `UMelodiaPCGWaterGameplayBridgeComponent`
(`:48`), which routes it into water gameplay. It never reaches narrative, quest, or traversal
state.

### The boundary that must be preserved

`PCGHeroMusic.cpp:624` states it deliberately:

> *"Presentation-only: the existing reactivity subsystem owns the shared material bus and never
> enters the combat or damage pipeline."*

**Keep that boundary.** Music must not become a second combat authority. But "never enters combat"
is not "never has a consequence" — a Zelda ocarina does not deal damage, it opens a door.

### The action

Wire `OnPatternCompleted` to **one** 7-verb narrative notification. `UMelodiaNarrativeSubsystem`
already owns idempotency via `ConsumedIntentIds`, so replaying the pattern cannot double-grant.

**Must not:** the puzzle layer never calls the JRPG template, never deals damage, and never
becomes a second traversal authority. It emits a notification; Narrative decides what it means.

---

## Seam 7 — Audio → world material bus

| | |
|---|---|
| **Owner** | `UMelodiaRhythmReactivitySubsystem` — owns the shared material bus and OSC emission |
| **Direction** | beat/grade → `MPC_Melodia_Palette` → materials, water, Niagara |
| **Carrier** | `UMelodiaAudioReactivePresentationSubsystem::TickPresentation` → MPC writes |
| **Language** | C++ |
| **Proof gate** | covered by M3 (DONE) for the material half |
| **Status** | **LIVE** |

Six live call sites feed it: `MelodiaAudioReactivePresentationSubsystem.cpp:141`,
`MelodiaJRPGPresentationRhythmComponent.cpp:195`, `MelodiaTraversalComponent.cpp:1012`,
`Piano/PCGHeroMusic.cpp:89, 581, 626`.

**Must not:** MPC writes happen on the game thread. Writing from a listener/daemon thread is a
silent no-op — this was a real defect fixed in `Content/Python/osc_server.py`; do not reintroduce
the pattern.

---

## Seam status summary

| # | Seam | Owner | Gate | Status |
|---|---|---|---|---|
| 1 | Quill → JRPG battle | `UMelodiaNarrativeSubsystem` | `repeat_consume` | UNPROVEN |
| 2 | JRPG result → Quill resume | `UMelodiaExternalJRPGBridgeSubsystem` | result matrix | UNPROVEN |
| 3 | Rhythm input → JRPG damage | `UMelodiaRhythmCombatSubsystem` | `rhythm_owner`, `rhythm_grade_to_result` | Partly locked; grade edge UNPROVEN |
| 4 | Battle HUD | `UMelodiaUIBridgeSubsystem` | `hud_single_writer` | **VIOLATED** — two writers |
| 5a | Wardrobe → presentation | `UMelodiaWardrobeSubsystem` | `wardrobe_equip_roundtrip` | UNPROVEN |
| 5b | Wardrobe → traversal capability | `UMelodiaWardrobeSubsystem` | `wardrobe_gameplay_hook` | UNPROVEN |
| 6 | Music as key → world | `APCGHeroMusicGraphHost` → Narrative | `music_world_key` | **NOT WIRED** |
| 7 | Audio → material bus | `UMelodiaRhythmReactivitySubsystem` | M3 | LIVE |

**One seam is violated (4), one is unwired (6), five are unproven.** None require new systems —
all seven have their machinery built.

---

## Rules this contract establishes

1. **One owner per seam.** A second owner is a defect, not a feature.
2. **Pillars talk to the authority layers through named seams only.** No pillar calls the JRPG
   template or QuillScript directly.
3. **An unproven seam may not be described as working.** Use the ledger:
   `python Tools/echo_run.py record <gate> pass|fail`.
4. **Music opens doors; the JRPG template deals damage.** The presentation-only boundary in the
   Piano module is load-bearing architecture, not a limitation to route around.
5. **Capability vocabularies are declared once.** Duplicated string literals across modules fail
   silently.
