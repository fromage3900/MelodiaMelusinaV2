"""Load a target level and run portfolio metadata + render exporters (needs RHI).

  UnrealEditor-Cmd.exe BS_GodFile.uproject ^
    -ExecutePythonScript="G:/EnvironmentPortfolio/BS_GodFile/Content/Python/run_portfolio_capture.py"

Override the level via env var (path was previously hardcoded+stale, silently
produced null metadata for every prior capture attempt):
  PORTFOLIO_CAPTURE_LEVEL=/Game/EnvSandbox/Environments/L_EscherAscent
"""
from __future__ import annotations

import json
import os
import subprocess
import sys
import time
from datetime import datetime, timezone
from pathlib import Path

PROJECT_ROOT = Path(__file__).resolve().parents[2]
REPORT = PROJECT_ROOT / "Saved" / "Audit" / "portfolio_capture.json"
# Was /Game/EnvSandbox/Levels/L_SakuraPath - that path has never existed; the
# real level is under Environments/Sakura/. Every prior capture silently
# no-op'd the load_level call and produced all-null scene metadata.
DEFAULT_LEVEL = "/Game/EnvSandbox/Environments/Sakura/L_SakuraPath"
LEVEL = os.environ.get("PORTFOLIO_CAPTURE_LEVEL", DEFAULT_LEVEL)
UE_CMD = Path(r"C:\Program Files\Epic Games\UE_5.8\Engine\Binaries\Win64\UnrealEditor-Cmd.exe")
UPROJECT = PROJECT_ROOT / "BS_GodFile.uproject"


def run_capture() -> dict:
    import unreal

    time.sleep(15)
    level_name = LEVEL.rsplit("/", 1)[-1]
    les = unreal.get_editor_subsystem(unreal.LevelEditorSubsystem)
    if les and unreal.EditorAssetLibrary.does_asset_exist(f"{LEVEL}.{level_name}"):
        les.load_level(LEVEL)
        # 3s wasn't enough for a real (non-empty) level - actors weren't
        # queryable yet even though the level asset had "loaded". Confirmed by
        # render_exporter (which runs after, needs no actor enumeration)
        # capturing correct pixels while scene_metadata (which ran first, 3s
        # after load) saw a fully empty actor list for the same level.
        time.sleep(8)
    else:
        unreal.log_error(f"PORTFOLIO_CAPTURE: level not found at {LEVEL} - metadata/renders will be empty")

    import portfolio_output_layout as layout
    import render_exporter as renders
    import scene_metadata_exporter as metadata

    layout.ensure_portfolio_layout()
    # Renders first (viewport capture naturally waits out its own TAA
    # warm-up) - metadata's actor enumeration piggybacks on that settle time
    # instead of racing it.
    render_result = renders.export_renders()
    meta_path = _write_scene_metadata_with_retry(metadata)
    layout.organize_portfolio_outputs()

    return {
        "ok": True,
        "level": LEVEL,
        "metadata": str(meta_path),
        "renders": render_result,
    }


def _write_scene_metadata_with_retry(metadata) -> Path:
    """Retry scene metadata export a few times in headless runs.

    UnrealEditor-Cmd can race between level load completing, log rotation,
    and EditorActorSubsystem population. A short retry loop is more robust
    than one-shot timing.
    """
    last_error = None
    for attempt in range(3):
        try:
            return metadata.write_scene_metadata()
        except Exception as exc:
            last_error = exc
            unreal.log(f"[PORTFOLIO_CAPTURE] scene_metadata attempt {attempt+1} failed: {exc}")
            time.sleep(5)
    raise RuntimeError(f"scene_metadata_exporter failed after retries: {last_error}")


def main() -> int:
    try:
        import unreal  # noqa: F401
        result = run_capture()
        report = {"timestamp": datetime.now(timezone.utc).isoformat(), **result}
        REPORT.parent.mkdir(parents=True, exist_ok=True)
        REPORT.write_text(json.dumps(report, indent=2), encoding="utf-8")
        print(f"PORTFOLIO_CAPTURE ok -> {REPORT}")
        return 0
    except ImportError:
        if not UE_CMD.exists():
            print(f"ERROR: {UE_CMD}")
            return 1
        log = PROJECT_ROOT / "Saved" / "Logs" / "portfolio_capture.log"
        cmd = [
            str(UE_CMD),
            str(UPROJECT),
            f"-ExecutePythonScript={(PROJECT_ROOT / 'Content/Python/run_portfolio_capture.py').as_posix()}",
            "-stdout",
            "-unattended",
            "-nosplash",
            "-DisablePlugins=Monolith",
            f"-log={log}",
        ]
        print(f"Launching portfolio capture (RHI) -> {log} [level={LEVEL}]")
        env = {**os.environ, "PORTFOLIO_CAPTURE_LEVEL": LEVEL}
        return subprocess.run(cmd, cwd=str(PROJECT_ROOT), env=env).returncode


if __name__ == "__main__":
    raise SystemExit(main())
