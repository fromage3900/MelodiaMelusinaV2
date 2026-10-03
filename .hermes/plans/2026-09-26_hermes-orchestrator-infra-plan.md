# PLAN — Hermes orchestrator: Jev routes, Hermes runs, Bedrock powers, Claude verifies (2026-09-26)

Owner ask: "route these big tasks to a Hermes agent … use my Hermes agent in Claireon as well as AWS
Bedrock … a Jev orchestrator system that delegates tasks wisely." Builds on
`Docs/ORCHESTRATION_HERMES_GATEWAY_2026-08-25.md` (Hermes owns plan/ledger/delivery; CLIs are hands) and
`Docs/Plans/HERMES_SPECIALIST_MODEL_FLEET_SETUP_2026-09-23.md` (lane map). This plan is the wiring, not a
new model survey.

## Jev ruling (live `jev-1.13.0`, 2026-09-26)
| Question | Ruling | Conf |
|---|---|---|
| Topology | **Hermes runtime · Jev routes · Claude verifies** | 0.96 |
| First canary | **Packaged cook + launch + log triage** | 0.90 |
| Bedrock role | Tiered primary for Hermes workers | 0.60 |
| Git authority | Worktree patch only; owner approves each op (already law) | 0.55 |
| Editor access | Hermes gets Claireon read-only; mutation only via a Monolith **editor lease** | **0.40 — owner decides (D1)** |

## Verified starting point (on disk, 2026-09-26)
- Hermes installed (`%LOCALAPPDATA%/hermes`): kanban + dispatch DB, sessions, subagents (cap 50), gateway
  (Discord), default model `nous / z-ai/glm-5.3-flash`, `fallback_providers: []`.
- **Bedrock already authenticated** (2026-09-05): bearer token in Hermes `.env`, `bedrock.region us-east-1`,
  `bedrock.discovery.enabled: false`.
- Hermes MCP client speaks **HTTP + bearer** (`tools/mcp_tool_transport.py`). Its `mcp_servers` has only
  `melodia` (disabled). No Claireon, no Monolith.
- Claireon: HTTP MCP at `127.0.0.1:60162` (stable per checkout, `Saved/Claireon/MCPServer.json`); optional
  always-on **proxy** (`-EnableMCPProxy` / `Scripts/Utilities/Start-MCPProxy.ps1`) keeps that port alive across
  editor restarts — the property long Hermes jobs need. Claireon's panel launch button only starts `claude`;
  "Hermes in Claireon" = Hermes as a Claireon MCP client (no plugin change needed).
- Jev: `typesafe_sdk.TypeSafeClient().system_one(state, questions{criteria})` in the Hermes venv.

## Status 2026-10-02 — H1 COMPLETE, all four mechanisms exist

H1 was "not started" when this section was first written. All four mechanisms are now
built and each has an offline test that runs with no network, no editor and no API key:

| # | Mechanism | Where | Evidence |
|---|---|---|---|
| 1 | Task Packet | `Tools/agent_router/task_packet.schema.json` | `Tools/test_agent_router.py` |
| 2 | Router | `Tools/model_router.py route` / `route-batch` | 35 tests; `route-batch` byte-identical across runs |
| 3 | Editor lease | `Tools/agent_lease.py` | second holder refused, STOP-file + MODAL_OPEN honoured, expiry reclaimed |
| 4 | **Verify gate** | `Tools/verify_gate.py` | `Tools/test_verify_gate.py`, 24 tests |

Mechanism 4 was the missing one and it was the dangerous gap: with packets, a router and
a lease, a loop could already be dispatched with **nothing able to stop a worker closing
its own card**. `verify_gate.py` closes that. `record` refuses a receipt with no artifact,
an artifact that is not on disk, or a verifier equal to the producer; `close` refuses a
missing/failing/self-certified receipt; `sweep` is the unattended pre-turn guard.

**`uncertain` is a first-class outcome and does not count as done.** That is deliberate:
if "I could not confirm this" were unrepresentable, agents would write `pass` to move the
loop. Finding this was worth the test — the first implementation *did* pass an `uncertain`
receipt through as success.

Two real bugs surfaced during H1 and are fixed at source, not by loosening a check: the
STOP-sentinel prefix test matched no filename, and an explicit `verify_kind` was being
overridden by inference.

### H2 is now unblocked; H3 widens from here

H2 (packaged cook + launch + log triage canary) is the next gate and has no unmet
dependency. The loop H2 exercises end to end is:

```
lane_dispatcher.py plan          # CURRENT_STATE.md section 4 -> lane assignments
model_router.py route <packet>   # packet -> tier/model/needs_editor/verify_kind
  -> worker lane executes
  -> verify_gate.py record       # an INDEPENDENT verifier opens the artifact
  -> verify_gate.py sweep        # pre-turn guard; a failed card stops the loop
  -> verify_gate.py close        # only a real receipt closes it
```

### What is still NOT built, and must not be assumed

- **H3 widening** (nightly read-only audits, bulk Blender `-b`, regression-harness repair).
- **Honcho/Discord reachability.** Honcho shares MEMORY across machines and Discord is the
  control channel; both are configured on the desktop per
  `Docs/ORCHESTRATION_HONCHO_DISCORD_SYNC_2026-10-01.md`, but Discord is still blocked on
  **two owner-only dev-portal steps** (turn OFF "Requires OAuth2 Code Grant", then re-invite
  the bot). Until the bot is in a guild it cannot be mentioned, so a phone-driven recursive
  loop is not yet reachable. Memory sharing does not depend on that.
- **Cross-machine STATE.** Files travel by git, memory by Honcho, but nothing yet told a
  laptop agent what the desktop agent had left it. That is now
  `Tools/workstation_status.py` — see the two-workstation contract.

## Status 2026-09-26 (end of session) — H0 in progress, owner-side
- **Bedrock key is dead:** runtime Converse → 403 "Please make sure your API Key is valid"; catalog list
  403; Mantle `/v1/models` 401. Owner: new API key (us-east-1) + Model access for the Qwen/Flash-class
  and Claude-class models → save into Hermes `.env`.
- **Hermes config edits are owner-applied** (Claude Code's auto-mode classifier blocks agent-config writes):
  `delegation` → `model: muse-glimmer:30b`, `provider: custom`, `base_url: http://127.0.0.1:11434/v1`,
  `api_key: ollama` (alternates on disk: `heretic-27b:latest`, `qwen3-coder:30b`, `qwen3:8b`,
  `granite4.2:3b/8b`); `mcp_servers.claireon: {url: http://127.0.0.1:60162/mcp}`; `melodia.enabled: true`.
  Backup first: `backups/config.yaml.pre-claireon-20260926`.
- Then `hermes --tui` from `BS_GodFile` = Hermes in Claireon (AGENTS.md binding rules load automatically).
  Until the lease exists: **one agent on the editor at a time** — owner-policed.
- Next build step: H1 (router + lease) — not started.

## Architecture
```
 Owner (phone/Discord/terminal)
   │  task ask
   ▼
 Hermes runtime ── kanban card = Task Packet ──► Jev router (system_one, closed sets)
   │                                              → lane · model tier · needs_editor · verify_kind
   ├─ worker lanes (Hermes subagents / CLIs)
   │    (lanes resolved via specs/orchestration/model_tiers.v1.json + Tools/model_router.py tier/tasks; Claude is NOT enabled on this Bedrock account)
   │    T3 / fast / bulk  → Mantle zai.glm-4.7-flash          (docs, triage, audit, manifests)
   │    T2 / code         → Mantle qwen.qwen3-coder-next / 480b (tools, tests, C++)
   │    T1 / deep review  → Mantle qwen.qwen3-235b-a22b-2507   (long reasoning, independent review)
   │    scoped_editor     → Hermes-in-Claireon, holds EDITOR LEASE (one at a time)
   │    T4 / offline_bulk → local Ollama via agent_bridge (free, overnight, zero cloud spend)
   │    gateway_chat      → Nous glm-5.3-flash   (status, phone replies)
   ├─ tools: Claireon (HTTP, read-only default) · melodia MCP · shell (ladder scripts, UAT, Blender -b)
   ▼
 Result packet + artifacts in Saved/Audit/<task_id>/
   ▼
 Verifier = Claude Code (owner quota spent on judgment only): opens the ARTIFACT, not the report
   ▼
 Owner approves any git / p4 / publish op
```

## The four mechanisms (the only new code)
1. **Task Packet** — `Tools/agent_router/task_packet.schema.json`: `id, goal, done_when[], inputs[],
   surfaces[], mutation_scope (none|files|editor|git), artifacts_expected[], budget_usd, max_turns`.
   One packet = one kanban card. `done_when` must name a file a verifier can open.
2. **Jev router** — a `route` subcommand on the EXISTING `Tools/model_router.py` (do not add a second
   router): one `system_one` call per packet, closed sets only
   (lane, tier, needs_editor, verify_kind ∈ {artifact_open, test_log, image_look, diff_review}). Records
   the model string; `classical-fallback` ⇒ card goes to the owner, never auto-dispatched.
3. **Editor lease** — `Saved/Agents/editor.lease` (holder, session, surface, expires_at). One holder at a
   time for any editor mutation; Claude Code sessions honour it too. Lease is refused when a
   `deploy/*_LOOP_STOP` file exists or a modal is open (`MODAL_OPEN` in the log). PIE/load_level only by
   the holder. This is how "never two surfaces on one graph" becomes enforced instead of remembered.
4. **Verify gate** — a card moves to Done only after the verifier writes `verified.json`
   (who, what artifact was opened, pass/fail). Hermes self-reports never close a card.

## Phases
- **H0 Plumbing (≈45 min, owner at keyboard for AWS console).**
  a. DONE 2026-09-26: new Bedrock **Mantle** key works (`https://bedrock-mantle.us-east-1.api.aws/v1`,
     env `AWS_BEARER_TOKEN_BEDROCK`); Qwen/GLM/gpt-oss verified; Claude → permission_error (skip).
  b. Hermes config: `bedrock.discovery.enabled: true` (discover ids — do not hard-code), add
     `fallback_providers: [bedrock]`, per-lane models under `auxiliary`/profiles.
  c. `mcp_servers.claireon: {url: http://127.0.0.1:60162/mcp}`; enable `melodia`; start the Claireon proxy.
  d. Smoke: Hermes calls Claireon `tool_search` (read-only) with the editor up, then again across an editor
     restart (proxy proof). Receipt `Saved/Audit/hermes_h0/`.
- **H1 Router + lease (jcode Fleet 1 packet 3).** `model_router.py route`, `Tools/agent_lease.py` + a 20-line Hermes skill
  that reads packets from kanban, calls the router, dispatches. Offline tests: routing is deterministic on a
  fixture packet set; lease refuses a second holder and honours STOP files.
- **H2 Canary (Jev 0.90): packaged cook + launch + log triage.** Packet: run
  `Tools/issue51_ladder.ps1 package` then `launch`, triage `BS_GodFile.log` with the bulk lane, write
  `launch.json` + a triage note. Claude verifies by opening `launch.json` and the log lines it cites.
  Pass = card closes with no Claude tokens spent on the 30+ min cook.
- **H3 Widen.** Regression-harness repair (`frames_captured 0`, battle-trigger via tagged contract), nightly
  read-only audits (Hermes cron), bulk Blender `-b` passes, Figma kit export. Phone status via the gateway.

## Owner decisions
- **D1 Editor access** (Jev 0.40): (a) Hermes read-only Claireon, mutation only under the lease via
  Monolith *(Jev pick)*; (b) Hermes may mutate through Claireon when it holds the lease; (c) no editor for
  Hermes at all.
- **D2 Bedrock budget:** monthly cap + per-packet `budget_usd` default (suggest $2 bulk / $10 scoped).
- ~~D3 Which Bedrock models~~ — answered 2026-09-26: Mantle open models yes, Claude no.
- **Fleet:** jcode swarm policy + Fleet 1 packets: `.jcode/swarm-prompt.md`, `.jcode/coordinator-bootstrap.md`;
  lanes registered by `deploy/setup_agent_lanes.ps1`; goal `.hermes/plans/2026-09-26_jcode-fleet-goal.md`.

## Guardrails every worker prompt inherits (Hermes context file)
Never-touch table and Red list from `CLAUDE.md`; git law (worktree patches only); `MelodiaIntegrationMap`
is not tidied and not loaded away from; no `load_asset` bulk loads (registry tags); save approved editor
work immediately; no PIE→load_level; delegated output is not evidence.

Note: `%LOCALAPPDATA%/hermes/bedrock_setup_complete.txt` prints a prefix of the Bedrock bearer token in
plain text — delete that line or the file.
