# Universal Environment Pipeline

This pipeline is generic. It supports SakuraPath and future scenes, but it does not own final Sakura level art direction.

## Goal

Make every new environment style follow a repeatable path:

```text
Style or biome brief
  -> modular assets / procedural layout
  -> universal material assignment
  -> generic PCG scatter standards
  -> L_Template or neutral test validation
  -> capture and manifests
  -> portfolio package
  -> website / Figma / ArtStation metadata
```

## Canonical Flow

1. **Choose style family or biome**
   - Examples: Zen, Baroque, Art Nouveau, Gothic, Sci-Fi, coastal, forest, courtyard.
   - Source docs: research notes, style genomes, material family manifests.

2. **Generate or import modular assets**
   - Use Blender/world manifest tooling when appropriate.
   - Keep source DCC assets outside transient Unreal folders.
   - Preserve the role-to-material boundary through `ROLE_UE_HINTS`.

3. **Assign material families**
   - Mesh/prop/trimsheet: `M_Master_Toon_Universal`.
   - Terrain: `M_Master_Toon_Landscape_HeightBlend`.
   - Water: `M_Water_Master_Grand_v6`.
   - Use material instances, not new masters, unless a new master is explicitly approved.

4. **Apply generic PCG standards**
   - Use universal PCG graphs and style wrappers.
   - Maintain tags such as `PCG_Ground`, `PCG_Volume`, and `PCG_Exclude`.
   - Keep scatter material assumptions documented through the material manifest.

5. **Validate in neutral context**
   - Prefer `L_Template` or another neutral test map for material and look-dev proof.
   - Do not require `L_SakuraPath` for generic validation.

6. **Capture proof artifacts**
   - Material grids.
   - Landscape slabs.
   - Water planes.
   - PCG top-down or diagnostic shots.
   - Breakdown plates where available.

7. **Compile package**
   - `compile_render_plates.py` -> `Saved/Portfolio/Renders/renders_manifest.json`
   - `material_family_manifest.py` -> material manifest and preview-compatible metadata.
   - `portfolio_aggregator.py` -> `Saved/Portfolio/portfolio_package.json`

8. **Generate presentation handoff**
   - Website configs.
   - Figma/design-system fields.
   - ArtStation-ready captions and stats.

## Completion Criteria

- A generic environment style can be validated without modifying Sakura.
- Material family metadata exists as JSON.
- Preview/capture gaps are reported rather than silently ignored.
- PCG and material assumptions are visible to agents and humans.
- Presentation layers consume package metadata or have an explicit manual handoff.
