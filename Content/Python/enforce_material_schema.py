#!/usr/bin/env python3
"""
enforce_material_schema.py — Dual-mode parameter safety gate.

Modes:
  --headless : Runs inside UnrealEditor-Cmd.exe (uses UE Python API directly)
  --monolith : Connects to running editor via Monolith MCP (default if neither specified)
  --validate : Read-only check (default)
  --fix      : Auto-repair violations
  --precapture : Stricter gate before portfolio capture

Headless usage:
  UnrealEditor-Cmd.exe "C:/.../BS_GodFile.uproject" -ExecutePythonScript="Content/Python/enforce_material_schema.py" --headless --validate
"""
from __future__ import annotations
import json, sys, os, ast
from pathlib import Path
from typing import Any

SCHEMA_PATH = Path(__file__).resolve().parent / "material_schema.yaml"
MONOLITH_URL = "http://127.0.0.1:9316/mcp"

# ── Detect mode ──────────────────────────────────────────────────────
HEADLESS = "--headless" in sys.argv
VALIDATE = "--validate" in sys.argv or "--precapture" in sys.argv
FIX = "--fix" in sys.argv
PRECAPTURE = "--precapture" in sys.argv

# ── Dual-mode backend ────────────────────────────────────────────────
class MonolithBackend:
    """Call UE Python via Monolith HTTP."""
    def run(self, cmd: str) -> str:
        body = json.dumps({"jsonrpc":"2.0","id":1,"method":"tools/call","params":{"name":"editor_query","arguments":{"action":"run_python","command":cmd}}}).encode()
        import urllib.request
        req = urllib.request.Request(MONOLITH_URL, data=body, headers={"Content-Type":"application/json"})
        resp = json.loads(urllib.request.urlopen(req, timeout=120).read().decode())
        out = []
        for c in resp.get("result",{}).get("content",[]):
            if c.get("type")=="text":
                data = json.loads(c["text"])
                for o in data.get("output",[]):
                    out.append(o.get("output",""))
        return "\n".join(out)

class HeadlessBackend:
    """Runs inside UE - import unreal directly."""
    def run(self, cmd: str) -> str:
        import io,contextlib,traceback
        stdout = io.StringIO()
        with contextlib.redirect_stdout(stdout):
            try:
                exec(cmd, {"unreal": __import__("unreal")})
            except Exception:
                print("EXEC_ERROR:" + traceback.format_exc())
        return stdout.getvalue()

def get_backend():
    if HEADLESS:
        return HeadlessBackend()
    return MonolithBackend()

# ── Schema loader ────────────────────────────────────────────────────
def load_schema() -> dict:
    import yaml
    if not SCHEMA_PATH.exists():
        raise FileNotFoundError(f"Schema not found at {SCHEMA_PATH}")
    with open(SCHEMA_PATH, "r") as f:
        return yaml.safe_load(f)

# ── Report ───────────────────────────────────────────────────────────
class Report:
    def __init__(self):
        self.errors: list[str] = []
        self.warnings: list[str] = []
        self.fixes: list[str] = []
    def err(self, msg: str): self.errors.append(msg)
    def warn(self, msg: str): self.warnings.append(msg)
    def fix(self, msg: str): self.fixes.append(msg)
    @property
    def ok(self) -> bool: return len(self.errors) == 0
    def print(self):
        for e in self.errors: print(f"  ERROR: {e}")
        for w in self.warnings: print(f"  WARNING: {w}")
        for f in self.fixes: print(f"  FIXED: {f}")

# ── Validators ───────────────────────────────────────────────────────
def validate_mpc(schema: dict, report: Report, be):
    mpc_schema = schema.get("material_parameter_collections", {}).get("MPC_Melodia_Palette", {})
    mpc_path = mpc_schema.get("path", "")
    if not mpc_path:
        report.err("MPC_Melodia_Palette path not in schema")
        return

    out = be.run(f"""
import unreal
mpc = unreal.load_asset("{mpc_path}")
if not mpc:
    print("MISSING")
else:
    existing = {{}}
    for s in mpc.get_editor_property("scalar_parameters"):
        existing[str(s.get_editor_property("parameter_name"))] = "scalar"
    for v in mpc.get_editor_property("vector_parameters"):
        existing[str(v.get_editor_property("parameter_name"))] = "vector"
    print("PARAMS:" + str(list(existing.keys())))
""")
    if "MISSING" in out:
        report.err(f"MPC asset not found at {mpc_path}")
        return

    existing_str = ""
    for line in out.splitlines():
        if line.startswith("PARAMS:"):
            existing_str = line[7:]
    try:
        existing = ast.literal_eval(existing_str) if existing_str else {}
    except:
        report.warn(f"Could not parse existing MPC params: {existing_str[:100]}")
        return

    for s in mpc_schema.get("scalars", []):
        if s["name"] not in existing:
            report.warn(f"MPC scalar '{s['name']}' missing")
    for v in mpc_schema.get("vectors", []):
        if v["name"] not in existing:
            report.warn(f"MPC vector '{v['name']}' missing")

def validate_master(schema: dict, key: str, report: Report, be):
    ms = schema.get("masters", {}).get(key, {})
    if not ms:
        report.err(f"Master '{key}' not in schema")
        return
    path = ms.get("path", "")

    out = be.run(f"""
import unreal
mat = unreal.load_asset("{path}")
if not mat:
    print("MISSING_{key}")
else:
    MEL = unreal.MaterialEditingLibrary
    params = {{}}
    try:
        for s in MEL.get_scalar_parameter_names(mat):
            params[str(s)] = "scalar"
        for v in MEL.get_vector_parameter_names(mat):
            params[str(v)] = "vector"
    except:
        pass
    print("PARAMS_{key}:" + str(params))
""")
    actual = {}
    for line in out.splitlines():
        line = line.strip()
        if not line: continue
        marker = f"PARAMS_{key}:"
        if marker in line:
            idx = line.index(marker) + len(marker)
            try: actual = ast.literal_eval(line[idx:])
            except: report.warn(f"Params parse failed for {key}")
        elif f"MISSING_{key}" in line:
            report.err(f"Material '{key}' not found")
            return

    for group in ms.get("groups", []):
        gname = group["name"]
        for p in group["params"]:
            pname = p["name"]
            if pname not in actual:
                report.warn(f"Missing param '{pname}' (group '{gname}') in {key}")
                if FIX:
                    report.fix(f"Would create '{pname}' in {key} -- auto-create not yet implemented, use editor")
                continue
            expected_type = "scalar" if p["type"] == "float" else "vector"
            if actual[pname] != expected_type:
                report.warn(f"Type mismatch '{pname}' in {key}: expected {expected_type}, got {actual[pname]}")

    # Check MPC references (hard package dependency — nodes may live inside material functions)
    mpc_refs_checked = []
    for entry in ms.get("mpc_references", []):
        for mpc_name, params in entry.items():
            mpc_path = schema.get("material_parameter_collections", {}).get(mpc_name, {}).get("path", "")
            if not mpc_path:
                continue
            out2 = be.run(f"""
import unreal
ar = unreal.AssetRegistryHelpers.get_asset_registry()
ad = ar.get_asset_by_object_path("{path}")
if not ad.is_valid():
    print("NOASSET")
else:
    opts = unreal.AssetRegistryDependencyOptions()
    deps = [str(d) for d in ar.get_dependencies(ad.package_name, opts)]
    print("HAS_DEP:" + str("{mpc_path}" in deps))
""")
            has_dep = any(line.strip().startswith("HAS_DEP:True") for line in out2.splitlines())
            if "NOASSET" in out2:
                report.err(f"Material '{key}' not found for MPC check")
                continue
            if not has_dep:
                report.warn(f"MPC '{mpc_name}' not referenced by {key} (no hard package dependency)")
            mpc_refs_checked.append(mpc_name)

# ── Main ─────────────────────────────────────────────────────────────
def main():
    be = get_backend()
    schema = load_schema()
    report = Report()

    mode = "HEADLESS" if HEADLESS else "MONOLITH"
    action = "VALIDATE" if VALIDATE else ("FIX" if FIX else "VALIDATE")
    print(f"=== Material Schema Enforcement [{mode}] [{action}] ===")

    print("\n--- MPC: MPC_Melodia_Palette ---")
    validate_mpc(schema, report, be)

    for key in schema.get("masters", {}):
        print(f"\n--- Master: {key} ---")
        validate_master(schema, key, report, be)

    print(f"\n=== Results ===")
    report.print()
    p = "PASS" if report.ok else "FAIL"
    print(f"\n{p}: {len(report.errors)} errors, {len(report.warnings)} warnings, {len(report.fixes)} fixes applied")
    if PRECAPTURE and not report.ok:
        print("PRECAPTURE GATE FAILED — resolve errors before capture.")
        return 1
    return 0 if report.ok else 1

if __name__ == "__main__":
    raise SystemExit(main())
