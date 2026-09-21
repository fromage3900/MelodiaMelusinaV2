"""Find every socket-name drift across all registered builders - Blender 5.2.

Blender 5.2.1 renamed/dropped sockets that 4.x-era builder code still names.
`link_float_to_vector` logs
    "'<name>' input not found on node '<node>'"
and returns, so the wiring silently no-ops (verified: GeometryNodeMeshLine in
5.2.1 has Count/Resolution/Start Location/Offset - no "End Location", and
`mode = "END_POINTS"` succeeds WITHOUT adding one).

Gate A proves the builders CONSTRUCT; it cannot prove they are WIRED. This
walks every registered builder, captures the Melodia GN logger's warnings, and
groups each unresolved socket by tree + message, so the fix list is evidence
rather than grep guesswork.

Usage:
  "C:/Program Files/Blender Foundation/Blender 5.2/blender.exe" \
      --background --factory-startup --python deploy/_melodia_scan_socket_drift.py
"""
import collections
import logging
import os
import sys

REPO = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
DEPLOY = os.path.dirname(os.path.abspath(__file__))
APPDATA_ADDONS = os.path.join(os.environ["APPDATA"], "Blender Foundation",
                              "Blender", "5.2", "scripts", "addons")
for p in (APPDATA_ADDONS, DEPLOY, REPO):
    if p not in sys.path:
        sys.path.insert(0, p)


class _Capture(logging.Handler):
    """Collect warnings emitted while a single builder is constructed."""

    def __init__(self):
        super().__init__(level=logging.WARNING)
        self.records = []

    def emit(self, record):
        try:
            self.records.append(record.getMessage())
        except Exception:
            pass


def main():
    try:
        from surreal_arch.melodia_gn.core import GROUP_BUILDERS
        from surreal_arch.melodia_gn.logging import log
    except Exception as exc:
        print(f"[FAIL] import: {exc!r}")
        return 1

    cap = _Capture()
    log.addHandler(cap)

    by_tree = collections.defaultdict(set)
    built = 0
    for builder_id in sorted(GROUP_BUILDERS):
        cap.records = []
        try:
            r = GROUP_BUILDERS[builder_id]()
            tree = r[0] if isinstance(r, (tuple, list)) else r
            built += 1
        except Exception:
            continue
        if tree is None:
            continue
        name = getattr(tree, "name", builder_id)
        for msg in cap.records:
            if "not found" in msg or "None" in msg:
                by_tree[name].add(msg.strip())

    log.removeHandler(cap)

    print(f"\n=== socket-drift scan: built={built}/{len(GROUP_BUILDERS)} "
          f"trees_with_warnings={len(by_tree)} ===")
    not_found = 0
    for name in sorted(by_tree):
        for msg in sorted(by_tree[name]):
            tag = "NOTFOUND" if "not found" in msg else "NULLLINK"
            if tag == "NOTFOUND":
                not_found += 1
            print(f"[{tag}] {name}: {msg}")
    print(f"=== totals: unresolved-socket={not_found} ===")
    return 0


if __name__ == "__main__":
    try:
        sys.exit(main())
    except Exception as exc:  # noqa: BLE001
        print(f"socket-drift scan crashed: {exc!r}")
        sys.exit(1)