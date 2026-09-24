# Hermes Bootstrap Mission — Specialist Model Fleet — 2026-09-23

You are Hermes, the Melodia Melusina orchestration owner.

Your task is to **set up and benchmark the new specialist-model fleet without changing Melodia's authority graph or silently replacing any working provider**.

## Read first

Read, in order:

1. `AGENTS.md`
2. `CURRENT_STATE.md`
3. `Docs/ORCHESTRATION_HERMES_GATEWAY_2026-08-25.md`
4. `Docs/Production/UNIVERSE_FOUNDRY_CONTRACT.md`
5. `Docs/Plans/HERMES_SPECIALIST_MODEL_FLEET_SETUP_2026-09-23.md`
6. `specs/orchestration/hermes_specialist_fleet.candidates.v1.json`
7. `Docs/Research/MODEL_ACCESS_GUIDE_2026-08-15.md`

## Mission constraints

- Do not write secrets into Git, shell history, benchmark JSON, screenshots, or chat transcripts.
- Report credential **presence/missing only**.
- Do not replace the current Hermes default permanently during a canary.
- Snapshot the current local Hermes configuration before changing providers.
- Restore the previous Hermes provider/default after every temporary provider probe unless the owner explicitly approves promotion.
- Do not edit `Tools/model_router.py` until a candidate has passed its canaries and the owner approves a routing diff.
- Do not grant Jev editor mutation authority.
- Do not let HappyOyster, image, voice, avatar, or multimodal models become gameplay/world/save authority.
- Do not install all candidates as always-on daemons.
- Do not claim a provider/model works until you make a real call.
- Do not self-certify implementation patches.

## Phase 0 — audit only

Before installing or changing anything, produce a compact audit containing:

- current date/time;
- repo HEAD + branch + dirty/clean state;
- Hermes version;
- `hermes doctor` result;
- current Hermes provider/base/model **without printing key values**;
- WSL availability/version;
- installed status/version for:
  - Muse Code
  - Devin
  - Claude Code
  - Kimi CLI
  - Codex
  - OpenCode
  - Goose
  - Pi / Muselinn if present
- `python Tools/model_router.py list`;
- detail for current `orchestrator`, `code`, `vision`, `deep`, `review` lanes;
- presence/missing for:
  - `MODEL_API_KEY`
  - `MIMO_API_KEY`
  - `STEP_API_KEY`
  - `INCEPTION_API_KEY`
  - current QwenCloud credential variable(s)
  - Devin authentication
- free disk / GPU summary relevant to Muse Glimmer.

Write sanitized audit output under:

`Saved/Audit/hermes_model_benchmarks/2026-09-23/setup_audit.json`

If the directory is ignored/untracked by policy, keep it local and report the exact path; do not change ignore policy just for this mission.

Then STOP and show the owner:
- what is already ready;
- which provider/account actions require the owner;
- which candidates can be tested immediately.

## Phase 1 — configure only owner-approved providers

Default suggested order:

1. MiMo V2.6 Pro
2. Muse Spark 1.3
3. Mercury 2.5
4. Step 5 Preview
5. Qwen3.8 Omni Flash

### MiMo special rule

Read Xiaomi's first-party Hermes integration guide referenced by the plan.

Before changing Hermes config:
- snapshot `~/.hermes/config.yaml` to a local timestamped backup outside Git;
- record old provider/base/default in sanitized audit;
- never print the key.

Configure only through supported Hermes config methods.

Run:

`hermes doctor`

Then run one B0 connectivity test and one B4 Foundry planning canary.

Restore the previous Hermes config afterward unless the owner says to keep MiMo as default.

### Meta / Muse

On Windows:
- use Meta Model API directly for API benchmarks;
- use WSL for Muse Code because the official Muse Code installer is macOS/Linux.

Before using Muse Code's `migrate` skill, display what configs it intends to import. Do not duplicate MCP servers.

### StepFun

Do not guess the Step 5 Preview model id. Query/inspect the current account/model listing or current first-party docs at setup time. Record the exact id used.

### Mercury

Use as a fast-subagent canary. Do not promote it to hard architecture tasks from speed alone.

## Phase 2 — run standard benchmarks

Use the benchmark definitions in the setup plan.

For every run, write one sanitized ledger record with:

- candidate;
- provider/surface;
- exact model id;
- benchmark id;
- repo HEAD;
- wall time;
- TTFT if available;
- token counts if reported;
- provider-reported or exactly derived cost if available, otherwise null;
- tool-call count if available;
- acceptance result;
- failure class;
- evidence paths.

Never infer missing prices.

## Phase 3 — specialist workers

### SWE-2

Verify current Devin Desktop/CLI access. Do not assume a generic API.

Only add a Hermes delegation adapter if Devin supports a suitably bounded/noninteractive invocation. Otherwise benchmark manually and keep status SPECIALIST/WATCH.

### Muse Glimmer

Before download:
- identify the exact supported model artifact/quantization;
- calculate disk requirement;
- compare against available VRAM/RAM;
- get owner approval for a large download.

First mission is read-only log/audit work.

### Qwen3.8 Omni

Use for multimodal defect/evidence packets. No editor mutation.

### HappyOyster

Use Faraway Mother as the first canary, but **Jev audits both before and after the run**.

#### J0 — preflight

Luna/Hermes assembles:
- approved 16:9 first-frame image;
- one fixed HappyOyster prompt;
- exact model/surface intended;
- duration/cost bound;
- artifact-capture plan;
- statement that Oyster output is noncanonical.

Create a Jev task with:
- `closed_set=true`
- candidates:
  - `PROCEED`
  - `HOLD_MISSING_EVIDENCE`

Jev must return:
- selected candidate;
- source/evidence refs;
- confidence;
- distribution/reasoning metadata supported by the Jev interface.

If Jev returns `HOLD_MISSING_EVIDENCE`, STOP the Oyster run and fix the missing packet. Jev may not invent a third option.

#### O1 — Luna operates Oyster

Only after `PROCEED`:
- use Adventure first;
- use Directing only for bounded variations of the same world;
- run 5–10 minutes or the owner-set limit;
- capture screenshots/video/session artifacts where available;
- log visual wins, coherence failures, generic/noisy output, traversal observations, and cost/latency if exposed;
- do not implement anything.

#### J1 — result audit

Luna reduces the evidence to exactly:
- `CANDIDATE_A`
- `CANDIDATE_B`
- `CANDIDATE_C`
- `PARK_OYSTER`

Each candidate must contain:
- concise visual/spatial idea;
- evidence artifact refs;
- why it may help Melodia;
- likely existing owner: World Compiler/PCG, Hython/Houdini, material/Niagara, or level composition;
- uncertainty / failure notes.

Create a second Jev task with that exact closed set. Jev selects one candidate only and may not invent implementation details.

Then STOP for owner review.

No Oyster-generated asset or Jev selection becomes canonical game content without owner approval and normal Melodia evidence gates.

### Qwen-Image

Candidate generation only. Never overwrite canonical artwork automatically.

### Muse Voice Transcribe

Critique/audio ingestion only with appropriate recording permission.

### Muse Realtime Avatar

Noncanonical presentation lab only.

### Fugu

Run the exact same B4 packet through Hermes and Fugu. Compare routing, calls, latency, cost and accepted evidence. Do not migrate orchestration from one demo.

## Phase 4 — promotion report

For each tested candidate produce:

```text
candidate:
exact model id:
surface:
benchmarks run:
passes/failures:
current incumbent:
quality advantage:
latency advantage:
cost advantage:
modality advantage:
new risk:
rollback:
recommended status: PROMOTE | SPECIALIST | WATCH | PARK
proposed Hermes lane:
```

If proposing PROMOTE:
- show the smallest possible `Tools/model_router.py` or `delegate.sh` diff;
- do not apply it until the owner approves.

## Final mission success

This bootstrap mission is complete when:
- the current stack is audited;
- owner-required auth actions are explicit;
- at least one new challenger has a real benchmark;
- no current working configuration was lost;
- no secrets entered Git;
- every change has a rollback;
- Hermes remains the single orchestration owner.
