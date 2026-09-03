"""Probe PCGEx node Settings classes available in the editor.

  python Content/Python/probe_pcgex_nodes.py
"""
from __future__ import annotations

import json
import subprocess
import sys
from datetime import datetime, timezone
from pathlib import Path

PROJECT_ROOT = Path(__file__).resolve().parents[2]
REPORT = PROJECT_ROOT / "Saved" / "Audit" / "pcgex_node_probe.json"
UE_CMD = Path(r"C:\Program Files\Epic Games\UE_5.8\Engine\Binaries\Win64\UnrealEditor-Cmd.exe")
UPROJECT = PROJECT_ROOT / "BS_GodFile.uproject"


def _probe_in_ue() -> dict:
    import unreal

    pcgex = sorted(
        n for n in dir(unreal)
        if "pcgex" in n.lower() and ("Settings" in n or "settings" in n)
    )
    stock = sorted(
        n for n in dir(unreal)
        if n.startswith("PCG") and n.endswith("Settings") and "pcgex" not in n.lower()
    )[:80]
    plugins = []
    for name in ("PCG", "PCGExtendedToolkit", "PCGPythonInterop"):
        try:
            plugins.append({"name": name, "enabled": unreal.PluginBlueprintLibrary.is_plugin_enabled(name)})
        except Exception:
            plugins.append({"name": name, "enabled": None})
    return {
        "timestamp": datetime.now(timezone.utc).isoformat(),
        "pcgex_settings_classes": pcgex,
        "pcgex_count": len(pcgex),
        "stock_pcg_sample": stock,
        "plugins": plugins,
    }


def main() -> int:
    try:
        import unreal  # noqa: F401
        report = _probe_in_ue()
        REPORT.parent.mkdir(parents=True, exist_ok=True)
        REPORT.write_text(json.dumps(report, indent=2), encoding="utf-8")
        print(f"PCGEX_PROBE_OK count={report['pcgex_count']} -> {REPORT}")
        return 0
    except ImportError:
        if not UE_CMD.exists():
            print(f"ERROR: {UE_CMD}")
            return 1
        cmd = [
            str(UE_CMD), str(UPROJECT),
            f"-ExecutePythonScript={(PROJECT_ROOT / 'Content/Python/probe_pcgex_nodes.py').as_posix()}",
            "-stdout", "-unattended", "-nullrhi", "-DisablePlugins=Monolith",
        ]
        return subprocess.run(cmd, cwd=str(PROJECT_ROOT)).returncode


if __name__ == "__main__":
    raise SystemExit(main())
