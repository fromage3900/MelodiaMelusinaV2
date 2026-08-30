#!/usr/bin/env python3
"""Branch health census for BS_GodFile.

Read-only. Answers: which branches carry unique work vs main, which are
local-only (unbacked), which are fully merged, and (optionally) the
binary-conflict surface between main and each divergent line.

Usage:
  python Tools/branch_health.py                    # census table + JSON
  python Tools/branch_health.py --conflicts        # + conflict surface for divergent lines
  python Tools/branch_health.py --json out.json    # write JSON report
  python Tools/branch_health.py --md out.md        # write markdown report

Excluded by design: refs/heads/legacy* and remotes/legacy-melodia/* (the old
V1 repo shares no lineage with V2 and is never a merge candidate).
"""
import argparse
import datetime
import json
import subprocess
import sys

EXCLUDE_PATTERNS = ("legacy-melodia",)


def git(*args):
    """Run git, return stripped stdout or None on failure."""
    try:
        r = subprocess.run(
            ["git"] + list(args),
            capture_output=True, text=True, timeout=120, encoding="utf-8", errors="replace",
        )
        if r.returncode != 0:
            return None
        return r.stdout.strip()
    except (subprocess.TimeoutExpired, OSError):
        return None


def count(spec):
    out = git("rev-list", "--count", spec)
    return int(out) if out is not None else -1


def is_ancestor(a, b):
    """True if commit a is an ancestor of commit b (a fully merged into b)."""
    r = subprocess.run(
        ["git", "merge-base", "--is-ancestor", a, b],
        capture_output=True, text=True,
    )
    return r.returncode == 0


def merge_base(a, b):
    return git("merge-base", a, b)


def commit_date(ref):
    out = git("log", "-1", "--format=%ci", ref)
    return out or "unknown"


def both_modified(base, ours, theirs):
    """Files changed on BOTH sides since merge-base = git conflict candidates."""
    try:
        ours_files = set(git("diff", "--name-only", base, ours).splitlines())
        theirs_files = set(git("diff", "--name-only", base, theirs).splitlines())
    except AttributeError:
        return None, None
    both = sorted(ours_files & theirs_files)
    binaries = [f for f in both if f.endswith((".uasset", ".umap"))]
    return both, binaries


def collect_refs():
    refs = []
    out = git("for-each-ref", "--format=%(refname:short)", "refs/heads")
    if out:
        refs += [r for r in out.splitlines() if r not in ("main",)]
    out = git("for-each-ref", "--format=%(refname:short)", "refs/remotes/origin")
    if out:
        refs += [r for r in out.splitlines()
                 if r not in ("origin/main", "origin/HEAD")]
    return [r for r in refs if not any(p in r for p in EXCLUDE_PATTERNS)]


def tracking_info(branch):
    """Return (upstream, is_local_only) for a local branch."""
    out = git("for-each-ref", "--format=%(upstream:short) %(upstream:track)",
              "refs/heads/" + branch)
    if out is None:
        return (None, True)
    parts = out.split()
    upstream = parts[0] if parts and parts[0] != "" else None
    gone = "gone" in out
    if upstream is None or gone:
        return (upstream, True)
    return (upstream, False)


def main():
    ap = argparse.ArgumentParser(description=__doc__)
    ap.add_argument("--conflicts", action="store_true",
                    help="estimate both-side-modified conflict surface for divergent lines")
    ap.add_argument("--json", dest="json_out", help="write JSON report here")
    ap.add_argument("--md", dest="md_out", help="write markdown report here")
    args = ap.parse_args()

    generated = datetime.datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    rows = []
    for ref in collect_refs():
        ahead = count("main..%s" % ref)
        behind = count("%s..main" % ref)
        if ahead < 0:
            rows.append({"branch": ref, "status": "UNREADABLE"})
            continue
        local_only = False
        upstream = None
        if not ref.startswith("origin/"):
            upstream, local_only = tracking_info(ref)
        status = ("merged" if ahead == 0
                  else "divergent" if behind > 0
                  else "ahead-only")
        rows.append({
            "branch": ref, "ahead": ahead, "behind": behind,
            "status": status, "upstream": upstream, "local_only": local_only,
        })

    divergent = [r for r in rows if r.get("status") in ("divergent", "ahead-only")]
    for r in divergent:
        base = merge_base("main", r["branch"])
        if base:
            r["merge_base"] = base
            r["merge_base_date"] = commit_date(base)
        if args.conflicts and base and r["ahead"] <= 250:
            both, binaries = both_modified(base, "main", r["branch"])
            if both is not None:
                r["conflict_files_both_sides"] = len(both)
                r["conflict_binary"] = len(binaries)

    unique_work = [r for r in rows if r.get("ahead", 0) > 0]
    unbacked = [r for r in rows
                if r.get("local_only") and r.get("ahead", 0) > 0]

    report = {
        "generated": generated,
        "total_refs": len(rows),
        "unique_work_branches": len(unique_work),
        "local_only_with_unique_work": [r["branch"] for r in unbacked],
        "merged_fully": sorted(r["branch"] for r in rows if r.get("status") == "merged"),
        "branches": rows,
    }

    # --- console table ---
    print("BS_GodFile branch health — %s" % generated)
    print("unique-work branches: %d | local-only unbacked: %s" % (
        len(unique_work), report["local_only_with_unique_work"] or "none"))
    print()
    hdr = "%-58s %6s %7s %10s %6s" % ("branch", "ahead", "behind", "status", "local")
    print(hdr)
    print("-" * len(hdr))
    for r in sorted(rows, key=lambda x: -x.get("ahead", 0)):
        if r.get("status") == "UNREADABLE":
            print("%-58s  UNREADABLE" % r["branch"])
            continue
        print("%-58s %6d %7d %10s %6s" % (
            r["branch"][:58], r["ahead"], r["behind"],
            r["status"], "YES" if r.get("local_only") else ""))
    if args.conflicts:
        print()
        print("Conflict surface (both-side-modified since merge-base):")
        for r in divergent:
            if "conflict_files_both_sides" in r:
                print("  %-58s both=%d (binary=%d, base=%s)"
                      % (r["branch"][:58], r["conflict_files_both_sides"],
                         r["conflict_binary"], r.get("merge_base_date", "?")[:10]))

    # --- file outputs ---
    if args.json_out:
        with open(args.json_out, "w", encoding="utf-8") as f:
            json.dump(report, f, indent=2)
        print("\nJSON -> %s" % args.json_out)
    if args.md_out:
        with open(args.md_out, "w", encoding="utf-8") as f:
            f.write("# Branch health census — %s\n\n" % generated)
            f.write("Local-only branches with unique work (no remote backup): %s\n\n"
                    % (report["local_only_with_unique_work"] or "none"))
            f.write("| Branch | Ahead | Behind | Status | Conflict both/binary |\n|---|---|---|---|---|\n")
            for r in sorted(rows, key=lambda x: -x.get("ahead", 0)):
                if r.get("status") == "UNREADABLE":
                    continue
                cb = ""
                if "conflict_files_both_sides" in r:
                    cb = "%d / %d" % (r["conflict_files_both_sides"], r["conflict_binary"])
                f.write("| `%s` | %d | %d | %s | %s |\n" % (
                    r["branch"], r["ahead"], r["behind"], r["status"], cb))
        print("MD   -> %s" % args.md_out)
    return 0


if __name__ == "__main__":
    sys.exit(main())
