"""Smoke test for Houdini Engine for UE5.8 — BS_GodFile.

Runs editor-closed (no `unreal` import required). Checks:
- .uproject has HoudiniEngine enabled
- Plugins/HoudiniEngine/HoudiniEngine.uplugin exists + version
- WP_CELL_SIZE_CM in pcg_scale_world_pipeline.py
- Houdini 22.0.368 hython exists
- Expected Houdini Engine Unreal plugin folder exists

Usage:
    py Content/Python/smoke_houdini_engine_pcg.py
    py Content/Python/smoke_houdini_engine_pcg.py --json

Exit 0 if all critical checks pass, 1 otherwise.
"""
from __future__ import annotations

import argparse
import json
import re
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
UPROJECT = ROOT / "BS_GodFile.uproject"
PLUGIN_UPLUGIN = ROOT / "Plugins" / "HoudiniEngine" / "HoudiniEngine.uplugin"
PCG_PIPELINE = ROOT / "Content" / "Python" / "pcg_scale_world_pipeline.py"
SMOKE_SPEC = ROOT / "Docs" / "WorldGen" / "HOUDINI_ENGINE_SMOKE_SPEC_2026-08-27.md"

HOUDINI_ROOT = Path(r"C:\Program Files\Side Effects Software\Houdini 22.0.368")
HYTHON = HOUDINI_ROOT / "bin" / "hython.exe"
HOUDINI_ENGINE_UNREAL_58 = Path(r"C:\Program Files\Side Effects Software\Houdini Engine\Unreal\22.0.368\5.8\HoudiniEngine")
UPROJECT_PLUGIN_SRC = Path(r"C:\Program Files\Side Effects Software\Houdini Engine\Unreal\22.0.368\5.8\HoudiniEngine\HoudiniEngine.uplugin")

def check_uproject() -> dict:
    if not UPROJECT.exists():
        return {"ok": False, "msg": f"missing {UPROJECT}"}
    text = UPROJECT.read_text(encoding="utf-8-sig")
    # handle both pretty-printed ("Name":  "HoudiniEngine" with variable whitespace) and compact
    if re.search(r'"Name"\s*:\s*"HoudiniEngine"', text):
        if re.search(r'"Name"\s*:\s*"HoudiniEngine"\s*,\s*"Enabled"\s*:\s*true', text, re.IGNORECASE | re.DOTALL):
            return {"ok": True, "msg": "HoudiniEngine Enabled in .uproject"}
        # fallback: any Enabled true near HoudiniEngine entry
        if re.search(r'HoudiniEngine[^}]*"Enabled"\s*:\s*true', text, re.IGNORECASE | re.DOTALL):
            return {"ok": True, "msg": "HoudiniEngine Enabled in .uproject"}
        return {"ok": False, "msg": "HoudiniEngine in .uproject but not Enabled:true"}
    return {"ok": False, "msg": "HoudiniEngine not in .uproject Plugins"}

def check_plugin_uplugin() -> dict:
    if not PLUGIN_UPLUGIN.exists():
        return {"ok": False, "msg": f"missing {PLUGIN_UPLUGIN}"}
    try:
        text = PLUGIN_UPLUGIN.read_text(encoding="utf-8")
        m = re.search(r'"VersionName"\s*:\s*"([^"]+)"', text)
        ver = m.group(1) if m else "unknown"
        return {"ok": True, "msg": f"found {PLUGIN_UPLUGIN} VersionName={ver}"}
    except Exception as e:
        return {"ok": False, "msg": f"read error: {e}"}

def check_wp_cell() -> dict:
    if not PCG_PIPELINE.exists():
        return {"ok": False, "msg": f"missing {PCG_PIPELINE}"}
    text = PCG_PIPELINE.read_text(encoding="utf-8")
    if "WP_CELL_SIZE_CM = 25_600" in text or "WP_CELL_SIZE_CM = 25600" in text:
        return {"ok": True, "msg": "WP_CELL_SIZE_CM=25600 found"}
    m = re.search(r"WP_CELL_SIZE_CM\s*=\s*(\d+)", text)
    if m:
        return {"ok": False, "msg": f"WP_CELL_SIZE_CM={m.group(1)} unexpected (expected 25600)"}
    return {"ok": False, "msg": "WP_CELL_SIZE_CM not found"}

def check_hython() -> dict:
    if HYTHON.exists():
        return {"ok": True, "msg": f"hython found {HYTHON}"}
    return {"ok": False, "msg": f"hython missing {HYTHON}"}

def check_engine_unreal_src() -> dict:
    if HOUDINI_ENGINE_UNREAL_58.exists():
        return {"ok": True, "msg": f"Engine Unreal 5.8 plugin exists {HOUDINI_ENGINE_UNREAL_58}"}
    return {"ok": False, "msg": f"missing {HOUDINI_ENGINE_UNREAL_58}"}

def check_spec() -> dict:
    if SMOKE_SPEC.exists():
        return {"ok": True, "msg": f"spec exists {SMOKE_SPEC}"}
    return {"ok": False, "msg": f"missing spec {SMOKE_SPEC}"}

def run_checks() -> dict:
    results = {
        "uproject": check_uproject(),
        "pluginUplugin": check_plugin_uplugin(),
        "wpCellSize": check_wp_cell(),
        "hython": check_hython(),
        "engineUnrealSrc": check_engine_unreal_src(),
        "spec": check_spec(),
    }
    # critical = all except spec is non-critical
    critical_keys = ["uproject", "pluginUplugin", "wpCellSize", "hython", "engineUnrealSrc"]
    ok = all(results[k]["ok"] for k in critical_keys)
    results["_ok"] = ok
    results["_nextSteps"] = []
    if not results["hython"]["ok"]:
        results["_nextSteps"].append("Install Houdini 22.0.368 via SideFX Launcher")
    if not results["pluginUplugin"]["ok"]:
        results["_nextSteps"].append("Copy Houdini Engine 5.8 plugin to Plugins/HoudiniEngine")
    if not results["uproject"]["ok"]:
        results["_nextSteps"].append("Add HoudiniEngine Enabled:true to BS_GodFile.uproject")
    if ok:
        results["_nextSteps"].append("Get Houdini Engine FREE license via SideFX, then reopen UE5.8 to compile HoudiniEngine modules")
        results["_nextSteps"].append("Author hda/ArpeggioStair_1.0.hda and place in L_HDA_Smoke")
    return results

def main() -> int:
    parser = argparse.ArgumentParser(description="Houdini Engine smoke for BS_GodFile")
    parser.add_argument("--json", action="store_true", help="output JSON only")
    args = parser.parse_args()

    results = run_checks()

    if args.json:
        print(json.dumps(results, indent=2))
    else:
        # Use ascii to avoid cp1252 tick/cross issues on Windows console
        print("=== Houdini Engine Smoke - BS_GodFile ===")
        for k, v in results.items():
            if k.startswith("_"):
                continue
            icon = "[OK]" if v["ok"] else "[FAIL]"
            print(f"{icon} {k:18s}: {v['msg']}")
        print(f"\nOverall: {'PASS' if results['_ok'] else 'FAIL'}")
        if results["_nextSteps"]:
            print("\nNext steps:")
            for s in results["_nextSteps"]:
                print(f"  - {s}")
        print(f"\nSpec: {SMOKE_SPEC}")

    return 0 if results["_ok"] else 1

if __name__ == "__main__":
    sys.exit(main())
