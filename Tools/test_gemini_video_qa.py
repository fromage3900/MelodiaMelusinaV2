#!/usr/bin/env python3
"""Comprehensive test suite for Tools/gemini_video_qa.py."""

from __future__ import annotations

import json
import os
import subprocess
import sys
import tempfile
import unittest
from pathlib import Path
from unittest.mock import MagicMock, patch

# Ensure Tools directory is on sys.path
sys.path.insert(0, str(Path(__file__).resolve().parent))

import gemini_video_qa as qa


class TestGeminiVideoQA(unittest.TestCase):
    """Test suite validating Melodia video QA bridge functionality and output contracts."""

    def setUp(self):
        self.temp_dir = tempfile.TemporaryDirectory()
        self.dir_path = Path(self.temp_dir.name)

        # Create dummy video file
        self.dummy_video = self.dir_path / "test_capture.mp4"
        self.dummy_video.write_bytes(b"MELODIA_TEST_VIDEO_PAYLOAD_12345\n" * 100)

    def tearDown(self):
        self.temp_dir.cleanup()

    def test_sanitize_secret(self):
        """Verify API keys and sensitive tokens are redacted from logs and errors."""
        secret_key = "AIzaSyD1234567890abcdefghijklmnopqrstuv"
        raw_msg = f"Error connecting with key {secret_key} to endpoint."
        sanitized = qa.sanitize_secret(raw_msg)
        self.assertNotIn(secret_key, sanitized)
        self.assertIn("[REDACTED_API_KEY]", sanitized)

        bearer_msg = "Authorization: Bearer secret_token_xyz_12345"
        sanitized_bearer = qa.sanitize_secret(bearer_msg)
        self.assertNotIn("secret_token_xyz_12345", sanitized_bearer)
        self.assertIn("[REDACTED_TOKEN]", sanitized_bearer)

    def test_compute_file_hash_and_size(self):
        """Verify deterministic SHA-256 calculation and file size."""
        sha256, size = qa.compute_file_hash_and_size(self.dummy_video)
        self.assertEqual(len(sha256), 64)
        self.assertEqual(size, len(b"MELODIA_TEST_VIDEO_PAYLOAD_12345\n" * 100))

        # Check non-existent file
        with self.assertRaises(FileNotFoundError):
            qa.compute_file_hash_and_size(self.dir_path / "non_existent.mp4")

    def test_missing_api_key_exit(self):
        """Verify missing GEMINI_API_KEY fails with actionable error message and exit code 1."""
        env = {k: v for k, v in os.environ.items() if k != "GEMINI_API_KEY"}
        cmd = [
            sys.executable,
            str(Path(__file__).parent / "gemini_video_qa.py"),
            "--video",
            str(self.dummy_video),
            "--profile",
            "overworld-ui",
        ]
        proc = subprocess.run(cmd, env=env, capture_output=True, text=True)
        self.assertEqual(proc.returncode, 1)
        self.assertIn("GEMINI_API_KEY environment variable is not set", proc.stderr)

    def test_verify_agentic_processing(self):
        """Verify detection of processing_call / processing_result steps."""
        # 1. With valid dynamic processing steps
        steps_with_proc = [
            {"type": "user_input", "content": [{"type": "text", "text": "start"}]},
            {"type": "processing_call", "id": "proc_123"},
            {"type": "processing_result", "call_id": "proc_123"},
            {"type": "model_output", "content": [{"type": "text", "text": "verdict"}]},
        ]
        verified, calls = qa.verify_agentic_processing(steps_with_proc)
        self.assertTrue(verified)
        self.assertEqual(len(calls), 2)
        self.assertEqual(calls[0]["type"], "processing_call")
        self.assertEqual(calls[0]["id"], "proc_123")
        self.assertEqual(calls[1]["type"], "processing_result")
        self.assertEqual(calls[1]["call_id"], "proc_123")

        # 2. Without processing steps (e.g. model failed to search timeline)
        steps_without_proc = [
            {"type": "user_input", "content": [{"type": "text", "text": "start"}]},
            {"type": "model_output", "content": [{"type": "text", "text": "verdict"}]},
        ]
        verified_no, calls_no = qa.verify_agentic_processing(steps_without_proc)
        self.assertFalse(verified_no)
        self.assertEqual(len(calls_no), 0)

    def test_parse_interaction_output(self):
        """Verify parsing of clean JSON, code-fenced JSON, and malformed responses."""
        valid_dict = {
            "overall_verdict": "PASS",
            "interactions": [
                {
                    "timestamp": "00:10.000",
                    "control": "Reticle",
                    "expected": "Dims to 32%",
                    "observed": "Dims properly",
                    "verdict": "PASS",
                    "confidence": 0.95,
                    "evidence_type": "visual_observation",
                }
            ],
            "defects": [],
            "healthy_sections": [],
            "manual_rechecks": [],
        }

        # Clean JSON
        parsed1 = qa.parse_interaction_output(json.dumps(valid_dict))
        self.assertEqual(parsed1["overall_verdict"], "PASS")
        self.assertEqual(len(parsed1["interactions"]), 1)

        # Code-fenced markdown JSON
        fenced = f"```json\n{json.dumps(valid_dict, indent=2)}\n```"
        parsed2 = qa.parse_interaction_output(fenced)
        self.assertEqual(parsed2["overall_verdict"], "PASS")

        # Wrapped JSON with surrounding text
        wrapped = f"Analysis complete. Here is the JSON:\n{json.dumps(valid_dict)}\nEnd of report."
        parsed3 = qa.parse_interaction_output(wrapped)
        self.assertEqual(parsed3["overall_verdict"], "PASS")

        # Invalid JSON
        with self.assertRaises(ValueError):
            qa.parse_interaction_output("Not JSON at all")

    def test_mock_run_contract_shape(self):
        """Verify the mock execution satisfies the full Output Contract base shape."""
        out_json = self.dir_path / "output_report.json"
        raw_json = self.dir_path / "raw_response.json"

        report = qa.run_video_qa(
            video_path=self.dummy_video,
            profile="overworld-ui",
            out_path=out_json,
            model="gemini-3.8-flash",
            processing_mode="agentic",
            save_raw=str(raw_json),
            mock=True,
        )

        # Verify contract keys
        self.assertEqual(report["schema_version"], 1)
        self.assertEqual(report["profile"], "overworld-ui")
        self.assertEqual(report["model"], "gemini-3.8-flash")
        self.assertEqual(report["processing_mode_requested"], "agentic")
        self.assertTrue(report["processing_mode_verified"])
        self.assertIn(report["overall_verdict"], ("PASS", "FAIL", "REVIEW"))

        # Video metadata
        video_meta = report["video"]
        self.assertEqual(video_meta["path"], str(self.dummy_video))
        self.assertEqual(len(video_meta["sha256"]), 64)
        self.assertGreater(video_meta["size_bytes"], 0)

        # Collections
        self.assertIsInstance(report["interactions"], list)
        self.assertIsInstance(report["defects"], list)
        self.assertIsInstance(report["healthy_sections"], list)
        self.assertIsInstance(report["manual_rechecks"], list)

        # Interaction entry verification
        self.assertGreater(len(report["interactions"]), 0)
        interaction_entry = report["interactions"][0]
        for key in ("timestamp", "control", "expected", "observed", "verdict", "confidence", "evidence_type"):
            self.assertIn(key, interaction_entry)

        # Defect entry verification
        self.assertGreater(len(report["defects"]), 0)
        defect_entry = report["defects"][0]
        for key in (
            "timestamp",
            "severity",
            "category",
            "observation",
            "expected",
            "confidence",
            "evidence_type",
            "recommended_recheck",
        ):
            self.assertIn(key, defect_entry)

        # Healthy section verification
        self.assertGreater(len(report["healthy_sections"]), 0)
        healthy_entry = report["healthy_sections"][0]
        for key in ("start_timestamp", "end_timestamp", "feature", "observation"):
            self.assertIn(key, healthy_entry)

        # Manual recheck verification
        self.assertGreater(len(report["manual_rechecks"]), 0)
        recheck_entry = report["manual_rechecks"][0]
        for key in ("timestamp", "reason", "context"):
            self.assertIn(key, recheck_entry)

        # Output files on disk
        self.assertTrue(out_json.exists())
        self.assertTrue(raw_json.exists())
        self.assertEqual(report["raw_response_path"], str(raw_json))

        # Check content on disk matches report
        disk_report = json.loads(out_json.read_text(encoding="utf-8"))
        self.assertEqual(disk_report["video"]["sha256"], report["video"]["sha256"])

    def test_mock_cli_execution(self):
        """Verify CLI execution in mock mode via subprocess."""
        out_json = self.dir_path / "cli_report.json"
        cmd = [
            sys.executable,
            str(Path(__file__).parent / "gemini_video_qa.py"),
            "--video",
            str(self.dummy_video),
            "--profile",
            "overworld-ui",
            "--out",
            str(out_json),
            "--mock",
        ]
        proc = subprocess.run(cmd, capture_output=True, text=True)
        self.assertEqual(proc.returncode, 0, f"CLI stderr: {proc.stderr}")
        self.assertTrue(out_json.exists())
        data = json.loads(out_json.read_text(encoding="utf-8"))
        self.assertEqual(data["profile"], "overworld-ui")
        self.assertEqual(data["overall_verdict"], "FAIL")

    def test_mocked_real_client_flow(self):
        """Verify the full SDK execution path using mocked GenAI Client."""
        mock_file_active = MagicMock()
        mock_file_active.name = "files/test_file_001"
        mock_file_active.uri = "https://generativelanguage.googleapis.com/v1beta/files/test_file_001"
        mock_file_active.state = "ACTIVE"
        mock_file_active.mime_type = "video/mp4"

        mock_payload = {
            "overall_verdict": "PASS",
            "interactions": [
                {
                    "timestamp": "00:05.100",
                    "control": "BowHUD Reticle",
                    "expected": "Reticle dims during idle",
                    "observed": "Reticle opacity drops to 32%",
                    "verdict": "PASS",
                    "confidence": 0.98,
                    "evidence_type": "visual_observation",
                }
            ],
            "defects": [],
            "healthy_sections": [
                {
                    "start_timestamp": "00:00.000",
                    "end_timestamp": "00:10.000",
                    "feature": "Locomotion UI",
                    "observation": "HUD stable",
                }
            ],
            "manual_rechecks": [],
        }

        mock_step_call = MagicMock()
        mock_step_call.type = "processing_call"
        mock_step_call.id = "call_xyz"

        mock_step_res = MagicMock()
        mock_step_res.type = "processing_result"
        mock_step_res.call_id = "call_xyz"

        mock_interaction = MagicMock()
        mock_interaction.output_text = json.dumps(mock_payload)
        mock_interaction.steps = [mock_step_call, mock_step_res]
        mock_interaction.model_dump.return_value = {"id": "int_123", "steps": []}
        mock_interaction.usage = MagicMock()
        mock_interaction.usage.prompt_tokens = 500
        mock_interaction.usage.candidates_tokens = 200
        mock_interaction.usage.total_tokens = 700

        mock_client = MagicMock()
        mock_client.files.upload.return_value = mock_file_active
        mock_client.files.get.return_value = mock_file_active
        mock_client.interactions.create.return_value = mock_interaction

        with patch.dict(os.environ, {"GEMINI_API_KEY": "fake_test_key"}), patch(
            "gemini_video_qa.genai.Client", return_value=mock_client
        ):
            report = qa.run_video_qa(
                video_path=self.dummy_video,
                profile="animation",
                model="gemini-3.8-flash",
                processing_mode="agentic",
                mock=False,
            )

            # Assertions
            self.assertEqual(report["profile"], "animation")
            self.assertEqual(report["overall_verdict"], "PASS")
            self.assertTrue(report["processing_mode_verified"])
            self.assertEqual(report["execution_metadata"]["processing_steps_found"], 2)
            self.assertEqual(report["execution_metadata"]["token_usage"]["total_tokens"], 700)

            # Check interaction.create was called with agentic processing
            create_call_kwargs = mock_client.interactions.create.call_args.kwargs
            self.assertEqual(create_call_kwargs["model"], "gemini-3.8-flash")
            inputs = create_call_kwargs["input"]
            video_input = [item for item in inputs if item.get("type") == "video"][0]
            self.assertEqual(video_input["processing"], "agentic")
            self.assertEqual(video_input["uri"], mock_file_active.uri)

    def test_agentic_unverified_when_no_processing_steps(self):
        """Verify that processing_mode_verified is False when agentic mode was requested but no processing steps occurred."""
        mock_file_active = MagicMock()
        mock_file_active.name = "files/test_file_002"
        mock_file_active.uri = "https://generativelanguage.googleapis.com/v1beta/files/test_file_002"
        mock_file_active.state = "ACTIVE"
        mock_file_active.mime_type = "video/mp4"

        mock_payload = {
            "overall_verdict": "PASS",
            "interactions": [],
            "defects": [],
            "healthy_sections": [],
            "manual_rechecks": [],
        }

        # Interaction response with NO processing_call / processing_result steps
        mock_interaction = MagicMock()
        mock_interaction.output_text = json.dumps(mock_payload)
        mock_interaction.steps = [
            MagicMock(type="user_input"),
            MagicMock(type="model_output"),
        ]
        mock_interaction.model_dump.return_value = {"id": "int_456"}

        mock_client = MagicMock()
        mock_client.files.upload.return_value = mock_file_active
        mock_client.files.get.return_value = mock_file_active
        mock_client.interactions.create.return_value = mock_interaction

        with patch.dict(os.environ, {"GEMINI_API_KEY": "fake_test_key"}), patch(
            "gemini_video_qa.genai.Client", return_value=mock_client
        ):
            report = qa.run_video_qa(
                video_path=self.dummy_video,
                profile="overworld-ui",
                processing_mode="agentic",
                mock=False,
            )
            # Requested agentic, but no processing_call steps -> processing_mode_verified must be False!
            self.assertEqual(report["processing_mode_requested"], "agentic")
            self.assertFalse(report["processing_mode_verified"])
            self.assertEqual(report["execution_metadata"]["processing_steps_found"], 0)

    def test_static_processing_mode(self):
        """Verify that static processing mode sets processing_mode_verified to True."""
        mock_file_active = MagicMock()
        mock_file_active.name = "files/test_file_003"
        mock_file_active.uri = "https://generativelanguage.googleapis.com/v1beta/files/test_file_003"
        mock_file_active.state = "ACTIVE"
        mock_file_active.mime_type = "video/mp4"

        mock_payload = {
            "overall_verdict": "PASS",
            "interactions": [],
            "defects": [],
            "healthy_sections": [],
            "manual_rechecks": [],
        }

        mock_interaction = MagicMock()
        mock_interaction.output_text = json.dumps(mock_payload)
        mock_interaction.steps = []
        mock_interaction.model_dump.return_value = {"id": "int_789"}

        mock_client = MagicMock()
        mock_client.files.upload.return_value = mock_file_active
        mock_client.files.get.return_value = mock_file_active
        mock_client.interactions.create.return_value = mock_interaction

        with patch.dict(os.environ, {"GEMINI_API_KEY": "fake_test_key"}), patch(
            "gemini_video_qa.genai.Client", return_value=mock_client
        ):
            report = qa.run_video_qa(
                video_path=self.dummy_video,
                profile="environment",
                processing_mode="static",
                mock=False,
            )
            self.assertEqual(report["processing_mode_requested"], "static")
            self.assertTrue(report["processing_mode_verified"])

    def test_all_profiles_supported(self):
        """Verify all defined profiles can be invoked cleanly."""
        profiles = ["overworld-ui", "animation", "environment", "choral-sheep", "gameplay", "custom"]
        for p in profiles:
            report = qa.run_video_qa(
                video_path=self.dummy_video,
                profile=p,
                custom_prompt="Extra check" if p == "custom" else None,
                mock=True,
            )
            self.assertEqual(report["profile"], p)
            self.assertIn("overall_verdict", report)

    def test_cli_stdout_output(self):
        """Verify CLI writes formatted JSON to stdout when --out is omitted."""
        cmd = [
            sys.executable,
            str(Path(__file__).parent / "gemini_video_qa.py"),
            "--video",
            str(self.dummy_video),
            "--profile",
            "overworld-ui",
            "--mock",
        ]
        proc = subprocess.run(cmd, capture_output=True, text=True)
        self.assertEqual(proc.returncode, 0)
        # Parse stdout as JSON
        data = json.loads(proc.stdout)
        self.assertEqual(data["schema_version"], 1)
        self.assertEqual(data["profile"], "overworld-ui")

    def test_cli_file_not_found(self):
        """Verify non-existent video triggers clean error and exit code 1."""
        cmd = [
            sys.executable,
            str(Path(__file__).parent / "gemini_video_qa.py"),
            "--video",
            str(self.dir_path / "does_not_exist.mp4"),
            "--mock",
        ]
        proc = subprocess.run(cmd, capture_output=True, text=True)
        self.assertEqual(proc.returncode, 1)
    def test_interaction_transient_retry(self):
        """Verify client.interactions.create retries on 503 transient errors and succeeds."""
        mock_file_active = MagicMock()
        mock_file_active.state = "ACTIVE"
        mock_file_active.name = "files/test_file_retry"
        mock_file_active.uri = "https://generativelanguage.googleapis.com/v1beta/files/test_file_retry"

        mock_payload = {
            "overall_verdict": "PASS",
            "interactions": [],
            "defects": [],
            "healthy_sections": [],
            "manual_rechecks": [],
        }

        mock_interaction = MagicMock()
        mock_interaction.output_text = json.dumps(mock_payload)
        mock_interaction.steps = [
            {"type": "processing_call", "id": "call_1"},
            {"type": "processing_result", "call_id": "call_1"},
        ]
        mock_interaction.model_dump.return_value = {"id": "int_retry"}

        mock_client = MagicMock()
        mock_client.files.upload.return_value = mock_file_active
        mock_client.files.get.return_value = mock_file_active
        # First call fails with 503, second succeeds
        mock_client.interactions.create.side_effect = [
            Exception("Error code: 503 - {'error': {'message': 'gemini-3.8-flash is currently experiencing high demand', 'code': 'service_unavailable'}}"),
            mock_interaction,
        ]

        with patch.dict(os.environ, {"GEMINI_API_KEY": "fake_test_key"}), patch(
            "gemini_video_qa.genai.Client", return_value=mock_client
        ), patch("gemini_video_qa.time.sleep", return_value=None):
            report = qa.run_video_qa(
                video_path=self.dummy_video,
                profile="animation",
                processing_mode="agentic",
                mock=False,
            )
            self.assertEqual(report["overall_verdict"], "PASS")
            self.assertEqual(mock_client.interactions.create.call_count, 2)


if __name__ == "__main__":
    unittest.main()
