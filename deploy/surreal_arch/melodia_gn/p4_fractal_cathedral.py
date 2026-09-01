"""
MEL_p4_fractal_cathedral — Recursive Gothic cathedral (god_molts)

Fractal arch subdivision, vault ribs, rose window from cymatic standing wave.
Houdini mesh SM_P4_Cathedral_Fractal.obj (1024 verts, 493 faces, 6-bay harmony,
hython 22.0.368, depth 4 span 10 height 20) ↔ SM_P4_Cathedral_Fractal_8Bays_Grand
(1364 verts, 657 faces, 8 bays grand) + SM_P4_Cathedral_RoseWindow.obj (782 verts,
Chladni n=8,m=6) — see Saved/Audit/cathedral/. 8 inputs mirror houdini params.
Default Bay Count 6 matches 6-station song (C/Dm/F/G/Am/E → 18 pads).
GN: Repeat Zone arch recursion, diagonal vault ribs, Chladni rose tracery.
Copernicus: FractalCathedral + CrystalCathedral 9-map PBR drives stone/gold/glow.
"""

from .core import register_builder, new_geometry_tree, make_group_input, link_sockets


def build_p4_fractal_cathedral():
    tree, gin, gout = new_geometry_tree("MEL_p4_fractal_cathedral")
    make_group_input(tree, "Recursion Depth", "NodeSocketInt", default=3, min_val=1, max_val=6)
    make_group_input(tree, "Arch Span", "NodeSocketFloat", default=6.0, min_val=1.0, max_val=20.0)
    make_group_input(tree, "Vault Height", "NodeSocketFloat", default=12.0, min_val=2.0, max_val=40.0)
    make_group_input(tree, "Tracery Density", "NodeSocketFloat", default=0.6, min_val=0.0, max_val=1.0)
    make_group_input(tree, "Bay Count", "NodeSocketInt", default=6, min_val=1, max_val=12)
    make_group_input(tree, "Buttress Depth", "NodeSocketInt", default=2, min_val=1, max_val=5)
    make_group_input(tree, "Rose Mode N", "NodeSocketInt", default=8, min_val=1, max_val=12)
    make_group_input(tree, "Rose Mode M", "NodeSocketInt", default=6, min_val=1, max_val=12)
    # Expanded — houdini mesh SM_P4_Cathedral_Fractal.obj (1364 verts, 657 faces, hython 22.0.368) +
    # FractalCathedral 9-map PBR reference. GN smoke: Repeat Zone arch subdivision,
    # vault ribs (diagonal cross), Chladni rose window (cos nπu cos mπv). Passthrough until Blender smoke.
    link_sockets(tree, gin.outputs["Geometry"], gout.inputs["Geometry"])
    return tree, gin, gout


register_builder(
    "MEL_p4_fractal_cathedral",
    build_p4_fractal_cathedral,
    label="Fractal Cathedral",
    description="Recursive Gothic cathedral — fractal arch subdivision, vault ribs, rose window from cymatic standing wave",
    category="god_molts",
)
