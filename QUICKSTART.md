# 𝄞 Melodia — Quick Start 𝄞

**Engine:** Unreal Engine 5.8 · Blender 5.2 LTS · C++20 · Python 3.11

> Get in, prove the thing you changed, leave the project healthier than you found it. ♪

---

## ♪ Read these before changing architecture

1. `README.md`
2. `Docs/Strategy/MELODIA_ENDLESS_JOURNEY_NORTH_STAR_2026-09-02.md`
3. `CURRENT_STATE.md`
4. `TODO.md`
5. `SYSTEM_MAP.md`
6. the Chapter / tool / subsystem doc you are actually touching

The P0 six-phase route is still a useful full-stack test. It is **not** mandatory pacing for every future story.

---

## ♫ Setup

You need:

- Unreal Engine 5.8;
- Visual Studio 2022 or Rider-compatible C++ toolchain;
- Blender 5.2 LTS;
- Git + Git LFS.

```powershell
git clone https://github.com/fromage3900/MelodiaMelusinaV2.git
cd MelodiaMelusinaV2
git lfs pull
.\deploy\validate_setup.ps1
```

A fresh Git clone is not guaranteed to contain the author's entire binary art workspace. Read the Git/LFS/Perforce notes before assuming a missing local art file means the project never had it.

---

## ♬ Second workstation / laptop

If this checkout is on a second machine, read:

`Docs/Plans/LAPTOP_WORKSTATION_SETUP_AND_OFFLOAD_2026-09-02.md`

**before** hydrating the full binary workspace or deciding the laptop should run every tool at once.

Start with the read-only workstation inspector:

```powershell
powershell -ExecutionPolicy Bypass -File .\deploy\inspect_workstation.ps1
```

The current profile is intentionally measured rather than guessed:

- **16 GB RAM** → worker-first: Git, docs/specs, Rider/VS Code, tests, bounded builds, Blender batch work, Three.js; short UE launch as a canary rather than a permanent all-tools-at-once session;
- **confirmed 32 GB RAM** → controlled hybrid: UE + Rider inspection/small edits become reasonable while the main PC still owns heavy lookdev, long PIE, full art libraries, and release packaging.

Each workstation should have its **own clone**. Git/Git LFS + explicit handoff branches are shared authority. Do not edit the same binary asset from both machines at once.

Before opening Rider, Blender, or Unreal on either machine, run the safe sync check:

```powershell
.\deploy\sync_workstation.ps1
```

To apply a safe fast-forward and hydrate only the lane you need:

```powershell
# Text/source only — no large LFS pull
.\deploy\sync_workstation.ps1 -Mode Sync

# Melusina House reference/source lane
.\deploy\sync_workstation.ps1 -Mode Sync -LfsProfile House

# Current gameplay/vertical-slice binaries
.\deploy\sync_workstation.ps1 -Mode Sync -LfsProfile Gameplay
```

The synchronizer never resets, cleans, rebases, stashes, force-pushes, or auto-merges divergence. If one machine is ahead, push that branch before switching machines. If both sides moved, it stops and tells you to reconcile explicitly.

Current two-workstation contract: `Docs/Production/TWO_WORKSTATION_SYNC_CONTRACT_2026-09-04.md`.


`Launch_Editor.bat` now respects `MELODIA_UNREAL_ROOT` when UE5.8 is installed somewhere other than the default Epic path.
Run the laptop acceptance test before hydrating more binary art:

```powershell
.\deploy\test_laptop_workstation.ps1 -Suite Smoke
```

After Smoke passes, use `-Suite Build` with Unreal closed, then run `-Suite Fast` or `-Suite Contracts` one at a time. Reserve `-Suite UE` for a machine that has passed the build and can afford command-line Unreal.

---

## ♬ Run the tests

```powershell
# Core Python / contract suite
.\run_tests.ps1

# Offline P0 / static preflight
& "C:\Program Files\Epic Games\UE_5.8\Engine\Binaries\ThirdParty\Python3\Win64\python.exe" Tools/verify_p0_offline.py

# Melodia MCP regression
& "C:\Program Files\Epic Games\UE_5.8\Engine\Binaries\ThirdParty\Python3\Win64\python.exe" Tools/test_melodia_mcp.py

# End-to-end release / hygiene checks
& "C:\Program Files\Epic Games\UE_5.8\Engine\Binaries\ThirdParty\Python3\Win64\python.exe" Tools/test_e2e_melusina_release.py
```

Old PASS counts are evidence for the commit that produced them. If you changed the thing, re-run the thing.

---

## ♪ Open the current game proof

```powershell
start BS_GodFile.uproject
```

The current First Dream / Sea Above integration surface is useful because it crosses the real owners:

```text
Quill / narrative
      ↓
exploration / world interaction
      ↓
Phoenix battle
      ↓
Melodia rhythm
      ↓
Wardrobe / Convergence consequence
      ↓
checkpoint / save / restore
```

Use `_VERTICAL_SLICE_SCOPE.md` and the current golden-run spec for the exact route.

---

## 𝄞 The engineering target

When touching runtime code, keep this song in your head:

```text
outfit / world state
        ↓
exploration / Starskiff
        ↓
Phoenix action
        ↓
rhythm execution
        ↓
Convergence / consequence
        ↓
reward / checkpoint
        ↓
save
        ↓
quit + relaunch
        ↓
restore
        ↓
load again with no duplication
```

Breadth that makes this less reliable is not progress.

### Current Git-health note

Do not continue persistence work by merging stale PR #54 wholesale. Reapply/transplant its small useful delta onto a fresh branch from current `main`, then continue the restore/idempotency work there.

---

## ♫ Author a Chapter

A Chapter should increasingly look like a package, not an excuse to edit the core.

Useful pieces:

- `specs/progression/<chapter>.v1.json`;
- optional pillar manifests;
- Quill source when needed;
- stable IDs;
- idempotent intents / rewards;
- explicit persistent change;
- assets / maps / content refs;
- offline validation;
- runtime proof where relevant;
- restart/load proof for durable state;
- packaged proof before release promotion.

Read:

- `Docs/Plans/REUSABLE_CHAPTER_VALIDATION_SYSTEM_2026-08-31.md`
- `Docs/Strategy/MELODIA_CHAPTER_TIER_AND_VOLUME_ARCHITECTURE_2026-09-02.md`

---

## ♬ Run the browser laboratories

These are for interaction, schema, UI, and presentation experiments. They are **not** parallel gameplay runtimes.

From the repo root:

```powershell
python -m http.server 8080
```

Then open whichever little world you want:

```text
http://127.0.0.1:8080/Docs/Tools/puzzle-sandbox/
http://127.0.0.1:8080/Prototypes/Web/MusicKey3D/
http://127.0.0.1:8080/Prototypes/Web/MelodiaFolio3D/
http://127.0.0.1:8080/Prototypes/Web/MelodiaFolio3D/mara.html
```

### ♪ Cymatic Sanctuary

`Docs/Tools/puzzle-sandbox/` is the 12-instrument Music-as-Key sandbox. Click instruments, build phrases, unlock sanctuary barriers, and export prototype JSON for comparison with the native UE music-as-key contract.

### ♫ MusicKey3D

World-interaction / watercolor / toon-shading laboratory.

### ♬ Traveling Folio

3D UI, Starskiff post, Thread navigation, and real tracked repo-model display.

---

## ♪ Packaging

Use the existing BuildCookRun path for the maps/content being certified. Do not let an old P0 map list silently become the eternal global package manifest.

Example baseline:

```powershell
& "C:\Program Files\Epic Games\UE_5.8\Engine\Build\BatchFiles\RunUAT.bat" BuildCookRun `
  -project="C:\EnvironmentPortfolio\BS_GodFile\BS_GodFile.uproject" `
  -noP4 -platform=Win64 -clientconfig=Development `
  -cook -build -stage -pak -archive
```

Record the build hash, exact content, and evidence for every promoted package.

---

## ♫ MCP / automation

Automation helps author and inspect Melodia. It does not get to become gameplay truth.

- Melodia MCP — schema / test / inspection tooling.
- Agent Bridge MCP — policy-enforced routing.
- Monolith MCP — live Unreal inspection/editor automation.
- ECHO / contracts — spec → validation → runtime evidence → promote.

**One editor mutation authority at a time.**

---

## 𝄞 The online boundary

Do not build the remote Gifts backend yet.

The evergreen architecture matters **now** because it changes stable IDs, save migrations, chapter packaging, claimed-reward history, and UI contracts. Networking can arrive later without the core game depending on it.

---

## ♬ Keep nearby

- `README.md`
- `CURRENT_STATE.md`
- `TODO.md`
- `DOC_INDEX.md`
- `SYSTEM_MAP.md`
- `DATA_FLOW.md`
- `_VERTICAL_SLICE_SCOPE.md`
- `TEST_READY.md`

> **Goal: make adding journeys routine and reopening the engine exceptional.** ♪
