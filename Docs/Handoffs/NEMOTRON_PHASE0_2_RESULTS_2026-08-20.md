# Nemotron Phase 0–2 Results — 2026-08-20

**Overall status:** **PASS (partial)** — OpenCode Zen Nemotron Lightning smoke + T5 fidelity pass; Claude Zen control and TokenRouter blocked; T1/T4 deferred (Monolith MCP off).

**Routing (owner correction):** **OpenCode Zen / Go + TokenRouter** — **not OpenRouter.**  
**Ultra via NIM:** **NOT USED** (OpenCode #34026).  
**Local Ollama/Qwen/Muse:** left alone (Ollama `api/ps` empty during runs).

**OpenCode version:** `1.18.18`  
**Audit dir:** `Saved/Audit/nemotron_harness_2026-08-20/`

---

## Decision gate (retargeted)

| Gate | Result |
|---|---|
| Zen smoke (Nemotron) before Ultra / long-context | **PASS** — `opencode/nemotron-3.5-lightning-free` |
| T1 / T4 / T5 Claude vs Nemotron | **PARTIAL** — T5 Lightning **PASS**; Claude Zen **BLOCKED** (credits); DeepSeek free used as alternate control **PASS**; T1/T4 **NOT_RUN** |
| Never Ultra via NIM | **Honored** |
| Prefer Zen Lightning slot from harness spec | **Used** (`provider: opencode_zen`, id `nemotron-3.5-lightning` → live ID `opencode/nemotron-3.5-lightning-free`) |

---

## Tooling discovered

| Asset | Role |
|---|---|
| `specs/nemotron_experiment_harness.json` | Experiment slots; Zen Lightning is the only `opencode_zen` model |
| `.opencode/opencode.jsonc` | Project OpenCode; **monolith `enabled: false`** |
| `~/.config/opencode/opencode.jsonc` | User MCP + TokenRouter provider; **`disabled_providers: ["tokenrouter"]`** |
| `~/.local/share/opencode/auth.json` | **Zen + Go credentials present** (`opencode auth list` → 2) |
| `Tools/model_router.py` | TokenRouter host `https://api.tokenrouter.com/v1`; keys from env / `C:\EnvironmentPortfolio\.mcp.json` |
| `Tools/run_math_models.py` / `run_math_guardrails.py` | MATH lanes (peer using Qwen/Muse — not touched) |
| `Tools/bp_sweep.py` | T5 ground truth |

### Zen / Go Nemotron model IDs (live `opencode models`)

| ID | Notes |
|---|---|
| `opencode/nemotron-3.5-lightning-free` | **Primary candidate used** |
| `opencode/nemotron-3-ultra-free` | Listed on Zen; **deferred** (decision gate: Super/Lightning before Ultra; never NIM) |
| *(none)* | **No Nemotron Super** ID on Zen/Go catalog today |

---

## Phase 0 — Setup + smoke

| Check | Status |
|---|---|
| Audit folder created | PASS |
| OpenCode pinned | PASS (`1.18.18`) |
| Zen auth | PASS |
| Smoke: Lightning replies `OK` | **PASS** (~29s, cost `$0`, session `ses_fe038bffeffe6zVtOGlB2mHEiX`) |
| TokenRouter `/models` + chat | **BLOCKED** — TCP timeout to `api.tokenrouter.com`; OpenCode also has TokenRouter **disabled** |

Evidence: `Saved/Audit/nemotron_harness_2026-08-20/phase0_zen_lightning.json`

---

## Phase 1 — Provider smoke (tools, no UE MCP)

| Run | Status | Notes |
|---|---|---|
| List ≤15 files in `Tools/` | **PASS** | 2× `glob` tool calls; returned real `.py` names; cost `$0` |

Evidence: `phase1_list_tools_raw.txt`

---

## Phase 2 — Harness subset (T1 / T4 / T5)

### T5 — `bp_sweep` fidelity (no UE required)

Ground truth (agent-run, not invented):

```text
python Tools/bp_sweep.py --filter MelodiaIntegration --skip-live --limit 40
→ 40 BPs / 99 graphs / 1697 nodes
→ EMPTY 72, DEAD 17, SHADOWED 0, DUPES 0, unreadable 0
```

| Model | Status | Wall | Cost | Verdict |
|---|---|---|---|---|
| `opencode/nemotron-3.5-lightning-free` | **PASS** | ~55s | $0 | Correct core counts; one unnecessary `todowrite`; minor display-name expansion vs truncated table |
| `opencode/claude-sonnet-4-5` | **BLOCKED** | ~31s | — | Zen `CreditsError` / insufficient balance |
| `opencode/deepseek-v4-flash-free` | **PASS** (alt control) | ~47s | $0 | Same core counts; longer but accurate |

### T1 / T4 — Monolith read tasks

**NOT_RUN.** UE Monolith listener is up (`127.0.0.1:9316`, one process), but project `.opencode/opencode.jsonc` keeps `"monolith": { "enabled": false }`. No live MCP tool surface for OpenCode until owner flips that (one-editor rule already satisfied).

---

## Cost cap

- Zen Lightning + DeepSeek free runs: **$0** observed.
- Claude Sonnet on Zen: **blocked before spend** (billing).
- No Ultra, no NIM, no OpenRouter, no long-context dump.
- TokenRouter never completed a request (timeout).

---

## Config gaps + owner commands

### 1. Claude Zen control (needed for true Claude vs Nemotron T1/T4/T5)

```powershell
# Top up OpenCode Zen workspace billing, then:
cd C:\EnvironmentPortfolio\BS_GodFile
opencode run -m opencode/claude-sonnet-4-5 --agent plan "Reply with exactly: OK"
```

Billing URL from error: `https://opencode.ai/workspace/wrk_01KWXDVRJWHT7V0578PCHEJC81/billing`

### 2. Enable Monolith for T1/T4 (UE already on 9316)

In `.opencode/opencode.jsonc`, set `"monolith"."enabled": true` (only while **one** editor listens on 9316), then:

```powershell
opencode run -m opencode/nemotron-3.5-lightning-free --agent plan --title t1-battleui "Using Monolith blueprint_query, read BP_BattleUI OnKeyDown lane-to-key bindings as JSON. Read-only."
opencode run -m opencode/nemotron-3.5-lightning-free --agent plan --title t4-cdo "Export DA_MelodiaIntegrationConfig CDO TravelLevelIds via Monolith get_cdo_properties; cross-check AGENTS.md allowlist; discrepancies only."
```

### 3. TokenRouter (optional third lane)

```powershell
# Key loads from C:\EnvironmentPortfolio\.mcp.json via Tools/model_router.py today,
# but OpenCode user config disables the provider and the host timed out from this box.
# Owner: confirm TokenRouter reachability, then remove "tokenrouter" from disabled_providers
# in %USERPROFILE%\.config\opencode\opencode.jsonc and re-auth if needed:
opencode auth list
# Probe:
python -c "import sys; sys.path.insert(0,'Tools'); from model_router import load_keys, ENDPOINTS; print(bool(load_keys()['tokenrouter']), ENDPOINTS['tokenrouter'])"
```

### 4. Nemotron Super ID gap

Zen/Go catalog has **Lightning free** and **Ultra free** only — **no Super**. Spec still lists Super as OpenRouter-era primary; under Zen routing, treat **Lightning** as the default experiment model until Super appears in `opencode models`.

---

## Paste-ready sentence (NVIDIA DevRel packet)

> On 2026-08-20 we ran a bounded Melodia Unreal/OpenCode harness smoke on **OpenCode Zen** (not NIM, not OpenRouter): **`opencode/nemotron-3.5-lightning-free`** completed Phase 0 single-turn OK, Phase 1 tool-using directory listing, and Phase 2 T5 `bp_sweep` fidelity (correctly quoting EMPTY=72 / DEAD=17 on MelodiaIntegration) at $0, while Claude Sonnet on Zen was blocked by workspace credits and Monolith MCP read tasks (T1/T4) remain gated on enabling the local 9316 server in project OpenCode config.

---

## Left for owner

1. Top up **OpenCode Zen** credits for Claude control compares.  
2. Enable **Monolith** in `.opencode/opencode.jsonc` and run **T1 + T4** on Lightning (then Claude).  
3. Restore/fix **TokenRouter** reachability if that lane is still desired (currently disabled + host timeout).  
4. When Super appears on Zen/Go, re-run the same gates; keep Ultra on Zen free only if needed — **never Ultra via NIM**.
