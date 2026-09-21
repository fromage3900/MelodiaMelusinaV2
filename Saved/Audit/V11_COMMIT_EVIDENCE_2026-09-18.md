# V11 Commit Evidence — 2026-09-18

**Branch:** `collab/laptop/brooch-sky-20260917`  
**Builder:** `gen_flower_brooch_v10.py` (headless, all 7 genomes)

---

## 1. C3 Petal Split

Petal block extracted from `build()` into reusable `petal_system(tree, gin, crown, phy, mat, flutter)`.  
Body tree calls it with `flutter=False` (invisible sampler for accent snap, stays time-free).  
Petals object calls it with `flutter=True` (live per-petal rotation via SceneTime).

New object: `FlowerBrooch_Petals`, parented to hero (identity local).  
New tree: `GN_BroochPetals_<genome>`, 217 nodes.

Sockets: Petal Amp (0.05 rad), Petal Rate (0.7 Hz), phase = index × 0.55.

**Evidence:** `Saved/Audit/v11_full_rebuild4.log`

    GN_BroochPetals_v10: 217 nodes | flutter amp=0.05 rate=0.7
    FINAL attach -> GN_FlowerBrooch_v10: verts=106135 polys=111534 dims(mm)=[59.72, 60.0, 21.41]

---

## 2. A1 Margin System

New socket: `Margin Exp` (0.2–4.0, default 1.0). Super-ellipse exponent driving the petal outline.  
n < 1 → needle/acuminate, n = 1 → round, n > 1 → squarish/cordate shoulders.  
Continuous interpolation between archetypes (replaces snapping).

Wired into `petal_surface()` as `w = (w_base) ^ margin_exp`.

---

## 3. Per-Link Dangle Lag

Each chain link now gets progressive rotation: `lag = (j+1) × 0.15` radians.  
The terminal pearl lags behind the hinge (the "quiver," not a rigid swing).  
Chain trees: 471–587 nodes (up from 351–437).

**Evidence:** `Saved/Audit/v11_dangle_lag_build.log`

    GN_BroochDangles_v10: 471 nodes | 8 chains | sway 12.0 deg @ 0.70

---

## 4. Filigree + Openwork

Full rim wire: a dedicated `CurvePrimitiveCircle` (64 res) at 0.94 × plate radius, swept with a round profile (0.012 units).  
Openwork: a second concentric wire (48 res, 0.006 radius) at +0.005 Z for a lace-backplate effect.  
Bypasses the cast (like dangles) so the wire stays crisp.

Sockets: Filigree Width (0.012 default), Filigree Depth (toggle).

---

## 5. Sparkle Stage 2

New object: `FlowerBrooch_Sparkles`, parented to hero (identity local).  
`GN_Brooch_Sparkles_v7` tree attached to it (49 nodes).  
Twinkle restored (SceneTime on own object, body stays fully cached).  
Standalone output (no passthrough geometry).

Companion: `gen_brooch_sparkles_v7.py` — builds tree + creates object in one pass.

---

## 6. Build Verification

All 7 genomes: 0.0% sizing error. 0 tracebacks. Material IDs intact.

    melodia_brooch_v1:      60.0 × 60.0 × 49.76 mm (target 60.0, err 0.0%)
    melodia_brooch_mini_v1: 32.0 × 32.0 × 28.03 mm (target 32.0, err 0.0%)
    melodia_brooch_halo_v1: 50.0 × 50.0 × 42.37 mm (target 50.0, err 0.0%)
    melodia_brooch_comet_v1: 68.0 × 68.0 × 58.26 mm (target 68.0, err 0.0%)
    melodia_brooch_nova_v1: 55.0 × 55.0 × 46.10 mm (target 55.0, err 0.0%)
    melodia_gala_tide_v1:   62.0 × 62.0 × 51.41 mm (target 62.0, err 0.0%)
    melodia_gala_umbra_v1:  58.0 × 58.0 × 48.36 mm (target 58.0, err 0.0%)

---

## 7. Files Changed

| File | Change |
|------|--------|
| `Tools/gen_flower_brooch_v10.py` | +840 lines: petal_system(), build_petals(), ensure_petal_system(), filigree, openwork, dangle lag, milgrain size socket, margin exp socket |
| `Tools/gen_brooch_sparkles_v7.py` | own-object sparkle field, standalone output |
| `Tools/brooch_pres_rig.py` | magic materials, keyframed animation, pin toggle |
| `Tools/brooch_sky.py` | Melusina Sky v3, genome auto-select |
