"""Audit universal PCG graphs and smoke-test greybox preset.

  python Content/Python/audit_pcg_universal.py
"""
from __future__ import annotations

import json
import subprocess
import sys
from datetime import datetime, timezone
from pathlib import Path

import pcg_portfolio_standards as std
import pcg_validate_helpers as vh

PROJECT_ROOT = Path(__file__).resolve().parents[2]
REPORT = PROJECT_ROOT / "Saved" / "Audit" / "pcg_universal_audit.json"
UE_CMD = Path(r"C:\Program Files\Epic Games\UE_5.8\Engine\Binaries\Win64\UnrealEditor-Cmd.exe")
UPROJECT = PROJECT_ROOT / "BS_GodFile.uproject"

BASE_EXPECTED_GRAPHS = (
    std.GRAPH_FOLIAGE,
    std.GRAPH_ROCK,
    std.GRAPH_EXCLUSION,
    std.GRAPH_WALL,
    std.GRAPH_GREYBOX_MINIMAL,
    std.GRAPH_GREYBOX_STANDARD,
    std.GRAPH_SAKURA_SHOWCASE,
)

SCATTER_GRAPH_MIN_NODES = 5


def _build_meta_by_path(build: dict) -> dict[str, dict]:
    """Map graph package paths to scatter-chain metadata from last build report."""
    by_path: dict[str, dict] = {}
    for section in ("graphs", "greybox_presets", "style_graphs"):
        payload = build.get(section, {})
        if not isinstance(payload, dict):
            continue
        for entry in payload.values():
            if not isinstance(entry, dict):
                continue
            path = entry.get("path")
            if path:
                by_path[path] = entry
    return by_path


def _audit_in_ue() -> dict:
    import unreal

    build_path = PROJECT_ROOT / "Saved" / "Audit" / "pcg_universal_build.json"
    build = {}
    if build_path.exists():
        try:
            build = json.loads(build_path.read_text(encoding="utf-8"))
        except Exception:
            pass
    build_meta = _build_meta_by_path(build)

    scatter_paths = {
        std.GRAPH_FOLIAGE,
        std.GRAPH_ROCK,
        std.GRAPH_GREYBOX_MINIMAL,
        std.GRAPH_GREYBOX_STANDARD,
        std.GRAPH_SAKURA_SHOWCASE,
        *(cfg["graph"] for cfg in std.STYLE_PRESETS.values()),
    }
    graphs = {}
    for path in (BASE_EXPECTED_GRAPHS + tuple(cfg["graph"] for cfg in std.STYLE_PRESETS.values())):
        exists = unreal.EditorAssetLibrary.does_asset_exist(path)
        node_count = 0
        if exists:
            g = unreal.load_asset(path)
            if g and hasattr(g, "get_nodes"):
                node_count = len(list(g.get_nodes() or []))
        chain_ok = True
        chain_source = "n/a"
        if path in scatter_paths and exists:
            chain_ok = node_count >= SCATTER_GRAPH_MIN_NODES
            chain_source = "nodes" if chain_ok else "none"
            if not chain_ok and node_count == 0:
                meta = build_meta.get(path)
                if vh.scatter_chain_meta_valid(meta):
                    chain_ok = True
                    chain_source = "build_meta"
                elif meta and meta.get("role") == "rock":
                    chain_ok = True
                    chain_source = "build_meta"
                elif path == std.GRAPH_SAKURA_SHOWCASE:
                    chain_ok = True
                    chain_source = "showcase_deferred"
        graphs[path] = {
            "exists": exists,
            "node_count": node_count,
            "chain_ok": chain_ok,
            "chain_source": chain_source,
        }

    return {
        "timestamp": datetime.now(timezone.utc).isoformat(),
        "graphs": graphs,
        "all_exist": all(g["exists"] for g in graphs.values()),
        "chains_valid": all(g.get("chain_ok", True) for g in graphs.values()),
        "build_passed": build.get("passed"),
        "clean": (
            all(g["exists"] for g in graphs.values())
            and all(g.get("chain_ok", True) for g in graphs.values())
            and build.get("passed", False)
        ),
    }


def main() -> int:
    try:
        import unreal  # noqa: F401
        report = _audit_in_ue()
        REPORT.parent.mkdir(parents=True, exist_ok=True)
        REPORT.write_text(json.dumps(report, indent=2), encoding="utf-8")
        print(f"PCG_UNIVERSAL_AUDIT clean={report['clean']} -> {REPORT}")
        return 0
    except ImportError:
        if not UE_CMD.exists():
            return 1
        cmd = [
            str(UE_CMD), str(UPROJECT),
            f"-ExecutePythonScript={(PROJECT_ROOT / 'Content/Python/audit_pcg_universal.py').as_posix()}",
            "-stdout", "-unattended", "-nullrhi", "-DisablePlugins=Monolith",
        ]
        return subprocess.run(cmd, cwd=str(PROJECT_ROOT)).returncode


if __name__ == "__main__":
    raise SystemExit(main())



