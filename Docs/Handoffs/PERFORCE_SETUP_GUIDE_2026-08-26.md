# Perforce (Helix Core) Setup Guide — MelodiaMelusinaV2
*Written 2026-08-26. Goal: move 2-person active UE dev team from Git to Perforce for proper binary asset locking.*

---

## Why Perforce

- Git + LFS is painful for UE at this project's scale (3.6GB+ binaries, `Content/*` gitignored)
- Perforce handles binary file locking natively — no `.uasset` merge conflicts
- UE Source Control panel integrates with Perforce out of the box
- Free tier: 5 users, unlimited storage (self-hosted)

---

## Step 1 — Install Helix Core Server (host PC)

1. Download: https://www.perforce.com/downloads/helix-core-p4d
2. Run installer, accept defaults (installs as a Windows service on port 1666)
3. Note your machine's local IP (`ipconfig` → IPv4 address)

---

## Step 2 — Install P4V on Both PCs

Download Helix Visual Client: https://www.perforce.com/downloads/helix-visual-client-p4v

---

## Step 3 — Networking (pick one)

**Option A — Tailscale (recommended, no router config needed)**
1. Install Tailscale on both PCs: https://tailscale.com/download
2. Sign in with the same account (or share the network)
3. Use the Tailscale IP of the host PC as the Perforce server address

**Option B — Port forward**
1. Forward port `1666` (TCP) on your router to the host PC's local IP
2. Use your public IP as the server address for the friend

---

## Step 4 — Create Depot and Import Project

In P4V on the host PC:
1. Connect to `localhost:1666`, create an admin user when prompted
2. Create a new depot: `Connection → Open Connection → Admin → Depots → New Depot`
   - Depot name: `MelodiaMelusinaV2`
   - Type: `local`
3. Create a workspace mapping the depot to your project folder
4. Add all project files: select folder → `Mark for Add` → `Submit`

---

## Step 5 — Connect UE to Perforce

In Unreal Editor on both PCs:
1. `Edit → Editor Preferences → Source Control`
2. Provider: **Perforce**
3. Server: `<host-tailscale-ip>:1666`
4. Username: your P4 username
5. Workspace: your workspace name
6. Click **Accept Settings**

From now on, right-click any asset in the Content Browser → `Source Control → Check Out` before editing.

---

## Step 6 — Friend Connects

1. Install P4V
2. Install Tailscale, join same network
3. Connect P4V to `<host-tailscale-ip>:1666`
4. Create a workspace pointing to their local project folder
5. Sync to get all files
6. Connect UE Source Control as above

---

## Notes

- The existing Git repo (GitHub) can remain as a code-only backup (`Source/`, `Config/`, `Plugins/`, `Docs/`)
- Do not run `git clean -fd` — see `_AGENT_WORKING_AGREEMENT.md` for why this is catastrophic
- Perforce file locking means only one person edits a `.uasset` at a time — always check out before editing
