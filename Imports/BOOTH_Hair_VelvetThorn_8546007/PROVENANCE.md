# BOOTH Velvet Thorn — Drill Twintails Hair (8546007) Provenance

**Status:** Source 3D hair pack staged for UE 5.8 Melusina hair presentation intake.  
**Do not treat this file as proof that Melusina/Melodia has imported these strand meshes into Unreal Engine Skeletal Mesh assets yet.**

---

## 1. Source

- **Publisher:** Velvet Thorn via BOOTH.pm
- **Pack Name:** Drill Twintails Hair — Structured Spiral Locks (BOOTH item 8546007)
- **Product Page:** `https://booth.pm/ja/items/8546007`
- **Direct Archive URL:** `https://booth.pm/ja/items/8546007`
- **Download Route:** BOOTH 0 JPY Free Download
- **Staged Archive File:** `Imports/BOOTH_Hair_VelvetThorn_8546007/VelvetThornDrillTwintails.zip`
- **Staged Archive SHA-256:** `PENDING_STAGING — compute via Get-FileHash -Algorithm SHA256 after download; do not invent`
- **Extracted Directory:** `Imports/BOOTH_Hair_VelvetThorn_8546007/extracted`
- **Intake Status:** Draft stub. No `.zip` on disk; no hash computed. Hash sentinel enforces second commit after real staging per `asset_recommendations.md:159` and `asset_recommendations.md:15`.

---

## 2. License Verification

The staged archive and extracted files are governed by:

**`BOOTH Free 0 JPY Commercial License / VN3 License Compatible`**  
Terms: Free for commercial use (商用利用: 許可), game integration permitted, modification permitted.

**License Terms & Rights:**
- 0 JPY acquisition cost.
- Commercial game inclusion and asset usage authorized by creator.
- Retain provenance record for project licensing audit compliance.
- Modification for skeletal binding, LOD, and material repoint permitted.

**Reference precedent:** existing staged perches verified under same model — `Imports/Environment/AnimeFoliage_Perch/PROVENANCE.md:12` and `asset_recommendations.md:174` (shop-perch 4561230) and `asset_recommendations.md:175` (青猫堂 5475631).

---

## 3. Contents Used & Geometry Audit

The expected archive contains structured drill/lock twintail mesh cards for strong distance silhouette:

- **Expected File Breakdown:** 10–16 files (FBX/OBJ + PNG textures + README/terms)
- **Expected Verified Polygon Count Range:** 6,000 to 12,000 triangles per twintail set (cards/locks, not Curves)
- **Asset Description:** Drill twintails — structured spiral locks with discrete card shells; geometric counterpart to the organic Abyss Empress layer.

**Representative Mesh Inventory (expected, to be confirmed on extraction):**
- `velvet_thorn_drill_twintails.fbx / .obj — Full twintail mesh (mesh cards/locks, not Curves)`
- `velvet_thorn_drill_left.fbx — Left drill lock`
- `velvet_thorn_drill_right.fbx — Right drill lock`
- `velvet_thorn_cap.fbx — Scalp cap / hairline mesh`
- `T_VelvetThorn_BC.png — BaseColor / albedo`
- `T_VelvetThorn_N.png — Normal map`
- `T_VelvetThorn_Sheen.png — Sheen/fuzz mask`
- `T_VelvetThorn_WindMask.png — Wind phase/stiffness mask`

**Geometry audit notes (to be filled after extraction):**
- Confirm strand type is **MESH (not Curves)** matching live assumption at `Docs/MELUSINA_BLENDER_WARDROBE_SSOT.md:91`.
- Confirm `sRGB false / TC_Masks` on sheen/wind masks and `sRGB false / TC_Normalmap` on normals per `Docs/MPC_UNIFY_FABRIC_PLAN_2026-08-20.md:79`.

---

## 4. Integration Decision & UE 5.8 Material Intake Rules

This asset pack is staged in `Imports/BOOTH_Hair_VelvetThorn_8546007/` as raw source material for Unreal Engine 5.8 hair presentation. It remains **presentation-only** this phase; battle wardrobe is deferred (`Docs/Research/INFINITY_NIKKI_PIPELINES_2026-08-14.md:88`).

**Intake & Material Rules for UE 5.8 (`Infinity Nikki` Aesthetic Alignment):**

1.  **Skeleton compatibility (authored, not solved):**
    - Validate actual mesh bone usage against `SK_Melusina_Skeleton` before promotion (`Docs/Research/INFINITY_NIKKI_PIPELINES_2026-08-14.md:72`). Share one Skeleton when names/hierarchy are consistent (`INFINITY_NIKKI_PIPELINES:221`). Same-skeleton hair uses `SetLeaderPoseComponent` via `MelodiaWardrobeComponent` (`Plugins/MelodiaWardrobe/Source/MelodiaWardrobe/Public/MelodiaWardrobeComponent.h:24`).
2.  **Import settings:**
    - `Normal Import Method = Import Normals` if FBX ships custom normals; else `Compute Normals, 60°` (`asset_recommendations.md:187`).
    - `Generate Lightmap UVs = false` for skeletal strands.
    - sRGB/compression fix per `Docs/MPC_UNIFY_FABRIC_PLAN_2026-08-20.md:79`.
3.  **Wardrobe slot:**
    - Maps to `EMelodiaWardrobeSlot::HairCharm` presentation and `ABP_Melusina_WaterHair` pipeline. The 6-slot vocabulary is `Body/Hat/Gloves/Shawl/Trail/HairCharm` (`Source/BS_GodFile/MelodiaIntegration/MelodiaNarrativeTypes.h:95`).
4.  **Kawaii physics presentation:**
    - Single `AnimGraphNode_KawaiiPhysics` rooted at `hair_root` on `ABP_Melusina_WaterHair` (`Docs/Handoffs/KAWAII_PHYSICS_PLACEMENT_AUDIT_2026-08-14.md:13`).
    - Baseline `damping 0.42 / stiffness 0.14 / limit 46°` (`Content/Python/tune_melusina_hair_kawaii.py:28`).
    - Bind `DA_Melusina_HairCollisionLimits` + `DA_Melusina_SkirtCollisionLimits` (`KAWAII_PHYSICS_PLACEMENT_AUDIT:16`; currently unbound per `KAWAII_PHYSICS_PLACEMENT_AUDIT:47`).
    - Validate via dedicated fixture `/Game/MelodiaIntegration/Tests/BP_KawaiiPhysicsPlacementProbe` (`KAWAII_PHYSICS_PLACEMENT_AUDIT:58`), not generic `BP_PhysicsPlacementSpawner` (`KAWAII_PHYSICS_PLACEMENT_AUDIT:26`).
5.  **Substrate Toon hair shading:**
    - Repoint to toon-hair instance from `M_Fabric_Melusina` opaque branch with `TP_Melusina` (`specs/toon_profiles/tp_melusina.json:2`) or `TP_Character`, `MF_ColorRamp3` pastel remap + `MF_NikkiDreamGrade`. Keep `Water (Advance).001` identity where present (`Docs/MELUSINA_BLENDER_WARDROBE_SSOT.md:29`).
    - Blendable GBuffer canonical; Adaptive Hero tier only (`Docs/Research/UE58_TOON_SHADER_EXTERNAL_PRACTICES_2026-08-14.md:41`). No native glints on Blendable (`UE58_TOON_SHADER_EXTERNAL_PRACTICES:32`).
6.  **Clipping:**
    - Authored `SlotCompatibility` + per-outfit `ClippingProfile` (`INFINITY_NIKKI_PIPELINES:22`, `:37`), not a full runtime solver. Keep dynamic skirt cloth disabled until skeletal deformation stable (`INFINITY_NIKKI_PIPELINES:75`).
7.  **Variant discipline:**
    - Versatile master reduces variants; transparency has its own perf treatment (`INFINITY_NIKKI_PIPELINES:21` / `UE58_TOON_MATERIAL_INTAKE:188`). No new hair master for this twintail — it is a mesh variant under the same presentation pipeline.

---

## 5. License Limits & Disclaimer

BOOTH assets permit commercial game distribution but prohibit standalone redistribution of raw source files. All files retained for internal game compilation.

**This provenance draft is not proof of UE import, not proof of hash, and not proof of runtime presentation.** After real download, replace `PENDING_STAGING` with the computed SHA-256 and update the extracted file count / polygon audit with measured values. Until then, treat this pack as **curated but not staged**, matching the remediation standard at `asset_recommendations.md:15`.

**Existing staged perches (reference):**
- `Imports/Environment/AnimeFoliage_Perch/` — 4561230 — SHA `FBC7EAEF27CB94520F5821F1280F3E80EDC628FD933E212C0575FF66360F7EC2` (`asset_recommendations.md:174`)
- `Imports/Audio/StringInstruments_Aoneko/` — 5475631 — SHA `456EC644E6D9B53EE89EAA613B6696CBA20B9DC4631704B8189AB41AD2B7A922` (`asset_recommendations.md:175`)

