# Jev plan audit — Holo4 overnight eval

Date: 2026-10-05 · Prototype: `Prototypes/JevHolo4EvalAudit/` · Skill: `system-one-conductor`
Provenance: **`source=jev-live`** — one `system_one` call, Choice + Choice + Noul + Score over one state.
Contract tests: **41/41 pass**.

## The verdict

| Question | Jev (live) | Classical fallback | |
|---|---|---|---|
| Next block | `LET_MATRIX_FINISH` (0.67) | `LET_MATRIX_FINISH` | agree |
| **Riskiest assumption** | **`GROUNDING_HOLDS_ON_LIVE_SOURCE` (0.47)** | `COMPUTE_IS_THE_BOUNDING_CONSTRAINT` | **disagree** |
| Owner decision gates next block? | yes, p=0.72 | — | |
| Readiness | 2 — "at least one task completed through tools with an artifact verified on disk" | 2 | agree |

### The disagreement is the finding

I expected the riskiest assumption to be **compute**. On this box that looks
obvious: 12 GB VRAM shared against a live editor, 1.36 tok/s, 12–24 min per answer.

Jev put **0.47 on grounding holding on live source** and only **0.09 on compute**.
Reasoning from the state: the prior grounding result was 17/17 verbatim quotes
with zero fabrications — but that was measured on a *small fixture*. T1 feeds it
1328 lines of real production C++.

That inversion matters more than a compute ceiling. A slow model costs time. A
model that emits **confident, fluent, false citations into `MelodiaNarrativeSubsystem.cpp`**
is a production hazard: fabricated code reads as authoritative, and the verdict's
best-measured strength is exactly the property under test.

**T1 is therefore not a formality — it is the test that can move the verdict from B toward D.** If it
hallucinates a verb on live source, everything else about the model becomes moot.

### Two defects the harness caught in my own code

Both were found by contract tests before any live call, which is the point of them:

1. **The classical fallback emitted a malformed distribution** — `riskiest_probs`
   summed to **0.85**, not 1.0. This is the same index/malformed-list defect the
   live guard rejects. The fallback was modelling the very failure it should never
   exhibit. Fixed by normalizing.
2. **My isolation test banned the word `Perforce`** and therefore failed the
   docstring line `NO Perforce` — the line promising not to touch Perforce. A prose
   ban punishes the safety statement. Rewritten to parse the AST and assert on
   **imports** instead of words.

### Live-call integrity notes

- **Key shape validated before the call** — `apikey_` prefix, no whitespace. A
  poisoned key fails late and opaquely as `Illegal header value`, minutes lost.
- **SDK 0.7.0, current `system_one(state=..., questions={id: q})` shape.** Confirmed
  `.create()` / `.ask()` are dead on this version.
- **The import is NOT wrapped in try/except.** A bare catch returning `None`
  silently relabels a live run as a fallback whose reason string then lies.
- **`readiness_probs` came back malformed** and the harness reported it rather than
  presenting indices as probabilities. The `Score` integer (`2`) is usable; its
  distribution is not. Recorded, not tidied away.

## Next block

**`LET_MATRIX_FINISH`.** Change nothing until all four tasks land. Every other
decision is downstream of one answer: can Holo4 complete a multi-step task through
tools with output anyone verifies?

Second-place option was `FIX_TRUNCATION_FIRST` at 0.31 — real, but only worth acting
on *after* T1 shows whether truncation is destroying the grounding result or merely
clipping its tail.

**Not** `PROMOTE_TO_ROUTER` at 0.00. Licence (CC BY-NC) plus a 12 GB card shared with
a live editor rules it out regardless of how the tasks score.

## Rollback

Delete `Prototypes/JevHolo4EvalAudit/`. It imports nothing from production, runs no
subprocess, writes exactly one file (`audit_log.json`), and touches no `.uasset`,
editor, ledger, or Perforce state.

`CURRENT_STATE.md` is deliberately **not** modified. If any of this earns canonical
status it lands there through the normal single-writer path.