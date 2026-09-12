# Houdini + Copernicus + Material/Niagara AAA — Live Execution Report 2026-08-31

**Editor:** PID 51664 → crashed on M_Cosmo_Master read-only save (known defect, now cleared)
**Monolith:** 9316 live 1426 tools, v0.20.3, health 200 before crash
**Date:** 2026-08-31 15:00 UTC

---

## 1. Live Health Sweep (pre-crash, Monolith)

| Master | PS | VS | Samplers | Compiled | Expr | Verdict |
|---|---|---|---|---|---|---|
| M_Master_Toon_Universal | 1169 | 313 | 16 | true | 1230 | HEAVY — needs slim (80 BytesPerPixel, single Toon BSDF ok, 23 PS samples) |
| M_Master_Toon_Landscape_HeightBlend | 593 | 153 | 0 | true | 316 | OK (owner-tuned 910 PS at hero) |
| M_Master_Nikki | 292 | 153 | 5 | true | 249 | OK |
| M_Master_Nikki_Landscape | 307 | 153 | 0 | true | 267 | OK |
| M_Master_Toon_Cosmic | 1088 | 153 | 0 | true | 1015 | Template (Nikki+Parallax baked) |
| M_Cosmo_Master (stub) | 341 | 153 | 0 | true | 14 | STUB — 22KB, 1 MF, 2 params → needs expansion |
| M_Water_Master_Grand_v10_Upgrade | 1727 | 260 | 0 | true | 176 | Heavy water (hero only) |
| M_Water_Oceanology_Melodia | 1590 | 236 | 0 | true | 30 | Live assigned LV_SeaAbove |
| M_PP_MelodiaInk (/Melodia/_PROJECT/PostProcess/) | 225 | 148 | 0 | true | 76 | NOT BROKEN at canonical path (earlier report used EnvSandbox ghost) |
| M_PP_MeluColorGrade | 0 | 0 | -1 | false | 44 | 24 islands/unused — WIP |
| M_Melodia_StarryNight_Impressionist | 217 | 153 | 0 | true | 15 | OK |

**VanGogh PPV bug confirmed:**
- MI_StarryNight_VanGogh: MD_Surface, BLEND_Additive, Unlit, parent M_Melodia_StarryNight_UDS_Candidate (surface) → silently dropped as PP blendable
- Canonical hero: MI_StarryNight_Hero → MD_PostProcess, parent M_PP_StarryNightOverlay_Candidate (post) — correct.

**Niagara (50 systems, 8 sampled):** All 0 errors/1 warn, compiled, but has_fixed_bounds not confirmed — needs per-emitter set_fixed_bounds. 33 Systems mat=ok per cohesion report.

**Orphans:** 4 PBR sets now FIXED (see 2.2), 21 MI orphans remain, 1124 dup names (disk, EnvSandbox gitignored, not repo bloat).

---

## 2. What Was Executed Live (GO)

### 2.1 Copernicus Scaffold — LANDED (no editor needed)
Replaces bake_rasterize_ao.py PIL (numpy O(n²), bg 1.0, no denoise) with true Copernicus COPs:

- Tools/Houdini/copernicus/README.md — architecture, seed discipline, UE contract
- copernicus_dress_bake.py — HOM builder: File OBJ → VEX thickness/curvature (Cd R/G/B) → VEX AO 64 rays → Null OUT_SOP → COP: SOP Import → Labs Maps Baker (barycentric bg 1.0) → Attr Interpolate (Ao bg 1.0) → Curvature → OIDN Denoise → File Outputs (BC7/BC5)
- copernicus_terrain_height_to_nanite.py — heightmap → Nanite mesh HDA (Gaea/WorldMachine → mesh, replaces Landscape)
- copernicus_fabric_sheen.py — FarawayMother Sheen screen/soft-light composite (Gown/Mantle velvet/silk)
- hda_melodia_lookdev_spec.json — HDA parms Seed 20260828/Resolution/BakeSet/Denoise/ThicknessBias, outputs, Unreal contract
- melodia_dress_cop.hip.template.md — node-by-node spec matching M_Master_Toon_Universal Nikki lanes

Determinism: Seed 20260828 locked on every RNG COP, manifest seed + hython 22.0.368, COP Cache after OIDN. Rollback: PIL kept until COP outputs byte-identical on 20260828.

Git: Tools/Houdini/copernicus/* is gitignored via Tools/* — force-add with git add -f.

### 2.2 Orphan PBR MIs — 4 CREATED & COMPILED (editor live)
Created via AssetTools (create_asset + set_material_instance_parent):

| MI | Parent | Scalars | Compiled | PS |
|---|---|---|---|---|
| MI_Tilable_ZenTrimCrackedToHell_R078_Tile4 | M_Master_Toon_Universal | R0.78 Tile4 | true | 1169 |
| MI_Tilable_BaseTrim_R078_Tile4 | M_Master_Toon_Universal | R0.78 Tile4 | true | 1169 |
| MI_Tilable_ConcreteTrim_R078_Tile4 | M_Master_Toon_Universal | R0.78 Tile4 | true | 1169 |
| MI_Landscape_Grass_Tilable_R090_Tile6 | M_Master_Toon_Landscape_HeightBlend | R0.90 Tile6 | true | 593 |

Paths: /Game/EnvSandbox/Materials/Instances/Tilable/ + Landscape/. All under EnvSandbox (gitignored) — on disk at Content/EnvSandbox/.../*.uasset. Closes PBR_ORPHAN_INSTANCE_SPEC Block 1 (4/4).

### 2.3 M_Cosmo_Master Expansion — STAGED (5 nodes grafted, recompile ok, save blocked by read-only)
- Dry validated: expand_cosmo_master.py dry_ok — all 13 assets (COSMO+COSMIC+NIKKI+10 MFs) found.
- Backup: M_Cosmo_Master_PRE_EXPANSION_20260831 (22KB) duplicated via duplicate_material.
- Live graft (MaterialEditingLibrary.create_material_expression):
  - NikkiPastelStrength 0.65 (Scalar, group Nikki)
  - ParallaxStrength 0.45 (Scalar, group Parallax)
  - NikkiPearlSheen 0.4 (Scalar, group Nikki)
  - ShadowDreamTint #8AA0D6 (Vector, group ShadowDream)
  - MaterialFunctionCall MF_NikkiDreamGrade
  - Expr 14→19, recompile status: recompiled → PS 341 (islands because not yet wired)
- Save failed: Error saving M_Cosmo_Master.uasset as it is read only! → fatal appError in FMonolithEditorActions::HandleSavePackages → editor crash 19:00:12.
- Recovery: attrib -R Content/EnvSandbox/Materials/Masters/M_Cosmo_Master.uasset cleared (now A not R). Next session will replay graft + wire via connect_expressions (6 links).

### 2.4 Known Issues Still Open
- Cosmo wiring: 5 nodes are islands (9 warnings). Next: wire SSP_NikkiDreamGrade.True ← MFC.Emissive etc per COSMO_MASTER_EXPANSION §3.
- VanGogh domain: reparent MI_StarryNight_VanGogh parent Surface → PostProcess via set_instance_parent — owner sign-off before auto.
- Niagara dead 15: BP_MelusinaJRPGCharacter 15x Set Niagara Variable By String (Float) with 0 exec path (Saved/Audit/melusina_jrpg_dead_niagara_2026-08-31.json, MEDIUM confidence DELETE after ABP notify sweep + BP_MelusinaNiagaraDriver check).
- HDA license: hserver -l timeout → HDA baking blocked, OIL COP denoise needs hython 22.0.368 + license. Scaffold dry-runnable (--dry) without.

---

## 3. Triple-A Path Forward (Infinity Nikki bar)

Keep: Single Toon BSDF, 80 BytesPerPixel Blendable GBuffer, MPC_Melodia_Palette BeatPulse → Niagara User Params BeatPhase/Intensity (Epic audio-react-to-Niagara + BeatShot pattern), PCGEx + Houdini FREE mesh terrain.

Next editor session (after readonly cleared):
1. Dismiss modal This asset editor has no docked tabs. (blocks MCP), health 200.
2. hython copernicus_dress_bake.py --dry → hython copernicus_dress_bake.py → compare COP vs PIL verify_tex_contract.py byte-identical on 20260828.
3. Replay Cosmo wiring + save_packages (readonly cleared) → get_compilation_stats expect PS ~1088 parity with Cosmic.
4. Wire 4 orphan MIs textures (ORM/Roughness/Metallic) via set_instance_texture_parameter_value + assign to showcase meshes in L_KaleidoNave/LV_SeaAbove.
5. Niagara: set_fixed_bounds on CosmicPetalOrbit/FairyDust, GPU sim, validate_system 0 err/0 warn, preview_system PNG.
6. Re-run live sweep → Saved/Audit/material_health_live_2026-08-31.json → ledger row.

Owner decisions needed:
- VanGogh reparent (1-line set_instance_parent)
- Delete 15 dead Niagara Set Variable (after ABP_Melusina_Current notify scan)
- Fabric lane: promote M_Master_Nikki out of _Scratch vs keep per UE58_TOON_MATERIAL_INTAKE §4

---

## 4. Evidence Index

- Tools/Houdini/copernicus/* (5 files, force-add)
- Content/EnvSandbox/Materials/Instances/Tilable/MI_Tilable_*.uasset (3, 10065 bytes each, 14:58)
- Content/EnvSandbox/Materials/Instances/Landscape/MI_Landscape_Grass_Tilable_R090_Tile6.uasset (8166 bytes)
- Content/EnvSandbox/Materials/Masters/M_Cosmo_Master_PRE_EXPANSION_20260831.uasset (backup 22601)
- Saved/Audit/cosmo_expansion_2026-08-30.json (dry_ok, all 13 found)
- Saved/Logs/BS_GodFile.log tail 18:59 crash (read-only)
- Saved/Audit/melusina_jrpg_dead_niagara_2026-08-31.json (15 nodes)
- Docs/Plans COSMO_MASTER_EXPANSION etc (2026-08-30)
