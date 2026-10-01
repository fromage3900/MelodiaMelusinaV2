# Honcho Memory + Discord Gateway — Sync & Operations

**Status:** 2026-10-01 · configured and verified on main workstation  
**Author:** fromage3900 / Hermes orchestrator lane  
**Supersedes:** nothing (new document)

---

## 1. What this covers

This document is the operating contract for two Hermes Agent services that together
enable cross-workstation continuity:

1. **Honcho** — the remote memory provider. Stores session memory, user profile, and
   dialectic reasoning in the cloud so any workstation with the same Honcho API key
   shares the same long-term memory.

2. **Discord Gateway** — the messaging platform. Connects the Hermes agent to Discord
   so you can interact with it from any device (desktop, laptop, phone) via DMs or
   server mentions.

Together they let you: start work on one machine, continue on another, and talk to
your agent from anywhere.

---

## 2. Prerequisites

### 2.1 Honcho (memory provider)

- Sign up at https://app.honcho.dev
- Generate an API key (Settings → API Keys)
- The key format is `hch-v3-...`

### 2.2 Discord bot

- Create a bot at https://discord.com/developers/applications
- Under **Bot → Privileged Gateway Intents**, enable:
  - **Server Members Intent** (required for allowlist resolution)
  - **Message Content Intent** (required to read what you type)
- Copy the bot token
- Invite the bot to your server with `applications.commands` and `bot` scopes

### 2.3 Environment variables

Both services read from `~/.hermes/.env`:

```bash
# Honcho
HONCHO_API_KEY=hch-v3-your-key-here

# Discord (also stored in config.yaml via `hermes config set`)
DISCORD_BOT_TOKEN=your-bot-token-here
DISCORD_ALLOWED_USERS=your-numeric-discord-user-id
```

> **Security note:** The `.env` file is never committed to Git. The Discord token
> is also stored in `config.yaml` (via `hermes config set`) for the gateway service,
> which does not inherit shell environment variables.

---

## 3. Configuration

### 3.1 Honcho setup

```bash
# Write the API key to ~/.hermes/.env
echo 'HONCHO_API_KEY=hch-v3-your-key-here' >> ~/.hermes/.env

# Create the Honcho config file
mkdir -p ~/.honcho
cat > ~/.honcho/config.json << 'EOF'
{
  "apiKey": "hch-v3-your-key-here",
  "baseUrl": "https://api.honcho.dev"
}
EOF

# Verify
hermes honcho status
hermes memory status
```

Expected: `hermes memory status` shows `Provider: honcho` and `Status: available`.

### 3.2 Discord gateway setup

```bash
# Enable Discord in the gateway
hermes config set gateway.platforms.discord.enabled true
hermes config set gateway.platforms.discord.token "your-bot-token-here"

# Set your numeric Discord user ID (for allowlist)
# Enable Developer Mode in Discord → right-click your name → Copy User ID
hermes config set gateway.platforms.discord.allowed_users "your-numeric-id"

# Restart the gateway
hermes gateway restart
```

### 3.3 Gateway management

```bash
hermes gateway status       # is it running?
hermes gateway start        # start background service
hermes gateway stop         # stop
hermes gateway restart      # restart
hermes gateway run          # foreground (debug)
```

---

## 4. Cross-workstation sync

### 4.1 How it works

```
┌─────────────────┐     ┌─────────────────┐
│   Desktop       │     │   Laptop        │
│   (main)        │     │   (worker)      │
│                 │     │                 │
│  Hermes Agent   │     │  Hermes Agent   │
│       │         │     │       │         │
│       ▼         │     │       ▼         │
│  Honcho Cloud   │◄───►│  Honcho Cloud   │
│  (shared memory)│     │  (shared memory)│
│                 │     │                 │
│  Discord GW     │◄───►│  Discord GW     │
│  (you talk here)│     │  (or here)      │
└─────────────────┘     └─────────────────┘
```

Both machines point to the same Honcho workspace. Memory written on one machine
is available on the other. The Discord gateway can run on either machine (or both,
with the same bot token — Discord will route messages to one of them).

### 4.2 Laptop setup

On the laptop, repeat the same configuration:

```bash
# 1. Install Hermes Agent
curl -fsSL https://hermes-agent.nousresearch.com/install.sh | bash

# 2. Configure Honcho (same API key)
echo 'HONCHO_API_KEY=hch-v3-your-key-here' >> ~/.hermes/.env
mkdir -p ~/.honcho
cat > ~/.honcho/config.json << 'EOF'
{
  "apiKey": "hch-v3-your-key-here",
  "baseUrl": "https://api.honcho.dev"
}
EOF

# 3. Configure Discord (same bot token)
hermes config set gateway.platforms.discord.enabled true
hermes config set gateway.platforms.discord.token "your-bot-token-here"
hermes config set gateway.platforms.discord.allowed_users "your-numeric-id"

# 4. Start the gateway
hermes gateway start

# 5. Verify
hermes honcho status
hermes memory status
hermes gateway status
```

### 4.3 Git-based file sync (the existing lane)

For repository files (source code, docs, specs, Blueprints), the existing Git-based
sync remains the authority:

```powershell
# On either machine
.\deploy\sync_workstation.ps1 -Mode Check
.\deploy\sync_workstation.ps1 -Mode Sync -LfsProfile Gameplay
```

See `Docs/Plans/LAPTOP_WORKSTATION_SETUP_AND_OFFLOAD_2026-09-02.md` for the full
workstation setup and handoff protocol.

---

## 5. Discord bot usage

### 5.1 Direct messages

DM the bot directly. It responds to everything (subject to allowlist).

### 5.2 Server channels

Mention the bot (`@Melusina`) in any server channel. It only responds to mentions
by default.

### 5.3 Slash commands

The gateway supports Hermes slash commands in Discord:

| Command | Purpose |
|---------|---------|
| `/help` | List available commands |
| `/status` | Agent and gateway status |
| `/memory` | Memory provider status |
| `/personality melusina` | Switch to Melusina persona |
| `/personality none` | Switch to default persona |

### 5.4 Pairing new users

If an unknown user DMs the bot, they can request access:

```
User: /pair
Bot: Your pairing code is ABCD-1234
User (owner): hermes pairing approve discord ABCD-1234
```

---

## 6. Honcho memory usage

### 6.1 How memory works

Honcho stores:
- **User profile** — who you are (name, role, preferences)
- **Session memory** — what happened in each session
- **Dialectic reasoning** — the agent's reasoning about your goals and context

Memory is injected into every session automatically. The agent can also explicitly
read/write memory via the `memory` tool.

### 6.2 Session strategy

The current config uses `per-directory` strategy: each working directory gets its own
Honcho session. This means `BS_GodFile` on desktop and `BS_GodFile` on laptop share
the same session (same directory name = same session).

```bash
# Check current strategy
hermes honcho strategy

# Change strategy (options: per-session, per-directory, per-repo, global)
hermes honcho strategy per-directory
```

### 6.3 Memory commands

```bash
hermes memory status          # provider status
hermes honcho status          # detailed Honcho connection info
hermes honcho peers           # show peer identities
hermes honcho sessions        # list known sessions
hermes honcho sync            # sync config to all profiles
```

---

## 7. Troubleshooting

### 7.1 Honcho not connecting

```bash
# Check if the API key is set
grep HONCHO_API_KEY ~/.hermes/.env

# Check the config file
cat ~/.honcho/config.json

# Re-verify
hermes honcho status
hermes memory status
```

Common causes:
- API key not in `~/.hermes/.env`
- `~/.honcho/config.json` missing or malformed
- Network/firewall blocking `api.honcho.dev`

### 7.2 Discord bot not responding

```bash
# Check gateway status
hermes gateway status

# Check Discord config
hermes config get platforms.discord

# Restart gateway
hermes gateway restart

# Run in foreground for debug logs
hermes gateway run
```

Common causes:
- Privileged Gateway Intents not enabled (Server Members + Message Content)
- `DISCORD_ALLOWED_USERS` set to username instead of numeric user ID
- Bot not invited to server with correct scopes

### 7.3 Gateway service doesn't inherit .env

The Windows gateway service (started via `hermes gateway start`) does NOT inherit
`~/.hermes/.env`. The Honcho API key must be in `~/.honcho/config.json` (which it
reads directly), and the Discord token must be in `config.yaml` (set via
`hermes config set`).

---

## 8. Security

- **Never commit** `~/.hermes/.env`, `~/.honcho/config.json`, or any file containing
  API keys or tokens to Git.
- The Discord bot token and Honcho API key are stored locally only.
- Honcho uses HTTPS for all API calls.
- The Discord gateway allowlist (`DISCORD_ALLOWED_USERS`) restricts who can
  interact with the bot.
- `hermes config set` stores values in `config.yaml` which IS in the Hermes home
  directory (not the project repo), so it is not committed.

---

## 9. Quick reference

| Task | Command |
|------|---------|
| Check Honcho status | `hermes honcho status` |
| Check memory status | `hermes memory status` |
| Check gateway status | `hermes gateway status` |
| Restart gateway | `hermes gateway restart` |
| Start gateway | `hermes gateway start` |
| Stop gateway | `hermes gateway stop` |
| Debug gateway | `hermes gateway run` |
| Sync workstation | `.\deploy\sync_workstation.ps1 -Mode Sync` |
| Set Discord token | `hermes config set gateway.platforms.discord.token "..."` |
| Set Honcho key | `echo 'HONCHO_API_KEY=...' >> ~/.hermes/.env` |

---

## 10. Related documents

- `Docs/ORCHESTRATION_HERMES_GATEWAY_2026-08-25.md` — original gateway/CLI reference
- `Docs/Plans/LAPTOP_WORKSTATION_SETUP_AND_OFFLOAD_2026-09-02.md` — laptop setup
- `deploy/sync_workstation.ps1` — Git/LFS sync script
- `Docs/Production/AGENT_PRODUCTION_PLAYBOOK.md` — production workflow router
- https://hermes-agent.nousresearch.com/docs/user-guide/features/honcho — official Honcho docs
