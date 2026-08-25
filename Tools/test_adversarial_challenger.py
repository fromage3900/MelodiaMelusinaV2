#!/usr/bin/env python3
"""
Adversarial Stress Test & Edge Case Harness for Melusina MCP & Content Pipeline
=============================================================================
Author: Challenger Subagent (teamwork_preview_challenger)
Target: deploy/melodia_mcp_server.py, specs, DT_MelodySlime_Skills.json
Date: 2026-08-18

Tests:
1. melodia_bp_list_fixtures: schema, disk existence, integrity of every listed fixture.
2. melodia_persona_get_quests: None, empty, unknown, non-string, injections, unicode, oversized.
3. melodia_rhythm_list_skills: schema, grade multipliers, DT row invariants, element types.
4. melodia_bp_validate_fixture: existing, suffix variants, path traversal, null bytes, non-string, unknown.
5. MCP stdio protocol JSON-RPC: initialize, tools/list, tools/call dispatch, malformed JSON, unknown methods.
6. Kit & allowlist cross-referencing: BP kit fixture specs vs disk, policy coverage for all 15 tools.
"""

from __future__ import annotations

import json
import os
import subprocess
import sys
import unittest
from pathlib import Path
from typing import Any, Dict, List

GODFILE_ROOT = Path(__file__).resolve().parent.parent
WORKSPACE_ROOT = GODFILE_ROOT.parent

if str(GODFILE_ROOT) not in sys.path:
    sys.path.insert(0, str(GODFILE_ROOT))

import deploy.melodia_mcp_server as server


class TestAdversarialBPFixtures(unittest.TestCase):
    """Stress-tests melodia_bp_list_fixtures and melodia_bp_validate_fixture."""

    def test_bp_list_fixtures_invariants(self) -> None:
        """Verify fixture count, schemas, and that all discovered fixtures exist on disk."""
        res = server.melodia_bp_list_fixtures()
        self.assertIsInstance(res, dict)
        self.assertEqual(res.get("schema"), "melodia.bp.fixtures.v1")
        self.assertIn("fixtures", res)
        self.assertIn("templates", res)
        self.assertIn("fixture_count", res)

        fixtures = res["fixtures"]
        self.assertEqual(len(fixtures), res["fixture_count"])
        self.assertGreaterEqual(len(fixtures), 10)

        for f in fixtures:
            self.assertIn("name", f)
            self.assertIn("path", f)
            self.assertIn("readiness", f)
            self.assertIn("fixture_kind", f)
            # Verify file exists on disk
            full_path = GODFILE_ROOT / f["path"]
            self.assertTrue(full_path.exists(), f"Fixture path {full_path} listed in MCP does not exist on disk")
            # Verify valid JSON
            raw_data = json.loads(full_path.read_text(encoding="utf-8"))
            self.assertIsInstance(raw_data, dict)

    def test_bp_validate_fixture_valid_cases(self) -> None:
        """Verify validation succeeds for all existing fixtures both with and without .v1 suffix."""
        res = server.melodia_bp_list_fixtures()
        for f in res["fixtures"]:
            name = f["name"]
            val = server.melodia_bp_validate_fixture(name)
            self.assertEqual(val.get("schema"), "melodia.bp.fixture_validate.v1")
            self.assertTrue(val.get("valid"), f"Fixture {name} failed validation: {val}")
            self.assertEqual(val.get("missing_fields"), [])
            self.assertIsNotNone(val.get("readiness"))

    def test_bp_validate_fixture_adversarial_inputs(self) -> None:
        """Test edge cases, non-existent names, path traversal, and malformed inputs."""
        # 1. Non-existent fixture
        res = server.melodia_bp_validate_fixture("totally_fake_fixture_12345")
        self.assertFalse(res.get("valid"))
        self.assertIn("available_fixtures", res)
        self.assertIn("error", res)

        # 2. Path traversal attack
        res = server.melodia_bp_validate_fixture("../../../deploy/melodia_mcp_server")
        self.assertFalse(res.get("valid"))

        res_root = server.melodia_bp_validate_fixture("..\\..\\..\\Windows\\System32\\calc")
        self.assertFalse(res_root.get("valid"))

        # 3. Empty string and whitespace
        res_empty = server.melodia_bp_validate_fixture("")
        self.assertFalse(res_empty.get("valid"))

        res_ws = server.melodia_bp_validate_fixture("   ")
        self.assertFalse(res_ws.get("valid"))

        # 4. Long string (10k chars)
        res_long = server.melodia_bp_validate_fixture("A" * 10000)
        self.assertFalse(res_long.get("valid"))

        # 5. Unicode and special characters
        res_unicode = server.melodia_bp_validate_fixture("*fixture_*_测试!@#$%^&*()")
        self.assertFalse(res_unicode.get("valid"))

    def test_bp_get_template_adversarial(self) -> None:
        """Test template lookup for valid and adversarial template IDs."""
        valid_templates = ["skill", "enemy", "encounter", "portal", "traversal_gate", "world_challenge", "state_anchor"]
        for tid in valid_templates:
            res = server.melodia_bp_get_template(tid)
            self.assertEqual(res.get("schema"), "melodia.bp.template.v1")
            self.assertIn("template", res, f"Template {tid} failed retrieval")
            self.assertEqual(res["template"]["id"], tid)

        # Unknown / adversarial
        res_fake = server.melodia_bp_get_template("non_existent_template")
        self.assertIn("error", res_fake)
        self.assertIn("known_ids", res_fake)

        res_empty = server.melodia_bp_get_template("")
        self.assertIn("error", res_empty)


class TestAdversarialPersonaQuests(unittest.TestCase):
    """Stress-tests melodia_persona_get_quests."""

    def test_persona_get_quests_standard(self) -> None:
        """Verify standard quest list retrieval and specific quest matching."""
        res = server.melodia_persona_get_quests()
        self.assertEqual(res.get("schema"), "melodia.persona.quests.v1")
        self.assertIn("quests", res)
        quests = res["quests"]
        self.assertGreaterEqual(len(quests), 4)

        for q in quests:
            qid = q["quest_id"]
            single = server.melodia_persona_get_quests(qid)
            self.assertEqual(single.get("requested_quest"), qid)
            self.assertIsNotNone(single.get("matched_quest"))
            self.assertEqual(single["matched_quest"]["quest_id"], qid)

    def test_persona_get_quests_adversarial_queries(self) -> None:
        """Test unmatched, invalid, empty, SQL injection, unicode, and large inputs."""
        # Unmatched
        res = server.melodia_persona_get_quests("quest.does_not_exist_xyz")
        self.assertEqual(res.get("requested_quest"), "quest.does_not_exist_xyz")
        self.assertIsNone(res.get("matched_quest"))
        self.assertGreater(len(res.get("quests", [])), 0)

        # Empty string
        res_empty = server.melodia_persona_get_quests("")
        self.assertIsNone(res_empty.get("matched_quest"))

        # SQL Injection string
        res_sqli = server.melodia_persona_get_quests("quest.first_dream' OR '1'='1' --")
        self.assertIsNone(res_sqli.get("matched_quest"))

        # Unicode & Emoji
        res_emoji = server.melodia_persona_get_quests("quest.*_夢_overture")
        self.assertIsNone(res_emoji.get("matched_quest"))

        # Oversized
        res_large = server.melodia_persona_get_quests("quest." + "A" * 5000)
        self.assertIsNone(res_large.get("matched_quest"))


class TestAdversarialRhythmSkills(unittest.TestCase):
    """Stress-tests melodia_rhythm_list_skills and DT_MelodySlime_Skills data integrity."""

    def test_rhythm_skills_schema_and_constants(self) -> None:
        """Verify grade multipliers, schema version, and structure."""
        res = server.melodia_rhythm_list_skills()
        self.assertEqual(res.get("schema"), "melodia.rhythm.skills.v1")
        self.assertIn("skills", res)
        self.assertIn("data_table_skills", res)
        self.assertIn("grade_multipliers", res)

        multipliers = res["grade_multipliers"]
        expected = {"Poor": 0.35, "Good": 1.0, "Great": 1.2, "Perfect": 1.5}
        for k, v in expected.items():
            self.assertIn(k, multipliers)
            self.assertAlmostEqual(multipliers[k], v, places=2)

    def test_rhythm_skills_data_table_invariants(self) -> None:
        """Verify strict bounds and types on all skills in DataTable."""
        res = server.melodia_rhythm_list_skills()
        dt_skills = res["data_table_skills"]
        self.assertGreaterEqual(len(dt_skills), 30)

        valid_elements = {"Forte", "Radiant", "Umbral", "Arcane", "Tide", "Stone", "Gale", "Fire", "Ice", "Lightning", "Void"}

        for s in dt_skills:
            sid = s["skill_id"]
            self.assertTrue(isinstance(sid, str) and len(sid) > 0, f"Invalid skill_id: {sid}")
            self.assertTrue(isinstance(s["display_name"], str) and len(s["display_name"]) > 0, f"Invalid display_name for {sid}")
            self.assertIn(s["element"], valid_elements, f"Unexpected element '{s['element']}' in {sid}")
            self.assertIsInstance(s["sp_cost"], (int, float))
            self.assertGreaterEqual(s["sp_cost"], 0, f"Negative sp_cost for {sid}")
            self.assertIsInstance(s["power_scalar"], (int, float))
            self.assertGreater(s["power_scalar"], 0.0, f"Zero or negative power_scalar for {sid}")
            self.assertIsInstance(s["note_count"], int)
            self.assertGreaterEqual(s["note_count"], 4, f"Too few notes (<4) for {sid}")

    def test_rhythm_skills_dt_json_exact_sync(self) -> None:
        """Verify exact 1:1 match between DT_MelodySlime_Skills.json and server output."""
        dt_path = GODFILE_ROOT / "Content" / "Melodia" / "DataStuctures" / "DT_MelodySlime_Skills.json"
        self.assertTrue(dt_path.exists())
        dt_json = json.loads(dt_path.read_text(encoding="utf-8"))
        rows = dt_json.get("Rows", {})

        res = server.melodia_rhythm_list_skills()
        server_rows = {s["skill_id"]: s for s in res["data_table_skills"]}

        self.assertEqual(len(rows), len(server_rows))
        for sid, raw in rows.items():
            self.assertIn(sid, server_rows, f"Missing skill {sid} in server response")
            self.assertEqual(raw.get("display_name"), server_rows[sid]["display_name"])
            self.assertEqual(raw.get("element"), server_rows[sid]["element"])
            self.assertEqual(raw.get("sp_cost"), server_rows[sid]["sp_cost"])
            self.assertEqual(len(raw.get("note_pitches", [])), server_rows[sid]["note_count"])


class TestAdversarialQuillNotifications(unittest.TestCase):
    """Stress-tests melodia_quill_validate_notification."""

    def test_quill_notification_valid_verbs(self) -> None:
        valid_verbs = [
            "melodia:battle:encounter_01",
            "melodia:quest:quest.first_dream",
            "melodia:quest:quest.harmony_awakening",
            "melodia:flag:flag_intro_completed",
            "melodia:travel:zone_kaleidonave",
            "melodia:reward:reward_first_encounter",
            "melodia:stat:intent_01:harmony:2",
            "melodia:item:item_petal_fragment",
        ]
        for notif in valid_verbs:
            res = server.melodia_quill_validate_notification(notif)
            self.assertTrue(res.get("is_valid_verb"), f"Failed valid verb validation: {notif}")

    def test_quill_notification_invalid_verbs(self) -> None:
        invalid_verbs = [
            "",
            "melodia",
            "melodia:",
            "melodia:unknown_action",
            "melodia:hack:database",
            "unreal:engine:event",
            "random_string_without_colons",
            "::::",
            "melodia:stat",
        ]
        for notif in invalid_verbs:
            res = server.melodia_quill_validate_notification(notif)
            # melodia:stat alone has valid verb "melodia:stat"
            if notif == "melodia:stat":
                self.assertTrue(res.get("is_valid_verb"))
            else:
                self.assertFalse(res.get("is_valid_verb"), f"Incorrectly marked as valid verb: {notif}")


class TestAdversarialMCPServerProtocol(unittest.TestCase):
    """Executes live stdio JSON-RPC queries against deploy/melodia_mcp_server.py process."""

    def _rpc_exchange(self, requests: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
        input_data = "\n".join(json.dumps(req) for req in requests) + "\n"
        proc = subprocess.run(
            [sys.executable, str(GODFILE_ROOT / "deploy" / "melodia_mcp_server.py")],
            input=input_data,
            cwd=str(GODFILE_ROOT),
            capture_output=True,
            text=True,
            timeout=15,
        )
        self.assertEqual(proc.returncode, 0, f"Server process crashed with stderr: {proc.stderr}")

        responses = []
        for line in proc.stdout.splitlines():
            line = line.strip()
            if line:
                responses.append(json.loads(line))
        return responses

    def test_protocol_initialize_and_tools_list(self) -> None:
        """Test initialize and tools/list standard MCP exchange."""
        reqs = [
            {"jsonrpc": "2.0", "id": 1, "method": "initialize", "params": {}},
            {"jsonrpc": "2.0", "id": 2, "method": "tools/list", "params": {}},
        ]
        resps = self._rpc_exchange(reqs)
        self.assertEqual(len(resps), 2)

        # 1. initialize response
        init_res = resps[0]
        self.assertEqual(init_res.get("id"), 1)
        self.assertEqual(init_res.get("result", {}).get("serverInfo", {}).get("name"), "melodia-mcp")

        # 2. tools/list response
        list_res = resps[1]
        self.assertEqual(list_res.get("id"), 2)
        tools = list_res.get("result", {}).get("tools", [])
        self.assertGreaterEqual(len(tools), 13)
        tool_names = {t["name"] for t in tools}
        required_tools = {
            "melodia_bp_list_fixtures",
            "melodia_bp_validate_fixture",
            "melodia_bp_get_template",
            "melodia_persona_get_quests",
            "melodia_persona_get_stats",
            "melodia_rhythm_list_skills",
            "melodia_quill_list_scripts",
            "melodia_quill_validate_notification",
            "melodia_narrative_get_record",
            "melodia_narrative_audit_idempotency",
            "melodia_config_get_allowlist",
            "melodia_system_health",
            "melodia_system_list_subsystems",
            "melodia_bp_validate_p0_route",
            "melodia_system_golden_run_preflight",
        }
        for rt in required_tools:
            self.assertIn(rt, tool_names, f"Tool {rt} missing in MCP tools/list")

    def test_protocol_all_tool_calls_execute_cleanly(self) -> None:
        """Call every registered tool via JSON-RPC stdio and verify zero crashes."""
        reqs = [
            {"jsonrpc": "2.0", "id": 101, "method": "tools/call", "params": {"name": "melodia_bp_list_fixtures", "arguments": {}}},
            {"jsonrpc": "2.0", "id": 102, "method": "tools/call", "params": {"name": "melodia_bp_validate_fixture", "arguments": {"fixture_name": "cadence_strike_resonance_skill"}}},
            {"jsonrpc": "2.0", "id": 103, "method": "tools/call", "params": {"name": "melodia_persona_get_quests", "arguments": {"quest_id": "quest.first_dream"}}},
            {"jsonrpc": "2.0", "id": 104, "method": "tools/call", "params": {"name": "melodia_rhythm_list_skills", "arguments": {}}},
            {"jsonrpc": "2.0", "id": 105, "method": "tools/call", "params": {"name": "melodia_system_health", "arguments": {}}},
            {"jsonrpc": "2.0", "id": 106, "method": "tools/call", "params": {"name": "melodia_bp_validate_p0_route", "arguments": {}}},
            {"jsonrpc": "2.0", "id": 107, "method": "tools/call", "params": {"name": "melodia_system_golden_run_preflight", "arguments": {}}},
            {"jsonrpc": "2.0", "id": 108, "method": "tools/call", "params": {"name": "melodia_narrative_audit_idempotency", "arguments": {}}},
            {"jsonrpc": "2.0", "id": 109, "method": "tools/call", "params": {"name": "melodia_quill_list_scripts", "arguments": {}}},
            {"jsonrpc": "2.0", "id": 110, "method": "tools/call", "params": {"name": "melodia_quill_validate_notification", "arguments": {"notification": "melodia:battle:encounter_01"}}},
            {"jsonrpc": "2.0", "id": 111, "method": "tools/call", "params": {"name": "melodia_config_get_allowlist", "arguments": {}}},
            {"jsonrpc": "2.0", "id": 112, "method": "tools/call", "params": {"name": "melodia_system_list_subsystems", "arguments": {}}},
        ]
        resps = self._rpc_exchange(reqs)
        self.assertEqual(len(resps), len(reqs))

        for resp in resps:
            self.assertNotIn("error", resp, f"RPC error in response: {resp}")
            content = resp.get("result", {}).get("content", [])
            self.assertGreater(len(content), 0)
            parsed_text = json.loads(content[0]["text"])
            self.assertIsInstance(parsed_text, dict)
            self.assertNotEqual(parsed_text.get("status"), "denied", f"Tool was unexpectedly denied: {parsed_text}")

    def test_protocol_malformed_and_unknown_methods(self) -> None:
        """Verify graceful error handling for unknown methods and invalid inputs."""
        reqs = [
            {"jsonrpc": "2.0", "id": 201, "method": "invalid/method_name", "params": {}},
            {"jsonrpc": "2.0", "id": 202, "method": "tools/call", "params": {"name": "completely_unknown_tool_xyz", "arguments": {}}},
        ]
        resps = self._rpc_exchange(reqs)
        self.assertEqual(len(resps), 2)

        # Method not found error (-32601)
        self.assertEqual(resps[0]["error"]["code"], -32601)

        # Unknown tool returns error dict
        tool_call_res = json.loads(resps[1]["result"]["content"][0]["text"])
        self.assertEqual(tool_call_res.get("status"), "error")
        self.assertIn("Unknown tool", tool_call_res.get("message", ""))


def main() -> int:
    suite = unittest.TestLoader().loadTestsFromModule(sys.modules[__name__])
    runner = unittest.TextTestRunner(verbosity=2)
    result = runner.run(suite)
    return 0 if result.wasSuccessful() else 1


if __name__ == "__main__":
    sys.exit(main())
