#!/usr/bin/env python3
from __future__ import annotations

import importlib.util
import json
import unittest
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
MODULE_PATH = ROOT / "Tools" / "universe_foundry.py"

spec = importlib.util.spec_from_file_location("universe_foundry", MODULE_PATH)
assert spec and spec.loader
uf = importlib.util.module_from_spec(spec)
spec.loader.exec_module(uf)

GENOME_PATH = ROOT / "specs" / "universe" / "faraway_mother.world_genome.v1.json"
DELTA_PATH = ROOT / "specs" / "universe" / "faraway_mother.resolved_demo.world_delta.v1.json"


class UniverseFoundryTests(unittest.TestCase):
    def setUp(self):
        self.genome = json.loads(GENOME_PATH.read_text(encoding="utf-8"))
        self.delta = json.loads(DELTA_PATH.read_text(encoding="utf-8"))

    def test_fixtures_validate(self):
        self.assertEqual([], uf.validate_genome(self.genome))
        self.assertEqual([], uf.validate_delta(self.delta, self.genome["world_id"]))

    def test_compile_is_deterministic(self):
        a = uf.build_mission(self.genome, self.delta)
        b = uf.build_mission(self.genome, self.delta)
        self.assertEqual(a, b)
        self.assertEqual(uf.content_hash(a), uf.content_hash(b))

    def test_jev_has_closed_candidate_sets_and_no_mutation(self):
        mission = uf.build_mission(self.genome, self.delta)
        jev_tasks = [t for t in mission["tasks"] if t["owner"] == "jev"]
        self.assertTrue(jev_tasks)
        for task in jev_tasks:
            self.assertEqual("none", task["mutation_surface"])
            self.assertTrue(task["jev_decision"]["closed_set"])
            self.assertGreaterEqual(len(task["jev_decision"]["candidates"]), 2)

    def test_missing_recipe_creates_data_authoring_task_not_new_compiler(self):
        mission = uf.build_mission(self.genome, self.delta)
        task = next(t for t in mission["tasks"] if t["id"] == "world_recipe_ready")
        self.assertEqual("world_content_specialist", task["owner"])
        self.assertIn("World Compiler recipe", task["done_when"])
        self.assertIn("second compiler", task["done_when"])

    def test_fixture_can_never_satisfy_real_persistence_gate_by_itself(self):
        mission = uf.build_mission(self.genome, self.delta)
        self.assertTrue(mission["delta_non_authoritative_fixture"])
        task = next(t for t in mission["tasks"] if t["id"] == "persistence_roundtrip")
        self.assertIn("real_game_save_export_delta", task["evidence_required"])
        self.assertIn("no_fixture_used_for_acceptance", task["evidence_required"])

    def test_world_mismatch_rejected(self):
        wrong = dict(self.delta)
        wrong["world_id"] = "sea_above"
        errors = uf.validate_delta(wrong, self.genome["world_id"])
        self.assertTrue(any("does not match genome" in e for e in errors))

    def test_mission_dependencies_and_authority_validate(self):
        mission = uf.build_mission(self.genome, self.delta)
        self.assertEqual([], uf.validate_mission(mission))


if __name__ == "__main__":
    unittest.main()
