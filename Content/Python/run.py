"""One CLI entry for the ~10 common project operations.

    py Content/Python/run.py <task> [args...]

Replaces remembering 259 script filenames. In-editor tasks require the editor
(Monolith or py console); disk tasks run anywhere. Extend TASKS as ops mature.
"""
from __future__ import annotations

import sys

TASKS = {
    # name: (module, callable, needs_editor, help)
    "pillars-build": ("setup_wp_pillar_levels", "build_all", True, "Scaffold/refresh all 4 WP pillar levels (kicks async PCG)"),
    "pillars-verify": ("setup_wp_pillar_levels", "verify", True, "Count ISM + WP per pillar (separate call after build)"),
    "audit-materials": ("audit_material_library", "main", True, "Full material library audit -> Saved/Audit"),
    "manifest-materials": ("material_family_manifest_full", "main", True, "Material family manifest for the website package"),
    "portfolio-package": ("portfolio_aggregator", "main", False, "Aggregate portfolio_package.json"),
    "website-handoff": ("package_to_website_handoff", "main", False, "Package -> my-site-clean handoff"),
    "catalog": ("build_asset_catalog", "main", True, "Searchable asset catalog (json + html)"),
}


def main(argv: list[str]) -> int:
    if not argv or argv[0] in ("-h", "--help", "help"):
        print("tasks:")
        for k, (_, _, ed, h) in TASKS.items():
            print(f"  {k:22s} {'[editor] ' if ed else '         '}{h}")
        return 0
    name = argv[0]
    if name not in TASKS:
        print(f"unknown task: {name} (run with --help)")
        return 1
    mod_name, fn_name, needs_editor, _ = TASKS[name]
    if needs_editor:
        try:
            import unreal  # noqa: F401
        except ImportError:
            print(f"task '{name}' must run inside the editor (Monolith run_python or py console)")
            return 1
    import importlib

    mod = importlib.import_module(mod_name)
    importlib.reload(mod)
    fn = getattr(mod, fn_name, None)
    if fn is None:
        print(f"{mod_name}.{fn_name} not found — update TASKS")
        return 1
    if name == "pillars-verify":
        results = {k: fn(k) for k in ("SakuraDream", "SpaceCathedral", "BaroqueGrotto", "CosmicOrrery")}
        print({k: v.get("passed") for k, v in results.items()})
        return 0 if all(v.get("passed") for v in results.values()) else 1
    out = fn()
    print(out if out is not None else "done")
    return 0


if __name__ == "__main__":
    raise SystemExit(main(sys.argv[1:]))
