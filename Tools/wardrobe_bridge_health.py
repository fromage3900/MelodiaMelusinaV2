#!/usr/bin/env python3
"""Read-only health report for the wardrobe control bridges.

The LiveLink adapter and Monolith MCP are TCP endpoints. OSC is UDP, so a
normal UDP socket cannot prove that a listener consumed a packet; by default
the report records UDP as configured/unverified. Pass --probe-udp only when an
explicit zero-payload probe is acceptable for the local bridge.
"""
from __future__ import annotations

import argparse
import json
import socket
from datetime import datetime, timezone
from pathlib import Path


def tcp_probe(host: str, port: int, timeout: float) -> dict:
    try:
        with socket.create_connection((host, port), timeout=timeout):
            return {"transport": "tcp", "host": host, "port": port, "status": "reachable"}
    except OSError as exc:
        return {"transport": "tcp", "host": host, "port": port, "status": "unreachable", "error": str(exc)}


def udp_probe(host: str, port: int, probe: bool) -> dict:
    result = {"transport": "udp", "host": host, "port": port}
    if not probe:
        result["status"] = "configured_unverified"
        return result
    try:
        with socket.socket(socket.AF_INET, socket.SOCK_DGRAM) as sock:
            sock.sendto(b"", (host, port))
        result["status"] = "sent_unverified"
    except OSError as exc:
        result["status"] = "unreachable"
        result["error"] = str(exc)
    return result


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--host", default="127.0.0.1")
    parser.add_argument("--livelink-port", type=int, default=9876)
    parser.add_argument("--monolith-port", type=int, default=9316)
    parser.add_argument("--osc-in-port", type=int, default=8000)
    parser.add_argument("--osc-out-port", type=int, default=9000)
    parser.add_argument("--timeout", type=float, default=1.0)
    parser.add_argument("--probe-udp", action="store_true")
    parser.add_argument("--report", default="Saved/T3D/wardrobe_bridge_health.json")
    args = parser.parse_args()

    checks = [
        tcp_probe(args.host, args.livelink_port, args.timeout),
        tcp_probe(args.host, args.monolith_port, args.timeout),
        udp_probe(args.host, args.osc_in_port, args.probe_udp),
        udp_probe(args.host, args.osc_out_port, args.probe_udp),
    ]
    tcp_ok = all(item["status"] == "reachable" for item in checks[:2])
    udp_ok = all(item["status"] != "unreachable" for item in checks[2:])
    payload = {
        "schema": "melodia.wardrobe_bridge_health.v1",
        "generated_at": datetime.now(timezone.utc).isoformat(),
        "ok": tcp_ok and udp_ok,
        "note": "UDP status is configured_unverified unless --probe-udp is supplied.",
        "checks": checks,
    }
    path = Path(args.report)
    if not path.is_absolute():
        path = Path(__file__).resolve().parents[1] / path
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(payload, indent=2) + "\n", encoding="utf-8")
    print(json.dumps(payload, indent=2))
    return 0 if payload["ok"] else 1


if __name__ == "__main__":
    raise SystemExit(main())
