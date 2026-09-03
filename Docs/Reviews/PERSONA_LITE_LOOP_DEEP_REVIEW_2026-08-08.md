# Persona-Lite Loop — Deep State Review (2026-08-08)

**Reviewer basis:** live Monolith (1330 actions, editor up) + committed C++/exports + compiled
QuillScript assets + task queue. Verification tiers used below:
**LIVE** = verified against the running editor/graph exports this session ·
**BUILT** = source/wiring present, no PIE proof ·
**OPEN** = work remaining.

## The loop, segment by segment

```
sanctuary conversation -> authored departure -> dream traversal -> one encounter
  -> typed result -> narrative consequence -> stable checkpoint/save
```

### 1. Sanctuary conversation — `L_MelusinaMorning`
| Item | Tier | Evidence |
|---|---|---|
| MorningIntro Quill script (reunion dialogue, option branch, battle notify, result branches, reward, flag, `$ End`) | **LIVE** | Compiled export `_morningintro.txt` (44 statements, full source readable) |
| Interpreter spawn + Start on BeginPlay (`BP_MelodiaSirMelodiousMorningIntro`) | BUILT | Graph export (`_sirmel_full.txt`) |
| Quill→JRPG bridge (7-verb allowlist, `melodia:battle:` dispatch) | BUILT | `MelodiaNarrativeSubsystem.cpp` (committed) |
| Dialogue UI skin + input-context push | BUILT | `MelodiaQuillPresentationWidgets.cpp:115-117` |
| Legacy dead nodes (`HandleMorningIntroEnded`, `Begin Window Departure`) | **LIVE** | Verified disconnected; `sir_cleanup.py` ready (dry-run passed) |
| Dialogue renders + notifies in PIE | **OPEN** | Owner 08-06: "dialogue not visible" — un-re-tested |
| Morning_RoomShell validator contract | **OPEN** | P0 gate; missing actor label |

### 2. Authored departure — RESOLVED this session
- **The departure authority is the Quill battle notification**, not travel and not
  `BeginWindowDeparture` — the compiled MorningIntro emits `melodia:battle:melodia_smoke_encounter`
  after the reunion branch. The orphaned departure nodes are dead code (option (a) in the runbook).
- `Dreamstate_WakePortal` destination fixed → `L_KaleidoNave` (B5). **Open risk:** portal targets a
  level that streams the level it lives in — re-entry loop possible; watch in the PIE walk.

### 3. Dream traversal — `L_KaleidoNave`
| Item | Tier | Evidence |
|---|---|---|
| Encounter actor tagged `melodia_smoke_encounter`, stock contract resolves | **LIVE** | 08-06 audit: exactly 1 actor, `StartBattle` CustomEvent + `offLevelBattleData` + `OnBattleOver` |
| Arrival trigger BP (`BP_KaleidoNaveArrivalTrigger`) built + placed | BUILT | Committed `c29fa3af` |
| Travel authority + allowlist + spawn placement | **LIVE** | `UMelodiaTravelSubsystem`; Kiro 08-01 readback (6/6 nodes) |
| End-to-end walk Morning→KaleidoNave→battle→return | **OPEN** | First PIE claim |

### 4. Stock JRPG encounter — `BP_BattleController`
| Item | Tier | Evidence |
|---|---|---|
| B3 rhythm seam (`UseSkillWithRhythm`, damage latch) | **LIVE** | `verify_battle_closure.py` 10/10 PASS |
| B4 result closure (Switch→Sequence→CompleteBattle 45/49/51 + legs) | **LIVE** | Same audit; Keys(99) on Fled leg = authored design |
| B7 grade display (`ShowRhythmGrade` implemented) | **LIVE** | Function graph export (4 nodes, correct signature) |
| Battle UI creation (B1) | BUILT | 08-07 wiring, compiled |
| Input parity Attack/Skill/Item/Flee (mouse/KB/controller) | **OPEN** | P0 gate |
| Victory/Defeat/Fled/unavailable result matrix | **OPEN** | P0 gate; each must resume/abort Quill exactly once |
| Rhythm HUD legend shows stale D/F/J/K | **OPEN** | P1; keys remapped Q/W/O/P in `OnKeyDown` |

### 5. Typed terminal result
- C++ resume path built (`ResumeQuillOnce`, idempotent intent consumption); **result-matrix gate OPEN**.
- Interpreter invalidation during broadcast: **OPEN** (P0).

### 6. Narrative consequence
| Item | Tier | Evidence |
|---|---|---|
| Reward IDs emitted (smoke_reward; solstice_drum/dawn_veil) | **LIVE** | Compiled .qsc exports; allowlist + equipment rows in author script (lines 88-92, 115-116) |
| Flag `melodia_smoke_complete` emitted | **LIVE** | Compiled export statement 39 |
| Flag+reward restore without duplication across save/load | **OPEN** | P0 gate |
| Missing/unknown script routed to safe location | **OPEN** | P0 gate |

### 7. Stable checkpoint/save — both documented wiring defects FIXED in live
| Item | Tier | Evidence |
|---|---|---|
| `OnNewGameStarted → Create Save Game Object` | **LIVE** | GameInstance EventGraph export (`CustomEvent_2 → CallFunction_1`) |
| Canonical slot `slotName_0 = "MelodiaJRPGSlot0"` used by Save Game to Slot | **LIVE** | Variable default + pin feed |
| LoadThisGame + travel-routed load fallback | BUILT | `MelodiaSaveSlotLibrary.cpp` |
| Cross-process restart round-trip | **OPEN** | P0 gate — the top blocker |
| Load with Quill unavailable, preserve state | **OPEN** | P0 gate |
| Manual save disabled during narrative battle | BUILT | Input-context `IsSavingAllowed`; runtime proof OPEN |

## Cross-cutting state

| Item | Tier | Notes |
|---|---|---|
| Startup: `L_MelodiaMainMenu`, GI `BP_MelodiaJRPGGameInstance`, GM `BP_MelodiaJRPGGameMode` | **LIVE** | `DefaultEngine.ini` |
| Main Menu New Game/Continue/Load → canonical GI | **OPEN** | P0 gate |
| Packaged build (2.1 GB, 5 maps) exists | BUILT | Launch test OPEN (P0) |
| Melody Token: mesh + 4 material variants + texture sets on disk | **LIVE** | `SM_MelodyToken`, `MI_MelodyToken_*` (local-only under EnvSandbox) |
| Token pickup actor + HUD widget | **OPEN** | Registry index stale; disk shows no pickup/BP HUD yet |
| Wallet restart-idempotence (grant→exit→relaunch→reject) | **OPEN** | P0 — the one case that reaches players |
| Regression gate | BUILT | 49 tests; 2 roguelike failures known/P3 |
| Material baseline gate | **LIVE** | 55 clean |
| PIE smoke gate | **LIVE** | ok-rule fixed; `ok_reason` mandatory |
| Sir rescue | BUILT | Compiled 01:49; PIE recruit proof OPEN |
| Skybound Refrain conditional bonus / Sir visuals | OPEN | P1 |

## Core remaining tasks — dependency-ordered

### First claim (everything else hangs off it)
1. **PIE walk of the route** `L_MelusinaMorning → battle → result → return`, gated by the fixed
   smoke runner (capture + `ok_reason` clean). This re-tests the 08-06 "not playable" verdict —
   the loop's wiring is now substantially different (B1/B3/B4/B7 + save fixes all landed since).

### Save foundation (P0)
2. Canonical save round-trip across **process restart** (slot `MelodiaJRPGSlot0`; grant-id
   idempotence is in scope here).
3. Wallet restart-idempotence test (same restart; must reject re-grant).
4. Flag + one reward restore without duplication (reopen-dialogue + reload paths).

### Result/edge gates (P0)
5. Victory/Defeat/Fled/unavailable result matrix — Quill resumes/aborts exactly once each.
6. No manual save during active narrative battle (input-context runtime proof).
7. Interpreter invalidation during terminal-result broadcast (recoverable pending result).
8. Input parity Attack/Skill/Item/Flee (mouse, keyboard, controller).

### Defensive gates (P0)
9. Load canonical slot with Quill unavailable → state preserved.
10. Missing/unknown script → authored safe location, without erasing valid state.

### Packaging (P0)
11. Main Menu New Game/Continue/Load → canonical GameInstance.
12. Launch-test the packaged build (walk outside the editor).
13. Morning_RoomShell validator contract repair/revise.

### Cleanup + P1 (do in any order, all gated)
14. `sir_cleanup.py --go` (dead departure nodes) + remove 2 verified data orphans in BP_BattleController; re-run audits.
15. Rhythm highway legend Q/W/O/P.
16. Token pickup + HUD (Kiro lane; mesh/materials done).
17. Skybound Refrain conditional bonus; Sir battle mesh/portrait/anim.
18. Portal re-entry-loop check during PIE walk.

## Corrections to the docs record (this session)

- **B3/B4/B7 are DONE** (live audit) — the 08-06/07 "stub/double-fire" findings predate the
  session's wiring; the committed `_postfix` export was stale vs the live graph.
- **Save-chain wiring defects are FIXED** (live export): `OnNewGameStarted` creates the save object;
  slot is canonical.
- **Sir departure resolved** — legacy dead code, not a missing wire.
- **WBP highway legend** and wallet pickup remain genuinely open; the stale asset-registry index
  must not be used as evidence either way.

## Risks

1. **Doc drift remains the top hazard** — this review itself will age; the audits
   (`verify_battle_closure.py`, `verify_baseline.py`, fixed smoke runner) are the durable truth.
2. Portal re-entry loop (B5 sublevel streaming).
3. PIE may surface runtime errors the fixed gate will now honestly fail — budget for a first
   failing pass; that is the gate working, not a regression.
4. Push still blocked; 61+ commits ahead of origin (local-only risk).
