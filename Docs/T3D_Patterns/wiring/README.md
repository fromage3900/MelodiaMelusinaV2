# Battle Controller Wiring — live-verified state (2026-08-08)

Source of truth: **the live graph** via `blueprint_query export_graph`, re-exported on every audit
run to `Exports/bp_battlecontroller_eventgraph_live.json`. The earlier committed exports
(`bp_battlecontroller_eventgraph.json` / `_postfix.json`) are **stale** — the 08-07 session moved
past them (they predate the Sequence fan-out and the UseSkillWithRhythm wiring).

Asset: `/Game/TurnBasedJRPGTemplate/Blueprints/Battle/BP_BattleController` (EventGraph, 699 nodes)

## Status: B3, B4 and B7 are DONE in the live graph

Verified by `Docs/T3D_Patterns/wiring/verify_battle_closure.py` — 10/10 invariants pass:

### B4 — victory/defeat closure (wired)
```
OnBattleOver event -> Fade Out(154) -> Hide Battle UI(53)
  -> Switch on E_BattleResult
       NewEnumerator0 -> Sequence_3 -> then_0: CompleteBattle(45) | then_1: PlayerWon(204)
       NewEnumerator1 -> Sequence_4 -> then_0: CompleteBattle(49) | then_1: EnemyWon(205)
       NewEnumerator2 -> Sequence_5 -> then_0: CompleteBattle(51) | then_1: Keys(99)
Keys(99) -> Update Player Units Data(187) -> Switch to Explore Mode(47)
```
`Keys(99)` on the **Fled** leg is the authored design (dead-unit rewards process whenever the
battle ends with kills), matching the original `_b4` fan-out intent. CompleteBattle 45/49/51 have
free `then` outputs — nothing dangles.

### B3 — rhythm skill seam (wired, double-fire gone)
```
UseMP(115).then -> Use Skill with Rhythm(194) -> Hide Skill Action Buttons(110)
  StockSkill <- Get currentSkill(116)
```
`Start Session` / `Branch` / `Use Skill` double-fire cluster: **absent**. `UseSkillWithRhythm`
(C++ `MelodiaRhythmCombatSubsystem.h:234-255`) defers UseSkill until `FinishSession` latches
`PendingDamageMultiplier` — the notify-vs-latch ~2.5s gap is closed. `Get/Clear Pending Damage
Multiplier` (183/186/34/35) wired in the damage paths.

## Known residuals (editor-session items)

1. **Data orphans** (reported by the audit, safe to remove): `Get currentBattle` (VariableGet_1),
   `Get currentSkill` (VariableGet_97) — no consumers. `sir_cleanup.py`-style removal via
   `remove_node`; re-run audit after.
2. **B7 — grade display: DONE.** `ShowRhythmGrade` function graph (4 nodes, exact C++-expected
   signature `GradeText:String / HitCount:Int / MissCount:Int`, no outputs) is implemented:
   `Entry -> ToText(GradeText) -> SetText(self=RhythmGradeText TextBlock)`. The C++ reflect call
   (`MelodiaUIBridgeSubsystem.cpp:136-163`) will resolve it. HitCount/MissCount params are
   currently unused in the body — display them if the design wants combo feedback.
3. **Sir departure — RESOLVED (option a).** The compiled MorningIntro script
   (`Saved/Sessions/2026-08-07/_morningintro.txt`, statements 0-44) is the departure authority:
   it emits `melodia:battle:melodia_smoke_encounter` after the reunion dialogue and branches on
   `melodia_battle_result` (victory/defeat/fled), then `melodia:flag:melodia_smoke_complete` and
   `$ End`. There is **no** `melodia:travel` and no `BeginWindowDeparture` path — the orphaned
   `HandleMorningIntroEnded` / `Begin Window Departure` nodes in
   `BP_MelodiaSirMelodiousMorningIntro` are legacy dead code. Delete them (reachability-lint
   gated). Do not re-wire option (b).
4. **Rhythm HUD input seam** (BP-side): `SubmitRatedInput` / `OnRhythmComplete` have zero
   occurrences in the battle controller graph BY DESIGN — they live in the presentation rhythm
   component (C++, `MelodiaJRPGPresentationRhythmComponent.cpp:125-148`, already fans out grade +
   NotifyCommandResolved) and the rhythm highway widget. No BP work expected here; verify at PIE.

## Regression gate

```bash
python Docs/T3D_Patterns/wiring/verify_battle_closure.py
```
Exits 1 on any invariant break; re-exports fresh evidence each run. Run it after any future
battle-controller edit, before claiming a P0 battle gate.
