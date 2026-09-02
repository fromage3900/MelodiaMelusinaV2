# Faraway Mother: PCG Ecosystem Architecture & Audio-Reactive Fabric Mountains
**Document Version:** 1.0.0
**Date:** 2026-09-01
**Target Engine:** Unreal Engine 5.8.0 | Blender 5.2 LTS | Houdini 22.0.368 | C++20 | Python 3.11
**Classification:** Canonical Technical Specification & System Architecture SSOT

---

## 1. Executive Summary & Core Design Thesis

### The Core Thesis: "Fabric is Geography; Landscape is Draped Anatomy"
Following the P0 *Sea Above* vertical slice (where "Water is Anatomy"), the P1/P2 Monolith *Faraway Mother* transitions the physical category error into tensile structures:
- **Tensioned Landforms:** Mountains are not static carved rock, but massive multi-kilometer woven sheets under active tensile loading.
- **Draped Anatomy:** Valleys and ridges correspond to anatomical folds, pleats, and gathers rather than classical fluvial erosion.
- **Acoustic Seams:** Musical resonance frequencies release or tighten landscape seams, opening physical traversal routes.

---

## 2. Four-Biome Procedural Ecosystem

The 8 km × 8 km procedural terrain (`LM_FarawayMother_Terrain` in `LV_FarawayMother_Prototype`) is partitioned into 4 distinct ecological and physical biomes:

```text
+─────────────────────────────────────────────────────────────────────────────────────────+
|                               FARAWAY MOTHER PCG BIOMES                                 |
+─────────────────────────────────────────────────────────────────────────────────────────+
   │
   ├──► [ 1. WeaveRidge ] (High Altitude / Max Tension: T > 0.60, Z > +1500 uu)
   │     - Geometry: Macro crests, tensioned seams, shoulder folds
   │     - Builders: MEL_mother_fabric_ridge, MEL_mother_shoulder_fold, MEL_mother_silk_vine
   │     - Material: MI_T_FarawayMother_Gown_CelestialSilkJacquard
   │
   ├──► [ 2. LaceCanopy ] (Mid-Slope / Moderate Tension: 0.40 <= T <= 0.60)
   │     - Geometry: Translucent lace trees, pearl berry understory, hanging veils
   │     - Builders: MEL_mother_lace_tree, MEL_mother_pearl_bush
   │     - Material: MI_T_FarawayMother_Veil_AquaticLullabyLace
   │
   ├──► [ 3. FrillValley ] (Lowland Basins / Low Tension: T < 0.40, Z < -1000 uu)
   │     - Geometry: Volumetric fog depressions, frill rocks, frill arches, brocade flowers
   │     - Builders: MEL_mother_valley_depression, MEL_mother_frill_rock, MEL_mother_frill_arch,
   │                 MEL_mother_brocade_flower, MEL_mother_fog_volume
   │     - Material: MI_T_FarawayMother_Corset_GildedAcanthusBrocade
   │
   └──► [ 4. ResonantSeamWay ] (Cymatic Nodal Corridors: |Chladni| < 0.12)
         - Geometry: Straight & curved fabric walkways, Heart Gate rhythm checkpoint
         - Builders: MEL_mother_walkway_straight, MEL_mother_walkway_curved, MEL_mother_heart_gate,
                     MEL_mother_head_silhouette, MEL_mother_hair_cascade
         - Material: MI_T_FarawayMother_Mantle_NightSkyVelvet
```

---

## 3. Mathematical Formulations & World Field Bus

### 3.1 2D Chladni Standing Wave Formulation
Surface displacement $Z(u, v)$ across the normalized unit domain $[0, 1] \times [0, 1]$ is evaluated using harmonic mode integers $(n, m) = (3, 5)$:

$$Z(u, v) = a \cos(3 \pi u) \cos(5 \pi v) - b \cos(5 \pi u) \cos(3 \pi v)$$

Where $a = 1.0, b = 1.0$.

### 3.2 Tension Gradient Vector Field
The physical surface tension scalar $T(u, v) \in [0, 1]$ is computed from the spatial gradient magnitude of the displacement surface:

$$\mathbf{T}(u, v) = \min\left(1.0, \frac{\|\nabla Z(u, v)\|}{8.0}\right)$$

### 3.3 Melodia World Field Bus Routing

All PCG graphs, Niagara particle systems, and shader material functions interface through standardized channels:

```text
[Melodia World Field Bus]
       │
       ├──► WorldField.Tension    : Controls PCG point density, WPO stretch, and silk vine sag
       ├──► WorldField.Resonance  : Maps harmonic mode (3, 5) to material pulse frequencies
       ├──► WorldField.Moisture   : Modulates understory pearl bush hydration and velvet sheen
       └──► WorldField.FilterFlow : Orients lace tree canopies along valley airflow currents
```

---

## 4. Multi-Frequency World Position Offset (WPO) Stack

Kilometer-scale fabric motion is evaluated directly in the vertex shader (`MF_FabricMountainWPO`) without CPU tessellation overhead:

$$\text{WPO}_{\text{Total}} = \text{WPO}_{\text{Macro}} + \text{WPO}_{\text{Medium}} + \text{WPO}_{\text{Micro}} + \text{WPO}_{\text{Wind}}$$

1. **Macro Swell ($\lambda \approx 1000\text{ m}$, Amp: $50\text{ m}$):**
   $$\sin(x \cdot 0.001 + t) \cdot \cos(y \cdot 0.001)$$
2. **Medium Folds ($\lambda \approx 100\text{ m}$, Amp: $15\text{ m}$):**
   $$\sin(x \cdot 0.01 + \text{Noise}) \cdot \cos(y \cdot 0.008)$$
3. **Micro Detail ($\lambda \approx 1\text{ m}$, Amp: $1\text{ m}$):**
   $$\text{Noise}(\text{WorldPos} \cdot 0.1) \cdot H_{\text{Cymatic}}$$
4. **Wind Response:**
   $$(\vec{W} \cdot \text{WorldPos}_{xz}) \cdot t \cdot \text{Turbulence}$$

---

## 5. Hero Music & Narrative Challenge Seam

### 5.1 The Heart Gate Rhythm Challenge
In the *ResonantSeamWay* corridor, the player encounters the **Mother Heart Gate** (`MEL_mother_heart_gate`):
- **Actor:** `APCGHeroMusicGraphHost` with attached `UMelodiaPCGNarrativeChallengeBridgeComponent`.
- **Challenge ID:** `challenge.mother_heart_gate`
- **Completion Flag:** `quest.p1_faraway_mother.heart_unlocked`
- **Idempotent Reward:** `reward.wardrobe.mother_velvet_mantle`

### 5.2 Traversal Capability Provider (`IMelodiaTraversalCapabilityProvider`)
Equipping the unlocked `mother_velvet_mantle` grants the **High-Tension Seam Glide / Slide** capability, enabling traversal across high-tension mountain ridges in the *WeaveRidge* biome.

---

## 6. Automation & Tooling Runbook

### 6.1 Ecosystem Generation
```powershell
# Generate deterministic PCG point distribution (30 pts per biome, 120 total)
python Tools/PCG/build_faraway_mother_pcg_ecosystem.py --points-per-biome 30

# Verify manifest integrity
python Tools/PCG/build_faraway_mother_pcg_ecosystem.py --verify
```

### 6.2 Level Assembly Verification
```powershell
# Run offline level assembly validation
python Content/Python/faraway_mother_pcg_assembly.py

# Live Unreal Editor staging (when inside UE Python environment)
python Content/Python/faraway_mother_pcg_assembly.py --apply
```
