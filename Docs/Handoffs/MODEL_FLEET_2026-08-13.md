# Model fleet handoff

> **UPDATED 2026-08-14 — Bedrock is WORKING, and the default is Qwen3 Coder Next.**
>
> The 08-13 diagnosis in this file was wrong twice. The real blocker was neither the root
> user nor an Anthropic use-case form: **`bedrock-mantle` is a separate IAM service**
> (`bedrock-mantle:*` actions, scoped to `project/default`) reached at
> **`https://bedrock-mantle.{region}.api.aws/v1`** — note `.api.aws`, **not**
> `.amazonaws.com`. Granting `bedrock-mantle:CreateInference` fixed it.
>
> **Default model: `qwen.qwen3-coder-next`** — set in `.opencode/opencode.jsonc` and
> leading the `code` and `cpp` chains in `Tools/model_router.py`.
>
> **Kimi IS on Bedrock.** This file previously said Moonshot was absent and an OpenRouter
> top-up was needed. True for `bedrock-runtime`, **false** for Mantle —
> `moonshotai.kimi-k2.5` and `kimi-k2-thinking` both answered live. No top-up needed.
>
> Verified 2026-08-14: `cpp` 5/5 PASS, `deep` 4/4 PASS.

## Using it

```powershell
$env:AWS_PROFILE = "bedrock"          # SigV4, or:
$env:AWS_BEARER_TOKEN_BEDROCK = "..." # a Bedrock API key
```

| Where | Setting |
|---|---|
| OpenCode / Rider | pinned to `bedrock-mantle/qwen.qwen3-coder-next` |
| Cline / Continue / any OpenAI client | base URL `https://bedrock-mantle.us-east-1.api.aws/v1`, model `qwen.qwen3-coder-next` |
| Router CLI | `python Tools/model_router.py chat cpp --prompt "..."` |

## Cost — measured, and not a constraint

Price List API, 2026-08-14, blended 1:2 in:out, at the measured **745K tokens/month**:

| Model | $/1M blended | $/month here |
|---|---|---|
| gpt-oss-20b | 0.27 | **0.20** |
| GLM 4.7 Flash | 0.29 | 0.22 |
| **Qwen3 Coder Next (default)** | **1.00** | **0.74** |
| Qwen3 Coder 480B | 1.39 | 1.04 |
| DeepSeek v3.2 | 1.73 | 1.29 |
| GLM 5 | 2.89 | 2.16 |

The whole spread is **under $2/month**. $200 is years of runway. **Choose on capability and
latency, not price** — a cheaper model that gets it wrong costs an hour, which is worth
more than the entire annual bill. Cheap tier (gpt-oss-20b, GLM 4.7 Flash) is for *speed*
on high-volume mechanical work, not for saving money.

Kimi and Devstral are absent from the Price List API, so their ledger rows are still
estimates — flagged in-line in `Tools/model_router.py`.

**Claude on Mantle is not wired:** `anthropic.*` rejects `/v1/chat/completions` and needs
`/v1/responses`.

---

## Lane 2 — OpenRouter (free tier; real money buys the rest)

Free-tier key. Paid-model daily quota exhausts mid-day (402s on Grok/DeepSeek/Mistral);
free models are unaffected. This is the wall Bedrock exists to bypass.

**Only reachable here, not on Bedrock:**
- **Kimi K3** (Moonshot) — provider absent from Bedrock entirely
- **Muse Spark 1.2** (Meta) — Bedrock's Meta catalogue is Llama only.
  Still in `BLOCKED`: needs 18+ confirmation at `openrouter.ai/settings/preferences`

A **$20–25 top-up** unlocks both. Start there, not $100 — the ledger shows the volume is
tiny and unused credit is dead money.

> **Rotate the key in `~/.junie/config.json`.** Stored in plaintext (normal for BYOK) but
> surfaced in a session transcript on 2026-08-13. Never committed. `openrouter.ai/settings/keys`.

## Lane 3 — TokenRouter

Host is `api.tokenrouter.com/v1` (**not** the dead `tokenrouter.ai`). Serves
`moonshotai/kimi-k3-free`. Drops out sporadically — a contributor to the 50% failure rate.

## Lane 4 — Ollama (local, free, offline)

`http://localhost:11434`. **Installed: `deepseek-r1:14b`, `qwen2.5-coder:7b` only.**
`qwen3:8b` is referenced by older docs and is **not installed** — `nl_to_blueprint.py`'s
default was corrected to `deepseek-r1:14b` on 2026-08-13.

## Lane 5 — Muse Code (Meta, WSL2)

`wsl -e muse` v0.1.0. Auth `~/.config/muse/auth.json` (chmod 600). Separate from Muse
Spark on OpenRouter. Scope per `.jcode/swarm-prompt.md` §MUSE.

## Lane 6 — Rider / OpenCode

`.opencode/opencode.jsonc` now declares an `amazon-bedrock` provider (Qwen3-Coder
Next/30B, DeepSeek v3.2, Sonnet 4.6). **No key in the file** — Bedrock uses the AWS
credential chain, honouring that config's own no-keys rule. Set `AWS_PROFILE=bedrock`
before launching Rider.

> Junie headless is **broken on Windows** (`readPipedInput` IOException) — interactive
> only. OpenCode is the more reliable Rider lane.
>
> **Open:** the owner reports Rider config and the ACP registry reset on 2026-08-13.
> Under investigation; my `.opencode/opencode.jsonc` edit (`3e4ff53c`) is a candidate
> cause being ruled in or out. Diagnosis only — **do not restore anything** until that
> lands, or a wrong restore overwrites whatever survived.

---

## Local-first update — 2026-08-13 (Cline)

The router is now **local-first**. Ollama (`127.0.0.1:11434`, RTX 4070 SUPER 12GB,
models on `F:\OllamaModels`) is wired in as an endpoint with a cheap `_ollama_reachable()`
liveness probe. Installed fleet confirmed live:
- `deepseek-r1:14b` — 14.8B Q4_K_M, 131K ctx — leads `triage`/`audit`/`deep`/`review`/`author`/`orchestrator`
- `qwen2.5-coder:7b` — 7.6B Q4_K_M, 32K ctx, tools — leads `code`/`cpp`

Every lane that can run locally now tries the free offline model BEFORE any paid call:
`cpp` is `qwen2.5-coder` → `deepseek-r1` → Bedrock Qwen3-Coder Next → … The Bedrock
tail still catches hard engine work, but a no-network session now solves common tasks
for $0. `qwen_daemon.py` default was corrected `qwen3:8b` → `deepseek-r1:14b` (the
formerly-referenced `qwen3:8b` was never installed).

### Muse Spark — free access lanes
- **OpenRouter free** (`meta/muse-spark-1.2`) is still in `BLOCKED` (needs 18+
  confirmation at `openrouter.ai/settings/preferences`). Unblock that once and it's free.
- **Muse Code (WSL2)** is the other Meta lane — `wsl -e muse`, separate from Spark.
- No other free Bedrock path: Bedrock's Meta catalogue is Llama only, so Muse Spark
  only exists on OpenRouter/its own endpoint.

### Recommended local C++ models for this rig (RTX 4070 SUPER, 12GB VRAM)
| Model (Ollama tag) | Params/Quant | VRAM | Why |
|---|---|---|---|
| `qwen2.5-coder:7b` (have) | 7.6B Q4_K_M | ~4.5GB | Good default coder; has tools |
| `deepseek-r1:14b` (have) | 14.8B Q4_K_M | ~9GB | Reasoning before big edits |
| `qwen2.5-coder:14b` | 14B Q4_K_M | ~9GB | Stronger code than 7b, still fits |
| `qwen2.5-coder:32b` (Q3/Q4) | 32B | ~13-18GB (partial offload) | Best local coder; exceeds 12GB cleanly |
| `deepseek-coder:6.7b` | 6.7B | ~4GB | Code-only specialist |
| `codellama:34b` (Q4) | 34B | ~18GB (partial) | C++/Godot-aware, legacy |

Long-term pick for C++ on this box: upgrade `qwen2.5-coder:7b` → `qwen2.5-coder:14b`
(same family, ~9GB, still fits in the 12GB VRAM alongside OS/UE) as the local C++
workhorse. For a genuinely stronger local C++ lane that fully fits, `qwen2.5-coder:32b:q4_K_M`
requires ~18GB, so it would offload to system RAM — usable but slower; only worth it if
you add VRAM or accept the slowdown.

## Ranked next actions

1. **Fill the account-level use-case form in the Bedrock console** — the only thing left.
   Credentials verified (`melodia-bedrock` resolves), IAM policy repaired, and the
   Model-access page is retired: serverless models auto-enable on first invocation once
   the form exists. All four models report `NOT_AUTHORIZED` solely because the form was
   never submitted (`get-use-case-for-model-access` → "You have not filled out the
   request form"). Region must be **us-east-1 / N. Virginia** in the console — the
   account-default `ca-central-1` doesn't host these models. Path: Bedrock → Model
   catalog → enable any model → submit use-case details. Claude may additionally need
   its agreement accepted, which the API can do once the form exists.
2. **Diagnose the 50% failure rate** — **DONE 2026-08-13** (commits `82fdfc21`,
   `f41bdde5`). Root cause: the `deep`/`review` chains started with kimi on the
   TokenRouter host, which times out sporadically, then hit the OpenRouter paid-quota
   402 wall — and before the Bedrock tail existed there was nothing left, so all
   candidates logged 0 tokens. Not a routing bug: the hosts were down/limited.
   Fixes landed: the ledger now records failure reasons (`error` field, truncated to
   300 chars, shown in `ledger`), and `.mcp.json`'s kimi entry points at the live
   `api.tokenrouter.com/v1` instead of the dead `tokenrouter.ai` (local fix — file is
   gitignored for keys). Next failure is diagnosable in one `ledger` call, not three
   live probes.
3. **Prompt caching** in `_bedrock_converse()` — **DONE 2026-08-13** (`f41bdde5`).
   System prompts on `us.anthropic.*` models get a `cachePoint` block (~90% off cache
   reads; Anthropic is the only Converse family that honours it — Qwen/DeepSeek ignore
   the field, which is harmless). Still owed: confirm a 0-token-cost cache read on a
   second identical call once the form is filled.
4. Rotate the OpenRouter key.
5. Optional $20–25 OpenRouter top-up for Kimi K3 and Muse Spark.
