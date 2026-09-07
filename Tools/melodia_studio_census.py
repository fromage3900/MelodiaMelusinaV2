"""Melodia Studio registry census + snapshot verifier.

Run headless:
  "C:/Program Files/Blender Foundation/Blender 5.2/blender.exe" --background \
      --factory-startup --python Tools/melodia_studio_census.py [-- --json OUT.json]

Reports (print lines are the gate; JSON is the snapshot artifact):
  - total registered builders vs Tools/registry_baseline.json (lost / new)
  - duplicate-name clusters (normalized v1/v2 + prefix folding)
  - category census + categories missing CATEGORY_META labels
  - baseline real-error builders (failures that are NOT input-dependent empties)

Consolidates the 2026-09-07 audit scripts (_census_dups, _census_panel,
_baseline_diff) into one durable tool. Saved/Audit is gitignored; this file
is the tracked authority. Snapshot policy: MELODIA_STUDIO_FINALIZE_SNAPSHOT_PLAN_2026-09-07.md.
"""
import collections
import json
import os
import re
import sys

REPO_ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
BASELINE = os.path.join(REPO_ROOT, "Tools", "registry_baseline.json")

# Live-install first, fall back to repo deploy tree (matches installer stamp path).
_ADDON_ROOTS = [
    os.path.expandvars(
        r"%APPDATA%\Blender Foundation\Blender\5.2\scripts\addons"),
    os.path.join(REPO_ROOT, "deploy"),
]
for root in _ADDON_ROOTS:
    if os.path.isdir(os.path.join(root, "surreal_arch")):
        sys.path.insert(0, root)
        break


def normalized_dup_clusters(ids):
    groups = collections.defaultdict(list)
    for k in ids:
        s = k.lower()
        s = re.sub(r"_v\d+$", "", s)
        s = re.sub(r"(mel|melodia|muse|mh|gb)_", "", s)
        groups[s].append(k)
    return {n: v for n, v in groups.items() if len(v) > 1}


def main():
    from surreal_arch.melodia_gn.core import (  # noqa: E402
        GROUP_BUILDERS, GROUP_METADATA, CATEGORY_META)

    ids = sorted(GROUP_BUILDERS.keys())
    print("CENSUS total builders:", len(ids))

    # duplicates
    dups = normalized_dup_clusters(ids)
    print("CENSUS dup-clusters:", len(dups))
    for n, v in sorted(dups.items()):
        print("  DUP", v)

    # categories
    cats = collections.Counter(
        GROUP_METADATA.get(k, {}).get("category", "<none>") for k in ids)
    no_label = sorted(c for c in cats
                      if c != "<none>" and not CATEGORY_META.get(c))
    no_cat = [k for k in ids if not GROUP_METADATA.get(k, {}).get("category")]
    print("CENSUS categories:", len(cats), " no-label:", no_label,
          " no-category builders:", len(no_cat))

    # baseline diff + real errors
    baseline = {}
    if os.path.exists(BASELINE):
        with open(BASELINE, encoding="utf-8-sig") as f:
            baseline = json.load(f)
    pkg = baseline.get("package", {})
    pkg_ids = set(pkg.keys())
    live_set = set(ids)
    lost, new = sorted(pkg_ids - live_set), sorted(live_set - pkg_ids)
    real_err = sorted(
        k for k, v in pkg.items()
        if not v.get("ok") and "empty geometry" not in v.get("error", ""))
    empties = sorted(
        k for k, v in pkg.items()
        if not v.get("ok") and "empty geometry" in v.get("error", ""))
    print("CENSUS baseline lost:", len(lost), lost[:10])
    print("CENSUS baseline new:", len(new), new[:10])
    print("CENSUS baseline real-errors:", len(real_err))
    for k in real_err:
        print("  ERR", k, "::", pkg[k].get("error", "")[:100])
    print("CENSUS baseline input-dependent empties:", len(empties))

    report = {
        "total": len(ids),
        "ids": ids,
        "dup_clusters": dups,
        "categories": dict(cats),
        "categories_no_label": no_label,
        "builders_no_category": no_cat,
        "baseline_lost": lost,
        "baseline_new": new,
        "baseline_real_errors": {k: pkg[k].get("error", "") for k in real_err},
        "baseline_empty_count": len(empties),
    }

    out = os.path.join(REPO_ROOT, "Saved", "Audit",
                       "melodia_studio_census.json")
    if "--json" in sys.argv:
        out = sys.argv[sys.argv.index("--json") + 1]
    os.makedirs(os.path.dirname(out), exist_ok=True)
    with open(out, "w", encoding="utf-8") as f:
        json.dump(report, f, indent=1)
    print("CENSUS json written:", out)

    # gate semantics: lost/new must be zero vs a fresh baseline; dup clusters
    # and real errors are reported for the F2/F2b ledger, not hard-failed here.
    ok = not lost and not new
    print("CENSUS RESULT:", "PASS" if ok else "DRIFT")
    return 0 if ok else 1


if __name__ == "__main__":
    sys.exit(main())
