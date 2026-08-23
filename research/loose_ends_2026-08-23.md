# Loose Ends Deep Research — 2026-08-23

Source: MELODIA_DEEP_INTAKE_REPORT.md:104-189, ORCHESTRA_CONVERGENCE:173-382, PROJECT.md:101-116, gate_ledger.json:196-340.

## Closed This Session
- DECISION_LOG duplicate 044 → 044b (KawaiiPhysics) — citation hazard `MelodiaWardrobeComponent.h:3` `BS_GodFile/_DECISION_LOG.md:130`
- Niche research + live verification kit shipped `research/melodia_niche_cozy-horror_ue_workflows.md:1`, `research/live_verification_kit.md:1`, `Tools/verify_p0_live.py:1`
- rhythm_owner intent marker `Saved/Echo/live_verify_rhythm_owner_intent.json`

## Still OPEN — requires editor/build (cannot fake without one-editor PIE)

| # | Loose End | Fix | Verify |
|---|---|---|---|
| 1 | 42 FBX pipeline outputs 0 files, 0 material_map.json | Regen `build_procedural_fbx_assets.py:452` or import `KitbashExport/OrnamentMusic_WIP/Gothic/` (35 FBX) to `Content/EnvSandbox/Meshes/Ornament/` | Glob material_map.json !=0, toon remap to `M_Master_Toon_Universal` |
| 2 | 3 Celestial meshes 1.4KB empty | Re-import or Regen via TD pipeline | In-editor mesh viewer |
| 3 | No collision sweep | Run `bp_sweep.py` + in-editor collision profile audit | `project_state.py --view integration` |
| 4 | Atlantis/Oceanology PROVENANCE only | Complete download → `ingest_aaa_underwater_packs.py` | Content/EnvSandbox/Meshes/Atlantis/ |
| 5 | `MelodiaPCGNarrativeChallengeBridgeComponent` needs closed-editor build | `GenerateProjectFiles + Build.bat` | Ledger `music_world_key` PIE: pattern → flag `challenge.first_resonance_echo.completed` |
| 6 | Catalog `form.first_resonance_echo` Glide unproven | PIE chain: pattern → flag → FormUnlockedAgainst → equip Cos_Accessories_MelusinaV2 → Glide active, suppressed in `battle_session` | Ledger `wardrobe_gameplay_hook` |
| 7 | `static_gates` FAIL 2026-08-14: M_Master_Simple 25→26, M_Master_Toon_Landscape 290→304 | Re-baseline `Docs/T3D_Baseline/` or revert drift | `echo_run.py` static_gates |
| 8 | `hud_single_writer` — two GameInstance subsystems + stock UI question | Merge `MelodiaJRPGBattleOverlaySubsystem:64` into `MelodiaUIBridgeSubsystem:124`, answer stock render via `melodia_ui_get_battle_hud` | One-editor PIE |
| 9 | `WBP_MelodiaRhythmHighway` legend D/F/J/K vs live Q/W/O/P | Fix widget legend | Visual |
| 10 | JumpWindup gated `bIsCrouched` but crouch disabled | Wire `bJumpWindup`/`JumpWindupVisualDuration=0.4` | PIE anim |

## Backlog (P1-P2, not blocking P0)
- Quarantine dirs 12 (deletion Red-tier), 120 duplicate short names `bp_sweep`, 11 WIP masters in `Masters/`, `Exports/*.blend` 5.6GB LFS, double-dot `l_melodia_dreamstate..umap` typo — all `_TASK_QUEUE.md:24-71`.

## Next Live Session Checklist
1. `curl http://localhost:9316/health` 2. `python Tools/project_state.py --view integration` 3. `python Tools/bp_live_path.py` 4. `python Tools/verify_p0_live.py --all` 5. Build → PIE → `echo_run.py record <gate> pass` (probe-only = HOLD `AGENTS.md`)

