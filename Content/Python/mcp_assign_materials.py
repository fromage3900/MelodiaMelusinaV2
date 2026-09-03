"""Assign sprite MIs to Sakura Niagara system renderers via Monolith MCP.

Run in-editor with MCP at http://127.0.0.1:9316/mcp
"""
from __future__ import annotations

import json
import urllib.request
from pathlib import Path

MCP_URL = "http://127.0.0.1:9316/mcp"
SAKURA = "/Game/EnvSandbox/VFX/Systems/Sakura"
MATS = "/Game/EnvSandbox/VFX/Materials"

# Full paths including UE asset name suffix
SYSTEM_RENDERER_MAP = [
    ("NS_SakuraPetals", "CanopyDrift", 0, f"{MATS}/MI_Niagara_Petal.MI_Niagara_Petal"),
    ("NS_SakuraPetals_v2", "Petals", 0, f"{MATS}/MI_Niagara_Petal.MI_Niagara_Petal"),
    ("NS_SakuraPetals_v2", "Petals", 1, f"{MATS}/MI_Niagara_Petal.MI_Niagara_Petal"),
    ("NS_SakuraGroundPetals", "GroundPetals", 0, f"{MATS}/MI_Niagara_Petal.MI_Niagara_Petal"),
    ("NS_SakuraDreamSparkle", "DreamMotes", 0, f"{MATS}/MI_Niagara_Sparkle.MI_Niagara_Sparkle"),
    ("NS_SakuraLanternMotes", "LanternMotes", 0, f"{MATS}/MI_Niagara_Mote.MI_Niagara_Mote"),
    ("NS_SakuraPondShimmer", "Ripples", 0, f"{MATS}/MI_Niagara_Pond.MI_Niagara_Pond"),
    ("NS_SakuraWaterPetals", "GroundPetals", 0, f"{MATS}/MI_Niagara_Petal.MI_Niagara_Petal"),
]


def _mcp_call(method: str, params: dict | None = None, timeout: int = 15) -> dict:
    payload = {"jsonrpc": "2.0", "id": 1, "method": method, "params": params or {}}
    req = urllib.request.Request(
        MCP_URL, data=json.dumps(payload).encode(),
        headers={"Content-Type": "application/json"},
    )
    try:
        with urllib.request.urlopen(req, timeout=timeout) as resp:
            return json.loads(resp.read().decode())
    except Exception as exc:
        return {"error": str(exc)}


def niagara(action: str, params: dict, timeout: int = 15) -> dict:
    result = _mcp_call("tools/call", {
        "name": "niagara_query",
        "arguments": {"action": action, "params": params},
    }, timeout=timeout)
    try:
        text = result.get("result", {}).get("content", [{}])[0].get("text", "{}")
        return json.loads(text)
    except Exception:
        return result


def main():
    # Step 1: Set materials
    for sys_name, emitter, rend_idx, mat_path in SYSTEM_RENDERER_MAP:
        asset = f"{SAKURA}/{sys_name}"
        result = niagara("set_renderer_material", {
            "asset_path": asset,
            "emitter": emitter,
            "renderer": rend_idx,
            "material": mat_path,
        })
        ok = "error" not in result
        status = "OK" if ok else f"FAIL: {result.get('error', str(result))[:100]}"
        print(f"SET {sys_name}/{emitter}[{rend_idx}] -> {mat_path}: {status}")

    # Step 2: Compile all
    print()
    for sys_name, _, _, _ in SYSTEM_RENDERER_MAP:
        asset = f"{SAKURA}/{sys_name}"
        niagara("request_compile", {"asset_path": asset})
        print(f"COMPILE {sys_name}")

    # Step 3: Save all
    print()
    for sys_name, _, _, _ in SYSTEM_RENDERER_MAP:
        asset = f"{SAKURA}/{sys_name}"
        r = niagara("save_system", {"asset_path": asset,
                                     "only_if_dirty": False})
        status = "OK" if "error" not in r else f"FAIL: {r.get('error', str(r))[:100]}"
        print(f"SAVE   {sys_name}: {status}")

    # Step 4: Verify
    print()
    print("=== Verify Renderer Materials ===")
    for sys_name, emitter, rend_idx, mat_path in SYSTEM_RENDERER_MAP:
        asset = f"{SAKURA}/{sys_name}"
        r = niagara("list_renderers", {"asset_path": asset, "emitter": emitter})
        renderers = r.get("renderers", [])
        for rend in renderers:
            if rend.get("index") == rend_idx:
                rm = rend.get("material", "NONE") or ""
                ok = mat_path in rm or mat_path.replace(".", "/")[-1] in rm
                match = "OK" if ok else "MISMATCH"
                print(f"  {match}: {sys_name}/{emitter}[{rend_idx}] -> {rm}")


if __name__ == "__main__":
    main()
