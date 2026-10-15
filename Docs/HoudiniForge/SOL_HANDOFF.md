# NEXT_SESSION_HANDOFF (read this first)
Updated 2026-10-15 ~13:10 ET by Grok Bot for Brennan. Branch lane/houdini-forge-staging, merged to main.

**Done (do not redo):**
- 84 Houdini Forge assets imported into UE under `/Game/Staging/HoudiniForge/` and committed (Git LFS) to main.
- This handoff lives at `Docs/HoudiniForge/SOL_HANDOFF.md` (repo). The working PC copy plus import scripts/logs/JSON stay under `Saved/Staging/GrokPrep/houdini_forge/` (gitignored, local only).

**Where things live:**
- Assets: `Content/Staging/HoudiniForge/{Carillon/Creatures,Carillon/Parts,Carillon/Skeletal,NPC/Dingle,LittleGuys/MusicBoxMimic,Gaudy}`.
- Anchor/lookdev contract: `Saved/Staging/GrokPrep/houdini_forge/ue_stage_pack/lookdev/CONTRACT.md` (+ stage_manifest.json).
- Import/verify scripts and results: `Saved/Staging/GrokPrep/houdini_forge/*.py|*.json|*.log`.

**Pending + owner:**
| Item | Owner |
|---|---|
| Gaudy v4 reimport with body-slot MIs (ChimeSnail and Dingle get MI_Brass_Engraved; Pearl Jellybell and Queen get MI_Brass_Iridescent) | Lookdev Manager |
| Cathedral v3.x (v3.1 and later) | Sol |
| In-editor vertex color/UV check of the staged meshes | Brennan (needs the editor) |
| Dingle collar clearance (~160 cm) check | Brennan / Sol |
| Anim pack import (pending, editor must be closed or Claude lane): root at crown pivot, root motion off; mixed creature scales, verify scale on import; no sockets/UCX: add sockets on UE skeleton and generate Physics Asset; Strike_Ring f8 needs an AnimNotify driving the ring. Source: ue_stage_pack\lookdev\anim\ (9 fbx/SKM_<Creature>_anim.fbx x 7 takes + ANIM_CLIPS.md; local only, Saved/ is gitignored) | Lookdev Manager |
| Aeolian dressing (Brennan-approved, existing assets only, owner 💧 for UE placement, needs editor closed or Claude lane): Weingarten facade + RoseTracery at S0_Amin7; known blockers: facade floats 8-54m, not refit to windows.json, no collision, 2 MI-less slots (Lookdev Manager mapping to contract MIs). New versioned Aeolian map; Brennan Ctrl+S. Inventory: Docs/HoudiniForge/AEOLIAN_INVENTORY_v1.md | 💧 (UE placement) / Lookdev Manager (MIs) |
| Proposed CURRENT_STATE.md line (not applied; see PR body) | Brennan |

**Lane status (verbatim from Brennan's session notes; paths relative to houdini_forge / ue_stage_pack):**

Cutie Patootie (asset prep): ue_stage_pack\cutie_v3_ready\ is canon; QC in IMPORT_LIST.md + _qc\. Next: strip zero-area faces/loose verts, repack UVs on full-res Dingle, add LODs. Accordeurs: accordeurs\rig_v1\RIG_PLAN.md (ARP bone list + markers), waiting on Brennan to build template rig once in UI; Mlle Merge v4 parked. Aeolian dressing: inventory in progress at overworld_dressing\AEOLIAN_INVENTORY_v1.md.

Lookdev Manager: ue_stage_pack\lookdev\CONTRACT.md is canon (MI-by-pitch, cathedral MI zones, NavMesh roaming via BP_EnemyExplorePawnBase); NIAGARA_PICK.md; UE_CODE_AUDIT.md. Gaudy in lookdev\gaudy\: v2 staged; v3 has 12 slots (0-4 fixed, 5+ detail), Col only vertex color set, wear/height in UV2/UV3, see MATID_VERTEXPAINT_v3.md. In progress (Lookdev Manager owns): gaudy v4 (per-creature ornaments, snail fit, baked textures in textures_v4\) and enemy BP anim clips in lookdev\anim\ (ANIM_CLIPS.md). Next session: import v4 with body MIs MI_Brass_Engraved (Snail, Dingle) and MI_Brass_Iridescent (jellybells); wire anim clips into enemy BPs.

---

# Houdini Forge -> Sol handoff (converge, don't reinvent)
Written by Grok Bot (💧), 2026-10-15 00:15 ET. Owner: Brennan. Status: STAGING ONLY. Nothing below is in Content/ yet. No git writes made.

## Rules this work follows (and Sol should keep)
- Canon first: CURRENT_STATE.md + lane docs. Reuse Brennan's masters, Niagara templates, BP_MelodiaNiagaraDriver, Tools/Houdini (melodia::ocean_cathedral::1.4, build_switchback_stairs.py, varied_corridors.py, sir_kinefx/, chladni_eigen.py).
- Only MIs of existing masters. No new masters. No scripted character-mesh imports (Brennan imports skeletal/morph assets himself).
- Never write under a running editor. Bots write only to Saved/Staging/GrokPrep/.
- Houdini is Apprentice: no FBX/ABC export, COP output watermarked. FBX comes from Blender; Houdini ships bgeo.sc / OBJ / JSON / CSV / EXRs written from Python.

## Locked conventions (the contract)
- Frame: JSON = "frame": "shared_zup_cm" (cm, Z-up, tile-centre origin). Flip Y exactly ONCE, on the way into UE. Blender FBX is in the UE frame and is labelled so.
- Pivot: bell crown everywhere (pivot_rule=crown). Rotations: rot_xyzw (FQuat order); bgeo uses orient in xyzw.
- Heights: deck_height_cm=618, clearance_cm=30 (usable 588). This is the BELL KIT envelope only; do NOT rescale the cathedral to it.
- Names: meshes SM_GPX_<Kit>_<Part> (e.g. SM_GPX_Carillon_Bell_C5); sockets SKT_<Root|Mount|Hinge|Emit|Weak>_<L|R|C|N|E|S|W>_<Idx>; cord joints CORD_<Side>_<Idx>_j0..j4.
- Per-bell fields: state (arch|awake|awake_roam|awake_combat), piece_id (links arch<->awake twins), part, socket_id, role, note, pitch_hz, size_scale, decay_s (ESTIMATE), hum_ratio 0.5, cord_id, has_cord, mount (floor|ceiling|cord|orbit), hang_cm, cord_swing, orbit_r_cm, orbit_phase, sway_phase, sway_amp, wobble_amp, weak_spot, roams, roam_width_cm, profile_id, deck_height_cm, clearance_cm.
- Sound comes from note/pitch_hz, never from mesh shape. Shape (profile_id) is chosen for silhouette.
- Gameplay rule: C3 bourdon = stationary floor boss per nave bay (weak_spot=1, no cord, roams=0). C3/G3/C4 = stationary low choir. C5-C6 roam halls/stairs single-file (awake_roam), regroup into full halo (awake_combat, ~13.6 m) only in open nave bays.
- Runtime: everything baked; no runtime sims. Swarm = position/rotation EXRs read by an EXISTING Niagara template, driven by BP_MelodiaNiagaraDriver (chord picks shape, beat tightens clump, max 6 rings/beat). Vellum veils/tail = vertex animation via MI of existing master. Strike wobble = cheap material wobble.
- Integration into the Ocean Cathedral = ADD extra PCG input/subgraph. Do NOT edit existing nodes in Brennan's cathedral PCG graph (it has his uncommitted edits).

## What exists (Saved/Staging/GrokPrep/houdini_forge/)
| Lane | Path | What | State |
|---|---|---|---|
| Cutie Patootie | cutie_gn/carillon/ | v1 blockout: 5 variants (Bell Spirit, Chandelier Wraith, Bell-Golem, Hydra, Inverted Tower), fbx/SM_GPX_Carillon_Parts.fbx (20 meshes), Carillon_parts.json (UE frame, stale), Carillon_parts_shared.json, SCALE_CHECK.md, Bell Hall mood render | done; bell set v1 is stale (C4/G4) |
| Cutie Patootie | cutie_gn/bell_creature/cord_bones.json | 11 cords x 5 joints, shared frame, active_cord_count 10 (CORD_N_0 = bourdon, has_cord 0) | done, merged by Blessed Boy |
| Cutie Patootie | cutie_gn/carillon_v2/ (+ vellum/) | v2 detail, packed UVs, OBJ pack, Pokemon-style Wraith/Hydra, Vellum-ready veils/tail/cords + vellum_pins.json, Dingle (big creature_flare body bell, chandelier arms, C5-C6 hand bells) | in progress |
| Blessed Boy | blessed_hda/carillon/out/ | melodia::dual_state_piece::0.1 (.hdanc), arch/awake/awake_roam points CSV+JSON, carillon_wake_xforms.json (72 f @24fps), rig_merge_report.json | done, parity pass, re-keyed crown/rot_xyzw |
| Blessed Boy | blessed_hda/carillon_swarm/ | 300 bells x 192 f swarm, swarm_pos/rot/data.exr (Python-written, no watermark), swarm_tex_bounds.json | done, parity 14/14 |
| Blessed Boy | research_cymatics_bells/ | CYMATICS_RESEARCH.md, BELL_CAD_SPEC.md, HANDOFF.md, bell_profile.py, profiles/ (7 sweep presets + morph) | done |
| Lookdev Manager | lookdev_ue/, ue_stage_pack/lookdev/ | CONTRACT.md, stage_manifest.json (targets under /Game/Staging/HoudiniForge/, import settings, MI per bell) | written, landing on disk UNCONFIRMED |
| 💧 | teardrop_build/ | Cathedral breakup + bell layer built on TOP of the existing Ocean Cathedral (scale hierarchy, repetition breakup, corridors from varied_corridors.py/switchback), as an add-on layer; canon HDA untouched | IN PROGRESS |
| 💧 | ue_stage_pack/blessed/ | copy of Blessed Boy's carillon + swarm outputs (his PC link is jammed) | copy running, unverified |

## MI picks (existing instances only, Content/EnvSandbox/Materials/Instances/Copernicus/)
Small (>C6) MI_Brass_FiligreeGold; mid (C4-C6) MI_Brass_Engraved; golem arms MI_Brass_HammeredPulse; large (C2-C4) MI_Brass_DeepSeaBell; bourdon MI_Brass_PatinaAnimated -> MI_Brass_Iridescent on wake (MI swap only).

## EXR import settings
sRGB off, RGBA16F / HDR compression, Nearest filter, no mips, Clamp.

## Manual for Brennan (not scripted)
- Cord skeleton FBX (Cutie) and MEL_lantern_nanny (morphs need a skeletal import; bundle at C:\Users\froma\lantern_nanny_bundle.zip, awaiting Brennan's OK).
- Saves: Brennan presses Ctrl+S himself.

## Open / placeholders
- Real doorway/arch widths unknown (only 6.18 m deck, 1.20 m stair, 2.10 m headroom, 48.2 m nave). roam_width_cm is a placeholder; verify after UE closes.
- decay_s is an estimate. C3/G3 sizes are extrapolated.
- Swarm weak spots: short 12-frame scatters, Chladni shapes read as lobes, some overlaps.
- Not done yet: the actor/Blueprint swap (hide instance -> spawn actor -> awake blend -> restore), the patrol splines, the Niagara template hookup. Sol should build these on the existing enemy/actor classes per CONTRACT.md, not new systems.

## Next steps (once Unreal is closed)
1. Verify ue_stage_pack against stage_manifest.json.
2. Headless commandlet import of static meshes + EXRs + point data to /Game/Staging/HoudiniForge/ (backup, skip on mismatch).
3. Brennan imports the skeletal pieces; Sol wires the actor swap + PCG add-on input into the Ocean Cathedral.

## Update 00:40 ET (per Brennan's sol_worker_prompts.json)
- Sol owns ALL UE staging and imports (Brennan keeps UE control; no bot imports). Luna owns the 1.6 walkability source.
- ue_stage_pack/blessed/: COMPLETE. 11 files, SHA-256 verified vs source (HASHES.txt), delivery_manifest.json. carillon_awake_points.* = awake_combat (alias awake).
- ue_stage_pack/lookdev/: CONTRACT.md + stage_manifest.json landed; NIAGARA_PICK.md (existing swarm + strike-ring templates, verified paths) pending.
- ue_stage_pack/cutie/: building (export_manifest.json, FBX re-import measurements, versioned folder).
- teardrop_build/ (cathedral alcoves, suspension points, silhouette variation, LUNA_NOTES.md): in progress.

## Staged in UE + committed (2026-10-15)
Committed on `lane/houdini-forge-staging` and merged to main. 84 .uasset files, about 30.7 MB, all Git LFS.

**Asset inventory (`/Game/Staging/HoudiniForge/`)**
| Folder | Count | Contents |
|---|---|---|
| Carillon/Creatures | 8 | v1 BellSpirit, v2 ChandelierWraith, v3 BellGolem, v5 InvertedTower; one Arch and one Awake each |
| Carillon/Parts | 64 | Bells A5-G5 / C4-C6 with profile variants, FaceDiscs, Crown/CrownSpikes, Filigree, Halo, Bloom, Canopy, Cord, Yoke, etc. |
| Carillon/Skeletal | 2 | SKM_Carillon_Cords, SKM_Carillon_Cords_Skeleton |
| NPC/Dingle | 1 | SM_GPX_NPC_Dingle_LOD |
| LittleGuys/MusicBoxMimic | 2 | SM_LG_MusicBoxMimic_Arch_v3 / _Awake_v3 |
| Gaudy | 7 | *_gaudy_v2: Dingle_LOD, ChimeSnail Arch/Awake, PearlJellybell Arch/Awake, PearlJellybell_Queen Arch/Awake |

**Import settings:** headless `UnrealEditor-Cmd` using `-run=pythonscript` (import_*.py / reimport*.py / fix_skm_cords.py in Saved/Staging/GrokPrep/houdini_forge/). Remove Degenerates is OFF. Vertex color import is set to Replace.

**Bell MI pitch rule:** above C6 uses MI_Brass_FiligreeGold. C4-C6 uses MI_Brass_Engraved. Below C4 uses MI_Brass_DeepSeaBell.

**Anchor contract:** `ue_stage_pack\lookdev\CONTRACT.md`.

**Pending:**
- Gaudy v4 reimport with body-slot MIs: ChimeSnail and Dingle get MI_Brass_Engraved; Pearl Jellybell and Queen get MI_Brass_Iridescent. Owner: Lookdev Manager.
- In-editor vertex color/UV check.
- Dingle collar clearance, about 160 cm.
- Cathedral v3.1 is owned by Sol.
- Anim pack import (pending, editor must be closed or Claude lane): root at crown pivot, root motion off; mixed creature scales, verify scale on import; no sockets/UCX: add sockets on UE skeleton and generate Physics Asset; Strike_Ring f8 needs an AnimNotify driving the ring.
- Aeolian dressing (Brennan-approved, existing assets only, owner 💧 for UE placement, needs editor closed or Claude lane): Weingarten facade + RoseTracery at S0_Amin7; known blockers: facade floats 8-54m, not refit to windows.json, no collision, 2 MI-less slots (Lookdev Manager mapping to contract MIs). New versioned Aeolian map; Brennan Ctrl+S.
