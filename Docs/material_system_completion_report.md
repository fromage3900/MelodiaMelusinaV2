# Material System Completion Report

**Date:** 2026-06-25  
**Mode:** Finalization (complete & stabilize — no redesign)  
**Project:** `BS_GodFile` / `Content/EnvSandbox/Materials`  
**Audit sources:** `audit_material_library.py`, disk scans, `MATERIAL_NODE_TREE_REVIEW.md`, builder scripts

---

## Executive summary

| Area | Status | Ship readiness |
|------|--------|----------------|
| **Primary spine** (`M_Master_Toon_Universal` + 13 `MI_Show_*`) | **Functional** — Substrate Toon BSDF, full thematic stack wired in Python | ✅ Ready after master rebuild + starter re-apply |
| **Landscape specialist** (`M_Master_Toon_Landscape_HeightBlend`) | **Functional** — Madoka/Itto/Nikki integrated | ✅ Ready after rebuild |
| **Water specialist** (`M_Water_Master_Grand_v6`) | **Built** — non-Toon translucent path (by design) | ✅ Ready (separate shading model) |
| **Impressionist specialists** | **Substrate Toon** per `setup_impressionist_materials.py` | ✅ Ready |
| **SDF / Melodia copy masters** (22 legacy on disk) | **Incomplete** — 22/65 masters lack `SubstrateToonBSDF` on disk | ⚠️ Blocker for SDF portfolio lane |
| **Instance library** (380 materials) | **Mixed** — 129 on Universal, 41 unknown parent, legacy `MI_Universal_*` remain | ⚠️ Needs reparent + archive pass |
| **Celestial / NASA** | **UE: procedural** via `MF_SpaceParallax`; NASA JPGs are MM-only | ✅ UE lane OK; MM lane unchecked |

**Verdict:** The **core portfolio material system** (Universal master + starters + trim sheets + landscape) is **production-ready after one editor rebuild cycle**. The **SDF/Melodia migration tail** and **dead MeshBlend refs** are the main blockers for full-library ship.

---

## 1. Pipeline completeness by system

### 1.1 Master materials

| Master | Builder | Substrate Toon (disk) | Output pins wired | Thematic layers |
|--------|---------|----------------------|-------------------|-----------------|
| `M_Master_Toon_Universal` | `setup_master_universal.py` | ✅ | BaseColor, Normal, Roughness, Metallic, Emissive → `SubstrateToonBSDF` | Nikki MF, Celestial MF, Madoka inline, Itto inline |
| `M_Master_Toon_Landscape_HeightBlend` | `setup_landscape_height_blend.py` | ✅ | Same Toon BSDF set | Madoka, Itto, Nikki MF (order differs — see standardization doc) |
| `M_Water_Master_Grand_v6` | `setup_master_water.py` | N/A (translucent) | Color, opacity, normal, emissive (water stack) | Nikki sparkle hooks |
| `M_Master_Impressionist_Toon` (+ Landscape) | `setup_impressionist_materials.py` | ✅ | Toon BSDF front material | Brush/impasto (separate family) |
| `M_Master_Toon_Unified` | `setup_master_toon.py` | ✅ on disk | Deprecated | Superseded by Universal |
| 22× `M_SDF_*` / hybrid copies | Melodia robocopy + partial conversion | ❌ | Legacy Default Lit / MooaToon graphs | SDF banding — separate from Universal thematic stack |

**Disk scan (2026-06-25):** 65 masters total — **43 Substrate Toon**, **22 legacy**.

### 1.2 Required output maps

| Map | Universal master | Notes |
|-----|------------------|-------|
| **BaseColor** | ✅ | Accumulator → Magical MF → Toon `BaseColor` |
| **Normal** | ✅ | Layer blend + `MF_NormalAdjust` + macro detail → Toon `Normal` |
| **Roughness** | ✅ | ORM split + gilding + Itto + wetness + audio pulse chain |
| **Metallic** | ✅ | ORM + gold lerp |
| **AO** | ⚠️ Implicit | ORM texture sampled; **no separate Substrate AO pin** — acceptable for Toon portfolio (contact/shadow via `MF_ShadowDreamGrade`) |
| **Emissive** | ✅ | Full accumulator (Nikki, Madoka, fairy, gold, audio, bloom) |

### 1.3 Instance generation

| Script | Parent master | Instance count (preset) | Status |
|--------|---------------|-------------------------|--------|
| `starter_instances.py` | `M_Master_Toon_Universal` | 13 `MI_Show_*` | ✅ Canonical; Madoka/Itto params exposed on 3 showcases (finalization pass) |
| `zen_instances.py` / `theme_instances.py` | Universal | 15+ Zen, Baroque | ✅ |
| `setup_trimsheet_instances.py` | Universal | ZenTrim + ClothTrim | ✅ |
| `setup_sakura_instances.py` | Universal + landscape/water | 8 Sakura | ✅ |
| `universal_instance_presets.py` | Universal (legacy) | 141+ dict entries | ⚠️ Deprecated — many still on disk |
| `setup_master_toon.py` | `M_Master_Toon_Unified` | Legacy `MI_Env_*` | ❌ 1 instance still on Unified (disk scan) |

**Instance parent scan (disk heuristic):** 129 → Universal, 8 → Water, 1 → Unified, 41 → unknown/other.

### 1.4 Trim sheet blending

| Component | Status |
|-----------|--------|
| `MF_LayerBlendAdvanced` + `MF_LayerHeightCompete` on Universal | ✅ |
| `trim_layer_presets.py` height LERP presets | ✅ |
| `setup_trimsheet_instances.py` | ✅ 4 trimsheet + cloth variants |
| `audit_zen_trimsheet.py` | ✅ AAA audit script exists |

### 1.5 PCG-driven variation

PCG assigns **material instances** to scattered meshes (`pcg_portfolio_standards.py`, Sakura/greybox setups). No PCG graph changes required for material finalization. Instance presets (`MI_Sakura_*`, grass/rock MI) reference Universal/landscape parents correctly in builder scripts.

---

## 2. Thematic family completion

### Nikki (Infinity Nikki environment)

| Check | Result |
|-------|--------|
| Material functions (`MF_Nikki*`) | ✅ 4 functions on disk + wired |
| Master param group `Nikki` | ✅ |
| Starter coverage | ✅ `MI_Show_NikkiHero`, `MI_Show_SkinSoft`, cross-polish on 8+ starters |
| Landscape wiring | ✅ `MF_NikkiDreamGrade` chain on landscape master |

### Madoka (witch barrier)

| Check | Result |
|-------|--------|
| Graph wiring (Universal + Landscape) | ✅ Voronoi → veins → rings → emissive |
| Dedicated `MF_Madoka` | ❌ Inline only (documented; not a ship blocker) |
| Starter/demo instances | ✅ `MI_Show_FairyHearts` now drives `MadokaGlowAmount` / `MadokaVeinEmissive` |
| Reserved params (`WitchBarrierPhaseSpeed`, etc.) | ⚠️ Exposed, partially reserved — defaults 0 |

### Itto (mythic carved)

| Check | Result |
|-------|--------|
| Graph wiring (Universal + Landscape) | ✅ Truchet → cracks → wear → roughness stack (ordering fix applied 2026-06-24) |
| Dedicated `MF_Itto` | ❌ Inline only |
| Starter/demo instances | ✅ `MI_Show_StoneCliff`, `MI_Show_InkWash` expose Itto scalars |
| Phase-2 params (`IttoErosionStrength`, `IttoWearDepth`, `IttoInkStrength`) | ⚠️ `IttoInkStrength` wired on InkWash; erosion/wear-depth reserved |

### Celestial (space parallax)

| Check | Result |
|-------|--------|
| `MF_SpaceParallax` on disk | ✅ |
| Wired in Universal master | ✅ After Nikki stack; LERP blend via `ConstellationStrength` |
| Starter `MI_Show_CelestialNebula` | ✅ Full param set |
| Legacy unwired params | ⚠️ `ConstellationPhase`, `CelestialTwinkle`, `CelestialGalaxyArms` kept for MI compat only |
| NASA image textures in UE | ⚠️ `T_NASA_*` exist under `Materials/Space/Textures/` but **not sampled by runtime graph** (procedural + `StarMap` sparkle catalog) |

---

## 3. Substrate compatibility

| Check | Result |
|-------|--------|
| `r.Substrate=True` in project config | ✅ (per `MATERIAL_MIGRATION.md`) |
| Universal / Landscape / Impressionist use `MaterialExpressionSubstrateToonBSDF` → Front Material | ✅ in builders |
| `scrub_legacy_shadingmodel.py` for invalid MSM_Toon | ✅ Tool exists |
| `convert_masters_to_substrate_toon.py` + `run_toon_conversion_pending.py` | ✅ Batch conversion for SDF copies |
| Legacy masters without Toon on disk | ❌ **22 masters** — run conversion pending script |
| `M_Water_Master_Grand_v6` without SubstrateToon string | ✅ Expected — translucent specialist |

---

## 4. Output consistency & naming

| Convention | Status |
|------------|--------|
| Masters `M_*` under `Materials/Masters/` | ✅ |
| Instances `MI_Show_*` showcase, `MI_Zen_*`, `MI_Sakura_*` | ✅ |
| Functions `MF_*` under `Materials/Functions/` | ✅ 33 functions |
| Toon profiles `TP_*` | ✅ 11 profiles |
| Param groups match `GROUP_*` constants in builders | ✅ Nikki, Celestial, Madoka, Itto, etc. |
| Legacy `MI_Universal_*` | ⚠️ Still present — use `archive_unused_instances.py` |

---

## 5. Celestial / NASA validation

| Layer | Role | Status |
|-------|------|--------|
| **UE runtime** | `MF_SpaceParallax` as variation layer after Nikki base color | ✅ Correct — not a parallel master |
| **StarMap input** | Texture param → `MF_SpaceParallax` | ✅ Wired from catalog/sparkle masks |
| **NASA 4K textures** (`T_NASA_MilkyWay_4K`, `T_NASA_StarMap_4K`) | Orphan on disk; wrong folder per schema | ⚠️ Artistic refs only — optional future `StarMap` swap |
| **Material Maker** | `Tools/MaterialMaker/NASA_Refs/` + `SG_Celestial` chain | 📋 Designed, not UE-runtime |
| **Standard structure preserved** | Celestial LERPs into color accumulator before Madoka | ✅ |

---

## 6. Production ship checklist

Run in editor (close material tabs first):

```text
py Content/Python/setup_master_universal.py --force
py Content/Python/setup_landscape_height_blend.py --force
py Content/Python/apply_starter_instances.py
py Content/Python/setup_trimsheet_instances.py
py Content/Python/fix_meshblend_activator_refs.py
py Content/Python/run_toon_conversion_pending.py
py Content/Python/review_portfolio_masters.py
py Content/Python/audit_material_library.py
```

**Pass criteria:**
- `master_review.json` — Universal + Landscape compile, no dead `MF_SpaceParallax`
- `material_library_audit.json` — `dead_material_refs` → 0 for MeshBlend + abstract texture
- Viewport spot-check: `setup_template_showcase.py` 11-sphere row

---

## 7. Related documents

- `missing_connections_report.md` — broken refs and inheritance gaps
- `standardization_fixes.md` — structural consistency and applied fixes
- `MATERIAL_NODE_TREE_REVIEW.md` — authoritative node stack reference
- `MATERIAL_INTEGRATION.md` — starter table and loop status
