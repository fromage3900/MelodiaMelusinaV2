"""
MEL_p4_cymatic_organ_pipes — Cymatic Organ Pipes (P4 music builder)

Walkable pipe organ — pipe heights from cymatic Chladni nodal values,
pipe diameters from BeatPhase, facade tracery from cymatic Height.
Each pipe is a tuned Static Mesh with collision.

Phase: P4 research_only per Master Index s3 — additive stub, no P1/P0 overwrite.
Editor-open safe; full node graph added when owner promotes.
"""

from .core import register_builder, new_geometry_tree, make_group_input, link_sockets


def build_p4_cymatic_organ_pipes():
    tree, gin, gout = new_geometry_tree("MEL_p4_cymatic_organ_pipes")
    # Inputs — minimal stub, full cymatic sampling wired in promoted build
    make_group_input(tree, "Pipe Count", "NodeSocketInt", default=16, min_val=3, max_val=64)
    make_group_input(tree, "Height Scale", "NodeSocketFloat", default=6.0, min_val=1.0, max_val=20.0)
    make_group_input(tree, "Diameter Scale", "NodeSocketFloat", default=0.35, min_val=0.1, max_val=1.5)
    make_group_input(tree, "Facade Style", "NodeSocketInt", default=0, min_val=0, max_val=4)
    make_group_input(tree, "Cymatic Variant", "NodeSocketInt", default=0, min_val=0, max_val=8)
    # Passthrough — keeps import + registry + GN Stack presence valid
    link_sockets(tree, gin.outputs["Geometry"], gout.inputs["Geometry"])
    return tree, gin, gout


register_builder(
    "MEL_p4_cymatic_organ_pipes",
    build_p4_cymatic_organ_pipes,
    label="Cymatic Organ Pipes",
    description="Walkable pipe organ — pipe heights from cymatic Chladni nodal values, pipe diameters from BeatPhase, facade tracery from cymatic Height; each pipe is a tuned Static Mesh with collision",
    category="music",
)
