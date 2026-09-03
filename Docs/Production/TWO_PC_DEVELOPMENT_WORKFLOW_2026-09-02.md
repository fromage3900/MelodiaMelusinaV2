# Melodia — Two-PC Development Workflow Plan

**Date:** 2026-09-02
**Status:** IMPLEMENTATION-READY
**Machines:**
- Main PC: Desktop workstation (full UE editor, rendering, lookdev)
- Laptop: Acer Nitro AN515-51, i5-7300HQ, 16 GB RAM, GTX 1050 Ti — `LAPTOP-Q8S5OSQ2`

---

## 1. The Three Creative Workflow Lanes

This plan gives you three distinct ways to work across machines — pick the lane that matches your current task. They are not mutually exclusive; you can switch between them within a single session.

---

## 2. Lane A — JetBrains Gateway (Laptop as Remote IDE Backend)

**Concept:** Run Rider's IDE backend on the laptop. Your main PC runs a thin JetBrains Client that connects over SSH. You get full Rider intelligence (Code Vision, Unreal IWYU, Blueprint reflection, shader editing) without installing UE on the main PC for code work.

**Why this is creative:** The laptop becomes a "headless brain" for C++ code navigation. You sit at your main PC with its superior display/peripherals, but all compilation and indexing happens on the laptop's clone. The main PC is just a window into the laptop's Rider.

### Architecture

```
Main PC (display)                    Laptop (compute)
┌──────────────────┐     SSH      ┌──────────────────────┐
│ JetBrains Client │◄────────────►│ JetBrains Rider      │
│ (thin UI)        │   port 22    │ (full backend)       │
│                  │              │ ┌──────────────────┐ │
│ You type here    │              │ │ Unreal C++ src   │ │
│ Results render   │              │ │ Git repo clone   │ │
│ here             │              │ │ Compiler toolchn │ │
└──────────────────┘              │ └──────────────────┘ │
                                  └──────────────────────┘
```

### Setup Steps

1. **Enable OpenSSH Server on the laptop:**
   ```powershell
   # PowerShell (Admin) on laptop
   Add-WindowsCapability -Online -Name OpenSSH.Server~~~~0.0.1.0
   Set-Service -Name sshd -StartupType Automatic
   Start-Service sshd
   New-NetFirewallRule -Name "OpenSSH" -DisplayName "OpenSSH" -Enabled True -Direction Inbound -Protocol TCP -Action Allow -LocalPort 22
   ```

2. **Install JetBrains Gateway on the main PC:**
   - Download from https://www.jetbrains.com/remote-development/gateway/
   - Or use Toolbox App → Gateway

3. **Configure the connection:**
   - Open Gateway → "New Connection" → SSH
   - Host: laptop's LAN IP (e.g., `192.168.1.x`)
   - Port: `22`
   - User: your laptop username
   - Auth: key pair (recommended) or password

4. **Select the IDE and project:**
   - Choose JetBrains Rider
   - Point to `P:\MelodiaMelusinaV2-Laptop\BS_GodFile.uproject`
   - Gateway downloads the Rider backend onto the laptop

5. **Working:**
   - You code on the main PC. Indexing, compilation, code analysis run on the laptop.
   - The laptop doesn't need a monitor (headless via SSH).
   - Blueprints/PIE still require the laptop's UE to run (see Lane C for offloading builds).

### When to use Lane A
- C++ refactoring across the whole codebase
- Code reviews with Code Vision lenses
- Header/include cleanup (IWYU)
- Shader authoring in Rider
- Any task where you want full IDE power but the laptop is the source of truth

### Constraints
- The laptop must be on and on the same network.
- Gateway needs to download the Rider backend once (~300 MB).
- PIE/debugging still requires the laptop's UE editor to be running (or you trigger builds from the main PC and view results).

---

## 3. Lane B — VS Code Remote SSH (Lightweight Scripts & Docs)

**Concept:** For lighter tasks — Python, PowerShell, JSON, Markdown, Three.js, docs — use VS Code Remote SSH. Much faster to connect than Gateway, uses fewer laptop resources.

### Setup

1. **VS Code on main PC:** Install the "Remote - SSH" extension.
2. **Connect:** `F1` → "Remote-SSH: Connect to Host" → `user@laptop-ip`
3. **Open folder:** `P:\MelodiaMelusinaV2-Laptop`

### When to use Lane B
- Python contract tests (`run_tests.ps1` prep)
- PowerShell deployment scripts
- Three.js / web prototype work
- JSON spec authoring
- Quick log inspection
- Any task where full Rider is overkill

### Constraints
- No UE C++ intelligence (use Lane A for that).
- No Blueprint editing.

---

## 4. Lane C — UBA (Unreal Build Accelerator) Distributed Compilation

**Concept:** When you trigger a C++ build on the main PC, UBA offloads individual compile jobs to the laptop. Both machines must have the repo, UE, and VS toolchain installed. UBA handles the distribution transparently.

### Why this is creative
Your 16 GB laptop becomes a compile worker. A build that takes 10 minutes on one machine can drop to 6 minutes with two. The laptop's 4-core i5 isn't fast, but it's free parallelism.

### Setup

Both machines need:
- Same version of Unreal Engine 5.8
- Same version of Visual Studio 2022 with matching workloads (import `.vsconfig`)
- The Melodia repo cloned and LFS-hydrated

**On both machines**, install the same UE 5.8 and VS 2022 toolchain (import `.vsconfig`).

**On the laptop**, the UBA executor must be actively running to accept compile jobs from the main PC. The laptop does NOT auto-register just because UBA is enabled on the main PC — the executor process must be started.

**BuildConfiguration.xml location:**
- `%LOCALAPPDATA%\UnrealBuildAccelerator\BuildConfiguration.xml` (per-user)
- Or `Engine\Programs\UnrealBuildAccelerator\BuildConfiguration.xml` (per-engine)

**On the main PC**, configure `BuildConfiguration.xml`:

```xml
<?xml version="1.0" encoding="utf-8" ?>
<Configuration xmlns="https://www.unrealengine.com/BuildConfiguration">
    <BuildConfiguration>
        <bAllowUBAExecutor>true</bAllowUBAExecutor>
    </BuildConfiguration>
    <UnrealBuildAccelerator>
        <bLaunchVisualizer>true</bLaunchVisualizer>
    </UnrealBuildAccelerator>
</Configuration>
```

**On the laptop**, also create `BuildConfiguration.xml` with the executor enabled so it can accept remote jobs:

```xml
<?xml version="1.0" encoding="utf-8" ?>
<Configuration xmlns="https://www.unrealengine.com/BuildConfiguration">
    <BuildConfiguration>
        <bAllowUBAExecutor>true</bAllowUBAExecutor>
    </BuildConfiguration>
</Configuration>
```

Once both machines have UBA configured and the executor is running on the laptop, compile jobs are distributed automatically — no separate Horde server needed for two machines.

### When to use Lane C
- Full C++ rebuilds after header changes
- Plugin compilation
- Any build where `-MaxParallelActions` would help

### Constraints
- Both machines must have the toolchain.
- First build populates UBA's file cache — subsequent builds are faster.
- Laptop's 16 GB limits how many parallel actions it can handle (start with 1, scale to 2 if stable).
- Network: gigabit LAN preferred; Wi-Fi works but slower.

---

## 5. Lane D — Git Branch Handoff Protocol

**Concept:** The laptop is a full clone. Work happens on a `collab/laptop/<task>` branch. When done, push to origin. Main PC fetches and fast-forwards `main`. Binary assets use LFS locks to prevent conflicts.

### Protocol

**Start a laptop task:**
```bash
cd P:/MelodiaMelusinaV2-Laptop
git switch main
git pull --ff-only
git status --short --branch
git lfs pull --include="Content/Melodia/Levels/**,Content/Melodia/PCG/**"
git switch -c collab/laptop/<short-task-name>
```

**Work:** Edit source, scripts, docs, blueprints (with editor closed on main PC).

**Finish a laptop task:**
```bash
git status --short --branch
git add <specific-files>
git commit -m "describe the laptop task"
git push -u origin collab/laptop/<short-task-name>
```

**On the main PC:**
```bash
git fetch origin
git switch main
git pull --ff-only
git merge --ff-only origin/collab/laptop/<short-task-name>
```

### LFS Locking (for binary assets)

If a task touches `.uasset`, `.umap`, `.blend`, `.fbx`, `.wav`, or textures:
```bash
git lfs lock Content/Melodia/Levels/MyLevel.umap
# ... edit ...
git lfs unlock Content/Melodia/Levels/MyLevel.umap
# or unlock on push: git lfs push --all origin && git lfs unlock ...
```

**Rule:** Never edit the same lockable binary on both machines at once.

### When to use Lane D
- All cross-machine work (this is the default)
- Source-only tasks (docs, scripts, C++): no locks needed
- Binary asset tasks: always lock first

---

## 6. Lane E — Hermes as the Orchestrator (The Creative Multi-Agent Lane)

**Concept:** Run Hermes on the main PC as your project manager. Hermes delegates coding tasks to the laptop via `delegate_task` (which runs a subagent with its own terminal context). You get a single conversation that dispatches work to both machines.

### Architecture

```
You (main PC)
    │
    ▼
Hermes (main PC)
    │
    ├── delegate_task → "Refactor X on laptop" → subagent on laptop (via SSH context)
    │
    ├── delegate_task → "Run contract tests on laptop" → subagent on laptop
    │
    └── direct tools → terminal/web_search on main PC
```

### Setup

The laptop must be accessible from the main PC. Since both are Windows on the same LAN:

1. **Option 1 — Hermes runs on the laptop directly:** Use `hermes --tui` or `hermes` on the laptop, then SSH in from the main PC. Hermes has full access to the laptop's repo, tools, and UE.

2. **Option 2 — Hermes on main PC delegates to laptop:** The `delegate_task` tool runs subagents in the same process. For true laptop offload, you'd run a separate Hermes instance on the laptop and coordinate via git (Lane D).

### When to use Lane E
- Overnight automation (Hermes on laptop runs test suites, writes reports)
- Parallel research (Hermes on main PC searches web, subagent on laptop probes UE internals)
- Batch operations (re-generate docs, run all contract tests, sweep for dead code)

---

## 7. Choosing Your Lane

| Task | Best Lane | Why |
|------|-----------|-----|
| C++ refactor, header cleanup | A (Gateway) | Full Rider intelligence, laptop is source of truth |
| Python scripts, JSON specs, docs | B (VS Code SSH) | Fast, lightweight |
| Full C++ rebuild | C (UBA) | Laptop compiles in parallel |
| Push work to main PC | D (Git handoff) | Clean branch protocol, LFS locks |
| Overnight automation | E (Hermes) | Laptop runs unattended |
| Blueprint editing | Local on laptop or main PC | Single-editor lock rule |
| PIE/testing | Local on whichever has UE open | Single-editor lock rule |

---

## 8. First Implementation Order

1. **Today:** Set up OpenSSH on the laptop (Lane A prerequisite).
2. **Today:** Install JetBrains Gateway on the main PC. Connect to the laptop. Verify Rider opens the project.
3. **Today:** Configure UBA on the main PC's `BuildConfiguration.xml` (Lane C). Trigger a test build to confirm the laptop picks up work.
4. **This week:** Establish the `collab/laptop/<task>` branch workflow (Lane D). Push a small doc branch from the laptop, merge on the main PC.
5. **This week:** Set up VS Code Remote SSH (Lane B) for lightweight tasks.
6. **Optional:** Configure Hermes cron jobs on the laptop for overnight test/report lanes (Lane E).

---

## 9. Anti-Patterns to Avoid

- **Do not run Lane A (Gateway) and local Rider on the main PC against the same laptop repo.** Two Rider instances indexing the same files = lock contention.
- **Do not run Lane C (UBA) builds while editing Blueprints locally.** UBA and the editor both need the toolchain.
- **Do not skip LFS locks on binary assets.** A merge conflict in a `.uasset` is unresolvable — you must pick one copy.
- **Do not use `git checkout -- .` on either machine.** It destroys uncommitted work. Use `git restore <file>` for targeted reverts.
- **Do not run two editors on the same UE project.** Single-editor lock rule applies across all lanes.

---

## 10. Summary

The laptop is not a second fragile copy of the main PC. It is:

- A **remote IDE brain** (Lane A)
- A **lightweight script station** (Lane B)
- A **compile worker** (Lane C)
- A **branch-based task worker** (Lane D)
- An **automation node** (Lane E)

Each lane preserves the project's core ownership model: one editor, one authority per system, explicit handoffs via git.
