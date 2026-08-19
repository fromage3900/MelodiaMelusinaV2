#!/usr/bin/env python3
"""
t3d_niagara_demo.py — Demo applying Melusina WaterFX presets to Niagara systems
and water hair materials via the T3D Niagara Injector.

Usage:
    python Tools/t3d_niagara_demo.py                         # apply all presets
    python Tools/t3d_niagara_demo.py --dry-run               # print what would be done
    python Tools/t3d_niagara_demo.py --preset day1           # apply day1 preset only
    python Tools/t3d_niagara_demo.py --preset waterfx        # apply WaterFX preset only
    python Tools/t3d_niagara_demo.py --preset waterhair      # apply water hair material preset only
    python Tools/t3d_niagara_demo.py --read-config           # read current emitter configs
    python Tools/t3d_niagara_demo.py --compile               # compile and verify all systems
"""

from __future__ import annotations

import json
import sys
import time
from pathlib import Path

# Allow running from Tools/ or project root
sys.path.insert(0, str(Path(__file__).resolve().parent))
from t3d_niagara_injector import T3DNiagaraInjector

PROJECT_ROOT = Path(__file__).resolve().parents[1]
SPECS_DIR = PROJECT_ROOT / "Specs"

PRESET_PATHS = {
    "waterfx": SPECS_DIR / "niagara_presets" / "melusina_waterfx.json",
    "day1": SPECS_DIR / "niagara_presets" / "melusina_waterfx_day1.json",
    "waterhair": SPECS_DIR / "material_presets" / "water_hair_presets.json",
}

# Niagara systems to verify after applying
NIAGARA_SYSTEMS = [
    "/Game/Melodia/VFX/Melusina_WaterFX",
    "/Game/EnvSandbox/VFX/Systems/NS_Uni_WaterMist",
]

# Water hair material
WATER_HAIR_MATERIAL = "/Game/EnvSandbox/Materials/Instances/Melusina/MI_Melusina_WaterHair"


def load_preset(name: str) -> dict | None:
    path = PRESET_PATHS.get(name) or Path(name)
    if not path.exists():
        print(f"  [FAIL] Preset not found: {path}")
        return None
    try:
        return json.loads(path.read_text(encoding="utf-8"))
    except json.JSONDecodeError as e:
        print(f"  [FAIL] Invalid JSON in {path}: {e}")
        return None


def dry_run_preset(name: str, preset: dict):
    print(f"\n  [DRY-RUN] {name}:")
    for section, data in preset.items():
        print(f"    {section}:")
        if isinstance(data, dict):
            for key, val in data.items():
                print(f"      {key}: {json.dumps(val, indent=2)[:120]}")
        elif isinstance(data, list):
            for item in data:
                print(f"      - {json.dumps(item, indent=2)[:120]}")


def main() -> int:
    import argparse
    parser = argparse.ArgumentParser(description="T3D Niagara Demo — Melusina WaterFX Presets")
    parser.add_argument("--dry-run", action="store_true", help="Print what would be done")
    parser.add_argument("--preset", choices=["waterfx", "day1", "waterhair", "all"],
                        default="all", help="Which preset to apply")
    parser.add_argument("--read-config", action="store_true",
                        help="Read and print current Niagara configs")
    parser.add_argument("--compile", action="store_true",
                        help="Compile and verify all Niagara systems")
    parser.add_argument("--mcp-url", default=None, help="Monolith MCP URL")
    args = parser.parse_args()

    injector = T3DNiagaraInjector(mcp_url=args.mcp_url)
    results: dict[str, list] = {}

    if args.read_config:
        print("=== Reading Niagara Emitter Configs ===\n")
        for ns_path in NIAGARA_SYSTEMS:
            print(f"--- {ns_path} ---")
            config = injector.read_emitter_config(ns_path)
            try:
                parsed = json.loads(config)
                print(json.dumps(parsed, indent=2))
            except (json.JSONDecodeError, TypeError):
                print(config)
            print()
        return 0

    print("=" * 60)
    print("T3D Niagara Demo — Melusina WaterFX Preset Application")
    print("=" * 60)
    print(f"  MCP URL: {args.mcp_url or 'http://127.0.0.1:9316/mcp'}")

    presets_to_apply = ["waterfx", "day1", "waterhair"] if args.preset == "all" else [args.preset]

    for preset_name in presets_to_apply:
        preset = load_preset(preset_name)
        if preset is None:
            continue

        if args.dry_run:
            dry_run_preset(preset_name, preset)
            continue

        print(f"\n=== Applying {preset_name} ===")
        start = time.time()
        result = injector.apply_preset(preset)
        elapsed = time.time() - start

        for section, entries in result.items():
            ok_count = sum(1 for e in entries if "ERROR" not in str(e))
            print(f"  {section}: {ok_count}/{len(entries)} OK")
            for i, entry in enumerate(entries[:5]):
                status = "OK" if "ERROR" not in str(entry) else "FAIL"
                print(f"    [{status}] {str(entry)[:120]}")
            if len(entries) > 5:
                print(f"    ... and {len(entries) - 5} more")

        print(f"  Elapsed: {elapsed:.2f}s")
        results[preset_name] = result

    if args.compile:
        print("\n=== Compiling & Verifying ===")
        for ns_path in NIAGARA_SYSTEMS:
            print(f"--- {ns_path} ---")
            ver = injector.compile_and_verify(ns_path)
            try:
                parsed = json.loads(ver)
                status = "OK" if parsed.get("ok") else "FAIL"
                print(f"  Status: {status}")
                if parsed.get("compile_errors"):
                    for e in parsed["compile_errors"]:
                        print(f"    Error: {e}")
            except (json.JSONDecodeError, TypeError):
                print(f"  {ver[:300]}")

    print("\nDone.")
    return 0


if __name__ == "__main__":
    sys.exit(main())
