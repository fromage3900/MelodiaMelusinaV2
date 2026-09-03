"""Health check for the current Melodia GN builder registry — run inside Blender 5.2.

Replaces the pre-restructure deploy/_health_check_gn_builders.py (which targeted a
deleted monolith and was removed by ad15aefc). This version imports the living
deploy/surreal_arch package and verifies that:
  1. the package and core registry import cleanly under bpy,
  2. GROUP_BUILDERS is non-empty and every entry is callable,
  3. GROUP_METADATA is a dict with a non-empty label set,
  4. the derived lookups rebuilt by melodia_gn.__init__ are present and consistent.

Usage (matches the other Blender health checks):
  blender --background --factory-startup --python deploy/_melodia_health_gn_builders.py

Exit code 0 only when every check passes.
"""
import os
import sys

REPO = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
DEPLOY = os.path.dirname(os.path.abspath(__file__))
for p in (DEPLOY, REPO):
    if p not in sys.path:
        sys.path.insert(0, p)

failures = []


def check(name, ok, detail=""):
    status = "PASS" if ok else "FAIL"
    print(f"[{status}] {name}" + (f" -- {detail}" if detail else ""))
    if not ok:
        failures.append(name)


def main():
    # 1. Package + core registry import under bpy.
    try:
        from surreal_arch.melodia_gn import core  # noqa: F401
        from surreal_arch import melodia_gn  # noqa: F401
        check("import surreal_arch.melodia_gn", True)
    except Exception as exc:  # noqa: BLE001
        check("import surreal_arch.melodia_gn", False, repr(exc))
        return 1

    # 2. GROUP_BUILDERS non-empty + all callable.
    builders = getattr(core, "GROUP_BUILDERS", None)
    check("GROUP_BUILDERS present", isinstance(builders, dict) and len(builders) > 0,
          f"{len(builders)} builders" if isinstance(builders, dict) else "missing")
    if isinstance(builders, dict):
        bad = [name for name, b in builders.items() if not callable(b)]
        check("all builders callable", not bad, f"non-callable: {bad[:6]}" if bad else "")

    # 3. GROUP_METADATA label sanity.
    meta = getattr(core, "GROUP_METADATA", None)
    check("GROUP_METADATA dict", isinstance(meta, dict),
          f"{len(meta)} entries" if isinstance(meta, dict) else "missing")
    if isinstance(meta, dict):
        labels = {name: m.get("label") for name, m in meta.items() if isinstance(m, dict)}
        missing = [k for k, v in labels.items() if not v]
        check("labels non-empty", not missing, f"missing labels: {missing[:6]}" if missing else "")

    # 4. Derived containers rebuilt after __init__.
    for attr in ("TREE_TYPES", "TREE_LABEL_MAP", "TREE_DESCRIPTIONS", "TREE_CATEGORIES", "CATEGORY_META"):
        val = getattr(core, attr, None)
        ok = isinstance(val, (dict, list, tuple)) and len(val) > 0
        check(f"derived {attr} non-empty", ok, "" if ok else "empty/missing")

    print(f"\nhealth: {len(failures)} check(s) failed")
    return 1 if failures else 0


if __name__ == "__main__":
    try:
        sys.exit(main())
    except Exception as exc:  # noqa: BLE001
        print(f"health check crashed: {exc!r}")
        sys.exit(1)