# Perforce (Helix Core) Setup Guide — MelodiaMelusinaV2

*Written 2026-08-26. **PREP ONLY — Perforce is not live.** Goal: hybrid content locking for a 2-person UE team while GitHub keeps code, docs, and CI.*

**Authority:** [PERFORCE_MIGRATION_PLAN_2026-08-13.md](../PERFORCE_MIGRATION_PLAN_2026-08-13.md) (design) · [PERFORCE_MIGRATION_HANDOFF_2026-08-26.md](../PERFORCE_MIGRATION_HANDOFF_2026-08-26.md) (execution record) · [INTEGRATION_ROADMAP_2026-08-26.md](../INTEGRATION_ROADMAP_2026-08-26.md) (stack)

---

## Why Perforce (hybrid, not all-in)

- Git + LFS cannot enforce exclusive checkout on `.uasset` / `.umap` at this project's scale (see measured findings in the Aug-13 plan).
- Perforce `typemap +l` gives **server-enforced** locks; UE's Perforce provider is first-class.
- **GitHub stays primary** for `Source/`, `Tools/`, `Docs/`, `deploy/`, `Plugins/`, `Config/`, `.github/`, Echo CI, and agent PRs.

**One path, one owner.** Do not submit the same path through Git/LFS and Perforce during transition.

---

## Step 1 — Install Helix Core Server (host PC)

1. Download: https://www.perforce.com/downloads/helix-core-p4d
2. Run installer, accept defaults (Windows service on port **1666**).
3. Record the host machine name for private access (Tailscale IP — see Step 3).

Helix Core Free: 5 users, 20 workspaces — sufficient for this team.

---

## Step 2 — Install P4V on both PCs

Download Helix Visual Client: https://www.perforce.com/downloads/helix-visual-client-p4v

---

## Step 3 — Networking (private overlay only)

**Recommended — Tailscale** (same pattern as [REMOTE_WSL_AGENT_STACK_2026-08-25.md](../PhoneOps/REMOTE_WSL_AGENT_STACK_2026-08-25.md)):

1. Install Tailscale on both PCs: https://tailscale.com/download
2. Join the same tailnet (or shared invite).
3. Use the host PC's **Tailscale IP** as the Perforce server address (`<tailscale-ip>:1666`).

**Do not expose port 1666 to the public internet.** No router port-forward for Perforce unless you explicitly accept that risk (not recommended).

---

## Step 4 — Create depot and seed **content roots only** (hybrid)

In P4V on the host PC:

1. Connect to `localhost:1666`; create an admin user when prompted.
2. Create depot **`//melodia`** (local depot type) — matches [Perforce/typemap.melodia.txt](../../Perforce/typemap.melodia.txt).
3. Create a workspace with a **narrow view** — Perforce roots only, for example:

```text
//melodia/Content/...   //<workspace>/Content/...
//melodia/Exports/...   //<workspace>/Exports/...
//melodia/RawArt/...    //<workspace>/RawArt/...
```

4. **Seed only these trees** from the preserved source checkout (hash-verify before submit):
   - `Content/` — Unreal packages, maps, environment art
   - `Exports/` — Blender stage exports (major LFS cost driver)
   - Raw-art tree on the owner machine (see Aug-13 plan / wardrobe SSOT docs)

5. **Do not** `Mark for Add` / submit any of the following into Perforce — they remain **Git-owned**:

```text
Source/  Tools/  Docs/  deploy/  Plugins/  Config/  specs/  .github/
BS_GodFile.uproject  *.md  *.py  *.json  *.ini  *.ps1
```

6. Before the first binary submit, install the typemap (admin):

```text
p4 typemap -i < Perforce/typemap.melodia.txt
```

Review [Perforce/p4ignore.txt](../../Perforce/p4ignore.txt) and workspace mappings so Git-owned paths never overlap the P4 view.

---

## Step 5 — Connect UE to Perforce (owner sign-off required)

`BS_GodFile.uproject` and `Config/DefaultEngine.ini` are on the never-touch list — **owner only**, after depot seed is verified.

When approved, on each UE workstation:

1. `Edit → Editor Preferences → Source Control`
2. Provider: **Perforce**
3. Server: `<host-tailscale-ip>:1666`
4. Username / workspace: per-user P4 accounts
5. **Accept Settings**

Right-click assets in Content Browser → `Source Control → Check Out` before editing.

---

## Step 6 — Collaborator connects

1. Install P4V + Tailscale on the second PC.
2. Connect P4V to `<host-tailscale-ip>:1666`.
3. Create a **separate workspace** (same depot view pattern; do not share workspace names).
4. Sync content roots; keep a Git clone for code/docs/CI separately or in the same tree with non-overlapping paths.
5. Wire UE Source Control after owner enables the provider.

---

## Preflight (read-only, run before any P4 command)

```powershell
git pull origin main
python Tools/perforce_migration_preflight.py
python Tools/perforce_migration_preflight.py --json
```

Never run from agents or scripts: `git clean`, `git reset --hard`, `git lfs prune`, `p4 reconcile` on Git-owned paths, or `.uproject` edits without owner approval.

---

## Notes

- GitHub remains canonical for code review, Echo gates, and cloud/phone agents.
- Do not run `git clean -fd` — see [_AGENT_WORKING_AGREEMENT.md](../../_AGENT_WORKING_AGREEMENT.md).
- Perforce locking: one editor per locked `.uasset` at a time.
- Acceptance test (from Aug-13 plan P7): clean machine opens `L_KaleidoNave` with no missing refs, following written instructions only.
