import ast
import unittest
from pathlib import Path


REPO = Path(__file__).resolve().parents[2]
SOURCE = REPO / "deploy" / "surreal_arch" / "melodia_gn" / "music_instruments.py"


def function_source(name):
    text = SOURCE.read_text(encoding="utf-8")
    tree = ast.parse(text)
    for node in tree.body:
        if isinstance(node, ast.FunctionDef) and node.name == name:
            return ast.get_source_segment(text, node)
    raise AssertionError("missing function %s" % name)


class InstrumentBuilderSourceContracts(unittest.TestCase):
    def test_tuning_fork_box_dimensions_are_wired(self):
        source = function_source("build_tuning_fork")
        self.assertIn('gin.outputs["Box Width"]', source)
        self.assertIn('gin.outputs["Box Height"]', source)
        self.assertIn('gin.outputs["Box Depth"]', source)
        self.assertIn('safe_node(tree, "ShaderNodeCombineXYZ"', source)

    def test_singing_bowl_is_open_and_controls_are_consumed(self):
        source = function_source("build_singing_bowl")
        self.assertIn('"GeometryNodeDeleteGeometry"', source)
        self.assertGreaterEqual(source.count('gin.outputs["Depth"]'), 2)
        self.assertIn('gin.outputs["Rim Width"]', source)
        self.assertIn('gin.outputs["Strike Point"]', source)

    def test_church_bell_uses_typed_clapper_and_socket_wiring(self):
        source = function_source("build_church_bell")
        self.assertIn('add_bool_param(tree, "Has Clapper", True)', source)
        self.assertNotIn('add_float_param(tree, "Has Clapper"', source)
        self.assertIn('clapper_xf,\n                        "Rotation"', source)
        self.assertNotIn('default_value = (\n                            swing.outputs', source)
        self.assertNotIn('"Shoulder Height"', source)


if __name__ == "__main__":
    unittest.main()
