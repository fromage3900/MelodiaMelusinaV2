# PIE Verification Checklist — 2026-08-03

**Purpose:** The single repeatable PIE walk that proves the core 20-min slice is actually playable — not just "systems exist." Do NOT claim PIE-readiness until this passes.
**Source-of-truth gates:** `_VERTICAL_SLICE_SCOPE.md`, `_TASK_QUEUE.md`, Kiro 2026-08-01 accounting, `MELODIA_AUTHORITATIVE_RHYTHM_COMBAT_WIRING_2026-08-03.md`.
**Status legend:** [ ] = not run · [x] = passed · [~] = blocked/deferred

---

## 1. Quill / Dialogue / Choice (the historically-buggy area)

The native adapters (`MelodiaQuillDialogWidget`, `MelodiaQuillSelectionWidget`, `MelodiaQuillBackgroundWidget`) carry one-shot guards, disabled-choice rejection, first-valid-choice focus, and scoped Dialogue input context. These are **static-correct** — this walk proves them at runtime.

- [ ] 1.1 Morning Sir interaction → visible Quill dialogue + traversal suppressed
- [ ] 1.2 Click/advance → **exactly one** advance (no double-fire on Enter+click)
- [ ] 1.3 Open a selection → first **valid** choice focused
- [ ] 1.4 Disabled choice cannot submit (click + keyboard)
- [ ] 1.5 Rapid/double input → one selection emitted
- [ ] 1.6 Force the plugin's old viewport bug → background adapter renders correctly
- [ ] 1.7 Close dialogue → input/cursor restore, no `MELODIA_INPUT_LEAK`
- [ ] 1.8 Menu over dialogue → out-of-order close keeps the right owner focused

## 2. Traversal / Input / Focus

- [ ] 2.1 Ground jump works in exploration
- [ ] 2.2 Double-tap glide while rising and falling
- [ ] 2.3 Land → gravity/air control restore
- [ ] 2.4 Begin glide, open Quill dialogue → glide stops immediately
- [ ] 2.5 During dialogue: walk/jump/glide/interact suppressed
- [ ] 2.6 Mouse + keyboard + gamepad dialogue input
- [ ] 2.7 Travel after dialogue → context clear + `placed=1`, no stuck cursor

## 3. Battle / Result Matrix (foundation gate)

- [ ] 3.1 Identify instantiated stock battle widget at runtime
- [ ] 3.2 Attack/Skill/Item/Flee mouse + keyboard + controller parity, no duplicate execution
- [ ] 3.3 **Victory** → resumes/aborts Quill exactly once
- [ ] 3.4 **Defeat** → resumes/aborts Quill exactly once
- [ ] 3.5 **Fled** → resumes/aborts Quill exactly once
- [ ] 3.6 **Unavailable** → resumes/aborts Quill exactly once
- [ ] 3.7 No manual save during an active narrative battle

## 4. Save / Load / Restart (the biggest gate — unblocks Continue/Load)

- [ ] 4.1 Create canonical `BP_JRPGSaveGame` slot
- [ ] 4.2 **Full process exit** → relaunch → load → state equivalent
- [ ] 4.3 One narrative flag restores without duplication
- [ ] 4.4 One reward restores without duplication
- [ ] 4.5 Load canonical slot with Quill unavailable → JRPG state preserved
- [ ] 4.6 Missing/unknown script → authored safe location, valid state not erased
- [ ] 4.7 Wallet restart-idempotence: grant → save → exit → relaunch → repeat grant **rejected**

## 5. Main Menu / Continue / Load (the "uncallable to Melusina" piece)

- [ ] 5.1 Main Menu buttons styled across all 4 states (Normal/Hover/Pressed/Disabled)
- [ ] 5.2 New Game → canonical JRPG GameInstance → exploration → Melusina
- [ ] 5.3 Continue → loads canonical slot (disabled until 4.2 passes)
- [ ] 5.4 Load Game → opens Save/Load screen (disabled until 4.2 passes)
- [ ] 5.5 Continue disabled with no canonical slot + explains why

## 6. Rhythm Combat (new native stack)

- [ ] 6.1 Harmonix clock assigned + registered → `HasMusicalTime()` true
- [ ] 6.2 Author first skill DataAsset rows (Cadence Strike / Lullaby Mend / Dissonant Silence)
- [ ] 6.3 Grade → authoritative request → stock resolver effect
- [ ] 6.4 No-clock behavior: defined fallback, never silent Perfect
- [ ] 6.5 Wallet integration: SP cost spent, shard reward on strong grade

## 7. Route / Travel (021b)

- [ ] 7.1 Morning → KaleidoNave (arrival-side BP fallout from Decision 021b) — diagnose before routing the playtest through it
- [ ] 7.2 KaleidoNave → battle → result → back to narrative

## 8. Launch-Test Packaged Build (the only open packaging item)

- [ ] 8.1 Run `BS_GodFile.exe`, walk Morning → KaleidoNave → battle outside the editor

---

## How to run

1. Editor open, Monolith on :9316 (for diagnostics).
2. Walk each section in order; mark `[x]` only on observed pass.
3. Any failure → record the exact symptom + log line, fix, re-run.
4. Do not mark the slice "PIE-ready" until all non-blocked items are `[x]`.

---

**End of Checklist**