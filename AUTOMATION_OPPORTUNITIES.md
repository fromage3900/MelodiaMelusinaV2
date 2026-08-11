# System Gap Analysis — Automation Opportunities

This document outlines pipeline inefficiencies, manual check steps, and opportunities for automation across the production and portfolio systems.

---

## 1. Material & Texture Pipeline Inefficiencies

*   **Manual Texture Catalog Syncing**: The scripts [portfolio_texture_catalog.py](file:///g:/EnvironmentPortfolio/BS_GodFile/Content/Python/portfolio_texture_catalog.py) and [integrate_compositing_textures.py](file:///g:/EnvironmentPortfolio/BS_GodFile/Content/Python/integrate_compositing_textures.py) scan texture folder paths on disk, but this process runs manually. It is not integrated into import tasks or loop triggers, which can result in stale catalog files.
*   **Decoupled Instance Reparenting**: When helper scripts (such as `archive_unused_instances.py`) move material instances on disk, redirectors are created. If the editor crashes or does not run `fix_migration_redirectors.py` immediately, parent-child inheritance chains can break.
*   **Manual Toon Profile Rebuilding**: When toon parameters or color steps are updated, the profiles (`TP_*`) must be modified manually in the editor. This step is not automated inside master rebuilding scripts.

---

## 2. World Layout & Import Inefficiencies

*   **Approximated Yaw Rotations**: The conversion formula `_blender_to_ue_rotation` inside [import_world_manifest.py](file:///g:/EnvironmentPortfolio/BS_GodFile/Content/Python/import_world_manifest.py) only calculates the Yaw angle, ignoring Pitch and Roll. This prevents the placement of rotated structures (such as collapsed arches or tilted towers).
*   **Decoupled FBX Auto-Importing**: The asset importer can request FBX imports but runs in the game thread, freezing the editor viewport during large layouts. It lacks asynchronous queue processing.

---

## 3. PCG & Capture Inefficiencies

*   **Asynchronous PCG Settle Sleep**: PCG point generation runs asynchronously. The validation script [pcg_validate_helpers.py](file:///g:/EnvironmentPortfolio/BS_GodFile/Content/Python/pcg_validate_helpers.py) uses arbitrary time delays to wait for point counts to settle. This delays loops and can cause incorrect metrics reporting.
*   **Headless Render Startup Overhead**: Capturing screenshots of updated assets requires spawning a headless Unreal process (`UnrealEditor-Cmd.exe`), which incurs heavy startup times. A persistent MCP hook could handle captures instantly without process restarts.
*   **Lack of Figma API Auto-Sync**: Rendered screenshots and stats manifests are outputted to `/Saved/Screenshots/`, but there is no automated script to trigger Figma API pushes, requiring artists to drag-and-drop assets manually.
