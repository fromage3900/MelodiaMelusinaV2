"""Central Automated Test Runner for Melodia PBR Material & Texture E2E Suite.

Executes all 4 Tiers:
- Tier 1: Opaque-Box Mathematical Invariants, Parameter Boundaries & Formatting Rules
- Tier 2: Subsystem & Component Operations (PIL Image Packing, Normal & Anisotropy Gating, Caustics)
- Tier 3: Cross-Component System Integration (Dual-Sheen, Sampler Optimization, Clock Harmonics)
- Tier 4: End-to-End Real-World Workloads (Wardrobe Slot Bindings, Lighting Stage, Grotto Simulation)

Usage:
    python run_e2e_material_suite.py
    python run_e2e_material_suite.py --tier 1
    python run_e2e_material_suite.py --tier 4 --verbose
    python run_e2e_material_suite.py --json-report Saved/Audit/e2e_test_report.json
"""

from __future__ import annotations

import argparse
import io
import json
import os
import sys
import time
import unittest
from datetime import datetime, timezone
from pathlib import Path
from typing import Any, Dict, List, Optional, Tuple

# Ensure current test folder is in sys.path
TEST_DIR = Path(__file__).resolve().parent
if str(TEST_DIR) not in sys.path:
    sys.path.insert(0, str(TEST_DIR))
PYTHON_DIR = TEST_DIR.parent
if str(PYTHON_DIR) not in sys.path:
    sys.path.insert(0, str(PYTHON_DIR))

# Import individual test modules
import test_pbr_texture_pipeline as mod_pbr
import test_fabric_instances as mod_fabric
import test_audio_harmony as mod_audio
import test_real_world_workloads as mod_workloads


# Mapping of Tiers to TestCase classes
TIER_CLASS_MAPPING = {
    1: [
        mod_pbr.TestPBRTextureInvariantsTier1,
        mod_fabric.TestFabricInvariantsTier1,
        mod_audio.TestAudioInvariantsTier1,
    ],
    2: [
        mod_pbr.TestPBRTexturePipelineTier2,
        mod_fabric.TestFabricPresetsTier2,
        mod_audio.TestAudioModulationTier2,
    ],
    3: [
        mod_fabric.TestFabricSystemIntegrationTier3,
        mod_audio.TestAudioHarmonySystemIntegrationTier3,
    ],
    4: [
        mod_workloads.TestRealWorldWorkloadsTier4,
    ],
}

FEATURE_COVERAGE_MAP = {
    "F1": {"name": "Automated ORM Packing Tool", "tiers": [1, 2], "status": "COVERED"},
    "F2": {"name": "Channel Validation & Invariant Harness", "tiers": [1, 2], "status": "COVERED"},
    "F3": {"name": "Repack Core Staging & Character Assets", "tiers": [2, 4], "status": "COVERED"},
    "F4": {"name": "Royal Velvet PBR Set & Preset", "tiers": [2, 3, 4], "status": "COVERED"},
    "F5": {"name": "Gilded Jacquard & Brocade PBR Set", "tiers": [2, 3, 4], "status": "COVERED"},
    "F6": {"name": "Sheer Silk & Chiffon PBR Set", "tiers": [2, 3, 4], "status": "COVERED"},
    "F7": {"name": "Baroque Filigree Lace PBR Set", "tiers": [2, 3, 4], "status": "COVERED"},
    "F8": {"name": "Gold-Threaded Embroidery PBR Set", "tiers": [2, 3, 4], "status": "COVERED"},
    "F9": {"name": "Iridescent Celestial Weave PBR Set", "tiers": [2, 3], "status": "COVERED"},
    "F10": {"name": "Wardrobe Material Slot Mapping", "tiers": [3, 4], "status": "COVERED"},
    "F11": {"name": "Dynamic Caustics & Wave Displacement Audio Modulation", "tiers": [2, 3, 4], "status": "COVERED"},
    "F12": {"name": "Sheen, Sparkle & Rune Glow Audio Pulsation", "tiers": [2, 3], "status": "COVERED"},
    "F13": {"name": "Water Bioluminescence & Niagara Harmony", "tiers": [2, 3, 4], "status": "COVERED"},
    "F14": {"name": "Substrate Sampler Optimization", "tiers": [3, 4], "status": "COVERED"},
    "F15": {"name": "Universal Master & Instance Verification", "tiers": [3, 4], "status": "COVERED"},
    "F16": {"name": "Multi-Tier E2E Test Suite", "tiers": [1, 2, 3, 4], "status": "COVERED"},
}


class StructuredTestResult(unittest.TextTestResult):
    """Custom TestResult tracking individual test execution times and status."""

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.test_records: List[Dict[str, Any]] = []
        self._test_start_time = 0.0

    def startTest(self, test):
        super().startTest(test)
        self._test_start_time = time.perf_counter()

    def addSuccess(self, test):
        super().addSuccess(test)
        elapsed = time.perf_counter() - self._test_start_time
        self.test_records.append({
            "test_id": test.id(),
            "name": test._testMethodName,
            "class": test.__class__.__name__,
            "status": "PASS",
            "elapsed_seconds": elapsed,
            "error": None,
        })

    def addFailure(self, test, err):
        super().addFailure(test, err)
        elapsed = time.perf_counter() - self._test_start_time
        self.test_records.append({
            "test_id": test.id(),
            "name": test._testMethodName,
            "class": test.__class__.__name__,
            "status": "FAIL",
            "elapsed_seconds": elapsed,
            "error": self._exc_info_to_string(err, test),
        })

    def addError(self, test, err):
        super().addError(test, err)
        elapsed = time.perf_counter() - self._test_start_time
        self.test_records.append({
            "test_id": test.id(),
            "name": test._testMethodName,
            "class": test.__class__.__name__,
            "status": "ERROR",
            "elapsed_seconds": elapsed,
            "error": self._exc_info_to_string(err, test),
        })


def run_e2e_suite(
    selected_tiers: Optional[List[int]] = None,
    verbose: bool = False,
    failfast: bool = False,
    json_report_path: Optional[Path] = None,
) -> Tuple[int, Dict[str, Any]]:
    """Execute the multi-tier E2E material test suite and generate structured report."""
    if selected_tiers is None:
        selected_tiers = [1, 2, 3, 4]

    print("================================================================================")
    print("           MELODIA PBR MATERIAL & TEXTURE E2E AUTOMATED TEST SUITE              ")
    print("================================================================================")
    print(f"Timestamp: {datetime.now(timezone.utc).isoformat()}")
    print(f"Executing Tiers: {selected_tiers}")
    print(f"Python Runtime: {sys.version.split()[0]} ({sys.executable})")
    print("--------------------------------------------------------------------------------\n")

    loader = unittest.TestLoader()
    suite = unittest.TestSuite()
    tier_test_counts = {t: 0 for t in selected_tiers}

    for tier in selected_tiers:
        classes = TIER_CLASS_MAPPING.get(tier, [])
        for cls in classes:
            loaded = loader.loadTestsFromTestCase(cls)
            tier_test_counts[tier] += loaded.countTestCases()
            suite.addTest(loaded)

    start_wall = time.perf_counter()
    stream = io.StringIO()
    runner = unittest.TextTestRunner(
        stream=stream,
        verbosity=2 if verbose else 1,
        failfast=failfast,
        resultclass=StructuredTestResult,
    )

    result: StructuredTestResult = runner.run(suite)
    elapsed_wall = time.perf_counter() - start_wall

    total_tests = result.testsRun
    failed_tests = len(result.failures)
    error_tests = len(result.errors)
    passed_tests = total_tests - (failed_tests + error_tests)
    pass_rate = (passed_tests / total_tests * 100.0) if total_tests > 0 else 0.0

    # Print Detailed Test Logs if verbose or failures exist
    output_log = stream.getvalue()
    if verbose or failed_tests > 0 or error_tests > 0:
        print("--- TEST EXECUTION TRACE ---")
        print(output_log)

    # Print Structured Tier Summary Table
    print("\n================================================================================")
    print("                           TEST EXECUTION SUMMARY                               ")
    print("================================================================================")
    print(f"{'Tier':<10} | {'Description':<35} | {'Tests':<8} | {'Status':<10}")
    print("-----------|-------------------------------------|----------|-----------")

    tier_descriptions = {
        1: "Unit & Invariant Rules",
        2: "Subsystem & Component Pipeline",
        3: "Cross-System Shading & Harmony",
        4: "End-to-End Real-World Workloads",
    }

    tier_failures = {t: 0 for t in selected_tiers}
    for record in result.test_records:
        if record["status"] != "PASS":
            # Identify tier of the failed class
            for t, classes in TIER_CLASS_MAPPING.items():
                if any(c.__name__ == record["class"] for c in classes):
                    if t in tier_failures:
                        tier_failures[t] += 1

    for tier in selected_tiers:
        desc = tier_descriptions.get(tier, "Custom Tier")
        count = tier_test_counts.get(tier, 0)
        status_str = "PASS [OK]" if tier_failures[tier] == 0 else f"FAIL ({tier_failures[tier]})"
        print(f"Tier {tier:<5} | {desc:<35} | {count:<8} | {status_str:<10}")

    print("--------------------------------------------------------------------------------")
    print(f"TOTAL TESTS RUN: {total_tests} | PASSED: {passed_tests} | FAILED: {failed_tests} | ERRORS: {error_tests}")
    print(f"OVERALL PASS RATE: {pass_rate:.1f}% | TOTAL DURATION: {elapsed_wall:.3f}s")
    print("================================================================================")

    # Print Feature Coverage Matrix
    print("\n================================================================================")
    print("                     FEATURE COVERAGE MATRIX (F1 - F16)                         ")
    print("================================================================================")
    print(f"{'Feature':<6} | {'Description':<48} | {'Tiers':<10} | {'Status':<8}")
    print("-------|--------------------------------------------------|------------|--------")
    for feat_id, feat_info in sorted(FEATURE_COVERAGE_MAP.items(), key=lambda x: int(x[0][1:])):
        tiers_str = ",".join(str(t) for t in feat_info["tiers"])
        print(f"{feat_id:<6} | {feat_info['name']:<48} | Tier {tiers_str:<5} | {feat_info['status']:<8}")
    print("================================================================================\n")

    # Generate Structured JSON Report
    report_dict = {
        "suite_name": "Melodia PBR Material & Texture E2E Automated Test Suite",
        "timestamp": datetime.now(timezone.utc).isoformat(),
        "total_tests": total_tests,
        "passed_tests": passed_tests,
        "failed_tests": failed_tests,
        "error_tests": error_tests,
        "pass_rate_percent": pass_rate,
        "duration_seconds": elapsed_wall,
        "selected_tiers": selected_tiers,
        "tier_summary": [
            {
                "tier": t,
                "description": tier_descriptions.get(t, ""),
                "test_count": tier_test_counts.get(t, 0),
                "failures": tier_failures.get(t, 0),
                "status": "PASS" if tier_failures.get(t, 0) == 0 else "FAIL",
            }
            for t in selected_tiers
        ],
        "feature_coverage": FEATURE_COVERAGE_MAP,
        "test_results": result.test_records,
    }

    if json_report_path:
        json_report_path = Path(json_report_path)
        json_report_path.parent.mkdir(parents=True, exist_ok=True)
        with open(json_report_path, "w", encoding="utf-8") as f:
            json.dump(report_dict, f, indent=2)
        print(f"[JSON Report Saved]: {json_report_path.resolve()}")

    exit_code = 0 if (failed_tests == 0 and error_tests == 0) else 1
    return exit_code, report_dict


def main():
    """Command-line entry point."""
    parser = argparse.ArgumentParser(description="Melodia PBR Material E2E Test Suite Runner")
    parser.add_argument(
        "--tier", "-t", type=str, default="all",
        help="Specific tier to execute (1, 2, 3, 4, or 'all')",
    )
    parser.add_argument(
        "--verbose", "-v", action="store_true",
        help="Enable detailed verbose output for all tests",
    )
    parser.add_argument(
        "--failfast", "-f", action="store_true",
        help="Stop execution on first test failure",
    )
    parser.add_argument(
        "--json-report", "-j", type=str,
        default=str(PYTHON_DIR.parent.parent / "Saved" / "Audit" / "e2e_material_test_report.json"),
        help="Path to save JSON execution report",
    )

    args = parser.parse_args()

    if args.tier.lower() == "all":
        tiers = [1, 2, 3, 4]
    else:
        try:
            tiers = [int(args.tier)]
        except ValueError:
            print(f"Error: Invalid tier '{args.tier}'. Must be 1, 2, 3, 4, or 'all'.")
            sys.exit(2)

    report_path = Path(args.json_report) if args.json_report else None
    exit_code, _ = run_e2e_suite(
        selected_tiers=tiers,
        verbose=args.verbose,
        failfast=args.failfast,
        json_report_path=report_path,
    )
    sys.exit(exit_code)


if __name__ == "__main__":
    main()
