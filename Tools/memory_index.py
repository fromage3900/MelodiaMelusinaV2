#!/usr/bin/env python3
"""Project Memory — searchable index over docs, ledger, and playtest reports.

Builds a keyword/structural index (headers weighted, then full text) so any
lane can answer "where is X documented" without re-reading every file.

Usage:
  python memory_index.py build
  python memory_index.py search "rhythm highway damage" [--top 8]
"""

import argparse
import json
import os
import re
import sys

ROOT = os.path.abspath(os.path.join(os.path.dirname(os.path.abspath(__file__)), ".."))
INDEX_OUT = os.path.join(ROOT, "Saved", "memory_index.json")
SCAN_DIRS = [
    ("Docs", os.path.join(ROOT, "Docs")),
    ("Root", ROOT),
    ("Playtest", os.path.join(ROOT, "Saved", "Playtest")),
]
FILE_RE = re.compile(r"\.(md|json|txt)$", re.IGNORECASE)
HEADER_RE = re.compile(r"^(#{1,4})\s+(.+)$")
TOP_PRIORITY = 3


def should_skip(path):
    low = path.lower()
    return any(x in low for x in [
        "\\intermediate\\", "\\binaries\\", "\\deriveddata\\", "\\saved\\logs\\",
        "\\content\\", "\\plugins\\monolith\\intermediate", "\\compatibilitylabs\\",
        "\\_github_deploy\\", "\\my-site", "\\.git\\", "\\wix\\", "\\imports\\",
        "node_modules", "\\deploy\\", "\\melodia-design-system\\", "\\_staging\\",
    ])


def build():
    entries = []
    seen = set()
    for group, base in SCAN_DIRS:
        if not os.path.isdir(base):
            continue
        for dirpath, _dirs, files in os.walk(base):
            for fname in files:
                if not FILE_RE.search(fname) or fname.startswith("_"):
                    continue
                path = os.path.join(dirpath, fname)
                if should_skip(path) or path in seen:
                    continue
                seen.add(path)
                rel = os.path.relpath(path, ROOT).replace("\\", "/")
                try:
                    with open(path, "r", encoding="utf-8", errors="replace") as fh:
                        text = fh.read()
                except Exception:
                    continue
                headers = []
                snippets = []
                for lineno, line in enumerate(text.splitlines(), 1):
                    m = HEADER_RE.match(line.strip())
                    if m:
                        headers.append({"level": len(m.group(1)), "text": m.group(2).strip(), "line": lineno})
                body = text.lower()
                for kw in ["allowlist", "ledger", "gate", "rhythm", "highway", "wiring",
                           "mcp", "monolith", "quill", "save", "travel", "token"]:
                    for m in re.finditer(re.escape(kw), body):
                        start = max(0, m.start() - 60)
                        snippets.append(text[start:m.start() + 60].replace("\n", " ").strip())
                        break
                entries.append({
                    "path": rel,
                    "group": group,
                    "title": os.path.basename(path),
                    "headers": headers[:40],
                    "keywords": snippets[:6],
                    "size": len(text),
                })
    idx = {"built": time_str(), "count": len(entries), "entries": entries}
    os.makedirs(os.path.dirname(INDEX_OUT), exist_ok=True)
    with open(INDEX_OUT, "w", encoding="utf-8") as fh:
        json.dump(idx, fh, indent=1)
    print("indexed %d files -> %s" % (len(entries), INDEX_OUT))


def time_str():
    import time
    return time.strftime("%Y-%m-%d %H:%M:%S")


def search(query, top):
    if not os.path.exists(INDEX_OUT):
        sys.exit("index missing: run `python memory_index.py build` first")
    with open(INDEX_OUT, encoding="utf-8") as fh:
        idx = json.load(fh)
    terms = [t for t in re.split(r"\W+", query.lower()) if len(t) > 2]
    scored = []
    for e in idx["entries"]:
        score = 0
        hay = " ".join(h["text"].lower() for h in e["headers"]) + " " + e["path"].lower() + " " + e["title"].lower()
        full = json.dumps(e["keywords"]).lower()
        for t in terms:
            if t in e["path"]:
                score += 4
            if t in e["title"]:
                score += 3
            if t in hay:
                score += 2
            if t in full:
                score += 1
        if score:
            scored.append((score, e))
    scored.sort(key=lambda x: -x[0])
    print("query: %s (%d hits of %d files)" % (query, len(scored), idx["count"]))
    for score, e in scored[:top]:
        hdr = e["headers"][0]["text"] if e["headers"] else ""
        print("\n[%2d] %s  (%s)" % (score, e["path"], hdr))
        for kw in e["keywords"][:2]:
            print("      ...%s..." % kw[:90])
    return 0 if scored else 1


def main():
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    sub = ap.add_subparsers(dest="cmd", required=True)
    sub.add_parser("build")
    p_s = sub.add_parser("search")
    p_s.add_argument("query")
    p_s.add_argument("--top", type=int, default=8)
    args = ap.parse_args()
    if args.cmd == "build":
        build()
    else:
        sys.exit(search(args.query, args.top))


if __name__ == "__main__":
    main()
