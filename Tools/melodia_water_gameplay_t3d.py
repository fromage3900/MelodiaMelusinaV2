#!/usr/bin/env python3
"""Safe Monolith protocol for the integrated PCG/water Blueprint lane.

This tool is deliberately parameterized by a live Blueprint path. It exports
and fingerprints before mutation, refuses a duplicate generated operation,
validates/injects one T3D cluster atomically, compiles, asserts the expected
operation, saves, and emits a rollback/provenance report. The existing
parameterized patterns remain the source of T3D payloads; this module owns the
water-specific target manifest and safety gates.
"""
from __future__ import annotations

import argparse
import hashlib
import json
import sys
from dataclasses import asdict, dataclass
from pathlib import Path
from typing import Any
from urllib.request import Request, urlopen


MONOLITH_URL = "http://127.0.0.1:9316/mcp"
PATTERN_ROOT = Path(__file__).resolve().parents[1] / "Docs" / "T3D_Patterns"


@dataclass(frozen=True)
class WaterT3DTarget:
    target_id: str
    purpose: str
    operation: str
    expected_marker: str
    required_nodes: tuple[str, ...]


TARGETS = (
    WaterT3DTarget("hero_host_begin_play", "bind generated hero host to water gameplay", "RebindToHost", "RebindToHost", ("RebindToHost",)),
    WaterT3DTarget("hero_host_end_play", "unregister world bindings on host teardown", "UnregisterWaterBindings", "UnregisterWaterBindings", ("UnregisterWaterBindings",)),
    WaterT3DTarget("note_judged_resonance", "route judged notes into typed resonance", "HandleNoteJudged", "HandleNoteJudged", ("HandleNoteJudged",)),
    WaterT3DTarget("pattern_completed_puzzle", "complete optional water puzzle", "HandlePatternCompleted", "HandlePatternCompleted", ("HandlePatternCompleted",)),
    WaterT3DTarget("controller_state_fanout", "fan state through existing interaction bus", "HandleWaterStateChanged", "HandleWaterStateChanged", ("HandleWaterStateChanged",)),
    WaterT3DTarget("device_interaction", "wire valve/pump/gate interaction", "InteractWithDevice", "InteractWithDevice", ("InteractWithDevice",)),
    WaterT3DTarget("platform_route_activation", "activate a route from water state", "SetRouteOpen", "SetRouteOpen", ("SetRouteOpen",)),
    WaterT3DTarget("platform_state_update", "publish logical platform state", "UpdatePlatformState", "UpdatePlatformState", ("UpdatePlatformState",)),
    WaterT3DTarget("buoyancy_debug_telemetry", "inspect authoritative sample/impact state", "HasAuthoritativeWaterSample", "HasAuthoritativeWaterSample", ("HasAuthoritativeWaterSample",)),
    WaterT3DTarget("save_load_rebind", "restore logical state after load", "RestoreSaveState", "RestoreSaveState", ("RestoreSaveState",)),
    WaterT3DTarget("runtime_diagnostic", "one-shot proof diagnostics", "GetPlatformMotionState", "GetPlatformMotionState", ("GetPlatformMotionState",)),
    WaterT3DTarget("sea_above_pulse_cycle", "drive 12-20s biological pulse cycle for false ocean and membrane", "SetScalarParameterValue", "SetScalarParameterValue", ("SetScalarParameterValue",)),
    WaterT3DTarget("sea_above_anomaly_burst", "trigger upward anomaly particle burst on pulse peak", "GreaterEqual_DoubleDouble", "GreaterEqual_DoubleDouble", ("GreaterEqual_DoubleDouble",)),
    WaterT3DTarget("sea_above_membrane_sheen", "modulate membrane Fresnel and sheen based on pulse intensity", "Lerp", "Lerp", ("Lerp",)),
)


def target_manifest() -> list[dict[str, Any]]:
    return [asdict(target) for target in TARGETS]


def get_target(target_id: str) -> WaterT3DTarget:
    for target in TARGETS:
        if target.target_id == target_id:
            return target
    raise KeyError(f"unknown water T3D target: {target_id}")


def _call(action: str, params: dict[str, Any], timeout: int = 180) -> dict[str, Any]:
    body = json.dumps({
        "jsonrpc": "2.0",
        "id": 1,
        "method": "tools/call",
        "params": {"name": "blueprint_query", "arguments": {"action": action, **params}},
    }).encode()
    request = Request(MONOLITH_URL, data=body, headers={"Content-Type": "application/json"})
    with urlopen(request, timeout=timeout) as response:
        envelope = json.loads(response.read().decode())
    text = envelope.get("result", {}).get("content", [{}])[0].get("text", "")
    return json.loads(text) if text else {}


def _graph_params(asset_path: str, graph_name: str | None) -> dict[str, Any]:
    params: dict[str, Any] = {"asset_path": asset_path}
    if graph_name:
        params["graph_name"] = graph_name
    return params


def _contains_marker(exported: Any, marker: str) -> bool:
    if isinstance(exported, dict):
        return any(_contains_marker(key, marker) or _contains_marker(value, marker) for key, value in exported.items())
    if isinstance(exported, list):
        return any(_contains_marker(value, marker) for value in exported)
    return marker.lower() in str(exported).lower()


def run_target(
    target_id: str,
    asset_path: str,
    pattern_name: str,
    placeholders: dict[str, str],
    graph_name: str | None = None,
    apply: bool = False,
) -> dict[str, Any]:
    target = get_target(target_id)
    graph_params = _graph_params(asset_path, graph_name)
    exported_before = _call("export_graph", graph_params)
    before = _call("get_graph_fingerprint", graph_params)
    if _contains_marker(exported_before, target.expected_marker):
        raise RuntimeError(f"refusing duplicate generated cluster: {target_id} already contains {target.expected_marker}")

    pattern_path = PATTERN_ROOT / "patterns" / (pattern_name if pattern_name.endswith(".t3d") else f"{pattern_name}.t3d")
    payload = pattern_path.read_text(encoding="utf-8")
    payload_hash = hashlib.sha256(payload.encode("utf-8")).hexdigest()
    validation = _call("validate_nodes_t3d", {
        "asset_path": asset_path,
        "t3d": payload,
        "placeholders": placeholders,
        **({"graph_name": graph_name} if graph_name else {}),
    })
    if not validation.get("valid") or not validation.get("engine_accepts", True):
        raise RuntimeError(f"T3D validation failed for {target_id}: {validation}")

    report: dict[str, Any] = {
        "target": asdict(target),
        "asset_path": asset_path,
        "graph_name": graph_name or "EventGraph",
        "pattern": str(pattern_path),
        "payload_sha256": payload_hash,
        "before_fingerprint": before.get("fingerprint"),
        "rollback_export": exported_before,
        "validation": validation,
        "applied": False,
    }
    if not apply:
        report["mode"] = "dry_run"
        return report

    injected = _call("inject_nodes_t3d", {
        "asset_path": asset_path,
        "t3d": payload,
        "placeholders": placeholders,
        "compile": True,
        **({"graph_name": graph_name} if graph_name else {}),
    })
    if not injected.get("injected") or not injected.get("compiled_clean", False):
        raise RuntimeError(f"injection/compile failed for {target_id}: {injected}")
    after_export = _call("export_graph", graph_params)
    after = _call("get_graph_fingerprint", graph_params)
    if not _contains_marker(after_export, target.expected_marker):
        raise RuntimeError(f"post-injection assertion failed for {target_id}: marker not found")
    saved = _call("save_asset", {"asset_path": asset_path})
    report.update({
        "injected": injected,
        "after_fingerprint": after.get("fingerprint"),
        "post_export": after_export,
        "saved": saved,
        "applied": True,
    })
    return report


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--list", action="store_true")
    parser.add_argument("--target")
    parser.add_argument("--asset")
    parser.add_argument("--pattern", default="guarded_call")
    parser.add_argument("--graph", default=None)
    parser.add_argument("--set", action="append", default=[])
    parser.add_argument("--go", action="store_true", help="mutate only after all live-path checks pass")
    args = parser.parse_args()

    if args.list:
        print(json.dumps(target_manifest(), indent=2))
        return 0
    if not args.target or not args.asset:
        parser.error("--target and --asset are required unless --list is used")
    placeholders = {}
    for item in args.set:
        if "=" not in item:
            parser.error(f"--set expects key=value: {item}")
        key, value = item.split("=", 1)
        placeholders[key] = value
    report = run_target(args.target, args.asset, args.pattern, placeholders, args.graph, args.go)
    print(json.dumps(report, indent=2, default=str))
    return 0


if __name__ == "__main__":
    sys.exit(main())

