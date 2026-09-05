# Cross-Machine Development Workflow — BS_GodFile

**Authoritative for:** PC (froma), Laptop, Humber Labs
**Last Updated:** 2026-09-02
**Status:** ACTIVE — implement before next machine switch

---

## 1. The Problem

You work across three machines:
- **Desktop PC (froma)** — primary authoring station, Windows 11, all tools installed
- **Laptop** — on-the-go, Humber Labs, coffee shops
- **Humber Labs** — college workstations, shared, fresh OS images

Without discipline, you'll hit:
- "Works on my machine" — missing plugins, wrong paths, stale assets
- Lost work — unsaved changes left on a machine you're not at
- Merge hell — divergent branches from autonomous hot loops
- LFS budget blowout — 10 GB metered, large files duplicated
- Editor crashes — stale DLLs, wrong Python version, missing modules

This document prevents that.

---

## 2. Golden Rules

### Rule 1: Git is the single source of truth
Everything that matters is in Git. If it's not committed, it doesn't exist. No exceptions.

### Rule 2: One branch per feature, never work on main directly
Main is sacred. Feature branches only. Merge via PR with CI green.

### Rule 3: Commit before you leave, pull before you start
Every machine switch = commit + push on old machine, pull + checkout on new machine.

### Rule 4: No autonomous work on shared machines
Hot loops, daemons, and cron jobs only run on your primary PC. Laptop and Humber Labs are pull-and-work only.

### Rule 5: LFS is metered — track only what ships
Bulk raw art stays local. Only curated `.uasset` files get LFS tracking.

---

## 3. Machine Setup Checklist

### Fresh Machine (Laptop / Humber Labs)

```powershell
# 1. Install prerequisites
#    - Git for Windows (with LFS)
#    - GitHub CLI (gh)
#    - Python 3.11 (NOT 3.14 — UE 5.8 uses 3.11)
#    - Unreal Engine 5.8
#    - Blender 5.2 LTS
#    - JetBrains Rider (for C++)

# 2. Clone
git clone https://github.com/fromage3900/MelodiaMelusinaV2.git
cd MelodiaMelusinaV2

# 3. Pull LFS assets
git lfs pull

# 4. Install Python deps
python -m pip install -r requirements.txt  # if exists
pip install onnx onnxruntime numpy pillow

# 5. Verify
python -m unittest discover -s Content/Python/Tests -p "test_*.py" 2>&1 | tail -3
```

### Primary PC (froma) — Already Set Up

- All tools installed
- All plugins configured
- Cron jobs running (hot loop, daemons)
- Monolith MCP on :9316

---

## 4. Machine Switch Protocol

### Leaving a Machine
```powershell
# 1. Save all editor work
# 2. Commit everything
git add -A
git commit -m "WIP: [description of work in progress]"
git push origin feature/<branch-name>

# 3. Note the branch name
echo "On branch: feature/<branch-name>"
```

### Arriving at a Machine
```powershell
# 1. Fetch latest
git fetch --all --prune

# 2. Checkout your branch
git checkout feature/<branch-name>
git pull origin feature/<branch-name>

# 3. Pull LFS assets
git lfs pull

# 4. Verify
python -m unittest discover -s Content/Python/Tests -p "test_*.py" 2>&1 | tail -3

# 5. Open editor
start BS_GodFile.uproject
```

---

## 5. Path Handling

All paths in code and docs use one of these forms:

| Form | Example | Use When |
|---|---|---|
| MSYS path (native) | `C:/EnvironmentPortfolio/BS_GodFile` | Git bash, Python, shell |
| Windows path | `C:\EnvironmentPortfolio\BS_GodFile` | Windows Explorer, some UE dialogs |
| UE path | `/Game/Melodia/...` | Unreal asset references |

**Never hardcode user-specific paths.** Use environment variables:
- `$HOME` or `~` for user home
- `$LOCALAPPDATA/Temp` for scratch files
- `git rev-parse --show-toplevel` for repo root

---

## 6. LFS Discipline

### What gets LFS tracking:
- `.uasset` files (curated, shipped assets)
- `.umap` files (levels)
- `.fbx` files (imported meshes)
- `.png`/`.exr` textures (shipped only)

### What stays local (gitignored):
- `Binaries/`, `Intermediate/`, `Saved/` (except `Saved/Audit/`, `Saved/Portfolio/`)
- `DerivedDataCache/`
- `Content/Textures/` (raw Figma exports — ~200 files)
- `Exports/` (working exports — ship to Helix Core or cold archive)

### LFS budget: 10 GB metered
Current usage: ~9.19 GB
Before adding large files: `git lfs ls-files | wc -l` and `git lfs footprint`

---

## 7. Editor Safety

### Single Editor Rule
Only ONE UnrealEditor instance per project. Check before opening:
```powershell
tasklist | grep UnrealEditor
```

### Python Version
UE 5.8 uses Python 3.11. Do NOT use Python 3.14 for editor scripts.
```powershell
# Check which Python UE will use
& "C:\Program Files\Epic Games\UE_5.8\Engine\Binaries\ThirdParty\Python3\Win64\python.exe" --version
```

### Plugin Dependencies
All 16 project plugins must be present. Check `.uproject` file for list.
Missing plugins = crash on load.

---

## 8. Cron Job Policy

### Runs on Primary PC only:
- `melodia-8h-hot-loop` (paused — do not re-enable on shared machines)
- `copernicus-pipeline-expand`
- `copernicus-session-saver`
- `universal-garment-loom-8h`

### Safe to run anywhere (read-only):
- `bsgodfile-git-health` (3am daily)
- `bsgodfile-recruiter-packet` (4am daily)
- `qwen-daemon-reader` (daytime)
- `qwen-daemon-overnight` (2am)

### Never run on shared machines:
- Anything that mutates the editor
- Anything that commits/pushes
- Anything that creates LFS objects

---

## 9. Backup Strategy

### Git Remote (GitHub)
- Code, configs, tools, specs, docs — all tracked
- LFS for curated assets
- Push at every machine switch

### Helix Core (Pilot)
- `Exports/` depot path (change 2, 50 files)
- Binary art that doesn't fit LFS budget
- Final cutover pending sign-off

### AWS Glacier
- Started 2026-08-13
- Long-term cold archive

### Local Backups
- `CompatibilityLabs/ProductionPreIntegrationBackup_2026-07-26`
- `Saved/Recovery/`
- Per-asset `_OLD` variants

---

## 10. Troubleshooting

| Symptom | Cause | Fix |
|---|---|---|
| "Large files not tracked by LFS" | Pre-commit hook | `git lfs track "<pattern>" && git add <file>` |
| "Unable to create index.lock" | Stuck git process | `taskkill /F /IM git.exe; rm -f .git/index.lock` |
| "Live coding failed" | New UFUNCTION/UPROPERTY | Full closed-editor UBT rebuild |
| "Module not found" | Missing plugin | Check `.uproject` plugin list |
| "Python version mismatch" | Using 3.14 instead of 3.11 | Use UE's bundled Python |
| "Push rejected: non-ff" | Divergent remote | `git pull --rebase origin main` or push to feature branch |
| "LFS budget exceeded" | Too many large files | Purge with `git filter-repo`, re-track only shipped assets |

---

*Melodia © 2026. Cross-machine stability is not optional — it's how you survive final year.*