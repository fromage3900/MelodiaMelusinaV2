#!/usr/bin/env python3
"""Pack-up check for the 02:00 clean offline C++ build of BS_GodFileEditor.

Run this BEFORE the build. It is offline and read-only: it changes nothing.

It answers, in one screen:
  1. is anything Unreal running right now (the editor belongs to the artist, and a
     second UE instance beside it is what took the machine down earlier tonight);
  2. which C++ files are OURS and will be compiled - so a failure can be attributed;
  3. which C++ paths belong to the OTHER session and are therefore not ours to fix;
  4. is the build actually runnable (the engine, the project, the command);
  5. what memory headroom the build has - a 7.7 GB mesh build and a C++ compile
     together is how the commit limit gets hit.

Usage:
    python Tools/prepare_house_build.py
"""

from __future__ import annotations

import pathlib
import subprocess
import sys

REPO_ROOT = pathlib.Path(__file__).resolve().parents[1]
PROJECT = REPO_ROOT / "BS_GodFile.uproject"
ENGINE = pathlib.Path(r"C:\Program Files\Epic Games\UE_5.8")
BUILD_BAT = ENGINE / "Engine" / "Build" / "BatchFiles" / "Build.bat"

# The C++ this agent added or changed for the dressing pipeline. These are OURS:
# a compile failure in one of them is ours to fix.
OUR_CPP = [
    "Source/BS_GodFile/MelodiaIntegration/MelodiaDressingCatalog.h",
    "Source/BS_GodFile/MelodiaIntegration/MelodiaDressingCatalog.cpp",
    "Source/BS_GodFile/MelodiaIntegration/MelodiaDressingTags.h",
    "Source/BS_GodFile/MelodiaIntegration/MelodiaDressingTags.cpp",
    "Source/BS_GodFile/MelodiaIntegration/MelodiaDressingSubsystem.h",
    "Source/BS_GodFile/MelodiaIntegration/MelodiaDressingSubsystem.cpp",
]

BUILD_COMMAND = (
    f'"{BUILD_BAT}" BS_GodFileEditor Win64 Development '
    f'-Project="{PROJECT}"'
)


def git(*args: str) -> str:
    try:
        return subprocess.run(["git", "-C", str(REPO_ROOT), *args],
                              capture_output=True, text=True, timeout=120).stdout
    except Exception:
        return ""


def unreal_processes() -> list[tuple[str, str, str]]:
    """(name, pid, started) for every Unreal process - interactive or commandlet."""
    out = []
    try:
        result = subprocess.run(
            ["powershell", "-NoProfile", "-Command",
             "Get-Process -Name UnrealEditor,UnrealEditor-Cmd -ErrorAction SilentlyContinue | "
             "ForEach-Object { \"$($_.ProcessName)|$($_.Id)|$($_.StartTime)\" }"],
            capture_output=True, text=True, timeout=120)
        for line in (result.stdout or "").splitlines():
            parts = line.strip().split("|")
            if len(parts) == 3:
                out.append((parts[0], parts[1], parts[2]))
    except Exception:
        pass
    return out


def memory_headroom() -> tuple[float, float]:
    try:
        result = subprocess.run(
            ["powershell", "-NoProfile", "-Command",
             "$c=(Get-Counter '\\Memory\\Committed Bytes').CounterSamples[0].CookedValue; "
             "$l=(Get-Counter '\\Memory\\Commit Limit').CounterSamples[0].CookedValue; "
             "\"$c|$l\""],
            capture_output=True, text=True, timeout=120)
        committed, limit = (result.stdout or "0|0").strip().split("|")[:2]
        return float(committed) / 1024**3, float(limit) / 1024**3
    except Exception:
        return 0.0, 0.0


def main() -> int:
    print("=" * 70)
    print("HOUSE BUILD PACK-UP - BS_GodFileEditor Win64 Development")
    print("=" * 70)

    print("\n1. UNREAL PROCESSES")
    processes = unreal_processes()
    interactive = [p for p in processes if p[0] == "UnrealEditor"]
    commandlets = [p for p in processes if p[0] == "UnrealEditor-Cmd"]
    if interactive:
        print("   INTERACTIVE EDITOR RUNNING - the build wants this closed:")
        for name, pid, started in interactive:
            print(f"      {name} PID {pid}, started {started}")
    else:
        print("   no interactive editor - good")
    if commandlets:
        print("   commandlets running (they hold the commit limit):")
        for name, pid, started in commandlets:
            print(f"      {name} PID {pid}, started {started}")
    else:
        print("   no commandlets running")

    print("\n2. OUR C++ (compiled by this build; a failure here is ours)")
    status = git("status", "--porcelain", "--", "Source/", "Plugins/")
    dirty = {}
    for line in (status or "").splitlines():
        if len(line) > 3:
            dirty[line[3:].strip()] = line[:2].strip()
    missing = []
    for path in OUR_CPP:
        state = dirty.get(path)
        exists = (REPO_ROOT / path).exists()
        if not exists:
            missing.append(path)
        elif state:
            print(f"   {state:>3}  {path}")
        else:
            print(f"   ---  {path}  (committed and clean)")
    if missing:
        print("   MISSING FROM THE TREE:")
        for path in missing:
            print(f"      {path}")

    print("\n3. THE OTHER SESSION'S C++ (not ours to fix - report, do not touch)")
    others = [path for path, state in dirty.items()
              if state and path not in OUR_CPP and path.endswith((".cpp", ".h", ".cs"))]
    print(f"   {len(others)} dirty C++ paths from other sessions will also be compiled")
    for path in others[:8]:
        print(f"      {path}")
    if len(others) > 8:
        print(f"      ... and {len(others) - 8} more")

    print("\n4. IS THE BUILD RUNNABLE")
    print(f"   project      : {'OK' if PROJECT.exists() else 'MISSING'}  {PROJECT.name}")
    print(f"   engine       : {'OK' if ENGINE.exists() else 'MISSING'}  {ENGINE}")
    print(f"   build script : {'OK' if BUILD_BAT.exists() else 'MISSING'}")
    print(f"   command      : {BUILD_COMMAND}")

    print("\n5. MEMORY HEADROOM")
    committed, limit = memory_headroom()
    if limit:
        print(f"   committed {committed:.1f} GB of {limit:.1f} GB limit "
              f"({100 * committed / limit:.0f}% used, {limit - committed:.1f} GB free)")
        if committed / limit > 0.75:
            print("   TIGHT: close everything else before the build")
    else:
        print("   (could not read the counters)")

    print("\nRULES FOR THE BUILD")
    print("   - the editor must be closed; do not launch one")
    print("   - a compile failure in the OTHER session's file is REPORTED, not fixed")
    print("   - a compile failure in OUR files is ours to fix")
    print("   - no Live Coding: this is a full build")

    if interactive:
        print("\n   NOT READY: an interactive editor is running")
        return 1
    print("\n   READY (the editor is closed)")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
