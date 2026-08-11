# Agent Coordination: Quantum + Rhythm Integration

**Date:** 2026-08-06
**Purpose:** Summarize agent-authored handoffs and next actions to stabilise the quantum experiment integration into the rhythm gameplay pipeline.

---

## Key agent-authored references (read these first)

- `QWEN_RHYTHM_SKILLS_SCOPE_2026-08-03.md` — Author: `Qwen3:8b` (subagent). Defines rhythm skill scaffolds, wallet conventions, and grant-id guidance. [Docs/Handoffs/QWEN_RHYTHM_SKILLS_SCOPE_2026-08-03.md]
- `QWEN_HARMONIX_QUARTZ_BATTLE_INTEGRATION_2026-08-03.md` — Author: UE Audio/Rhythm Systems Engineer. Clock and session wiring for rhythm presentation. [Docs/Handoffs/QWEN_HARMONIX_QUARTZ_BATTLE_INTEGRATION_2026-08-03.md]
- `CLINE_WIRING_EXECUTION_2026-08-06.md` — Author: Cline (wiring blueprint expert). Live-coding, enum-pin fix, and PIE verification checklist. [Docs/Handoffs/CLINE_WIRING_EXECUTION_2026-08-06.md]
- `QUANTUM_GAMEPLAY_EXPERIMENT_2026-08-06.md` and `QUANTUM_GAMEPLAY_EXPERIMENT_PROTO_2026-08-06.md` — New: quantum experiment policy and proto for UE↔Python↔Q# contract (classical baseline + Q# kernel). [Docs/Handoffs/]
- `BS_GodFile/AGENTS.md` — Project agent rules; updated with quantum usage guidance.

---

## Short summary

Goal: Use a real Q# experiment as an asynchronous selector for authored rhythm patterns (Cadence Strike vertical slice). Keep grading/timing deterministic in UE. We must coordinate owners so this addition does not violate Decision 009/016/017 (see `QWEN_RHYTHM_SKILLS_SCOPE`).

---

## Recommended owners & responsibilities

- Rhythm Systems (owner): implement UE Blueprint/C++ polling + apply-result logic; ensure `StartSession("CadenceStrike")` triggers an async request and fallback pattern while waiting for the result. Owner: **Audio/Rhythm Systems Engineer** (author of Harmonix handoff).

- Wiring / Live Coding (owner): apply the Monolith enum-pin fix and validate Live Coding workflow during PIE. Owner: **Cline** (wiring blueprint expert).

- Quantum Experiment (owner): maintain `BS_GodFile/Content/Python/quantum` service, wire the Q# kernel to handle >2 candidates as next step, run simulator/azure tests, and publish results to Saved/QuantumResults. Owner: repo maintainer / you.

- QA / PIE (owner): run PIE walk(s), measure latency and result quality vs classical baseline, fill `Docs/PIE_VERIFICATION_CHECKLIST_2026-08-03.md`. Owner: QA engineer / integrator.

- Wallet & Economy (owner): confirm post-battle grant flow; ensure token grants fire only from the post-battle result handler. Owner: Systems Engineer (see Qwen doc).

---

## Immediate next actions (short, assigned)

1. Rhythm Systems: implement Blueprint/C++ polling + apply-result logic that reads `Saved/QuantumResults/<job_id>.json` and applies `winner_id` into the note highway builder. (File to create: EditorUtility/Blueprint that listens for new files). — Owner: Rhythm Systems — Priority: P0
	- Added `BS_GodFile/Content/Python/quantum/ue_apply_result.py` and updated quantum README with editor usage to help this task.

2. Quantum Experiment: extend Q# kernel to support tournament selection (N>2) and add telemetry hooks to log `backend`, `latency_ms`, and `score_delta_vs_classical`. — Owner: Quantum Experiment — Priority: P1

3. Wiring: run Live Coding patch (enum-pin fix) and run PIE terminal path to ensure battle-and-return loop is green. Report using the verified checklist. — Owner: Cline — Priority: P0

4. QA: Run 50 paired tests (classical vs Q#) on `CadenceStrike` candidate sets, measure mean score and mean decision latency. Populate `Docs/QUANTUM_EXPERIMENT_RESULTS_2026-08-XX.md`. — Owner: QA — Priority: P1

5. Documentation: add a short how-to in `Docs/HOWTO_Quantum_Rhythm.md` describing how to run the service, run the editor helper, and wire the Blueprint. — Owner: You / Integrator — Priority: P2

---

## Communication and coordination plan

- Post this file to the repo (done). Ping the owners above in your project chat with links to the files and the short action items.
- Ask each owner for a one-line Ack + ETA in the PR or issue that tracks the work.
- When a task is complete, update the todo list in the repo and file a short test report under `Docs/Handoffs/`.

---

## Pickup points for implementers

- UE rhythm wiring: `Docs/Handoffs/QWEN_HARMONIX_QUARTZ_BATTLE_INTEGRATION_2026-08-03.md` and `CLINE_WIRING_EXECUTION_2026-08-06.md` (use its PIE checklist).
- Quantum service: `BS_GodFile/Content/Python/quantum/service.py`, `layout_ranker.py`, and `qsharp_layout_ranker.qs`.
- Editor helper: `BS_GodFile/Content/Python/quantum/ue_apply_result.py` (reads/writes `Saved/QuantumResults/`).

---

If you'd like, I will open issues/PR templates for each of the five immediate actions and add the owner/ETA placeholders. Which tasks should I open issues for automatically? (default: 1–3)