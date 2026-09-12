# Sea Above — Aurora Glacier Gaea Build Handoff (2026-08-26)

## Deliverable: UE-ready terrain maps (built, verified)
Source: `Saved/Audit/gaea_setups/aurora_glacier/build/`
- `AuroraGlacier_Height.png`   — 2048×2048 32bpp — **Mesh Terrain heightmap donor**
- `AuroraGlacier_Flow.png`     — 2048×2048 32bpp — flow/water mask
- `AuroraGlacier_Curvature.png`— 2048×2048 32bpp — curvature/cliff mask
- `gaea_build_verify.json`     — build + resolution `diagnostic`

Built via Gaea Swarm CLI (`Gaea.Swarm.exe`) headless from
`Saved/Audit/gaea_setups/aurora_glacier/AuroraGlacier_MeshTerrainExport_Final.terrain`
(already contains the UE exporter / `QuadSpinner.Gaea.Nodes.Unreal` node). Committed
assembly plan documents this in `Docs/Art/TONIGHT_ASSEMBLY_PLAN_2026-08-26.md`.

## Next (UE editor open, Monolith 9316 up)
1. Drive `Content/Python/stage_*gaea_mesh_terrain_import*.py` against `AuroraGlacier_Height.png`
   → `/Game/_PROJECT/ResonantWorld/Offline/GaeaSetups/AuroraGlacierMesh`.
2. Assign `M_Master_Toon_Landscape_HeightBlend`-derived substrate MI.
3. Place inverted V10 `OceanPreview` plane at basin low point as the false-ocean (Aurora
   lacks a `Sea.Water` mask; the Canyon River-with-Sea graph gives that if desired later).

## Cortex / automation note
`Gaea.Swarm.exe` is the CLI automation surface; good basis for the future `gaea-mcp`
server. `prepare_gaea_seaabove_export_native.ps1` targets the sea graph (Canyon) and is
committed (force-added; `Tools/WorldGen` is ignored).