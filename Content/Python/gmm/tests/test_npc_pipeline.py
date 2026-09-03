"""No-editor contract tests for the VRM4U NPC pipeline."""
from __future__ import annotations

import unittest
from unittest.mock import patch

from gmm.npc import audit_npc
from gmm.npc.battle_integration import NPC_VARIANTS, generate_npc_enemy_defs
from gmm.npc.vrm4u_import import vrm4u_capabilities
from gmm.npc.cloth_setup import ClothConfig, validate_all_cloth_presets, validate_cloth_config
from gmm.ui.commands import run_gmm


class TestVRM4UReadiness(unittest.TestCase):
    def test_capabilities_fail_closed_outside_unreal(self):
        report = vrm4u_capabilities()
        self.assertFalse(report["ok"])
        self.assertEqual(report["state"], "unavailable")
        self.assertFalse(report["plugin_enabled"])

    def test_capabilities_command_is_registered(self):
        result = run_gmm("gmm.npc.vrm4u_capabilities", {})
        self.assertFalse(result.ok)
        self.assertEqual(result.outputs["state"], "unavailable")


class TestClothConfiguration(unittest.TestCase):
    def test_checked_in_presets_are_valid(self):
        self.assertEqual(validate_all_cloth_presets(), {})

    def test_invalid_solver_and_ranges_are_rejected(self):
        errors = validate_cloth_config(ClothConfig(
            piece_name="cape",
            archetype="CosmicWeaver",
            mobile_solver="Unknown",
            pc_solver="Unknown",
            mobile_iterations=0,
            pc_iterations=0,
            mobile_stiffness=2.0,
        ))
        self.assertIn("unsupported mobile_solver: Unknown", errors)
        self.assertIn("unsupported pc_solver: Unknown", errors)
        self.assertIn("mobile_iterations must be at least 1", errors)
        self.assertIn("pc_iterations must be at least 1", errors)
        self.assertIn("mobile_stiffness must be between 0 and 1", errors)


class TestNPCAuditDispatch(unittest.TestCase):
    def test_single_npc_passes_each_audit_its_supported_arguments(self):
        with (
            patch.object(audit_npc, "audit_skeletal_mesh", return_value=[]) as skeletal,
            patch.object(audit_npc, "audit_lods", return_value=[]) as lods,
            patch.object(audit_npc, "audit_materials", return_value=[]) as materials,
            patch.object(audit_npc, "audit_cloth", return_value=[]) as cloth,
            patch.object(audit_npc, "audit_battle_integration", return_value=[]) as battle,
            patch.object(audit_npc, "audit_npc_blueprint", return_value=[]) as blueprint,
        ):
            report = audit_npc.audit_single_npc("SD_01_SakuraMaiden", "SakuraDreamer", "/Game/Test/SK_Test")

        self.assertEqual(report.failed, 0)
        skeletal.assert_called_once_with("SD_01_SakuraMaiden", "/Game/Test/SK_Test")
        lods.assert_called_once_with("SD_01_SakuraMaiden", "/Game/Test/SK_Test")
        materials.assert_called_once_with("SD_01_SakuraMaiden", "/Game/Test/SK_Test")
        cloth.assert_called_once_with("SD_01_SakuraMaiden", "/Game/Test/SK_Test", "SakuraDreamer")
        battle.assert_called_once_with("SD_01_SakuraMaiden", "SakuraDreamer")
        blueprint.assert_called_once_with("SD_01_SakuraMaiden")


class TestNPCBattleDefinitions(unittest.TestCase):
    def test_every_variant_generates_a_unique_battle_enemy(self):
        generated = generate_npc_enemy_defs()
        self.assertEqual(set(generated), set(NPC_VARIANTS))
        self.assertEqual(len({entry["enemy_id"] for entry in generated.values()}), len(generated))
        self.assertTrue(all(entry["max_hp"] > 0.0 for entry in generated.values()))
        self.assertTrue(all(entry["max_toughness"] > 0.0 for entry in generated.values()))


if __name__ == "__main__":
    unittest.main()
