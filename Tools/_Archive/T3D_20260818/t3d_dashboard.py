#!/usr/bin/env python3
"""
t3d_dashboard.py - text dashboards over the committed T3D material baseline.

WHY

Docs/T3D_Baseline/material_catalog.json is the only byte-exact record of the
material spine, and verify_baseline.py answers exactly one question about it:
"has anything drifted, yes or no." That is the right shape for a gate and the
wrong shape for understanding what you actually have.

This renders the same data as something you can read: where the complexity
lives, which assets dominate the spine, how the families compare, and -- with
--live -- what the editor currently disagrees with.

Offline by default. No editor needed unless you pass --live.

    python Tools/t3d_dashboard.py                    # overview
    python Tools/t3d_dashboard.py --view families    # one view
    python Tools/t3d_dashboard.py --live             # add live drift
    python Tools/t3d_dashboard.py --out Saved/Dashboards/t3d.txt

Views: overview | families | heaviest | complexity | tags | drift | all
"""
import argparse
import datetime
import importlib.util
import json
import os
import sys
from collections import Counter

HERE = os.path.dirname(os.path.abspath(__file__))
PROJECT = os.path.dirname(HERE)
BASE = os.path.join(PROJECT, "Docs", "T3D_Baseline")
CATALOG = os.path.join(BASE, "material_catalog.json")

WIDTH = 78


# ---------------------------------------------------------------- formatting

def rule(ch="-"):
    return ch * WIDTH


def header(title, sub=""):
    out = ["", "=" * WIDTH, f" {title}"]
    if sub:
        out.append(f" {sub}")
    out.append("=" * WIDTH)
    return out


def bar(value, peak, width=28, fill="#", empty="."):
    if peak <= 0:
        return empty * width
    n = int(round((value / peak) * width))
    return (fill * n).ljust(width, empty)


def human(n):
    for unit in ("B", "KB", "MB"):
        if abs(n) < 1024 or unit == "MB":
            return f"{n:,.0f}{unit}" if unit == "B" else f"{n/1.0:,.1f}{unit}"
        n /= 1024.0
    return f"{n}"


def kb(n):
    return f"{n/1024:,.1f} KB"


# ---------------------------------------------------------------- data

def load_catalog():
    with open(CATALOG, encoding="utf-8") as fh:
        return json.load(fh)


def all_assets(cat):
    out = []
    for fam_name, fam in cat["families"].items():
        for a in fam["assets"]:
            a = dict(a)
            a["_family"] = fam_name
            out.append(a)
    return out


def load_verifier():
    """verify_baseline.py owns export + canonical; reuse it rather than
    reimplementing the truncation guard and the reorder tolerance."""
    spec = importlib.util.spec_from_file_location(
        "vb", os.path.join(BASE, "verify_baseline.py"))
    mod = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(mod)
    return mod


# ---------------------------------------------------------------- views

def view_overview(cat, assets):
    lines = header("T3D BASELINE - OVERVIEW",
                   datetime.datetime.now().strftime("%Y-%m-%d %H:%M"))
    total_nodes = cat.get("total_nodes", sum(a["nodes"] for a in assets))
    total_bytes = cat.get("total_payload_bytes", sum(a["payload_bytes"] for a in assets))
    total_lines = sum(a.get("lines", 0) for a in assets)
    nodes = [a["nodes"] for a in assets] or [0]
    nodes_sorted = sorted(nodes)
    median = nodes_sorted[len(nodes_sorted) // 2]

    lines += [
        f"  assets tracked      {len(assets):>10,}",
        f"  families            {len(cat['families']):>10,}",
        f"  total nodes         {total_nodes:>10,}",
        f"  total payload       {kb(total_bytes):>10}",
        f"  total lines         {total_lines:>10,}",
        "",
        f"  nodes per asset     min {min(nodes):<5} median {median:<5} max {max(nodes):<5}",
        f"  mean payload        {kb(total_bytes/max(1,len(assets)))}",
        "",
        "  baseline is byte-exact; verify_baseline.py gates it, and tolerates",
        "  exporter object reordering (see canonical() there).",
    ]
    return lines


def view_families(cat, assets):
    lines = header("BY FAMILY")
    fams = sorted(cat["families"].items(), key=lambda kv: -kv[1]["nodes"])
    peak = max((f["nodes"] for _, f in fams), default=1)
    lines.append(f"  {'family':<24}{'assets':>7}{'nodes':>8}  {'share of nodes':<30}")
    lines.append("  " + rule()[:WIDTH - 2])
    for name, f in fams:
        lines.append(f"  {name[:23]:<24}{f['count']:>7}{f['nodes']:>8}  {bar(f['nodes'], peak)}")
    lines.append("")
    lines.append(f"  {'family':<24}{'payload':>12}")
    lines.append("  " + rule()[:WIDTH - 2])
    for name, f in fams:
        lines.append(f"  {name[:23]:<24}{kb(f['payload_bytes']):>12}")
    return lines


def view_heaviest(cat, assets, top=15):
    lines = header(f"HEAVIEST {top} ASSETS", "by node count - where the complexity actually lives")
    ranked = sorted(assets, key=lambda a: -a["nodes"])[:top]
    peak = ranked[0]["nodes"] if ranked else 1
    lines.append(f"  {'asset':<40}{'nodes':>6}{'payload':>11}  {'':<20}")
    lines.append("  " + rule()[:WIDTH - 2])
    for a in ranked:
        lines.append(f"  {a['name'][:39]:<40}{a['nodes']:>6}{kb(a['payload_bytes']):>11}  "
                     f"{bar(a['nodes'], peak, 18)}")
    tot = sum(a["nodes"] for a in assets)
    share = sum(a["nodes"] for a in ranked) / max(1, tot) * 100
    lines += ["", f"  these {len(ranked)} assets carry {share:.0f}% of all nodes in the spine"]
    return lines


def view_complexity(cat, assets):
    lines = header("COMPLEXITY DISTRIBUTION", "node-count buckets")
    buckets = [(0, 9, "trivial   1-9"), (10, 29, "small    10-29"), (30, 79, "medium   30-79"),
               (80, 199, "large    80-199"), (200, 10 ** 9, "huge      200+")]
    counts = []
    for lo, hi, label in buckets:
        members = [a for a in assets if lo <= a["nodes"] <= hi]
        counts.append((label, members))
    peak = max((len(m) for _, m in counts), default=1)
    for label, members in counts:
        lines.append(f"  {label:<16}{len(members):>4}  {bar(len(members), peak, 30)}")
    lines.append("")
    huge = [a for a in assets if a["nodes"] >= 200]
    if huge:
        lines.append("  assets at 200+ nodes (edit these with T3D injection, not by hand):")
        for a in sorted(huge, key=lambda x: -x["nodes"]):
            lines.append(f"    {a['name'][:44]:<46}{a['nodes']:>5} nodes")
    return lines


def view_tags(cat, assets):
    lines = header("TAGS")
    tags = Counter()
    for a in assets:
        for t in (a.get("tags") or []):
            tags[t] += 1
    if not tags:
        lines.append("  (no tags recorded in the catalog)")
        return lines
    peak = max(tags.values())
    for tag, n in tags.most_common():
        lines.append(f"  {tag[:28]:<30}{n:>4}  {bar(n, peak, 28)}")
    untagged = [a for a in assets if not a.get("tags")]
    if untagged:
        lines += ["", f"  untagged assets: {len(untagged)}"]
        for a in untagged[:10]:
            lines.append(f"    {a['name']}")
    return lines


def view_drift(cat, assets):
    """Live comparison. Requires the editor + Monolith on 9316."""
    lines = header("LIVE DRIFT", "re-exported from the editor and compared to baseline")
    try:
        vb = load_verifier()
    except Exception as e:
        lines.append(f"  cannot load verify_baseline.py: {e}")
        return lines

    clean = reordered = drifted = failed = 0
    detail = []
    for a in sorted(assets, key=lambda x: x["name"]):
        payload, err = vb.export(a["ue_path"])
        if err:
            failed += 1
            detail.append(("FAIL", a["name"], err[:40]))
            continue
        import hashlib
        sha = hashlib.sha256(payload.encode("utf-8")).hexdigest()
        if sha == a["sha256"]:
            clean += 1
            continue
        try:
            baseline_text = open(os.path.join(BASE, a["file"]), encoding="utf-8").read()
        except OSError as e:
            failed += 1
            detail.append(("FAIL", a["name"], f"baseline unreadable: {e}"))
            continue
        if vb.reordered_only(baseline_text, payload):
            reordered += 1
            detail.append(("REORDER", a["name"], "sibling order only - not a change"))
        else:
            drifted += 1
            live_nodes = payload.count("Begin Object Class=")
            detail.append(("DRIFT", a["name"],
                           f"{a['nodes']} -> {live_nodes} nodes, "
                           f"{a['payload_bytes']:,} -> {len(payload.encode()):,} B"))

    lines += [
        f"  clean {clean}   reordered {reordered}   drifted {drifted}   failed {failed}",
        "",
    ]
    if detail:
        for kind, name, note in detail:
            lines.append(f"  {kind:<8}{name[:34]:<36}{note}")
    else:
        lines.append("  everything matches the baseline byte for byte.")
    return lines


VIEWS = {
    "overview": view_overview,
    "families": view_families,
    "heaviest": view_heaviest,
    "complexity": view_complexity,
    "tags": view_tags,
}


def main():
    ap = argparse.ArgumentParser(description="Text dashboards over the T3D material baseline.")
    ap.add_argument("--view", default="all",
                    choices=list(VIEWS) + ["drift", "all"],
                    help="which view to render (default: all)")
    ap.add_argument("--live", action="store_true",
                    help="also re-export from the editor and report drift")
    ap.add_argument("--top", type=int, default=15, help="rows in the heaviest view")
    ap.add_argument("--out", help="also write the dashboard to this path")
    args = ap.parse_args()

    if not os.path.exists(CATALOG):
        print(f"ERROR no catalog at {CATALOG}")
        return 2

    cat = load_catalog()
    assets = all_assets(cat)

    lines = []
    if args.view == "all":
        for name, fn in VIEWS.items():
            lines += fn(cat, assets, args.top) if name == "heaviest" else fn(cat, assets)
    elif args.view == "drift":
        lines += view_drift(cat, assets)
    else:
        fn = VIEWS[args.view]
        lines += fn(cat, assets, args.top) if args.view == "heaviest" else fn(cat, assets)

    if args.live and args.view != "drift":
        lines += view_drift(cat, assets)

    lines.append("")
    text = "\n".join(lines)
    print(text)

    if args.out:
        path = args.out if os.path.isabs(args.out) else os.path.join(PROJECT, args.out)
        os.makedirs(os.path.dirname(path), exist_ok=True)
        with open(path, "w", encoding="utf-8", newline="\n") as fh:
            fh.write(text + "\n")
        print(f"written: {path}")
    return 0


if __name__ == "__main__":
    sys.exit(main())
