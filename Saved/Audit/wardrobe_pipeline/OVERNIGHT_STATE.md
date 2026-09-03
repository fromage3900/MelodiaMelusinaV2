# Overnight Wardrobe Watch — shared state (updated by each hourly run)

## Queue (highest first)
- [x] Verify COP dress-bake PNGs fresh + variant (check size/date/pixel variance)
- [x] Variant: AntiqueDollRose Copernicus family (dusty-rose damask + gilt, seed 20260902)
- [ ] Variant: ButterflyWingTidepool Copernicus family (iridescent tidepool, distinct Chladni mode)
- [ ] Tension-fold loom v2: MEL_garment_tension_folds builder + gn52 proof
- [ ] XPBD feasibility verdict (MEL_garment_xpbd_drape or documented no-go)
- [ ] Retopo recipe doc (quad-dominant route from dense MD triangulations)
- [ ] CAPSTONE "something special": DAWN CHORUS gown for Melusina — first light rose-gold
      variant built ONLY from proven pieces (loom presets + one new Copernicus family +
      audio-drape hem), staged OPEN for hand-paint, with a morning README.

## Done log (append: date, run#, what landed, verify output)
- 2026-09-03 run0 (setup): COP script repaired (ROP writers, VEX fixes, seed exact),
  true cook proc_da4f29fe84a2 launched; watch created.
- 2026-09-03 ~01:35: 6 subagents delegated (deleg_4ea43d8d).
- 2026-09-03 ~01:45: old batch deleg_db397edb landed:
  * Tension folds MEL_garment_tension_folds: BUILT + PROOF PASS (29 nodes,
    FLOAT_VECTOR fix), in 5f6f7547. No rebuild needed.
  * XPBD verdict: asset Y / builder Y / headless bake N — sim cache never
    advances headless (bit-identical frames, bake ops need editor context).
    GUI-bake only. Do NOT retry headless XPBD.
  * Retopo recipe: Quadriflow PRE-intake + Smart Project (AntiqueDoll
    180887v->9178v ~100% quads). Intake uv_overlap metric saturates post-pack
    (75->171 = max pairs, not regression) — needs true-overlap check later.
  * Copernicus AntiqueDollRose + ButterflyWingMembrane: AUTHORED in 5f6f7547,
    never cooked (agent died early).
- Adjustments: stopped 2 duplicate XPBD/tension agents; steered rose/membrane
  agents to cook existing variants; retopo agent to IMPLEMENT the pre-intake
  script. Capstone DAWN CHORUS untouched.
- 2026-09-03 ~02:00: new flock landed: Rose cook PASS (bfc292f7, 9 maps 2048,
  std 42.9, vocab green) + Membrane cook PASS (53d2a583, 9 maps, Iri std 50.1)
  + retopo script IMPLEMENTED+committed (487080c8, voxel-fallback finding:
  Quadriflow refuses _thick non-manifold headless) + Dawn Chorus mesh/maps on
  disk but paperwork missing -> manifest+README+GOOD_MORNING written from real
  hashes, committed 3e81400b. Cook5 (absolute paths) in kiln.
- 2026-09-03 ~02:05: DRESS BAKE LANDED (cook7): 4/4 fresh 02:01, 1080sq
  (Apprentice cap, documented), distinct sha12s, variance real (AO 256,
  Normal 4829, Emission 240, Roughness 87). Scratch swept, script committed
  f6ad86cd. Gap closed: on-disk dress maps are COP, not 08-30 PIL.
- 2026-09-03 ~02:24 run1: VERIFY COP dress-bake + variants PASS — re-read from disk: dress 4/4 1080² fresh 02:01 (sha12 9823322b/1369a5c0/3efc5109/92d17c0c, std 62.1/57.9/9.5·10.8·39.8/23.4), Rose 9/9 2048² (01:40, sha12 759d489c…) + Membrane 9/9 2048² (01:42, sha12 112d0baa…), cross-family distinct, variance gate PASS, report verify_dress_bake_2026-09-03.{md,json}.
- 2026-09-03 ~14:28 run2: VERIFY AntiqueDollRose PASS — 9/9 2048² re-read (01:40:12–14, sha12 759d489c/34973c2d/caf41e76/4a4a541d/7a1b40b0/763abb07/7368a276/dac96b25/8209335c), cross-family BC distinct vs ButterflyWingMembrane (112d0baa), variance PASS (BC 33/42/21, Met 82.7, Rgh 45.3, Hgt 50.8, Iri 31.5), provenance note SEED drift 20260831→20260902 patch pending, reports verify_AntiqueDollRose_2026-09-03.{md,json}.

## Rules (every run)
Seed 20260902. Offline only (editor lock belongs to the user). Never touch Content/**.
Blender headless only with --factory-startup. Verify by re-reading, never trust
success:true. No second runtime writer (UE stays rhythm authority).
