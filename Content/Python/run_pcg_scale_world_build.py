"""Run the staged World Partition PCG/HLOD/nav build outside the live editor.

The command wrapper intentionally uses Unreal's documented builder commandlet
instead of inventing an editor-only generation loop. It is safe to dry-run
while another editor lane is active; actual execution requires the editor DLL
lock to be released.
"""
from __future__ import annotations

import argparse
import json
import subprocess
from pathlib import Path


PROJECT_ROOT = Path(__file__).resolve().parents[2]
UE_CMD = Path(r"C:\Program Files\Epic Games\UE_5.8\Engine\Binaries\Win64\UnrealEditor-Cmd.exe")
UPROJECT = PROJECT_ROOT / "BS_GodFile.uproject"
LOG_DIR = PROJECT_ROOT / "Saved" / "Logs"
LEVEL_DEFAULT = "/Game/EnvSandbox/PCG/Musical/Hero/L_PCG_Hero_ScaleWorldProof"
BUILDER_SETTINGS = "/Game/EnvSandbox/PCG/Musical/Hero/DA_PCGHeroBuilderSettings"
GRAPH_NAMES = (
    "PCG_Hero_ResonanceCathedral",
    "PCG_Hero_ArpeggioBridge",
    "PCG_Hero_BellTreeGarden",
    "PCG_Hero_XylophoneTrail",
    "PCG_Hero_CrystalHarpGrove",
    "PCG_Hero_WaterGameplayInteractive",
)
BUILD_REPORT = PROJECT_ROOT / "Saved" / "Audit" / "pcg_scale_world_build.json"


def commandlet_asset_path(path: str) -> str:
    """Return the explicit object path expected by native soft-object loading."""
    package, _, object_name = path.rpartition("/")
    if not object_name or "." in object_name:
        return path
    return f"{path}.{object_name}"


def assert_editor_dll_unlocked() -> None:
    """Reject commandlet writes while the live editor owns the game module."""
    dll = PROJECT_ROOT / "Binaries" / "Win64" / "UnrealEditor-BS_GodFile.dll"
    if not dll.exists():
        raise FileNotFoundError(dll)
    try:
        with dll.open("r+b"):
            pass
    except OSError as exc:
        raise RuntimeError(
            "Unreal Editor still holds UnrealEditor-BS_GodFile.dll; close the editor before staged builders"
        ) from exc


def command_for(level: str, builder: str, *, graph_names: tuple[str, ...] = (), settings: str = BUILDER_SETTINGS, extra: tuple[str, ...] = ()) -> list[str]:
    command = [
        str(UE_CMD),
        str(UPROJECT),
        level,
        "-Unattended",
        "-NoSplash",
        "-stdout",
        "-SCCProvider=None",
        # The workstation's Installed DDC graph currently points at an
        # unavailable G:/UE_DDC and a non-writable Zen service. Commandlets
        # must still have a writable cache for PCG/HLOD/nav artifacts, so use
        # UE's documented in-memory fallback for this proof build.
        "-DDC-ForceMemoryCache",
        # Keep unattended stages off the shared user-temp shader workspace.
        # Multiple editor/commandlet lanes can otherwise collide on the same
        # transfer files even when the project DLL is unlocked.
        "-ShaderWorkingDir=Saved/ShaderWorkingDir/PCGScaleWorld",
        "-run=WorldPartitionBuilderCommandlet",
        f"-Builder={builder}",
    ]
    if builder == "PCGWorldPartitionBuilder":
        command.extend([
            "-AllowCommandletRendering",
            f"-PCGBuilderSettings={commandlet_asset_path(settings)}",
            "-IterativeCellLoading",
            "-IterativeCellSize=25600",
            "-AssetGatherAll",
            "-GenerateComponentEditingModeLoadAsPreview",
            # Proof inputs created by headless/editor lanes may retain the
            # native Normal serialized mode; include both modes explicitly.
            "-GenerateComponentEditingModeNormal",
        ])
        if graph_names:
            command.append(f"-IncludeGraphNames={';'.join(graph_names)}")
    command.extend(extra)
    return command


def run_stage(name: str, command: list[str], *, dry_run: bool) -> int:
    LOG_DIR.mkdir(parents=True, exist_ok=True)
    log_path = LOG_DIR / f"pcg_scale_world_{name}.log"
    full = command + [f"-Log={log_path}"]
    print(f"[{name}] {' '.join(full)}")
    if dry_run:
        return 0
    if not UE_CMD.exists():
        raise FileNotFoundError(UE_CMD)
    completed = subprocess.run(
        full,
        cwd=str(PROJECT_ROOT),
        stdout=subprocess.PIPE,
        stderr=subprocess.STDOUT,
        text=True,
        encoding="utf-8",
        errors="replace",
    )
    log_path.write_text(completed.stdout, encoding="utf-8")
    print(completed.stdout)
    return completed.returncode


def write_build_report(report: dict, path: Path = BUILD_REPORT) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(report, indent=2), encoding="utf-8")


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--level", default=LEVEL_DEFAULT)
    parser.add_argument("--settings", default=BUILDER_SETTINGS)
    parser.add_argument("--dry-run", action="store_true")
    parser.add_argument("--skip-rvt", action="store_true")
    parser.add_argument(
        "--stop-on-failure",
        action="store_true",
        help="stop after the first failed stage; default keeps collecting later-stage audit evidence",
    )
    args = parser.parse_args()

    stages = [
        ("pcg", command_for(args.level, "PCGWorldPartitionBuilder", graph_names=GRAPH_NAMES, settings=args.settings)),
        ("hlod", command_for(args.level, "WorldPartitionHLODsBuilder", extra=("-AllowCommandletRendering",))),
        ("nav", command_for(args.level, "WorldPartitionNavigationDataBuilder", extra=("-AllowCommandletRendering",))),
        ("minimap", command_for(args.level, "WorldPartitionMiniMapBuilder", extra=("-AllowCommandletRendering",))),
    ]
    if not args.skip_rvt:
        stages.append(("rvt", command_for(args.level, "WorldPartitionRVTBuilder", extra=("-AllowCommandletRendering",))))

    if not args.dry_run:
        assert_editor_dll_unlocked()

    report = {
        "level": args.level,
        "settings": args.settings,
        "dry_run": bool(args.dry_run),
        "stages": [],
        "production_maps_touched": False,
    }
    report_path = BUILD_REPORT if not args.dry_run else BUILD_REPORT.with_name("pcg_scale_world_build_dry_run.json")

    for name, command in stages:
        result = run_stage(name, command, dry_run=args.dry_run)
        report["stages"].append({
            "name": name,
            "command": command,
            "return_code": result,
            "log": str(LOG_DIR / f"pcg_scale_world_{name}.log"),
        })
        write_build_report(report, report_path)
        if result != 0 and args.stop_on_failure:
            print(f"[{name}] failed with exit code {result}")
            return result
    report["ok"] = all(int(stage.get("return_code", 1)) == 0 for stage in report["stages"])
    write_build_report(report, report_path)
    if report["ok"]:
        print("PCG_SCALE_WORLD_BUILD_OK")
        return 0
    print("PCG_SCALE_WORLD_BUILD_INCOMPLETE")
    return 1


if __name__ == "__main__":
    raise SystemExit(main())
