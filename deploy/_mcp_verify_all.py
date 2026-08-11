# Unified headless verify for Surreal Architecture v2.68.
# Always use --factory-startup to avoid loading user addons (10+ min hang).
#
# Usage:
#   blender --background --factory-startup --python deploy/_mcp_verify_all.py
#   blender --background --factory-startup --python deploy/_mcp_verify_all.py -- world
#   blender --background --factory-startup --python deploy/_mcp_verify_all.py -- overhaul
import os
import runpy
import sys

DEPLOY = os.path.dirname(os.path.abspath(__file__))
MODE = os.environ.get("MCP_VERIFY_MODE", "all")
if "--" in sys.argv:
    idx = sys.argv.index("--")
    if idx + 1 < len(sys.argv):
        MODE = sys.argv[idx + 1].lower()

SCRIPTS = {
    "overhaul": os.path.join(DEPLOY, "_mcp_verify_overhaul.py"),
    "world": os.path.join(DEPLOY, "_mcp_verify_world.py"),
    "os": os.path.join(DEPLOY, "_mcp_verify_os.py"),
    "blender": os.path.join(DEPLOY, "_mcp_verify_blender_5_2.py"),
}

print(f"=== SURREAL VERIFY ALL (mode={MODE}) ===")
print("NOTE: launch Blender with --factory-startup for reliable headless runs")

failed = []
if MODE in ("all", "overhaul"):
    print("\n>>> Running overhaul verify...")
    try:
        runpy.run_path(SCRIPTS["overhaul"], run_name="__main__")
    except SystemExit as e:
        if e.code:
            failed.append("overhaul")
    except Exception as e:
        print(f"overhaul verify error: {e}")
        failed.append("overhaul")

if MODE in ("all", "world"):
    print("\n>>> Running world verify...")
    try:
        runpy.run_path(SCRIPTS["world"], run_name="__main__")
    except SystemExit as e:
        if e.code:
            failed.append("world")
    except Exception as e:
        print(f"world verify error: {e}")
        failed.append("world")

if MODE in ("all", "os"):
    print("\n>>> Running OS verify...")
    try:
        runpy.run_path(SCRIPTS["os"], run_name="__main__")
    except SystemExit as e:
        if e.code:
            failed.append("os")
    except Exception as e:
        print(f"os verify error: {e}")
        failed.append("os")

if MODE in ("all", "blender"):
    print("\n>>> Running Blender 5.2 MCP verify...")
    try:
        # blender verify runs via Python subprocess (not inside Blender)
        import subprocess as sp
        r = sp.run(
            [sys.executable, SCRIPTS["blender"]],
            capture_output=True, text=True, timeout=300,
        )
        print(r.stdout)
        if r.returncode != 0:
            print(f"blender verify stderr: {r.stderr[:500]}")
            failed.append("blender")
    except Exception as e:
        print(f"blender verify error: {e}")
        failed.append("blender")

if failed:
    print(f"\n=== VERIFY FAILED: {', '.join(failed)} ===")
    sys.exit(1)

print("\n=== ALL VERIFY OK ===")
