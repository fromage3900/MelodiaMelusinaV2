# PCG Scale Fix Documentation

## The Problem

**Blender → Unreal Engine Scale Mismatch**

- **Blender**: 1 unit = 1 meter (exports VRM at 1.7m tall character)
- **Unreal Engine**: 1 unit = 1 centimeter (imports VRM as 1.7cm tall)
- **Result**: All static meshes authored in Blender at 1m scale appear 100× too small in UE

## Affected Constants in `pcg_portfolio_standards.py`

### Mesh Scale Constants (Need ×100)

| Constant | Current | Corrected (×100) | Mesh Types |
|----------|---------|------------------|------------|
| `GRASS_SCALE_MIN` | 0.6 | 60.0 | grass, flower, moss |
| `GRASS_SCALE_MAX` | 1.0 | 100.0 | grass, flower, moss |
| `ROCK_SCALE_MIN` | 0.4 | 40.0 | rock, ruin, cactus, scree |
| `ROCK_SCALE_MAX` | 1.2 | 120.0 | rock, ruin, cactus, scree |
| `PETAL_SCALE_MIN` | 0.18 | 18.0 | petal |
| `PETAL_SCALE_MAX` | 0.55 | 55.0 | petal |
| `FLOWER_SCALE_MIN` | 0.35 | 35.0 | flower |
| `FLOWER_SCALE_MAX` | 0.85 | 85.0 | flower |
| `DECOR_SCALE_MIN` | 0.65 | 65.0 | decor, lantern, neon, cactus |
| `DECOR_SCALE_MAX` | 1.35 | 135.0 | decor, lantern, neon, cactus |

### Style Preset Scales (Need ×100)

| Preset | Current Scale | Corrected Scale |
|--------|---------------|-----------------|
| meadow_bloom | (0.35, 0.85) | (35, 85) |
| blossom_path | (0.18, 0.55) | (18, 55) |
| lantern_grove | (0.65, 1.35) | (65, 135) |
| garden_ruins | (0.8, 1.8) | (80, 180) |
| sakura_petal_drift | (0.18, 0.55) | (18, 55) |
| zen_moss_groundcover | (0.45, 0.9) | (45, 90) |
| desert_arid | (0.8, 2.2) | (80, 220) |
| desert_oasis | (0.5, 0.9) | (50, 90) |
| cyberpunk_alley | (0.6, 1.5) | (60, 150) |
| cyberpunk_rooftop | (0.7, 1.8) | (70, 180) |
| alpine_pine_forest | (0.5, 1.2) | (50, 120) |
| alpine_scree | (0.4, 1.0) | (40, 100) |
| sakura_grove | (0.35, 0.85) | (35, 85) |
| ornamental_architecture | (0.8, 1.5) | (80, 150) |
| ornamental_detail_layer | (0.5, 1.2) | (50, 120) |

### Architectural Scales (Already Correct - Greybox authored in UE)

| Constant | Value | Status |
|----------|-------|--------|
| `COLUMN_HEIGHT_MIN` | 200.0 | ✓ Already cm |
| `COLUMN_HEIGHT_MAX` | 400.0 | ✓ Already cm |
| `ARCH_WIDTH_MIN` | 100.0 | ✓ Already cm |
| `ARCH_WIDTH_MAX` | 500.0 | ✓ Already cm |
| `FLOOR_TILE_SIZE` | 400.0 | ✓ Already cm |

### PCG Volume Scale (Actor Scale, Not Mesh Scale)

| Constant | Value | Note |
|----------|-------|------|
| `PCG_VOLUME_SCALE` | (10.0, 10.0, 3.0) | Actor scale, not mesh scale |

## Application Points in `pcg_graph_builder.py`

### 1. `configure_spawner()` (line ~241)
```python
# BEFORE:
apply_transform(desc, scale_min=std.GRASS_SCALE_MIN, scale_max=std.GRASS_SCALE_MAX)

# AFTER:
apply_transform(desc, scale_min=std.GRASS_SCALE_MIN * BLENDER_TO_UE_SCALE, scale_max=std.GRASS_SCALE_MAX * BLENDER_TO_UE_SCALE)
```

### 2. `wire_scatter_chain()` (line ~402)
```python
# BEFORE:
apply_transform(xform_settings, scale_min=std.GRASS_SCALE_MIN, scale_max=std.GRASS_SCALE_MAX)

# AFTER:
apply_transform(xform_settings, scale_min=std.GRASS_SCALE_MIN * BLENDER_TO_UE_SCALE, scale_max=std.GRASS_SCALE_MAX * BLENDER_TO_UE_SCALE)
```

### 3. `wire_mesh_scatter_chain()` (line ~471)
```python
# BEFORE:
apply_transform(s_xf, scale_min=std.COLUMN_HEIGHT_MIN, scale_max=std.COLUMN_HEIGHT_MAX)

# AFTER:
apply_transform(s_xf, scale_min=std.COLUMN_HEIGHT_MIN, scale_max=std.COLUMN_HEIGHT_MAX)  # Already in cm
```

### 4. Style Preset Application
```python
# In apply_transform calls from style presets:
"scale": (std.FLOWER_SCALE_MIN * BLENDER_TO_UE_SCALE, std.FLOWER_SCALE_MAX * BLENDER_TO_UE_SCALE)
```

## Implementation Strategy

1. **Add constant** at top of `pcg_portfolio_standards.py`:
   ```python
   BLENDER_TO_UE_SCALE = 100.0
   ```

2. **Multiply all mesh scale constants** by `BLENDER_TO_UE_SCALE`

3. **Update `apply_transform` calls** in `pcg_graph_builder.py` to use scaled values

3. **Style presets** automatically use corrected constants

## NPC Pipeline Mesh Scales

NPC archetype `MeshScale` values in `battle_integration.py` and `archetype_library.py` are **already correct** for UE (1.1, 1.2, 0.95 etc.) — these are applied to already-imported skeletal meshes.

## Validation Checklist

After fix applied:
- [ ] VRM character (1.7m in Blender) → 170cm in UE
- [ ] Grass blades (0.6m in Blender) → 60cm in UE
- [ ] Rock (1.0m in Blender) → 100cm in UE
- [ ] Petal (0.3m in Blender) → 30cm in UE
- [ ] Floor tile (4m in Blender) → 400cm in UE
- [ ] Column (3m in Blender) → 300cm in UE
- [ ] NPC archetype MeshScale 1.0 → correct proportion

## Rollback Plan

If fix breaks existing PCG captures:
1. Revert constants in `pcg_portfolio_standards.py`
2. Re-capture portfolio screenshots
3. Document as known migration