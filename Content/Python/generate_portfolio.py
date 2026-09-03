"""Single entry point for the portfolio export pipeline.

Run from project root:
  python Content/Python/generate_portfolio.py

In editor:
  py Content/Python/generate_portfolio.py

Steps (sequential, failure-reporting):
  1. ensure_portfolio_layout()
  2. scene_metadata_exporter.write_scene_metadata()
  3. capture_material_previews.write_previews_manifest()
  4. capture_portfolio_renders.run_all_captures() (viewport + Monolith captures)
  5. compile_render_plates.write_renders_manifest() (idempotent disk compiler)
  6. portfolio_aggregator.ensure_package_written() -> Saved/Portfolio/portfolio_package.json
  7. package_to_website_handoff.write_handoff() -> _github_deploy/generated/*_config.json

UE steps (metadata + renders) require RHI; shell launch omits -nullrhi.
"""
from __future__ import annotations

import json
import subprocess
import time
import os
from datetime import datetime, timezone
from pathlib import Path

PROJECT_ROOT = Path(__file__).resolve().parents[2]
REPORT = PROJECT_ROOT / "Saved" / "Audit" / "generate_portfolio.json"
PACKAGE_PATH = PROJECT_ROOT / "Saved" / "Portfolio" / "portfolio_package.json"
LEVEL = "/Game/EnvSandbox/Environments/Sakura/L_SakuraPath"


def _resolve_unreal_command() -> Path:
    configured = os.environ.get("MELODIA_UNREAL_ROOT")
    if not configured:
        config_path = PROJECT_ROOT / "Config" / "paths.json"
        try:
            config = json.loads(config_path.read_text(encoding="utf-8"))
        except (OSError, json.JSONDecodeError):
            config = {}
        paths = config.get("paths") if isinstance(config, dict) else {}
        defaults = config.get("defaults") if isinstance(config, dict) else {}
        configured = paths.get("unreal") or defaults.get("unreal")
    root = Path(configured or r"C:\Program Files\Epic Games\UE_5.8")
    if not root.is_absolute():
        root = (PROJECT_ROOT.parent / root).resolve()
    return root / "Engine" / "Binaries" / "Win64" / "UnrealEditor-Cmd.exe"


UE_CMD = _resolve_unreal_command()
UPROJECT = PROJECT_ROOT / "BS_GodFile.uproject"


def _log(message: str) -> None:
    line = f"[GeneratePortfolio] {message}"
    try:
        import unreal

        unreal.log(line)
    except ImportError:
        print(line)


def _load_portfolio_level() -> None:
    import unreal

    les = unreal.get_editor_subsystem(unreal.LevelEditorSubsystem)
    asset_path = f"{LEVEL}.L_SakuraPath"
    if les and unreal.EditorAssetLibrary.does_asset_exist(asset_path):
        _log(f"loading level {LEVEL}")
        les.load_level(LEVEL)
        time.sleep(3)
    else:
        _log(f"level not found, using current editor level ({asset_path})")


def run_portfolio_pipeline() -> dict:
    """Execute all portfolio steps and preserve a complete failure report."""
    import portfolio_aggregator as aggregator
    import compile_render_plates as plates
    import portfolio_output_layout as layout
    import capture_portfolio_renders as capture
    import capture_material_previews as previews
    import scene_metadata_exporter as metadata
    import export_genome_axis as genome_axis
    import audit_pcg_heatmap as pcg_heatmap
    import stats_exporter as stats
    import package_to_website_handoff as website_handoff

    time.sleep(15)
    steps: list[dict] = []

    def step(name: str, fn) -> None:
        _log(f"START {name}")
        try:
            result = fn()
            payload = result if isinstance(result, dict) else {"result": str(result)}
            steps.append({"step": name, "ok": True, **payload})
            _log(f"OK {name}")
        except Exception as exc:
            steps.append({"step": name, "ok": False, "error": str(exc)})
            _log(f"FAIL {name}: {exc}")

    step(
        "ensure_portfolio_layout",
        lambda: {
            "paths": {
                key: str(value)
                for key, value in layout.ensure_portfolio_layout().items()
                if isinstance(value, Path)
            }
        },
    )

    _load_portfolio_level()

    step("scene_metadata_exporter", lambda: {"path": str(metadata.write_scene_metadata())})
    step("export_genome_axis", lambda: {"path": str(genome_axis.write_genome_axis())})
    step("audit_pcg_heatmap", lambda: {"path": str(pcg_heatmap.generate_heatmap()["heatmap"]["path"])})
    step("capture_material_previews", lambda: {"path": str(previews.write_previews_manifest())})
    step("capture_portfolio_renders", capture.run_all_captures)
    step("stats_exporter", lambda: {"path": str(stats.write_stats())})
    step("compile_render_plates", lambda: {"path": str(plates.write_renders_manifest(plates.compile_renders_manifest()))})

    package_path: str | None = None
    _log("START portfolio_aggregator")
    try:
        package, out_path = aggregator.ensure_package_written()
        package_path = str(out_path)
        warning_count = len(package.get("metadata", {}).get("validation_warnings", []))
        steps.append(
            {
                "step": "portfolio_aggregator",
                "ok": True,
                "path": package_path,
                "warnings": warning_count,
            }
        )
        _log(f"OK portfolio_aggregator -> {out_path} (warnings={warning_count})")
    except Exception as exc:
        steps.append({"step": "portfolio_aggregator", "ok": False, "error": str(exc)})
        _log(f"FAIL portfolio_aggregator: {exc}")

    step("package_to_website_handoff", website_handoff.write_handoff)

    all_ok = PACKAGE_PATH.is_file() and bool(steps) and all(
        entry.get("ok") is True for entry in steps
    )
    report = {
        "timestamp": datetime.now(timezone.utc).isoformat(),
        "steps": steps,
        "portfolio_package": package_path,
        "all_ok": all_ok,
    }

    REPORT.parent.mkdir(parents=True, exist_ok=True)
    REPORT.write_text(json.dumps(report, indent=2), encoding="utf-8")
    _log(f"complete all_ok={all_ok} report={REPORT}")
    return report


def main() -> int:
    try:
        import unreal  # noqa: F401

        report = run_portfolio_pipeline()
        package_exists = PACKAGE_PATH.is_file()
        print(
            f"GENERATE_PORTFOLIO all_ok={report['all_ok']} "
            f"package={report.get('portfolio_package')} -> {REPORT}"
        )
        return 0 if report["all_ok"] and package_exists else 1
    except ImportError:
        if not UE_CMD.exists():
            print(f"ERROR: Unreal Editor not found at {UE_CMD}")
            return 1
        log = PROJECT_ROOT / "Saved" / "Logs" / "generate_portfolio.log"
        log.parent.mkdir(parents=True, exist_ok=True)
        disable_monolith = os.environ.get("PORTFOLIO_CAPTURE_MONOLITH", "0").strip() not in ("1", "true", "TRUE", "yes", "YES")
        cmd = [
            str(UE_CMD),
            str(UPROJECT),
            f"-ExecutePythonScript={(PROJECT_ROOT / 'Content/Python/generate_portfolio.py').as_posix()}",
            "-stdout",
            "-unattended",
            "-nosplash",
            *(["-DisablePlugins=Monolith"] if disable_monolith else []),
            f"-log={log}",
        ]
        print(f"Launching portfolio pipeline (RHI) -> {log}")
        return subprocess.run(cmd, cwd=str(PROJECT_ROOT)).returncode


if __name__ == "__main__":
    raise SystemExit(main())
