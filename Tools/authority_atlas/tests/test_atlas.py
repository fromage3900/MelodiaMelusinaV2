from pathlib import Path
import sys
import unittest

REPO_ROOT = Path(__file__).resolve().parents[3]
sys.path.insert(0, str(REPO_ROOT))

from Tools.authority_atlas.atlas import (  # noqa: E402
    AUDIT_DATE,
    JSON_RELATIVE_PATH,
    REPORT_RELATIVE_PATH,
    build_atlas,
    normalized_json_bytes,
    render_markdown,
)
from Tools.authority_atlas.policy import CLASSIFICATIONS, CORE_DOMAINS  # noqa: E402


class AuthorityAtlasTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.atlas = build_atlas(REPO_ROOT)

    def test_two_builds_are_byte_identical(self):
        second = build_atlas(REPO_ROOT)
        self.assertEqual(normalized_json_bytes(self.atlas), normalized_json_bytes(second))

    def test_every_core_domain_has_named_owner(self):
        owners = {item["domain"]: item["canonical_owner"] for item in self.atlas["authority_map"]}
        self.assertEqual(set(CORE_DOMAINS), set(owners))
        self.assertFalse(self.atlas["validation"]["core_domains_without_owner"])

    def test_required_node_fields_and_classifications(self):
        required = {
            "path", "symbol", "lifecycle", "state_owned", "public_mutations",
            "save_participation", "consumers", "canonical_owner",
            "runtime_reachability_evidence", "verdict", "confidence", "source_citations",
        }
        self.assertTrue(self.atlas["nodes"])
        for node in self.atlas["nodes"]:
            self.assertTrue(required.issubset(node), node["id"])
            self.assertIn(node["classification"], CLASSIFICATIONS)

    def test_stock_blueprints_are_explicit_live_evidence_nodes(self):
        by_symbol = {node["symbol"]: node for node in self.atlas["nodes"]}
        for symbol in ("BP_BattleController", "BP_JRPGSaveGame", "BP_BattleUI"):
            self.assertEqual("CANONICAL", by_symbol[symbol]["classification"])
            self.assertEqual("LIVE_EVIDENCE_REQUIRED", by_symbol[symbol]["runtime_reachability_evidence"]["tier"])

    def test_gmm_and_reflection_risks_are_reported(self):
        self.assertGreater(self.atlas["gmm_blast_radius"]["module_count"], 0)
        self.assertTrue(self.atlas["gmm_blast_radius"]["gameplay_authority_like_files"])
        self.assertTrue(any(not item["inside_external_jrpg_bridge"] for item in self.atlas["reflection_boundary_findings"]))

    def test_dated_outputs_and_report_claims(self):
        self.assertEqual("2026-08-24", AUDIT_DATE)
        self.assertIn("20260824", JSON_RELATIVE_PATH)
        self.assertIn("2026-08-24", REPORT_RELATIVE_PATH)
        report = render_markdown(self.atlas)
        self.assertIn("# Gameplay Authority Atlas - 2026-08-24", report)
        self.assertNotIn("2026-08-23", report)
        self.assertIn("Static reachability is not runtime proof", report)
        self.assertIn("Focused GMM blast radius", report)


if __name__ == "__main__":
    unittest.main()
