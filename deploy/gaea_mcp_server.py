#!/usr/bin/env python3
"""
Gaea MCP server — headless Gaea 2 terrain graph inspect + Swarm build via MCP.

Read-only paths (inspect/list/verify) work offline. Exec (build/stage/inject)
spawns the Gaea.Swarm CLI or rewrites .terrain JSON and is gated through
Tools/mcp_policy.py (write requires owner approval, matching the project's
per-tool policy).

Registration: add to C:\\EnvironmentPortfolio\\.mcp.json as server "gaea" pointing
at this file with env GAEA_SWARM_EXE + GAEA_PROJECT_ROOT.
"""
from __future__ import annotations

import hashlib
import json
import os
import re
import shutil
import subprocess
import sys
from pathlib import Path
from typing import Any

try:
    from mcp.server.fastmcp import FastMCP
except ImportError:  # allow py_compile / import on machines without the MCP SDK
    FastMCP = None  # type: ignore[assignment]

ROOT = Path(__file__).resolve().parent.parent
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

try:
    from Tools.mcp_policy import authorize_tool  # noqa: E402
except Exception:  # pragma: no cover - degrade gracefully outside the repo
    authorize_tool = None  # type: ignore[assignment]

SWARM_EXE = os.environ.get(
    "GAEA_SWARM_EXE",
    r"C:\Program Files\QuadSpinner\Gaea 2\Gaea.Swarm.exe",
)
PROJECT_ROOT = Path(os.environ.get("GAEA_PROJECT_ROOT", ROOT))
SETUPS_DIR = PROJECT_ROOT / "Saved" / "Audit" / "gaea_setups"

if FastMCP is not None:
    mcp = FastMCP("gaea")
else:  # pragma: no cover
    mcp = None  # type: ignore[assignment]


def _confine(path: str | None) -> Path:
    """Resolve a path and forbid escaping the project + Gaea roots."""
    if not path:
        raise ValueError("path required")
    p = Path(path).resolve()
    allowed = [PROJECT_ROOT.resolve(), Path(SWARM_EXE).parent.parent.resolve()]
    if p == PROJECT_ROOT.resolve():
        return p
    if not any(p == a or a in p.parents for a in allowed):
        raise PermissionError(f"path outside allowed roots: {p}")
    return p


def _normalise(value: str | None) -> str:
    return (value or "").replace("\\", "/").lower()


def _sha256(path: Path) -> str:
    h = hashlib.sha256()
    with path.open("rb") as f:
        for chunk in iter(lambda: f.read(1 << 20), b""):
            h.update(chunk)
    return h.hexdigest()


def _strip_trailing_commas(text: str) -> str:
    """Remove trailing commas before } or ] while respecting strings."""
    result: list[str] = []
    in_str = False
    esc = False
    i = 0
    n = len(text)
    while i < n:
        ch = text[i]
        if in_str:
            if esc:
                esc = False
            elif ch == "\\":
                esc = True
            elif ch == '"':
                in_str = False
            result.append(ch)
        else:
            if ch == '"':
                in_str = True
                result.append(ch)
            elif ch == ",":
                j = i + 1
                while j < n and text[j] in " \t\r\n":
                    j += 1
                if j < n and text[j] in "}]":
                    pass
                else:
                    result.append(ch)
            else:
                result.append(ch)
        i += 1
    return "".join(result)


def _load_terrain(path: Path) -> dict[str, Any]:
    raw = path.read_text(encoding="utf-8", errors="replace")
    clean = _strip_trailing_commas(raw)
    return json.loads(clean)


def _terrain(data: dict[str, Any]) -> dict[str, Any]:
    return data["Assets"]["$values"][0]["Terrain"]


def _all_ids(data: dict[str, Any]) -> set[int]:
    """Collect every numeric $id and Id in the document."""
    ids: set[int] = set()
    text = json.dumps(data)
    for m in re.finditer(r'"\$id"\s*:\s*"(\d+)"', text):
        ids.add(int(m.group(1)))
    for m in re.finditer(r'"Id"\s*:\s*(\d+)', text):
        ids.add(int(m.group(1)))
    return ids


def _next_ids(data: dict[str, Any], count: int) -> list[int]:
    existing = _all_ids(data)
    start = max(existing) + 1 if existing else 1
    return list(range(start, start + count))


def _find_sink_nodes(data: dict[str, Any]) -> list[dict[str, Any]]:
    """Return nodes whose PrimaryOut port has no downstream Record."""
    terrain = _terrain(data)
    nodes = terrain.get("Nodes", {})
    sinks: list[dict[str, Any]] = []
    for key, node in nodes.items():
        if key.startswith("$") or not isinstance(node, dict):
            continue
        for port in node.get("Ports", {}).get("$values", []):
            if port.get("Type", "").startswith("PrimaryOut") and not port.get("Record"):
                sinks.append({
                    "id": node.get("Id"),
                    "name": node.get("Name"),
                    "type": node.get("$type", "").split(",")[0].split(".")[-1],
                })
                break
    return sinks


def _dump_graph(source: Path) -> dict[str, Any]:
    data = _load_terrain(source)
    terrain = _terrain(data)
    nodes = terrain.get("Nodes", {})
    out: list[dict[str, Any]] = []
    sinks = _find_sink_nodes(data)
    for key, node in nodes.items():
        if key.startswith("$") or not isinstance(node, dict):
            continue
        short_type = node.get("$type", "?").split(",")[0].split(".")[-1]
        out.append({
            "id": node.get("Id"),
            "name": node.get("Name", "?"),
            "type": short_type,
        })
    selected = terrain.get("State", {}).get("SelectedNode")
    return {"node_count": len(out), "nodes": out, "sinks": sinks, "selected_node": selected}


def _find_matching_brace(text: str, open_pos: int) -> int:
    """Return the position of the matching close brace for `open_pos`."""
    depth = 0
    in_str = False
    esc = False
    i = open_pos
    n = len(text)
    while i < n:
        ch = text[i]
        if in_str:
            if esc:
                esc = False
            elif ch == "\\":
                esc = True
            elif ch == '"':
                in_str = False
        else:
            if ch == '"':
                in_str = True
            elif ch == "{":
                depth += 1
            elif ch == "}":
                depth -= 1
                if depth == 0:
                    return i
        i += 1
    raise RuntimeError("no matching close brace")


def _inject_export_node_text(
    raw: str,
    target_node_id: int,
    from_port: str,
    export_name: str,
) -> dict[str, Any]:
    """Inject a PNG16 Export node into the existing Nodes object text.

    We locate the Nodes object, reserve ids, serialize only the new node,
    and insert it as a new key-value pair with indentation matching the file.
    Existing node text is left untouched.
    """
    data = json.loads(_strip_trailing_commas(raw))
    terrain = _terrain(data)
    nodes = terrain.get("Nodes", {})
    if str(target_node_id) not in nodes:
        raise ValueError(f"target node {target_node_id} not found")

    ids = _next_ids(data, 10)
    nid, pos_id, save_defs_id, save_def_id, disabled_id, ports_id, pid_in, pid_out, rid, mods_id = ids
    target = nodes[str(target_node_id)]
    pos = target.get("Position", {"X": 0.0, "Y": 0.0})
    new_x = pos.get("X", 0.0) + 400.0
    new_y = pos.get("Y", 0.0)

    export_node = {
        "$id": str(nid),
        "$type": "QuadSpinner.Gaea.Nodes.Export, Gaea.Nodes",
        "Format": "PNG16",
        "Id": nid,
        "Name": export_name,
        "Position": {"$id": str(pos_id), "X": new_x, "Y": new_y},
        "SaveDefinitions": {
            "$id": str(save_defs_id),
            "$values": [
                {
                    "$id": str(save_def_id),
                    "Node": nid,
                    "Filename": export_name,
                    "Format": "PNG16",
                    "IsEnabled": True,
                    "DisabledInProfiles": {"$id": str(disabled_id), "$values": []},
                }
            ],
        },
        "Ports": {
            "$id": str(ports_id),
            "$values": [
                {
                    "$id": str(pid_in),
                    "Name": "In",
                    "Type": "PrimaryIn, Required",
                    "Record": {
                        "$id": str(rid),
                        "From": target_node_id,
                        "To": nid,
                        "FromPort": from_port,
                        "ToPort": "In",
                    },
                    "IsExporting": True,
                },
                {
                    "$id": str(pid_out),
                    "Name": "Out",
                    "Type": "PrimaryOut",
                    "IsExporting": True,
                },
            ],
        },
        "Modifiers": {"$id": str(mods_id), "$values": []},
    }

    nodes_start = raw.find('"Nodes":')
    if nodes_start < 0:
        raise RuntimeError("Nodes key not found")
    open_brace = raw.find("{", nodes_start)
    if open_brace < 0:
        raise RuntimeError("Nodes opening brace not found")
    nodes_end = _find_matching_brace(raw, open_brace) + 1

    # Detect the indentation used for node keys inside Nodes.
    nodes_body = raw[open_brace + 1:nodes_end - 1]
    key_indent = "            "  # fallback 12 spaces
    m = re.search(r'^(\s+)"\d+":\s*\{', nodes_body, re.MULTILINE)
    if m:
        key_indent = m.group(1)

    # Serialize the new node and build the entry with matching indentation.
    node_json = json.dumps(export_node, indent=2, ensure_ascii=False)
    inner_indent = key_indent + "  "
    lines = node_json.splitlines()
    entry_lines = [f'{key_indent}"{nid}": {{'] + [inner_indent + line for line in lines[1:]]
    entry_text = "\n".join(entry_lines)

    # Insert the new node between the last node entry and the closing of Nodes.
    # Pattern captures: last node close + newline + Nodes close + comma + Groups.
    pattern = r'(\n(\s*)}\s*\n(\s*)})(,\s*\n(\s*)"Groups":)'
    m = re.search(pattern, raw)
    if not m:
        raise RuntimeError("could not locate Nodes closing pattern")
    node_close_indent = m.group(2)
    nodes_close_indent = m.group(3)
    replacement = (
        f"\n{node_close_indent}}},\n"
        f"{entry_text}\n"
        f"{nodes_close_indent}}}"
        f"{m.group(4)}"
    )
    new_raw = raw[:m.start()] + replacement + raw[m.end():]

    return {
        "raw": new_raw,
        "export_node_id": nid,
        "export_name": export_name,
        "target_node_id": target_node_id,
    }


# --------------------------------------------------------------------------- #
# FastMCP tools
# --------------------------------------------------------------------------- #
if mcp is not None:

    @mcp.tool()
    def list_ga_recipes() -> list[str]:
        """Scan gaea_setups for melodia.gaea_setup.v1 recipe JSON files."""
        found = []
        for base in [PROJECT_ROOT / "Docs" / "WorldGen", SETUPS_DIR]:
            if not base.is_dir():
                continue
            for j in base.rglob("*.json"):
                try:
                    data = json.loads(j.read_text(encoding="utf-8"))
                except Exception:
                    continue
                if data.get("schema", "").startswith("melodia.gaea_setup"):
                    found.append(str(j.resolve()))
        return found

    @mcp.tool()
    def inspect_terrain(source: str) -> dict[str, Any]:
        """Inspect a Gaea .terrain JSON graph: nodes + output sinks (fast, offline)."""
        return _dump_graph(_confine(source))

    @mcp.tool()
    def verify_build(directory: str) -> dict[str, Any]:
        """Gate PNGs in a build dir by existence + size > 0. Returns report."""
        d = _confine(directory)
        if not d.is_dir():
            raise FileNotFoundError(d)
        pngs = sorted(d.glob("*.png"))
        return {"png_count": len(pngs), "files": [str(x.resolve()) for x in pngs]}

    @mcp.tool()
    def stage_example_for_export(
        source: str,
        variant_name: str,
        target_node_id: int | None = None,
        from_port: str = "Out",
        approval: str = "owner",
    ) -> dict[str, Any]:
        """Copy a stock Gaea example into the project and inject a PNG16 Export node.

        If target_node_id is omitted, State.SelectedNode is used when it is a sink;
        otherwise the highest-id sink is chosen. The resulting .terrain can be built
        immediately with build_terrain.
        """
        if authorize_tool is None:
            raise PermissionError("policy layer unavailable")
        decision = authorize_tool("gaea_stage_example_for_export", "mutate", approval)
        if not decision.get("allowed"):
            raise PermissionError(decision.get("reason", "policy denied stage"))
        src = _confine(source)
        if "examples" not in _normalise(str(src)):
            raise PermissionError("source must be a stock Gaea example")

        data = _load_terrain(src)
        sinks = _find_sink_nodes(data)
        terrain = _terrain(data)
        if target_node_id is None:
            selected = terrain.get("State", {}).get("SelectedNode")
            if selected and any(s["id"] == selected for s in sinks):
                target_node_id = selected
            elif sinks:
                target_node_id = sinks[-1]["id"]
            else:
                raise ValueError("no sink node found; pass target_node_id explicitly")

        raw = src.read_text(encoding="utf-8", errors="replace")
        export_name = f"{variant_name}_Height"
        inject = _inject_export_node_text(raw, target_node_id, from_port, export_name)

        dst_dir = SETUPS_DIR / variant_name
        dst_dir.mkdir(parents=True, exist_ok=True)
        dst = dst_dir / f"{variant_name}.terrain"
        dst.write_text(inject["raw"], encoding="utf-8")

        recipe = {
            "schema": "melodia.gaea_export_recipe.v1",
            "source": str(src.resolve()),
            "destination": str(dst.resolve()),
            "variant": variant_name,
            "target_node_id": target_node_id,
            "from_port": from_port,
            "export_node_id": inject["export_node_id"],
            "export_filename": export_name,
        }
        recipe_path = dst_dir / "export_recipe.json"
        recipe_path.write_text(json.dumps(recipe, indent=2, ensure_ascii=False), encoding="utf-8")

        return {
            "source": str(src.resolve()),
            "destination": str(dst.resolve()),
            "recipe": str(recipe_path.resolve()),
            "variant": variant_name,
            "target_node_id": target_node_id,
            "from_port": from_port,
            "export_node_id": inject["export_node_id"],
            "sinks": sinks,
            "policy": decision,
        }

    @mcp.tool()
    def build_terrain(
        source: str,
        buildpath: str,
        resolution: str | None = None,
        profile: str | None = None,
        vars_json: str | None = None,
        approval: str = "owner",
    ) -> dict[str, Any]:
        """Run Gaea Swarm headless to build source into buildpath."""
        if authorize_tool is None:
            raise PermissionError("policy layer unavailable")
        decision = authorize_tool("gaea_build_terrain", "mutate", approval)
        if not decision.get("allowed"):
            raise PermissionError(decision.get("reason", "policy denied build"))
        src = _confine(source)
        if "examples" in _normalise(str(src)):
            raise PermissionError("refusing to build over stock Gaea examples")
        dst = _confine(buildpath)
        dst.mkdir(parents=True, exist_ok=True)
        ps = (
            f"Start-Process -FilePath '{SWARM_EXE}' "
            f"-ArgumentList '--Filename', '\"{src}\"', '--buildpath', '\"{dst}\"', '--silent' "
            f"-Wait -NoNewWindow -RedirectStandardOutput '{dst}\\swarm_out.log' "
            f"-RedirectStandardError '{dst}\\swarm_err.log'"
        )
        proc = subprocess.run(
            ["powershell", "-NoProfile", "-ExecutionPolicy", "Bypass", "-Command", ps],
            capture_output=True,
            text=True,
            encoding="utf-8",
            errors="replace",
            timeout=1800,
        )
        produced = [p.name for p in dst.glob("*.png")]
        return {
            "exit": proc.returncode,
            "stdout_tail": proc.stdout[-1200:] if proc.stdout else "",
            "stderr_tail": proc.stderr[-800:] if proc.stderr else "",
            "produced": produced,
            "manifest_sha256": {n: _sha256(dst / n) for n in produced if (dst / n).is_file()},
        }

if __name__ == "__main__":
    if mcp is None:  # pragma: no cover
        raise SystemExit("mcp SDK not importable; cannot start server")
    mcp.run()
