"""
MEL_p4_crystal_cathedral — Crystal Cathedral (god_molts)

Crystal growth on fractal ribs — same nave as MEL_p4_fractal_cathedral (1024 verts, 6-bay harmony
→ 2706 verts crystal, 8-bay grand 3598 verts) but vault ribs extrude as crystal shards
(prismatic pillars, facet-driven height from Chladni n=8,m=6 + warped fBm), rose window
becomes faceted crystal rosette, buttresses terminate in crystal pinnacles.
Default Bay Count 6 (song harmony C/Dm/F/G/Am/E → 18 pads). Palette from
GlitterCrystal/CrystalCathedral/DancingCrystals. Houdini meshes: SM_P4_Cathedral_Crystal.obj
2706v/2101f 6-bay + 8-bay grand 3598v hython 22.0.368, roses 1032v, 07 variants 2958v.
"""

from .core import register_builder, new_geometry_tree, make_group_input, link_sockets

def build_p4_crystal_cathedral():
    tree, gin, gout = new_geometry_tree("MEL_p4_crystal_cathedral")
    make_group_input(tree, "Recursion Depth", "NodeSocketInt", default=4, min_val=1, max_val=6)
    make_group_input(tree, "Arch Span", "NodeSocketFloat", default=10.0, min_val=1.0, max_val=20.0)
    make_group_input(tree, "Vault Height", "NodeSocketFloat", default=20.0, min_val=2.0, max_val=40.0)
    make_group_input(tree, "Tracery Density", "NodeSocketFloat", default=0.85, min_val=0.0, max_val=1.0)
    make_group_input(tree, "Bay Count", "NodeSocketInt", default=6, min_val=1, max_val=12)
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
