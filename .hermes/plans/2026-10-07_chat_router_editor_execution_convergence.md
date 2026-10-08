# PLAN — Chat-to-Hermes router execution convergence (2026-10-07)

**Status:** APPROVED FOR PLANNING ONLY; implementation and live-editor proof not yet run by this document.
**Owner objective:** Plan in conversational ChatGPT, delegate bounded Melodia missions to cost-appropriate model workers on the Windows workstation/laptop, inspect real evidence, and approve editor or Git operations without manually re-briefing each model.
**Repository:** fromage3900/MelodiaMelusinaV2, canonical landing branch main.
**This document is an implementation addendum**, not a competing architecture, not permission for autonomous mutation, and not evidence of local-machine connectivity.

## 0. Authority, scope, and invariants

Read these before implementation:
- [Hermes orchestrator authority](2026-09-26_hermes-orchestrator-infra-plan.md): Hermes owns mission state/ledger and execution; Jev may assist bounded routing; independent verifier checks artifacts.
- [Model routing canon](../../Docs/Production/MODEL_ROUTING_CANON.md), [tier registry](../../specs/orchestration/model_tiers.v1.json), and [routing implementation](../../Tools/model_router.py): one live routing authority, no parallel model router.
- [Hermes gateway](../../Docs/ORCHESTRATION_HERMES_GATEWAY_2026-08-25.md): the existing CLI/Discord transport, not a second scheduler.
- [Task-packet schema](../../Tools/agent_router/task_packet.schema.json), [editor lease](../../Tools/agent_lease.py), [MCP policy](../../Tools/mcp_policy.py), and [Melodia MCP server](../../deploy/melodia_mcp_server.py).
- [Agent agreement](../../_AGENT_WORKING_AGREEMENT.md), [AGENTS](../../AGENTS.md), [CLAUDE](../../CLAUDE.md), and [current state](../../CURRENT_STATE.md) for active runtime, Git/P4, protected paths, and user instructions.

**Invariant:** one canonical writer to a live Unreal graph; one editor lease holder for any mutating operation; no background git branch switches, merge/rebase/reset/push, P4 submit, publishing, or destructive asset change without explicit owner authorization. No worker certifies its own result. No unreviewed fallback to a paid model. No secrets in Git, task packets, chat transcripts, or audit bundles. No direct exposure of local Monolith/Claireon ports to the internet.

**Scope boundary:** regular Chat has a GitHub connector but does **not** inherently see or control the user's local Windows desktop or the G: drive. A working remote control path requires a separately verified, approved local agent/plugin bridge. Do not equate a GitHub task packet with execution on the user's computer. On-phone support is a distinct later compatibility/security check.

## 1. Grounded repository baseline (GitHub main inspected 2026-10-07)

| Surface | Checked-in state | Implication |
|---|---|---|
| Tools/model_router.py | Supports pick, chat, tier, tasks, audit, route, route-batch; packet validation/decisions, provider fallbacks and ledger | Reuse it; **route returns a decision** with a dispatch flag, not proof that a tool-using worker ran |
| Tools/agent_router/task_packet.schema.json | Defines id, goal, done_when, inputs, mutation_paths, surfaces, mutation_scope, task_class, artifacts, budgets and turn limits | Preserve schema; extend only for demonstrated execution needs |
| Tools/test_agent_router.py | Offline tests for determinism, escalation, fail-closed routing, local-only budget and lease behavior | Existing regression base, **not a current live pass receipt** |
| Tools/agent_lease.py | Single-writer editor lease at Saved/Agents/editor.lease with expiry, STOP-file and modal refusal | Enforce at the actual mutating call boundary; a local file lease is **not** a distributed lock between unrelated machines |
| Tools/lane_dispatcher.py | Read-only plan/report over CURRENT_STATE.md, does not execute queue items | Do not confuse this with an execution dispatcher |
| deploy/agent_bridge_mcp.py | Routes specialized intents and exposes UE command preparation; ue_editor_command can return status=prepared | Prepared is **not executed**; raw UE calls stay policy-gated/denied unless a separately authorized path exists |
| deploy/melodia_mcp_server.py | MCP stdio gateway, read-only offline behavior, policy-checked writes and Monolith fallback when live | Extend/use typed surface rather than an arbitrary shell/UE command escape hatch |
| Docs/MELODIA_MCP_TOOL_REFERENCE.md | Documents loopback Monolith 127.0.0.1:9316 and Claireon 127.0.0.1:60162, plus MCP transport | Validate live health on user's machine; never assume endpoints are currently running |
| .codex/config.toml and .jcode/mcp.json | Some registration examples contain C:/EnvironmentPortfolio/BS_GodFile absolute paths | Verify canonical G: project location and remove path brittleness in a scoped, separately approved change |
| .hermes/plans/2026-09-26_hermes-orchestrator-infra-plan.md | H0/H1/H2/H3 topology and intended packaged-cook canary already specified | Continue the plan; do **not** start over or rename authority |

**Verification limitation:** these findings are code/document inspection on remote GitHub main only. No Hermes daemon, model API, Monolith/Claireon, Windows filesystem, UE5.8 session, PIE, cook, or local credentials have been contacted by this plan-authoring pass. The older plan's historical H0/H1 statuses may now be stale; recheck locally before declaring a phase complete.

## 2. Proposed end-to-end mission lifecycle

Design intent (the missing execution seam is deliberately bounded):

```text
Owner (ChatGPT conversation / Windows Desktop or approved remote gateway)
    -> explicit mission request and approval scope
    -> existing Hermes kanban + Task Packet (one stable ID)
    -> Tools/model_router.py route <packet.json> --json
    -> validate decision and capabilities; fail closed on classical-fallback
    -> Hermes claims card / assigns one worker in an isolated execution workspace
    -> worker uses allowed filesystem, CLI, MCP tools inside packet fences
    -> editor mutations only through authorized policy + editor lease
    -> worker produces Saved/Audit/<id>/ evidence + status receipt
    -> independent verifier OPENS actual artifacts/logs/frames
    -> owner reviews result; approves promotion or requests repair
```

**Required states:** queued -> validated -> routed -> claimed -> running -> evidence_ready -> verifying -> accepted | rejected | blocked | cancelled.

A routing decision with dispatch=true only authorizes the **next attempt** after the runner verifies prerequisites. It is not the state running or accepted. Every transition records task ID, worker/model/provider, start/end timestamps, attempt number, workspace/ref, permitted tool surface, status/error, artifact paths and budget consumed. Every task is idempotent by ID; restart must not start a duplicate concurrent worker. Timeouts, crash recovery, stale claim cleanup and explicit STOP/cancel require tests.

**Execution contract:** the selected model may lack tools. An LLM text completion from model_router.py chat must never be represented as a shell, asset change, test run or editor action. Only a named worker harness with explicit tool capabilities can execute. Serialize editor work, but run unrelated read-only/log/doc tasks in parallel workspaces.

## 3. Prioritized phases with acceptance evidence

### P0 — Audit what is *actually executable* (first; read-only)

1. On the workstation, record git branch/worktree/P4 status and the active UE process before any mutation. Do not switch the editor's checkout.
2. Run existing offline tests and router audits; do not suppress failures:
   ```powershell
   python Tools/model_router.py audit --json
   python Tools/test_agent_router.py
   python Tools/test_model_tiers.py
   python Tools/agent_lease.py status
   python Tools/model_router.py route Tools/agent_router/fixtures/doc_link_repair.json --json
   ```
3. Check configured provider IDs against live accessible catalogs **using an authenticated, opt-in probe**; confirm keys exist by boolean presence only, not contents. Test the least-cost model before promoting any provider. Preserve local-only T4 as hard zero-spend.
4. Inspect Hermes's actual CLI gateway, installed plugins, configured MCP clients, and the Claireon proxy's health. Verify editor-backed read-only tools once with UE open, then once after an editor restart if safe. Treat AWS/cloud/model state noted on 2026-09-26 as historical, not a live claim.
5. Record failed/missing prerequisites and owner actions in Saved/Audit/router_convergence_p0/ including tool versions, sanitized output and no credentials.

**PASS:** reproducible command outputs, recorded route/chat consistency, every required endpoint marked live/dead/untested and a minimal allowed worker identified. **FAIL:** missing schema, unreachable necessary endpoint, stale credentials, misleading success receipt, or unsafe editor state. Never fix this phase by replacing the router.

### P1 — Route -> real worker execution (first implementation seam)

1. Implement the smallest **Hermes-side adapter** consuming an existing validated Task Packet and routing decision; call the existing supported worker/CLI transport rather than spawning an uncontrolled generic subprocess from model output.
2. Require per-packet explicit allowlists for readable/writable paths, model cost cap, turn/time cap, allowed tools, and required artifact. Reject unknown surface, missing entrypoint, invalid model ID, budget overrun, editor-write request without lease, or owner-only Git/P4 request.
3. Return a typed execution receipt with fields task_id, attempt, route_snapshot, worker, model, provider, state, start/end, exit, errors, artifacts and verification_pending. Never log credentials or raw environment.
4. Implement STOP/cancel, concurrency/claim, crash/restart idempotency and stale-lease behavior. Keep each worker in its designated worktree or staging folder; never commit or checkout against an open editor.
5. Unit-test routes with mocks, disconnected models and a deliberately tool-less LLM. Show a true command/artifact invocation, not only a fluent answer.

**PASS:** a low-risk offline packet produces a real file under Saved/Audit/<id>/, a matching execution receipt, and a separate verifier can read it. Model unavailable -> blocked/failed, **not** fake success, unauthorized paid fallback or endless retries.

### P2 — Expose *scoped* read-only missions through the existing MCP/gateway

1. Reuse deploy/melodia_mcp_server.py and its mcp_policy gate where applicable; do not install a second world/editor controller.
2. Give a client the minimal named operations: submit approved packet, query packet status, read sanitized artifacts, request cancellation. Scope/approve registration and transport through the existing Hermes gateway. Workstation-first; **do not presume regular Chat mobile can access local MCP**.
3. Verify caller identity, per-operation authorization, tool input schema and output size limits; prevent arbitrary command execution and traversal outside permitted paths. Treat incoming chat, Discord, tool results and model text as untrusted.
4. Keep localhost editor/MCP ports loopback-only. If remote access is desired, use an authenticated narrow bridge, explicit allowlists and private channel; do not expose Monolith, Claireon or the full MCP process publicly.
5. Prove a chat-originated status/read-only request reaches Hermes and returns evidence. If local ChatGPT plugin registration is unsupported in the current desktop install/account, keep the existing CLI/Discord gateway as the delivery path.

**PASS:** from a separately verified client, submit -> queue -> run -> fetch artifact succeeds with identity/permission checks; denied command/unknown tool cannot cross the boundary.

### P3 — Read-only Unreal canary (first embodied/editor step)

Target: **inspect Melusina's currently active runtime animation/retarget chain**, not rewrite it. Cross-reference CURRENT_STATE.md and the October 5 runtime canon; avoid stale one-off retarget folders.

1. A single Hermes worker verifies current UE5.8 project/editor and queries only read-only Claireon/Monolith/approved typed tools.
2. Collect actual asset paths, loaded anim blueprint/skeleton, relevant state-machine/transitions, retarget chain, editor/log observations and optional owner-approved screenshots.
3. Return a compact evidence bundle Saved/Audit/melusina_animation_readonly_<id>/ with manifest.json, observations.md, log excerpts and screenshots only if actually captured.
4. A different verifier inspects source evidence, marks verified.json pass/fail/uncertain and explicitly calls out anything requiring PIE.
5. No editor changes, no PIE, no save/reimport, no forced map load, and no self-certification during this canary.

**PASS:** owner can distinguish an observed runtime fact from a conjecture, trace each finding to a real artifact and request a subsequent scoped repair. If the editor is not available, report blocked and fall back to an offline-only repo inspection clearly labeled as such.

### P4 — Gated editor mutation and independent proof (later, opt-in)

The owner must settle D1 from the September 26 plan **before** this phase. Safe recommended default: Claireon read-only; Monolith typed mutation only with editor lease, explicit approval and audit trail.

- Acquire lease with holder/session, honor STOP/modal, check it again at the tool boundary, and release in finally. The lease does not replace a single shared editor coordinator.
- Back up/identify exact asset; declare expected diff and rollback path. Never use generic Python console injection as the default editor-write interface.
- Test one reversible, non-critical scoped asset change only with owner approval; save it, re-open the asset, and independently verify visually/with a gate. Handle UAsset/LFS/P4 permissions and dirty packages.
- Keep Git/P4 landing as a *separate explicit owner approval* even when the worker successfully authored files. Do not bundle branch switches, merges or submissions into this phase.

**PASS:** observed before/after asset evidence, reproducible verification, no second writer and a reliable restoration path. Any ambiguous editor state -> STOP.

### P5 — Remote/mobile convenience (optional after P0-P3)

Owner wants to remain in conversational Chat while planning missions. Verify current ChatGPT Desktop local-plugin eligibility separately from iPhone regular-Chat capabilities and Work/Codex; **do not promise unrestricted PC control**. If direct connector access is absent, use the existing authenticated Hermes/Discord gateway to deliver task packets and status, with human approval for sensitive actions. Remote capability should expose mission-level verbs, never full desktop control by accident.

**PASS:** approved remote request queues a bounded *read-only* task, result can be reviewed on phone, and revoking access stops new requests. No remote public editor port.

## 4. Execution order, owners, and spend discipline

| Sequence | Executor | Verifier | Gate |
|---|---|---|---|
| P0 audit | Local CLI / Hermes operator, no mutation | Owner reviews sanitized receipts | Endpoints and policy reality known |
| P1 worker handoff | Scoped T2 executor implementing pre-decided contract | Different T1 reviewer + offline tests | Real artifact and correct fail states |
| P2 client interface | T2 MCP worker with narrow tool surface | Independent security/policy test | Chat-origin request no longer implies arbitrary shell |
| P3 Melusina inspection | Cheapest capable read-only editor agent | Independent model/human checks captured artifacts | Runtime observation substantiated |
| P4 optional mutation | One lease-holding editor worker | Fresh visual/gate verification; owner approves Git/P4 | Safe reversible UE proof |
| P5 optional remote | Gateway maintainer | Owner tests revoke/deny | Mobile status/mission submission with scoped auth |

Model selection stays in Tools/model_router.py. Keep T4_LOCAL / free production tasks from silently falling back to paid providers. T0 frontier is reserved for an architecture/schema/convergence decision, not log triage or repeated tool polling. Preserve a human-visible per-task dollar ceiling; absent permission means fail closed. Do not use a self-reported agent answer as evidence.

## 5. Explicit blocker/risk ledger

- **Gap A — selection != execution:** route's dispatch=true is a decision, not a worker run. P1 closes it.
- **Gap B — intent != UE command:** deploy/agent_bridge_mcp.py ue_editor_command can return prepared and its unauthorized tool path is policy-denied. P2/P3 must use supported typed calls with receipts.
- **Gap C — host reachability:** GitHub connector and this mobile Chat do not make a local process addressable. P2/P5 verify a supported bridge.
- **Gap D — path/checkout skew:** some checked-in agent configs reference C:/EnvironmentPortfolio/BS_GodFile while the live authoritative project may be on G:. Resolve under the actual one-editor/P4 discipline before running workers.
- **Gap E — model registry drift:** audit --probe-models may reveal IDs/provider auth discrepancies; do not edit model policy or assume Bedrock credit remains active without receipts.
- **Gap F — concurrency:** editor.lease is a local file coordination aid, not network-wide enforcement; serialize at the one true editor worker.
- **Gap G — stale runbooks:** September 26 H0/H1 notes were snapshots. Revalidate state rather than checking boxes because the code now exists.
- **Gap H — secrets:** pre-existing local gateway/token files need a separate credential hygiene check; never collect values in the plan, log or Git.

## 6. Definition of done (for this plan)

The architecture is considered operational only when all of these are evidenced:

- [ ] Router audit and agent-router tests execute successfully on the actual PC (or failures recorded and fixed).
- [ ] Task packet routes to a genuine executable worker with no model-policy or cost drift.
- [ ] One offline canary creates an actual openable artifact and non-self-issued verification.
- [ ] Hermes can report queued/running/blocked/complete with durable idempotent receipts.
- [ ] Read-only UE inspection captures facts from the live project without collateral mutation.
- [ ] Unauthorized write, missing editor lease, unavailable provider, and STOP all fail closed.
- [ ] Git/P4 remain explicit owner approval actions; there is no background branch switching against the editor.
- [ ] Chat/desktop/phone client support is reported **as tested**, not inferred from product marketing or a plan.
- [ ] Owner can submit a bounded mission, inspect proof, and explicitly approve any promotion.

## 7. Immediate handoff / first bounded session

**Do next:** P0 only. Have the local owner or Hermes operator run the five listed read-only commands from the canonical live project, capture sanitized results under Saved/Audit/router_convergence_p0/, and report which of (a) routing, (b) actual worker invocation, (c) Claireon/MCP transport, and (d) editor-read access are verified. Do not alter the running UE session. Only after that, implement the smallest P1 adapter with a single offline evidence-producing packet.

**Do not do yet:** new router, new persistent scheduler, default-open network tunnel, generic UE exec surface, autonomous asset rewrites, remote PC control claims, or broad branch cleanup.

**Commit scope of this authoring pass:** this Markdown plan alone on main. No code, config, model policy, credentials, Git/P4 state outside GitHub main, or local editor files are modified.
