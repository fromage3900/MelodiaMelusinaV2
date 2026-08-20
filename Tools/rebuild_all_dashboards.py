#!/usr/bin/env python3
"""
rebuild_all_dashboards.py — regenerate every pipeline dashboard in one command.

Runs the existing dashboard generators (from the repo root, via subprocess) and
prints a summary table of the output files:

    Tools/rebuild_t3d_dashboards.py  -> Saved/t3d-catalog.html
                                       Saved/agent-dashboard-t3d.html
                                       (+ wix mirror when the wix dir exists)
    Tools/metrics_dashboard.py       -> Saved/metrics_dashboard.html
    Tools/live_dashboard.py          -> Saved/live_dashboard.html
    Tools/loop_monitor.py --html     -> Saved/loop_monitor.html

    Tools/project_health_dashboard.py -> Saved/project_health.html
                                       Saved/Audit/project_health_claims.json
                                       (+ wix/project_health.html when wix exists)

The MCP-backed generators degrade gracefully when Monolith is down (they write
dashboards showing error states), so this script never crashes; a generator
that fails to produce its output file is reported as FAIL.
"""
import subprocess
import sys
from pathlib import Path

PROJECT_ROOT = Path(__file__).resolve().parents[1]
TOOLS = PROJECT_ROOT / "Tools"
SAVED = PROJECT_ROOT / "Saved"
WIX = Path(r"C:\EnvironmentPortfolio\wix")

GENERATORS = [
    {
        "name": "rebuild_t3d_dashboards.py",
        "args": [],
        "outputs": ["Saved/t3d-catalog.html", "Saved/agent-dashboard-t3d.html"],
    },
    {"name": "metrics_dashboard.py", "args": [], "outputs": ["Saved/metrics_dashboard.html"]},
    {"name": "live_dashboard.py", "args": [], "outputs": ["Saved/live_dashboard.html"]},
    {"name": "loop_monitor.py", "args": ["--html"], "outputs": ["Saved/loop_monitor.html"]},
    {"name": "project_health_dashboard.py", "args": [], "outputs": ["Saved/project_health.html"]},
]


def output_paths(gen) -> list[Path]:
    paths = [Path(o) for o in gen["outputs"]]
    if gen["name"] in {"rebuild_t3d_dashboards.py", "project_health_dashboard.py"} and WIX.is_dir():
        paths += [WIX / Path(o).name for o in gen["outputs"] if Path(o).suffix == ".html"]
    return paths


def mtime(path: Path):
    try:
        return path.stat().st_mtime
    except OSError:
        return None


def run() -> int:
    print("Rebuilding all dashboards...\n")
    rows = []
    for gen in GENERATORS:
        outputs = output_paths(gen)
        before = {p: mtime(p) for p in outputs}
        cmd = [sys.executable, str(TOOLS / gen["name"])] + gen["args"]
        try:
            proc = subprocess.run(cmd, cwd=str(PROJECT_ROOT), capture_output=True, text=True, timeout=300)
            rc = proc.returncode
            tail = (proc.stdout + proc.stderr).strip().splitlines()[-4:]
        except subprocess.TimeoutExpired:
            rc = -1
            tail = ["[timed out after 300s]"]
        except OSError as e:
            rc = -2
            tail = [f"[could not launch: {e}]"]

        for p in outputs:
            after = mtime(p)
            if p.exists():
                size = p.stat().st_size
                if rc != 0:
                    status = f"OK (rc={rc})"
                elif before[p] is not None and after is not None and after <= before[p]:
                    status = "OK (unchanged)"
                else:
                    status = "OK"
            else:
                size = 0
                status = "FAIL"
                if tail:
                    tail = tail[-3:]
            rows.append((gen["name"], str(p), size, status, "; ".join(tail)))

    print(f"{'generator':<28} {'path':<58} {'bytes':>9}  status")
    print("-" * 110)
    for name, path, size, status, detail in rows:
        print(f"{name:<28} {path:<58} {size:>9}  {status}")
        if detail and status != "OK":
            for line in detail.split("; "):
                print(f"    note: {line}")

    failed = [r for r in rows if r[3] == "FAIL"]
    print()
    print(f"serve with: python -m http.server 8080 -d Saved")
    if failed:
        print(f"{len(failed)} output(s) missing; check the generator notes above.")
        return 1
    print("All dashboards present.")
    return 0


if __name__ == "__main__":
    sys.exit(run())
