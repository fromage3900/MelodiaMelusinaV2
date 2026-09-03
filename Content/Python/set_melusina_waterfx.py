"""In-editor script: Apply Melusina WaterFX presets to Niagara systems and materials.

Runs inside UE 5.8 Python (Editor Utility Widget, Python Console, or editor_query:run_python).

Usage in UE editor (Python Console):
    exec(open("Content/Python/set_melusina_waterfx.py").read())

Usage via Monolith MCP:
    POST /mcp {"jsonrpc":"2.0","id":1,"method":"tools/call",
               "params":{"name":"editor_query","arguments":{"action":"run_python","script":open("Content/Python/set_melusina_waterfx.py").read()}}}

Functions:
    apply_preset(name) — apply a preset by name: 'subtle_drip', 'moderate_splash', 'heavy_water', 'dry', 'magical_glow'
    apply_waterfx_params(params) — directly set WaterFX emitter parameters from a dict
    apply_mist_params(params) — directly set WaterMist parameters
    set_water_hair_preset(name) — apply water hair material preset
    read_waterfx_config() — print current Niagara emitter config
"""
from __future__ import annotations

import json
import sys
from pathlib import Path

import unreal

# ── Asset paths ──────────────────────────────────────────────────────────────

WATERFX_PATH = "/Game/Melodia/VFX/Melusina_WaterFX"
WATERMIST_PATH = "/Game/EnvSandbox/VFX/Systems/NS_Uni_WaterMist"
WATER_HAIR_MI_PATH = "/Game/EnvSandbox/Materials/Instances/Melusina/MI_Melusina_WaterHair"
MPC_PALETTE_PATH = "/Game/Melodia/_PROJECT/04_Materials/MPC_Melodia_Palette"
PROJECT_ROOT = Path(__file__).resolve().parents[2]

# ── Water hair material presets ──────────────────────────────────────────────

WATER_HAIR_PRESETS = {
    "subtle_drip": {
        "HairDripIntensity": 0.35, "SplashForce": 0.25, "WaterOpacity": 0.72,
        "WaterRoughness": 0.28, "MagicalIntensity": 0.15, "CausticIntensity": 0.08,
        "DripSpeed": 0.2, "DripLength": 0.08,
    },
    "moderate_splash": {
        "HairDripIntensity": 0.55, "SplashForce": 0.65, "WaterOpacity": 0.82,
        "WaterRoughness": 0.22, "MagicalIntensity": 0.18, "CausticIntensity": 0.12,
        "DripSpeed": 0.3, "DripLength": 0.12,
    },
    "heavy_water": {
        "HairDripIntensity": 0.85, "SplashForce": 1.2, "WaterOpacity": 0.95,
        "WaterRoughness": 0.15, "MagicalIntensity": 0.25, "CausticIntensity": 0.2,
        "DripSpeed": 0.5, "DripLength": 0.2,
    },
    "dry": {
        "HairDripIntensity": 0.0, "SplashForce": 0.0, "WaterOpacity": 0.0,
        "WaterRoughness": 0.4, "MagicalIntensity": 0.0, "CausticIntensity": 0.0,
        "DripSpeed": 0.0, "DripLength": 0.0,
    },
    "magical_glow": {
        "HairDripIntensity": 0.2, "SplashForce": 0.1, "WaterOpacity": 0.4,
        "WaterRoughness": 0.35, "MagicalIntensity": 0.5, "CausticIntensity": 0.3,
        "DripSpeed": 0.1, "DripLength": 0.05,
    },
}

# ── WaterFX Day 1 default params ─────────────────────────────────────────────

WATERFX_DAY1 = {
    "WaterSplashEmitter": {
        "SpawnRate": 60.0, "Lifetime": 1.8, "SplashForce": 0.25,
        "DropletDensity": 0.35, "GravityScale": 0.55, "DragCoefficient": 3.0,
        "CollisionRadius": 0.015, "SurfaceTension": 0.25, "Viscosity": 0.12,
    },
    "WaterSheetEmitter": {
        "SpawnRate": 15.0, "Lifetime": 0.6, "SheetWidth": 0.08, "SheetForce": 0.1,
    },
}

WATERMIST_DAY1 = {
    "SpawnRate": 25.0, "Lifetime": 4.0, "MistOpacity": 0.18,
    "MistScale": 1.5, "DriftSpeed": 0.05,
}


# ── Helpers ──────────────────────────────────────────────────────────────────

def _set_scalar(mi: unreal.MaterialInstanceConstant, name: str, value: float) -> bool:
    try:
        unreal.MaterialEditingLibrary.set_material_instance_scalar_parameter_value(mi, name, value)
        return True
    except Exception as e:
        print(f"  [WARN] Could not set {name}={value}: {e}")
        return False


def _set_niagara_param(
    ns: unreal.NiagaraSystem, emitter_name: str, param_name: str, value: float | bool | str
) -> bool:
    emitters = ns.get_editor_property("emitter_handles") or []
    target = None
    for e in emitters:
        if e and e.get_editor_property("emitter_name") == emitter_name:
            target = e
            break
    if not target:
        print(f"  [WARN] Emitter '{emitter_name}' not found")
        return False

    user_params = ns.get_editor_property("user_parameters") or {}
    if param_name in user_params:
        try:
            user_params[param_name].set_value(value)
            return True
        except Exception:
            pass

    try:
        script_params = target.get_editor_property("script_parameters") or []
        for sp in script_params:
            name = sp.get_editor_property("name") if hasattr(sp, "get_editor_property") else str(sp)
            if name == param_name:
                sp.set_editor_property("value", value)
                return True
    except Exception:
        pass

    print(f"  [WARN] Parameter '{param_name}' not found on emitter '{emitter_name}'")
    return False


def _get_emitter(ns: unreal.NiagaraSystem, name: str):
    emitters = ns.get_editor_property("emitter_handles") or []
    for e in emitters:
        if e and e.get_editor_property("emitter_name") == name:
            return e
    return None


# ── Public API ───────────────────────────────────────────────────────────────

def apply_waterfx_params(params: dict[str, dict[str, float]], save: bool = True) -> dict:
    """Set emitter parameters on Melusina_WaterFX from a dict of {emitter: {param: value}}."""
    ns = unreal.load_asset(WATERFX_PATH)
    if not ns:
        return {"ok": False, "error": f"Could not load {WATERFX_PATH}"}

    results = {}
    for emitter_name, emitter_params in params.items():
        emitter_results = {}
        for param_name, value in emitter_params.items():
            ok = _set_niagara_param(ns, emitter_name, param_name, value)
            emitter_results[param_name] = "OK" if ok else "FAIL"
        results[emitter_name] = emitter_results

    if save:
        unreal.EditorAssetLibrary.save_loaded_asset(ns, only_if_is_dirty=False)

    print(f"[WaterFX] Applied params: {json.dumps(results, indent=2)}")
    return {"ok": True, "results": results}


def apply_mist_params(params: dict[str, float], save: bool = True) -> dict:
    """Set parameters on NS_Uni_WaterMist from a dict of {param: value}."""
    ns = unreal.load_asset(WATERMIST_PATH)
    if not ns:
        return {"ok": False, "error": f"Could not load {WATERMIST_PATH}"}

    emitter = _get_emitter(ns, "WaterMist")
    if not emitter:
        return {"ok": False, "error": "WaterMist emitter not found"}

    results = {}
    for param_name, value in params.items():
        ok = _set_niagara_param(ns, "WaterMist", param_name, value)
        results[param_name] = "OK" if ok else "FAIL"

    if save:
        unreal.EditorAssetLibrary.save_loaded_asset(ns, only_if_is_dirty=False)

    print(f"[WaterMist] Applied params: {json.dumps(results, indent=2)}")
    return {"ok": True, "results": results}


def set_water_hair_preset(preset_name: str, save: bool = True) -> dict:
    """Apply a named water hair material preset."""
    params = WATER_HAIR_PRESETS.get(preset_name)
    if not params:
        return {"ok": False, "error": f"Unknown preset: {preset_name}. Options: {list(WATER_HAIR_PRESETS.keys())}"}

    mi = unreal.load_asset(WATER_HAIR_MI_PATH)
    if not mi:
        return {"ok": False, "error": f"Could not load {WATER_HAIR_MI_PATH}"}

    results = {}
    for param_name, value in params.items():
        ok = _set_scalar(mi, param_name, value)
        results[param_name] = "OK" if ok else "FAIL"

    if save:
        unreal.EditorAssetLibrary.save_loaded_asset(mi, only_if_is_dirty=False)

    print(f"[WaterHair] Preset '{preset_name}': {json.dumps(results, indent=2)}")
    return {"ok": True, "preset": preset_name, "results": results}


def apply_preset(name: str = "subtle_drip", save: bool = True) -> dict:
    """Apply a complete set of presets across all Melusina water VFX systems.

    name: one of 'subtle_drip', 'moderate_splash', 'heavy_water', 'dry', 'magical_glow'
    """
    print(f"[WaterFX] Applying full preset: {name}")
    result = {}

    hair_result = set_water_hair_preset(name, save=save)
    result["water_hair"] = hair_result

    if name == "dry":
        fx_params = {e: {p: 0.0 for p in params} for e, params in WATERFX_DAY1.items()}
        mist_params = {p: 0.0 for p in WATERMIST_DAY1}
    else:
        fx_params = WATERFX_DAY1
        if name == "moderate_splash":
            fx_params["WaterSplashEmitter"]["SplashForce"] = 0.65
            fx_params["WaterSplashEmitter"]["DropletDensity"] = 0.75
        elif name == "heavy_water":
            fx_params["WaterSplashEmitter"]["SplashForce"] = 1.5
            fx_params["WaterSplashEmitter"]["DropletDensity"] = 1.0
            fx_params["WaterSplashEmitter"]["SpawnRate"] = 200.0
        elif name == "magical_glow":
            fx_params["WaterSplashEmitter"]["SplashForce"] = 0.1
            fx_params["WaterSplashEmitter"]["DropletDensity"] = 0.2

        mist_params = dict(WATERMIST_DAY1)
        if name == "moderate_splash":
            mist_params["MistOpacity"] = 0.35
        elif name == "heavy_water":
            mist_params["MistOpacity"] = 0.6
            mist_params["SpawnRate"] = 60.0
        elif name == "magical_glow":
            mist_params["MistOpacity"] = 0.5

    fx_result = apply_waterfx_params(fx_params, save=save)
    result["waterfx"] = fx_result

    mist_result = apply_mist_params(mist_params, save=save)
    result["watermist"] = mist_result

    print(f"[WaterFX] Preset '{name}' applied.")
    return result


def read_waterfx_config() -> dict | None:
    """Read current WaterFX emitter config and print it."""
    ns = unreal.load_asset(WATERFX_PATH)
    if not ns:
        print(f"ERROR: Could not load {WATERFX_PATH}")
        return None

    result = {"system_path": WATERFX_PATH, "emitters": []}
    emitters = ns.get_editor_property("emitter_handles") or []
    for e in emitters:
        entry = {"name": str(e.get_editor_property("emitter_name") if e else "unknown")}
        try:
            user_params = ns.get_editor_property("user_parameters") or {}
            entry["user_parameters"] = {str(k): str(v) for k, v in user_params.items()}
        except Exception as exc:
            entry["user_params_error"] = str(exc)
        try:
            script_params = e.get_editor_property("script_parameters") or []
            entry["script_parameters"] = []
            for sp in script_params:
                name = sp.get_editor_property("name") if hasattr(sp, "get_editor_property") else str(sp)
                val = sp.get_editor_property("value") if hasattr(sp, "get_editor_property") else None
                entry["script_parameters"].append({"name": str(name), "value": str(val)})
        except Exception as exc:
            entry["script_params_error"] = str(exc)
        try:
            modules = e.get_editor_property("emitter_modules") or []
            entry["modules"] = [str(m.get_class().get_name()) for m in modules if m]
        except Exception:
            pass
        result["emitters"].append(entry)

    print(json.dumps(result, indent=2))
    return result


def read_mist_config() -> dict | None:
    """Read current WaterMist emitter config."""
    ns = unreal.load_asset(WATERMIST_PATH)
    if not ns:
        print(f"ERROR: Could not load {WATERMIST_PATH}")
        return None

    result = {"system_path": WATERMIST_PATH, "emitters": []}
    emitters = ns.get_editor_property("emitter_handles") or []
    for e in emitters:
        entry = {"name": str(e.get_editor_property("emitter_name") if e else "unknown")}
        try:
            user_params = ns.get_editor_property("user_parameters") or {}
            entry["user_parameters"] = {str(k): str(v) for k, v in user_params.items()}
        except Exception:
            pass
        result["emitters"].append(entry)

    print(json.dumps(result, indent=2))
    return result


# ── Main (when run directly in UE console) ──────────────────────────────────

if __name__ == "__main__":
    args = sys.argv[1:] if hasattr(sys, "argv") else []
    if not args or args[0] in ("--help", "-h"):
        print(__doc__)
        print("\nCommands:")
        print("  apply_preset('subtle_drip')  # or moderate_splash, heavy_water, dry, magical_glow")
        print("  read_waterfx_config()")
        print("  read_mist_config()")
        print("  set_water_hair_preset('subtle_drip')")
    elif args[0] == "read_config":
        read_waterfx_config()
        read_mist_config()
    else:
        preset_name = args[0] if args[0] in WATER_HAIR_PRESETS else "subtle_drip"
        apply_preset(preset_name)
