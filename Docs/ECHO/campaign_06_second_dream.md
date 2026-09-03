# Campaign 06 — Second Dream Expansion (Chapter 2)

**Gate chain:** `ch2_second_dream.dream2_author` → `dream2_runtime` →
`dream2_promote`

**Predecessor:** `ch1_gameplay.promote` (Chapter 1 must be promoted first)

**Lane:** author → gameplay → orchestrator

## Overview

This campaign extends the narrative gameplay loop beyond the First Dream
(Chapter 1). It introduces a new level, new dialogue, and a new encounter that
builds on the proven Melodia rhythm-combat system. The Second Dream is the first
content to ship under the topological Echo system — all Chapter 1 predecessors
must be PASS before this chain begins.

## Gate 1 — `dream2_author` (author lane)

### Evidence required
1. New level (`L_SecondDream`) placed in `Content/Melodia/Levels/`.
2. Dialogue authored via Quill in `Content/Melodia/Dialogue/SecondDream_*.qsc`.
3. New encounter registered in `DA_MelodiaIntegrationConfig` allowlist.
4. `validate-spec` passes against the 7-verb contract.

### Record
```
python Tools/echo_run.py record ch2_second_dream.dream2_author pass --layer ch2_second_dream --lane author --note "level + dialogue + allowlist"
```

### Prerequisite check
```
python Tools/echo_run.py topo check-promote ch2_second_dream.dream2_author
```
This will FAIL unless `ch1_gameplay.promote` is PASS.

## Gate 2 — `dream2_runtime` (gameplay lane)

### Evidence required
1. Editor up, Monolith answering on port 9316.
2. PIE smoke on `L_SecondDream` — 0 crashes.
3. Real-input walk: sanctuary → departure → dream traversal (Q/W keys).
4. JRPG encounter triggers, Victory/Defeat resolved through the combat system.
5. `Melodia.Wiring` Automation RunTests pass.

### Record
```
python Tools/echo_run.py record ch2_second_dream.dream2_runtime pass --layer ch2_second_dream --lane gameplay --note "PIE 0 crashes, Victory path clean"
```

### Editor requirement
This gate is **editor-gated** — it requires the UE editor running with Monolith
MCP active. A HOLD is written if the editor is unreachable.

## Gate 3 — `dream2_promote` (orchestrator lane)

### Prerequisites
- `dream2_runtime` must be PASS.
- `runtime` (Chapter 1) must be PASS (cross-layer dependency).

### Evidence required
1. `git add` exact paths only: level uasset, dialogue .qsc, DA_ config diff.
2. `git_safe_push.py --check-only` passes LFS budget.
3. `record_gate.py --report` updated with campaign evidence.

### Record
```
python Tools/echo_run.py record ch2_second_dream.dream2_promote pass --layer ch2_second_dream --lane orchestrator --note "committed Second Dream content"
```

## Cross-layer dependency

The Second Dream chain depends on `ch1_gameplay.promote`. Even though
`dream2_author` has no other predecessors, the promote gate for Chapter 1 must be
PASS first. This is enforced by the topological DAG:

```
ch1_gameplay.runtime → ch1_gameplay.save_load → ch1_gameplay.repeat_consume → ch1_gameplay.package_launch → ch1_gameplay.promote
                                                                                                                      ↓
                                                                                                        ch2_second_dream.dream2_author → dream2_runtime → dream2_promote
```

## Lane dispatch

- **author** → `x-ai/grok-4.5` (narrative content generation)
- **gameplay** → `deepseek/deepseek-v4-flash` (Blueprint, C++)
- **orchestrator** → `x-ai/grok-4.20-multi-agent` (promote decision)
