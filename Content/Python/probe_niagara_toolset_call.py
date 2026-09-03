"""Probe NiagaraToolset_System.call_method for add_emitter."""
from __future__ import annotations

import json
from pathlib import Path

import unreal

out: dict = {"methods_tried": []}
toolset = unreal.NiagaraToolset_System
for method in ("add_emitter", "AddEmitter", "create_system_from_emitter", "duplicate_emitter_to_system"):
    try:
        out["methods_tried"].append({"method": method, "has": hasattr(toolset, method)})
    except Exception as exc:
        out["methods_tried"].append({"method": method, "error": str(exc)})

# Try call_method if available
dest = "/Game/EnvSandbox/VFX/_Probe/NS_ProbeFromTemplate"
lib = __import__("material_lib")
lib.ensure_directory("/Game/EnvSandbox/VFX/_Probe")
if unreal.EditorAssetLibrary.does_asset_exist(dest):
    unreal.EditorAssetLibrary.delete_asset(dest)

asset_tools = unreal.AssetToolsHelpers.get_asset_tools()
factory = unreal.NiagaraSystemFactoryNew()
system = asset_tools.create_asset("NS_ProbeFromTemplate", "/Game/EnvSandbox/VFX/_Probe", unreal.NiagaraSystem, factory)
emitter = unreal.load_asset("/Niagara/DefaultAssets/Templates/Emitters/Fountain.Fountain")
out["system_created"] = system is not None
out["emitter_loaded"] = emitter is not None

if system and emitter:
    for method in ("add_emitter", "AddEmitter"):
        try:
            result = toolset.call_method(method, system, emitter, "ProbeEmitter")
            out[f"call_method_{method}"] = str(result)
        except Exception as exc:
            out[f"call_method_{method}"] = f"error: {exc}"

    # try set_editor_property on system
    try:
        handles = system.get_emitter_handles()
        out["initial_handles"] = len(handles)
    except Exception as exc:
        out["initial_handles"] = f"error: {exc}"

report = Path(__file__).resolve().parents[2] / "Saved" / "Audit" / "niagara_toolset_call_probe.json"
report.parent.mkdir(parents=True, exist_ok=True)
report.write_text(json.dumps(out, indent=2, default=str), encoding="utf-8")
print(json.dumps(out, indent=2, default=str))
