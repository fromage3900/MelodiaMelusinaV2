# Agent System Ownership & Coordination — Environment Portfolio Platform

This document defines the system ownership boundaries, coordination protocols, and safety interlocks for the multi-agent production team.

---

## 1. Candidate System Ownership

To prevent merge conflicts and ensure clear responsibilities, each major subsystem is assigned a primary candidate owner agent. 

```
                               ┌───────────────────────────┐
                               │  QA & SENTINEL AGENT      │
                               │  - Editor Automation      │
                               │  - Audit Loops            │
                               └─────────────┬─────────────┘
                                             │
      ┌──────────────────────────────────────┼──────────────────────────────────────┐
      ▼                                      ▼                                      ▼
┌─────────────┐                        ┌─────────────┐                        ┌─────────────┐
│  GEOMETRY   │                        │ INTEGRATION │                        │  MATERIAL   │
│    AGENT    │                        │    AGENT    │                        │    AGENT    │
│  - Blender  │                        │ - Importer  │                        │ - Masters   │
│  - Genomes  │                        │ - Live Link │                        │ - Instances │
│  - Trims    │                        │ - MPC/TOD   │                        │ - MM Engine │
└──────┬──────┘                        └──────┬──────┘                        └──────┬──────┘
       │                                      │                                      │
       │                                      ▼                                      │
       │                               ┌─────────────┐                               │
       └──────────────────────────────►│  PLACEMENT  │◄──────────────────────────────┘
                                       │    AGENT    │
                                       │ - PCG Ex    │
                                       │ - Scatters  │
                                       └─────────────┘
```

| Subsystem | Candidate Owner Agent | Co-Owners / Readers | Code/Asset Directory Boundary |
| :--- | :--- | :--- | :--- |
| **1. Material System** | **Material Pipeline Agent (MPA)** | SQA (Read Only) | `Content/Python/setup_master_*.py`, `Content/Python/material_lib.py`, `setup_material_functions.py` |
| **2. Material Instance System** | **Material Pipeline Agent (MPA)** | SQA (Read Only) | `Content/Python/apply_*.py`, `starter_instances.py`, `universal_instance_presets.py` |
| **3. Trim Sheet System** | **Procedural Geometry Agent (PGA)** | MPA (Co-Owner) | `deploy/surreal_arch/trim_bake.py`, `Content/Python/setup_trimsheet_instances.py` |
| **4. PCG System** | **Procedural Placement Agent (PPA)** | SQA / PGA (Read Only) | `Content/Python/pcg_graph_builder.py`, `setup_pcg_*.py`, `pcg_portfolio_standards.py` |
| **5. Scene Integration System** | **World Integration Agent (WIA)** | MPA / PPA (Co-Owners) | `Content/Python/setup_template_showcase.py`, `setup_sakura_scene.py`, `setup_*_mpc.py` |
| **6. Editor Automation System** | **QA & Sentinel Agent (SQA)** | WIA (Co-Owner) | `Content/Python/init_unreal.py`, `run_editor_tasks_headless.py`, `run_editor_session.py` |
| **7. MCP Integration System** | **World Integration Agent (WIA)** | SQA (Read Only) | `Plugins/UnrealMCP/Source/`, `Content/Python/monolith_mcp_client.py` |
| **8. Portfolio Scene Pipeline** | **World Integration Agent (WIA)** | SQA (Co-Owner) | `Content/Python/run_portfolio_orchestrator_loop_tick.py`, `deploy/*_loop.ps1` |
| **9. Asset Import Pipeline** | **World Integration Agent (WIA)** | PGA (Co-Owner) | `Content/Python/import_world_manifest.py`, `deploy/surreal_world/export.py` |

---

## 2. Coordination Protocols & Handshakes

Agents must communicate across system boundaries using structured protocols.

### 2.1 The Geometry-to-Import Handshake (PGA ➔ WIA)
1.  **Export Trigger**: The PGA compiles snap rules, runs the layout generator, bakes trim vertex colors, and writes the `{WorldRoot}.world.json` manifest.
2.  **File Event**: The manifest is saved under `deploy/surreal_world/export/`.
3.  **Import Trigger**: The WIA detects the new manifest, runs `import_world_manifest.py`, parses coordinates, resolves static meshes from `WorldExport/World_*.fbx`, and spawns the HISM components.
4.  **Verification**: The SQA runs `_mcp_verify_world.py` to confirm that all transforms imported successfully and that no assets are missing.

### 2.2 The Material-to-Geometry Handshake (MPA ➔ PGA)
1.  **Convention Update**: When the MPA modifies albedo mappings or parameter inputs on `M_Master_Toon_Universal`, they must update the `ROLE_UE_HINTS` mappings inside `deploy/surreal_world/export.py`.
2.  **Taxonomy Matching**: The PGA reads `ROLE_UE_HINTS` to ensure that generated objects specify material hints that map to valid Unreal asset paths.
3.  **Verification**: The SQA runs `audit_material_parameters.py` and `audit_material_library.py` to confirm that all instances resolve their parent parameters.

### 2.3 The Placement-to-Scene Handshake (PPA ➔ WIA)
1.  **Boundary Setup**: The WIA places physical boundary tags (`PCG_Volume`, `PCG_Ground`) on meshes in levels like `L_SakuraPath`.
2.  **Scatter Generation**: The PPA runs the universal and style wrappers (`setup_pcg_universal.py` and `setup_pcg_sakura.py`) to read those volumes and scatter the static mesh collections (`SMC_*`).
3.  **Verification**: The SQA runs `audit_pcg_portfolio.py` to verify that all volumes contain generated points and that no overlapping geometry collisions occur.

---

## 3. Safety Interlocks & Loop Control

To protect the integrity of the project files, the background loops run under strict safety interlocks.

```
[ Loop Tick ] ──► Run SQA Health Check (run_verify.ps1)
                       │
                       ├──► [ PASS ] ──► Proceed with Agent Cycle
                       │
                       └──► [ FAIL ] ──► Write Loop Stop File & Halt Loop
```

1.  **Pre-Tick Health Check**: Before executing any generation, import, or build cycle, loop runners must run `powershell deploy/run_verify.ps1 -Mode all`.
2.  **Halt Trigger**: If the health check fails (returns non-zero or outputs syntax/reference errors), the loop runner must immediately write a `{SYSTEM}_LOOP_STOP` file to the `deploy/` directory and exit the process.
3.  **Safety Lockout**: While a `*_LOOP_STOP` file exists, no agent is permitted to write to the `/Game/EnvSandbox/` directory.
4.  **Resolution Protocol**: The SQA must isolate the error using local logs (`Saved/Logs/` and `Saved/Audit/`), fix the broken reference or syntax error, run the verify script manually until it passes, remove the stop file, and restart the loop using `deploy/start_*_loop.ps1`.
