"""Compile and bind ZenForestTest Niagara renderers through the live editor MCP."""
from __future__ import annotations

import json
import urllib.request
from pathlib import Path

MCP_URL = "http://127.0.0.1:9316/mcp"
ROOT = Path("G:/EnvironmentPortfolio/BS_GodFile")
REPORT = ROOT / "Saved/Audit/zenforest_niagara_mcp.json"
SYSTEM_ROOT = "/Game/EnvSandbox/VFX/Systems/Sakura"
MATERIAL_ROOT = "/Game/EnvSandbox/VFX/Materials"
SYSTEMS = (
    ("NS_SakuraPetals_v2", "MI_Niagara_Petal_Instance"),
    ("NS_SakuraGroundPetals", "MI_Niagara_Petal_Instance"),
    ("NS_SakuraPetalGust", "MI_Niagara_Gust_Instance"),
    ("NS_SakuraWaterPetals", "MI_Niagara_Petal_Instance"),
    ("NS_CosmicPetalOrbit", "MI_Niagara_NebulaPetal"),
    ("NS_SakuraCosmicAurora", "MI_Niagara_AuroraRibbon"),
)


def material_name_from_path(value: str) -> str:
    return value.rsplit("/", 1)[-1].rsplit(".", 1)[-1] if value else ""


def call(action: str, params: dict) -> dict:
    payload = {"jsonrpc": "2.0", "id": 1, "method": "tools/call", "params": {"name": "niagara_query", "arguments": {"action": action, "params": params}}}
    req = urllib.request.Request(MCP_URL, data=json.dumps(payload).encode(), headers={"Content-Type": "application/json"})
    with urllib.request.urlopen(req, timeout=30) as response:
        outer = json.loads(response.read().decode())
    text = outer.get("result", {}).get("content", [{}])[0].get("text", "{}")
    if not isinstance(text, str):
        return text
    try:
        return json.loads(text)
    except json.JSONDecodeError:
        return {"raw": text}


def main() -> int:
    report = {"systems": [], "errors": []}
    for system_name, material_name in SYSTEMS:
        system_path = f"{SYSTEM_ROOT}/{system_name}"
        material_path = f"{MATERIAL_ROOT}/{material_name}.{material_name}"
        entry = {"system": system_name, "material": material_path, "assignments": [], "readback": [], "compile": None, "diagnostics": None, "save": None}
        try:
            emitters = call("list_emitters", {"asset_path": system_path})
            emitter_rows = emitters.get("result", emitters.get("emitters", []))
            if not isinstance(emitter_rows, list):
                emitter_rows = []
            for emitter in emitter_rows:
                emitter_name = emitter.get("name", emitter) if isinstance(emitter, dict) else str(emitter)
                renderers = call("list_renderers", {"asset_path": system_path, "emitter": emitter_name})
                rows = renderers.get("result", renderers.get("renderers", []))
                if not isinstance(rows, list):
                    continue
                for renderer in rows:
                    index = renderer.get("index", 0)
                    result = call("set_renderer_material", {"asset_path": system_path, "emitter": emitter_name, "renderer_index": int(index), "material": material_path})
                    entry["assignments"].append({"emitter": emitter_name, "renderer": index, "result": result})
            entry["compile"] = call("request_compile", {"asset_path": system_path})
            entry["diagnostics"] = call("get_system_diagnostics", {"asset_path": system_path})
            entry["save"] = call("save_system", {"asset_path": system_path, "only_if_dirty": False})
            emitters = call("list_emitters", {"asset_path": system_path})
            emitter_rows = emitters.get("emitters", [])
            for emitter in emitter_rows if isinstance(emitter_rows, list) else []:
                emitter_name = emitter.get("name", emitter) if isinstance(emitter, dict) else str(emitter)
                renderers = call("list_renderers", {"asset_path": system_path, "emitter": emitter_name})
                rows = renderers.get("renderers", [])
                for renderer in rows if isinstance(rows, list) else []:
                    entry["readback"].append({
                        "emitter": emitter_name,
                        "renderer": renderer.get("index", 0),
                        "material": renderer.get("material"),
                    })
        except Exception as exc:
            entry["error"] = str(exc)
            report["errors"].append(f"{system_name}: {exc}")
        report["systems"].append(entry)
    report["ok"] = not report["errors"] and all(
        s["compile"] is not None and s["diagnostics"] is not None and not s["diagnostics"].get("has_issues", True) and s["save"] is not None and
        all("error" not in a["result"] and "raw" not in a["result"] for a in s["assignments"]) and
        all(a.get("material") == s["material"] for a in s["readback"])
        for s in report["systems"]
    )
    REPORT.parent.mkdir(parents=True, exist_ok=True)
    REPORT.write_text(json.dumps(report, indent=2), encoding="utf-8")
    print(json.dumps(report, indent=2))
    return 0 if report["ok"] else 1


if __name__ == "__main__":
    raise SystemExit(main())
