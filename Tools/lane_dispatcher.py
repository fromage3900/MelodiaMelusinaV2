#!/usr/bin/env python3
"""Lane Dispatcher — route queue items to the right model lane.

Gameplay queue authority (in order, first that exists + yields items):
  1. Docs/Handoffs/CORE_GAMEPLAY_CLOSEOUT_PLAN_2026-08-11.md
  2. Docs/Handoffs/CORE_SYSTEMS_HANDOFF_2026-08-10.md  (## 2. Execution order)
  3. _VERTICAL_SLICE_SCOPE.md
  4. NEXT_ACTIONS.md  (platform/website — last resort; not gameplay SSOT)

Classifies each item and assigns the best model lane via model_router policy.
Read-only: writes Saved/dispatch_report.md, never mutates the queue.

Usage:
  python lane_dispatcher.py plan                (dry-run assignment report)
  python lane_dispatcher.py plan --json
  python lane_dispatcher.py plan --queue <path>
"""

import argparse
import json
import os
import re
import sys

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from model_router import POLICY, BLOCKED  # noqa: E402

ROOT = os.path.abspath(os.path.join(os.path.dirname(os.path.abspath(__file__)), ".."))
REPORT = os.path.join(ROOT, "Saved", "dispatch_report.md")

QUEUE_CANDIDATES = [
    os.path.join(ROOT, "Docs", "Handoffs", "CORE_GAMEPLAY_CLOSEOUT_PLAN_2026-08-11.md"),
    os.path.join(ROOT, "Docs", "Handoffs", "CORE_SYSTEMS_HANDOFF_2026-08-10.md"),
    os.path.join(ROOT, "_VERTICAL_SLICE_SCOPE.md"),
    os.path.join(ROOT, "NEXT_ACTIONS.md"),
]

# Order matters for ties: prefer narrower classes listed first among equals via best_n.
CLASSIFIER = {
    "playtest": ["playtest", "real-input", "real input", "runtime gate", "campaign 1",
                 "campaign 2", "campaign 3", "campaign 4", "onkeydown", "slate-sendinput",
                 "rhythm→damage", "rhythm->damage", "save_load", "repeat_consume",
                 "package_launch", "result matrix", "round trip"],
    "cpp": ["melodiaintegration", "c++", "cpp", "uclass", "ufunction", "live coding",
            "closed-editor build", "postbattle", "rhythmcombat", "restorepartyafterbattle",
            "damage-scalar", "damage scalar"],
    "mcp": ["monolith", "mcp", "inject_nodes", "t3d inject", "blueprint_query",
            "material_query", "export_graph"],
    "daemon": ["daemon", "overnight", "continuous_loop", "unattended", "ollama"],
    "docs": ["handoff", "fold-in", "documentation", "session handoff", "readme"],
    "audit": ["audit", "check", "validate", "verify", "scan", "sweep", "probe",
              "bp_sweep", "fingerprint", "staleness", "preconditions", "hygiene"],
    "author": ["quill script", "author dialogue", "narrative beat", "write dialogue"],
    "orchestrator": ["plan", "priority", "roadmap", "strategy", "decision", "sequence"],
    "vision": ["capture", "render", "screenshot", "frame", "preview", "still", "video"],
    "review": ["benchmark", "research", "aaa", "compare", "portfolio", "criteria"],
    "code": ["blueprint", "compile", "inject", "t3d", "wiring",
             "material", "shader", "niagara", "pcg", "fix", "defect", "python", "pie"],
}
DEFAULT_CLASS = "code"


def classify(text):
    """Score title (before first newline) 3x heavier than body."""
    parts = text.split("\n", 1)
    title = parts[0].lower()
    body = parts[1].lower() if len(parts) > 1 else ""
    best, best_n = DEFAULT_CLASS, 0
    for cls, words in CLASSIFIER.items():
        n = 3 * sum(1 for w in words if w in title) + sum(1 for w in words if w in body)
        if n > best_n:
            best, best_n = cls, n
    return best


def assign(items):
    out = []
    for item in items:
        # title weighted separately from detail body
        blob = item["title"] + "\n" + " ".join(item["detail"])
        cls = classify(blob)
        if cls not in POLICY:
            cls = DEFAULT_CLASS
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


def _parse_steps(lines):
    """Parse '### Step N — title' from closeout plans."""
    items = []
    current = None
    for line in lines:
        m = re.match(r"^###\s+Step\s+(\d+)\s+[—\-–]\s+(.+)$", line.strip())
        if m:
            if current:
                items.append(current)
            title = re.sub(r"\*\*|~~|`", "", m.group(2)).strip()
            current = {"number": int(m.group(1)), "title": title, "detail": []}
            continue
        if current and line.startswith("## "):
            items.append(current)
            current = None
            continue
        if current and line.strip() and not line.startswith("```"):
            current["detail"].append(line.strip())
    if current:
        items.append(current)
    return items


def _parse_numbered(lines, start_patterns):
    """Parse '1. title' / '### 1. title' style items inside optional section headers."""
    items = []
    current = None
    in_section = not start_patterns
    for line in lines:
        if start_patterns and any(re.search(p, line, re.IGNORECASE) for p in start_patterns):
            in_section = True
            continue
        if in_section and start_patterns and re.match(r"^##\s+", line):
            if not any(re.search(p, line, re.IGNORECASE) for p in start_patterns):
                break
        m = re.match(r"^(?:#{1,4}\s+)?(?:\*\*)?(\d+)\.(?:\*\*)?\s+(.+)$", line.strip())
        if m and in_section:
            if current:
                items.append(current)
            title = re.sub(r"\*\*|~~|`", "", m.group(2)).strip()
            # skip DONE strikethrough-only leftovers that are pure status headers
            if title.upper().startswith("DONE"):
                continue
            current = {"number": int(m.group(1)), "title": title, "detail": []}
        elif current and line.strip() and not line.startswith("```"):
            current["detail"].append(line.strip())
    if current:
        items.append(current)
    return items


def parse_queue_file(path):
    with open(path, encoding="utf-8") as fh:
        lines = fh.readlines()
    name = os.path.basename(path).lower()
    if "closeout" in name:
        steps = _parse_steps(lines)
        if steps:
            return steps
    if "core_systems" in name:
        return _parse_numbered(lines, [r"Execution order"])
    if "vertical_slice" in name:
        return _parse_numbered(lines, [r"Open work", r"Remaining", r"^##\s+Queue"]) or \
               _parse_numbered(lines, [])
    items = _parse_numbered(lines, [r"^##\s+Queue"])
    if not items:
        items = _parse_numbered(lines, [])
    return items


def resolve_queue(explicit=None):
    if explicit:
        path = explicit if os.path.isabs(explicit) else os.path.join(ROOT, explicit)
        if not os.path.exists(path):
            sys.exit("queue not found: %s" % path)
        return path, parse_queue_file(path)
    for path in QUEUE_CANDIDATES:
        if not os.path.exists(path):
            continue
        items = parse_queue_file(path)
        if items:
            return path, items
    sys.exit("no queue file yielded items; tried:\n  " + "\n  ".join(QUEUE_CANDIDATES))


def plan(json_out, queue_path=None):
    path, items = resolve_queue(queue_path)
    assignments = assign(items)
    if json_out:
        print(json.dumps({"queue": path, "assignments": assignments}, indent=2))
        return 0
    os.makedirs(os.path.dirname(REPORT), exist_ok=True)
    with open(REPORT, "w", encoding="utf-8") as fh:
        fh.write("# Lane Dispatch Report\n\n")
        fh.write("Queue authority: `%s`\n\n" % path)
        fh.write("Vision: Quill → encounter → JRPG → typed result → resume once.\n")
        fh.write("Policy: `Docs/Production/MODEL_LANES_2026-08-12.md`\n\n")
        for a in assignments:
            mark = " BLOCKED: %s" % a["blocked"] if a["blocked"] else ""
            fh.write("- **Q%d** %s\n  - class=%s lane=%s (%s)%s\n" % (
                a["number"], a["title"], a["class"], a["model"], a["note"], mark))
    print("queue: %s" % path)
    print("report: %s" % REPORT)
    for a in assignments:
        mark = " BLOCKED" if a["blocked"] else ""
        print("Q%d [%s] %-42s %s%s" % (
            a["number"], a["class"], a["model"], a["title"][:60], mark))
    return 0


def main():
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("cmd", choices=["plan"])
    ap.add_argument("--json", action="store_true")
    ap.add_argument("--queue", help="override queue file path")
    args = ap.parse_args()
    if args.cmd == "plan":
        sys.exit(plan(args.json, args.queue))


if __name__ == "__main__":
    main()
