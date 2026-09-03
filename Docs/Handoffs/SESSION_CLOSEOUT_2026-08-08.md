# Session closeout — 2026-08-08

Branch: `sonnet-core-mechanics-20260808`. Nine commits. Everything below was verified
against the live graph or the filesystem; no claim here rests on a document.

---

## The headline

**`BP_MelodiaBattleUI` was shadowing its parent with ten empty custom events, including
`ShowBattleUI`.**

A child Blueprint that re-declares a parent's custom event replaces the parent's version in
the generated class. `BP_BattleController` calls `ShowBattleUI` virtually on the constructed
widget — which is the child — so it ran an empty stub, and the parent's implementation,
the one that creates and binds the rhythm highway, never executed. That is why the battle
UI did not appear, and why nothing done to the rhythm layer could have shown up.

The ten are gone; those calls now resolve to the parent. Independently confirmed by a node
title changing itself from "Target is BP Melodia Battle UI" to "Target is BP Battle UI".

This is the purest instance yet of the defect class this project keeps paying for: the
child *looked* complete with all 28 events present, and ten were hollow. No fingerprint,
compile, or smoke test can see it.

---

## Everything fixed

| Fix | Evidence |
|---|---|
| 10 shadowed events removed from `BP_MelodiaBattleUI` | lint 0 violations; closure still 10/10 |
| `BP_BattleUI.OnKeyUp` remapped D/F/J/K → Q/W/O/P | both graphs read back Q/W/O/P, lanes 0-3 aligned |
| 12 orphaned fragments removed from `BP_MelodiaBattleUI` | lint 0 violations |
| 5 debris nodes removed from `BP_MelodiaJRPGGameInstance` | lint 0 violations |
| Floating `AddDelegate` stub removed from MorningIntro | lint 0 violations |
| `WBP_MelodiaRhythmHighway` legend → Q/W/O/P | property read-back |
| Fingerprint baseline moved to tracked path, hard-fails when missing | verified by removing it |
| `bp_regression_checker --update` no longer wipes 277 entries | merge verified, 278 preserved |
| Material gate stops reporting false drift on exporter reordering | 51/4 → 55 clean; 6/6 assertions |
| `graph_reachability` treats macro tunnels as entries | `BP_BattleController` 0 violations |
| `BLUEPRINT_WIRING_CONTRACT` §1 corrected | — |
| `MONOLITH_GUIDE` Recipe 16 step 0 + sibling-graph caveat | — |

### The `OnKeyUp` bug, specifically

`OnKeyDown` had been remapped to Q/W/O/P in a previous session; the sibling `OnKeyUp` graph,
which clears lane state with the *same four keys*, was left on D/F/J/K. So pressing Q lit
lane 0 and releasing it matched nothing — `SetLanePressed(0, false)` never fired and every
lane latched lit for the rest of a session. Fingerprint moved, compile clean, closure 10/10
throughout, because the defect was a pin default in a graph nobody thought to check.

---

## New tooling

All read-only. See `AGENTS.md` § "Verification tools" for the table.

`bp_live_path.py` · `bp_sweep.py` · `ui_style_audit.py` · `t3d_dashboard.py` ·
`project_state.py`, plus assertions in `test_canonical.py` and `test_ui_style_audit.py`.

Writing the tests caught two bugs that would otherwise have shipped into a design spec:
alpha was splitting `#FFFFFF` across seven clusters instead of being one colour at seven
opacities, and `to_hex` clamped HDR so two different glows both printed `#00FFFF`.

---

## Findings not yet acted on

1. **Duplicate content trees.** `BP_BattleUI` exists twice (live + `_ThirdParty` orphan
   island with its own `BP_BattleController`), and
   `Content/MelodiaIntegration/Content_MelodiaIntegration/` is a 33-asset untracked mirror
   dating to 2026-07-26 that still contains the *unfixed* shadowed `BP_MelodiaBattleUI`.
   Every name in it collides with a real asset. Not deleted — untracked means
   unrecoverable, and needs owner sign-off.
2. **Editor crashes.** Five reports today. Root cause is a User Defined Struct with an
   invalid default instance, `S_RoomSettings_BS`, walked by Monolith's own
   `FUserDefinedStructIndexer::IndexAsset`. A mitigation is already applied in the working
   tree (`bIndexEnabled=False`) — decide whether to keep it off or repair and re-enable.
   Full write-up: `Docs/Handoffs/EDITOR_CRASH_DIAGNOSIS_2026-08-08.md`.
3. **Three concurrent editors** caused most of today's instability and the loss of 39
   unsaved packages. Now rule 7 in `AGENTS.md` § Safe working rules.
4. **UI drift.** 137 widget blueprints, 898 styled widgets, 59 distinct font face/size
   pairs, 90 colours collapsing to 46 tokens. Two cyans at HDR gain 214x and 255x.
5. **`BP_BattleUI` (parent) has 17 dead nodes** while the pristine `_ThirdParty` copy has
   zero — so the live copy accumulated them, plausibly during rhythm integration.
   `BP_JRPGPlayerController` has 34.
6. **`bp_sweep` full run is still owed.** It died during the three-editor incident; scoped
   runs are clean. Even 8 blueprints showed 8 empty-bodied events, 2 of them in
   `BP_MelodiaJRPGGameMode`.

---

## Full sweep results

`Tools/bp_sweep.py` over the gameplay scope (`Melodia|TurnBasedJRPGTemplate`, excluding
`_ThirdParty`): **299 blueprints, 663 graphs, 17,176 nodes.**

| Class | Count | Where |
|---|---|---|
| SHADOWED | 10 | **all in the mirror tree; ZERO in live assets** |
| DUPES | 16 | **all caused by the mirror tree; no other structural duplicates** |
| EMPTY | 304 | events declared with no body, project-wide |
| DEAD | 239 | exec nodes with no path from an entry |
| unreadable | 0 | |

The first two rows are the load-bearing result: this morning's `BP_MelodiaBattleUI` fix was
complete, no second instance of the shadowing bug exists anywhere in 299 blueprints, and a
single folder deletion removes 100% of both defect classes.

Worst offenders by weight (empty ×2 + dead), excluding the mirror: the template
`PlayerUnits` base (41 dead), `BP_JRPGPlayerController` (38 dead),
`BP_MelodiaJRPGPlayerController` (37), `BP_Character_PEN` (19), `BP_BattleUI` (18).
Relevant to the polish lanes: `WBP_MainMenu`, `WBP_Battle_Rhythm` and the three Quill
widgets each carry 4 empty events.

Raw output is written to `Saved/Dashboards/` — which is **gitignored**, so it does not
survive a clean checkout. Re-run the tool rather than trusting a stale copy; that is the
intended workflow (a committed export is an output, not an input).

## Corrections made during the session

Recorded because a wrong claim left standing is this project's most expensive failure mode.

- I reported the GameInstance save chain as broken (`shouldLoadTransform_0` /
  `shouldLoadEnemyPawns_0` "never set"). **Wrong** — all 16 events are wired and both
  variables have many live setters; only one orphaned pair was dead.
- I relayed a sub-agent's finding that `SwitchToStaticCamera` and `UnitHasEnoughMP` are
  never invoked. **Wrong** — both are instantiated and wired. The search used the
  identifier form while node titles are spaced.
- I attributed four drifted materials to a parallel session. **Wrong** — nothing had
  changed; the gate was order-sensitive.
- The first crash write-up recommended steps already taken; corrected in place once the
  `bIndexEnabled=False` mitigation was spotted.

---

## Where to start next

`Docs/Handoffs/PARALLEL_LANES_2026-08-08.md` — 14 lanes partitioned by contended resource,
with the editor as an exclusive lock. First priority is unchanged and unblocked:
**observe the rhythm loop in PIE.** Everything is verified connected; nothing is verified
to play.
