# Melodia Melusina — Blender cockpit (cine + assets)

**Addon:** Preferences name **Melodia Studio** (module id `surreal_architecture_gen`; operators remain `surreal_arch.*`). Sidebar category: **Melodia Studio**.

**SSOT stage:** `KitbashExport/Melodia_Portfolio_Stage_v4.blend`  
**Blender:** **5.2** (`C:\Program Files\Blender Foundation\Blender 5.2\blender.exe`)  
**Game mesh bus:** `KitbashExport/OrnamentalMeshes/SM_Orn_*.fbx` (gothic v1, 15)  
**Musical mesh bus:** `KitbashExport/MusicalOrnamentalMeshes/SM_Orn_*.fbx` (musical v1, 7)  
**Character / wardrobe:** [`Docs/MELUSINA_BLENDER_WARDROBE_SSOT.md`](MELUSINA_BLENDER_WARDROBE_SSOT.md)  
**Live Link** (`Docs/BLENDER_LIVELINK.md`) stays scratch-only → `/Game/LiveLink/` — never Ornament SKU or wardrobe.  
**MCP (new, 2026-08-06):** `deploy/blender_5.2_mcp.py` — stdio MCP server via `.mcp.json` server `"blender-5.2"`. Launches headless `blender.exe --factory-startup` per tool call. Tools: `get_scene_info`, `get_active_object`, `execute_blender_code`, `list_genomes` (56 styles across 8 groups), `apply_style`, `create_mesh`, `list_materials`, `export_fbx`. No persistent daemon, no TCP sockets.  
**Live GUI MCP (optional):** Cursor `user-blender` / `uvx blender-mcp` on port **9876** (same port as LiveLink TCP — enable BlenderMCP addon in the open 5.2 session).  
**Legacy MCP (deprecated):** port 9877 TCP socket adapter at `deploy/surreal_arch_mcp_adapter.py` — old 5.1 pattern, kept for reference only. Port **9317** HTTP claims in older docs are not the classroom default.

**School install / verify (no AI chat required):**
```powershell
cd deploy
.\install_melodia_studio.ps1
.\verify_melodia_studio.ps1
.\run_blender_smoke_queue.ps1
```

**Melodia Studio / GN status (2026-08-12):** deploy targets Blender 5.2 with **165** registered GN builders (12 categories). Hub panel `SURREAL_ARCH_PT_genome_carousel` nests GN Stack, Stage, bridges, and Living Portrait. Studio review additions: Solo Object (`surreal_arch.solo_object`) and Ivy (Bagapie). `FILIGREE_*` monolith rewrites remain deferred.

## Core commands

| Goal | Command |
|------|---------|
| Master studio refresh | In open 5.2: run `Tools/setup_melusina_master_studio.py` (MCP / Text Editor) |
| Beauty plate (Melusina) | `"C:\Program Files\Blender Foundation\Blender 5.2\blender.exe" KitbashExport/Melodia_Portfolio_Stage_v4.blend -b -P Tools/melodia_stage_shot.py -- --preset beauty --lights nikki` |
| Plate batch (musical / hero / outfit) | `… 5.2\blender.exe … -P Tools/run_melodia_plate_batch.py -- --musical --hero --outfit fv2_accordion` |
| Outfit plate | `… melodia_stage_shot.py -- --preset beauty --lights nikki --subject outfit:<OutfitId>` |
| Inventory Melusina meshes | `… inventory_melusina_stage_meshes.py` → `Saved/Audit/melusina_stage_mesh_inventory.json` |
| Ensure Wardrobe_* + import outfit | Prefer `Tools/populate_cathedral_review_queue.py` / `Tools/populate_musical_ornament_review.py` (legacy doc name `populate_stage_review_queue.py` is absent — do not invent it) |
| Export wardrobe FBX | `… export_melusina_wardrobe.py -- --outfit-id <OutfitId>` → `Exports/MelusinaClothes/` |
| **Prep ornament + musical authoring** | `python Tools/prep_ornament_music_mesh_session.py` then open stage with `-P Tools/prep_ornament_music_mesh_session.py` (EXPORT + Melodia GN + review grid). Queue: `Saved/Audit/ornament_music_authoring_queue.json` |
| Cute ornament bake | `blender --factory-startup -b -P Tools/test_cute_gn_ornaments.py` |
| Ornament FBX bake (15) | `blender --factory-startup -b -P Tools/regenerate_ornaments_surreal_arch.py` |
| Musical ornament bake (7) | `blender --factory-startup -b -P Tools/regenerate_musical_ornaments_surreal_arch.py` |
| Musical ornaments → stage | `blender KitbashExport/Melodia_Portfolio_Stage_v4.blend -b -P Tools/populate_musical_ornament_review.py -- --save` |
| Push ornament to gameplay | In UE: `py Content/Python/import_ornament_fbx.py --prep` · musical: `… --musical --prep` · or watcher / `run_ornament_kitbash_pipeline.ps1 -ImportFromKitbash` |

## Wardrobe (Lane D)

| Goal | Command |
|------|---------|
| Inventory meshes | `blender KitbashExport/Melodia_Portfolio_Stage_v4.blend -b -P Tools/inventory_melusina_stage_meshes.py -- --ensure-wardrobe --save` |
| Import outfit pack | Prefer wardrobe inventory + FBX import scripts in wardrobe SSOT; legacy `populate_stage_review_queue.py` is not in repo |
| Outfit beauty plate | `… -P Tools/melodia_stage_shot.py -- --preset beauty --lights nikki --subject outfit:<id>` |
| Export clothes FBX | `… -P Tools/export_melusina_wardrobe.py -- --outfit-id <id>` |

Audit: `Saved/Audit/melusina_stage_mesh_inventory.json` · Exports: `Exports/MelusinaClothes/<id>/`

Chain:

```text
Blender bake → KitbashExport → import_ornament_fbx → package ZIP
```

## Stage shot presets (`Tools/melodia_stage_shot.py`)

**Cameras** (`--preset`):

| preset | Stage camera |
|--------|----------------|
| `beauty` | `Cam_Beauty` |
| `front` | `Cam_Front` |
| `macro` | `Cam_Macro` |
| `low` | `Cam_Low` |
| `silhouette` | `Cam_Beauty` + Silhouette lights |
| `three_quarter` | `Cam_Beauty` |

**Lights** (`--lights`): `nikki` · `jewelry` · `silhouette` (collection toggles `Lights_*`)

**Subjects** (`--subject`):

```text
--subject melusina
--subject outfit:<OutfitId>
--subject ornament:vault_ribs
--subject ornament:corbel
--subject ornament:crown_molding
--subject ornament:torus_knot
--subject ornament:musical
```

Ornament shots auto-import FBX into `RenderSubject` and auto-aim. Melusina uses composed stage cameras unless `--auto-aim`. Outfit shots show `Wardrobe_<id>` + `Asset_melusina` (hair protected). Musical review grid lives under stage empty `MusicalOrnaments_Review` (Lane B — not wardrobe).

Passport sidecars land in `my-site-clean/generated/passports/`.

## Review Queue / authoring smoke

Before packaging or store screenshots:
- Open Blender 5.2 with the stage and confirm Melodia Studio N-panel draws.
- In Melodia Studio, smoke-test `SHEET_MUSIC_RAIL`, `TREBLE_CLEF`, `NOTE_HEAD`, one ornament builder, `ARCH`, and one registered `CASTLE_*` route.
- Confirm Review Queue Prev / Solo / Next, Solo Object, and Ivy (Bagapie) use soft visibility/local view only.
- Do not save over `Melodia_Portfolio_Stage_*.blend` from agent automation; the artist owns stage saves.

## Ornament → UE gameplay

| Script | Role |
|--------|------|
| `Content/Python/import_ornament_fbx.py` | FBX → `/Game/EnvSandbox/Meshes/Ornament/` (`replace_existing`) |
| `… --musical --prep` | Musical FBX → `/Game/EnvSandbox/Meshes/OrnamentMusical/` |
| `Content/Python/package_musical_ornament_kitbash.py` | Products + web JSON for musical sibling SKU |
| `watch_ornament_export_and_package.py --also-import` | Poll 15/15 gothic → UE import → ZIP |
| `run_ornament_kitbash_pipeline.ps1 -ImportFromKitbash` | Headless Cmd import + prep + package |

Audit: `Saved/Audit/ornament_fbx_import.json` · musical: `Saved/Audit/musical_ornament_fbx_import.json` / `musical_ornament_bake_manifest.json`

### Musical Ornament Kitbash (sibling SKU)

Celestial sheet-music set (7 meshes) — **not** the gothic 15 and **not** 2D `T_Melodia_*` Game UI alphas.

```text
blender --factory-startup -b -P Tools/regenerate_musical_ornaments_surreal_arch.py
python Content/Python/package_musical_ornament_kitbash.py --zip
# UE (when editor idle):
py Content/Python/import_ornament_fbx.py --musical --prep
```

Stage review: `MusicalOrnaments_Review` collection on v4. Shot hint: `--subject ornament:musical`.

## Related docs

- Stage toggles: [`KitbashExport/STAGE_README_v4.md`](../KitbashExport/STAGE_README_v4.md)
- Character / wardrobe: [`MELUSINA_BLENDER_WARDROBE_SSOT.md`](MELUSINA_BLENDER_WARDROBE_SSOT.md)
- Live Link: [`Docs/BLENDER_LIVELINK.md`](BLENDER_LIVELINK.md)
- Ornament sell plan: [`Docs/ORNAMENT_KITBASH_SELL_PLAN.md`](ORNAMENT_KITBASH_SELL_PLAN.md)
- World JSON (layout, not SKU): [`Docs/BLENDER_UE_WORLD_PIPELINE.md`](BLENDER_UE_WORLD_PIPELINE.md)
