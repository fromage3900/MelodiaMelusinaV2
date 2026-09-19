# BROOCH V11 REPAIR — 2026-09-19

Repairs the v11 petal-split regression documented in BROOCH_GN_STAGING_FINDINGS_2026-09-18.md.
All fixes are asset-side in `Tools/gen_flower_brooch_v10.py` (v11.2). Rebuild logs:
`v11_repair_full.log` .. `v11_repair_full5.log` (1-4 failed for the reasons below; 5 shipped).

## Root causes found (probe chain: probe_v11_repair → probe9 per-link bisect → probe10 subtree dump)

1. **THE OVOID (closed-shell silhouette).** The v11 milgrain row converted its bead size
   with `Milgrain Size × 100` under the comment "socket is in mm, convert to units". The
   conversion was inverted (mm→units divides; the socket was already authored in tree units,
   0.012 u = 1.2 mm). Result: 48 beach-ball spheres of 1.2 u radius centered at z≈0 — the
   0.498 u-tall symmetric "closed bud" ovoid that ate the flower silhouette from every angle.
   Isolated by cumulative per-link bisect (`probe9_cumulative.log`): +gold milgrain material
   jumped h 0.0706 → 0.4976; every other gold part innocent. Fix: wire Milgrain Size straight
   into the proto sphere radius.
2. **Petals/dangles undersize (19/16 mm parts).** The split trees are authored in raw petal
   units (~3.5x smaller than the body's mm() composite). The render rig compensated with
   absolute RS overrides (0.722/0.769). Asset-side fix: solve each split tree from
   measurement at land time — RS = wanted_span / authored_span (petals want 1.10 × target,
   dangles 1.00 × target). Solved: petals 0.7870 (span 83.9 → 66 mm), dangles 0.9349
   (span 64.2 → 60 mm).
3. **Duplicate "Real Scale" socket on GN_BroochPetals_v10.** `clone_interface` copies the
   body's Real Scale input; `build_petals` then added a second one. Fix: reuse-if-present.
4. **attach() AttributeError ('NodeTreeInterfaceSocketGeometry' has no 'default_value').**
   The modifier sync iterated interface inputs and read default_value unguarded; geometry
   input sockets (Outline pass) raise. Fixed in attach() + ensure_petal_object() +
   ensure_dangle_object() (guard + skip). This is what killed the v11_full_rebuild4 final attach.
5. **gn_only() measurement allowlist.** It kept only `GN_FlowerBrooch*`/`GN_BroochDangles*`
   enabled while measuring, so a `GN_BroochPetals*` modifier was hidden and measured 0.0
   (petals solve silently skipped, RS left at 1.0). Added GN_BroochPetals to the allowlist.

## Incidents during repair (both caught, both fixed)

- First K-ratio attempt (S×3.482/S×3.710) poisoned the solve: the dangles at 2.66 RS entered
  the hero+dangles union measurement and the solver shrank the hero to 21 mm to compensate.
  Reverted; replaced with the measured per-tree solve above. The rig's 0.722/0.769 are
  ABSOLUTE values that only equal S×K at S=0.2073 — K formulation is wrong for other genomes.
- `_solve_split` first passed the BODY tree name to build_dangles, which uses its name
  argument as-is → it deleted and replaced `GN_FlowerBrooch_v10` with a dangles tree → the
  following petals clone found no "Petal Count" → KeyError. build_dangles must receive
  dangle_tree_name(used); build_petals receives the body name. Documented at the call site.

## Save blocker (environmental, not code)

`Saved/MelusinasHouse/FlowerBrooch.blend` carried the Windows READ-ONLY attribute
(set after the 2026-09-18 07:20 save). Rebuilds 1-4 ran fully and then failed to save
("Cannot save blend file ... not writable"). Cleared with os.chmod 0o666; rebuild 5 saved.

## Verified result (rebuild 5, saved 2026-09-19 01:49)

- Hero: dims [59.72, 60.0, 21.41] mm, err 0.0% vs 60 target, no re-solve needed
  (the milgrain fix alone restored the v10-era solve). All 7 genomes err 0.0%.
- Per-material census: MID_Metal_Petal spans the full 59.72×60.0 — petals are the widest
  element again. Outline shell wraps the squat flower (was wrapping the ovoid).
- Probe census (`probe_v11_verify.log`): hero bbox [0.6005, 0.6029, 0.2148] (was 0.51 tall),
  petals [0.663, 0.664, 0.254], dangles [0.611, 0.247, 0.106], sentinel verts = 0.
- Vision check on renders: hero = open gold sunburst flower with beaded rim, no cage/ovoid;
  petals solo = open blooming rosette, complete petals. (`v11_repair_verify/*.png`)
- Lissajous veil spike re-rendered on the repaired base: `spike_veil_beauty.png`,
  `spike_veil_sil.png` — woven 3:2:5 lissajous wires + beads, clean symmetric silhouette,
  no defects (vision-checked). Citadel spike also re-rendered.
- Website pass re-run from the repaired blend (BLEND override):
  `website_pass_20260919_v11repair.log` → outputs under `Saved/Website/Brooch/`.

## Render-side rig note

`Tools/brooch_pres_rig.py`'s RS guard (`_cur < 0.5 * hero`) now correctly skips — the
assets carry their own solved scale. The guard stays as a safety net for stale blends.
