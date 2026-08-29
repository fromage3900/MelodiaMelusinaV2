# GN Preset Library — Monolith Kit & Taxonomy

**Date:** 2026-08-29  
**Author:** Melusina (Hermes agent)  
**Scope:** `deploy/surreal_arch/melodia_gn/`  
**Status:** Live, registered, preset-tested offline

---

## 1. Monolith Kit — New Builders

A 5-builder kit implementing the **gothic coastal monolith** visual direction from
`Docs/Art/MONOLITH_CONCEPT_ART_BACKLOG_2026-08-26.md` (The Last Reflection P0).

### Visual Direction

> Moonlit basalt coast filled with tide pools and broken mirrors, every reflection
> showing the same impossible pale ocean, a vast manta-ray silhouette gliding
> beneath a puddle..., gothic coastal monolith, tiny lone figure for scale,
> cold silver-blue lighting, serene existential dread.

The rule: **model only the anatomy the player must understand; imply the rest
with terrain silhouette, water volumes, fog, lighting, and shaders.**

### Builder Inventory

| ID | Name | Concept |
|---|---|---|
| `MEL_monolith_spire` | Monolith Spire | Single basalt spire with mirror inlay slit + tide-pool basin. Implies vast submerged body. |
| `MEL_monolith_field` | Monolith Field | Scatter spires across a 2D plane. Noise-driven per-instance scale. Overworld traversable. |
| `MEL_monolith_manta_silhouette` | Manta Silhouette | Flat wide winged curve — the implied body beneath reflection pools. Decal/shadow-catcher mask. |
| `MEL_monolith_tide_pool` | Tide Pool | Basin with reflective water plane + broken mirror shards. Every reflection shows the same ocean. |
| `MEL_monolith_reflection_portal` | Reflection Portal | Broken gothic arch frame. Every reflective surface shows the impossible ocean. |

### Preset Recipes (15 total, 3 per builder)

| Builder | Preset | Vibe |
|---|---|---|
| Spire | `COASTAL_FRAGMENT` | Default — single fragment, tide pool, subtle mirror |
| Spire | `DEEP_GIANT` | Tall, slim, deep water — vast submerged body implied |
| Spire | `MIRROR_TOWER` | Heavy fracture — reads as broken reflection portal |
| Field | `SHORELINE_SCATTER` | Moderate density, natural variation |
| Field | `DEEP_RUINS` | Dense, tall — drowned civilization |
| Field | `MIRROR_FOREST` | Wide, low, heavy inlay — every surface reflects |
| Manta | `PELAGIC_GHOST` | Default vast wingspan, gentle curve |
| Manta | `BROKEN_WING` | Asymmetric, fractured — wounded leviathan |
| Manta | `TIDE_POOL_RAY` | Small, tight — fits in a single basin |
| Tide Pool | `BASIN_REFLECTION` | Calm water, few shards, pale ocean |
| Tide Pool | `SHARD_STORM` | Dozens of reflective shards, fractured sky |
| Tide Pool | `DEEP_ABYSS` | Deep basin, dark water — vast thing moving below |
| Portal | `GOTHIC_DOORWAY` | Intact pointed arch, pale ocean reflection |
| Portal | `BROKEN_ARCH` | Fractured top, distorting reflection |
| Portal | `MIRROR_GATE` | Wide, low, all-mirror — ocean everywhere |

### Composition Guide

```
LV_SeaAbove_Prototype composition (suggested):

  [MEL_monolith_field] — SHORELINE_SCATTER (foreground, waterline)
      └─ instanced MEL_monolith_spire × 16 with COASTAL_FRAGMENT preset

  [MEL_monolith_spire] × 3 — DEEP_GIANT (midground, deep water)
      └─ scale 3×, mirror inlay near-zero, tide pool depth 2.0

  [MEL_monolith_tide_pool] × 6 — BASIN_REFLECTION (ground plane)
      └─ nested MEL_monolith_manta_silhouette (TIDE_POOL_RAY) inside each

  [MEL_monolith_reflection_portal] × 2 — BROKEN_ARCH (hero setpieces)
      └─ scale 2×, frame thickness 0.4, broken top 0.6
```

### Material Contract

| Surface | Master | Key Params |
|---|---|---|
| Basalt body | `M_Master_Toon_Universal_Alpha` | Dark cool grey, Roughness 0.85 |
| Mirror inlay | `M_Master_Toon_Universal_Alpha` | Emissive pale blue (0.42, 0.75, 1.0), Strength 2.0 |
| Water plane | `M_Oceanology_NikkiHero` (or fallback) | Planar reflection, pale aqua tint |
| Manta ribbon | `M_Master_Nikki` | Iridescent sheen, dual-lobe, pearl shift |

---

## 2. GN Preset Library — Full Taxonomy

### Registry Architecture

```
GROUP_BUILDERS[tree_name]     → callable (the builder function)
GROUP_METADATA[tree_name]     → {label, description, category, builder, hidden, role}
BUILDERS_PRESETS[builder_id]  → {label, presets, preset_labels, preset_descriptions}
```

- **GROUP_BUILDERS** — registered by each module via `register_builder()`
- **BUILDERS_PRESETS** — curated parameter sets, one dict per builder
- Preset keys match the **exact** group-input socket names (e.g. `"Base Width"`, not `"base_width"`)
- Accessors: `builders_with_presets()`, `preset_names(id)`, `preset_param_sets(id)`, `export_all_presets_json(path)`

### Category Map (13 categories)

| Category | Icon | Builders | Role |
|---|---|---|---|
| `primitives` | MESH_GRID | 5 | Arrays, bounding boxes, instance on spline |
| `profiles` | MESH_CYLINDER | 6 | Columns, balusters, posts, rails, finials |
| `math_attrs` | NODETREE | 6 | Add, subtract, power scale, store attribute |
| `structures` | HOME | 3 | Gazebo, arch, roof assemblies |
| `effects` | SHADERFX | 6 | Displace, wave, cast, wireframe, smooth, magic |
| `ornament` | DECORATE | 5 | Vine, radial, grid, frame, panel |
| `filigree` | MOD_CURVE | 3 | Spiral, rosette, harmonic orb |
| `music` | FILE_SOUND | 50+ | Note heads, clefs, staffs, baroque instruments, jingles, harps |
| `castle` | MOD_BUILD | 17 | Crenellations, walls, towers, gatehouses, buttresses, keeps |
| `operations` | AUTOMERGE_ON | 3 | Iterate, bounded, power clamp |
| `mesh_tools` | EDITMODE_HLT | 8 | Bevels, insets, remesh, smooth, dual |
| `set_dressing` | PLUGIN | 17 | Water/music themed structures, gazebos, fountains, bridges |
| **`monolith`** | **MOD_BUILD** | **5** | **Gothic coastal monolith kit — spires, fields, manta, tide pools, portals** |

### Builder Count

| Category | Count |
|---|---|
| primitives | 5 |
| Profiles | 6 |
| Math & Attributes | 6 |
| Structures | 3 |
| Magic Effects | 6 |
| Ornament | 5 |
| Filigree & Crests | 3 |
| Musical Notation | 50+ |
| Castle Kit | 17 |
| Operations | 3 |
| Mesh Tools | 8 |
| Set Dressing | 17 |
| **Monolith Kit** | **5** |
| **Total** | **~130+** |

### Preset Count

| Category | Curated Presets |
|---|---|
| Water (effects) | 5 |
| Music (music) | 30+ |
| Castle (castle) | 12 |
| Nikki (set_dressing) | 9 |
| **Monolith (monolith)** | **15** |
| **Total** | **~80+** |

---

## 3. How to Add a New Preset

1. **Identify the builder** — find its `register_builder()` call in the module
2. **Match socket names** — preset keys must equal the `add_*_param()` names exactly
3. **Add to BUILDERS_PRESETS** — append under the builder's entry in `presets.py`
4. **Include label + description** — `preset_labels` and `preset_descriptions` are optional but recommended
5. **Test offline** — `python -c "from deploy.surreal_arch.melodia_gn.presets import audit_presets; print(audit_presets())"`

### Example

```python
# In presets.py, inside BUILDERS_PRESETS:
"MEL_monolith_spire": {
    "label": "Monolith Spire",
    "preset_labels": {
        "COASTAL_FRAGMENT": "Coastal Fragment",
    },
    "preset_descriptions": {
        "COASTAL_FRAGMENT": "Default gothic coastal basalt spire.",
    },
    "presets": {
        "COASTAL_FRAGMENT": {
            "Base Width": 3.0,        # matches add_float_param name
            "Height": 12.0,
            "Taper": 0.32,
            "Fracture Count": 4,      # matches add_int_param name
            "Mirror Inlay": 0.18,
            "Tide Pool Depth": 0.45,
        },
    },
},
```

---

## 4. File Map

| File | Role |
|---|---|
| `deploy/surreal_arch/melodia_gn/monolith.py` | 5 monolith builders + register_builder calls |
| `deploy/surreal_arch/melodia_gn/presets.py` | BUILDERS_PRESETS dict (all curated presets) |
| `deploy/surreal_arch/melodia_gn/core.py` | GROUP_BUILDERS, GROUP_METADATA, CATEGORY_META |
| `deploy/surreal_arch/melodia_gn/__init__.py` | Module imports (registers all builders) |
| `deploy/surreal_arch/melodia_gn/stack.py` | GN Stack UI panel (shows categories + builders) |

---

## 5. Git History

- `deploy/surreal_arch/melodia_gn/monolith.py` — **NEW** (5 builders, 15 presets)
- `deploy/surreal_arch/melodia_gn/presets.py` — **MODIFIED** (added monolith section)
- `deploy/surreal_arch/melodia_gn/core.py` — **MODIFIED** (added `monolith` category)
- `deploy/surreal_arch/melodia_gn/__init__.py` — **MODIFIED** (import monolith module)
