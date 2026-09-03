"""
MEL_p4_tapestry_citadel — mother: Tapestry Citadel (P4 stub)

Citadel of tapestry walls — assembles mother_tapestry_wall instances into
curtain walls / bastions / gatehouse. Every wall IS a tapestry — wall Height
drives pleat displacement, embroidery atlas drives trim, PCG sampler for
Nanite wall distribution.

Phase: P4 stub 2026-09-01 — minimal inputs, passthrough geometry; full node
graph added when editor work begins. Follows mother_tapestry_wall.py pattern,
category mother.
"""

from .core import register_builder, new_geometry_tree, make_group_input, link_sockets


def build_p4_tapestry_citadel():
    tree, gin, gout = new_geometry_tree("MEL_p4_tapestry_citadel")
    # Inputs — citadel assembly controls
    make_group_input(tree, "Citadel Radius", "FLOAT", default=28.0, min_value=5.0, max_value=200.0)
    make_group_input(tree, "Wall Height", "FLOAT", default=10.0, min_value=2.0, max_value=30.0)
    make_group_input(tree, "Bastion Count", "INT", default=6, min_value=3, max_value=12)
    make_group_input(tree, "Tapestry Variant", "INT", default=0, min_value=0, max_value=7)
    make_group_input(tree, "Gate Width", "FLOAT", default=4.5, min_value=1.0, max_value=12.0)
    # Geometry: passthrough (placeholder links, refined in Blender)
    # Curtain walls + bastions + gatehouse instances of mother_tapestry_wall
    # wired here in morning smoke; keep minimal so import + registry succeeds.
    link_sockets(gin, "Geometry", gout, "Geometry")
    return tree, gin, gout


register_builder(
    "MEL_p4_tapestry_citadel",
    build_p4_tapestry_citadel,
    label="Tapestry Citadel",
    description="Citadel of tapestry walls — mother_tapestry_wall instances into curtain walls/bastions/gatehouse; tapestry Height drives displacement, embroidery drives trim; Nanite + PCG",
    category="mother",
)
