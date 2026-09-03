#!/usr/bin/env python3
"""
run_headless.py — Launch UE-Cmd to run Python scripts headlessly.

Usage:
    # Validate material schema (read-only)
    python run_headless.py --validate

    # Fix schema violations
    python run_headless.py --fix

    # Pre-capture gate (stricter)
    python run_headless.py --precapture

    # Run a custom Python script
    python run_headless.py --script "Content/Python/my_script.py"

    # Run with specific args to the script
    python run_headless.py --script "Content/Python/enforce_material_schema.py" -- --validate
"""
from __future__ import annotations
import subprocess, sys, os, json, time
from pathlib import Path

PROJECT = Path(__file__).resolve().parents[2] / "BS_GodFile.uproject"
ENGINE = Path("C:/Program Files/Epic Games/UE_5.8/Engine/Binaries/Win64/UnrealEditor-Cmd.exe")
OUTPUT_DIR = Path(__file__).resolve().parents[1] / "Saved" / "Audit"
os.environ["UE_PYTHON_OUTPUT"] = str(OUTPUT_DIR)

SCRIPTS = {
    "validate": "Content/Python/enforce_material_schema.py --headless --validate",
    "fix": "Content/Python/enforce_material_schema.py --headless --fix",
    "precapture": "Content/Python/enforce_material_schema.py --headless --precapture",
}

def run_headless(script_path: str, script_args: str = "") -> dict:
    """Launch UE-Cmd, execute a Python script, return output."""
    if not ENGINE.exists():
        return {"ok": False, "error": f"Engine not found at {ENGINE}"}
    if not PROJECT.exists():
        return {"ok": False, "error": f"Project not found at {PROJECT}"}

    OUTPUT_DIR.mkdir(parents=True, exist_ok=True)
    timestamp = time.strftime("%Y%m%d_%H%M%S")
    log_path = OUTPUT_DIR / f"headless_{timestamp}.log"

    cmd = [
        str(ENGINE),
        str(PROJECT),
        "-ExecutePythonScript",
        f"{script_path} {script_args}",
        "-unattended",      # no confirmation dialogs
        "-noP4",             # no Perforce
        "-nullRHI",          # no GPU needed for parameter enumeration
        "-NOSOUND",
        "-log",
        "-stdout",           # force output to stdout
        "-FullStdOutLogOutput",
    ]

    print(f"  Launching UE-Cmd...")
    print(f"  Script: {script_path} {script_args}")
    print(f"  Log: {log_path}")
    sys.stdout.flush()

    try:
        result = subprocess.run(
            cmd,
            capture_output=True,
            text=True,
            timeout=900,  # first launch DDC compile can take 5-15m
            creationflags=subprocess.CREATE_NO_WINDOW if sys.platform == "win32" else 0,
        )
        # Save full output
        log_path.write_text(result.stdout + "\n--- STDERR ---\n" + result.stderr)

        # Extract Python output between markers
        full = result.stdout + result.stderr
        return {"ok": True, "output": full, "log": str(log_path), "returncode": result.returncode}
    except subprocess.TimeoutExpired:
        return {"ok": False, "error": "Timed out after 300s"}
    except Exception as e:
        return {"ok": False, "error": str(e)}

def main():
    # Parse args
    script = None
    script_args = ""
    remaining = sys.argv[1:]

    for key, sc in SCRIPTS.items():
        if f"--{key}" in remaining:
            script = sc
            remaining = [r for r in remaining if f"--{key}" not in r]
            break

    # Custom script?
    for i, arg in enumerate(remaining):
        if arg == "--script" and i + 1 < len(remaining):
            script = remaining[i + 1]
            # Collect any remaining args after --
            if "--" in remaining:
                idx = remaining.index("--")
                script_args = " ".join(remaining[idx + 1:])
            break

    if not script:
        print("Usage:")
        for key in SCRIPTS:
            print(f"  python run_headless.py --{key}")
        print("  python run_headless.py --script path/to/script.py -- --extra-args")
        return 1

    print(f"=== Headless UE Execution ===")
    if "enforce_material_schema" in script:
        print(f"  Mode: {script.split()[-1]}")
        print(f"  Schema: Content/Python/material_schema.yaml")

    result = run_headless(script, script_args)

    if result.get("ok"):
        print(f"\n  Return code: {result.get('returncode')}")
        # Print last lines of output (the script's stdout)
        output = result.get("output", "")
        # Extract just the script output lines (between engine noise)
        lines = output.splitlines()
        important = [l for l in lines if any(m in l for m in 
            ["ERROR:", "WARNING:", "PASS:", "FAIL:", "FIXED:", "=== Results", "Schema:", "MPC:", "Missing", "=== Material"])]
        for l in important:
            print(f"  {l}")
        print(f"\n  Full output saved to: {result.get('log')}")
        return result.get("returncode", 0)
    else:
        print(f"  FAILED: {result.get('error')}")
        return 1

if __name__ == "__main__":
    raise SystemExit(main())
