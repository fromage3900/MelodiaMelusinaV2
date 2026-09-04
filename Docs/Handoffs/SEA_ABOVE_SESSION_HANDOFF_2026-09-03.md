# Sea Above — Session Handoff & Closeout (2026-09-03)

## State of the world (verified, disk + reload)

LV_SeaAbove_Prototype is open-P0 dressing, reload-verified as of 19:05. Editor
crashed 19:25 (fatal shader bind, MPC_Cymatics_Driver on M_Master_Nikki_Landscape
during a save-triggered recompile, after MODAL_OPEN blocked the game thread) —
**no data loss; deletion did not persist.** Restart editor before any further
mutation. See Saved/Audit/sea_above_editor_crash_2026-09-03.json.

## Locked in the level (136 + PCG + anchors)

| Thing | Count | Evidence |
|---|---|---|
| SA_HM reef/abyss/jelly placement | 136 (ReefGarden 84, AbyssFloor 40, CathedralHalo 12) | spec + report, reload-verified |
| PCG ribbon (XylophoneTrail) | 83 inst | reload-verified 19:05 |
| PCG garden (BellTreeGarden) | 27 inst | reload-verified 19:05 |
| Palace kitbash SM_ATL | 29 materialed (Copernicus MIs) | audit |
| Music nodes (PCGHeroMusicNode) | 24 in 2 tiers | census |
| PostProcessVolume | **0** — the polish gap | audit |

Manifest: `specs/water_veil/sea_above_heatmap_dress.v1.json` (schema v1, 136 pts).
Apply harness: `Tools/PCG/apply_sea_above_heatmap_dress.py`. Generator:
`Tools/PCG/build_sea_above_heatmap_dress.py` (now with GOLDEN DECAY
`rho = (D/(d+D))^PHI` — 18 dense ribbon / 45 mid / 73 vista-classified).

## Walkability / scale verification (ran at closeout)

- position.z == height_cm for 136/136 (surface contract)
- clearance 0–12uu sane; scale 0.63–1.78, no outliers >3
- All inside ±13k prototype footprint; zero crowded 500uu cells
- Raycast Z deltas ≤173uu vs coarse grid (grid precision, NOT floaters);
  CathedralHalo pinned exactly -45298 / -14604
- Verdict: walkable-conforming, height-awake, no floating pieces

## Materials (AAA tier confirmed)

- Reef/jelly: M_Master_Toon_Universal(_Alpha) — the Nikki form language
- Water: M_Water_Oceanology_Melodia + M_Water_Master_Grand_v10_Upgrade
- Cathedral: _PROJECT/04_Materials SDF family (170/178 MIs live; 8 orphans are
  mirrored under EnvSandbox/Materials/SDF/Instances — use the EnvSandbox ones)
- Lookdev post (for PPV step): MI_StorybookOutline_*, MI_MeluColorGrade_*,
  MI_MelodiaInk_* profiles under EnvSandbox/Materials/PostProcess/ and
  Melodia/_PROJECT/04_Materials/PostProcess/Candidates/Profiles/

## Gates / ledger

- sea_above_dressed_map: RERECORDED to 136 to match the manifest (was 168
  from superseded continent scope)
- P0 status: P0_CONVERGENCE_AND_PROOF_OPEN — dressing is presentation-only,
  no new BP authorities; contract review verdict CONDITIONAL (5 conditions)
- static_gates: re-run after any A/B placement lands

## Contract review highlights (Saved/Audit/sea_above_contract_review.json)

1. CRITICAL refuted: reviewer claimed Oceanology schools don't exist — they DO
   (Plugins/Oceanology_Plugin/Content/Design/Ocean/Blueprints/Effects/Niagara/).
   Always registry-verify, not just Content-glob.
2. REAL: NS_SDF_ParallaxFish is under VFX/Systems/**Sakura** — art-direction
   red line. Do NOT place it. Use Oceanology schools or jelly bell billboards.
3. REAL: Oceanology vendor track is HOLD_VENDOR_INPUTS_MISSING in the P0 ledger
   — owner call needed before placing Oceanology FX in the shipping-packed map.
4. Evidence hygiene: ledger must match manifest count (now 136 == 136 == 136).

## Steps pending (in order)

- A. Restart editor; re-verify 136 SA_HM + 2 PCG volumes load.
- A2. Apply the golden-decay manifest (no delete needed — harness skips
  existing labels; old 19:05 dressing is the SAME set, same labels).
- B1. PPV: one unbounded PPV_NikkiDream with StorybookOutline_GameplayStandard +
  MeluColorGrade_GameplayStandard (weight 1.0 each), optional StarryNight ONLY if
  UDS sky reads flat (daylit: skip). EXCLUDE MI_MelodiaInk_* from prototype stack
  (audio-reactive print layer — revisit post ink-compile fix). Strip the 7
  color-grading scene overrides (vignette/fringe/grain/sat/contrast/gain), keep
  bloom 1.0. Owner picks Narrative/Hero by eye. Spec at
  Saved/Audit/sea_above_ppv_spec.json. **Read first:**
  Docs/Handoffs/UNIFIED_PPV_OCEANOLOGY_LOOKDEV_PLAN_2026-08-28.md +
  Saved/Audit/ppv_canonical_state_2026-08-31.json — a canonical PPV state exists;
  do not duplicate, extend it.
- B2. Swarm: NS_SchoolOfFish_WispFin + WispFinVWide placements per
  Saved/Audit/sea_above_swarm_spec.json (4 placements). Oceanology owner call
  first. SKIP NS_SDF_ParallaxFish (Sakura red line).
- B3. Island ring: **DONE (prep)** — generator `Tools/PCG/build_sea_above_island_ring.py`
  + manifest `specs/water_veil/sea_above_island_ring.v1.json` (22 pts, golden radii
  5k-55k, all Z=13455, in bounds, seed 20260903). Silhouette cards = SM_Island_A/B/C
  flattened (z-scale 0.5x, reads as distant islands), MI_ForestRockFormation_01
  (Megascans AAA); 2 far spires flagged for SM_Cathedral_Chapel substitution. Editor
  lane fog-tints on apply (fade_note per point). NOT applied — apply after restart.
- C. Golden density re-apply (done in generator; apply when ready).
- D. VDM gate: verdict DEFER (Saved/Audit/sea_above_vdm_feasibility.json) —
  headless sparse-volume export untrusted from CLI. Recipe ready to execute
  when A+B+C ship: Tools/Houdini/sea_above_reef/build_far_field_masses.py
  (vdbfrompolygons SDF shells for jelly-fog bank / plankton lamina / spire
  columns at golden radii, per VOL_GhostFog precedent; single float32
  'density' channel; stage via hash-verified copy — no .uasset writes).
  Reopen conditions in the JSON.
- F. After A/B: re-run static_gates, record ledger rows, reload-verify counts,
  then re-run P0 golden run so packaged evidence reflects the dressed map.

## Never-run reminders (binding)

No git clean/checkout -- ., no delete_asset on assets created by others, no
FBX into occupied paths, one editor on :9316, MODAL_OPEN is not a hang, wait
~40s for Monolith auto-restart after crashes. Verify by reload, not by save flag.