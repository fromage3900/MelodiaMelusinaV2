"""Create curated starter MI_Show_* instances for M_Master_Toon_Universal.

The 141+ MI_Universal_* presets in universal_instance_presets.py are DEPRECATED.
Use starter_instances.py + apply_starter_instances.py instead.

Run after setup_master_universal.py:
  py "G:/EnvironmentPortfolio/BS_GodFile/Content/Python/apply_starter_instances.py"

This module remains as a thin alias for older docs/scripts.
"""
from __future__ import annotations

import json
from pathlib import Path

REPORT = Path(__file__).resolve().parents[2] / "Saved" / "Audit" / "universal_instances.json"

# Deprecated — kept so imports don't break; do not extend.
CORE_INSTANCES: list[dict] = []
EXTRA_INSTANCES: list[dict] = []
INSTANCES: list[dict] = []


def build_instances() -> list[dict]:
    import apply_starter_instances as apply_mod

    return apply_mod.build_starter_instances()


def main() -> int:
    try:
        import unreal  # noqa: F401
    except ImportError:
        print("Requires Unreal Editor Python")
        print("Preferred: py Content/Python/apply_starter_instances.py")
        return 1

    results = build_instances()
    report = {
        "deprecated": True,
        "use_instead": "apply_starter_instances.py",
        "instances": results,
        "count": len(results),
    }
    REPORT.parent.mkdir(parents=True, exist_ok=True)
    REPORT.write_text(json.dumps(report, indent=2), encoding="utf-8")
    print(json.dumps(report, indent=2))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
