#!/usr/bin/env python3
"""Run Monolith Phase A for all 22 new cymatic variants serially."""

import subprocess
import sys
from pathlib import Path

VARIANTS = [
    "CymaticOrchid",
    "SingingDune",
    "FarawayCelestialSilk",
    "FarawayNightVelvet",
    "FarawayAquaLace",
    "FarawayGildedRidge",
    "FarawayAlabasterDrape",
    "FarawayNacreVeil",
    "FarawayMoonChiffon",
    "FarawayLullabyFleece",
    "MelodiaHeroGem",
    "MelodiaGoldSilk",
    "MelodiaMotherPearl",
    "MelodiaSapphireGlass",
    "MelodiaRoseVelvet",
    "MelodiaMoonlace",
    "MelodiaForestEmerald",
    "MelodiaAmethystVein",
    "MelodiaAuroraGlass",
    "PrismaticObsidian",
    "RoyalVelvetBrocade",
    "WeepingWillow",
    "MoonlitMoss",
    "SingingSilk",
]

PROJECT_ROOT = Path(__file__).resolve().parents[0]
LOG_FILE = PROJECT_ROOT / "Saved" / "Audit" / "monolith_phaseA_2026-09-03.log"
SCRIPT = PROJECT_ROOT / "Tools" / "monolith_execution_plan_parallel.py"

def run_variant(variant: str) -> bool:
    """Run Phase A for a single variant. Returns True on success."""
    cmd = [
        sys.executable, str(SCRIPT),
        "--phase", "A",
        "--variant", variant,
        "--execute"
    ]
    print(f"\n{'='*60}")
    print(f"Running Phase A for {variant}...")
    print(f"{'='*60}")
    
    with open(LOG_FILE, "a") as log:
        log.write(f"\n{'='*60}\n")
        log.write(f"Variant: {variant}\n")
        log.write(f"{'='*60}\n")
        
        result = subprocess.run(cmd, stdout=subprocess.PIPE, stderr=subprocess.STDOUT, 
                               text=True, timeout=300, cwd=PROJECT_ROOT)
        
        log.write(result.stdout)
        print(result.stdout)
        
        if result.returncode != 0:
            log.write(f"\n[FAILED] Variant {variant} exited with code {result.returncode}\n")
            print(f"[FAILED] Variant {variant} exited with code {result.returncode}")
            return False
    
    return True

def main():
    LOG_FILE.parent.mkdir(parents=True, exist_ok=True)
    
    print(f"Starting Monolith Phase A for {len(VARIANTS)} variants")
    print(f"Log file: {LOG_FILE}")
    
    results = {}
    for variant in VARIANTS:
        success = run_variant(variant)
        results[variant] = "PASS" if success else "FAIL"
    
    # Summary
    print(f"\n{'='*60}")
    print("SUMMARY")
    print(f"{'='*60}")
    for variant, status in results.items():
        print(f"  {variant}: {status}")
    
    passed = sum(1 for s in results.values() if s == "PASS")
    print(f"\nTotal: {passed}/{len(VARIANTS)} passed")
    
    with open(LOG_FILE, "a") as log:
        log.write(f"\n{'='*60}\n")
        log.write("SUMMARY\n")
        log.write(f"{'='*60}\n")
        for variant, status in results.items():
            log.write(f"  {variant}: {status}\n")
        log.write(f"\nTotal: {passed}/{len(VARIANTS)} passed\n")
    
    return 0 if passed == len(VARIANTS) else 1

if __name__ == "__main__":
    sys.exit(main())