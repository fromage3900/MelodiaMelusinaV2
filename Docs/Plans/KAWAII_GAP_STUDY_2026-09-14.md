# Kawaii vs Ours — gap study 2026-09-14 (vendor headers + live CDO)

## What the vendor recommends (from our vendored 1.21.0 headers)
- Skirts: BoneSubdivision for leg-penetration + BoneConstraintSubdivision for
  horizontal (layered) gaps + feedback scale; limits via DA or PhysicsAsset.
- 5.6+: PhysicsAsset bodies usable as limits (PhysicsAssetForLimits), shared
  collision groups, bone-constraint DAs for cloth coherence.
- Teleport thresholds, warmup frames, per-chain damping/stiffness curves.

## Ours (live CDO, verified tonight)
HAIR (ABP_Melusina_WaterHair / hair_root): stiff 0.07, damp 0.3, limit 75,
subdiv 3 (657 dummies, perf warning), densify OFF, PhysicsAssetForLimits NONE,
BoneConstraintsDataAsset NONE, world collision OFF, DA = 1 root sphere (r8.5,
now DISABLED as helmet test).
SKIRT (ABP_Melusina_Current / c_kilt_master_x): stiff 0.18, damp 0.45, limit 45,
subdiv 1 + densify ON, constr-subdiv 3 (layer bridging ON), DA = 2 thigh capsules.

## Gaps (what we're doing wrong)
1. No PhysicsAsset bound on EITHER node — SK_Melusina_FIXED_Hair_PhysicsAsset
   sits orphaned; vendor's head-collision path unused. Hair has zero head/neck
   collision (hair skeleton lacks head bones; DA sphere was the only guard).
2. Skirt pelvis/hips uncovered (skeleton has no pelvis bone; thighs only).
3. Hair subdiv 3 without densify = 657 dummies (perf + stability); vendor pairs
   subdiv with densify or lowers count.
4. BoneConstraintsDataAsset unused — layered kilt panels share no coherence constraints.
5. Kilt Chaos ClothAsset is an empty stub (no skeleton/physics) — converge or delete.

## Vendor verdicts applied (2026-09-14, from portal docs + 1.21 headers)
- Damping doctrine 0.1-0.3 / Stiffness 0.05-0.2 / WorldDamping 0.5-0.8.
- Hair: WorldDampingLocation 0.35 -> 0.65 (was below doctrine).
- Skirt: Damping 0.45 -> 0.3 (top of doctrine).
- Inner (not Outer) spheres follow head shape — our disabled root sphere was
  Outer; if helmet breaks, rebuild it as INNER per vendor, not Outer.
- PhysicsAsset auto-collision path exists (1.17+); ours still unbound.
Both ABPs compiled clean, saved.

## Standing test
Hair root sphere OFF (saved). If helmet breaks: sphere was the jailer → build
proper head collision via FIXED physics asset. If not: weights/rig question.
