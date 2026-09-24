# Grok Fleet — Sakana Fugu Setup + Glassgarden Canary — 2026-09-24

You are the Grok setup fleet for Melodia Melusina.

Goal: make Sakana Fugu available as an **isolated orchestration benchmark** on the owner's Windows workstation, prove connectivity, and leave it ready for the Reef That Looks Back / Glassgarden comparison. Do not promote Fugu into permanent Melodia routing.

## Authority

Read first:

- `AGENTS.md`
- `CURRENT_STATE.md`
- `Docs/Plans/HERMES_SPECIALIST_MODEL_FLEET_SETUP_2026-09-23.md`
- `specs/orchestration/hermes_specialist_fleet.candidates.v1.json`
- `Docs/Production/UNIVERSE_FOUNDRY_CONTRACT.md`
- `Docs/Houdini/LATE_MONOLITH_VISUAL_ESCALATION_BIBLE_2026-08-29.md`
- `Docs/Art/DAILY_CANON_AUDIT_2026-08-29.md`

Project authority remains:

owner -> Hermes -> bounded specialist -> existing deterministic owner -> independent evidence.

Jev remains bounded decision/audit only.

Fugu is a benchmark candidate, not a new authority.

## Fleet split

Use at most three Grok workers and keep mutation surfaces serialized.

### Grok A — setup operator

Owns all local Fugu/Codex configuration writes.

### Grok B — independent verifier

Read-only. Verifies official docs, config diff, secret hygiene, and canary evidence. It must not edit the same config files as Grok A.

### Grok C — benchmark runner

Runs the Fugu canary only after A reports setup complete and B reports the config safe. No production repo or Unreal mutation.

Never let two workers write `~/.codex/config.toml` or related Fugu profile files concurrently.

## Phase 0 — local truth

From the actual `BS_GodFile` Git root:

1. report branch, HEAD, and `git status --short --branch`;
2. do not reset, clean, stash, rebase, or switch an intentional dirty worktree;
3. report OS/shell, WSL availability, Codex CLI version, Python version, and whether the OpenAI Python package is already available;
4. report only whether `SAKANA_API_KEY` is present — NEVER print its value;
5. inspect current user-local Codex config paths before writing anything.

Do not touch Unreal.

## Phase 1 — verify first-party Fugu surface

Use the current Sakana first-party pages as authority:

- `https://console.sakana.ai/get-started`
- `https://console.sakana.ai/models`
- `https://sakana.ai/fugu-max-release/`

Current expected contract to verify, not blindly assume:

- API base `https://api.sakana.ai/v1`;
- secret env `SAKANA_API_KEY`;
- OpenAI-compatible Responses / Chat Completions / Models APIs;
- Anthropic-compatible Messages API;
- `fugu-max` current Max alias;
- `fugu-ultra` current Ultra alias;
- official Codex support;
- native Windows should use the documented manual setup or direct API rather than executing the Ubuntu/macOS one-line installer in PowerShell.

If first-party docs now differ, follow the current docs and report the drift.

## Phase 2 — missing-key behavior

If `SAKANA_API_KEY` is missing:

- do not invent, scrape, or request the key value in chat;
- do not store a placeholder secret in Git;
- report: `OWNER_ACTION_REQUIRED: create Sakana API key and expose it locally as SAKANA_API_KEY`;
- you may prepare non-secret profile/config structure only if doing so cannot overwrite existing settings;
- do not claim connectivity.

If the key exists, continue.

## Phase 3 — direct API connectivity canary

Before touching permanent model routing:

1. query the documented Models API and record the exposed Fugu model ids;
2. run one `fugu-max` B0 probe through the official OpenAI-compatible surface;
3. request exactly one JSON object:

```json
{
  "model_seen": "string",
  "task_class": "orchestration_connectivity",
  "ready": true
}
```

Pass only if:

- the request succeeds;
- output parses as JSON;
- the requested/current Fugu model is confirmable;
- wall time is recorded;
- usage/cost is recorded only if actually returned;
- no tool result is invented.

Do not use Fugu Ultra yet.

## Phase 4 — isolated Codex profile

Set up the **official Sakana Fugu Codex profile** without replacing the owner's existing Codex defaults.

Native Windows:

- use Sakana's documented manual Codex setup;
- do not run the Ubuntu/macOS curl-to-bash installer from PowerShell.

If intentionally operating inside WSL and the owner wants the WSL Codex surface, the official installer may be used there after verifying it will not replace unrelated configuration.

Before edits:

- make timestamped local backups of existing `~/.codex/config.toml`, `~/.codex/fugu.config.toml`, and `~/.codex/fugu.json` when present;
- backups stay outside Git;
- never copy credentials into the backup report.

Target:

- isolated profile name: `fugu`;
- default model inside that profile: `fugu-max`;
- reasoning effort: `high`;
- provider: Sakana API;
- provider base: `https://api.sakana.ai/v1`;
- credential reference: `SAKANA_API_KEY`;
- preserve Sakana's documented stream-retry / idle-timeout settings when supported by the installed Codex version.

Inspect `codex --help` / current profile behavior before launching. Use the official `fugu` profile route only if the installed CLI supports it.

Do not change normal Codex default model/provider.

## Phase 5 — profile verification

Prove:

- normal Codex config/default still resolves as it did before;
- the isolated `fugu` profile resolves to Sakana;
- `fugu-max` is selectable;
- no secret was written to repo or config as a literal when an environment reference is supported;
- no unrelated MCP/app configuration was changed.

Grok B reviews the diff and returns:

`CONFIG_SAFE | CONFIG_NEEDS_FIX`

If `CONFIG_NEEDS_FIX`, A fixes only the cited issue and B rechecks.

## Phase 6 — Glassgarden orchestration canary

Run only if there is already an owner/Jev-selected HappyOyster Glassgarden evidence packet.

If no selected Oyster evidence exists, report `FUGU_READY_WAITING_FOR_OYSTER` and STOP here.

If evidence exists, freeze it as immutable input and give **the same packet** to Fugu and later Hermes.

Fugu task:

> You are being benchmarked as a production orchestrator, not an ideation model. Using the selected HappyOyster evidence for The Reef That Looks Back / Glassgarden Shoals, produce the smallest deterministic production DAG capable of recreating one portfolio-quality Unreal hero shot using existing Melodia owners. Do not redesign the concept. Do not mutate the repo or Unreal. There is no literal giant eye mesh. The eye must emerge from reef ecology, pigmentation, water depth, and composition.

Require exactly:

```text
FUGU_GLASSGARDEN_DAG

target:
selected_oyster_evidence:

nodes:
  - id
  - purpose
  - existing_owner
  - inputs
  - outputs
  - dependencies
  - mutation_surface
  - rollback
  - evidence_required

first_visible_proof:
estimated_risk:
new_architecture_proposed: false
explicitly_not_building:
final_status: READY_FOR_COMPARISON | NEEDS_EVIDENCE | PARK
```

Existing owners may include only real project surfaces such as:

- Houdini/Hython;
- World Compiler/PCG;
- current materials/MPC presentation chain;
- Niagara;
- Oceanology;
- level composition;
- render/capture.

Automatic failure conditions:

- second World Compiler;
- second MPC writer;
- giant literal eye/eyeball system;
- new Monolith framework;
- unsupported asset/path invention presented as fact;
- production mutation during benchmark;
- Fugu grading/promoting itself.

Capture exact output, model alias/resolved id if available, wall time, usage/cost if actually reported, retries, and failures.

## Phase 7 — stop condition

Do NOT:

- edit `Tools/model_router.py`;
- make Fugu the Hermes default;
- change permanent provider routing;
- launch Fugu Ultra simply because Max works;
- touch UE/Houdini production content;
- implement the Glassgarden DAG;
- commit secrets;
- update `CURRENT_STATE.md` from connectivity alone.

## Final report

Return:

```text
FUGU SETUP
git root:
branch/head:
SAKANA_API_KEY present: yes|no
models API:
fugu-max connectivity:
resolved model id:
wall time:
usage/cost if reported:
Codex fugu profile:
normal Codex default preserved:
Grok B config verdict:
Glassgarden canary: NOT_RUN | READY_WAITING_FOR_OYSTER | COMPLETE
evidence paths:
owner action required:
```

Then STOP.
