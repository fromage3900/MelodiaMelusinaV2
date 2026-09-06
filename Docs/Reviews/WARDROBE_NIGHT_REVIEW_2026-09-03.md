# Wardrobe Night Review — 2026-09-02 evening → 2026-09-03 ~02:30

## What the night set out to do
Advance the interchangeable wardrobe (Nikki lens): GN loom builders, Copernicus
families, retopo route, canonical dress COP bake, hourly watch + subagent flock,
and one gift.

## Landed (verified, committed unless noted)
- MEL_garment_tension_folds: 29 nodes, PROOF PASS (5f6f7547). FLOAT_VECTOR fix.
- MEL_garment_xpbd_drape: builder constructs, XPBD_PROOF PASS — but headless
  BAKE is NO-GO (sim cache bit-identical, bake ops need editor). GUI-bake only.
- AntiqueDollRose cook PASS bfc292f7 — 9 maps 2048, std 42.9, vocab 0 collisions.
- ButterflyWingMembrane cook PASS 53d2a583 — 9 maps 2048, Iri std 50.1.
- Retopo script IMPLEMENTED 487080c8 — Quadriflow refuses _thick non-manifold
  headless; voxel fallback 180,895v -> 9,168v 100% quads, 20 slots kept.
- Canonical dress COP bake f6ad86cd — 4/4 fresh 1080sq, distinct hashes,
  AO 256 / Normal 4829 / Emission 240 / Roughness 87.
- Dawn Chorus gift staged + manifest/README/morning letter 3e81400b.
- Watch wardrobe-night-watch hourly, live; ledger OVERNIGHT_STATE.md.
- In flight: FirstLightDawn family cook (uncommitted parallax.py changes).

## Hard truths paid for (also in melodia-copernicus-dress-bake skill)
file-COP .cook() never writes; size_ref wants an image; tracingmode 2 skips
cage/high; custom slots take FLOAT only; wrangle class 0 = detail;
ROP downsamples to 1024 unless setres; Apprentice caps saves at 1920x1080;
sopimport needs usesoppath = 1; metric uv_overlap saturates post-pack.

## Scars (honest)
- Deleted ButterflyWingMembrane mid-edit once; restored, diff verified +9 only.
- Cook1-5 wrote nothing (stale Aug-28 PNGs believed briefly); cook4 rendered
  4x identical images (shared source) at 1024.
- Garbled subagent summaries (2) recovered via transcript grep, not assumed.
- Temp/ scripts vanish (gateway cleanup) — scratch moved in-repo, then swept.

## Open
- FirstLightDawn verify/stage/commit. True-overlap UV metric. Material-ID
  reassignment post-Quadriflow. ButterflyWing 818k full retopo run. Licensed
  host for true 4K dress maps. Editor-gated S4/S5 (MIs, ground-snaps).
