# DREAMY_STYLIZED_ARCH_PLAN_2026-09-09

## Research Summary: Dreamy Stylized Architecture

### 2026 Trends (from web research)
1. **Arches layered within arches** — barrel-vaulted entrances, oversized arched windows
2. **Curved walls as space separators** — no sharp corners, soft geometry
3. **Ethereal elegance** — minimalist luxury with light, airy materials
4. **Gothic Revival interior design** — lancet windows, pointed arches, tracery
5. **Barrel vault ceilings** — curved arches softening passage transitions
6. **Warm brass/gold accents** — metallic finishes against light stone/white

### Comparison: Available Gothic vs Dreamy Stylized

| Element | Current Gothic Kit | Dreamy Stylized Need |
|---------|-------------------|---------------------|
| Pointed arches | GB_GOTHIC_PORTAL (lancet doorway) | YES - core element |
| Barrel vault | Not in gothic_kit, in romanesque | YES - need curved ceiling |
| Tracery | GB_GOTHIC_TRACERY_PANEL (6-petal) | YES - but needs refinement |
| Buttresses | GB_GOTHIC_BUTTRESS | PARTIAL - too structural |
| Flying buttresses | NOT available | YES - dreamy exterior |
| Rose windows | NOT available | YES - Gothic rose window variant |
| Ornamentation | Bagapie ivy (gothic_tracery, vault_ribs) | YES - needs delicate gold |
| Curved walls | GB_CORRIDOR_BEND (90deg) | NO - need soft curves |

### Available Architecture Graphs
- GRAPH_CLOISTER: Gothic monastery walk (corridor → bend → portal)
- GRAPH_ROMANESQUE_APSE: Semicircular apse recess with barrel vault
- GRAPH_ZEN_ROJI_PATH: Stepped path with torii gate (good for curved flow)

### Available Melodia GN Ornaments
- ORN_VINE: trailing ornamental vine
- ORN_RADIAL: radial pattern (starbursts)
- ORN_FRAME: picture frame / arch surround
- ORN_PANEL: decorative panel
- ORN_GRID: grid pattern
- CASTLE_TOWER, CASTLE_KEEP, CASTLE_CRENELLATION (castle kit)

## New House Stage Plan

### Stage 1: Curved Wall Interior (Entombment)
**Goal**: Create a dreamy interior with curved walls separating spaces

**Reusable Components**:
1. **MEL_curved_wall** — GN group: adjustable arc wall segment (radius 1-10m, angle 30-180 degrees)
   - Parameters: `arc_radius`, `arc_angle`, `wall_height`, `wall_thickness`
   - Use existing `SurrealArch_Cube` as base with Bend modifier
   - Collection: `Stage_Architecture/StyledWalls/SoftCurve`

2. **MEL_barrel_vault_ceiling** — GN group: barrel vault between two curved walls
   - Parameters: `vault_length`, `vault_radius`, `vault_thickness`
   - Connects to curved walls via snap points
   - Collection: `Stage_Architecture/StyledWalls/Vaults`

3. **MEL_gold_ornament_strip** — GN group: thin gold bead string along wall edges
   - Parameters: `strip_length`, `bead_size`, `bead_spacing`, `curve_offset`
   - Reuses existing ornament distribution logic
   - Material: MH_MAT_Ornament_Gold (0.95, 0.85, 0.2, metallic 0.9, rough 0.25)
   - Collection: `Stage_Decor/GoldAccents/OrnamentStrips`

**Layout**: 
- 3 curved wall segments forming a C-shape (270° arc)
- Barrel vault ceiling connecting them
- Gold bead strips along all wall/ceiling joints
- Dimensions: 12m diameter, 3.5m height

### Stage 2: Gothic Portal Refinement
**Goal**: Refine existing Gothic portal for dreamy aesthetic

**Reusable Components**:
1. **MEL_dreamy_gothic_arch** — Refined gothic portal
   - Slimmer proportions (door width 1.2m, height 2.4m)
   - Extended lancet point (height multiplier 1.5x)
   - Gold tracery inlay along arch perimeter
   - Collection: `Stage_Architecture/Arches/DreamyGothic`

2. **MEL_rose_window_small** — Small circular rose window
   - Diameter: 1.2-2.0m
   - 8-12 radial tracery segments
   - Gold metal frame, translucent "glass" (emission shader)
   - Collection: `Stage_Architecture/Windows/RoseWindows`

**Integration**: Gothic arch as entry point to curved wall interior (Stage 1)

### Stage 3: Interior Styling & Lighting
**Goal**: Dreamy interior with ethereal lighting

**Reusable Components**:
1. **MEL_gold_light_strip** — Linear gold LED strip
   - Along ceiling/wall intersections
   - Emission: gold (0.95, 0.85, 0.2) at 5-10 emission strength
   - Collection: `Stage_Lighting/GoldStrips`

2. **MEL_suspended_crystal** — Hanging crystal ornaments
   - Varied sizes (0.1-0.3m)
   - Gold mounting points, translucent crystal bodies
   - Collection: `Stage_Decor/Crystals`

3. **MEL_curved_staircase** — Spiral/curved staircase
   - Parameters: `step_count`, `spiral_radius`, `step_width`
   - Gold handrail with bead string
   - Collection: `Stage_Architecture/Stairs/Curved`

## UE Import Considerations
- All GN groups must produce clean, single-material meshes
- Use `bpy.ops.object.convert` to real meshes before FBX export
- UV unwrap with seams at ornament joints
- Material naming: MH_MAT_* prefix for UE material instance mapping
- FBX export settings: apply modifiers, forward=-Z, up=Y

## Existing Assets to Leverage
- MH_MAT_Ornament_Gold (already created for study ornaments)
- SurrealArch_Cube GN group (8 instances for procedural geometry)
- Bagapie ivy system (for organic growth on curved walls)
- Higgsas geometry nodes (for procedural detail)
- Existing Gothic kit builders (build_gothic_portal, build_gothic_bay)

## File Structure for New Stages
```
Saved/MelusinasHouse/
  Stage01_CurvedInterior.blend
  Stage02_DreamyGothic.blend
  Stage03_LightingDecor.blend
  Stage_Hero_LightingSet.blend  (portfolio renders)

deploy/surreal_arch/melodia_gn/
  curved_wall.py
  barrel_vault.py
  gold_ornament_strip.py
  dreamy_arch.py
  rose_window.py
```
