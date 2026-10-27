# Faraway Mother HDA Convergence — working report (2026-10-27)

Mission: reconcile PR #542, verify Poitou HDA offline, inventory assets, prepare integration.
Read-only phase first; no live editor (Sol/Kimi lanes protected); isolated hython only (MCP `hython_run_script` = separate hython.exe process; nothing saved to production paths).

## GATE: PASS (PR reconciliation + offline HDA verification) / BLOCKED (Perforce check)

## VERIFIED
**P2 — PR #542 vs workstation** (fetched to `pr542-salvage`, f5b6d1b20; 18 files):
- `layout_v0.json` — IDENTICAL (worktree diff 0). 14 of 16 VEX snippets byte-IDENTICAL.
- `snip/lscape.vex` IDENTICAL modulo CRLF.
- `snip/kit.vex` — NEWER_LOCAL (2026-10-22 H22 `addprim` wiring fix).
- `build_poitou_hda.py` — NEWER_LOCAL: worktree Oct 22 (545 lines) adds the pound-lock feature
  (`lock.vex` + piano-key note wrangle + `collision.vex` proxies as output 7 + full `f_lock` parm tab);
  PR copy (514 lines) predates it. PR_ONLY: none. Local-only companions not in PR:
  `snip/{lock,collision,iles}.vex`, `snip/{parms,skirt,water}.py`.
- Verdict: workstation is the authority; PR #542 = provenance/recovery of an older snapshot.

**P3 — isolated hython Gates 0/2 on `Tools/Poitou/hda/poitou_layout_live.hdalc`:**
- sha256 `2a12f...` recorded in `Saved/Audit/tmp/poitou_layout_gate02.json` (full hash in file);
  3,931,? bytes (see JSON; file mtime Oct 27 family — recorded in JSON).
- Gate 0 PASS: definition installs; node type `poitou_layout_live_v6` (Sop, "Poitou Layout Live", v1.0);
  102 exposed parms including the `f_lock` tab (lock_on, lock_u, lock_chamber_l, lock_coping_h,
  lock_gate_style, lock_steps_n, lock_step_note_base, jetty_len, jetty_wid, lockhouse_style,
  lock_ornament, lock_lamp, lock_bridge) — proving the binary was built by the NEWER local builder.
- Gate 2 PASS: instance cooks with 0 node errors; 8 top-level outputs (idx 0..7): landscape(9 prims),
  points(14,260 pts), route_curve(261), skirt_mesh(14,280/14,000), water(12,275/9,847),
  masonry(447,052/329,439), generated(571,346/278,322), collision(13,259/678). Two extra idx-0
  outputs are internal to child subnets (heightfield_1km, create_mask_layers) — not defects.
- Determinism: two forced cooks produce identical per-output point hashes.
- Drive: `lock_on` 1->0 changes output geometry (proven), restores on 1.
- UE attributes intact: `unreal_material` paths present on landscape (MI_Poitou_Landscape_Nikki),
  skirt (MI_Poitou_FarStone), water (MI_WaterV10_Integrated_CalmPond), masonry/generated
  (MI_Poitou_Arase_Brick, Poplar_Band1, Ruin_Limestone; M_Limestone_Rubble_Core, M_Tufa_Stone_Blocks),
  collision (M_Poitou_Stone_Plinth).

## PRESERVED
- All local work (newer builder + lock/collision snippets untouched).
- Heart Gate V3 (`Assignment2/HoudiniPrototypes/faraway_almost_gate_v3.py`, modified today 19:29) — Kimi's active file, not opened for write.
- Live UE level and all Content/ assets — no editor operation performed (Sol's lane).
- Perforce: no submit attempted; server down anyway.

## CHANGED
- No commits yet this task. New files only under `Saved/Audit/` (this report, gate JSONs, debug JSONs).
- Registry NOT modified (per mission: no registration before acceptance; pins should be added by
  integrator from the measured numbers above).

## P4 — Asset inventory (newest actual versions)
- Heart Gate V2: `faraway_heart_gate_v2.py` (Oct 27 15:54) + staging `FarawayHeartGateV2_20261027_01..11`.
- Heart Gate V3 (Kimi, ACTIVE — hands off): `faraway_almost_gate_v3.py` (Oct 27 19:29) + staging
  `FarawayAlmostGateV3_20261027_01/02`; related `faraway_almost_gate{,_geometry,_ornaments}.py`.
- Hero terrain: `Saved/Staging/HoudiniForge/FarawayHeroComposition_20261027_01` (FarawayHeroTerrain.hda,
  ±4 km global coords) — live in `L_FarawayMother_Blockout` as `HDA_Faraway_ContinuousLandscape_LIVE`.
- Hero monolith R&D: `FarawayHeroMonolith_Luna_20261027_01..04` + `faraway_hero_monolith_rnd.py`.
- Village: HDA authority `FarawayVillage_20261026_11_Artist`; native revision `FarawayVillage_20261027_Stairs03`
  (sha256 79e7c0ec... in CURRENT_STATE.md); live actor `HDA_Faraway_Village_Foundations_LIVE_20261026`.
- Registered Faraway HDAs (hda_registry, all active, Gate-2 green per registry notes 2026-10-23/24):
  heart_gate, silk_peak, frill_arch, lace_bridge, terraced_island, motherfold_basin, silk_ribbon,
  orchard_tree — builders under `Tools/Houdini/faraway/` (gitignored `Tools/*` — same force-add
  caveat as poitou_abbey_builder).
- ClothTrim consumers: EnchantedInteriors KB3D_ECI_FabTavernClothTrim material+textures;
  `MI_T_ClothTrim_{Base4K,Gingham,Linen,Plush}`; `Content/Python/cloth_trim_textures.py`.
- SilkMountainRange + hand-authored Nanite cloth/rock: owner-authored, not present in repo paths
  (owner's private workspace) — recorded, not pursued.

## NOT RUN
- Perforce opened-files check (server localhost:1666 refused — server not running).
- The recovered builder itself (scene-clearing script) — per mission, only in a disposable workspace;
  not required since Gate 2 proved the already-built binary.
- Any UE editor / PIE / packaging proof (Sol owns the editor).
- Gate 1 (UE import) — not in scope tonight.

## BLOCKERS
- Perforce server down: reconciliation of opened files/changelists deferred until the server is
  restarted. Not blocking the git-side conclusion.

## NEXT (single smallest step)
Integrator pins `poitou_layout_live` into `hda_registry.v1.json` with the measured output counts
above (copy from `Saved/Audit/tmp/poitou_layout_gate02.json`) and force-adds the newer
`build_poitou_hda.py` + `snip/kit.vex|lock.vex|collision.vex` (gitignored `Tools/*`) so PR #542's
recovery can be merged as provenance without ever overwriting the newer local builder.
