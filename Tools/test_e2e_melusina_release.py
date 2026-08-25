#!/usr/bin/env python3
"""
Melusina End-to-End Release & Verification Test Suite
=====================================================
Target: Melusina Agent Test Harness & Melodia Release Readiness
Author: Test Writer Subagent (teamwork_preview_test_writer)
Date: 2026-08-18

Test Hierarchy (4 Tiers):
  Tier 1: Repository Open-Source Hygiene Verification
          - Release files existence (README, LICENSE, CONTRIBUTING, .gitignore, CODE_OF_CONDUCT, SECURITY)
          - Strict UTF-8 encoding validation and zero-corruption / zero-mojibake invariant
          - .gitignore rule enforcement for scratch binaries and reports
  Tier 2: GitPages Documentation & Asset Verification
          - wix/melusina-agent-harness.html existence and structural validity
          - MATH metrics documentation (TCA, PAR, SCR, RCF, TER)
          - Model comparison documentation (Nous Hermes 3, LongCat, Qwen 2.5-Coder, DeepSeek-R1, baselines)
          - tools/validate_assets.py execution & hard-tier asset verification
  Tier 3: Programmatic MCP & Live UE5 Content Verification
          - melodia_mcp_server module import and schema compliance
          - Programmatic melodia_bp_list_fixtures() and fixture validation
          - Programmatic melodia_persona_get_quests() verification
          - Programmatic melodia_rhythm_list_skills() and DataTable verification
          - Quill notification contract and subsystem health scan
  Tier 4: Melusina MCP & Daemon Regression Suite
          - Tools/test_melodia_mcp.py (13/13 passing)
          - Tools/test_melodia_ollama_validation.py (6/6 passing)
          - Tools/test_ollama_daemons_stress.py (19/19 passing)

Usage:
  python Tools/test_e2e_melusina_release.py
  python -m unittest Tools/test_e2e_melusina_release.py
"""

from __future__ import annotations

import json
import os
import re
import subprocess
import sys
import unittest
from pathlib import Path
from typing import Any, Dict, List, Set, Tuple

# Locate project roots
GODFILE_ROOT = Path(__file__).resolve().parent.parent
WORKSPACE_ROOT = GODFILE_ROOT.parent

# Ensure GODFILE_ROOT is on sys.path for local module imports
if str(GODFILE_ROOT) not in sys.path:
    sys.path.insert(0, str(GODFILE_ROOT))


# =============================================================================
# Helper Utilities
# =============================================================================

def read_file_strict_utf8(path: Path) -> str:
    """Read a file enforcing strict UTF-8 decoding without errors."""
    if not path.exists():
        raise FileNotFoundError(f"Required file not found: {path}")
    with open(path, "r", encoding="utf-8", errors="strict") as f:
        return f.read()


def check_for_mojibake_or_corruption(content: str, filename: str) -> List[str]:
    """
    Detects common encoding corruption patterns:
    - Unicode replacement character (U+FFFD)
    - Repetitive question-mark box replacement patterns ('? ? ? ?', '???')
    - Known Windows-1252 / ANSI mojibake artifacts ('â€™', 'Ã©', 'Â ')
    """
    errors: List[str] = []

    # 1. Unicode replacement char
    if "\ufffd" in content:
        errors.append(f"{filename}: Contains Unicode replacement character U+FFFD ('\\ufffd')")

    # 2. Corrupted box replacement patterns (e.g., '? ? ? ?' or '? Docs ?')
    corrupt_qmark_patterns = [
        re.compile(r"\?\s+\?\s+\?\s+\?"),
        re.compile(r"\?\s+(?:Docs|Architecture|Subsystems|Overview|Melodia)\s+\?"),
        re.compile(r"\[\?\s*\?\]"),
    ]
    for pattern in corrupt_qmark_patterns:
        match = pattern.search(content)
        if match:
            errors.append(f"{filename}: Contains corrupted replacement artifact: '{match.group(0)}'")

    # 3. ANSI / Windows-1252 to UTF-8 double-encoding mojibake
    mojibake_tokens = ["â€™", "â€œ", "â€", "Ã©", "Ã ", "Ã¼", "â€""]
    for token in mojibake_tokens:
        if token in content:
            errors.append(f"{filename}: Contains mojibake byte sequence: '{token}'")

    return errors


# =============================================================================
# TIER 1: Repository Open-Source Hygiene Verification
# =============================================================================

class TestTier1OpenSourceHygiene(unittest.TestCase):
    """Verifies open-source community standards, file presence, and UTF-8 encoding."""

    REQUIRED_GODFILE_FILES = [
        "README.md",
        "LICENSE",
        "CONTRIBUTING.md",
        ".gitignore",
        "CODE_OF_CONDUCT.md",
        "SECURITY.md",
    ]

    REQUIRED_WORKSPACE_FILES = [
        "README.md",
        ".gitignore",
    ]

    def test_01_godfile_hygiene_files_exist(self) -> None:
        """Verify all standard open-source release files exist in BS_GodFile."""
        missing = []
        for filename in self.REQUIRED_GODFILE_FILES:
            file_path = GODFILE_ROOT / filename
            if not file_path.exists():
                missing.append(str(file_path))
            else:
                self.assertGreater(
                    file_path.stat().st_size, 20,
                    f"File {filename} in BS_GodFile is empty or truncated (< 20 bytes)"
                )
        self.assertEqual(missing, [], f"Missing required open-source release files in BS_GodFile: {missing}")

    def test_02_workspace_root_hygiene_files_exist(self) -> None:
        """Verify key workspace root release files exist."""
        missing = []
        for filename in self.REQUIRED_WORKSPACE_FILES:
            file_path = WORKSPACE_ROOT / filename
            if not file_path.exists():
                missing.append(str(file_path))
            else:
                self.assertGreater(
                    file_path.stat().st_size, 20,
                    f"File {filename} at workspace root is empty or truncated (< 20 bytes)"
                )
        self.assertEqual(missing, [], f"Missing required release files at workspace root: {missing}")

    def test_03_strict_utf8_encoding_no_corruption(self) -> None:
        """Verify all release files decode cleanly under strict UTF-8 with zero mojibake."""
        all_errors = []
        for filename in self.REQUIRED_GODFILE_FILES:
            file_path = GODFILE_ROOT / filename
            if file_path.exists():
                try:
                    content = read_file_strict_utf8(file_path)
                    mojibake_errs = check_for_mojibake_or_corruption(content, filename)
                    all_errors.extend(mojibake_errs)
                except Exception as e:
                    all_errors.append(f"{filename} UTF-8 decoding error: {e}")

        self.assertEqual(
            all_errors, [],
            f"UTF-8 encoding or corruption errors found in release files:\n" + "\n".join(all_errors)
        )

    def test_04_readme_structure_and_professional_tone(self) -> None:
        """Verify BS_GodFile/README.md contains essential sections and professional tone."""
        readme_path = GODFILE_ROOT / "README.md"
        self.assertTrue(readme_path.exists(), "BS_GodFile/README.md does not exist")
        content = read_file_strict_utf8(readme_path)

        # Essential architectural keywords
        required_topics = [
            "Melodia",
            "Unreal Engine",
            "Model Context Protocol",
            "Architecture",
            "License",
        ]
        for topic in required_topics:
            self.assertIn(
                topic.lower(), content.lower(),
                f"BS_GodFile/README.md is missing expected topic: '{topic}'"
            )

        # Invariant: No leaked internal developer slop/debug shorthand
        slop_phrases = ["owner-lock worked", "tell the family", "wasteoftime", "4thtimestillnobones"]
        for slop in slop_phrases:
            self.assertNotIn(
                slop.lower(), content.lower(),
                f"BS_GodFile/README.md contains forbidden developer slop: '{slop}'"
            )

    def test_05_gitignore_contains_scratch_and_build_patterns(self) -> None:
        """Verify .gitignore includes proper rules for build artifacts and scratch outputs."""
        gitignore_path = GODFILE_ROOT / ".gitignore"
        self.assertTrue(gitignore_path.exists(), "BS_GodFile/.gitignore does not exist")
        content = read_file_strict_utf8(gitignore_path)

        required_patterns = ["Intermediate/", "Binaries/", "DerivedDataCache/", "Saved/"]
        for pat in required_patterns:
            self.assertIn(pat, content, f"BS_GodFile/.gitignore missing build ignore pattern: '{pat}'")


# =============================================================================
# TIER 2: GitPages Documentation & Asset Verification
# =============================================================================

class TestTier2GitPagesDocumentation(unittest.TestCase):
    """Verifies GitPages webfront whitepaper, MATH benchmark metrics, and asset integrity."""

    HARNESS_HTML_PATH = WORKSPACE_ROOT / "wix" / "melusina-agent-harness.html"
    HARNESS_DOC_PATH = GODFILE_ROOT / "Docs" / "MELUSINA_AGENT_TEST_HARNESS.md"
    VALIDATE_ASSETS_SCRIPT = WORKSPACE_ROOT / "tools" / "validate_assets.py"

    def test_01_harness_documentation_sources_exist(self) -> None:
        """Verify either the webfront HTML or markdown whitepaper is available and valid UTF-8."""
        html_exists = self.HARNESS_HTML_PATH.exists()
        doc_exists = self.HARNESS_DOC_PATH.exists()
        self.assertTrue(
            html_exists or doc_exists,
            f"Neither {self.HARNESS_HTML_PATH} nor {self.HARNESS_DOC_PATH} exists"
        )

        if html_exists:
            content = read_file_strict_utf8(self.HARNESS_HTML_PATH)
            self.assertIn("<!DOCTYPE html>", content, "HTML harness missing <!DOCTYPE html>")
            self.assertIn("<html", content, "HTML harness missing <html tag")
            self.assertIn("</html>", content, "HTML harness missing </html> tag")

        if doc_exists:
            content = read_file_strict_utf8(self.HARNESS_DOC_PATH)
            self.assertIn("Melusina Agent Test Harness", content)

    def test_02_math_metrics_documented(self) -> None:
        """Verify all 5 formal MATH evaluation metrics are documented with definitions."""
        # Check in HTML or Markdown whitepaper
        content = ""
        if self.HARNESS_HTML_PATH.exists():
            content += read_file_strict_utf8(self.HARNESS_HTML_PATH)
        if self.HARNESS_DOC_PATH.exists():
            content += "\n" + read_file_strict_utf8(self.HARNESS_DOC_PATH)

        required_metrics = [
            ("TCA", "Tool Call Accuracy"),
            ("PAR", "Policy Adherence Rate"),
            ("SCR", "State Convergence Rate"),
            ("RCF", "Recovery from Feedback"),
            ("TER", "Token Efficiency Ratio"),
        ]

        missing_metrics = []
        for acronym, full_name in required_metrics:
            if acronym not in content and full_name.lower() not in content.lower():
                missing_metrics.append(f"{acronym} ({full_name})")

        self.assertEqual(
            missing_metrics, [],
            f"Documentation missing required MATH metrics: {missing_metrics}"
        )

    def test_03_model_comparisons_and_tracks_documented(self) -> None:
        """Verify model comparison matrix and 4 benchmark tracks are documented."""
        content = ""
        if self.HARNESS_HTML_PATH.exists():
            content += read_file_strict_utf8(self.HARNESS_HTML_PATH)
        if self.HARNESS_DOC_PATH.exists():
            content += "\n" + read_file_strict_utf8(self.HARNESS_DOC_PATH)

        required_models = ["Nous Hermes 3", "LongCat", "Qwen", "DeepSeek"]
        for model in required_models:
            self.assertIn(
                model.lower(), content.lower(),
                f"Documentation missing benchmark comparison for model: '{model}'"
            )

        required_tracks = [
            "Lighting",
            "Camera",
            "Narrative",
            "Blueprint",
        ]
        for track in required_tracks:
            self.assertIn(
                track.lower(), content.lower(),
                f"Documentation missing benchmark track: '{track}'"
            )

    def test_04_validate_assets_script_passes(self) -> None:
        """Execute tools/validate_assets.py and verify 0 hard-tier missing assets."""
        self.assertTrue(
            self.VALIDATE_ASSETS_SCRIPT.exists(),
            f"Asset validation script not found: {self.VALIDATE_ASSETS_SCRIPT}"
        )

        result = subprocess.run(
            [sys.executable, str(self.VALIDATE_ASSETS_SCRIPT)],
            cwd=str(WORKSPACE_ROOT),
            capture_output=True,
            text=True,
            timeout=30,
        )
        self.assertEqual(
            result.returncode, 0,
            f"tools/validate_assets.py failed with returncode {result.returncode}.\nSTDOUT: {result.stdout}\nSTDERR: {result.stderr}"
        )
        self.assertIn("Asset validation passed", result.stdout)


# =============================================================================
# TIER 3: Programmatic MCP & Live UE5 Content Verification
# =============================================================================

class TestTier3ProgrammaticMCPAndLiveContent(unittest.TestCase):
    """Verifies MCP server interfaces, fixtures, quests, rhythm skills, and data tables."""

    @classmethod
    def setUpClass(cls) -> None:
        """Import the Melodia MCP server dynamically."""
        from deploy.melodia_mcp_server import (
            melodia_bp_list_fixtures,
            melodia_bp_validate_fixture,
            melodia_persona_get_quests,
            melodia_rhythm_list_skills,
            melodia_quill_validate_notification,
            melodia_system_health,
        )
        cls.melodia_bp_list_fixtures = staticmethod(melodia_bp_list_fixtures)
        cls.melodia_bp_validate_fixture = staticmethod(melodia_bp_validate_fixture)
        cls.melodia_persona_get_quests = staticmethod(melodia_persona_get_quests)
        cls.melodia_rhythm_list_skills = staticmethod(melodia_rhythm_list_skills)
        cls.melodia_quill_validate_notification = staticmethod(melodia_quill_validate_notification)
        cls.melodia_system_health = staticmethod(melodia_system_health)

    def test_01_programmatic_bp_list_fixtures(self) -> None:
        """Verify melodia_bp_list_fixtures returns schema-valid fixtures including rhythm skill."""
        res = self.melodia_bp_list_fixtures()
        self.assertIsInstance(res, dict, "melodia_bp_list_fixtures must return a dict")
        self.assertEqual(res.get("schema"), "melodia.bp.fixtures.v1")
        self.assertGreater(res.get("fixture_count", 0), 0, "Fixture count must be > 0")

        fixtures = res.get("fixtures", [])
        self.assertTrue(len(fixtures) > 0, "Fixtures list must not be empty")

        fixture_names = [f.get("name") for f in fixtures]
        has_skill_fixture = any("skill" in name.lower() for name in fixture_names if name)
        self.assertTrue(
            has_skill_fixture,
            f"At least one rhythm skill fixture must be registered. Found: {fixture_names}"
        )

        # Validate single_target_resonance_skill fixture contract structure
        val = self.melodia_bp_validate_fixture("single_target_resonance_skill")
        self.assertEqual(val.get("schema"), "melodia.bp.fixture_validate.v1")
        self.assertEqual(val.get("fixture_name"), "single_target_resonance_skill")
        self.assertEqual(val.get("kind"), "melodia_content_fixture")

    def test_02_programmatic_persona_get_quests(self) -> None:
        """Verify melodia_persona_get_quests returns registered quest definitions."""
        res = self.melodia_persona_get_quests()
        self.assertIsInstance(res, dict)
        self.assertEqual(res.get("schema"), "melodia.persona.quests.v1")

        quests = res.get("quests", [])
        self.assertGreater(len(quests), 0, "Registered quests list must not be empty")

        quest_ids = [q.get("quest_id") for q in quests]
        self.assertTrue(
            any("quest." in qid for qid in quest_ids if qid),
            f"Expected canonical quest ID (e.g. 'quest.first_dream'). Found: {quest_ids}"
        )

        # Query specific quest
        target_qid = quest_ids[0]
        single_res = self.melodia_persona_get_quests(target_qid)
        self.assertEqual(single_res.get("requested_quest"), target_qid)

    def test_03_programmatic_rhythm_list_skills(self) -> None:
        """Verify melodia_rhythm_list_skills returns discovered skills and grade multipliers."""
        res = self.melodia_rhythm_list_skills()
        self.assertIsInstance(res, dict)
        self.assertEqual(res.get("schema"), "melodia.rhythm.skills.v1")

        skills = res.get("skills", [])
        self.assertGreater(len(skills), 0, "Discovered rhythm skills list must not be empty")

        grade_multipliers = res.get("grade_multipliers", {})
        expected_grades = {"Poor": 0.35, "Good": 1.0, "Great": 1.2, "Perfect": 1.5}
        for grade, mult in expected_grades.items():
            self.assertIn(grade, grade_multipliers, f"Missing grade multiplier for '{grade}'")
            self.assertAlmostEqual(
                grade_multipliers[grade], mult, places=2,
                msg=f"Grade multiplier mismatch for '{grade}'"
            )

    def test_04_rhythm_skills_datatable_json_integrity(self) -> None:
        """Verify DT_MelodySlime_Skills.json exists and contains structured skill rows."""
        dt_path = GODFILE_ROOT / "Content" / "Melodia" / "DataStuctures" / "DT_MelodySlime_Skills.json"
        self.assertTrue(dt_path.exists(), f"Skills DataTable JSON not found at {dt_path}")

        data = json.loads(read_file_strict_utf8(dt_path))
        self.assertEqual(data.get("DataType"), "SkillData")
        rows = data.get("Rows", {})
        self.assertGreater(len(rows), 0, "DT_MelodySlime_Skills.json Rows dict is empty")

        # Validate schema of first row
        first_row_key = next(iter(rows))
        row = rows[first_row_key]
        required_fields = ["skill_id", "display_name", "element", "sp_cost", "power_scalar", "note_pitches", "note_durations"]
        for field in required_fields:
            self.assertIn(field, row, f"Skill row '{first_row_key}' missing field '{field}'")

    def test_05_quill_notification_dispatch_and_system_health(self) -> None:
        """Verify Quill notification validation against the 7-verb dispatch table and system health."""
        # Test valid verb
        res = self.melodia_quill_validate_notification("melodia:quest:quest.first_dream")
        self.assertTrue(res.get("is_valid_verb"), f"Expected valid verb for quest notification: {res}")
        self.assertEqual(res.get("verb"), "melodia:quest")

        # Test health scan
        health = self.melodia_system_health()
        self.assertIn("status", health)
        self.assertIn("checks", health)
        self.assertTrue(
            health.get("checks", {}).get("specs", {}).get("allowlist_seed"),
            "Health check reports missing allowlist seed"
        )


# =============================================================================
# TIER 4: Melusina MCP & Daemon Regression Suite
# =============================================================================

class TestTier4MelusinaRegressionSuite(unittest.TestCase):
    """Executes the verified regression test suites for MCP, Ollama validation, and daemons."""

    def test_01_regression_test_melodia_mcp(self) -> None:
        """Execute Tools/test_melodia_mcp.py and assert 13/13 passing."""
        test_script = GODFILE_ROOT / "Tools" / "test_melodia_mcp.py"
        self.assertTrue(test_script.exists(), f"Script not found: {test_script}")

        result = subprocess.run(
            [sys.executable, str(test_script)],
            cwd=str(GODFILE_ROOT),
            capture_output=True,
            text=True,
            timeout=45,
        )
        self.assertEqual(
            result.returncode, 0,
            f"Tools/test_melodia_mcp.py failed with code {result.returncode}.\nSTDOUT: {result.stdout}\nSTDERR: {result.stderr}"
        )
        m = re.search(r"(\d+)/(\d+) passed, (\d+)/(\d+) failed", result.stdout)
        self.assertIsNotNone(
            m,
            "Expected MCP runner summary 'X/Y passed, Z/Y failed' in output\n"
            f"STDOUT: {result.stdout[-2000:]}\nSTDERR: {result.stderr[-2000:]}",
        )
        passed, total, failed, failed_total = (int(g) for g in m.groups())
        self.assertEqual(
            total, failed_total,
            f"MCP runner summary inconsistent: {m.group(0)}",
        )
        self.assertEqual(
            failed, 0,
            f"MCP runner reported failures: {m.group(0)}",
        )
        self.assertEqual(
            passed, total,
            f"MCP runner reported incomplete pass: {m.group(0)}",
        )

    def test_02_regression_test_melodia_ollama_validation(self) -> None:
        """Execute Tools/test_melodia_ollama_validation.py and assert 6/6 passing."""
        test_script = GODFILE_ROOT / "Tools" / "test_melodia_ollama_validation.py"
        self.assertTrue(test_script.exists(), f"Script not found: {test_script}")

        result = subprocess.run(
            [sys.executable, str(test_script)],
            cwd=str(GODFILE_ROOT),
            capture_output=True,
            text=True,
            timeout=30,
        )
        self.assertEqual(
            result.returncode, 0,
            f"Tools/test_melodia_ollama_validation.py failed with code {result.returncode}.\nSTDOUT: {result.stdout}\nSTDERR: {result.stderr}"
        )
        self.assertIn("Ran 6 tests", result.stderr + result.stdout)

    def test_03_regression_test_ollama_daemons_stress(self) -> None:
        """Execute Tools/test_ollama_daemons_stress.py and assert 19/19 passing."""
        test_script = GODFILE_ROOT / "Tools" / "test_ollama_daemons_stress.py"
        self.assertTrue(test_script.exists(), f"Script not found: {test_script}")

        result = subprocess.run(
            [sys.executable, str(test_script)],
            cwd=str(GODFILE_ROOT),
            capture_output=True,
            text=True,
            timeout=45,
        )
        self.assertEqual(
            result.returncode, 0,
            f"Tools/test_ollama_daemons_stress.py failed with code {result.returncode}.\nSTDOUT: {result.stdout}\nSTDERR: {result.stderr}"
        )
        self.assertIn("Ran 19 tests", result.stderr + result.stdout)


# =============================================================================
# Main Execution Runner & ANSI Reporting
# =============================================================================

def run_suite() -> int:
    """Run all 4 tiers and display structured diagnostic summary."""
    print("=" * 80)
    print("MELUSINA AGENT TEST HARNESS - END-TO-END RELEASE VERIFICATION SUITE")
    print("=" * 80)
    print(f"GodFile Root:   {GODFILE_ROOT}")
    print(f"Workspace Root: {WORKSPACE_ROOT}")
    print(f"Python Runtime: {sys.executable} ({sys.version.split()[0]})")
    print("-" * 80)

    loader = unittest.TestLoader()
    suite = unittest.TestSuite()

    tier_classes = [
        ("Tier 1: Repository Open-Source Hygiene Verification", TestTier1OpenSourceHygiene),
        ("Tier 2: GitPages Documentation & Asset Verification", TestTier2GitPagesDocumentation),
        ("Tier 3: Programmatic MCP & Live UE5 Content Verification", TestTier3ProgrammaticMCPAndLiveContent),
        ("Tier 4: Melusina MCP & Daemon Regression Suite", TestTier4MelusinaRegressionSuite),
    ]

    total_tests = 0
    for title, cls in tier_classes:
        tests = loader.loadTestsFromTestCase(cls)
        total_tests += tests.countTestCases()
        suite.addTests(tests)

    print(f"Loaded {total_tests} test cases across 4 verification tiers.\n")

    runner = unittest.TextTestRunner(verbosity=2)
    result = runner.run(suite)

    print("\n" + "=" * 80)
    if result.wasSuccessful():
        print(f"VERIFICATION RESULT: ALL {result.testsRun} TESTS PASSED CLEANLY (0 FAILURES, 0 ERRORS)")
        print("=" * 80)
        return 0
    else:
        print(f"VERIFICATION RESULT: FAILED ({len(result.failures)} failures, {len(result.errors)} errors)")
        print("=" * 80)
        return 1


if __name__ == "__main__":
    sys.exit(run_suite())
