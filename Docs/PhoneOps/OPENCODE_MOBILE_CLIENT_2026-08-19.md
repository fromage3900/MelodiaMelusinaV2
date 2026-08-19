# OpenCode Mobile Client — setup (2026-08-19)

**Repo:** [bmpenuelas/opencode-mobile-client](https://github.com/bmpenuelas/opencode-mobile-client)  
**Role:** Native Android/iOS shell around the OpenCode Web UI — connect to your **workstation** OpenCode server over LAN or Tailscale. Monitor and steer Nemotron harness runs (Lane B) from phone while UE stays on desktop.

**Not a replacement for:** Cursor cloud agents (PR/docs lane), jcode swarm (desktop parallel coding), or direct Monolith access (server runs on desktop only).

---

## Fit in today's parallel plan

| Lane | Tool | Mobile client use |
|---|---|---|
| A (no editor) | Cloud agent / grep | — |
| B (editor open) | OpenCode background tabs | **Phone watches Nemotron Phase 1b/2 sessions** |
| C–D | Claireon build + T8 | Phone can reconnect after server restart |
| E | PIE runtime gate | Optional: check harness output from couch |
| **F (this doc)** | Mobile app + `opencode serve` | Setup once; use all day |

Add **Lane F** parallel to A: clone/build app on phone while workstation runs Phase 0.

---

## Prerequisites

- OpenCode CLI installed on Windows workstation (already used via Rider `Ctrl+\` → `127.0.0.1:4096`)
- Phone and workstation on **same LAN**, or **Tailscale** on both (recommended away from home)
- For native app: Node 18+, npm 9+; Android Studio **or** Xcode for device builds

---

## Step 1 — Start OpenCode server (workstation, REQUIRED)

Default Rider integration binds `127.0.0.1` only — **mobile cannot reach that**. For phone access bind all interfaces:

### With auth (recommended)

```powershell
# PowerShell — set once per session or in profile
$env:OPENCODE_SERVER_PASSWORD = "<pick-a-strong-password>"

# From repo root or any cwd where opencode finds AGENTS.md
opencode serve --hostname 0.0.0.0 --port 4096
```

App username defaults to **`opencode`**. Password = `OPENCODE_SERVER_PASSWORD`.

### Firewall (Windows)

Allow inbound TCP **4096** on Private network profile only — not Public.

```powershell
New-NetFirewallRule -DisplayName "OpenCode Mobile" -Direction Inbound -Protocol TCP -LocalPort 4096 -Action Allow -Profile Private
```

### Verify from phone network

From another device (or phone browser on Wi‑Fi):

```bash
curl -u opencode:<password> http://<workstation-lan-ip>:4096/
```

If using **Tailscale**, use the machine's `100.x.x.x` address instead of LAN IP.

---

## Step 2 — Clone and build mobile client

```bash
git clone https://github.com/bmpenuelas/opencode-mobile-client.git
cd opencode-mobile-client
npm install
npm run build
```

### Android (device or emulator)

```bash
npx cap add android   # first time only
npx cap sync
npx cap open android
```

Build/run from Android Studio. Cleartext HTTP to LAN is expected — repo documents `networkSecurityConfig` for local HTTP.

### iOS (macOS + Xcode only)

```bash
npx cap add ios         # first time only
npx cap sync
npx cap open ios
```

---

## Step 3 — Add server profile in app

| Field | Value |
|---|---|
| Name | `Melodia Workstation` |
| URL | `http://<LAN-IP-or-Tailscale-IP>:4096` |
| Username | `opencode` |
| Password | same as `OPENCODE_SERVER_PASSWORD` |
| Auto-connect | optional |

**Do not** use `127.0.0.1` on the phone — that points at the phone itself.

---

## Step 4 — Smoke test with today's Nemotron work

1. Workstation: `opencode serve --hostname 0.0.0.0 --port 4096` (password set)
2. Workstation: enable Monolith in `.opencode/opencode.jsonc` when UE open (Lane B)
3. Phone: connect → confirm OpenCode Web UI loads
4. Phone: open **plan** tab → paste T3 prompt (read-only, no MCP needed on phone to verify UI)
5. Confirm session visible on desktop OpenCode (shared server = shared sessions)

Record connect result → `Saved/Audit/nemotron_harness_2026-08-19/mobile_client_smoke.json` (local):

```json
{
  "date": "2026-08-19",
  "server_url": "http://REDACTED:4096",
  "auth": true,
  "health_check": "pass|fail",
  "iframe_load": "pass|fail|native_webview_fallback",
  "shared_session_with_desktop": "yes|no|untested",
  "notes": ""
}
```

---

## Security (read before exposing port 4096)

- OpenCode on your workstation has **`bash: allow`** and **`edit: ask`** per `.opencode/opencode.jsonc` — phone access = remote agent access to repo + shell.
- **Use password auth always** when binding `0.0.0.0`.
- **Prefer Tailscale** over port-forwarding to the public internet.
- **Never** expose 4096 on a VPS without TLS reverse proxy + strong auth.
- MCP (Monolith `:9316`) stays on localhost — mobile client talks to OpenCode only; OpenCode on desktop reaches Monolith.

---

## Troubleshooting (from upstream README)

| Symptom | Fix |
|---|---|
| Cannot connect | Server on `0.0.0.0` not `127.0.0.1`; firewall; correct LAN/Tailscale IP |
| HTTP 401 | Set password in app profile |
| Blank iframe after 8s | Menu → "Open in isolated native webview" |
| Works in app, not browser dev | Expected CORS on `localhost:5173` — use native build |
| Embedding blocked | `X-Frame-Options` — use native webview fallback |

Full upstream doc: [README.md](https://github.com/bmpenuelas/opencode-mobile-client/blob/main/README.md)

---

## Commands reference (upstream)

| Command | Purpose |
|---|---|
| `npm run dev` | Vite UI dev (CORS limits — not full test) |
| `npm test` | Vitest unit tests |
| `npm run cap:sync` | Sync web build to native projects |
| `npm run store:verify` | Pre-release checklist |

---

## After today

- [ ] Add Tailscale IP to server profile if not on same Wi‑Fi daily
- [ ] Document workstation IP in a **local only** note (not committed)
- [ ] Decide: mobile for **monitoring only** vs **primary steer** for long Nemotron runs
- [ ] If Claireon session (Lane D) changes MCP config, restart `opencode serve` before phone reconnect
