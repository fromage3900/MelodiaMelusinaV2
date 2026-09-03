# Handoff — Material Pipeline Reorg-Verified + Core Standard Sweep (2026-08-15)

**Pick up:** `Saved/Audit/{material_folder_reorg_verified,straggler_niche_rework,pbr_dedupe_quarantine,pbr_dedupe_deleted,full_pbr_sweep,core_standard_sweep,core_standard_summary}_2026-08-15.json` · commit `4dbc4e12` on `feature/repo-lockin-20260813`

**Editor:** one UnrealEditor (verify `Get-Process UnrealEditor` + port 9316 ping — **never trust a PID**; the editor cycled 3x this session: 51812→55784→40288).

---

## What landed (all verified by re-read)

### Phase 0 — Reorg verified + evidence corrected
- **Disk truth: the SDF reorg DID land** — 53 masters at `Masters/SDF/`, 0 at root, `_Scratch/` holds 30 items (landscape quarantines + Universal backups). The audit JSONs recording `moved:0/57 FAILED` were stale evidence of the pre-chmod-fix first attempt.
- Referencer sweep: **0 broken parents** across 173 SDF MIs (loaded + parent read-back), **0 referencers at old `Masters/M_SDF_*` paths**, all 133 referencers at `Materials/SDF/Instances/`.
- T3D baseline: catalog Nikki paths fixed `_Scratch`→`Masters/`; Nikki baselines re-exported via `verify_baseline.py --update` → **55/55 clean, 0 drift, 0 failed**.
- New evidence: `material_folder_reorg_verified_2026-08-15.json`.

### Phase 1 — Straggler niche rework (owner: "make them into more niche materials")
- `M_HybridWater_SDF_Inst` → **`Masters/SDF/`** (SDF-Hybrid Water niche; parent `M_HybridStone_SDF`; 0 refs).
- `_Scratch_WaveScaleFixTest` → renamed **`M_Water_WaveScaleFix`** in `_Scratch/` (compiled water master: 81 exprs, Gerstner/caustics/shoreline set; 0 refs).
- `M_Master_Toon_Universal_NikkiChainRepair` + `_V2` → `_Scratch/` (consolidation references; 0 refs).
- `M_Master_Toon_Universal_NikkiChainIntegratedV1` → renamed **`M_Master_Toon_Universal_NikkiChain`** (stays at `Masters/`; **8 NikkiIntegrated MIs verified resolving**).
- Masters root: 62 → **58**. Evidence: `straggler_niche_rework_2026-08-15.json`.

### Phase 2/3 — Dedupe, quarantine-first (owner-approved)
- **718 duplicate mesh twins staged** (moved, not deleted) to `Meshes/_staging_dedupe_2026-08-15/`; keep-referenced logic handled the 2 edge cases exactly (floorFull keep root; template-floor keep twin); 0 failed.
- **Phase E clean** → 724 staged assets (718 + 6 package sidecars incl. zero-ref `MI_Env_LowPolyCrystals`) deleted with per-asset zero-referencer proof. **0 bad slots, 0 unfinished MIs, 1,686 meshes scanned.**
- Evidence: `pbr_dedupe_quarantine_2026-08-15.json` (718 rows) · `pbr_dedupe_deleted_2026-08-15.json` (724) · `full_pbr_sweep_2026-08-15.json`.

### Phase 4 — Core standard sweep (owner: LayerA + per-slot PBR + ShadowDream + verified; no default maps)
- **Refined default set created** (7 maps): `Textures/Defaults/T_Default_{Albedo,Normal,ORM,Roughness,Metallic,Height,AO}` (built from ZenTrim_Base4K + T_Neutral_ORM).
- **117 MIs routed** (class A null-albedo → defaults; class B noise-albedo → defaults; class C degenerate TW → normalized to 1.0 with prior values recorded).
- **88 `_Loose` MIs** that rendered the master's abstract-noise albedo (`sbs_-_seamless_abstract_pack`) → refined defaults + LayerA + ShadowDream. **0 noise defaults remain across 1,468 mesh-referenced MIs.**
- **ShadowDream: 0 missing, 0 wrong values** (all 1,468 = 0.3).
- **35 remaining `textured_bad` = ALL procedural/lookdev allowlist** (Baroque/Zen/Escher/Showcase2/Preset/Sakura water+petals/CosmicOrrery) — exempt per owner; every one **polished** (ParallaxStrength 0.35 + DreamRimStrength 0.25 + DreamIntensity 0.3).
- Final layer-A: textured_ok **1582→1782**, textured_bad **153→35** (allowlisted), flat_bad 0. 240/240 changed assets saved.
- Evidence: `core_standard_sweep_2026-08-15.json` · `core_standard_summary_2026-08-15.json` · `layer_a_state_2026-08-14.json` (refreshed).

## Git
- Committed: **`4dbc4e12`** `feat(materials): verified SDF reorg, straggler niche rework, dedupe quarantine, core standard sweep` (13 files; pre-commit LFS/size gate passed). Exact paths only — **foreign pre-staged files from the 08-14 session left in the index** (convert_masters_to_substrate_toon.py, expand_nikki_masters.py, 4 baseline .t3d re-exports, etc.).

## Scripts added this session (Content/Python/)
- `quarantine_phase_d.py` — Phase D quarantine-first (move to staging, zero-ref delete gated on Phase E)
- `phase_e_verify.py` — binding-safe Phase E re-census (MaterialEditingLibrary param getters absent in this UE 5.8 binding)
- `delete_staged_dupes.py` — delete staged dupes only after Phase E clean + per-asset zero-ref proof

## Traps hit this session (extend AGENTS.md rule set)
1. **`rename_loaded_asset` with a NAME change leaves a full-size stale duplicate at the source path** (the 4 same-name folder moves were clean). Same-name moves are the safe pattern; name-change renames need a disk-verify + cleanup pass.
2. **`EditorAssetLibrary.load_asset` / `does_asset_exist` fail without the asset-name suffix** (`path.name`); `get_referencers` requires package-name form + `AssetRegistryDependencyOptions`; `MaterialEditingLibrary` param getters (`has_material_instance_parameter`) absent — use `material_query` or direct MIC override-array reads.
3. **`__file__` is undefined in Monolith run_python stdin execution** — scripts run via stdin need absolute paths.
4. **`MODAL_OPEN` "This asset editor has no docked tabs"** blocked the game thread once (dismissed via window message; port recovered). Not a hang (AGENTS.md rule 8) — but the "editor died" symptom repeated 3x this session; each time the editor was externally cycled and MCP returned.
5. **`save_dirty_packages()` needs `save_map_packages` arg** in this binding; and saves ALL dirty (incl. foreign lanes' work) — targeted `save_asset` per owned path is the rule.

## Still open (owner-call, unchanged from prior handoffs)
- 24 runtime duplicate short names incl. the real 2-location dup `MI_SakuraLandscape` (Masters/ + Instances/Sakura/); `MI_IridescentRock` also still at Masters root.
- 59 zero-override MIs; ~773 Textures_Shared non-byte-identical copies; 12 `_Scratch` zero-ref test assets.
- Universal master TriplanarPro parity + overhaul Stages A–E; SDF conversion track (VinylGroove/Facade_Baroque/CelestialStarMap + `M_SDF_ParallaxPulse` fix).
- Nikki BaseTint dedupe on `M_Master_Nikki` (verify `VectorParameter_0` dead before removing).
- Water: 9 native-integration promotion gates still OPEN; v11 blocked on them + `RefractionStrength` fresh-connection audit.
- `material_family_manifest_full.py` capture (AAA plan Phase 6) — still not run; do it in the next editor session.
