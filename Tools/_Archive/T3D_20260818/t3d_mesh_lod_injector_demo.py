#!/usr/bin/env python3
"""
t3d_mesh_lod_injector_demo.py — demo: generate LOD groups for SK_Melusina
and export the resulting LOD info via T3DMeshLODInjector.

Usage:
    python Tools/t3d_mesh_lod_injector_demo.py [--dry-run]

Requires:
    - Monolith MCP server running at localhost:9316/mcp
    - Unreal Editor running with BS_GodFile project loaded
    - SK_Melusina mesh at expected path
"""

import json
import os
import sys

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from mcp_client import monolith
from t3d_mesh_lod_injector import T3DMeshLODInjector

PROJECT_ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))

LOD_PRESET = os.path.join(PROJECT_ROOT, "specs", "lod_presets", "melusina_lod.json")
MESH_PATH = "/Game/Melodia/Characters/Melusina/SK_Melusina"
LOD_COUNTS = [224123, 112061, 56030]
SCREEN_SIZES = [1.0, 0.5, 0.2]


def verify_monolith():
    result = monolith("editor_query", {"action": "run_python", "script": "print('pong')"})
    return "pong" in result


def main():
    dry_run = "--dry-run" in sys.argv

    print("=" * 60)
    print("T3D Mesh LOD Injector — SK_Melusina Demo")
    print("=" * 60)
    print(f"  Mesh: {MESH_PATH}")
    print(f"  Source tris: {LOD_COUNTS[0]}")
    print(f"  LOD1: {LOD_COUNTS[1]} tris ({LOD_COUNTS[1]/LOD_COUNTS[0]*100:.0f}%)")
    print(f"  LOD2: {LOD_COUNTS[2]} tris ({LOD_COUNTS[2]/LOD_COUNTS[0]*100:.0f}%)")
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

    injector = T3DMeshLODInjector()

    # --- Step 1: Export current LOD info (baseline) ---
    print("[1/4] Exporting current LOD configuration (baseline)...")
    if dry_run:
        print("  Would call export_lod_info() on SK_Melusina")
    else:
        try:
            current = injector.export_lod_info(MESH_PATH)
            print(f"  Current LOD info:\n{current[:800]}")
        except Exception as e:
            print(f"  WARN: Could not export LOD info: {e}")
            print("  Continuing...")

    # --- Step 2: Generate LOD groups ---
    print()
    print("[2/4] Generating LOD groups...")
    if dry_run:
        print(f"  Would generate LODs with tri counts: {LOD_COUNTS}")
    else:
        try:
            result = injector.generate_lod_groups(MESH_PATH, LOD_COUNTS)
            print(f"  Generate result: {result[:300]}")
        except Exception as e:
            print(f"  ERROR: {e}")

    # --- Step 3: Set screen sizes ---
    print()
    print("[3/4] Setting LOD screen size thresholds...")
    if dry_run:
        print(f"  Would set screen sizes: {SCREEN_SIZES}")
    else:
        try:
            result = injector.set_lod_screen_sizes(MESH_PATH, SCREEN_SIZES)
            print(f"  Screen size result: {result[:200]}")
        except Exception as e:
            print(f"  ERROR: {e}")

    # --- Step 4: Export post-injection LOD info ---
    print()
    print("[4/4] Exporting post-injection LOD configuration...")
    if dry_run:
        print("  Would call export_lod_info() to verify")
    else:
        try:
            final = injector.export_lod_info(MESH_PATH)
            print(f"  Post-injection LOD info:\n{final[:800]}")
        except Exception as e:
            print(f"  WARN: Could not export final LOD info: {e}")

    # --- Step 5: Apply full preset (optional) ---
    print()
    print(f"[bonus] Full preset at: {LOD_PRESET}")
    if dry_run:
        with open(LOD_PRESET) as f:
            preset = json.load(f)
        print(f"  Preset has {len(preset['lod_groups'])} LOD groups")
        print(f"  Would apply via apply_lod_preset()")
    else:
        print("  Preset available at: spec/lod_presets/melusina_lod.json")
        print("  Run apply_lod_preset() manually for full preset application.")

    print()
    print("Done.")


if __name__ == "__main__":
    main()
