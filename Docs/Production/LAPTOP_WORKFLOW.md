# Laptop Workflow Guide — BS_GodFile

> **For:** On-the-go development, Humber Labs, coffee shops, low-memory machines
> **Last Updated:** 2026-09-03
> **Status:** ACTIVE — use when working away from the desktop workstation
> **Prerequisites:** Git for Windows (with LFS), Python 3.11, Blender 5.2 LTS

---

## 1. Clone the Repo on a Laptop

The full repo is ~130GB. You don't need that. Use **sparse checkout** to materialize only the paths you'll actually work with.

### Option A: Sparse Checkout (Recommended)

```bash
# Clone without checking out files first
git clone --no-checkout https://github.com/fromage3900/MelodiaMelusinaV2.git
cd MelodiaMelusinaV2

# Enable sparse checkout (cone mode = faster, pattern-based)
git sparse-checkout init --cone

# Set which paths to materialize
git sparse-checkout set \
  Source \
  Tools \
  Docs \
  specs \
  deploy \
  projects \
  Content/Melodia \
  Content/MelodiaIntegration \
  Plugins/Monolith/Source \
  Plugins/QuillScript/Source \
  INDEX.md UNIVERSITY.md PORTFOLIO.md QUICKSTART.md

# Now checkout — only the above paths appear on disk
git checkout main
```

**Result:** ~10-15GB instead of 130GB.

### Option B: Blob Filter (Skip Large Files Entirely)

```bash
# Clone but skip blobs larger than 1MB — they download only if checked out
git clone --filter=blob:limit=1m https://github.com/fromage3900/MelodiaMelusinaV2.git
cd MelodiaMelusinaV2
git sparse-checkout init --cone
git sparse-checkout set Source Tools Docs Content/Melodia Content/MelodiaIntegration
git checkout main
```

Use this if you're on a metered connection or very small SSD. LFS files won't download until you explicitly `git lfs pull`.

### Option C: Shallow Clone (Latest History Only)

```bash
git clone --depth 1 --no-checkout https://github.com/fromage3900/MelodiaMelusinaV2.git
cd MelodiaMelusinaV2
git sparse-checkout init --cone
git sparse-checkout set Source Tools Docs
git checkout main
```

Use this for quick code review or documentation work. You can't push from a shallow clone without unshallowing first.

---

## 2. Tier 1 vs Tier 2 — What Lives Where

### Tier 1: Desktop Archive (Full 130GB)

The **source of truth**. Lives on the desktop workstation or an external drive. Contains everything:

| Path | Size | Why It's Here |
|------|------|---------------|
| `Content/` (all) | 88GB | Full game content, including EnvSandbox (24G), templates, third-party |
| `Saved/` | 12GB | Generated data, logs, cook output, daemon reports |
| `.git/` (full) | 29GB | Complete history + LFS object cache |
| `Binaries/`, `Intermediate/` | Large | Build artifacts, compiled shaders |
| `CompatibilityLabs/` | Large | Backup snapshots |
| `Imports/` | Varies | Cascadeur inbox, raw mocap sources |

**You do NOT need this on a laptop.**

### Tier 2: Laptop Working Copy (~10-15GB)

Only what you need to actually work:

| Path | Purpose |
|------|---------|
| `Source/` | C++ code (MelodiaIntegration, BS_GodFile) |
| `Tools/` | Python scripts, GN builders, health checks |
| `Docs/` | All documentation, plans, research |
| `Content/Melodia/` | Ship-ready game content (4.8GB) |
| `Content/MelodiaIntegration/` | Configs, allowlists (12MB) |
| `specs/`, `deploy/`, `projects/` | Specs, deployment scripts, project files |
| `Plugins/*/Source/` | Plugin source code (Monolith, QuillScript) |

### What's Excluded from Laptop

| Excluded Path | Size | Reason |
|---------------|------|--------|
| `Content/EnvSandbox/` | 24GB | Test environment, not shippable |
| `Content/_ThirdParty/` | Varies | Stock template, re-downloadable |
| `Content/TurnBasedJRPGTemplate/` | Varies | Stock UE template |
| `Saved/` (most) | 12GB | Generated, regenerable |
| `CompatibilityLabs/` | Varies | Backups |
| `Binaries/`, `Intermediate/`, `DerivedDataCache/` | Large | Build artifacts |
| `Content/Textures/` (raw) | ~200 files | Figma exports, gitignored |

---

## 3. Sync Changes Between Laptop and Desktop

Three strategies, pick based on network availability:

### Strategy A: Git Remote (Preferred — When Network Allows)

```bash
# On laptop: commit and push
git add -A
git commit -m "WIP: [description]"
git push origin feature/<branch-name>

# On desktop: pull and continue
git fetch --all --prune
git checkout feature/<branch-name>
git pull origin feature/<branch-name>
git lfs pull
```

**Golden rule:** Commit before you leave, pull before you start. Every machine switch = commit + push on old, pull + checkout on new.

### Strategy B: Git Bundle (No Network — Sneakernet)

When network is blocked (port 443/22 timeout), use a bundle file on a USB drive:

```bash
# On desktop: create a bundle of your branch
git bundle create BS_GodFile_work.bundle feature/<branch-name>

# Verify the bundle is valid
git bundle verify BS_GodFile_work.bundle

# Copy to USB, then on laptop:
git bundle unbundle BS_GodFile_work.bundle
# Or add as a remote:
git remote add usb /path/to/BS_GodFile_work.bundle
git fetch usb
git merge usb/feature/<branch-name>
```

For incremental updates (only new commits since last sync):

```bash
# On desktop (after initial bundle exists):
git bundle create BS_GodFile_incremental.bundle LAST_SYNC_COMMIT..HEAD

# Tag the sync point
git tag -f last-sync
```

### Strategy C: Patch Files (Small Changes — Email/Discord)

For small changes (docs, configs, a few files):

```bash
# On laptop: create patch from last N commits
git format-patch -3 --stdout > my_changes.patch

# Transfer file (email, Discord, USB), then on desktop:
git am < my_changes.patch
```

Or for uncommitted changes:

```bash
git diff > working_changes.patch
# On desktop:
git apply working_changes.patch
```

### Sync Checklist

- [ ] Commit all changes on the machine you're leaving
- [ ] Push to remote OR create bundle/patch
- [ ] On the arriving machine: pull/unbundle/apply
- [ ] Run `git lfs pull` if LFS files changed
- [ ] Verify: `python Tools/gn_health_check.py` (offline mode)
- [ ] Confirm branch: `git branch -vv`

---

## 4. Git Config for Low-Memory Machines

Laptops and Humber Labs workstations often have limited RAM. Git can be memory-hungry. Tune it:

```bash
# Reduce memory footprint of pack operations
git config --global pack.windowMemory "100m"
git config --global pack.packSizeLimit "100m"
git config --global pack.threads "1"

# Use less memory for delta compression
git config --global core.bigFileThreshold "50m"

# Disable preload index (saves RAM)
git config --global core.preloadIndex false

# Run garbage collection more aggressively
git config --global gc.auto 256
git config --global gc.autoPackLimit 50

# Use the filesystem cache less aggressively
git config --global core.fscache false

# Limit simultaneous pack threads
git config --global pack.deltaCacheSize "50m"

# Speed up status/diff on large repos
git config --global core.untrackedCache true
git config --global core.fsmonitor true
```

### Low-Memory Clone/Fetch

```bash
# Fetch with minimal memory usage
git -c pack.windowMemory=100m -c pack.threads=1 fetch --depth=1

# If OOM during clone, use --depth and unshallow later
git clone --depth 1 --no-checkout https://github.com/fromage3900/MelodiaMelusinaV2.git
cd MelodiaMelusinaV2
git fetch --unshallow  # only when you need full history
```

### When Git Runs Out of Memory

```bash
# Kill stuck git processes
taskkill /F /IM git.exe 2>/dev/null
taskkill /F /IM git-lfs.exe 2>/dev/null

# Clear the index lock if stuck
rm -f .git/index.lock

# Retry with single thread
git -c pack.threads=1 -c pack.windowMemory=50m fetch
```

---

## 5. LFS Partial Clone/Fetch Strategies

LFS is currently **broken** on the remote (404s on fetch for 14,000+ objects). The local `.git/lfs` cache on the desktop has copies, but the server rejects them. Until LFS is fixed, use these strategies:

### Strategy A: Don't Fetch LFS on Laptop

If you don't need the actual asset files (just code/docs):

```bash
# Skip LFS entirely on clone
GIT_LFS_SKIP_SMUDGE=1 git clone --no-checkout https://github.com/fromage3900/MelodiaMelusinaV2.git
cd MelodiaMelusinaV2
git sparse-checkout init --cone
git sparse-checkout set Source Tools Docs
git checkout main
```

LFS pointers stay as small text files. You see the metadata, not the assets.

### Strategy B: Fetch Only Specific LFS Files

```bash
# Fetch only what you need
git lfs fetch --include="Content/Melodia/Characters/Melusina/**" --exclude=""

# Or fetch recent LFS objects only
git lfs fetch --recent
```

### Strategy C: Selective LFS Pull

```bash
# Pull LFS for a specific directory only
git lfs pull --include="Content/Melodia/" --exclude="Content/EnvSandbox/"

# Verify what's been downloaded
git lfs ls-files | head -20
```

### Strategy D: Manual LFS Object Transfer (Desktop → Laptop)

When the LFS remote is broken but the desktop has cached objects:

```bash
# On desktop: find the LFS object files
ls .git/lfs/objects/

# Copy specific objects to laptop via USB
# Place them in .git/lfs/objects/ maintaining the same directory structure
# (first 2 chars / next 2 chars / remaining 36 chars)
```

### LFS Budget Discipline

Current LFS usage: ~9.19 GB of 10 GB metered. Before adding large files:

```bash
# Check current LFS usage
git lfs ls-files | wc -l
git lfs footprint

# See largest LFS objects
git lfs ls-files --size | sort -k2 -h | tail -20
```

**What gets LFS tracking:**
- `.uasset` files (curated, shipped assets only)
- `.umap` files (levels)
- `.fbx` files (imported meshes)
- `.png`/`.exr` textures (shipped only)

**What stays local (gitignored):**
- `Binaries/`, `Intermediate/`, `Saved/` (except `Saved/Audit/`, `Saved/Portfolio/`, `Saved/AnimationReference/`)
- `DerivedDataCache/`
- `Content/Textures/` (raw Figma exports)
- `Exports/` (working exports)

---

## 6. What You CAN Do on a Laptop

### Code (C++ and Python)

- Edit `Source/` C++ files in any text editor or Rider (if installed)
- Edit `Tools/` Python scripts
- Run Python tools that don't need the UE editor:
  ```bash
  python Tools/gn_health_check.py          # GN health check (offline)
  python Tools/bp_sweep.py --help          # Blueprint sweep (needs editor for full)
  python Tools/project_state.py --view integration
  ```
- Write and run unit tests:
  ```bash
  python -m unittest Content.Python.Tests.test_qsc_allowlist_contract
  ```

### Documentation

- Write/edit `Docs/` markdown files
- Update `Docs/Production/` plans and summaries
- Create new documentation (this file is an example)
- Edit `UNIVERSITY.md`, `PORTFOLIO.md`, `INDEX.md`, `QUICKSTART.md`

### Blender Geometry Nodes Work

This is a **primary laptop workflow**. All GN builders run in Blender 5.2 without UE:

```bash
# Run GN health check (offline — no Blender needed)
python Tools/gn_health_check.py

# Run GN health check (live — inside Blender)
# Open Blender → Scripting tab → run:
import subprocess
subprocess.run(["python", "Tools/gn_health_check.py", "--live"])
```

**GN systems you can work on:**
- `deploy/surreal_arch/melodia_gn/` — 60+ surreal architecture builders
- `Tools/BlenderAddons/blender_kawaii_gn/` — Kawaii GN (24 modules)
- `Tools/BlenderAddons/blender_brutalist_gn/` — Brutalist GN (9 modules)
- `Tools/BlenderAddons/melodia_studio/` — MIDI→World pipeline (30 modules)
- `Tools/BlenderAddons/resonant_world_studio/` — Resonant World (5 modules)
- `Tools/BlenderAddons/melodia_aura/` — Melodia Aura (3 modules)
- `Tools/BlenderAddons/melodia_showroom/` — Showroom (9 modules)
- `Tools/BlenderAddons/melodia_stage/` — Stage (4 modules)
- `Tools/BlenderAddons/melodia_pose_audit/` — Pose Audit (4 modules)
- `Tools/BlenderAddons/GenesisCore/` — GenesisCore (31 modules)

### Animation

- Author hand-keyed animations in Blender 5.2
- Use `Templates/Melusina_Animation_Stage.blend` (96KB template)
- Generate new templates: `python Tools/create_animation_template.py`
- Reference library: `Saved/AnimationReference/` (body mechanics, acting, lipsync, walk cycles)
- Edit animation import pipeline docs: `Docs/Production/BLENDER_HANDKEYED_ANIM_IMPORT_PIPELINE_2026-08-22.md`

### Planning and Research

- Write production plans in `Docs/Production/`
- Update research docs in `Docs/Research/`
- Work on portfolio breakdowns in `Docs/Portfolio/`
- Update task ledgers and gate status

### Git Operations

- Commit, branch, merge locally
- Create bundles for offline transfer
- Review history and diffs
- Resolve merge conflicts
- Rebase feature branches

---

## 7. What You CAN'T Do on a Laptop

### No Unreal Engine Editor

The laptop does **not** have UE 5.8. This means:

- **No `.uasset` editing** — you can't open or modify Blueprint assets
- **No PIE (Play In Editor)** — no runtime testing
- **No T3D injection** — `t3d_blueprint_injector.py` needs the editor on :9316
- **No Monolith MCP** — editor-mutating tools won't work
- **No shader compilation** — `.usf`/`.ush` edits can't be tested
- **No cooking/packaging** — `Build.bat` and UAT aren't available
- **No C++ compilation** — no UBT, no Live Coding

### No Mocap Retarget

- **No Rokoko retargeting** — needs the editor + Live Link
- **No VRM4U pipeline** — VRM import needs UE
- **No Cascadeur→UE workflow** — animation export to `.uasset` is editor-bound

### No Big Renders

- **No Path Tracer** — hardware ray tracing needs a GPU you don't have
- **No movie render queue** — editor-only feature
- **No Niagara simulation** — GPU particle systems need the editor
- **No Substrate materials** — the new UE 5 material system needs compilation

### No Editor-Dependent Tools

These tools **will not run** on the laptop:

| Tool | Why It Fails |
|------|--------------|
| `t3d_blueprint_injector.py` | Needs editor on :9316 |
| `bp_regression_checker.py` | Needs editor for fingerprint |
| `pie_smoke_runner.py` | Needs PIE |
| `nl_to_blueprint.py` | Needs T3D injection |
| `t3d_material_curve_injector.py` | Needs Monolith |
| `bp_live_path.py` | Needs editor for runtime check |
| `continuous_loop.py` | Needs editor for fix-verify |

---

## 8. Test GN Changes Without the UE Editor

You can fully validate Geometry Nodes changes on a laptop using Blender 5.2.

### Step 1: Offline Health Check (No Blender Needed)

```bash
# From repo root
python Tools/gn_health_check.py
```

This checks:
- Every GN module imports without errors
- `__init__.py` files exist with proper `bl_info` + `register`
- Registries are populated (KAWAII_GN_REGISTRY, etc.)
- Build functions exist

Output: `Saved/Audit/gn_health_report_YYYY-MM-DD.json`

### Step 2: Live Health Check (Inside Blender)

Open Blender 5.2 → Scripting tab → New text block → paste:

```python
import subprocess
import sys
import os

repo = r"C:\EnvironmentPortfolio\BS_GodFile"  # adjust path
os.chdir(repo)
result = subprocess.run(
    [sys.executable, "Tools/gn_health_check.py", "--live"],
    capture_output=True, text=True
)
print(result.stdout)
if result.stderr:
    print("STDERR:", result.stderr)
```

Or run from Blender's Python console:

```python
import sys
sys.path.insert(0, r"C:\EnvironmentPortfolio\BS_GodFile")
exec(open(r"C:\EnvironmentPortfolio\BS_GodFile\Tools\gn_health_check.py").read())
```

### Step 3: Manual GN Testing in Blender

For each GN system you modified:

1. Open Blender 5.2
2. Enable the addon: Edit → Preferences → Add-ons → search for the GN system
3. Open a new Geometry Nodes workspace
4. Add the node group you modified
5. Verify it builds without errors
6. Check the output mesh/geometry
7. Adjust parameters to test edge cases

### Step 4: Verify Import Chain

```python
# Test that a specific GN builder imports and runs
import sys
sys.path.insert(0, r"C:\EnvironmentPortfolio\BS_GodFile\Tools\BlenderAddons\melodia_studio")

import importlib
mod = importlib.import_module("melodia_studio")
print("Registry:", getattr(mod, "MELODIA_GN_REGISTRY", "not found"))
```

### Step 5: Run Related Unit Tests

```bash
# If the GN system has tests
python -m unittest Content.Python.Tests.test_<system_name>

# Or run all tests
python -m unittest discover -s Content/Python/Tests -p "test_*.py"
```

### GN Testing Checklist

- [ ] `python Tools/gn_health_check.py` passes (0 errors)
- [ ] Modified GN module imports in Blender without errors
- [ ] Node group builds and produces expected geometry
- [ ] No console errors in Blender's System Console
- [ ] Existing builders still work (regression check)
- [ ] `__init__.py` has valid `bl_info` and `register`/`unregister`
- [ ] New files are tracked by git (`git status`)

---

## 9. Commit and Push When Network Allows

### Local Commit Workflow

```bash
# 1. Check what changed
git status
git diff --stat

# 2. Stage changes
git add -A                    # everything
# OR
git add Source/MyFile.cpp     # specific files

# 3. Commit with a meaningful message
git commit -m "feat(gn): add new castle builder with parametric towers"

# 4. Verify
git log --oneline -5
git status
```

### Commit Message Format

```
<type>(<scope>): <description>

Types:
  feat     — new feature (new GN builder, new tool, new doc)
  fix      — bug fix
  docs     — documentation only
  chore    — maintenance (gitignore, __init__.py, etc.)
  refactor — code change that neither fixes nor adds
  test     — adding tests
  perf     — performance improvement

Examples:
  feat(gn): add sakura tree builder to Kawaii GN
  fix(hook): allow Saved/AnimationReference/*.md in pre-commit
  docs(production): add laptop workflow guide
  chore(git): track new animation tools
```

### Push When Network Restores

```bash
# Check if network is back
git fetch origin

# If fetch succeeds, push
git push origin main

# If on a feature branch
git push origin feature/<branch-name>

# If push rejected (divergent remote)
git pull --rebase origin main
git push origin main
```

### If HTTPS Fails, Try SSH

```bash
git remote set-url origin git@github.com:fromage3900/MelodiaMelusinaV2.git
git push origin main
```

### Push Queue (When Network is Blocked)

Currently **8 commits ahead of origin/main** (as of 2026-09-03). When network restores:

```bash
# Push all at once
git push origin main

# Or push specific commits
git push origin d6cd9e03:main
```

### Offline Commit Discipline

Even without network, **commit frequently**:

```bash
# Commit every logical unit of work
git add Docs/Production/LAPTOP_WORKFLOW.md
git commit -m "docs(production): add laptop workflow guide"

# Commit WIP before switching machines
git add -A
git commit -m "WIP: halfway through GN castle refactor"

# Amend if you forgot something
git add Tools/forgotten_file.py
git commit --amend --no-edit
```

### Pre-Commit Hook Notes

The repo has a pre-commit hook that:
- Blocks files larger than 50MB (unless LFS-tracked)
- Blocks `Saved/` paths (except `Saved/Audit/`, `Saved/Portfolio/`, `Saved/AnimationReference/`)
- Blocks `Content/Textures/` (gitignored)

If the hook blocks your commit:

```bash
# See what the hook is complaining about
git commit -v

# If it's a false positive, fix the issue
# (track with LFS, move to allowed path, etc.)

# NEVER bypass with --no-verify unless you're certain
```

---

## Quick Reference Card

| Task | Command |
|------|---------|
| Clone (sparse) | `git clone --no-checkout <url>` → `git sparse-checkout init --cone` → `git sparse-checkout set ...` → `git checkout main` |
| Clone (no LFS) | `GIT_LFS_SKIP_SMUDGE=1 git clone --no-checkout <url>` |
| Check sparse paths | `git sparse-checkout list` |
| Add sparse path | `git sparse-checkout add <path>` |
| Disable sparse | `git sparse-checkout disable` |
| Create bundle | `git bundle create <file> <branch>` |
| Unbundle | `git bundle unbundle <file>` |
| Create patch | `git format-patch -N --stdout > patch` |
| Apply patch | `git am < patch` |
| GN health check | `python Tools/gn_health_check.py` |
| GN health (live) | `python Tools/gn_health_check.py --live` |
| Low-mem fetch | `git -c pack.threads=1 -c pack.windowMemory=50m fetch` |
| LFS skip | `GIT_LFS_SKIP_SMUDGE=1 git clone ...` |
| LFS selective | `git lfs pull --include="Content/Melodia/"` |
| Check LFS usage | `git lfs footprint` |
| Kill stuck git | `taskkill /F /IM git.exe` |

---

## Troubleshooting

| Symptom | Cause | Fix |
|---------|-------|-----|
| "fatal: not a git repository" | Wrong directory | `cd C:\EnvironmentPortfolio\BS_GodFile` |
| "sparse checkout" errors | Not initialized | `git sparse-checkout init --cone` |
| "LFS object not found" | LFS remote broken | `GIT_LFS_SKIP_SMUDGE=1` or copy from desktop |
| "Out of memory" during git | Too many threads | `git -c pack.threads=1 -c pack.windowMemory=50m fetch` |
| "Push rejected: non-ff" | Divergent remote | `git pull --rebase origin main` |
| "index.lock exists" | Stuck git process | `taskkill /F /IM git.exe; rm -f .git/index.lock` |
| "Large file blocked" | Pre-commit hook | Track with LFS or move to allowed path |
| "Module not found" in GN | Missing `__init__.py` | Create with `bl_info` + `register` |
| GN health check fails | Import error | Read `Saved/Audit/gn_health_report_*.json` |

---

*This guide is part of the BS_GodFile infrastructure plan. See also:*
- *[LONG_TERM_INFRASTRUCTURE_PLAN.md](LONG_TERM_INFRASTRUCTURE_PLAN.md) — full infrastructure plan*
- *[GIT_STATE_2026-09-03.md](GIT_STATE_2026-09-03.md) — current git state and push queue*
- *[CROSS_MACHINE_WORKFLOW_2026-09-02.md](CROSS_MACHINE_WORKFLOW_2026-09-02.md) — cross-machine development workflow*
- *[CHARACTER_ANIMATION_2_SEMESTER_PLAN.md](CHARACTER_ANIMATION_2_SEMESTER_PLAN.md) — animation production plan*
- *[GEOMETRY_NODES_COMPLETE_REFERENCE.md](../../Research/GEOMETRY_NODES_COMPLETE_REFERENCE.md) — GN system reference*
