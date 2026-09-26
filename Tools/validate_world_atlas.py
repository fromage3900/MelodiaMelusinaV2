#!/usr/bin/env python3
"""Validate the Melodia World Atlas as inventory, provenance and anti-regression contract."""
from __future__ import annotations

import json
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
ATLAS = ROOT / "specs" / "world_atlas.v1.json"
OWNERSHIP = ROOT / "specs" / "source_control_ownership.v1.json"
RUNG_ORDER = ("SOURCE_PRESENT", "SOURCE_BUILT", "LIVE_PROVEN", "RESTART_PROVEN", "PACKAGED_PROVEN", "PORTFOLIO_APPROVED")
REQUIRED_SYSTEMS = {"world_atlas", "universe_foundry", "world_compiler", "houdini_foundry", "melodia_studio", "ue_pcg", "perforce", "git"}


def _covers(root: str, path: str) -> bool:
    root = root.replace("\\", "/").rstrip("/")
    path = path.replace("\\", "/").rstrip("/")
    return path == root or path.startswith(root + "/")


def _load(path: Path) -> dict:
    return json.loads(path.read_text(encoding="utf-8"))


def validate(atlas: dict, ownership: dict, check_files: bool = True) -> list[str]:
    errors: list[str] = []
    if atlas.get("schema") != "melodia.world_atlas/v1":
        errors.append("unexpected atlas schema")

    rungs = atlas.get("evidence_rungs")
    if rungs != list(RUNG_ORDER):
        errors.append("evidence_rungs must match the canonical evidence ladder")

    spine = atlas.get("production_spine")
    if not isinstance(spine, dict) or not REQUIRED_SYSTEMS.issubset(spine):
        errors.append("production_spine is missing canonical owners")

    worlds = atlas.get("worlds")
    if not isinstance(worlds, list) or len(worlds) < 6:
        errors.append("atlas must contain at least six seeded worlds")
        worlds = worlds if isinstance(worlds, list) else []

    bundle_names = {b.get("name") for b in ownership.get("level_bundles", []) if isinstance(b, dict)}
    ids: set[str] = set()
    route_orders: set[int] = set()
    for world in worlds:
        if not isinstance(world, dict):
            errors.append("world entry must be an object")
            continue
        wid = world.get("world_id")
        if not isinstance(wid, str) or not wid or wid in ids:
            errors.append(f"invalid or duplicate world_id: {wid!r}")
        ids.add(wid)
        rung = (world.get("evidence") or {}).get("rung")
        if rung not in RUNG_ORDER:
            errors.append(f"{wid}: invalid evidence rung {rung!r}")
        order = world.get("route_order")
        if order is not None:
            if not isinstance(order, int) or order in route_orders:
                errors.append(f"{wid}: invalid/duplicate route_order {order!r}")
            else:
                route_orders.add(order)
        ue = world.get("ue") or {}
        bundle = ue.get("source_control_bundle")
        if bundle is not None and bundle not in bundle_names:
            errors.append(f"{wid}: unknown source-control bundle {bundle!r}")
        repo_map = ue.get("repo_map_path")
        if ue.get("checked_in") and (not isinstance(repo_map, str) or not repo_map):
            errors.append(f"{wid}: checked_in world requires repo_map_path")
        elif check_files and ue.get("checked_in") and not (ROOT / repo_map).is_file():
            errors.append(f"{wid}: checked-in map missing: {repo_map}")
        for ref in world.get("evidence_refs", []):
            if check_files and isinstance(ref, str) and not ref.startswith("Saved/") and not (ROOT / ref).exists():
                errors.append(f"{wid}: evidence ref missing: {ref}")

    git_roots = (ownership.get("authorities") or {}).get("git", {}).get("roots", [])
    p4 = (ownership.get("authorities") or {}).get("perforce", {})
    p4_roots = p4.get("roots", [])
    p4_exclusions = p4.get("exclude_roots", [])
    protected = atlas.get("protected_git_entry_points")
    if not isinstance(protected, list) or not protected:
        errors.append("protected_git_entry_points must be non-empty")
        protected = []
    for path in protected:
        git_owned = any(_covers(root, path) for root in git_roots)
        p4_owned = any(_covers(root, path) for root in p4_roots) and not any(_covers(ex, path) for ex in p4_exclusions)
        if not git_owned or p4_owned:
            errors.append(f"protected Git entry point has wrong source-control owner: {path}")
        if check_files and not (ROOT / path).exists():
            errors.append(f"protected Git entry point missing: {path}")

    census = atlas.get("branch_census")
    if check_files and (not isinstance(census, str) or not (ROOT / census).is_file()):
        errors.append("branch census file is missing")
    return errors


def main() -> int:
    atlas = _load(ATLAS)
    ownership = _load(OWNERSHIP)
    errors = validate(atlas, ownership, check_files=True)
    if errors:
        print("FAIL: world atlas contract")
        for error in errors:
            print(f"  - {error}")
        return 1
    print(f"PASS: world atlas contract ({len(atlas['worlds'])} worlds, {len(atlas['protected_git_entry_points'])} protected Git entry points)")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
