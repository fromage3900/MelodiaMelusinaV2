# Nemotron × OpenCode × Unreal — Research + Experiment Plan (2026-08-19)

**Status:** Research complete (Tasks 1–3). Experiments designed (Tasks 4–7). **Not yet run.**

**Scope:** Evaluate whether NVIDIA Nemotron models are viable for agentic coding in this repo's
OpenCode + Unreal MCP workflow — as primary harness, long-context specialist, or cheap
background agent.

**Do not assume marketing claims.** NVIDIA positions Nemotron 3 for agents; OpenCode integration
for Ultra is currently broken. Evidence from experiments (Tasks 4–7) decides adoption.

---

## 1. Model lineup (August 2026)

### Four active lineages

| Lineage | Architecture | Size range | Agentic coding? |
|---|---|---|---|
| **Nemotron 3** | Hybrid Mamba-Transformer MoE (LatentMoE + MTP) | 30B–550B (3B–55B active) | **Yes — current flagship** |
| **Llama-Nemotron** | Llama 3.1/3.3 + NVIDIA post-training | 8B–253B | Yes (tool calling trained) |
| **Nemotron-H** | Hybrid Mamba-Transformer (dense) | 4B–56B | No — base/research, 8K context |
| **Nemotron 4** | Dense Transformer | 340B | **No — 4K context, synthetic-data only** |

**Clarification:** "Nemotron-H 253B" does not exist. 253B is **Llama-3.1-Nemotron-Ultra-253B-v1**
(Llama lineage, not Nemotron-H).

### Models relevant to this workflow

#### Nemotron 3 Super 120B-A12B (primary candidate)

| Field | Value |
|---|---|
| Total / active params | 120B / 12B per token |
| Context | Up to **1M** tokens |
| Tool calling | Yes — multi-environment RL (10+ envs) |
| Agentic training | Explicitly trained for agent harnesses (OpenCode cited in NVIDIA docs) |
| Cloud API | NIM serverless; **prefer OpenRouter** for OpenCode (see §2) |
| Pricing (NIM) | ~$0.15–0.40/M input, ~$0.60–1.50/M output |
| Local (NVFP4) | 1× B200 or DGX Spark; FP8: 2× H100/H200 |
| Release | March 2026 |

#### Nemotron 3 Ultra 550B-A55B (capability ceiling)

| Field | Value |
|---|---|
| Total / active params | 550B / 55B per token |
| Context | Up to **1M** tokens |
| Tool calling | Yes — complex multi-step orchestration |
| Agentic training | OpenCode, OpenHands, Kilo Code, Continue cited in model card |
| Cloud API | NIM ~$0.50/M in, ~$2.20/M out; OpenRouter ~$0.60/M in, ~$3.60/M out |
| Local (NVFP4) | 4× B200 single node; FP8: 8× H200 |
| Release | June 2026 |
| **OpenCode status** | **Broken via NIM** — hangs at Build/Thinking (#34026); 45+ min / 5-call stop (#42168) |

#### Nemotron 3 Nano 30B-A3B (cheap background candidate)

| Field | Value |
|---|---|
| Active params | ~3.2B |
| Context | 262K |
| NIM pricing | $0.05/M in, $0.20/M out |
| Local | ~18GB at 4-bit → single RTX 4090/5090 |
| Note | NIM endpoint deprecation scheduled **2026-08-25** — migrate before then |

#### Llama-3.3-Nemotron-Super-49B-v1.5 (Hopper-friendly fallback)

| Field | Value |
|---|---|
| Params | 49B dense |
| Context | 128K |
| Tool calling | Yes — iterative DPO for tool calling; `llama_nemotron_json` vLLM parser |
| Best for | Tool-heavy agents when Blackwell unavailable |

#### Llama-3.1-Nemotron-Ultra-253B-v1

| Field | Value |
|---|---|
| Params | 253B dense |
| Context | 128K |
| Tool calling | Yes |
| Local | 8× H100 single node |

#### Nemotron 4 340B — **do not use for coding agents**

4K context ceiling disqualifies any multi-file or multi-turn agent workflow.

### Practical selection matrix

| Use case | Model |
|---|---|
| Primary OpenCode harness (if experiments pass) | Nemotron 3 Super via **OpenRouter** |
| Maximum capability (when OpenCode fixed) | Nemotron 3 Ultra via OpenRouter |
| Cheap background / exploration | Nemotron 3 Nano or Super |
| Hopper-only local | Llama-Nemotron-Super-49B-v1.5 |
| **Avoid** | Nemotron 4 340B, Nemotron-H (no tool calling), Ultra via NIM in OpenCode |

### Self-hosted vLLM note (not OpenCode client concern)

For Nemotron 3 Super/Ultra on vLLM:

```bash
--enable-auto-tool-choice \
--tool-call-parser qwen3_coder \
--reasoning-parser nemotron_v3
```

Old `nemotron_json` parser broken in vLLM 0.20.x+. NIM hosted and OpenRouter handle this
server-side — OpenCode needs no parser config when using those paths.

---

## 2. OpenCode integration

### Provider paths (ranked for reliability)

| Rank | Path | Notes |
|---|---|---|
| 1 | **OpenRouter** (`openrouter.ai/api/v1`) | No Nemotron-specific OpenCode bugs filed |
| 2 | **OpenCode Zen** — Nemotron 3.5 Lightning | Added 2026-08-11; curated/tested by OpenCode team |
| 3 | NVIDIA NIM cloud (`integrate.api.nvidia.com/v1`) | Super works; Ultra hangs (#34026) |
| 4 | Self-hosted vLLM | Requires correct parsers; not for initial experiments |

### Reference config — Nemotron Super via OpenRouter

Save as a local override (do not commit API keys). Project `.opencode/opencode.jsonc` inherits
model from `~/.config/opencode`; pin there or in a gitignored local file.

```json
{
  "$schema": "https://opencode.ai/config.json",
  "model": "openrouter/nvidia/nemotron-3-super-120b-a12b",
  "provider": {
    "openrouter": {
      "npm": "@ai-sdk/openai-compatible",
      "name": "OpenRouter",
      "options": {
        "baseURL": "https://openrouter.ai/api/v1",
        "apiKey": "{env:OPENROUTER_API_KEY}"
      },
      "models": {
        "nvidia/nemotron-3-super-120b-a12b": {
          "name": "Nemotron 3 Super 120B",
          "limit": { "context": 1000000, "output": 32768 }
        }
      }
    }
  },
  "agent": {
    "build": { "temperature": 1.0, "top_p": 0.95, "max_tokens": 32000 },
    "plan":  { "temperature": 1.0, "top_p": 0.95, "max_tokens": 32000 }
  }
}
```

### Known OpenCode + Nemotron issues (Aug 2026)

| Issue | Symptom | Workaround |
|---|---|---|
| #34026 | Ultra 550B hangs at Build/Thinking, zero stream | Use OpenRouter; or Super instead |
| #42168 | 45+ min minor changes; stops after ~5 tool calls | OpenRouter; long timeout if NIM |
| #40185 | NIM streaming / tool-call failures (umbrella) | OpenRouter |
| `extraBody` / `chat_template_kwargs` | Rejected by `@ai-sdk/openai-compatible` | Omit; model runs without explicit thinking control |

### MCP (model-agnostic OpenCode bugs — affect all models)

- Silent MCP connection drops after 60–120s idle (#29190, #23997)
- No heartbeat / reconnect on HTTP SSE
- Context compaction can permanently drop MCP clients (#23556)

**Mitigation for experiments:** restart OpenCode between runs; keep sessions short; one MCP
surface at a time (Monolith **or** VibeUE, not both — matches AGENTS.md Decision 025).

### NVIDIA training on OpenCode traces

Nemotron 3 Ultra training includes ~615K synthetic OpenCode agentic task rows
(`NVAgenticCLIPrompts-v1`, `NVAgenticSkills-v1`, etc.). Model was trained for this harness;
integration layer is the current gap, not necessarily base capability.

### Model comparison in OpenCode (pre-experiment expectation)

| Model | Tool calls | MCP | Speed | Production-ready? |
|---|---|---|---|---|
| Claude Sonnet/Opus | Excellent | Same OC bugs | Fast | Yes |
| Qwen3-Coder | Good (some Plus/Max loop bugs) | Same | Good | Yes |
| DeepSeek V4 | Good via direct API; R1 needs reasoning_content passthrough | Same | Good | Yes via API |
| Nemotron Super | Good via OpenRouter | Same | Moderate | **Test first** |
| Nemotron Ultra | **Broken via NIM** | Same | Very slow if runs | **No until #34026 fixed** |

---

## 3. Nemotron × Unreal (public evidence)

| Integration | Status | Evidence |
|---|---|---|
| ACE LLM plugin (Nemotron-Mini-4B runtime NPC) | Shipped | NVIDIA blog, *Mecha BREAK*, ACE docs |
| Nemotron 3 33B → Unreal MCP via Ollama + Codex CLI | Community | `unreal-ai-connection` PR #104 (deprecated Jul 2026) |
| Nemotron → OpenCode → Monolith MCP | **No public example** | Would be first documented instance |
| Nemotron NIM → Claireon / Epic UE5.8 MCP | No public example | Technically trivial (OpenAI-compat) |
| Nemotron + Claireon specifically | No public evidence | MCP-agnostic; Claude-only docs |

**Distinction:** Lack of public write-ups ≠ nobody doing it. Tooling is compatible; this repo's
experiments would produce the first documented OpenCode + Monolith + Nemotron trace.

---

## 4. Experiment 4 — Harness model comparison

**Goal:** Same OpenCode + Unreal environment; only model varies.

### Constants

- OpenCode version pinned for the session
- Same MCP: Monolith on 9316 (enable in `.opencode/opencode.jsonc` when UE open)
- Same `AGENTS.md`, `CLAUDE.md`, task prompts verbatim
- `temperature: 1.0`, `top_p: 0.95` where provider allows
- Fresh session per model per task (no shared context)

### Models

| Slot | Model | Provider |
|---|---|---|
| Control | Claude Sonnet 4.5 | Anthropic |
| A | Nemotron 3 Super 120B | **OpenRouter** |
| B | Nemotron 3 Ultra 550B | **OpenRouter only** (not NIM) |
| C | DeepSeek V4 / R1 | OpenRouter or DeepSeek API |
| D | Qwen3-Coder-480B | OpenRouter |
| E | Nemotron 3.5 Lightning | OpenCode Zen (if available) |

### Task battery

| ID | Task | Stresses |
|---|---|---|
| T1 | Read `BP_BattleUI` OnKeyDown via Monolith; report lane-key bindings as JSON | Tool selection, read-only |
| T2 | Wire `RestorePartyAfterBattle` call site; compile + fingerprint assert | Write + verify loop |
| T3 | Find all callers of a named function; trace reachability | Multi-tool planning |
| T4 | Export `DA_MelodiaIntegrationConfig` CDO; cross-check TravelLevelIds vs AGENTS.md | Cross-source, anti-hallucination |
| T5 | Run `bp_sweep.py` scoped; interpret output in one paragraph | Tool output fidelity |
| T6 | Three-step: find BP → read property → set → re-read verify | Context retention |

### Metrics (record per task per model)

Tool-call accuracy, malformed calls, unnecessary calls, planning quality (1–5 human),
context retention, goal drift, compile errors (T2), recovery behavior, task completion (Y/N),
input/output tokens, wall time, human intervention count + reason.

### Evidence output

Save under `Saved/Audit/nemotron_harness_<date>/`:

- `run_<model>_<task>.json` — structured metrics
- `transcript_<model>_<task>.md` — session export if available
- `summary.csv` — all runs aggregated

---

## 5. Experiment 5 — Long-context claim (Unreal-specific)

**Goal:** Does 1M context improve cross-system reasoning, or add noise?

### Conditions

| Cond | Model | Context strategy |
|---|---|---|
| A | Ultra (OpenRouter) | Full project dump (~500K–800K tokens) |
| B | Ultra | Curated relevant files only |
| C | Super | Curated (same as B) |
| D | Claude Sonnet | Curated (200K cap) |
| E | Llama-Nemotron-Super-49B | Curated (128K cap) |

### Tasks (cross-system)

| ID | Task |
|---|---|
| LCT-1 | Allowlisted narrative IDs in config but never referenced in `.qs` scripts |
| LCT-2 | `BP_BattleUI` events with C++ callers — list call sites |
| LCT-3 | Verify `melodia:stat:` idempotency claim in `MelodiaNarrativeSubsystem.cpp` vs AGENTS.md |
| LCT-4 | Material spec assets vs `bp_fingerprints.json` baseline gaps |
| LCT-5 | Full trace: Quill `melodia:battle:` → `BP_BattleController` in level |

### Metrics

Answer correctness vs manual ground truth, hallucination count, relevant/irrelevant citation
ratio (condition A), missed cross-references, token cost A vs B.

**Run after Experiment 4** — only meaningful once baseline model quality is known.

---

## 6. Experiment 6 — MCP surface complexity

**Goal:** Reasoning limit vs tool-schema overload?

### Surfaces (Nemotron Super only first, then Claude control)

| Surface | Approx tools | Character |
|---|---|---|
| A | Epic native UE5.8 MCP | ~150+ flat |
| B | Claireon | ~5 + dynamic `tool_search` |
| C | Current multi-MCP (Monolith + VibeUE) | ~266 overlapping |

Use T1–T3 subset from Experiment 4 on each surface.

### Metrics

Incorrect tool selection, unnecessary calls, context growth per step, syntax errors, schema
confusion (wrong arg names across tools), Claireon discovery→use success, recovery after failure.

### Prerequisite gate

Before surface sweep: one Super-via-OpenRouter run of T1 must complete without premature
5-call termination. If it fails on OpenRouter too, problem is model/harness — not surface.

---

## 7. Experiment 7 — Cheap persistent agent architecture

**Goal:** Nemotron background + Claude foreground — when does it save money without adding errors?

### Candidate Nemotron tasks (low write risk)

- Repository exploration / code search
- Documentation sync (read C++, patch AGENTS.md section)
- Asset inventory (specs vs disk)
- Unreal inspection (CDO reads via Monolith)
- Repetitive verification (`bp_sweep`, compile check, fingerprint assert)
- Background report generation for Claude handoff

### Hold on Claude (high risk)

- Blueprint graph mutation + assert loop
- Ambiguous cross-system traces without ground truth
- Anything touching `Content/TurnBasedJRPGTemplate/Blueprints/Skills/` from Python

### Architecture under test

```
Session A (Nemotron Super, plan mode or read-heavy build):
  exploration → structured JSON report
Session B (Claude build):
  consumes A output → mutations + verify
```

### Metrics

Handoff accuracy, Session B token reduction vs no-precursor, error introduction rate,
cost (Nemotron $ + Claude $ vs Claude alone), latency (does A finish before B needs it?).

---

## 8. Today's work plan (2026-08-19)

**Execution plan moved to:** [`TODAY_2026-08-19_PARALLEL_PLAN.md`](TODAY_2026-08-19_PARALLEL_PLAN.md)

Summary:

| Lane | When | Work |
|---|---|---|
| A (no editor) | NOW | pull main → Phase 0 → 1a smoke → T3 grep |
| B (editor open) | Background OC tabs | 1b T1 Monolith → Phase 2 T1/T4/T5 × 3 models |
| C (editor closed) | Owner | Claireon worktree + build + connect |
| D (new session) | After Claireon | T8 context cost Monolith vs Claireon → GH issue |
| E | PIE window | VS P0 real-key runtime gate (unchanged) |

---

## 9. Open questions / blockers

| Blocker | Owner action |
|---|---|
| Ultra hangs in OpenCode (#34026) | Watch OpenCode releases; use OpenRouter for Ultra tests |
| MCP idle drops | Restart OpenCode between experiment runs |
| Claireon not in repo | Install/test Claireon before Experiment 6 surface B |
| Nano NIM deprecation 2026-08-25 | Migrate Nano experiments to OpenRouter before deadline |
| No Nemotron in committed `.opencode/opencode.jsonc` | Intentional — keys live in user config |

---

## 10. Primary sources

- [Nemotron 3 Super NIM docs](https://docs.nvidia.com/nim/large-language-models/latest/models/nemotron-3-super.html)
- [Nemotron 3 Ultra model card](https://huggingface.co/nvidia/NVIDIA-Nemotron-3-Ultra-550B-A55B)
- [NVIDIA build.nvidia.com](https://build.nvidia.com) — NIM catalog + pricing
- [OpenCode config schema](https://opencode.ai/config.json)
- OpenCode GitHub issues: #34026, #42168, #40185, #33618 (Qwen tool loops)
- [NVIDIA ACE UE5 plugins blog](https://developer.nvidia.com/blog/build-on-device-ai-companions-with-the-nvidia-ace-game-agent-sdk-and-unreal-engine-5-plugins/)
- Project: `.opencode/opencode.jsonc`, `AGENTS.md` § MCP surfaces

---

## 11. Decision criteria (after experiments)

**Adopt Nemotron Super as default harness if:** T1/T4/T5 match Claude on correctness;
tool-call accuracy ≥90%; no premature loop termination; cost savings ≥30% at equal task completion.

**Use Nemotron as background only if:** read tasks pass but T2 fails or needs intervention;
handoff accuracy ≥95% on factual claims.

**Stay on Claude if:** malformed tool calls >10%; goal drift on T3/T6; or OpenRouter Super
shows same 5-call termination as NIM Ultra.

**Revisit Ultra when:** OpenCode #34026 closed and a single T1 completes in <5 min via OpenRouter.
