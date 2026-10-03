"""Offline validator for the canonical Melusina WaterHair physics probe."""
from __future__ import annotations

import argparse
import json
from pathlib import Path
from typing import Any

PROJECT = Path(__file__).resolve().parents[1]
DEFAULT_CONTRACT = PROJECT / "specs/anim_presets/melusina_hair_physics.json"


def read_json(path: Path) -> dict[str, Any]:
    value = json.loads(path.read_text(encoding="utf-8-sig"))
    if not isinstance(value, dict):
        raise ValueError(f"{path}: expected JSON object")
    return value


def validate_probe(probe: dict[str, Any], contract: dict[str, Any], tolerance: float = 1e-4) -> dict[str, Any]:
    errors: list[str] = []
    if probe.get("asset") != contract["asset"]:
        errors.append("asset does not match canonical WaterHair AnimBP")
    if probe.get("mesh") != contract["mesh"]:
        errors.append("mesh does not match canonical WaterHair mesh")
    if probe.get("node_count") != 1:
        errors.append("exactly one KawaiiPhysics node is required")
    nodes = probe.get("nodes") or []
    node = nodes[0] if len(nodes) == 1 else {}
    if node.get("name") != contract["node"]:
        errors.append("KawaiiPhysics node identity changed")
    if node.get("root_bone") != contract["root_bone"]:
        errors.append(f"KawaiiPhysics root must remain {contract['root_bone']}")
    actual = dict(node.get("physics_settings") or {})
    for key in ("gravity", "enable_wind", "wind_scale", "dummy_bone_length", "bone_subdivision_count", "need_warm_up", "warm_up_frames"):
        actual[key] = node.get(key)
    for key, wanted in contract["settings"].items():
        got = actual.get(key)
        if isinstance(wanted, float):
            try:
                matches = abs(float(got) - wanted) <= tolerance
            except (TypeError, ValueError):
                matches = False
        else:
            matches = got == wanted
        if not matches:
            errors.append(f"{key}: expected {wanted!r}, got {got!r}")
    return {"schema": "melodia.melusina_hair_physics_gate.v1", "ok": not errors, "errors": errors, "asset": probe.get("asset"), "profile": contract["schema"]}


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("probe", type=Path)
    parser.add_argument("--contract", type=Path, default=DEFAULT_CONTRACT)
    parser.add_argument("--output", type=Path)
    args = parser.parse_args(argv)
    report = validate_probe(read_json(args.probe.resolve()), read_json(args.contract.resolve()))
    if args.output:
        args.output.resolve().write_text(json.dumps(report, indent=2) + "\n", encoding="utf-8")
    print(json.dumps(report, indent=2))
    return 0 if report["ok"] else 1


if __name__ == "__main__":
    raise SystemExit(main())
