# DeepSeek — Handoff 2026-08-12 (afternoon: core gameplay closeout, read-only lane)

**Host:** DeepSeek via OpenRouter (`deepseek/deepseek-v4-flash` — the stale `deepseek-v4` slug was
fixed in `87b2938d`; do not use the old one). Router: `Tools/model_router.py`.
**Lane:** **read-only source analysis and written verdicts.** You have the sources; you do not have
the PC, the editor, or PIE.
**Repo state:** `main` @ `62c7920d`, in sync with `v2/main`.

> Your output is a **verdict with quoted call order**, not a patch and not a plan. Every previous
> cloud lane that produced a plan instead of a verdict added work rather than removing it.

## ⚠ Lane separation — read before you touch anything

**Muse is working the same closeout in parallel, on the host, right now.** Muse owns the *edits*;
you own the *verdicts*. Do not write into Muse's files.

| Owner | Files |
|---|---|
| **Muse** (do not touch) | `Source/**` incl. `MelodiaJRPGPostBattleLibrary`, `Tools/lane_dispatcher.py`, `Tools/memory_index.py`, `AGENTS.md`, `deploy/surreal_arch/**`, `.gitignore` |
| **You** | `Docs/Reports/*_VERDICT_2026-08-12.md` — new files only |

Muse is wiring `RestorePartyAfterBattle` (closeout Step 5). **Your D2 verdict reads the same
battle-end path.** Read it, do not edit it, and if your verdict contradicts what Muse implemented,
say so in the verdict — do not fix it yourself.

---

## 0. The evidence standard — this is the whole point of your lane

**A gate is certified only when `record_gate.py <id> pass` has written a row.** Prose in a session
log is not a row. You cannot write rows. Therefore your job is to make the owner's editor session
as short as possible by settling in advance every question that can be settled from source.

Current ledger (22 rows, `Saved/gate_ledger.json`):

| Gate | Status |
|---|---|
| `runtime` | **fail** (honest row, 2026-08-11) — THE blocker |
| `static_gates` | ~~fail~~ → **PASSING** as of `0e34eaed` (Muse lane, 2026-08-12): 12 material drifts accepted, graph_reachability/bp_sweep scoped to shipped defects, static chain ALL OK. Do not analyze this gate. |
| `save_load` | **open** — never closed, not once |
| `repeat_consume` | **open** |
| `package_launch` | **open** |

Thirteen earlier gates pass (`jump_windup`, `sprint_speed`, `material_slots`, `save_system`,
`pie_smoke`, `gameplay_smoke`, `battle_encounter`, …). Do not re-open them.

---

## 1. Settled — do not re-derive these

| Fact | Source |
|---|---|
| Damage-scalar sequencing **PASS**, call order quoted | `78867a33` |
| `curentMP` typo is real in stock `S_PlayerUnitData`; library spelling correct; only call-site wiring remains | `533352d8` |
| `PendingDamageMultiplier` must **not** be reset on invalidate — `StartSession` owns the reset. This is deliberate. Do not flag it. | closeout plan §Step 3 |
| Route is Morning → KaleidoNave; Dreamstate merged out | closeout plan §Step 4 |
| Beat map is loaded from the `128BPMarpeggiomelody_beatgrid` MIDI, never hand-built | `MelodiaMusicClockSubsystem.cpp:50-51,167-179` |
| Highway-ownership fix is **compiled** | `MelodiaRhythmHUDWidget.cpp:146-151` | **Superseded:** owner confirmed rhythm highway WORKED in live PIE on 2026-08-12. See `RHYTHM_GAME_LOCKED_2026-08-12.md`. |

---

## 2. Your tasks, in order

### D1 — Save round-trip idempotency audit (pre-clears gates `save_load` + `repeat_consume`)

This is the highest-value thing you can do, because **Step 7 has never closed** and the failure it
catches is exactly the kind visible in source.

Read and produce a written verdict on:

- The canonical save chain against slots `MelodiaJRPGSlot0/1/2` (`MelodiaSaveSlotLibrary.h/.cpp`,
  `MelodiaSaveRecoverySubsystem.h/.cpp`, `BP_JRPGSaveGame`).
- **The specific question:** is there any reward, stat, or dialogue-consumption guard that lives in
  **memory only** and would therefore double-pay after a full editor exit and relaunch? Name the
  member, the file, and the line. An in-memory `TSet<FGuid>` of consumed intents that is never
  serialized is the archetype — say so explicitly if you find one, and say so explicitly if you
  do not.
- `melodia:stat:` idempotency per `<IntentId>`. Two *different* beats awarding the same stat is
  allowed; the same beat awarding twice is not. State which one the code implements.

**Deliverable:** `Docs/Reports/SAVE_IDEMPOTENCY_VERDICT_2026-08-12.md` — verdict first line
(`PASS` / `FAIL` / `HOLD` + one clause), then the quoted call order, then the file:line evidence.

### D2 — Result-matrix reachability verdict (pre-clears Step 6 / Campaign 4)

Four outcomes — **Victory, Defeat, Fled, unavailable** — must each resume or abort Quill
**exactly once**. From source only, answer for each of the four:

1. Which code path reaches it?
2. Does that path call `ResumeQuillOnce()` exactly once, more than once, or never?
3. Is there a stub-silent defeat (a branch that returns without resuming)?
4. Can a pending result be lost, or a mid-battle save be taken?

Cross-check against `verify_battle_closure.py` (the 10/10 precondition) and
`MelodiaJRPGBattleOverlaySubsystem` / `MelodiaExternalJRPGBridgeSubsystem`.

**Deliverable:** `Docs/Reports/RESULT_MATRIX_VERDICT_2026-08-12.md`, a four-row table with file:line
per row. A row you cannot settle from source is **HOLD**, not a guess.

### D3 — Input-path disambiguation (de-risks the `runtime` gate before the owner sits down)

The 6-lane intake reached consensus that the input path is ambiguous: **raw `OnKeyDown` vs Enhanced
Input**. The `runtime` gate needs real keys through `BP_BattleUI::OnKeyDown` → `RegisterLaneHit`;
probe-only is a HOLD.

Settle from source, and only from source:

- Which authority actually receives Q/W/O/P during battle — `BP_BattleUI::OnKeyDown`, or
  `UMelodiaInputContextSubsystem` / Enhanced Input? If both are live, say which wins and why.
- Does the widget have focus at the moment the battle UI appears? Name what sets it.
- Do lanes unlight on `OnKeyUp`, and is `ShowRhythmGrade` reachable from the same path?
- `MELODIA_RHYTHM session=` has **never once appeared in a log**. From source: what is the exact
  precondition chain that would emit it? List every condition, in order, that must be true.

**Deliverable:** `Docs/Reports/INPUT_PATH_VERDICT_2026-08-12.md`. That last list is the most useful
artifact you can produce today — it turns the owner's editor session from exploration into a
checklist.

### D4 — Kimi's Q/W/O/P ergonomics finding (one paragraph, no more)

Kimi flagged that **W→O is a 6-key hand shift** on the rhythm layout. This is a *feel* decision the
owner owns. Write one paragraph: the shift distance, the alternative layouts that keep the same
lane count, and stop. Do not redesign the input map.

---

## 3. Hard boundaries

- **Read-only.** No edits to `Source/`, `Content/`, `Config/`, or any `.uasset`. Your commits are
  Markdown reports under `Docs/Reports/` or nothing.
- **Do not record a gate row.** Ever, from this lane.
- **Do not produce runtime claims.** No cloud lane has ever produced runtime evidence, and the
  consensus from the 6-lane fan-out was that pretending otherwise is the project's main failure
  mode. Confirming the evidence standard is not the same as meeting it.
- If a paid-model call 402s, you have hit the free-tier daily quota. Fall back to a free model and
  say in the report which model produced the verdict.

---

## 4. Format contract for every deliverable

```
VERDICT: PASS | FAIL | HOLD — <one clause>

<quoted call order, in execution sequence>

<file:line evidence, one per claim>

<single "one real thing I noticed" line, optional>
```

No executive summaries. No recommendations sections. No next-steps tables.
