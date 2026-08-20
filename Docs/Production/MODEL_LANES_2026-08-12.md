# Model Lanes + Local Daemon Policy — 2026-08-12

**Authority for routing:** `Tools/model_router.py` `POLICY` dict.  
**Authority for agent behaviour:** `_AGENT_WORKING_AGREEMENT.md` + `AGENTS.md` Core Vision.  
**Gameplay queue:** `_VERTICAL_SLICE_SCOPE.md` / `Docs/Handoffs/CORE_SYSTEMS_HANDOFF_2026-08-10.md`  
(platform/website queue `NEXT_ACTIONS.md` is **not** gameplay authority).

---

## 1. Research summary (project state ↔ model fit)

### Project state (Aug 12)

- Mechanically close, **play-unproven**: JRPG bridge, rhythm mapping, beat map, mirror
  quarantine, Echo tooling are real; `runtime` gate still has **no real-input ledger row**.
- Recent commits skew docs/tools/infra over play certification.
- Integration falters on: dual HUD writers, silent allowlist no-ops, missing call sites
  (`RestorePartyAfterBattle`), presentation gaps (highway notes), evidence-vs-prose drift.

### Frontier models for *this* workload

This repo is long C++/Blueprint context, Monolith MCP (~1300 actions), and evidence discipline
— not greenfield web apps.

| Workload | Prefer | Why |
|---|---|---|
| Repo-scale C++ / UE bridge / hard debug | Claude Opus 5 / Opus 4.8 / Fable 5 | SWE-Bench Pro / repo coherence |
| Long shell + many tool calls | GPT-5.6 Sol (Ultra/subagents) | Terminal-Bench / DeepSWE horizon |
| MCP multi-server orchestration | Opus 4.8 (MCP Atlas ~82%); Gemini 3.1 Pro; Kimi K2.7/K3 | Multi-tool conditional branching |
| 1M-context intake / audits | Gemini 3.1 Pro, Nemotron Ultra, DeepSeek V4 Flash | Cheap wide context |
| Volume / cost | DeepSeek V4 Flash, Kimi, Qwen3-Coder-Next | Triage — not sole owner of HUD ownership bugs |

**Harness beats brand:** wrong queue, probe-as-play, dual MCP writers fail every model equally.

---

## 2. Core project vision (bind every lane)

One playable loop — stay small:

```text
Quill dialogue → allowlisted encounter → JRPG battle (Melusina) → typed result
  → Quill resumes once → exploration / checkpoint
```

Product shape (`_VERTICAL_SLICE_SCOPE.md`): Persona-lite, readable decisions, intentional
feedback. If a mechanic does not improve decisions, feedback, attachment, or flow — defer it.

**Agents must not:** invent parallel combat authority, rebuild JRPG in MelodiaCore, expand
scope into portfolio art direction, or “certify” gates without ledger rows.

---

## 3. Task classes (finer separation)

Router classes in `Tools/model_router.py`. Use the **narrowest** class that fits.

| Class | Job | Cloud / API default | Local daemon default |
|---|---|---|---|
| `triage` | Classify, summarize, route | Nemotron Ultra free / gpt-oss-20b | `qwen3:8b` or `gpt-oss:20b` |
| `audit` | Read-only sweeps, static gates | Nemotron Ultra → DeepSeek V4 Flash | `qwen3-coder:14b` / Laguna XS |
| `code` | General Python/tools/docs code | DeepSeek V4 Flash → Codestral | `qwen3-coder:14b` |
| `cpp` | UE C++ / MelodiaIntegration | Frontier Opus / Sol when available; else DeepSeek V4 Pro | `qwen3-coder:32b` or `devstral-small` |
| `mcp` | Monolith/MCP multi-step tool plans | Grok 4.5 / Mistral Medium; Opus when paid | `qwen3-coder-next` (80A3) / GLM-5.x if VRAM |
| `playtest` | Real-input runtime gate only | Grok 4.5 verifier + harness (not probe) | Local only for report grading — **keys via harness** |
| `author` | Quill / narrative / dialogue | Mistral Medium 3.5 | `mistral` / `qwen3:14b` |
| `deep` | Slow hard reasoning | Kimi K3 free | `kimi` local if cluster; else skip |
| `review` | Fresh-eyes / intake | Grok 4.5 | `nemotron` VL / text |
| `orchestrator` | Multi-agent plan | Grok 4.20 multi-agent | **Do not loop locally** — human/coordinator |
| `vision` | Frames / contact sheets | Mistral Medium / Muse Spark | Nemotron VL local if available |
| `daemon` | Unattended overnight loops | — | **Local only** (see §4) |
| `docs` | Handoffs / fold-ins | DeepSeek V4 Flash | `qwen3:8b` |

Lane dispatcher keywords map into these classes; gameplay items win over platform wording.

---

## 4. Local models for long-term daemon loops

Daemons (`continuous_loop`, Echo static gates, intake fan-out, memory rebuild) must be
**cheap, offline-capable, and boring**. Prefer Ollama / vLLM OpenAI-compatible endpoint at
`http://127.0.0.1:11434/v1` (or project `LOCAL_LLM_BASE_URL`).

### Recommended stack by VRAM

| VRAM | Primary daemon model | Role | Notes |
|---|---|---|---|
| 8 GB | `qwen3:8b` | triage + docs | Raise `num_ctx` ≥ 32k in Modelfile |
| 16 GB | `qwen3-coder:14b` | code + audit loops | Best cost/quality for overnight |
| 24 GB | `qwen3-coder:32b` **or** `devstral-small` | cpp-ish + agentic fix loops | Devstral for multi-file agent trails |
| 24–48 GB MoE | `qwen3-coder-next` (80B-A3B) | mcp/code daemon | ~3B active — strong agentic, local-friendly |
| 48 GB+ | `glm-5.2` / large Kimi if licensed | hard audit / deep | Single-node top open scores |
| Cluster | Kimi K3 | deep only | Not for always-on daemon cost |

**Also strong for agentic daemons:** Laguna XS 2.1 (33B/3B active, 256K ctx) when available via
Ollama; MiniMax M3 if you need 1M ctx + vision in one local weight.

### Daemon rules (non-negotiable)

1. **No editor writes from free-roaming daemons.** Static gates / audits only unless a
   human-owned jcode worker holds the single editor lock.
2. **No `record_gate.py … pass` from local models.** Ledger pass/fail is human or paid
   playtest lane with assertion JSON.
3. **No recursive spawn.** One daemon process; coordinator owns fan-out.
4. **Context:** default Ollama `num_ctx` is too small — set ≥ 32k (prefer 128k for audit).
5. **Fallback:** if local health-check fails, `daemon` class skips cloud (avoid silent bill);
   surface FAIL in `Saved/router_ledger.jsonl`.
6. **Vision daemons:** use free Nemotron VL or local VL only — free-tier OpenRouter image
   input 402s on paid models.

### Suggested Ollama pull set

```bash
ollama pull qwen3:8b
ollama pull qwen3-coder:14b
ollama pull qwen3-coder:32b   # if 24GB+
# optional agentic:
# ollama pull qwen3-coder-next
# ollama pull devstral-small
```

Point router local endpoint:

```bash
set LOCAL_LLM_BASE_URL=http://127.0.0.1:11434/v1
set LOCAL_LLM_API_KEY=ollama
```

---

## 5. How agents stick to lanes + vision

1. Read `_AGENT_WORKING_AGREEMENT.md` first (always).
2. Pick a **task class** from §3 before first write; run
   `python Tools/model_router.py pick <class> --detail`.
3. Gameplay work: queue from vertical slice / core systems handoff — **not** `NEXT_ACTIONS.md`.
4. Done only when: change shipped **or** ledger row written for the claimed gate.
5. Subagents: keep `AGENTS.md` under 32 KB so Muse/jcode do not truncate — detail lives here
   and in `Docs/Production/T3D_MONOLITH_REFERENCE.md`.

### Lane write fences (gameplay)

| Lane | May write | Must not |
|---|---|---|
| `cpp` / integration | `Source/BS_GodFile/MelodiaIntegration/` | MelodiaCore combat authority rebuild |
| `mcp` / BP wiring | Via Monolith only; one editor | Second MCP surface on same graph |
| `playtest` | `Saved/Playtest/*.json`, ledger via harness | Probe-only `runtime pass` |
| `daemon` | `Saved/Audit/`, Echo reports, memory index | Content `.uasset` / Config Red files |
| `author` | Quill scripts / narrative docs | Inventory grants via stub `melodia:item:` |
| portfolio swarm | Per `.jcode/swarm-prompt.md` PGA/MPA/… | Sakura / `_PROJECT/` / Red deletes |

---

## 6. Integration failure modes (for review/audit lanes)

Audit and review models should hunt these first — not invent new systems:

1. Probe calls presented as play evidence
2. Dual writers on `UMelodiaRhythmHUDWidget` without ownership
3. Relaxed editor allowlist masking Shipping failures
4. Missing call sites (`RestorePartyAfterBattle`)
5. Duplicate short names / shadowed parent events
6. Docs claiming done without `Saved/gate_ledger.json` rows

---

## 7. Ops notes

- Free-tier OpenRouter quota exhausts mid-day — schedule paid frontier early.
- Rotate any leaked Figma key (redacted in docs; owner action).
- `lane_dispatcher.py` must read gameplay queue authority (fixed 2026-08-12).
