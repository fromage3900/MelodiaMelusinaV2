# Melodia Studio — Garment Atelier Convergence (2026-09-09)

**Status:** Active / Canonical  
**Branch:** `main`  
**Commit:** `f60f52b6` (merge: studio-integration — garment smart bevel + atelier wiring)  
**Engine:** Blender 5.2.1 LTS  
**Node budget:** 94 nodes across 4 builders  

---

## 1. What the Atelier Does

Infinity Nikki-style garment surface authoring — four stages that turn a raw garment shell into a render-ready outfit with material regions, crisp trim, clean UVs, and fold shadow:

| Stage | Builder | Nodes | Purpose |
|-------|---------|-------|---------|
| 1 | `MEL_garment_material_id` | 29n/3l | Assign integer material IDs by region (fabric=1, trim=2, hem=3, neck=4) |
| 2 | `MEL_garment_smart_bevel` | 20n/22l | Material-aware edge bevel — fabric edges rounded, trim edges sharp |
| 3 | `MEL_garment_trim_uv` | 27n/30l | Trim-sheet UV — cylindrical for fabric, planar for trim, texel-normalized |
| 4 | `MEL_garment_vertex_ao` | 18n/18l | Bake fold AO into vertex colors from tension_fold or rest deviation |

Pipeline order: **1 → 2 → 3 → 4** (material ID feeds bevel and UV; fold AO reads from prior deformation stages).

---

## 2. Region Detection (Stage 1)

Material ID assignment uses three independent tests per face:

- **Height banding:** bounding box Y → hem (bottom 15%), neckline (top 10%), fabric (middle)
- **Edge proximity:** `GeometryNodeInputMeshEdgeNeighbors` finds boundary edges → `GeometryNodeProximity` measures distance to boundary → trim if within `Border Width` (default 5cm)
- **Priority cascade:** border (2) overrides hem (3) and neck (4); neck overrides hem; fabric (1) is the fallback

Output: integer attribute `material_id` on FACE domain. Downstream stages read this.

---

## 3. Smart Bevel (Stage 2)

Material-aware edge bevel that respects the trim/fabric boundary:

- **Auto weight:** `GeometryNodeInputMeshEdgeAngle` → compare to threshold → store `bevel_weight_auto` on EDGE domain
- **Material factor:** read `material_id` (FACE → edge interpolation) → if `>= 2` (trim), multiply weight by `Trim Bevel Factor` (default 0.3)
- **Priority chain:** manual `bevel_weight` > auto weight > 1.0
- **Final width:** `Base Width × material_factor × weight`

Result: fabric edges get soft rounded bevels; trim borders stay crisp — the signature Infinity Nikki look.

---

## 4. Trim-Sheet UV (Stage 3)

Dual projection system with material-aware blending:

- **Cylindrical (fabric):** `atan2(x,z) → U`, `y - min_y → V`. Standard garment unwrap.
- **Planar (trim):** `x - min_x → U`, `z - min_z → V`. Top-down projection for trim sheets.
- **Blend:** `ShaderNodeMix(FLOAT2)` with factor `(material_id >= 2) × Planar Blend`
- **Texel normalization:** divide UV by bounding box dimension → consistent pixels/meter regardless of mesh scale

Output: `uv_garment` FLOAT2 attribute on FACE domain.

---

## 5. Vertex AO (Stage 4)

Bakes ambient occlusion from fold depth into vertex colors:

- **Fold depth source:** reads `tension_fold` (POINT) if exists, else derives from `|position - rest_position|` (deviation from rest)
- **AO curve:** `clamp(depth × AO Strength, 0, 1)`
- **Darkening:** `final = Base Color × (1 - AO × 0.6)`
- **Output:** `Color` FLOAT_COLOR attribute on CORNER domain

---

## 6. Integration with Existing Systems

| Existing system | Atelier connection |
|---------------|-------------------|
| `MEL_garment_tension_folds` | Provides `tension_fold` and `rest_position` attributes for AO |
| `MEL_garment_loom_variation` | Precedes atelier — creates the base garment shape |
| `MEL_garment_uv_unwrap` | Superseded by `MEL_garment_trim_uv` (adds planar + material blend) |
| `MEL_garment_audio_drape` | Parallel lane — audio-reactive displacement |
| `MEL_garment_xpbd_drape` | Research lane — real cloth sim (single-shell, no self-collision) |
| `apply_universal_music_pass` | Available to all atelier builders via `new_geometry_tree` |
| Material palette (`materials_kit.py`) | 30 named materials (STONE, MARBLE, WATER, STAINED, GOLD, GOTHIC_DARK, GENSHIN, etc.) — atelier output drives material assignment |

---

## 7. Files Added

```
deploy/surreal_arch/melodia_gn/garment_material_id.py   (186 lines)
deploy/surreal_arch/melodia_gn/garment_smart_bevel.py   (191 lines)
deploy/surreal_arch/melodia_gn/garment_trim_uv.py       (210 lines)
deploy/surreal_arch/melodia_gn/garment_vertex_ao.py     (118 lines)
deploy/surreal_arch/melodia_gn/__init__.py              (modified — 4 new imports)
```

Category: `garment` (Garment Atelier, icon MATCLOTH)

---

## 8. Verification

All 4 builders verified in Blender 5.2.1 headless:

```
MEL_garment_material_id:  BUILT — 29 nodes, 33 links
MEL_garment_smart_bevel:  BUILT — 20 nodes, 22 links
MEL_garment_trim_uv:      BUILT — 27 nodes, 30 links
MEL_garment_vertex_ao:    BUILT — 18 nodes, 18 links
4/4 builders pass
```

---

## 9. Known Limitations

- **No island packing:** Blender 5.2 has no native GN pack-islands node. UV projection is continuous (no overlapping for convex shells).
- **Single-shell XPBD:** `MEL_garment_xpbd_drape` has no self-collision — layered shells (underskirt + skirt) interpenetrate.
- **No runtime authority:** Atelier is offline authoring/bake only. Unreal remains the runtime garment authority.

---

## 10. Next Steps (when needed)

- Material ID → Unreal material slot bridge (data attribute drives material index)
- Trim-sheet atlas generation (auto-generate trim texture from border UV islands)
- KawaiiPhysics ear/tail/bell binding for garment accessories
- Groom real-strand cook for hero shots
