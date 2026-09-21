# Brooch FULL PLAN — 2026-09-19 (lighting rework + asset audit + polish roadmap)

**Authority:** supersedes `BROOCH_V11_SILHOUETTE_PLAN_2026-09-17.md` as the current task list;
`BROOCH_V10_GRANDMASTER_PLAN.md` remains the architecture record. Builder = `Tools/gen_flower_brooch_v10.py`
(v11.2), scene = `Saved/MelusinasHouse/FlowerBrooch.blend` (repaired + saved 2026-09-19).

## 1. Current state (all evidence-verified)

- v11.2 repair DONE: milgrain ×100 inversion removed, measured per-tree RS solve
  (hero 60×60×21.4mm target-exact, petals 66mm span, dangles 60mm, zero sentinel verts).
  Evidence: `Saved/Audit/BROOCH_V11_REPAIR_2026-09-19.md`, probe suite `probe_v11_*.py`,
  renders `Saved/Audit/v11_repair_verify/`. Committed d637bad4 + f26b0e82, pushed.
- Website set SHIPPED from the repaired blend: 6 loops + 24 stills, all frame checks OK
  (incl. sweep_umbral + turntable_editorial_dark, both failed pre-repair).
- Silhouette spikes PROVEN on the repaired base: `star_citadel`, `lissajous_veil`
  (`Saved/Audit/spike_veil_beauty.png` / `spike_veil_sil.png` — clean, no defects).
- Live relight test VALIDATED 2026-09-19: `Saved/Audit/scene_relight_v1.png` (§4).

## 2. Asset audit (2026-09-19)

### 2.1 Live scene inventory (13 objects)
| Object | Type | State |
|---|---|---|
| FlowerBrooch | mesh + GN_Brooch + Bevel_Detail + Outline | repaired, solved |
| FlowerBrooch_Petals | mesh + GN_Petals + Outline | solved RS 0.787 |
| FlowerBrooch_Dangles | mesh + GN_Dangles + Outline | solved RS 0.9349 |
| FlowerBrooch_Sparkles | mesh + GN_Sparkles_v7 | own object (twinkle allowed) |
| LAB_Cam | camera 50mm | NOT set as scene camera (defect, §4) |
| _LAB_key/_fill/_rim/_under/_spark | 5 lights | superseded by §4 spec |
| _LAB_panel_front/right | 3.2m/2.4m white cards | REMOVE (owner: "don't like the Lab cards") |
| temp_obj | empty mesh, hidden | DELETE (junk) |
| World | starry navy backdrop | KEEP (brand backdrop) |

### 2.2 Genome drift (finding #1 — fix in presets work)
`genome/melodia_brooch_v1.json` is stale in three fields: `default_graph` → `GN_FlowerBrooch_v5`
(real: v10), `lineage.sverchok` (SV_* trees retired — brooch is GN-only since 2026-09-16),
`module_sequence` lists v5-era modules (no petals/dangles/sparkles split). Action: genome v2 with
a first-class `silhouette` block (V11 plan §1) + corrected lineage. Old file stays as history.

### 2.3 Variants: 2 of 6 proven
| Variant | Status |
|---|---|
| star_citadel | SPIKED + rendered |
| lissajous_veil | SPIKED + rendered clean |
| aurora_fan | needs ARC placement mode (V11 §5) |
| crystal_burst | needs faceted shard prototypes, two whorls |
| shell_coil | needs spiral curve + swept terraced profile |
| dragon_lattice | needs fractal panels + boolean crown ring |
| golden_field (stretch) | phyllotaxis micro-petals; test at 128px first |

### 2.4 Scripts: canonical vs historical
- CANONICAL: `Tools/gen_flower_brooch_v10.py` (builder), `Tools/brooch_pres_rig.py` (staging +
  lighting authority), `Tools/brooch_pres_shot.py`, probe suite (Saved/Audit/probe_v11_*).
- HISTORICAL (do not extend): `sv_*.py` (Sverchok, retired), `capture_v4b/v5/card2/lab/silhouettes.py`,
  `render_studio.py`, `analyze_dump.py`, `recon_twobrooch.py`, `mat_recon.py`. Keep as record;
  do not wire new features through them.

### 2.5 Other assets
- Cut sheets: DXF nested per genome (mini/halo/comet/nova/v1) in `brooch_lab/export/` — physical
  production path exists; regenerate after any silhouette change.
- Renders: website set current; `brooch_lab/renders/` is v5-era (stale, keep as history only).
- Backups: ~110 timestamped blends in `backups/` — prune policy: keep labeled ones
  (preV10run/preSVkill/cleanup) + last 10 timestamped; archive the rest to G: with the owner.
- CurveFillet addon: NOT in this repo. Gate for P2: confirm it has a headless Python API
  (then drive it in the rebuild) or it becomes one live-Blender pass. Do not fake headless use.

## 3. Lighting rework — SPEC (validated by test render)

Owner direction 2026-09-19: drop the Lab cards ("maybe a floor is fine"), stronger rim,
wisely varied light points. Test render `Saved/Audit/scene_relight_v1.png` proves it:

- DELETE `_LAB_panel_front` + `_LAB_panel_right` from the saved scene.
- KEEP a matte near-black floor (base ~0.02, roughness 0.9) — grounds the piece; enlarge so the
  floor edge stays out of frame (test showed a faint floor-edge shape bottom-left).
- KEEP the starry backdrop world.
- Rim becomes TWO kickers (the luxury tell):
  - Rim L: AREA ~320W, warm gold (1.0, 0.85, 0.60), behind-left, small (0.35) — carves petal tips.
  - Rim R: SPOT ~420W, cool lavender (0.75, 0.80, 1.00), behind-right — separates beads/dangles.
- Key: warm AREA ~200W size 1.5 (soft metal modeling, not flattening).
- Under-fill: AREA ~90W (dangle undersides). Gem spark point stays (fire).
- Front fill + panels: removed (they caused the flat "lab card" look).
- Palette note: warm-gold vs cool-lavender kickers complement the pearl-pink/gold/lavender palette —
  vision-verified "tasteful, luxury product shot" in the test.
- OWNERSHIP: lighting authority = `Tools/brooch_pres_rig.py`. The saved scene keeps only floor +
  backdrop + LAB_Cam; the rig builds lights per shot. Set LAB_Cam as the scene's active camera.

## 4. Polish roadmap (ordered)

| # | Item | Scope | Gate |
|---|---|---|---|
| P1 | Silhouette presets: genome v2 `silhouette` block + builder branch; ship citadel + veil | builder + genome | variant contact sheet 256/128/64px, icon legibility, silhouette-distance separation |
| P2 | CurveFillet pass on wire joins (veil crossings, dangle figure-8 links, filigree-to-rim) | one polish pass | headless-API check first; render diff vs current joins |
| P3 | Center gem + scene hygiene (gem in the dark center dish; set LAB_Cam active; delete temp_obj; apply §3 to the SAVED scene) | small tree tweak + scene edit | relight render re-verified |
| P4 | Website re-pass on the relit scene | pres rig + pass script | 6 loops + 24 stills all OK again |
| P5 | Remaining variants, owner pick order (aurora_fan needs ARC mode built first) | builder features | per-variant icon gate + census + sizing 0.0% |
| P6 | Parametric wing builder (venation/pair-count/membrane genome fields; registers in Melodia Studio; reuses P2 fillet work) | new GN builder | same evidence standard |
| — | Audio-reactive sparkle/sway | PARKED — MelodiaCore rhythm lane, not a bake | (rhythm pillar drives presentation) |

## 5. Evidence standard (unchanged)

A gate is done when its render + assertion JSON exist and the check passes — no prose-only
certification. Read-only probes for forensics; only the builder re-saves the blend
(auto-backup + save, write-open check first).

## 6. Execution status (2026-09-20)

P1 — Silhouette presets: PLUMBING + GATE COMPLETE.
- Canonical variant home: `Tools/brooch_silhouettes.py` (ported from the historical spike;
  trees `GN_BroochSil_Citadel` / `GN_BroochSil_Veil`; importable, side-effect-free). Builder
  call site lands after each genome's final solve, guarded, driven by per-genome
  `silhouette.active` ('flower' = none).
- Genome v2: `genome/melodia_brooch_v2.json` — stale v5 graph/lineage/module_sequence
  corrected; `silhouette` block added (flower/star_citadel/lissajous_veil, span_factor 1.15).
  Validates clean through `brooch_genome.load_genome`.
- ICON GATE PASSED: `Saved/Audit/sil_icons/` (18 native renders: 3 presets x beauty/sil x
  256/128/64) + `sil_presets_contact_sheet.png`. Vision verdict: all variants legible at 64px,
  silhouettes clean, citadel = star-fort crown, veil = woven wires, no clipping/floating.
  Solves: citadel x1.705, veil x2.672 -> span 0.946 = plate 0.822 x 1.15, exact.
- Builder no-regression run: `Saved/Audit/full6_noRegression.log` (canonical genome, flower
  default) proves the call site does not perturb the shipped build.
- Open: per-genome preset switch on request; DXF cut-sheet regen after any silhouette change.

P3 — Scene hygiene + lighting rework: APPLIED TO THE SAVED BLEND (except the center gem,
still open as the builder tweak it is).
- Backup: `backups/FlowerBrooch_preScenePolish_20260920_004805.blend`.
- Deleted: `_LAB_panel_front`, `_LAB_panel_right`, `_LAB_rim` (old), `_LAB_fill`, `temp_obj`.
  Added permanent `_LAB_floor` (matte near-black). `LAB_Cam` is now the scene camera — the
  file no longer opens camera-less. Census verified: 11 objects.
- Rig per §3: key 200W warm / rimL 320W gold / rimR 420W lavender / under 90W / spark 16W.
  Verify render `Saved/Audit/scene_relight_applied.png`: luxury read confirmed (rim-carved,
  grounded, no blown highlights). OPEN FIX: under-light's long soft shadow intrudes
  bottom-left — halve `_LAB_under` to ~50W and re-verify.
- Ownership amendment: the saved scene now carries this validated resting rig; per-shot
  authority stays with `brooch_pres_rig.py` (PRES_* lights), unchanged.
