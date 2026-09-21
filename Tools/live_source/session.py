"""Session CLI — the runbook face of the live-source harness.

  python session.py check  <path> [--verb Idle]
  python session.py ledger [--source ROKOKO]

`check` classifies a capture file, runs its source preflight, records the
take in the session ledger at SOURCE_PREPARED (advancing past that requires
receipts — see ledger.py). `ledger` lists what the session has so far.
"""

from __future__ import annotations

import argparse
import json
import os
import sys

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from ledger import Ledger, Take  # noqa: E402
from preflight import classify, preflight  # noqa: E402


def cmd_check(args) -> int:
    path = os.path.abspath(args.path)
    if not os.path.exists(path):
        print(f"NOT FOUND: {path}")
        return 1
    result = preflight(path)
    kind = result["source"]
    print(json.dumps(result, indent=2, sort_keys=True))

    if kind not in ("ROKOKO", "CASCADEUR", "OBSBOT"):
        return 1

    verb = args.verb or os.path.splitext(os.path.basename(path))[0]
    verb = verb.split("_")[0] if kind == "OBSBOT" else verb
    ledger = Ledger()
    take_id = ledger.next_take_id(kind, verb)
    take = Take(take_id=take_id, source=kind, verb=verb, path=path,
                checks=result["checks"])
    if kind == "OBSBOT" and result["checks"].get("preset_1080p60") is False:
        take.blockers.append("preset_deviation: acting-reference take, "
                             "not a MOCAP-preset source")
    ledger.upsert(take)
    ledger.save()
    print(f"ledger: {take_id} recorded (SOURCE_PREPARED)")
    return 0


def cmd_ledger(args) -> int:
    ledger = Ledger()
    rows = sorted(ledger.takes.values(), key=lambda t: t.take_id)
    if args.source:
        rows = [t for t in rows if t.source == args.source]
    for t in rows:
        flag = "  BLOCKED:" + ",".join(t.blockers) if t.blockers else ""
        print(f"{t.take_id:34s} {t.evidence:16s} {len(t.receipts)} receipt(s){flag}")
    print(f"-- {len(rows)} take(s)")
    return 0


if __name__ == "__main__":
    ap = argparse.ArgumentParser(description=__doc__)
    sub = ap.add_subparsers(dest="cmd", required=True)
    p = sub.add_parser("check")
    p.add_argument("path")
    p.add_argument("--verb", default=None)
    p.set_defaults(fn=cmd_check)
    p = sub.add_parser("ledger")
    p.add_argument("--source", default=None)
    p.set_defaults(fn=cmd_ledger)
    args = ap.parse_args()
    sys.exit(args.fn(args))
