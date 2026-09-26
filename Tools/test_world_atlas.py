#!/usr/bin/env python3
"""Offline contract tests for the Melodia World Atlas."""
from __future__ import annotations

import copy
import importlib.util
import json
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
spec = importlib.util.spec_from_file_location("world_atlas", ROOT / "Tools" / "validate_world_atlas.py")
module = importlib.util.module_from_spec(spec)
assert spec and spec.loader
spec.loader.exec_module(module)
ATLAS = json.loads((ROOT / "specs" / "world_atlas.v1.json").read_text(encoding="utf-8"))
OWNERSHIP = json.loads((ROOT / "specs" / "source_control_ownership.v1.json").read_text(encoding="utf-8"))


def check(condition, message):
    if not condition:
        raise AssertionError(message)


def main():
    check(not module.validate(ATLAS, OWNERSHIP, check_files=True), "checked-in atlas must validate")
    check(len(ATLAS["worlds"]) >= 6, "seed world set must remain present")
    check("Content/Python/pcg/resonance_ecology_processor.py" in ATLAS["protected_git_entry_points"], "Resonance Ecology must be protected")

    dup = copy.deepcopy(ATLAS)
    dup["worlds"][1]["world_id"] = dup["worlds"][0]["world_id"]
    check(any("duplicate world_id" in e for e in module.validate(dup, OWNERSHIP, check_files=False)), "duplicate world ids must fail")

    bad_rung = copy.deepcopy(ATLAS)
    bad_rung["worlds"][0]["evidence"]["rung"] = "VIBES_PROVEN"
    check(any("invalid evidence rung" in e for e in module.validate(bad_rung, OWNERSHIP, check_files=False)), "invented evidence rung must fail")

    bad_bundle = copy.deepcopy(ATLAS)
    bad_bundle["worlds"][0]["ue"]["source_control_bundle"] = "L_Imaginary"
    check(any("unknown source-control bundle" in e for e in module.validate(bad_bundle, OWNERSHIP, check_files=False)), "unknown bundle must fail")

    bad_route = copy.deepcopy(ATLAS)
    bad_route["worlds"][1]["route_order"] = bad_route["worlds"][0]["route_order"]
    check(any("route_order" in e for e in module.validate(bad_route, OWNERSHIP, check_files=False)), "duplicate route order must fail")

    wrong_owner = copy.deepcopy(OWNERSHIP)
    wrong_owner["authorities"]["perforce"]["exclude_roots"] = []
    check(any("wrong source-control owner" in e for e in module.validate(ATLAS, wrong_owner, check_files=False)), "PCG source must never become effective Perforce content")

    print("PASS: world atlas contract tests (8 assertions)")


if __name__ == "__main__":
    main()
