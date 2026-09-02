# Melodia — Laptop Workstation Setup & Offload Plan

**Status:** ready-to-run onboarding plan  
**Target machine:** ASUS Nitro laptop; exact SKU, RAM, GPU, and SSD capacity must be measured  
**Updated:** 2026-09-02  
**Project:** `fromage3900/MelodiaMelusinaV2` / `BS_GodFile.uproject`

## 1. Outcome

This laptop becomes a second Melodia workstation with a clear role:

- **Main PC:** Unreal Editor, heavy PIE/rendering, full lookdev, large art libraries, final cook/package, and GPU-bound work.
- **Laptop:** source/docs, Rider/VS Code, deterministic tests, bounded C++ builds, Blender batch work, Three.js/web prototypes, asset preparation, and overnight automation.
- **Shared authority:** Git/Git LFS and explicit handoff branches. Each machine has its own clone. Do not edit the same binary asset from both machines at once.

The setup is deliberately hardware-gated. A 16 GB laptop is a worker-first node; a confirmed 32 GB laptop can become a hybrid UE/editor node. The ASUS Nitro name alone is not enough to decide.

## 2. Repository facts verified before this plan

| Area | Current project contract |
|---|---|
| Unreal | UE 5.8; project file is `BS_GodFile.uproject` |
| Code/tooling | C++20; documented Python baseline 3.11 |
| DCC | Blender 5.2 LTS is the documented baseline; the laptop already has Blender configured |
| IDE | Rider is the preferred Unreal C++ IDE; VS Code is the lightweight scripts/docs/JSON editor |
| Source control | Git + Git LFS; repo hooks are enabled with `git config core.hooksPath .githooks` |
| UE onboarding | `bash deploy/collaborator_onboarding.sh lightweight .` keeps the checkout UE-capable without hydrating every tracked binary |
| Validation | `deploy/validate_setup.ps1 -SkipServices -CheckLfsHydration` |
| Bulk art | The collaborator guide records an authored S3 art drop of about 3.06 GiB; marketplace/vendor libraries are not redistributed through Git |
| Current launcher | `Launch_Editor.bat` uses the safe in-memory DDC workaround; it now resolves the UE install through `MELODIA_UNREAL_ROOT` when set |

Do not make the first laptop session depend on the complete art library. A fresh lightweight checkout can open with missing references until the required art drop is synced; that is different from an unhydrated Git LFS pointer.

## 3. Measure the laptop first

Run the helper after cloning:

~~~powershell
powershell -ExecutionPolicy Bypass -File .\deploy\inspect_workstation.ps1
~~~

It writes a local, ignored report to `Saved\Workstation\<computer>-workstation-report.json`. Do not commit machine-specific reports, credentials, or local paths.

Before cloning, Task Manager can give a quick answer. The PowerShell checks below are the authoritative raw measurements:

~~~powershell
Get-CimInstance Win32_ComputerSystem |
  Select-Object Manufacturer, Model,
    @{Name="RAM_GB";Expression={[math]::Round($_.TotalPhysicalMemory / 1GB, 1)}}

Get-CimInstance Win32_PhysicalMemory |
  Select-Object Manufacturer, Capacity, Speed, PartNumber

Get-CimInstance Win32_VideoController |
  Select-Object Name, DriverVersion,
    @{Name="VRAM_GB";Expression={
      if ($_.AdapterRAM -gt 0 -and $_.AdapterRAM -lt 17592186044416) {
        [math]::Round($_.AdapterRAM / 1GB, 1)
      } else { $null }
    }}

Get-Volume |
  Where-Object { $_.DriveType -eq 'Fixed' } |
  Select-Object DriveLetter, FileSystemLabel,
    @{Name="Free_GB";Expression={[math]::Round($_.SizeRemaining / 1GB, 1)}},
    @{Name="Size_GB";Expression={[math]::Round($_.Size / 1GB, 1)}}
~~~

### Hardware profile decision

| Measured result | Laptop role | First-session rule |
|---|---|---|
| 16 GB RAM | **Worker-first** | Keep the UE checkout lightweight. Run Rider, UE, Blender, browser, and local model services as separate active modes rather than all at once. Use `-MaxParallelActions=1` for builds. |
| 32 GB RAM | **Hybrid** | UE + Rider is reasonable for inspection and small edits; Blender or a build can run in a controlled second mode. Keep heavy rendering and full art work on the main PC. |
| 48 GB+ RAM and a suitable discrete GPU | **Full candidate** | Consider broader UE/editor use only after the validator, C++ build, and one clean editor launch pass. This is still not permission to duplicate the entire art library. |
| Unknown/weak GPU or nearly full SSD | **Worker-first** | Treat it as a CPU/tooling node until the GPU and free space are confirmed. |

GPU matters more than the product name for Lumen/Nanite and high-resolution rendering. Compare the measured adapter against Epic's current [Unreal hardware and software specifications](https://dev.epicgames.com/documentation/en-us/unreal-engine/hardware-and-software-specifications-for-unreal-engine) before assigning rendering work.

## 4. Install order

### 4.1 Windows, firmware, power, and storage

1. Finish Windows Update and reboot.
2. Install the current GPU driver for the measured NVIDIA/AMD adapter.
3. Use the laptop on AC power for UE builds and Blender batch work.
4. Keep the Windows page file system-managed; do not disable it to “save disk.”
5. Put the repository and UE on the internal SSD, not a network share. Avoid placing a Derived Data Cache on a nearly full or removable drive.
6. Keep heavy background startup apps off while profiling the first UE launch.

### 4.2 Git and Git LFS

Install Git for Windows with Git LFS support. Git LFS's per-user initialization is:

~~~powershell
git lfs install
~~~

The repo's `.gitattributes` marks Unreal packages, levels, source meshes, textures, audio, and other binary formats as LFS/lockable. Do not bypass that with `git add -f`.

### 4.3 Clone a laptop-specific lightweight checkout

Run this in Git Bash on the laptop:

~~~bash
GIT_LFS_SKIP_SMUDGE=1 git clone https://github.com/fromage3900/MelodiaMelusinaV2.git MelodiaMelusinaV2-Laptop
cd MelodiaMelusinaV2-Laptop

git config core.autocrlf false
git config core.hooksPath .githooks
git lfs install

bash deploy/collaborator_onboarding.sh lightweight .
~~~

The lightweight tier includes the project, source, plugins, required gameplay routes, tools, docs, and scoped LFS payloads. It is the correct first choice for 16 GB and a good first validation for 32 GB.

Use the full tier only after the laptop passes the lightweight acceptance gates and has enough SSD space:

~~~bash
bash deploy/collaborator_onboarding.sh full .
~~~

The full tier still does not create the missing bulk environment library. If a level needs the authored art drop, use the documented S3 route only with credentials supplied outside the repository:

~~~bash
aws configure --profile artdrop
aws s3 sync s3://melodia-artdrop-322037002075/EnvSandbox/ Content/EnvSandbox/ --profile artdrop
~~~

Never commit AWS configuration, keys, `.env` files, or vendor-library credentials.

### 4.4 Visual Studio C++ toolchain

Rider still needs a functioning Windows C++ toolchain for Unreal projects. In Visual Studio Installer, import the repository's `.vsconfig`. It currently requests the native desktop/game workloads, VC tools, Clang support, Windows 11 SDK 22621, and Unreal components.

Install the toolchain before the first plugin build. The laptop does not need to use Visual Studio as its daily editor; VS 2022 supplies the compiler, SDK, debugger integration, and Unreal build prerequisites.

### 4.5 Rider

1. Install Rider.
2. Open `BS_GodFile.uproject`, not only the `Source` folder.
3. Set Rider as the Unreal source-code editor.
4. Allow Rider's UnrealLink/RiderLink integration when Unreal prompts for it.
5. Keep Rider as the primary C++/Unreal IDE so the project has one code navigation and refactoring authority.

JetBrains' [Unreal Engine Rider documentation](https://www.jetbrains.com/help/rider/Working_with_Unreal_Engine.html) is the current reference for RiderLink, Blueprint support, debugging, and Unreal project integration.

### 4.6 VS Code

Use VS Code for:

- Python, PowerShell, Bash, JSON, Markdown, and web/Three.js work;
- quick log/spec inspection;
- lightweight repository review when Rider would be unnecessary.

Install only the extensions needed for those lanes: C/C++ syntax/navigation if useful, Python, PowerShell, EditorConfig, and Markdown support. Do not create a second competing Unreal project model unless a task specifically needs it.

### 4.7 Unreal Engine 5.8

Install UE 5.8 through the Epic Games Launcher. The documented default is:

~~~text
C:\Program Files\Epic Games\UE_5.8
~~~

If the laptop uses another path, set the user-level environment variable instead of editing tracked configuration:

~~~powershell
[Environment]::SetEnvironmentVariable(
  "MELODIA_UNREAL_ROOT",
  "D:\Epic Games\UE_5.8",
  "User"
)
~~~

Replace the example path with the measured install path, open a new terminal, and verify:

~~~powershell
$env:MELODIA_UNREAL_ROOT
Test-Path "$env:MELODIA_UNREAL_ROOT\Engine\Binaries\Win64\UnrealEditor.exe"
~~~

The portable `Launch_Editor.bat` honors this variable and retains the repository's known DDC startup workaround.

### 4.8 Blender

Because Blender is already configured, do not rebuild that setup immediately. Confirm that Blender launches and, if it lives outside the default path, set:

~~~powershell
[Environment]::SetEnvironmentVariable(
  "MELODIA_BLENDER_ROOT",
  "D:\Blender\Blender 5.2",
  "User"
)
~~~

Use the laptop for background Blender/Python work with the editor closed:

~~~powershell
blender.exe -b <file.blend> --python <script.py>
~~~

## 5. Build and validation order

Run the following from PowerShell in the repository root.

### 5.0 Laptop test ladder

The one-command runner keeps the cheap tests separate from the editor/build lanes. It records Git provenance, before/after status, command output, and a JSON evidence report under `Saved\Workstation\`.

~~~powershell
# Low-memory first pass; safe default for 16 GB
.\deploy\test_laptop_workstation.ps1 -Suite Smoke

# Existing Python/GMM/P0 tests
.\deploy\test_laptop_workstation.ps1 -Suite Fast

# ECHO, progression, route, and adversarial contracts
.\deploy\test_laptop_workstation.ps1 -Suite Contracts

# Closed-editor C++/plugin build; start with one action
.\deploy\test_laptop_workstation.ps1 -Suite Build -MaxParallelActions 1

# UE command-line automation; requires a successful build and no open editor
.\deploy\test_laptop_workstation.ps1 -Suite UE

# Full ladder; long and intentionally explicit
.\deploy\test_laptop_workstation.ps1 -Suite All
~~~

| Suite | What it proves | Laptop guidance |
|---|---|---|
| `Smoke` | Hardware/toolchain inspection, portable setup validation, offline contract floor, MCP/wardrobe/source-control/package contracts | First test on every checkout; appropriate for 16 GB |
| `Fast` | `run_tests.ps1 -Suite Fast` plus Smoke | Run one suite at a time |
| `Contracts` | `run_tests.ps1 -Suite Contracts` plus Smoke | Run when changing progression, ECHO, or route contracts |
| `Build` | Closed-editor UE 5.8 plugin build with `-NoUBA` and selected `-MaxParallelActions`, then required DLL validation | AC power; editor closed; 16 GB defaults to 1 |
| `UE` | `UnrealEditor-Cmd.exe` with `-unattended -nop4 -NullRHI` for `Automation RunTests Melodia` and focused `Melodia.Integration.WardrobeGlide` | Prefer 32 GB/hybrid or the main PC |
| `All` | Every lane above | Not a first-night test on 16 GB |

A green NullRHI automation run is not visual proof. The normal-render First Dream/Sea Above PIE route still needs human/editor evidence on the machine assigned to rendering. The test runner is a reproducibility gate, not a substitute for experiential review.

If you intentionally have uncommitted work, omit `-RequireClean`. Use it only when proving a clean checkout:

~~~powershell
.\deploy\test_laptop_workstation.ps1 -Suite Smoke -RequireClean
~~~

### 5.1 Hardware/toolchain report

~~~powershell
powershell -ExecutionPolicy Bypass -File .\deploy\inspect_workstation.ps1
~~~

### 5.2 Repository and LFS validation

~~~powershell
powershell -ExecutionPolicy Bypass -File .\deploy\validate_setup.ps1 `
  -SkipServices `
  -CheckLfsHydration
~~~

Fix every `FAIL` before opening the editor. Optional service warnings are expected unless that particular lane is being used.

### 5.3 Closed-editor plugin build

On a 16 GB machine, start with one build action:

~~~powershell
$ueRoot = if ($env:MELODIA_UNREAL_ROOT) {
  $env:MELODIA_UNREAL_ROOT
} else {
  "C:\Program Files\Epic Games\UE_5.8"
}

& "$ueRoot\Engine\Build\BatchFiles\Build.bat" `
  BS_GodFileEditor Win64 Development `
  -Project="$PWD\BS_GodFile.uproject" `
  -NoUBA `
  -MaxParallelActions=1
~~~

Then rerun:

~~~powershell
powershell -ExecutionPolicy Bypass -File .\deploy\validate_setup.ps1 `
  -SkipServices `
  -CheckLfsHydration `
  -RequirePluginBinaries
~~~

Keep Unreal closed during this build. The first compile is the most useful proof that the Visual Studio toolchain, UE version, plugin source, and LFS hydration agree.

### 5.4 Tests and editor launch

After validation:

~~~powershell
.\run_tests.ps1
~~~

For a hybrid/full candidate, launch the project with:

~~~powershell
.\Launch_Editor.bat
~~~

For a 16 GB worker-first laptop, treat a short editor launch as an acceptance test, not a requirement to keep UE open while Rider, Blender, a browser, and other services are active. The main PC remains the default for long PIE sessions, Lumen/Nanite lookdev, and final packaging.

## 6. What the laptop should do

| Lane | Laptop | Main PC |
|---|---|---|
| Git, docs, specs, branch preparation | Primary | Review/merge |
| Rider source work and code navigation | Primary | Primary for larger edits |
| Python/PowerShell contract tests | Primary | On demand |
| Closed-editor C++/plugin build | 16 GB: one action; 32 GB: controlled build | Larger parallel build |
| Blender batch exports and procedural generation | Good candidate | Interactive heavy sculpt/lookdev |
| Three.js/Folio/MusicKey prototypes | Primary | Review/integration |
| UE Editor, short map inspection | 32 GB hybrid only; 16 GB sparingly | Primary |
| Long PIE/debugging sessions | Not default on 16 GB | Primary |
| Lumen/Nanite/high-resolution rendering | Only if measured GPU proves it | Primary |
| Full authored art drop and vendor libraries | Avoid by default | Preferred |
| Cook/package/release certification | Not default | Primary |
| Ollama/local model serving | Off by default on 16 GB; only foreground/idle on 32 GB | Prefer main PC or a dedicated worker profile |

The goal is to move work that is deterministic and text/source-heavy away from the main PC without turning the laptop into a second fragile copy of the whole content workspace.

## 7. Handoff protocol between machines

Each workstation gets its own clone. Do not point both Unreal Editors at one shared live folder.

### Start a laptop task

~~~bash
git switch main
git pull --ff-only
git status --short --branch
git lfs pull --include="Content/Melodia/Levels/**,Content/Melodia/PCG/**"
git switch -c collab/laptop/<short-task-name>
~~~

The repository pre-push policy accepts the `collab/` prefix. Use a more specific LFS include for the task rather than hydrating everything.

### Finish a laptop task

~~~bash
git status --short --branch
git add <specific-files>
git commit -m "describe the laptop task"
git push -u origin collab/laptop/<short-task-name>
~~~

On the main PC:

~~~bash
git fetch origin
git switch main
git pull --ff-only
git merge --ff-only origin/collab/laptop/<short-task-name>
~~~

If the task changes a lockable `.uasset`, `.umap`, `.blend`, `.fbx`, texture, or audio asset, take the LFS lock before editing when the remote supports it:

~~~bash
git lfs lock <path/to/asset>
~~~

Do not edit the same lockable binary on both branches and hope Git will resolve it. Source, docs, specs, and scripts are the easiest lanes to move between machines.

Never copy `Saved/`, `Intermediate/`, `Binaries/`, `.rider/`, `.idea/`, or `DerivedDataCache/` between workstations as if they were source. They are machine-local/generated state.

## 8. Optional LAN offload — later phase

Do not begin with a networked Unreal/MCP worker. First prove that the laptop is healthy locally and can push a small branch that the main PC can consume.

If a LAN worker is added later:

- bind services to the private LAN only when remote access is actually needed;
- keep Windows Firewall rules scoped to the home/private network;
- never expose UE MCP, Blender MCP, Ollama, VOICEVOX, or Quantum ports to the public internet;
- use Git artifacts and explicit commands as the source of truth, not simultaneous edits in a shared folder;
- document the worker's hostname, IP reservation, service ports, and shutdown behavior in a separate dated handoff.

The current configured service ports are in `Config/paths.json`; their presence does not mean they should run on every machine.

## 9. Acceptance checklist

- [ ] Exact RAM, GPU/VRAM, CPU, SSD, and free-space measurements recorded locally.
- [ ] Laptop profile selected: worker-first, hybrid, or full candidate.
- [ ] Windows/GPU driver/power setup complete.
- [ ] Git and Git LFS installed; `git lfs install` succeeds.
- [ ] Lightweight sparse checkout is complete.
- [ ] `core.hooksPath` is `.githooks`.
- [ ] `MELODIA_UNREAL_ROOT` and optional `MELODIA_BLENDER_ROOT` resolve correctly.
- [ ] `.vsconfig` toolchain is installed.
- [ ] Rider opens `BS_GodFile.uproject`.
- [ ] VS Code opens scripts/docs without becoming a second Unreal authority.
- [ ] `validate_setup.ps1 -SkipServices -CheckLfsHydration` has no core failures.
- [ ] Closed-editor plugin build completes with the machine-appropriate parallelism.
- [ ] `-RequirePluginBinaries` validation passes.
- [ ] `run_tests.ps1` passes or its failures are recorded.
- [ ] A small `collab/laptop/...` branch is pushed and consumed from the main PC.
- [ ] Any missing art is classified as “not tracked” versus “unhydrated LFS,” not guessed at.

## 10. First-night order

1. Measure RAM/GPU/free space.
2. Install/update Git LFS and clone the lightweight tier.
3. Import `.vsconfig`.
4. Install/launch Rider and VS Code.
5. Install/verify UE 5.8 and set `MELODIA_UNREAL_ROOT` if needed.
6. Run the workstation inspector and portable validator.
7. Run `.\deploy\test_laptop_workstation.ps1 -Suite Smoke`.
8. If Smoke passes, run `.\deploy\test_laptop_workstation.ps1 -Suite Build -MaxParallelActions 1` with Unreal closed.
9. Run `Fast` or `Contracts` one at a time, based on the work you plan to offload.
10. Run `UE` only if the measured profile and build pass justify command-line Unreal; otherwise use the main PC for this lane.
11. Open UE once if the profile permits.
12. Push a small documentation or script branch and pull it on the main PC.
13. Only then decide whether this machine deserves broader LFS art hydration or a LAN worker role.

## References

- [Melodia Quick Start](../../QUICKSTART.md)
- [Melodia Collaborator Setup](../../COLLABORATOR_SETUP.md)
- [Epic Unreal hardware and software specifications](https://dev.epicgames.com/documentation/en-us/unreal-engine/hardware-and-software-specifications-for-unreal-engine)
- [JetBrains Rider for Unreal Engine](https://www.jetbrains.com/help/rider/Working_with_Unreal_Engine.html)
- [Git LFS](https://git-lfs.com/)
