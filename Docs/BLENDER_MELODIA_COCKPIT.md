# Melodia Melusina — Blender cockpit (cine + assets)

**Start here for any Blender / Melodia Studio session.** Gameplay/UE work stays on [`_SESSION_HANDOFF.md`](../_SESSION_HANDOFF.md).

## Open in 30 seconds

| | |
|--|--|
| **Blender** | **5.2** — `C:\Program Files\Blender Foundation\Blender 5.2\blender.exe` |
| **Live stage (SSOT)** | `G:\EnvironmentPortfolio\BS_GodFile\Melodia_Portfolio_Stage_v22_ZenRebuild_WIP.blend` |
| **Addon** | Preferences name **Melodia Studio** (module `surreal_architecture_gen`, operators `surreal_arch.*`). N-panel tab: **Melodia Studio**. |
| **Do not save** the portfolio stage from an agent unless `MELODIA_ALLOW_STAGE_SAVE=1`. |

```powershell
& "C:\Program Files\Blender Foundation\Blender 5.2\blender.exe" "G:\EnvironmentPortfolio\BS_GodFile\Melodia_Portfolio_Stage_v22_ZenRebuild_WIP.blend"
```

After a crash or restart: **N → BlenderMCP → Connect to MCP server** (port **9876**). Melodia Studio **Live Bridge → Start Server** is LiveLink, not MCP — different button.

Agent ping: `python Tools/blender_mcp_client.py get_scene_info`

## Studio Health (2026-08-17) — musical heroes on deploy

```text
GN builders=173 menu=173 sections=12/12 section_trees=173
hidden=27 (them_* + PCG v1 aliases)  visible_stack=146
Review_Queue RQ_MEL_* = 165 (live v22 not resynced this pass)
```

Headless evidence: [`Saved/Audit/gn_music_heroes_2026-08-17_1437.json`](../Saved/Audit/gn_music_heroes_2026-08-17_1437.json) (7/7). Prior greybox smoke: [`Saved/Audit/gn_stub_rewrite_2026-08-17_1335.json`](../Saved/Audit/gn_stub_rewrite_2026-08-17_1335.json). AppData sync skipped (hung lookdev `blender.exe`).

## Studio Health (2026-08-17) — greybox pass on deploy

```text
GN builders=169 menu=169 sections=12/12 section_trees=169
hidden=27 (them_* + PCG v1 aliases)  visible_stack=142
Review_Queue RQ_MEL_* = 165 (live v22 not resynced this pass)
```

Headless evidence: [`Saved/Audit/gn_stub_rewrite_2026-08-17_1335.json`](../Saved/Audit/gn_stub_rewrite_2026-08-17_1335.json). Next-work plan: [`deploy/surreal_arch/Docs/GN_EXPANSION_PLAN_2026-08-17.md`](../deploy/surreal_arch/Docs/GN_EXPANSION_PLAN_2026-08-17.md) (08-12 kept as history).

## Studio Health (2026-08-12 19:48 ET) — B0/B1 green

```text
GN builders=165 menu=165 sections=12/12 section_trees=165
Review_Queue RQ_MEL_* = 165
```

Evidence: [`Saved/Audit/melodia_studio_sections_2026-08-12_1948.md`](../Saved/Audit/melodia_studio_sections_2026-08-12_1948.md) · [`…parity_2026-08-12_1948.md`](../Saved/Audit/melodia_studio_parity_2026-08-12_1948.md).

**Expansion:** [`deploy/surreal_arch/Docs/GN_EXPANSION_PLAN_2026-08-17.md`](../deploy/surreal_arch/Docs/GN_EXPANSION_PLAN_2026-08-17.md) supersedes 08-12 for next work. Presets **42/173**, STUDIO_LABELS include music heroes + greybox Structures ids.

**GN Stack smoke (expand the panel; ≥1 builder each):** Castle Kit · Musical Notation · Ornament · Magic Effects. Click **Circular Array** on a selected mesh — a Geometry Nodes modifier should appear.

**Sync & Reload:** only after `deploy\sync_surreal_to_live.ps1` when Blender was *already* open. A fresh start already loads AppData. The old operator crashed 5.2 by reloading itself; the timer fix is on disk — **restart Blender once** before using that button again.

**Sections bug (fixed):** Health could show `builders=165` while GN Stack categories stayed empty (`TREE_CATEGORIES` import alias). Rebuild now mutates containers in place; `stack.py` reads `core.TREE_*`.

**Workflow after live v22:** [`Docs/Handoffs/WORKFLOW_UNIFY_2026-08-12.md`](Handoffs/WORKFLOW_UNIFY_2026-08-12.md) — five doors, GN visual review on `GN_Review_Grid`, freeze Set Dressing.

Lanes: [BLENDER_MELODIA_STUDIO_HANDOFFS_2026-08-12.md](Handoffs/BLENDER_MELODIA_STUDIO_HANDOFFS_2026-08-12.md). Remaining: **B3 editable ornaments** on live v22. Cam_Beauty (B2-live) landed 2026-08-13 — live site https://fromage3900.github.io/my-site/.

## Ports (do not mix these up)

| Port | What | When |
|------|------|------|
| **9876** | **BlenderMCP** — Cursor/agent ↔ the *open* 5.2 GUI (`Tools/blender_mcp_client.py`, `uvx blender-mcp`) | Enable addon, then **Connect to MCP server** after every restart |
| **9876** | **LiveLink** TCP — Blender → UE `/Game/LiveLink/` scratch only | Melodia Studio → Live Bridge → Start Server. Never ornament/wardrobe SSOT. See [`BLENDER_LIVELINK.md`](BLENDER_LIVELINK.md) |
| Headless | `deploy/blender_5.2_mcp.py` — new `blender.exe --factory-startup` per call | No TCP. Not the live v22 session |
| 9877 / 9317 | Legacy adapters | Do not use |

**Kitbash buses (not the live stage):** gothic `KitbashExport/OrnamentalMeshes/SM_Orn_*.fbx` (15) · musical `KitbashExport/MusicalOrnamentalMeshes/SM_Orn_*.fbx` (7). Older plate scripts still point at `KitbashExport/Melodia_Portfolio_Stage_v4.blend`. Wardrobe: [`MELUSINA_BLENDER_WARDROBE_SSOT.md`](MELUSINA_BLENDER_WARDROBE_SSOT.md).

**School install / verify (no AI chat required):**
```powershell
cd deploy
.\install_melodia_studio.ps1
.\verify_melodia_studio.ps1
.\run_blender_smoke_queue.ps1
```

Hub panel `SURREAL_ARCH_PT_genome_carousel` nests GN Stack, Stage, bridges, and Living Portrait. Solo Object (`surreal_arch.solo_object`) and Ivy (Bagapie) are in the review tools. `FILIGREE_*` monolith rewrites remain deferred.

## Core commands

Beauty-plate / wardrobe commands below still point at historical `KitbashExport/Melodia_Portfolio_Stage_v4.blend`. Live portfolio stage is **v22** (see Open in 30 seconds); v4 is not the pin.

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
- Open **v22** in Blender 5.2. N-panel **Melodia Studio** must draw. **Studio Health** → `sections=12/12 section_trees=165`.
- Expand **GN Stack** and confirm ≥1 builder in Castle Kit, Musical Notation, Ornament, and Magic Effects.
- Click **Circular Array** (or `SHEET_MUSIC_RAIL` / `TREBLE_CLEF` / `NOTE_HEAD` / one ornament / `ARCH` / one `CASTLE_*`).
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
