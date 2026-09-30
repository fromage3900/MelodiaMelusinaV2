#!/usr/bin/env python3
from __future__ import annotations

import copy
import importlib.util
import json
import shutil
import sys
import unittest
from pathlib import Path

ROOT = Path(__file__).resolve().parents[3]
MODULE_PATH = ROOT / "Tools" / "Houdini" / "foundry" / "houdini_foundry.py"

spec = importlib.util.spec_from_file_location("houdini_foundry", MODULE_PATH)
assert spec and spec.loader
hf = importlib.util.module_from_spec(spec)
sys.modules["houdini_foundry"] = hf
spec.loader.exec_module(hf)

RECIPE_DIR = ROOT / "recipes" / "houdini_foundry"
TILE_RECIPE = RECIPE_DIR / "field_atlas_sea_above_test_tile.v1.json"
CATHEDRAL_RECIPE = RECIPE_DIR / "crystal_cathedral_6bay_harmony.v1.json"


class HoudiniFoundryTests(unittest.TestCase):
    def test_committed_recipes_and_requests_validate(self):
        for path in sorted(RECIPE_DIR.glob("*.json")):
            data = hf.load_json(path)
            errors = hf.validate_request(data) if data["schema"] == hf.REQUEST_SCHEMA else hf.validate_recipe(data)
            self.assertEqual([], errors, path.name)

    def test_plan_is_deterministic(self):
        recipe = hf.load_json(TILE_RECIPE)
        self.assertEqual(hf.build_plan(recipe), hf.build_plan(copy.deepcopy(recipe)))

    def test_tile_seeds_are_stable_and_distinct(self):
        recipe = hf.load_json(TILE_RECIPE)
        recipe["region"].pop("only_tiles")
        tiles = hf.plan_tiles(recipe)
        self.assertEqual(4, len(tiles))
        self.assertEqual(len(tiles), len({t["seed"] for t in tiles}))
        self.assertEqual(len(tiles), len({t["tile_id"] for t in tiles}))
        for t in tiles:
            self.assertTrue(0 <= t["seed"] < hf.SEED_MOD)
            self.assertEqual(t["seed"], hf.derive_seed(recipe["seed"], recipe["recipe_id"], "tile", t["ix"], t["iy"]))

    def test_test_first_restricts_to_one_tile(self):
        self.assertEqual(["tx-001_ty+000"], [t["tile_id"] for t in hf.plan_tiles(hf.load_json(TILE_RECIPE))])

    def test_rejects_mpc_writer(self):
        recipe = hf.load_json(CATHEDRAL_RECIPE)
        recipe["authority"]["writes_mpc"] = True
        self.assertTrue(any("writes_mpc" in e for e in hf.validate_recipe(recipe)))

    def test_rejects_houdini_as_runtime_owner(self):
        recipe = hf.load_json(CATHEDRAL_RECIPE)
        recipe["authority"]["runtime_owner"] = "houdini"
        self.assertTrue(any("runtime_owner" in e for e in hf.validate_recipe(recipe)))

    def test_rejects_workstation_paths(self):
        recipe = hf.load_json(CATHEDRAL_RECIPE)
        recipe["params"]["hython"] = "C:\\Program Files\\Side Effects Software\\Houdini 22.0.368\\bin\\hython.exe"
        self.assertTrue(any("workstation path" in e for e in hf.validate_recipe(recipe)))

    def test_rejects_unknown_channel(self):
        recipe = hf.load_json(TILE_RECIPE)
        recipe["params"]["channels"].append("vibes")
        self.assertTrue(any("vibes" in e for e in hf.validate_recipe(recipe)))

    def test_existing_channel_names_match_point_row(self):
        columns = {c["name"] for c in hf.load_json(ROOT / "specs" / "schemas" / "world_compiler_point_row.v1.json")["columns"]}
        for channel in hf.load_json(hf.CHANNELS_PATH)["channels"]:
            existing = channel["existing_name"] or ""
            if existing.startswith("points.csv "):
                self.assertIn(existing.split()[1], columns, channel["name"])

    def test_verify_detects_tampered_output(self):
        work = ROOT / "Saved" / "HoudiniFoundry" / "_unittest"
        work.mkdir(parents=True, exist_ok=True)
        try:
            out = work / "field.bin"
            out.write_bytes(b"melodia")
            rel = out.relative_to(ROOT).as_posix()
            recipe = hf.load_json(CATHEDRAL_RECIPE)
            manifest = {
                "schema": hf.MANIFEST_SCHEMA,
                "recipe_id": recipe["recipe_id"],
                "recipe_sha256": hf.content_hash(recipe),
                "seed": recipe["seed"],
                "houdini_version": "22.0.368",
                "tool": {"path": "Tools/Houdini/foundry/houdini_foundry.py", "git_sha": "test"},
                "status": "PASS",
                "outputs": [{"path": rel, "sha256": hf.sha256_file(out), "bytes": 7}],
            }
            mpath = work / "bake_manifest.json"
            mpath.write_text(json.dumps(manifest), encoding="utf-8")
            self.assertEqual([], hf.verify_manifest(mpath))
            out.write_bytes(b"melodiA")
            self.assertTrue(any("sha256 mismatch" in e for e in hf.verify_manifest(mpath)))
        finally:
            shutil.rmtree(work, ignore_errors=True)


    def test_verify_rejects_stale_recipe_hash(self):
        work = ROOT / "Saved" / "HoudiniFoundry" / "_unittest_hash"
        work.mkdir(parents=True, exist_ok=True)
        try:
            out = work / "field.bin"
            out.write_bytes(b"melodia")
            rel = out.relative_to(ROOT).as_posix()
            recipe = hf.load_json(CATHEDRAL_RECIPE)
            manifest = {
                "schema": hf.MANIFEST_SCHEMA,
                "recipe_id": recipe["recipe_id"],
                "recipe_sha256": "0" * 64,
                "seed": recipe["seed"],
                "houdini_version": "22.0.368",
                "tool": {"path": "Tools/Houdini/foundry/houdini_foundry.py", "git_sha": "test"},
                "status": "PASS",
                "outputs": [{"path": rel, "sha256": hf.sha256_file(out), "bytes": 7}],
            }
            mpath = work / "bake_manifest.json"
            mpath.write_text(json.dumps(manifest), encoding="utf-8")
            self.assertTrue(any("recipe_sha256 mismatch" in e for e in hf.verify_manifest(mpath)))
        finally:
            shutil.rmtree(work, ignore_errors=True)


if __name__ == "__main__":
    unittest.main()
