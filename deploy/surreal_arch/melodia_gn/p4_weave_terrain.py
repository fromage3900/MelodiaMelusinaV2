"""
MEL_p4_weave_terrain — Weave Terrain (mother) — cloth-terrain hybrid stub

Cloth-terrain hybrid: pleat ridges ARE the heightmap via PleatedRange
technique (BASE_H 140, PLEAT_AMP 60, PLEAT_PERIOD 88, SEAM_DEPTH 90,
SEAM_WIDTH 26 from Saved/Audit/faraway_mother/cloth_mountains_v0_manifest.json),
embroidery motif scatter, seam valleys as flow. Bakes to R16 + Nanite.

Phase: P4 research stub 2026-09-01 — minimal registry + I/O so import
and GN Stack succeed; full heightfield+scatter graph lands in morning smoke.
"""

from .core import register_builder, new_geometry_tree, make_group_input, link_sockets

# PleatedRange constants from cloth_mountains_v0_manifest.json
BASE_H = 140.0
PLEAT_AMP = 60.0
PLEAT_PERIOD = 88.0
SEAM_DEPTH = 90.0
SEAM_WIDTH = 26.0
MOTIF_PERIOD = 46.0

def build_p4_weave_terrain():
    tree, gin, gout = new_geometry_tree("MEL_p4_weave_terrain")
    # Inputs — minimal stub (full ranges refined in Blender smoke)
    make_group_input(tree, "NodeSocketFloat", "Tile Size", default=2000.0, min_val=100.0, max_val=4000.0)
    make_group_input(tree, "NodeSocketFloat", "Pleat Amplitude", default=PLEAT_AMP, min_val=0.0, max_val=120.0)
    make_group_input(tree, "NodeSocketFloat", "Pleat Period", default=PLEAT_PERIOD, min_val=20.0, max_val=200.0)
    make_group_input(tree, "NodeSocketFloat", "Seam Depth", default=SEAM_DEPTH, min_val=0.0, max_val=200.0)
    make_group_input(tree, "NodeSocketFloat", "Seam Width", default=SEAM_WIDTH, min_val=1.0, max_val=80.0)
    make_group_input(tree, "NodeSocketFloat", "Motif Density", default=0.5, min_val=0.0, max_val=1.0)
    # Passthrough — full pleat/seam/scatter graph added in morning smoke
    link_sockets(tree, gin.outputs["Geometry"], gout.inputs["Geometry"])
    return tree, gin, gout

register_builder(
    "MEL_p4_weave_terrain",
    build_p4_weave_terrain,
    label="Weave Terrain",
    description="Cloth-terrain hybrid — pleat ridges as heightmap (PleatedRange BASE_H 140 PLEAT_AMP 60 PLEAT_PERIOD 88 SEAM_DEPTH 90), embroidery scatter, seam valleys; R16 + Nanite",
    category="mother",
)
