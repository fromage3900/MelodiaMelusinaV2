# Hermes cross-device sync — desktop handoff (2026-10-01)

**For:** the agent running on Brennan's **desktop PC** (canonical `origin/main` machine).
**From:** the laptop session, `P:\MelodiaMelusinaV2-Laptop`.
**Read this before doing anything.** It contains the exact steps to finish the link, and the
verified state of the laptop side so you do not have to re-derive it.

---

## 1. What was actually broken (and is now fixed)

The owner's complaint was *"my Hermes setup isn't syncing properly."* The root cause was **not**
sync. It was this:

```
model.default = upstage/solar-pro4:free   ->  HTTP 400: Model is unavailable
```

`upstage/solar-pro4:free` **no longer exists** in the Nous catalog. The catalog (426 models,
fetched live 2026-10-01) offers `upstage/solar-pro4` (paid), `upstage/solar-pro-3`,
`upstage/solar-mini4` — there is no `:free` variant any more. Every session died mid-run, tools
did not fire, and context looked stale. That *presents* as a sync bug and is not one.

**Fixed on the laptop:** `model.default = meituan/longcat-2.5-preview:free`, verified live.

**Check this on the desktop first.** If the desktop is also pinned to a retired model, it will
fail the same way and you will misdiagnose it as sync:

```bash
hermes config get model.default
curl -s https://inference-api.nousresearch.com/v1/models \
  -H "Authorization: Bearer $NOUS_API_KEY" | grep -o '"id":"[^"]*"' | grep -i solar
```

Only **7 free models** remain. Any of them can be retired the same way. See §5.

---

## 2. What already works — do not rebuild it

**Honcho cloud memory is live and proven end-to-end.** No LAN, no IP, no firewall involved.
It travels over the internet.

Proven on the laptop 2026-10-01:

1. Wrote a real coursework fact to the Honcho workspace.
2. Started a **fresh** session in the Humber directory.
3. Asked it from memory only, no tools.
4. It returned `P:\OneDrive\Documents\GitHub\GAME259_2025_Winter_B` unprompted.

Cloud workspace state at time of writing:

```
workspace: hermes
peers:     Brennan, hermes
sessions:  hermes (0 msgs)
           hermes-sync-selftest (2 msgs)
           MelodiaMelusinaV2-Laptop (12 msgs)
           GAME259_2025_Winter_B (5 msgs)
```

**Per-directory memory works.** Running a session inside a folder creates a cloud session named
after that folder (`session_strat: per-directory`). Each course folder gets its own thread
automatically. This is the mechanism that makes coursework context follow the owner.

**The coursework is already cloud-synced.** `P:\OneDrive` is the OneDrive root
(`Documents\GitHub\GAME259_2025_Winter_B`). The desktop sees the same folder through OneDrive.
Nothing to move, nothing to copy.

---

## 3. What the desktop must do

### 3a. Join the same Honcho account  *(this is the whole sync story)*

```bash
hermes honcho status
```

- If it shows `Provider: honcho` with peers `Brennan` / `hermes` — **already done**, skip to §3b.
- If not:

```bash
hermes memory setup honcho
```

Choose **cloud**, then the device-login flow. Same account as the laptop. That is the entire
requirement for notes/planning/session context to follow the owner between machines.

**Verify:**

```bash
hermes honcho status
```

Expect `Workspace: hermes`, `User peer: Brennan`, `AI peer: hermes`, `Session strat:
per-directory`.

### 3b. The LAN peer link  *(optional — only needed for live desktop<->laptop control)*

This is **not** required for memory sync. It is a separate, lower-value capability. Two
independent defaults block it, and both must be fixed:

**Blocker 1 — the API server binds to loopback by default.**

`hermes_cli/config_defaults.py:2911-2913`:

```
"API_SERVER_HOST": _msg(
    "Host/bind address for the API server (default: 127.0.0.1). API_SERVER_KEY is still "
    "required even on loopback binds.", ...)
```

So nothing is reachable off-box until the desktop sets `0.0.0.0` explicitly.

**Blocker 2 — the iPhone hotspot is classified as a Public network.**

Windows blocks all inbound on Public. Probed on the desktop `172.20.10.8`:
ports **445, 3389, 135, 8642 — all filtered.** 445/3389/135 are the three Windows always has
open on a Private network, so all three being filtered is the tell.

**Desktop steps (admin PowerShell):**

```powershell
# 1. make the hotspot a Private network
Get-NetConnectionProfile
Set-NetConnectionProfile -InterfaceAlias "Wi-Fi" -NetworkCategory Private

# 2. firewall rule
New-NetFirewallRule -DisplayName "Hermes API Server" -Direction Inbound `
  -Protocol TCP -LocalPort 8642 -Action Allow -Profile Private
```

**Then in `C:\Users\<you>\AppData\Local\hermes\.env`:**

```
API_SERVER_ENABLED=true
API_SERVER_KEY=<openssl rand -hex 32>
API_SERVER_HOST=0.0.0.0
API_SERVER_PORT=8642
```

`API_SERVER_KEY` is mandatory whenever the server is enabled — **the server refuses to start
without it**, and it must be >= 16 chars.

```bash
hermes gateway restart
```

Expect: `[API Server] API server listening on http://0.0.0.0:8642`

**Verify from the laptop:**

```bash
curl -s http://172.20.10.8:8642/v1/models -H "Authorization: Bearer <key>"
```

### 3c. The laptop side is ALREADY DONE

For the record, so you do not duplicate it. The laptop has:

```
API_SERVER_ENABLED=true
API_SERVER_KEY=<set, 64 hex chars>
API_SERVER_HOST=0.0.0.0
API_SERVER_PORT=8642
```

and is confirmed listening:

```
TCP    0.0.0.0:8642    0.0.0.0:0    LISTENING
```

Laptop address on the hotspot: **172.20.10.2**. Desktop: **172.20.10.8**.

---

## 4. Network facts (they will change — read this before debugging)

The owner runs both machines on an **iPhone personal hotspot**. That has consequences:

- Subnet is `172.20.10.0/28` — only `.1` through `.14` are usable.
- Addresses are **DHCP and will change**. `.8` today, something else tomorrow.
- The hotspot **disappears entirely** when the phone's hotspot is switched off.
- The earlier `10.0.0.0/24` sweep in the status doc was the **home WiFi**, a different network.
  Do not reuse those addresses.

**Do not build anything durable on these addresses.** For a reliable peer link the owner needs
the home WiFi with a DHCP reservation or static address for the desktop.

Desktop identity for future scans: MAC `1c-ce-51-95-d4-64` (real OUI, AzureWave WiFi adapter),
TTL 128 (Windows). Every other live host on the hotspot had a **randomized MAC** — those are
phones, not the desktop.

---

## 5. Known open items

| # | Item | State |
|---|------|-------|
| P0 | Nous Portal spend cap at **$22.00 / $22.00** | Owner adding credits. Blocks heavy work. |
| P7 | Only **7 free models** remain; any can be retired like `solar-pro4:free` | Configure a fallback chain: `hermes fallback add` |
| P1 | `AGENTS.md` was truncating (43,777 chars vs 31,457 limit, 28% dropped per session) | Trim staged at `AGENTS.md.new` (29,795 chars) — **not yet installed** |
| P2 | `hermes sync` (skills cloud) | **Unavailable** — `feature_enabled: false` server-side for this account. Do not plan around it. |
| P3 | LAN peer link | Laptop done; desktop blocked on §3b |
| — | SMS send | Twilio 401, placeholder creds in `.env`. Not functional. |

**The 7 remaining free models** (as of 2026-10-01):

```
inclusionai/ling-3.0-flash-sante:free
poolside/laguna-s-2.1:free
poolside/laguna-xs-2.1:free
meituan/longcat-2.0:free
inclusionai/ling-3.0-flash-fin:free
stepfun/step-3.7-flash:free
meituan/longcat-2.5-preview:free     <- currently pinned on the laptop
```

---

## 6. Git state — read before committing

Per the **GIT PIPELINE LAW** at the top of `AGENTS.md` (owner directive 2026-09-06):

- Canonical authority is `origin/main`, maintained on the **desktop**.
- The laptop is a Blender/asset-prep hub. Its local `main` must mirror `origin/main` exactly.
- No branch creation, commit, merge, rebase, reset or push without **explicit owner permission
  per operation plus a written plan stated first**.

At time of writing the laptop is on `collab/laptop/brooch-sky-20260917` with **77 staged and
100 modified files that are NOT part of this work** (brooch-sky asset work). This handoff was
committed **scoped to its own files only** — those 177 files were deliberately left untouched.

**The desktop agent will not see this document until it reaches `origin/main`.** Committing to
`collab/laptop/brooch-sky-20260917` does not make it visible to you. Someone must merge
desktop-side. If you are reading this, that merge already happened.

---

## 7. One-paragraph summary

Memory sync works and needs nothing but the desktop signing into the same Honcho account. The
"not syncing" symptom was a retired default model (`upstage/solar-pro4:free`), now replaced.
The LAN peer link is optional, blocked by a loopback bind default plus a Public-network
firewall classification on an iPhone hotspot, and is not worth hardening until the machines
sit on stable addresses. The coursework already lives in OneDrive. The only genuine blockers
are the spend cap and the fact that free models keep getting retired.
