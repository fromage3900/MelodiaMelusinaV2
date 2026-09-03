"""
MEL_p4_molten_shell_city — god_molts: Molten Shell City (P4 stub)

Shell as city — plates as districts, fracture seams as streets, growth rings as terraces.
P4 shell-city kit: shell geometry reimagined as urban fabric; plates become districts,
seams become streets, concentric growth rings become terraced levels.

Phase: P4 stub 2026-09-01 — minimal inputs, passthrough geometry; full node graph
added when editor work begins. Follows mother_tapestry_wall.py pattern, category god_molts.
"""

from .core import register_builder, new_geometry_tree, make_group_input, link_sockets


def build_p4_molten_shell_city():
    tree, gin, gout = new_geometry_tree("MEL_p4_molten_shell_city")
    # Inputs — Shell as city controls
    make_group_input(tree, "Shell Scale", "FLOAT", default=12.0, min_value=0.5, max_value=100.0)
    make_group_input(tree, "Fracture Count", "INT", default=8, min_value=1, max_value=32)
    make_group_input(tree, "Terrace Levels", "INT", default=5, min_value=1, max_value=16)
    make_group_input(tree, "Street Width", "FLOAT", default=0.4, min_value=0.02, max_value=4.0)
    make_group_input(tree, "Iridescence", "FLOAT", default=0.7, min_value=0.0, max_value=1.0)
    # Geometry: passthrough (placeholder links, refined in Blender)
    # Keep minimal so import + registry succeeds; full node graph added when editor work begins.
    link_sockets(gin, "Geometry", gout, "Geometry")
    return tree, gin, gout


register_builder(
    "MEL_p4_molten_shell_city",
    build_p4_molten_shell_city,
    label="Molten Shell City",
    description="Shell as city — plates as districts, fracture seams as streets, growth rings as terraces",
    category="god_molts",
)
