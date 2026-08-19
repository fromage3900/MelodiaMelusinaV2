# Today — 2026-08-19 parallel plan

**Supersedes** §8 evening checklist in [`NEMOTRON_OPENCODE_UE_RESEARCH_2026-08-19.md`](NEMOTRON_OPENCODE_UE_RESEARCH_2026-08-19.md) for execution order.

**Spec:** [`specs/nemotron_experiment_harness.json`](../../specs/nemotron_experiment_harness.json)  
**Audit dir:** `Saved/Audit/nemotron_harness_2026-08-19/`  
**T3 ground truth (repo):** `specs/nemotron_ground_truth/T3_handle_quill_notification.json`  
**Runtime copies:** `Saved/Audit/nemotron_harness_2026-08-19/` (gitignored, local evidence)

---

## Two lanes — do not block each other

| Lane | When | Owner | Blocks editor? |
|---|---|---|---|
| **A — No editor** | NOW | Cloud agent / grep / git | No |
| **B — Editor open** | Background OpenCode tabs | Owner workstation | Yes (one UE) |
| **C — Editor closed** | After B | Owner | Build only |
| **D — Claireon session** | After C connects | New session | Yes (one UE) |
| **E — VS P0** | When editor free for PIE | Owner | Yes — **still P0 for livelihood** |

Rhythm + Quill remain **LOCKED WORKED**. Runtime ledger (real keys) is still VS P0 when you have a PIE window — it does not wait for Nemotron.

---

## Lane A — NOW (parallel, no editor)

Execute in order; any step can run while UE is closed.

```
pull main
  → Nemotron Phase 0 (audit dir, OpenRouter config, pin OpenCode version)
  → Phase 1a: no-MCP smoke (Nemotron Super single-turn, no tools)
  → T3 grep task (ground truth already in audit/ground_truth/)
```

### Checklist

- [ ] `git checkout main && git pull origin main` (workstation; cloud: merge or rebase doc branch)
- [ ] `Saved/Audit/nemotron_harness_2026-08-19/` exists
- [ ] OpenRouter key in `~/.config/opencode` or env — **not committed**
- [ ] Phase 1a prompt: *"Reply with the word OK and list three files in Tools/ whose names start with bp_"*
- [ ] Phase 1a record → `run_nemotron_super_1a_smoke.json`
- [ ] T3: run grep path in OpenCode **or** score agent output against `ground_truth/T3_handle_quill_notification.json`
- [ ] Optional: send **Digital Extremes** + **Promethean AI** applications (75 min, no UE)

### T3 scoring (no MCP required)

Agent must identify:

1. `QuillscriptInterpreter.cpp:849` → `OnNotified.Broadcast`
2. `MelodiaNarrativeSubsystem.cpp:64` → `AddUniqueDynamic` bind
3. Test direct calls in `MelodiaIntegrationTests.cpp`
4. No false Blueprint callers

---

## Lane B — WHILE EDITOR OPEN (background OpenCode tabs)

**One UnrealEditor.** Monolith on `:9316` only. Fresh OpenCode session per model per task.

```
Phase 1b: T1 with Monolith (Nemotron Super via OpenRouter)
Phase 2:  T1 + T4 + T5 × 3 models
```

### Models (Phase 2)

| # | Model | Provider |
|---|---|---|
| 1 | Claude Sonnet 4.5 | Anthropic |
| 2 | Nemotron 3 Super 120B | OpenRouter |
| 3 | Qwen3-Coder **or** DeepSeek | OpenRouter / configured |

**Skip:** Nemotron Ultra via NIM (#34026 hang). Ultra via OpenRouter only if Super passes 1b.

### Tasks

| ID | Needs UE | Prompt summary |
|---|---|---|
| T1 | Yes | `BP_BattleUI` OnKeyDown lane keys → JSON |
| T4 | Yes | `DA_MelodiaIntegrationConfig` TravelLevelIds vs AGENTS.md |
| T5 | No | `bp_sweep.py` scoped run → one paragraph |

Record each run → `run_<model>_<task>.json` + row in `summary.csv`.

**Stop:** Premature stop after ~5 tool calls → note in audit; do not run T2 write probe.

---

## Lane C — THEN (editor closed, owner)

Claireon setup — **no OpenCode Nemotron runs during build.**

```
Claireon worktree
  → closed-editor UE 5.8 build with Claireon plugin
  → connect MCP (verify tool_search + python_execute)
```

Deliverable: Claireon MCP answering on documented port; build log saved to audit folder.

---

## Lane D — AFTER Claireon connects (new session)

**Alternate sessions — never Monolith + Claireon in the same OpenCode session.**

### T8 — Context cost benchmark

Compare tool-schema / context overhead for the **same read-only task** on two surfaces:

| Run | MCP surface | Session |
|---|---|---|
| T8-M | Monolith only (~116 tools) | OpenCode session 1 |
| T8-C | Claireon (~5 + discovery) | OpenCode session 2 **after restart** |

**Suggested task:** T1 (BP_BattleUI OnKeyDown JSON) or lighter: *"How many actors in persistent level of L_KaleidoNave?"* via each surface.

**Metrics to record:**

- Input tokens (first request with tools registered)
- Tokens per turn through task completion
- Tool-call count
- Wall time
- Incorrect tool selections
- Context growth rate (tokens/step)

Output → `Saved/Audit/nemotron_harness_2026-08-19/T8_context_cost_<surface>.json`

### Claireon 5.8 build report → GitHub issue

File on **believer-oss/Claireon** or this repo if fork — include:

- UE version (5.8.x), platform, build result
- Plugin connect steps that worked / failed
- MCP tool count observed
- Comparison note vs Monolith for T8

Template: `Saved/Audit/nemotron_harness_2026-08-19/claireon_ue58_build_report.md`

---

## Lane E — VS P0 (livelihood — when PIE window available)

Not displaced by Nemotron. Run when you need First Dream gate closure:

1. Real-key stock battle (Morning → KaleidoNave, Q/W/O/P)
2. `playtest_harness.py` + assertion JSON + `record_gate.py runtime`

---

## Job applications (parallel to Lane A)

| Send today | Blocker cleared? |
|---|---|
| Digital Extremes (Junior/Intermediate) | Portfolio live at `fromage3900.github.io/my-site/wix/application-hub.html` |
| Promethean AI Junior Artist (ArtStation jobs) | Same + lead with stills |
| Epic MegaGrants | Optional — fill $ ask first |

Do **not** send: Infold senior, Compulsion (no posting).

---

## Decision after today

| Outcome | Next |
|---|---|
| Super passes 1a+1b+T1/T4/T5 | Schedule Exp 7 background-agent trial |
| Super fails tool calls | Stay Claude primary; Nemotron Nano for grep-only |
| T8: Claireon << Monolith tokens | Prefer Claireon for Nemotron; Monolith for Claude |
| T8: Claireon discovery fails | Surface B blocked; stay Monolith-only |
| Runtime gate certified | Deprioritize all Nemotron vs VS closeout |

---

## File manifest (end of day)

```
Saved/Audit/nemotron_harness_2026-08-19/
  ground_truth/T3_handle_quill_notification.json
  run_nemotron_super_1a_smoke.json
  run_<model>_T1.json …
  summary.csv
  T8_context_cost_monolith.json
  T8_context_cost_claireon.json
  claireon_ue58_build_report.md
```
