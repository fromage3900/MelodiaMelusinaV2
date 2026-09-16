# Accessory & Eyewear — Handoff & Contact Sheet

**Date:** 2026-09-12
**Branch:** `collab/laptop/eyewear-closeout-20260912`
**PR:** [#199](https://github.com/fromage3900/MelodiaMelusinaV2/pull/199) — OPEN, MERGEABLE
**Canonical repo:** `origin/main` (to be merged)

---

## What this branch carries

| System | Files | Status |
|---|---|---|
| Eyewear GN builders | `deploy/surreal_arch/melodia_gn/eyewear.py` | 6 builders, all verified |
| Bead fix (8.0) | `core.py` `_PROP_SCALE_PREFIXES` | Default music pulse OFF for prop-scale |
| Silhouettes (8.1) | `build_eyewear_front` | 6 shapes, per-shape corner radius |
| Rim edge break (8.2/11.1) | `build_eyewear_front` | `Rim Edge Break` param, profile fillet |
| Pair manifold check | `Tools/eyewear_verify/pair_manifold_check.py` | PASS — watertight |
| Accessory studio | `Tools/setup_accessory_studio.py` | Fade sky, 3-point light, 5 cameras |
| Silhouette grid | `Saved/Accessories/Silhouette_Grid_v1.blend` | 6 pairs, mesh hosts |
| Contact sheet | `Saved/Accessories/contact_sheet_silhouettes.png` | 6 renders, labeled |

---

## Eyewear family — 6 builders

| Builder | ID | Purpose |
|---|---|---|
| Eyewear Front | `MEL_eyewear_front` | Frame front: 2 rims + bridge, 6 silhouettes |
| Eyewear Temple | `MEL_eyewear_temple` | Arm, ear drop, hinge fold, sine inlay |
| Eyewear Hinge | `MEL_eyewear_hinge` | Barrel stack, realized, material slot |
| Eyewear Lens | `MEL_eyewear_lens` | Both lenses, flat plano, material slot |
| Eyewear Pair | `MEL_eyewear_pair` | Assembled: front + 2 temples + 2 hinges |
| Eyewear Hero | `MEL_eyewear_hero` | Full surface: all pieces + lenses + flourishes |

### Silhouettes (param `Silhouette` on front builder)

| Index | Name | Character |
|---|---|---|
| 0 | Rect | Sharp modern |
| 1 | Panto | Round vintage (uses `Panto Round` param) |
| 2 | Cat-Eye | Editorial sweep (uses `Cat Eye Taper`/`Sweep`) |
| 3 | Aviator | Teardrop |
| 4 | Browline | Straight top bar |
| 5 | Round | Circular |

All stay inscribed in the same A×B boxing rectangle — outer width `2A + DBL + 2*RimThickness` is invariant (measured: 134.000 mm for A54 B34 DBL18).

---

## Live workflow

### Step 1 — Addon sync (Blender closed)
```
deploy/_sync_addon_to_blender_5_2.py
```

### Step 2 — Verify addon loads
```python
from surreal_arch.melodia_gn.core import GROUP_BUILDERS
print([k for k in GROUP_BUILDERS if 'eyewear' in k])
```

### Step 3 — Create mesh host (NOT empty)
```python
bpy.ops.mesh.primitive_cube_add(size=0.10, location=(0, 0, 0))
host = bpy.context.active_object
mod = host.modifiers.new("GN", "NODES")
mod.node_group = GROUP_BUILDERS["MEL_eyewear_hero"]()
host.rotation_euler = (-1.5707963267948966, 0, 0)  # Stand up
```

### Step 4 — Set silhouette
```python
for it in mod.node_group.interface.items_tree:
    if getattr(it, "name", None) == "Silhouette" and getattr(it, "in_out", None) == "INPUT":
        it.default_value = 2  # 0-5
```

### Step 5 — Assign materials to slots
```python
for it in mod.node_group.interface.items_tree:
    n = getattr(it, "name", None) or ""
    if "Material" in n and getattr(it, "in_out", None) == "INPUT":
        mod[it.name] = bpy.data.materials["<your_mat>"]
```

### Step 6 — Render contact sheet
```
python Tools/eyewear_verify/make_contact_sheet.py
```

---

## Test harnesses (all RESULT PASS)

| Script | What it proves |
|---|---|
| `bead_size_check.py` | Bead radius == parameter within 2% |
| `bead_music_pass_test.py` | Music pulse was the 25% overscale (now fixed) |
| `hero_verify.py` | All 6 builders register + build + assemble |
| `silhouette_check.py` | Box invariant across silhouettes, branch alive |
| `pair_manifold_check.py` | Assembled pair is watertight (0 non-manifold edges) |

---

## Open items (NOT blocking merge)

| Item | Status | Notes |
|---|---|---|
| 8.3 Lens base curve | Not started | Sag driven by radial distance, per-eye or spanned |
| 8.4 Chain + findings | Not started | `MEL_eyewear_chain` has 0 occurrences in eyewear.py |
| 8.5 UV + export gate | Deferred | `GeometryNodeUVUnwrap` has no geometry socket in 5.2 |
| Materials M1-M11 | Not started | Komikaze path is desktop-only |

---

## File map

```
Saved/Accessories/
├── Melodia_Accessory_Studio_v1.blend    (715 KB — studio schema)
├── Silhouette_Grid_v1.blend             (170 KB — 6 pairs)
├── contact_sheet_silhouettes.png        (115 KB — all 6 renders)
├── silhouette_{rect,panto,cateye,aviator,browline,round}.png
└── preview_grid_.png

Tools/
├── setup_accessory_studio.py            (studio setup)
└── eyewear_verify/                      (12 test + staging scripts)

deploy/surreal_arch/melodia_gn/
└── eyewear.py                           (6 builders, 1200+ lines)

Docs/Planning/
├── ACCESSORY_EXECUTION_PLAN_2026-09-12.md
└── ACCESSORY_LOOKDEV_SUITE_2026-09-12.md
```

---

*Handoff by Melodia Agent, 2026-09-12.*
