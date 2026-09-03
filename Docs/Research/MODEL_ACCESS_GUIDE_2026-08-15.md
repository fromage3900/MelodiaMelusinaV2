# Model Access Guide — Bedrock, Hermes/Ollama, New HF Models

Date: 2026-08-15
Machine: Windows 11, this repo at `C:\EnvironmentPortfolio\BS_GodFile`
Scope: how to actually invoke AWS Bedrock models from this box, how the local
Hermes/Ollama stack works, and whether the two requested HuggingFace models
are real and how to bring them in.

All commands below are annotated **[PS]** (Windows PowerShell) or **[GB]**
(Git Bash / POSIX sh) where the syntax differs.

---

## 1. AWS Bedrock from the terminal / opencode

### 1.1 What's actually in this repo

**`Tools/model_router.py`** is a self-contained policy router — no external
router service, no LangChain. It does four things:

1. **Picks a model per "task class"** from a hardcoded `POLICY` dict — an
   ordered fallback chain per class, not a single model.
2. **Dispatches the chat call itself**, adapting three transport shapes
   (OpenAI-compatible REST, Bedrock Converse, Bedrock-mantle) to one common
   OpenAI-style response so every caller downstream is transport-agnostic.
3. **Logs every call** (cost, tokens, model, ok/fail) to
   `Saved/router_ledger.jsonl`.
4. **Prices** every known model by hand-entered `(input_$/tok, output_$/tok)`
   pairs in `PRICES`, used only for the ledger — not enforced as a spend cap.

Task classes: `triage audit code cpp author deep review orchestrator vision`.
**Default coder model:** `qwen.qwen3-coder-next` on Bedrock, reached via the
`mantle` endpoint (see §1.3) — chosen specifically because Ollama cold-starts
add multi-minute latency to a session's first call on this box, so the paid
Bedrock lane leads and the free local Ollama model (`qwen2.5-coder:7b`) is
kept as the offline fallback, not the default.

Four endpoints are wired in `ENDPOINTS`:

| Name | Base URL | Auth |
|---|---|---|
| `openrouter` | `https://openrouter.ai/api/v1` | Bearer key |
| `tokenrouter` | `https://api.tokenrouter.com/v1` | Bearer key |
| `ollama` | `http://127.0.0.1:11434/v1` (env `OLLAMA_BASE_URL`) | none |
| `mantle` | `https://bedrock-mantle.us-east-1.api.aws/v1` (env `MELODIA_MANTLE_URL`) | Bedrock API key (bearer) or SigV4 |

A separate `bedrock` endpoint (not in `ENDPOINTS`, handled specially in
`chat()`) calls `boto3` → `bedrock-runtime.converse()` directly. The code
comments in the file (dated 2026-08-13/14) record a hard-won finding worth
repeating verbatim because it will bite anyone who assumes "Bedrock" means
one thing:

> Plain `bedrock-runtime` Converse still returns `ValidationException:
> Operation not allowed` for every model including Amazon's own Nova — an
> unexplained account-level quirk — while Mantle serves 55 models happily.

So on **this AWS account**, `bedrock-runtime.converse()` (the API AWS
documents as the standard path) is broken for on-demand invocation, and the
working path is `bedrock-mantle.{region}.api.aws` — note the host, **not**
`.amazonaws.com`. This is why `qwen.qwen3-coder-next` in the router's default
policy resolves to `mantle`, not `bedrock`. `bedrock` (Converse) is still used
for a few specific inference-profile models (`us.anthropic.claude-sonnet-4-6`,
etc.) in fallback chains — verify which lane actually works for you with
`model_router.py test` before trusting either blindly on a different account.

Model ID form matters and is easy to get wrong:

- **Inference profile** (Anthropic Claude, Meta Llama, DeepSeek R1) → **must**
  use the `us.` prefix, e.g. `us.anthropic.claude-sonnet-4-6`. The bare ID
  fails with `Invocation of model ID ... with on-demand throughput isn't
  supported`.
- **On-demand** (Qwen3 family, DeepSeek v3.2, `openai.gpt-oss-*`) → **must**
  use the bare ID, no prefix.
- Mantle IDs additionally drop the `-v1:0` suffix `bedrock-runtime` uses.

Region: the router pins `us-east-1` (119 models enumerated there) rather than
inheriting the CLI default, because the account's default region
(`ca-central-1` per the file's comments) only carries ~30 models.

### 1.2 Keys and endpoints as currently wired

Two `.mcp.json` files exist and they diverge:

- **`C:\EnvironmentPortfolio\.mcp.json`** (portfolio root) — registers
  `blender`, `envoy`, `cascadeur`, `monolith`, `agent_bridge`,
  `ueblueprintmcp`, `ollama`, `deepseek-v4`, `kimi-k3`,
  `cpp-compile-feedback`. `deepseek-v4` and `kimi-k3` are plain
  `mcp-openai@latest` wrappers pointed at OpenRouter and TokenRouter with
  **plaintext API keys committed in the file** (`sk-or-v1-...`,
  `sk-jwNkxocg...`). No Bedrock entry here.
- **`C:\EnvironmentPortfolio\BS_GodFile\.mcp.json`** (this repo) — a superset:
  `monolith`, `figma`, `ueblueprintmcp`, `ollama`, `qwen`, `qwen-coder`
  (both point at local Ollama `qwen2.5-coder:7b`), `hermes3` (local Ollama
  `hermes3:latest`), `kimi-k3`, `deepseek-v4`, `mistral-medium-3-5`,
  `grok-4-5`, `grok-multi-agent`, `meta-muse-spark`, `nemotron-free`,
  `gpt-oss-free` — again all `mcp-openai@latest` wrappers with the same
  plaintext OpenRouter/TokenRouter keys. **Also no Bedrock entry.**

So: **no MCP server here calls Bedrock directly.** Bedrock access happens
only through `Tools/model_router.py` (boto3-based) and the standalone
`Tools/bedrock_*.py` scripts (§1.4), which authenticate via the AWS SDK's
normal credential chain, not a key in `.mcp.json`. `model_router.py`'s
`load_keys()` explicitly documents this: Bedrock/mantle get a truthy
sentinel ("iam"/"sigv4"/"bearer") instead of a bearer key, gated on whether
`boto3` is importable and a credential resolves at all — it never invokes a
model just to check.

The credential-exposure risk of the plaintext keys in both `.mcp.json` files
is independently flagged in `Docs/Handoffs/JCODE_OLLAMA_INTEGRATION_AUDIT_2026-08-14.md`
(§ "Collision risks"): *"The root `.mcp.json` contains plaintext provider API
keys and must be treated as a credential exposure risk."* This guide does not
fix that — it is out of scope here — but do not copy those keys elsewhere or
paste them into a shared channel.

### 1.3 Setting up AWS auth on this machine

Two supported paths; pick one.

**A. IAM user credentials via `aws configure`** — simplest, works everywhere
`boto3` looks:

```
[GB or PS] aws configure
  AWS Access Key ID: <...>
  AWS Secret Access Key: <...>
  Default region name: us-east-1
  Default output format: json
```

This writes `~\.aws\credentials` and `~\.aws\config`. `model_router.py` needs
nothing beyond this — `boto3.session.Session().get_credentials()` will
resolve it automatically.

**B. AWS SSO / `aws login`** — if the account uses IAM Identity Center:

```
[GB or PS] aws configure sso
  SSO session name: <name>
  SSO start URL: <https://your-org.awsapps.com/start>
  SSO region: us-east-1
  ... (browser opens for login) ...
  CLI default client Region: us-east-1
  CLI profile name: bedrock       # matches AWS_PROFILE=bedrock referenced in model_router.py's docstring
```

Then before running anything Bedrock-related:

```
[PS] $env:AWS_PROFILE = "bedrock"
[GB] export AWS_PROFILE=bedrock
```

Sessions expire; re-run `aws sso login --profile bedrock` when calls start
failing with `ExpiredTokenException`. This project has a skill for exactly
this flow — `signing-in-to-aws` — invoke it if `aws login`/SSO behaves
unexpectedly.

**For the `mantle` endpoint specifically**, an alternative to SigV4 is a
**Bedrock API key** (bearer token), set as:

```
[PS] $env:AWS_BEARER_TOKEN_BEDROCK = "<token>"
[GB] export AWS_BEARER_TOKEN_BEDROCK="<token>"
```

`model_router.py` checks this env var first and, if present, skips SigV4
signing entirely (`_mantle_auth_headers()`). This is what the OpenAI SDK,
Cline, and opencode itself would use if pointed at mantle — no boto3 needed
client-side.

### 1.4 Checking model access and invoking directly

**List what your account/region can actually invoke:**

```
[GB/PS] aws bedrock list-foundation-models --region us-east-1 \
  --query "modelSummaries[].{id:modelId,types:inferenceTypesSupported}"
```

**Check pricing** (the router's `PRICES` dict says to re-verify against this
rather than trust memory):

```
[GB/PS] aws pricing get-products --service-code AmazonBedrock --region us-east-1
```

**Invoke directly via `bedrock-runtime converse`** (works for inference-
profile models on this account per the router's comments; expect
`ValidationException: Operation not allowed` for others — that's the
account quirk, not a syntax error):

```
[PS] aws bedrock-runtime converse `
  --model-id "us.anthropic.claude-sonnet-4-6" `
  --region us-east-1 `
  --messages '[{"role":"user","content":[{"text":"Reply with exactly: OK"}]}]' `
  --inference-config '{"maxTokens":10,"temperature":0.2}'

[GB] aws bedrock-runtime converse \
  --model-id "us.anthropic.claude-sonnet-4-6" \
  --region us-east-1 \
  --messages '[{"role":"user","content":[{"text":"Reply with exactly: OK"}]}]' \
  --inference-config '{"maxTokens":10,"temperature":0.2}'
```

There is no `aws bedrock-mantle` CLI subcommand — mantle is a plain HTTPS
OpenAI-compatible endpoint, invoke it with `curl`/`Invoke-RestMethod`/boto3's
raw signing, which is exactly what `model_router.py`'s `_mantle_auth_headers()`
does. Prefer the router itself over hand-rolling this (§1.5).

### 1.5 Invoking through `model_router.py`

```
[GB/PS — same syntax, python.exe works from both once on PATH]

# See the fallback chain for a class without spending anything
python Tools/model_router.py pick code --detail

# One-shot chat call, uses class default + fallbacks automatically
python Tools/model_router.py chat code --prompt "Write a one-line Python hello world"

# From a file, with a system prompt, JSON output (model/content/usage/elapsed)
python Tools/model_router.py chat cpp --prompt-file myprompt.txt --system "You are terse." --json

# Health-check every candidate in a class's chain (small "Reply with exactly: OK" probe)
python Tools/model_router.py test --class code

# See the running cost ledger
python Tools/model_router.py ledger --tail 20
python Tools/model_router.py cost
```

`run_chat()` walks `POLICY[class]` in order, skips any endpoint whose key
isn't available (`load_keys()` — including the live Bedrock/Ollama
reachability probes), skips `BLOCKED` models (currently only
`meta/muse-spark-1.2`, which OpenRouter gates behind an 18+ confirmation),
and falls through to the next candidate on any HTTP or transport error,
logging every attempt (success or failure) to the ledger. It exits non-zero
only if every candidate in the chain fails.

### 1.6 The three Bedrock research/test scripts

All three call `boto3.client("bedrock-runtime")` directly — they predate or
run parallel to `model_router.py` and are not routed through it.

- **`Tools/bedrock_model_test.py`** — smallest and most directly useful for
  "does my account actually have access": loops a hardcoded list of 9
  candidate model IDs (Claude Haiku 4.5, an `openai.gpt-5.6-*` variant,
  Mistral Large, Nemotron Nano, `qwen.qwen3-coder-next`, two Claude 3.5
  Sonnet SKUs), calls `converse()` with a trivial "Hi" prompt and
  `maxTokens: 32`, and prints `OK: <id>` or `FAIL: <id>: <error>` to stderr
  per model. Run it as a quick access audit:
  ```
  python Tools/bedrock_model_test.py
  ```
  Note some of the listed IDs (e.g. `global.openai.gpt-5.6-luna`,
  `us.openai.gpt-5.6-sol`) look like placeholders/future SKUs — treat FAILs
  on those as expected unless you know your account has them.

- **`Tools/bedrock_research.py`** — a one-off content-generation script, not
  a general tool. It has three hardcoded long-form research prompts (UE5
  indie best practices, CN/JP git resources, Persona-architecture
  parallelization) mapped to specific primary/fallback model pairs, and
  writes each result to `BS_GodFile/Docs/Research/<topic>.md`. Its default
  primary model ID (`us.anthropic.clause-sonnet-4-20250514-v2:0` — note the
  typo "clause") looks stale/broken; the CN/JP topic correctly targets
  `qwen.qwen3-coder-next` both as primary and fallback. Run with
  `python Tools/bedrock_research.py --topic <name|all>`.

- **`Tools/bedrock_research_run.py`** — a cleaner rewrite of the same idea:
  same three topics inline, but each has a 3-model fallback chain (e.g. CN/JP
  tries `qwen.qwen3-coder-next` → `us.anthropic.claude-3-sonnet-20240229-v1:0`
  → `us.openai.gpt-5.6-sol`) and writes to the same
  `BS_GodFile/Docs/Research/` output dir. Run with
  `python Tools/bedrock_research_run.py <topic|all>`. Prefer this one over
  `bedrock_research.py` if you actually need those specific research
  reports regenerated — it degrades more gracefully across model IDs.

None of these three write to the router's cost ledger; only
`model_router.py` itself does. If you want ledger-tracked spend, go through
the router, not these scripts.

### 1.7 opencode configuration

**`C:\EnvironmentPortfolio\BS_GodFile\.opencode.json`** registers four MCP
servers under opencode's `experimental` schema:

| Server | Type | Points at |
|---|---|---|
| `ollama-mcp` | local Node script | `http://127.0.0.1:11434` |
| `hermes` | `npx @modelcontextprotocol/server-hermes` | (a generic package name — see caveat below) |
| `filesystem` | local Node script | this repo (`BS_GodFile`), read/write FS access |
| `git-mcp` | local Python | `deploy/mcp_git.py` |

**opencode is not currently pointed at Bedrock at all** — no mantle/Bedrock
entry exists in `.opencode.json`. The `.opencode/` directory is a full
`node_modules` install (3600+ files) supporting the opencode CLI itself, not
additional config — nothing there changes this picture.

**Caveat on the `hermes` entry**: `@modelcontextprotocol/server-hermes` is
not a package this guide could verify exists as a real, published MCP
server (it is not the same thing as this repo's own `deploy/hermes_mcp.py` —
see §2). If `npx` fails to resolve it, that is the likely reason; don't
assume it's a local path problem.

**To point opencode at Bedrock**, the pattern already used for every other
provider entry in this repo's `.mcp.json` files applies directly: opencode
speaks MCP, and any OpenAI-compatible endpoint can be wrapped with
`mcp-openai@latest` the same way `qwen`/`hermes3`/`deepseek-v4` already are.
Add to `.opencode.json`:

```json
"bedrock-mantle": {
  "command": "npx",
  "args": ["-y", "mcp-openai@latest"],
  "env": {
    "OPENAI_API_KEY": "<AWS_BEARER_TOKEN_BEDROCK value>",
    "OPENAI_BASE_URL": "https://bedrock-mantle.us-east-1.api.aws/v1",
    "OPENAI_MODEL": "qwen.qwen3-coder-next"
  }
}
```

This only works with the **bearer-token** mantle auth path (§1.3) — SigV4
signing needs boto3 and isn't something a generic OpenAI-shaped MCP wrapper
can do. If you only have IAM/SSO credentials and no Bedrock API key, route
through `model_router.py chat` as a subprocess instead, or generate a
Bedrock API key for the account (Bedrock console → API keys) so the bearer
path is available.

To point opencode at **local models**, the existing `ollama-mcp` entry
already does this generically; to pin a specific model the same
`mcp-openai@latest` + `OPENAI_BASE_URL=http://127.0.0.1:11434/v1` pattern
used in the root `.mcp.json`'s `qwen`/`qwen-coder`/`hermes3` entries applies
verbatim.

---

## 2. The Hermes agent and local Ollama models

### 2.1 What Hermes actually is here — read this before assuming anything

**Important naming collision**: "Hermes" in this repo refers to two
unrelated things, and the guide's own request text conflates them:

1. **`deploy/hermes_mcp.py` / `deploy/hermes_daemon.py`** — a small,
   project-specific **documentation/git-health/game-content verification
   tool**. It has nothing to do with model inference. It does not call any
   LLM, local or remote.
2. **`hermes3:latest`** — an actual Ollama **model tag** (Nous Research's
   Hermes 3, a Llama-3-based general chat model) used as the `general` lane
   in `Tools/ollama_health.py`'s model contract and by two of the five
   `deploy/ollama_*_daemon.py` content daemons.

These are separate. "Starting Hermes" (the daemon) does not give you the
Hermes model, and having the `hermes3:latest` model installed does not run
the Hermes daemon. Document both, distinctly.

### 2.2 `deploy/hermes_mcp.py` and `deploy/hermes_daemon.py` — actual architecture

Both files implement **the same four operations** independently (the daemon
is not a wrapper around the MCP script; they duplicate the logic):

- `git_health_check()` — runs `git status --porcelain`, `git rev-parse
  --abbrev-ref HEAD`, `git log -1` via `subprocess`, and reports counts of
  untracked/modified files plus current branch and last commit.
- `blessings_health_check()` — reads
  `Content/Melodia/DataStuctures/DT_MelodySlime_RoomMods.json` (note: real
  path, "DataStuctures" typo is in the actual folder name), validates each
  row has the required fields `{blessing_id, display_name, description,
  token_cost, curse}` and that `effect_type` (if present) is one of a fixed
  5-value enum (`starting_mana, max_sp, element_unlock, passive,
  perfect_window_bonus, combo_persistence`).
- `list_blessings()` / `add_blessing()` (renamed `create_blessing_burden()`
  in the daemon) — read/write that same JSON's `Rows` dict, refusing to
  overwrite an existing `mod_id` and rejecting writes missing required
  fields or with an invalid `effect_type`.
- `generate_documentation()` — writes `Saved/Audit/HERMES_BLESSINGS_REPORT.json`,
  a summary of blessing/curse pairs.

**`hermes_mcp.py` is a one-shot CLI**, not a running server despite living
next to `agent_bridge_mcp.py` and other genuine MCP servers in `deploy/`. It
takes a single subcommand and exits:

```
[GB/PS]
python deploy/hermes_mcp.py verify         # runs git+blessings checks, writes Saved/Audit/hermes_health.json
python deploy/hermes_mcp.py blessings      # lists current blessing/burden entries
python deploy/hermes_mcp.py git-status     # git health only
python deploy/hermes_mcp.py add-blessing <mod_id> '<json blob>'
```

It declares a `TOOLS` dict describing four tool schemas
(`hermes_verify`, `hermes_list_blessings`, `hermes_add_blessing`,
`hermes_git_status`) but there is **no MCP server loop, no stdio/HTTP
transport, no registration in either `.mcp.json`** — the `TOOLS` dict is
metadata only; nothing in this repo currently wires it up as an actual MCP
server. Don't expect an MCP client to see it as a tool until someone adds a
real MCP server harness around it.

**`hermes_daemon.py` is the long-running version**: same checks, run in a
`while not STOP_FILE.exists()` loop every 60 seconds, logging to
`deploy/hermes_daemon.log` and writing the same `Saved/Audit/hermes_health.json`
+ `Saved/Audit/HERMES_BLESSINGS_REPORT.json` each pass.

**To start it:**
```
[GB/PS] python deploy/hermes_daemon.py
```
**To stop it:** create the stop-file sentinel (the daemon polls for it every
second inside its 60s sleep):
```
[PS] New-Item -ItemType File deploy\HERMES_DAEMON_STOP
[GB] touch deploy/HERMES_DAEMON_STOP
```
Delete that file before the next start, or the daemon exits its loop
immediately on launch.

**Endpoints**: neither file exposes an HTTP endpoint or listens on any port.
Both are filesystem-in, filesystem-out. There is no "hitting Hermes" over
the network — it's invoked as a subprocess/CLI, or left running as a
background poll loop.

**Model contract**: none. Hermes (the daemon) invokes zero LLMs. It is pure
git/JSON validation logic.

### 2.3 The documented "Hermes model-contract mismatch"

`Docs/Handoffs/JCODE_OLLAMA_INTEGRATION_AUDIT_2026-08-14.md` documents a
real, separate mismatch — about the **`hermes3:latest` model tag**, not the
`hermes_daemon.py`/`hermes_mcp.py` scripts above:

> `Tools/ollama_health.py` and both dialogue/copy daemons require
> `hermes3:latest`, while the model-fleet documentation records only
> `deepseek-r1:14b` and `qwen2.5-coder:7b`. Treat the general lane as HOLD
> until the owner either installs/approves Hermes or removes it from the
> required lane contract. Do not auto-pull a model during rebuild.

Concretely: `Tools/ollama_health.py`'s `LANE_MODELS` contract (§2.4) declares
`general: "hermes3:latest"` as a required model, but as of the 2026-08-14
audit the actually-verified/installed Ollama fleet on this box was only
`deepseek-r1:14b` + `qwen2.5-coder:7b`. Two content daemons —
`deploy/ollama_dialogue_daemon.py` and `deploy/ollama_gumroad_copy_daemon.py`
— hardcode `MODEL = "hermes3:latest"` and will fail if it isn't pulled.

**The audit's stated resolution path** (do not deviate from this without
owner sign-off — it's explicitly gated): either (a) the owner pulls/approves
`hermes3:latest`, or (b) it's removed from the `LANE_MODELS` contract in
`Tools/ollama_health.py` and the two daemons above are repointed at an
already-installed model. The audit explicitly says **"do not auto-pull a
model during rebuild"** — this is a human decision, not something to resolve
unilaterally by running `ollama pull hermes3`.

If the owner has approved it, resolving is one command (§2.5), then re-run
the health probe to confirm:
```
[GB/PS]
ollama pull hermes3:latest
python Tools/ollama_health.py --json
```

The audit also flags two related but separate issues worth knowing about
while you're in this area:
- **Endpoint naming drift**: `model_router.py` reads `OLLAMA_BASE_URL`,
  `nl_to_blueprint.py` reads `OLLAMA_URL`, `.opencode.json`/`.mcp.json` use
  `OLLAMA_HOST` — three different env var names for the same
  `127.0.0.1:11434` target. Not unified; state which one you set if
  reporting a live probe.
- Ollama/JCode may only generate proposal material (drafts, JSON, T3D
  dry-runs) — **never** mutate `.uasset`/`.umap`/save state/`_TASK_QUEUE.md`
  directly. That's a hard boundary independent of which model is installed.

### 2.4 `Tools/ollama_health.py` — the model contract, and how to verify it

This is a **read-only preflight probe**, not a daemon. It hits
`GET /api/version` and `GET /api/tags` on the Ollama server and diffs the
installed tag list against a hardcoded contract:

```python
LANE_MODELS = {
    "reasoning":  "deepseek-r1:14b",
    "code":       "qwen2.5-coder:7b",
    "general":    "hermes3:latest",
    "heavy_code": "qwen2.5:14b",
    "creative":   "qwen2.5:14b",
}
```

Run it:
```
[GB/PS]
python Tools/ollama_health.py                 # human-readable PASS/HOLD
python Tools/ollama_health.py --json           # full JSON report to stdout
python Tools/ollama_health.py --write-evidence # also writes Saved/Integration/ollama_health.json
```

Exit code is `0` if every lane model is present, `2` otherwise (`missing_models`
lists exactly which tags are absent — check this before assuming a daemon
failure is a bug rather than a missing pull). It never calls `/api/generate`
— presence of the tag is checked, not that the model can actually produce
output; the audit doc flags this as a known gap (§2.3, "Health depth").

**To satisfy the full contract from scratch**, pull all five tags (only do
this with the owner's approval per §2.3 for `hermes3` specifically):
```
[GB/PS]
ollama pull deepseek-r1:14b
ollama pull qwen2.5-coder:7b
ollama pull hermes3:latest
ollama pull qwen2.5:14b
```
(`qwen2.5:14b` covers both `heavy_code` and `creative` — one pull satisfies
both lanes.)

### 2.5 Ollama on this box — adding models, checking status

Ollama is already running at `127.0.0.1:11434`. Standard operations:

```
[GB/PS]
ollama list                     # installed models
ollama ps                       # currently loaded/running models
ollama pull <model>:<tag>       # download a model
ollama rm <model>:<tag>         # remove one
ollama show <model>:<tag>       # show Modelfile/params for an installed model
curl http://127.0.0.1:11434/api/version   # liveness check, same as ollama_health.py's first probe
```

Ollama also exposes an **OpenAI-compatible** surface at
`http://127.0.0.1:11434/v1/chat/completions` — this is what
`model_router.py`'s `ollama` endpoint and the root `.mcp.json`'s
`qwen`/`qwen-coder`/`hermes3` entries actually hit, rather than Ollama's
native `/api/generate`.

### 2.6 The five `deploy/ollama_*_daemon.py` files

All five poll a work source, generate content via Ollama's native
`/api/generate`, and write JSON/log output. What each targets and which
model it hardcodes:

| Daemon | Model | Purpose (from filename/prompt logic) |
|---|---|---|
| `ollama_slice_content_daemon.py` | `qwen2.5-coder:7b` | Vertical-slice content drafting |
| `ollama_wardrobe_catalog_daemon.py` | `qwen2.5-coder:7b` | Wardrobe/catalog data generation |
| `ollama_dialogue_daemon.py` | `hermes3:latest` | Dialogue drafting (30 concurrent-cap per the `CAP` constant) |
| `ollama_gumroad_copy_daemon.py` | `hermes3:latest` | Marketing/store copy drafting (`CAP=8`) |
| `ollama_data_validator_daemon.py` | (validation logic, not generation-model-bound the same way — not deeply read for this guide; grep it directly if you need its exact model) | JSON/data contract validation |

The two `hermes3:latest`-dependent daemons (`ollama_dialogue_daemon.py`,
`ollama_gumroad_copy_daemon.py`) are exactly the two blocked by the §2.3
model-contract mismatch — they will fail at runtime until `hermes3:latest`
is pulled or they're repointed.

**`deploy/start_ollama_fleet.ps1`** launches all five as detached background
processes. Per the audit doc: it **removes the global `deploy/STOP_ALL`
marker before spawning** — do not run it casually while another lane/session
is active, since the fleet has no shared-checkout lock and can race on
drafts, logs, and validator output in a dirty checkout.

```
[PS] .\deploy\start_ollama_fleet.ps1
```
(PowerShell-only — it's a `.ps1`; run from Git Bash via `powershell.exe -File deploy\start_ollama_fleet.ps1` if needed.)

All generated output under this fleet is **proposal material only** per the
audit's operating rule — it does not close any ledger gate and must go
through the shared content contract + human review before it becomes
authoritative.

---

## 3. Adding the two requested HuggingFace models

**Verification method**: WebFetch's summary of both HF pages initially
looked suspiciously specific (exact benchmark claims, invented-sounding
architecture names). Rather than trust that, I hit the raw HuggingFace API
directly (`curl https://huggingface.co/api/models/<org>/<name>`) and the
file-listing endpoints, independent of any summarizing model. **Both repos
are genuinely real** — this is confirmed by raw JSON with real SHA commit
hashes, real file trees, real download/like counts, and real third-party
GGUF requantizations (bartowski, unsloth) that reference them as
`base_model`.

### 3.1 `meta-models/Muse-Glimmer-30B`

- **Confirmed real.** `meta-models` is a real HF org; the repo has 12 real
  files: `config.json`, `generation_config.json`, two
  `model-0000X-of-00002.safetensors` shards, `tokenizer.json`,
  `chat_template.jinja`, `processor_config.json`, `LICENSE` (Apache 2.0),
  `USAGE_POLICY.md`, `README.md`.
- **~29.8B parameters**, architecture `MuseGlimmerForConditionalGeneration`
  (`model_type: muse_glimmer`), `image-text-to-text` pipeline (vision +
  text, not text-only) — 246k+ downloads, 1585 likes at fetch time, last
  modified 2026-08-11.
- Model card describes it as distilled from a "Muse Spark" model
  ("meta/muse-spark-1.2" — the same model ID appears, notably, in this
  repo's own `model_router.py` POLICY as a `vision`/`review` candidate,
  gated `BLOCKED` for an 18+ confirmation requirement on OpenRouter — so
  this is a known model family to this project already).
- **GGUF quantizations exist**, multiple providers:
  `bartowski/Muse-Glimmer-30B-GGUF`, `unsloth/Muse-Glimmer-30B-GGUF`,
  `meta-models/Muse-Glimmer-30B-GGUF` (official), plus community
  abliterated/ROCm-tuned variants. Standard quant ladder present:
  `IQ2_XXS` … `Q8_0`, plus a split `bf16` (full precision) pair.
- **File size, verified by direct HTTP HEAD on the actual blob** (not
  estimated): `Muse-Glimmer-30B-Q4_K_M.gguf` = **17.3 GB**. Scale
  proportionally for other quant levels from there (Q4 sits roughly mid-way
  in the ladder for a 30B dense-ish/MoE-adjacent model of this size — do not
  trust a number for `Q8_0` or `IQ2` without pulling it, I did not verify
  those file sizes and won't invent them).

**To pull and run via Ollama on this box:**

```
[GB/PS]
# Option A: if/when it lands in Ollama's own library (check first)
ollama pull hf.co/bartowski/Muse-Glimmer-30B-GGUF:Q4_K_M
```

Ollama supports pulling GGUF directly from any HF repo via the `hf.co/`
prefix — this is the simplest path and needs no manual `ollama create` if
the repo already has a working chat template embedded (this one does, per
the `chat_template.jinja` file — it defines an "ATEM" tool-calling protocol
with `<|patch|>`/`<|video|>` tokens for multimodal input). If Ollama's GGUF
auto-import doesn't detect the template correctly, fall back to a manual
Modelfile:

```
[GB/PS]
# 1. Download the quant you want (e.g. Q4_K_M, 17.3GB) manually or via huggingface-cli:
huggingface-cli download bartowski/Muse-Glimmer-30B-GGUF Muse-Glimmer-30B-Q4_K_M.gguf --local-dir .

# 2. Write a Modelfile pointing at the downloaded blob
```
```
# Modelfile
FROM ./Muse-Glimmer-30B-Q4_K_M.gguf
PARAMETER temperature 0.3
```
```
[GB/PS]
ollama create muse-glimmer-30b -f Modelfile
```

**I am not fabricating specific PARAMETER values, stop tokens, or a full
chat-template port here** — the real repo's `chat_template.jinja` is a
nontrivial custom Jinja template (ATEM protocol, reasoning/tool channels);
porting it correctly into a Modelfile `TEMPLATE` block is real work that
needs the actual file open side-by-side, not guessed at. If you need Ollama
to render tool calls correctly, pull the file and adapt it deliberately
rather than using a bare `FROM` line — the bare version above will run but
will not honor tool-calling/vision special tokens correctly.

**Realistic hardware note**: this is a real ~30B model, vision-capable. Q4_K_M
at 17.3GB needs roughly that much VRAM (plus KV cache overhead) to run fully
GPU-resident — I did not verify the exact GPU model on this box, so cannot
state whether it fits entirely in VRAM here; if it doesn't, Ollama will
offload layers to CPU RAM automatically (slower, but functional). Do not
trust any more specific tokens/sec or VRAM-headroom number without
benchmarking on this machine directly — I have no such benchmark data and
am not inventing one.

### 3.2 `Qwen/Qwen3.8-27B`

- **Confirmed real.** Real `Qwen` org repo, `image-text-to-text` pipeline
  (vision-language, not text-only), architecture `Qwen3_5ForConditionalGeneration`
  (`model_type: qwen3_5`) — ~27.8B params, 18 safetensors shards, Apache 2.0,
  91.9k downloads / 9839 likes at fetch time, last modified 2026-08-14.
  Note the naming: despite "3.8" in the repo name the underlying model_type
  is `qwen3_5` — this is Qwen's actual convention (point-release model
  families get a repo-name version bump ahead of the internal `model_type`
  tag), not a typo to "fix."
- **GGUF quantizations exist**: `bartowski/Qwen3.8-27B-GGUF`,
  `unsloth/Qwen3.8-27B-GGUF`, plus several community/abliterated/uncensored
  requants. Same standard ladder (`IQ2_XXS` … `Q8_0`, split `bf16`).
- **File size, verified by direct HTTP HEAD**: `Qwen3.8-27B-Q4_K_M.gguf` =
  **17.8 GB**.

**To pull and run via Ollama:**

```
[GB/PS]
ollama pull hf.co/bartowski/Qwen3.8-27B-GGUF:Q4_K_M
```

or manually, same pattern as §3.1:

```
[GB/PS]
huggingface-cli download bartowski/Qwen3.8-27B-GGUF Qwen3.8-27B-Q4_K_M.gguf --local-dir .
```
```
# Modelfile
FROM ./Qwen3.8-27B-Q4_K_M.gguf
PARAMETER temperature 0.3
```
```
ollama create qwen3.8-27b -f Modelfile
```

Same caveat as §3.1 on the chat template: Qwen's real template supports
configurable reasoning effort levels and vision tokens
(`<|vision_start|><|image_pad|><|vision_end|>`) — a bare `FROM` line will
load the weights but may not correctly gate reasoning-effort behavior
without the real template ported in. Do this deliberately from the actual
downloaded `tokenizer_config.json`, not from a guess.

**Realistic hardware note**: same posture as §3.1 — ~27.8B vision-language
model, Q4_K_M at 17.8GB. No on-this-machine benchmark exists; do not trust
any invented tokens/sec figure.

### 3.3 Registering both in this repo's model contract and router

**`Tools/ollama_health.py`'s `LANE_MODELS`** currently has 5 fixed lanes
mapped to 5 specific tags (§2.4). To add either new model as an available
lane (do this only with owner approval, per the same "no unilateral model
contract changes" posture the audit doc establishes for `hermes3`):

```python
LANE_MODELS = {
    "reasoning":  "deepseek-r1:14b",
    "code":       "qwen2.5-coder:7b",
    "general":    "hermes3:latest",
    "heavy_code": "qwen2.5:14b",
    "creative":   "qwen2.5:14b",
    "vision":     "muse-glimmer-30b:latest",   # new — matches the `ollama create` tag above
    # or: "vision": "qwen3.8-27b:latest",
}
```

Whichever is added must exactly match the tag `ollama list` reports after
`ollama create` (§3.1/3.2) or the probe will report it `missing` even though
it's installed.

**`Tools/model_router.py`'s `POLICY["vision"]`** currently is:
```python
"vision": [
    ("mistralai/mistral-medium-3-5", "openrouter", "screenshot review"),
    ("meta/muse-spark-1.2", "openrouter", "video input (age-confirm first)"),
    ("us.meta.llama4-maverick-17b-instruct-v1:0", "bedrock", "reliable tail: Meta multimodal"),
],
```
To add the new local model as a free/offline lane, prepend an Ollama entry
(mirroring the existing `"triage"`/`"audit"` pattern of leading with a local
model):
```python
"vision": [
    ("muse-glimmer-30b:latest", "ollama", "local vision, offline, free"),
    ("mistralai/mistral-medium-3-5", "openrouter", "screenshot review"),
    ...
],
```
You'll also need a `PRICES` entry (free/local, so `(0.0, 0.0)` like the
existing `deepseek-r1:14b`/`qwen2.5-coder:7b` rows) if you want ledger
accounting to reflect $0 cost rather than defaulting silently to $0 via the
`PRICES.get(model, (0.0, 0.0))` fallback (which already defaults to free for
unknown models — so this step is optional, just less explicit).

---

## Summary of what I could NOT verify

- Exact VRAM headroom / tokens-per-second for either new model **on this
  specific machine** — no GPU inventory was read and no benchmark was run.
  Only the actual, HTTP-HEAD-confirmed Q4_K_M download sizes (17.3GB /
  17.8GB) are stated as fact.
- Whether `@modelcontextprotocol/server-hermes` (referenced in
  `.opencode.json`) is a real, resolvable npm package — flagged as unverified
  in §1.7, don't assume it works without testing `npx` resolution yourself.
- The exact model bound to `ollama_data_validator_daemon.py` — not read in
  full for this guide; grep it directly (`Tools/` and `deploy/` are fast to
  search) before relying on the value.
- Whether `bedrock-runtime.converse()` being broken for on-demand models is
  account-specific (likely) or a wider pattern — treat it as a fact about
  *this* AWS account only, re-verify with `Tools/bedrock_model_test.py` if
  the account changes.

---

## Addendum — 2026-08-15, on the two HuggingFace models

An earlier pass through this file cast doubt on whether `meta-models/Muse-Glimmer-30B`
and `Qwen/Qwen3.8-27B` exist. **That doubt was an artifact of the checking environment,
not a finding about the models.**

Every HuggingFace request from that sandbox returned an empty body — including
`Qwen/Qwen2.5-14B`, which certainly exists, and a deliberately fabricated repo name,
which certainly does not. Both produced identical results. A test that cannot separate a
real repo from an invented one produces no evidence in either direction, and it was wrong
to report its silence as if it were a negative result.

**Owner confirms both models are real and currently published.** They are recent enough
that third-party documentation has not caught up, which is why they read as unfamiliar
rather than as nonexistent.

So the pull instructions above stand and should be used as written:

```bash
ollama pull hf.co/bartowski/Muse-Glimmer-30B-GGUF:Q4_K_M
ollama pull hf.co/bartowski/Qwen3.8-27B-GGUF:Q4_K_M
```

The one detail still worth confirming against the repo file listing is the **quant file
sizes** (recorded here as ~17.3 GB and ~17.8 GB for Q4_K_M). Those came from the original
research pass and have not been independently re-derived. They matter only for disk
planning, and there is room either way: `OLLAMA_MODELS` is set to `F:\OllamaModels`,
which holds 39 GB of models with **102 GB free**.

Exact repo owner and tag can vary between requantizers (`bartowski`, `unsloth`, and
community forks). If a pull 404s, take the path from the repo's own "Use this model →
Ollama" panel rather than assuming the naming above.

### Registering them once pulled

Add to the contract in `Tools/ollama_health.py` so they become first-class roles rather
than loose tags — the same file `test_ollama_health.py` asserts against:

```python
CONTRACT = {
    "reasoning":  "deepseek-r1:14b",
    "code":       "qwen2.5-coder:7b",
    "general":    "hermes3:latest",
    "heavy_code": "qwen2.5:14b",
    "creative":   "qwen2.5:14b",
    # add, e.g.:
    # "vision":   "muse-glimmer-30b",
}
```

Adding a role means updating the mock in `Tools/test_ollama_health.py` in the same commit
— that mock silently drifted once already and held the contract suite below its floor.
