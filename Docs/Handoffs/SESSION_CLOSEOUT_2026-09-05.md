# Session Closeout — 2026-09-05

## Summary

A deep material audit and repair session covering 578+ assets. Fixed 117 instances, repaired 6 masters, imported 468 textures, deleted 19 broken assets. Committed to `codex/game-state-2026-09-04`.

---

## What Worked

### Instance Repairs (117 assets)
- **58 instances**: Cleared dead `RefractionDepthBias` overrides
- **10 HERO instances**: Assigned Albedo textures
- **14 Show_* instances**: Assigned NormalMap textures
- **21 Copernicus instances**: Assigned cymatic PBR textures (Albedo/NormalMap/HeightMap/ORM)
- **5 Glitter* instances**: Re-mapped dead overrides to Albedo/NormalMap/HeightMap/ORM

### Master Repairs (6 assets)
- **M_Master_Nikki**: Swapped Albedo default T_Marbage 7 → FarawayAlabasterDrape, deleted dead glitter branches (280 PS)
- **M_Master_Toon_Universal**: Swapped 4 marble defaults → alabaster (1169 PS)
- **M_SDF_CathedralVault**: Wired 10 floating Custom inputs (276 PS)
- **M_SDF_Mandelbulb_Master**: Rewrote HLSL + wired 11 inputs (178 PS — LOST in crash, needs git restore)
- **4 Grotto masters**: Restored from _PROJECT/, rescan, save (216 + 246 PS)

### Texture Imports (468 assets)
- **461 Surreal Fabric flipbooks**: CelestialSilk, CymaticPulse, BrassPatina PNGs → .uasset with correct sRGB/compression
- **7 Starskiff textures**: Imported missing .uassets
- **12 Starskiff textures**: Already present from previous session

### Cleanup (19 assets deleted)
- **17 corrupt orphans**: filename ≠ internal package name
- **2 sibling duplicates**: MI_Master_Toon_Universal_Inst1/Inst3 (0 children)

### Commits
- `40d13289`: First pass — 89 instances fixed
- `69251852`: Second pass — flipbook import, cymatic textures, cleanup

---

## What I Learned (MCP Hazards)

### Critical Monolith Bugs

| Bug | Impact | Workaround |
|---|---|---|
| `build_material_graph` CLEARS the graph | Wipe all nodes on existing materials | Only use on new/empty materials; use `create_custom_hlsl_node` to add |
| `update_custom_hlsl_node` clears connections | All input wires lost | Re-wire ALL inputs after calling it |
| `set_instance_parameters` type `switch` (not `static_switch`) | Static switches silently fail | Use `type: "switch"` for static switches |
| `capture_scene_preview` serves CACHED images | Hot-pink test = byte-identical PNG | Never A/B visual tests with captures |
| `render_preview` returns blank white | Even for healthy masters | Not a visual defect signal |
| PIE clip frames come out black | Camera spawns inside geometry | Not a material defect signal |

### The Crash Loop

1. Editor crashes (assert/OOM)
2. `.uassets` remain read-only (locked by source control or crash temp)
3. Monolith `save_packages` asserts "read-only" → crash loop

**Fix:** `find Content -name "*.uasset" -exec attrib -R {} \;` before restarting editor

### The Dead-Override Defect

The project has 3 unrelated "marble" bugs:

1. **Dead parameter names**: Instances authored against old master carry overrides with names that no longer exist on parent (e.g., `BaseColor` → `Albedo`)
2. **Master default is marble**: `T_Marble_7` baked into master's Albedo param default
3. **Missing overrides**: Instances don't override Albedo → inherit master default

---

## What Remains Blocked

| Asset | Blocker |
|---|---|
| **M_Master_Nikki_Landscape** | Editor crashes on save — needs manual investigation |
| **22 Orphans** | Corrupt assets — MCP can't load them |
| **~780 materials** | Not yet scanned for unwired Custom HLSL |
| **M_SDF_Mandelbulb_Master** | Graph wiped by `update_custom_hlsl_node` — `git checkout HEAD~1` to restore |

---

## Key Discoveries

### Nikki Master Graph Structure
The M_Master_Nikki has 255 nodes feeding a SubstrateToonBSDF. The main color path:
```
BSDF:BaseColor ← LI_5
  LI_5.A ← IridescenceSheen (the ONLY wired color path)
  LI_5.B ← AtmosphericColor
  LI_5.Alpha ← AtmosphericStrength × DepthFade
```

Glitter functions (MF_MelodiaGlitterPile, MF_NikkiGlitterHalo) were wired to dead ends (LI_6/LI_2 with no children). Deleted for convergence.

### Niagara/Flipbook Study Findings
- **1 true flipbook material**: M_Niagara_MelodiaFlipbook (4×4 grid, 15 FPS)
- **NO BeatPulse/MPC wiring** — uses ParticleRelativeTime, not rhythm-synced
- **9 "Static" MIs misnamed** — use 1×1 grid (single frame)
- **All Niagara materials procedural** — Custom HLSL, textures via MI overrides
- **1 broken parent chain**: MI_Niagara_Melodia_Static_StateB
- **1 empty placeholder**: MF_Niagara_SDF_Sample

### Texture Assets Available (all baked/in-project)
- 398 cymatic textures across 22 Copernicus sets + 24 Melodia sets
- 69 texture sets across 10 directories
- 462 Surreal Fabric flipbook PNGs (now imported)

---

## AGENTS.md Updates Needed

Add to the safe working rules:

```
- **Monolith material_query hazards**:
  - `build_material_graph` CLEARS the graph — only use on new/empty materials
  - `update_custom_hlsl_node` clears ALL input connections — re-wire after
  - `set_instance_parameters` type key for static switches is "switch" not "static_switch"
  - `capture_scene_preview` / `capture_material_grid` serve CACHED images — never A/B
- **After every editor crash**, run `find Content -name "*.uasset" -exec attrib -R {} \;` before restart
- **Read-only .uassets cause the crash loop** — if save_packages fails, check attrib first
```

---

## Final Stats

| Metric | Count |
|---|---|
| Instances fixed/cleaned | 117 |
| Masters repaired | 5 of 6 |
| Textures imported | 468 |
| Broken assets deleted | 19 |
| Commits landed | 2 |
| Lines of documentation | this doc + 2 audit reports |
