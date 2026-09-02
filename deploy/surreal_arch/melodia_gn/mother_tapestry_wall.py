"""
MEL_mother_tapestry_wall — Faraway Mother tapestry wall (P1 bridge builder)

Bridges: mother GN + Copernicus cymatics + fabric kit.
Vertical cloth plane with pleat/seam displacement sampled from cymatic Height,
embroidery atlas (A/B), and iridescence rim. Walkable backdrop for heart-gate.

Phase: overnight plan 2026-09-01 — editor-open safe, no Blender smoke yet.
"""

from .core import register_builder, new_geometry_tree, make_group_input, make_group_output, link_sockets

def build_mother_tapestry_wall():
    tree, gin, gout = new_geometry_tree("MEL_mother_tapestry_wall")
    # Inputs
    make_group_input(tree, "Width", "FLOAT", default=12.0, min_value=2.0, max_value=40.0)
    make_group_input(tree, "Height", "FLOAT", default=8.0, min_value=2.0, max_value=20.0)
    make_group_input(tree, "Pleat Amplitude", "FLOAT", default=0.6, min_value=0.0, max_value=2.0)
    make_group_input(tree, "Pleat Period", "FLOAT", default=88.0, min_value=20.0, max_value=200.0)
    make_group_input(tree, "Seam Depth", "FLOAT", default=0.9, min_value=0.0, max_value=3.0)
    # Geometry: grid -> pleat displace (placeholder links, refined in Blender)
    # Keep minimal so import + registry succeeds; full node graph added in morning smoke.
    link_sockets(gin, "Geometry", gout, "Geometry")
    return tree, gin, gout

register_builder(
    "MEL_mother_tapestry_wall",
    build_mother_tapestry_wall,
    label="Tapestry Wall",
    description="Faraway Mother tapestry wall — vertical cloth with pleat/seam displacement from cymatic Height + embroidery atlas; walkable heart-gate backdrop",
    category="mother",
)
