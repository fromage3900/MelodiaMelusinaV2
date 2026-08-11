"""Run remaining portfolio material integration inside the interactive editor.

Output Log:
  py "G:/EnvironmentPortfolio/BS_GodFile/Content/Python/run_editor_integration.py"

Steps: compositing integration, phase A safe, dead-node audit, storybook PP rebuild.
"""
from __future__ import annotations

import json
import sys
from datetime import datetime, timezone
from pathlib import Path

PROJECT_ROOT = Path(__file__).resolve().parents[2]
REPORT = PROJECT_ROOT / "Saved" / "Audit" / "editor_integration.json"


def _step(name: str, fn) -> dict:
    import unreal

    unreal.log(f"[EditorIntegration] >>> {name}")
    try:
        rc = fn()
        ok = rc in (None, 0)
        return {"step": name, "ok": ok, "returncode": rc}
    except Exception as exc:
        unreal.log_error(f"[EditorIntegration] FAILED {name}: {exc}")
        return {"step": name, "ok": False, "error": str(exc)}


def main() -> int:
    import unreal

    unreal.log("=== EDITOR MATERIAL INTEGRATION ===")
    steps: list[dict] = []

    steps.append(_step("compositing textures", lambda: __import__("integrate_compositing_textures").main()))
    steps.append(_step("phase A safe", lambda: __import__("run_phase_a_safe").main()))
    steps.append(_step("dead node audit", lambda: __import__("audit_dead_material_nodes").main()))
    steps.append(
        _step(
            "storybook outline rebuild",
            lambda: __import__("setup_storybook_outline").build_all(force=True),
        )
    )

    report = {
        "timestamp": datetime.now(timezone.utc).isoformat(),
        "steps": steps,
        "all_ok": all(s.get("ok") for s in steps),
    }
    REPORT.parent.mkdir(parents=True, exist_ok=True)
    REPORT.write_text(json.dumps(report, indent=2), encoding="utf-8")
    unreal.log(f"[EditorIntegration] report -> {REPORT}")
    try:
        unreal.EditorLoadingAndSavingUtils.save_dirty_packages(True, True)
    except Exception:
        pass
    return 0 if report["all_ok"] else 1


if __name__ == "__main__":
    raise SystemExit(main())
