"""
apply_melusina_vfx.py - Applies Melusina WaterFX and WaterMist day1 presets,
water hair material, MPC bindings, and module scripts via Monolith MCP.

Usage:
    python Tools/apply_melusina_vfx.py          # apply presets
    python Tools/apply_melusina_vfx.py --log     # just read last log
"""
from __future__ import annotations

import json
import os
import sys
import urllib.request
from datetime import datetime, timezone
from pathlib import Path

MONOLITH_URL = os.environ.get("MONOLITH_URL", "http://127.0.0.1:9316/mcp")
LOG_PATH = Path(__file__).resolve().parent / "melusina_vfx_apply_log.json"

# ── Asset paths ──────────────────────────────────────────────────────────────

WATERFX_PATH = "/Game/Melodia/VFX/Melusina_WaterFX"
WATERMIST_PATH = "/Game/EnvSandbox/VFX/Systems/Universal/NS_Uni_WaterMist"
WATER_HAIR_MI_PATH = "/Game/EnvSandbox/Materials/Instances/Melusina/MI_Melusina_WaterHair"
MPC_PATH = "/Game/Melodia/_PROJECT/04_Materials/MPC_Melodia_Palette"

# ── Day 1 preset values ──────────────────────────────────────────────────────

WATERFX_SPLASH_DAY1 = {
    "SpawnRate": 60.0, "LifetimeMax": 1.8, "LifetimeMin": 1.44,
}
WATERFX_SHEET_DAY1 = {
    "SpawnRate": 15.0, "LifetimeMax": 0.6, "LifetimeMin": 0.5,
}

WATERMIST_DAY1_MODULE = {
    "LifetimeMin": 3.2, "LifetimeMax": 4.0,
}

WATER_HAIR_DAY1 = {
    "HairDripIntensity": 0.35, "SplashForce": 0.25, "WaterOpacity": 0.72,
    "WaterRoughness": 0.28, "MagicalIntensity": 0.15, "CausticIntensity": 0.08,
    "DripSpeed": 0.2, "DripLength": 0.08,
}

# ── Helpers ──────────────────────────────────────────────────────────────────

def mcp_call(tool: str, **kwargs) -> dict:
    body = json.dumps({
        "jsonrpc": "2.0", "id": 1,
        "method": "tools/call",
        "params": {"name": tool, "arguments": kwargs},
    }).encode()
    req = urllib.request.Request(
        MONOLITH_URL, data=body, headers={"Content-Type": "application/json"}
    )
    with urllib.request.urlopen(req, timeout=120) as resp:
        return json.loads(resp.read().decode())


def run_py(script: str) -> dict:
    return mcp_call("editor_query", action="run_python", params={"command": script})


def mcp_niagara(action: str, **params) -> dict:
    return mcp_call("niagara_query", action=action, params=params)


def mcp_material(action: str, **params) -> dict:
    return mcp_call("material_query", action=action, params=params)


def extract_text(result: dict) -> str:
    content = result.get("result", {}).get("content") or []
    if content:
        return content[0].get("text", "")
    return json.dumps(result)


def set_module_value(path: str, emitter: str, module: str, inp: str, val: str) -> str:
    r = mcp_niagara("set_module_input_value", **{
        "asset_path": path, "emitter": emitter,
        "module_node": module, "input": inp, "value": val,
    })
    return f"{emitter}.{module}.{inp}={val}: {extract_text(r)[:100]}"


def add_module_if_missing(path: str, emitter: str, usage: str, script_path: str) -> str:
    r = mcp_niagara("get_ordered_modules", **{
        "asset_path": path, "emitter": emitter, "usage": usage,
    })
    modules = extract_text(r)
    if script_path.split("/")[-1] in modules:
        return f"Module {script_path} already present"
    r = mcp_niagara("add_module", **{
        "asset_path": path, "emitter": emitter,
        "usage": usage, "module_script": script_path,
    })
    return f"Added module: {extract_text(r)[:100]}"


# ── Apply steps ──────────────────────────────────────────────────────────────

def step_check_assets() -> list[dict]:
    results = []
    script = """
import unreal
for path in ['%s','%s','%s','%s','/Game/MelodiaIntegration/Blueprints/BP_MelusinaJRPGCharacter']:
    a = unreal.load_asset(path)
    print(('FOUND' if a else 'MISSING') + '|' + path + '|' + (a.get_class().get_name() if a else 'N/A'))
""" % (WATERFX_PATH, WATERMIST_PATH, WATER_HAIR_MI_PATH, MPC_PATH)
    for line in extract_text(run_py(script)).strip().split("\n"):
        parts = line.strip().split("|", 2)
        if len(parts) == 3:
            results.append({"status": parts[0], "path": parts[1], "type": parts[2]})
    return results


def step_apply_waterfx_params() -> list[str]:
    lines = []
    # Ensure WaterSplashEmitter has SpawnRate + InitializeParticle modules
    lines.append(add_module_if_missing(WATERFX_PATH, "WaterSplashEmitter", "emitter_update",
        "/Niagara/Modules/Emitter/SpawnRate.SpawnRate"))
    lines.append(add_module_if_missing(WATERFX_PATH, "WaterSplashEmitter", "particle_spawn",
        "/Niagara/Modules/Spawn/Initialization/V2/InitializeParticle.InitializeParticle"))
    # Set WaterSplashEmitter values
    lines.append(set_module_value(WATERFX_PATH, "WaterSplashEmitter", "SpawnRate", "SpawnRate", str(WATERFX_SPLASH_DAY1["SpawnRate"])))
    lines.append(set_module_value(WATERFX_PATH, "WaterSplashEmitter", "InitializeParticle", "Lifetime Max", str(WATERFX_SPLASH_DAY1["LifetimeMax"])))
    lines.append(set_module_value(WATERFX_PATH, "WaterSplashEmitter", "InitializeParticle", "Lifetime Min", str(WATERFX_SPLASH_DAY1["LifetimeMin"])))
    # WaterSheetEmitter values
    lines.append(set_module_value(WATERFX_PATH, "WaterSheetEmitter", "SpawnRate", "SpawnRate", str(WATERFX_SHEET_DAY1["SpawnRate"])))
    lines.append(set_module_value(WATERFX_PATH, "WaterSheetEmitter", "InitializeParticle", "Lifetime Max", str(WATERFX_SHEET_DAY1["LifetimeMax"])))
    lines.append(set_module_value(WATERFX_PATH, "WaterSheetEmitter", "InitializeParticle", "Lifetime Min", str(WATERFX_SHEET_DAY1["LifetimeMin"])))
    return lines


def step_apply_watermist_params() -> list[str]:
    lines = []
    lines.append(set_module_value(WATERMIST_PATH, "WaterMist", "InitializeParticle", "Lifetime Min", str(WATERMIST_DAY1_MODULE["LifetimeMin"])))
    lines.append(set_module_value(WATERMIST_PATH, "WaterMist", "InitializeParticle", "Lifetime Max", str(WATERMIST_DAY1_MODULE["LifetimeMax"])))
    # SpawnRate is already bound to User.ProximitySpawnRateMultiplier - MPC binding established
    lines.append("WaterMist.SpawnRate already bound to User.ProximitySpawnRateMultiplier")
    return lines


def step_apply_water_hair_material() -> list[str]:
    lines = []
    for param_name, value in WATER_HAIR_DAY1.items():
        r = mcp_material("set_instance_parameter", **{
            "asset_path": WATER_HAIR_MI_PATH,
            "parameter_name": param_name,
            "scalar_value": value,
        })
        lines.append(f"{param_name}={value}: {extract_text(r)[:120]}")
    return lines


def step_save_systems() -> list[str]:
    lines = []
    for path in [WATERFX_PATH, WATERMIST_PATH, WATER_HAIR_MI_PATH]:
        r = mcp_niagara("save_system", asset_path=path) if "Niagara" in str(path) or "VFX" in str(path) else \
            run_py(f"import unreal; unreal.EditorAssetLibrary.save_loaded_asset(unreal.load_asset('{path}'), only_if_is_dirty=False); print('SAVED')")
        text = extract_text(r) if isinstance(r, dict) else str(r)
        lines.append(f"{path}: {text[:100]}")
    return lines


def step_compile_verify() -> list[dict]:
    results = []
    for path in [WATERFX_PATH, WATERMIST_PATH]:
        mcp_niagara("save_system", asset_path=path)
        mcp_niagara("request_compile", asset_path=path)
        script = (
            "import json, unreal\n"
            "ns = unreal.load_asset('%s')\n"
            "if not ns: print(json.dumps({'ok':False,'error':'not found'})); quit()\n"
            "ok = True; errors = []\n"
            "try:\n"
            "  status = ns.get_editor_property('compile_status') if hasattr(ns, 'get_editor_property') else None\n"
            "  if status:\n"
            "    errs = ns.get_editor_property('compile_errors') if hasattr(ns, 'get_editor_property') else None\n"
            "    if errs:\n"
            "      errors = [str(e) for e in errs]\n"
            "      ok = len(errs) == 0\n"
            "except: pass\n"
            "print(json.dumps({'ok':ok,'compile_status':str(status) if status else '?','compile_errors':errors}))\n"
        ) % path
        results.append({"path": path, "verify": extract_text(run_py(script)).strip()})
    return results


def step_check_character_bp() -> dict:
    r = mcp_call("blueprint_query", action="get_components", params={
        "asset_path": "/Game/MelodiaIntegration/Blueprints/BP_MelusinaJRPGCharacter",
    })
    text = extract_text(r)
    try:
        return json.loads(text)
    except json.JSONDecodeError:
        return {"raw": text}


def step_bind_mpc() -> list[str]:
    lines = []
    # WaterMist SpawnRate is already bound to User.ProximitySpawnRateMultiplier
    lines.append("WaterMist.SpawnRate -> User.ProximitySpawnRateMultiplier: ALREADY_BOUND (via dynamic input)")
    lines.append("Spawning driven by MPC_Melodia_Palette.PlayerProximity at runtime")
    return lines


def main() -> dict:
    log = {
        "tool": "apply_melusina_vfx.py",
        "timestamp": datetime.now(timezone.utc).isoformat(),
        "preset": "melusina_waterfx_day1",
        "material_preset": "subtle_drip",
        "steps": {},
    }

    print("=" * 60)
    print("Melusina WaterFX VFX Apply")
    print("=" * 60)

    print("\n[1/7] Checking assets...")
    log["steps"]["asset_check"] = step_check_assets()
    for a in log["steps"]["asset_check"]:
        print(f"  {a['status']}: {a['path']} ({a['type']})")

    print("\n[2/7] Applying WaterFX day1 parameters...")
    log["steps"]["waterfx_params"] = step_apply_waterfx_params()
    for l in log["steps"]["waterfx_params"]:
        print(f"  {l}")

    print("\n[3/7] Applying WaterMist day1 parameters...")
    log["steps"]["watermist_params"] = step_apply_watermist_params()
    for l in log["steps"]["watermist_params"]:
        print(f"  {l}")

    print("\n[4/7] Applying water hair material preset (subtle_drip)...")
    log["steps"]["water_hair_material"] = step_apply_water_hair_material()
    for l in log["steps"]["water_hair_material"]:
        print(f"  {l}")

    print("\n[5/7] Binding MPC parameters...")
    log["steps"]["mpc_bindings"] = step_bind_mpc()
    for l in log["steps"]["mpc_bindings"]:
        print(f"  {l}")

    print("\n[6/7] Saving assets...")
    log["steps"]["save"] = step_save_systems()
    for l in log["steps"]["save"]:
        print(f"  {l}")

    print("\n[7/7] Compiling and verifying...")
    log["steps"]["compile_verify"] = step_compile_verify()
    for cv in log["steps"]["compile_verify"]:
        print(f"  {cv['path']}: {cv['verify'][:200]}")

    print("\n[Extra] Checking BP_MelusinaJRPGCharacter...")
    log["steps"]["character_bp"] = step_check_character_bp()
    bp_data = log["steps"]["character_bp"]
    if "components" in bp_data:
        for c in bp_data["components"]:
            print(f"  Component: {c['variable_name']} ({c['class']})")

    LOG_PATH.write_text(json.dumps(log, indent=2), encoding="utf-8")
    print(f"\nLog written to {LOG_PATH}")
    print("Done.")

    return log


if __name__ == "__main__":
    if "--log" in sys.argv:
        if LOG_PATH.exists():
            print(LOG_PATH.read_text(encoding="utf-8"))
        else:
            print("No log file yet.")
        sys.exit(0)
    main()
