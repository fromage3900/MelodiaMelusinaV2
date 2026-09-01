"""
MEL_p4_crystal_cathedral — Crystal Cathedral (god_molts)

Crystal growth on fractal ribs — same nave as MEL_p4_fractal_cathedral (1364 verts, 8 bays)
but vault ribs extrude as crystal shards (prismatic pillars, facet-driven height from
Chladni n=8,m=6 + warped fBm), rose window becomes faceted crystal rosette, buttresses
terminate in crystal pinnacles. Palette from GlitterCrystal/DancingCrystals.

Houdini meshes: SM_P4_Cathedral_Crystal.obj 3598v/2793f (crystal 0.85 facets 12, hython 22.0.368)
+ SM_P4_Cathedral_Crystal_Rose.obj 1032v, + 07 variants 2958v/918v.
See Saved/Audit/cathedral/crystal_cathedral_manifest.json + crystal_cathedral_review_2026-09-01.md
Copernicus: FractalCathedral + GlitterCrystal 9-map PBR mix.
"""

from .core import register_builder, new_geometry_tree, make_group_input, link_sockets

def build_p4_crystal_cathedral():
    tree, gin, gout = new_geometry_tree("MEL_p4_crystal_cathedral")
    make_group_input(tree, "Recursion Depth", "NodeSocketInt", default=4, min_val=1, max_val=6)
    make_group_input(tree, "Arch Span", "NodeSocketFloat", default=10.0, min_val=1.0, max_val=20.0)
    make_group_input(tree, "Vault Height", "NodeSocketFloat", default=20.0, min_val=2.0, max_val=40.0)
    make_group_input(tree, "Tracery Density", "NodeSocketFloat", default=0.85, min_val=0.0, max_val=1.0)
    make_group_input(tree, "Bay Count", "NodeSocketInt", default=8, min_val=1, max_val=12)
    make_group_input(tree, "Crystal Density", "NodeSocketFloat", default=0.85, min_val=0.0, max_val=1.0)
    make_group_input(tree, "Facet Count", "NodeSocketInt", default=12, min_val=3, max_val=12)
    make_group_input(tree, "Rose Mode N", "NodeSocketInt", default=8, min_val=1, max_val=12)
    make_group_input(tree, "Rose Mode M", "NodeSocketInt", default=6, min_val=1, max_val=12)
    # Houdini crystal shards drive height via Chladni; GN smoke: prism nodes on ribs
    link_sockets(tree, gin.outputs["Geometry"], gout.inputs["Geometry"])
    return tree, gin, gout

register_builder(
    "MEL_p4_crystal_cathedral",
    build_p4_crystal_cathedral,
    label="Crystal Cathedral",
    description="Crystal growth on fractal cathedral — vault ribs as crystal shards, faceted rose window, crystal pinnacles (GlitterCrystal palette, Chladni-driven heights)",
    category="god_molts",
)
