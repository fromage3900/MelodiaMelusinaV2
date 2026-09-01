"""
MEL_p4_fractal_cathedral — Recursive Gothic cathedral (god_molts)

Fractal arch subdivision, vault ribs, rose window from cymatic standing wave.
P4 stub — full Repeat Zone recursion wired in Blender smoke.
"""

from .core import register_builder, new_geometry_tree, make_group_input, link_sockets


def build_p4_fractal_cathedral():
    tree, gin, gout = new_geometry_tree("MEL_p4_fractal_cathedral")
    make_group_input(tree, "Recursion Depth", "NodeSocketInt", default=3, min_val=1, max_val=6)
    make_group_input(tree, "Arch Span", "NodeSocketFloat", default=6.0, min_val=1.0, max_val=20.0)
    make_group_input(tree, "Vault Height", "NodeSocketFloat", default=12.0, min_val=2.0, max_val=40.0)
    make_group_input(tree, "Tracery Density", "NodeSocketFloat", default=0.6, min_val=0.0, max_val=1.0)
    # Minimal passthrough — refined in Blender with Repeat Zone, cymatic rose window
    link_sockets(tree, gin.outputs["Geometry"], gout.inputs["Geometry"])
    return tree, gin, gout


register_builder(
    "MEL_p4_fractal_cathedral",
    build_p4_fractal_cathedral,
    label="Fractal Cathedral",
    description="Recursive Gothic cathedral — fractal arch subdivision, vault ribs, rose window from cymatic standing wave",
    category="god_molts",
)
