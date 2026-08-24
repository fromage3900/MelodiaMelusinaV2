# Blender Addon Manifest — 2026-07-30

Generated after rebuilding Blender 5.2 clean, following the addon-corruption incident (a badly-installed "Melodia Studio" addon dumped loose scripts into `scripts/addons`/`scripts/startup`, including an auto-starting network daemon on port 9876/9877 causing a 1-second UI hitch). This manifest exists so a future rebuild is "read this file," not "dig through quarantine folders while stressed."

**Source of truth going forward**: keep this file updated whenever an addon is added/removed. Current live location: `AppData\Roaming\Blender Foundation\Blender\5.2\scripts\addons\`.

## Custom / project-owned (move to `Tools/BlenderAddons/`, load via an extra Script Directory — see below)

These are this project's own tooling, not third-party addons. They only ever lived in Blender's AppData profile, which is exactly the folder that just got wiped — moving them into the game repo means they're version-controlled and survive any future Blender reinstall automatically.

| Addon folder | Notes |
|---|---|
| `blender_brutalist_gn` | Custom Geometry Nodes style-genome tool, matches `deploy/surreal_arch/melodia_gn/` in the UE project |
| `blender_kawaii_gn` | Custom Geometry Nodes style-genome tool, same family as above |
| `GenesisCore` | Core support library for the above GN tools (name matches the "style genome" architecture referenced elsewhere in this project) |
| `fromage_roof_generator` / `FromageRoof_v3.1` | Custom procedural roof generator (two versions present — confirm which is current before moving both) |
| `melodia_icons` | Custom icon set for the above tools' UI |
| `melodia_pose_audit` | Melodia character rig pose audit addon, headless-safe |
| `melodia_showroom` | Integrated terrain→dress→frame→render pipeline for Resonant World showroom shots |
| `melodia_stage` | One-click character turntable & studio staging |
| `melodia_studio` | Resonant World terrain generation, dressing styles, and musical expansion presets |
| `rust_gpu_sdf_addon` | Custom SDF/procedural-geometry tool |
| `Procedural_Generation_Toolkit` | Custom, name is generic — verify contents before assuming scope |
| `blender_art_nouveau_greybox`, `blender_baroque_greybox` | Custom architectural-style greybox generators (referenced in earlier project session history) — **not present in the 5.1 quarantine snapshot or current 5.2 addons folder**, only existed in the older 4.2 snapshot. Either superseded/renamed, or genuinely lost — worth checking `deploy/surreal_arch/` in the main UE repo, which may already have the equivalent logic. |

## Third-party — recognized, commercial/community addons (safe to keep as normal Blender addons)

| Addon folder | Product (best identification from naming) |
|---|---|
| `MACHIN3tools` | MACHIN3tools (well-known modeling toolkit) |
| `MESHmachine` | MESHmachine (hard-surface modeling) |
| `ZenUV`, `Zеn UV v5.0.3.0 vfxMed` | Zen UV (UV toolkit) — two copies present, confirm which version is active |
| `CURVEmachine` | CURVEmachine |
| `archipack_20` | Archipack (architecture generator) |
| `animaide-master` | Animaide |
| `sverchok-master` | Sverchok (node-based procedural generation) |
| `flip_fluids_addon` | FLIP Fluids |
| `poliigon-addon-blender` | Poliigon asset library plugin |
| `send2ue` | Official Epic "Send to Unreal" bridge |
| `Blender-Unreal-Export-Addon` | Another Unreal export bridge — confirm this isn't redundant with `send2ue` |
| `rokoko-studio-live-blender-master`, `Rokoko Libraries` | Rokoko mocap tools |
| `quad_remesher` | Quad Remesher |
| `SimpleBake` | SimpleBake (baking toolkit) |
| `SwingyBonePhysicsAddon`, `Jiggle_Maker` | Physics/jiggle-bone tools |
| `UvSquares-master` | UV Squares |
| `collider_tools` | Collider Tools |
| `ZenDock` | ZenDock UI |

## Unverified / needs a source label

Everything else in the current addon list (`AE2BLEND_1_3_1`, `Advanced-Cones-master`, `AnimationRetimer-main`, `Animation_Layers`, `Beavel`, `Blender-BakeLab2-master`, `BlenderTools-20231109043947`, `Bligify-master`, `Combine V2`, `Curtain_Maker_Pro_S4c_v6`, `Handy Curve Profile`, `JDLC_Base`, `LightPainter`, `LiquiFeel`, `Mesh Cleaner Pro v0.1.3`, `N-Panel Orchestrator`/`N-Panel_Orchestrator`, `Sanctus-Bake`, `Sanctus-Library`, `SeamlessLab`, `Surface Fill v0.2.7`, `VSEQF-master`, `assets_library_builder`, `audvis`, `autoConstraintsFree_v1_1_0`, `auto_bake`, `cloud_generator`, `coiled_spring`, `ctools_braids`, `deep_paint_pro_v1.2.7`, `fluffy_maker`, `inkform.py` (confirmed: single-file addon, "Inkform" by Kevin Ramirez/Kevandram, Grease-Pencil-to-mesh), `inkform_v1.0`, `modules`, `nijigp`, `ocd_2`, `physical-starlight-atmosphere`, `projection_modeling`, `quad_unwrap-master`, `quicksnap-1_4_9`, `remap_presets`, `sound_waveform_display`, `speedsculpt`, `voxel_skinning`, `wrapper_addon`) — third-party addons of unconfirmed provenance (Fab/Blender Market purchase vs. free/GitHub). Not a safety concern (all confirmed to be legitimate self-contained addon folders during the rebuild, none matched the quarantined-daemon pattern) — just worth filling in the source next time you touch one, so this manifest stays useful.

## What was deliberately excluded from the rebuild (still quarantined, not reinstalled)

- `Blender_CorruptedBackup/5.1/scripts/addons/_QUARANTINE_BROKEN_ADDONS/` — the original "Melodia Studio" addon, dumped as loose files at addons-root instead of its own folder. Contains real, valuable work (`surreal_architecture_gen.py`, `surreal_arch/`, `surreal_greybox/`, `surreal_os/`, `surreal_world/`, `blender_melodia_unified`) — should be reinstalled properly as one isolated addon folder if/when wanted back, not loose files.
- `Blender_CorruptedBackup/5.1/scripts/startup/_QUARANTINE/` — 4 files, all auto-starting network-daemon variants (`blender_server_9876_v2.py`, `blender_mcp_auto_9877.py`, `melodia_autostart_mcp.py`, `auto_load_addons.py`). If an Unreal-Blender live-link bridge is wanted again, rebuild it as a real addon with a manual "Start Bridge" button — never as an auto-running `scripts/startup` file.

## One-time manual step still needed

To actually load the custom addons from their new repo location, add the repo path as an extra Script Directory: **Blender → Edit → Preferences → File Paths → Script Directories → Add** → point at `C:\EnvironmentPortfolio\BS_GodFile\Tools\BlenderAddons\`. This can't be done from outside Blender safely (`userpref.blend` is a binary file, not safe to hand-edit) — it's a 30-second one-time click, not a recurring task.

**Current state (2026-08-24)**: the 13 custom addons above exist in BOTH places right now — Blender's own `scripts/addons/` (where they're actively loaded from today) AND the new `Tools/BlenderAddons/` repo location (the new source of truth going forward). This is deliberate, not a mistake — once you've done the Script Directories step above and confirmed everything still loads correctly from the new path, the copies inside `scripts/addons/` can be deleted so there's only one copy to keep in sync.
