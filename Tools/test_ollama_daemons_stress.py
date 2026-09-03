#!/usr/bin/env python3
"""Comprehensive adversarial and stress testing suite for Melodia Ollama Daemons and Fallback routing.

Covers:
- deploy/ollama_dialogue_daemon.py
- deploy/ollama_gumroad_copy_daemon.py
- scripts/daemon_content_gen.py
- Tools/ollama_health.py
"""
from __future__ import annotations

import json
import os
import sys
import unittest
from pathlib import Path
from unittest.mock import MagicMock, patch

TOOLS_DIR = Path(__file__).resolve().parent
ROOT_DIR = TOOLS_DIR.parent
SCRIPTS_DIR = ROOT_DIR.parent / "scripts"
DEPLOY_DIR = ROOT_DIR / "deploy"

sys.path.insert(0, str(TOOLS_DIR))
sys.path.insert(0, str(SCRIPTS_DIR))
sys.path.insert(0, str(DEPLOY_DIR))

import daemon_content_gen as dcg
import ollama_dialogue_daemon as odd
import ollama_gumroad_copy_daemon as ogcd
import ollama_health


class _MockResponse:
    def __init__(self, data: dict | bytes | str, status: int = 200):
        if isinstance(data, dict):
            self.content = json.dumps(data).encode("utf-8")
        elif isinstance(data, str):
            self.content = data.encode("utf-8")
        else:
            self.content = data
        self.status = status

    def __enter__(self):
        return self

    def __exit__(self, *args):
        return False

    def read(self):
        return self.content


class TestOllamaDialogueDaemonStress(unittest.TestCase):
    """Stress tests for deploy/ollama_dialogue_daemon.py."""

    def test_resolve_model_env_dialogue_specific(self):
        with patch.dict(os.environ, {"OLLAMA_DIALOGUE_MODEL": "test-dialogue-model:latest"}):
            self.assertEqual(odd.resolve_model(), "test-dialogue-model:latest")

    def test_resolve_model_env_generic(self):
        with patch.dict(os.environ, {"OLLAMA_DIALOGUE_MODEL": "", "OLLAMA_MODEL": "test-generic:14b"}):
            self.assertEqual(odd.resolve_model(), "test-generic:14b")

    @patch("urllib.request.urlopen")
    def test_resolve_model_tags_preferred_hierarchy(self, mock_urlopen):
        mock_urlopen.return_value = _MockResponse({
            "models": [
                {"name": "deepseek-coder:6.7b"},
                {"name": "deepseek-r1:14b"},
            ]
        })
        # deepseek-r1:14b has higher priority than deepseek-coder:6.7b in PREFERRED_MODELS
        with patch.dict(os.environ, {}, clear=True):
            resolved = odd.resolve_model("http://fake/tags")
            self.assertEqual(resolved, "deepseek-r1:14b")

    @patch("urllib.request.urlopen")
    def test_resolve_model_tags_unrecognized_fallback(self, mock_urlopen):
        mock_urlopen.return_value = _MockResponse({
            "models": [{"name": "custom-finetune:v1"}]
        })
        with patch.dict(os.environ, {}, clear=True):
            resolved = odd.resolve_model("http://fake/tags")
            self.assertEqual(resolved, "custom-finetune:v1")

    @patch("urllib.request.urlopen")
    def test_resolve_model_tags_unreachable_fallback(self, mock_urlopen):
        mock_urlopen.side_effect = OSError("Connection refused")
        with patch.dict(os.environ, {}, clear=True):
            resolved = odd.resolve_model("http://fake/tags")
            self.assertEqual(resolved, "qwen2.5-coder:7b")

    def test_run_dry_run_success(self):
        exit_code = odd.run_dry_run("qwen2.5-coder:7b")
        self.assertEqual(exit_code, 0)


class TestOllamaGumroadCopyDaemonStress(unittest.TestCase):
    """Stress tests for deploy/ollama_gumroad_copy_daemon.py."""

    def test_resolve_model_env_gumroad_specific(self):
        with patch.dict(os.environ, {"OLLAMA_GUMROAD_MODEL": "test-gumroad:7b"}):
            self.assertEqual(ogcd.resolve_model(), "test-gumroad:7b")

    @patch("urllib.request.urlopen")
    def test_resolve_model_tags_preferred(self, mock_urlopen):
        mock_urlopen.return_value = _MockResponse({
            "models": [{"name": "qwen2.5-coder:14b"}]
        })
        with patch.dict(os.environ, {}, clear=True):
            self.assertEqual(ogcd.resolve_model("http://fake/tags"), "qwen2.5-coder:14b")

    @patch("urllib.request.urlopen")
    def test_resolve_model_unreachable_fallback(self, mock_urlopen):
        mock_urlopen.side_effect = OSError("Timed out")
        with patch.dict(os.environ, {}, clear=True):
            self.assertEqual(ogcd.resolve_model("http://fake/tags"), "qwen2.5-coder:7b")

    def test_run_dry_run_success(self):
        exit_code = ogcd.run_dry_run("qwen2.5-coder:7b")
        self.assertEqual(exit_code, 0)


class TestDaemonContentGenStress(unittest.TestCase):
    """Stress tests for scripts/daemon_content_gen.py."""

    @patch("daemon_content_gen._http_post_json")
    def test_primary_muse_success(self, mock_post):
        mock_post.return_value = (200, {"choices": [{"message": {"content": "Dialogue content"}}]})
        res = dcg.generate_muse_narrative()
        self.assertTrue(res)
        self.assertEqual(mock_post.call_count, 1)
        self.assertEqual(mock_post.call_args[0][1]["model"], "meta/muse-spark-1.2")

    @patch("daemon_content_gen._http_post_json")
    def test_403_forbidden_cloud_fallback(self, mock_post):
        mock_post.side_effect = [
            (403, {"error": {"message": "Age attestation required"}}),
            (200, {"choices": [{"message": {"content": "Un-gated cloud fallback dialogue"}}]}),
        ]
        res = dcg.generate_muse_narrative()
        self.assertTrue(res)
        self.assertEqual(mock_post.call_count, 2)
        self.assertEqual(mock_post.call_args_list[1][0][1]["model"], "deepseek/deepseek-v4-flash")

    @patch("daemon_content_gen._http_post_json")
    def test_403_and_cloud_fail_local_ollama_fallback(self, mock_post):
        mock_post.side_effect = [
            (403, {"error": {"message": "Forbidden"}}),
            (502, "Bad Gateway"),
            (200, {"choices": [{"message": {"content": "Local Ollama dialogue"}}]}),
        ]
        res = dcg.generate_muse_narrative()
        self.assertTrue(res)
        self.assertEqual(mock_post.call_count, 3)
        self.assertEqual(mock_post.call_args_list[2][0][1]["model"], "qwen2.5-coder:7b")

    @patch("daemon_content_gen._http_post_json")
    def test_all_fallbacks_failing_gracefully(self, mock_post):
        mock_post.side_effect = [
            (403, {"error": {"message": "Forbidden"}}),
            (503, "Service Unavailable"),
            (-1, "Connection refused"),
        ]
        res = dcg.generate_muse_narrative()
        self.assertFalse(res)
        self.assertEqual(mock_post.call_count, 3)

    @patch("daemon_content_gen._http_post_json")
    def test_qwen_logic_generation(self, mock_post):
        mock_post.return_value = (200, {"choices": [{"message": {"content": '{"difficulty": 1.2}'}}]})
        self.assertTrue(dcg.generate_qwen_logic())

        mock_post.return_value = (-1, "Socket timeout")
        self.assertFalse(dcg.generate_qwen_logic())

    def test_dry_run_execution(self):
        self.assertEqual(dcg.run_dry_run(), 0)


class TestOllamaHealthStress(unittest.TestCase):
    """Stress tests for Tools/ollama_health.py."""

    @patch("urllib.request.urlopen")
    def test_probe_lane_fallbacks_active(self, mock_urlopen):
        def fake_urlopen(request, timeout):
            if request.full_url.endswith("/api/version"):
                return _MockResponse({"version": "0.32.14"})
            return _MockResponse({
                "models": [
                    {"name": "deepseek-r1:7b"},
                    {"name": "qwen2.5-coder:7b"},
                ]
            })

        mock_urlopen.side_effect = fake_urlopen
        report = ollama_health.probe("http://127.0.0.1:11434")
        self.assertTrue(report["healthy"])
        self.assertEqual(report["lanes"]["reasoning"]["model"], "deepseek-r1:7b")
        self.assertEqual(report["lanes"]["creative"]["model"], "deepseek-r1:7b")
        self.assertEqual(report["lanes"]["heavy_code"]["model"], "qwen2.5-coder:7b")
        self.assertEqual(report["missing_models"], [])

    @patch("urllib.request.urlopen")
    def test_probe_unreachable_endpoint(self, mock_urlopen):
        mock_urlopen.side_effect = OSError("Connection refused")
        report = ollama_health.probe("http://127.0.0.1:19999")
        self.assertFalse(report["reachable"])
        self.assertFalse(report["healthy"])
        self.assertIn("Connection refused", report["error"])

    @patch("urllib.request.urlopen")
    def test_probe_malformed_json_response(self, mock_urlopen):
        mock_urlopen.return_value = _MockResponse(b"MALFORMED_NON_JSON")
        report = ollama_health.probe("http://127.0.0.1:11434")
        self.assertFalse(report["healthy"])
        self.assertIn("invalid JSON", report["error"])


if __name__ == "__main__":
    unittest.main()
