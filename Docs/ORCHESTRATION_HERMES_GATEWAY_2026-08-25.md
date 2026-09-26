# Hermes Gateway & Multi-CLI Orchestration

> **Current wiring (2026-09-26):** [`.hermes/plans/2026-09-26_hermes-orchestrator-infra-plan.md`](../.hermes/plans/2026-09-26_hermes-orchestrator-infra-plan.md)
> — Hermes runtime · Jev router · Claude verifier · editor lease · Bedrock/local lanes. This file stays
> the gateway/CLI reference; do not build a second router from it.

**Status:** 2026-08-25 · Hermes Agent v0.20.5
**Author:** fromage3900 / Hermes orchestrator lane

Hermes Agent is the **architectural orchestrator** of this project. It decides *what* to do,
routes *which* agent lane runs it, and delegates concrete implementation work to specialized
coding CLIs. This doc is the operating contract for that arrangement.

---

## 1. The architecture

```text
                        ┌──────────────────────────────────────┐
                        │   Hermes Agent (orchestrator)        │
                        │   - decides WHAT / WHICH lane        │
                        │   - owns memory, skills, gates, cron │
                        │   - gateway = Discord + SMS + CLI    │
                        └──────────────────────────────────────┘
                                     │  delegate_task / spawn
                 ┌───────────────────┼─────────────────────────┐
                 ▼                   ▼                          ▼
          Claude Code CLI       Kimi CLI                  (other CLIs)
          (Anthropic)           (Moonshot)                jcode / opencode / codex
```

- **Hermes owns the plan, the evidence ledger, the gates, memory and delivery.**
- **Claude Code / Kimi CLI are the hands** — they implement, review, refactor under a brief.
- Nothing an agent lane claims is "done" until the gate has a ledger row
  (see `AGENTS.md` → Echo pipeline). Delegation does not change that rule.

## 2. Delegation router

`deploy/orchestrate/delegate.sh` wraps both CLIs in one interface:

```bash
# Delegate a coding task to Claude Code (print mode, non-interactive)
bash deploy/orchestrate/delegate.sh claude "Add error handling to Tools/foo.py" \
  --dir /c/EnvironmentPortfolio/BS_GodFile --max-turns 15

# Read-only review lane (Claude restricted to Read only)
bash deploy/orchestrate/delegate.sh claude "Review Tools/foo.py for bugs" --readonly

# Delegate to Kimi CLI (permission-less --yolo, trusted lanes only)
bash deploy/orchestrate/delegate.sh kimi "Refactor Tools/bar.py" \
  --dir /c/EnvironmentPortfolio/BS_GodFile

# Health check
bash deploy/orchestrate/delegate.sh status
```

**Routing policy (align with `Tools/model_router.py`):**

| Work class            | Prefer        | Notes                                    |
|-----------------------|---------------|------------------------------------------|
| Deep review / audit   | Claude (readonly) | `--readonly` = `--allowedTools Read`   |
| Multi-turn coding     | Claude or Kimi| `--max-turns` caps runaway loops         |
| Fast/parallel edits   | Kimi          | `--yolo` auto-approves; trusted lanes only |
| Editor / Monolith work| Hermes (MCP)  | Never two MCP surfaces on one graph      |

## 3. Prerequisites / auth status (2026-08-25)

| CLI    | Version | Auth status                          | Action needed                                |
|--------|---------|--------------------------------------|----------------------------------------------|
| claude | 2.1.239 | **NOT logged in**                    | `claude auth login` (browser OAuth)          |
| kimi   | 0.26.0  | Config present; **quota 403 on test**| Kimi subscription/quota (see `.kimi-code`)   |

**Hermes gateway model:** switched from local `ollama` (qwen3.8-27b, ollama daemon DOWN) to
**Nous Portal** (`deepseek/deepseek-v4-flash-0731`). This is required so the Discord/SMS bots
have a reachable inference provider. Ollama can be restored later with
`hermes model` → Ollama when the daemon is up.

## 4. Gateway platforms

The Hermes gateway is a single background process connecting Discord, SMS and CLI. It runs the
full agent (tools, memory, slash commands, cron) on every platform.

### The Melusina persona (verified 2026-08-25)

The gateway answers **in-character as Melusina**, the bard protagonist — not as generic Hermes.
Registered as a custom personality and set as the active default:

- `agent.personalities.melusina` in `~/.hermes/config.yaml` — short persona string.
- Full voice/soul at `Docs/Personas/MELUSINA_PERSONA_SOUL.md` (project source of truth).
- `display.personality = melusina` — active default for CLI + gateway (Discord/SMS).
- Switch back anytime with `/personality none`; re-enable with `/personality melusina`.
- Verified end-to-end: a test query returned an in-character reply (rain on stone, Sir
  Melodious's four notes, strings tuned).

**Character ground truth (from project docs):** Melusina is a bard whose music is tied to her
emotional state; emotionally strained at the story's start; bonded to Sir Melodious, her cockatoo
companion who anchors the power in her songs; found-family warmth; rhythm/Songcraft is her
identity. (`Docs/FULL_GAME_LOOSE_SCOPE_2026-07-31.md`,
`Docs/MELODIA_FIRST_20_MINUTES_VERTICAL_SLICE.md`.)

### Discord bot ("Melusina")

- **Token:** present in `~/.hermes/.env` (`DISCORD_BOT_TOKEN`) — **verified valid** against
  Discord API (bot `zunda`, id `1539128471790288986`).
- **Blocker (verified at runtime 2026-08-25):** the gateway cannot connect until
  **Privileged Gateway Intents** are enabled for the bot in the Discord Developer Portal.
  → https://discord.com/developers/applications → your application (id `1539128471790288986`)
  → **Bot** → Privileged Gateway Intents → enable **Server Members Intent** AND
  **Message Content Intent** → Save Changes. Then restart the gateway.
  Without Message Content the bot can't read what you type; without Server Members it can't
  resolve the allowlist. This is the #1 reason a Discord bot goes silent.
- **Allowlist:** `DISCORD_ALLOWED_USERS=fromage39` — ⚠️ this should be your **numeric Discord
  user ID** (Settings → Advanced → Developer Mode → right-click your name → Copy User ID), not
  your username. Fix if the bot denies you.
- **Gateway model:** must be a live provider (now Nous Portal).
- **Behaviors:** DMs respond to everything; server channels require `@mention` by default;
  DM-pairing lets unknown users request access with a one-time code
  (`hermes pairing approve <platform> <code>`).

### SMS (Twilio)

- **Credentials:** `TWILIO_ACCOUNT_SID`, `TWILIO_AUTH_TOKEN`, `TWILIO_PHONE_NUMBER`,
  `SMS_WEBHOOK_URL` are **NOT yet in `.env`** — SMS is not wired.
- **Required to enable:** Twilio account + a number with SMS capability, plus a public webhook
  URL (Twilio POSTs inbound texts to `https://<host>:8080/webhooks/twilio`). Local dev can
  expose it with `cloudflared tunnel --url http://localhost:8080` (both `cloudflared` and
  `ngrok` are installed). `aiohttp` is present (`.env` sms dep).
- **Security:** defaults deny everyone — set `SMS_ALLOWED_USERS=+1...` to your number(s).

## 5. Starting / managing the gateway

```bash
hermes gateway status       # is it running?
hermes gateway setup        # interactive platform wizard
hermes gateway start        # start installed background service
hermes gateway stop / restart
hermes gateway run          # foreground (debug)
```

A Windows login item (`Hermes_Gateway.vbs`) is already installed but no process was running;
start it with `hermes gateway start` (or `hermes gateway` in a terminal to watch logs).

## 6. The orchestrator loop (how Hermes uses this)

1. A task arrives (from you, a cron job, Discord DM, or SMS).
2. Hermes picks the lane (via `Tools/model_router.py` classes) and writes a self-contained brief.
3. If it's implementable by a coding CLI, Hermes calls `delegate.sh claude|kimi "brief"`.
4. The worker returns; Hermes verifies against the evidence ledger / gate standard.
5. Hermes reports back on the originating platform.

**Working agreement still binds every delegated worker:** do the job asked, ship it, stop; never
compensate; no parallel authority over the same surface; never run destructive git on the repo.

---

## 7. Universe Foundry mission dispatch

For world-scale production, Hermes may consume the deterministic mission emitted by `Tools/universe_foundry.py`. The mission DAG does not replace Hermes memory/gates and does not execute tools itself; it gives Hermes a content-addressed set of legal specialist jobs, dependencies, stop conditions and evidence requirements.

Faraway Mother World Zero:

```bash
python Tools/universe_foundry.py compile \
  --genome specs/universe/faraway_mother.world_genome.v1.json \
  --delta specs/universe/faraway_mother.resolved_demo.world_delta.v1.json
```

Hermes dispatches ready tasks through existing lanes. Jev is called only for tasks whose `owner=jev`, and those tasks always carry closed candidate sets. A fixture delta may exercise orchestration but may not certify persistence.

Durable contract: `Docs/Production/UNIVERSE_FOUNDRY_CONTRACT.md`.

---

## 8. Specialist model fleet setup — 2026-09-23

The current setup/benchmark plan for new model specialists is:

`Docs/Plans/HERMES_SPECIALIST_MODEL_FLEET_SETUP_2026-09-23.md`

Machine-readable candidates:

`specs/orchestration/hermes_specialist_fleet.candidates.v1.json`

Rules:

- this is **not live routing policy**;
- do not modify `Tools/model_router.py` merely because a provider connects;
- run the plan's canaries and record cost/latency/evidence first;
- credentials remain outside Git;
- restore the previous Hermes default after provider canaries unless the owner explicitly promotes a candidate;
- modality-specific systems (HappyOyster, image, voice, avatar) receive purpose-built sidecars rather than being forced into a text chat router;
- first recommended setup canary is MiMo V2.6 Pro because Xiaomi publishes a first-party Hermes Agent integration guide;
- Muse Code runs through WSL on the Windows workstation unless Meta publishes a supported native Windows path.

Promotion remains owner-approved and evidence-backed.

---

### Evidence

- `deploy/orchestrate/delegate.sh` — delegation router (tested; claude/kimi invoked, auth-gated).
- This file — the operating contract.
- `~/.hermes/.env` — Discord token (present), Twilio (absent).
