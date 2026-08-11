"""Pure tests for reusable visual chunk planning."""
from __future__ import annotations

import unittest

from pcg_visual_chunk_builder import build_visual_world_plan, validate_visual_world_plan
from pcg_scale_world_pipeline import (
    HERO_GRAPH_PATHS,
    WP_CELL_SIZE_CM,
    build_chunk_grid,
    chunk_origin_cm,
    hero_slots_for_chunk,
)


class VisualChunkBuilderTests(unittest.TestCase):
    def test_world_plan_is_deterministic_and_reuses_graph_assets(self):
        first = build_visual_world_plan(3900, radius=2)
        second = build_visual_world_plan(3900, radius=2)
        self.assertEqual(first, second)
        self.assertEqual(first["chunk_count"], 25)
        self.assertTrue(first["graph_reuse"])
        self.assertEqual(validate_visual_world_plan(first), [])
        self.assertTrue(all(path.startswith("/Game/") for path in HERO_GRAPH_PATHS))
        self.assertEqual(first["static_spec_count"], 25 * 16 + 25 * 2)
        self.assertTrue(all(not spec["interactive"] for spec in first["static_specs"]))

    def test_static_tiles_use_authored_library_and_one_owner_seams(self):
        plan = build_visual_world_plan(3900, radius=1)
        static_specs = plan["static_specs"]
        self.assertEqual(len([spec for spec in static_specs if spec["tier"] == "biome_dressing"]), 9 * 16)
        seam_specs = [spec for spec in static_specs if spec["tier"] == "seam_corridor"]
        # 12 internal interfaces plus 6 outward interfaces owned by the
        # visible window and continued by the next streamed ring.
        self.assertEqual(len(seam_specs), 18)
        self.assertEqual(len({spec["edge_signature"] for spec in seam_specs}), len(seam_specs))
        self.assertTrue(all(spec["mesh"].startswith("/Game/EnvSandbox/Greybox_Kit/") for spec in static_specs))

    def test_chunk_origins_align_to_world_partition_grid(self):
        for manifest in build_chunk_grid(3900, radius=2):
            self.assertEqual(
                tuple(manifest.world_origin_cm),
                chunk_origin_cm(manifest.chunk_x, manifest.chunk_y),
            )
            self.assertEqual(manifest.chunk_size_cm, WP_CELL_SIZE_CM)

    def test_sparse_landmarks_keep_the_proof_triad_stable(self):
        self.assertEqual(hero_slots_for_chunk(3900, 0, 0), ("ResonanceCathedral",))
        self.assertEqual(hero_slots_for_chunk(3900, 1, 0), ("ArpeggioBridge",))
        self.assertEqual(hero_slots_for_chunk(3900, -1, 0), ("BellTreeGarden",))

    def test_shared_curve_anchors_match_across_streaming_seams(self):
        manifests = build_chunk_grid(3900, radius=1)
        self.assertEqual(validate_visual_world_plan(build_visual_world_plan(3900, radius=2)), [])
        by_coord = {(entry.chunk_x, entry.chunk_y): entry.to_dict() for entry in manifests}
        for (chunk_x, chunk_y), current in by_coord.items():
            for direction, neighbor_coord, opposite, transverse in (
                ("east", (chunk_x + 1, chunk_y), "west", "y_cm"),
                ("north", (chunk_x, chunk_y + 1), "south", "x_cm"),
            ):
                neighbor = by_coord.get(neighbor_coord)
                if neighbor:
                    self.assertEqual(
                        current["border_anchor_layout"][direction][transverse],
                        neighbor["border_anchor_layout"][opposite][transverse],
                    )


if __name__ == "__main__":
    unittest.main()
