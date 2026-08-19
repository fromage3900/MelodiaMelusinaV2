# Campaign 1 — Rhythm→Damage Delta in PIE

> **STATUS 2026-08-13: gate CLOSED. Owner verified real keyboard input through
> `BP_BattleUI::OnKeyDown`.** Ledger row `[PASS] runtime 2026-08-13`, session
> `owner-realkey-20260813`. This campaign is retained as the **method** for a
> rhythm-on/off damage-delta measurement, not as an open gate. Do not re-run it to
> "prove the loop plays" — that question is settled. Re-run it only if you want the
> A/B damage numbers themselves (e.g. for item 4 of AGENTS.md "Next work", the
> damage-scalar sequencing check).

**Gate id:** `runtime`
**Blocks:** nothing — closed 2026-08-13. Was: "everything downstream"
**A/B rule:** Decision 024 — rhythm on vs `melodia.Rhythm.Disable 1`, NOT
full-Perfect vs full-Miss (Decision 016 sets no miss penalty, that delta is
zero by design).
**Evidence:** two damage numbers + a `MELODIA_RHYTHM session=` log line.
**Evidence standard:** AGENTS.md § "Evidence standard — runtime/rhythm gates
(2026-08-11)" applies. In short: a ledger row, real keyboard input, and a
committed report JSON next to the frames. A probe-only run is a HOLD.

## What "PLAYing" means here (and what it does NOT)

The campaign is about a player-facing loop, so the run must exercise the real
input path:

- Real keys through `BP_BattleUI::OnKeyDown` (Q/W/O/P → `RegisterLaneHit`), or
  a documented `InputKey` injection into the focused widget. Calling
  `subsystem.register_lane_hit()` straight from Python proves the native seam
  responds; it does not prove a player pressing keys sees a highway. **That was
  demonstrated by the owner on 2026-08-13**, which is what closed the gate; the
  distinction above remains the standard any future gate must clear.

## Preconditions

1. Exactly one editor on 9316: `Get-Process UnrealEditor` → one PID.
2. `python Tools/echo_run.py status` → editor reachable: yes.
3. Static chain clean: `python Tools/echo_run.py run static_gates`
   (each gate `[ok]`; any HOLD/FAIL blocks this campaign).
4. The `melodia.Rhythm.Disable 1` toggle exists in the build (Decision 024).
5. `Content/Python/rhythm_battle_runtime_probe.py` runs as committed (it was
   fixed 2026-08-11 after a `skill_class` NameError made the committed version
   crash on entry). If you modify the probe, commit it **before** running —
   the harness that produced the evidence must be the harness on disk.
6. The highway-ownership fix in `MelodiaRhythmHUDWidget.cpp`
   (`bExecutionDrivingHighway`) is compiled and **owner-confirmed in PIE
   (2026-08-12 — RHYTHM GAME WORKED)**. See
   `Docs/Handoffs/RHYTHM_GAME_LOCKED_2026-08-12.md`. This campaign still
   requires real Q/W/O/P + ledger packaging; do not reopen highway ownership.

## Run

1. Start PIE on the authored loop route:
   `L_MelusinaMorning → L_KaleidoNave` (`L_Melodia_Dreamstate` was merged into
   KaleidoNave on 2026-08-10). Use the shortest live path that reaches the
   `melodia_smoke_encounter` battle — see `_VERTICAL_SLICE_SCOPE.md` for the tagged actor.
2. Reach the rhythm skill, play a lane run with **real input**. Confirm:
   - beat advances (`UMelodiaMusicClockSubsystem::OnMelodiaBeat`)
   - grade moves (`UMelodiaRhythmCombatSubsystem::RegisterLaneHit`)
   - lanes light on Q/W/O/P and unlight on release (OnKeyUp fix)
   - `ShowRhythmGrade` renders into `RhythmGradeText`
3. Record damage number A with rhythm enabled.
4. Toggle `melodia.Rhythm.Disable 1`, replay the identical input, record
   damage number B.
5. Grep the log for `MELODIA_RHYTHM session=` — the session line must exist
   (it never has; its absence is the whole point of this campaign).
6. Damage A ≠ damage B is the deliverable. If they are equal, the loop is
   still not PLAYing — do not record the gate.

## Evidence artifacts (all three, or it did not happen)

- `MELODIA_RHYTHM session=` log line (excerpt committed with the record).
- Assertion report JSON next to the frames (damage numbers, turn movement,
  error counts) produced by the committed harness.
- The harness that produced both, committed before the run.

## Record

```text
python Tools/echo_run.py record runtime pass --note "rhythm on dmg=A, off dmg=B, MELODIA_RHYTHM session= present"
```

or `fail` with the delta and the log excerpt. A pass with two equal numbers is
a corrupted record — the ledger is only as honest as the row.

**Status 2026-08-13: CLOSED, unconditionally.** The owner verified real keyboard
input through `BP_BattleUI::OnKeyDown`; ledger row `[PASS] runtime 2026-08-13`,
session `owner-realkey-20260813`. Owner statements are ground truth
(`_AGENT_WORKING_AGREEMENT.md` rule 4) — do not go verify it.

History, so the row is readable later: an earlier `pass` was recorded 2026-08-12
18:57 (session `pie_smoke_1_145605`) whose note read *"Restoration wired in
CompleteBattle & PIE smoke session verified on L_KaleidoNave"*. That evidence was
about the result-matrix/restoration path, not real input, so it did not meet this
campaign's own standard. The 08-13 owner verification is what actually closed the
gate; the 08-12 row should be read as a restoration-path record, not an input-path one.

The A/B damage-delta procedure above is still worth running once for the **numbers**
(AGENTS.md "Next work" item 4 — the damage notify may fire ~2.5 s before the scalar
latches). That is a measurement, not a gate.
