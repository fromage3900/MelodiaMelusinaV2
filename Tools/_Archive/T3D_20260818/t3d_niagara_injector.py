#!/usr/bin/env python3
"""
T3D Niagara Module Injector - injects Niagara parameter changes, module scripts,
and MPC bindings via Monolith MCP in a single transaction.

Targets the `niagara_query:add_module`, `editor_query:run_python`, and
`material_query:set_instance_parameter` Monolith commands.

How it works:
1. For emitter parameters: dispatches `editor_query:run_python` with inline
   Python that uses `unreal.NiagaraSystem` API.
2. For module scripts: dispatches `niagara_query:add_module` with the
   ModuleScript source and stage.
3. For MPC bindings: dispatches `material_query:set_instance_parameter` or
   writes a ModuleScript that samples the MPC at runtime.
4. For emitter config: exports the current emitter stack via inline Python.

Usage:
    injector = T3D NiagaraInjector()
    injector.set_emitter_parameter("/Game/.../NS_WaterFX", "Emitter1",
                                   "SpawnRate", 100.0)
    injector.add_module_script("/Game/.../NS_WaterFX", "Emitter1",
                               "ProximityDriver", script_source, "EmitterUpdate")
    injector.bind_mpc_parameter("/Game/.../NS_WaterFX", "Emitter1",
                                "SpawnRate", "/Game/.../MPC_Palette", "PlayerProximity")
    config = injector.read_emitter_config("/Game/.../NS_WaterFX")
    errors = injector.compile_and_verify("/Game/.../NS_WaterFX")
"""

from __future__ import annotations

import json
import os
import sys
import urllib.error
import urllib.request
from pathlib import Path

MONOLITH_URL = os.environ.get("MONOLITH_URL", "http://127.0.0.1:9316/mcp")


def monolith(method: str, args: dict | None = None, timeout: int = 30) -> str:
    """Call Monolith MCP tool and return the text content of the first item."""
    body = {
        "jsonrpc": "2.0",
        "id": 1,
        "method": "tools/call",
        "params": {"name": method, "arguments": args or {}},
    }
    req = urllib.request.Request(
        MONOLITH_URL,
        data=json.dumps(body).encode(),
        headers={"Content-Type": "application/json"},
    )
    try:
        with urllib.request.urlopen(req, timeout=timeout) as resp:
            envelope = json.loads(resp.read().decode())
    except (urllib.error.URLError, OSError, json.JSONDecodeError) as e:
        return f"ERROR:{e}"

    if "error" in envelope:
        return f"ERROR:{envelope['error']}"
    content = envelope.get("result", {}).get("content") or []
    if not content:
        return "ERROR:empty content"
    return content[0].get("text", "")


def _resolve_niagara_path(path: str) -> str:
    """Ensure path has no file extension - Niagara system assets don't use them."""
    return path.rsplit(".", 1)[0] if "." in path else path


def _make_python_set_param_script(
    niagara_path: str, emitter_name: str, param_name: str, value: float | bool | str
) -> str:
    """Generate inline Python to set a parameter on a Niagara emitter via the Python API."""
    if isinstance(value, str):
        val_literal = json.dumps(value)
    elif isinstance(value, bool):
        val_literal = "True" if value else "False"
    else:
        val_literal = str(value)

    return (
        "import unreal\n"
        f"ns = unreal.load_asset({json.dumps(niagara_path)})\n"
        "if not ns:\n"
        f"  print('ERROR: could not load {niagara_path}')\n"
        "  quit()\n"
        f"emitters = ns.get_editor_property('emitter_handles') or []\n"
        "target = None\n"
        "for e in emitters:\n"
        f"  ename = e.get_editor_property('emitter_name') if e else ''\n"
        f"  if ename == {json.dumps(emitter_name)}:\n"
        "    target = e\n"
        "    break\n"
        "if not target:\n"
        f"  print('ERROR: emitter {emitter_name} not found')\n"
        "  quit()\n"
        "# Try setting via user parameter first\n"
        "user_params = ns.get_editor_property('user_parameters') or {}\n"
        f"if {json.dumps(param_name)} in user_params:\n"
        "  param = user_params[{json.dumps(param_name)}]\n"
        "  try:\n"
        f"    param.set_value({val_literal})\n"
        "    print(f'SET_OK: {json.dumps(param_name)}={val_literal}')\n"
        "    quit()\n"
        "  except Exception as exc:\n"
        "    print(f'WARN: user param set failed: {exc}')\n"
        "# Fallback: try emitter script parameter\n"
        "try:\n"
        "  script_params = target.get_editor_property('script_parameters') or []\n"
        "  for sp in script_params:\n"
        "    pname = sp.get_editor_property('name') if hasattr(sp, 'get_editor_property') else str(sp)\n"
        f"    if pname == {json.dumps(param_name)}:\n"
        "      try:\n"
        f"        sp.set_editor_property('value', {val_literal})\n"
        "        print(f'SET_OK: {json.dumps(param_name)}={val_literal} (script param)')\n"
        "        quit()\n"
        "      except Exception as exc:\n"
        "        print(f'WARN: script param set failed: {exc}')\n"
        "except Exception as exc:\n"
        "  print(f'WARN: could not access script params: {exc}')\n"
        f"print('ERROR: parameter {param_name} not found on {emitter_name}')\n"
    )


def _make_python_read_config_script(niagara_path: str) -> str:
    """Generate inline Python to export current emitter configuration."""
    return (
        "import json\n"
        "import unreal\n"
        f"ns = unreal.load_asset({json.dumps(niagara_path)})\n"
        "if not ns:\n"
        f"  print('ERROR: could not load {niagara_path}')\n"
        "  quit()\n"
        "result = {'system_path': ns.get_path_name(), 'emitters': []}\n"
        "emitters = ns.get_editor_property('emitter_handles') or []\n"
        "for e in emitters:\n"
        "  entry = {'name': str(e.get_editor_property('emitter_name') if e else 'unknown')}\n"
        "  # User parameters\n"
        "  try:\n"
        "    user_params = ns.get_editor_property('user_parameters') or {}\n"
        "    entry['user_parameters'] = {}\n"
        "    for k, v in user_params.items():\n"
        "      entry['user_parameters'][str(k)] = str(v)\n"
        "  except Exception as exc:\n"
        "    entry['user_params_error'] = str(exc)\n"
        "  # Script parameters\n"
        "  try:\n"
        "    script_params = e.get_editor_property('script_parameters') or []\n"
        "    entry['script_parameters'] = []\n"
        "    for sp in script_params:\n"
        "      name = sp.get_editor_property('name') if hasattr(sp, 'get_editor_property') else str(sp)\n"
        "      val = sp.get_editor_property('value') if hasattr(sp, 'get_editor_property') else None\n"
        "      entry['script_parameters'].append({'name': str(name), 'value': str(val)})\n"
        "  except Exception as exc:\n"
        "    entry['script_params_error'] = str(exc)\n"
        "  # Modules\n"
        "  try:\n"
        "    modules = e.get_editor_property('emitter_modules') or []\n"
        "    entry['modules'] = [str(m.get_class().get_name()) for m in modules if m]\n"
        "  except Exception as exc:\n"
        "    entry['modules_error'] = str(exc)\n"
        "  result['emitters'].append(entry)\n"
        "print(json.dumps(result))\n"
    )


def _make_python_compile_verify_script(niagara_path: str) -> str:
    """Generate inline Python to find and report compile errors on a Niagara system."""
    return (
        "import json\n"
        "import unreal\n"
        f"ns = unreal.load_asset({json.dumps(niagara_path)})\n"
        "if not ns:\n"
        "  print(json.dumps({'ok': False, 'error': f'could not load {niagara_path}'}))\n"
        "  quit()\n"
        "result = {'ok': True, 'path': ns.get_path_name()}\n"
        "# Force compile\n"
        "try:\n"
        "  ns.request_compile()\n"
        "except Exception as exc:\n"
        "  result['compile_error'] = str(exc)\n"
        "# Query compile status\n"
        "try:\n"
        "  status = ns.get_editor_property('compile_status') if hasattr(ns, 'get_editor_property') else None\n"
        "  if status:\n"
        "    result['compile_status'] = str(status)\n"
        "    errors = ns.get_editor_property('compile_errors') if hasattr(ns, 'get_editor_property') else None\n"
        "    if errors:\n"
        "      result['compile_errors'] = [str(e) for e in errors]\n"
        "      result['ok'] = len(errors) == 0\n"
        "except Exception as exc:\n"
        "  result['status_error'] = str(exc)\n"
        "# Check message log\n"
        "try:\n"
        "  log = unreal.SystemLibrary.get_system_messages(True)\n"
        "  niagara_msgs = [m for m in (log or []) if 'niagara' in str(m).lower() or 'waterfx' in str(m).lower()]\n"
        "  if niagara_msgs:\n"
        "    result['log_messages'] = niagara_msgs[:20]\n"
        "except Exception:\n"
        "  pass\n"
        "print(json.dumps(result))\n"
    )


def _make_python_material_set_param_script(
    material_path: str, scalar_params: dict[str, float] | None = None,
    vector_params: dict[str, tuple[float, float, float, float]] | None = None
) -> str:
    """Generate inline Python to set material instance parameters."""
    lines = [
        "import unreal",
        f"mi = unreal.load_asset({json.dumps(material_path)})",
        "if not mi:",
        f"  print('ERROR: could not load {material_path}')",
        "  quit()",
    ]
    if scalar_params:
        for name, val in scalar_params.items():
            lines.append(
                f"unreal.MaterialEditingLibrary.set_material_instance_scalar_parameter_value(mi, {json.dumps(name)}, {val})"
            )
    if vector_params:
        for name, val in vector_params.items():
            lines.append(
                f"unreal.MaterialEditingLibrary.set_material_instance_vector_parameter_value(mi, {json.dumps(name)}, unreal.LinearColor({val[0]}, {val[1]}, {val[2]}, {val[3]}))"
            )
    lines.append("print('SET_OK')")
    return "\n".join(lines)


class T3DNiagaraInjector:
    """
    Batch-injects Niagara parameter changes, module scripts, and MPC bindings
    via Monolith MCP.

    Each method dispatches a single MCP call and returns the text result.
    """

    def __init__(self, mcp_url: str | None = None):
        self.mcp_url = mcp_url or MONOLITH_URL

    def _call(self, method: str, args: dict | None = None, timeout: int = 30) -> str:
        """Dispatch a Monolith MCP call."""
        body = {
            "jsonrpc": "2.0",
            "id": 1,
            "method": "tools/call",
            "params": {"name": method, "arguments": args or {}},
        }
        req = urllib.request.Request(
            self.mcp_url,
            data=json.dumps(body).encode(),
            headers={"Content-Type": "application/json"},
        )
        try:
            with urllib.request.urlopen(req, timeout=timeout) as resp:
                envelope = json.loads(resp.read().decode())
        except (urllib.error.URLError, OSError, json.JSONDecodeError) as e:
            return f"ERROR:{e}"
        if "error" in envelope:
            return f"ERROR:{envelope['error']}"
        content = envelope.get("result", {}).get("content") or []
        if not content:
            return "ERROR:empty content"
        return content[0].get("text", "")

    def set_emitter_parameter(
        self, niagara_path: str, emitter_name: str, param_name: str,
        value: float | bool | str, timeout: int = 60
    ) -> str:
        """Set a scalar/boolean/string parameter on a Niagara emitter.

        Dispatches inline Python via editor_query:run_python.
        """
        path = _resolve_niagara_path(niagara_path)
        script = _make_python_set_param_script(path, emitter_name, param_name, value)
        return self._call("editor_query", {
            "action": "run_python",
            "script": script,
        }, timeout=timeout)

    def set_batch_parameters(
        self, niagara_path: str, emitter_params: dict[str, dict[str, float | bool | str]],
        timeout: int = 90
    ) -> list[str]:
        """Set multiple parameters across emitters in individual calls.

        emitter_params: {emitter_name: {param_name: value, ...}, ...}
        """
        results = []
        for emitter_name, params in emitter_params.items():
            for param_name, value in params.items():
                r = self.set_emitter_parameter(niagara_path, emitter_name, param_name, value, timeout)
                results.append(f"{emitter_name}.{param_name}: {r}")
        return results

    def add_module_script(
        self, niagara_path: str, emitter_name: str, module_name: str,
        script_source: str, stage: str = "EmitterUpdate", timeout: int = 30
    ) -> str:
        """Inject a ModuleScript into a Niagara emitter's update/spawn/handler stage.

        stage: 'EmitterUpdate', 'EmitterSpawn', 'ParticleSpawn', 'ParticleUpdate', 'ParticleEvent'
        """
        path = _resolve_niagara_path(niagara_path)
        return self._call("niagara_query", {
            "action": "add_module",
            "asset_path": path,
            "emitter": emitter_name,
            "module_name": module_name,
            "script_source": script_source,
            "stage": stage,
        }, timeout=timeout)

    def bind_mpc_parameter(
        self, niagara_path: str, emitter_name: str, param_name: str,
        mpc_path: str, mpc_param_name: str, timeout: int = 60
    ) -> str:
        """Bind an MPC scalar parameter to a Niagara emitter float parameter.

        Injects a ModuleScript in the EmitterUpdate stage that reads the MPC
        value and writes it to the target parameter at runtime.
        """
        path = _resolve_niagara_path(niagara_path)
        script_source = (
            f"MPC = Engine.MaterialParameterCollection'{mpc_path}.{mpc_path.split('/')[-1]}';\n"
            f"float {mpc_param_name}_Value = MPC.GetScalarParameterValue('{mpc_param_name}');\n"
            f"{param_name} = {mpc_param_name}_Value;"
        )
        module_name = f"MPC_{mpc_param_name}_Binding"
        return self.add_module_script(
            path, emitter_name, module_name, script_source, "EmitterUpdate", timeout
        )

    def read_emitter_config(self, niagara_path: str, timeout: int = 60) -> str:
        """Export current emitter configuration as JSON.

        Returns a JSON string with system info, emitters, user/script
        parameters, and module lists.
        """
        path = _resolve_niagara_path(niagara_path)
        script = _make_python_read_config_script(path)
        return self._call("editor_query", {
            "action": "run_python",
            "script": script,
        }, timeout=timeout)

    def compile_and_verify(self, niagara_path: str, timeout: int = 60) -> str:
        """Compile a Niagara system and report compile errors.

        Returns a JSON string with ok/error status.
        """
        path = _resolve_niagara_path(niagara_path)
        script = _make_python_compile_verify_script(path)
        return self._call("editor_query", {
            "action": "run_python",
            "script": script,
        }, timeout=timeout)

    def set_material_instance_parameters(
        self, material_path: str,
        scalar_params: dict[str, float] | None = None,
        vector_params: dict[str, tuple[float, float, float, float]] | None = None,
        timeout: int = 30
    ) -> str:
        """Set material instance scalar and/or vector parameters.

        Dispatches inline Python via editor_query:run_python.
        """
        script = _make_python_material_set_param_script(
            material_path, scalar_params, vector_params
        )
        return self._call("editor_query", {
            "action": "run_python",
            "script": script,
        }, timeout=timeout)

    def apply_preset(
        self, preset_path: str | dict, timeout: int = 120
    ) -> dict[str, list[str]]:
        """Apply a complete preset spec to Niagara systems and materials.

        The preset dict can contain:
            'niagara_systems': {niagara_path: {emitter_name: {param: value}}}
            'module_scripts': [{niagara_path, emitter, module_name, source, stage}]
            'mpc_bindings': [{niagara_path, emitter, param, mpc_path, mpc_param}]
            'material_instances': {material_path: {scalars: {}, vectors: {}}}
        Returns a dict with result keys for each category.
        """
        if isinstance(preset_path, str):
            with open(preset_path, "r") as f:
                preset = json.load(f)
        else:
            preset = preset_path

        results: dict[str, list[str]] = {}

        if "niagara_systems" in preset:
            results["niagara_systems"] = []
            for niagara_path, emitters in preset["niagara_systems"].items():
                for emitter_name, params in emitters.items():
                    r = self.set_batch_parameters(niagara_path, {emitter_name: params})
                    results["niagara_systems"].extend(r)

        if "module_scripts" in preset:
            results["module_scripts"] = []
            for ms in preset["module_scripts"]:
                r = self.add_module_script(
                    ms["niagara_path"], ms["emitter"], ms["module_name"],
                    ms["source"], ms.get("stage", "EmitterUpdate")
                )
                results["module_scripts"].append(r)

        if "mpc_bindings" in preset:
            results["mpc_bindings"] = []
            for binding in preset["mpc_bindings"]:
                r = self.bind_mpc_parameter(
                    binding["niagara_path"], binding["emitter"],
                    binding["param"], binding["mpc_path"], binding["mpc_param"]
                )
                results["mpc_bindings"].append(r)

        if "material_instances" in preset:
            results["material_instances"] = []
            for mat_path, mat_config in preset["material_instances"].items():
                r = self.set_material_instance_parameters(
                    mat_path,
                    scalar_params=mat_config.get("scalars"),
                    vector_params=mat_config.get("vectors")
                )
                results["material_instances"].append(r)

        return results


# ---------------------------------------------------------------------------
# CLI
# ---------------------------------------------------------------------------

def cli_main() -> int:
    import argparse

    parser = argparse.ArgumentParser(
        description="T3D Niagara Module Injector - CLI mode"
    )
    parser.add_argument("--niagara", help="Niagara system asset path")
    parser.add_argument("--set-param", action="append", default=[],
                        help="Set param: <emitter>.<name>=<value>")
    parser.add_argument("--bind-mpc", action="append", default=[],
                        help="Bind MPC: <emitter>.<name>=<mpc_path>:<mpc_param>")
    parser.add_argument("--add-module", action="append", default=[],
                        help="Add module: <emitter>:<name>:<stage>")
    parser.add_argument("--source", help="ModuleScript source file path (for --add-module)")
    parser.add_argument("--read-config", action="store_true",
                        help="Read and print emitter config")
    parser.add_argument("--compile", action="store_true",
                        help="Compile and verify the system")
    parser.add_argument("--preset", help="Apply a preset JSON file")
    parser.add_argument("--material-param", action="append", default=[],
                        help="Set material scalar: <material_path>:<name>=<value>")
    args = parser.parse_args()

    injector = T3DNiagaraInjector()

    if args.preset:
        print(f"[T3D] Applying preset: {args.preset}")
        results = injector.apply_preset(args.preset)
        print(json.dumps(results, indent=2))
        return 0

    if not args.niagara and not args.material_param:
        parser.print_help()
        return 1

    for sp in args.set_param:
        parts = sp.split("=", 1)
        if len(parts) != 2:
            print(f"ERROR: invalid --set-param format: {sp}")
            return 1
        emitter_dot_name, value_str = parts
        if "." not in emitter_dot_name:
            print(f"ERROR: --set-param needs <emitter>.<name>: {sp}")
            return 1
        emitter_name, param_name = emitter_dot_name.split(".", 1)
        try:
            value = float(value_str)
        except ValueError:
            if value_str.lower() in ("true", "false"):
                value = value_str.lower() == "true"
            else:
                value = value_str
        print(f"[T3D] Setting {args.niagara} {emitter_name}.{param_name}={value}")
        result = injector.set_emitter_parameter(args.niagara, emitter_name, param_name, value)
        print(f"  Result: {result[:200]}")

    for bm in args.bind_mpc:
        parts = bm.split("=", 1)
        if len(parts) != 2:
            print(f"ERROR: invalid --bind-mpc format: {bm}")
            return 1
        emitter_dot_name, mpc_spec = parts
        if ":" not in mpc_spec:
            print(f"ERROR: --bind-mpc needs <mpc_path>:<mpc_param>: {bm}")
            return 1
        mpc_path, mpc_param = mpc_spec.split(":", 1)
        if "." not in emitter_dot_name:
            print(f"ERROR: --bind-mpc needs <emitter>.<name>: {bm}")
            return 1
        emitter_name, param_name = emitter_dot_name.split(".", 1)
        print(f"[T3D] Binding MPC {args.niagara} {emitter_name}.{param_name} -> {mpc_path}:{mpc_param}")
        result = injector.bind_mpc_parameter(args.niagara, emitter_name, param_name, mpc_path, mpc_param)
        print(f"  Result: {result[:200]}")

    for am in args.add_module:
        if not args.source:
            print("ERROR: --add-module requires --source <file>")
            return 1
        parts = am.split(":")
        if len(parts) < 2:
            print(f"ERROR: --add-module needs <emitter>:<name>[:<stage>]: {am}")
            return 1
        emitter_name = parts[0]
        module_name = parts[1]
        stage = parts[2] if len(parts) > 2 else "EmitterUpdate"
        try:
            source = Path(args.source).read_text(encoding="utf-8")
        except Exception as e:
            print(f"ERROR: reading source file: {e}")
            return 1
        print(f"[T3D] Adding module {args.niagara} {emitter_name}:{module_name} ({stage})")
        result = injector.add_module_script(args.niagara, emitter_name, module_name, source, stage)
        print(f"  Result: {result[:200]}")

    if args.read_config:
        print(f"[T3D] Reading config: {args.niagara}")
        config = injector.read_emitter_config(args.niagara)
        try:
            parsed = json.loads(config)
            print(json.dumps(parsed, indent=2))
        except (json.JSONDecodeError, TypeError):
            print(config)

    if args.compile:
        print(f"[T3D] Compiling: {args.niagara}")
        result = injector.compile_and_verify(args.niagara)
        try:
            parsed = json.loads(result)
            status = "OK" if parsed.get("ok") else "FAIL"
            print(f"  Compile: {status}")
            if parsed.get("compile_errors"):
                for e in parsed["compile_errors"]:
                    print(f"    Error: {e}")
        except (json.JSONDecodeError, TypeError):
            print(f"  Result: {result[:300]}")

    for mp in args.material_param:
        parts = mp.split(":", 1)
        if len(parts) != 2:
            print(f"ERROR: invalid --material-param format: {mp}")
            return 1
        mat_path, name_eq_val = parts
        if "=" not in name_eq_val:
            print(f"ERROR: --material-param needs <name>=<value>: {mp}")
            return 1
        param_name, value_str = name_eq_val.split("=", 1)
        try:
            value = float(value_str)
        except ValueError:
            value = value_str
        print(f"[T3D] Setting material param {mat_path}.{param_name}={value}")
        result = injector.set_material_instance_parameters(mat_path, scalar_params={param_name: value})
        print(f"  Result: {result[:200]}")

    return 0


if __name__ == "__main__":
    sys.exit(cli_main())
