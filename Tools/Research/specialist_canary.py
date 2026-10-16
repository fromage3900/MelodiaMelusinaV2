#!/usr/bin/env python3
"""Dependency-free, read-only specialist-canary packet validator/launcher.
Never installs models, runs third-party code, calls endpoints, or writes to repo.
"""
from __future__ import annotations

import argparse
import json
from pathlib import Path
import sys

ROOT = Path(__file__).resolve().parents[2]
PATH = ROOT / "specs" / "agent_canaries" / "specialist_models_20261015.json"
ACCESS = {"local_weights", "local_backend_possible", "free_source", "research_checkpoint"}
KINDS = {"model", "agent_framework", "mcp_bridge", "model_wrapper", "model_sdk"}
PRIORITY = {"P0", "P1", "P2", "P3"}
REQUIRED = {"houdini-vex-v11", "ue-expert-v2", "tdmcp"}
FIELDS = {"id", "kind", "priority", "access", "license", "url",
          "lane", "requirements", "proof", "status", "owner", "writer_allowed"}

def validate(data: dict) -> list[str]:
    errs: list[str] = []
    if data.get("schema") != "melodia.specialist_agent_canaries.v1":
        errs.append("unexpected schema")
    if data.get("default_mode") != "READ_ONLY":
        errs.append("default must be READ_ONLY")
    review = data.get("review_model", {})
    if review.get("official_api_model_id") != "deepseek-flash":
        errs.append("DeepSeek alias not pinned to official deepseek-flash")
    if review.get("is_free_api_guaranteed") is not False:
        errs.append("do not claim free API entitlement")
    rows = data.get("candidates", [])
    if not isinstance(rows, list) or not rows:
        return errs + ["nonempty candidate list required"]
    seen: set[str] = set()
    for i, row in enumerate(rows):
        if not isinstance(row, dict):
            errs.append(f"row {i} must be object")
            continue
        missing = FIELDS - set(row)
        if missing:
            errs.append(f"row {i} missing {sorted(missing)}")
            continue
        id_ = row["id"]
        if not isinstance(id_, str) or not id_.replace("-", "").isalnum():
            errs.append(f"row {i} invalid id")
        if id_ in seen:
            errs.append(f"row {i} duplicate id {id_}")
        seen.add(id_)
        if row["kind"] not in KINDS:
            errs.append(f"{id_} invalid kind")
        if row["access"] not in ACCESS:
            errs.append(f"{id_} invalid access")
        if row["priority"] not in PRIORITY:
            errs.append(f"{id_} invalid priority")
        if row["status"] != "NOT_RUN" or row["writer_allowed"] is not False:
            errs.append(f"{id_} must start NOT_RUN without write permissions")
        if not isinstance(row["url"], str) or not row["url"].startswith("https://"):
            errs.append(f"{id_} requires HTTPS upstream")
        for field in ("license", "lane", "requirements", "proof", "owner"):
            if not isinstance(row[field], str) or len(row[field].strip()) < 5:
                errs.append(f"{id_} missing useful {field}")
    if not REQUIRED.issubset(seen):
        errs.append(f"required canaries missing: {sorted(REQUIRED - seen)}")
    return errs

def self_test(data: dict) -> None:
    assert not validate(data), validate(data)
    broken = json.loads(json.dumps(data))
    broken["review_model"]["is_free_api_guaranteed"] = True
    assert any("free API" in x for x in validate(broken))
    broken = json.loads(json.dumps(data))
    broken["candidates"][0]["writer_allowed"] = True
    assert any("write permissions" in x for x in validate(broken))
    broken = json.loads(json.dumps(data))
    broken["candidates"].append(dict(broken["candidates"][0]))
    assert any("duplicate" in x for x in validate(broken))

def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    sub = parser.add_subparsers(dest="command", required=True)
    for cmd in ("validate", "list", "self-test"):
        sub.add_parser(cmd)
    p = sub.add_parser("packet")
    p.add_argument("candidate_id")
    args = parser.parse_args()
    try:
        data = json.loads(PATH.read_text(encoding="utf-8"))
    except (OSError, json.JSONDecodeError) as exc:
        print(f"HOLD: manifest not readable: {exc}", file=sys.stderr)
        return 2
    errors = validate(data)
    if errors:
        for e in errors:
            print(f"FAIL: {e}", file=sys.stderr)
        return 1
    if args.command == "validate":
        print(f"STATIC_PACKET_PASS: {len(data['candidates'])} NOT_RUN candidates; no model test implied")
    elif args.command == "self-test":
        self_test(data)
        print("SELF_TEST_PASS: mutation, duplicate and false-free-API gates reject bad fixtures")
    elif args.command == "list":
        for row in data["candidates"]:
            print(f"{row['priority']:2} {row['id']:24} {row['kind']:16} {row['status']}")
    else:
        row = next((r for r in data["candidates"] if r["id"] == args.candidate_id), None)
        if row is None:
            print("Unknown candidate", file=sys.stderr)
            return 2
        print(f"CANDIDATE: {row['id']} — {row['lane']}\nURL: {row['url']}"
              f"\nACCESS: {row['access']}\nLICENSE: {row['license']}"
              f"\nPREFLIGHT: {row['requirements']}\nEVIDENCE REQUIRED: {row['proof']}"
              "\nPERMISSION: READ ONLY; NOT_RUN; no model/API/edit authorization")
    return 0

if __name__ == "__main__":
    raise SystemExit(main())
