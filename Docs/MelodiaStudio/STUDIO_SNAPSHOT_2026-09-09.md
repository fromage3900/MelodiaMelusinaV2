# Melodia Studio — Snapshot 2026-09-09

**Canonical State Document**  
**Date:** 2026-09-09  
**Commit:** `1c2b2a57` (main)  
**Engine:** Blender 5.2.1 LTS  

---

## 1. What Melodia Studio Is

Melodia Studio is the Blender Geometry Nodes garment and decoration authoring pipeline for the Melodia Melusina project. It builds Infinity Nikki-style garment surfaces — material-aware fabric regions, trim sheets, edge bevels, and fold ambient occlusion — all offline in Blender, exported to Unreal Engine 5.8.

---

## 2. The Garment Atelier (4-Builder Pipeline)

| Stage | Builder | Nodes | Purpose |
|-------|---------|-------|---------|
| 1 | `MEL_garment_material_id` | 29n/33l | Face region → integer material ID (fabric=1, trim=2, hem=3, neck=4) |
| 2 | `MEL_garment_smart_bevel` | 20n/22l | Material-aware bevel: fabric edges rounded, trim edges sharp |
| 3 | `MEL_garment_trim_uv` | 27n/30l | Trim-sheet UV: cylindrical for fabric, planar for trim, texel-normalized |
| 4 | `MEL_garment_vertex_ao` | 26n/25l | Fold depth → vertex color AO from tension_fold or rest deviation |

**Pipeline order:** 1 → 2 → 3 → 4  
**Total node budget:** 102 nodes across 4 builders  
**Verification:** 4/4 build cleanly in Blender 5.2.1 headless

---

## 3. Existing Garment Builders (Pre-Atelier)

| Builder | Purpose | Status |
|---------|---------|--------|
| `MEL_garment_uv_unwrap` | Cylindrical UV projection | Superseded by trim_uv |
| `MEL_garment_loom_variation` | Seed-driven fold/drape displacement | Active — precedes atelier |
| `MEL_garment_tension_folds` | Rest-position vs deviation fold mask | Active — provides attributes for AO |
| `MEL_garment_audio_drape` | Audio-reactive fold via Sound node | Active — parallel lane |
| `MEL_garment_xpbd_drape` | Real Cloth Dynamics (XPBD) sim | Research lane — single-shell, no self-collision |

---

## 4. Infinity Nikki Kit

| Builder | Purpose |
|---------|---------|
| `MEL_nikki_bloom_pavilion` | Floral canopy pavilion with heart/star filigree |
| `MEL_nikki_wardrobe_nook` | Garment nook: rods, mirror, plush pedestal |
| `MEL_nikki_podium_runway` | Runway podium with sakura petal fall |
| `MEL_nikki_sheet_rail_hero` | Consolidated hero sheet-music railing |
| `MEL_nikki_star_pendant` | Star-shaped musical pendant |
| `MEL_nikki_heart_filigree` | Heart token filigree (IcoSphere + cone) |
| `MEL_nikki_wall_beads` | Vertical bead strings for wall siding |
| `MEL_sdf_star_panel` | Star-shaped void cut into thin panel (SDF) |

---

## 5. Dreamy Architecture Kit

| Builder | Purpose |
|---------|---------|
| `MEL_barrel_vault_ceiling` | Semicircular vault ceiling |
| `MEL_dreamy_gothic_arch` | Slim lancet arch with gold tracery inlay |
| `MEL_rose_window_small` | Radial tracery rose window |
| `MEL_curved_wall` | Adjustable arc wall |
| `MEL_gold_ornament_strip` | Gold bead distribution along curves |
| `MEL_gold_light_strip` | Emissive gold LED lighting strip |

---

## 6. Core Infrastructure

| System | Status |
|--------|--------|
| `apply_universal_music_pass` | Radial harmonic pulse — available to all builders |
| `materials_kit.py` | 30 named materials (STONE through GENSHIN) |
| `mesh_tools.py` | Bevel, inset, poke, subdivision, remesh, smooth |
| `infinity_nikki_kit.py` | Pastel fantasy ease-of-use kit |
| Garment Atelier categories | `garment` (Garment Atelier), `nikki` (Infinity Nikki) |

---

## 7. Verification Status

```
MEL_garment_material_id:  BUILT — 29 nodes, 33 links
MEL_garment_smart_bevel:  BUILT — 20 nodes, 22 links
MEL_garment_trim_uv:      BUILT — 27 nodes, 30 links
MEL_garment_vertex_ao:    BUILT — 26 nodes, 25 links
MEL_sdf_star_panel:       BUILT — 24 nodes, 28 links
MEL_nikki_star_pendant:   BUILT — 16 nodes, 17 links
MEL_nikki_heart_filigree: BUILT — 15 nodes, 16 links
MEL_nikki_wall_beads:     BUILT — 17 nodes, 19 links
MEL_barrel_vault_ceiling: BUILT — 33 nodes, 40 links
MEL_dreamy_gothic_arch:   BUILT — 41 nodes, 46 links
MEL_rose_window_small:    BUILT — 30 nodes, 34 links
MEL_curved_wall:          BUILT — 14 nodes, 13 links
MEL_gold_ornament_strip:  BUILT — 15 nodes, 12 links
MEL_gold_light_strip:     BUILT — 11 nodes, 9 links
```

---

## 8. Known Limitations

- **No island packing:** Blender 5.2 has no native GN pack-islands node
- **Single-shell XPBD:** `MEL_garment_xpbd_drape` has no self-collision
- **No runtime authority:** Atelier is offline authoring only — Unreal remains runtime authority

---

## 9. Documentation

- `Docs/MelodiaStudio/GARMENT_ATELIER_CONVERGENCE_2026-09-09.md`
- `Docs/Art/UNIVERSAL_GARMENT_FABRIC_DRAPERY_2026-09-02.md`
- `Docs/Art/CYMATIC_GARMENT_NIKKI_PIPELINE_2026-09-02.md`
- `Docs/Art/SURREAL_FABRIC_NIKKI_AUDIT_2026-09-02.md`

---

## 10. Next Steps

- Material ID → Unreal material slot bridge
- Trim-sheet atlas generation from border UV islands
- KawaiiPhysics accessory binding
- Groom real-strand cook for hero shots
