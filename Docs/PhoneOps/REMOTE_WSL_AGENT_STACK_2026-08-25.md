# Remote WSL agent stack (phone-first) — 2026-08-25

Infrastructure plan for operating MelodiaMelusinaV2 from an iPhone through a private path into Windows → WSL2 → tmux → agent CLIs → Git.

**Scope:** docs and conventions only. No gameplay, Unreal, Blender, or architecture changes.  
**Authority:** [`_AGENT_WORKING_AGREEMENT.md`](../../_AGENT_WORKING_AGREEMENT.md). Melodia ship remains P0.

## Target path

```text
iPhone
  → Blink / SSH / Mosh
  → Windows (private overlay only — not public internet)
  → WSL2 (prefer existing Ubuntu)
  → tmux session: melusina
  → Claude Code / Codex / Kimi / OpenCode / Pi / Hermes
  → Git
  → MelodiaMelusinaV2
```

## Two environments (do not conflate)

| Host | What it is | What phone can do today |
|------|------------|-------------------------|
| **Cursor Cloud** | Ubuntu VM, repo at `/workspace`, no WSL, no Windows OpenSSH, no UE | Docs, audits, PRs — **this path already works** ([SETUP.md](SETUP.md)) |
| **Windows UE PC** | Live editor, Monolith, Blender, local agent CLIs, WSL Muse (documented) | Editor work; Blink→SSH only after private access is configured **on that PC** |

A cloud agent **cannot** install or verify Windows OpenSSH, Tailscale, WSL2, or local CLIs. Run the PC audit on the PC (commands below).

## Cloud audit snapshot (2026-08-25)

Verified on Cursor Cloud only — **not** a claim about the Windows box.

| Item | Cloud status |
|------|----------------|
| OS | Ubuntu 24.04 |
| WSL / `/mnt/c` | Absent |
| Git | 2.43.0 · remote MelodiaMelusinaV2 |
| SSH client | Present |
| OpenSSH **server** | Not installed |
| Mosh | Not found |
| tmux | 3.5a present; no `melusina` session |
| Node / npm / Python | Present (Node 22 / Python 3.12) |
| Claude / Codex / Kimi / OpenCode / Pi / Ollama CLIs | Not on PATH |
| Tailscale | Not installed |
| Hermes CLI | Not on PATH |
| Hermes **in-repo** | `deploy/hermes_daemon.py` — local doc/git daemon, **not** an iPhone messaging gateway |
| `Docs/AI/` | Does not exist (use `Docs/AI_*.md` + this PhoneOps set) |

Documented on the Windows box (read docs; do not treat as live-verified from cloud):

- WSL2 Ubuntu + Muse — [MUSE_CODE_LANE_2026-08-11.md](../Production/MUSE_CODE_LANE_2026-08-11.md)
- OpenCode (Rider) — `.opencode/`
- jcode swarm — [JCODE_SWARM_PIPELINE.md](JCODE_SWARM_PIPELINE.md)
- Phone primary today — Cursor iOS → Cloud Agents ([SETUP.md](SETUP.md))

## Safety rules (binding for any PC prep)

Do **not**:

- Modify Unreal / Blender / project settings / Blueprints for this stack
- Expose SSH to the public internet
- Open firewall rules for arbitrary inbound internet
- Reset the repo, force-checkout, or run `git clean`
- Install random third-party bootstrap scripts
- Give agents unrestricted destructive shell access
- Auto-launch autonomous agent loops

Prefer:

- Existing WSL Ubuntu (do not reinstall if suitable)
- Tailscale or another authenticated private overlay
- Existing installations over new ones
- Owner approval before installs listed under **Needs approval**

## Status boards

### READY NOW (cloud / phone)

1. Cursor iOS → Cloud Agents → MelodiaMelusinaV2 → draft PRs
2. Read this doc + [AGENT_LANE_HANDOFF.md](AGENT_LANE_HANDOFF.md) + [MOBILE_LANES.md](MOBILE_LANES.md)
3. Docs-only and closed-editor C++ lanes per [AGENTS.md](../../AGENTS.md)

### ALREADY INSTALLED (cloud — verified)

Git, SSH client, tmux binary, Node, npm, Python, in-repo Hermes daemon scripts.

### NEEDS INSTALLATION (Windows PC — verify first)

OpenSSH Server (or SSH into WSL only), Tailscale (recommended), Mosh (optional), agent CLIs you choose, tmux **inside** WSL, messaging gateway only if Hermes is used as mobile orchestrator.

### NEEDS APPROVAL

1. Full Phase-1 audit **on the Windows PC** (paste output back)
2. Tailscale (or name existing private overlay)
3. Which agent CLIs to install
4. Creating WSL `melusina` tmux helpers
5. Hermes-as-mobile-orchestrator + messaging gateway choice
6. Any repo relocate from `/mnt/c/...` → WSL `~/` (propose only; never auto-move)

### SECURITY CONCERNS

- Public SSH = rejected
- Agent destructive git = already forbidden (`AGENTS.md`)
- Hermes daemon logs under the project ≠ iPhone auth surface

## WSL

- If WSL2 + Ubuntu already exist and suit development → **do not reinstall**
- Prefer stable Ubuntu unless a project config says otherwise
- Muse lane already assumes WSL2 Ubuntu reading the Windows project tree
- If the live tree is only under `/mnt/c/...`, expect NTFS I/O cost for heavy git/agent work; migration plan is separate and owner-approved

### PC audit commands (run on Windows)

PowerShell:

```powershell
winver
wsl -l -v
Get-Service sshd -ErrorAction SilentlyContinue | Format-List Status,StartType
Get-Command git, tailscale, mosh -ErrorAction SilentlyContinue
git --version
```

Inside preferred WSL distro:

```bash
uname -a
tmux -V
command -v claude codex kimi opencode pi hermes ollama node npm python3 git
pwd
git -C /path/to/MelodiaMelusinaV2 status -sb
git -C /path/to/MelodiaMelusinaV2 branch --show-current
git -C /path/to/MelodiaMelusinaV2 remote -v
git -C /path/to/MelodiaMelusinaV2 worktree list
```

Report whether the repo is on a Windows mount (`/mnt/c/...`) or native WSL filesystem (`~/...`). Do not relocate automatically.

## tmux workspace (proposed — not created from cloud)

Session name: `melusina`

```text
melusina
├── claude
├── codex
├── kimi
├── opencode
├── hermes
└── monitor
```

Rules:

- Do **not** auto-launch every agent
- Helper script responsibilities only: start workspace, attach, list windows, report which panes look active
- No autonomous loops

Implementation waits for PC shell access + approval.

## Git (remote workflow)

- Do not alter branch / commit / push as part of infra prep unless the owner asks
- Reliable remote Git = identity + auth already working for the operator; cloud agents use GitHub token via Cursor
- Canonical integration branch: `origin/main`
- Cloud worktrees live under `/workspace` (overlay) — not the UE Content tree

## Agent branch convention (document only — no branches yet)

```text
agent/claude/<short-topic>
agent/codex/<short-topic>
agent/kimi/<short-topic>
agent/opencode/<short-topic>
agent/pi/<short-topic>
```

Cursor Cloud continues to use `cursor/<name>-ca02` (or the run’s required suffix). Do not create `agent/*` branches until explicitly requested.

Each lane identifies itself via [AGENT_LANE_HANDOFF.md](AGENT_LANE_HANDOFF.md): branch, commit, task, authority, handoff, validation.

## Hermes

| Mode | Status |
|------|--------|
| In-repo daemon (`deploy/hermes_daemon.py`) | Exists — docs/git health style monitoring on the project machine |
| Mobile orchestration (iPhone message → remote agent → Git) | **Not configured**; needs approved messaging gateway (e.g. Telegram/Discord bot) + constrained shell |
| Auto-install from cloud | **Forbidden** until owner approves |

## Mobile access

| Path | Status |
|------|--------|
| Cursor iOS → Cloud Agents → GitHub | Ready now |
| Blink → SSH/Mosh → Windows → WSL | Needs PC audit + private overlay |
| Tailscale | Recommended next step on PC; do not install from cloud |
| Public SSH | Never |

## Exact next steps

1. Owner runs PC audit commands above; paste results into a cloud/phone follow-up.
2. Approve Tailscale (or name overlay) + which CLIs.
3. On WSL only: install missing pieces, create `melusina` tmux helpers, no auto-loops.
4. Start using [AGENT_LANE_HANDOFF.md](AGENT_LANE_HANDOFF.md) for lane tips; keep `_TASK_QUEUE.md` / P0 ledger as product authority.
5. Keep P0 Melodia live proof on the editor box; this stack stays infrastructure.

## Related

- [AGENT_LANE_HANDOFF.md](AGENT_LANE_HANDOFF.md) — shared handoff fields + states
- [SETUP.md](SETUP.md) — current phone/cloud setup
- [MOBILE_LANES.md](MOBILE_LANES.md) — phone vs PC ownership
- [JCODE_SWARM_PIPELINE.md](JCODE_SWARM_PIPELINE.md) — Windows jcode (parallel coding)
- [MUSE_CODE_LANE_2026-08-11.md](../Production/MUSE_CODE_LANE_2026-08-11.md) — WSL Muse
- [PHONE_ARTIST_BRIDGE_HANDOFF_2026-08-11.md](../Handoffs/PHONE_ARTIST_BRIDGE_HANDOFF_2026-08-11.md)
