# Melusina Inverted-Hull Generation — Geo Nodes Expansion Plan

**Status:** owner-requested spec (2026-10-16). Source of truth for generating Melusina's inverted-hull outline shell procedurally in Blender Geometry Nodes, so the UE-side `M_Melodia_Outline` material has one editable upstream instead of a one-off FBX bake.

## 1. Purpose

Replace the current "bake at FBX export" hull with a Geo Nodes node tree that is the single source of truth for the inverted hull. The hull shell is rendered from inside-out (backfaces) by `M_Melodia_Outline` (Masked / Two-Sided / DefaultLit), so the silhouette line is driven by world-position offset on the hull mesh plus per-instance width controls in UE.

Consolidating here also removes the 12 duplicate modifier copies currently scattered across the blend (verified via Blender port 9877).

## 2. Current state (verified)

Inspector census from `G:\_Transport_20260930_blend-rescue\MELUSINA_blend_rescue_20261006.blend` (PID 1336, Blender 5.2.1 LTS, port 9877):

| Item | Verified fact |
|---|---|
| Live modifier | `Outline [GeoNodes].023` (`show=True`) on `Melusina`; shared with `Hair Strand.008`, `Melusina_FrontPanel`, `PM3D_Cube3D1.001`, `R_Eyebrow`, `R_Eyebrow.002` |
| Duplicate copies | 12 others (`.002 .008 .009 .023-.032`), ~90 nodes each — not a single source of truth |
| Bake timing | Modifier is **live, not baked**; bakes only at FBX export |
| Body mesh | 18,791 verts; hull slot `SBW_Outline.003` → UE `MI_Melusina_Outline_005` |
| Other outline materials | `Outline.004` (eyebrows), `Outline.005` (shawl), `Outline.006` (skirt panel); star shaders `Outline Shader *.031/.033` on hair strands |
| UE contract | `specs/anim_presets/melusina_v2_material_map.json` routes all outline tokens to approved MIs (25 entries) |

Assignment census (modifier → object) was captured; re-parenting the UE `MI_HullOutline_*` family onto `M_Melodia_Outline` is tracked as separate material work (this plan covers the Blender generation side only).

## 3. Design — Geo Nodes hull tree

The tree runs on the body mesh and emits the inverted-hull shell:

1. **Input** — the body surface mesh to outline.
2. **Capture attributes** — per-vertex normals, position, and any existing outline-width attribute painted on the body.
3. **Inward solidify** — extrude geometry inward along vertex normals by `HullDepth` (the outline width). This is the shell thickness.
4. **Flip normals / invert winding** — reverse face winding so the hull renders as backfaces (the "inverted" hull). Backface culling off / Two-Sided enabled in UE so the shell is visible from outside.
5. **UVs** — generate hull UVs (capped/box or transferred from body) so the outline material maps consistently across body/skirt/hat zones.
6. **Output** — hull mesh written to the hull material slot, assigned `SBW_Outline.*` family in Blender → UE `MI_Melusina_Outline_005`.

**Exposed modifier inputs (one place to tune):**
- `HullDepth` — shell thickness (maps to UE `OutlineExtraWidth` per-MI)
- `NormalFlip` — toggle winding inversion
- `UVScale` — outline UV tiling

**Single-source rule:** the Geo Nodes tree is the only place the hull shape is authored. The FBX export is derived from it; nobody hand-tweaks the baked hull in UE.

## 4. Expansion phases

**Phase 1 — Replicate the current bake.** Inspect the exact node tree inside `Outline [GeoNodes].023` (node types + settings), rebuild it as a clean single tree, verify its FBX-exported hull matches today's baked hull (vertex count, shell depth, normal direction). Consolidate the 12 duplicates onto this one tree.

**Phase 2 — Per-zone width.** Separate hull output per material zone (body / skirt / hat / eyebrow / shawl), each with its own `HullDepth`, mapping to per-MI `OutlineExtraWidth` values (`Character_Heavy` / `Character_Thin` / `Hairline` / `Hero` / `Ghost` / `Environment`).

**Phase 3 — Line boil in Geo.** Add animated per-vertex normal jitter at a low frame rate (on 2s/3s ≈ 8 Hz), quantized so it reads as hand-drawn ink, not crawl. Output as a vertex attribute or per-vertex offset that UE reads via `OutlineBoilAmount`/`OutlineBoilRate`/`OutlineBoilScale`. Alternative (recommended for runtime editability): keep boil purely in the UE material and use Geo only for the static hull shape — decision needed (see §6).

**Phase 4 — Export automation.** Blender script applies Geo Nodes → exports hull LODs → imports to UE → reparents to `M_Melodia_Outline` → sets per-MI width params. Idempotent and re-runnable.

## 5. Risks / open decisions

- **12 duplicate modifiers** must be consolidated to one tree before any expansion, or every zone gets tuned 12 times.
- **Self-intersection:** inset distance must not cause the hull shell to fold on tight curvature (hat brim, skirt panels, eyebrow arches). Validate after Phase 1.
- **Vertex count:** 18,791 verts on the body → hull shell LOD strategy needed so the outline doesn't dominate the triangle budget (CI gate `triangle_budget: max_250k`).
- **Width sync:** single source of truth — GeoNodes `HullDepth` OR UE `OutlineExtraWidth`. Recommend UE owns runtime width (editable per-instance without re-export), GeoNodes owns the base shell shape.
- **Boil location:** GeoNodes-animated (baked) vs UE material-animated (runtime). Recommend UE material for editability; if baked in Geo, the boil attribute must survive FBX export.

## 6. Integration with UE

Feeds `M_Melodia_Outline` (Masked / Two-Sided / DefaultLit) via `MI_Melusina_Outline_005` family under `/Game/Melodia/Characters/Melusina/Materials/`. UE-side controls after this plan:

| Scope | Parameter | Owner |
|---|---|---|
| Global (MPC `MPC_MelodiaInk`) | `OutlineColor`, `OutlineGlobalWeight`, `OutlineWidthScale` | MPC |
| Per-instance (each hull MI) | `OutlineExtraWidth` (maps to GeoNodes `HullDepth`) | MI Details panel |
| New (line boil) | `OutlineBoilAmount`, `OutlineBoilRate`, `OutlineBoilScale` | MI Details panel |

Never edit `M_Master_Toon_Universal` (1,303 expressions). Never apply `OverlayMaterial` to runtime units.
