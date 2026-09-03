# Asset Import & Pipeline Execution Handoff
**Date:** 2026-08-13
**Target:** Cloud Agent / Desktop Agent

## Current Context
The *Melodia* environment art platform has staged thousands of CC0/free stylized assets (Kenney nature/architecture, musical props, plus high-quality anime assets from BOOTH.pm/GitHub) into the `BS_GodFile\Imports\` directory. 

We have written the complete Phase 1 & 2 Python ingestion scripts to bring these assets into Unreal Engine 5.8 without cluttering the project with hundreds of default generated materials.

## Execution Checklist

### 1. Verification
- Verify that the `teamwork_preview` background agents have finished downloading the BOOTH and GitHub assets. Check the `Imports/` folder for new `PROVENANCE.md` files.
- Run `BS_GodFile\Scripts\prep_imports.bat` to ensure the folder structures are correct before ingestion.

### 2. Connect to Unreal MCP
- Connect to the **UE Monolith MCP Server** on port `9316`. The Unreal Editor must be open for the Python API to execute.

### 3. Run Pipeline Scripts
Execute the following scripts in order via Monolith Python execution (or from the UE command line):
1.  **Bulk Intake:** Run `BS_GodFile\Scripts\unreal_asset_intake.py`. This uses the Monolith `mesh_query:import_mesh` endpoints to ingest all FBX/GLTF/WAV files headless, *intentionally skipping material generation*.
2.  **Material Setup:** Run `BS_GodFile\Scripts\unreal_material_setup.py`. This generates our stylized Toon Material Instances (Nature, Stone, Wood, Metal) parented to `M_Master_Toon_Universal` with Substrate toggles optimized.

### 4. Audio Hookup
- We have generated `metasound_ui_routing.json`. Use this stub to configure the `MSS_JRPG_UI_Master` MetaSound graph in the Editor.
- We have generated `DT_AudioEvents.csv`. Import this into Unreal Engine as a DataTable using the `UMelodiaRhythmSkillDefinition` row structure (the Harmonix plugin will automatically resolve the `TSoftObjectPtr` paths to the imported MIDI/WAV assets).

### 5. Credits Registration (every import, always)
Every imported pack gets a credit row **in the same session it is ingested**:
1. Add the pack row to `Docs/CREDITS.md` (creator, source URL, license, usage).
2. Add/verify the coverage row in `Docs/SOURCES_MATRIX.md` for the `Content/` folder it landed in.
3. Run `python Tools/credits_gate.py` — it must PASS (exit 0). No row → fail → no import is "done".
4. If the creator/source is unknown, add a `pending` row with **no guessed name** and flag the owner — an uncredited row is preferable to a wrong credit.
5. New store purchases belong in the staging provenance table (`F:\Library\Assets\Downloads_Zips` / `Packs`, `F:\Inbox\Downloads_Sweep_2026-07-11`) per `Docs/CREDITS.md` § Staging provenance.
6. **C: is the only live workspace.** G:/F: copies of the repo are mirrors — never edit or import from them.

## Strict Guardrails
- **DO NOT** run standard Unreal FBX imports manually, as they will generate thousands of junk materials that pollute the project. Use the Python script.
- **DO NOT** re-run these scripts if the `Intermediate` cache was just cleared; allow the Editor 5-15 minutes to recompile shaders upon startup.
