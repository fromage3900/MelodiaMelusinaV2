#!/usr/bin/env python3
"""Lane Dispatcher — route queue items to the right model lane.

Reads NEXT_ACTIONS.md (queue authority), classifies each item, and assigns the
best model lane via model_router policy. Read-only by default: writes an
assignment report to Saved/dispatch_report.md, never mutates the queue.

Usage:
  python lane_dispatcher.py plan                (dry-run assignment report)
  python lane_dispatcher.py plan --json
"""

import argparse
import json
import os
import re
import sys

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from model_router import POLICY, BLOCKED  # noqa: E402

ROOT = os.path.abspath(os.path.join(os.path.dirname(os.path.abspath(__file__)), ".."))
QUEUE = os.path.join(ROOT, "NEXT_ACTIONS.md")
REPORT = os.path.join(ROOT, "Saved", "dispatch_report.md")

CLASSIFIER = {
    "code": ["blueprint", "c++", "compile", "inject", "t3d", "build", "wiring", "gate",
             "material", "shader", "niagara", "pcg", "fix", "defect"],
    "audit": ["audit", "check", "validate", "verify", "scan", "review", "sweep", "probe"],
    "author": ["dialogue", "quill", "narrative", "write", "author", "script", "voice", "content"],
    "orchestrator": ["plan", "priority", "roadmap", "strategy", "decision", "track", "sequence"],
    "vision": ["capture", "render", "screenshot", "frame", "preview", "still", "video"],
    "review": ["benchmark", "research", "aaa", "compare", "portfolio", "criteria"],
}
DEFAULT_CLASS = "code"


def classify(text):
    low = text.lower()
    best, best_n = DEFAULT_CLASS, 0
    for cls, words in CLASSIFIER.items():
        n = sum(1 for w in words if w in low)
        if n > best_n:
            best, best_n = cls, n
    return best


def parse_queue():
    if not os.path.exists(QUEUE):
        sys.exit("queue not found: %s" % QUEUE)
    items = []
    with open(QUEUE, encoding="utf-8") as fh:
        lines = fh.readlines()
    current = None
    in_queue = False
    for line in lines:
        if re.match(r"^##\s+Queue", line, re.IGNORECASE):
            in_queue = True
            continue
        if in_queue and line.startswith("## ") and not re.match(r"^##\s+Queue", line, re.IGNORECASE):
            break
        m = re.match(r"^(\d+)\.\s+(.+)$", line.strip())
        if m and in_queue:
            if current:
                items.append(current)
            current = {"number": int(m.group(1)), "title": m.group(2).strip(), "detail": []}
        elif current and line.strip() and not line.startswith("```"):
            current["detail"].append(line.strip())
    if current:
        items.append(current)
    return items


def assign(items):
    out = []
    for item in items:
        cls = classify(item["title"] + " " + " ".join(item["detail"]))
        lane = POLICY[cls][0]
        blocked = BLOCKED.get(lane[0])
        out.append({
            "number": item["number"],
            "title": item["title"],
            "class": cls,
            "model": lane[0],
            "endpoint": lane[1],
            "note": lane[2],
            "blocked": blocked,
        })
    return out


def plan(json_out):
    items = parse_queue()
    assignments = assign(items)
    if json_out:
        print(json.dumps(assignments, indent=2))
        return 0
    os.makedirs(os.path.dirname(REPORT), exist_ok=True)
    with open(REPORT, "w", encoding="utf-8") as fh:
        fh.write("# Lane Dispatch Report\n\n")
        for a in assignments:
            mark = " BLOCKED: %s" % a["blocked"] if a["blocked"] else ""
            fh.write("- **Q%d** %s\n  - class=%s lane=%s (%s)%s\n" % (
                a["number"], a["title"], a["class"], a["model"], a["note"], mark))
    print("report: %s" % REPORT)
    for a in assignments:
        mark = " BLOCKED" if a["blocked"] else ""
        print("Q%d [%s] %-42s %s%s" % (a["number"], a["class"], a["model"], a["title"][:60], mark))
    return 0


def main():
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("cmd", choices=["plan"])
    ap.add_argument("--json", action="store_true")
    args = ap.parse_args()
    if args.cmd == "plan":
        sys.exit(plan(args.json))


if __name__ == "__main__":
    main()
