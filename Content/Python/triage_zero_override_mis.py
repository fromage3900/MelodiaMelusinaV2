"""triage_zero_override_mis.py

Read-only triage of zero-override material instances from mi_runtime_audit.json.
For each zero-override MI: resolve its twin (`_Default` vs bare), count registry
referencers, and bucket it:

  - deletable_pair  : zero referencers AND a zero-override twin with the same
                      parent exists (one of the pair is redundant).
  - referenced      : has registry referencers (meshes/BP/etc use this shell as
                      the material slot) - must stay, owner tuning target.
  - unique_shell    : zero referencers, no twin - a pure default shell that is
                      the only instance of its master; harmless, keep unless
                      owner wants the master referenced directly.
  - check           : anything unexpected for manual review.

Never deletes. Writes Saved/Audit/zero_override_triage_<date>.json.

Run via Monolith editor_query run_python (read-only registry queries).
"""
from __future__ import annotations

import json
import os
from datetime import date

import unreal  # noqa: F401

AUDIT_PATH = os.path.normpath(os.path.join(
    os.path.dirname(os.path.abspath(__file__)),
    "..", "..", "Saved", "Audit", "mi_runtime_audit.json"))
OUT_PATH = os.path.normpath(os.path.join(
    os.path.dirname(os.path.abspath(__file__)),
    "..", "..", "Saved", "Audit",
    "zero_override_triage_%s.json" % date.today().isoformat()))


def _referencers(package_name: str) -> list:
    try:
        ar = unreal.AssetRegistryHelpers.get_asset_registry()
        opts = unreal.AssetRegistryDependencyOptions(
            include_soft_package_references=True,
            include_hard_package_references=True,
            include_searchable_names=False,
            include_soft_management_references=True,
            include_hard_management_references=True)
        return sorted(str(r) for r in (ar.get_referencers(package_name, opts) or []))
    except Exception as exc:
        return ["<ERR:%s>" % exc]


def _pkg(path: str) -> str:
    return path.split(".", 1)[0]


def _last(path: str) -> str:
    return _pkg(path).rsplit("/", 1)[-1]


def main():
    with open(AUDIT_PATH, encoding="utf-8") as fh:
        audit = json.load(fh)
    rows = audit["results"]
    zero = [r for r in rows if r.get("zero_override")]
    by_name = {_last(r["path"]): r for r in zero}
    buckets = {"deletable_pair": [], "referenced": [], "unique_shell": [], "check": []}
    seen_pairs = set()
    for r in zero:
        name = _last(r["path"])
        parent = _pkg(r["parent"])
        refs = _referencers(_pkg(r["path"]))
        twin_name = None
        if name.endswith("_Default"):
            twin_name = name[: -len("_Default")]
        else:
            twin_name = name + "_Default"
        twin = by_name.get(twin_name)
        twin_same_parent = bool(twin) and _pkg(twin["parent"]) == parent
        rec = {
            "path": r["path"],
            "parent": parent,
            "twin": twin_name if twin else None,
            "twin_same_parent": twin_same_parent,
            "referencers": refs,
        }
        if refs and not (isinstance(refs, list) and len(refs) == 1 and str(refs[0]).startswith("<ERR")):
            buckets["referenced"].append(rec)
        elif twin and twin_same_parent and not refs:
            pair_key = tuple(sorted([name, twin_name]))
            if pair_key not in seen_pairs:
                seen_pairs.add(pair_key)
                rec["pair"] = sorted([name, twin_name])
                buckets["deletable_pair"].append(rec)
            else:
                buckets["check"].append(dict(rec, reason="pair_second_encounter"))
        elif not refs:
            buckets["unique_shell"].append(rec)
        else:
            buckets["check"].append(dict(rec, reason="unexpected"))

    payload = {
        "generated": date.today().isoformat(),
        "note": "Zero-override MI triage (read-only, referencer-proof). No deletions.",
        "counts": {k: len(v) for k, v in buckets.items()},
        "buckets": buckets,
    }
    os.makedirs(os.path.dirname(OUT_PATH), exist_ok=True)
    with open(OUT_PATH, "w", encoding="utf-8") as fh:
        json.dump(payload, fh, indent=2)
    print("WROTE|%s" % OUT_PATH)
    print("COUNTS|%s" % json.dumps(payload["counts"]))
    for key in ("deletable_pair", "referenced", "unique_shell", "check"):
        items = buckets[key]
        print("BUCKET|%s|%d" % (key, len(items)))
        for item in items[:8]:
            print("  - %s | refs=%d | twin=%s" % (
                _last(item["path"]), len(item.get("referencers") or []),
                item.get("twin") or "-"))


if __name__ == "__main__":
    main()
