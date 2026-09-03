"""Check material state for all 4 masters."""
from __future__ import annotations

import json
from pathlib import Path

import urllib.request
import unreal


def call(action: str, **kw) -> dict:
    payload = json.dumps(
        {"jsonrpc": "2.0", "id": 1, "method": "tools/call",
         "params": {"name": "material_query", "arguments": {"action": action, **kw}}}
    ).encode()
    req = urllib.request.Request("http://127.0.0.1:9316/mcp", data=payload,
                                  headers={"Content-Type": "application/json"})
    with urllib.request.urlopen(req, timeout=120) as r:
        env = json.loads(r.read().decode())
    return json.loads(env["result"]["content"][0]["text"])


ASSET = "/Game/EnvSandbox/Materials/Masters/M_Master_Toon_Universal"
MASTERS = [
    "/Game/EnvSandbox/Materials/Masters/M_Master_Toon_Universal",
    "/Game/EnvSandbox/Materials/Masters/M_Master_Landscape",
    "/Game/EnvSandbox/Materials/Masters/M_Master_Nikki",
    "/Game/EnvSandbox/Materials/Masters/M_Master_Nikki_Landscape",
]


def main() -> int:
    for m in MASTERS:
        cur = call("get_all_expressions", asset_path=m)
        val = call("validate_material", asset_path=m)
        stats = call("get_compilation_stats", asset_path=m)
        name = m.split("/")[-1]
        expr = cur["expression_count"]
        ps = stats.get("num_pixel_shader_instructions", "N/A")
        vs = stats.get("num_vertex_shader_instructions", "N/A")
        samps = stats.get("num_samplers", "N/A")
        errors = len([i for i in val["issues"] if i["severity"] == "error"])
        warnings = len([i for i in val["issues"] if i["severity"] == "warning"])
        print(f"{name}: expr={expr} PS={ps} VS={vs} samplers={samps} err={errors} warn={warnings}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())