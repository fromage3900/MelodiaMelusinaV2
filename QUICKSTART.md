# 🚀 Melodia — Quick Start & Developer Guide

**Get up and running with the Melodia Rhythm-JRPG in 5 minutes!**
**Engine Target:** Unreal Engine 5.8.0 | Blender 5.2 LTS | C++20 | Python 3.11
**Status (2026-09-01):** 10/10 P0 Gameplay Completion Gates PASS | 524/524 Automated Tests Passing

---

## 🛠️ 1. Prerequisites & Environment Setup

### Required Software
- **Unreal Engine 5.8.0**: Installed at `C:\Program Files\Epic Games\UE_5.8\`
- **Visual Studio 2022**: Desktop development with C++ (v143 toolset)
- **Blender 5.2 LTS**: Installed at `C:\Program Files\Blender Foundation\Blender 5.2\`
- **Git & Git LFS**: Installed and enabled

### Initial Setup Commands (PowerShell)
```powershell
# 1. Clone the repository
git clone https://github.com/fromage3900/MelodiaMelusinaV2.git
cd MelodiaMelusinaV2

# 2. Hydrate Git LFS assets
git lfs pull

# 3. Validate local environment and background services
.\deploy\validate_setup.ps1
```

---

## 🧪 2. Running Automated Tests

Melodia provides a fully automated test harness across Python simulations, C++ automation tests, MCP tool policies, and asset contract validators:

```powershell
# Run the core automated test suite (GMM Simulations + P0 Integration + ECHO Contracts)
.\run_tests.ps1

# Run offline P0 preflight gate verification (12 static checks)
& "C:\Program Files\Epic Games\UE_5.8\Engine\Binaries\ThirdParty\Python3\Win64\python.exe" Tools/verify_p0_offline.py

# Run Melodia MCP regression test suite (38 tests)
& "C:\Program Files\Epic Games\UE_5.8\Engine\Binaries\ThirdParty\Python3\Win64\python.exe" Tools/test_melodia_mcp.py

# Run end-to-end release & hygiene verification suite (17 tests across 4 tiers)
& "C:\Program Files\Epic Games\UE_5.8\Engine\Binaries\ThirdParty\Python3\Win64\python.exe" Tools/test_e2e_melusina_release.py
```

---

## 🎮 3. Playing the Vertical Slice & Chapter Loop in Editor (PIE)

The P0 vertical slice implements the standardized **6-Phase Reusable Chapter Gameplay Loop**:

### Step 1: Open the Project in Unreal Editor
```powershell
start BS_GodFile.uproject
```

### Step 2: Open the Chapter 1 Sanctuary Map
- Open `/Game/Melodia/Levels/Opening/L_MelusinaMorning`
- Press **Play in Editor (PIE)** (Alt + P)

### Step 3: Experience the 6-Phase Gameplay Flow
1. **Phase 1 (Sanctuary Dialogue):** Approach the NPC anchor; engage in QuillScript branching dialogue. Unlocks departure gate upon completion.
2. **Phase 2 (Overworld & Music Key):** Proceed through departure portal to the Sea Above journey map (`LV_SeaAbove_Prototype`). Step on harmonic resonance nodes (`APCGHeroMusicGraphHost`) to unlock the forward route.
3. **Phase 3 (Turn-Based Combat & Rhythm Highway):** Enter the battle arena (`L_KaleidoNave`). In the single-writer HUD (`UMelodiaUIBridgeSubsystem`), select an attack or skill. Hit incoming notes on the Rhythm Highway (keys: `Q`, `W`, `O`, `P`) to scale damage by your accuracy grade (`Poor: 0.35` to `Perfect: 1.5`).
4. **Phase 4 (Battle Resolution & Rewards):** Defeat the boss. The narrative subsystem handles resolution and idempotently grants the chapter reward outfit.
5. **Phase 5 (Wardrobe Traversal Upgrade):** Equip the new outfit to activate the `Glide` traversal capability (`IMelodiaTraversalCapabilityProvider`), allowing you to traverse over the portal chasm.
6. **Phase 6 (Canonical Checkpoint):** Reach the checkpoint anchor. Player stats, quest flags, wardrobe, and inventory serialize cleanly to `BP_JRPGSaveGame`.

---

## 📦 4. Packaging the Standalone Win64 Shipping Build

To build and cook a fresh standalone Win64 package containing all canonical gameplay maps:

```powershell
& "C:\Program Files\Epic Games\UE_5.8\Engine\Build\BatchFiles\RunUAT.bat" BuildCookRun `
  -project="C:\EnvironmentPortfolio\BS_GodFile\BS_GodFile.uproject" `
  -noP4 -platform=Win64 -clientconfig=Development `
  -cook -build -stage -pak -archive `
  -archivedirectory="C:\EnvironmentPortfolio\BS_GodFile\Saved\Packages\P0_Closeout_20260901" `
  -map="/Game/Melodia/Levels/Opening/L_MelusinaMorning+/Game/EnvSandbox/Environments/L_KaleidoNave+/Game/Melodia/Maps/LV_SeaAbove_Prototype+/Game/Melodia/Maps/MelodiaMainMenu"
```

To run the packaged game:
```powershell
& "Saved\Packages\P0_Closeout_20260901\Windows\BS_GodFile.exe" -log
```

---

## 🤖 5. Model Context Protocol (MCP) Automation

The repository includes local MCP servers for automated inspection, testing, and Unreal Editor control:

- **Melodia MCP (`deploy/melodia_mcp_server.py`):** Schema tools for QuillScript, narrative state, quest registries, and Blueprint fixtures.
- **Agent Bridge MCP (`deploy/agent_bridge_mcp.py`):** Policy-enforced routing bridge preventing unsafe mutations while exposing typed inspection commands.
- **Monolith MCP (Port `9316`):** Live Unreal Editor JSON-RPC bridge for Blueprint inspection and reflection.

---

## 📚 6. Key Documentation Links

- **Authoritative Evening Plan:** [Docs/Handoffs/MELODIA_EVENING_PLAN_P0_AND_CHAPTER_LOOP_2026-09-01.md](Docs/Handoffs/MELODIA_EVENING_PLAN_P0_AND_CHAPTER_LOOP_2026-09-01.md)
- **Current Architectural State:** [CURRENT_STATE.md](CURRENT_STATE.md)
- **Master Task Ledger:** [TODO.md](TODO.md)
- **Gate Ledger:** `Saved/gate_ledger.json`
- **P0 Golden Run Specification:** `specs/p0/core_p0_dream_golden_run.v1.json`
- **Documentation Index:** [DOC_INDEX.md](DOC_INDEX.md)
