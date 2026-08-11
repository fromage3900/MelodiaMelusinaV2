"""Safe UE 5.8 World Partition builder wrapper.

The wrapper refuses to run while any editor process exists. It intentionally
does not stop processes, use Live Coding, or mutate the editor world.
"""

from __future__ import annotations

import argparse
import subprocess
from pathlib import Path


PROJECT_ROOT = Path(__file__).resolve().parents[2]
UE_CMD = Path(r"C:\Program Files\Epic Games\UE_5.8\Engine\Binaries\Win64\UnrealEditor-Cmd.exe")
UPROJECT = PROJECT_ROOT / "BS_GodFile.uproject"


def editor_is_active() -> tuple[bool, str]:
    probe = subprocess.run(
        [
            "powershell",
            "-NoProfile",
            "-Command",
            "$p=Get-Process UnrealEditor,UnrealEditor-Cmd -ErrorAction SilentlyContinue; if ($p) { $p | Select-Object Id,ProcessName; exit 2 }",
        ],
        capture_output=True,
        text=True,
        check=False,
    )
    return probe.returncode != 0, probe.stdout.strip()


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--map", required=True, help="World Partition map package path")
    parser.add_argument(
        "--builder",
        default="PCGWorldPartitionBuilder",
        choices=("PCGWorldPartitionBuilder", "WorldPartitionHLODsBuilder"),
    )
    parser.add_argument("--graphs", default="", help="Semicolon-separated PCG graph names")
    parser.add_argument("--iterative-cell-size", type=int, default=25600)
    parser.add_argument("--log", default="Saved/Logs/world_partition_builder_safe.log")
    args = parser.parse_args()

    if not UE_CMD.exists():
        print(f"Missing UnrealEditor-Cmd: {UE_CMD}")
        return 1
    if not UPROJECT.exists():
        print(f"Missing project: {UPROJECT}")
        return 1

    active, details = editor_is_active()
    if active:
        print("Refusing commandlet launch while an Unreal editor process is active.")
        if details:
            print(details)
        return 2

    log_path = PROJECT_ROOT / args.log
    log_path.parent.mkdir(parents=True, exist_ok=True)
    command = [
        str(UE_CMD),
        str(UPROJECT),
        args.map,
        "-Unattended",
        "-AllowCommandletRendering",
        "-stdout",
        "-run=WorldPartitionBuilderCommandlet",
        f"-Builder={args.builder}",
        "-SCCProvider=None",
        "-IterativeCellLoading=True",
        f"-IterativeCellSize={args.iterative_cell_size}",
        "-OneComponentAtATime=True",
        "-AssetGatherAll=True",
        f"-Log={log_path}",
    ]
    if args.graphs:
        command.append(f"-IncludeGraphNames={args.graphs}")

    print(">>>", " ".join(command))
    return subprocess.run(command, cwd=str(PROJECT_ROOT), check=False).returncode


if __name__ == "__main__":
    raise SystemExit(main())
