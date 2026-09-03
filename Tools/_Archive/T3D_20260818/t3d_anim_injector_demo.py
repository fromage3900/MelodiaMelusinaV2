#!/usr/bin/env python3
"""
t3d_anim_injector_demo.py - demo: tune Melusina locomotion blendspace
and apply AnimBP variable defaults via T3DAnimBlueprintInjector.

Usage:
    python Tools/t3d_anim_injector_demo.py [--dry-run]

Requires:
    - Monolith MCP server running at localhost:9316/mcp
    - Unreal Editor running with BS_GodFile project loaded
    - Melusina assets at expected paths
"""

import json
import os
import sys

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from mcp_client import monolith
from t3d_anim_injector import T3DAnimBlueprintInjector

PROJECT_ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))

BLEND_PRESET = os.path.join(PROJECT_ROOT, "specs", "anim_presets", "melusina_locomotion_blend.json")
VAR_PRESET = os.path.join(PROJECT_ROOT, "specs", "anim_presets", "melusina_anim_vars.json")


def verify_monolith():
    """Quick connectivity check."""
    result = monolith("editor_query", {"action": "run_python", "script": "print('pong')"})
    return "pong" in result


def main():
    dry_run = "--dry-run" in sys.argv

    print("=" * 60)
    print("T3D AnimBP Injector - Melusina Demo")
    print("=" * 60)
    print(f"  Project: {PROJECT_ROOT}")
    print(f"  Dry run: {dry_run}")
    print()

    if not dry_run:
        print("  Checking Monolith MCP connectivity...")
        if not verify_monolith():
            print("  ERROR: Monolith MCP unreachable. Start Monolith + Unreal Editor first.")
            sys.exit(1)
        print("  Monolith OK.")
    else:
        print("  [DRY RUN] Skipping connectivity check.")
    print()

    injector = T3DAnimBlueprintInjector()

    # --- Step 1: Apply blendspace preset ---
    print("[1/3] Applying blendspace preset...")
    if dry_run:
        with open(BLEND_PRESET) as f:
            preset = json.load(f)
        for s in preset["samples"]:
            print(f"  Would set sample[{s['index']}] {s['label']} -> {s['animation']} @ speed={s['speed']}")
    else:
        results = injector.apply_blendspace_preset(BLEND_PRESET)
        for r in results:
            status = "OK" if "OK:" in str(r.get("result", "")) else "?"
            print(f"  [{status}] Sample {r['sample']}: {str(r.get('result', ''))[:120]}")

    # --- Step 2: Apply AnimBP variable defaults ---
    print()
    print("[2/3] Applying AnimBP variable defaults...")
    if dry_run:
        with open(VAR_PRESET) as f:
            preset = json.load(f)
        for var_name, var_info in preset["variables"].items():
            print(f"  Would set {var_name} = {var_info['default']} ({var_info['type']})")
    else:
        results = injector.apply_anim_var_preset(VAR_PRESET)
        for r in results:
            status = "OK" if "OK:" in str(r.get("result", "")) else "?"
            val_preview = str(r.get("result", ""))[:100]
            print(f"  [{status}] {r['variable']}: {val_preview}")

    # --- Step 3: Verify compilation ---
    print()
    print("[3/3] Compiling AnimBP...")
    abp_path = "/Game/Melodia/Characters/Melusina/ABP_Melusina_Current"
    if dry_run:
        print(f"  Would compile {abp_path}")
    else:
        result = monolith("blueprint_query", {
            "action": "compile_blueprint",
            "asset_path": abp_path,
        })
        print(f"  Compile result: {result[:200] if result else 'OK (no output)'}")

    print()
    print("Done.")


if __name__ == "__main__":
    main()
