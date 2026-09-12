# Missing Connections Report

**Date:** 2026-06-25  
**Source:** `Saved/Audit/material_library_audit.json`, disk scans, builder cross-reference  
**Scope:** Broken inheritance, dead refs, unwired params, missing texture links

---

## Summary counts

| Issue class | Count | Severity |
|-------------|-------|----------|
| Dead material / function refs | **73** | 🔴 High |
| Missing texture refs (on disk) | **12** | 🔴 High |
| Orphan textures (unreferenced) | **9** | 🟡 Medium |
| Masters missing Substrate Toon (disk) | **22** | 🔴 High (SDF lane) |
| Legacy `_PROJECT` path edges (EnvSandbox) | **33** unique | 🟡 Medium |
| Instances on deprecated Unified master | **1** | 🟡 Medium |
| Celestial legacy params (unwired by design) | **3** | 🟢 Low (compat) |
| Itto Phase-2 params (partially reserved) | **2** | 🟢 Low |

---

## 1. Dead function references

### 1.1 MeshBlend activator (35 refs)

**Broken target:** `/Game/Art/Materials/Master/Materials/MF_MeshBlend_Activator_Index`

**Affected:** 35+ SDF/hybrid masters (e.g. `M_SDF_Baroque`, `M_SDF_GothicArchitecture`, `M_HybridStone_SDF`, …)

**Fix script (exists):** `Content/Python/fix_meshblend_activator_refs.py`  
**Retarget:** `/Game/EnvSandbox/Materials/Functions/MF_MeshBlend_Activator_Index_0`

**Status:** Not run in this finalization pass (requires editor). **Blocker** for SDF master compile health.

---

## 2. Missing texture references

### 2.1 Abstract pack stale path (11 refs)

**Broken target:** `/Game/Textures/sbs_-_seamless_abstract_pack_-_512x512/512x512/Texture_512x512`  
**Valid asset on disk:** `Texture_512x512_1` (and `_2`…`_50`) — no bare `Texture_512x512`

**Affected sources:**
- `M_Master_Toon_Universal`
- `M_Master_Toon_Landscape_HeightBlend`
- Multiple `MI_Show_*` and legacy `MI_Universal_*` instances

**Root cause:** Stale serialized path from pre-catalog migration. Catalog (`portfolio_texture_catalog.py`) already points to `Texture_512x512_1`.

**Fix:** Rebuild masters + re-apply starters (forces `apply_master_defaults`):

```text
py Content/Python/setup_master_universal.py --force
py Content/Python/setup_landscape_height_blend.py --force
py Content/Python/apply_starter_instances.py
```

---

### 2.2 Sakura bark `_PROJECT` ref (1 ref)

**Broken target:** `/Game/_PROJECT/04_Materials/Textures/Spokes/512x512/Texture_512x512`  
**Source:** `MI_Sakura_Bark`

**Fix:** Run `patch_portfolio_texture_paths.py` or re-apply `setup_sakura_instances.py` with catalog wiring.

---

## 3. Broken inheritance chains

### 3.1 Deprecated unified master

| Instance (disk) | Expected parent | Actual |
|-----------------|-----------------|--------|
| 1× material referencing `M_Master_Toon_Unified` | `M_Master_Toon_Universal` | Still on Unified |

**Fix:** `Content/Python/reparent_unified_instances.py`

### 3.2 Legacy `MI_Universal_*` (141+ presets)

- Still under `Instances/Environment/` and `_Archive/`
- Many reference stale textures and duplicate starter capabilities
- **Not deleted** (by project policy)

**Fix:** `archive_unused_instances.py` + use `LEGACY_ALIASES` in `starter_instances.py` for name mapping.

### 3.3 Unknown parent instances (41 on disk)

Heuristic scan could not resolve parent string in uasset bytes. Likely:
- Landscape instances (`MI_Landscape_*`)
- Impressionist / SDF instances
- Archived copies

**Action:** Run in-editor `sync_all_material_instances.py` after master rebuild to validate param inheritance.

---

## 4. Unwired / legacy parameters

### 4.1 Celestial compat params (no graph wire)

| Parameter | Group | Notes |
|-----------|-------|-------|
| `ConstellationPhase` | Celestial | Replaced by `MF_SpaceParallax` |
| `CelestialTwinkle` | Celestial | Replaced by Nikki sparkle + MF |
| `CelestialGalaxyArms` | Celestial | Replaced by `CelestialGalaxyStrength` / `GalaxyDepth` |

**Impact:** Old `MI_Universal_*` celestial instances may set these — **no visual effect**. Migrate to `CelestialNebulaStrength`, `CelestialGalaxyStrength`, `CelestialToonSteps`.

### 4.2 Madoka reserved

| Parameter | Status |
|-----------|--------|
| `WitchBarrierMazeTightness` | Wired const in graph; param reserved |
| `WitchBarrierPhaseSpeed` | Reserved for future animation |
| `MadokaRadialSpeed` | Exposed; no time node in graph |

### 4.3 Itto Phase-2

| Parameter | Status |
|-----------|--------|
| `IttoErosionStrength` | Exposed; not connected to height erosion |
| `IttoWearDepth` | Reserved for parallax height integration |
| `IttoInkStrength` | Wired on ink showcase (`MI_Show_InkWash`) |

---

## 5. Orphan textures

| Path | Notes |
|------|-------|
| 8× `SDF/Textures/Marble/Marble_*` | Unused marble pack — archive or wire to SDF instances |
| `Materials/Space/Textures/T_NASA_MilkyWay_4K` | NASA ref — not bound to `MF_SpaceParallax` (procedural path active) |

---

## 6. Cross-system gaps (documented, not bugs)

| Gap | System | Notes |
|-----|--------|-------|
| No `MF_Madoka` / `MF_Itto` | Thematic | Inline graphs — functional, not extracted |
| NASA JPGs MM-only | Celestial | UE uses procedural parallax; MM `SG_Celestial` unchecked in ROADMAP |
| AO not on Toon BSDF pin | Output maps | Shadow/contact handled via `MF_ShadowDreamGrade` |
| Water master non-Substrate | Specialist | Intentional translucent stack |

---

## 7. Recommended fix order

1. `fix_meshblend_activator_refs.py` — clears 35 dead SDF refs  
2. `setup_master_universal.py --force` + `setup_landscape_height_blend.py --force` — clears abstract texture stale paths on masters  
3. `apply_starter_instances.py` — refreshes 13 canonical instances + Madoka/Itto demo params  
4. `run_toon_conversion_pending.py` — Substrate Toon on remaining 22 masters  
5. `reparent_unified_instances.py` + `archive_unused_instances.py` — inheritance cleanup  
6. `audit_material_library.py` — verify `dead_material_refs` → 0

---

## 8. Audit artifact locations

| Report | Path |
|--------|------|
| Library audit | `Saved/Audit/material_library_audit.json` |
| Parameter audit | `Saved/Audit/material_parameter_audit.json` (editor run returned empty materials — re-run in open editor) |
| Master review | `Saved/Audit/master_review.json` (after `review_portfolio_masters.py`) |
| MeshBlend fix log | `Saved/Audit/meshblend_activator_fix.json` |
