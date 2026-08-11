"""Pure tests for the scale-world and BellTreeGarden contracts."""
from __future__ import annotations

import unittest

from build_pcg_hero_arpeggio_bridge import build_classic_bridge_architecture_branches
from build_pcg_hero_bell_tree_garden import BELL_PATTERN, bell_midi_pattern, build_bell_branch_curve_points, build_bell_garden_layout, build_classic_bell_architecture_branches
from build_pcg_hero_resonance_cathedral import build_classic_architecture_branches
from build_pcg_water_gameplay_interactive import build_water_gameplay_layout
from pcg_scale_world_pipeline import (
    GENERATOR_VERSION,
    WP_CELL_SIZE_CM,
    build_chunk_grid,
    interactive_placements_for_chunk,
    make_chunk_manifest,
    scale_contract,
    shared_border_signature,
    stable_chunk_seed,
    stable_interactive_actor_id,
    validate_grid,
    validate_chunk_manifest,
)
from run_pcg_scale_world_build import command_for, commandlet_asset_path
from pcg_visual_chunk_builder import build_visual_world_plan


class ScaleWorldContractTests(unittest.TestCase):
    def test_three_by_three_grid_is_deterministic_and_seam_safe(self):
        first = build_chunk_grid(3900, radius=1)
        second = build_chunk_grid(3900, radius=1)
        self.assertEqual([entry.to_dict() for entry in first], [entry.to_dict() for entry in second])
        self.assertEqual(len(first), 9)
        self.assertEqual(validate_grid(first), [])
        self.assertEqual(first[0].chunk_size_cm, WP_CELL_SIZE_CM)
        by_coord = {(entry.chunk_x, entry.chunk_y): entry for entry in first}
        self.assertEqual(by_coord[(0, 0)].hero_slot_assignments, ("ResonanceCathedral",))
        self.assertEqual(by_coord[(1, 0)].hero_slot_assignments, ("ArpeggioBridge",))
        self.assertEqual(by_coord[(-1, 0)].hero_slot_assignments, ("BellTreeGarden",))
        self.assertEqual(by_coord[(0, 1)].hero_slot_assignments, ("XylophoneTrail",))
        self.assertIn("DL_Musical_HeroGameplay", first[0].data_layer_assignments)

    def test_shared_edge_signature_is_order_independent(self):
        forward = shared_border_signature(3900, 0, 0, 1, 0)
        reverse = shared_border_signature(3900, 1, 0, 0, 0)
        self.assertEqual(forward, reverse)
        self.assertEqual(stable_chunk_seed(3900, 0, 0), stable_chunk_seed(3900, 0, 0, GENERATOR_VERSION))

    def test_hero_volume_bindings_carry_nikki_dressing_recipes(self):
        plan = build_visual_world_plan(3900, radius=1)
        recipes = {spec["nikki_dressing_recipe"] for spec in plan["hero_volume_specs"]}
        self.assertIn("ResonanceCathedral", recipes)
        self.assertIn("ArpeggioBridge", recipes)
        self.assertIn("BellTreeGarden", recipes)
        self.assertIn("XylophoneTrail", recipes)
        self.assertIn("CrystalHarpGrove", recipes)

    def test_manifest_rejects_wrong_grid_scale(self):
        manifest = make_chunk_manifest(3900, 0, 0).to_dict()
        manifest["chunk_size_cm"] = 1024
        self.assertTrue(validate_chunk_manifest(manifest))

    def test_bell_garden_has_eighteen_unique_seeded_notes(self):
        nodes, _ = build_bell_garden_layout()
        self.assertEqual(len(nodes), 18)
        seeds = [(node_index << 16) | ((branch + 1) << 8) | midi for _, _, _, node_index, _lane, midi, branch in nodes]
        self.assertEqual(len(seeds), len(set(seeds)))
        self.assertEqual(tuple(midi for *_, midi, _branch in nodes), bell_midi_pattern())
        self.assertEqual(set(midi % 12 for midi in BELL_PATTERN), {0, 2, 4, 7, 9})
        self.assertEqual(len(build_bell_branch_curve_points()), 18)

    def test_pcg_builder_command_contains_scale_safe_flags(self):
        command = command_for(
            "/Game/EnvSandbox/PCG/Musical/Hero/L_PCG_Hero_ScaleWorldProof",
            "PCGWorldPartitionBuilder",
            graph_names=("PCG_Hero_BellTreeGarden",),
        )
        joined = " ".join(command)
        self.assertIn("-IterativeCellLoading", joined)
        self.assertIn("-IterativeCellSize=25600", joined)
        self.assertIn("-AssetGatherAll", joined)
        self.assertIn("-stdout", joined)
        self.assertIn("-GenerateComponentEditingModeNormal", joined)
        self.assertIn("-DDC-ForceMemoryCache", joined)
        self.assertIn("-ShaderWorkingDir=Saved/ShaderWorkingDir/PCGScaleWorld", joined)
        self.assertIn("-IncludeGraphNames=PCG_Hero_BellTreeGarden", joined)
        self.assertIn("PCG_Hero_CrystalHarpGrove", command_for(
            "/Game/EnvSandbox/PCG/Musical/Hero/L_PCG_Hero_ScaleWorldProof",
            "PCGWorldPartitionBuilder",
            graph_names=("PCG_Hero_CrystalHarpGrove",),
        )[-1])

    def test_hero_architecture_keeps_walkable_negative_space(self):
        bridge = build_classic_bridge_architecture_branches(24, 180.0, 1800.0, 220.0)
        self.assertNotIn("classic bridge portals", {branch["label"] for branch in bridge})
        self.assertTrue(all(branch["mesh"].endswith(("SM_Greybox_Floor_4x4", "SM_Greybox_HalfWall_4", "SM_column_02")) for branch in bridge))

        bells = build_classic_bell_architecture_branches(18, 260.0, 900.0, 300.0, 3)
        columns = next(branch for branch in bells if branch["label"] == "classic bell garden columns")
        arches = next(branch for branch in bells if branch["label"] == "classic bell garden branch arches")
        self.assertEqual(len(columns["points"]), 6)
        self.assertEqual(len(arches["points"]), 3)

        cathedral = build_classic_architecture_branches(4, 480.0, 220.0, 1800.0)
        column_branch = next(branch for branch in cathedral if branch["label"] == "classic measured columns")
        self.assertGreaterEqual(abs(column_branch["points"][0][0][1]), 880.0)

    def test_commandlet_asset_path_is_explicit(self):
        self.assertEqual(
            commandlet_asset_path("/Game/EnvSandbox/PCG/Musical/Hero/DA_PCGHeroBuilderSettings"),
            "/Game/EnvSandbox/PCG/Musical/Hero/DA_PCGHeroBuilderSettings.DA_PCGHeroBuilderSettings",
        )

    def test_interactive_water_placements_are_stable_and_gameplay_owned(self):
        manifests = build_chunk_grid(3900, radius=1)
        harp_manifest = next(entry for entry in manifests if entry.hero_slot_assignments == ("CrystalHarpGrove",))
        placements = harp_manifest.interactive_placement_specs
        self.assertEqual(len(placements), 8)
        self.assertEqual(len({placement.stable_actor_id for placement in placements}), 8)
        self.assertTrue(all(placement.exclude_from_hlod for placement in placements))
        self.assertTrue(all(placement.gameplay_data_layer == "DL_Musical_HeroGameplay" for placement in placements))
        self.assertEqual(
            placements[0].stable_actor_id,
            stable_interactive_actor_id(3900, 1, 1, "CrystalHarpGrove", 0, "resonance_station"),
        )
        self.assertEqual(validate_chunk_manifest(harp_manifest.to_dict()), [])

    def test_scale_contract_explicitly_binds_water_runtime(self):
        contract = scale_contract()
        dependency_names = {entry["class"] for entry in contract["runtime_dependencies"]}
        self.assertIn("APCGHeroMusicNode", dependency_names)
        self.assertIn("APCGHeroMusicGraphHost", dependency_names)
        self.assertIn("UMelodiaWaterGameplaySubsystem", dependency_names)
        self.assertIn("UMelodiaWaterInteractionSubsystem", dependency_names)
        self.assertIn("AMelodiaWaterPlatform", dependency_names)
        self.assertEqual(contract["interactive_placement_contract"]["gameplay_data_layer"], "DL_Musical_HeroGameplay")
        self.assertTrue(contract["interactive_placement_contract"]["exclude_from_hlod"])

    def test_water_graph_layout_contains_devices_and_both_platform_modes(self):
        layout = build_water_gameplay_layout()
        roles = {entry["role"] for entry in layout}
        self.assertIn("resonance_station", roles)
        self.assertIn("valve_anchor", roles)
        self.assertIn("water_gate_anchor", roles)
        self.assertIn("moving_platform", roles)
        self.assertIn("buoyant_platform", roles)
        self.assertIn("current_volume_anchor", roles)
        self.assertEqual({entry["motion_mode"] for entry in layout if entry["motion_mode"] != "None"}, {"KinematicRoute", "PhysicsBuoyant"})


if __name__ == "__main__":
    unittest.main()
