"""Offline checks for the request schema and the committed T3D fixtures."""

from __future__ import annotations

import json
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
SCHEMA_PATH = ROOT / "specs" / "schemas" / "t3d_mutation_request.v1.json"
REQUESTS = [
    ROOT / "specs" / "t3d" / "live_probe_print.json",
    ROOT / "specs" / "wardrobe" / "wardrobe_t3d_request.example.json",
    ROOT / "specs" / "t3d" / "sea_above_pulse_driver.json",
    ROOT / "specs" / "t3d" / "sea_above_anomaly_burst.json",
]


def load(path: Path) -> dict:
    value = json.loads(path.read_text(encoding="utf-8"))
    assert isinstance(value, dict), path
    return value


def main() -> int:
    schema = load(SCHEMA_PATH)
    properties = schema.get("properties", {})
    for field in ("$schema", "nodes", "connections", "pin_defaults", "expected_postconditions", "t3d", "verification"):
        assert field in properties, f"schema missing property: {field}"
    assert "required" in properties["expected_postconditions"]
    assert "expected_delta" in properties["expected_postconditions"]["properties"]
    assert "reexport_after_save" in properties["verification"]["properties"]

    for path in REQUESTS:
        request = load(path)
        assert request.get("schema") == "melodia.t3d_mutation_request.v1", path
        assert isinstance(request.get("operations"), list) and request["operations"], path
        verification = request.get("verification")
        assert isinstance(verification, dict), path
        assert verification.get("compile_zero_errors") is True, path
        assert verification.get("assert_graph_match") is True, path
        assert verification.get("reexport_after_save") is True, path

    live = load(REQUESTS[0])
    post = live.get("expected_postconditions")
    assert isinstance(post, dict)
    assert post["required_nodes"] == ["Probe"]
    assert post["forbidden_nodes"] == []
    assert post["required_connections"] == []
    assert post["expected_delta"]["new_nodes"] == ["Probe"]
    assert post["expected_delta"]["new_connections"] == []
    assert post["compile_error_count"] == 0
    assert post["reexport_after_save"] is True

    print(f"validated T3D request schema and {len(REQUESTS)} committed fixtures")
    print("validated explicit required/forbidden nodes, connections, compile count, and saved re-export fields")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
