"""Material unification orchestrator — MCP audit + Ollama SDF generation + UE execution.

Connects to Monolith MCP (port 9316) for audit/health, Ollama (port 11434) for
stylized SDF material script generation, then queues UE Python scripts for execution.

Usage:
  py Content/Python/execute_material_unification.py --audit       # MCP audit only
  py Content/Python/execute_material_unification.py --ollama-sdf  # Generate SDF scripts via Ollama
  py Content/Python/execute_material_unification.py --run-sdf     # Execute stylized SDF build
  py Content/Python/execute_material_unification.py --all         # Full pipeline
  py Content/Python/execute_material_unification.py --test-ollama # Test Ollama connectivity

DO NOT TOUCH: UniversalMasterToon (M_Master_Toon_Universal)
"""
from __future__ import annotations

import json
import subprocess
import sys
import time
import urllib.error
import urllib.request
from datetime import datetime, timezone
from pathlib import Path
from typing import Any

PROJECT_ROOT = Path(__file__).resolve().parents[2]
PYTHON_DIR = PROJECT_ROOT / "Content" / "Python"
REPORT_DIR = PROJECT_ROOT / "Saved" / "Audit"
REPORT_DIR.mkdir(parents=True, exist_ok=True)

MCP_URL = "http://127.0.0.1:9316/mcp"
OLLAMA_URL = "http://localhost:11434"

UE_CMD = Path(r"C:\Program Files\Epic Games\UE_5.8\Engine\Binaries\Win64\UnrealEditor-Cmd.exe")
UPROJECT = PROJECT_ROOT / "BS_GodFile.uproject"

MATERIALS_ROOT = "/Game/EnvSandbox/Materials"
MASTER_DIR = f"{MATERIALS_ROOT}/Masters"
SDF_INST_DIR = f"{MATERIALS_ROOT}/SDF/Instances"

SDF_MASTER = f"{MASTER_DIR}/M_Toon_SDF"
SDF_MASTER_MATURED = f"{MASTER_DIR}/M_Master_SDF_Toon"

# SDF masters path (may be in Masters/ or SDF/)
SDF_MASTERS_FS = PROJECT_ROOT / "Content" / "EnvSandbox" / "Materials" / "Masters"
SDF_INST_FS = PROJECT_ROOT / "Content" / "EnvSandbox" / "Materials" / "SDF" / "Instances"

# ── SDF instance check-list ─────────────────────────────────────────────────
SDF_INSTANCE_NAMES = [
    "MI_Toon_SDF_Wall", "MI_Toon_SDF_Floor", "MI_Toon_SDF_Accent",
    "MI_Toon_SDF_Rim", "MI_Toon_SDF_Ornamental",
    "MI_SDF_CathedralVault", "MI_SDF_FlyingButtress", "MI_SDF_BaroqueColumn",
    "MI_SDF_GildedAltar", "MI_SDF_GothicRoseWindow", "MI_SDF_Grass_Field",
]

STYLIZED_NAMES = [
    "MI_SDF_CelestialVinyl", "MI_SDF_TealCeramic", "MI_SDF_RosyQuartz",
    "MI_SDF_MossyCopper", "MI_SDF_VoidStarlight", "MI_SDF_IvoryScrollwork",
]

# ── Ollama prompt for generating new stylized SDF scripts ───────────────────

OLLAMA_SDF_SYSTEM = """You are a Unreal Engine 5.8 material pipeline expert for the BS_GodFile environment art project.
Generate ONLY valid, runnable Python code following the exact conventions of the project's setup_sdf_materials.py.
Use Substrate Toon BSDF material instances parented to M_Toon_SDF.
Output ONLY the Python code in a ```python block. No explanations, no markdown outside the block."""

OLLAMA_SDF_USER = """Create a complete Python script following BS_GodFile conventions to build new stylized Substrate Toon SDF material instances.

Parent master: /Game/EnvSandbox/Materials/Masters/M_Toon_SDF.M_Toon_SDF
Target directory: /Game/EnvSandbox/Materials/SDF/Instances/

New instances to create (with base tint, accent tint, band scale, band strength):

__SPECS__

Follow this EXACT pattern (from the project's setup_sdf_materials.py):

```python
from __future__ import annotations
import json
from datetime import datetime, timezone
from pathlib import Path
import unreal

PROJECT_ROOT = Path(__file__).resolve().parents[2]
REPORT_DIR = PROJECT_ROOT / "Saved" / "Audit"

MATERIALS_ROOT = "/Game/EnvSandbox/Materials"
SDF_INST_DIR = f"{MATERIALS_ROOT}/SDF/Instances"
PARENT = f"{MATERIALS_ROOT}/Masters/M_Toon_SDF.M_Toon_SDF"

STYLIZED = [...]

def _ensure_directory(path: str) -> None:
    if not unreal.EditorAssetLibrary.does_directory_exist(path):
        unreal.EditorAssetLibrary.make_directory(path)

def build_stylized_instances() -> list[dict]:
    results = []
    parent = unreal.load_asset(PARENT)
    asset_tools = unreal.AssetToolsHelpers.get_asset_tools()
    factory = unreal.MaterialInstanceConstantFactoryNew()
    for spec in STYLIZED:
        path = f"{SDF_INST_DIR}/{spec['name']}"
        full = f"{path}.{spec['name']}"
        if unreal.EditorAssetLibrary.does_asset_exist(full):
            continue
        inst = asset_tools.create_asset(spec['name'], SDF_INST_DIR, unreal.MaterialInstanceConstant, factory)
        unreal.MaterialEditingLibrary.set_material_instance_parent(inst, parent)
        unreal.MaterialEditingLibrary.set_material_instance_vector_parameter_value(
            inst, "BaseTint", unreal.LinearColor(*spec['tint']))
        unreal.MaterialEditingLibrary.set_material_instance_vector_parameter_value(
            inst, "AccentTint", unreal.LinearColor(*spec['accent']))
        unreal.MaterialEditingLibrary.set_material_instance_scalar_parameter_value(
            inst, "SDF_BandScale", spec['band_scale'])
        unreal.MaterialEditingLibrary.set_material_instance_scalar_parameter_value(
            inst, "SDF_BandStrength", spec['band_strength'])
        unreal.EditorAssetLibrary.save_loaded_asset(inst, only_if_is_dirty=False)
        results.append(spec)
    return results

def build_all() -> int:
    results = build_stylized_instances()
    unreal.EditorLoadingAndSavingUtils.save_dirty_packages(True, True)
    return 0

if __name__ == '__main__':
    raise SystemExit(build_all())
```

Generate the COMPLETE script with all the specified instances filled into the STYLIZED list.
Return ONLY the Python code in ```python block."""


# ── MCP helpers ──────────────────────────────────────────────────────────────

def _mcp_call(tool: str, args: dict, timeout: int = 15) -> dict:
    payload = {"jsonrpc": "2.0", "id": int(time.time() * 1000) % 100000,
               "method": "tools/call", "params": {"name": tool, "arguments": args}}
    req = urllib.request.Request(MCP_URL, data=json.dumps(payload).encode(),
                                 headers={"Content-Type": "application/json"}, method="POST")
    try:
        with urllib.request.urlopen(req, timeout=timeout) as resp:
            return json.loads(resp.read().decode())
    except Exception as exc:
        return {"error": str(exc)}


def _mcp_text(tool: str, args: dict) -> str:
    result = _mcp_call(tool, args)
    for block in result.get("result", {}).get("content") or []:
        if isinstance(block, dict) and block.get("type") == "text":
            return block["text"]
    return json.dumps(result)


def _mcp_json(tool: str, args: dict) -> dict:
    text = _mcp_text(tool, args)
    try:
        return json.loads(text) if isinstance(json.loads(text), dict) else {"text": text}
    except (json.JSONDecodeError, TypeError):
        return {"text": text}


# ── Ollama helpers ───────────────────────────────────────────────────────────

def _ollama_query(model: str, system: str, prompt: str, timeout: int = 180) -> str:
    payload = {"model": model, "system": system, "prompt": prompt,
               "stream": False, "options": {"temperature": 0.2}}
    req = urllib.request.Request(f"{OLLAMA_URL}/api/generate",
                                 data=json.dumps(payload).encode(),
                                 headers={"Content-Type": "application/json"}, method="POST")
    with urllib.request.urlopen(req, timeout=timeout) as resp:
        return json.loads(resp.read().decode()).get("response", "")


def _ollama_ping() -> tuple[bool, list[str]]:
    try:
        req = urllib.request.Request(f"{OLLAMA_URL}/api/tags", method="GET")
        result = json.loads(urllib.request.urlopen(req, timeout=5).read().decode())
        models = [m.get("name", "") for m in result.get("models", [])]
        return True, models
    except Exception:
        return False, []


# ── Step 1: MCP health ──────────────────────────────────────────────────────

def step_mcp_health() -> dict:
    status = _mcp_json("monolith_status", {})
    return status


# ── Step 2: Audit SDF materials (filesystem check) ───────────────────────────

def step_audit_sdf() -> dict:
    audits: dict[str, list[str]] = {"masters_exist": [], "masters_missing": [],
                                     "instances_exist": [], "instances_missing": [],
                                     "stylized_exist": [], "stylized_missing": [],
                                     "other_sdf_masters": [], "cleanup_test_assets": []}

    for name in ["M_Toon_SDF", "M_Master_SDF_Toon"]:
        path = SDF_MASTERS_FS / f"{name}.uasset"
        if path.exists():
            audits["masters_exist"].append(name)
        else:
            audits["masters_missing"].append(name)

    for name in SDF_INSTANCE_NAMES:
        path = SDF_INST_FS / f"{name}.uasset"
        if path.exists():
            audits["instances_exist"].append(name)
        else:
            audits["instances_missing"].append(name)

    for name in STYLIZED_NAMES:
        path = SDF_INST_FS / f"{name}.uasset"
        if path.exists():
            audits["stylized_exist"].append(name)
        else:
            audits["stylized_missing"].append(name)

    # Scan for other SDF masters
    for p in sorted(SDF_MASTERS_FS.glob("M_SDF_*.uasset")):
        audits["other_sdf_masters"].append(p.stem)

    # Flag test artifacts for cleanup
    for p in SDF_MASTERS_FS.glob("M_SDF_Test*.uasset"):
        audits["cleanup_test_assets"].append(str(p))

    return audits


# ── Step 3: Generate stylized SDF scripts via Ollama ─────────────────────────

def _build_specs_text() -> str:
    lines = []
    for name, tint, accent, bscale, bstrength, style, tags in [
        ("MI_SDF_CelestialVinyl", (0.82,0.71,0.35,1.0), (0.12,0.08,0.22,1.0), 0.045, 0.30, "celestial gold + dark vinyl bands", ["magical","baroque","henshin"]),
        ("MI_SDF_TealCeramic", (0.25,0.48,0.52,1.0), (0.85,0.88,0.92,1.0), 0.06, 0.18, "teal ceramic + white band relief", ["architectural","clean","modern"]),
        ("MI_SDF_RosyQuartz", (0.95,0.72,0.78,1.0), (0.82,0.48,0.55,1.0), 0.04, 0.15, "rosy pink quartz + cherry blossom shimmer", ["sakura","warm","translucent"]),
        ("MI_SDF_MossyCopper", (0.42,0.55,0.38,1.0), (0.72,0.45,0.22,1.0), 0.055, 0.28, "aged copper + moss patina", ["nature","aged","ornament"]),
        ("MI_SDF_VoidStarlight", (0.06,0.04,0.12,1.0), (0.18,0.22,0.95,1.0), 0.08, 0.42, "void black + starlight blue", ["celestial","cosmic","deep"]),
        ("MI_SDF_IvoryScrollwork", (0.92,0.88,0.78,1.0), (0.75,0.62,0.32,1.0), 0.035, 0.25, "ivory parchment + gold filigree", ["manuscript","warm","ornate"]),
    ]:
        lines.append(f"  - name: {name}")
        lines.append(f"    tint: {tint}")
        lines.append(f"    accent: {accent}")
        lines.append(f"    band_scale: {bscale}")
        lines.append(f"    band_strength: {bstrength}")
        lines.append(f"    style: {style}")
        lines.append(f"    tags: {tags}")
    return "\n".join(lines)


def step_generate_ollama_sdf() -> dict:
    result: dict[str, Any] = {"ollama_available": False, "model_used": None,
                               "generated": False, "output_path": None, "error": None}
    ok, models = _ollama_ping()
    result["ollama_available"] = ok
    if not ok:
        result["error"] = "Ollama not reachable"
        return result

    result["available_models"] = models

    # Select best model for code generation
    model = None
    for preferred in ("qwen2.5-coder:7b", "deepseek-r1:14b", "hermes3:latest"):
        if preferred in models:
            model = preferred
            break
    if not model:
        model = next((m for m in models if "embed" not in m.lower()), models[0])
    result["model_used"] = model

    user_prompt = OLLAMA_SDF_USER.replace("__SPECS__", _build_specs_text())
    print(f"  Generating SDF script with {model}...")

    try:
        response = _ollama_query(model, OLLAMA_SDF_SYSTEM, user_prompt, timeout=300)
    except Exception as exc:
        result["error"] = str(exc)
        return result

    # Extract Python code
    import re
    code_match = re.search(r"```(?:python)?\s*\n(.*?)```", response, re.DOTALL)
    if code_match:
        code = code_match.group(1).strip()
    else:
        # Try to find usable code in raw response
        code = response.strip()
        if not code.startswith(("from ", "import ", "#")):
            result["error"] = "No Python code block in Ollama response"
            result["raw_response"] = response[:1000]
            return result

    output_path = PYTHON_DIR / "setup_stylized_sdf_ollama_gen.py"
    output_path.write_text(code, encoding="utf-8")
    result["generated"] = True
    result["output_path"] = str(output_path)
    result["code_length"] = len(code)
    print(f"  Generated -> {output_path} ({len(code)} chars)")

    return result


# ── Step 4: Run UE Python script ─────────────────────────────────────────────

def step_run_ue_script(script_name: str) -> dict:
    result: dict[str, Any] = {"script": script_name, "ran": False, "returncode": None}
    script_path = PYTHON_DIR / script_name
    if not script_path.exists():
        result["error"] = f"Script not found: {script_path}"
        return result

    if not UE_CMD.exists():
        result["error"] = f"UE not found: {UE_CMD}"
        return result

    log_path = PROJECT_ROOT / "Saved" / "Logs" / f"mcp_orch_{script_name}.log"
    log_path.parent.mkdir(parents=True, exist_ok=True)

    cmd = [str(UE_CMD), str(UPROJECT),
           f"-ExecutePythonScript={script_path.as_posix()}",
           "-stdout", "-unattended", "-nosplash",
           f"-log={log_path}"]
    print(f"  Running: {' '.join(cmd[:4])}...")
    try:
        proc = subprocess.run(cmd, cwd=str(PROJECT_ROOT),
                              capture_output=True, text=True, timeout=600)
        result["ran"] = True
        result["returncode"] = proc.returncode
        result["stdout_tail"] = proc.stdout[-2000:] if proc.stdout else ""
        result["stderr_tail"] = proc.stderr[-500:] if proc.stderr else ""
    except subprocess.TimeoutExpired:
        result["error"] = "Timeout (10 min)"
    except Exception as exc:
        result["error"] = str(exc)

    return result


# ── Main ─────────────────────────────────────────────────────────────────────

def main() -> int:
    import argparse
    parser = argparse.ArgumentParser(description="Material Unification Orchestrator")
    parser.add_argument("--audit", action="store_true", help="MCP health + filesystem audit")
    parser.add_argument("--ollama-sdf", action="store_true", help="Generate stylized SDF script via Ollama")
    parser.add_argument("--run-sdf", action="store_true", help="Run stylized SDF build in UE")
    parser.add_argument("--test-ollama", action="store_true", help="Test Ollama connectivity")
    parser.add_argument("--all", action="store_true", help="Full pipeline")
    args = parser.parse_args()

    if not any(vars(args).values()):
        args.audit = True

    reports: dict[str, Any] = {"timestamp": datetime.now(timezone.utc).isoformat()}
    overall_ok = True

    # ── MCP Health ───────────────────────────────────────────────────────────
    if args.audit or args.all:
        print("=== MCP Health ===")
        status = step_mcp_health()
        reports["mcp_health"] = status
        eng = status.get("engine_version", "?")
        ver = status.get("version", "?")
        running = status.get("server_running", False)
        print(f"  Monolith v{ver}  UE {eng}  running={running}")
        if not running:
            overall_ok = False

    # ── Audit ────────────────────────────────────────────────────────────────
    if args.audit or args.all:
        print("\n=== SDF Audit (filesystem) ===")
        audit = step_audit_sdf()
        reports["sdf_audit"] = audit
        print(f"  Masters: {len(audit['masters_exist'])}/{len(audit['masters_exist'])+len(audit['masters_missing'])} exist")
        print(f"  Instances: {len(audit['instances_exist'])}/{len(audit['instances_exist'])+len(audit['instances_missing'])} exist")
        print(f"  Stylized: {len(audit['stylized_exist'])}/{len(audit['stylized_exist'])+len(audit['stylized_missing'])} exist")
        if audit["stylized_missing"]:
            print(f"  Missing stylized: {', '.join(audit['stylized_missing'])}")

    # ── Test Ollama ──────────────────────────────────────────────────────────
    if args.test_ollama:
        print("\n=== Ollama Connectivity ===")
        ok, models = _ollama_ping()
        reports["ollama_test"] = {"reachable": ok, "models": models}
        if ok:
            print(f"  Reachable: {len(models)} models")
            for m in sorted(models):
                print(f"    {m}")
        else:
            print("  NOT reachable")

    # ── Generate via Ollama ──────────────────────────────────────────────────
    if args.ollama_sdf or args.all:
        print("\n=== Ollama SDF Script Generation ===")
        gen_result = step_generate_ollama_sdf()
        reports["ollama_generation"] = gen_result
        if gen_result.get("generated"):
            print("  Ollama generation OK")
        elif gen_result.get("error"):
            print(f"  Ollama error: {gen_result['error']}")
            overall_ok = False
        else:
            print("  Skipped (no models)")

    # ── Run stylized SDF build ───────────────────────────────────────────────
    if args.run_sdf or args.all:
        print("\n=== Run Stylized SDF Build (UE headless) ===")
        run_result = step_run_ue_script("setup_stylized_sdf.py")
        reports["run_stylized_sdf"] = run_result
        if run_result.get("ran"):
            rc = run_result["returncode"]
            print(f"  Return code: {rc}")
            if rc != 0:
                overall_ok = False
                if run_result.get("stderr_tail"):
                    print(f"  Stderr: {run_result['stderr_tail'][:500]}")
        else:
            print(f"  Did not run: {run_result.get('error', '?')}")

    # ── Write report ─────────────────────────────────────────────────────────
    report_path = REPORT_DIR / "material_unification_orchestrator.json"
    report_path.write_text(json.dumps(reports, indent=2, ensure_ascii=False, default=str),
                           encoding="utf-8")
    print(f"\nReport: {report_path}")
    return 0 if overall_ok else 1


if __name__ == "__main__":
    raise SystemExit(main())
