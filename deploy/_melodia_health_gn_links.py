"""GN socket-link audit - surface silently-dropped links. Run inside Blender 5.2.

`core.link_sockets` / `core.link_float_to_vector` never raise on a dropped link
(one bad link must not kill an 800-node tree), but a silently-dropped link is
the silent-no-op defect class: the tree still builds and the gate stays green
while a sub-effect is miswired. On 2026-09-18 there were 19 distinct
(tree, class) pairs across 18 builders, all invisible to `verify_addon.py`.

This script builds every registered builder and reports the recorder's findings
(`core.link_failures()`). It prefers the CHECKOUT on sys.path so it can audit
uncommitted work; set MELODIA_AUDIT_LIVE=1 to audit the synced live addon.

Usage:
  "C:/Program Files/Blender Foundation/Blender 5.2/blender.exe" \\
      --background --factory-startup --python deploy/_melodia_health_gn_links.py

Exit 0 only when no links were dropped.
"""
import collections
import os
import sys

REPO = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
DEPLOY = os.path.dirname(os.path.abspath(__file__))
APPDATA_ADDONS = os.path.join(os.environ["APPDATA"], "Blender Foundation",
                              "Blender", "5.2", "scripts", "addons")

if os.environ.get("MELODIA_AUDIT_LIVE") == "1":
    sys.path.insert(0, APPDATA_ADDONS)
else:
    sys.path.insert(0, DEPLOY)          # checkout wins -> audits uncommitted work
    sys.path.append(APPDATA_ADDONS)


def classify(message):
    if "End Location" in message and "Mesh Line" in message:
        return "End Location socket absent on Mesh Line (5.2)"
    if "cannot link component" in message:
        return "link_float_to_vector component link error"
    if "input not found" in message:
        return "target input socket not found (renamed/absent)"
    if "cannot link" in message:
        return "type mismatch (node vs socket)"
    if "are None" in message:
        return "None socket (socket absent)"
    return "other"


def main():
    import bpy  # noqa: F401
    from surreal_arch.melodia_gn import core

    print("loaded core from:", core.__file__)
    core.reset_link_failures()

    ids = sorted(core.GROUP_BUILDERS)
    built = 0
    build_errs = 0
    for key in ids:
        try:
            core.GROUP_BUILDERS[key]()
            built += 1
        except Exception:
            build_errs += 1

    failures = core.link_failures()
    per_tree = collections.OrderedDict(
        (name, collections.Counter(classify(m) for m in msgs))
        for name, msgs in sorted(failures.items())
    )
    class_totals = collections.Counter()
    for counter in per_tree.values():
        for cls, n in counter.items():
            class_totals[cls] += 1  # distinct trees per class

    print("")
    print("builders=%d built=%d build_errors=%d" % (len(ids), built, build_errs))
    print("trees_with_dropped_links=%d" % len(per_tree))
    print("")
    print("CLASS TOTALS (distinct trees):")
    for cls, n in class_totals.most_common():
        print("  %-4d %s" % (n, cls))
    print("")
    print("PER TREE:")
    for name, counter in per_tree.items():
        detail = ", ".join("%s=%d" % (c, n) for c, n in counter.most_common())
        print("  %-30s %s" % (name, detail))

    print("")
    print("link-audit: %d tree(s) with dropped links" % len(per_tree))
    return 1 if per_tree else 0


if __name__ == "__main__":
    raise SystemExit(main())
