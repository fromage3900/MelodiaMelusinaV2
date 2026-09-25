# Hermes Specialist Model Fleet Setup Plan — 2026-09-23

**Status:** setup/benchmark plan only — no candidate below is promoted to production by this document.  
**Orchestrator authority:** existing Hermes gateway + `Tools/model_router.py`.  
**World-scale mission authority:** `Docs/Production/UNIVERSE_FOUNDRY_CONTRACT.md`.  
**Bounded judgment:** Jev remains decision-only; it does not acquire editor mutation authority.  
**Current-state authority:** `CURRENT_STATE.md` remains the only source for what is actually PRESENT / LIVE / PROVEN.

## 0. Goal

Build a **specialist model fleet** under Hermes without turning Melodia into a pile of overlapping chatbots.

The target shape is:

```text
owner intent
    |
    v
Hermes
  - parses task
  - chooses lane
  - enforces budget / branch / evidence
  - dispatches one specialist
    |
    +--> frontier planner / reviewer
    +--> coding executor
    +--> fast subagent
    +--> multimodal inspector
    +--> local persistent observer
    +--> world-model ideation sidecar
    +--> voice / image / avatar specialist
    |
    v
existing Melodia owner
World Compiler / Hython / TD / UE / Git / Echo
    |
    v
independent evidence
```

**The model is never the authority.** The task contract, repository authority graph, deterministic systems, and evidence gates remain the authority.

## 1. Non-negotiable setup rules

1. **No secrets in Git.** Provider keys live in environment variables, provider credential stores, or `~/.hermes/` only.
2. **No candidate is added to production routing before a canary.**
3. **No surprise paid fallback.** Hermes must know whether a lane is free/local/paid before dispatch.
4. **One editor writer.** A stronger model does not relax the single-Unreal-editor / single-mutation-surface rule.
5. **No self-certification.** The model that writes a patch cannot be the only model/process that accepts it.
6. **Do not replace existing owners.** New models sit behind Hermes; they do not become a second World Compiler, Jev, save system, TD director, or task ledger.
7. **Modality matters.** Text APIs, coding CLIs, world models, image models, and realtime voice/avatar systems are different surfaces. Do not force all of them through `Tools/model_router.py chat`.
8. **Default result is PARK.** A model earns a lane by measurable usefulness, not novelty.

## 2. First-party-verified candidate fleet

The machine-readable candidate registry is:

`specs/orchestration/hermes_specialist_fleet.candidates.v1.json`

### 2.1 Frontier baselines

These are the controls for comparison, not the point of this plan:

| Lane | Candidate | Role |
|---|---|---|
| frontier planner/reviewer | GPT-6 Sol | difficult planning, review, repo/system reasoning |
| frontier planner/implementer | Claude Opus 5.5 | long implementation, codebase work, review |
| frontier challenger | Grok 4.7 | coding/agent comparison where current access exists |

Hermes should benchmark challengers against the **same task packet** rather than comparing vibes.

### 2.2 Meta Muse lane

#### Muse Spark 1.3 — PRIORITY

First-party status: Meta released Muse Spark 1.3 on 2026-09-02 and recommends `muse-spark-1.3` for new work. It supports text/image/video/PDF input, ~1M context, agentic/coding workflows, and max reasoning on eligible access tiers.

Official:
- https://research.meta.ai/blog/introducing-muse-spark-1-3
- https://dev.meta.ai/docs/models
- https://dev.meta.ai/docs/quickstart

Hermes use:
- long-context repo planner;
- multimodal screenshot/video reviewer;
- independent implementation reviewer;
- optional coding worker through Muse Code / Model API.

Access:
- Model API base: `https://api.meta.ai/v1`
- model: `muse-spark-1.3`
- secret: `MODEL_API_KEY`
- OpenAI-compatible and Anthropic-compatible surfaces are documented.

**Windows note:** Muse Code's official installer is macOS/Linux. On the user's Windows workstation, treat **WSL** as the canonical Muse Code host unless Meta documents a native Windows path later.

#### Muse Code 1.2.1 — PRIORITY TOOLING UPDATE

Current changelog adds:
- live `/mcp` inventory;
- `migrate` skill for Claude Code / Codex memory + MCP config;
- image labels that persist through resume/forks;
- `/rewind`;
- voice input;
- session protocol improvements.

Official:
- https://dev.meta.ai/docs/muse-code/changelog

Hermes use:
- specialist coding CLI;
- MCP-aware repo worker;
- resume/fork experiments;
- not a replacement for Hermes orchestration.

#### Muse Glimmer — LOCAL WATCH / CANARY

30B open-weight local agent model, Apache 2.0, intended for always-on local agent workflows and single-consumer-GPU deployment.

Official:
- https://research.meta.ai/blog/introducing-muse-glimmer-open-agentic-model

Hermes use:
- persistent local log/repo observer;
- evidence preprocessor;
- cheap judge/triage lane;
- never an editor writer until independently proven.

#### Muse Voice Transcribe — SPECIALIST

Streaming ASR / diarization / endpointing.

Official:
- https://research.meta.ai/blog/introducing-muse-voice-transcribe

Hermes use:
- class critique transcription;
- spoken art-direction ingestion;
- mocap / voice-session notes -> task packet;
- vocabulary bias for Melodia proper nouns.

#### Muse Realtime Avatar — WATCH

Released 2026-09-23 as a realtime embodiment layer paired with Muse Realtime Voice.

Official:
- https://research.meta.ai/blog/bringing-your-muse-to-life

Hermes use:
- future Melusina character-presentation / interactive prototype lane only;
- **not** a current game animation or runtime authority.

### 2.3 Xiaomi MiMo lane

#### MiMo V2.6 Pro — PRIORITY

First-party release 2026-09-22. Official docs expose OpenAI- and Anthropic-compatible protocols.

Official:
- https://mimo.mi.com/docs/en-US/news/latest/v2-6
- https://mimo.mi.com/models/en-US/mimo-v2.6-pro

Access:
- base: `https://api.xiaomimimo.com/v1`
- model: `mimo-v2.6-pro`
- secret: `MIMO_API_KEY`

**Important:** Xiaomi now publishes an official Hermes Agent integration guide:
- https://mimo.mi.com/docs/en-US/tokenplan/integration/hermes-agent

The official guide configures Hermes with a custom provider and validates using `hermes doctor`.

Hermes use:
- general agent challenger;
- long-horizon planning/coding;
- orchestration-worker benchmark;
- musical/MIDI content experiments only after normal project authority checks.

#### MiMo V2.6 Pro UltraSpeed — PRIORITY LATENCY CANARY

Official model name:
- `mimo-v2.6-pro-ultraspeed`

Hermes use:
- Jev-adjacent *latency comparison*;
- rapid candidate generation;
- fast repo triage;
- never promoted to Jev's authority simply because it is faster.

### 2.4 StepFun lane

#### Step 5 Preview — PRIORITY BENCHMARK

StepFun currently presents Step 5 Preview as its new frontier model for real-world tasks.

Official:
- https://platform.stepfun.ai/

Access:
- base: `https://api.stepfun.ai/v1`
- secret: `STEP_API_KEY`
- OpenAI-compatible examples are published.
- **Do not hard-code a model id from memory.** Hermes must query/currently confirm the exact public model id during setup because the public landing page currently uses a placeholder in its generic example.

Hermes use:
- Universe Foundry plan generation;
- repo/audit tasks;
- cost-quality comparison against frontier planners.

### 2.5 Cognition lane

#### SWE-2 — PRIORITY CODING SPECIALIST

Released 2026-09-10. Cognition positions SWE-2 as its current advanced software-engineering model with multiple reasoning-effort levels and improved verification discipline.

Official:
- https://cognition.com/blog/swe-2

Current first-party access described in the release:
- Devin Desktop / CLI;
- rollout through Devin Web / Fusion.

**Do not pretend this is a generic OpenAI-compatible API unless Cognition documents one.**

Hermes use:
- bounded implementation specialist;
- test-writing / regression-fix lane;
- terminal/repo task canary;
- best evaluated as a CLI worker behind `delegate.sh` or a dedicated adapter, not as a `model_router.py chat` endpoint.

### 2.6 Qwen / QwenCloud lane

#### Qwen3.8-Omni-Flash — PRIORITY MULTIMODAL SPECIALIST

Released 2026-09-18; native text/image/audio/video, up to 1M context, agentic/tool-use focus.

Official:
- https://docs.qwencloud.com/changelog/models
- https://qwen.ai/research/qwen3.8-livetranslate

Model id:
- `qwen3.8-omni-flash`

Hermes use:
- inspect UE gameplay video + screenshots + audio;
- convert multimodal evidence into a bounded engineering/art packet;
- TD/AE/media-review specialist;
- never accept its own observations without target-side verification.

#### HappyOyster 1.0 — PRIORITY WEIRD-LAB

Released 2026-09-18.

Models:
- `happyoyster-1.0-adventure`
- `happyoyster-1.0-directing`
- `happyoyster-1.0-acting`

Official:
- https://docs.qwencloud.com/developer-guides/getting-started/world-model/happyoyster-guide
- https://docs.qwencloud.com/api-reference/world-model/happyoyster-overview
- https://docs.qwencloud.com/api-reference/world-model/happyoyster-integration-flow

Hermes use:
- **Adventure:** spatial/world ideation you can walk through;
- **Directing:** realtime previs and authored world-performance exploration;
- **Acting:** noncanonical character-performance exploration.

Authority rule:
> HappyOyster may propose visual/spatial possibilities. It never writes canonical World Genome, gameplay state, or UE world truth directly.

Recommended Faraway Mother canary:
1. Luna prepares one approved 16:9 first-frame image, one fixed Oyster prompt, a time/cost bound, and the evidence-capture checklist;
2. Luna converts readiness into the closed Jev preflight set `PROCEED | HOLD_MISSING_EVIDENCE`;
3. Jev audits the packet and selects one preflight candidate with source/confidence/distribution;
4. only on `PROCEED`, Luna operates HappyOyster Adventure first and Directing only if needed;
5. Luna captures artifacts and observations without declaring a winner;
6. Luna reduces the useful findings to exactly three authored candidates `CANDIDATE_A | CANDIDATE_B | CANDIDATE_C`, plus `PARK_OYSTER`;
7. Jev audits the evidence and selects **one** member of that closed set with source/confidence/distribution;
8. the owner reviews Jev's bounded decision before any production implementation;
9. Hython / World Compiler / UE may reproduce an owner-approved idea deterministically through existing authority.

Jev is the **bounded audit/decision layer**, not a creative generator. It may not invent a fourth idea, rewrite Oyster output, or mutate implementation state.

#### Qwen-Image-2.1 — SPECIALIST WATCH

Released/open-sourced 2026-09-20; compact unified image generation/editing with transparent-image support.

Official current research listing:
- https://qwen.ai/research/qwen3.8-livetranslate

Hermes use:
- alpha/filigree/decal/material-mask concept variations;
- UI ornament candidate sheets;
- not final authored portfolio art by default;
- keep as a modality-specific image lane, not text-router policy.

### 2.7 Sakana lane

#### Fugu Max / Fugu Ultra v2 — ORCHESTRATION BENCHMARK

Released 2026-09-11; Fugu focuses on orchestrating pools of open/specialist models.

Official:
- https://sakana.ai/fugu-max-release/

Hermes use:
- benchmark **routing strategy**, not replace Hermes by default;
- give Fugu and Hermes the same immutable mission packet;
- compare model selection, calls, latency, cost, retries, evidence quality, and accepted result.

Do not integrate permanently until there is an official programmable access surface appropriate for this repo and it beats the existing Hermes route on a real task.

### 2.8 Inception lane

#### Mercury 2.5 — PRIORITY FAST SUBAGENT

Released 2026-09-08; current first-party docs describe tunable reasoning, parallel tool calls, structured JSON, and OpenAI-compatible access.

Official:
- https://www.inceptionlabs.ai/blog/introducing-mercury-2-5
- https://www.inceptionlabs.ai/models

Hermes use:
- context compaction;
- tool/MCP search;
- log triage;
- manifest summarization;
- fast candidate generation;
- cheap fan-out support calls.

Do **not** assign Mercury the hardest UE architecture task just because it is extremely fast.

## 3. Proposed Hermes role map

This is a **candidate map**, not live policy:

| Hermes lane | First canary | Challenger(s) |
|---|---|---|
| `frontier_plan` | complex read-only plan | GPT-6 Sol / Opus 5.5 / Muse Spark 1.3 / MiMo V2.6 Pro / Step 5 Preview |
| `frontier_review` | independent PR review | Opus 5.5 / GPT-6 Sol / Muse Spark 1.3 |
| `code_executor` | bounded repo patch | SWE-2 / Muse Code / MiMo V2.6 Pro |
| `fast_subagent` | log + manifest triage | Mercury 2.5 / MiMo UltraSpeed |
| `multimodal_review` | gameplay capture -> issue packet | Qwen3.8 Omni Flash / Muse Spark 1.3 |
| `local_observer` | read-only overnight audit | Muse Glimmer |
| `world_ideation` | Faraway first-frame exploration | HappyOyster Adventure / Directing |
| `orchestrator_benchmark` | same mission packet | Hermes vs Fugu Max / Ultra v2 |
| `image_variants` | filigree/alpha candidate sheet | Qwen-Image-2.1 |
| `speech_ingest` | critique audio -> task packet | Muse Voice Transcribe |
| `avatar_lab` | noncanonical character presence | Muse Realtime Avatar |

## 4. Setup waves

### Wave 0 — freeze the current truth

Before installing anything:

```powershell
python Tools/model_router.py list
python Tools/model_router.py pick orchestrator --detail
python Tools/model_router.py pick code --detail
python Tools/model_router.py pick vision --detail
hermes doctor
```

Record:
- Hermes version;
- `Tools/model_router.py` HEAD SHA;
- currently configured provider/model;
- existing CLI versions;
- existing credentials **by presence only** (never values);
- baseline task costs/latencies where available.

Evidence directory:

`Saved/Audit/hermes_model_benchmarks/2026-09-23/`

### Wave 1 — lowest-friction API challengers

Set up one at a time:

1. **MiMo V2.6 Pro / UltraSpeed**
2. **Muse Spark 1.3**
3. **Mercury 2.5**
4. **Step 5 Preview**
5. **Qwen3.8 Omni Flash**

For each provider Hermes must:

1. detect whether the required environment secret exists;
2. if missing, stop and ask the owner to create/connect it;
3. add config in user-local Hermes/provider config, **not Git secrets**;
4. run one `READY` connectivity probe;
5. run benchmark B0 below;
6. write a sanitized benchmark row;
7. restore the previous Hermes default unless the owner explicitly promotes it.

**Important:** Xiaomi's official guide changes Hermes's single custom provider. Hermes must snapshot the current local Hermes config before changing it and restore it after the canary. Do not overwrite a working gateway configuration blindly.

### Wave 2 — coding / local workers

1. **Muse Code 1.2.1 in WSL**
   - install/upgrade;
   - use `migrate` only after reviewing what it will import;
   - inspect `/mcp`;
   - do not duplicate existing MCP servers.

2. **SWE-2 via Devin Desktop/CLI**
   - verify current Devin CLI access;
   - add a dedicated `delegate.sh` worker adapter only if the CLI supports bounded noninteractive execution appropriate for Hermes;
   - otherwise keep manual canary.

3. **Muse Glimmer**
   - check hardware/model format first;
   - keep it local and read-only for first canary;
   - compare against the current local Qwen/other daemon lanes before adding disk-heavy duplicate models.

### Wave 3 — specialist sidecars

1. Qwen3.8 Omni multimodal review
2. HappyOyster Adventure/Directing
3. Qwen-Image-2.1
4. Muse Voice Transcribe
5. Muse Realtime Avatar
6. Fugu orchestration comparison

These are **not** ordinary chat-router endpoints. Each gets a purpose-built adapter only after a useful canary.

## 5. Standard benchmark pack

Every general/coding candidate must see the same immutable packet.

### B0 — connectivity / schema discipline

Prompt requests:
- one exact JSON object;
- no prose;
- fields: `model_seen`, `task_class`, `ready`.

Pass:
- valid JSON;
- no invented tool result;
- latency recorded.

### B1 — read-only repo convergence

Input:
- `AGENTS.md`;
- `CURRENT_STATE.md`;
- one scoped subsystem contract.

Task:
> Identify the smallest correct next action without proposing a parallel implementation.

Pass:
- names existing authority correctly;
- no mutation;
- no duplicate subsystem;
- cites exact repo paths.

### B2 — bounded code patch

Use a disposable branch / small testable utility.

Pass:
- scope discipline;
- tests;
- no unrelated edits;
- independent review passes;
- measured wall time + token/cost data.

### B3 — multimodal evidence

Give the candidate:
- one UE screenshot;
- one short gameplay clip when supported;
- one relevant expected-state contract.

Task:
> Produce a bounded defect/evidence packet, not an implementation fantasy.

Pass:
- observable facts separated from hypotheses;
- maps issue to real owner/path;
- does not claim a fix was executed.

### B4 — Universe Foundry planner

Use:
- Faraway Mother World Genome;
- Foundry contract;
- generated mission DAG.

Task:
> Explain the next unblocked mission node and produce a worker brief.

Pass:
- preserves Hermes/Jev/World Compiler/Hython/TD/UE authority;
- does not bypass the DAG;
- evidence requirements carried through.

### B5 — fast subagent

Feed:
- large build/test log;
- manifest diff;
- one known failing test.

Pass:
- useful structured result;
- low wall time;
- no fabricated root cause;
- cost low enough to justify frequent fan-out.

## 6. Benchmark ledger

Each run records at minimum:

```json
{
  "run_id": "...",
  "timestamp": "...",
  "candidate": "...",
  "provider": "...",
  "surface": "api|cli|local|world-model|image|voice",
  "benchmark": "B0|B1|B2|B3|B4|B5",
  "repo_head": "...",
  "input_tokens": null,
  "output_tokens": null,
  "wall_seconds": 0,
  "time_to_first_token_seconds": null,
  "tool_calls": null,
  "reported_cost_usd": null,
  "accepted": false,
  "failure_class": null,
  "evidence": [],
  "notes": ""
}
```

Never manufacture cost when a provider does not return usage/pricing information. Store `null`.

## 7. Promotion rules

A candidate may enter `Tools/model_router.py` or `delegate.sh` only when:

1. it passes the relevant canary twice;
2. it beats or usefully complements an existing lane on at least one measurable dimension:
   - accepted quality;
   - cost;
   - latency;
   - modality;
   - local/privacy/offline capability;
3. rollback is trivial;
4. auth is external to Git;
5. the model does not require weakening project authority;
6. its real provider/model identifier is verified at setup time;
7. a second process/model independently checks any production patch.

Promotion outcomes:

- **PROMOTE:** earns a named Hermes lane.
- **SPECIALIST:** useful only for one modality/task family.
- **WATCH:** interesting but no current payoff.
- **PARK:** remove/disable; keep research note only.

## 8. Exact first setup order for Hermes

When the owner says **"Hermes, set up the new specialist fleet"**, do this in order:

### Step 1 — read contracts

Read:
- `AGENTS.md`
- `CURRENT_STATE.md`
- `Docs/ORCHESTRATION_HERMES_GATEWAY_2026-08-25.md`
- `Docs/Production/UNIVERSE_FOUNDRY_CONTRACT.md`
- this plan
- `specs/orchestration/hermes_specialist_fleet.candidates.v1.json`

### Step 2 — audit local surfaces

Report, do not mutate yet:
- Hermes version + doctor result;
- WSL availability;
- installed CLIs: Muse, Devin, Claude, Kimi, Codex, OpenCode, Goose/Pi if present;
- current model router policy;
- current environment **key names present/missing only**;
- current GPU/disk constraints relevant to Glimmer.

### Step 3 — ask owner only for missing account actions

Examples:
- generate Meta Model API key;
- generate MiMo API key / Token Plan credentials;
- generate StepFun key;
- generate Inception key;
- QwenCloud credentials;
- Devin access.

Do not ask the owner to paste secrets into Git or a task document.

### Step 4 — configure one provider at a time

Priority:

```text
MiMo V2.6 Pro
-> Muse Spark 1.3
-> Mercury 2.5
-> Step 5 Preview
-> Qwen3.8 Omni Flash
-> SWE-2 / Devin
-> Muse Code
-> Muse Glimmer
-> HappyOyster
-> Fugu
-> image / voice / avatar specialists
```

Why MiMo first: Xiaomi publishes a direct Hermes Agent integration guide, so it is the smallest high-confidence Hermes-specific canary.

### Step 5 — benchmark before routing

Run B0 + the role-appropriate benchmark. Do not modify `Tools/model_router.py` merely because connectivity succeeds.

### Step 6 — propose routing diff

Hermes reports:

```text
candidate:
role:
current incumbent:
measured advantage:
measured disadvantage:
estimated/observed cost:
rollback:
recommendation: PROMOTE | SPECIALIST | WATCH | PARK
```

Owner approves promotion.

### Step 7 — bounded integration

Only then:
- add endpoint/provider support if needed;
- add candidate to the smallest relevant `POLICY` lane;
- add/extend tests;
- record evidence;
- do not reorder unrelated lanes.

## 9. Model-specific canaries

### MiMo Pro

Canary:
> Read the Universe Foundry contract and Faraway Mother genome. Produce the next Hermes worker brief in strict JSON. No repo mutation.

Compare:
- GPT-6 Sol;
- Opus 5.5;
- current Hermes planner.

### MiMo UltraSpeed

Canary:
- 20 small Jev-style closed-set decisions;
- compare latency and candidate-set adherence;
- this does **not** promote it to Jev authority.

### Muse Spark 1.3

Canary:
- one long-context repo + screenshot review;
- then one read-only PR review.

Muse Code canary:
- resume/fork a bounded disposable-branch task;
- inspect `/mcp`;
- verify it did not duplicate or silently change MCP config.

### Step 5 Preview

Canary:
- same B4 Foundry planning task as MiMo/Muse/frontier baselines;
- focus on accepted output per dollar / wall time.

### SWE-2

Canary:
- fix one deliberately scoped failing utility test on a disposable branch;
- require test + patch + explanation;
- independent frontier reviewer judges it.

### Qwen3.8 Omni Flash

Canary:
- 20–60s gameplay capture + screenshot + current UI/visual contract;
- output observations, likely owner, exact reproduction/evidence request;
- no code mutation.

### Mercury 2.5

Canary:
- 5 parallel B5 support calls:
  - summarize test failure;
  - extract relevant paths;
  - compact long agent transcript;
  - structure manifest diff;
  - rank tool-search candidates.
- compare aggregate latency/cost with current cheap lane.

### Muse Glimmer

Canary:
- overnight/read-only agent:
  - inspect latest logs;
  - group failures;
  - prepare morning brief;
  - no writes except its own audit output.

### HappyOyster Adventure / Directing

Canary:

**J0 — Jev preflight audit**
- Luna assembles first-frame, fixed prompt, duration/cost bound, capture checklist, and explicit authority note;
- authored closed set: `PROCEED | HOLD_MISSING_EVIDENCE`;
- Jev selects one candidate and returns source/confidence/distribution;
- `HOLD_MISSING_EVIDENCE` stops the run until Luna fixes the packet.

**O1 — Oyster exploration**
- on `PROCEED`, Luna runs Adventure first;
- 5–10 minutes bounded exploration/directing;
- export screenshots/video/session artifacts where available;
- record failures/noise as evidence;
- Luna does not promote or implement anything.

**J1 — Jev result audit**
- Luna extracts exactly three implementation-independent ideas from the evidence;
- closed set: `CANDIDATE_A | CANDIDATE_B | CANDIDATE_C | PARK_OYSTER`;
- each candidate must include evidence refs, visual/spatial claim, likely existing Melodia owner, and explicit uncertainty;
- Jev selects exactly one and returns source/confidence/distribution;
- Jev may not invent a candidate or implementation.

**Owner gate**
- the owner reviews the selected candidate;
- no generated asset is automatically imported into UE;
- implementation, if approved, returns to World Compiler / Hython / PCG / material / level-composition owners.

### Fugu Max / Ultra v2

Canary:
- give Fugu the exact B4 packet used by Hermes;
- compare orchestration trace;
- no architectural adoption from one demo.

### Qwen-Image-2.1

Canary:
- 8 transparent ornamental/filigree variations constrained by the current Figma token palette;
- human selects candidates;
- never overwrite canonical design assets automatically.

### Muse Voice Transcribe

Canary:
- one 5–10 minute critique/class recording with consent;
- bias vocabulary for Melodia terms;
- output transcript + action-item candidates;
- Hermes converts only owner-approved items into tasks.

### Muse Realtime Avatar

Canary:
- optional noncanonical Melusina presentation test from approved reference media;
- no gameplay/animation pipeline replacement.

## 9b. Jev audit pattern for generative sidecars

Use this pattern whenever a specialist generates open-ended creative output (world models, image models, avatar/previs systems):

```text
Luna/Hermes prepares bounded packet
        |
        v
Jev preflight audit
PROCEED | HOLD_MISSING_EVIDENCE
        |
        v
specialist generates/explores
        |
        v
Luna/Hermes captures evidence
and authors a closed candidate set
        |
        v
Jev result audit / bounded selection
        |
        v
owner approval
        |
        v
existing deterministic Melodia owner
```

The producing specialist never grades itself. Jev never invents candidates. The owner remains the final promotion/implementation gate.

## 10. Changes explicitly forbidden during setup

Hermes must not:

- rewrite `Tools/model_router.py` into a new orchestration framework;
- replace Jev;
- add twelve always-running daemons;
- install local giant weights without disk/VRAM review;
- add a paid fallback without owner approval;
- commit credentials;
- let a world/image/avatar model write canonical game state;
- install TouchDesigner tooling in the game repo;
- claim a provider works because docs say it should;
- update `CURRENT_STATE.md` until a real canary has run.

## 11. Definition of success

The setup project is successful when:

- at least one **new general challenger** is benchmarked;
- one **fast subagent** is benchmarked;
- one **coding specialist** is benchmarked;
- one **multimodal specialist** is benchmarked;
- HappyOyster completes one bounded World Foundry ideation experiment;
- every promoted lane has evidence, cost/latency notes, and a rollback;
- Hermes still has one clear routing/authority graph;
- the project gained capability without gaining chaos.
