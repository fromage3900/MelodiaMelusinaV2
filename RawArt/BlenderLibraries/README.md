# BlenderLibraries — third-party GN node libraries (LOCAL ONLY)

This directory holds third-party Blender node-group libraries that Melodia
Studio builders reference. Contents are NOT committed (licensed third-party
distribution — see .gitignore). Each workstation places its own copy.

## Higgsas/

Required by: `deploy/surreal_arch/higgsas_bridge.py` (33 NT* arch nodes),
`melodia_gn/core_forms_kit.py` (NTSpin/NTTaper pillars),
`melodia_gn/walls_kit.py` (NTBricks Grid/NTSolidify walls).

Source: Higgsas Geometry Nodes Toolset v1.3 (vfxMed distribution).

Placement — copy from the toolset archive so this exact file exists:

    RawArt/BlenderLibraries/Higgsas/Blender 5.0 Higgsas Geo Node Groups v13.blend
    RawArt/BlenderLibraries/Higgsas/blender_assets.cats.txt

Path resolution order (`deploy/surreal_arch/capabilities.py`):

1. addon preference `higgsas_library_path` (Edit > Preferences > Melodia Studio)
2. `<repo>/RawArt/BlenderLibraries/Higgsas/Blender 5.0 Higgsas Geo Node Groups v13.blend`
3. legacy `G:\programs\BlenderPlugins\...` (original authoring PC)
4. `%USERPROFILE%\Downloads\Higgsas_Geometry_Nodes_Toolset_v1.3\...`

If unresolved, Higgsas-dependent builders fall back to primitive geometry
(graceful, but degraded — verify with `deploy/higgsas_verify.py`).
