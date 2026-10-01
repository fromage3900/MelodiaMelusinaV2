# Hermes cross-device sync — status & fix plan

**Date:** 2026-09-30
**Machine:** LAPTOP-Q8S5OSQ2 (10.0.0.10) · `P:\MelodiaMelusinaV2-Laptop`
**Goal:** Brennan's Hermes notes/planning/sessions follow him between the laptop and the
main desktop PC (where the Humber schoolwork lives), without re-typing context.

---

## 1. What was actually tested (2026-09-30)

| # | Test | Method | Result |
|---|------|--------|--------|
| 1 | Honcho cloud memory round-trip | Wrote 2 messages to workspace `hermes` via SDK, read them back from a separate client | **PASS** — 2/2 returned |
| 2 | Honcho semantic recall | `peer.search("Humber schoolwork")` | **PASS** — returned the stored message |
| 3 | Honcho recall inside a real agent session | Fresh `hermes chat -q` calling `honcho_search` | **PASS** — cloud context surfaced in-session |
| 4 | Melusina persona | `personalities.melusina` + `display.personality`, live query | **PASS** — replied in character |
| 5 | Context-file truncation | `context_file_max_chars` raised, re-ran session | **FIXED** — warning gone |
| 6 | Gateway process | `hermes gateway status` | **RUNNING** — restarted, PID 21096, Windows login item |
| 7 | Webhook listener | `curl localhost:8644/` | **UP** — HTTP 404 on `/`, 401 on unsigned webhook POST (correct) |
| 7b | Stale module warning | `hermes gateway restart` | **PERSISTS** — see P6; code pulled but gateway did not relaunch itself |
| 8 | Discord bot exists | `GET /api/v10/applications/1539128471790288986` | **PASS** — HTTP 200, name `zunda`, public |
| 8b | Discord privileged intents | decode app flags `8953856` | **PASS** — Members + Message Content both ENABLED |
| 9 | Discord token on laptop | grep `.env` | **ABSENT** — desktop-side only |
| 10 | SMS send | `hermes send --to sms:+1519...` | **FAIL** — Twilio 401, placeholder creds |
| 11 | Desktop reachable on LAN | ping sweep + port probe | **FOUND** — `172.20.10.8` (iPhone hotspot), TTL=128, real MAC `1c-ce-51-95-d4-64` |
| 11b | api_server bind default | read `hermes_cli/config_defaults.py:2911` | **LOOPBACK** — `127.0.0.1`; root cause of P3 |
| 11c | Desktop ports | probe 445/3389/135/8642 | **ALL FILTERED** — hotspot is a Public network; Windows blocks inbound |
| 13 | Humber coursework location | search OneDrive roots | **FOUND** — `P:\OneDrive\Documents\GitHub\GAME259_2025_Winter_B` |
| 14 | Humber Hermes project | `hermes project create` | **DONE** — slug `humber-coursework` |
| 15 | OneDrive root | registry `UserFolder` | **`P:\OneDrive`** — coursework already cloud-synced |
| 16 | Per-directory cloud memory | ran a session `--in` the Humber dir, listed cloud sessions | **PASS** — `GAME259_2025_Winter_B` is its own cloud session |
| 17 | Session messages in cloud | read back the Humber session | **PASS** — messages stored and returned |
| 18 | Recall of a real coursework fact | wrote the path to Honcho, then asked a fresh session from memory | **PASS** — returned `P:\OneDrive\...\GAME259_2025_Winter_B` unprompted |
| 19 | **Default model validity** | compared `model.default` against the live Nous catalog | **FAIL → FIXED** — see below |
| 12 | `hermes sync` (skills cloud) | `hermes sync status` | **DISABLED** — `feature_enabled: false` server-side |

### Findings that matter

- **THE ACTUAL SYNC BUG — the default model was retired.** `model.default` was set to
  `upstage/solar-pro4:free`. The live Nous catalog (426 models) offers `upstage/solar-pro4`
  (paid), `upstage/solar-pro-3`, `upstage/solar-mini4` — **there is no `:free` variant any
  more.** Every session failed with `HTTP 400: Model is unavailable`. This is what "my setup
  isn't syncing properly" actually looked like: sessions dying mid-run, tools not firing,
  context appearing stale. **Fixed:** `model.default = meituan/longcat-2.5-preview:free`
  (verified live, 2026-10-01). Only 7 free models remain — see P7.
- **The memory half of sync works.** Honcho is live, authenticated, and round-trips through
  the cloud. Proven end-to-end: wrote the coursework path to Honcho, then asked a fresh
  session from memory only and it returned `P:\OneDrive\Documents\GitHub\GAME259_2025_Winter_B`
  unprompted.
- **Per-directory memory is proven.** Running a session in the Humber folder created
  `GAME259_2025_Winter_B` as its own cloud session. Each course folder gets its own thread
  automatically. This is the mechanism that makes coursework context follow you.
- **The coursework is already cloud-synced.** `P:\OneDrive` is the OneDrive root, holding
  `Documents\GitHub\GAME259_2025_Winter_B`. The desktop sees the same folder. Nothing to move.
- **The $22/$22 Nous Portal cap** is still at 100% and must move before anything heavy runs.
  *(Owner is adding credits.)*
- **AGENTS.md was silently truncating** — 43,777 chars against a 31,457 limit, ~12,320 chars
  (28% of project context) dropped at every session start. Mitigated two ways below.
- **The peer link is blocked by two defaults, not faults.** `API_SERVER_HOST` defaults to
  `127.0.0.1`, and the iPhone hotspot makes Windows classify the network as **Public**, which
  blocks all inbound — 445/3389/135 were all filtered on the desktop. Both need fixing.
- **`hermes sync` cannot be used** — the feature is off for this Nous account, server-side.
  Do not plan around it.
- **The hotspot is ephemeral.** `172.20.10.8` is DHCP on an iPhone hotspot; it changes and
  disappears. Fine for testing, not for a durable peer link.

---

## 2. Fix plan

Ordered by dependency. Items 1–3 are unblocked and partly done.

### P0 — Raise the spend cap  *(blocks everything else)*
- **Why:** at $22/$22 every run is on the edge; failures masquerade as sync bugs.
- **Do:** raise the cap or add credit at https://portal.nousresearch.com/manage-subscription
- **Verify:** `hermes chat -q "reply OK"` shows no cap warning.
- **Owner:** Brennan (billing action, cannot be automated).

### P0b — DONE: default model replaced
- **Was:** `upstage/solar-pro4:free` → `HTTP 400: Model is unavailable`. The `:free` variant
  no longer exists in the catalog. This was the real cause of the "not syncing properly" feel.
- **Now:** `meituan/longcat-2.5-preview:free`, verified live 2026-10-01.
- **See P7** for keeping this from happening again — free models get retired.

### P7 — Pin a durable model  *(prevents a repeat of P0b)*
- **Why:** only **7 free models** remain on the Nous catalog. Any of them can be retired the
  same way `solar-pro4:free` was, silently breaking every session again.
- **Current free options:** `inclusionai/ling-3.0-flash-sante:free`,
  `poolside/laguna-s-2.1:free`, `poolside/laguna-xs-2.1:free`, `meituan/longcat-2.0:free`,
  `inclusionai/ling-3.0-flash-fin:free`, `stepfun/step-3.7-flash:free`,
  `meituan/longcat-2.5-preview:free`
- **Do:** once credits land, switch to a paid frontier model for real work, and configure a
  **fallback chain** (`hermes fallback add`) so a retired model degrades instead of failing.
- **Verify:** `hermes fallback list` shows a chain; a session survives a dead primary.

### P1 — Install the trimmed AGENTS.md  *(staged, one command)*
- **Why:** stops 12,320 chars of project context being dropped every session.
- **Staged at:** `P:\MelodiaMelusinaV2-Laptop\AGENTS.md.new` (29,795 chars — under limit, 1,662 headroom)
- **Backup:** `AGENTS.md.bak-20260930-190520` (original, 44,041 bytes)
- **Do:** `cd /p/MelodiaMelusinaV2-Laptop && cp AGENTS.md.new AGENTS.md`
- **Verify:** file ≤ 31,457 chars; no `TRUNCATED` warning on next session.
- **Note:** the guard at `tools/file_tools_write_guards.py:171-184` blocks agent writes to
  AGENTS.md by design. Must be installed by hand — do not disable the guard.
- **Interim already applied:** `context_file_max_chars = 48000` (belt-and-braces; the trim is
  still worth doing so the file is right for every other tool that reads it).

### P2 — Decide who owns the Discord bot  *(decision, then one token)*
- **Bot:** "zunda" / Melusina persona, app id `1539128471790288986`. **Verified live via public
  API** (HTTP 200): `bot_public: true`, `bot_require_code_grant: false`, `hook: true`,
  install scope `applications.commands`, permissions `"0"`.
- **Privileged intents are ALREADY ENABLED** — this corrects the 2026-08-25 doc, which listed
  them as the blocker. Decoded from app flags `8953856`:
  - `GATEWAY_PRESENCE_LIMITED` (1<<13) — **SET**
  - `GATEWAY_GUILD_MEMBERS_LIMITED` (1<<15) — **SET** (Server Members)
  - `GATEWAY_MESSAGE_CONTENT_LIMITED` (1<<19) — **SET** (Message Content)
  - `APPLICATION_COMMAND_BADGE` (1<<23) — **SET** (has slash commands)
  - No unaccounted flag bits. **Nothing left to enable in the Developer Portal.**
- **Still to check:** `DISCORD_ALLOWED_USERS` must be the **numeric user ID**, not `fromage39`.
- **Permissions `"0"`** means the bot was installed with no server permissions — fine for DMs,
  insufficient for server-channel replies. If you want it in a server, re-invite with
  Send Messages + Read Message History.
- **Critical:** two gateways must never hold the same bot token — they fight over the
  connection and both break. Pick one:
  - **(a) Desktop owns the bot**, laptop talks to it via `hermes peer`. Requires the desktop
    gateway to run the `api_server` platform and be reachable on the LAN.
  - **(b) Laptop owns the bot** — move the token here. Desktop then uses Discord from any device.
- **Recommendation:** (a). The desktop is the always-on machine that holds the schoolwork.
- **Verify:** DM the bot from the phone, get a reply; `hermes gateway status` shows the platform.

### P3 — Link the two machines (`hermes peer`)
- **Why:** lets this laptop hand work to the desktop agent and read its state — the actual
  "pick up where I left off" mechanic for Humber work.
- **Root cause found 2026-09-30:** `API_SERVER_HOST` defaults to `127.0.0.1`
  (`hermes_cli/config_defaults.py:2911-2913`) — **loopback only**. The laptop can never
  connect until the desktop sets `API_SERVER_HOST=0.0.0.0`. Also `API_SERVER_ENABLED=true`
  and an `API_SERVER_KEY` are required (the key is required even on loopback binds).
- **Desktop firewall** will block inbound 8642 by default — needs an explicit allow rule,
  `-Profile Private`.
- **Status:** desktop not reachable during the 2026-09-30 sweep. Live hosts on `10.0.0.0/24`:
  `.4`, `.22`, `.78` — none exposed a Hermes port. Desktop was off or has the API server
  disabled (which is the default).
- **Do:** follow `Docs/Handoffs/DESKTOP_PEER_SETUP_2026-09-30.md` (desktop steps 1–4), then
  from the laptop: `hermes peer add desktop --url http://<desktop-ip>:8642 --key <KEY>`
- **Verify:** `curl -s -m 5 http://<desktop-ip>:8642/v1/models` returns **HTTP 401** (working,
  key required). Connection refused = not running / loopback-bound / firewalled.
  Then `hermes peer dm desktop "status"` returns a reply.

### P4 — Point Hermes at the Humber folder  *(the actual schoolwork sync)*
- **Why:** sessions use `per-directory` strategy, so each course folder gets its own cloud
  memory thread. This is what makes coursework context stick across machines.
- **FOUND 2026-09-30:** the coursework is at
  `P:\OneDrive\Documents\GitHub\GAME259_2025_Winter_B` — Humber GAME259, containing the
  `BTeamProjectTilde` Unreal project (`.uproject`, Source/, Content/, Plugins/).
- **It is already cloud-synced** — `P:\OneDrive` is the OneDrive root (`UserFolder` registry
  value), so it syncs to the desktop automatically. Several files are online-only
  placeholders (0 bytes on disk, Permission denied on read); OneDrive hydrates on access.
- **Done:** Hermes project workspace created —
  `hermes project create "Humber Coursework" ... --use` → slug `humber-coursework`
  (`p_b07acf72`), primary folder the GAME259 path.
- **Note:** the outer `GAME259_2025_Winter_B` folder is not a git repo (`.git` present but
  `git log` says "not a git repository" — likely an online-only `.git`). Hydrate the folder
  in OneDrive before doing git work in it.
- **Verify:** `hermes honcho sessions` shows a per-directory mapping once a session runs there;
  ask a coursework question and get recalled context.

### P5 — SMS  *(low priority, currently dead)*
- **Why not now:** Discord gives the same "chat from anywhere" result for free.
- **State:** `.env` holds placeholders — SID 12 chars (real: 34), token 16 chars (real: 32),
  number `+1234...`. Also `SMS_INSECURE_NO_SIGNATURE=true`, which must be off before any
  public webhook.
- **Do:** real Twilio credentials + a tunnel (`cloudflared`/`ngrok` both installed) if wanted.

### P6 — Housekeeping
- **Stale-module warning persists** — `hermes gateway restart` ran and the gateway is healthy
  (PID 21096, 2 platforms connected), but the "previous update did not restart running
  gateways" notice still prints. State file `.update_check` shows `ver 0.21.3`,
  `head a51143fb` → `target 09681e79`, `behind 8923`. The checkout is 8,923 commits behind the
  published tree; the warning is a version-skew signal, not a live fault. Clear it properly
  with a real `hermes update`, or leave it — it is cosmetic while the gateway runs.
- **AGENTS.md / CLAUDE.md duplicate policy** — both restate the git law and working agreement,
  ~12KB of overlap. Consolidate after P1 lands.
- **Skills Hub** — `hermes skills list` to initialize (currently "directory not initialized").
- **npm vulnerabilities** — browser tools (3), web workspace (9), ui-tui (4) per `hermes doctor`.

---

## 3. Applied 2026-09-30 (already done, no action needed)

| Change | Value | Where |
|--------|-------|-------|
| Memory provider | `honcho` (cloud, OAuth) | `config.yaml` `memory.provider` |
| Honcho workspace / peers | `hermes` · user `Brennan` · AI `hermes` | `honcho.json` |
| Session strategy | `per-directory` | `honcho.json` |
| Recall mode | `hybrid` (auto-inject + tools) | `honcho.json` |
| Melusina persona | installed + active | `config.yaml` `personalities.melusina`, `display.personality` |
| Context file limit | `48000` | `config.yaml` `context_file_max_chars` |
| honcho-ai SDK | 2.5.1 | hermes venv |

Honcho tools now available in chat: `honcho_context`, `honcho_search`, `honcho_profile`,
`honcho_reasoning`, `honcho_conclude`.

---

## 4. Verification standard

A step is done only when it has observable output, not a claim:

- memory → a query returns cloud-stored content
- persona → a reply is in character
- AGENTS.md → `len(open('AGENTS.md').read()) <= 31457` and no `TRUNCATED` warning
- Discord → a DM from the phone gets a reply
- peer → `hermes peer dm desktop "status"` returns
- cap → no `cap` warning on a live query

---

## 5. Open questions for the owner

1. Raise the Nous cap, or add credit? *(blocks P0–P6 testing)*
2. Discord bot: desktop-owned (recommended) or laptop-owned?
3. Humber folder: sync it here, or drive the desktop remotely?
4. Is the desktop's Hermes gateway running, and is it on 10.0.0.4 or 10.0.0.22?
