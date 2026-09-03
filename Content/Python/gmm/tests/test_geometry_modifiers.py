import unittest
from typing import cast

from gmm.geometry.modifiers import GeometryModifier, ModifierStack
from gmm.geometry.procedural_window import WindowSpec, build_window_cutters, build_window_stack
from gmm.geometry.schemas import validate_bevel_parameters, validate_boolean_parameters
from gmm.ui.commands import run_gmm


class TestGeometryModifiers(unittest.TestCase):
    def test_bevel_schema_accepts_safe_parameters(self):
        self.assertEqual(validate_bevel_parameters({"width": 0.04, "segments": 3}), [])

    def test_bevel_schema_rejects_unbounded_parameters(self):
        errors = validate_bevel_parameters({"width": 0, "segments": 64, "profile": 2})
        self.assertEqual(len(errors), 3)

    def test_stack_orders_and_serializes_modifiers(self):
        stack = ModifierStack("/Game/Test/SM_Cube")
        stack.add(GeometryModifier("bevel", "bevel"))
        stack.add(GeometryModifier("smooth", "smooth"))
        stack.move("smooth", 0)
        stack.set_enabled("bevel", False)
        stack.mark_previewed()

        data = stack.to_dict()
        modifiers = cast(list[dict[str, object]], data["modifiers"])
        self.assertEqual([item["id"] for item in modifiers], ["smooth", "bevel"])
        self.assertFalse(modifiers[1]["enabled"])
        self.assertEqual(data["lifecycle"], "preview")
        self.assertEqual(stack.validate(), [])

    def test_duplicate_ids_and_invalid_parameters_are_rejected(self):
        stack = ModifierStack("/Game/Test/SM_Cube")
        stack.add(GeometryModifier("bevel", "bevel"))
        with self.assertRaises(ValueError):
            stack.add(GeometryModifier("bevel", "bevel"))
        with self.assertRaises(ValueError):
            stack.set_parameter("bevel", "segments", 100)

    def test_actor_inspection_is_fail_closed_outside_unreal(self):
        result = run_gmm("gmm.geometry.describe_actor", {"actor_path": "/Game/Test/BP_Cube"})
        self.assertFalse(result.ok)
        self.assertEqual(result.outputs["state"], "unavailable")
        self.assertEqual(result.outputs["actor_path"], "/Game/Test/BP_Cube")

    def test_capabilities_command_is_structured_outside_unreal(self):
        result = run_gmm("gmm.geometry.capabilities", {})
        self.assertFalse(result.ok)
        self.assertEqual(result.outputs["state"], "unavailable")
        self.assertIn("plugins", result.outputs)
        self.assertIn("classes", result.outputs)

    def test_command_validates_stack_without_unreal(self):
        result = run_gmm("gmm.geometry.modifier_stack", {
            "target": "/Game/Test/SM_Cube",
            "preview": True,
            "modifiers": [{"id": "bevel_primary", "type": "bevel"}],
        })
        self.assertTrue(result.ok, result.error)
        self.assertEqual(result.outputs["lifecycle"], "preview")

    def test_command_rejects_invalid_stack(self):
        result = run_gmm("gmm.geometry.modifier_stack", {
            "target": "/Game/Test/SM_Cube",
            "modifiers": [{"id": "bad", "type": "bevel", "parameters": {"segments": 99}}],
        })
        self.assertFalse(result.ok)
        self.assertEqual(result.error, "invalid_stack")

    def test_preview_session_requires_confirmation_and_tracks_hash(self):
        session_id = "test_preview_lifecycle"
        preview = run_gmm("gmm.geometry.modifier_stack", {
            "target": "/Game/Test/SM_Cube",
            "preview": True,
            "session_id": session_id,
            "modifiers": [{"id": "bevel_primary", "type": "bevel"}],
        })
        self.assertTrue(preview.ok, preview.error)
        self.assertEqual(preview.outputs["state"], "preview")
        self.assertTrue(preview.outputs["stack_hash"])

        not_confirmed = run_gmm("gmm.geometry.bake", {"session_id": session_id})
        self.assertFalse(not_confirmed.ok)
        self.assertEqual(not_confirmed.error, "bake_confirmation_required")

        committed = run_gmm("gmm.geometry.commit_preview", {"session_id": session_id})
        self.assertTrue(committed.ok, committed.error)
        baked = run_gmm("gmm.geometry.bake", {"session_id": session_id, "confirm": True})
        self.assertTrue(baked.ok, baked.error)
        self.assertEqual(baked.outputs["state"], "baked")
        cleared = run_gmm("gmm.geometry.clear_preview", {"session_id": session_id})
        self.assertTrue(cleared.ok, cleared.error)
        self.assertEqual(cleared.outputs["state"], "cleared")

    def test_lifecycle_can_be_committed_and_baked_explicitly(self):
        stack = ModifierStack("/Game/Test/SM_Cube")
        stack.mark_committed()
        self.assertEqual(stack.lifecycle, "committed")
        stack.mark_baked()
        self.assertEqual(stack.lifecycle, "baked")

    def test_boolean_modifier_types_are_supported(self):
        for modifier_type in ("boolean_difference", "boolean_union", "boolean_intersect"):
            with self.subTest(modifier_type=modifier_type):
                modifier = GeometryModifier(
                    "bool_test",
                    modifier_type,
                    parameters={"cutter_mesh_path": "/Game/Test/SM_Cutter"},
                )
                self.assertEqual(modifier.validate(), [])

    def test_boolean_parameters_are_validated(self):
        errors = validate_boolean_parameters("boolean_difference", {
            "operation": "union",
            "cutter_mesh_path": "",
            "cutter_location": {"x": 0, "y": "bad", "z": 0},
            "cutter_rotation": {"pitch": 0, "yaw": 0, "roll": 0},
            "cutter_scale": {"x": 1, "y": 1, "z": 1},
            "show_preview": "yes",
            "preserve_cutter": False,
        })
        self.assertIn("operation 'union' does not match modifier_type 'boolean_difference'", errors)
        self.assertIn("cutter_mesh_path must be a non-empty Unreal asset path string", errors)
        self.assertIn("cutter_location.y must be a number", errors)
        self.assertIn("show_preview must be a boolean", errors)

    def test_procedural_window_produces_expected_cutters(self):
        spec = WindowSpec(
            wall_width=8.0,
            wall_height=3.5,
            wall_thickness=0.3,
            window_width=1.2,
            window_height=1.4,
            window_sill_height=1.0,
            count=3,
        )
        cutters = build_window_cutters(spec)
        self.assertEqual(len(cutters), 3)
        self.assertEqual(cutters[0].modifier_type, "boolean_difference")
        self.assertEqual(cutters[0].parameters["cutter_mesh_path"], "/Game/EnvSandbox/Meshes/Primitives/SM_WindowCutter")
        self.assertEqual(cutters[0].parameters["operation"], "difference")

        stack = build_window_stack("/Game/Test/SM_Wall", spec)
        self.assertEqual(stack.target, "/Game/Test/SM_Wall")
        self.assertEqual(len(stack.items), 3)
        self.assertEqual(stack.validate(), [])

    def test_procedural_window_rejects_invalid_spec(self):
        with self.assertRaises(ValueError):
            WindowSpec(count=-1)

    def test_boolean_preview_command_is_fail_closed_outside_unreal(self):
        result = run_gmm("gmm.geometry.boolean_preview", {
            "asset_path": "/Game/Test/SM_Wall",
            "modifier_type": "boolean_difference",
            "parameters": {"cutter_mesh_path": "/Game/Test/SM_Cutter"},
        })
        self.assertFalse(result.ok)
        self.assertEqual(result.outputs["state"], "unavailable")

    def test_boolean_apply_command_is_fail_closed_outside_unreal(self):
        result = run_gmm("gmm.geometry.boolean_apply", {
            "asset_path": "/Game/Test/SM_Wall",
            "modifier_type": "boolean_difference",
            "parameters": {"cutter_mesh_path": "/Game/Test/SM_Cutter"},
        })
        self.assertFalse(result.ok)
        self.assertEqual(result.outputs["state"], "unavailable")


if __name__ == "__main__":
    unittest.main()
