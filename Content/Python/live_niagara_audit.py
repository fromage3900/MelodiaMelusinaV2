"""Live audit of all production Universal/Sakura/Ambient/Magical Aurora systems.

Read-only. Queries every /Game/EnvSandbox/VFX/Systems/*.uasset via Monolith
niagara_query and records per-system: emitters, renderers (type + material),
user params, diagnostics, and whether any renderer resolves to an Engine/Niagara
default material. Output written to Saved/Audit/live_niagara_audit.json.

Run from Python outside the editor (editor must be open with Monolith):
  py Content/Python/live_niagara_audit.py
"""
from __future__ import annotations

import json
from datetime import datetime, timezone
from pathlib import Path

try:
    import monolith_mcp_client as mcp
except ModuleNotFoundError:
    import sys
    sys.path.insert(0, str(Path(__file__).resolve().parent))
    import monolith_mcp_client as mcp

ROOT = Path(__file__).resolve().parents[2]
OUT = ROOT / "Saved" / "Audit" / "live_niagara_audit.json"

SYSTEMS_ROOT = "/Game/EnvSandbox/VFX/Systems"

SYSTEMS = [
    "NS_MagicTrail",
    "Ambient/NS_ConstellationTwinkle",
    "Ambient/NS_EmberMotes",
    "Ambient/NS_FairyDust",
    "Magical/NS_MagicalHenshinBurst",
    "Magical/NS_MagicTrail",
    "Sakura/NS_ConstellationDraw",
    "Sakura/NS_CosmicPetalOrbit",
    "Sakura/NS_SakuraCosmicAurora",
    "Sakura/NS_SakuraDreamSparkle",
    "Sakura/NS_SakuraGroundPetals",
    "Sakura/NS_SakuraLanternMotes",
    "Sakura/NS_SakuraPetalGust",
    "Sakura/NS_SakuraPetals",
    "Sakura/NS_SakuraPetals_v2",
    "Sakura/NS_SakuraPondShimmer",
    "Sakura/NS_SakuraWaterPetals",
    "Sakura/NS_SDF_Foliage_Bush",
    "Sakura/NS_SDF_Foliage_Grass",
    "Sakura/NS_SDF_Foliage_Vine",
    "Sakura/NS_SDF_ParallaxFish",
    "Sakura/NS_SDF_ParallaxPulse",
    "Sakura/NS_SDF_PulsingGeometry",
    "Sakura/NS_WindRibbonGust",
    "Universal/NS_Uni_DustShafts",
    "Universal/NS_Uni_Fireflies",
    "Universal/NS_Uni_GroundWisps",
    "Universal/NS_Uni_LeafDrift",
    "Universal/NS_Uni_MistSheet",
    "Universal/NS_Uni_PollenSparkle",
    "Universal/NS_Uni_RainRipples",
    "Universal/NS_Uni_WaterMist",
]

DEFAULT_MARKERS = (
    "niagara/defaultassets",
    "defaultsystem",
    "fountainlightweight",
    "minimallightweight",
    "radialburst",
    "directionalburst",
)


def _text(resp: dict) -> str:
    if isinstance(resp, dict) and "content" in resp:
        for block in resp.get("content") or []:
            if isinstance(block, dict) and block.get("type") == "text":
                return block["text"]
    return str(resp)


def get_summary(path: str) -> dict:
    try:
        raw = mcp.call_tool("niagara_query", {"action": "get_system_summary", "params": {"asset_path": path}})
        text = _text(raw)
        try:
            return json.loads(text)
        except json.JSONDecodeError:
            return {"raw": text}
    except Exception as exc:
        return {"error": str(exc)}


def get_emitters(path: str) -> list:
    try:
        raw = mcp.call_tool("niagara_query", {"action": "list_emitters", "params": {"asset_path": path}})
        text = _text(raw)
        try:
            return json.loads(text)
        except json.JSONDecodeError:
            return []
    except Exception:
        return []


def get_user_params(path: str) -> list:
    try:
        raw = mcp.call_tool("niagara_query", {"action": "get_user_parameters", "params": {"asset_path": path}})
        text = _text(raw)
        try:
            return json.loads(text)
        except json.JSONDecodeError:
            return []
    except Exception:
        return []


def get_emitter_renders(path: str, emitter: str) -> dict:
    try:
        raw = mcp.call_tool("niagara_query", {"action": "get_emitter_summary", "params": {"asset_path": path, "emitter": emitter}})
        text = _text(raw)
        try:
            return json.loads(text)
        except json.JSONDecodeError:
            return {"raw": text}
    except Exception as exc:
        return {"error": str(exc)}


def get_diagnostics(path: str) -> dict:
    try:
        raw = mcp.call_tool("niagara_query", {"action": "get_system_diagnostics", "params": {"asset_path": path}})
        text = _text(raw)
        try:
            return json.loads(text)
        except json.JSONDecodeError:
            return {"raw": text}
    except Exception as exc:
        return {"error": str(exc)}


def audit() -> dict:
    results = []
    for rel in SYSTEMS:
        path = f"{SYSTEMS_ROOT}/{rel}.{rel.rsplit('/', 1)[-1]}"
        entry = {"system": rel.rsplit('/', 1)[-1], "asset_path": path,
                 "summary": get_summary(path)}
        emitters = get_emitters(path)
        entry["emitters_list"] = emitters
        # Rich per-emitter detail (renderer materials, modules, sim target)
        rich = []
        sumy = entry.get("summary") or {}
        if isinstance(sumy, dict) and isinstance(sumy.get("emitters"), list):
            names = [e.get("name") for e in sumy["emitters"] if isinstance(e, dict) and e.get("name")]
        else:
            names = []
        for em_name in names:
            if em_name:
                rich.append({"emitter": em_name, "detail": get_emitter_renders(path, em_name)})
        entry["emitter_detail"] = rich
        entry["user_params"] = get_user_params(path)
        entry["diagnostics"] = get_diagnostics(path)
        results.append(entry)
    return results


def main() -> int:
    if not mcp.ping():
        print("ERROR: Monolith not reachable (editor closed?).")
        return 1
    data = audit()
    OUT.parent.mkdir(parents=True, exist_ok=True)
    OUT.write_text(json.dumps(data, indent=2), encoding="utf-8")
    # Summary line
    for e in data:
        sysn = e["system"]
        sumy = e.get("summary") or {}
        ems = sumy.get("emitters") if isinstance(sumy, dict) else None
        n = len(ems) if isinstance(ems, list) else "?"
        labels = []
        if isinstance(ems, list):
            for x in ems:
                if isinstance(x, dict):
                    labels.append(x.get("name") or "?")
        print(f"{sysn}: {n} emitters :: {', '.join(str(l) for l in labels[:6])}")
    print(f"\n-> {OUT}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())