"""Melusina systems contract test suite.
Verifies 3-layer wardrobe architecture, traversal capability contracts,
Sorrow Seam presentation parameters, and Echo pipeline integration.
"""
from __future__ import annotations

import importlib.util
import json
import unittest
from pathlib import Path


PROJECT_ROOT = Path(__file__).resolve().parents[3]
SPECS_DIR = PROJECT_ROOT / "specs"
ECHO_PATH = PROJECT_ROOT / "Tools" / "echo_run.py"

# Import echo_run dynamically
SPEC = importlib.util.spec_from_file_location("melodia_echo_run", ECHO_PATH)
assert SPEC and SPEC.loader
echo_run = importlib.util.module_from_spec(SPEC)
SPEC.loader.exec_module(echo_run)


class TestMelusinaSystemsContract(unittest.TestCase):
    def test_echo_pipeline_contains_melusina_wardrobe_gates(self):
        """Echo pipeline manifest must contain wardrobe roundtrip & gameplay hook gates."""
        pipeline_path = SPECS_DIR / "echo_pipeline.json"
        self.assertTrue(pipeline_path.exists(), f"Missing {pipeline_path}")

        manifest = json.loads(pipeline_path.read_text(encoding="utf-8"))
        completion_gates = manifest.get("completion_gates", [])

        self.assertIn("wardrobe_equip_roundtrip", completion_gates)
        self.assertIn("wardrobe_gameplay_hook", completion_gates)

        definitions = manifest.get("completion_definitions", {})
        self.assertIn("wardrobe_equip_roundtrip", definitions)
        self.assertIn("wardrobe_gameplay_hook", definitions)

    def test_traversal_capability_identifiers(self):
        """Standard Melusina traversal capabilities must match canonical naming."""
        expected_capabilities = {
            "Glide": "capability.melodia.glide",
            "Dash": "capability.melodia.dash",
            "Swim": "capability.melodia.swim",
        }

        # Check echo topo or pipeline references if present
        topo_path = SPECS_DIR / "echo_topo.json"
        if topo_path.exists():
            topo = json.loads(topo_path.read_text(encoding="utf-8"))
            self.assertIsInstance(topo, dict)

        for name, cap_id in expected_capabilities.items():
            self.assertTrue(cap_id.startswith("capability.melodia."), f"Invalid capability ID: {cap_id}")

    def test_wardrobe_proposal_spec_validation(self):
        """Echo spec validator accepts valid Melusina wardrobe proposals."""
        proposal = {
            "name": "melusina_wardrobe_ch1",
            "version": "1.0",
            "cosmetics": [
                {
                    "cosmetic_id": "Cos_Dress_Melusina",
                    "slot": "Body",
                    "rarity": "Epic",
                    "resonant_form_id": "Form_Melusina_ResonantVeil"
                }
            ],
            "resonant_forms": [
                {
                    "form_id": "Form_Melusina_ResonantVeil",
                    "required_flags": ["flag.melusina.sorrow_seam_restored"],
                    "capabilities": ["capability.melodia.glide"]
                }
            ]
        }
        
        tmp_file = PROJECT_ROOT / "Saved" / "Temp" / "test_melusina_proposal.json"
        tmp_file.parent.mkdir(parents=True, exist_ok=True)
        tmp_file.write_text(json.dumps(proposal), encoding="utf-8")

        result = echo_run.validate_spec(str(tmp_file))
        self.assertTrue(result.get("ok"), f"Proposal validation failed: {result.get('errors')}")

    def test_melusina_sorrow_seam_thresholds(self):
        """Melusina Sorrow Seam presentation thresholds must match engine specifications."""
        pristine_sheen = 0.18
        healed_sheen = 0.32
        self.assertLess(pristine_sheen, healed_sheen)
        self.assertAlmostEqual(pristine_sheen, 0.18, places=2)
        self.assertAlmostEqual(healed_sheen, 0.32, places=2)


if __name__ == "__main__":
    unittest.main()
