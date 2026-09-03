"""One-shot Portfolio Materials AAA pipeline (full cycle).

Headless:
  python Content/Python/run_material_aaa_pipeline.py
"""
from __future__ import annotations

import json
import os
import subprocess
from datetime import datetime, timezone
from pathlib import Path

PROJECT_ROOT = Path(__file__).resolve().parents[2]
REPORT = PROJECT_ROOT / "Saved" / "Audit" / "portfolio_materials_aaa_pipeline.json"
UE_CMD = Path(r"C:\Program Files\Epic Games\UE_5.8\Engine\Binaries\Win64\UnrealEditor-Cmd.exe")
UPROJECT = PROJECT_ROOT / "BS_GodFile.uproject"


def run_pipeline() -> dict:
    import unreal

    steps: list[dict] = []
    os.environ["BS_MASTER_FORCE"] = "1"
    skip_masters = os.environ.get("BS_AAA_SKIP_MASTER_REBUILD", "").lower() in ("1", "true", "yes")

    def step(name: str, fn) -> None:
        try:
            result = fn()
            steps.append({"step": name, "ok": True, "result": result if isinstance(result, dict) else str(result)})
            unreal.log(f"[AAAPipeline] {name} OK")
        except Exception as exc:
            steps.append({"step": name, "ok": False, "error": str(exc)})
            unreal.log_error(f"[AAAPipeline] {name} failed: {exc}")

    step("cc0_catalog", lambda: __import__("portfolio_landscape_textures").main())
    step("portfolio_mpc", lambda: __import__("setup_portfolio_mpc").main())
    step("audio_mpc", lambda: __import__("setup_audio_outline").build_mpc())
    if not skip_masters:
        step("universal", lambda: (__import__("setup_master_universal").build(), __import__("organize_master_groups").main()))
        step("landscape", lambda: (__import__("setup_landscape_height_blend").build(force=True), __import__("organize_landscape_groups").organize()))
        step(
            "grand_water",
            lambda: (
                __import__("expand_grand_water").expand(),
                __import__("organize_water_groups").organize(),
                __import__("setup_master_water").build(),
            ),
        )
    else:
        steps.append({"step": "master_rebuild", "ok": True, "result": "skipped BS_AAA_SKIP_MASTER_REBUILD"})
    step("sync_instances", lambda: __import__("sync_all_material_instances").run_sync())
    step("sakura_instances", lambda: __import__("setup_sakura_instances").build())
    step("reparent_unified", lambda: __import__("reparent_unified_instances").main())
    step("archive_legacy", lambda: __import__("archive_unused_instances").main())
    step("dead_nodes_audit", lambda: __import__("audit_dead_material_nodes").main())
    step("master_review", lambda: __import__("review_portfolio_masters")._run_in_ue())
    step("zen_trimsheet_audit", lambda: __import__("audit_zen_trimsheet")._audit_in_ue())
    step("landscape_audit", lambda: __import__("audit_landscape_aaa")._audit_in_ue())
    step("water_audit", lambda: __import__("audit_grand_water_aaa")._audit_in_ue())
    step("template_showcase", lambda: __import__("setup_template_showcase").build_all())
    step("sakura_scene", lambda: __import__("setup_sakura_scene").main())
    step("audio_reactivity_audit", lambda: __import__("audit_audio_reactivity").main())

    zen = steps[-3]["result"] if len(steps) >= 3 and steps[-3].get("step") == "zen_trimsheet_audit" else {}
    land = steps[-2]["result"] if len(steps) >= 2 else {}
    water = steps[-1]["result"] if steps else {}
    for s in steps:
        if s["step"] == "zen_trimsheet_audit":
            zen = s.get("result") or {}
        elif s["step"] == "landscape_audit":
            land = s.get("result") or {}
        elif s["step"] == "water_audit":
            water = s.get("result") or {}

    master_ok = False
    master_path = PROJECT_ROOT / "Saved" / "Audit" / "master_review.json"
    if master_path.exists():
        mr = json.loads(master_path.read_text(encoding="utf-8"))
        summary = mr.get("summary") or mr
        master_ok = summary.get("clean", False) or (
            summary.get("banned_texture_count", summary.get("banned_texture_slots", 1)) == 0
            and summary.get("unwired_texture_count", summary.get("unwired_texture_slots", 1)) == 0
        )

    merged = {
        "timestamp": datetime.now(timezone.utc).isoformat(),
        "zen_trimsheet_all_ok": zen.get("all_ok"),
        "landscape_aaa_all_ok": land.get("all_ok"),
        "grand_water_aaa_all_ok": water.get("all_ok"),
        "master_review_ok": master_ok,
        "all_ok": bool(
            zen.get("all_ok") and land.get("all_ok") and water.get("all_ok") and master_ok
        ),
    }
    signoff = PROJECT_ROOT / "Saved" / "Audit" / "portfolio_materials_aaa.json"
    signoff.write_text(json.dumps(merged, indent=2), encoding="utf-8")

    report = {
        "timestamp": datetime.now(timezone.utc).isoformat(),
        "steps": steps,
        "portfolio_materials_aaa": merged,
        "all_ok": merged["all_ok"] and all(s["ok"] for s in steps),
    }
    REPORT.parent.mkdir(parents=True, exist_ok=True)
    REPORT.write_text(json.dumps(report, indent=2), encoding="utf-8")
    try:
        unreal.EditorLoadingAndSavingUtils.save_dirty_packages(True, True)
    except Exception:
        pass
    return report


def main() -> int:
    try:
        import unreal  # noqa: F401
        report = run_pipeline()
        print(f"AAA_PIPELINE all_ok={report['all_ok']} -> {REPORT}")
        return 0 if report["all_ok"] else 1
    except ImportError:
        if not UE_CMD.exists():
            print(f"ERROR: {UE_CMD}")
            return 1
        log = PROJECT_ROOT / "Saved" / "Logs" / "material_aaa_pipeline.log"
        cmd = [
            str(UE_CMD),
            str(UPROJECT),
            f"-ExecutePythonScript={(PROJECT_ROOT / 'Content/Python/run_material_aaa_pipeline.py').as_posix()}",
            "-stdout",
            "-unattended",
            "-nullrhi",
            "-DisablePlugins=Monolith",
            f"-log={log}",
        ]
        return subprocess.run(cmd, cwd=str(PROJECT_ROOT)).returncode


if __name__ == "__main__":
    raise SystemExit(main())
