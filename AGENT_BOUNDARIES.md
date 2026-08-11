# Agent System Ownership & Boundaries — Environment Portfolio Platform

This document establishes the system ownership boundaries, write access permissions, and conflict resolution protocols for the multi-agent production team.

---

## 1. Agent Roles & Subsystem Mapping

To prevent code overlap and merge conflicts, each subsystem is assigned a single primary owner agent.

```
                  ┌───────────────────────────────┐
                  │      QA & SENTINEL AGENT      │
                  │   Audits, validation, status  │
                  └───────────────┬───────────────┘
                                  │
         ┌────────────────────────┼────────────────────────┐
         ▼                        ▼                        ▼
┌─────────────────┐      ┌─────────────────┐      ┌─────────────────┐
│  GEOMETRY AGENT │      │ PLACEMENT AGENT │      │  MATERIAL AGENT │
│   Blender OS,   │      │   Unreal PCG,   │      │ Masters, PBR,   │
│ Style Genomes   │      │  PCGEx scatter  │      │ Material Maker  │
└────────┬────────┘      └─────────────────┘      └────────┬────────┘
         │                                                 │
         │          ┌───────────────────────────┐          │
         └─────────►│     INTEGRATION AGENT     │◄─────────┘
                    │   Live Link, HISM Import  │
                    └───────────────────────────┘
```

### 1.1 Procedural Geometry Agent (PGA)
*   **Subsystem Ownership**: Trim Sheet System (baking), Style Genomes, kit geometries, and layouts.
*   **Write Access boundaries**:
    *   `deploy/surreal_os/`
    *   `deploy/surreal_greybox/`
    *   `deploy/surreal_architecture_gen.py`
    *   `research/`

### 1.2 Material Pipeline Agent (MPA)
*   **Subsystem Ownership**: Material System, Material Instance System, and Material Maker PBR Engine.
*   **Write Access boundaries**:
    *   `Content/Python/setup_master_*.py`
    *   `Content/Python/material_lib.py`
    *   `Content/Python/apply_*.py`
    *   `Content/Python/starter_instances.py`
    *   `Tools/MaterialMaker/`
    *   `/Game/EnvSandbox/Materials/`

### 1.3 Procedural Placement Agent (PPA)
*   **Subsystem Ownership**: PCG System and PCGEx graph scatter setups.
*   **Write Access boundaries**:
    *   `Content/Python/pcg_graph_builder.py`
    *   `Content/Python/setup_pcg_*.py`
    *   `Content/Python/pcg_portfolio_standards.py`
    *   `/Game/EnvSandbox/PCG/`

### 1.4 World Integration Agent (WIA)
*   **Subsystem Ownership**: Import Pipeline, MCP Integration Layer, and Scene System.
*   **Write Access boundaries**:
    *   `Content/Python/import_world_manifest.py`
    *   `Content/Python/portfolio_scene_integration.py`
    *   `Content/Python/setup_template_showcase.py`
    *   `Content/Python/setup_sakura_scene.py`
    *   `Content/Python/setup_*_mpc.py`
    *   `Tools/BlenderLiveLink/`
    *   `/Game/EnvSandbox/WorldImport/`
    *   `/Game/EnvSandbox/Environments/`

### 1.5 QA & Sentinel Agent (SQA)
*   **Subsystem Ownership**: Editor Automation System, test verification orchestrators, and audit scripts.
*   **Write Access boundaries**:
    *   `Content/Python/audit_*.py`
    *   `Content/Python/fix_*.py`
    *   `deploy/run_verify.ps1`
    *   `deploy/_mcp_verify_*.py`

---

## 2. Overlap Prevention Protocols

To ensure parallel development remains stable, agents must adhere to the following boundary restrictions:

1.  **Shared Interface Rule**: If an agent needs to reference or modify variables controlled by another subsystem (e.g., the PGA assigning material paths to generated kits), they must use the defined project interface contracts:
    *   `deploy/surreal_world/export.py` contains `ROLE_UE_HINTS`, which acts as the boundary interface between the PGA's geometries and the MPA's material instances.
2.  **No Direct Cross-Writes**: Under no circumstances should an agent write to a directory outside of their designated boundaries. For example, the PPA must never modify `import_world_manifest.py`, and the PGA must never write to `/Game/EnvSandbox/Materials/`.
3.  **Conflict Resolution**:
    *   If a parameter name change is required on a master shader, the MPA must push the change and update the corresponding audit rules.
    *   The WIA will then update coordinate transformations to align with the new material inputs.
    *   The SQA will run the verification suite to ensure that references are rewired successfully.

---

## 3. Branching & Continuous Verification Rules

*   **Header Isolation**: Python files must start with a descriptive header defining the Candidate Owner Agent.
*   **Headless Validation**: Headless execution runs must not produce disk locks or asset errors.
*   **Loop Safety Lockout**: If any SQA script (e.g., `audit_material_library.py`) fails, a `*_LOOP_STOP` sentinel file is created, and all agent writes to the content database are immediately locked out until the SQA clears the failure.
