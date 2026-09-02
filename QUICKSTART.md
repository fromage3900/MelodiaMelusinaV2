# Melodia — Quick Start & Developer Guide

**Engine:** Unreal Engine 5.8 | Blender 5.2 LTS | C++20 | Python 3.11  
**Product lens:** evergreen single-player Rhythm-JRPG; current engineering focus is runtime closure.

---

## 1. Read first

Before changing architecture, read:

1. `README.md`
2. `Docs/Strategy/MELODIA_ENDLESS_JOURNEY_NORTH_STAR_2026-09-02.md`
3. `CURRENT_STATE.md`
4. `TODO.md`
5. `SYSTEM_MAP.md`

The old six-phase P0 loop remains a useful integration test, but future Chapters may be combat-light, traversal-only, creature-focused, Starskiff-focused, or Monolith Events.

---

## 2. Setup

Required:

- Unreal Engine 5.8
- Visual Studio 2022 / Rider-compatible C++ toolchain
- Blender 5.2 LTS
- Git + Git LFS

```powershell
git clone https://github.com/fromage3900/MelodiaMelusinaV2.git
cd MelodiaMelusinaV2
git lfs pull
.\deploy\validate_setup.ps1
```

Bulk art/LFS/Perforce policy is documented separately; do not assume a fresh clone mirrors the author's entire local binary workspace.

---

## Second workstation / laptop

If this checkout is on a second machine, read [the laptop workstation setup and offload plan](Docs/Plans/LAPTOP_WORKSTATION_SETUP_AND_OFFLOAD_2026-09-02.md) before hydrating broad LFS content or opening long editor sessions. Run the local hardware/toolchain inspector first:

~~~powershell
powershell -ExecutionPolicy Bypass -File .\deploy\inspect_workstation.ps1
~~~

The plan assigns 16 GB machines to worker-first duties and confirmed 32 GB machines to a controlled hybrid role.

---

## 3. Run tests

```powershell
# Core Python / contract suite
.\run_tests.ps1

# Offline P0/static preflight
& "C:\Program Files\Epic Games\UE_5.8\Engine\Binaries\ThirdParty\Python3\Win64\python.exe" Tools/verify_p0_offline.py

# Melodia MCP regression
& "C:\Program Files\Epic Games\UE_5.8\Engine\Binaries\ThirdParty\Python3\Win64\python.exe" Tools/test_melodia_mcp.py

# End-to-end release/hygiene checks
& "C:\Program Files\Epic Games\UE_5.8\Engine\Binaries\ThirdParty\Python3\Win64\python.exe" Tools/test_e2e_melusina_release.py
```

Historical pass counts are evidence for their captured baseline. Re-run relevant suites after changing the code/specs they cover.

---

## 4. Play the current proof slice

Open:

```powershell
start BS_GodFile.uproject
```

The current integration proof revolves around First Dream / Sea Above content and demonstrates the stable core:

- Quill/narrative initiation;
- exploration/world interaction;
- Phoenix turn-based battle;
- Melodia rhythm execution;
- Wardrobe gameplay/traversal consequence;
- checkpoint/save/restore.

Use `_VERTICAL_SLICE_SCOPE.md` and the current P0 golden-run spec for the exact proof route.

Do **not** infer from this route that every future Chapter must contain the same phases.

---

## 5. Current engineering target

When working on core runtime, prefer proving this chain:

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
repeat load with no duplication
```

A change that adds breadth but makes this less reliable is not progress.

---

## 6. Authoring future Chapters

A durable Chapter should be package-shaped:

- `specs/progression/<chapter>.v1.json`;
- optional pillar manifests;
- Quill source if needed;
- stable IDs and idempotent intents/rewards;
- assets/maps/content refs;
- offline validation;
- runtime proof where applicable;
- restart/idempotency proof for durable state;
- packaged proof before release promotion.

See `Docs/Plans/REUSABLE_CHAPTER_VALIDATION_SYSTEM_2026-08-31.md` and the canonical chapter-tier strategy.

---

## 7. Packaging

Use the existing BuildCookRun workflow for the specific maps/content being certified. P0 packaging examples remain useful, but future Voyages/Volumes will have their own explicit content manifests rather than one permanent global map list.

Example P0 baseline:

```powershell
& "C:\Program Files\Epic Games\UE_5.8\Engine\Build\BatchFiles\RunUAT.bat" BuildCookRun `
  -project="C:\EnvironmentPortfolio\BS_GodFile\BS_GodFile.uproject" `
  -noP4 -platform=Win64 -clientconfig=Development `
  -cook -build -stage -pak -archive
```

Record exact packaged content, build hash, and validation evidence for each promoted release.

---

## 8. MCP / automation

Automation supports the game; it does not become gameplay authority.

- Melodia MCP: schema/test/inspection tooling.
- Agent Bridge MCP: policy-enforced routing.
- Monolith MCP: live Unreal inspection/editor automation.
- ECHO/contract pipeline: spec → validation → runtime evidence → promote.

Use one editor mutation authority at a time.

---

## 9. Strategy boundary

Do not build the future optional Gift/remote-manifest backend yet. The evergreen model currently changes **ID discipline, save compatibility, chapter packaging, and product language**. Networking comes after local persistence closure.

---

## 10. Key links

- `README.md`
- `CURRENT_STATE.md`
- `TODO.md`
- `DOC_INDEX.md`
- `SYSTEM_MAP.md`
- `DATA_FLOW.md`
- `_VERTICAL_SLICE_SCOPE.md`
- `TEST_READY.md`

**Goal:** make adding journeys routine and reopening the engine exceptional.
