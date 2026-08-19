"""Read-only baseline export of the four Melodia master materials.

Calls Monolith (http://127.0.0.1:9316/mcp) material_query to snapshot the live
on-disk state of:
  - M_Master_Toon_Universal
  - M_Master_Toon_Landscape_HeightBlend
  - M_Master_Nikki
  - M_Master_Nikki_Landscape

Writes JSON per asset to Saved/Audit/master_graphs_<timestamp>/.

Usage (repo-side, editor open):
  python Tools/export_master_graphs.py
"""
from __future__ import annotations

import json
import sys
import time
from datetime import datetime, timezone
from pathlib import Path
from urllib.error import URLError
from urllib.request import Request, urlopen

MONOLITH_URL = "http://127.0.0.1:9316/mcp"
PROJECT_ROOT = Path(__file__).resolve().parents[1]
OUT_DIR = PROJECT_ROOT / "Saved" / "Audit"

MASTERS = {
    "M_Master_Toon_Universal": "/Game/EnvSandbox/Materials/Masters/M_Master_Toon_Universal",
    "M_Master_Toon_Landscape_HeightBlend": "/Game/EnvSandbox/Materials/Masters/M_Master_Toon_Landscape_HeightBlend",
    "M_Master_Nikki": "/Game/EnvSandbox/Materials/Masters/M_Master_Nikki",
    "M_Master_Nikki_Landscape": "/Game/EnvSandbox/Materials/Masters/M_Master_Nikki_Landscape",
}


def call_tool(name: str, arguments: dict, timeout: int = 120) -> dict:
    payload = json.dumps({
        "jsonrpc": "2.0",
        "id": 1,
        "method": "tools/call",
        "params": {"name": name, "arguments": arguments},
    }).encode()
    req = Request(MONOLITH_URL, data=payload, headers={"Content-Type": "application/json"})
    with urlopen(req, timeout=timeout) as resp:
        envelope = json.loads(resp.read().decode())
    text = envelope.get("result", {}).get("content", [{}])[0].get("text", "")
    try:
        return json.loads(text)
    except (json.JSONDecodeError, TypeError):
        return {"raw": text}


def export_master(asset_path: str) -> dict:
    result: dict = {"asset_path": asset_path}
    for action in ("export_material_graph", "get_all_expressions", "get_material_parameters",
                   "validate_material", "get_compilation_stats"):
        for attempt in range(3):
            try:
                result[action] = call_tool("material_query", {"action": action, "asset_path": asset_path})
                break
            except (URLError, TimeoutError, OSError) as e:
                print(f"  retry {action} ({attempt + 1}): {e}", file=sys.stderr)
                time.sleep(3)
        else:
            result[action] = {"error": "monolith unreachable"}
    return result


def main() -> int:
    stamp = datetime.now(timezone.utc).strftime("%Y%m%d_%H%M%S")
    out_dir = OUT_DIR / f"master_graphs_{stamp}"
    out_dir.mkdir(parents=True, exist_ok=True)
    manifest: dict = {"timestamp": datetime.now(timezone.utc).isoformat()}
    for stem, path in MASTERS.items():
        print(f"Exporting {stem} ...")
        data = export_master(path)
        (out_dir / f"{stem}.json").write_text(json.dumps(data, indent=1), encoding="utf-8")
        manifest[stem] = {"asset_path": path, "file": f"{stem}.json"}
    (out_dir / "manifest.json").write_text(json.dumps(manifest, indent=1), encoding="utf-8")
    print(json.dumps({"out_dir": str(out_dir), "masters": list(MASTERS)}))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
